// S7 执行轨迹慢推 — PageCam 慢推真实证据页 + 一处高亮落定。
// 真实素材：reports-full.png（执行轨迹 run:agent_demo\trajectory.jsonl，
// DeepStream 管线生成 / 声学异常检测 逐步耗时）。慢推后锁死，高亮一枚即收，
// 不加装饰光效。落定后 70f 真静止。
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import { PageCam, CamKey } from './lib/PageCam';
import { BG, BLUE } from './tokens';
import layout from '../live-layout.json';

const PAGE_H = layout.reports.pageH; // 2942
const TRAJ = layout.reports.boxes.trajectory; // {x:336, y:2425.5, w:1480, h:423}

// 高亮第 2 步「声学异常检测 268ms」行（实测行距 ~45，行2中心 ≈ 面板 y145）
const HL = { x: TRAJ.x + 20, y: TRAJ.y + 131, w: TRAJ.w - 40, h: 28 };

const CAM_KEYS: CamKey[] = [
  { frame: 0, cx: 960, cy: 2355, zoom: 0.92 },
  { frame: 110, cx: 1060, cy: 2455, zoom: 1.12 },
  { frame: 180, cx: 1060, cy: 2455, zoom: 1.12 },
];

export const S7Trace: React.FC = () => {
  const frame = useCurrentFrame();
  const hlIn = interpolate(frame, [76, 90], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const hlSettled = frame >= 90;

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <PageCam src="textures/live/reports-full.png" pageH={PAGE_H} keys={CAM_KEYS}>
        {/* 高亮：一枚蓝色圆角框 + 极浅填充，落定后静止 */}
        <div
          style={{
            position: 'absolute', left: HL.x, top: HL.y, width: HL.w, height: HL.h,
            borderRadius: 8,
            border: `2px solid ${BLUE}`,
            background: 'rgba(0,113,227,0.06)',
            opacity: hlIn,
            transform: `scale(${(0.985 + 0.015 * hlIn).toFixed(4)})`,
            transformOrigin: 'left center',
            boxShadow: hlSettled ? 'none' : `0 0 ${Math.round((1 - hlIn) * 12)}px rgba(0,113,227,0.25)`,
          }}
        />
      </PageCam>
    </AbsoluteFill>
  );
};
