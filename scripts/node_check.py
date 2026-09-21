#!/usr/bin/env python3
"""组委会 Spark 云节点远程自检工具。

从仓库根的 .env 读取 SPARK_* 配置（凭据不入仓库），SSH 登录后批量执行
自检命令并打印输出。用法：

    python scripts/node_check.py             # 标准自检
    python scripts/node_check.py "任意命令"   # 执行单条远程命令
"""
from __future__ import annotations

import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]

STANDARD_CHECKS = r'''
echo "=== host ==="; hostname; uname -m; head -2 /etc/os-release
echo "=== gpu ==="; nvidia-smi || echo "nvidia-smi 失败"
echo "=== cuda ==="; nvcc -V 2>&1 | tail -1
echo "=== disk ==="; df -h / | tail -1; df -h ~ | tail -1
echo "=== mem/cpu ==="; free -h | head -2; nproc
echo "=== python ==="; python3 -V; pip3 -V 2>&1 | head -1
echo "=== docker ==="; docker info 2>/dev/null | grep -E "Server Version|Storage Driver" || echo "docker 不可用"
echo "=== node ==="; node -v 2>/dev/null || echo "node 未装"
echo "=== conda ==="; conda --version 2>/dev/null || echo "conda 未装"
echo "=== tmux ==="; tmux -V 2>/dev/null || echo "tmux 未装"
echo "=== 预置模型 ==="; ls /home/xsuper/models/ 2>/dev/null || echo "无预置模型目录"
'''


def load_env() -> dict[str, str]:
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    env = load_env()
    host, port, user = env["SPARK_HOST"], int(env["SPARK_SSH_PORT"]), env["SPARK_USER"]
    password = env["SPARK_PASSWORD"]
    command = " ".join(sys.argv[1:]) or STANDARD_CHECKS

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password, timeout=30)
    try:
        _, stdout, stderr = client.exec_command(command, timeout=600)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        print(out)
        if err.strip():
            print("[stderr]", err[:2000], file=sys.stderr)
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
