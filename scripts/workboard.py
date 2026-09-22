#!/usr/bin/env python3
"""只读任务板：检查架子完整性并列出下一步，不执行修复或验收。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "docs" / "work"
TASK_STATES = {"pending", "in_progress", "blocked", "done", "deferred"}
CHECK_STATES = {"not_run", "passed", "failed", "skipped"}


def inspect():
    tasks = json.loads((WORK / "tasks.json").read_text(encoding="utf-8"))["tasks"]
    checks = json.loads((WORK / "acceptance.json").read_text(encoding="utf-8"))["checks"]
    by_id = {t["id"]: t for t in tasks}
    by_check = {c["id"]: c for c in checks}
    errors = []
    if len(by_id) != len(tasks) or len(by_check) != len(checks):
        errors.append("重复任务或验收 ID")
    for c in checks:
        if c["status"] not in CHECK_STATES:
            errors.append(f"{c['id']}: 非法验收状态")
        if c["status"] == "passed" and not c.get("evidence"):
            errors.append(f"{c['id']}: passed 缺少证据")
    for t in tasks:
        if t["status"] not in TASK_STATES:
            errors.append(f"{t['id']}: 非法任务状态")
        if not t["acceptance"]:
            errors.append(f"{t['id']}: 缺少验收规格")
        for dep in t["depends_on"]:
            if dep not in by_id:
                errors.append(f"{t['id']}: 未知依赖 {dep}")
        for cid in t["acceptance"]:
            if cid not in by_check:
                errors.append(f"{t['id']}: 未知验收 {cid}")
        if t["status"] == "done":
            if not t.get("evidence"):
                errors.append(f"{t['id']}: done 缺少证据")
            if any(by_check.get(cid, {}).get("status") != "passed" for cid in t["acceptance"]):
                errors.append(f"{t['id']}: 验收尚未全部通过")
            if any(by_id.get(dep, {}).get("status") != "done" for dep in t["depends_on"]):
                errors.append(f"{t['id']}: 依赖尚未完成")
    visiting, visited = set(), set()

    def visit(tid):
        if tid in visiting:
            errors.append(f"循环依赖: {tid}")
            return
        if tid in visited or tid not in by_id:
            return
        visiting.add(tid)
        for dep in by_id[tid]["depends_on"]:
            visit(dep)
        visiting.remove(tid)
        visited.add(tid)

    for tid in by_id:
        visit(tid)
    referenced = {cid for t in tasks for cid in t["acceptance"]}
    for cid in by_check.keys() - referenced:
        errors.append(f"未关联任务的验收: {cid}")
    return tasks, checks, errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["check", "status", "next"])
    args = ap.parse_args()
    try:
        tasks, checks, errors = inspect()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"任务板读取失败: {exc}")
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.command == "check":
        print(f"架子检查通过：{len(tasks)} 项任务，{len(checks)} 项验收规格。未执行产品测试。")
    elif args.command == "status":
        for t in tasks:
            print(f"{t['id']} [{t['priority']}] 阶段 {t['phase']} {t['status']}: {t['title']}")
    else:
        by_id = {t["id"]: t for t in tasks}
        ready = [t for t in tasks if t["status"] == "pending"
                 and all(by_id[d]["status"] == "done" for d in t["depends_on"])]
        for t in sorted(ready, key=lambda t: (t["phase"], t["priority"], t["id"])):
            print(f"{t['id']}: {t['title']} | 验收 {', '.join(t['acceptance'])}")
        if not ready:
            print("没有就绪的待办；请查看进行中、阻塞或完成状态。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
