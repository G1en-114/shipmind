---
name: engine-room-visual-inspector
description: 机舱视觉巡检。当需要从视频/图片中识别仪表读数与设备状态（压力表、温度表、液位计、运行指示灯）并与声学证据交叉确认时使用。触发词：仪表、读数、视频巡检、看一眼、设备状态、表盘、压力表、看一眼现场。不适用于：纯音频任务（用 engine-room-acoustic-sentinel）、无图像输入的任务。
version: 0.1.0
entry: scripts/visual_inspect.py
---

# 机舱视觉巡检

## 两级实现（与 manual-rag-query 同构）

1. **本地 CV 轨**（当前）：表盘定位（亮度阈值 + 连通域 + 径向亮度直方图）→ 指针检测
   （红色指针优先取尖端方向；黑指针用中环角度直方图 + 显著性过滤）→ 屏幕坐标角度
   → 归一化读数。零第三方依赖，对合成表盘数据确定性可复现。
2. **官方 TAO 轨**（升级）：`tao-generate-image-grounding`（NVIDIA，需 TAO Data Services
   与本地 vLLM 端点）做开放词汇定位，接 TAO/NeMo 微调小 VLM 读数与表盘量程识别。
   接口一致，替换不影响调用方。

## 量程处理（关键设计）

CV 轨输出**归一化读数 `fraction`（0–1）**——绝对读数需要表盘量程，而量程来自：
表盘印刷数字（由 VLM 轨读取）或设备台账配置。量程未知时 `value` 为 null，
**禁止假设量程换算**。

## 执行流程

1. 定位表盘（未定位 → 返回空 readings + note）
2. 检测指针（红/黑两路；角度直方图不显著 → unreadable）
3. 输出 bbox + fraction + 置信度 + 检测方式

## 禁止行为

- 指针检测失败必须输出 `unreadable`，**禁止猜测数值**
- 量程未知时禁止给绝对读数
- 表盘定位缺失时禁止"全图猜读"

## 输出契约

```json
{"readings": [{"device": "gauge@320,322", "fraction": 0.126,
               "value": 5.05, "unit": "bar", "max_pressure": 40.0,
               "bbox": [86, 86, 554, 554], "confidence": 0.95,
               "needle_angle_deg": 169.1, "method": "red_needle"}]}
```

## 实测（130 张合成表盘，2026-09-22）

归一化读数 MAE **0.056**（红指针 0.029 / 黑指针 0.075），56% 样本误差 < 2%，
拒判 4 个（模糊/遮挡下正确行为），最大误差 0.65（离群，已记录）。
