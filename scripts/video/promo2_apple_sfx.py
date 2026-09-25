#!/usr/bin/env python3
"""Create a quiet, minimal sound bed for the Apple-style ShipMind promo."""
from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

SR = 48000
DURATION = 42.0
RNG = np.random.default_rng(412)
mix = np.zeros((round(SR * DURATION), 2), dtype=np.float64)


def smooth(x: np.ndarray, n: int) -> np.ndarray:
    return np.convolve(x, np.ones(n) / n, mode="same")


def add(mono: np.ndarray, start: float, gain: float, pan: float = 0.0) -> None:
    stereo = np.column_stack((mono * np.sqrt((1 - pan) / 2), mono * np.sqrt((1 + pan) / 2)))
    i = round(start * SR)
    j = min(len(mix), i + len(stereo))
    mix[i:j] += stereo[: j - i] * gain


def breath(duration: float = 1.1) -> np.ndarray:
    n = round(duration * SR)
    raw = RNG.standard_normal(n)
    air = smooth(raw, 100) - smooth(raw, 950)
    envelope = np.sin(np.linspace(0, np.pi, n)) ** 2.4
    return air * envelope


def tone(freq: float, duration: float = 1.8) -> np.ndarray:
    n = round(duration * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + .25 * np.sin(2 * np.pi * freq * 2 * t)) * np.exp(-t * 3.2)


t = np.arange(len(mix)) / SR
room = smooth(RNG.standard_normal(len(mix)), 300) * .006 + np.sin(2 * np.pi * 31 * t) * .0012
mix[:, 0] += room
mix[:, 1] += np.roll(room, 190)

for i, change in enumerate((5, 11, 18, 25, 32, 38)):
    add(breath(), change - .5, .045, (-.14, .12, -.1, .14, -.08, 0)[i])
for when, freq in ((3.0, 420), (9.0, 560), (23.0, 680), (30.0, 520), (40.0, 440)):
    add(tone(freq), when, .012)

mix = np.tanh(mix)
mix *= .68 / max(np.max(np.abs(mix)), 1e-9)
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("runs/delivery/video/shipmind-promo2-apple-sfx.wav"))
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(args.output), "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(SR)
    wav.writeframes((mix * 32767).astype("<i2").tobytes())
print(args.output)
