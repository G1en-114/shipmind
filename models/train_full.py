#!/usr/bin/env python3
"""全量 AE 训练 + 断点续训：每个 epoch 末存 checkpoint，中断后 --resume 接着跑。

与 models/train_ae.py 同一套配方（DCASE2020 官方：640 维 log-mel → 瓶颈 8 维 AE），
增加：全量数据、checkpoint、多机种循环、CPU 并行特征提取。

用法：
    python models/train_full.py --data-root /root/data/dcase2020 --machines pump,valve,fan \
        --epochs 30 --resume
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# 必须在 import numpy 之前设置：多进程 + 多线程 BLAS 会线程超额订阅
# （N worker × 每 worker 20 BLAS 线程 = 大量线程抢少量核心，load 可飙到 200+）
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_ae import (AutoEncoder, FRAMES, HOP, N_FFT, auc, collect,  # noqa: E402
                      feature_vectors, pauc, standardize)

CKPT_DIR = Path(__file__).resolve().parent / "ckpt"


def _feat_one(args):
    path, stats = args
    return feature_vectors(Path(path), stats)


def collect_parallel(files: list[Path], stats: dict | None, workers: int) -> np.ndarray:
    """多进程特征提取（大文件集时瓶颈在解码+FFT，208 核机器可秒级完成）。"""
    if workers <= 1 or len(files) < 8:
        return np.concatenate([feature_vectors(f, stats) for f in files])
    with ProcessPoolExecutor(max_workers=workers) as ex:
        parts = list(ex.map(_feat_one, [(str(f), stats) for f in files], chunksize=4))
    return np.concatenate(parts)


def train_one(machine_root: Path, epochs: int, batch: int, workers: int,
              ckpt: Path, resume: bool, log_every: int = 2) -> dict:
    train_dir = machine_root / "train"
    test_dir = machine_root / "test"
    files = sorted(train_dir.glob("*.wav"))
    n_test_n = len(sorted(test_dir.glob("normal_id_*.wav")))
    n_test_a = len(sorted(test_dir.glob("anomaly_id_*.wav")))
    print(f"[{machine_root.name}] train {len(files)} | test normal {n_test_n} anom {n_test_a}",
          flush=True)

    # 断点三件套：模型权重 ckpt / 训练进度 meta / 特征缓存 feat
    # （特征提取是最耗时的一步，必须缓存，否则每次 resume 都要重跑十几分钟）
    meta = ckpt.with_suffix(".meta.npz")
    feat_cache = ckpt.with_name(ckpt.stem + "_feat.npy")
    ae = AutoEncoder()
    start_ep, stats = 0, None

    if resume and ckpt.exists() and meta.exists():
        d, m = np.load(ckpt), np.load(meta)
        ae.W = [d[f"W{i}"] for i in range(len(ae.W))]
        ae.b = [d[f"b{i}"] for i in range(len(ae.b))]
        start_ep = int(m["epoch"]) + 1
        stats = {"mean": float(m["mean"]), "std": float(m["std"])}
        print(f"[{machine_root.name}] 续训：从 epoch {start_ep} 开始", flush=True)

    if resume and feat_cache.exists():
        x = np.load(feat_cache)
        print(f"[{machine_root.name}] 特征缓存命中 {x.shape}", flush=True)
    else:
        t0 = time.time()
        sample = collect_parallel(files[:64], None, workers)
        stats = {"mean": float(sample.mean()), "std": float(sample.std()) + 1e-6}
        x = collect_parallel(files, stats, workers)
        feat_cache.parent.mkdir(parents=True, exist_ok=True)
        np.save(feat_cache, x)
        print(f"[{machine_root.name}] 特征完成 {x.shape} 用时 {time.time()-t0:.0f}s（已缓存）",
              flush=True)

    if start_ep >= epochs:
        print(f"[{machine_root.name}] 已完成 {start_ep} epoch，跳过训练", flush=True)
    else:
        rng = np.random.default_rng(0)
        steps = max(len(x) // batch, 1)
        for ep in range(start_ep, epochs):
            order = rng.permutation(len(x))
            tot = 0.0
            for s in range(steps):
                idx = order[s * batch:(s + 1) * batch]
                if len(idx) < 8:
                    continue
                tot += ae.train_step(x[idx])
            if ep % log_every == 0 or ep == epochs - 1:
                print(f"[{machine_root.name}] epoch {ep:3d} loss {tot/steps:.5f}", flush=True)
            # 每个 epoch 末都存：权重 + 进度 + 标准化参数，中断后可精确续训
            ckpt.parent.mkdir(parents=True, exist_ok=True)
            ae.save(ckpt)
            np.savez(meta, epoch=ep, **stats)

    # 3) 全量评测
    x_n = collect_parallel(sorted(test_dir.glob("normal_id_*.wav")), stats, workers)
    x_a = collect_parallel(sorted(test_dir.glob("anomaly_id_*.wav")), stats, workers)
    s = np.concatenate([ae.score(x_n), ae.score(x_a)])
    y = np.concatenate([np.zeros(len(x_n)), np.ones(len(x_a))]).astype(int)
    mu = float(s[y == 0].mean())
    return {
        "machine": machine_root.name,
        "n_train_files": len(files), "n_test_normal": len(x_n), "n_test_anom": len(x_a),
        "auc_error": round(auc(y, s), 4),
        "auc_deviation": round(auc(y, np.abs(s - mu)), 4),
        "pauc_0.1_error": round(pauc(y, s), 4),
        "pauc_0.1_deviation": round(pauc(y, np.abs(s - mu)), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True, help="解压后的 DCASE 目录（含 pump/valve/fan）")
    ap.add_argument("--machines", default="pump,valve,fan")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--workers", type=int,
                    default=min(8, (os.cpu_count() or 8)),
                    help="特征提取进程数；BLAS 线程已在脚本内限为 2，避免线程超额订阅")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    results = []
    for m in args.machines.split(","):
        root = Path(args.data_root) / m.strip()
        if not root.exists():
            print(f"跳过 {m}（目录不存在）")
            continue
        r = train_one(root, args.epochs, args.batch, args.workers,
                      CKPT_DIR / f"ae_{m.strip()}.npz", args.resume)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)

    out = CKPT_DIR / "full_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("结果已写入", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
