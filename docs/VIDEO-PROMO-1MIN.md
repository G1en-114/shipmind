# ShipMind 一分钟宣传片 v10

定位：英文主画面、60 秒、1920×1080、30 fps。视觉概念为 **“一页不断被贴满的航海日志”**。本片只负责建立记忆点和证明真机工作负载，完整功能操作留给五分钟演示。

## 视觉系统

全片保持混合媒材拼贴画，不切换成普通科技宣传片：米白海图纸、夜海照片残片、撕纸纤维、半透明和纸胶带、半调网点、橡皮章、红笔圈注和轻微错版印刷。产品截图作为贴在日志页上的“证据照片”，不能直接全屏硬切。

| 项目 | 规则 |
|---|---|
| 色彩 | 米白 `#f5f1e6`、海图蓝 `#14304d`、信号蓝 `#0071e3`、告警橙 `#ff9500`、危红 `#ff3b30`、声呐绿 `#34c759` |
| 字体 | 标题逐字母独立剪贴，混用粗无衬线、衬线、窄体与打字机字形；统一基线、受控字距和约 ±3° 倾角，保证可读性 |
| 动效 | 以 12 fps 量化运动，再输出 30 fps；卡片落定带轻微回弹；转场只用撕、贴、翻、盖章 |
| 阴影 | 真实纸片短阴影，禁止霓虹、玻璃拟态、3D 金属和发光 HUD |
| 证据 | 装饰底图允许 AI 生成；频谱、表盘、雷达、AI 回答必须来自真实 Spark 页面或计算结果 |

装饰底图已生成并固化为 `scripts/video/assets/gen/nautical-collage-bg-v1.png`。它没有文字、品牌和产品 UI，只承担海图纸与夜海拼贴质感。

底图不是静帧。每个场景都会重新裁切和排列夜海、海图、半调纹理与胶带碎片；碎片分别从画外进入，撕裂边缘持续低频起伏，折痕的高光和阴影沿纸面缓慢移动。场景切换时更换素材占位和主次关系，不能让同一张海图在六个镜头中保持同一构图。

v10 以 v6 的稳定构图和阅读节奏为基准。主场景之间参考 `transition-reference.mp4` 的物体转场：Spark 设备退成证据卡堆，雷达与声呐纸片收拢后揭示 AI 操作台，操作台缩成六张平台缩略卡，末段品牌卡向外散开。转场只移动拼贴物件，不缩放整幅画面；落稳后标题、产品、卡片和字幕保持静止。第二幕将 Spark 放在左侧，规格信息改成彩色报纸档案卡。第四幕将真实操作台放在左侧，右侧使用专门生成的航海 AI 值班官拼贴主体，以雷达、声学纸带和 `ASK / TRACE / CITE` 标签解释人的判断路径。末幕以货船为主体，并加入 `SAFER SHIPS · CLEARER DECISIONS` 双层便签。

信息卡不能单独出现。每张文字纸片必须和对应的物件碎片组成一个视觉单元：异响配波形、手册配书页与书签、日志配表格、声学配频谱、表盘配指针、雷达配回波、航线配折线。标题固定在左上纸签，主要证据占右侧或下方，印章只承担结论，不与主证据争抢中心。

## 60 秒分镜

### 0:00–0:06 · 一个人，一整条船

- 夜海残片压在海图纸左侧，标题贴纸：`03:00 · MID-OCEAN`。
- 三张窄纸条依次落下：`FAULTS CAUGHT BY EAR`、`MANUALS HARD TO SEARCH`、`LOGS WRITTEN BY HAND`。
- 镜像后的彩色货船剪贴从右侧进入并占据画面右半边；它位于背景之上、全部标题/标签/字幕之下，不遮挡信息。
- 红章：`OFFLINE FIRST`。
- 不再展示未经核实的卫星通信价格。

### 0:06–0:17 · NVIDIA DGX Spark 主镜头

- `NVIDIA DGX SPARK` 大标题像报纸头版标题拍落。
- 设备占画面约 55%，使用经官方产品图检索校对后的早期报纸风格剪贴素材：泛黄新闻纸、粗网点、双色油墨、交叉排线和轻微套印偏差。
- 三张规格纸签依次进入：`GB10 GRACE BLACKWELL`、`128 GB UNIFIED MEMORY`、`ALWAYS-ON AGENT WORKLOAD`。
- 蓝章：`RUNNING THE WORKLOAD`。这一镜先让评委看见平台主体，再进入 ShipMind 工作负载。

### 0:17–0:28 · 四路证据

- 标题：`FOUR STREAMS · ONE BRIEFING`。
- 四张证据卡错位落下：声学、高置信度表盘读数、雷达目标数量、航线横偏；另加入水听器与流动频谱剪贴，说明声呐证据来源。
- 数据来自演示时的当前快照，画面角落持续显示 `SYNTHETIC INPUTS · REAL SPARK COMPUTE`。
- 红章：`HUMAN REVIEW`。

