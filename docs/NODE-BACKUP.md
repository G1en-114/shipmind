# GB10 节点备份与重建清单

> 2026-09-25 ｜ 云节点关停前的备份记录 + 新节点重建手册
> 配套：`docs/NODE-GUIDE.md`（使用指南）、`docs/NODE-DEPLOY.md`（部署清单）、`scripts/node_bootstrap.sh`（一键重建）

---

## 1. 已备份到本地（runs/backup/）

| 文件 | 大小 | 内容 | 来源 |
|---|---|---|---|
| `duty.jsonl` | 19KB | **AI 值班官真实问答历史**（"轴承异常风险高"等研判 + 船员追问，Qwen3-4B-FP8 本地作答）——节点独有数据，演示素材 | `~/shipmind/runs/ai-duty/` |
| `ai-duty-config.json` | <1KB | 值班日志轮转配置 | 同上 |
| `trajectory-agent_demo.jsonl` | 8KB | 端到端编排执行轨迹（含官方 Skill 派发） | `~/shipmind/runs/agent_demo/` |
| `kope67_L_10fps.mp4` | 24MB | MODD2 真实 USV 视频（900 帧 / 90 秒 / 1278×958）——可由本地帧重新合成，但已留成品 | `~/data/modd2/clips/` |
| `heur.log` / `train_full.log` / `webui.log` | ~2MB | 节点侧训练/评测/服务日志（答辩过程证据） | `~/logs/` |
| `node-pip-user.txt` | <1KB | 节点 pip 用户包清单（环境复现参考） | pip3 list |

## 2. 不需要备份的（可再生）

| 项 | 再生方式 |
|---|---|
| 数据集（DCASE 3.2G / DeepShip / SeaShipsSeg / MaSTr1325 / MODD2） | 本地 `D:\datasets` 全量副本；或按 `docs/DATA-LICENSES.md` 重新下载 |
| 评测夹具 | `python3 evals/make_fixtures.py` + `sensors/gauge_synth.py`（确定性） |
| 官方 Skill（`~/.agents/skills`） | 仓库 `official-skills/installed/` 有 vendored 副本 |
| Node 22（`~/.local/node22`） | 重装一条命令（见 NODE-GUIDE） |
| AE checkpoint / 声纹分类器 | 训练脚本在仓库；声纹模型 `models/sonar_clf.npz` 也在仓库 |

## 3. Qwen 模型：只留配置，不留权重

权重（4.9GB）**不下载到本地**——ModelScope 节点内直连，随时重拉。保留的是下载与启动配置：

**权重来源**（ModelScope，节点内下载约 5–10 分钟）：
```
modelscope download --model Qwen/Qwen3-4B-Instruct-2507-FP8 --local_dir ~/models/qwen3-4b-fp8
```

**备选权重**（已在本地 `D:\invadi` 仓库无副本、节点已删，需要时同法重拉）：
```
Qwen/Qwen3-30B-A3B-Instruct-2507-FP8   # 30GB，vLLM 0.25 原生支持，更强本地大脑
Qwen/Qwen3.6-35B-A3B-FP8               # 35GB，vLLM 0.25 不支持其架构，勿选
```

**启动配置**（已固化进仓库 `scripts/node_start_vllm.sh`，照抄即可）：
```
docker run --gpus all --shm-size=16g \
  -e FLASHINFER_DISABLE_VERSION_CHECK=1 \
  -v /home/Developer/models:/models:ro -p 127.0.0.1:9000:9000 \
  qwen-agentworld:vllm bash -c "VLLM_USE_DEEP_GEMM=0 vllm serve <权重路径> \
  --served-model-name <名> --host 0.0.0.0 --port 9000 \
  --max-model-len 8192 --gpu-memory-utilization 0.45 --enforce-eager"
```

⚠️ 预置镜像 `qwen-agentworld:vllm`（vLLM 0.25）若新节点没有，需换基础镜像或查组委会说明——这是唯一无法完全自包化的依赖。

## 4. 新节点重建手册（5 步，约 20 分钟）

```bash
# 1) 同步代码（本地执行）
python scripts/node_deploy.py

# 2) 一键重建（依赖 + 夹具 + 后台下载权重 + 起值班台）
bash ~/shipmind/scripts/node_bootstrap.sh

# 3) 轮询权重下载完成（约 5–10 分钟）
grep -q EXIT_CODE ~/logs/weights4b.log && echo READY

# 4) 起本地大脑（参数已固化）
bash ~/shipmind/scripts/node_start_vllm.sh

# 5) 全量验证（StepFun key 环境变量注入）
cd ~/shipmind && STEPFUN_API_KEY=<key> python3 evals/run_evals.py   # 期望 32/32（2 条真实 MIMII 用例 SKIP）
```

## 5. 节点关停 checklist（本次已执行 ✓）

- [x] AI 值班日志 → `runs/backup/duty.jsonl`
- [x] 执行轨迹 → `runs/backup/`
- [x] MODD2 mp4 成片 → `runs/backup/`
- [x] 服务日志 → `runs/backup/`
- [x] pip 包清单 → `runs/backup/`
- [x] 数据集本地副本确认（D:\datasets）
- [x] Qwen 下载/启动配置固化进仓库（`node_bootstrap.sh` / `node_start_vllm.sh`）
- [x] 仓库全部推送 GitHub（含 .env 排除）
- [ ] 停止自建服务（`tmux kill-server`、`docker rm -f vllm-qwen`）——关停前执行，避免 OOM 孤儿进程
