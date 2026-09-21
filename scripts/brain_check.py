#!/usr/bin/env python3
"""大脑自检：对话 sanity + 路由三连（两正一负）。在节点上于仓库根运行。

    python3 scripts/brain_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.brain import chat, choose_skill  # noqa: E402
from harness.registry import load_skills  # noqa: E402


def main() -> int:
    print("== 1. 对话 sanity ==")
    print(chat([{"role": "user",
                 "content": "用一句话回答：你是谁？运行在什么硬件上？"}],
               max_tokens=100))

    print("== 2. 路由三连（两正一负）==")
    ready = [s for s in load_skills() if s.entry]
    cases = [
        ("3号泵刚才有金属摩擦声，帮我判断一下", "engine-room-acoustic-sentinel"),
        ("我们现在偏出航线了吗", "route-deviation-watch"),
        ("今天晚饭吃什么", None),
    ]
    n_pass = 0
    for query, expect in cases:
        got = choose_skill(query, ready)
        ok = got == expect
        n_pass += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {query} -> {got} (期望 {expect})")

    print(f"{n_pass}/{len(cases)} passed")
    return 0 if n_pass == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
