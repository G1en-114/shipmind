---
name: engine-room-visual-inspector
description: 机舱视觉巡检。当需要从视频/图片中识别仪表读数与设备状态（压力表、温度表、液位计、运行指示灯）并与声学证据交叉确认时使用。触发词：仪表、读数、视频巡检、看一眼、设备状态、表盘、压力表。不适用于：纯音频任务（用 engine-room-acoustic-sentinel）、无图像输入的任务。
version: 0.1.0
entry: scripts/visual_inspect.py
---

# 机舱视觉巡检（D4 交付）

## 执行流程（规划）

1. 抽帧（DeepStream 管线 / ffmpeg）
2. `tao-generate-image-grounding`（官方 Skill，保持原样）定位表盘与设备部件
3. 小 VLM 读数识别（TAO/NeMo 微调，见 PROJECT-PLAN §5）
4. 与声学证据交叉确认（同源时间戳）
5. 输出带框截图 + 读数表

## 禁止行为

- 读数模糊时必须输出 `unreadable`，禁止猜测数值。
- 表盘定位缺失时禁止"全图猜读"。

## 输出契约（规划）

```json
{"readings": [{"device": "pressure_gauge_01", "value": 4.2, "unit": "bar",
               "bbox": [x1, y1, x2, y2], "confidence": 0.9}]}
```
