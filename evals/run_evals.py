#!/usr/bin/env python3
"""统一评测运行器：执行各 Skill 的 cases.jsonl，输出 PASS/FAIL 表与 last_run.json。

夹具缺失时自动调用 make_fixtures.py。退出码：全过 0，否则 1。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ["normal", "watch", "alarm", "critical"]

SKILLS = [
    {"name": "engine-room-acoustic-sentinel",
     "entry": "skills-src/engine-room-acoustic-sentinel/scripts/acoustic_sentinel.py",
     "cases": "skills-src/engine-room-acoustic-sentinel/evals/cases.jsonl",
     "checker": "acoustic"},
    {"name": "route-deviation-watch",
     "entry": "skills-src/route-deviation-watch/scripts/route_watch.py",
     "cases": "skills-src/route-deviation-watch/evals/cases.jsonl",
     "checker": "route"},
    {"name": "radar-ppi-interpreter",
     "entry": "skills-src/radar-ppi-interpreter/scripts/ppi_detect.py",
     "cases": "skills-src/radar-ppi-interpreter/evals/cases.jsonl",
     "checker": "radar"},
    {"name": "sonar-acoustic-fingerprint",
     "entry": "skills-src/sonar-acoustic-fingerprint/scripts/sonar_fingerprint.py",
     "cases": "skills-src/sonar-acoustic-fingerprint/evals/cases.jsonl",
     "checker": "sonar"},
    {"name": "navlog-autofill",
     "entry": "skills-src/navlog-autofill/scripts/navlog.py",
     "cases": "skills-src/navlog-autofill/evals/cases.jsonl",
     "checker": "navlog"},
    {"name": "manual-rag-query",
     "entry": "skills-src/manual-rag-query/scripts/rag_query.py",
     "cases": "skills-src/manual-rag-query/evals/cases.jsonl",
     "checker": "rag"},
    {"name": "engine-room-visual-inspector",
     "entry": "skills-src/engine-room-visual-inspector/scripts/visual_inspect.py",
     "cases": "skills-src/engine-room-visual-inspector/evals/cases.jsonl",
     "checker": "visual"},
]


def first_json(text: str) -> dict | None:
    idx = text.find("{")
    if idx < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[idx:])
        return obj
    except json.JSONDecodeError:
        return None


def build_args(checker: str, case: dict) -> list[str]:
    if checker == "acoustic":
        return ["compare", case["audio"], "--baseline",
                "evals/fixtures/acoustic/baseline",
                "--device", case.get("device", "pump")]
    if checker == "route":
        return [case["nmea"], "--route", case["route"]]
    if checker == "radar":
        return [case["fixture"]]
    if checker == "sonar":
        return [case["audio"], "--mode", "rule"]
    if checker == "navlog":
        return [case["events"]]
    if checker == "rag":
        return ["--query", case["query"], "--top-k", "3", "--json"]
    if checker == "visual":
        if case.get("mode") == "aggregate":
            return ["--eval-dir", case["eval_dir"]]
        return [case["fixture"]]
    raise ValueError(checker)


def check(case: dict, rc: int, out: dict | None) -> tuple[bool, str]:
    if case.get("expect") == "rejected":
        return rc == 2, f"rc={rc}"
    if rc == 2 or out is None:
        return False, f"意外拒绝或无 JSON (rc={rc})"
    if "expect_level" in case:
        return out.get("level") == case["expect_level"], f"level={out.get('level')}"
    if "expect_level_min" in case:
        lv = out.get("level")
        ok = lv in LEVELS and LEVELS.index(lv) >= LEVELS.index(case["expect_level_min"])
        return ok, f"level={lv}"
    if "expect_features" in case:
        feats = {e.get("feature") for e in out.get("evidence", []) if isinstance(e, dict)}
        ok = bool(set(case["expect_features"]) & feats)
        return ok, f"evidence={sorted(f for f in feats if f)}"
    if "expect_min_targets" in case:
        n = out.get("n_targets", 0)
        return n >= case["expect_min_targets"], f"n_targets={n}"
    if case.get("expect_zero_targets"):
        n = out.get("n_targets", -1)
        return n == 0, f"n_targets={n}"
    if "expect_label_contains" in case:
        label = out.get("label", "")
        return case["expect_label_contains"] in label, f"label={label}"
    if "expect_label" in case:
        return out.get("label") == case["expect_label"], f"label={out.get('label')}"
    if "expect_n_events" in case:
        return out.get("n_events") == case["expect_n_events"], f"n_events={out.get('n_events')}"
    if case.get("expect") == "no_hit":
        answers = out.get("answers", [])
        ok = answers == [] and bool(out.get("note"))
        return ok, f"answers={len(answers)} note={'有' if out.get('note') else '无'}"
    if "expect_source_contains" in case:
        answers = out.get("answers", [])
        if not answers:
            return False, "无命中"
        # 检索质量按 recall@3 衡量：期望来源出现在前三即算命中
        # （同一问题常有多个相关章节，如泵手册故障表与 SMS 响应程序都相关）
        top3 = answers[:3]
        src_ok = any(case["expect_source_contains"] in a.get("source", "") for a in top3)
        sec_ok = any(case.get("expect_section_contains", "") in a.get("section", "")
                     for a in top3)
        quote_ok = all(len(a.get("quote", "")) >= 5 for a in answers)
        ok = src_ok and sec_ok and quote_ok
        return ok, f"top3={[a.get('source') + ':' + a.get('section', '')[:12] for a in top3]}"
    if "expect_frac_mae_max" in case:
        mae = out.get("frac_mae", 1.0)
        n = out.get("n", 0)
        ok = mae <= case["expect_frac_mae_max"] and n >= case.get("expect_n_min", 1)
        return ok, f"n={n} frac_mae={mae} rejected={out.get('n_rejected')}"
    return True, "no expectation"


def main() -> int:
    fixtures = ROOT / "evals" / "fixtures"
    if not fixtures.exists():
        print(">> fixtures 缺失，生成中…")
        subprocess.run([sys.executable, str(ROOT / "evals" / "make_fixtures.py")],
                       check=True, cwd=ROOT)

    results, n_pass = [], 0
    for sk in SKILLS:
        cases_path = ROOT / sk["cases"]
        cases = [json.loads(line) for line in
                 cases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for case in cases:
            args = build_args(sk["checker"], case)
            proc = subprocess.run([sys.executable, str(ROOT / sk["entry"]), *args],
                                  capture_output=True, text=True, cwd=ROOT)
            out = first_json(proc.stdout or "")
            ok, note = check(case, proc.returncode, out)
            n_pass += ok
            results.append({"skill": sk["name"], "id": case["id"],
                            "pass": ok, "note": note})
            print(f"[{'PASS' if ok else 'FAIL'}] {sk['name']}/{case['id']}  {note}")

    total = len(results)
    print(f"\n{n_pass}/{total} passed")
    (ROOT / "evals" / "last_run.json").write_text(json.dumps(
        {"passed": n_pass, "total": total, "results": results},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if n_pass == total else 1


if __name__ == "__main__":
    sys.exit(main())
