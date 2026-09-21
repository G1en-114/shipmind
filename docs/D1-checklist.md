# D1 清单（2026-09-20，训练营当天）

目标：今天结束前，主 Agent 能跑通、声学 Skill 有第一版、数据和征文都开个头。不追求效果，追求**闭环存在**。

## 环境（优先，阻塞后面一切）

```bash
# 1. skills CLI（必须 ≥ v1.5.16，旧版装上不显示）
npx skills@latest --version

# 2. 浏览官方目录
npx skills@latest add nvidia/skills --list

# 3. 装本项目要用的官方 Skill
npx skills@latest add nvidia/skills \
  --skill rag-blueprint \
  --skill deepstream-generate-pipeline \
  --skill tao-generate-image-grounding \
  --skill vss-generate-video-report \
  --skill tao-generate-referring-expressions \
  --yes

# 4. 验证
npx skills list && npx skills check
```

- OpenClaw 作为本地会话宿主：无独立 CLI target，把 skill 目录**整目录复制进 workspace**，再 `openclaw skills list --eligible` 验证。
- vLLM 0.28 起本地推理端点；GB10 上必须加 `VLLM_USE_DEEP_GEMM=0` 和 `--moe-backend triton`，否则 DeepGEMM 报 `CUDA_ERROR_INVALID_IMAGE`。
- Step 3.7 Flash：申请 key 或走 NIM 本地部署；接入只需改 `base_url` / `model_name` / `api_key` 三个值。
- StepAudio-Skills：`npx skills add` 装好，语音链路留到 D6 再接，今天只需确认装得上。

## 数据（B 负责，今天至少落到盘）

- 声学：下载 MIMII / ToyADMOS（泵、阀、风机，正好对应机舱设备），确认许可与文件结构。
- 视觉：找海事类他船/漂浮物检测公开数据集，下载一小批（先要能跑，不要贪多）。
- 自录：用手机录 3–5 段机舱/仪表视频，每段 1–2 分钟，覆盖正常与异常两种状态。
- 文本：COLREGs 条文 + 一份公开设备手册样本，整理成 Markdown 供 RAG 使用。

## 仓库与征文（今天必须开头的两件事）

- `git init`，README 已是提交要求里那份项目说明的底稿，往里填即可。
- **征文开栏**：CSDN 或知乎建专栏，发第一篇「十日谈 Day 0：我们为什么做一条船上的副驾」。征文只占 5%，但它是唯一一个今天花 30 分钟就能锁定、且越早开始越省力的分数。

## 今日分工

| 人 | 今天要完成的 |
|---|---|
| A（二进制安全） | 上述环境全部装通；搭 Harness 骨架（Skill 运行时 + 轨迹记录的最小版）；DeepStream 跑通一条示例管线 |
| B（机器学习） | 数据集全部落盘；声学模型 baseline 跑通（先不管精度，先有 extract 和 compare 两个子命令）；建 `evals/cases.jsonl` 并放 3 条用例 |

## 验收标准（今晚自查）

1. 终端里问主 Agent 一个问题，它能正确加载并调用一个官方 Skill。
2. `python scripts/acoustic_sentinel.py extract <音频>` 能输出特征 JSON。
3. 仓库有 README、有一个自研 Skill 的 SKILL.md、有 evals 目录。
4. 征文第一篇已发布。
