#!/usr/bin/env python3
"""COLREGs 会遇态势分类（确定性，零容差评测）。

区间采用 Zhao & Roh (2019, Ocean Engineering 191:106436) 对 COLREGs 区域的
通行工程划分：对遇 |θ|≤5° 且航向近似相反；追越 |θ|>112.5°；交叉 5°<|θ|≤112.5°，
右舷有他船者让路。本函数只做态势判定，不生成操纵建议（那是决策层的事）。

用法：
    python classify_encounter.py --own-heading 010 --target-bearing 030 \
        --target-heading 340 --cpa-m 800 --tcpa-s 420
    python classify_encounter.py --selftest
"""
from __future__ import annotations

import argparse
import json

# 会遇判定门限
HEAD_ON_MAX = 5.0        # 对遇：相对方位角 ≤5°
OVERTAKE_MIN = 112.5     # 追越：|θ| > 112.5°
HEADING_OPPOSITE = 170.0  # 对遇还需两船航向近似相反（差值 ≥170°）
CPA_ALARM_M = 1852.0     # CPA 小于 1 海里视为构成碰撞危险
TCPA_ALARM_S = 3600.0    # TCPA 小于 1 小时


def heading_diff(a: float, b: float) -> float:
    """两航向差，归一到 [0, 180]。"""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def classify(own_heading: float, target_bearing: float, target_heading: float,
             cpa_m: float | None = None, tcpa_s: float | None = None) -> dict:
    """target_bearing：他船相对本船的真方位（0-360，本船船首为 0 的相对方位）。"""
    rel = (target_bearing - own_heading) % 360.0
    if rel > 180:
        rel -= 360.0
    abs_rel = abs(rel)
    hd = heading_diff(own_heading, target_heading)

    risk = None
    if cpa_m is not None and tcpa_s is not None:
        risk = (cpa_m < CPA_ALARM_M) and (tcpa_s < TCPA_ALARM_S)

    if abs_rel <= HEAD_ON_MAX and hd >= HEADING_OPPOSITE:
        situation = "HEAD_ON"
        duty = "BOTH_ALTER_STARBOARD"
        rule = "Rule 14"
    elif abs_rel > OVERTAKE_MIN:
        situation = "OVERTAKING"
        # 追越船让路；被追越船在接近到足以构成危险前保持航向航速
        duty = "GIVE_WAY_IF_OVERTAKING"
        rule = "Rule 13"
    else:
        situation = "CROSSING"
        rule = "Rule 15"
        duty = "GIVE_WAY" if rel > 0 else "STAND_ON"

    return {
        "situation": situation,
        "duty": duty,
        "rule": rule,
        "relative_bearing_deg": round(rel, 1),
        "heading_diff_deg": round(hd, 1),
        "collision_risk": risk,
        "note": "无危险" if risk is False else
                ("构成碰撞危险" if risk else "未提供 CPA/TCPA"),
    }


SELFTEST = [
    # (参数..., 期望 situation, 期望 duty)
    (10, 15, 190, "HEAD_ON", "BOTH_ALTER_STARBOARD"),      # 对遇：同向反向
    (10, 40, 190, "CROSSING", "GIVE_WAY"),                 # 右舷 30° 交叉
    (10, 340, 190, "CROSSING", "STAND_ON"),                # 左舷 30° 交叉
    (10, 200, 20, "OVERTAKING", "GIVE_WAY_IF_OVERTAKING"), # 追越
    (10, 60, 40, "CROSSING", "GIVE_WAY"),                  # 右舷大角度交叉
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--own-heading", type=float)
    ap.add_argument("--target-bearing", type=float)
    ap.add_argument("--target-heading", type=float)
    ap.add_argument("--cpa-m", type=float)
    ap.add_argument("--tcpa-s", type=float)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        n_pass = 0
        for oh, tb, th, exp_s, exp_d in SELFTEST:
            r = classify(oh, tb, th, 1000.0, 600.0)
            ok = r["situation"] == exp_s and r["duty"] == exp_d
            n_pass += ok
            print(f"[{'PASS' if ok else 'FAIL'}] own={oh} brg={tb} hdg={th} "
                  f"-> {r['situation']}/{r['duty']} (期望 {exp_s}/{exp_d})")
        print(f"{n_pass}/{len(SELFTEST)} passed")
        return 0 if n_pass == len(SELFTEST) else 1

    if None in (args.own_heading, args.target_bearing, args.target_heading):
        ap.error("需要 --own-heading --target-bearing --target-heading")
    print(json.dumps(classify(args.own_heading, args.target_bearing,
                              args.target_heading, args.cpa_m, args.tcpa_s),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import json
    raise SystemExit(main())
