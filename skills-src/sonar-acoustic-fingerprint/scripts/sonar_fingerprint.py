#!/usr/bin/env python3
"""被动声纹（民用海事感知）：LOFAR 窄带谱线 + DEMON 包谱 → 规则分类。

--mode rule：谱线统计，可解释，当前可用。
--mode ml  ：ShipsEar/DeepShip 分类器占位（D7 交付），未上线前明确拒绝。
"""
from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np


def load_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as wf:
        ch, sw, sr = wf.getnchannels(), wf.getsampwidth(), wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    if sw == 2:
        data = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, "<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError("仅支持 16/32bit PCM wav")
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return data, sr


def lofar_spectrum(sig: np.ndarray, sr: int, nfft: int = 8192):
    win = np.hanning(nfft)
    step = nfft // 2
    blocks = max((len(sig) - nfft) // step, 1)
    acc = np.zeros(nfft // 2 + 1)
    for i in range(blocks):
        seg = sig[i * step: i * step + nfft] * win
        acc += np.square(np.abs(np.fft.rfft(seg)))
    freqs = np.fft.rfftfreq(nfft, 1.0 / sr)
    return freqs, acc / blocks


def find_tonals(freqs, spec, f_lo=4.0, f_hi=500.0):
    band = (freqs >= f_lo) & (freqs <= f_hi)
    idx = np.nonzero(band)[0]
    base = float(np.median(spec[idx])) + 1e-12
    peaks = []
    for i in idx[1:-1]:
        if spec[i] > spec[i - 1] and spec[i] >= spec[i + 1] and spec[i] > 6 * base:
            peaks.append((float(freqs[i]), float(spec[i])))
    peaks.sort(key=lambda x: -x[1])
    return peaks[:20], base


def harmonic_series(peaks, df: float):
    """在谱线中找最佳基频：允许 k·f0 匹配，返回 (匹配阶数, f0, 阶列表)。

    容差取 max(2%, 1.5×频率分辨率/目标频率)：nfft 量化本身可造成半个 bin
    以上的偏差，在低频段（如 41 Hz 处一 bin 即 4.8%）固定百分比容差会漏配。
    """
    best = (0, None, [])
    for f0, _ in peaks:
        if f0 < 3:
            continue
        matched = []
        for k in range(1, 9):
            target = f0 * k
            tol = max(0.02, 1.5 * df / target)
            hit = next((f for f, _ in peaks if abs(f - target) / target < tol), None)
            if hit:
                matched.append(k)
        if len(matched) > best[0]:
            best = (len(matched), f0, matched)
    return best


def demon_shaft(sig: np.ndarray, sr: int, f_lo=1.0, f_hi=30.0):
    """平方包络低通 → 包谱，返回 1–30Hz 内最强分量（轴频估计）。"""
    win = max(int(sr * 0.02), 1)
    env = np.convolve(np.square(sig), np.ones(win) / win, mode="same")
    env = env - env.mean()
    spec = np.abs(np.fft.rfft(env * np.hanning(len(env))))
    freqs = np.fft.rfftfreq(len(env), 1.0 / sr)
    band = (freqs >= f_lo) & (freqs <= f_hi)
    if not band.any():
        return None
    idx = np.nonzero(band)[0]
    return float(freqs[idx[int(np.argmax(spec[band]))]])


def classify_rule(freqs, spec, n_peaks, n_harm, f0) -> tuple[str, float]:
    total = float(spec.sum()) + 1e-12
    mid = (freqs >= 200) & (freqs < 2000)
    # 平坦谱的固有中频占比 ≈ 0.225（1800/8000），阈值必须显著高于它，
    # 否则任何纯宽带噪声都会被误判成拖轮/渔船类。
    mid_ratio = float(spec[mid].sum()) / total
    if n_harm >= 3 and f0 and f0 < 100:
        return "large_cargo_or_tanker", min(0.9, 0.4 + 0.1 * n_harm)
    if n_harm >= 2 and f0 and 100 <= f0 < 400:
        return "medium_vessel", min(0.8, 0.4 + 0.1 * n_harm)
    if n_peaks == 0 and mid_ratio > 0.4:
        return "tug_or_fishing", 0.45
    return "unknown", 0.2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--mode", choices=["rule", "ml"], default="rule")
    args = ap.parse_args()

    if args.mode == "ml":
        print(json.dumps({"error": "ShipsEar/DeepShip 分类器尚未训练（D7 交付），"
                                   "当前仅 rule 模式可用"}, ensure_ascii=False),
              file=sys.stderr)
        return 3

    try:
        sig, sr = load_wav(args.audio)
    except (ValueError, FileNotFoundError, wave.Error) as exc:
        print(json.dumps({"error": str(exc), "label": "unknown", "confidence": 0.0,
                          "mode": "rule_fallback", "evidence": {}},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    if len(sig) / sr < 5:
        print(json.dumps({"error": "音频不足 5 秒", "label": "unknown", "confidence": 0.0,
                          "mode": "rule_fallback", "evidence": {}},
                         ensure_ascii=False), file=sys.stderr)
        return 2

    freqs, spec = lofar_spectrum(sig, sr)
    peaks, _ = find_tonals(freqs, spec)
    df = float(freqs[1] - freqs[0])
    n_harm, f0, matched = harmonic_series(peaks, df)
    shaft = demon_shaft(sig, sr)
    label, confidence = classify_rule(freqs, spec, len(peaks), n_harm, f0)

    print(json.dumps({
        "label": label,
        "confidence": round(confidence, 2),
        "mode": "rule_fallback",
        "evidence": {
            "tonal_count": len(peaks),
            "f0_hz": round(f0, 2) if f0 else None,
            "harmonics_matched": matched,
            "demon_shaft_hz_est": round(shaft, 2) if shaft else None,
        },
        "note": "规则匹配结果，非 ML 分类；正式结论需结合雷达目标交叉印证",
        "audio": args.audio,
    }, ensure_ascii=False, indent=2))
    print(f"MEDIA:{Path(args.audio).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
