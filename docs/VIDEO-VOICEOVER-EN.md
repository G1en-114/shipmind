# ShipMind 60-second English voice-over

This script matches the six burned-in English subtitle cards in the v9 promo. Target delivery: a mature male broadcast voice with calm authority and restrained urgency, approximately 97 words per minute. Leave the marked pauses open so the paper, radar, sonar and impact effects can breathe.

The generated delivery uses `en-US-ChristopherNeural` as its source voice, then applies slower pacing, lower pitch, broadcast EQ, compression and loudness normalization. It follows the supplied sample's broad performance direction; it is not an exact clone of the sample speaker.

## Clean recording copy

At three a.m., mid-ocean, one engineer may be watching an entire ship.

NVIDIA DGX Spark is the local compute behind ShipMind, powered by the GB10 Grace Blackwell Superchip and unified memory.

It combines acoustic changes, gauge readings, radar detections, sonar evidence, and route deviation into one evidence-bound briefing.

Ask how things are now. The local Qwen model, served by vLLM on Spark, answers with evidence and keeps the human in review.

DGX Spark, NVIDIA Agent Skills, DeepStream, StepFun, Qwen, and vLLM form one reproducible agent workload.

Synthetic inputs. Real Spark compute. Intelligence stays on board. ShipMind.

## Timed performance copy

| Time | Delivery | Exact line |
|---|---|---|
| 00:00–00:06 | Low and contained. Stress **three a.m.** and **entire ship**. | At **three a.m.**, mid-ocean, / one engineer may be watching an **entire ship**. |
| 00:06–00:17 | Open up on the product name. Brief pause after ShipMind. | **NVIDIA DGX Spark** is the local compute behind **ShipMind**. / Powered by the **GB10 Grace Blackwell Superchip** / and unified memory. |
| 00:17–00:28 | Build rhythm through the evidence list; land firmly on briefing. | It combines **acoustic changes**, / **gauge readings**, / **radar detections**, / **sonar evidence**, / and **route deviation** / into one evidence-bound **briefing**. |
| 00:28–00:44 | Ask the first sentence naturally, then answer with confidence. | Ask: **how are things now?** / The local **Qwen** model, served by **vLLM on Spark**, / answers with evidence / and keeps the **human in review**. |
| 00:44–00:54 | Crisp product roll-call; do not rush the final claim. | **DGX Spark**, / **NVIDIA Agent Skills**, / **DeepStream**, / **StepFun**, / **Qwen**, and **vLLM** / form one reproducible agent workload. |
| 00:54–01:00 | Short declarative hits. Half-beat pause between sentences. | **Synthetic inputs.** / **Real Spark compute.** / Intelligence stays **on board**. / **ShipMind.** |

The slash `/` marks a short pause and should not be spoken.

## Pronunciation

| Term | Suggested pronunciation | Chinese cue |
|---|---|---|
| NVIDIA | en-VID-ee-uh | 恩-维迪亚 |
| DGX | dee-jee-ex | D-G-X，逐字母 |
| GB10 | gee-bee-ten | G-B-ten |
| Grace Blackwell | grace BLACK-well | 格蕾丝·布莱克威尔 |
| ShipMind | ship-mind | ship + mind |
| Qwen | kwen | 接近“昆”，单音节 |
| vLLM | vee-el-el-em | V-L-L-M，逐字母 |
| DeepStream | deep-stream | deep + stream |
| StepFun | step-fun | step + fun |

## Recording notes

- Record at 48 kHz, 24-bit WAV, mono.
- Keep the raw voice dry: no music, room reverb, limiter or noise-gate pumping.
- Aim for peaks around -9 to -6 dBFS. Leave final loudness and ducking to the mix.
- Record two takes: one calm and cinematic, one 8–10% more urgent. Keep the timing identical.
- Hold silence from 00:59.2 to 01:00 so the final fade can close cleanly.

## Chinese meaning reference

凌晨三点，远在海上，一名工程师可能正守望着整条船。NVIDIA DGX Spark 是 ShipMind 的本地算力核心，由 GB10 Grace Blackwell 超级芯片与统一内存提供支撑。它把声学变化、仪表读数、雷达检测、声呐证据和航线偏移汇总成一份有证据依据的简报。只需问一句“现在情况如何？”，由 vLLM 在 Spark 上承载的本地 Qwen 模型就会依据证据作答，并保留人工复核。DGX Spark、NVIDIA Agent Skills、DeepStream、StepFun、Qwen 和 vLLM 共同组成一个可复现的 Agent 工作负载。合成输入，真实 Spark 计算。智能留在船上。ShipMind。
