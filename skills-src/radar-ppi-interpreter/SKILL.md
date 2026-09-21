---
name: radar-ppi-interpreter
description: 民用雷达 PPI 解读。当需要从雷达平面位置显示（PPI）回波场中检测目标、输出目标方位/距离/相对航向、或评估碰撞趋势（配合 CPA/TCPA）时使用。数据为合成 PPI（数据即仿真）。触发词：雷达、目标、PPI、回波、态势、方位、检测。不适用于：音频任务（用 sonar-acoustic-fingerprint 或 engine-room-acoustic-sentinel）、航线走廊判定本身（用 route-deviation-watch）。
version: 0.1.0
entry: scripts/ppi_detect.py
---

# 雷达 PPI 解读（合成数据 + 经典 CV）

极坐标回波场（方位 × 距离）→ 噪声底估计 → 阈值分割 → 连通域聚类 → 目标列表。合成器与检测器配套，检测参数全部输出供 verifier 复核。

## 前置提问（缺失必须先问，禁止猜测）

1. **PPI 回波场**：`.npy`（方位×距离，由 `ppi_synth.py` 生成或相同约定渲染）。
2. **量程**：最大距离（米），用于把距离 bin 换算回米。

## 执行流程

1. 估计噪声底（全场景 mean/std）。
2. 阈值 `mean + 8σ` 分割，4-连通域聚类。
3. 簇内单元数 < 4 判为杂波丢弃（抗虚警）。
4. 输出目标方位（deg）、距离（m）、簇大小、峰值 SNR、置信度。

## 禁止行为

- 空海面场景不得输出虚警目标（负向用例零容忍）。
- 禁止把杂波簇报成目标；置信度必须附峰值 SNR 供复核。
- 结论必须标注"合成 PPI 数据"，禁止暗示真实雷达。

## 输出契约

```json
{
  "targets": [{"bearing_deg": 45.0, "range_m": 3000, "cells": 24, "peak_snr": 18.2, "confidence": 0.73}],
  "n_targets": 1
}
```
