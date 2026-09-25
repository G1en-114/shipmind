// S9 收束 — tension-camera-moves · D pull-back-isolation（库内校验通过）。
// demo 参数真相：demos/camera/tension-camera-moves/PullBackIsolation.tsx。
// 适配：主卡 = ShipMind 字标卡（关键判断，交给人。）；兄弟卡 = 8 张真实
// 采集切图；背景沉入 #08090c（DESIGN-SPEC 深色）。命门保持：scale 2.2→0.62
// / 110f out-cubic、origin 锁主卡中心、兄弟卡按距离错峰熄灭（帧 30 起每 8f
// 一张、16f 内 opacity→0 + brightness→0.3）、主卡双层白光晕 60–100f 淡入、
// 全片句号真静止 ≥40f。
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import { BG, DARK, INK, MUTED, FAINT, FONT } from './tokens';

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

// 8 张真实切图兄弟卡：相对主卡中心的偏移 + 显示尺寸（按切图真实比例）
const SIBS = [
  { src: 'overview-ai', dx: -620, dy: -330, w: 400, h: 158 },
  { src: 'overview-situation', dx: 10, dy: -390, w: 380, h: 220 },
  { src: 'overview-radar', dx: 620, dy: -320, w: 360, h: 182 },
  { src: 'overview-console', dx: -680, dy: 20, w: 440, h: 89 },
  { src: 'overview-acoustic', dx: 700, dy: 40, w: 400, h: 129 },
  { src: 'overview-gauge', dx: -600, dy: 360, w: 230, h: 144 },
  { src: 'reports-trajectory', dx: 40, dy: 400, w: 400, h: 114 },
  { src: 'overview-route', dx: 640, dy: 350, w: 380, h: 30 },
].map((s) => ({ ...s, dist: Math.hypot(s.dx, s.dy) }));

// 按离主卡距离排名 → 错峰熄灭顺序（近的先灭）
const RANKED = SIBS.map((_, i) => i).sort((a, b) => SIBS[a].dist - SIBS[b].dist);
const FADE_START = RANKED.reduce<number[]>((acc0, idx, rank) => {
  acc0[idx] = 30 + rank * 8;
  return acc0;
}, []);
const FADE_DUR = 16;

const HERO_W = 640;
const HERO_H = 420;

export const S9Outro: React.FC = () => {
  const frame = useCurrentFrame();

  // 相机后拉：2.2（怼在字卡特写）→ 0.75（大远景孤悬；0.62 为卡内典型值，
  // 本片上调到 0.75 保证收尾句在终帧 ≥32px 可读——终检 Q11 判例）
  const scale = interpolate(frame, [0, 110], [2.2, 0.75], {
    easing: Easing.out(Easing.cubic), ...clamp,
  });

  // 背景沉入黑暗：#f5f5f7 → #08090c（60–110f）
  const bgT = interpolate(frame, [60, 110], [0, 1], { easing: Easing.inOut(Easing.quad), ...clamp });
  const mix = (a: number, b: number) => Math.round(a + (b - a) * bgT);
  const bg = `rgb(${mix(245, 8)},${mix(245, 9)},${mix(247, 12)})`;

  // 主卡白光晕淡入（60–100f）
  const glow = interpolate(frame, [60, 100], [0, 0.4], { ...clamp });

  return (
    <AbsoluteFill style={{ backgroundColor: bg, overflow: 'hidden', position: 'relative' }}>
      <div
        style={{
          position: 'absolute', inset: 0,
          transform: `scale(${scale})`,
          transformOrigin: '960px 540px',
        }}
      >
        {/* 兄弟卡：真实切图，错峰熄灭 */}
        {SIBS.map((s, i) => {
          const t0 = FADE_START[i];
          const op = interpolate(frame, [t0, t0 + FADE_DUR], [1, 0], {
            easing: Easing.out(Easing.quad), ...clamp,
          });
          const bright = interpolate(frame, [t0, t0 + FADE_DUR], [1, 0.3], { ...clamp });
          return (
            <div
              key={s.src}
              style={{
                position: 'absolute',
                left: 960 + s.dx - s.w / 2,
                top: 540 + s.dy - s.h / 2,
                width: s.w,
                height: s.h,
                opacity: op,
                filter: `brightness(${bright})`,
                borderRadius: 10,
                boxShadow: '0 10px 30px rgba(0,0,0,0.10)',
                overflow: 'hidden',
              }}
            >
              <Img
                src={staticFile(`textures/live/${s.src}.png`)}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              />
            </div>
          );
        })}

        {/* 主卡：ShipMind 字标，孤悬暗场中央 */}
        <div
          style={{
            position: 'absolute',
            left: 960 - HERO_W / 2,
            top: 540 - HERO_H / 2,
            width: HERO_W,
            height: HERO_H,
            borderRadius: 16,
            background: '#ffffff',
            boxShadow: `0 0 80px rgba(255,255,255,${glow.toFixed(3)}), 0 0 160px rgba(255,255,255,${(glow * 0.6).toFixed(3)})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 96, letterSpacing: '-0.02em', color: INK, lineHeight: 1 }}>
            Ship<span style={{ color: '#0071e3' }}>Mind</span>
          </div>
          <div style={{ width: 64, height: 3, borderRadius: 2, background: '#0071e3', marginTop: 28, marginBottom: 26 }} />
          <div style={{ fontFamily: FONT, fontWeight: 600, fontSize: 44, color: MUTED }}>关键判断，交给人。</div>
          <div style={{ position: 'absolute', bottom: 28, fontFamily: FONT, fontSize: 22, color: FAINT }}>
            本地推理 · 合成演示数据
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 常量导出供 workbench/终检引用
export const S9_HERO = { w: HERO_W, h: HERO_H };
export const S9_DARK = DARK;
export const S9_BG_LIGHT = BG;
