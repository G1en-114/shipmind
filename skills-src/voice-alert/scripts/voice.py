#!/usr/bin/env python3
"""语音链路：StepFun ASR / TTS（零依赖 urllib）。

机舱噪音环境下，告警播报**只播分级与动作**，不播技术细节——听不清还要安全。
用法：
    python voice.py --tts "3号泵轴承异响，建议切换备用泵" --out alert.wav
    python voice.py --asr input.wav
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load_env() -> dict[str, str]:
    env = dict(os.environ)
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def tts(text: str, out: Path, model: str = "step-tts-2") -> dict:
    env = load_env()
    payload = {"model": model, "input": text, "voice": "linjiajiejie"}
    req = urllib.request.Request(
        env["STEPFUN_BASE_URL"].rstrip("/") + "/audio/speech",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {env['STEPFUN_API_KEY']}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        audio = resp.read()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    return {"ok": True, "file": str(out), "bytes": len(audio), "text": text}


def asr_(wav: Path, model: str = "step-asr") -> dict:
    env = load_env()
    import uuid
    boundary = uuid.uuid4().hex
    parts = [f"--{boundary}".encode()]
    parts.append(b'Content-Disposition: form-data; name="file"; '
                 b'filename="' + wav.name.encode() + b'"')
    parts.append(b"Content-Type: audio/wav\r\n")
    parts.append(wav.read_bytes())
    parts.append(f"--{boundary}".encode())
    parts.append(b'Content-Disposition: form-data; name="model"\r\n')
    parts.append(model.encode())
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"\r\n".join(parts)
    req = urllib.request.Request(
        env["STEPFUN_BASE_URL"].rstrip("/") + "/audio/transcriptions",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "Authorization": f"Bearer {env['STEPFUN_API_KEY']}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {"ok": True, "text": data.get("text", ""), "raw": data}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tts", help="要合成的文本")
    ap.add_argument("--out", default="output/alert.wav")
    ap.add_argument("--asr", dest="asr_file", help="待识别音频")
    args = ap.parse_args()
    try:
        if args.tts is not None and not args.tts.strip():
            print(json.dumps({"ok": False, "error": "播报文本为空，拒绝合成"},
                             ensure_ascii=False), file=sys.stderr)
            return 2
        if args.tts:
            print(json.dumps(tts(args.tts, Path(args.out)), ensure_ascii=False))
            print(f"MEDIA:{Path(args.out).resolve()}")
            return 0
        if args.asr_file:
            print(json.dumps(asr_(Path(args.asr_file)), ensure_ascii=False))
            return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)[:300]},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    ap.error("需要 --tts 或 --asr")


if __name__ == "__main__":
    raise SystemExit(main())
