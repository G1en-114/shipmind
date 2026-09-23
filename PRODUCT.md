# ShipMind

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

项目文档定义的用户为船舶机舱与驾驶台值班人员。当前交付为比赛演示原型，兼顾评审理解项目机制。操作台优先、介绍页独立是本轮依据文档作出的设计假设。

## Product Purpose

把声学、视觉、雷达、航线和手册引用汇集到本地值班台，让观察可追溯到来源及执行结果。

## Capabilities and Constraints

FastAPI 与原生 HTML/CSS/JavaScript；无构建链、无外部字体或 CDN 依赖。演示素材为合成音频、PPI、NMEA 与表盘。现有六接口提供本地分析和历史轨迹/报告；报告引用审核仅检查存在性。语音与可选 StepFun 大脑为在线增强，不在前端虚构离线可用状态。DGX Spark 是目标平台，不能把本机 API 可达写成真机运行。

## Brand Commitments

名称 ShipMind / 智舷；中文界面；民用海事感知；手册为自拟演示语料。不添加上船实测、商用客户或新的模型指标承诺。

## Evidence on Hand

README.md、docs/HANDOFF.md、docs/TAKEOVER-REVIEW-PLAN.md、evals/BENCHMARK.md、corpus/manuals/ 及当前 API。历史数字与当前回归分开呈现。

## Product Principles

- 显示数据来源，不把演示快照称为实时船舶遥测。
- 分开告警严重度、分析失败和空状态。
- 操作能连接已有能力，尚未接入的能力只作说明。
- 本地核心与在线增强边界清晰。
