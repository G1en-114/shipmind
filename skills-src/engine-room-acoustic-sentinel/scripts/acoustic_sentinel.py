#!/usr/bin/env python3
"""机舱声学异常哨兵 — 特征提取与基线对比

设计原则：
  1. 只依赖 numpy 与标准库，ARM64 上无需编译，降低 DGX Spark 上的部署风险；
  2. 输出可解释 —— 每条告警必须能指出是哪个特征、偏离了多少，不允许只给一个分数；
  3. 无基线时不得给出"设备正常"的结论，只能给出绝对阈值下的弱判断并显式标注。

用法：
    python acoustic_sentinel.py extract <audio.wav>
    python acoustic_sentinel.py compare <audio.wav> --baseline <目录> [--device pump]
    python acoustic_sentinel.py baseline <目录> [--device pump]     # 建立基线统计
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import wave
from pathlib import Path

import numpy as np

# 频段划分（Hz）。机舱异响多出现在中高频段，低频段主要是主机燃烧与管路噪声。
BANDS = {
    "low": (20.0, 200.0),
    "mid": (200.0, 2000.0),
    "high": (2000.0, 8000.0),
    "ultra": (8000.0, 16000.0),
}

# 各设备类型的默认阈值。真实项目中应从该设备的历史数据标定，此处为冷启动值。
DEVICE_PROFILES = {
    "pump": {"rms_watch": 0.05, "rms_alarm": 0.12, "high_ratio_alarm": 0.35},
    "bearing": {"rms_watch": 0.04, "rms_alarm": 0.10, "high_ratio_alarm": 0.40},
    "fan": {"rms_watch": 0.06, "rms_alarm": 0.14, "high_ratio_alarm": 0.30},
    "main_engine": {"rms_watch": 0.10, "rms_alarm": 0.22, "high_ratio_alarm": 0.25},
    "generic": {"rms_watch": 0.06, "rms_alarm": 0.14, "high_ratio_alarm": 0.35},
}

# 特征名 -> 人类可读说明。evidence 中直接使用，保证告警可解释。
FEATURE_LABELS = {
    "rms": "整体能量（RMS）",
    "crest_factor": "波峰因数（冲击性）",
    "spectral_centroid": "频谱质心（音色明亮度）",
    "spectral_flatness": "频谱平坦度（噪声性）",
    "zero_crossing_rate": "过零率（高频成分）",
    "band_ratio_low": "低频段能量占比",
    "band_ratio_mid": "中频段能量占比",
    "band_ratio_high": "高频段能量占比",
    "band_ratio_ultra": "超高频段能量占比",
}

# 显著上升的特征 -> 可能成因。只收录"本身上升即有意义"的特征：频段占比之和恒为 1，
# 某段上移会机械性压低其余段，互补效应不能当作独立证据。这是启发式映射，必须配合
# 手册检索结果输出，不得单独作为故障结论。
CAUSE_HINTS = {
    "band_ratio_high": ["轴承磨损或润滑不良", "动静部件摩擦"],
    "band_ratio_ultra": ["轴承早期点蚀", "气蚀或流态不稳"],
    "crest_factor": ["周期性冲击", "松动或间隙过大"],
}


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """读取 wav，返回 (单声道 float32 归一化到 [-1, 1], 采样率)。"""
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sample_width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sample_width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    elif sample_width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        raise ValueError(f"不支持的采样位宽: {sample_width * 8} bit")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    if framerate < 16000:
        raise ValueError(
            f"采样率 {framerate} Hz 低于 16000 Hz 要求，"
            "无法可靠分析 8kHz 以上的高频异响，请重采样后重试"
        )
    if len(data) / framerate < 5.0:
        raise ValueError(
            f"音频时长 {len(data) / framerate:.1f}s 不足 5s，样本过短不做结论"
        )

    return data, framerate


def extract_features(data: np.ndarray, sr: int) -> dict[str, float]:
    """提取一组可解释的时域与频域特征。"""
    rms = float(np.sqrt(np.mean(np.square(data))))
    peak = float(np.max(np.abs(data)))

    # 频域特征一律基于功率谱（|X|^2）。若用幅度谱求和，宽带噪声会因 bin 数量远多于
    # 窄带信号而在累加中占绝对优势，频段占比将失去判别意义。
    power = np.square(np.abs(np.fft.rfft(data * np.hanning(len(data)))))
    freqs = np.fft.rfftfreq(len(data), 1.0 / sr)
    total = float(np.sum(power)) + 1e-12

    centroid = float(np.sum(freqs * power) / total)
    flatness = float(np.exp(np.mean(np.log(power + 1e-12))) / (np.mean(power) + 1e-12))
    zcr = float(np.mean(np.abs(np.diff(np.sign(data)))))

    band_ratios = {}
    for name, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        band_ratios[f"band_ratio_{name}"] = float(np.sum(power[mask]) / total)

    return {
        "rms": rms,
        "crest_factor": (peak / (rms + 1e-12)),
        "spectral_centroid": centroid,
        "spectral_flatness": flatness,
        "zero_crossing_rate": zcr,
        **band_ratios,
    }


def build_baseline(baseline_dir: Path) -> dict:
    """对基线目录中所有 wav 提取特征，计算每特征的均值与标准差。"""
    files = sorted(baseline_dir.glob("*.wav"))
    if not files:
        raise ValueError(f"基线目录 {baseline_dir} 中没有 wav 文件")

    rows = []
    for f in files:
        data, sr = load_audio(f)
        rows.append(extract_features(data, sr))

    stats = {}
    for key in rows[0]:
        values = np.array([r[key] for r in rows], dtype=np.float64)
        stats[key] = {"mean": float(values.mean()), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0}

    return {"n_files": len(files), "features": stats}


def load_or_build_baseline(baseline_dir: Path, device: str) -> dict:
    cache = baseline_dir / ".baseline.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    baseline = build_baseline(baseline_dir)
    baseline["device"] = device
    cache.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    return baseline


def assess(features: dict[str, float], baseline: dict | None, device: str) -> tuple[str, list[dict], list[str]]:
    """判定等级，返回 (level, evidence, possible_causes)。"""
    profile = DEVICE_PROFILES.get(device, DEVICE_PROFILES["generic"])
    evidence: list[dict] = []
    causes: list[str] = []
    level = "normal"

    if baseline is None:
        # 无基线：只做绝对阈值判断，且明确不可给出"正常"结论。
        if features["rms"] >= profile["rms_alarm"]:
            level = "alarm"
        elif features["rms"] >= profile["rms_watch"]:
            level = "watch"
        evidence.append({
            "feature": "rms",
            "value": round(features["rms"], 4),
            "baseline": None,
            "delta": None,
            "note": "无基线可比，仅绝对阈值判断",
        })
        return level, evidence, causes

    # 有基线：按各特征的 z 分数排序，取偏离最大的前三个作为证据。
    # std 下限防护：基线录音近乎全同时 std→0 会让 z 无意义地爆炸，
    # 以均值的 5% 作为离散度下限（工业录音本底抖动真实存在）。
    scored = []
    for key, value in features.items():
        stat = baseline["features"].get(key)
        if not stat:
            continue
        std_eff = max(stat["std"], 0.05 * abs(stat["mean"]), 1e-9)
        if std_eff <= 1e-9:
            continue
        z = (value - stat["mean"]) / std_eff
        scored.append((abs(z), key, value, stat, z))

    scored.sort(reverse=True)

    deviation = math.sqrt(sum(z * z for _, _, _, _, z in scored) / max(len(scored), 1))

    for _, key, value, stat, z in scored[:3]:
        evidence.append({
            "feature": key,
            "label": FEATURE_LABELS.get(key, key),
            "value": round(value, 5),
            "baseline": round(stat["mean"], 5),
            "delta": round(value - stat["mean"], 5),
            "z": round(z, 2),
        })
        hints = CAUSE_HINTS.get(key)
        # 只认"本身上升"且相对变化超过 50% 的特征，避免把频段互补效应当成独立证据。
        if hints and z >= 3.0 and value >= stat["mean"] * 1.5:
            causes.extend(hints)

    if deviation >= 4.0 or any(abs(e.get("z", 0)) >= 5.0 for e in evidence):
        level = "critical"
    elif deviation >= 2.5:
        level = "alarm"
    elif deviation >= 1.5:
        level = "watch"

    return level, evidence, sorted(set(causes))


def cmd_extract(args: argparse.Namespace) -> int:
    data, sr = load_audio(Path(args.audio))
    features = extract_features(data, sr)
    print(json.dumps({"sample_rate": sr, "duration_s": round(len(data) / sr, 2), "features": features},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    baseline_dir = Path(args.baseline)
    baseline = load_or_build_baseline(baseline_dir, args.device)
    data, sr = load_audio(Path(args.audio))
    features = extract_features(data, sr)
    level, evidence, causes = assess(features, baseline, args.device)

    result = {
        "device_type": args.device,
        "condition": args.condition,
        "level": level,
        "evidence": evidence,
        "possible_causes": causes,
        "manual_refs": [],
        "audio_clip": os.path.abspath(args.audio),
        "baseline_files": baseline["n_files"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 契约要求：最终回复最后一个非空行是纯文本 MEDIA 路径。
    print(f"MEDIA:{os.path.abspath(args.audio)}")
    return 0 if level in ("normal", "watch") else 1


def cmd_baseline(args: argparse.Namespace) -> int:
    baseline = build_baseline(Path(args.baseline))
    baseline["device"] = args.device
    out = Path(args.baseline) / ".baseline.json"
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out), "n_files": baseline["n_files"]}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="机舱声学异常哨兵")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="提取音频特征")
    p_extract.add_argument("audio")
    p_extract.set_defaults(func=cmd_extract)

    p_compare = sub.add_parser("compare", help="与基线对比并判定等级")
    p_compare.add_argument("audio")
    p_compare.add_argument("--baseline", required=True, help="基线 wav 目录")
    p_compare.add_argument("--device", default="pump", choices=sorted(DEVICE_PROFILES))
    p_compare.add_argument("--condition", default="rated", choices=["rated", "partial_load", "startup"])
    p_compare.set_defaults(func=cmd_compare)

    p_baseline = sub.add_parser("baseline", help="从目录建立基线统计")
    p_baseline.add_argument("baseline")
    p_baseline.add_argument("--device", default="pump", choices=sorted(DEVICE_PROFILES))
    p_baseline.set_defaults(func=cmd_baseline)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as exc:
        print(json.dumps({"error": str(exc), "level": "rejected"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
