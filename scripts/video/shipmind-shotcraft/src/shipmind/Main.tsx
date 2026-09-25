// ShipMind Promo 02 — 主时间轴。SHOTS（shots.ts）是唯一事实源；
// 字幕/音效全部从它派生（相对表达式）。切换：浅色场之间 12f 通过共享底色
// 溶解；AI 暗场两侧硬切（DESIGN-SPEC）。
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate, useCurrentFrame, Easing } from 'remotion';
import { SHOTS, TOTAL, FADES, STATEMENTS, SFX, BGM_SRC } from './shots';
import { Statement } from './Statement';
import { BG } from './tokens';
import { S1Signal } from './S1Signal';
import { S2SparkHero } from './S2SparkHero';
import { S3TiltReveal } from './S3TiltReveal';
import { S4LiveStrip } from './S4LiveStrip';
import { S5Gauge } from './S5Gauge';
import { S6Terminal } from './S6Terminal';
import { S7Trace } from './S7Trace';
import { S8LocalCompute } from './S8LocalCompute';
import { S9Outro } from './S9Outro';

const FadeShell: React.FC<{
  fadeIn: number;
  fadeOut: number;
  duration: number;
  children: React.ReactNode;
}> = ({ fadeIn, fadeOut, duration, children }) => {
  const f = useCurrentFrame();
  const inOp = fadeIn > 0
    ? interpolate(f, [0, fadeIn], [0, 1], {
        extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
      })
    : 1;
  const outOp = fadeOut > 0
    ? interpolate(f, [duration - fadeOut, duration], [1, 0], {
        extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic),
      })
    : 1;
  return <AbsoluteFill style={{ opacity: fadeIn + fadeOut > 0 ? inOp * outOp : 1 }}>{children}</AbsoluteFill>;
};

const SCENES: { key: keyof typeof SHOTS; comp: React.FC }[] = [
  { key: 's1Signal', comp: S1Signal },
  { key: 's2SparkHero', comp: S2SparkHero },
  { key: 's3TiltReveal', comp: S3TiltReveal },
  { key: 's4LiveStrip', comp: S4LiveStrip },
  { key: 's5Gauge', comp: S5Gauge },
  { key: 's6Terminal', comp: S6Terminal },
  { key: 's7Trace', comp: S7Trace },
  { key: 's8LocalCompute', comp: S8LocalCompute },
  { key: 's9Outro', comp: S9Outro },
];

export const ShipMindPromo: React.FC<{ bgm?: boolean }> = ({ bgm = true }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {SCENES.map(({ key, comp: Comp }) => {
        const shot = SHOTS[key];
        const fade = FADES[key];
        return (
          <Sequence key={key} from={shot.from} durationInFrames={shot.duration} name={key}>
            <FadeShell fadeIn={fade.in} fadeOut={fade.out} duration={shot.duration}>
              <Comp />
            </FadeShell>
          </Sequence>
        );
      })}

      {/* 一句一镜的字幕（各自独立 Sequence，场景之上） */}
      {STATEMENTS.map((st) => (
        <Sequence
          key={st.key + st.from}
          from={st.from}
          durationInFrames={st.duration}
          name={`statement-${st.key}`}
        >
          <Statement text={st.text} duration={st.duration} dark={st.dark} top={st.top} />
        </Sequence>
      ))}

      {/* SFX 钉帧表（相对帧表达式；长样本显式截断） */}
      {SFX.map((s, i) => (
        <Sequence key={`sfx-${i}`} from={s.from} durationInFrames={s.durationInFrames ?? 90} name={`sfx-${s.src}`}>
          <Audio src={staticFile(`audio/${s.src}`)} volume={s.volume} />
        </Sequence>
      ))}

      {/* BGM：布尔 inputProp 单独包住，与 SFX 解耦（同一时间线出双版本） */}
      {bgm ? (
        <Audio
          src={staticFile(`audio/${BGM_SRC}`)}
          volume={(f: number) =>
            interpolate(
              f,
              [0, 36, TOTAL - 90, TOTAL - 6],
              [0, 0.32, 0.32, 0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.quad) },
            )
          }
        />
      ) : null}
    </AbsoluteFill>
  );
};
