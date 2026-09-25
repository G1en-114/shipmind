#!/usr/bin/env python3
"""Place promo-two narration in its scene windows and mix it over the quiet bed."""
from __future__ import annotations

import argparse
import json
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

SR = 48000
ROOT = Path(__file__).resolve().parents[2]
TIMELINE = ROOT / "scripts/video/promo2_timeline.json"


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        if wav.getframerate() != SR or wav.getsampwidth() != 2:
            raise ValueError(f"Unexpected WAV format: {path}")
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float64) / 32768
    return data.reshape(-1, channels).mean(1) if channels > 1 else data


def write_wav(path: Path, audio: np.ndarray, channels: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if channels == 2 and audio.ndim == 1:
        audio = np.column_stack((audio, audio))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())


parser = argparse.ArgumentParser()
parser.add_argument("--raw-dir", type=Path, default=Path("runs/delivery/video/promo2_voice_raw"))
parser.add_argument("--sfx", type=Path, default=Path("runs/delivery/video/shipmind-promo2-sfx.wav"))
parser.add_argument("--voice", type=Path, default=Path("runs/delivery/video/shipmind-promo2-voice.wav"))
parser.add_argument("--mix", type=Path, default=Path("runs/delivery/video/shipmind-promo2-mix.wav"))
args = parser.parse_args()

scenes = json.loads(TIMELINE.read_text(encoding="utf-8"))["scenes"]
voice = np.zeros(round(72 * SR), dtype=np.float64)
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
processed = args.raw_dir / "processed"
processed.mkdir(parents=True, exist_ok=True)

for index, scene in enumerate(scenes, 1):
    source = args.raw_dir / f"segment-{index:02d}.wav"
    start = float(scene["start"]) + 0.42
    target = float(scene["end"]) - start - 0.35
    raw = read_wav(source)
    tempo = max(1.0, len(raw) / SR / target)
    out = processed / f"segment-{index:02d}.wav"
    filters = (
        f"atempo={tempo:.8f},highpass=f=70,lowpass=f=11500,"
        "bass=g=1.8:f=150:w=.7,equalizer=f=2400:t=q:w=1.1:g=1.0,"
        "acompressor=threshold=0.12:ratio=2.2:attack=9:release=120,loudnorm=I=-21:TP=-4:LRA=7"
    )
    subprocess.run(
        [ffmpeg, "-y", "-i", str(source), "-af", filters, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(out)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    segment = read_wav(out)[: round(target * SR)]
    fade = min(round(0.04 * SR), len(segment) // 4)
    segment[:fade] *= np.linspace(0, 1, fade)
    segment[-fade:] *= np.linspace(1, 0, fade)
    position = round(start * SR)
    voice[position : position + len(segment)] += segment

write_wav(args.voice, voice, 1)
with wave.open(str(args.sfx), "rb") as wav:
    bed = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, 2) / 32768
envelope = np.convolve(np.abs(voice), np.ones(round(0.1 * SR)) / round(0.1 * SR), mode="same")
duck = 1 - 0.5 * np.clip(envelope / 0.04, 0, 1)
mixed = voice[:, None] * 0.92 + bed[: len(voice)] * duck[:, None] * 0.075
mixed = np.tanh(mixed * 1.05)
mixed *= 0.92 / max(np.max(np.abs(mixed)), 1e-9)
write_wav(args.mix, mixed, 2)
print(args.voice)
print(args.mix)
