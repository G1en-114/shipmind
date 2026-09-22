# ShipMind 项目交接报告

> 撰写：2026-09-22 ｜ 用途：交给更强的 AI 审查并接手
> 仓库：https://github.com/G1en-114/shipmind ｜ 本地：`D:\invadi`
> 提交截止：**2026-09-29** ｜ 预赛结果 10-08 ｜ 决赛路演 **10-15 苏州金鸡湖**

---

## 1. 项目是什么

**ShipMind（智舷）——船舶离线值守多智能体副驾**。参加 NVIDIA DGX Spark Hackathon「Agent Skills 开发挑战赛」（队名 Devx，2 人）。

一句话：把一台 DGX Spark 搬上船，机舱里**听**异响、**看**仪表、**查**手册、**说**处置、**记**日志；驾驶台外**读**雷达、**辨**声纹、**守**航线——全部智能体跑在船端一台设备上。

**核心论证（本地部署必要性，已联网核实）**：《海上交通安全法》第 24 条要求我国管辖海域通信须经境内海岸电台或卫星关口站转接 + 星链海事资费 $1000/月·1TB 起 + 机舱告警需秒级响应。政策顺风：《智能船舶发展行动计划(2019-2021)》三部委联合印发、CCS《智能船舶规范》2026 版 6/1 生效。

**评审权重**：实用性/创新 25% ｜ 智能体与模型优化深度 25% ｜ 完整性 20% ｜ 平台适配 15% ｜ 演示 10% ｜ 征文 5%。

**提交物四件套**：GitHub 仓库（✅）＋ B 站演示视频（❌）＋ 十日谈征文（❌ 素材齐未发布）＋ 团队合影（❌）。

---

## 2. 当前状态（全部可验证）

### 2.1 评测基线

```bash
cd D:\invadi && python evals/run_evals.py     # 期望 31/31
```

GB10 真机上也验证过（25 用例版；新增的官方桥接/大脑路由 6 例尚未在节点重跑，见 §5）。

### 2.2 已完成

| 模块 | 状态 | 证据 |
|---|---|---|
| 自研 Harness | ✅ | `harness/`：注册表/路由（大脑优先+关键词兜底）/输出契约校验/执行轨迹录制回放/编排器 |
| 编排大脑（双端点） | ✅ | 本地 Qwen3-4B-FP8（vLLM 0.25，GB10，离线）↔ Step 3.7-flash API；`scripts/brain_check.py` 三连（含负例）6/6 一致 |
| 9 个自研 Skill | ✅ | 声学哨兵（启发式+AE 双轨）/航线偏离/雷达 PPI（CA-CFAR）/声纹（规则+ML 双轨）/值班日志/视觉巡检/手册 RAG/报告生成/语音播报 |
| 6 个官方 NVIDIA Skill | ✅ 接入 | `official-skills/` vendored（pin `fd9f1466`）；deepstream-generate-pipeline **真跑**返回真实 gst-launch 管线，其余 5 个 advisory 展开并标注前置条件 |
| 端到端编排 | ✅ | `scripts/agent_demo.py`：提问→大脑路由→执行（自研/官方）→轨迹；四连问 4/4 |
| 跨线融合 | ✅ | `scripts/fusion_demo.py`：雷达×声纹×航线×COLREGs 五智能体 → verifier 复核 → 报告+播报 |
| Web 值班台 | ✅ | `web/`：FastAPI 六接口 + 原生 JS 六面板；Edge headless 截图验证渲染 |
| 评测体系 | ✅ | 31 用例（正/负/边界）；`evals/BENCHMARK.md` 声学双轨全量对照 |
| 数据 | ✅ | DCASE 3 机种、DeepShip 四类、MODD2 视频、MaSTr1325、SeaShipsSeg + 四类自产合成 |
| 文档 | ✅ | README（提交用）、PROJECT-PLAN v1.2、MASTER-CHECKLIST、BENCHMARK、NODE-DEPLOY、NODE-INCIDENT、REFERENCES、DATA-LICENSES、DEVLOG |

### 2.3 关键数字（答辩素材）

- **声学双轨全量对照**（DCASE/MIMII，按文件评测）：启发式 pump 0.687 / valve 0.777 / fan 0.630，**三机种全胜** AE（0.602/0.490/0.529）；启发式仅需 200 条建基线，AE 用全量训练集。
- **发现**：AE 带符号重构误差在 pump 上倒挂（0.260），因该子集异常是"信号变更弱"——证伪"异常=误差更高"的默认假设。
- **声纹 ML**：DeepShip 四类按文件划分（防同船泄漏）测试集 0.431（随机 0.25）。
- **视觉**：130 张合成表盘归一化读数 MAE 0.056（红指针 0.029）。
- **CA-CFAR**：检出目标与真值精确吻合，空海面 0 虚警。

---

## 3. 未完成的工作（按优先级）

### P1 演示物料（都要用户参与，最紧）