### 0:28–0:44 · 视觉高潮：AI 值班操作台

- 横向裁切 Spark 真机英文界面 `spark-ai-english.png`，作为带撕边、胶带和纸影的证据照片贴入。
- 先出现提问：`ASK: HOW ARE THINGS NOW?`
- 操作台滚动显示 `OBS → YOU → AI`，重点圈出当前状态、证据和人工复核建议。
- 绿色印章：`~3s ON SPARK`。
- 这一段必须保留页面中的“合成演示 / 合成观测”标识。

### 0:44–0:54 · 主办方产品栈

- 六组带图形的拼贴纸片：`NVIDIA DGX SPARK`、`NVIDIA AGENT SKILLS`、`DEEPSTREAM`、`STEPFUN 3.7 FLASH`、`QWEN3-4B-FP8`、`VLLM`。
- 产品名使用准确的文字纸签而非生成式 Logo；每项注明其在当前工作路径中的真实角色。
- 红章：`34 / 34 CURRENT CHECKS`。不使用“六个官方服务都已运行”的表述。

### 0:54–1:00 · 收束

- 大标题：`INTELLIGENCE STAYS ON BOARD`。
- 红章：`SYNTHETIC · REVIEWED · REPRODUCIBLE`。
- `github.com/G1en-114/shipmind` 打字出现，最后 0.8 秒淡黑。

## 英文配音

录音用定稿、读音和表演提示见 `docs/VIDEO-VOICEOVER-EN.md`；剪辑对齐文件见 `runs/delivery/video/shipmind-voiceover-en.srt`。

| 时间 | 配音 |
|---|---|
| 0:00 | At three a.m., an unfamiliar vibration breaks a ship's steady rhythm. |
| 0:06 | With NVIDIA DGX Spark onboard, ShipMind brings powerful local AI to the watch—compact, responsive, and ready beyond the network. |
| 0:17 | It unites acoustics, gauges, radar, sonar, and route movement into one clear, evidence-backed picture. |
| 0:28 | The engineer asks, “How are things now?” In seconds, the local AI traces the change, cites the signals, and shows what to inspect next. |
| 0:44 | Agent Skills, DeepStream, StepFun, Qwen, and vLLM turn Spark into a complete, reproducible workflow. |
| 0:54 | Safer ships. Clearer decisions. ShipMind. |

约 91 词，留出纸张声、键盘声和盖章声的呼吸空间。先录制配音，再微调镜头边界，不通过加速配音强行卡时长。

## 事实边界

| 可以说 | 不可以说 |
|---|---|
| 代码和模型实际运行在 DGX Spark | 已接入真实船载传感器 |
| Qwen 真机问答约 3 秒 | 所有回答都固定为 3 秒 |
| 当前回归 34/34 | 模型已达到生产安全等级 |
| 输入为合成夹具和本地回放 | 输入为实时船舶遥测 |
| 已集成官方 Skill；演示中实际执行 DeepStream 管线生成 | 六个 NVIDIA 官方服务都已完整部署运行 |
| 声纹是独立演示样本 | 声纹已经和雷达目标完成身份关联 |

## 制作文件

- 时间线：`scripts/video/timeline.json`
- 渲染器：`scripts/video/collage.py`
- 装饰底图：`scripts/video/assets/gen/nautical-collage-bg-v1.png`
- Spark 报纸风格主体：`scripts/video/assets/gen/dgx-spark-newspaper-v2.png`
- 货船剪贴：`scripts/video/assets/gen/cargo-ship-newspaper-v1.png`
- 雷达剪贴：`scripts/video/assets/gen/marine-radar-newspaper-v1.png`
- 声呐剪贴：`scripts/video/assets/gen/sonar-hydrophone-newspaper-v1.png`
- AI 值班官剪贴：`scripts/video/assets/gen/ai-duty-officer-collage-v1.png`
- Spark 英文真机截图：`runs/ui-review/spark-ai-english.png`
- 6 秒开场样片：`runs/delivery/video/shipmind-collage-v5-intro-preview.mp4`
- 60 秒无声母版：`runs/delivery/video/shipmind-promo-v5-silent.mp4`
- 母版接触表：`runs/delivery/video/shipmind-promo-v5-contact.jpg`

v7 最终交付：

- 带普通音效成片：`runs/delivery/video/shipmind-promo-v7-sfx.mp4`
- 无声母版：`runs/delivery/video/shipmind-promo-v7-silent.mp4`
- 独立普通音效轨：`runs/delivery/video/shipmind-promo-v7-sfx.wav`
- v7 接触表：`runs/delivery/video/shipmind-promo-v7-contact.jpg`
- 音效生成器：`scripts/video/sfx.py`
- 音视频封装器：`scripts/video/mux_sfx.py`

