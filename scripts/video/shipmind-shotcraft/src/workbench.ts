// Workbench manifest — ShipMind Promo 02 如何拆解为可编辑轨道。
// workbench（skill 目录下，`node scripts/open.mjs <本工程>`）读取 WORKBENCH，
// 把整片重建成 shots / captions / SFX 轨，每个单元与其在 shipmind/Main.tsx 中
// 的 <Sequence> 位置一一对应。所有时序均 import 自 shots.ts（唯一事实源），
// 这里不存在第二份会漂移的时间表。运动时值（缓动/相机/卡片命门参数）刻意不暴露。
import { createElement, type FC } from 'react';
import { SHOTS, TOTAL, STATEMENTS, SFX } from './shipmind/shots';
import { ShipMindPromo } from './shipmind/Main';
import { Statement } from './shipmind/Statement';
import { S1Signal } from './shipmind/S1Signal';
import { S2SparkHero } from './shipmind/S2SparkHero';
import { S3TiltReveal } from './shipmind/S3TiltReveal';
import { S4LiveStrip } from './shipmind/S4LiveStrip';
import { S5Gauge } from './shipmind/S5Gauge';
import { S6Terminal } from './shipmind/S6Terminal';
import { S7Trace } from './shipmind/S7Trace';
import { S8LocalCompute } from './shipmind/S8LocalCompute';
import { S9Outro } from './shipmind/S9Outro';

// —— schema field helpers（shape = workbench PropField）——
type Field = Record<string, unknown> & { type: string; key: string; label: string; default: unknown };
const text = (key: string, label: string, def: string): Field => ({ type: 'text', key, label, default: def });
const color = (key: string, label: string, def: string): Field => ({ type: 'color', key, label, default: def });
const bool = (key: string, label: string, def: boolean): Field => ({ type: 'boolean', key, label, default: def });

// 场景单元：component + 默认 props + 语境级 schema（节奏命门保持常量）
const scene = (
  key: keyof typeof SHOTS,
  label: string,
  component: FC,
  schema: Field[] = [],
  props: Record<string, unknown> = {},
) => ({
  id: key,
  label,
  from: SHOTS[key].from,
  duration: SHOTS[key].duration,
  component: component as FC<Record<string, unknown>>,
  props,
  schema,
});

const SHIPMIND_WORKBENCH = {
  name: 'ShipMind · Promo 02',
  fps: 30,
  width: 1920,
  height: 1080,
  total: TOTAL,
  background: '#f5f5f7',
  shots: [
    scene('s1Signal', 'S1 信号开场（细线写一次）', S1Signal),
    scene('s2SparkHero', 'S2 Spark 聚光主角（spotlight-hero-card）', S2SparkHero),
    scene('s3TiltReveal', 'S3 总览俯仰揭示（tilt-reveal）', S3TiltReveal),
    scene('s4LiveStrip', 'S4 声学纸带流（oscilloscope-stream）', S4LiveStrip),
    scene('s5Gauge', 'S5 表盘自检（needle-sweep-selftest）', S5Gauge),
    scene('s6Terminal', 'S6 AI 终端三站（terminal-3d，硬切进出）', S6Terminal),
    scene('s7Trace', 'S7 执行轨迹慢推 + 高亮', S7Trace),
    scene('s8LocalCompute', 'S8 四路汇聚 Spark', S8LocalCompute),
    scene('s9Outro', 'S9 拉远孤立收束（pull-back-isolation）', S9Outro),
  ],
  transitions: [], // 溶解在各场景内（FadeShell）；AI 暗场为硬切，无独立转场单元
  captions: STATEMENTS.map((st, i) => ({
    id: `statement-${i + 1}`,
    label: st.text,
    from: st.from,
    duration: st.duration,
    component: Statement as FC<Record<string, unknown>>,
    props: { text: st.text, duration: st.duration, dark: st.dark ?? false },
    schema: [
      text('text', '文案', st.text),
      color('color', '文字色', st.dark ? '#f5f5f7' : '#1d1d1f'),
      bool('dark', '深色场', st.dark ?? false),
    ],
    durationProp: 'duration',
    cardId: 'statement',
    cardName: '一句一镜字幕',
  })),
  sfx: SFX.map((s, i) => ({
    id: `sfx-${i + 1}`,
    from: s.from,
    duration: s.durationInFrames ?? 90,
    src: `audio/${s.src}`,
    volume: s.volume,
  })),
  // z-order：字幕在场景之上（与 Main.tsx 渲染顺序一致）
  order: ['captions'] as const,
  // 未改动的原片，供工作台逐帧对照
  original: ((props: Record<string, unknown>) => createElement(ShipMindPromo, props)) as FC<Record<string, unknown>>,
};
export const WORKBENCH = SHIPMIND_WORKBENCH;
