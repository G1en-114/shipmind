# DGX Spark 五分钟真机演示验收

日期：2026-09-23（Asia/Shanghai）  
节点：`spark-a24e`（DGX Spark / GB10 / ARM64）  
访问路径：本机浏览器 → `127.0.0.1:8895` SSH 隧道 → Spark `127.0.0.1:8888`

## 结果

- 连续运行：300 秒（13:07:18–13:12:18）。
- 阶段：值班总览、机舱监测、航行态势、日志与证据、手册检索、项目介绍、回到总览，共 7 段。
- 覆盖接口：`alerts`、`logs`、`manual`、`situation`、`spectrum`、`trajectory`、`visual`。
- API 响应：254 次；HTTP 4xx/5xx：0。
- 浏览器 JavaScript 异常：0。
- 固定表盘底图：通过；表针运动：通过；声学纸带推进：通过；桌面横向溢出：无。
- 结束时前端数据错误对象为空。

## Spark 计算链

- `brain_check.py`：本地 Qwen3-4B-FP8 对话可用，Skill 路由 3/3 通过。
- `agent_demo.py --batch --no-voice`：4 条请求全部经大脑路由；声学、航线、雷达自研 Skill 执行成功；DeepStream 官方 Skill 实际生成管线。
- 演示不启动训练、不加载新模型、不调用在线语音。

## 资源安全

演示前、中、后 Spark 可用内存均为 57GiB。结束时 load average 为 `1.93 / 0.71 / 0.30`，vLLM 容器约 5.63GiB RSS，未出现持续资源增长。vLLM GPU 分配约 56.3GiB；Web 服务常驻内存约 65MiB。

## 证据

- 浏览器机器结果：`runs/ui-review/spark-5min.json`
- 最终页面截图：`runs/ui-review/spark-5min.png`
- AI 真机研判结果：`runs/ui-review/spark-ai.json`
- AI 桌面与窄屏截图：`runs/ui-review/spark-ai-desktop.png`、`runs/ui-review/spark-ai-mobile.png`

## AI 值班官补充验收（2026-09-23）

- `/api/briefing` 经 SSH 转发调用 Spark 本机 Web 服务，2.35 秒返回。
- 返回模型：`Qwen3-4B-FP8 · DGX Spark`；结论、摘要、建议均由本机模型生成。
- 页面固定展示 4 路可核对证据、Skill 链、“合成观测”和人工复核建议。
- 桌面宽 1440 px、移动宽 390 px 均无横向溢出，浏览器运行时错误为 0。
- 验收后 Spark 可用统一内存 57 GiB；`vllm` 与 `webui` 健康检查均为 200，未启动新模型。

## 值班操作台补充验收（2026-09-23）

- 在网页输入“目前怎么样？”后，Spark Qwen 约 3.03 秒返回，输入框自动清空，操作台自动滚动到底部。
- 操作员问题、AI 回答、自动研判和系统设置均持久化到 `runs/ai-duty/duty.jsonl`。
- 单文件轮转阈值 1 MB 与 2 MB 切换通过，最终恢复为默认 2 MB，并保留 3 个归档。
- 日志 API 只从文件尾部读取所需行数，不会因归档变大而把整份日志载入内存。
- 桌面与 390 px 移动端无横向溢出，浏览器运行时错误为 0。
- Spark 轨迹：`~/shipmind/runs/agent_demo/trajectory.jsonl`

数据口径：浏览器和 Skill 计算均运行在 Spark；输入仍以合成夹具和本地演示语料为主，不代表真实船舶遥测或上船实测。
