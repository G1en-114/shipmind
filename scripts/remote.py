#!/usr/bin/env python3
"""通用远程执行工具：从 .env 读取 <前缀>_HOST/PORT/USER/PASSWORD，SSH 执行命令。

用法：
    python scripts/remote.py SEETA "nvidia-smi"          # 自租开发机
    python scripts/remote.py SPARK "free -h"             # 组委会节点
    python scripts/remote.py SEETA --upload 本地 远程      # SFTP 上传
    python scripts/remote.py SEETA --download 远程 本地     # SFTP 下载
    python scripts/remote.py SEETA --tmux-start 名 "命令"   # tmux 托管启动
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def connect(prefix: str) -> paramiko.SSHClient:
    env = load_env()
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(env[f"{prefix}_HOST"], port=int(env[f"{prefix}_PORT"]),
              username=env[f"{prefix}_USER"], password=env[f"{prefix}_PASSWORD"],
              timeout=30, banner_timeout=30)
    return c


def run(c: paramiko.SSHClient, cmd: str, timeout: int = 600,
        stream: bool = False) -> tuple[str, str, int]:
    _, out, err = c.exec_command(cmd, timeout=timeout)
    if not stream:
        o = out.read().decode("utf-8", "replace")
        e = err.read().decode("utf-8", "replace")
        return o, e, out.channel.recv_exit_status()
    # 流式：边收边打，适合下载/训练等长任务
    lines = []
    while True:
        if out.channel.recv_ready():
            data = out.channel.recv(4096).decode("utf-8", "replace")
            lines.append(data)
            print(data, end="", flush=True)
        if out.channel.exit_status_ready() and not out.channel.recv_ready():
            break
        time.sleep(0.2)
    rc = out.channel.recv_exit_status()
    e = err.read().decode("utf-8", "replace")
    return "".join(lines), e, rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", help=".env 中的配置前缀，如 SEETA / SPARK")
    ap.add_argument("command", nargs="?", help="要执行的远程命令")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--upload", nargs=2, metavar=("LOCAL", "REMOTE"))
    ap.add_argument("--download", nargs=2, metavar=("REMOTE", "LOCAL"))
    ap.add_argument("--tmux-start", nargs=2, metavar=("SESSION", "CMD"),
                    help="在 tmux 中托管启动（SSH 断开也不中断）")
    args = ap.parse_args()

    c = connect(args.prefix)
    try:
        if args.upload:
            sftp = c.open_sftp()
            local, remote = args.upload
            try:
                rsize = sftp.stat(remote).st_size
                if rsize == Path(local).stat().st_size:
                    print(f"已存在且大小一致，跳过: {remote}")
                    return 0
                print(f"远端已存在部分文件（{rsize}B），将覆盖续传由调用方保证")
            except IOError:
                pass
            sftp.put(local, remote)
            sftp.close()
            print(f"上传完成 {local} -> {remote}")
            return 0
        if args.download:
            sftp = c.open_sftp()
            remote, local = args.download
            sftp.get(remote, local)
            sftp.close()
            print(f"下载完成 {remote} -> {local}")
            return 0
        if args.tmux_start:
            session, cmd = args.tmux_start
            c.exec_command(f"tmux kill-session -t {session} 2>/dev/null; "
                           f"tmux new -d -s {session} '{cmd}'")
            print(f"tmux 会话 {session} 已启动")
            return 0
        if not args.command:
            ap.error("需要提供 command，或使用 --upload/--download/--tmux-start")
        o, e, rc = run(c, args.command, args.timeout)
        if o:
            print(o, end="" if o.endswith("\n") else "\n")
        if e.strip():
            print("[stderr]", e[:2000], file=sys.stderr)
        return rc
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
