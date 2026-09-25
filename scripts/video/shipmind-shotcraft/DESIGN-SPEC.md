# ShipMind Promo 02 — Shotcraft Design Spec

## Mode and product brief

- Mode: autonomous free creation.
- Purpose: a second, independent product film for judges and technical partners.
- Audience: maritime engineers, hackathon judges, DGX Spark / local-AI partners.
- Belief to earn: ShipMind turns separate synthetic onboard observations into a clear, reviewable watch picture while keeping inference local and the human responsible for the decision.
- Required proof: real ShipMind overview, radar, acoustic strip, gauge, Spark AI console, execution trace / report, DGX Spark as the compute subject.
- Data boundary: only repository demo fixtures and synthetic observations. The film must not imply shipboard validation, production customers, or autonomous decisions.
- Output: 1920×1080, 30 fps, about 50 seconds, Chinese primary copy, restrained English microcopy.

## Requirement-to-execution decisions

| Requirement | Execution decision |
|---|---|
| Apple-like simplicity | Warm `#f5f5f7` space, deep `#08090c` contrast scenes, one subject and one sentence per shot, no decorative collage. |
| Real product | Capture local pages at 1920×1080 with deviceScaleFactor 2; use element cutouts and layout coordinates. |
| DGX Spark must be visible | Clean transparent Spark product render gets one full hero action and returns as the local-compute anchor. |
| Real-time signals | Acoustic curve streams as a paper tape; gauge performs one physical self-test and settles; radar stays recognizably from the product. |
| AI value | Ask/answer terminal becomes a spatial three-station journey: observe → infer → recommend. |
| Human control and evidence | Final functional proof uses reports / trajectory screenshot and the line “关键判断，交给人”. |
| Audio restraint | Quiet tech-house bed plus sparse cinematic whoosh / impact / light accents; also render a no-BGM version with SFX retained. |

## Visual and motion tokens

- Product palette: background `#f5f5f7`, surface `#ffffff`, text `#1d1d1f`, muted `#6e6e73`, action blue `#0071e3`, dark `#08090c`.
- Type: local Microsoft YaHei UI / Segoe UI; heavy display at 72–104 px, body at 28–34 px, microcopy at 18–22 px.
- Radius: 14 px product panels; 22–28 px only for cinematic framing shells.
- Light: broad neutral studio key; shadows with vertical offset and soft falloff; no colored halo.
- Brand axes: low-to-medium energy, serious and premium. Main move ~42–48f, cubic or bezier `(0.4,0,0.6,1)`, no comic bounce. Mechanical gauge may use its documented 5–8° rebound.
- Holds: every hero action finishes with at least 30f of true stillness.

## Reference motion breakdown

| Technique | Reference implementation | Adaptation |
|---|---|---|
| Large white space | One centered sentence or one page object at a time | Preserve; use ShipMind system colors and Chinese copy. |
| UI as physical object | Screens tilt, rise and settle in a clean studio | Use PageCam / tilt-reveal with real 2× page texture. |
| Minimal typography | Short declarative lines between product shots | Keep each card to one claim; no persistent lower-third subtitles. |
| Soft transitions | Bright fields dissolve and objects carry across cuts | 10–16f luminance-matched transitions; reserve hard cut for AI dark scene. |
| Product close | Brand wordmark lands and holds | Pull-back isolation resolves to ShipMind and Spark, then holds 40f. |

## Function-to-shot mapping

| Product function | Chosen card / style | Exact demo source | Reason |
|---|---|---|---|
| Spark as product hero | `spotlight-hero-card` | `demos/opening/spotlight-hero-card/SpotlightHeroCard.tsx` | A complete single-subject action arc with premium pace. |
| Overview reveal | `overhead-camera-moves · tilt-reveal` | `demos/camera/overhead-camera-moves/TiltReveal.tsx` | Turns the real dashboard into a physical product surface. |
| Acoustic continuity | `chart-live-moves · oscilloscope-stream` | `demos/data/chart-live-moves/OscilloscopeStreamV2.tsx` | Expresses live continuity through right-edge writing and one event. |
| Gauge reading | `gauge-readout-moves · needle-sweep-selftest` | `demos/data/gauge-readout-moves/NeedleSweepSelftest.tsx` | Gives the instrument one credible mechanical ritual and a stable final value. |
| AI workflow | `terminal-3d` | `demos/camera/terminal-3d/Terminal3D.tsx` | Converts logs and reasoning into a readable spatial journey. |
| Closing | `tension-camera-moves · pull-back-isolation` | `demos/camera/tension-camera-moves/PullBackIsolation.tsx` | Leaves one final responsible-decision message in a quiet dark field. |

## Storyboard and frame timeline

| # | Time | Shot | Key motion |
|---|---:|---|---|
| 1 | 0–5s | “船上发生的一切，都从信号开始。” | Thin acoustic trace writes once, then holds. |
| 2 | 5–11s | Spark hero: “一台设备。守住一条航线。” | Spotlight locks; Spark rises, floats, settles. |
| 3 | 11–17s | Real overview: “每一种观测，汇成一张值班图。” | Dashboard tilts from tabletop to front-on and holds. |
| 4 | 17–23s | Radar + acoustic + route: “信号持续流动。” | Real page remains grounded; live strip writes across once. |
| 5 | 23–28s | Gauge: “读数不再是一张静态图片。” | Needle sweeps full range, rebounds to the live panel reading (4.67 bar at final capture), locks. |
| 6 | 28–35s | AI: “直接问：现在怎么样？” | Three dark console stations: observe → infer → recommend. |
| 7 | 35–41s | Trace and report: “每一步，都能追溯。” | Slow push through the real evidence page, one highlight settles. |
| 8 | 41–46s | Local compute: “计算留在船上。” | Four data paths converge on Spark; no glow swarm. |
| 9 | 46–50s | “关键判断，交给人。 ShipMind.” | Pull back, surroundings extinguish, wordmark holds. |

Production release: internally approved for implementation after checking all required functions, proof sources, data boundaries, selected card constraints, and hold budgets.

Amendments during implementation (independent review round 1):
- Gauge value follows the live synthetic panel at final capture: 4.67 bar (spec draft said 5.38; earlier captures showed 5.59). All scenes (S5 needle settle, S6 terminal lines) stay consistent with the captured panel.
- Overview page re-captured with 6.5s settle so async panels (值班日志/雷达/航线) show real content instead of loading placeholders.
- S2 sentence timed to the wide-shot phase only (clear of the 2.6× close-up); S9 closing card enlarged (终态 scale 0.75) so the final line reads ≥32px; S6 dark world shifted down 130px to clear its title bar.
