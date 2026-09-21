---
name: sonar-acoustic-fingerprint
description: 被动声纹监测（民用海事感知）。当需要从水听器音频中提取船舶声纹特征（LOFAR 窄带谱线=螺旋桨叶频谐波、DEMON 包谱=轴频）、判别目标船类并给出证据谱线时使用。触发词：声纹、声呐、水听器、螺旋桨、LOFAR、DEMON、目标船、船型判别。不适用于：机舱设备自身故障检测（用 engine-room-acoustic-sentinel）、雷达目标检测。
version: 0.1.0
entry: scripts/sonar_fingerprint.py
---

# 被动声纹（民用海事感知）

只做被动接收与船类判别（港口/渔业/海事监测场景）。规则轨先行（谱线统计可解释），ML 轨（ShipsEar/DeepShip 分类器）D7 接入后须双轨对照。

## 前置提问（缺失必须先问，禁止猜测）

1. **水听器音频**：wav/flac，≥ 5 秒。
2. **场景**：锚地/航道/开阔水域——影响背景噪声假设。

## 执行流程

1. LOFAR：分块功率谱平均，找显著谱线（> 6× 频带中位数）。
2. 谐波列匹配：对候选基频 f0 允许 ±2% 容差匹配 k·f0（k=1..8）。
3. DEMON：平方包络低通 → 包谱，估轴频。
4. 规则分级（rule 模式）：≥3 阶谐波且 f0<100Hz → 大型货船/油轮类；2 阶且 100–400Hz → 中型船；无谱线且中频宽带 → 拖轮/渔船类；否则 unknown。
5. 输出必须附证据（谱线数、f0、匹配阶数、轴频估计），供 verifier 复核与雷达交叉印证。

## 禁止行为

- 纯噪声或证据不足必须输出 unknown（confidence≤0.2），禁止硬判船型。
- 仅使用"被动声纹监测 / 民用海事感知"表述，禁止任何军用声呐叙事。
- ML 分类器未上线前禁止宣称"AI 识别准确率"。

## 输出契约

```json
{
  "label": "large_cargo_or_tanker",
  "confidence": 0.7,
  "mode": "rule_fallback",
  "evidence": {"tonal_count": 8, "f0_hz": 14.0, "harmonics_matched": [1,2,3,4,5], "demon_shaft_hz_est": 14.1}
}
```
