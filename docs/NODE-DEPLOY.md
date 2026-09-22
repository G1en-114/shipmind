# GB10 节点部署清单（DGX Spark 真机验证）

2026-09-22 实测：**25/25 评测在 spark-65（GB10 / ARM64）全绿**。

## 1. 依赖

```bash
pip3 install --user --break-system-packages numpy scipy pillow fastapi uvicorn
```

- numpy / scipy：声学 AE、声纹 ML、float32 wav 读取
- pillow：视觉巡检、表盘合成
- fastapi / uvicorn：值班台

## 2. 代码与数据同步

从本地（Windows）同步到节点 `~/shipmind/`：

- 代码：`harness/` `sensors/` `skills-src/` `models/*.py` `evals/*.py` `scripts/` `web/` `tools/`
- 语料：`corpus/manuals/*.md`（RAG 检索源，**必须同步，否则检索无命中**）
- 模型：`models/sonar_clf.npz`（声纹 ML 轨）
- 评测用例：**所有** `skills-src/*/evals/cases.jsonl`（漏同步会引用旧夹具路径）

夹具在节点上重新生成（不入 git）：

```bash
cd ~/shipmind && rm -rf evals/fixtures \
  && python3 evals/make_fixtures.py \
  && python3 sensors/gauge_synth.py --out evals/fixtures/gauges --n-train 100 --n-val 30
```

## 3. 凭据

节点**不放 .env**。StepFun key 经环境变量传入（节点手册要求凭据不进共享位置）：

```bash
STEPFUN_API_KEY=<key> STEPFUN_BASE_URL=https://api.stepfun.com/v1 python3 evals/run_evals.py
```

## 4. 踩过的坑

| 现象 | 原因 |
|---|---|
| RAG 三条用例"无命中" | `corpus/` 未同步 |
| acoustic 两条 rc=2 | 节点上是旧版 `cases.jsonl`（引用已改名的夹具路径） |
| visual/report rc=1 | 夹具未在节点生成；且先同步 report 夹具后又 `rm -rf evals/fixtures` 把它删了——**顺序应是先清目录、再生成、最后同步增量** |
| voice rc=2 | 节点无 .env，key 需环境变量传入 |
| gauges 目录缺失 | `sensors/gauge_synth.py` 未同步 |

## 5. 已知节点限制

- GitHub / HuggingFace / Zenodo 从节点不可达（ModelScope 可达）→ 大文件走本地下载后同步
- 系统 node 18 跑不动 skills CLI（已装用户级 Node 22 于 `~/.local/node22`）
- 预置 vLLM 镜像 0.25 不支持 Qwen3.6-35B 架构（`Qwen3_5MoeForConditionalGeneration`），
  本地大脑用 Qwen3-4B-FP8；启动参数见 `scripts/node_start_vllm.sh`
