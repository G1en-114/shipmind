#!/usr/bin/env python3
"""巡检报告生成：汇集多源证据 → 逐条挂证据 → verifier 复核 → Markdown 报告。

输入：一次值守/巡检的各 Skill 输出（JSON，含 step id）。
输出：Markdown 报告 + 结论证据映射；verifier 驳回的条目标注"待复核"而非静默删除。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verifier import verify  # noqa: E402


def compose(rounds: list[dict], title: str = "机舱巡检报告") -> dict:
    """rounds: [{step_id, skill, output}]"""
    pool = {r["step_id"]: r["output"] for r in rounds}

    # 从各 Skill 输出提炼结论（每条必须挂证据）
    claims = []
    for r in rounds:
        sid, out = r["step_id"], r["output"]
        if r["skill"] == "engine-room-acoustic-sentinel" and out.get("level") != "normal":
            ev = out.get("evidence", [])
            top = ev[0] if ev else {}
            claims.append({
                "claim": f"声学检测 {out['level']} 级："
                         f"{top.get('label', top.get('feature', ''))} "
                         f"偏离基线 {top.get('delta', '')}",
                "evidence_refs": [f"{sid}:evidence"],
            })
        elif r["skill"] == "engine-room-visual-inspector":
            for rec in out.get("readings", []):
                if rec.get("value") not in (None, "unreadable"):
                    claims.append({
                        "claim": f"仪表读数 {rec['value']} {rec.get('unit', '')}"
                                 f"（{rec.get('method', '')}）",
                        "evidence_refs": [f"{sid}:readings"],
                    })
        elif r["skill"] == "radar-ppi-interpreter":
            for t in out.get("targets", [])[:3]:
                claims.append({
                    "claim": f"雷达目标 方位 {t['bearing_deg']}° 距离 {t['range_m']}m",
                    "evidence_refs": [f"{sid}:targets"],
                })
        elif r["skill"] == "sonar-acoustic-fingerprint":
            if out.get("label") != "unknown":
                ev = out.get("evidence", {})
                claims.append({
                    "claim": f"声纹判别 {out['label']}（置信度 {out.get('confidence')}，"
                             f"基频 {ev.get('f0_hz')}Hz，{ev.get('tonal_count')} 条谱线）",
                    "evidence_refs": [f"{sid}:evidence"],
                })
        elif r["skill"] == "route-deviation-watch":
            claims.append({
                "claim": f"航线状态 {out['level']}（最大横偏 {out.get('max_xte_m')}m，"
                         f"走廊半宽 {out.get('corridor_half_width_m')}m）",
                "evidence_refs": [f"{sid}:max_xte_m"],
            })

    v = verify(claims, pool)
    lines = [f"# {title}", "",
             f"- 证据步骤数：{len(rounds)}",
             f"- 结论数：{v['n_claims']}（通过 {v['n_accepted']} / 驳回 {v['n_rejected']}）",
             f"- verifier 结论：{v['verdict']}", "", "## 结论清单", ""]
    for a in v["accepted"]:
        lines.append(f"- [已核实] {a['claim']}")
    for r in v["rejected"]:
        lines.append(f"- [待复核] {r['claim']} —— 原因：{'；'.join(r['problems'])}")
    lines += ["", "## 证据明细", ""]
    for r in rounds:
        lines.append(f"### {r['step_id']}（{r['skill']}）")
        lines.append("```json")
        lines.append(json.dumps(r["output"], ensure_ascii=False, indent=1)[:800])
        lines.append("```")
        lines.append("")
    return {"report_md": "\n".join(lines), "conclusions": claims, "verifier": v}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help='JSON：{"title": "...", "rounds": [{step_id, skill, output}]}')
    args = ap.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if "rounds" not in data:
        print(json.dumps({"error": "需要 rounds 字段"}, ensure_ascii=False), file=sys.stderr)
        return 2
    out = compose(data["rounds"], data.get("title", "机舱巡检报告"))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"MEDIA:{Path(args.input).resolve()}")
    return 0 if out["verifier"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
