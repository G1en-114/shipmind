# NVIDIA DGX Spark 黑客松 · Agent Skills 开发挑战赛 —— 备赛浓缩笔记

> 整理日期：2026-09-20（线上训练营当天）
> 来源：官方活动页 + 赛事规则截图（评审标准 / 提交要求）+ 三份训练营讲义
> （何琨《DGX Spark 本地视觉 Agent 技能开发实战》、刘春晖《NVIDIA Skills 开发实战》、周旭《StepFun 多模态 × NV-AgentSkills Harness 演进实践》）

---

## 1. 赛程与关键节点 ⏰

| 阶段 | 时间 |
|---|---|
| 线上训练营（规则讲解＋技术实战课） | **9 月 20 日** 10:00–12:00 |
| **预赛作品提交（截止！）** | **9 月 20 日 — 9 月 29 日** |
| 预赛评选 | 9 月 30 日 — 10 月 8 日 |
| 总决赛暨现场路演 | **10 月 15 日** 13:30–17:00，苏州金鸡湖国际会议中心 A 馆 A109-110 |

- 咨询邮箱：`china_developer@nvidia.com`（建议将 nvidia.com 加入邮箱白名单）
- 特邀合作伙伴：赞奇科技 XSUPERZONE、阶跃星辰 StepFun、华硕 ASUS
- 讲师：何琨（NVIDIA 开发者社区，CV/HPC）、刘春晖（NVIDIA 电信行业 AI 解决方案，LLM/Token Factory/AI Agent）、周旭（StepFun StepCLI 产品负责人）
- 同期：NVIDIA 中国开发者日（10.15 动手实践日＋认证考试；10.16 主论坛日＋颁奖）

## 2. 评审标准（决定精力怎么分配）

| 维度 | 权重 | 要点 |
|---|---|---|
| 项目实用性、行业落地价值与技术创新性 | **25%** | 技术实现/架构/方案有创新，充分体现 DGX Spark 平台优势，突破传统思路、解决技术痛点 |
| 智能体与模型优化技术深度 | **25%** | 多智能体协同、模型调优深度、**Skills 设计与融合**、差异化技术方案 |
| 项目完整性 | **20%** | 功能完整、运行稳定、前后端完整、文档规范详实、可顺利完成演示 |
| 平台适配性 | **15%** | 充分发挥 DGX Spark 全栈能力，合理运用 NVIDIA 技术栈/开源模型/SDK，**以及 StepFun 阶跃星辰模型的使用** |
| 演示效果 | **10%** | Demo 视频流畅、展示清晰、逻辑严谨 |
| 赛事征文 | **5%** | 黑客松"十日谈"开发历程 |

## 3. 提交物清单（全部以 URL 提交到组委会表单）

1. **项目开源**：完整项目上传 GitHub / 码云。仓库内需包含：
   - 项目说明文档（**≥500 字**：作品特点、核心亮点、技术实现方案、架构设计思路、优化方案）
   - 部署说明（如何利用**本地算力**部署智能体、如何优化大模型、如何设计 Agent Skills）
   - 技术栈说明（列明所用 **NVIDIA SDK、NVIDIA 及 StepFun 阶跃星辰模型**）
   - 以上可用 README 形式体现，**必须包含 skill markdown 文件**
2. **作品演示视频**：上传 B 站，提交链接
3. **十日谈征文**：CSDN / 知乎等技术社区记录历程，提交链接
4. **团队资料**：团队合影，提交表单

群规纪律：仅交流技术与赛事内容；问题反馈组委会（勿在社媒发不当言论）；社媒分享 AI 作品须标注 AI 生成；**勿泄露 API 账号、密钥等敏感信息**。

---

## 4. 技术底座：Agent Skills 是什么

