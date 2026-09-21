#!/usr/bin/env python3
"""把仓库骨架同步到组委会 Spark 云节点（排除凭据与生成物）。

用法：python scripts/node_deploy.py
之后用 node_check.py 在节点上执行命令，例如：
    python scripts/node_check.py "cd ~/shipmind && python3 evals/run_evals.py"
"""
from __future__ import annotations

import sys
import tarfile
import tempfile
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parent))
from node_check import load_env  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {".git", ".env", ".zcode", "evals/fixtures", "runs", "data",
           "__pycache__", ".smoke", "models"}


def want(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if path.is_dir():
        return not any(rel == e or rel.startswith(e + "/") for e in EXCLUDE)
    return not any(rel == e or rel.startswith(e + "/") for e in EXCLUDE) \
        and not path.name.endswith(".pyc") \
        and ".env" not in path.name


def make_tar() -> Path:
    fd, name = tempfile.mkstemp(suffix=".tgz")
    import os
    os.close(fd)
    out = Path(name)
    with tarfile.open(out, "w:gz") as tf:
        for p in sorted(ROOT.rglob("*")):
            if want(p):
                tf.add(p, arcname=p.relative_to(ROOT).as_posix())
    return out


def main() -> int:
    env = load_env()
    tgz = make_tar()
    size_mb = tgz.stat().st_size / 1e6
    print(f"打包完成：{size_mb:.1f} MB")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(env["SPARK_HOST"], port=int(env["SPARK_SSH_PORT"]),
                   username=env["SPARK_USER"], password=env["SPARK_PASSWORD"],
                   timeout=30)
    try:
        sftp = client.open_sftp()
        remote_tgz = "shipmind_upload.tgz"
        sftp.put(str(tgz), remote_tgz)
        sftp.close()
        print("上传完成")
        _, stdout, stderr = client.exec_command(
            "mkdir -p ~/shipmind && tar xzf ~/shipmind_upload.tgz -C ~/shipmind "
            "&& rm ~/shipmind_upload.tgz && echo SYNCED && "
            "find ~/shipmind -type f | wc -l", timeout=60)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err.strip():
            print("[stderr]", err[:1000], file=sys.stderr)
    finally:
        client.close()
    tgz.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
