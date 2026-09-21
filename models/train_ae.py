#!/usr/bin/env python3
"""机舱声学 ML 轨：自编码器（DCASE2020 Task2 官方配方，numpy 重实现）。

配方（已核实，见 docs/REFERENCES.md）：
  log-mel n_mels=128 × frames=5 → 640 维输入向量
  AE 结构 128-128-128-128-8-128-128-128-128（BatchNorm+ReLU）
  MSE 重构误差 → 异常评分；AUC + pAUC(max_fpr=0.1)

用法：
    python scripts/train_ae.py --normal-dir <正常样本目录> --epochs 100
    python scripts/train_ae.py --score --ckpt <模型.npz> --dir <待测目录>

数据源可换：MIMII pump/valve（D3 用，免申请）、ShipsEar/DeepShip（D7 船纹轨）。
"""
from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

import numpy as np

N_MELS, FRAMES, N_FFT, HOP = 128, 5, 1024, 512
DIM = N_MELS * FRAMES  # 640
HIDDEN = [128, 128, 128, 128, 8, 128, 128, 128, 128]


def load_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        ch, sw, sr = wf.getnchannels(), wf.getsampwidth(), wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    if sw == 2:
        d = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
    elif sw == 4:
        d = np.frombuffer(raw, "<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError("仅支持 16/32bit PCM")
    if ch > 1:
        d = d.reshape(-1, ch).mean(axis=1)
    return d, sr


def logmel(sig: np.ndarray, sr: int) -> np.ndarray:
    """log-mel 特征 [T, n_mels]。纯 numpy 梅尔滤波器组。"""
    n_frames = max((len(sig) - N_FFT) // HOP, 1)
    win = np.hanning(N_FFT)
    fmin, fmax = 20.0, sr / 2.0
    fft_freqs = np.fft.rfftfreq(N_FFT, 1.0 / sr)
    mel_lo = 2595.0 * np.log10(1 + fmin / 700.0)
    mel_hi = 2595.0 * np.log10(1 + fmax / 700.0)
    mels = np.linspace(mel_lo, mel_hi, N_MELS + 2)
    hz = 700.0 * (10 ** (mels / 2595.0) - 1.0)
    fb = np.zeros((N_MELS, len(fft_freqs)))
    for m in range(N_MELS):
        lo, mid, hi = hz[m], hz[m + 1], hz[m + 2]
        up = (fft_freqs - lo) / max(mid - lo, 1e-9)
        down = (hi - fft_freqs) / max(hi - mid, 1e-9)
        fb[m] = np.clip(np.minimum(up, down), 0, 1)
    frames = np.stack([sig[i * HOP: i * HOP + N_FFT] * win
                       for i in range(n_frames)])
    spec = np.abs(np.fft.rfft(frames, axis=1)) ** 2  # [T, n_fft/2+1]
    mel = frames @ fb.T if False else spec @ fb.T  # [T, n_mels]
    return np.log(mel + 1e-6).astype(np.float32)


# 全局特征标准化参数（训练时从 normal 集估计，评分/微调时复用）。
# log-mel 未归一化时输入范围约 [-14, 0]，直接训会 NaN。
MU_PATH = Path(__file__).resolve().parents[1] / "models" / "logmel_stats.npz"


def standardize(lm: np.ndarray, stats: dict | None = None) -> tuple[np.ndarray, dict]:
    if stats is None:
        stats = {"mean": float(lm.mean()), "std": float(lm.std()) + 1e-6}
    return (lm - stats["mean"]) / stats["std"], stats


def feature_vectors(path: Path, stats: dict | None = None) -> np.ndarray:
    sig, sr = load_wav(path)
    lm = logmel(sig, sr)
    lm, used = standardize(lm, stats)
    vecs = []
    for t in range(lm.shape[0] - FRAMES + 1):
        vecs.append(lm[t:t + FRAMES].reshape(-1))
    if not vecs:
        return np.zeros((0, DIM), dtype=np.float32)
    return np.stack(vecs)


class AutoEncoder:
    """稠密 AE，BatchNorm 简化为 LayerNorm-free 直连 + ReLU；瓶颈 8 维。"""

    def __init__(self, dim: int = DIM):
        rng = np.random.default_rng(0)
        # 层尺寸：输入 → 4×128 → 瓶颈 8 → 4×128 → 输出（与输入同维）
        self.dims = [dim, 128, 128, 128, 128, 8, 128, 128, 128, 128, dim]
        assert len(self.dims) == len(HIDDEN) + 2, "HIDDEN 必须恰好是中间 9 层"
        self.W, self.b = [], []
        for i in range(len(self.dims) - 1):
            fan_in = self.dims[i]
            self.W.append(rng.standard_normal((fan_in, self.dims[i + 1])).astype(np.float32)
                          * math.sqrt(2.0 / fan_in))
            self.b.append(np.zeros(self.dims[i + 1], dtype=np.float32))

    def forward(self, x: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
        acts, a = [x], x
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = a @ W + b
            a = z if i == len(self.W) - 1 else np.maximum(z, 0)  # 输出层线性
            acts.append(a)
        return acts[-1], acts

    def train_step(self, x: np.ndarray, lr: float = 3e-4) -> float:
        x = np.clip(x, -10.0, 10.0)  # 防标准化后极端值引爆前向
        _, acts = self.forward(x)
        pred = acts[-1]
        delta = 2.0 * (pred - x) / x.shape[0]
        grads_W = [None] * len(self.W)
        grads_b = [None] * len(self.b)
        for i in reversed(range(len(self.W))):
            a_prev = acts[i]
            grads_W[i] = a_prev.T @ delta
            grads_b[i] = delta.sum(axis=0)
            if i > 0:
                delta = (delta @ self.W[i].T) * (acts[i] > 0)  # ReLU 导数
            g = np.concatenate([grads_W[i].ravel(), grads_b[i]])
            norm = np.linalg.norm(g) + 1e-8
            if norm > 5.0:  # 全局梯度裁剪：numpy 手写反传无自适应，必须防爆
                grads_W[i] *= 5.0 / norm
                grads_b[i] *= 5.0 / norm
        for i in range(len(self.W)):
            self.W[i] -= lr * grads_W[i]
            self.b[i] -= lr * grads_b[i]
        return float(np.mean((pred - x) ** 2))

    def score(self, x: np.ndarray) -> np.ndarray:
        pred, _ = self.forward(x)
        return np.mean((pred - x) ** 2, axis=1)

    def save(self, path: Path) -> None:
        np.savez(path, **{f"W{i}": w for i, w in enumerate(self.W)},
                 **{f"b{i}": b for i, b in enumerate(self.b)})

    @classmethod
    def load(cls, path: Path) -> "AutoEncoder":
        ae = cls()
        d = np.load(path)
        ae.W = [d[f"W{i}"] for i in range(len(ae.W))]
        ae.b = [d[f"b{i}"] for i in range(len(ae.b))]
        return ae


def collect(wav_dir: Path, stats: dict | None = None) -> np.ndarray:
    files = sorted(wav_dir.glob("*.wav"))
    if not files:
        raise ValueError(f"{wav_dir} 无 wav 文件")
    return np.concatenate([feature_vectors(f, stats) for f in files])


def auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    order = np.argsort(y_score)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(y_score) + 1)
    pos = y_true.sum()
    neg = len(y_true) - pos
    return float((ranks[y_true == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def pauc(y_true: np.ndarray, y_score: np.ndarray, max_fpr: float = 0.1) -> float:
    order = np.argsort(-y_score)
    y_true = y_true[order]
    y_score = y_score[order]
    n_neg = (y_true == 0).sum()
    tps = np.cumsum(y_true)
    fprs = np.arange(1, len(y_true) + 1) - tps
    fprs = fprs / n_neg
    keep = fprs <= max_fpr
    if not keep.any():
        return 0.0
    tpr = tps[keep] / max((y_true == 1).sum(), 1)
    return float(np.mean(tpr))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normal-dir", help="正常样本 wav 目录")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--ckpt", default="models/ae_ckpt.npz")
    ap.add_argument("--score", action="store_true", help="评分模式")
    ap.add_argument("--test-dir", help="待测目录（normal/ 与 anom/ 两个子目录）")
    args = ap.parse_args()

    if args.score:
        ae = AutoEncoder.load(Path(args.ckpt))
        stats = dict(np.load(MU_PATH))
        test = Path(args.test_dir)
        x_n = collect(test / "normal", stats)
        x_a = collect(test / "anom", stats)
        s = np.concatenate([ae.score(x_n), ae.score(x_a)])
        y = np.concatenate([np.zeros(len(x_n)), np.ones(len(x_a))]).astype(int)
        print(json.dumps({"auc": round(auc(y, s), 4),
                          "pauc_0.1": round(pauc(y, s), 4),
                          "n_normal": len(x_n), "n_anom": len(x_a)},
                         ensure_ascii=False))
        return 0

    x = collect(Path(args.normal_dir))
    stats = {"mean": float(np.mean(x)), "std": float(np.std(x)) + 1e-6}
    x, _ = standardize(x, stats)
    MU_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez(MU_PATH, **stats)
    ae = AutoEncoder()
    rng = np.random.default_rng(0)
    for ep in range(args.epochs):
        idx = rng.permutation(len(x))[: args.batch]
        loss = ae.train_step(x[idx])
        if ep % 20 == 0 or ep == args.epochs - 1:
            print(f"epoch {ep:3d} loss {loss:.5f}")
    ckpt = Path(args.ckpt)
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ae.save(ckpt)
    print(json.dumps({"ckpt": str(ckpt), "train_vectors": len(x)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
