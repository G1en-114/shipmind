#!/usr/bin/env python3
"""骨架自检：注册表 → 路由（含负向）→ plan 执行（契约校验 + 轨迹落盘）。

在仓库根目录运行：python harness/selftest.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.orchestrator import Orchestrator  # noqa: E402


def main() -> int:
    orch = Orchestrator(run_dir="runs/selftest")
    ready = sorted(n for n, s in orch.skills.items() if s.entry)
    planned = sorted(n for n, s in orch.skills.items() if not s.entry)
    print("== Skill 注册表 ==")
    print(json.dumps({"ready": ready, "planned": planned}, ensure_ascii=False, indent=2))

    print("== 路由（含负向用例）==")
    for q in ["3号泵声音不对，帮我听听有没有异响",
              "帮我查一下手册里轴承磨损的章节",
              "今天晚饭吃什么"]:
        hit = orch.route(q)
        print(json.dumps({"query": q, "route": hit.name if hit else None},
                         ensure_ascii=False))

    print("== plan 执行（声学 Skill）==")
    plan = [{
        "skill": "engine-room-acoustic-sentinel",
        "args": ["compare", "evals/fixtures/acoustic/pump_bearing_worn_01.wav",
                 "--baseline", "evals/fixtures/acoustic/baseline", "--device", "pump"],
    }]
    results = orch.execute_plan(plan)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