- **Agent = LLM + Harness**：Harness 是跑 agent 的那层壳（Context → Observe → Reason → Act 循环、记忆、路由、技能加载、安全治理）。
- **Skill = 一个目录**：`SKILL.md + scripts/ + references/ + evals/`。frontmatter 的 `name / description` 决定何时被触发；渐进式披露三层：
  1. 常驻：name + description ≈ **100 token**；
  2. 命中任务：展开 SKILL.md 正文（建议 <5K token）；
  3. 执行需要时：才读 scripts / references / assets。
- 长 prompt 是一次性代码，skill 是**可复用、可校验、可分发**的专家经验资产（"让每一段 prompt 都能活第二次"）。
- 生态规模：官方目录 `github.com/NVIDIA/skills` 从产品仓**每日自动同步**；41 条产品线、300+ verified skills（2026-09 口径；StepFun 口径 2026-08 为 343 个）；仓库 5 个月 ★3,181 / 373 forks；skills.sh 前 100 个 skill 累计安装 ~187,000 次；50+ 客户端收敛到同一格式（Anthropic 开源规范，跨 Claude Code / Codex / Cursor / OpenClaw / Kiro / Aider 等）。

## 5. "NVIDIA-verified" 信任链（理解治理，写进文档加分）

**Verified = Cataloged + Scanned + Evaluated + Signed + Documented**，五件套缺一不进目录：

| 关卡 | 回答的问题 | 证据产物 |
|---|---|---|
| Cataloged | 谁拥有这个能力 | 产品团队源仓库每日同步 |
| Scanned（SkillSpector Tier1） | 运行安全吗 | 68 种漏洞模式/17 类别（提示注入、越权、工具投毒、供应链等；对齐 OWASP LLM Top10 / MITRE ATLAS），高危直接拦截 |
| Evaluated（SkillEvaluator Tier3） | 真的有用吗 | 同一 Agent 同一任务集带/不带 skill 各跑一遍，差值即实测贡献；5 维度 Security/Correctness/Discoverability/Effectiveness/Efficiency，发布为 BENCHMARK.md；evals 必须含负向用例 |
| Signed（OMS 签名） | 下载后被篡改过吗 | OpenSSF 规范、逐文件分离式签名 `skill.oms.sig`，NVIDIA 根证书验证 |
| Documented（Skill Card） | 用户接受了什么 | 描述/Owner/License 与部署地域/依赖凭据/风险与缓解 |

参考数据（官方 BENCHMARK 提升，claude-code）：Correctness 96%(+81)、Discoverability 90%(+70)、Effectiveness 80%(+75)、Efficiency 71%(+40)。
治理分层：**运行时管行为**（NeMo Guardrails / OpenShell / NemoClaw 沙箱），**技能层管能力准入**（Verified Skills）。

## 6. 上手：安装与选型

四条命令（需 skills CLI ≥ v1.5.16，用 `skills@latest` 避免旧版装上不显示）：

```bash
npx skills@latest add nvidia/skills --list          # ① 浏览目录
npx skills@latest add nvidia/skills                 # ② 交互式安装
npx skills add nvidia/skills --skill rag-blueprint --yes   # ③ 装指定 skill（可重复 --skill）
npx skills list && npx skills check && npx skills update   # ④ 检查与更新
```

- `--agent claude-code | codex | cursor | kiro-cli | cortex …` 可重复指定多个目标；Claude Code 里 `/reload-skills` 当场生效。
- OpenClaw 无独立 CLI target：固定官方提交后**整目录复制进 workspace**，再 `openclaw skills list --eligible` 验证。

**选型方法——从任务出发，不从产品名出发**（5 步）：
1. 先说清目标动作：部署 / 生成 / 训练 / 检索 / 评估 / 排障？
2. 在 Catalog 找最接近的 Skill，读 description 与「不适用」范围（Negative Triggers）；
3. 检查前置依赖：硬件、凭证、产品版本；
4. 读 skill-card.md 的风险与许可（能否商用、部署地域）；
5. 先跑最小样例再接业务数据，记录所用上游 commit。

