#!/usr/bin/env python3
"""证据审核 Agent（verifier）：逐条核对"结论 ↔ 证据"，无证据即驳回。

多智能体协同的实证：主 Agent 产出报告后，由本模块独立复核——
每条结论必须能指到具体证据（声学特征数值 / 视觉框 / 手册原文引用 / 声纹谱线 /
雷达检测参数），否则标记 rejected 并给出缺失项。禁止无证据结论进入最终输出。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 证据引用格式："<skill>/<case_id>:<字段路径>"，如 acoustic-001:evidence
# 本模块只做结构与存在性校验（证据是否被引用、被引用处是否真有内容），
# 不重复判断证据本身的正确性（那是各 Skill 自己 evals 的职责）。

REQUIRED_REF_FIELDS = {
    "acoustic": ["evidence"],
    "radar": ["targets"],
    "sonar": ["evidence"],
    "visual": ["readings"],
    "route": ["max_xte_m"],
    "rag": ["answers"],
}


def split_ref(ref: str) -> tuple[str, str]:
    """'acoustic-001:evidence' → ('acoustic-001', 'evidence')"""
    if ":" in ref:
        head, _, field = ref.partition(":")
        return head, field
    return ref, ""


def resolve(evidence_pool: dict, ref: str):
    """从证据池按引用路径取值。证据池形如 {step_id: output_dict}。"""
    step_id, field = split_ref(ref)
    payload = evidence_pool.get(step_id)
    if payload is None:
        return None, f"引用不存在: {step_id}"
    if not field:
        return payload, None
    cur = payload
    for part in field.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None, f"字段路径无效: {ref}"
    return cur, None


def verify(claims: list[dict], evidence_pool: dict) -> dict:
    """claims: [{claim, evidence_refs: [...]}]"""
    accepted, rejected = [], []
    for i, c in enumerate(claims):
        text = (c.get("claim") or "").strip()
        refs = c.get("evidence_refs") or []
        problems = []
        if not text:
            problems.append("结论为空")
        if not refs:
            problems.append("无证据引用")
        for ref in refs:
            val, err = resolve(evidence_pool, ref)
            if err:
                problems.append(err)
            elif val in (None, "", [], {}):
                problems.append(f"证据为空: {ref}")
        if problems:
            rejected.append({"index": i, "claim": text, "problems": problems})
        else:
            accepted.append({"index": i, "claim": text, "n_refs": len(refs)})
    return {
        "ok": not rejected,
        "n_claims": len(claims),
        "n_accepted": len(accepted),
        "n_rejected": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "verdict": "通过" if not rejected else f"驳回 {len(rejected)} 条",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?",
                    help='JSON 文件：{"claims": [...], "evidence_pool": {...}}；缺省读 stdin')
    args = ap.parse_args()
    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON 解析失败: {e}", "rejected": True},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    if "claims" not in data or "evidence_pool" not in data:
        print(json.dumps({"error": "需要 claims 与 evidence_pool 两个字段"},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    result = verify(data["claims"], data["evidence_pool"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
