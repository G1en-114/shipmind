#!/usr/bin/env python3
"""NMEA 0183 模拟器：沿给定航线生成 RMC/GGA 句，支持固定横向漂移（演示用仿真源）。

示例：
  python sensors/nmea_simulator.py --route evals/fixtures/nmea/route.json \
      --drift-m 800 --out evals/fixtures/nmea/watch_drift.nmea
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
from pathlib import Path

R_EARTH = 6371008.8


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    d = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * R_EARTH * math.asin(math.sqrt(d))


def move_toward(a, b, dist_m):
    """从 a 向 b 前进 dist_m；到达 b 时返回剩余距离 0。"""
    total = haversine_m(a, b)
    if total <= dist_m:
        return b, dist_m - total
    f = dist_m / total
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), 0.0


def bearing_deg(a, b) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return math.degrees(math.atan2(x, y)) % 360


def drift_offset(pos, brg_deg, drift_m):
    """向航线右舷（航向+90°）平移 drift_m。"""
    lat = pos[1]
    brg = math.radians(brg_deg + 90)
    dlat = drift_m * math.cos(brg) / 111320.0
    dlon = drift_m * math.sin(brg) / (111320.0 * math.cos(math.radians(lat)))
    return (pos[0] + dlon, lat + dlat)


def checksum(body: str) -> str:
    c = 0
    for ch in body:
        c ^= ord(ch)
    return f"{c:02X}"


def fmt_lat(lat: float):
    deg = int(abs(lat))
    minutes = (abs(lat) - deg) * 60
    return f"{deg:02d}{minutes:07.4f}", ("N" if lat >= 0 else "S")


def fmt_lon(lon: float):
    deg = int(abs(lon))
    minutes = (abs(lon) - deg) * 60
    return f"{deg:03d}{minutes:07.4f}", ("E" if lon >= 0 else "W")


def sentences(pos, speed_kn: float, cog: float, ts: datetime.datetime):
    t = ts.strftime("%H%M%S.%f")[:-4]
    d = ts.strftime("%d%m%y")
    latstr, ns = fmt_lat(pos[1])
    lonstr, ew = fmt_lon(pos[0])
    rmc = (f"GNRMC,{t},A,{latstr},{ns},{lonstr},{ew},"
           f"{speed_kn:.1f},{cog:.1f},{d},,,A")
    gga = f"GNGGA,{t},{latstr},{ns},{lonstr},{ew},1,08,0.9,12.0,M,0.0,M,,"
    return f"${rmc}*{checksum(rmc)}", f"${gga}*{checksum(gga)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", required=True,
                    help='航线 json：{"waypoints": [[lon,lat],...], "corridor_half_width_m": 1852}')
    ap.add_argument("--speed-kn", type=float, default=12.0)
    ap.add_argument("--interval-s", type=float, default=10.0)
    ap.add_argument("--drift-m", type=float, default=0.0, help="向航线右侧的固定横向漂移")
    ap.add_argument("--t0", default="2026-09-21T00:00:00")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    route = json.loads(Path(args.route).read_text(encoding="utf-8"))["waypoints"]
    step = args.speed_kn * 0.5144 * args.interval_s
    ts = datetime.datetime.fromisoformat(args.t0)
    pos = tuple(route[0])
    lines: list[str] = []

    for i in range(len(route) - 1):
        b = tuple(route[i + 1])
        brg = bearing_deg(pos, b)
        guard = 0
        while pos != b:
            pos, _ = move_toward(pos, b, step)
            out = drift_offset(pos, brg, args.drift_m) if args.drift_m else pos
            rmc, gga = sentences(out, args.speed_kn, brg, ts)
            lines += [rmc, gga]
            ts += datetime.timedelta(seconds=args.interval_s)
            guard += 1
            if guard > 100000:
                raise RuntimeError("航段未收敛，检查 waypoint 间距与速度设置")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out_path), "fixes": len(lines) // 2,
                      "drift_m": args.drift_m}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
