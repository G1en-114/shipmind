#!/usr/bin/env python3
"""雷达 PPI 合成器：极坐标（方位×距离）回波场渲染——目标高斯团 + 海杂波 + 高斯噪声。

合成即数据源：演示与评测全程可控，输出 .npy + 真值 json。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True,
                    help='目标 json：[{"bearing_deg":45,"range_m":3000,"snr":20},...]')
    ap.add_argument("--az-bins", type=int, default=720)
    ap.add_argument("--rng-bins", type=int, default=400)
    ap.add_argument("--max-range-m", type=int, default=8000)
    ap.add_argument("--clutter", type=float, default=0.8, help="近程海杂波指数分布均值")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True, help="输出基名（生成 <out>.npy 与 <out>.truth.json）")
    args = ap.parse_args()

    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    rng = np.random.default_rng(args.seed)
    az = np.arange(args.az_bins) * 360.0 / args.az_bins
    r = np.arange(args.rng_bins) * args.max_range_m / args.rng_bins
    ra, rr = np.meshgrid(az, r, indexing="ij")

    field = rng.normal(0.0, 1.0, ra.shape)
    near = rr < args.max_range_m * 0.3
    field = field + np.where(near, rng.exponential(args.clutter, ra.shape), 0.0)

    for t in targets:
        amp = float(t.get("snr", 20.0))
        d_az = ((ra - t["bearing_deg"] + 180) % 360) - 180
        blob = amp * np.exp(
            -(d_az ** 2 / (2 * 2.5 ** 2)
              + (rr - t["range_m"]) ** 2 / (2 * (0.01 * args.max_range_m) ** 2)))
        field += blob

    out_base = Path(args.out)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(out_base) + ".npy", field.astype(np.float32))
    Path(str(out_base) + ".truth.json").write_text(json.dumps(
        {"targets": targets, "az_bins": args.az_bins, "rng_bins": args.rng_bins,
         "max_range_m": args.max_range_m, "seed": args.seed},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out_base) + ".npy", "n_targets": len(targets)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
