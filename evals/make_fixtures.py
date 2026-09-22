#!/usr/bin/env python3
"""生成评测夹具（确定性种子）。run_evals 在夹具缺失时自动调用。"""
from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "evals" / "fixtures"


def save_wav(path: Path, sig: np.ndarray, sr: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.clip(sig, -1.0, 1.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def acoustic() -> None:
    # 清掉陈旧基线缓存，保证基线统计永远对应当前夹具
    stale = FIX / "acoustic/baseline/.baseline.json"
    if stale.exists():
        stale.unlink()
    sr = 16000
    rng = np.random.default_rng(42)
    t = np.arange(sr * 6) / sr

    def realization() -> np.ndarray:
        # 基线必须是独立采样（同 80Hz 工频 + 独立噪声），否则 std≈0
        # 会让正常样本的 z 分数爆炸——工业录音的本底抖动是真实存在的
        return 0.3 * np.sin(2 * np.pi * 80 * t) + 0.05 * rng.standard_normal(len(t))

    for i in range(3):
        save_wav(FIX / "acoustic/baseline" / f"n{i}.wav", realization())
    # 评分目录约定：normal/ + anom/（DCASE 风格），训练用 baseline/
    save_wav(FIX / "acoustic/normal/pump_normal_01.wav", realization())
    worn = (0.3 * np.sin(2 * np.pi * 80 * t)
            + 0.25 * np.sin(2 * np.pi * 4000 * t)
            + 0.05 * rng.standard_normal(len(t)))
    save_wav(FIX / "acoustic/anom/pump_bearing_worn_01.wav", worn)
    save_wav(FIX / "acoustic/pump_short_2s.wav", realization()[: sr * 2])


def sonar() -> None:
    sr = 16000
    rng = np.random.default_rng(7)
    t = np.arange(sr * 8) / sr
    cargo = 0.05 * rng.standard_normal(len(t))
    for k in range(1, 6):
        cargo = cargo + (0.12 / k) * np.sin(2 * np.pi * 14 * k * t + 0.3 * k)
    save_wav(FIX / "sonar/cargo_like.wav", cargo)
    save_wav(FIX / "sonar/noise_only.wav", 0.15 * rng.standard_normal(len(t)))


def routes() -> None:
    p = FIX / "nmea/route.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "waypoints": [[122.20, 31.00], [122.60, 31.05], [123.00, 31.02]],
        "corridor_half_width_m": 1852,
    }), encoding="utf-8")
    # watch 档漂移 1200m：落在走廊 1852m 的 0.5~1 倍区间（926~1852m）
    (FIX / "nmea/garbage.nmea").write_text(
        "$GPTXT,not,a,fix*00\n$GPRMC,broken,line\n", encoding="utf-8")


def radar() -> None:
    p = FIX / "radar"
    p.mkdir(parents=True, exist_ok=True)
    (p / "two_targets.json").write_text(json.dumps([
        {"bearing_deg": 45.0, "range_m": 3000, "snr": 20},
        {"bearing_deg": 210.0, "range_m": 6000, "snr": 16},
    ]), encoding="utf-8")
    (p / "empty.json").write_text("[]", encoding="utf-8")


def report() -> None:
    p = FIX / "report"
    p.mkdir(parents=True, exist_ok=True)
    (p / "rounds_good.json").write_text(json.dumps({
        "title": "机舱巡检报告（测试）", "rounds": [
            {"step_id": "acoustic-001", "skill": "engine-room-acoustic-sentinel",
             "output": {"level": "alarm", "evidence": [
                 {"feature": "band_ratio_high", "label": "高频段能量占比", "delta": 0.38}]}},
            {"step_id": "visual-001", "skill": "engine-room-visual-inspector",
             "output": {"readings": [{"value": 5.05, "unit": "bar", "method": "red_needle"}]}}
        ]}, ensure_ascii=False), encoding="utf-8")
    (p / "rounds_bad.json").write_text(json.dumps({
        "title": "机舱巡检报告（测试）", "rounds": [
            {"step_id": "acoustic-001", "skill": "engine-room-acoustic-sentinel",
             "output": {"level": "alarm", "evidence": []}}
        ]}, ensure_ascii=False), encoding="utf-8")

def navlog() -> None:
    p = FIX / "navlog/events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {"ts": "2026-09-21T02:10:00Z", "type": "alarm",
         "text": "3号泵轴承区域高频能量异常（alarm）"},
        {"ts": "2026-09-21T02:12:30Z", "type": "action",
         "text": "切换备用泵，降负荷运行"},
        {"ts": "2026-09-21T03:00:00Z", "type": "info",
         "text": "雷达 045° 发现目标，声纹判为渔船类"},
    ]
    p.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events),
                 encoding="utf-8")


def nmea_tracks() -> None:
    sim = ROOT / "sensors" / "nmea_simulator.py"
    route = FIX / "nmea/route.json"
    for name, drift in (("on_track.nmea", 0), ("watch_drift.nmea", 1200),
                        ("alarm_drift.nmea", 2000)):
        subprocess.run([sys.executable, str(sim), "--route", str(route),
                        "--drift-m", str(drift),
                        "--out", str(FIX / "nmea" / name)],
                       check=True, cwd=ROOT)


def radar_fields() -> None:
    synth = ROOT / "skills-src/radar-ppi-interpreter/scripts/ppi_synth.py"
    for targets_json, out in (("two_targets.json", "two_targets"),
                              ("empty.json", "empty")):
        subprocess.run([sys.executable, str(synth),
                        "--targets", str(FIX / "radar" / targets_json),
                        "--out", str(FIX / "radar" / out)],
                       check=True, cwd=ROOT)


if __name__ == "__main__":
    acoustic()
    sonar()
    routes()
    radar()
    report()
    navlog()
    nmea_tracks()
    radar_fields()
    print("fixtures ready:", FIX)