**写 Skill 三条心法**：① 窄触发、强路由（SKILL.md 是路由表不是百科）；② 前置提问（关键参数缺失先问用户，禁止猜）；③ 安全边界内嵌（不改 checked-in 配置、不打印明文 token、能复用缓存就不调贵模型）。

## 7. Skill 目录速览与重点产品线

覆盖 8 大类：Agentic AI（rag-blueprint、aiq-research、nemo-retriever）、数据科学与优化（accelerated-computing-cudf、cuopt-routing-api-python、portfolio-optimization）、推理与部署（dynamo-*）、训练 AI（nemo-*、mcore-run-on-slurm）、Vision AI（deepstream-*、vss-*、tao-*）、Physical AI（omniverse-cad-to-simready、paidf-auto-labeling）、边缘与基础设施（jetson-llm-serve、jetson-memory-audit）、科学与医疗（cudaq-guide、nv-segment-ct、earth2studio-*）。

| 产品线 | 垂类场景 | 落地形态 |
|---|---|---|
| RAG Blueprint（3 skills） | 企业知识库 / 智能客服 | Docker Compose / Helm 一键全栈 RAG，触发词 deploy/enable/troubleshoot/shutdown |
| cuOpt + Portfolio（6+1） | 物流调度 / 量化金融 | LP/QP/VRP 求解、Mean-CVaR 组合优化 |
| VSS（15 skills） | 安防 / 视频运营 | 边缘视频搜索与摘要；"理解视频"实为 4 个 skill：vss-ask-video / vss-summarize-video / vss-search-archive / vss-generate-video-report |
| DeepStream（13 skills） | 工业视觉 / 智慧交通 | generate-pipeline → import-vision-model → profile-pipeline 产出 pyservicemaker 代码 |

## 8. 参考架构：DGX Spark 本地视觉 Agent（何琨 demo，可作架构蓝本）

调用栈：**OpenClaw**（本地会话·工具调用·workspace Skill 加载）→ 官方 TAO Skill / 自研 Skill（任务契约与执行顺序）→ **TAO 7.1.0 Data Services（ARM64，auto_label 等）** → **vLLM 0.28.0**（OpenAI 兼容 API）→ **Qwen3.6-35B-A3B-FP8**（本地多模态）→ 交付 JSON / KITTI / 带框图片（OpenClaw mediaUrl 回传）。

- 硬件：NVIDIA GB10，ARM64/SBSA；模型 35B 总参 / ~3B 激活，权重 ~37.5GB，Demo 用 65K context，国内可从 ModelScope 下载。
- **GB10 实测修复**：`VLLM_USE_DEEP_GEMM=0` + `--moe-backend triton`，否则自动选 DeepGEMM 报 `CUDA_ERROR_INVALID_IMAGE`。
- **核心原则：官方 Skill 保持原样（pin 上游提交，保留 skill-card/签名/评测），环境差异放外部适配层**（`workspace/tools/run-official-skill.sh` 处理本地端点与容器适配）。改了官方 Skill 签名即失效——修改要么进适配层，要么进自研 Skill。
- **串联示范**：`tao-generate-image-grounding`（图片+caption → 短语·像素框·score，开放词汇定位）→ KITTI 转换 → `tao-generate-referring-expressions`（KITTI 框 → 区域描述·整图 caption·double_check 复核）→ 自研后处理。**能不能串起来看输出契约，不看名字**。
- **自研 Skill 范例 `local-pedestrian-detector`**：
  - 结构：`skills-src/<name>/SKILL.md + scripts/run.sh + scripts/pedestrian_detect.py`；
  - 8 步数据流：逐行人 caption → Grounding（官方）→ KITTI 转换 → Referring Expressions（官方）→ person 类筛选 → IoU 去重 → 0–1000 坐标回映射原图尺寸 → JSON + 带框 JPEG；
  - 禁止行为（不推断身份/年龄/国籍/关系/意图）**写进 SKILL.md**，不靠提示词临时叮嘱；
  - **输出回传契约**：最终回复最后一个非空行必须是纯文本 `MEDIA:/绝对路径/result.jpg`——"生成了文件 ≠ 用户看到了图片"，输出通道也是契约的一部分。

