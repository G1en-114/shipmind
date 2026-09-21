#!/usr/bin/env bash
# 在节点上以 tmux 托管启动 vLLM（GB10 实测参数：禁 DeepGEMM + triton MoE 后端）
set -e
cd ~
tmux kill-session -t vllm 2>/dev/null || true
docker rm -f vllm-qwen 2>/dev/null || true
tmux new -d -s vllm 'docker run --gpus all --name vllm-qwen --shm-size=16g \
  -v /home/Developer/models:/models:ro -p 127.0.0.1:9000:9000 \
  qwen-agentworld:vllm bash -c "VLLM_USE_DEEP_GEMM=0 vllm serve /models/qwen3.6-35b-a3b-fp8 \
  --served-model-name qwen3.6-35b-a3b-fp8 --moe-backend triton \
  --host 0.0.0.0 --port 9000 --max-model-len 32768" > /home/Developer/vllm-serve.log 2>&1'
echo SERVE_LAUNCHED
