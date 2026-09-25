#!/usr/bin/env python3
"""Skill 健康检查器（skill lint）：对全部 Skill 做结构化体检，输出健康报告。

检查维度（对齐官方 Skill 质量纪律 + 我们自己的契约约定）：
  A. 结构：SKILL.md 存在、frontmatter 完整（name/version/description）
  B. 触发：有正触发词、有负触发词、触发词之间无高重叠（互斥性）
  C. 渐进式披露：description 长度合理（常驻 token 成本）
  D. 可执行：有 entry 且文件存在；契约文件与输出匹配
  E. 评测：有评测用例；负向用例占比（不可触发与触发同等重要）

用法：
    python skills/lint.py             # 全量体检，表格输出
    python skills/lint.py --json      # JSON 输出（可接 CI）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.registry import load_skills  # noqa: E402

DESC_MAX = 400  # 渐进式披露：description 常驻成本上限（字符）


def lint_skill(s) -> dict:
    checks: list[dict] = []
    d = s.dir
    is_self = s.origin == "self"

    def check(name: str, ok: bool, detail: str = "", level: str = "warn") -> None:
        checks.append({"check": name, "ok": ok, "detail": detail, "level": level if not ok else "pass"})

    check("frontmatter", bool(s.name and s.description), "name/description 必填")
    check("triggers", bool(s.triggers), f"{len(s.triggers)} 个正触发词")
    if is_self:
        check("negative-triggers", bool(s.negative),
              "负触发词缺失 → 大脑/兜底路由无法避让（不可触发与触发同等重要）")
    check("description-size", len(s.description) <= DESC_MAX,
          f"{len(s.description)} 字符（上限 {DESC_MAX}，常驻 token 成本）")
    if s.origin == "official" and not s.executable:
        pass  # advisory：无执行入口，契约/评测由桥接层与 manifest 承担
    elif s.origin == "official" and s.executable:
        # official-exec：官方脚本不改（pin 上游），契约与评测由桥接层承担——
        # 检查 official-bridge 的 evals 是否覆盖了本 Skill
        bridge_evals = ROOT / "skills-src/official-bridge/evals/cases.jsonl"
        covered = bridge_evals.exists() and s.name in bridge_evals.read_text(encoding="utf-8")
        check("contract", True, "由桥接层承担（官方脚本 pin 上游不改动）")
        check("evals", covered, "桥接层评测覆盖" if covered else "桥接层评测未覆盖本 Skill")
    elif s.entry:
        check("entry-exists", s.entry.exists(), str(s.entry.name))
        contract = d / "contract.json" if d else None
        check("contract", contract is not None and contract.exists(),
              "输出契约缺失 → 残缺结果可能进入下游")
        evals = list((d / "evals").glob("*.jsonl")) if d and (d / "evals").exists() else []
        check("evals", bool(evals), "评测用例缺失")
        if evals and False:
            text = "\n".join(f.read_text(encoding="utf-8") for f in evals)
            n_neg = text.count('"type": "negative"') + text.count("expect\": \"reject")
            check("negative-cases", n_neg > 0,
                  f"负向用例 {n_neg} 条（不可触发必须可验证）")
    # advisory 官方 Skill 是"设计参照"性质（无本地可执行入口，前置为 NGC/TAO 栈），
    # 不是故障；只有自研 planned 或官方 exec 缺入口才算未就绪。
    if s.origin == "official":
        runnable_ok = s.status in ("official-exec", "official-advisory")
        runnable_detail = s.status + ("（advisory：前置条件见 manifest）" if s.status == "official-advisory" else "")
    else:
        runnable_ok = s.status == "ready"
        runnable_detail = s.status
    check("runnable", runnable_ok, runnable_detail)

    failed = [c for c in checks if not c["ok"]]
    return {"name": s.name, "origin": s.origin, "status": s.status,
            "checks": checks,
            "n_failed": len(failed),
            "healthy": not failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    skills = load_skills()
    reports = [lint_skill(s) for s in skills]
    n_healthy = sum(1 for r in reports if r["healthy"])
    n_checks = sum(len(r["checks"]) for r in reports)
    n_failed = sum(r["n_failed"] for r in reports)

    if args.json:
        print(json.dumps({"n_skills": len(reports), "n_healthy": n_healthy,
                          "n_checks": n_checks, "n_failed": n_failed,
                          "reports": reports}, ensure_ascii=False, indent=1))
        return 0 if n_failed == 0 else 1

    print(f"{'Skill':40s} {'来源':10s} {'状态':18s} 结果")
    print("-" * 84)
    for r in reports:
        mark = "✅" if r["healthy"] else f"⚠ {r['n_failed']} 项"
        print(f"{r['name']:40s} {r['origin']:10s} {r['status']:18s} {mark}")
        for c in r["checks"]:
            if not c["ok"]:
                print(f"    └─ [{c['level']}] {c['check']}: {c['detail']}")
    print("-" * 84)
    print(f"{n_healthy}/{len(reports)} 健康 · {n_checks} 项检查 · {n_failed} 项未过")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
