// S2 Spark 聚光主角 — spotlight-hero-card 全参数移植（卡名已过 library.json 校验）。
// demo 参数真相：demos/opening/spotlight-hero-card/SpotlightHeroCard.tsx。
// 适配：主角从页面卡片换成 DGX Spark 产品渲染图（透明底，去毛边）；
// 轮廓光束沿设备包围盒跑两圈；强调色琥珀→产品蓝 #0071e3。
// 命门保持：rise 10f bezier(0.2,1.25,0.3,1)、悬停 54f sin bob(4px/40f)、
// reseat 18f press 0.997、光束两圈快慢有别、双层影随高度生长、锁定→落地 ≈98f。
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import { PageCam, CamKey } from './lib/PageCam';
import { BG, BLUE, EASE_POP, EASE_RESEAT } from './tokens';

const SCENE_LEN = 180;

// 舞台：Spark 置于 1920×1080 浅色场中央（基础宽 440，推进 2.6× 后 ≈1144px 特写）
const DEV_W = 440;
const DEV_H = Math.round((DEV_W * 1122) / 1402); // 352
const DEV_X = 960 - DEV_W / 2;
const DEV_Y = 560 - DEV_H / 2;
const RX = 28;

// 相机：正视全景（0–32 静止，聚光灯游走锁定）→ 16f 斜侧推进（rotY 34° 主导）→
// 锁死到结束。焦点取设备中心左移 30px，让设备落画面偏右。
const MCX = 960 - 30;
const MCY = 560;
const CAM_KEYS: CamKey[] = [
  { frame: 0, cx: 960, cy: 540, zoom: 0.78, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 },
  { frame: 32, cx: 960, cy: 540, zoom: 0.78, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 },
  { frame: 48, cx: MCX, cy: MCY, zoom: 2.6, rotX: 8, rotY: 34, rotZ: 2, persp: 1200 },
  { frame: 138, cx: MCX, cy: MCY, zoom: 2.6, rotX: 8, rotY: 34, rotZ: 2, persp: 1200 },
];
const PUSH_EASE = Easing.bezier(0.35, 0, 0.2, 1);

const BEAM_CORE = 'rgba(240,247,255,0.98)';

