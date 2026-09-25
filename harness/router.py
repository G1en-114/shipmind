"""关键词路由骨架。真实路由由主 Agent（Step 3.7 Flash）承担，此为可测试的降级实现。

负向路由是硬要求：不命中任何 Skill 时必须返回 None，禁止硬凑。
"""
from __future__ import annotations

from .registry import SkillEntry


def route(query: str, skills: list[SkillEntry]) -> SkillEntry | None:
    q = query.lower()
    best: SkillEntry | None = None
    best_score = 0
    for s in skills:
        if s.entry is None:
            continue
        # 统一 lower 并去重：触发词若与 description 词块重复，只按触发词权重计一次
        trig = {k.lower() for k in s.triggers}
        extra = {k for k in s.keywords() if k not in trig}
        score = sum(2 for kw in trig if kw in q) + sum(1 for kw in extra if kw in q)
        # 负触发扣分：命中负触发词 2 分——语义冲突时宁可少分也不误触发
        neg = {k.lower() for k in getattr(s, "negative", [])}
        score -= sum(2 for kw in neg if kw in q)
        if score > best_score:
            best, best_score = s, score
    return best
