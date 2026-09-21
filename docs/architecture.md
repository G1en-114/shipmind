# ShipMind 架构图

> 图例：✅ 已实现可运行 ｜ 🔜 规划中（D4–D8）｜ 数据与代码均在本地/节点，运行路径零云端

## 1. 总体架构

```mermaid
flowchart TB
    subgraph SHIP["🚢 船端 · DGX Spark · 离线闭环 · 运行时零云端"]
        direction TB

        U["船员<br/>语音 / 触屏"]
        ASR["StepAudio 本地 ASR / TTS"]
        OC["OpenClaw 本地会话宿主<br/>官方 Skill pin 上游提交后整目录入 workspace"]
        BRAIN["主 Agent 编排与路由<br/>Step 3.7 Flash（NIM 本地）"]

        subgraph SL["Skill 层"]
            direction TB
            subgraph ER["机舱哨兵线"]
                direction LR
                S1["声学哨兵<br/>engine-room-acoustic-sentinel ✅"]
                S2["视觉巡检<br/>engine-room-visual-inspector 🔜"]
                S3["手册RAG<br/>manual-rag-query 🔜"]
                S4["值班日志<br/>navlog-autofill ✅"]
                S5["巡检报告<br/>report-composer 🔜"]
            end
            subgraph SA["态势感知线"]
                direction LR
                S6["声纹<br/>sonar-acoustic-fingerprint ✅"]
                S7["雷达PPI<br/>radar-ppi-interpreter ✅"]
                S8["航线偏离<br/>route-deviation-watch ✅"]
            end
        end

        V["证据审核 Agent（verifier）🔜<br/>逐条核对 结论 ↔ 证据，无证据即驳回"]

        subgraph H["自研 Harness ✅"]
            direction LR
            H1["Skill 运行时<br/>渐进式披露"]
            H2["路由<br/>大脑优先 / 关键词兜底"]
            H3["输出契约校验"]
            H4["执行轨迹<br/>录制 / 回放 / diff"]
            H5["本地算力预算调度"]
        end

        W["值班台 Web 🔜<br/>告警流 · 频谱 · 航线走廊 · 雷达态势 · 轨迹回放"]

        subgraph SEN["传感器接入层（模拟源映射真实设备）"]
            direction LR
            E1["音频<br/>MIMII / DeepShip / 自录"]
            E2["视频<br/>MODD2 真实 + 合成表盘"]
            E3["导航<br/>NMEA 0183 模拟器"]
            E4["雷达<br/>PPI 合成器"]
        end

        INF["推理：vLLM 0.25（GB10 本地）<br/>知识：RAG Blueprint 本地向量库"]
    end

    CLOUD["☁️ 开发期专用 · 组委会 Spark 云节点<br/>数据镜像 · 耗时训练 · 模型制品分发"]
    GH["📦 GitHub 仓库<br/>每日 push —— 节点无备份，git 即灾备"]

    U --> ASR
    ASR --> OC
    OC --> BRAIN
    BRAIN --> SL
    SL --> V
    V --> W
    H -. 承载 .-> SL
    SEN --> SL
    INF --> BRAIN
    CLOUD -. 仅开发期同步 .-> SHIP
    SHIP --> GH
```

## 2. 跨线融合数据流（演示主线的“多智能体协同”实证）

```mermaid
flowchart LR
    RAD["雷达 PPI 检测<br/>目标方位 / 距离 / CPA-TCPA"]
    SON["声纹分类<br/>疑似拖网渔船 + 谱线证据"]
    NAV["航线模块<br/>本船走廊态势"]
    REG["COLREGs 知识库<br/>会遇条款原文"]

    FUSE{"跨线融合<br/>态势研判"}
    VRF{"verifier<br/>逐条核证据"}

    OUT1["🔊 语音播报"]
    OUT2["📄 态势报告"]
    OUT3["📝 航海日志"]

    RAD --> FUSE
    SON --> FUSE
    NAV --> FUSE
    REG --> FUSE
    FUSE --> VRF
    VRF -->|证据齐全| OUT1
    VRF --> OUT2
    VRF --> OUT3
    VRF -->|无证据| REJ["驳回重做<br/>（禁止无证据结论）"]
```

一条链路串起四个智能体与五类证据（雷达检测参数、声纹谱线、航线态势、规则原文、声学特征）——这是评审“多智能体协同”的直接证据。

## 3. 数据资产与流向

```mermaid
flowchart TB
    subgraph OPEN["免申请公开数据"]
        direction LR
        D1["DCASE 2020<br/>MIMII + ToyADMOS<br/>pump / valve / fan"]
        D2["DeepShip 四类<br/>货船 / 客船 / 油轮 / 拖轮"]
        D3["MODD2 视频<br/>28 序列真实 USV 拍摄"]
        D4["MaSTr1325<br/>1325 张海面图 + 掩膜"]
        D5["SeaShipsSeg<br/>1200 张船舶图"]
    end

    subgraph SYN["自产合成（许可最干净）"]
        direction LR
        Y1["NMEA 0183 轨迹"]
        Y2["PPI 回波场"]
        Y3["模拟表盘<br/>读数 + bbox 精确标签"]
        Y4["声学 / 日志夹具"]
    end

    subgraph USE["用途"]
        direction LR
        U1["机舱声学 ML 轨<br/>（AE，三机种对照）"]
        U2["声纹 ML 轨 🔜"]
        U3["DeepStream / VSS<br/>真实视频管线 🔜"]
        U4["海面 / 障碍分割 🔜"]
        U5["各 Skill evals<br/>（13/13 通过）"]
    end

    D1 --> U1
    D2 --> U2
    D3 --> U3
    D4 --> U4
    D5 --> U4
    Y1 --> U5
    Y2 --> U5
    Y3 --> U4
    Y4 --> U5
    Y3 --> U3
```

## 4. 评测体系（Tier3 式对照）

```mermaid
flowchart LR
    C1["evals/cases/*.jsonl<br/>正向 / 负向 / 边界"]
    R["evals/run_evals.py<br/>统一运行器"]
    B["evals/BENCHMARK.md<br/>双轨对照 · 三机种 AUC"]

    C1 --> R
    R -->|"13/13 通过"| B
    B -->|"节点恢复后全量复跑"| B
```

负向用例（不该触发时必须不触发）与正向同等重要；确定性模块（航线 XTE/CPA、日志）零容差，ML 模块给置信度与 AUC。
