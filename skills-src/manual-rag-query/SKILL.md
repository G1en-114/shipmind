---
name: manual-rag-query
description: 本地知识库检索。当需要查询设备手册、COLREGs 避碰规则、公司 SMS 体系文件的条款原文并带引用回答时使用。触发词：手册、规则、条款、查一下、COLREGs、SMS、会遇、追越、直航、交叉。不适用于：仪表读数（用 engine-room-visual-inspector）、音频分析（用 engine-room-acoustic-sentinel / sonar-acoustic-fingerprint）。
version: 0.1.0
entry: scripts/rag_query.py
---

# 手册与规则 RAG（D5 交付，基于官方 rag-blueprint）

官方 Skill 保持原样接入，本 Skill 只做业务路由与引用格式化。

## 执行流程（规划）

1. 加载本地向量库（rag-blueprint；语料 = 自拟合成手册 + COLREGs 条文）
2. 检索 top-k → 摘录原文与章节号
3. 回答必须逐条带 `quote + source + section`，供 verifier 复核

## 禁止行为

- 检索不到必须明说"手册中未找到"，禁止编造章节号或条文。
- 引用必须是检索结果原文，禁止改写后当原文引用。
- COLREGs 问答必须附条款号（如 Rule 15 交叉局面），禁止凭记忆裸答。

## 输出契约（规划）

```json
{"answers": [{"claim": "...", "quote": "...", "source": "...", "section": "..."}]}
```
