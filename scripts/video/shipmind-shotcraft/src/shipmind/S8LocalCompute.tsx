// S8 计算留在船上 — 四路观测通道汇聚到 DGX Spark。
// 四条细线依次画入（路径生长）+ 一枚脉冲点各自到达，设备一次合拢环 +
// 微压；无光效群发（DESIGN-SPEC：no glow swarm）。通道名与产品语义一致
// （声学/雷达/航线/表盘 = 四路合成观测）。
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import { BG, BLUE, FAINT, FONT, MONO, EASE_OUTCUBIC } from './tokens';

const DEV_W = 470;
const DEV_H = Math.round((DEV_W * 1122) / 1402); // 376
const DEV_X = 1250 - DEV_W / 2; // 1015
const DEV_Y = 560 - DEV_H / 2; // 372

const CH = [
  { label: '声学', ox: 210, oy: 300 },
  { label: '雷达', ox: 180, oy: 452 },
  { label: '航线', ox: 210, oy: 610 },
  { label: '表盘', ox: 180, oy: 756 },
];
const EX = 1020; // 汇入设备左缘（DEV_X=1015，线头触到设备本体）
const EY = 560;

// cubic bezier 脉冲点位置（De Casteljau，纯函数）
const bez = (t: number, ox: number, oy: number) => {
  const c1x = ox + 330, c1y = oy;
  const c2x = EX - 380, c2y = EY;
  const u = 1 - t;
  const x = u * u * u * ox + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t * t * t * EX;
  const y = u * u * u * oy + 3 * u * u * t * c1y + 3 * u * t * t * c2y + t * t * t * EY;
  return { x, y };
};

export const S8LocalCompute: React.FC = () => {
  const frame = useCurrentFrame();

  const ringT = interpolate(frame, [80, 98], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const ringOp = interpolate(frame, [80, 86, 98], [0, 0.9, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const press = interpolate(frame, [80, 82, 84], [1, 0.997, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const devIn = interpolate(frame, [4, 18], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <svg width={1920} height={1080} style={{ position: 'absolute', inset: 0 }}>
        {CH.map((c, i) => {
          const t0 = 18 + i * 9;
          const draw = interpolate(frame, [t0, t0 + 18], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear,
          });
          const dotU = interpolate(frame, [t0 + 18, t0 + 32], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE_OUTCUBIC,
          });
          const dot = dotU > 0 && dotU < 1 ? bez(dotU, c.ox, c.oy) : null;
          return (
            <g key={i}>
              <path
                d={`M ${c.ox} ${c.oy} C ${c.ox + 330} ${c.oy}, ${EX - 380} ${EY}, ${EX} ${EY}`}
                fill="none"
                stroke={BLUE}
                strokeWidth={2.5}
                strokeLinecap="round"
                opacity={0.5}
                pathLength={1}
                strokeDasharray="1 1"
                strokeDashoffset={1 - draw}
              />
              {dot ? <circle cx={dot.x} cy={dot.y} r={6} fill={BLUE} /> : null}
            </g>
          );
        })}
      </svg>

      {/* 通道标签（微文案，克制的起点标注） */}
      {CH.map((c, i) => {
        const t0 = 18 + i * 9;
        const op = interpolate(frame, [t0 - 6, t0], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        });
        return (
          <div
            key={i}
            style={{
              position: 'absolute', left: c.ox - 4, top: c.oy - 46,
              fontFamily: FONT, fontSize: 32, fontWeight: 600, color: '#6e6e73',
              opacity: op,
            }}
          >
            {c.label}
          </div>
        );
      })}

      {/* Spark 设备（本地算力主体） */}
      <div
        style={{
          position: 'absolute', left: DEV_X, top: DEV_Y, width: DEV_W, height: DEV_H,
          opacity: devIn, transform: `scale(${press})`,
        }}
      >
        <Img
          src={staticFile('spark-clean.png')}
          style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block',
            filter: 'drop-shadow(0 14px 24px rgba(30,32,38,0.14)) drop-shadow(0 40px 80px rgba(30,32,38,0.18))' }}
        />
      </div>
      {/* 合拢环脉冲（一次即收） */}
      {ringOp > 0.01 ? (
        <div
          style={{
            position: 'absolute', left: DEV_X - 10, top: DEV_Y - 10,
            width: DEV_W + 20, height: DEV_H + 20, borderRadius: 36,
            border: `2.5px solid ${BLUE}`, opacity: ringOp,
            transform: `scale(${(1 + ringT * 0.05).toFixed(4)})`,
          }}
        />
      ) : null}
      {/* 设备微文案 */}
      <div
        style={{
          position: 'absolute', left: DEV_X - 60, top: DEV_Y + DEV_H + 26, width: DEV_W + 120,
          textAlign: 'center', fontFamily: MONO, fontSize: 18, fontWeight: 500, color: FAINT,
        }}
      >
        DGX SPARK · 本地推理
      </div>
    </AbsoluteFill>
  );
};
