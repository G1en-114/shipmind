---
name: route-deviation-watch
description: 航线偏离哨兵。当需要判断本船是否偏离计划航线（waypoint 走廊）、计算横偏距离 XTE、或评估与目标船的最近会遇距离 CPA/TCPA 时使用。触发词：航线、偏航、偏离、XTE、走廊、航路点、会遇、CPA、TCPA、船位。不适用于：机舱音频分析（用 engine-room-acoustic-sentinel）、手册条文查询（用 manual-rag-query）、无 NMEA 输入的任务。
version: 0.1.0
triggers: 航线,偏航,偏离,XTE,走廊,航路点,会遇,CPA,TCPA,船位,偏出航线
negative-triggers: 机舱音频,声纹,雷达目标检测,手册查询,仪表读数
entry: scripts/route_watch.py
---

# 航线偏离哨兵（确定性模块，零容差评测）

从 NMEA 0183 轨迹对照计划航线，输出越限分级与（可选）CPA/TCPA。纯确定性计算，评测用精确断言。

## 前置提问（缺失必须先问，禁止猜测）

1. **NMEA 轨迹文件**：RMC/GGA 句（AIS 模拟流亦可）。
2. **计划航线**：waypoint 序列 + 走廊半宽（米）。
3. （可选）**目标船轨迹**：提供后输出 CPA/TCPA。

## 执行流程

1. 解析 RMC 有效定位（status=A）；有效定位 < 3 → `rejected`。
2. 对每个船位取各航段横向偏移的最小绝对值（球面公式）。
3. 分级：`max_xte < 0.5×走廊` → normal；`< 1×走廊` → watch；否则 alarm。
4. 若给目标轨迹：直线运动模型求 CPA/TCPA；TCPA ≤ 0 标注"正在远离"。
5. 输出契约 JSON，末尾 `MEDIA:<轨迹文件绝对路径>`。

## 禁止行为

- 走廊半宽未提供时禁止使用默认值硬算，必须先问。
- 定位跳变（相邻两点距离 > 航速允许）必须标注 anomaly，不得静默平滑。

## 输出契约

```json
{
  "level": "normal|watch|alarm",
  "max_xte_m": 0.0,
  "corridor_half_width_m": 1852,
  "n_fixes": 100,
  "worst_fix": [122.3, 31.01],
  "cpa_m": 1500.0, "tcpa_s": 600.0
}
```
