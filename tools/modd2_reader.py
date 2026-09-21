#!/usr/bin/env python3
"""MODD2 标注读取器：.mat → JSON（sea_edge 折线 + obstacles 边界框）。

MODD2（Multi-modal Obstacle Detection Dataset 2）来自真实 USV 拍摄，
公开下载（box.vicos.si/borja/modd2_dataset/），标注为 MATLAB .mat 格式。

用法：
    python tools/modd2_reader.py --root D:\\datasets\\modd2 --seq kope67-00-00004500-00005050
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import scipy.io as sio


def read_frame(mat_path: Path) -> dict:
    d = sio.loadmat(mat_path)["annotations"][0, 0]
    out: dict = {"frame": mat_path.stem, "sea_edge": None, "obstacles": []}

    se = d["sea_edge"]
    if se.size:
        arr = se[0] if se.dtype == object else se
        if hasattr(arr, "shape") and arr.size:
            out["sea_edge"] = np.asarray(arr, dtype=float).reshape(-1, 2).tolist()

    ob = d["obstacles"]
    if ob.size:
        for i in range(ob.shape[1] if ob.ndim > 1 else ob.size):
            o = ob[0, i] if ob.ndim > 1 else ob[i]
            if not hasattr(o, "dtype") or o.dtype.names is None:
                continue
            rec = {}
            for name in o.dtype.names:
                v = np.asarray(o[name])
                rec[name] = v.ravel().tolist()
            out["obstacles"].append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="MODD2 解压根目录（含 annotations/video）")
    ap.add_argument("--seq", help="序列名（如 kope67-00-00004500-00005050）；缺省列全部")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    root = Path(args.root)
    gt_root = root / "annotations" / "annotationsV2_rectified"
    seqs = [args.seq] if args.seq else sorted(p.name for p in gt_root.iterdir())
    print(json.dumps({"sequences": len(seqs), "names": seqs[:5]}, ensure_ascii=False))

    for s in seqs[:1]:
        mats = sorted((gt_root / s / "ground_truth").glob("*.mat"))
        print(json.dumps({"seq": s, "frames": len(mats)}, ensure_ascii=False))
        for m in mats[: args.limit]:
            r = read_frame(m)
            print(json.dumps({"frame": r["frame"],
                              "sea_edge_pts": len(r["sea_edge"]) if r["sea_edge"] else 0,
                              "obstacles": len(r["obstacles"]),
                              "obstacle_keys": list(r["obstacles"][0].keys()) if r["obstacles"] else []},
                             ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
