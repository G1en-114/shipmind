#!/usr/bin/env python3
"""雷达目标检测：逐方位线 1D 距离向 CA-CFAR + 连通域聚类。

CA-CFAR 公式（Skolnik/Richards 教材公开方法论，自行实现）：
    阈值因子 α = N·(Pfa^(-1/N) − 1)，N 为训练单元数
    噪声估计 = (训练窗和 − 保护窗和) / 有效训练单元数
    门限 = 噪声估计 × α

相比全局 mean+8σ 单阈值：逐 beam 估计噪声底，可适应距离向的杂波起伏
（近程海杂波强、远程弱），且 Pfa 可控。全局阈值保留为降级路径。

抗虚警：簇内单元数 < min_cells 判为杂波丢弃——空海面场景必须零虚警。
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np


def _gauss_factor(pfa: float) -> float:
    """零均值高斯噪声的单侧 Pfa 门限因子 k：P(N(0,1) > k) = pfa。"""
    try:
        from scipy.special import erfinv
        return float(np.sqrt(2.0) * erfinv(1.0 - 2.0 * pfa))
    except Exception:
        return {1e-2: 2.326, 1e-3: 3.09, 1e-4: 3.719, 1e-5: 4.265}.get(pfa, 3.09)


def cfar_1d(line: np.ndarray, num_train: int, num_guard: int,
            pfa: float, noise_model: str = "gaussian") -> tuple[np.ndarray, np.ndarray]:
    """对单条距离向回波做 CA-CFAR。返回 (门限数组, 检测掩码)。

    两种噪声模型（关键区别，踩过的坑）：
      - gaussian（默认，匹配本仓 PPI 合成器的零均值高斯 I/Q 噪声）：
        噪声用训练窗 **RMS** 估计，门限 = k·RMS，其中 k 由高斯单侧 Pfa 决定。
        若误用教科书 α 公式（训练窗均值），零均值噪声的均值≈0 会让门限塌到 0，
        全场虚警。
      - exponential（真实雷达功率/包络数据）：门限 = α·mean，α = N(Pfa^(-1/N)−1)。
    """
    n = len(line)
    half = num_train + num_guard
    thresh = np.full(n, np.inf)
    k = _gauss_factor(pfa)
    alpha = num_train * (pfa ** (-1.0 / num_train) - 1.0)
    for i in range(n):
        lo, hi = i - half, i + half + 1
        if lo < 0 or hi > n:
            continue
        train_cells = np.concatenate([line[lo:i - num_guard],
                                      line[i + num_guard + 1:hi]])
        if train_cells.size == 0:
            continue
        if noise_model == "gaussian":
            noise = float(np.sqrt(np.mean(np.square(train_cells))))
            thresh[i] = noise * k
        else:
            noise = float(train_cells.mean())
            thresh[i] = noise * alpha
    return thresh, line > thresh


def detect(field: np.ndarray, num_train: int, num_guard: int, pfa: float,
           min_cells: int, az_bins: int, rng_bins: int, max_range_m: int,
           noise_model: str = "gaussian") -> list[dict]:
    """逐 beam CFAR → 跨 beam 连通域聚类（3 维邻域含相邻 beam 同距离）。"""
    mask = np.zeros_like(field, dtype=bool)
    for b in range(field.shape[0]):
        _, m = cfar_1d(field[b], num_train, num_guard, pfa, noise_model)
        mask[b] = m
    if not mask.any():
        return []

    seen = np.zeros_like(mask, dtype=bool)
    targets = []
    for i, j in zip(*np.nonzero(mask)):
        if seen[i, j]:
            continue
        q = deque([(int(i), int(j))])
        seen[i, j] = True
        cells = []
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
        # 置信度：峰值相对全场中位数（CFAR 已自适应，这里只做排序用）
        targets.append({
            "bearing_deg": round(float(ys.mean()) * 360.0 / az_bins, 1),
            "range_m": round(float(xs.mean()) * max_range_m / rng_bins, 1),
            "cells": len(cells),
            "peak": round(peak, 1),
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
    ap.add_argument("--num-train", type=int, default=24, help="CFAR 训练单元数（单侧）")
    ap.add_argument("--num-guard", type=int, default=4, help="CFAR 保护单元数（单侧）")
    ap.add_argument("--pfa", type=float, default=1e-4, help="设计虚警率")
    ap.add_argument("--min-cells", type=int, default=6)
    ap.add_argument("--mode", choices=["cfar", "global"], default="cfar",
                    help="cfar=逐 beam CA-CFAR；global=旧版全局阈值（降级路径）")
    ap.add_argument("--noise-model", choices=["gaussian", "exponential"],
                    default="gaussian",
                    help="gaussian=零均值 I/Q 噪声（本仓合成器，RMS 估计）；"
                         "exponential=雷达功率/包络数据（均值估计+教科书 α）")
    args = ap.parse_args()

    field = np.load(args.fixture)
    if args.mode == "global":
        mask = field > (field.mean() + 8.0 * field.std())
        targets = []
        seen = np.zeros_like(mask, dtype=bool)
        for i, j in zip(*np.nonzero(mask)):
            if seen[i, j]:
                continue
            q = deque([(int(i), int(j))])
            seen[i, j] = True
            cells = []
            while q:
                y, x = q.popleft()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if len(cells) < args.min_cells:
                continue
            ys = np.array([c[0] for c in cells], dtype=float)
            xs = np.array([c[1] for c in cells], dtype=float)
            peak = float(field[ys.astype(int), xs.astype(int)].max())
            targets.append({"bearing_deg": round(float(ys.mean()) * 360 / args.az_bins, 1),
                            "range_m": round(float(xs.mean()) * args.max_range_m / args.rng_bins, 1),
                            "cells": len(cells), "peak_snr": round(peak, 1),
                            "confidence": round(min(0.99, peak / 25), 2)})
        targets.sort(key=lambda t: -t["confidence"])
    else:
        targets = detect(field, args.num_train, args.num_guard, args.pfa,
                         args.min_cells, args.az_bins, args.rng_bins,
                         args.max_range_m, args.noise_model)

    print(json.dumps({
        "targets": targets, "n_targets": len(targets), "fixture": args.fixture,
        "params": {"mode": args.mode, "noise_model": args.noise_model,
                   "num_train": args.num_train, "num_guard": args.num_guard,
                   "pfa": args.pfa, "min_cells": args.min_cells},
    }, ensure_ascii=False, indent=2))
    print(f"MEDIA:{Path(args.fixture).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
