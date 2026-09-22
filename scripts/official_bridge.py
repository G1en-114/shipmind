#!/usr/bin/env python3
"""官方 NVIDIA Skill 桥接层：让 6 个官方 Skill 真正进入我们的编排链路。

两种接入方式（如实区分，不虚构）：
  - **executable**（已实测可跑）：deepstream-generate-pipeline 有零依赖脚本，
    本模块直接执行它，返回真实 gst-launch pipeline。
  - **advisory**（指令型 Skill）：官方 Skill 无可执行入口，按 Skill 范式的
    "渐进式披露"由本模块返回其 SKILL.md 内容（name/description 常驻，正文按需展开），
    并附实测前置条件。**需要 NGC/TAO/VSS 栈的 4 个如实标注，不假装能跑。**

用法：
    python scripts/official_bridge.py --list
    python scripts/official_bridge.py --skill deepstream-generate-pipeline \
        --query "process a recorded mp4 with inference"
    python scripts/official_bridge.py --skill rag-blueprint --query "如何部署 RAG"
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "official-skills" / "manifest.json"
DEFAULT_INSTALL = ROOT / "official-skills" / "installed"  # 仓库内 vendored 副本（自包含）


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def install_path() -> Path:
    return Path(os.environ.get("OFFICIAL_SKILLS_DIR", str(DEFAULT_INSTALL)))


def list_skills() -> list[dict]:
    m = load_manifest()
    out = []
    for s in m["skills"]:
        installed = (install_path() / s["name"] / "SKILL.md").exists()
        out.append({"name": s["name"], "executable": s["executable"],
                    "installed": installed, "license": s["license"],
                    "prerequisites": s["prerequisites"]})
    return out


def run_executable(skill: dict, query: str, top_k: int = 3) -> dict:
    """真跑官方 Skill 的可执行入口。"""
    base = install_path() / skill["name"]
    entry = base / skill["entry"]
    if not entry.exists():
        return {"ok": False, "error": f"入口不存在: {entry}",
                "hint": "官方 Skill 未安装到本机"}
    proc = subprocess.run(
        [sys.executable, str(entry), "--query", query,
         "--top-k", str(top_k), "--format", "json"],
        capture_output=True, text=True, cwd=str(entry.parent), timeout=300)
    raw = proc.stdout or ""
    i = raw.find("{")
    if i < 0:
        return {"ok": False, "error": "官方 Skill 无 JSON 输出",
                "stderr_tail": proc.stderr[-300:]}
    data, _ = json.JSONDecoder().raw_decode(raw[i:])
    pipelines = [p.get("pipeline") for p in data.get("retrieved_pipelines", [])
                 if p.get("pipeline")]
    return {"ok": True, "executed": True, "skill": skill["name"],
            "confidence": data.get("confidence"),
            "pipelines": pipelines[:top_k],
            "n_retrieved": data.get("num_retrieved")}


def run_advisory(skill: dict, query: str, max_chars: int = 1500) -> dict:
    """指令型 Skill：按渐进式披露返回 SKILL.md 正文。"""
    sk = install_path() / skill["name"] / "SKILL.md"
    if not sk.exists():
        return {"ok": False, "error": f"SKILL.md 不存在: {sk}",
                "hint": "官方 Skill 未安装到本机"}
    text = sk.read_text(encoding="utf-8")
    body = text.split("---", 2)[-1].strip() if text.startswith("---") else text
    return {"ok": True, "executed": False, "skill": skill["name"],
            "mode": "advisory",
            "prerequisites": skill["prerequisites"],
            "our_usage": skill.get("our_usage", ""),
            "guidance": body[:max_chars],
            "note": "官方 Skill 为指令型（供 Agent 展开），非 CLI 工具；"
                    "其前置条件未满足时不假装执行，如实返回其指令内容供参考"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--skill")
    ap.add_argument("--query")
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    if args.list:
        print(json.dumps({"install_path": str(install_path()),
                          "skills": list_skills()}, ensure_ascii=False, indent=2))
        return 0
    if not args.skill or not args.query:
        ap.error("需要 --skill 与 --query（或用 --list）")

    m = load_manifest()
    skill = next((s for s in m["skills"] if s["name"] == args.skill), None)
    if skill is None:
        print(json.dumps({"ok": False,
                          "error": f"未知 Skill: {args.skill}",
                          "available": [s["name"] for s in m["skills"]]},
                         ensure_ascii=False), file=sys.stderr)
        return 2

    out = (run_executable(skill, args.query, args.top_k)
           if skill["executable"] else run_advisory(skill, args.query))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