## 9. StepFun 模型接入（平台适配性 15% 明确要求）

- **Step 3.7 Flash**（2026-05-28 发布）：198B 总参 / 11B 激活，1.8B 原生视觉编码器，256K 上下文，图+视频输入，生产级工具调用，最高 400 tok/s，**Apache 2.0 开源，Day-0 上线 NVIDIA NIM**（NVFP4 + NeMo 配方）。多模态线与 Agent 线在一代产品上合流：多模态和工具调用走同一 MoE 主干，无需外挂视觉 MCP。
- **换模型 = 改三个值**：`base_url` / `model_name` / `api_key`（NVIDIA tao 类 skill 的 SKILL.md 原文即 "...or any other OpenAI-compatible endpoint"）。能力侧还有 StepAudio-Skills（TTS/ASR/语音推理，npx skills 安装）。
- ⚠️ **接口兼容 ≠ 行为等价**：换模型必须过回归评测（跑 evals 对比）。
- 分工口径：**MCP 管连接，skill 管知识，harness 管调度**——三件事各管各的；操作给 CLI、决策给路由、能力给技能。
- 官方 VSS 部署 demo 参考组合：Agent 用 Qwen3.8-Flash-Next，Pipeline 用 Nemotron-3.5-Lightning-30B-A3B-NVFP4(-DSpark) / Qwen3-VL-4B-Instruct-FP8；`vss-deploy-profile` 的 SKILL.md 只做路由表，细节内置产品团队验证过的知识（DGX Spark 用 30081 端口 standalone LLM；`.env` 不得直接改，走 copy → generated.env → dry-run → resolved.yml）。

## 10. 已知坑与边界（提前规避）

- skills CLI 旧版装上不显示 → 用 `skills@latest`（≥v1.5.16）。
- vLLM 在 GB10 上 DeepGEMM 报错 → 见第 8 节修复参数。
- 触发稳定性：Claude 等常不主动触发（HN 称 "silent failure"）→ 触发词工程（正/负 triggers 写进 description）是方向，仍需自测。
- 目录碎片化：`.claude/skills` 与 `.agents/skills` 各自为政 → Vercel skills CLI 跨 agent 建链解决。
- 信任根自分发：根证书放在仓库里由被验证者分发，属治理层已知软肋（可作方案讨论点）。
- 一个 skill 可以通过所有安全检查却让 Agent 表现更差 → 一定要跑带/不带 skill 的对照（Tier3 思路），评审的"技术深度"分就藏在这里。

## 11. 备赛映射：评审标准 → 行动清单

| 评分项 | 对应动作 |
|---|---|
| 创新+落地 25% | 选一个真实行业痛点场景；用「官方 Skill 串联 + 自研 Skill」结构（参照第 8 节范式），突出 DGX Spark 本地/离线/隐私优势 |
| 技术深度 25% | 多智能体协同（主 agent + 子 agent 分工）；模型调优（量化/上下文/预算控制）；自研 skill 带 evals + 对照评测数据 |
| 完整性 20% | 前后端跑通、README 规范（500+ 字、部署说明、技术栈说明、**skill markdown 文件**）、现场可复现演示 |
| 平台适配 15% | 明确列出 NVIDIA SDK/技术栈（TAO、vLLM、NIM、skills CLI…）**＋ StepFun 模型**（如 Step 3.7 Flash 做 agent 大脑，改 3 个值接入并附回归评测） |
| 演示 10% | B 站视频：脚本化、3–5 分钟内讲清痛点→架构→现场运行→结果可视化（带框图/报告输出） |
| 征文 5% | 开赛即建 CSDN/知乎专栏，按"十日谈"节奏记录（也反哺 README 素材） |

**最紧的 deadline：9 月 29 日提交全部作品（GitHub 开源 + B 站视频 + 征文链接 + 团队合影）。**
