#!/usr/bin/env python3
"""端到端编排演示：用户一句话 → 大脑路由 → 执行（自研/官方）→ verifier → 播报。

这是"多智能体协同"的可演示形态：主 Agent（大脑）根据输入选择 Skill，
自研 Skill 走子进程执行，官方 Skill 走桥接层；结论经 verifier 逐条核证据后才输出。

与 scripts/fusion_demo.py 的区别：后者是固定场景脚本；本模块由大脑**动态决策**。

用法：
    python scripts/agent_demo.py "3号泵有异响，帮我判断"
    python scripts/agent_demo.py "偏航了吗"
    python scripts/agent_demo.py "生成一个处理机舱录像的 deepstream 管线"
    python scripts/agent_demo.py --batch          # 跑内置四连问
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.orchestrator import Orchestrator  # noqa: E402

# 自研 Skill 的演示参数（真实数据/夹具）
SELF_ARGS = {
    "engine-room-acoustic-sentinel": ["compare", "evals/fixtures/acoustic/anom/pump_bearing_worn_01.wav",
                                      "--baseline", "evals/fixtures/acoustic/baseline",
                                      "--device", "pump"],
    "route-deviation-watch": ["evals/fixtures/nmea/watch_drift.nmea",
                              "--route", "evals/fixtures/nmea/route.json"],
    "radar-ppi-interpreter": ["evals/fixtures/radar/two_targets.npy"],
    "sonar-acoustic-fingerprint": ["evals/fixtures/sonar/cargo_like.wav", "--mode", "rule"],
    "engine-room-visual-inspector": ["evals/fixtures/gauges/train/train_00000.jpg"],
}

BATCH = [
    "3号泵刚才有金属摩擦声，帮我判断一下",
    "我们现在偏出航线了吗",
    "雷达上有什么目标",
    "帮我生成一个处理机舱录像的 deepstream 管线",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--no-voice", action="store_true")
    args = ap.parse_args()

    orch = Orchestrator(run_dir="runs/agent_demo")
    queries = BATCH if args.batch else ([args.query] if args.query else None)
    if not queries:
        ap.error("需要 query 或 --batch")

    results = []
    for q in queries:
        name, how = orch.route_smart(q)
        rec = {"query": q, "route": name, "route_via": how, "steps": []}
        if name is None:
            rec["note"] = "大脑判断无需调用任何 Skill（负向路由）"
            results.append(rec)
            print(json.dumps(rec, ensure_ascii=False))
            continue

        skill = orch.skills[name]
        if skill.origin == "official":
            out = orch.execute_official(name, q)
            rec["steps"].append({"skill": name, "origin": "official",
                                 "executed": out.get("executed"),
                                 "summary": (out.get("pipelines") or [""])[0][:80]
                                 if out.get("executed") else
                                 f"advisory（前置：{'/'.join(out.get('prerequisites', []))}）"})
        else:
            sargs = SELF_ARGS.get(name, [])
            r = orch.execute_step(name, sargs) if sargs else {"ok": False, "error": "无演示参数"}
            out = r.get("output") or {}
            rec["steps"].append({
                "skill": name, "origin": "self", "ok": r.get("ok"),
                "summary": (f"{out.get('level', out.get('label', out.get('situation', '')))}"
                            f" {out.get('n_targets', '') or ''}").strip()})
        rec["result_keys"] = sorted(out.keys())[:6] if isinstance(out, dict) else []
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False))

    # 汇总：大脑路由命中率
    n_official = sum(1 for r in results
                     if any(s.get("origin") == "official" for s in r["steps"]))
    print(json.dumps({
        "n_queries": len(results),
        "routed": sum(1 for r in results if r["route"]),
        "negative_routed": sum(1 for r in results if r["route"] is None),
        "official_dispatched": n_official,
        "trajectory": "runs/agent_demo/trajectory.jsonl",
    }, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
