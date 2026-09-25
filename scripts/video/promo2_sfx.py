#!/usr/bin/env python3
"""Build a restrained 72-second nautical archive sound bed."""
from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

SR = 48000
DURATION = 72.0
RNG = np.random.default_rng(227)
mix = np.zeros((round(SR * DURATION), 2), dtype=np.float64)


def smooth(x: np.ndarray, n: int) -> np.ndarray:
    return np.convolve(x, np.ones(n) / n, mode="same")


def add(sound: np.ndarray, start: float, level: float, pan: float = 0.0) -> None:
    stereo = np.column_stack((sound * np.sqrt((1 - pan) / 2), sound * np.sqrt((1 + pan) / 2)))
    i = max(0, round(start * SR))
    j = min(len(mix), i + len(stereo))
    mix[i:j] += stereo[: j - i] * level


def page_turn(duration: float = 0.9) -> np.ndarray:
    n = round(duration * SR)
    t = np.arange(n) / SR
    raw = RNG.standard_normal(n)
    paper = smooth(raw, 120) - smooth(raw, 900)
    return paper * np.sin(np.pi * t / duration) ** 2


def sonar(freq: float = 620.0, duration: float = 1.5) -> np.ndarray:
    n = round(duration * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.3)


# Low ship/operations-room ambience. It should be felt before it is noticed.
t = np.arange(len(mix)) / SR
raw = RNG.standard_normal(len(mix))
room = smooth(raw, 240) * 0.011 + np.sin(2 * np.pi * 34 * t) * 0.0023
mix[:, 0] += room
mix[:, 1] += np.roll(room, 170)

for i, change in enumerate((7, 17, 26, 37, 47, 58, 65)):
    add(page_turn(), change - 0.45, 0.085, (-0.2, 0.15, -0.1, 0.18, -0.12, 0.12, 0)[i])
for when, freq in ((3.3, 520), (23.0, 740), (33.0, 610), (51.0, 880), (67.2, 470)):
    add(sonar(freq), when, 0.025)

mix = np.tanh(mix * 1.1)
mix *= 0.78 / max(np.max(np.abs(mix)), 1e-9)

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("runs/delivery/video/shipmind-promo2-sfx.wav"))
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(args.output), "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(SR)
    wav.writeframes((mix * 32767).astype("<i2").tobytes())
print(args.output)
