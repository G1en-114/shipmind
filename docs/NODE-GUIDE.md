# GB10 Spark 云节点使用指南（交接）

> 面向：接手项目的 AI ｜ 更新：2026-09-23
> 配套文档：`docs/HANDOFF.md`（总交接）、`docs/NODE-DEPLOY.md`（部署清单）、`docs/NODE-INCIDENT.md`（事故记录）

---

## 1. 节点是什么、怎么连

组委会为本比赛提供的 **DGX Spark（GB10）云节点**，每队一台，是项目"本地算力"叙事的载体，**也是演示必须跑的环境**（评审"平台适配性 15%"）。

| 项 | 值 |
|---|---|
| 登录 | `ssh -p 6065 Developer@106.13.186.155`（密码在 `D:\invadi\.env` 的 `SPARK_PASSWORD`，**不入仓库**） |
| 主机名 | 登录表写 spark-65，实际显示 `spark-a24e` |
| 硬件 | GB10 / ARM64(aarch64) / **121GB 统一内存**（CPU/GPU 共池）/ 20 核 / 3.7TB 盘 |
| 软件 | Ubuntu 24.04、CUDA 13.0（驱动 580.82）、Docker 28.3、系统 Python 3.12（注意见 §4）、tmux、ffmpeg 6.1 |
| 代码位置 | `~/shipmind/`（从仓库同步） |
| 数据位置 | `~/data/`（dcase2020 3.2G / deepship / seashipsseg / mastr1325 / modd2 含已合成 mp4） |
| 跳板 | 50 台节点共用一个公网 IP；SSH 6065 → 内网 22；业务端口 7065/8065/9065 → 内网 7000/8888/9000 |

**自动化**（本地跑，凭据自动从 `.env` 读）：

```bash
python scripts/node_check.py "任意远程命令"          # 执行
python scripts/remote.py SPARK "任意远程命令"        # 同上（通用版）
python scripts/node_deploy.py                       # 整仓同步（tar+SFTP，自动排除 .env/fixtures/权重）
```

## 2. 正在节点上跑着的东西（别误杀）

| tmux 会话 | 内容 | 端口 |
|---|---|---|
| `vllm` | vLLM 0.25 + Qwen3-4B-FP8（本地大脑） | 127.0.0.1:9000 |
| `webui` | 值班台 FastAPI（新前端） | 127.0.0.1:8888 |

查看：`tmux ls`；进会话：`tmux attach -t vllm`（退出按 Ctrl+B 再按 D，**不要 Ctrl+C**——那会杀掉服务）。

**演示值班台**：SSH 时加转发 `ssh -p 6065 -L 8888:localhost:8888 Developer@106.13.186.155`，本地浏览器开 http://localhost:8888/ 。

## 3. 红线（节点手册明文，违反会被回收节点/取消资格）

1. **禁止 `reboot` / `shutdown` / `poweroff`**——远程托管，重启后只能等现场人工恢复。
2. **禁止改系统级配置**：登录密码、sshd、防火墙/iptables、驱动、BIOS。
3. **禁止 scp 单文件 >1GB**——50 台共享公网出口，大文件在节点内直接下载（ModelScope 可达；GitHub/HuggingFace/Zenodo **不可达**）。
4. **公网映射端口（7065/8065/9065）上的服务必须加鉴权**；我们所有服务只绑 127.0.0.1，遵守此规。
5. 禁止扫描内网其他节点、转租节点、存隐私数据。
6. 节点**无备份**——git 远端就是灾备，**每次改完节点上的东西要保证仓库里有源头**。

## 4. 已知深坑（全部踩过，规避方法在右边）

| 坑 | 规避 |
|---|---|
| **统一内存 OOM**：vLLM 默认 `gpu_memory_utilization 0.9` 会吃光 121GB → 整机调度饿死，SSH 认证通过但会话建不起来（我们发生过一次，3 小时自愈） | 启动 vLLM 必须带 `--gpu-memory-utilization 0.45 --enforce-eager`，另加 `FLASHINFER_DISABLE_VERSION_CHECK=1`（预置镜像 flashinfer 版本不匹配）。固化在 `scripts/node_start_vllm.sh`，照抄 |
| vLLM 0.25 不认 Qwen3.6-35B 架构；198B 的 step-3.7-flash 显存放不下 | 本地大脑 = Qwen3-4B-FP8；大模型走 StepFun API |
| 节点 GitHub/HF/Zenodo 直连全断 | 代码用 `node_deploy.py` 从本地推；模型走 ModelScope（节点可装 `pip install modelscope`） |
| 交互 shell 是 conda base，**没有 numpy** | 给用户命令用 `pip install numpy scipy pillow fastapi uvicorn` 装进 base，或用 `/usr/bin/python3`（numpy 装在 --user） |
| 系统 node 18 跑不动 skills CLI | 用户级 Node 22：`export PATH=$HOME/.local/node22/bin:$PATH` |
| SFTP 大文件偶发断 | 单流 sftp.put 可行（92MB/175s 实测）；重试即可 |
| `rm -rf evals/fixtures` 会把手工同步的 report 夹具一起删（翻车过） | report 夹具已并入 `make_fixtures.py`，**永远先 make_fixtures 再跑评测** |
| 手工挑文件同步漏过 corpus/cases/sensors（翻车 5 次） | 一律 `node_deploy.py` 整仓部署，废弃手工清单 |
| StepFun key 不放节点 .env | 评测时环境变量注入：`STEPFUN_API_KEY=... python3 evals/run_evals.py`（节点可达 api.stepfun.com，已验） |
| 官方 Skill 装在 `~/.agents/skills`，仓库另有 vendored 副本 | 桥接层默认用仓库内 `official-skills/installed/`，自包含 |

## 5. 标准操作流程（照抄即可）

```bash
# 同步代码 + 重建夹具 + 全量评测（34/34）
python scripts/node_deploy.py
python scripts/node_check.py "cd ~/shipmind && rm -rf evals/fixtures && \
  python3 evals/make_fixtures.py >/dev/null && \
  python3 sensors/gauge_synth.py --out evals/fixtures/gauges --n-train 100 --n-val 30 >/dev/null && \
  STEPFUN_API_KEY=<.env里取> python3 evals/run_evals.py | tail -3"

# 重启本地大脑（若挂）
python scripts/node_check.py "bash ~/shipmind/scripts/node_start_vllm.sh"

# 重启值班台
python scripts/node_check.py "tmux kill-session -t webui; \
  tmux new -d -s webui 'cd ~/shipmind && python3 -m uvicorn web.server:app --host 127.0.0.1 --port 8888 > ~/logs/webui.log 2>&1'"

# 健康一览
python scripts/node_check.py "uptime; free -h | head -2; tmux ls; \
  curl -s -m 5 http://127.0.0.1:9000/v1/models | head -c 80; echo; \
  curl -s -o /dev/null -w 'webui:%{http_code}\n' http://127.0.0.1:8888/"
```

**健康判据**：load < 18（20 核）、available 内存 > 30G、`vllm`/`webui` 会话在、9000/8888 返回 200。available < 15G 时先杀新开的活，别动 vllm。

## 6. 用户侧约定（对人的，别违反）

- 给用户的命令一律 **PowerShell 单行**（不吃 bash 续行反斜杠；scp 大写 `-P`；用 `Select-Object` 不用 `tail`）。
- 用户自己的服务器（`.env` 里 SEETA_*，付费机）**已弃用，不要主动使用**。
- 节点操作可自动化（paramiko 已就绪），但**破坏性操作前先跟用户确认**。
