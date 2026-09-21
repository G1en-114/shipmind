---
name: navlog-autofill
description: 航海/轮机日志自动生成。当需要把一轮值守的事件流（告警、处置动作、态势发现）整理成标准班志文本与统计时使用。触发词：日志、轮机日志、航海日志、班志、记录、填写日志。不适用于：巡检报告（用 report-composer）、实时播报（用 StepAudio）。
version: 0.1.0
entry: scripts/navlog.py
---

# 值班日志自动生成（确定性模块）

事件流 JSONL → 排序、格式化、统计。与声学哨兵同属"零容差评测"的确定性层。

## 执行流程

1. 逐行解析事件（`{"ts": "...", "type": "alarm|action|info|...", "text": "..."}`）。
2. 任一行缺 `ts`/`text` 或非 JSON → 整体 `rejected`，不做"尽力而为"的模糊日志。
3. 按时间排序，格式化为 `[ts] [TYPE] text`，尾部附分类统计。
4. 输出契约 JSON（log_text + n_events + by_type），末尾 `MEDIA:` 行。

## 禁止行为

- 禁止合并、改写或省略事件原文。
- 禁止在日志中加入评价性语言（日志只记录事实与动作）。

## 输出契约

```json
{"log_text": "...", "n_events": 3, "by_type": {"alarm": 1}}
```
