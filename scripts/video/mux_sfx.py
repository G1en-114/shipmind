#!/usr/bin/env python3
"""Mux the rendered silent master with the non-verbal effects bed."""
from __future__ import annotations
import argparse,subprocess
from pathlib import Path
import imageio_ffmpeg

ap=argparse.ArgumentParser();ap.add_argument('video',type=Path);ap.add_argument('audio',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-i',str(args.video),'-i',str(args.audio),'-c:v','copy','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',str(args.output)]
subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL);print(args.output)
