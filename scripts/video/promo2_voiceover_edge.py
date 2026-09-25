#!/usr/bin/env python3
"""Generate the eight Chinese narration segments for ShipMind promo two."""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
TIMELINE = ROOT / "scripts/video/promo2_timeline.json"
OUT = ROOT / "runs/delivery/video/promo2_voice_raw"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = json.loads(TIMELINE.read_text(encoding="utf-8"))["scenes"]
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    for index, scene in enumerate(scenes, 1):
        mp3 = OUT / f"segment-{index:02d}.mp3"
        wav = OUT / f"segment-{index:02d}.wav"
        speech = edge_tts.Communicate(
            scene["voiceover"],
            "zh-CN-YunyangNeural",
            rate="-8%",
            pitch="-8Hz",
            volume="+0%",
        )
        await speech.save(str(mp3))
        subprocess.run(
            [ffmpeg, "-y", "-i", str(mp3), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print(OUT)


if __name__ == "__main__":
    asyncio.run(main())
