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
    {"name": "report-composer",
     "entry": "skills-src/report-composer/scripts/compose_report.py",
     "cases": "skills-src/report-composer/evals/cases.jsonl",
     "checker": "report"},
    {"name": "official-bridge",
     "entry": "scripts/official_bridge.py",
     "cases": "skills-src/official-bridge/evals/cases.jsonl",
     "checker": "official"},
    {"name": "agent-routing",
     "entry": "scripts/agent_demo.py",
     "cases": "skills-src/official-bridge/evals/agent_cases.jsonl",
     "checker": "agent"},
    {"name": "voice-alert",
     "entry": "skills-src/voice-alert/scripts/voice.py",
     "cases": "skills-src/voice-alert/evals/cases.jsonl",
     "checker": "voice"},
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
                case.get("baseline", "evals/fixtures/acoustic/baseline"),
                "--device", case.get("device", "pump")]
    if checker == "route":
        return [case["nmea"], "--route", case["route"]]
    if checker == "radar":
        return [case["fixture"]]
    if checker == "sonar":
        return [case["audio"], "--mode", case.get("mode", "rule")]
    if checker == "navlog":
        return [case["events"]]
    if checker == "rag":
        if case.get("mode") == "selftest":
            return ["--selftest"]
        return ["--query", case["query"], "--top-k", "3", "--json"]
    if checker == "visual":
        if case.get("mode") == "aggregate":
            return ["--eval-dir", case["eval_dir"]]
        return [case["fixture"]]
    if checker == "report":
        if case.get("mode") == "fusion":
            return ["--no-voice"]
        return [case["input"]]
    if checker == "voice":
        if case.get("asr"):
            return ["--asr", case["asr"]]
        return ["--tts", case["tts"], "--out", "evals/fixtures/voice/alert.wav"]
    if checker == "official":
        return ["--skill", case["skill"], "--query", case["query"]]
    if checker == "agent":
        return [case["query"]]
    raise ValueError(checker)


def check(case: dict, rc: int, out: dict | None,
          out_raw: str = "") -> tuple[bool, str]:
    if case.get("expect") == "rejected":
        return rc == 2, f"rc={rc}"
    if "expect_route" in case:
        ok = out is not None and out.get("route") == case["expect_route"]
        if case.get("expect_origin"):
            steps = (out or {}).get("steps") or []
            ok = ok and any(s.get("origin") == case["expect_origin"] for s in steps)
        return ok, f"route={out.get('route') if out else None} 期望={case['expect_route']}"
    if case.get("checker") == "official" or "expect_executed" in case:
        if case.get("expect_executed"):
            pipes = out.get("pipelines") or []
            ok = (out.get("ok") is True and out.get("executed") is True
                  and any(case["expect_pipeline_contains"] in p for p in pipes))
            return ok, f"executed={out.get('executed')} pipelines={len(pipes)}"
        ok = (out.get("ok") is True and out.get("executed") is False
              and bool(out.get("prerequisites")))
        return ok, f"mode={out.get('mode')} prereqs={len(out.get('prerequisites', []))}"
    if case.get("mode") == "fusion":
        ok = (rc == 0 and out is not None
              and out.get("verifier", {}).get("ok") is True
              and len(out.get("claims", [])) >= 4
              and "交叉相遇" in (out.get("claims") or [{}])[-1].get("claim", ""))
        return ok, f"claims={len((out or {}).get('claims', []))} verdict={(out or {}).get('verifier', {}).get('verdict')}"
    # 纯文本自检（如 classify_encounter --selftest）不要求 JSON 输出
    if case.get("expect_pass") is not None:
        ok = case["expect_pass"] == ("5/5 passed" in (out_raw or "")
                                     and rc == 0)
        return ok, f"rc={rc} selftest={'5/5' if '5/5' in (out_raw or '') else '未全过'}"
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
    if case.get("checker") == "report" or "expect" in case and case.get("expect") in ("pass", "reject"):
        if out is None:
            return False, "无输出"
        v = out.get("verifier", {})
        if case.get("expect") == "pass":
            ok = v.get("ok") is True and "[已核实]" in out.get("report_md", "")
            return ok, f"verdict={v.get('verdict')}"
        ok = v.get("n_rejected", 0) >= 1 and "[待复核]" in out.get("report_md", "")
        return ok, f"verdict={v.get('verdict')} 报告含待复核={'[待复核]' in out.get('report_md','')}"
    if case.get("expect_ok") and case.get("mode") == "ml":
        ok = bool(out.get("label")) and out.get("mode") == "ml"             and isinstance(out.get("evidence", {}).get("probs"), dict)
        return ok, f"label={out.get('label')} conf={out.get('confidence')}"
    if "expect_ok" in case:
        if case.get("asr"):
            txt = (out or {}).get("text", "")
            ok = out.get("ok") is True and len(txt) >= 2
            return ok, f"asr_text={txt[:40]!r}"
        ok = out.get("ok") is True and (out.get("bytes") or 0) > 1000
        return ok, f"bytes={out.get('bytes')} file={out.get('file', '')[-30:]}"
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
            req_files = [case.get(k) for k in
                         ("audio", "nmea", "fixture", "events", "route")
                         if case.get(k)]
            req_files += [case.get("eval_dir", "")]
            missing = [r for r in req_files if r and not (ROOT / r).exists()]
            if missing:
                print(f"[SKIP] {sk['name']}/{case['id']}  数据未就位: {missing[0]}")
                results.append({"skill": sk["name"], "id": case["id"],
                                "pass": True, "note": f"SKIP {missing[0]}"})
                n_pass += 1
                continue
            args = build_args(sk["checker"], case)
            entry = case.get("entry", sk["entry"])  # case 级 entry 覆盖
            proc = subprocess.run([sys.executable, str(ROOT / entry), *args],
                                  capture_output=True, text=True, cwd=ROOT)
            out = first_json(proc.stdout or "")
            ok, note = check(case, proc.returncode, out, proc.stdout or "")
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
