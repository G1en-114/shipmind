// S1 信号开场 — "船上发生的一切，都从信号开始。"
// 浅色场，一句话 + 一条细声学迹线写一次然后定住（DESIGN-SPEC 分镜 #1）。
// 迹线是纯 worldX 函数（帧确定性），一次写入，无尖峰事件（尖峰只属于 S4）。
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import { BG, BLUE, FAINT, FONT, MONO } from './tokens';

const W = 1060;
const H = 130;
const X = (1920 - W) / 2;
const Y = 600;
const WRITE_START = 36;
const WRITE_END = 108; // 72f 写入

// 平静基线 + 极缓起伏（dB 语义：-28.8 上下 ±0.9）
const wave = (x: number): number =>
  0.34 * Math.sin(x * 0.021) +
  0.27 * Math.sin(x * 0.052 + 1.7) +
  0.18 * Math.sin(x * 0.013 + 4.2) +
  0.12 * Math.sin(x * 0.087 + 2.3);
const yOf = (x: number): number => H / 2 - wave(x) * (H * 0.32);

export const S1Signal: React.FC = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [WRITE_START, WRITE_END], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear,
  });
  const N = 220;
  const nPts = Math.max(2, Math.round(N * p));
  const pts: string[] = [];
  for (let i = 0; i <= nPts; i++) {
    const px = (i / N) * W;
    pts.push(`${px.toFixed(2)},${yOf(px).toFixed(2)}`);
  }
  const headX = (nPts / N) * W;
  const headY = yOf(headX);
  const writing = f >= WRITE_START && f < WRITE_END;
  const settled = f >= WRITE_END;
  const lineIn = interpolate(f, [WRITE_START - 6, WRITE_START], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {/* 极浅基线区：两条灰色标线 */}
      <div style={{ position: 'absolute', left: X, top: Y, width: W, height: H, opacity: lineIn }}>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 1, background: 'rgba(0,0,0,0.055)' }} />
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 1, background: 'rgba(0,0,0,0.055)' }} />
        <svg width={W} height={H} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
          <polyline
            points={pts.join(' ')}
            fill="none"
            stroke={BLUE}
            strokeWidth={3}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {writing ? (
            <>
              <circle cx={headX} cy={headY} r={11} fill={BLUE} opacity={0.22} style={{ filter: 'blur(4px)' }} />
              <circle cx={headX} cy={headY} r={4.5} fill={BLUE} />
            </>
          ) : null}
        </svg>
      </div>
      {/* 落定后的微型标注（克制的英文微文案） */}
      <div
        style={{
          position: 'absolute', left: X, top: Y + H + 22, width: W,
          display: 'flex', justifyContent: 'space-between',
          fontFamily: MONO, fontSize: 18, fontWeight: 500, color: FAINT,
          opacity: settled ? 1 : 0,
        }}
      >
        <span>-10s</span>
        <span>声学频谱 · synthetic</span>
        <span>现在</span>
      </div>
      {/* 页脚数据口径（合成演示数据） */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, bottom: 44, textAlign: 'center',
          fontFamily: FONT, fontSize: 17, color: FAINT, opacity: 0.85,
        }}
      >
        演示内容 · 全部为合成观测数据
      </div>
    </AbsoluteFill>
  );
};
