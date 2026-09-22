"""编排骨架：显式 plan 执行器 + 路由。

真实 LLM 规划（Step 3.7 Flash，经 OpenAI 兼容端点）在 key 就绪后接入，
接口保持不变：plan = [{"skill": <name>, "args": [...]}]，每步产出经
contract 校验并记入执行轨迹。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from .contracts import load_contract, validate
from .registry import load_skills
from .router import route
from .trajectory import TrajectoryRecorder

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_first_json(text: str) -> dict | None:
    """Skill 输出末尾允许带 MEDIA: 行，取首个完整 JSON 对象。"""
    idx = text.find("{")
    if idx < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[idx:])
        return obj
    except json.JSONDecodeError:
        return None


class Orchestrator:
    def __init__(self, run_dir: str | Path = "runs/demo"):
        self.skills = {s.name: s for s in load_skills()}
        self.recorder = TrajectoryRecorder(run_dir)

    def route(self, query: str):
        return route(query, list(self.skills.values()))

    def route_smart(self, query: str) -> tuple[str | None, str]:
        """大脑优先路由，关键词路由兜底。返回 (skill名或None, 路由方式)。"""
        from .brain import choose_skill
        try:
            ready = [s for s in self.skills.values() if s.entry]
            name = choose_skill(query, ready)
            if name is None:
                return None, "brain"
            s = self.skills.get(name)
            if s and s.name != "official-bridge" and (
                    (s.entry and s.origin == "self")
                    or s.origin == "official"):
                return name, "brain"
        except Exception:
            pass  # 大脑不可达时静默降级，值守系统不能因路由器失联而停摆
        hit = self.route(query)
        return (hit.name, "keyword") if hit else (None, "keyword")

    def execute_step(self, skill_name: str, args: list[str]) -> dict:
        skill = self.skills.get(skill_name)
        if skill is None or skill.entry is None or skill.dir is None:
            return {"ok": False, "error": f"skill 不可用: {skill_name}"}
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, str(skill.entry), *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        duration = time.time() - t0
        output = parse_first_json(proc.stdout or "")
        ok, errors = True, []
        contract = load_contract(skill.dir)
        if contract and output is not None:
            ok, errors = validate(contract, output)
        accepted = proc.returncode in (0, 1) and output is not None and ok
        result = {
            "ok": accepted,
            "skill": skill_name,
            "returncode": proc.returncode,
            "duration_s": round(duration, 3),
            "output": output,
        }
        if errors:
            result["contract_errors"] = errors
        if proc.returncode not in (0, 1) and proc.stderr:
            result["stderr_tail"] = proc.stderr.strip().splitlines()[-1]
        self.recorder.record(skill_name, args, output or {}, proc.returncode, duration)
        return result

    def execute_official(self, skill_name: str, query: str) -> dict:
        """派发到官方 NVIDIA Skill（经 scripts/official_bridge.py）。"""
        skill = self.skills.get(skill_name)
        if skill is None or skill.origin != "official":
            return {"ok": False, "error": f"不是官方 Skill: {skill_name}"}
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "official_bridge.py"),
             "--skill", skill_name, "--query", query],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=600)
        raw = proc.stdout or ""
        i = raw.find("{")
        if i < 0:
            return {"ok": False, "error": "桥接层无输出",
                    "stderr_tail": proc.stderr[-300:]}
        out, _ = json.JSONDecoder().raw_decode(raw[i:])
        self.recorder.record(f"official/{skill_name}", [query],
                             out, proc.returncode, 0.0)
        return out

    def execute_plan(self, plan: list[dict]) -> list[dict]:
        return [self.execute_step(step["skill"], step["args"]) for step in plan]
