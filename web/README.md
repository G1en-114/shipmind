# ShipMind 值班台（Web 演示台）

> 2026-09-23：新版采用浅色、克制的 Apple 风格值班界面，原生 HTML/CSS/JS，无 CDN、字体下载或前端构建链。设计规则见根目录 `DESIGN.md`；本轮验证见 `docs/FRONTEND-DELIVERY.md`。

## 新版页面与操作

- **值班总览**：360° 雷达、目标选择和 4/8/12 km 量程、告警对照、频谱、表盘、历史轨迹与报告。
- **机舱监测 / 航行态势**：聚焦相关观测；雷达不裁掉后半圈，超量程目标有明确提示。
- **日志与证据**：展开最近 30 步输入/输出，查看完整报告并导出 Markdown。
- **手册检索**：通过 `/api/manual?q=...` 运行本地 BM25，保留原文、来源和章节。
- **认识 ShipMind**：项目介绍、处理流程、已接入能力、本地/在线边界及官方 Skill 接入状态。

刷新为 30 秒一次，可关闭；刷新互斥，隐藏页面和介绍/手册页暂停自动分析。错误会显示重试入口，并将历史数据标为过期。连接状态只代表当前 Web 数据服务，不探测或宣称大脑/GPU 在线。

## PowerShell 启动

```powershell
python -m pip install numpy pillow fastapi uvicorn
```

```powershell
python -X utf8 -m uvicorn web.server:app --host 127.0.0.1 --port 8890
```

打开 `http://127.0.0.1:8890/`。仍支持任意本地端口。开发环境需先生成已有夹具：

```powershell
python -X utf8 evals/make_fixtures.py
```

```powershell
python -X utf8 sensors/gauge_synth.py --out evals/fixtures/gauges --n-train 100 --n-val 30
```

```powershell
python -X utf8 scripts/fusion_demo.py --no-voice
```

缺报告/轨迹时显示空状态；缺观测素材时显示错误。本次没有修复全仓干净部署问题，模型制品与完整夹具管理仍按接手计划推进。

## 回归验证

接口适配测试使用 `unittest` 与 FastAPI TestClient（额外安装 httpx）：

```powershell
python -X utf8 -m unittest web.test_server -v
```

前端主文件为 `web/index.html`、`web/static/app.css`、`web/static/app.js`；`web/server.py` 提供静态资源和数据接口。

## 数据与能力边界

- `/api/alerts`、`/api/spectrum`：合成泵音频经过声学 Skill 计算；时间是分析时间。
- `/api/visual`：合成表盘读数与检测框，不是实时摄像头。
- `/api/situation`：PPI 检出目标、模拟 NMEA 航线和独立声纹样本；没有目标跟踪、跨传感器关联或实际海图。
- `/api/logs`、`/api/trajectory`：已保存的历史报告和执行记录，不保证属于当前观测刷新。
- `/api/manual`：自拟合成手册的本地检索，表格摘录可能不完整，界面明确标记缺失单元。

只绑定 127.0.0.1。页面不自动调用 StepFun、语音或远程模型，也不会把本地 API 连通标成 GB10 验收成功。WebSocket、连续遥测、任意素材上传、场景执行控制和统一运行 ID 仍未实现。
