#!/usr/bin/env bash
# 在节点上以 tmux 托管启动 vLLM。
# GB10 实测参数（2026-09-21 故障后修正）：
#   1) FLASHINFER_DISABLE_VERSION_CHECK=1 —— 预置镜像内 flashinfer 版本不匹配
#   2) --gpu-memory-utilization 0.45      —— 统一内存架构，默认 0.9 会吃光 121GB 整机内存
#   3) --enforce-eager                    —— 跳过 CUDA graph 捕获（该路径曾致 API server 卡死）
#   4) VLLM_USE_DEEP_GEMM=0               —— GB10 上 DeepGEMM 报 CUDA_ERROR_INVALID_IMAGE
set -e
MODEL=${1:-/models/qwen3-4b-fp8}
NAME=${2:-qwen3-4b-fp8}
cd ~
tmux kill-session -t vllm 2>/dev/null || true
docker rm -f vllm-qwen 2>/dev/null || true
tmux new -d -s vllm "docker run --gpus all --name vllm-qwen --shm-size=16g \
  -e FLASHINFER_DISABLE_VERSION_CHECK=1 \
  -v /home/Developer/models:/models:ro -p 127.0.0.1:9000:9000 \
  qwen-agentworld:vllm bash -c \"VLLM_USE_DEEP_GEMM=0 vllm serve $MODEL \
  --served-model-name $NAME --host 0.0.0.0 --port 9000 \
  --max-model-len 8192 --gpu-memory-utilization 0.45 --enforce-eager\" \
  > /home/Developer/vllm-serve.log 2>&1"
echo "SERVE_LAUNCHED model=$MODEL name=$NAME"
echo "等待约 60-90 秒后用以下命令验证："
echo "  curl -s http://127.0.0.1:9000/v1/models"
