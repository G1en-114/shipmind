---
name: official-bridge
description: 官方 NVIDIA Skill 桥接层。当需要调用官方 Skill（DeepStream 管线生成 / RAG Blueprint / TAO grounding / VSS 视频问答与报告）时使用。触发词：官方skill、deepstream、管线、gst-launch、rag-blueprint、tao、grounding、vss、视频报告。不适用于：自研 Skill 的功能调用。
version: 0.1.0
entry: ../../scripts/official_bridge.py
---

# 官方 Skill 桥接

两种接入方式（如实区分）：

- **executable**（已实测）：`deepstream-generate-pipeline` 有零依赖脚本，直接执行并返回真实 gst-launch pipeline。
- **advisory**：其余 5 个为指令型 Skill（无可执行入口），按 Skill 范式的渐进式披露返回其 SKILL.md 正文，并附实测前置条件。前置条件（NGC key / TAO 容器 / VSS 服务）未满足时**不假装执行**。

编排层派发：`Orchestrator.execute_official(skill, query)`。
