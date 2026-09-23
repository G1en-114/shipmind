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
import math
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

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
AI_LOG_DIR = ROOT / "runs" / "ai-duty"
AI_LOG_PATH = AI_LOG_DIR / "duty.jsonl"
AI_LOG_CONFIG = AI_LOG_DIR / "config.json"
_AI_LOG_LOCK = threading.Lock()
_AI_INFERENCE_LOCK = threading.Lock()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=240)


class LogConfigRequest(BaseModel):
    max_mb: int = Field(ge=1, le=64)


def _configured_log_limit() -> int:
    default = int(os.getenv("SHIPMIND_AI_LOG_MAX_BYTES", str(2 * 1024 * 1024)))
    try:
        saved = json.loads(AI_LOG_CONFIG.read_text(encoding="utf-8"))
        default = int(saved.get("max_bytes", default))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return max(64 * 1024, min(default, 64 * 1024 * 1024))


_AI_LOG_MAX_BYTES = _configured_log_limit()


def _rotate_ai_log(incoming_bytes: int = 0) -> None:
    """Rotate a bounded JSONL log, retaining three archives."""
    if not AI_LOG_PATH.exists() or AI_LOG_PATH.stat().st_size + incoming_bytes <= _AI_LOG_MAX_BYTES:
        return
    oldest = AI_LOG_PATH.with_suffix(".jsonl.3")
    if oldest.exists():
        oldest.unlink()
    for index in (2, 1):
        source = AI_LOG_PATH.with_suffix(f".jsonl.{index}")
        if source.exists():
            source.replace(AI_LOG_PATH.with_suffix(f".jsonl.{index + 1}"))
    AI_LOG_PATH.replace(AI_LOG_PATH.with_suffix(".jsonl.1"))