| 项 | 依赖 |
|---|---|
| B 站视频（脚本已定 6 分钟结构） | 录屏工具 + B 站账号（**用户未定**） |
| 十日谈征文每日发布 | **平台未定**（CSDN/知乎）；Day 0–2 素材在 `docs/DEVLOG.md` |
| 团队合影 | 用户两位同框 |
| 路演 PPT + 演讲稿 + 问答 | 10/8 后；需团队信息（姓名/学校或公司，**未提供**） |

### P2 技术稳健性（审查发现，未修）

| # | 问题 | 建议 |
|---|---|---|
| P5 | 声纹 ML 0.431 绝对值低；DeepShip 仅 46 文件 | 已诚实标注；提升需更多数据/算力 |
| P6 | 视觉有 1 个 0.646 灾难性离群（约 180° 反向），显著性过滤没拦住 | 分析黑指针反向锁定模式，加双峰检验或提高拒判门槛 |
| P7 | voice.py 的 ASR 分支零测试零实测（只有 TTS 用例） | 加一条真实语音用例 |
| P8 | `run_evals` 的声学用例全是合成夹具（80Hz 正弦+噪声），真实 MIMII 只进 BENCHMARK 脚本 | 给 run_evals 加 2 条真实 MIMII 用例（本地和节点都有数据） |
| P9 | 节点代码同步靠手工挑文件，已翻车 5 次（corpus 漏/cases 旧版/sensors 漏/顺序错删夹具/gauges 没生成） | 一律改用 `scripts/node_deploy.py` 整仓部署；正确顺序已沉淀在 `docs/NODE-DEPLOY.md` |

### P3 节点验证缺口

**最新代码（官方桥接、agent_demo、brain 修复、bigram 路由）尚未在 GB10 节点上跑过**。同步时必须带上：`corpus/`、**所有** `skills-src/*/evals/cases.jsonl`、`sensors/`、`models/sonar_clf.npz`、`official-skills/`。StepFun key 经环境变量传（节点不放 `.env`）。

---

## 4. 环境与访问

| 资源 | 详情 |
|---|---|
| **组委会 GB10 节点**（主力算力） | `ssh -p 6065 Developer@106.13.186.155`，主机名 spark-a24e（登录表 spark-65）。凭据在 `D:\invadi\.env`（gitignored）。GB10/ARM64/121GB 统一内存/20 核/Docker 28.3/预置 vLLM 0.25 镜像。**只用于官方节点**，可自动化（paramiko，`scripts/node_check.py`、`remote.py`） |
| StepFun API key | 在 `.env`；模型：step-3.7-flash（262K+视觉）、step-5-preview（1M）、step-tts-2、step-asr |
| 自租付费服务器 | **已弃用**（用户决定只用官方算力）。SeetaCloud RTX PRO 6000，SSH 信息在 `.env`（SEETA_*）。**不要主动使用** |
| 本地开发机 | Windows + Git Bash + Python 3.13（anaconda）；PowerShell 是用户终端 |

---

## 5. 硬约束（不可协商，都是用户明确要求）

1. **不做安全方向**（用户认为该生态已成熟）。二进制安全技能只体现在 Harness 工程化（轨迹录制回放、契约校验）。
2. **宁波海事局执法案不写进任何材料**（用户明确指示）。法条 §24 保留。
3. **声呐表述红线**：只说"被动声纹监测/民用海事感知"，不用军用叙事。
4. **手册语料必须自拟合成**（版权安全），已标注"演示用合成手册"。
5. **凭据不进仓库**：`.env` gitignored；节点上不放 `.env`（key 走环境变量）；提交前 `git log -p | grep -i key` 自查。
6. **节点手册红线**：禁止 reboot/shutdown；禁止 scp >1GB（共享带宽，节点内直下）；公网端口必须加鉴权；长任务进 tmux；预置模型目录只读。
7. **给用户的命令必须是 PowerShell 单行**（不支持 bash 反斜杠续行；scp 用大写 `-P`；用 `Select-Object` 不用 `tail`）。
8. 用户偏好：**他自己的服务器给命令他执行**；官方节点可自动化。

---

## 6. 已知深坑（都踩过，别再踩）

