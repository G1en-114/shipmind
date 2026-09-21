# 节点故障记录与求助信息（2026-09-21）

## 故障现象

- 节点：spark-a24e（登录表主机名 spark-65，队名 Devx，序号 15）
- SSH：`ssh -p 6065 Developer@106.13.186.155`
- TCP 可达（约 50ms），sshd 响应正常，密码验证通过
- **认证成功后会话建立卡死**，无任何输出，也不返回错误码
- 此前节点上运行：vLLM Docker 容器（镜像 `qwen-agentworld:vllm`，容器名 `vllm-qwen`，为 4B 模型预留约 106GB KV cache，占统一内存 121GB 的绝大部分）

## 判断

内存耗尽导致进程调度饥饿：sshd 能完成认证，但无法为登录会话 fork/exec shell。节点未重启、未改系统配置、未动驱动。所有项目资产（代码在 GitHub、数据在本地 D 盘）不受影响。

## 求助信息（直接复制发送）

> 主题：spark-65 节点 SSH 认证后无法建立会话，疑似内存耗尽
>
> 组委会技术支持好，
>
> 我们是 Devx 队（序号 15），分配的节点是 spark-65（登录显示主机名 spark-a24e，SSH 端口 6065）。
>
> 现象：SSH 连接与密码认证均正常，但认证成功后会话无法建立（卡住无输出），已持续约 XX 分钟，重试无效。TCP 端口可达，说明节点网络层存活。
>
> 原因（我们判断）：我们在节点上启动了 vLLM Docker 容器（镜像 qwen-agentworld:vllm，容器名 vllm-qwen），该容器为模型预留了约 106GB KV cache，占满 GB10 统一内存，导致系统进程调度饥饿。
>
> 需要协助：请从跳板机侧强制停止并删除名为 `vllm-qwen` 的容器（或重启该节点的 Docker 服务）。我们没有执行 reboot，没有修改任何系统配置、驱动或防火墙规则。
>
> 联系：姓名 / 电话 / 微信
>
> Devx 队

发送渠道（按优先级）：
1. 选手群内 @组委会技术支持（最快）
2. 邮箱 china_developer@nvidia.com（赛事页公布的咨询邮箱）

## 节点恢复后的操作（按顺序）

```bash
docker rm -f vllm-qwen          # 删除吃内存的容器
tmux kill-session -t weights    # 停掉 30B 权重下载（暂不需要）
sleep 10 && free -h             # 确认内存回来
```

后续重启本地推理端点时，必须带内存约束（见 scripts/node_start_vllm.sh，需更新）：

```bash
--gpu-memory-utilization 0.45 --enforce-eager
```

## 教训记录

GB10 是统一内存架构：vLLM 的 `gpu_memory_utilization` 默认 0.9 意味着吃掉全机 121GB 内存的 90%，**小模型也必须显式限制**。同时 `--enforce-eager` 在 ARM64 上可跳过 CUDA graph 捕获（该路径疑似导致 API server 卡死）。这两条已写入 README 部署说明。
