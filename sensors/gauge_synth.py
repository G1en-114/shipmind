#!/usr/bin/env python3
"""模拟表盘合成器：生成带精确读数标签的仪表图像（PIL，零外部数据依赖）。

许可最干净（自产）、标签零成本（渲染时已知）、数量无限；与 PPI 合成器同属
"sensor simulation layer"。输出 COCO 风格 bbox + 精确读数，供 visual-inspector
微调与 evals 使用。

脏污/眩光/遮挡参数化，逼近机舱真实成像条件。
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def draw_gauge(rng: random.Random, size: int = 640) -> tuple[Image.Image, dict]:
    """画一只圆形压力表，返回 (图像, 标注)。"""
    img = Image.new("RGB", (size, size), (28, 30, 34))
    d = ImageDraw.Draw(img)
    cx = cy = size // 2
    r = int(size * rng.uniform(0.34, 0.42))

    # 表盘背景（做旧金属/塑料）
    face = rng.choice([(238, 240, 242), (226, 228, 230), (245, 243, 235), (210, 214, 218)])
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=face, outline=(60, 60, 60), width=4)

    # 刻度：0 ~ max_pressure
    max_p = rng.choice([10, 16, 25, 40, 60])
    n_ticks = rng.choice([20, 25, 40])
    for i in range(n_ticks + 1):
        ang = math.radians(135 + i * (270 / n_ticks))
        long_t = i % 5 == 0
        r1 = r * (0.80 if long_t else 0.86)
        r2 = r * 0.93
        w = 4 if long_t else 2
        d.line([cx + r1 * math.cos(ang), cy + r1 * math.sin(ang),
                cx + r2 * math.cos(ang), cy + r2 * math.sin(ang)],
               fill=(30, 30, 30), width=w)

    # 数字标注（每 5 格一个）
    step = max_p / n_ticks
    for i in range(0, n_ticks + 1, 5):
        ang = math.radians(135 + i * (270 / n_ticks))
        rr = r * 0.66
        x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        d.text((x - 8, y - 8), f"{i * step:g}", fill=(20, 20, 20))

    # 指针（真实读数）
    reading = round(rng.uniform(0.08, 0.95) * max_p, 2)
    frac = reading / max_p
    ang = math.radians(135 + frac * 270)
    nl = r * 0.78
    d.line([cx, cy, cx + nl * math.cos(ang), cy + nl * math.sin(ang)],
           fill=rng.choice([(200, 30, 30), (20, 20, 20)]), width=6)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(40, 40, 40))

    # 单位与编号文字
    d.text((cx - 20, cy + r * 0.45), rng.choice(["bar", "MPa", "kPa"]), fill=(40, 40, 40))
    d.text((cx - 28, cy - r * 0.55), f"P-{rng.randint(100, 999)}", fill=(60, 60, 60))

    ann = {
        "bbox_xyxy": [cx - r, cy - r, cx + r, cy + r],
        "reading": reading,
        "unit": "bar",
        "max_pressure": max_p,
        "gauge_type": "pressure",
    }
    return img, ann


def degrade(img: Image.Image, rng: random.Random) -> Image.Image:
    """机舱成像退化：模糊/噪声/眩光/油污/暗角/遮挡。"""
    w, h = img.size
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 2.2)))
    arr = np.asarray(img).astype(np.float32)
    if rng.random() < 0.7:  # 传感器噪声
        arr += np.random.default_rng(rng.randrange(1 << 30)).normal(
            0, rng.uniform(3, 14), arr.shape)
    if rng.random() < 0.5:  # 亮度/对比度
        arr = arr * rng.uniform(0.55, 1.15) + rng.uniform(-25, 25)
    if rng.random() < 0.4:  # 眩光
        gx, gy = rng.randint(0, w), rng.randint(0, h)
        yy, xx = np.mgrid[0:h, 0:w]
        g = np.exp(-(((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * (w * 0.28) ** 2)))
        arr += (g * rng.uniform(40, 110))[..., None]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    if rng.random() < 0.35:  # 油污斑块
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(rng.randint(1, 4)):
            bx, by = rng.randint(0, w), rng.randint(0, h)
            br = rng.randint(20, 90)
            d.ellipse([bx - br, by - br, bx + br, by + br],
                      fill=(40, 32, 20, rng.randint(25, 70)))
    if rng.random() < 0.25:  # 部分遮挡（管线/电缆）
        d = ImageDraw.Draw(img)
        y0 = rng.randint(0, h)
        d.rectangle([0, y0, w, y0 + rng.randint(15, 70)], fill=(35, 38, 42))
    return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="evals/fixtures/gauges")
    ap.add_argument("--n-train", type=int, default=200)
    ap.add_argument("--n-val", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--size", type=int, default=640)
    args = ap.parse_args()

    out = Path(args.out)
    records = []
    for split, n in (("train", args.n_train), ("val", args.n_val)):
        (out / split).mkdir(parents=True, exist_ok=True)
        rng = random.Random(args.seed + (0 if split == "train" else 1000))
        for i in range(n):
            img, ann = draw_gauge(rng, args.size)
            img = degrade(img, rng)
            name = f"{split}_{i:05d}.jpg"
            img.save(out / split / name, quality=88)
            records.append({
                "split": split, "file": f"{split}/{name}",
                "bbox_xyxy": ann["bbox_xyxy"], "reading": ann["reading"],
                "unit": ann["unit"], "max_pressure": ann["max_pressure"],
            })
    (out / "annotations.json").write_text(json.dumps(
        {"n": len(records), "records": records}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(json.dumps({"out": str(out), "n_records": len(records)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
