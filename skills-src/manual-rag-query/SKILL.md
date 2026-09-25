---
name: manual-rag-query
description: 本地知识库检索。当需要查询设备手册、COLREGs 避碰规则、公司 SMS 体系文件的条款原文并带引用回答时使用。触发词：手册、规则、条款、查一下、COLREGs、SMS、会遇、追越、直航、交叉、轴承、气蚀、换泵。不适用于：仪表读数（用 engine-room-visual-inspector）、音频分析（用 engine-room-acoustic-sentinel / sonar-acoustic-fingerprint）。
version: 0.1.0
triggers: 手册,规则,条款,查一下,COLREGs,SMS,会遇,追越,直航,交叉,轴承磨损原因,气蚀
negative-triggers: 实时检测,音频分析,仪表读数,雷达目标,语音播报
entry: scripts/rag_query.py
---

# 手册与规则 RAG

## 后端说明（重要）

- **当前后端**：本地 BM25 检索（`scripts/rag_query.py`，零第三方依赖、离线可复现），
  语料为 `corpus/manuals/` 下的**自拟合成手册**（离心泵运维手册 / COLREGs 要点 / SMS 应急摘要）。
- **升级路径**：官方 `rag-blueprint`（NVIDIA，Docker Compose / NIM）——需要 NIM API key，
  检索质量随向量模型提升。两者接口一致，替换后端不影响调用方。

## 执行流程

1. 对 query 分词（英文按词、中文按 bigram，无分词库依赖）
2. BM25 检索 top-k 块（按 `###`/`##` 标题切块，保留章节号）
3. 输出必须逐条带 `quote + source + section`，quote 必须是语料原文

## 禁止行为

- 检索不到必须明说"手册中未找到"，**禁止编造章节号或条文**
- 引用必须是检索结果原文，禁止改写后当原文引用
- COLREGs 问答必须附条款号（如 Rule 15 交叉局面），禁止凭记忆裸答

## 输出契约

```json
{
  "query": "...",
  "answers": [
    {"score": 7.8, "source": "centrifugal-pump.md", "section": "3.1 高频啸叫伴金属摩擦音",
     "quote": "原文摘录", "text": "块全文"}
  ]
}
```

无命中时 `answers` 为空数组并附 `note`。