| 坑 | 规避 |
|---|---|
| GB10 统一内存：vLLM 默认 `gpu-memory-utilization 0.9` 会吃光 121GB → 节点 OOM、SSH 认证后会话建不起来 | 必须 `--gpu-memory-utilization 0.45` + `--enforce-eager` + `FLASHINFER_DISABLE_VERSION_CHECK=1`（见 `scripts/node_start_vllm.sh`） |
| vLLM 0.25 不支持 Qwen3.6-35B 架构（`Qwen3_5MoeForConditionalGeneration`） | 本地大脑用 Qwen3-4B-FP8；198B 的 step-3.7-flash 走 API（显存+架构双重不可行，README 已写明） |
| 节点网络：GitHub/HuggingFace/Zenodo 不可达，ModelScope 可达 | 大数据本地下载后同步；模型权重走 ModelScope |
| 节点系统 node 18 跑不动 skills CLI | 用户级 Node 22 在 `~/.local/node22`，远程命令要 `export PATH` 前缀 |
| `harness/brain.py` 的 ROUTER_PROMPT 用 `.format()`，**花括号必须转义**（`{{"skill": ...}}`），否则 `choose_skill` 抛异常被静默捕获 → 路由随机翻车 | 已修；改 prompt 时注意 |
| Git Bash 把 `/tmp/xxx` 参数翻译成 Windows 临时目录，与 Python 内写的 `/tmp` 不一致 | 一律用仓库内相对路径 |
| Windows 本地 `python` 是 anaconda；节点 `python3` 是 /usr/bin/python3（numpy 装在 --user） | 节点交互 shell 是 conda base，没装 numpy——给用户的命令要么 `pip install numpy scipy`，要么用 `/usr/bin/python3` |
| 官方 Skill 装在 `~/.agents/skills`，仓库内 vendored 在 `official-skills/installed/` | 桥接层默认用仓库内副本（自包含） |
| 关键词路由对中文整段匹配失效 | 已改 bigram；大脑失败时兜底才可靠 |
| StepFun API 偶发瞬时失败 → 大脑降级 → 路由可能 None | 重试即可；别当成真 bug |

---

## 7. 快速上手路径（给接手的 AI）

```bash
# 1. 本地全量评测
cd D:\invadi && python evals/run_evals.py                      # 31/31

# 2. 端到端演示（需大脑端点；本地无 vLLM，用 StepFun API）
$env:BRAIN_BASE_URL="https://api.stepfun.com/v1"; $env:BRAIN_MODEL="step-3.7-flash"
$env:BRAIN_API_KEY="<.env 里的 key>"
python scripts/agent_demo.py --batch                           # 4/4 路由+执行

# 3. Web 值班台
python -m uvicorn web.server:app --host 127.0.0.1 --port 8888  # 只绑本地

# 4. 节点操作（凭据在 .env）
python scripts/node_check.py "uptime; free -h | head -2"
python scripts/node_deploy.py                                  # 整仓同步（推荐）

# 5. 冒烟全链路
bash scripts/smoke.sh
```

**文档导航**：`README.md`（项目说明/技术栈/部署）→ `docs/PROJECT-PLAN.md`（方案 v1.2 权威）→ `docs/MASTER-CHECKLIST.md`（总控清单）→ `docs/NODE-DEPLOY.md`（节点部署）→ `evals/BENCHMARK.md`（双轨数据）→ `docs/DEVLOG.md`（开发日志/征文素材）→ `docs/REFERENCES.md`（调研参考）→ `docs/NODE-INCIDENT.md`（OOM 事故记录）。

---

## 8. 给审查者的诚实清单（弱点与风险）

1. **"多智能体协同"的证据链偏薄**：大脑路由是真的、verifier 是真的、官方 Skill 派发是真的；但融合演示（`fusion_demo.py`）仍是固定场景脚本，动态多 Agent 协商/分工没有。评审 25% 那档可能被挑战"协同体现在哪"。
2. **官方 Skill 只有一个真跑**：deepstream-generate-pipeline 有可执行入口所以真跑；其余 5 个受限于 NGC key / TAO 容器 / VSS 服务，只能 advisory。这是如实标注的边界，但"平台适配 15%"的实质证据主要靠 vLLM + 官方 Skill 集成 + skills CLI。
3. **声纹 ML 0.431 是最弱的数字**（虽赢了随机线）。
4. **视觉有一个 180° 反向的灾难性读数**（n=130 中 1 个）。
5. **本地大脑是 4B**，能力有限；198B 无法本地部署（显存+架构），这是硬事实但演示时本地端点的回答质量会明显弱于 StepFun API。
6. **演示依赖 StepFun API**（语音链路、以及选择用 API 端点时的大脑）——断网场景下语音不可用，这一点已在 README 如实标注，但若评委要求"完全离线演示"，需要提前切换到本地端点并预录语音。
7. **代码质量**：单文件脚本为主、缺少单元测试框架、部分脚本有重复逻辑；对黑客松节奏是合理取舍，但不是生产级。
8. **未上船实测**，数据以公开数据集+仿真源为主（已如实标注）。

---

## 9. 建议的下一步顺序

1. **同步最新代码到节点并跑 31/31**（带上 §3-P3 列的全部文件）——闭合"DGX Spark 部署"证据链。
2. 修 P6（视觉离群）→ P8（真实 MIMII 用例）→ P7（ASR 用例），都是 1 小时内可完成的稳健性修复。
3. **催用户定三件事**：征文平台、B 站账号、团队信息。
4. 9/27–28 演示物料周：录屏（本地端点 + StepFun 端点各录一版）、剪辑、发 B 站、征文补齐、合影。
5. 9/29 提交四件套；10/8 后若晋级，PPT + 演讲稿 + 现场彩排。
