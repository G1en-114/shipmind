"""输出契约校验：Skill 的结构化输出缺字段/错类型即失败，残缺结果不得进入下游。"""
from __future__ import annotations

import json
from pathlib import Path

_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


def load_contract(skill_dir: Path) -> dict | None:
    p = Path(skill_dir) / "contract.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def validate(contract: dict, output: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for key in contract.get("required", []):
        if key not in output:
            errors.append(f"缺少必填字段: {key}")
    for key, typ in contract.get("types", {}).items():
        if key not in output:
            continue
        expected = _TYPES.get(typ)
        value = output[key]
        if expected and not isinstance(value, expected):
            errors.append(f"字段 {key} 类型应为 {typ}，实为 {type(value).__name__}")
        elif typ == "number" and isinstance(value, bool):
            errors.append(f"字段 {key} 类型应为 number，实为 bool")
    return (not errors), errors
