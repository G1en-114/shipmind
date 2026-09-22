#!/usr/bin/env python3
"""ShipMind 值班台后端：FastAPI，只绑 127.0.0.1（不暴露公网）。

面板数据源全部来自本地 Skill 输出（确定性可复现）：
  /api/alerts     实时告警流（声学分级）
  /api/spectrum   频谱/波形 + 告警特征
  /api/visual     视觉带框截图（base64）
  /api/situation  航线走廊 + 雷达态势
  /api/logs       日志/报告
  /api/trajectory 执行轨迹回放

启动：uvicorn web.server:app --host 127.0.0.1 --port 8888
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills-src/engine-room-acoustic-sentinel/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/radar-ppi-interpreter/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/route-deviation-watch/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/sonar-acoustic-fingerprint/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/manual-rag-query/scripts"))

FIX = ROOT / "evals" / "fixtures"


def _skill_output(script: str, args: list[str]) -> dict:
    import subprocess
    proc = subprocess.run([sys.executable, str(ROOT / script), *args],
                          capture_output=True, text=True, cwd=str(ROOT))
    raw = proc.stdout or ""
    i = raw.find("{")
    if i < 0:
        return {}
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw[i:])
        return obj
    except json.JSONDecodeError:
        return {}


def alerts() -> list[dict]:
    """告警流：对三个机种的合成夹具各跑一次声学检测。"""
    out = []
    cases = [("pump", "evals/fixtures/acoustic/anom/pump_bearing_worn_01.wav", "critical"),
             ("valve", "evals/fixtures/acoustic/normal/pump_normal_01.wav", "normal")]
    for dev, audio, _ in cases:
        r = _skill_output("skills-src/engine-room-acoustic-sentinel/scripts/acoustic_sentinel.py",
                          ["compare", audio, "--baseline",
                           "evals/fixtures/acoustic/baseline", "--device", "pump"])
        if not r:
            continue
        ev = r.get("evidence", [])
        out.append({
            "ts": "2026-09-22T00:00:00Z",
            "device": dev,
            "level": r.get("level"),
            "top_feature": ev[0].get("label") if ev else None,
            "delta": ev[0].get("delta") if ev else None,
            "causes": r.get("possible_causes", []),
        })
    return out


def spectrum() -> dict:
    import numpy as np
    sys.path.insert(0, str(ROOT / "skills-src/engine-room-acoustic-sentinel/scripts"))
    import acoustic_sentinel as A
    data, sr = A.load_audio(FIX / "acoustic/anom/pump_bearing_worn_01.wav")
    feats = A.extract_features(data, sr)
    # 频谱（下采样到 128 点供前端画）
    spec = np.abs(np.fft.rfft(data[:16384] * np.hanning(16384)))
    freqs = np.fft.rfftfreq(16384, 1.0 / sr)
    idx = np.linspace(0, len(spec) - 1, 128).astype(int)
    return {"features": feats,
            "spectrum": [round(float(v), 2) for v in 20 * np.log10(spec[idx] + 1e-9)],
            "freq_labels": [round(float(freqs[i]), 1) for i in idx]}


def visual() -> dict:
    """抽帧 + 读数 + 带框（返回 base64 图）。"""
    import base64
    from PIL import Image, ImageDraw
    img_path = FIX / "gauges/train/train_00000.jpg"
    r = _skill_output("skills-src/engine-room-visual-inspector/scripts/visual_inspect.py",
                      [str(img_path)])
    box = None
    if r.get("readings"):
        box = r["readings"][0].get("bbox")
    im = Image.open(img_path).convert("RGB")
    if box:
        ImageDraw.Draw(im).rectangle(box, outline=(255, 60, 60), width=4)
    import io
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=80)
    return {"image_b64": base64.b64encode(buf.getvalue()).decode(),
            "reading": (r.get("readings") or [{}])[0],
            "bbox": box}


def situation() -> dict:
    radar = _skill_output("skills-src/radar-ppi-interpreter/scripts/ppi_detect.py",
                          ["evals/fixtures/radar/two_targets.npy"])
    route = _skill_output("skills-src/route-deviation-watch/scripts/route_watch.py",
                          ["evals/fixtures/nmea/on_track.nmea", "--route",
                           "evals/fixtures/nmea/route.json"])
    sonar = _skill_output("skills-src/sonar-acoustic-fingerprint/scripts/sonar_fingerprint.py",
                          ["evals/fixtures/sonar/cargo_like.wav", "--mode", "rule"])
    return {"radar": radar, "route": route, "sonar": sonar}


def logs() -> dict:
    p = ROOT / "evals/fixtures/report/fusion_rounds.json"
    if not p.exists():
        return {"report_md": "", "note": "先跑 python scripts/fusion_demo.py 生成报告"}
    r = _skill_output("skills-src/report-composer/scripts/compose_report.py", [str(p)])
    return {"report_md": r.get("report_md", ""), "verifier": r.get("verifier", {})}


def trajectory() -> dict:
    sys.path.insert(0, str(ROOT / "harness"))
    from trajectory import load, diff
    runs = sorted((ROOT / "runs").glob("*/trajectory.jsonl")) if (ROOT / "runs").exists() else []
    if not runs:
        return {"runs": [], "note": "先跑 python harness/selftest.py 生成轨迹"}
    latest = runs[-1]
    steps = load(latest)
    return {"runs": [str(p.relative_to(ROOT)) for p in runs],
            "latest": {"path": str(latest.relative_to(ROOT)), "steps": len(steps),
                       "detail": steps[-3:]}}


def create_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="ShipMind 值班台")
    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/alerts")
    def _alerts():
        return {"alerts": alerts()}

    @app.get("/api/spectrum")
    def _spectrum():
        return spectrum()

    @app.get("/api/visual")
    def _visual():
        return visual()

    @app.get("/api/situation")
    def _situation():
        return situation()

    @app.get("/api/logs")
    def _logs():
        return logs()

    @app.get("/api/trajectory")
    def _trajectory():
        return trajectory()

    @app.get("/", response_class=HTMLResponse)
    def _index():
        return (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)
