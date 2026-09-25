// Apple-style one-sentence statement per shot. Rendered inside its own
// <Sequence from={st.from} durationInFrames={st.duration}>; `duration` comes
// from the STATEMENTS table in shots.ts.
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { INK, FONT } from './tokens';

export const Statement: React.FC<{
  text: string;
  duration: number;
  dark?: boolean;
  fadeIn?: number;
  fadeOut?: number;
  top?: number;
  size?: number;
}> = ({ text, duration, dark, fadeIn = 12, fadeOut = 12, top = 104, size = 64 }) => {
  const local = useCurrentFrame();
  const inOp = interpolate(local, [0, fadeIn], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const outOp = interpolate(local, [duration - fadeOut, duration], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const rise = interpolate(local, [0, fadeIn], [14, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top,
        textAlign: 'center',
        fontFamily: FONT,
        fontSize: size,
        fontWeight: 700,
        letterSpacing: '-0.015em',
        lineHeight: 1.25,
        color: dark ? '#f5f5f7' : INK,
        opacity: inOp * outOp,
        transform: `translateY(${rise}px)`,
      }}
    >
      {text}
    </div>
  );
};
