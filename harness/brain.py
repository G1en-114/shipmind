"""编排大脑客户端：OpenAI 兼容 chat completions，零第三方依赖。

端点可换——"换模型 = 改三个值"的践行：.env 里改
  BRAIN_BASE_URL / BRAIN_MODEL / BRAIN_API_KEY
即可在 ollama（本地桥接）↔ NIM（本地正式）↔ StepFun API（远程）之间切换，
切换后必须跑回归评测（evals/）证明行为等价。
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    # 默认指向**实际在跑的**本地端点：GB10 上 vLLM 0.25 服务 Qwen3-4B-FP8。
    # （Qwen3.6-35B 的架构 Qwen3_5MoeForConditionalGeneration 不被 vLLM 0.25 支持，
    #   且 198B×FP8 超出 GB10 统一内存，故本地大脑用 4B；198B 的 step-3.7-flash 走
    #   StepFun API，切换只改这三个值。）
    "BRAIN_BASE_URL": "http://127.0.0.1:9000/v1",
    "BRAIN_MODEL": "qwen3-4b-fp8",
    "BRAIN_API_KEY": "",
}


def load_env() -> dict[str, str]:
    env = dict(DEFAULTS)
    env.update(os.environ)
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() in DEFAULTS:  # 只接受白名单键
                    env[k.strip()] = v.strip()
    return env


def chat(messages: list[dict], *, temperature: float = 0.2,
         max_tokens: int = 512, timeout: int = 120) -> str:
    env = load_env()
    base = env["BRAIN_BASE_URL"].rstrip("/")
    payload = {
        "model": env["BRAIN_MODEL"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Content-Type": "application/json"}
    if env["BRAIN_API_KEY"]:
        headers["Authorization"] = f"Bearer {env['BRAIN_API_KEY']}"
    req = urllib.request.Request(base + "/chat/completions",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    message = data["choices"][0]["message"]
    content = (message.get("content") or "").strip()
    # 思考型模型（step-3.7-flash 等）content/reasoning 分字段；思考吃满
    # max_tokens 时 content 可能为空——此时退化取思考尾部，宁可有信息不空转
    if not content:
        content = (message.get("reasoning_content")
                   or message.get("reasoning") or "").strip()
    if "</think>" in content:
        content = content.split("</think>", 1)[1]
    return content.strip()


ROUTER_PROMPT = """你是船舶值守系统的 Skill 路由器。根据用户请求，从候选 Skill 中选出最合适的一个；\
如果没有任何候选适用，必须返回 "NONE"，禁止硬凑。

候选 Skill（名称 | 来源 | 用途）：
{catalog}

规则：
- 只输出 JSON，格式 {{"skill": "<名称或NONE>"}}，不要输出任何其他文字。
- 与音频/机舱设备相关选 acoustic；与航线/船位相关选 route；与雷达目标相关选 radar；\
与水听器/船型相关选 sonar；与日志生成相关选 navlog。
- 来源为 official 的是 NVIDIA 官方 Skill（deepstream-generate-pipeline 生成视频分析管线、
rag-blueprint 用于 RAG 部署、tao-* 用于图像定位、vss-* 用于视频问答报告），
用户明确提到这些能力时选它们。

示例：
  请求"3号泵有异响" → {{"skill": "engine-room-acoustic-sentinel"}}
  请求"偏航了吗" → {{"skill": "route-deviation-watch"}}
  请求"生成 deepstream 管线" → {{"skill": "deepstream-generate-pipeline"}}
  请求"今天天气如何" → {{"skill": "NONE"}}

判定要点：只要请求涉及某个候选的职责范围就必须选它，禁止返回 NONE；
只有与所有候选都完全无关（闲聊、常识、无关领域）时才返回 NONE。

用户请求：{query}"""


def choose_skill(query: str, skills: list) -> str | None:
    """让大脑从候选中选 Skill；解析失败或 NONE 返回 None（负向路由兜底在调用方）。"""
    catalog = "\n".join(
        f"- {s.name} | {s.description[:80]}" for s in skills)
    raw = chat([{"role": "user",
                 "content": ROUTER_PROMPT.format(catalog=catalog, query=query)}],
               temperature=0.0, max_tokens=200, timeout=60)
    idx = raw.find("{")
    if idx < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw[idx:])
    except json.JSONDecodeError:
        return None
    name = obj.get("skill")
    if not name or name == "NONE":
        return None
    return name
