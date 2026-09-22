---
name: voice-alert
description: 告警语音播报与语音指令识别。当需要把分级告警/处置步骤转为语音播报（机舱噪音环境），或把船员语音指令转为文字时使用。触发词：播报、语音、念出来、说出来、听一下、语音指令。不适用于：无声任务、文本日志（用 navlog-autofill）。
version: 0.1.0
entry: scripts/voice.py
---

# 告警语音（StepFun ASR/TTS）

## 设计原则

**机舱噪音环境下只播分级与动作，不播技术细节**——听不清还要占注意力是负收益。
播报模板：`{设备} {分级}，{动作}`，如"3 号泵 alarm，切换备用泵"。

## 禁止行为

- 禁止播报未经 verifier 复核的结论
- 禁止在播报中泄露原始特征数值（无行动指导意义）
- TTS 失败时降级为文本输出，禁止静默丢弃告警

## 用法

```bash
python voice.py --tts "3号泵 alarm，切换备用泵" --out output/alert.wav
python voice.py --asr crew_command.wav
```
