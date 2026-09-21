# 技术参考库（REFERENCES）

> 2026-09-21 由三个调研代理检索核实后整理；标注"待核实"处赛前人工确认。
> 用途：ML 轨实现照方抓药、答辩引用、许可合规。**许可红线见文末，先读红线再拷任何代码。**

## 1. 机舱声学异常检测（ML 轨，D6–D7）

| 资源 | 链接 | 许可 | 采用建议 |
|---|---|---|---|
| DCASE 2020 Task 2 官方 baseline | github.com/y-kawagu/dcase2020_task2_baseline | Copyright Hitachi（LICENSE 待核实） | **配方已逐行核实**：log-mel `n_mels=128 × frames=5 = 640 维`输入 → 稠密 AE `128-128-128-128-8-128-128-128-128`（BatchNorm+ReLU）→ MSE 重构误差评分，AUC/pAUC(max_fpr=0.1)。TensorFlow 1.x 写的——**重实现不拷码**，numpy 几百行可写 |
| DCASE 2020 开发集（MIMII+ToyADMOS 合集） | zenodo.org/record/3678171 | **CC BY-NC-SA 4.0**（已核实） | 只下 `dev_data_pump.zip` + `dev_data_valve.zip`（对齐机舱场景）；自带 train/normal 与 test/{normal,anom} 划分，直接算 AUC 与启发式轨对照 |
| IDNN（Wilkinghoff 2021） | arXiv:2104.04517（待核实） | 论文 | AE 之后的第二轨：输入复制对齐时移帧，适合泵/阀周期声，仍是全连接 |
| DCASE 2023/2024 first-shot 设定 | dcase.community | — | 只作答辩谈资；单船单机种场景用 2020 设定即可，不追新 |

## 2. 船舶被动声纹（D7）

| 资源 | 链接 | 许可 | 采用建议 |
|---|---|---|---|
| DeepShip 数据集 | github.com/irfankamboh/DeepShip | 待核实（邮件申请制） | **主训练集**：4 类（cargo/tanker/passenger/tug），~50h，32kHz；申请邮件今天发占坑 |
| DeepShip 防泄漏划分法 | github.com/ZhuPengsen/Method-for-Splitting-the-DeepShip-Dataset | 待核实 | **必须照做**：默认划分有同船跨 train/test 泄漏；只取 4 类、按船划分（ship-wise split），否则准确率虚高会被评委戳穿 |
| ShipsEar 数据集 | atlanttic.uvigo.es；论文 Santos-Domínguez et al., Applied Acoustics 2016（doi:10.1016/j.apacoust.2016.11.044，条目已核实） | 申请制，条款待核实 | 备选第二集（90 段、11 船类+背景）；做 5 类（去背景）设定与文献可比 |
| DEMONet | arXiv:2411.02758 | 论文 | 架构参考首选：DEMON 谱主输入 + 多专家分支；VAE 分支砍掉省算力 |
| DEMON 谱提取（抗噪） | MDPI JMSE 2025 (14:1459)；IEEE Access 2021 | 论文 | 包络谱计算细节参考 |
| LOFAR/DEMON 准确率口径 | 多篇综合 | — | 答辩用区间表述：ShipsEar 5 类 95–98%（有泄漏争议）、DeepShip 4 类按船划分 85–95%；**不引用未核实的具体数字** |

## 3. 雷达 PPI（S2）

