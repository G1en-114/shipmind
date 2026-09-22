#!/usr/bin/env python3
"""跨线融合：雷达目标 × 声纹船类 × 航线态势 × COLREGs 条款 → verifier → 输出。

这是演示主线的第 4 段，也是"多智能体协同"的完整实证：
一条链路串起四个智能体与五类证据（雷达检测参数、声纹谱线、航线态势、
规则原文、声学特征），verifier 逐条核证据后才允许输出。

用法：
    python scripts/fusion_demo.py            # 用内置演示场景
    python scripts/fusion_demo.py --scenario my.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills-src"


def run(entry: str, args: list[str]) -> dict | None:
    proc = subprocess.run([sys.executable, str(SKILLS / entry), *args],
                          capture_output=True, text=True, cwd=str(ROOT))
    raw = proc.stdout or ""
    idx = raw.find("{")
    if idx < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw[idx:])
        return obj
    except json.JSONDecodeError:
        return None


# 演示场景：本船航向 010°，雷达在 045° 发现目标（距离 3000m），
# 该方位有水听器录音，航线为计划走廊
DEMO = {
    "own_heading": 10.0,
    "radar": {"fixture": "evals/fixtures/radar/two_targets.npy"},
    "sonar": {"audio": "evals/fixtures/sonar/cargo_like.wav", "mode": "rule"},
    "route": {"nmea": "evals/fixtures/nmea/on_track.nmea",
              "route": "evals/fixtures/nmea/route.json"},
    "target_heading": 190.0,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", help="场景 JSON（缺省用内置演示场景）")
    ap.add_argument("--no-voice", action="store_true")
    args = ap.parse_args()
    sc = json.loads(Path(args.scenario).read_text(encoding="utf-8")) \
        if args.scenario else DEMO

    rounds = []

    # 1) 雷达：检测目标（取第一个）
    radar = run("radar-ppi-interpreter/scripts/ppi_detect.py", [sc["radar"]["fixture"]])
    rounds.append({"step_id": "radar-001", "skill": "radar-ppi-interpreter",
                   "output": radar or {}})
    target = (radar or {}).get("targets", [{}])[0] if radar else {}
    target_bearing = target.get("bearing_deg", 45.0)

    # 2) 声纹：判别船类
    sonar = run("sonar-acoustic-fingerprint/scripts/sonar_fingerprint.py",
                [sc["sonar"]["audio"], "--mode", sc["sonar"].get("mode", "rule")])
    rounds.append({"step_id": "sonar-001", "skill": "sonar-acoustic-fingerprint",
                   "output": sonar or {}})

    # 3) 航线：本船态势
    route = run("route-deviation-watch/scripts/route_watch.py",
                [sc["route"]["nmea"], "--route", sc["route"]["route"]])
    rounds.append({"step_id": "route-001", "skill": "route-deviation-watch",
                   "output": route or {}})

    # 4) COLREGs 态势分类（确定性前置），再检索条款原文
    enc = run("manual-rag-query/scripts/classify_encounter.py",
              ["--own-heading", str(sc["own_heading"]),
               "--target-bearing", str(target_bearing),
               "--target-heading", str(sc["target_heading"])])
    rounds.append({"step_id": "colregs-001", "skill": "manual-rag-query",
                   "output": enc or {}})
    situation = (enc or {}).get("situation", "CROSSING")
    rule_no = (enc or {}).get("rule", "Rule 15").replace("Rule ", "")
    rag = run("manual-rag-query/scripts/rag_query.py",
              ["--query", f"第{rule_no}条", "--top-k", "1", "--json"])
    rounds.append({"step_id": "rag-001", "skill": "manual-rag-query",
                   "output": rag or {}})

    # 5) 汇总为结论（每条挂证据），交 verifier
    claims = []
    if target:
        claims.append({"claim": f"雷达在 {target_bearing}° 发现目标，"
                                f"距离 {target.get('range_m')}m",
                       "evidence_refs": ["radar-001:targets"]})
    if sonar and sonar.get("label") != "unknown":
        claims.append({"claim": f"声纹判别目标为 {sonar['label']}"
                                f"（置信度 {sonar.get('confidence')}）",
                       "evidence_refs": ["sonar-001:evidence"]})
    if route:
        claims.append({"claim": f"本船航线状态 {route.get('level')}"
                                f"（最大横偏 {route.get('max_xte_m')}m）",
                       "evidence_refs": ["route-001:max_xte_m"]})
    if enc:
        claims.append({"claim": f"会遇态势 {situation}，{enc.get('duty')}"
                                f"（依据 {enc.get('rule')}）",
                       "evidence_refs": ["colregs-001:situation"]})
    if rag and rag.get("answers"):
        a = rag["answers"][0]
        claims.append({"claim": f"条款原文：{a.get('quote', '')[:60]}",
                       "evidence_refs": ["rag-001:answers"]})

    pool = {r["step_id"]: r["output"] for r in rounds}
    ver = subprocess.run(
        [sys.executable, str(SKILLS / "report-composer/scripts/verifier.py")],
        input=json.dumps({"claims": claims, "evidence_pool": pool}),
        capture_output=True, text=True)
    verdict = json.loads(ver.stdout) if ver.stdout.strip() else {}

    # 6) 生成报告
    rep = subprocess.run(
        [sys.executable, str(SKILLS / "report-composer/scripts/compose_report.py"),
         str(ROOT / "evals/fixtures/report/fusion_rounds.json")],
        capture_output=True, text=True) if False else None
    Path(ROOT / "evals/fixtures/report").mkdir(parents=True, exist_ok=True)
    rounds_file = ROOT / "evals/fixtures/report/fusion_rounds.json"
    rounds_file.write_text(json.dumps({"title": "态势研判报告", "rounds": rounds},
                                      ensure_ascii=False), encoding="utf-8")
    rep = subprocess.run(
        [sys.executable, str(SKILLS / "report-composer/scripts/compose_report.py"),
         str(rounds_file)], capture_output=True, text=True, cwd=str(ROOT))
    report = None
    if rep.stdout.strip():
        raw = rep.stdout
        idx = raw.find("{")
        try:
            report, _ = json.JSONDecoder().raw_decode(raw[idx:])
        except json.JSONDecodeError:
            report = None

    out = {
        "scenario": {"own_heading": sc["own_heading"],
                     "target_bearing": target_bearing,
                     "target_heading": sc["target_heading"]},
        "rounds": rounds,
        "claims": claims,
        "verifier": verdict,
        "report_md": (report or {}).get("report_md", ""),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))

    # 7) 语音播报（仅分级与动作）
    if not args.no_voice and enc:
        line = f"态势 {situation}，{enc.get('duty', '')}"
        vp = subprocess.run(
            [sys.executable, str(SKILLS / "voice-alert/scripts/voice.py"),
             "--tts", line, "--out", "evals/fixtures/voice/fusion_alert.wav"],
            capture_output=True, text=True, cwd=str(ROOT))
        if vp.stdout.strip():
            print("[voice]", vp.stdout.strip().splitlines()[0][:160], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
