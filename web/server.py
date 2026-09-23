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
import os
import sys
import base64
import io
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills-src/engine-room-acoustic-sentinel/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/radar-ppi-interpreter/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/route-deviation-watch/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/sonar-acoustic-fingerprint/scripts"))
sys.path.insert(0, str(ROOT / "skills-src/manual-rag-query/scripts"))

FIX = ROOT / "evals" / "fixtures"
_SIM_STARTED = time.monotonic()
_VISUAL_CACHE: dict[str, dict] = {}
_SPECTRUM_BASE: dict | None = None


def _skill_output(script: str, args: list[str]) -> dict:
    import subprocess
    from fastapi import HTTPException
    try:
        proc = subprocess.run([sys.executable, str(ROOT / script), *args],
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
                              cwd=str(ROOT), timeout=25)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "分析超时，请稍后重试")
    if proc.returncode not in (0, 1):
        raise HTTPException(503, "分析未完成，请检查本地演示素材是否已生成")
    raw = proc.stdout or ""
    i = raw.find("{")
    if i < 0:
        raise HTTPException(503, "分析未返回有效数据")
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw[i:])
        if not isinstance(obj, dict) or obj.get("error"):
            raise HTTPException(503, "分析结果不可用")
        return obj
    except json.JSONDecodeError:
        raise HTTPException(503, "分析结果格式异常")


def alerts() -> list[dict]:
    """告警流：对三个机种的合成夹具各跑一次声学检测。"""
    out = []
    cases = [("泵 · 异常样本", "evals/fixtures/acoustic/anom/pump_bearing_worn_01.wav"),
             ("泵 · 正常对照", "evals/fixtures/acoustic/normal/pump_normal_01.wav")]
    for dev, audio in cases:
        r = _skill_output("skills-src/engine-room-acoustic-sentinel/scripts/acoustic_sentinel.py",
                          ["compare", audio, "--baseline",
                           "evals/fixtures/acoustic/baseline", "--device", "pump"])
        if not r:
            continue
        ev = r.get("evidence", [])
        out.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": audio,
            "synthetic": True,
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
    global _SPECTRUM_BASE
    if _SPECTRUM_BASE is None:
        data, sr = A.load_audio(FIX / "acoustic/anom/pump_bearing_worn_01.wav")
        feats = A.extract_features(data, sr)
        spec = np.abs(np.fft.rfft(data[:16384] * np.hanning(16384)))
        freqs = np.fft.rfftfreq(16384, 1.0 / sr)
        idx = np.linspace(0, len(spec) - 1, 128).astype(int)
        _SPECTRUM_BASE = {"features": feats,
                          "spectrum": 20 * np.log10(spec[idx] + 1e-9),
                          "freq_labels": freqs[idx]}
    elapsed = time.monotonic() - _SIM_STARTED
    phase = elapsed * 1.6
    base = _SPECTRUM_BASE
    values = base["spectrum"] + 2.2 * np.sin(np.arange(128) / 7.0 + phase)
    values += 0.55 * np.sin(np.arange(128) / 2.8 - phase * 1.7)
    feats = dict(base["features"])
    feats["rms"] = float(feats.get("rms", 0) * (1 + 0.035 * np.sin(phase)))
    feats["crest_factor"] = float(feats.get("crest_factor", 0) + 0.08 * np.sin(phase * .7))
    return {"features": feats,
            "spectrum": [round(float(v), 2) for v in values],
            "freq_labels": [round(float(v), 1) for v in base["freq_labels"]],
            "synthetic": True, "frame": int(elapsed * 10),
            "sampled_at": datetime.now(timezone.utc).isoformat()}


