#!/usr/bin/env python3
"""航线偏离哨兵：NMEA RMC 轨迹 × waypoint 走廊 → XTE 越限分级，可选 CPA/TCPA。

确定性模块：给定输入必须得给定输出（评测零容差）。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

R_EARTH = 6371008.8


def parse_rmc(path: str | Path) -> list[tuple[float, float]]:
    """解析 RMC 有效定位（status=A），返回 [(lon, lat), ...]。

    句型判取首字段（GNRMC/GPRMC 均可），不能用 ",RMC," 子串匹配——
    talker 前缀里 RMC 前没有逗号。
    """
    fixes = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("$"):
            continue
        fields = line[1:].split("*")[0].split(",")
        if len(fields) < 12 or not fields[0].endswith("RMC") or fields[2] != "A":
            continue
        if len(fields[3]) < 4 or len(fields[5]) < 5:
            continue
        try:
            lat = int(fields[3][:2]) + float(fields[3][2:]) / 60.0
            lon = int(fields[5][:3]) + float(fields[5][3:]) / 60.0
        except ValueError:
            continue
        if fields[4] == "S":
            lat = -lat
        if fields[6] == "W":
            lon = -lon
        fixes.append((lon, lat))
    return fixes


def haversine_m(a, b) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    d = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * R_EARTH * math.asin(math.sqrt(d))


def bearing_deg(a, b) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return math.degrees(math.atan2(x, y))


def cross_track_m(p, a, b) -> float:
    """球面横向偏移（米，带符号：右舷为正）。"""
    d13 = haversine_m(a, p) / R_EARTH
    if d13 == 0:
        return 0.0
    t13 = math.radians(bearing_deg(a, p))
    t12 = math.radians(bearing_deg(a, b))
    return math.asin(math.sin(d13) * math.sin(t13 - t12)) * R_EARTH


def level_for(max_xte: float, corridor: float) -> str:
    if max_xte < 0.5 * corridor:
        return "normal"
    if max_xte < corridor:
        return "watch"
    return "alarm"


def cpa_tcpa(own, target, interval_s: float) -> dict:
    """直线运动模型 CPA/TCPA：各自首尾定位求速度向量，局部平面求解。"""
    lat0 = own[len(own) // 2][1]
    kx = 111320.0 * math.cos(math.radians(lat0))
    ky = 111320.0

    def to_xy(track):
        p0, p1 = track[0], track[-1]
        n = max(len(track) - 1, 1)
        x0, y0 = p0[0] * kx, p0[1] * ky
        x1, y1 = p1[0] * kx, p1[1] * ky
        return (x0, y0), ((x1 - x0) / n, (y1 - y0) / n)

    (ox, oy), (ovx, ovy) = to_xy(own)
    (tx, ty), (tvx, tvy) = to_xy(target)
    rx, ry = tx - ox, ty - oy
    vx, vy = tvx - ovx, tvy - ovy
    vv = vx * vx + vy * vy
    t = -(rx * vx + ry * vy) / vv if vv > 0 else 0.0
    cpa = math.hypot(rx + t * vx, ry + t * vy)
    return {
        "cpa_m": round(cpa, 1),
        "tcpa_s": round(t * interval_s, 1),
        "tcpa_note": "approaching" if t > 0 else "receding",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("nmea", help="本船 NMEA 轨迹（RMC/GGA）")
    ap.add_argument("--route", required=True,
                    help='航线 json：{"waypoints": [[lon,lat],...], "corridor_half_width_m": 1852}')
    ap.add_argument("--target", help="目标船 NMEA 轨迹（可选，输出 CPA/TCPA）")
    ap.add_argument("--interval-s", type=float, default=10.0,
                    help="轨迹定位间隔秒数（用于 TCPA 换算）")
    args = ap.parse_args()

    fixes = parse_rmc(args.nmea)
    if len(fixes) < 3:
        print(json.dumps({"error": "有效 RMC 定位不足 3 个", "level": "rejected"},
                         ensure_ascii=False), file=sys.stderr)
        return 2

    route = json.loads(Path(args.route).read_text(encoding="utf-8"))
    wps = [tuple(w) for w in route["waypoints"]]
    corridor = float(route.get("corridor_half_width_m", 1852))
    if corridor <= 0 or len(wps) < 2:
        print(json.dumps({"error": "航线定义无效", "level": "rejected"},
                         ensure_ascii=False), file=sys.stderr)
        return 2

    max_xte, worst = 0.0, None
    for p in fixes:
        xte = min(abs(cross_track_m(p, wps[i], wps[i + 1]))
                  for i in range(len(wps) - 1))
        if xte > max_xte:
            max_xte, worst = xte, p

    out = {
        "level": level_for(max_xte, corridor),
        "max_xte_m": round(max_xte, 1),
        "corridor_half_width_m": corridor,
        "n_fixes": len(fixes),
        "worst_fix": list(worst) if worst else None,
    }
    if args.target:
        tgt = parse_rmc(args.target)
        if len(tgt) >= 2:
            out.update(cpa_tcpa(fixes, tgt, args.interval_s))

    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"MEDIA:{Path(args.nmea).resolve()}")
    return 0 if out["level"] in ("normal", "watch") else 1


if __name__ == "__main__":
    raise SystemExit(main())
