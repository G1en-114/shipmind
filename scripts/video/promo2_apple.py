#!/usr/bin/env python3
"""Render ShipMind promo two in a restrained Apple-like product-film language."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / "scripts/video/promo2_apple_timeline.json").read_text(encoding="utf-8"))
W, H = 1920, 1080
INK = (29, 29, 31)
MUTED = (110, 110, 115)
PAPER = (247, 247, 249)
BLUE = (0, 113, 227)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)


F_TITLE = font(82, True)
F_HERO = font(104, True)
F_BODY = font(30)
F_SMALL = font(21)
F_LABEL = font(18, True)


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 4


def smoothstep(a: float, b: float, x: float) -> float:
    if a == b:
        return float(x >= b)
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def fit(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    out = im.copy()
    out.thumbnail(size, Image.Resampling.LANCZOS)
    return out


def rgba(path: str) -> Image.Image:
    return Image.open(ROOT / path).convert("RGBA")


SPARK = rgba("scripts/video/assets/gen/dgx-spark-clean-v1.png")
OVERVIEW = rgba("runs/ui-review/spark-5min.png")
AI = rgba("runs/ui-review/spark-ai-desktop.png")
DARK = rgba("runs/ui-review/dark-mode-desktop-final.png")


def base(color=PAPER) -> Image.Image:
    return Image.new("RGBA", (W, H), (*color, 255))


def text_center(im: Image.Image, text: str, y: int, face: ImageFont.FreeTypeFont, fill=INK, alpha=255, spacing=12) -> None:
    layer = Image.new("RGBA", im.size)
    draw = ImageDraw.Draw(layer)
    box = draw.multiline_textbbox((0, 0), text, font=face, spacing=spacing, align="center")
    x = (W - (box[2] - box[0])) // 2
    draw.multiline_text((x, y), text, font=face, fill=(*fill, alpha), spacing=spacing, align="center")
    im.alpha_composite(layer)


def text_left(im: Image.Image, text: str, xy: tuple[int, int], face: ImageFont.FreeTypeFont, fill=INK, alpha=255, spacing=12) -> None:
    layer = Image.new("RGBA", im.size)
    ImageDraw.Draw(layer).multiline_text(xy, text, font=face, fill=(*fill, alpha), spacing=spacing)
    im.alpha_composite(layer)


def paste_shadow(im: Image.Image, obj: Image.Image, xy: tuple[int, int], blur=35, opacity=65, offset=(0, 24)) -> None:
    shadow = Image.new("RGBA", im.size)
    alpha = obj.getchannel("A").point(lambda p: p * opacity // 255)
    silhouette = Image.new("RGBA", obj.size, (0, 0, 0, 0))
    silhouette.putalpha(alpha)
    shadow.alpha_composite(silhouette, (xy[0] + offset[0], xy[1] + offset[1]))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(shadow)
    im.alpha_composite(obj, xy)


def screen(im: Image.Image, shot: Image.Image, box: tuple[int, int, int, int], radius=26, alpha=255, angle=0.0) -> None:
    x, y, w, h = box
    src = shot.copy()
    ratio = max(w / src.width, h / src.height)
    src = src.resize((round(src.width * ratio), round(src.height * ratio)), Image.Resampling.LANCZOS)
    left = (src.width - w) // 2
    top = (src.height - h) // 2
    src = src.crop((left, top, left + w, top + h))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=alpha)
    src.putalpha(mask)
    if angle:
        src = src.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        x -= (src.width - w) // 2
        y -= (src.height - h) // 2
    paste_shadow(im, src, (x, y), blur=30, opacity=56, offset=(0, 22))


def crop_tile(src: Image.Image, crop: tuple[float, float, float, float], size: tuple[int, int]) -> Image.Image:
    l, t, r, b = crop
    region = src.crop((round(src.width * l), round(src.height * t), round(src.width * r), round(src.height * b)))
    return region.resize(size, Image.Resampling.LANCZOS)


def scene_signal(t: float, d: float) -> Image.Image:
    im = base()
    p = ease(t / 1.2)
    y = round(335 + 28 * (1 - p))
    text_center(im, "船上发生的一切，\n都从信号开始。", y, F_HERO, alpha=round(255 * p), spacing=18)
    q = smoothstep(1.3, 2.6, t)
    text_center(im, "SHIPMIND · ONBOARD INTELLIGENCE", 625, F_LABEL, MUTED, round(255 * q))
    # A single live signal line gives the otherwise quiet opening a pulse.
    line = Image.new("RGBA", im.size)
    draw = ImageDraw.Draw(line)
    width = round(620 * smoothstep(2.0, 4.0, t))
    x0 = W // 2 - width // 2
    pts = []
    for x in range(width + 1):
        phase = x / 38 - t * 2.8
        amp = 4 + 26 * math.exp(-((x - width * 0.54) / max(1, width * 0.08)) ** 2)
        pts.append((x0 + x, 770 + math.sin(phase) * amp))
    if len(pts) > 1:
        draw.line(pts, fill=(*BLUE, 205), width=3)
    im.alpha_composite(line)
    return im


def scene_spark(t: float, d: float) -> Image.Image:
    im = base()
    p = ease(t / 1.15)
    text_left(im, "一台设备。\n守住一条航线。", (150, 220), F_TITLE, alpha=round(255 * p), spacing=16)
    text_left(im, "船端本地推理 · 断网仍可演示核心流程", (156, 445), F_BODY, MUTED, round(255 * smoothstep(.8, 1.8, t)))
    text_left(im, "Powered locally by NVIDIA DGX Spark", (158, 510), F_SMALL, BLUE, round(255 * smoothstep(1.1, 2.1, t)))
    scale = 0.58 + 0.05 * ease(t / d)
    obj = SPARK.resize((round(SPARK.width * scale), round(SPARK.height * scale)), Image.Resampling.LANCZOS)
    x = round(965 + 70 * (1 - p))
    y = round(245 + math.sin(t * 0.72) * 7)
    paste_shadow(im, obj, (x, y), blur=42, opacity=72, offset=(0, 34))
    return im


def scene_overview(t: float, d: float) -> Image.Image:
    im = base()
    p = ease(t / 1.0)
    text_center(im, "每一种观测，汇成一张清晰值班图。", 115, F_TITLE, alpha=round(255 * p))
    text_center(im, "同一时间轴。相同来源。可追溯的变化。", 235, F_BODY, MUTED, round(255 * smoothstep(.55, 1.5, t)))
    w = round(1460 + 50 * ease(t / d))
    h = round(w * 0.54)
    x = (W - w) // 2
    y = round(365 + 34 * (1 - p) + math.sin(t * .5) * 3)
    screen(im, OVERVIEW, (x, y, w, h), radius=28, alpha=round(255 * p), angle=-0.35)
    return im


def scene_signals(t: float, d: float) -> Image.Image:
    im = base()
    p = ease(t / 1.0)
    text_center(im, "声学。表盘。雷达。航线。", 108, F_TITLE, alpha=round(255 * p))
    text_center(im, "同步被看见。", 222, F_BODY, BLUE, round(255 * smoothstep(.65, 1.5, t)))
    labels = [("声学频谱", "连续纸带"), ("表盘读数", "5.38 bar"), ("雷达态势", "02 个目标"), ("航线变化", "偏移 17.8 m")]
    boxes = [(125, 390, 780, 270), (985, 390, 780, 270), (125, 720, 780, 250), (985, 720, 780, 250)]
    for i, ((label, value), (x, y, w, h)) in enumerate(zip(labels, boxes)):
        q = ease((t - .35 * i) / 1.15)
        yy = round(y + 30 * (1 - q))
        tile = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        td = ImageDraw.Draw(tile)
        td.rounded_rectangle((1, 1, w - 2, h - 2), radius=24, fill=(255, 255, 255, round(255 * q)), outline=(229, 229, 234, round(255 * q)), width=2)
        td.text((28, 24), label, font=F_SMALL, fill=(*INK, round(255 * q)))
        td.text((w - 28, 27), value, font=F_LABEL, anchor="ra", fill=(*MUTED, round(255 * q)))
        if i == 0:
            pts = []
            for xx in range(35, w - 35, 3):
                amp = 12 + 45 * math.exp(-((xx - w * .56) / (w * .10)) ** 2)
                pts.append((xx, h * .63 + math.sin(xx / 19 + t * 4) * amp))
            td.line(pts, fill=(*BLUE, round(230 * q)), width=4)
            td.line((35, h * .63, w - 35, h * .63), fill=(210, 220, 232, round(170 * q)), width=1)
        elif i == 1:
            cx, cy, rr = 150, 158, 76
            td.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(210, 214, 220, round(255 * q)), width=8)
            angle = -1.0 + math.sin(t * .7) * .08
            td.line((cx, cy, cx + math.cos(angle) * 60, cy + math.sin(angle) * 60), fill=(255, 69, 58, round(255 * q)), width=5)
            td.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(*INK, round(255 * q)))
            td.text((285, 120), "5.38", font=font(58, True), fill=(*BLUE, round(255 * q)))
            td.text((435, 153), "bar", font=F_SMALL, fill=(*MUTED, round(255 * q)))
        elif i == 2:
            cx, cy = w // 2, 145
            for rr in (45, 82, 118):
                td.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(202, 218, 238, round(190 * q)), width=2)
            for a in (0, math.pi / 2):
                td.line((cx - math.cos(a) * 128, cy - math.sin(a) * 128, cx + math.cos(a) * 128, cy + math.sin(a) * 128), fill=(215, 224, 235, round(170 * q)), width=1)
            for dx, dy in ((55, -38), (-82, 63)):
                td.ellipse((cx + dx - 7, cy + dy - 7, cx + dx + 7, cy + dy + 7), fill=(255, 149, 0, round(255 * q)))
            sweep = -1.5 + t * .45
            td.line((cx, cy, cx + math.cos(sweep) * 120, cy + math.sin(sweep) * 120), fill=(*BLUE, round(220 * q)), width=4)
        else:
            pts = [(45, 185), (170, 158), (310, 170), (445, 105), (600, 124), (730, 76)]
            td.line(pts, fill=(*BLUE, round(235 * q)), width=5, joint="curve")
            for px, py in pts:
                td.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(*BLUE, round(255 * q)))
            sx, sy = pts[-1]
            td.polygon(((sx + 12, sy), (sx - 12, sy - 9), (sx - 8, sy + 12)), fill=(*INK, round(255 * q)))
        paste_shadow(im, tile, (x, yy), blur=22, opacity=32, offset=(0, 15))
    return im


def scene_ask(t: float, d: float) -> Image.Image:
    im = base((8, 9, 12))
    p = ease(t / 1.0)
    text_left(im, "直接问：\n现在怎么样？", (140, 175), F_TITLE, (245, 245, 247), round(255 * p), spacing=16)
    text_left(im, "本地 AI 引用证据，\n给出检查建议。", (148, 435), F_BODY, (166, 166, 174), round(255 * smoothstep(.7, 1.6, t)), spacing=10)
    text_left(im, "回答不替代值班判断", (148, 575), F_SMALL, (90, 170, 255), round(255 * smoothstep(1.1, 2.0, t)))
    w, h = 1120, 725
    x = round(720 + 60 * (1 - p))
    y = round(185 + math.sin(t * .55) * 4)
    screen(im, AI, (x, y, w, h), radius=28, alpha=round(255 * p), angle=.45)
    return im


def scene_local(t: float, d: float) -> Image.Image:
    im = base()
    p = ease(t / 1.0)
    text_center(im, "计算留在船上。", 92, F_TITLE, alpha=round(255 * p))
    text_center(im, "关键判断，交给人。", 205, F_BODY, MUTED, round(255 * smoothstep(.6, 1.5, t)))
    obj = SPARK.resize((670, round(SPARK.height * 670 / SPARK.width)), Image.Resampling.LANCZOS)
    ox, oy = (W - obj.width) // 2, 455
    # Four clean data paths converge once, giving the scene one authored motion.
    layer = Image.new("RGBA", im.size)
    draw = ImageDraw.Draw(layer)
    endpoints = [(130, 430), (130, 760), (1790, 430), (1790, 760)]
    labels = ["ACOUSTIC", "GAUGE", "RADAR", "ROUTE"]
    for i, ((sx, sy), label) in enumerate(zip(endpoints, labels)):
        q = ease((t - .35 - i * .12) / 1.4)
        tx, ty = W // 2 + (-170 if sx < W // 2 else 170), 665
        ex, ey = sx + (tx - sx) * q, sy + (ty - sy) * q
        draw.line((sx, sy, ex, ey), fill=(*BLUE, round(130 * q)), width=3)
        draw.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), fill=(*BLUE, round(230 * q)))
        tw = draw.textbbox((0, 0), label, font=F_LABEL)[2]
        draw.text((sx - tw // 2, sy + (22 if sy < 600 else -44)), label, font=F_LABEL, fill=(*MUTED, round(255 * q)))
    im.alpha_composite(layer)
    paste_shadow(im, obj, (ox, oy), blur=40, opacity=65, offset=(0, 30))
    return im


def scene_close(t: float, d: float) -> Image.Image:
    im = base((8, 9, 12))
    p = ease(t / .9)
    text_center(im, "ShipMind", 330, F_HERO, (245, 245, 247), round(255 * p))
    text_center(im, "让信号被看见。让判断更从容。", 505, F_BODY, (176, 176, 184), round(255 * smoothstep(.55, 1.45, t)))
    line = Image.new("RGBA", im.size)
    draw = ImageDraw.Draw(line)
    width = round(420 * smoothstep(1.2, 2.7, t))
    draw.rounded_rectangle((W // 2 - width // 2, 650, W // 2 + width // 2, 654), radius=2, fill=(*BLUE, 220))
    im.alpha_composite(line)
    text_center(im, "LOCAL AI FOR EVERY WATCH", 710, F_LABEL, (110, 170, 235), round(255 * smoothstep(1.4, 2.8, t)))
    return im


SCENES = {
    "signal": scene_signal,
    "spark": scene_spark,
    "overview": scene_overview,
    "signals": scene_signals,
    "ask": scene_ask,
    "local": scene_local,
    "close": scene_close,
}


def render_at(t: float) -> Image.Image:
    scene = CFG["scenes"][-1]
    index = len(CFG["scenes"]) - 1
    for i, candidate in enumerate(CFG["scenes"]):
        if candidate["start"] <= t < candidate["end"]:
            scene = candidate
            index = i
            break
    local = t - scene["start"]
    current = SCENES[scene["id"]](local, scene["end"] - scene["start"])
    remaining = scene["end"] - t
    if index < len(CFG["scenes"]) - 1 and remaining < .52:
        nxt = CFG["scenes"][index + 1]
        progress = smoothstep(.52, 0, remaining)
        incoming = SCENES[nxt["id"]](.52 - remaining, nxt["end"] - nxt["start"])
        return Image.blend(current, incoming, progress)
    return current


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("stills", "preview", "full"), default="stills")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    out_dir = ROOT / "runs/delivery/video"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "stills":
        target = out_dir / "shipmind-promo2-apple-stills"
        target.mkdir(parents=True, exist_ok=True)
        for i, scene in enumerate(CFG["scenes"], 1):
            t = scene["start"] + (scene["end"] - scene["start"]) * .58
            render_at(t).convert("RGB").save(target / f"{i:02d}-{scene['id']}.jpg", quality=94)
        print(target)
        return
    duration = 14 if args.mode == "preview" else CFG["duration_s"]
    output = args.output or out_dir / ("shipmind-promo2-apple-preview-v1.mp4" if args.mode == "preview" else "shipmind-promo2-apple-v1-silent.mp4")
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), CFG["fps"], (W, H))
    for frame in range(round(duration * CFG["fps"])):
        source_t = frame / CFG["fps"] * (CFG["duration_s"] / duration)
        rgb = np.asarray(render_at(source_t).convert("RGB"))
        writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    writer.release()
    print(output)


if __name__ == "__main__":
    main()
