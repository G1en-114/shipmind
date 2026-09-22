#!/usr/bin/env python3
"""机舱视觉巡检：表盘定位 + 指针读数（经典 CV，确定性可复现）。

两级实现（与 manual-rag-query 同构的分层策略）：
  1. **本地 CV 轨**（当前）：表盘定位（亮度阈值+连通域+径向直方图）→ 指针检测
     （红色优先，否则用径向暗线）→ 角度映射读数。零依赖，对合成表盘数据确定性可复现。
  2. **官方 TAO 轨**（升级）：`tao-generate-image-grounding`（NVIDIA，需 TAO Data Services
     与 vLLM 端点）做开放词汇定位，接微调小 VLM 读数。接口一致，替换不影响调用方。

用法：
    python visual_inspect.py <图片> [--json]
    python visual_inspect.py --eval <目录> --annotations annotations.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def find_dial(gray: np.ndarray) -> tuple[tuple[int, int], int] | None:
    """定位表盘：阈值取亮区 → 质心 → 径向亮度直方图定半径。"""
    thr = np.percentile(gray, 70)
    mask = gray > thr
    if mask.sum() < 500:
        return None
    ys, xs = np.nonzero(mask)
    cx, cy = int(xs.mean()), int(ys.mean())
    # 从质心向外，亮度降到峰值 40% 处视为边缘
    max_r = int(min(gray.shape) / 2) - 2
    radii = np.arange(10, max_r)
    prof = []
    yy, xx = np.mgrid[0:gray.shape[0], 0:gray.shape[1]]
    for r in radii[::4]:
        ring = (np.abs(xx - cx) < r + 4) & (np.abs(xx - cx) >= r - 4) \
            & (np.abs(yy - cy) < r + 4) & (np.abs(yy - cy) >= r - 4)
        prof.append(gray[ring].mean() if ring.any() else 0.0)
    prof = np.array(prof)
    peak = prof.max()
    below = np.nonzero(prof < peak * 0.4)[0]
    r = int(radii[::4][below[0]]) if len(below) else max_r
    return (cx, cy), max(r, 30)


def needle_angle(img: np.ndarray, cx: int, cy: int, r: int) -> tuple[float, float, str]:
    """检测指针角度与置信度。返回 (屏幕坐标角度, 置信度, 方式)。

    角度用**屏幕坐标**（y 向下、0=右、顺时针为正）——与表盘扫掠 135°→405° 的
    定义一致；若转成数学坐标（y 向上）会把方向搞反。
    """
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx - cx, yy - cy
    dist = np.hypot(dx, dy)
    # 只在中环（避开中心轴盖与外圈刻度）找指针
    band = (dist > r * 0.30) & (dist < r * 0.78)

    red = (img[:, :, 0] > 140) & (img[:, :, 1] < 100) & (img[:, :, 2] < 100) & band
    if red.sum() >= 8:
        ys, xs = np.nonzero(red)
        # 取离中心最远的若干点定方向（指针尖端）
        d = np.hypot(xs - cx, ys - cy)
        far = d >= np.percentile(d, 80)
        ang = np.degrees(np.arctan2((ys[far] - cy).mean(), (xs[far] - cx).mean()))
        conf = min(0.95, red.sum() / 60.0)
        return ang % 360, round(conf, 2), "red_needle"

    # 黑指针：沿各角度在中环上数暗像素，指针是粗径向线，其角度桶计数最高
    gray = img.mean(axis=2)
    band_vals = gray[band]
    if band_vals.size >= 50:
        dark_thr = np.percentile(band_vals, 10)
        dark = (gray < dark_thr) & band
        if dark.sum() >= 8:
            ys, xs = np.nonzero(dark)
            ang_pix = np.degrees(np.arctan2(ys - cy, xs - cx)) % 360
            hist, _ = np.histogram(ang_pix, bins=360, range=(0, 360))
            best = int(np.argmax(hist))
            peak = hist[best]
            # 显著性过滤：指针应是明显凸出的径向结构；噪声/污渍的直方图是平的。
            # 不显著时判 unreadable，而不是猜一个方向（模糊必须拒判，禁止猜测）
            nonzero = hist[hist > 0]
            median = float(np.median(nonzero)) if nonzero.size else 0.0
            if peak >= max(6.0, 2.5 * median):
                lo, hi = (best - 3) % 360, (best + 4) % 360
                sel = (ang_pix >= lo) | (ang_pix <= hi) if lo > hi else \
                      ((ang_pix >= lo) & (ang_pix <= hi))
                if sel.sum() >= 4:
                    ang = float(ang_pix[sel].mean())
                    # 双峰歧义检测：若非指针区还存在与主峰相当的第二径向结构
                    # （≈180° 对侧的刻度线被误当指针），读数方向不可信 → 拒判
                    second = hist.copy()
                    second[sel if False else np.zeros(len(second), dtype=bool)] = 0
                    for k in range(6):
                        for off in ((best + k) % 360, (best - k) % 360):
                            second[off] = 0
                    others = second[second > 0]
                    if others.size and float(others.max()) > 0.5 * peak:
                        return 0.0, 0.0, "ambiguous"
                    return ang % 360, 0.55, "dark_needle"

    return 0.0, 0.0, "none"


def angle_to_fraction(angle: float) -> float:
    """屏幕坐标角度 → 归一化读数（0–1）。表盘扫掠 135°→405°。"""
    return ((angle - 135.0) % 360.0) / 270.0


def fraction_to_reading(frac: float, max_pressure: float) -> float:
    return round(frac * max_pressure, 2)


def inspect(path: Path, max_pressure: float | None = 40.0) -> dict:
    try:
        img = np.asarray(Image.open(path).convert("RGB"))
    except Exception as exc:
        return {"file": str(path), "readings": [], "note": f"无法读取图像: {exc}"}
    gray = img.mean(axis=2)
    dial = find_dial(gray)
    if dial is None:
        return {"file": path.name, "readings": [], "note": "未定位到表盘"}
    (cx, cy), r = dial
    ang, conf, how = needle_angle(img, cx, cy, r)
    if how == "none" or conf < 0.2:
        return {"file": path.name,
                "readings": [{"device": f"gauge@{cx},{cy}", "value": "unreadable",
                              "fraction": None,
                              "bbox": [cx - r, cy - r, cx + r, cy + r],
                              "confidence": round(conf, 2)}],
                "note": "指针检测失败，标为 unreadable（禁止猜测数值）"}
    frac = round(angle_to_fraction(ang), 4)
    rec = {"device": f"gauge@{cx},{cy}", "fraction": frac,
           "unit": "bar", "max_pressure": max_pressure,
           "bbox": [cx - r, cy - r, cx + r, cy + r],
           "confidence": conf, "needle_angle_deg": round(ang, 1), "method": how}
    # 量程未知时只给 fraction（绝对读数需量程：配置提供或 VLM 轨读表盘数字）
    rec["value"] = (fraction_to_reading(frac, max_pressure)
                    if max_pressure else None)
    return {"file": path.name, "readings": [rec]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?")
    ap.add_argument("--max-pressure", type=float, default=40.0)
    ap.add_argument("--eval-dir", help="评测目录（配 annotations.json）")
    ap.add_argument("--annotations", default="annotations.json")
    args = ap.parse_args()

    if args.eval_dir:
        d = Path(args.eval_dir)
        ann = json.loads((d / args.annotations).read_text(encoding="utf-8"))
        truth = {r["file"].split("/")[-1]: r for r in ann["records"]}
        ferr, n, by_method, rejected = [], 0, {}, 0
        for f in sorted(d.glob("train/*.jpg"))[:60] + sorted(d.glob("val/*.jpg"))[:20]:
            r = inspect(f)
            t = truth.get(f.name)
            if t is None or not r["readings"]:
                continue
            rec = r["readings"][0]
            if rec.get("fraction") is None:
                rejected += 1
                continue
            n += 1
            true_frac = float(t["reading"]) / float(t["max_pressure"])
            ferr.append(abs(rec["fraction"] - true_frac))
            m = rec.get("method", "?")
            by_method.setdefault(m, []).append(abs(rec["fraction"] - true_frac))
        if not n:
            print(json.dumps({"error": "无可评样本"}, ensure_ascii=False))
            return 2
        ferr = np.array(ferr)
        out = {"n": n, "n_rejected": rejected,
               "frac_mae": round(float(ferr.mean()), 4),
               "frac_within_2pct": round(float((ferr < 0.02).mean()), 3),
               "frac_max_err": round(float(ferr.max()), 3)}
        for m, es in by_method.items():
            out[f"frac_mae_{m}"] = round(float(np.mean(es)), 4)
            out[f"n_{m}"] = len(es)
        print(json.dumps(out, ensure_ascii=False))
        return 0

    if not args.image:
        ap.error("需要提供 image，或使用 --eval-dir")
    out = inspect(Path(args.image), args.max_pressure)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"MEDIA:{Path(args.image).resolve()}")
    # 无读数（未定位表盘 / 无法读取图像）→ 拒绝，与其他 Skill 的 rc=2 约定一致
    return 0 if out.get("readings") else 2


if __name__ == "__main__":
    raise SystemExit(main())
