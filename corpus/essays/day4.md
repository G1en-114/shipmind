# 十日谈 · Day 4（2026-09-24）：六十一秒宣传片，零外部素材

> 本文是"十日谈"第五篇。[Day 0](链接) · [Day 1](链接) · [Day 2](链接) · [Day 3](链接)。

## 起因：评委不会读完 README

技术线收尾那天我们意识到一个问题：README 写了 13700 字、评测 34/34、双端验证——但这些**评委不一定会看完**。报名要求里有一条"作品演示视频，上传 B 站"，而大多数评审的真实行为是：先看视频，有印象才翻代码。

所以今天的主任务只有一个：**把 60 秒宣传片做出来**。

## 一条铁律：零外部素材

定规则的时候我们想清楚了一件事：宣传片里出现的每一帧、每一个声音，都必须能回答"从哪来"。

- **画面**：全部来自真实 Skill 输出——值班台的雷达 PPI、声学频谱、表盘读数、融合链路的结论面板。没有一张 stock 图。
- **音效**：全部用 numpy 合成——撞击声是正弦+噪声+指数衰减，纸感翻页是带通噪声+82Hz 毛毡残响，敲击提示是正弦短音。`scripts/video/sfx.py` 一百行,零音频文件引用。
- **配音**：Windows 自带 SAPI 合成，再用 atempo 链把语速拟合到分镜时间窗。不请配音、不蹭 TTS 配额。
- **字体/背景**：系统字体 + 程序化绘制的渐变。

结果：60 秒、1920×1080、30fps,成片 107MB,**全链路可复现**——`collage.py` 一条命令从帧序列渲染成片，`sfx.py` 生成音效床，`voiceover_build.py` 混音。这也回答了许可问题：整条片子没有任何需要授权的素材。

## 六幕结构与十一次迭代

分镜（`timeline.json`）讲了完整的故事：

```
0–6s   MID-OCEAN        "One watch. Too many signals."
6–17s  NVIDIA DGX SPARK "The local compute behind ShipMind."
17–28s FOUR STREAMS     "Acoustics · Gauge · Radar · Route"
28–44s ASK: HOW ARE THINGS NOW?（本地 Qwen3-4B 约 3 秒作答）
44–54s THE PLATFORM STACK（Agent Skills · DeepStream · StepFun · Qwen · vLLM）
54–60s INTELLIGENCE STAYS ON BOARD · Team Devx
```

从 v3 到 v11 迭代了九版：v5 加了开场、v6/v8/v9 调转场、v10 出有声版、v11 重新配音。中间还有一个有意思的听感修正：最初过场用的是"预告片式 whoosh+重击"，复看 v11 后觉得太闹、抢了配音，把音效换成了柔和的翻页声，并把音量压到配音之下——**宣传片是给信息服务的，不是炫技**。

## 一个意外的技术收获

本地没有 ffmpeg，配音对齐怎么办？发现 `imageio_ffmpeg` 包自带一个 ffmpeg 二进制——`voiceover_build.py` 调它做变速和混音。这条经验也写进了 README 的依赖说明候选。

## 反思：为什么只有 60 秒

初稿想做 3 分钟，砍到 60 秒的过程砍掉了三分之一的"功能展示"。最后留下的判断标准是：**每一秒必须让评委看到"这东西真的在跑"**——雷达目标在动、频谱在跳、表盘读数和检测框都在真实 Skill 输出上。功能清单在 README 里，演示负责让人相信它。

## 明天

值班官语音链路进宣传片（v12 若配音轨需要），然后开始录值班台实操片段——宣传片是"电影"，实操录屏是"证据"，两者缺一不可。

---

*本系列是 DGX Spark 黑客松"十日谈"开发记录，项目代码开源（Apache-2.0）：[GitHub 仓库](链接)。宣传片全链路可复现：`scripts/video/`（collage / sfx / voiceover_build），时间线在 `timeline.json`。*
