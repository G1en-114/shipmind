#!/usr/bin/env python3
"""启发式轨全量评测：与 train_full.py 同一批 test 文件、同一套特征（acoustic_sentinel.py），
算 AUC 做双轨对等比较。用法：
    python3 models/eval_heuristic_full.py --data-root ~/data/dcase2020 --machines pump,valve,fan
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "skills-src/engine-room-acoustic-sentinel/scripts"))
import acoustic_sentinel as A  # noqa: E402


def _score_one(args):
    path, stats = args
    data, sr = A.load_audio(Path(path))
    feats = A.extract_features(data, sr)
    zs = [(feats[k] - stats[k]["mean"])
          / max(stats[k]["std"], 0.05 * abs(stats[k]["mean"]), 1e-9)
          for k in feats]
    return float(np.sqrt(np.mean(np.square(zs))))


def feats_of(path):
    data, sr = A.load_audio(Path(path))
    return A.extract_features(data, sr)


def auc(y, s) -> float:
    o = np.argsort(s)
    r = np.empty_like(o, dtype=float)
    r[o] = np.arange(1, len(s) + 1)
    p, n = y.sum(), len(y) - y.sum()
    return float((r[y == 1].sum() - p * (p + 1) / 2) / (p * n))


def run(machine_root: Path, workers: int) -> dict:
    train_dir, test_dir = machine_root / "train", machine_root / "test"
    train_files = sorted(train_dir.glob("*.wav"))
    sample = train_files[:: max(1, len(train_files) // 200)][:200]  # 200 条估基线

    with ProcessPoolExecutor(max_workers=workers) as ex:
        base_feats = list(ex.map(feats_of, sample))
    stats = {k: {"mean": float(np.mean([b[k] for b in base_feats])),
                 "std": float(np.std([b[k] for b in base_feats], ddof=1))}
             for k in base_feats[0]}

    n_files = sorted(test_dir.glob("normal_id_*.wav"))
    a_files = sorted(test_dir.glob("anomaly_id_*.wav"))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        sn = list(ex.map(_score_one, [(str(f), stats) for f in n_files]))
        sa = list(ex.map(_score_one, [(str(f), stats) for f in a_files]))

    y = np.concatenate([np.zeros(len(sn)), np.ones(len(sa))]).astype(int)
    s = np.concatenate([sn, sa])
    return {
        "machine": machine_root.name,
        "n_baseline_files": len(sample),
        "n_test_normal": len(n_files), "n_test_anom": len(a_files),
        "auc_heuristic": round(auc(y, s), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--machines", default="pump,valve,fan")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    results = []
    for m in args.machines.split(","):
        root = Path(args.data_root) / m.strip()
        if not root.exists():
            continue
        r = run(root, args.workers)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)

    out = Path(__file__).resolve().parent / "ckpt" / "heuristic_full.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("结果已写入", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