v8 最终交付：

- 带普通音效成片：`runs/delivery/video/shipmind-promo-v8-sfx.mp4`
- 无声母版：`runs/delivery/video/shipmind-promo-v8-silent.mp4`
- 独立普通音效轨：`runs/delivery/video/shipmind-promo-v8-sfx.wav`
- v8 接触表：`runs/delivery/video/shipmind-promo-v8-contact.jpg`

当前 v7 无声母版已验收为 1800 帧、1920×1080、30 fps、60.0 秒，文件大小 121,275,674 字节，SHA-256 为 `B06B20E56317D17B62F216B4A47E4EA5D91DEB4C79337C39BA03908AE4C02E01`。

v7 带音效成片同样为 1800 帧、1920×1080、30 fps、60.0 秒；音轨为 48 kHz 双声道 AAC，独立 WAV 为 48 kHz 双声道、60.0 秒。带音效文件大小 123,221,560 字节，SHA-256 为 `383BA59220C7FA1CBE808DF9F7B804711B34DD22981876D195703667004E3735`。

v8 带音效成片为 1800 帧、1920×1080、30 fps、60.0 秒，文件大小 98,309,230 字节，SHA-256 为 `1F8744033A0F8846844C49AE55B00CAEF96A59C928AA25639F1E3905FBEBC7B7`。

v9 最终交付：

- 完整男声与音效成片：`runs/delivery/video/shipmind-promo-v9-voiced.mp4`
- 无声母版：`runs/delivery/video/shipmind-promo-v9-silent.mp4`
- 独立中年广播男声轨：`runs/delivery/video/shipmind-voiceover-v9.wav`
- 男声与普通音效混音：`runs/delivery/video/shipmind-promo-v9-voice-sfx.wav`
- v9 接触表：`runs/delivery/video/shipmind-promo-v9-contact.jpg`
- 转场参考片工作副本：`runs/delivery/video/transition-reference.mp4`
- 转场预览：`runs/delivery/video/shipmind-collage-v9-transition-preview.mp4`

男声采用中年英文广播音色方向合成，并按参考样本的低沉、稳重、近讲质感做速率、音高、均衡与动态处理；它是音色方向匹配，不宣称对样本说话人的精确克隆。旁白期间普通音效自动避让。

v9 完整成片已验收为 1800 帧、1920×1080、30 fps、60.0 秒；音轨为 48 kHz 双声道 AAC。文件大小 98,548,130 字节，SHA-256 为 `B4DC241DF8022D1FBA51D7930B2EFB49131D4C28229F3E3452843B59D1243669`。

v10 最终交付（当前推荐版本）：

- 完整男声与音效成片：`runs/delivery/video/shipmind-promo-v10-voiced.mp4`
- 无声母版：`runs/delivery/video/shipmind-promo-v10-silent.mp4`
- 独立中年广播男声轨：`runs/delivery/video/shipmind-voiceover-v10.wav`
- 男声与普通音效混音：`runs/delivery/video/shipmind-promo-v10-voice-sfx.wav`
- 同步英文字幕：`runs/delivery/video/shipmind-voiceover-en.srt`
- v10 接触表：`runs/delivery/video/shipmind-promo-v10-contact.jpg`

v10 完整成片已验收为 1800 帧、1920×1080、30 fps、60.0 秒；音轨为 48 kHz 双声道 AAC。文件大小 107,546,544 字节，SHA-256 为 `C1ECEE0986C68DFA3D3EB286CAC3DCC0180D9C6BEDDEBE6A83AAB044B2253A20`。

生成压缩样片：

```powershell
python scripts\video\collage.py --mode preview
```

生成 60 秒无声母版：

```powershell
python scripts\video\collage.py --mode full
```

无声母版输出为 `runs/delivery/video/shipmind-promo-v10-silent.mp4`。配音与纸张、键盘、雷达、声呐、盖章等普通音效由脚本生成和混音，便于按同一时间线复现。

## 发布前检查

- [ ] 截图中没有节点 IP、账号、密码或隧道信息。
- [ ] “合成演示 / 合成观测”在产品证据镜头中清晰可见。
- [ ] AI 回答没有无依据的压力高低判断，也没有把声呐样本绑定到雷达目标。
- [ ] `34/34`、约 3 秒和日志上限与最终提交号的验收记录一致。
- [ ] 官方 Skill 的“集成”和“实际执行”使用不同措辞。
- [ ] AI 生成图只用作装饰背景，真实计算区域没有被生成图替换。
- [ ] B 站发布时按实际素材勾选 AI 生成声明。
- [ ] 成片记录提交号、SHA-256、字幕复核人和发布 URL。
