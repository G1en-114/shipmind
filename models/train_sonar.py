#!/usr/bin/env python3
"""声纹 ML 轨：DeepShip 四类 → 特征（LOFAR/DEMON，复用规则轨）→ 逻辑回归分类器。

设计原则：
  1. 特征与规则轨**同源**（tonal_count / f0 / 谐波阶数 / DEMON 轴频 / 频段占比…），
     因此 ML 轨与规则轨可直接对照——"同一组特征，学习式组合 vs 人工阈值"。
  2. 划分按**文件**（recording-wise）而非片段——DeepShip 默认按段划分存在同船
     样本跨 train/test 泄漏（ZhuPengsen 方法学仓库已证实），按文件划分才诚实。
  3. 纯 numpy 实现，CPU 可训。

用法：
    python train_sonar.py --data-root D:/datasets/deepship --segments 20
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402
from scipy.io import wavfile  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "skills-src/sonar-acoustic-fingerprint/scripts"))
import sonar_fingerprint as S  # noqa: E402

FEATURES = ["tonal_count", "f0_hz", "n_harm", "demon_shaft", "mid_ratio",
            "rms", "centroid", "zcr", "hi_ratio", "ultra_ratio",
            "flatness", "lo_ratio"]
CLASSES = ["Cargo", "Passengership", "Tanker", "Tug"]


def read_wav(path: Path):
    sr, data = wavfile.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if data.dtype != np.float32:
        data = data.astype(np.float32)
        if np.abs(data).max() > 1.5:  # int16 之类未归一化
            data = data / 32768.0
    return data, sr


def seg_features(args):
    path, start, dur = args
    data, sr = read_wav(Path(path))
    seg = data[int(start * sr): int((start + dur) * sr)]
    if len(seg) < sr * 5:
        return None
    freqs, spec = S.lofar_spectrum(seg, sr)
    peaks, _ = S.find_tonals(freqs, spec)
    df = float(freqs[1] - freqs[0])
    n_harm, f0, matched = S.harmonic_series(peaks, df)
    shaft = S.demon_shaft(seg, sr)
    total = float(spec.sum()) + 1e-12
    mid = (freqs >= 200) & (freqs < 2000)
    hi = (freqs >= 2000) & (freqs < 8000)
    ultra = (freqs >= 8000) & (freqs < 16000)
    lo = (freqs >= 20) & (freqs < 200)
    flatness = float(np.exp(np.mean(np.log(spec + 1e-12))) / (np.mean(spec) + 1e-12))
    rms = float(np.sqrt(np.mean(seg ** 2)))
    centroid = float(np.sum(freqs * spec) / total)
    zcr = float(np.mean(np.abs(np.diff(np.sign(seg)))))
    return [len(peaks), f0 or 0.0, len(matched), shaft or 0.0,
            float(spec[mid].sum()) / total, rms, centroid, zcr,
            float(spec[hi].sum()) / total, float(spec[ultra].sum()) / total,
            flatness, float(spec[lo].sum()) / total]


class SoftmaxRegression:
    """多项逻辑回归（numpy，L2 正则，标准缩放由外部完成）。"""

    def __init__(self, n_features: int, n_classes: int, lr: float = 0.5,
                 epochs: int = 400, l2: float = 1e-3):
        self.W = np.zeros((n_features, n_classes))
        self.b = np.zeros(n_classes)
        self.lr, self.epochs, self.l2 = lr, epochs, l2

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        n, d = X.shape
        Y = np.zeros((n, self.W.shape[1]))
        Y[np.arange(n), y] = 1.0
        for _ in range(self.epochs):
            z = X @ self.W + self.b
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            p /= p.sum(axis=1, keepdims=True)
            grad = (p - Y) / n
            self.W -= self.lr * (X.T @ grad + self.l2 * self.W)
            self.b -= self.lr * grad.sum(axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(X @ self.W + self.b, axis=1)


def rule_predict(feat: list[float]) -> int:
    """规则轨（sonar_fingerprint.classify_rule）输出 → DeepShip 四类的映射。

    规则轨原输出为 large_cargo_or_tanker / medium_vessel / tug_or_fishing /
    unknown 四类，与 DeepShip 的四类船型不是同一套标签体系，此处按
    "大型慢速→Tanker、中型→Passengership、小功率宽带→Tug、兜底→Cargo" 映射。
    **该对照只作量级参考，标签体系不对等是已知局限**，文档中如实标注。
    """
    tonal, f0, n_harm, mid_ratio = feat[0], feat[1], feat[2], feat[4]
    if n_harm >= 3 and 0 < f0 < 100:
        return CLASSES.index("Tanker")
    if n_harm >= 2 and 100 <= f0 < 400:
        return CLASSES.index("Passengership")
    if tonal == 0 and mid_ratio > 0.4:
        return CLASSES.index("Tug")
    return CLASSES.index("Cargo")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--segments", type=int, default=20, help="每个文件切几段")
    ap.add_argument("--seg-dur", type=float, default=10.0)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    root = Path(args.data_root)
    jobs, labels, files_of = [], [], []
    for ci, cls in enumerate(CLASSES):
        d = root / cls
        if not d.exists():
            continue
        for f in sorted(d.glob("*.wav")):
            data, sr = read_wav(f)
            dur = len(data) / sr
            for k in range(args.segments):
                start = (dur - args.seg_dur) * k / max(args.segments - 1, 1)
                if start < 0:
                    start = 0
                jobs.append((str(f), start, args.seg_dur))
                labels.append(ci)
                files_of.append(f.name)

    print(f"总片段 {len(jobs)}，提取特征…", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        feats = list(ex.map(seg_features, jobs))
    keep = [i for i, f in enumerate(feats) if f is not None]
    X = np.array([feats[i] for i in keep], dtype=np.float64)
    y = np.array([labels[i] for i in keep])
    fnames = [files_of[i] for i in keep]
    print(f"有效片段 {len(X)}，用时 {time.time()-t0:.0f}s", flush=True)

    # 按文件划分（防同船泄漏）
    uniq = sorted(set(fnames))
    rng = np.random.default_rng(0)
    rng.shuffle(uniq)
    n_test_file = max(1, len(uniq) // 3)
    test_files = set(uniq[:n_test_file])
    te = np.array([f in test_files for f in fnames])
    tr = ~te
    print(f"文件级划分：train {sum(tr)} 段 / test {sum(te)} 段"
          f"（测试文件 {len(test_files)}/{len(uniq)}）", flush=True)

    mu, sd = X[tr].mean(axis=0), X[tr].std(axis=0) + 1e-9
    Xs = (X - mu) / sd

    clf = SoftmaxRegression(X.shape[1], len(CLASSES))
    clf.fit(Xs[tr], y[tr])
    pred = clf.predict(Xs[te])

    acc = float((pred == y[te]).mean())
    rule_pred = np.array([rule_predict(f) for f in X[te]])
    rule_acc = float((rule_pred == y[te]).mean())

    cm = np.zeros((len(CLASSES), len(CLASSES)), dtype=int)
    for t, p in zip(y[te], pred):
        cm[t, p] += 1

    # 保存模型（权重 + 标准化参数 + 特征顺序），供 sonar skill 的 --mode ml 使用
    model_path = Path(__file__).resolve().parent / "sonar_clf.npz"
    np.savez(model_path, W=clf.W, b=clf.b, mu=mu, sd=sd,
             classes=np.array(CLASSES))
    print(f"模型已保存 {model_path}", flush=True)

    out = {
        "model": str(model_path),
        "n_train_segments": int(tr.sum()), "n_test_segments": int(te.sum()),
        "n_files_total": len(uniq), "n_test_files": len(test_files),
        "ml_accuracy": round(acc, 4), "rule_accuracy": round(rule_acc, 4),
        "confusion_matrix": {"classes": CLASSES, "matrix": cm.tolist()},
        "split_note": "按文件划分（recording-wise），避免 DeepShip 同船样本泄漏",
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
