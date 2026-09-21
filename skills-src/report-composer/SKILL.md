---
name: report-composer
description: 巡检报告生成。当一轮值守/巡检（声学+视觉+知识+态势）完成、需要汇总多源证据生成结构化报告时使用。触发词：报告、汇总、总结、生成巡检报告、写报告。不适用于：日志填写（用 navlog-autofill）、单条告警播报（用 StepAudio）。
version: 0.1.0
entry: scripts/compose_report.py
---

# 巡检报告生成（D6 交付，调用官方 vss-generate-video-report）

## 执行流程（规划）

1. 汇集本轮全部证据（各 Skill 输出 JSON + 带框图路径）
2. 逐条结论挂证据引用（声学特征数值 / 视觉框 / 手册原文 / 声纹谱线 / 雷达检测参数）
3. 交 verifier（证据审核 Agent）逐条复核，无证据即驳回
4. 生成 Markdown 报告 + 带框图附件

## 禁止行为

- 报告中不允许出现无证据结论。
- verifier 驳回的条目必须标注"待复核"而非静默删除。
- 报告措辞与声纹 Skill 同一红线：被动声纹/民用海事感知。

## 输出契约（规划）

```json
{"report_md": "...", "conclusions": [{"claim": "...", "evidence_refs": ["acoustic-001:evidence", "radar-001:targets[0]"]}]}
```
