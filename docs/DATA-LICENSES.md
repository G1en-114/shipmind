# 数据集许可台账（2026-09-21 核实）

规则：许可不明确的数据集不进仓库，只写获取方式；音频一律不进仓库（再分发限制）。

## A. 免申请、直接下载（✅ 主用）

| 数据集 | 用途 | 许可 | 大小/获取 | 核实状态 |
|---|---|---|---|---|
| **DCASE 2020 Task2 开发集**（含 MIMII + ToyADMOS） | 机舱声学 ML 轨主数据 | **CC BY-NC-SA 4.0** | Zenodo 3678171；dev_data_pump.zip 1.0GB / valve 1.0GB / fan 1.4GB / slider 1.0GB / ToyCar 1.8GB / ToyConveyor 1.9GB；Open 标签、无需登录 | ✅ 已核实（Zenodo 页面直读） |
| ToyADMOS（同上合集内） | 声学补充 | 同上 | 同上 | ✅ |
| **DeepShip（GitHub 部分）** | 声纹正数据 | 仓库无 LICENSE（需注明出处） | 4 类文件夹（Cargo/Passengership/Tanker/Tug）**GitHub 直下**；完整版需邮件 mirfan@mail.nwpu.edu.cn；47h04m、265 艘船、Strait of Georgia 实录 | ✅ 已核实（仓库 README 原文） |
| **UFPR-ADMR-v1**（UFPR 自动仪表读数） | visual-inspector 表盘读数 | 学术用途（页面注明） | GitHub raysonlaroca/ufpr-admr-v1-dataset，★10，含标注 | ✅ 仓库已核实；**下载方式与许可细节待打开页面确认** |
| LunarSheep00/Yolo-Ship-Detection | 海面船只检测补充 | MIT | GitHub 小仓库 | ✅ 存在性核实（★1，质量待评） |
| QinggangSUN/unknown_number_source_separation | 水声辐射噪声源分离参考 | MIT | GitHub ★21 | ✅ 存在性核实 |

## B. 需申请（⏳ 已发/待发，不阻塞）

| 数据集 | 用途 | 状态 |
|---|---|---|
| DeepShip 完整版 | 声纹按船划分正式实验 | 邮件申请（模板见 docs/APPLY-EMAILS.md） |
| ShipsEar（atlanttic.uvigo.es） | 声纹第二数据集（90 段、11 船类+背景） | 邮件申请（模板同文件） |

## C. 自产合成（✅ 已完成）

| 数据 | 用途 | 位置 |
|---|---|---|
| NMEA 0183 轨迹（三种漂移档） | 航线偏离 | sensors/nmea_simulator.py + evals/fixtures/nmea/ |
| PPI 回波场（含空海面负例） | 雷达检测 | skills-src/radar-ppi-interpreter/scripts/ppi_synth.py |
| 声学夹具（正常/轴承磨损/过短） | 声学哨兵 + AE 训练 | evals/make_fixtures.py |
| 机舱事件流 JSONL | 日志生成 | evals/fixtures/navlog/ |

## D. 决策记录

1. **声纹管线不等申请**：先在 DCASE2020 的 6 类机器声上端到端跑通（管线与数据源无关），DeepShip/ShipsEar 到位后只换数据源。
2. **DeepShip GitHub 部分是意外之喜**：4 类船型直下，意味着声纹训练数据其实**当场可得**，申请只影响“完整版 + 按船划分”的正式实验。
3. **仪表读数有了正经来源**：UFPR-ADMR-v1 比自录强（带标注、规模大）；自录视频降级为补充。
4. 所有音频数据（DCASE/DeepShip/ShipsEar）按许可**只进节点磁盘，不进 git**。
