// Single source of truth for the film's timeline. Captions and SFX pins are
// derived from SHOTS with relative expressions — never bare frame numbers
// (pipeline 阶段5.9 / 阶段6.4).
export const FPS = 30;

export const SHOTS = {
  s1Signal: { from: 0, duration: 150 }, // 0–5s    信号开场：细线写一次
  s2SparkHero: { from: 150, duration: 180 }, // 5–11s   Spark 聚光主角
  s3TiltReveal: { from: 330, duration: 180 }, // 11–17s  真实总览俯仰揭示
  s4LiveStrip: { from: 510, duration: 180 }, // 17–23s  声学纸带流
  s5Gauge: { from: 690, duration: 150 }, // 23–28s  表盘自检
  s6Terminal: { from: 840, duration: 210 }, // 28–35s  AI 三站空间巡航（硬切进出）
  s7Trace: { from: 1050, duration: 180 }, // 35–41s  执行轨迹慢推
  s8LocalCompute: { from: 1230, duration: 150 }, // 41–46s  四路汇聚 Spark
  s9Outro: { from: 1380, duration: 150 }, // 46–51s  拉远孤立 + 字标
} as const;

export const TOTAL =
  SHOTS.s9Outro.from + SHOTS.s9Outro.duration; // 1530f = 51s

// light→light cuts dissolve through the shared bg; the AI dark scene is
// entered/left on hard cuts (DESIGN-SPEC: reserve hard cut for AI dark scene).
export const FADES = {
  s1Signal: { in: 0, out: 12 },
  s2SparkHero: { in: 12, out: 12 },
  s3TiltReveal: { in: 12, out: 12 },
  s4LiveStrip: { in: 12, out: 12 },
  s5Gauge: { in: 12, out: 0 }, // hard cut into dark terminal
  s6Terminal: { in: 0, out: 0 }, // hard cut both sides
  s7Trace: { in: 0, out: 12 },
  s8LocalCompute: { in: 12, out: 12 },
  s9Outro: { in: 12, out: 0 },
} as const;

// one sentence per shot, shown in clean whitespace (no persistent lower-thirds)
const S = SHOTS;
export const STATEMENTS: {
  key: keyof typeof SHOTS;
  text: string;
  dark?: boolean;
  top?: number;
  from: number;
  duration: number;
}[] = [
  { key: 's1Signal', text: '船上发生的一切，都从信号开始。', from: S.s1Signal.from + 14, duration: 124 },
  { key: 's2SparkHero', text: '一台设备。守住一条航线。', from: S.s2SparkHero.from + 2, duration: 44 },
  { key: 's3TiltReveal', text: '每一种观测，汇成一张值班图。', from: S.s3TiltReveal.from + 6, duration: 49 },
  { key: 's4LiveStrip', text: '信号持续流动。', from: S.s4LiveStrip.from + 8, duration: 30 },
  { key: 's5Gauge', text: '读数不再是一张静态图片。', from: S.s5Gauge.from + 10, duration: 88 },
  { key: 's6Terminal', text: '直接问：现在怎么样？', dark: true, top: 80, from: S.s6Terminal.from + 10, duration: 64 },
  { key: 's7Trace', text: '每一步，都能追溯。', from: S.s7Trace.from + 6, duration: 56 },
  { key: 's8LocalCompute', text: '计算留在船上。', from: S.s8LocalCompute.from + 12, duration: 88 },
];

// sound design pinned to animation beats — all `from` are SHOTS-relative
// expressions. Volumes set per source; keyboard samples get explicit
// durationInFrames (long-sample rule).
export const SFX: { from: number; src: string; volume: number; durationInFrames?: number }[] = [
  // S1 信号开场
  { from: S.s1Signal.from + 8, src: 'transition-soft.mp3', volume: 0.35 },
  { from: S.s1Signal.from + 36, src: 'swoosh-quick.mp3', volume: 0.28 }, // 细线起笔
  // S2 Spark 聚光主角（卡内钉法：rise=+48, beam=+60, reseat=+130）
  { from: S.s2SparkHero.from + 48, src: 'whoosh-big.mp3', volume: 0.5 },
  { from: S.s2SparkHero.from + 60, src: 'sparkle.mp3', volume: 0.35 },
  { from: S.s2SparkHero.from + 130, src: 'transition-snap.mp3', volume: 0.5 },
  // S3 俯仰揭示（前 55f 字幕留白；主抬升 +55，落定 +106）
  { from: S.s3TiltReveal.from + 55, src: 'whoosh-fast.mp3', volume: 0.4 },
  { from: S.s3TiltReveal.from + 106, src: 'transition-snap.mp3', volume: 0.4 },
  // S4 纸带流（推进 +2，尖峰经过写入点 ≈+97）
  { from: S.s4LiveStrip.from + 2, src: 'swoosh-quick.mp3', volume: 0.32 },
  { from: S.s4LiveStrip.from + 97, src: 'pop.mp3', volume: 0.4 },
  // S5 表盘自检（点火 +14，落定 +53）
  { from: S.s5Gauge.from + 14, src: 'swoosh-quick.mp3', volume: 0.4 },
  { from: S.s5Gauge.from + 53, src: 'pop.mp3', volume: 0.5 },
  // S6 终端三站（硬切；打字机逐站 keyboard；站间 soft）
  { from: S.s6Terminal.from + 9, src: 'keyboard.mp3', volume: 0.4, durationInFrames: 40 },
  { from: S.s6Terminal.from + 54, src: 'transition-soft.mp3', volume: 0.3 },
  { from: S.s6Terminal.from + 85, src: 'keyboard.mp3', volume: 0.4, durationInFrames: 40 },
  { from: S.s6Terminal.from + 115, src: 'transition-soft.mp3', volume: 0.3 },
  { from: S.s6Terminal.from + 146, src: 'keyboard.mp3', volume: 0.35, durationInFrames: 28 },
  // S7 轨迹慢推（推进起 +2，高亮落定 +88）
  { from: S.s7Trace.from + 2, src: 'swoosh-quick.mp3', volume: 0.3 },
  { from: S.s7Trace.from + 88, src: 'pop.mp3', volume: 0.35 },
  // S8 四路汇聚（逐线到达递减 +50/+59/+68/+77，合拢 +80）
  { from: S.s8LocalCompute.from + 6, src: 'transition-soft.mp3', volume: 0.3 },
  { from: S.s8LocalCompute.from + 50, src: 'pop.mp3', volume: 0.4 },
  { from: S.s8LocalCompute.from + 59, src: 'pop.mp3', volume: 0.32 },
  { from: S.s8LocalCompute.from + 68, src: 'pop.mp3', volume: 0.26 },
  { from: S.s8LocalCompute.from + 77, src: 'pop.mp3', volume: 0.2 },
  { from: S.s8LocalCompute.from + 80, src: 'impact-cine.mp3', volume: 0.45, durationInFrames: 50 },
  // S9 收束固定句式：riser(拉远起) → impact(字标孤悬) → sparkle(余韵)
  { from: S.s9Outro.from + 30, src: 'riser-cine.mp3', volume: 0.4, durationInFrames: 80 },
  { from: S.s9Outro.from + 110, src: 'impact-cine.mp3', volume: 0.55, durationInFrames: 40 },
  { from: S.s9Outro.from + 118, src: 'sparkle.mp3', volume: 0.3, durationInFrames: 30 },
];

export const BGM_SRC = 'bgm/bgm-tech-house.mp3';
