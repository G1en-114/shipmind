// S4 声学纸带流 — chart-live-moves · A oscilloscope-stream（库内校验通过）。
// demo 参数真相：demos/data/chart-live-moves/OscilloscopeStreamV2.tsx。
// 适配：真实页保持 grounding（PageCam 推近真实 overview 的声学面板），
// 绘图区以面板白覆盖后在同一坐标系重绘网格 + 实时流线；
// 流速 8px/f、写入点亮 + 余辉、一次突发尖峰（2.2×）、out-cubic 刹停、
// 刹停后 ≥36f 真静止；波形纯 worldX 函数（帧确定性）。
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import { PageCam, CamKey } from './lib/PageCam';
import { BG, BLUE, BLUE_DEEP } from './tokens';
import layout from '../live-layout.json';

const PANEL = layout.overview.boxes.acoustic; // page 坐标 {x:336, y:1399.2, w:963.6, h:310.2}
const PAGE_H = layout.overview.pageH; // 1802

// 绘图区（面板内 CSS px，来自切图像素测量）：x 58–950, y 66–210
// dB→y 映射：y = 66 + (-25 - dB) * 24（-25→66，-31→210），基线 -28.8→157
const PLOT = { x: 58, y: 66, w: 892, h: 144 };
const BASE_DB = -28.5;
const AMP_DB = 0.9;
const dbToY = (db: number) => PLOT.y + (-25 - db) * 24;

// 流线时序（场景相对帧）：推进 0–48；写入 56 起 8px/f；刹停 126–138；之后真静止
const HOLD = 56;
const FREEZE_START = 126;
const FREEZE_END = 138;
const SPEED = 8;
const SPIKE_X0 = 260;
const SPIKE_W = 160;
const SPIKE_GAIN = 1.2;

const env = (x: number): number => {
  if (x <= SPIKE_X0 || x >= SPIKE_X0 + SPIKE_W) return 1;
  const p = (x - SPIKE_X0) / SPIKE_W;
  return 1 + SPIKE_GAIN * (0.5 - 0.5 * Math.cos(p * Math.PI * 2));
};
const effTime = (frame: number): number => {
  const t = (f: number) => Math.max(f - HOLD, 0) * SPEED;
  if (frame <= FREEZE_START) return t(frame);
  const brakeDist = (t(FREEZE_END) - t(FREEZE_START)) * 0.45;
  return (
    t(FREEZE_START) +
    interpolate(frame, [FREEZE_START, FREEZE_END], [0, brakeDist], {
      easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp',
    })
  );
};
const wave = (x: number): number =>
  0.34 * Math.sin(x * 0.021) +
  0.27 * Math.sin(x * 0.052 + 1.7) +
  0.18 * Math.sin(x * 0.013 + 4.2) +
  0.12 * Math.sin(x * 0.087 + 2.3);
// 世界像素 → dB → 面板内 y
const dbAt = (worldX: number): number => BASE_DB + wave(worldX) * AMP_DB * env(worldX);
const yAt = (worldX: number): number => dbToY(dbAt(worldX));

// 相机：全页正视 → 推近声学面板（落定后锁死）
const CAM_KEYS: CamKey[] = [
  { frame: 0, cx: 960, cy: 880, zoom: 1.0 },
  { frame: 48, cx: PANEL.x + PLOT.x + PLOT.w / 2 - 30, cy: 1455, zoom: 1.55 },
  { frame: 180, cx: PANEL.x + PLOT.x + PLOT.w / 2 - 30, cy: 1455, zoom: 1.55 },
];

export const S4LiveStrip: React.FC = () => {
  const frame = useCurrentFrame();
  const T = effTime(frame);
  const frozen = frame >= FREEZE_END;
  const glowOp = interpolate(frame, [FREEZE_START, FREEZE_END], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // 写入点：绘图区右缘
  const N = 200;
  const pts: string[] = [];
  for (let i = 0; i <= N; i++) {
    const px = (i / N) * PLOT.w;
    const worldX = T - (PLOT.w - px);
    pts.push(`${(PLOT.x + px).toFixed(2)},${yAt(worldX).toFixed(2)}`);
  }
  const headY = yAt(T);
  const headX = PLOT.x + PLOT.w;
  const spikeK = Math.min(Math.max((env(T) - 1) / SPIKE_GAIN, 0), 1);
  const hot = spikeK > 0.22;
  const dotColor = hot ? BLUE_DEEP : BLUE;

  // 余辉段：写入点往回 160px
  const TAIL = 160;
  const tailPts: string[] = [];
  if (!frozen) {
    for (let i = 0; i <= 40; i++) {
      const px = PLOT.w - TAIL + (i / 40) * TAIL;
      const worldX = T - (PLOT.w - px);
      tailPts.push(`${(PLOT.x + px).toFixed(2)},${yAt(worldX).toFixed(2)}`);
    }
  }

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <PageCam src="textures/live/overview-full.png" pageH={PAGE_H} keys={CAM_KEYS}>
        {/* 绘图区：面板白覆盖 + 重绘网格（真实轴标/统计行保留在覆盖区外） */}
        <div
          style={{
            position: 'absolute',
            left: PANEL.x + PLOT.x - 2,
            top: PANEL.y + PLOT.y - 2,
            width: PLOT.w + 4,
            height: PLOT.h + 4,
            background: '#ffffff',
          }}
        >
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                position: 'absolute', left: 0, right: 0,
                top: (PLOT.h / 4) * i, height: 1, background: 'rgba(0,0,0,0.07)',
              }}
            />
          ))}
        </div>
        {/* 实时流线（页面空间 SVG，原点=面板原点，点为面板相对坐标） */}
        <svg
          width={PANEL.w}
          height={PANEL.h}
          viewBox={`0 0 ${PANEL.w} ${PANEL.h}`}
          style={{
            position: 'absolute',
            left: PANEL.x,
            top: PANEL.y,
            overflow: 'visible',
          }}
        >
          <polyline
            points={pts.join(' ')}
            fill="none"
            stroke={BLUE}
            strokeWidth={4}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {!frozen && glowOp > 0 ? (
            <polyline
              points={tailPts.join(' ')}
              fill="none"
              stroke="#7fb3e8"
              strokeWidth={8}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={0.5 * glowOp}
              style={{ filter: 'blur(2px)' }}
            />
          ) : null}
          {!frozen && glowOp > 0 ? (
            <>
              <circle cx={PLOT.x + PLOT.w} cy={headY} r={22} fill={dotColor} opacity={0.3 * glowOp} style={{ filter: 'blur(5px)' }} />
              <circle cx={PLOT.x + PLOT.w} cy={headY} r={9} fill={dotColor} opacity={glowOp} />
            </>
          ) : null}
        </svg>
      </PageCam>
    </AbsoluteFill>
  );
};
