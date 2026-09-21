#!/usr/bin/env bash
# 机舱声学异常哨兵 — 统一入口
# 适配层：处理本地环境差异，官方 Skill 本体保持不被修改。
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Windows 上 python3 常解析到应用商店占位程序，因此优先用 python。
if [[ -z "${PYTHON:-}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON=python
  else
    PYTHON=python3
  fi
fi

exec "$PYTHON" "$SKILL_DIR/scripts/acoustic_sentinel.py" "$@"
