// S5 表盘自检 — gauge-readout-moves · A needle-sweep-selftest（库内校验通过）。
// demo 参数真相：demos/data/gauge-readout-moves/NeedleSweepSelftest.tsx。
// 适配：卡面判例「实战贴真 dashboard 时优先找页面里现成的 gauge 组件特写，
// 没有再造」——真实面板是 canvas 烤死指针，无法驱动；按卡口径以 SVG 复刻盘面
// （深色方块 + 白盘 + 刻度 + 红针，几何按切图像素测量），覆盖在真实切图的
// 表盘方块正上方；面板其余全部为真实截图（表盘读数 4.67 bar / 置信度 98% /
// 检测方法 动态指针，重采后的实时合成值）。落针角 = -135° + 4.67/10×270 ≈ -8.9°，
// 与真实指针方向一致。
// 命门保持：去程 12f ease-out 甩满 270°、回程落过头 8° 再回摆、落定 ≥30f 真静止。
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import { BG, BLUE, FONT } from './tokens';

const SCALE = 1.8;
const PANEL_W = 496;
const PANEL_H = 310;
const STAGE_X = 960 - (PANEL_W * SCALE) / 2;
const STAGE_Y = (1080 - PANEL_H * SCALE) / 2 + 46;

// 表盘方块（面板内 CSS px，切图测量）：左上 (36,79)，163.5 见方
const SQ = { x: 36, y: 79, s: 163.5 };
const C = SQ.s / 2; // 盘心（方块中心）
const R_FACE = 74;
const VALUE_DEG = (4.67 / 10) * 270; // 126.1°（0–10 bar 映射 270° 量程；读数以重采后的真实面板为准）
const OVERSHOOT = 8;

// 自检时序（场景相对帧）
const IGNITE = 14;
const sweepDeg = (frame: number): number => {
  if (frame <= IGNITE) return 0;
  if (frame <= IGNITE + 12) {
    return interpolate(frame, [IGNITE, IGNITE + 12], [0, 270], { easing: Easing.out(Easing.cubic) });
  }
  if (frame <= IGNITE + 32) {
    return interpolate(frame, [IGNITE + 12, IGNITE + 32], [270, VALUE_DEG - OVERSHOOT], {
      easing: Easing.inOut(Easing.cubic),
    });
  }
  return interpolate(frame, [IGNITE + 32, IGNITE + 39], [VALUE_DEG - OVERSHOOT, VALUE_DEG], {
    easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp',
  });
};

// 刻度：整圈小刻度每 15°，主刻度每 45°
const ticks: React.ReactNode[] = [];
for (let k = 0; k < 24; k++) {
  const a = (k * 15 * Math.PI) / 180;
  const major = k % 3 === 0;
  const r0 = major ? 58 : 63;
  ticks.push(
    <line
      key={k}
      x1={C + r0 * Math.sin(a)}
      y1={C - r0 * Math.cos(a)}
      x2={C + 70 * Math.sin(a)}
      y2={C - 70 * Math.cos(a)}
      stroke={major ? '#3a3a3c' : '#8e8e93'}
      strokeWidth={major ? 2.5 : 1.4}
    />,
  );
}

export const S5Gauge: React.FC = () => {
  const frame = useCurrentFrame();
  const d = sweepDeg(frame);

  // 落定环脉冲（蓝，一圈即收）
  const ringT = interpolate(frame, [53, 66], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const ringOp = interpolate(frame, [53, 58, 66], [0, 0.8, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  // 落定微压
  const press = interpolate(frame, [51, 53, 54], [1, 0.997, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <div
        style={{
          position: 'absolute', left: STAGE_X, top: STAGE_Y,
          width: PANEL_W, height: PANEL_H,
          transform: `scale(${SCALE})`, transformOrigin: 'top left',
          filter: 'drop-shadow(0 18px 40px rgba(0,0,0,0.10))',
        }}
      >
        {/* 真实面板切图（表盘读数 5.59 bar · 置信度 98% · 检测方法 动态指针） */}
        <Img
          src={staticFile('textures/live/overview-gauge.png')}
          style={{ position: 'absolute', left: 0, top: 0, width: PANEL_W, height: PANEL_H, display: 'block' }}
        />
        {/* SVG 复刻盘面：盖住烤死的真实指针，执行自检仪式 */}
        <div style={{ position: 'absolute', left: SQ.x, top: SQ.y, width: SQ.s, height: SQ.s, transform: `scale(${press})` }}>
          <svg width={SQ.s} height={SQ.s} viewBox={`0 0 ${SQ.s} ${SQ.s}`} style={{ position: 'absolute', inset: 0 }}>
            <rect x={0} y={0} width={SQ.s} height={SQ.s} rx={10} fill="#101114" />
            <circle cx={C} cy={C} r={R_FACE} fill="#f4f4f6" />
            {ticks}
            {/* 指针：默认指 12 点，rotate = -135° + d */}
            <g transform={`rotate(${(-135 + d).toFixed(3)} ${C} ${C})`}>
              <line x1={C} y1={C + 16} x2={C} y2={C - 60} stroke="#d64541" strokeWidth={5.5} strokeLinecap="round" />
            </g>
            <circle cx={C} cy={C} r={8} fill="#1d1d1f" />
            <circle cx={C} cy={C} r={3.2} fill="#f4f4f6" />
          </svg>
          {/* 落定环脉冲 */}
          {ringOp > 0.01 ? (
            <div
              style={{
                position: 'absolute', inset: -6, borderRadius: 14,
                border: `2px solid ${BLUE}`, opacity: ringOp,
                transform: `scale(${(1 + ringT * 0.045).toFixed(4)})`,
              }}
            />
          ) : null}
        </div>
      </div>
      {/* 克制的微文案（真实面板语义的英文注脚） */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: STAGE_Y + PANEL_H * SCALE + 34,
          textAlign: 'center', fontFamily: FONT, fontSize: 20, color: '#98989d',
        }}
      >
        DYNAMIC NEEDLE · SYNTHETIC READING
      </div>
    </AbsoluteFill>
  );
};
