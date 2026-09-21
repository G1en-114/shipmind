"""执行轨迹录制与回放：每次 Skill 执行追加一条 JSONL，可回放、可 diff。

这是"像调试二进制程序一样调试 Agent"的载体：同一段素材跑两次，
diff 报出哪个步骤、哪些字段变了——确定性验收（同素材 5 次结果一致）就靠它。
"""
from __future__ import annotations

import json
import time
from pathlib import Path


class TrajectoryRecorder:
    def __init__(self, run_dir: str | Path = "runs/demo"):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / "trajectory.jsonl"
        self._f = open(self.path, "a", encoding="utf-8")

    def record(self, skill: str, args: list[str], output: dict,
               returncode: int, duration_s: float) -> None:
        self._f.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "skill": skill,
            "args": args,
            "returncode": returncode,
            "duration_s": round(duration_s, 3),
            "output": output,
        }, ensure_ascii=False) + "\n")
        self._f.flush()

    def close(self) -> None:
        self._f.close()


def load(path: str | Path) -> list[dict]:
    return [json.loads(line)
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def diff(path_a: str | Path, path_b: str | Path) -> dict:
    """比较两次执行：同步骤输出不一致即报出（字段级）。"""
    a, b = load(path_a), load(path_b)
    changes: list[dict] = []
    for i, (sa, sb) in enumerate(zip(a, b)):
        if sa["skill"] != sb["skill"]:
            changes.append({"step": i, "kind": "skill_changed",
                            "a": sa["skill"], "b": sb["skill"]})
            continue
        keys = set(sa["output"] or ()) | set(sb["output"] or ())
        fields = sorted(k for k in keys
                        if (sa["output"] or {}).get(k) != (sb["output"] or {}).get(k))
        if fields:
            changes.append({"step": i, "kind": "output_changed",
                            "skill": sa["skill"], "fields": fields})
    if len(a) != len(b):
        changes.append({"kind": "step_count", "a": len(a), "b": len(b)})
    return {"identical": not changes, "changes": changes}
