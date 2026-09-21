# 数据集许可台账（2026-09-21 核实，已按实际下载状态更新）

规则：许可不明确/需授权的数据集不进仓库；音频一律不进 git（再分发限制）。

## A. 免申请、已下载到本地 D:\datasets（✅ 主用）

| 数据集 | 用途 | 许可 | 大小/状态 |
|---|---|---|---|
| **DCASE 2020 Task2 开发集**（MIMII + ToyADMOS） | 机舱声学 ML 轨主数据 | **CC BY-NC-SA 4.0** | Zenodo 3678171；pump 1.03GB ✅ / valve 1.0GB ⏳ / fan 1.4GB ⏳（本地代理下载中，完成后传节点） |
| **DeepShip（GitHub 部分，4 类）** | 声纹正数据 | 仓库无 LICENSE（注明出处） | 525MB tarball ✅ 已解压 `D:\datasets\deepship`（Cargo/Passengership/Tanker/Tug，699MB 解压后）；完整版需邮件 mirfan@mail.nwpu.edu.cn |
| **SeaShipsSeg**（1200 张标注船舶图，6 船型） | 视觉/态势补充 | 仓库无 LICENSE（注明出处） | 222MB tarball ✅ 已解压 `D:\datasets\seashipsseg`（images/ + annotations/train,val） |

## B. 曾误判为“免申请”，核实后需授权（❌ 不用）

| 数据集 | 实际情况 |
|---|---|
| **UFPR-ADMR-v1** | ❌ Copel 公司资产，须机构授权人（非学生）签署许可协议发教授 menotti@inf.ufpr.br，1–5 工作日回链接 |
| **Mileeena/synthetic-analog-gauges** | ❌ HF 门控数据集（401），需登录并申请访问（许可虽为 CC-BY-4.0） |
| FirulAI/data_meters | ❌ 名字像电表实际是 WNUT NER 文本数据 |
| Paco4365483/pressure_gauge | ❌ 无 license |
| Francesco/gauge-u2lwv | ⚠️ 未门控、CC 许可，但 parquet 内嵌图、读数标注不清晰——备选，暂不用 |

## C. 自产合成（✅ 已完成，许可最干净）

| 数据 | 用途 | 位置 |
|---|---|---|
| NMEA 0183 轨迹（三种漂移档） | 航线偏离 | sensors/nmea_simulator.py |
| PPI 回波场（含空海面负例） | 雷达检测 | skills-src/radar-ppi-interpreter/scripts/ppi_synth.py |
| **模拟表盘（读数+bbox 精确标签）** | 视觉读数 | sensors/gauge_synth.py → evals/fixtures/gauges/ |
| 声学夹具（正常/轴承磨损/过短） | 声学哨兵 + AE 训练 | evals/make_fixtures.py |
| 机舱事件流 JSONL | 日志生成 | evals/fixtures/navlog/ |

## D. 决策记录

1. **表盘数据改为自产合成**：三个候选（UFPR / Mileeena / Paco）全部需授权或无许可，自产合成器标签精确、数量无限、零许可风险，且与雷达 PPI 合成器同属 sensor simulation layer，架构叙事一致。
2. **DeepShip GitHub 部分是意外之喜**：4 类船型当场可得，声纹训练数据不卡审批；申请邮件只服务“完整版 + 按船划分”的正式实验。
3. **DCASE 改本地下载**：节点直连 Zenodo 仅 ~30KB/s（31 分钟 60MB），本地代理 ~1.7MB/s，快 50 倍；下完 SFTP 传节点。
4. 所有音频（DCASE/DeepShip/ShipsEar）按许可只进磁盘、不进 git。
5. 后续候选（未下载）：yasumorishima/hormuz-ship-tracker（AIS 航迹，★9）、LunarSheep00/Yolo-Ship-Detection（MIT）。
