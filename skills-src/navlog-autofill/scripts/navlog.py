#!/usr/bin/env python3
"""值班日志自动生成：事件流 JSONL → 排序、格式化、统计（确定性，零容差评测）。"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("events", help="事件流 JSONL：{ts, type, text}")
    ap.add_argument("--title", default="轮机日志 Engine Log")
    ap.add_argument("--watch", default="0000-0400", help="班次时段")
    args = ap.parse_args()

    events = []
    for line in Path(args.events).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"error": f"非 JSON 行: {line[:40]}", "rejected": True},
                             ensure_ascii=False), file=sys.stderr)
            return 2
        if not isinstance(e, dict) or not e.get("ts") or not e.get("text"):
            print(json.dumps({"error": f"事件缺少 ts/text: {line[:40]}", "rejected": True},
                             ensure_ascii=False), file=sys.stderr)
            return 2
        events.append(e)

    if not events:
        print(json.dumps({"error": "事件流为空", "rejected": True},
                         ensure_ascii=False), file=sys.stderr)
        return 2

    events.sort(key=lambda e: e["ts"])
    counts = Counter(str(e.get("type", "info")) for e in events)
    lines = [f"# {args.title}（{args.watch} 班）", ""]
    for e in events:
        lines.append(f"[{e['ts']}] [{str(e.get('type', 'info')).upper()}] {e['text']}")
    lines += ["", f"共 {len(events)} 条事件："
              + "，".join(f"{k} {v} 条" for k, v in sorted(counts.items()))]

    print(json.dumps({
        "log_text": "\n".join(lines),
        "n_events": len(events),
        "by_type": dict(counts),
    }, ensure_ascii=False, indent=2))
    print(f"MEDIA:{Path(args.events).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
