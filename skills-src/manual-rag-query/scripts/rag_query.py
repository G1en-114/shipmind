#!/usr/bin/env python3
"""手册/规则检索：本地 BM25 + 引用溯源。零第三方依赖，离线可复现。

架构说明：本脚本是 manual-rag-query 的**当前后端**（本地 BM25，语料为自拟合成手册）。
官方 rag-blueprint（NVIDIA，Docker Compose/NIM 部署）是升级路径——需要 NIM API key，
且检索质量随向量模型提升。两者接口一致：返回带原文引用的答案条目。

用法：
    python rag_query.py "3号泵轴承异响可能是什么原因"
    python rag_query.py --query "..." --top-k 3 --json
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[3] / "corpus" / "manuals"
K1, B = 1.5, 0.75


def tokenize(text: str) -> list[str]:
    """中英文混合分词：英文按词，中文按 bigram（无需分词库）。"""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


def chunk_markdown(path: Path) -> list[dict]:
    """按 ### 标题切块，保留章节号与来源，供引用溯源。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    title, section, buf = path.stem, "（导言）", []
    chunks: list[dict] = []
    for ln in lines:
        if ln.startswith("### "):
            if buf:
                chunks.append({"source": path.name, "title": title,
                               "section": section, "text": "\n".join(buf).strip()})
            section, buf = ln.lstrip("# ").strip(), []
        elif ln.startswith("## "):
            if buf:
                chunks.append({"source": path.name, "title": title,
                               "section": section, "text": "\n".join(buf).strip()})
            section, buf = ln.lstrip("# ").strip(), []
        else:
            buf.append(ln)
    if buf:
        chunks.append({"source": path.name, "title": title,
                       "section": section, "text": "\n".join(buf).strip()})
    return [c for c in chunks if len(c["text"]) >= 20]


class BM25:
    TITLE_BOOST = 2.0  # 章节标题命中权重：按"第15条"检索应命中条款小节本身，
                       # 而非正文里提到"第 15 条"的其他条款（Rule 13 就提到了 15/17）

    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.tf_text = [Counter(tokenize(d["text"])) for d in docs]
        self.tf_title = [Counter(tokenize(d["section"])) for d in docs]
        self.tf = [t + Counter({k: v * int(self.TITLE_BOOST) for k, v in ti.items()})
                   for t, ti in zip(self.tf_text, self.tf_title)]
        self.df = Counter()
        for t in self.tf:
            for tok in t:
                self.df[tok] += 1
        self.len = [max(sum(t.values()), 1) for t in self.tf]
        self.avgdl = sum(self.len) / max(len(self.len), 1)
        self.n = len(docs)

    def search(self, query: str, top_k: int = 3) -> list[tuple[float, dict]]:
        q = tokenize(query)
        scored = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for tok in set(q):
                if tok not in self.tf[i]:
                    continue
                idf = math.log(1 + (self.n - self.df[tok] + 0.5) / (self.df[tok] + 0.5))
                f = self.tf[i][tok]
                score += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * self.len[i] / self.avgdl))
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]


def build_index() -> BM25:
    docs: list[dict] = []
    if not CORPUS.exists():
        return BM25([])
    for p in sorted(CORPUS.glob("*.md")):
        docs.extend(chunk_markdown(p))
    return BM25(docs)


def answer(query: str, top_k: int = 3) -> list[dict]:
    idx = build_index()
    hits = idx.search(query, top_k)
    out = []
    for score, doc in hits:
        # 引用必须是原文摘录：取命中块中最相关的前几句
        sentences = [s.strip() for s in doc["text"].splitlines()
                     if s.strip() and not s.strip().startswith(("|", ">", "#", "-", "*"))]
        quote = sentences[0] if sentences else doc["text"][:120]
        out.append({
            "score": round(score, 3),
            "source": doc["source"],
            "section": doc["section"],
            "quote": quote[:200],
            "text": doc["text"][:600],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--query", dest="query_opt")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    q = args.query_opt or args.query
    if not q:
        ap.error("需要提供 query")

    hits = answer(q, args.top_k)
    payload = {"query": q, "answers": hits}
    if not hits:
        payload["note"] = "手册中未找到相关内容"
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
