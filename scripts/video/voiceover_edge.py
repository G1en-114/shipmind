#!/usr/bin/env python3
"""Generate six authoritative English narration segments with a broadcast male voice."""
from __future__ import annotations
import asyncio,subprocess
from pathlib import Path
import edge_tts,imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/delivery/video/voice_raw';OUT.mkdir(parents=True,exist_ok=True)
LINES=(
 "At three A M, an unfamiliar vibration breaks a ship's steady rhythm.",
 'With NVIDIA D G X Spark onboard, Ship Mind brings powerful local A I to the watch—compact, responsive, and ready beyond the network.',
 'It unites acoustics, gauges, radar, sonar, and route movement into one clear, evidence-backed picture.',
 'The engineer asks, how are things now? In seconds, the local A I traces the change, cites the signals, and shows what to inspect next.',
 'Agent Skills, Deep Stream, Step Fun, Kwen, and V L L M turn Spark into a complete, reproducible workflow.',
 'Safer ships. Clearer decisions. Ship Mind.',
)

async def main():
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    for i,text in enumerate(LINES,1):
        mp3=OUT/f'segment-{i:02d}.mp3';wav=OUT/f'segment-{i:02d}.wav'
        speech=edge_tts.Communicate(text,'en-US-ChristopherNeural',rate='-8%',pitch='-10Hz',volume='+0%')
        await speech.save(str(mp3))
        subprocess.run([ffmpeg,'-y','-i',str(mp3),'-ar','48000','-ac','1','-c:a','pcm_s16le',str(wav)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(OUT)

if __name__=='__main__':asyncio.run(main())
