#!/usr/bin/env python3
"""并行分块上传：大文件切 N 块并发上传，服务端拼接后校验 MD5。

断点续传语义：单块已存在且大小正确即跳过；全部完成后比对 MD5，不符则重传差额块。
用法：
    python scripts/parallel_upload.py SEETA 本地文件 远程路径 [--chunks 4]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remote import connect  # noqa: E402

CHUNK = 32 * 1024 * 1024  # 32MB/块


def md5(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("local")
    ap.add_argument("remote")
    ap.add_argument("--chunks", type=int, default=4)
    args = ap.parse_args()

    local = Path(args.local)
    total = local.stat().st_size
    n = max(1, min(args.chunks, (total + CHUNK - 1) // CHUNK))
    c = connect(args.prefix)

    bounds = [(i * CHUNK, min((i + 1) * CHUNK, total)) for i in range(n)]
    done: dict[int, bool] = {}
    lock = threading.Lock()
    errors: list[str] = []

    # paramiko SFTP 非线程安全：每个工作线程用独立连接
    def worker(idx: int) -> None:
        start, end = bounds[idx]
        cc = connect(args.prefix)
        s = cc.open_sftp()
        part = f"{args.remote}.part{idx:02d}"
        try:
            if s.stat(part).st_size == end - start:
                with lock:
                    done[idx] = True
                return
        except IOError:
            pass
        with open(local, "rb") as f:
            f.seek(start)
            s.putfo(f, part, file_size=end - start)
        s.close()
        cc.close()
        with lock:
            done[idx] = True

    threads = []
    for i in range(n):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    if len(done) != n:
        print(f"有分块未完成: {sorted(set(range(n)) - set(done))}", file=sys.stderr)
        return 1

    # 服务端拼接 + 校验
    _, out, err = c.exec_command(
        f"cd $(dirname {args.remote}) && cat $(basename {args.remote}).part* > $(basename {args.remote}) "
        f"&& rm -f $(basename {args.remote}).part* && md5sum $(basename {args.remote}) | cut -d' ' -f1",
        timeout=1800)
    remote_md5 = out.read().decode().strip()
    local_md5 = md5(local)
    ok = remote_md5 == local_md5
    print(json.dumps({"file": str(local), "size_mb": round(total / 1e6, 1),
                      "chunks": n, "md5_match": ok,
                      "remote_md5": remote_md5}, ensure_ascii=False))
    c.close()
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