def visual() -> dict:
    """抽帧 + 读数 + 带框（返回 base64 图）。"""
    from PIL import Image, ImageDraw
    paths = sorted((FIX / "gauges/train").glob("train_*.jpg"))
    if not paths:
        raise RuntimeError("没有找到表盘仿真帧")
    frame = int((time.monotonic() - _SIM_STARTED) * 0.6) % len(paths)
    # 轮换真实合成帧；遇到视觉模型拒判时自动跳到下一帧，保持演示连续可读。
    chosen = None
    for offset in range(len(paths)):
        candidate = paths[(frame + offset) % len(paths)]
        key = str(candidate)
        if key not in _VISUAL_CACHE:
            r = _skill_output("skills-src/engine-room-visual-inspector/scripts/visual_inspect.py",
                              [str(candidate)])
            box = (r.get("readings") or [{}])[0].get("bbox")
            im = Image.open(candidate).convert("RGB")
            if box:
                ImageDraw.Draw(im).rectangle(box, outline=(255, 60, 60), width=4)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=80)
            _VISUAL_CACHE[key] = {"image_b64": base64.b64encode(buf.getvalue()).decode(),
                                  "reading": (r.get("readings") or [{}])[0], "bbox": box}
        if isinstance(_VISUAL_CACHE[key].get("reading", {}).get("value"), (int, float)):
            chosen = candidate
            frame = (frame + offset) % len(paths)
            break
    img_path = chosen or paths[frame]
    result = dict(_VISUAL_CACHE[str(img_path)])
    result.update({"synthetic": True, "frame": frame,
                   "sampled_at": datetime.now(timezone.utc).isoformat(),
                   "source": str(img_path.relative_to(ROOT))})
    return result


def situation() -> dict:
    radar = _skill_output("skills-src/radar-ppi-interpreter/scripts/ppi_detect.py",
                          ["evals/fixtures/radar/two_targets.npy"])
    route = _skill_output("skills-src/route-deviation-watch/scripts/route_watch.py",
                          ["evals/fixtures/nmea/on_track.nmea", "--route",
                           "evals/fixtures/nmea/route.json"])
    sonar = _skill_output("skills-src/sonar-acoustic-fingerprint/scripts/sonar_fingerprint.py",
                          ["evals/fixtures/sonar/cargo_like.wav", "--mode", "rule"])
    from route_watch import parse_rmc
    route["waypoints"] = json.loads((FIX / "nmea/route.json").read_text(encoding="utf-8"))["waypoints"]
    route["fixes"] = parse_rmc(str(FIX / "nmea/on_track.nmea"))
    return {"radar": radar, "route": route, "sonar": sonar, "synthetic": True}


def logs() -> dict:
    p = ROOT / "evals/fixtures/report/fusion_rounds.json"
    if not p.exists():
        return {"report_md": "", "note": "先跑 python scripts/fusion_demo.py 生成报告"}
    r = _skill_output("skills-src/report-composer/scripts/compose_report.py", [str(p)])
    return {"report_md": r.get("report_md", ""), "verifier": r.get("verifier", {}),
            "source": str(p.relative_to(ROOT)), "source_updated_at": p.stat().st_mtime,
            "verification_scope": "reference_presence_only"}


def trajectory() -> dict:
    sys.path.insert(0, str(ROOT / "harness"))
    from trajectory import load, diff
    runs = sorted((ROOT / "runs").glob("*/trajectory.jsonl")) if (ROOT / "runs").exists() else []
    if not runs:
        return {"runs": [], "note": "先跑 python harness/selftest.py 生成轨迹"}
    latest = max(runs, key=lambda p: p.stat().st_mtime)
    steps = load(latest)
    return {"runs": [str(p.relative_to(ROOT)) for p in runs],
            "latest": {"path": str(latest.relative_to(ROOT)), "steps": len(steps),
                       "updated_at": latest.stat().st_mtime,
                       "detail": steps[-30:]}}


def create_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    from fastapi import Query
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="ShipMind 值班台")
    app.mount("/static", StaticFiles(directory=str(ROOT / "web/static")), name="static")
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

    @app.get("/api/manual")
    def _manual(q: str = Query(min_length=1, max_length=200)):
        return _skill_output("skills-src/manual-rag-query/scripts/rag_query.py",
                             ["--query", q, "--top-k", "3", "--json"])

    @app.get("/", response_class=HTMLResponse)
    def _index():
        return (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)
