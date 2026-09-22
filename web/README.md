# ShipMind 值班台（Web 演示台）

六大面板，数据全部来自本地 Skill 输出（确定性可复现，无 mock 数据）：

| 面板 | 数据源 |
|---|---|
| 实时告警流 | engine-room-acoustic-sentinel（四级分级 + 证据特征 + 成因） |
| 声学频谱 | 同一 Skill 的特征 + FFT 频谱（前端 canvas 绘制） |
| 视觉巡检 | engine-room-visual-inspector（带框截图 base64 + 读数/置信度/方式） |
| 态势 | radar-ppi-interpreter + route-deviation-watch + sonar-acoustic-fingerprint（极坐标 PPI 图） |
| 执行轨迹 | harness/trajectory.py 录制的 JSONL（回放最近步骤与耗时） |
| 日志与报告 | report-composer（含 verifier 结论） |

## 启动

```bash
pip install fastapi uvicorn
python -m uvicorn web.server:app --host 127.0.0.1 --port 8888
# 浏览器打开 http://127.0.0.1:8888/
```

**只绑 127.0.0.1**（组委会节点手册要求：暴露到公网的端口必须加鉴权；本地调试不暴露）。

## 技术选型

FastAPI + 原生 HTML/JS（无构建链、无前端框架），保证 GB10（ARM64）上零额外依赖部署。
页面 10 秒自动刷新；深色"驾驶台"风格。

## 已实现 / 待补

- ✅ 六面板数据管道全通（2026-09-22 本地验证：六个接口 200、渲染正常）
- 待补：告警流的时间序列（当前为快照）、WebSocket 推送（当前轮询）、态势面板叠加声纹标识
