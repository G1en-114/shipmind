#!/usr/bin/env bash
# 全链路冒烟：夹具 → 各 Skill → 统一评测 → Harness 自检
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "== 1/4 生成夹具 =="
python evals/make_fixtures.py

echo "== 2/4 统一评测 =="
python evals/run_evals.py

echo "== 3/4 Harness 自检（注册表/路由/plan 执行/轨迹）=="
python -m harness.selftest

echo "== 4/4 轨迹 diff 演示 =="
python - <<'PY'
import json
from harness.trajectory import load, diff
steps = load("runs/selftest/trajectory.jsonl")
print(json.dumps({"recorded_steps": len(steps)}, ensure_ascii=False))
PY

echo "SMOKE OK"