| 资源 | 链接 | 许可 | 采用建议 |
|---|---|---|---|
| CA-CFAR 公式 | Skolnik/Richards 教材（公开方法论） | 公式自由 | `α = N·(Pfa^(-1/N) − 1)`，训练窗−保护窗；**逐方位线 1D 距离向 CFAR** 替换当前全局 mean+8σ（保留全局阈值作降级路径）。典型参数 num_train 16–24、num_guard 2–4、Pfa 1e-3~1e-4 |
| tsaith/radar | github.com/tsaith/radar | **无许可证** | 只核对公式，**不可拷码**（无许可=保留所有权利） |
| CFAR 可视化调参 GUI | github.com/fzzfbyx/CFAR-radar-algorithm_MATLAB_GUI | **MIT** | 选 train/guard/Pfa 参数组合的参考 |
| radar_pi（OpenCPN 雷达插件） | github.com/opencpn-radar-pi/radar_pi | **GPL-2.0（只读不抄）** | `src/emulator/`（合成 spokes）、`example/*.pcap.gz`（真实航海雷达录制→回归测试数据）；`src/Arpa.cpp`/`Kalman.cpp`（目标跟踪）、`GuardZone.cpp`（扇区警戒+迟滞）值得读 |
| PPI 公开数据集 | — | — | **检索结论：不存在公开航海导航雷达 PPI+真值数据集**——合成是正解，README 如此表述 |
| 合成器增强方向 | radar_pi spoke 结构；Swerling 起伏；瑞利杂波 | — | 数据结构对齐 spoke（方位+距离单元+强度）；加近距衰减杂波与扫描间去相关 |

## 4. 导航计算与 NMEA（S1）

| 资源 | 链接 | 许可 | 采用建议 |
|---|---|---|---|
| pynmeagps | github.com/semuconsulting/pynmeagps | **BSD-3** | 校验和/流式解析主参照（纯标准库，可抄） |
| pynmea2 | github.com/Knio/pynmea2 | **MIT** | 句型字段表（RMC/RMB/APB/XTE）与测试用例参照 |
| XTE 球面公式 | movable-type.co.uk/scripts/latlong.html（Cross-track distance） | 公开网页 | `dxt = asin(sin δ13 · sin(θ13−θ12)) · R`；**符号约定对齐 OpenCPN：航迹左侧为负** |
| OpenCPN XTE/CPA 语义 | github.com/OpenCPN/OpenCPN：`model/src/routeman.cpp`(L475-507)、`ais_state_vars.cpp`(L38-78 告警阈值) | GPL（只读） | XTE 到达点切换、CPA/TCPA 告警阈值与去抖语义 |
| geographiclib | github.com/geographiclib/geographiclib | **MIT** | 航段超长需测地线精确解时再引入；短航段球面公式足够 |

## 5. COLREGs 会遇态势（D7，喂给 manual-rag-query 的确定性前置分类）

| 资源 | 链接 | 许可 | 采用建议 |
|---|---|---|---|
| Zhao & Roh 2019 | doi:10.1016/j.oceaneng.2019.106436（Ocean Engineering 191:106436，Crossref 已核实） | 论文 | 会遇区间（业界沿用）：**追越 \|θ\|>112.5°；对遇 \|θ\|≤5° 且航向近似相反；交叉 5°<\|θ\|≤112.5°，右舷有他船者让路**。写成纯函数 `classify_encounter()`，精确阈值读 PDF 后固化＋单测 |
| 会遇分类开源实现 | github.com/ntnu-itk-autonomous-ship-lab/collision_avoidance_identifier | **MIT** | 与我们最同构的开源实现，态势分类区间代码+测试样本可直接借鉴 |
| COLAV 状态机 | github.com/michaelstolberger27/usv-navigation | MIT | 态势分类与避碰决策解耦的分层参考 |
| 会遇场景生成 | github.com/aavek/Aeolus-Ocean | BSD-3 | 造会遇测试场景验证分类函数 |

## 6. 许可红线（先读这里）

1. **CC BY-NC-SA 4.0**（DCASE/MIMII/ToyADMOS）：非商业比赛可用；须署名；衍生数据同许可；**赛后商用必须换自采数据或另获授权**。
2. **ShipsEar / DeepShip 音频一律不得进公开仓库**——只写申请方式与下载指引；引用名称与论文没问题。
3. **无许可证仓库**（tsaith/radar、Udacity 系项目）：保留所有权利，公式自己写。
4. **GPL**（radar_pi、OpenCPN）：只读学思路，一行不抄；我们仓库是 Apache-2.0，不得被传染。
5. **MIT/BSD 可安全借鉴**：pynmeagps、pynmea2、geographiclib、fzzfbyx GUI、collision_avoidance_identifier、Aeolus-Ocean。
6. dcase2020_task2_baseline 代码：重实现（结构已核实），不复制文件。
