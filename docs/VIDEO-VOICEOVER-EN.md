# ShipMind 60-second English voice-over

This script matches the six burned-in English subtitle cards in the v10 promo. Target delivery: a mature male broadcast voice with calm authority and restrained urgency. All six passages use one base synthesis rate; only small 1.01–1.10× timing corrections keep scene boundaries clean.

The generated delivery uses `en-US-ChristopherNeural` as its source voice, then applies slower pacing, lower pitch, broadcast EQ, compression and loudness normalization. It follows the supplied sample's broad performance direction; it is not an exact clone of the sample speaker.

## Clean recording copy

At three a.m., an unfamiliar vibration breaks a ship's steady rhythm.

With NVIDIA DGX Spark onboard, ShipMind brings powerful local AI to the watch—compact, responsive, and ready beyond the network.

It unites acoustics, gauges, radar, sonar, and route movement into one clear, evidence-backed picture.

The engineer asks, “How are things now?” In seconds, the local AI traces the change, cites the signals, and shows what to inspect next.

Agent Skills, DeepStream, StepFun, Qwen, and vLLM turn Spark into a complete, reproducible workflow.

Safer ships. Clearer decisions. ShipMind.

## Timed performance copy

| Time | Delivery | Exact line |
|---|---|---|
| 00:00–00:06 | Quiet tension; land on **steady rhythm**. | At **three a.m.**, / an unfamiliar vibration breaks a ship's **steady rhythm**. |
| 00:06–00:17 | Open up on the product name and three benefits. | With **NVIDIA DGX Spark onboard**, / ShipMind brings powerful local AI to the watch— / **compact, responsive**, and ready **beyond the network**. |
| 00:17–00:28 | Build cleanly through the sensor list; land on one picture. | It unites **acoustics, gauges, radar, sonar**, / and route movement / into one clear, **evidence-backed picture**. |
| 00:28–00:44 | Ask naturally; answer with growing confidence. | The engineer asks, **“How are things now?”** / In seconds, the local AI traces the change, / cites the signals, / and shows what to inspect next. |
| 00:44–00:54 | Crisp platform roll-call; finish on workflow. | **Agent Skills, DeepStream, StepFun, Qwen**, and **vLLM** / turn Spark into a complete, reproducible **workflow**. |
| 00:54–01:00 | Deliver as three confident beats and a brand sign-off. | **Safer ships.** / **Clearer decisions.** / **ShipMind.** |

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