export const S2SparkHero: React.FC = () => {
  const frame = useCurrentFrame();

  const macroIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.2, 1),
  });

  // --- 游走聚光灯：4 个中间站后锁定设备心（50%, 52%）---
  const spotEase = Easing.bezier(0.4, 0, 0.3, 1);
  const spotX = interpolate(frame, [4, 8, 16, 22, 28, 48], [25, 25, 70, 42, 50, 50], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: spotEase,
  });
  const spotY = interpolate(frame, [4, 8, 16, 22, 28, 48], [30, 30, 45, 60, 52, 52], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: spotEase,
  });
  const spotOn = interpolate(frame, [2, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const poolBase = interpolate(frame, [22, 32, 48], [620, 420, 360], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.3, 1),
  });
  const poolPulse = interpolate(frame, [32, 36, 41], [0, 0.06, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const poolRx = poolBase * (1 + poolPulse);
  const poolRy = poolBase * 0.8 * (1 + poolPulse);
  const vignette = interpolate(frame, [22, 32, 48, 130, 152], [0.16, 0.34, 0.42, 0.42, 0.1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // --- 设备弹起：rise(48→58 过冲) → 悬停(58→112, 54f sin bob) → reseat(112→130) ---
  const rise = interpolate(frame, [48, 58], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE_POP,
  });
  const reseat = interpolate(frame, [112, 130], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE_RESEAT,
  });
  const lift = rise * (1 - reseat);
  const bob = Math.sin(((frame - 58) / 40) * Math.PI * 2) * 4 * lift;
  const z = 110 * lift + bob;
  const press = interpolate(frame, [126, 129, 130], [1, 0.997, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  // 双层影随高度生长（悬浮成立的关键；浅底上加深保证可读）
  const devShadow = `drop-shadow(0 ${(10 * lift).toFixed(1)}px ${(12 + 14 * lift).toFixed(1)}px rgba(24,26,32,${(0.3 * lift).toFixed(3)})) drop-shadow(0 ${(52 * lift).toFixed(1)}px ${(96 * lift).toFixed(1)}px rgba(24,26,32,${(0.34 * lift).toFixed(3)}))`;

  // 原位呼吸描边（设备腾空后，蓝描边呼吸；落地瞬间增亮消失）
  const slotVis = Math.min(1, rise * 2) * (1 - reseat);
  const landPulse = interpolate(frame, [126, 130, 134], [0, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const slotEdge = Math.min(1, 0.4 * (1 - reseat)) + landPulse * 0.6;
  const slotBreath = 0.55 + 0.45 * Math.sin(frame / 9);

  // --- 轮廓光束两圈：lap1(60→74) 快而亮，lap2(80→100) 慢而弱 ---
  const beam1Prog = interpolate(frame, [60, 74], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear,
  });
  const beam1On = frame >= 59 && frame <= 75;
  const beam2Prog = interpolate(frame, [80, 100], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.4, 1),
  });
  const beam2On = frame >= 79 && frame <= 101;
  const beamTrail = interpolate(frame, [100, 112], [0.35, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const bw = DEV_W + 6;
  const bh = DEV_H + 6;

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <AbsoluteFill style={{ opacity: macroIn }}>
        <PageCam src="textures/live/studio.png" pageH={1080} keys={CAM_KEYS} ease={PUSH_EASE}>
          {/* 页面空间：舞台即"页面"。设备以 page-space 定位。 */}
          {slotVis > 0.02 ? (
            <div
              style={{
                position: 'absolute', left: DEV_X - 3, top: DEV_Y - 3,
                width: DEV_W + 6, height: DEV_H + 6, borderRadius: RX + 3,
                border: `1.5px solid ${BLUE}`, opacity: slotEdge * (0.5 + 0.5 * slotBreath),
                pointerEvents: 'none',
              }}
            />
          ) : null}

          <div
            style={{
              position: 'absolute', left: DEV_X, top: DEV_Y, width: DEV_W, height: DEV_H,
              transform: `translateZ(${z}px) scale(${press})`,
              transformOrigin: 'center center', transformStyle: 'preserve-3d',
            }}
          >
            <Img
              src={staticFile('spark-clean.png')}
              style={{
                position: 'absolute', inset: 0, width: '100%', height: '100%',
                display: 'block', objectFit: 'contain', filter: lift > 0.01 ? devShadow : undefined,
              }}
            />
            {/* 顶面高光扫过（悬浮期） */}
            <div
              style={{
                position: 'absolute', inset: 0,
                background: 'linear-gradient(160deg, rgba(255,255,255,0.42), transparent 42%)',
                opacity: lift, pointerEvents: 'none',
              }}
            />

            {/* 轮廓光束：SVG rounded-rect 两圈 */}
            {(beam1On || beam2On) && lift > 0.4 ? (
              <svg
                width={bw} height={bh} viewBox={`0 0 ${bw} ${bh}`}
                style={{
                  position: 'absolute', left: -3, top: -3, overflow: 'visible', pointerEvents: 'none',
                  opacity: beam1On ? 1 : 0.62,
                  filter: `drop-shadow(0 0 6px ${BLUE}) drop-shadow(0 0 18px rgba(200,228,255,0.55))`,
                }}
              >
                <rect x={2} y={2} width={bw - 4} height={bh - 4} rx={RX} fill="none"
                  stroke={BLUE} strokeWidth={beam1On ? 5 : 3.5} strokeLinecap="round"
                  pathLength={1} strokeDasharray="0.14 1"
                  strokeDashoffset={-(beam1On ? beam1Prog : beam2Prog)} />
                <rect x={2} y={2} width={bw - 4} height={bh - 4} rx={RX} fill="none"
                  stroke={BEAM_CORE} strokeWidth={beam1On ? 2.5 : 1.75} strokeLinecap="round"
                  pathLength={1} strokeDasharray="0.14 1"
                  strokeDashoffset={-(beam1On ? beam1Prog : beam2Prog)} />
              </svg>
            ) : null}
            {beamTrail > 0.01 ? (
              <div
                style={{
                  position: 'absolute', inset: -3, borderRadius: RX + 3,
                  border: `1.5px solid ${BLUE}`, opacity: beamTrail, pointerEvents: 'none',
                }}
              />
            ) : null}
          </div>
        </PageCam>

        {/* 聚光灯光池 + 外部压暗（中性灰，非琥珀） */}
        <AbsoluteFill
          style={{
            background: `radial-gradient(${poolRx}px ${poolRy}px at ${spotX}% ${spotY}%, rgba(255,255,255,0.34), rgba(244,246,250,0.14) 45%, rgba(52,54,60,${vignette * spotOn}) 100%)`,
            pointerEvents: 'none', opacity: spotOn,
          }}
        />
        <AbsoluteFill
          style={{
            background: `radial-gradient(300px 220px at ${spotX - 6}% ${spotY + 10}%, rgba(255,255,255,0.22), transparent 70%)`,
            pointerEvents: 'none', opacity: spotOn * 0.7,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// 悬停期时长校验：锁定(32)→落地(130) ≈ 98f ≈ 3.3s（卡 R3：质感镜头放慢到 3 秒）
export const S2_BEAM_LAP1_FROM = 60;
export const S2_RESEAT_FRAME = 130;
export const S2_HOLD = SCENE_LEN - 138;
