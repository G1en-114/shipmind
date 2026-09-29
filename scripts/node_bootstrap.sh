#!/usr/bin/env bash
# ============================================================
# ShipMind 新节点一键重建（GB10 云节点关停/更换后使用）
# 前提：代码已同步到 ~/shipmind（用本地 node_deploy.py 或 git clone）
# 产物：依赖就绪 + 评测夹具 + Qwen3-4B 权重 + vLLM(9000) + 值班台(8888)
# 用法：bash ~/shipmind/scripts/node_bootstrap.sh
# ============================================================
set -euo pipefail

echo "== 1/6 系统依赖 =="
DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq python3-pip tmux ffmpeg 2>&1 | tail -1 || true

echo "== 2/6 Python 依赖（用户级）==="
pip3 install --user --break-system-packages -q numpy scipy pillow fastapi uvicorn modelscope 2>&1 | tail -1 || \
pip3 install -q numpy scipy pillow fastapi uvicorn modelscope 2>&1 | tail -1

echo "== 3/6 评测夹具重建（确定性，不入 git）=="
cd ~/shipmind
rm -rf evals/fixtures
python3 evals/make_fixtures.py >/dev/null
python3 sensors/gauge_synth.py --out evals/fixtures/gauges --n-train 100 --n-val 30 >/dev/null
ls evals/fixtures/

echo "== 4/6 Qwen3-4B-FP8 权重（ModelScope，约 5GB，节点内下载快）=="
export PATH="$HOME/.local/bin:$PATH"
mkdir -p ~/models
tmux kill-session -t weights 2>/dev/null || true
tmux new -d -s weights 'python3 -m modelscope download --model Qwen/Qwen3-4B-Instruct-2507-FP8 --local_dir ~/models/qwen3-4b-fp8 > ~/logs/weights4b.log 2>&1; echo EXIT_CODE=$? >> ~/logs/weights4b.log'
echo "下载已在 tmux 会话 weights 后台进行；进度: tail -f ~/logs/weights4b.log"

echo "== 5/6 等 vLLM 所需权重就绪后启动服务 =="
echo "（权重下载完成后手动执行下一步，或轮询："
echo "  grep -q EXIT_CODE ~/logs/weights4b.log && bash ~/shipmind/scripts/node_start_vllm.sh"
echo "  脚本会自动带齐 GB10 四参数：显存限容 0.45 / enforce-eager / flashinfer 绕过 / 禁 DeepGEMM）"

echo "== 6/6 值班台（不依赖权重，可先起）=="
tmux kill-session -t webui 2>/dev/null || true
tmux new -d -s webui 'cd ~/shipmind && python3 -m uvicorn web.server:app --host 127.0.0.1 --port 8888 > ~/logs/webui.log 2>&1'
sleep 5
curl -s -o /dev/null -w "webui: %{http_code}\n" http://127.0.0.1:8888/ || echo "webui 启动中，稍后自检"

echo "== 完成。StepFun key 用环境变量注入（节点不放 .env）："
echo "  STEPFUN_API_KEY=<key> STEPFUN_BASE_URL=https://api.stepfun.com/v1 python3 evals/run_evals.py"