def _append_ai_log(kind: str, message: str, **detail) -> dict:
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind,
             "message": str(message), **detail}
    encoded = (json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with _AI_LOG_LOCK:
        AI_LOG_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_ai_log(len(encoded))
        with AI_LOG_PATH.open("ab") as handle:
            handle.write(encoded)
    return entry


def ai_log_state(limit: int = 80) -> dict:
    def tail(path: Path, count: int) -> list[dict]:
        if not path.exists() or count <= 0:
            return []
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            position = handle.tell()
            data = b""
            while position > 0 and data.count(b"\n") <= count:
                chunk = min(8192, position)
                position -= chunk
                handle.seek(position)
                data = handle.read(chunk) + data
        rows = []
        for line in data.splitlines()[-count:]:
            try:
                row = json.loads(line.decode("utf-8", errors="replace"))
                if isinstance(row, dict):
                    rows.append(row)
            except json.JSONDecodeError:
                continue
        return rows

    entries = []
    with _AI_LOG_LOCK:
        paths = [AI_LOG_PATH] + [AI_LOG_PATH.with_suffix(f".jsonl.{i}") for i in (1, 2, 3)]
        for path in paths:
            remaining = limit - len(entries)
            if remaining <= 0:
                break
            entries = tail(path, remaining) + entries
        current_bytes = AI_LOG_PATH.stat().st_size if AI_LOG_PATH.exists() else 0
    try:
        display_path = str(AI_LOG_PATH.relative_to(ROOT))
    except ValueError:
        display_path = str(AI_LOG_PATH)
    return {"entries": entries[-limit:], "current_bytes": current_bytes,
            "max_bytes": _AI_LOG_MAX_BYTES, "archives": 3,
            "path": display_path}


def set_ai_log_limit(max_mb: int) -> dict:
    global _AI_LOG_MAX_BYTES
    _AI_LOG_MAX_BYTES = max_mb * 1024 * 1024
    with _AI_LOG_LOCK:
        AI_LOG_DIR.mkdir(parents=True, exist_ok=True)
        AI_LOG_CONFIG.write_text(json.dumps({"max_bytes": _AI_LOG_MAX_BYTES}), encoding="utf-8")
        _rotate_ai_log()
    _append_ai_log("system", f"日志轮转阈值设为 {max_mb} MB")
    return ai_log_state(20)


def _live_gauge(frame: int) -> dict:
    """生成同一只固定表盘，仅改变指针位置；用于五分钟演示流。"""
    from PIL import Image, ImageDraw
    size = 640
    img = Image.new("RGB", (size, size), (30, 32, 35))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    radius = 226
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                 fill=(238, 240, 242), outline=(55, 55, 55), width=5)
    for i in range(41):
        angle = math.radians(135 + i * 270 / 40)
        long_tick = i % 5 == 0
        r1 = radius * (0.79 if long_tick else 0.85)
        r2 = radius * 0.93
        draw.line((cx + r1 * math.cos(angle), cy + r1 * math.sin(angle),
                   cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)),
                  fill=(35, 35, 35), width=4 if long_tick else 2)
    for i, label in enumerate(("0", "2", "4", "6", "8", "10")):
        angle = math.radians(135 + i * 54)
        rr = radius * .63
        draw.text((cx + rr * math.cos(angle) - 8, cy + rr * math.sin(angle) - 8),
                  label, fill=(30, 30, 30))
    elapsed = frame / 10
    pressure = 5.0 + .55 * math.sin(elapsed * .35) + .12 * math.sin(elapsed * .9)
    pressure = round(max(0.6, min(9.2, pressure)), 2)
    angle = math.radians(135 + pressure / 10 * 270)
    needle_len = radius * .77
    # 指针由浏览器叠加并做连续补间；底图保持完全稳定。
    draw.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(40, 40, 40))
    draw.text((cx - 22, cy + radius * .46), "bar", fill=(40, 40, 40))
    draw.text((cx - 30, cy - radius * .55), "P-101", fill=(60, 60, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return {"image_b64": base64.b64encode(buf.getvalue()).decode(),
            "reading": {"value": pressure, "unit": "bar", "confidence": .98,
                        "method": "simulation_pointer"},
            "pointer_angle_deg": math.degrees(angle),
            "bbox": [cx - radius, cy - radius, cx + radius, cy + radius]}


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
    values = base["spectrum"] + .28 * np.sin(np.arange(128) / 7.0 + phase * .22)
    values += .08 * np.sin(np.arange(128) / 2.8 - phase * .31)
    feats = dict(base["features"])
    feats["rms"] = float(feats.get("rms", 0) * (1 + .006 * np.sin(phase * .18)))
    feats["crest_factor"] = float(feats.get("crest_factor", 0) + .015 * np.sin(phase * .13))
    return {"features": feats,
            "spectrum": [round(float(v), 2) for v in values],
            "freq_labels": [round(float(v), 1) for v in base["freq_labels"]],
            "level_db": round(-28.0 + .7 * math.sin(elapsed * .42) +
                              .16 * math.sin(elapsed * 1.3), 2),
            "synthetic": True, "frame": int(elapsed * 10),
            "sampled_at": datetime.now(timezone.utc).isoformat()}


def visual() -> dict:
    """固定表盘 + 时间变化指针，避免演示中仪表外观跳变。"""
    frame = int((time.monotonic() - _SIM_STARTED) * 10)
    result = _live_gauge(frame)
    result.update({"synthetic": True, "frame": frame,
                   "sampled_at": datetime.now(timezone.utc).isoformat(),
                   "source": "sensors/live_gauge.py (fixed dial, animated pointer)"})
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


def _current_ai_context() -> tuple[dict, list[dict]]:
    """Collect one current, auditable observation bundle for the local brain."""
    alert_data = alerts()
    visual_data = visual()
    situation_data = situation()
    abnormal = next((x for x in alert_data if x.get("level") != "normal"), alert_data[0])
    reading = visual_data.get("reading", {})
    facts = {
        "acoustic": {"level": abnormal.get("level"), "feature": abnormal.get("top_feature"),
                     "causes": abnormal.get("causes", [])[:2]},
        "gauge": {"value": reading.get("value"), "unit": reading.get("unit"),
                  "confidence": reading.get("confidence")},
        "route": {"level": situation_data["route"].get("level"),
                  "max_xte_m": situation_data["route"].get("max_xte_m")},
        "radar": {"n_targets": len(situation_data["radar"].get("targets", []))},
        "sonar": {"label": situation_data["sonar"].get("label"),
                  "confidence": situation_data["sonar"].get("confidence")},
    }
    evidence = [
        {"label": "声学", "value": f"{abnormal.get('top_feature') or '信号变化'} · {abnormal.get('level')}"},
        {"label": "表盘", "value": f"{reading.get('value', '—')} {reading.get('unit', '')} · {round(float(reading.get('confidence', 0))*100)}%"},
        {"label": "航线", "value": f"横偏 {situation_data['route'].get('max_xte_m', '—')} m"},
        {"label": "雷达", "value": f"检出 {len(situation_data['radar'].get('targets', []))} 个目标"},
    ]
    return facts, evidence


def briefing() -> dict:
    """由 Spark 本地大脑把多路观测压缩为可核对的值班结论。"""
    from fastapi import HTTPException
    from harness.brain import chat
    if not _AI_INFERENCE_LOCK.acquire(blocking=False):
        raise HTTPException(429, "Spark 本地大脑正在处理上一项任务")
    try:
        facts, evidence = _current_ai_context()
        _append_ai_log("observation", "四路合成观测已汇总", evidence=evidence)
        prompt = """你是船端 AI 值班官。只根据给出的合成演示观测做简短研判，不得补充未提供的事实。
输出严格 JSON：{"headline":"不超过18字的结论","summary":"不超过70字的依据概括","action":"不超过55字的建议，必须包含人工复核"}。
不要输出 Markdown，不要描述自己，不要声称已控制设备。观测如下：\n""" + json.dumps(facts, ensure_ascii=False)
        raw = chat([{"role": "user", "content": prompt}], temperature=0.1,
                   max_tokens=240, timeout=60)
        start = raw.find("{")
        if start < 0:
            raise ValueError("未返回 JSON")
        decision, _ = json.JSONDecoder().raw_decode(raw[start:])
        if not all(isinstance(decision.get(k), str) and decision[k].strip()
                   for k in ("headline", "summary", "action")):
            raise ValueError("研判字段不完整")
    except HTTPException:
        raise
    except Exception as exc:
        _append_ai_log("error", f"本轮研判未完成：{type(exc).__name__}")
        raise HTTPException(503, f"Spark 本地大脑暂未完成研判：{type(exc).__name__}")
    finally:
        _AI_INFERENCE_LOCK.release()
    result = {**decision, "evidence": evidence,
            "skills": ["声学哨兵", "视觉巡检", "航线哨兵", "雷达解读"],
            "model": "Qwen3-4B-FP8 · DGX Spark", "synthetic": True,
            "generated_at": datetime.now(timezone.utc).isoformat()}
    _append_ai_log("ai", decision["headline"], summary=decision["summary"],
                   action=decision["action"], model=result["model"])
    result["log"] = ai_log_state(20)
    return result


def ask_duty_officer(question: str) -> dict:
    """Answer an operator question from a fresh observation bundle and persist both sides."""
    from fastapi import HTTPException
    from harness.brain import chat
    if not _AI_INFERENCE_LOCK.acquire(blocking=False):
        raise HTTPException(429, "Spark 本地大脑正在处理上一项任务")
    operator_entry = _append_ai_log("operator", question)
    try:
        facts, evidence = _current_ai_context()
        prompt = """你是船端 AI 值班官。根据当前合成观测回答操作员问题。
要求：中文，不超过120字；先给当前状态，再给依据和建议；涉及处置时必须要求人工复核；不得虚构数据，不得声称已控制设备。
压力观测没有给出正常区间，只能复述读数，不得称为偏高或偏低；雷达检出不等于风险；声呐样本与雷达目标没有关联。
当前观测：""" + json.dumps(facts, ensure_ascii=False) + "\n操作员问题：" + question
        answer = chat([{"role": "user", "content": prompt}], temperature=0.1,
                      max_tokens=260, timeout=60).strip()
        if not answer:
            raise ValueError("回答为空")
        answer = answer.replace("```", "").strip()
        ai_entry = _append_ai_log("ai", answer, model="Qwen3-4B-FP8 · DGX Spark")
        return {"question": question, "answer": answer, "evidence": evidence,
                "model": "Qwen3-4B-FP8 · DGX Spark", "synthetic": True,
                "generated_at": ai_entry["ts"], "entries": [operator_entry, ai_entry],
                "log": ai_log_state(80)}
    except HTTPException:
        raise
    except Exception as exc:
        _append_ai_log("error", f"问答未完成：{type(exc).__name__}")
        raise HTTPException(503, f"Spark 本地大脑暂未回答：{type(exc).__name__}")
    finally:
        _AI_INFERENCE_LOCK.release()


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

    @app.get("/api/briefing")
    def _briefing():
        return briefing()

    @app.post("/api/ai/ask")
    def _ask(payload: AskRequest):
        return ask_duty_officer(payload.question.strip())

    @app.get("/api/ai/logs")
    def _ai_logs(limit: int = Query(default=80, ge=1, le=300)):
        return ai_log_state(limit)

    @app.post("/api/ai/log-config")
    def _ai_log_config(payload: LogConfigRequest):
        return set_ai_log_limit(payload.max_mb)

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
