// S3 真实总览俯仰揭示 — overhead-camera-moves · A tilt-reveal（库内校验通过）。
// demo 参数真相：demos/camera/overhead-camera-moves/TiltReveal.tsx。
// 适配：FakeDashboard → 真实采集的 overview-full.png（1920×1802 @2x）。
// 命门保持：rotX 关键帧 [-80, 2.6, -0.9, 0]（f25→68→72→76）、transformOrigin
// 50% 0%、perspective 600→1200 与 perspOrigin 5%→40% 联动、scale 3.2→1、
// translateY 200→0、backfaceVisibility hidden + translateZ(4px) 兜底、
// 全部动画 f76 结束后长真静止（180-76=104f）。
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import { BG } from './tokens';
import layout from '../live-layout.json';

const HOLD = 55; // 前段留白给一句字幕（空场平躺窄带期），55f 起主抬升
const MOVE = 43;
const PAGE_H = layout.overview.pageH; // 1802

export const S3TiltReveal: React.FC = () => {
  const f = useCurrentFrame();

  const rotX = interpolate(
    f,
    [HOLD, HOLD + MOVE, HOLD + MOVE + 4, HOLD + MOVE + 8],
    [-80, 2.6, -0.9, 0],
    { easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );
  const p = interpolate(f, [HOLD, HOLD + MOVE], [0, 1], {
    easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const scale = interpolate(p, [0, 1], [3.2, 1]);
  const ty = interpolate(p, [0, 1], [200, 0]);
  const persp = interpolate(p, [0, 1], [600, 1200]);
  const perspY = interpolate(p, [0, 1], [5, 40]);

  return (
    <AbsoluteFill style={{ backgroundColor: BG, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: 0, perspective: persp, perspectiveOrigin: `50% ${perspY}%` }}>
        <div
          style={{
            width: 1920,
            height: PAGE_H,
            transformOrigin: '50% 0%',
            transform: `translateY(${ty}px) scale(${scale}) rotateX(${rotX}deg)`,
            backfaceVisibility: 'hidden',
          }}
        >
          <div style={{ transform: 'translateZ(4px)' }}>
            <Img
              src={staticFile('textures/live/overview-full.png')}
              style={{ position: 'absolute', top: 0, left: 0, width: 1920, height: PAGE_H, display: 'block' }}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
