#!/usr/bin/env python3
"""雷达目标检测（经典 CV）：噪声底估计 → 阈值分割 → 连通域聚类 → 目标方位/距离。

抗虚警规则：簇内单元数 < min_cells 判为杂波丢弃——空海面场景必须零虚警。
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np


def detect(field: np.ndarray, thr_sigma: float, min_cells: int,
           az_bins: int, rng_bins: int, max_range_m: int) -> list[dict]:
    thr = float(field.mean()) + thr_sigma * float(field.std())
    mask = field > thr
    seen = np.zeros_like(mask, dtype=bool)
    targets = []
    for i, j in zip(*np.nonzero(mask)):
        if seen[i, j]:
            continue
        q = deque([(int(i), int(j))])
        seen[i, j] = True
        cells: list[tuple[int, int]] = []
        while q:
            y, x = q.popleft()
            cells.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                        and mask[ny, nx] and not seen[ny, nx]):
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(cells) < min_cells:
            continue
        ys = np.array([c[0] for c in cells], dtype=float)
        xs = np.array([c[1] for c in cells], dtype=float)
        peak = float(field[ys.astype(int), xs.astype(int)].max())
        targets.append({
            "bearing_deg": round(float(ys.mean()) * 360.0 / az_bins, 1),
            "range_m": round(float(xs.mean()) * max_range_m / rng_bins, 1),
            "cells": len(cells),
            "peak_snr": round(peak, 1),
            "confidence": round(min(0.99, peak / 25.0), 2),
        })
    targets.sort(key=lambda t: -t["confidence"])
    return targets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixture", help="PPI 回波场 .npy（方位×距离）")
    ap.add_argument("--az-bins", type=int, default=720)
    ap.add_argument("--rng-bins", type=int, default=400)
    ap.add_argument("--max-range-m", type=int, default=8000)
    ap.add_argument("--thr-sigma", type=float, default=8.0)
    ap.add_argument("--min-cells", type=int, default=4)
    args = ap.parse_args()

    field = np.load(args.fixture)
    targets = detect(field, args.thr_sigma, args.min_cells,
                     args.az_bins, args.rng_bins, args.max_range_m)
    print(json.dumps({
        "targets": targets,
        "n_targets": len(targets),
        "fixture": args.fixture,
        "params": {"thr_sigma": args.thr_sigma, "min_cells": args.min_cells},
    }, ensure_ascii=False, indent=2))
    print(f"MEDIA:{Path(args.fixture).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
