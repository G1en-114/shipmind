// S6 AI 终端三站空间巡航 — camera · terminal-3d（库内校验通过）。
// demo 参数真相：demos/camera/terminal-3d/Terminal3D.tsx（设计坐标 480×270 ×K4）。
// 本片以 1920×1080 原生建模（K=1 相对输出，等价于设计值×4），文字按布局尺寸
// 栅格化，天然清晰。命门保持：相机=关键帧累加+逆变换（只改 pose 数据不改
// transform 串）、飞行 sin(π) 正弦拉远鼓包、距离聚焦 /1680 blur 2.2、
// 打字 0.09 窗口/输出 0.022 每行错峰、TYPE 均在到站后、第三站留 ≥0.04 尾量。
// 内容适配：三站 = 观察 → 推断 → 建议，语料取自产品真实值班日志/问询语义。
// 深色场 #08090c（DESIGN-SPEC：硬切进出保留给 AI 暗场）。
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import { DARK, FONT, MONO } from './tokens';

const DESIGN = 180; // demo 时长 180f；本场景 210f（末站 30f 静止）
const SCENE_LEN = 210;

const inOutCubic = Easing.inOut(Easing.cubic);
const outCubic = Easing.out(Easing.cubic);
const seg = (t: number, a: number, b: number, ease?: (x: number) => number): number => {
  if (b === a) return t >= b ? 1 : 0;
  const u = Math.min(1, Math.max(0, (t - a) / (b - a)));
  return ease ? ease(u) : u;
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

type Vec = Record<string, number>;
const acc = (t: number, base: Vec, kfs: { at: number[]; to: Vec }[], keys: string[], ease: (x: number) => number) => {
  const out: Vec = {};
  for (const k of keys) out[k] = base[k];
  let prev = base;
  for (const kf of kfs) {
    const u = seg(t, kf.at[0], kf.at[1], ease);
    for (const k of keys) out[k] += u * (kf.to[k] - prev[k]);
    prev = kf.to;
  }
  return out;
};

// 三站：3D 位姿（设计值×4）+ 真实产品语料（命令短、输出 3–4 行）
const DATA = [
  {
    pose: { x: -1200, y: -136, z: -440, ry: 24 },
    title: 'shipmind@spark · 值班日志',
    cmd: '$ shipmind observe --all',
    out: [
      '声学 高频段能量占比 · critical',
      '表盘 4.67 bar · 置信度 98%',
      '航线 横偏 17.8 m · 雷达 2 目标',
      '四路合成观测已汇总',
    ],
  },
  {
    pose: { x: 384, y: 248, z: 360, ry: -16 },
    title: '值班员问询',
    cmd: '$ 问 "目前怎么样？"',
    out: [
      '冷却水压 4.67 bar 异常升高',
      '声学高频段能量同步上升',
      '多路迹象一致 · 置信度 98%',
      '建议进入人工复核流程',
    ],
  },
  {
    pose: { x: 1608, y: -296, z: -240, ry: -32 },
    title: '建议与追溯',
    cmd: '$ shipmind recommend',
    out: [
      '排查冷却系统 高频段振动',
      '建议主机转速降至 85%',
      '证据链已写入 执行轨迹',
      '关键判断 交由值班员确认',
    ],
  },
];

const STEP = [
  [0, 0.02],
  [0.3, 0.44],
  [0.64, 0.78],
];
const TYPE = [0.05, 0.47, 0.81];
const PK = ['x', 'y', 'z', 'ry'];

export const S6Terminal: React.FC = () => {
  const frame = useCurrentFrame();
  const t = Math.min(frame / DESIGN, 1);

  // 相机姿态 = 关键帧累加（两段飞行，inOutCubic）
  const v = acc(t, DATA[0].pose, [
    { at: STEP[1], to: DATA[1].pose },
    { at: STEP[2], to: DATA[2].pose },
  ], PK, inOutCubic);
  // 飞行途中正弦拉远鼓包（设计 210px×4）
  let pull = 0;
  for (let i = 1; i < 3; i++) {
    const u = seg(t, STEP[i][0], STEP[i][1]);
    pull += Math.sin(u * Math.PI) * 840;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: DARK, overflow: 'hidden' }}>
      <div
        style={{
          position: 'absolute', inset: 0,
          background: 'radial-gradient(120% 90% at 50% 0%, #151827, #08090c 70%)',
          perspective: '3600px',
          transformStyle: 'preserve-3d',
          transform: 'translateY(130px)', // 整体下移：顶部留给一句字幕，避免与终端标题栏粘连
        }}
      >
        {/* 相机逆变换载体：先拉远/推近，再反转角，再反平移 */}
        <div
          style={{
            position: 'absolute', inset: 0, transformStyle: 'preserve-3d',
            transform: `translateZ(${300 * 4 - pull}px) rotateY(${-v.ry}deg) translate3d(${-v.x}px,${-v.y}px,${-v.z}px)`,
          }}
        >
          {DATA.map((d, i) => {
            const p = d.pose;
            const focus = 1 - Math.min(1, Math.abs(v.x - p.x) / 1680);
            const ty = seg(t, TYPE[i], TYPE[i] + 0.09);
            const n = Math.floor(ty * d.cmd.length + 0.0001);
            const caretOp =
              ty >= 1 ? (Math.floor(t * 26) % 2 ? 0.15 : 0.9) : Math.floor(t * 40) % 2 ? 0.35 : 1;
            return (
              <div
                key={i}
                style={{
                  position: 'absolute', left: '50%', top: '50%',
                  width: 1200, height: 704, margin: '-352px 0 0 -600px',
                  borderRadius: 36, background: '#0e1017', overflow: 'hidden',
                  boxShadow: '0 96px 240px rgba(0,0,0,.7), inset 0 0 0 4px #2a3040',
                  transform: `translate3d(${p.x}px,${p.y}px,${p.z}px) rotateY(${p.ry}deg)`,
                  opacity: 0.34 + focus * 0.66,
                  filter: `blur(${((1 - focus) * 2.2).toFixed(2)}px) brightness(${(0.7 + focus * 0.3).toFixed(3)})`,
                }}
              >
                {/* 标题栏：红黄绿灯 + 标题 */}
                <div
                  style={{
                    position: 'absolute', left: 0, top: 0, width: '100%', height: 88,
                    background: 'linear-gradient(180deg,#242a38,#1b202b)', borderBottom: '4px solid #2c3242',
                  }}
                >
                  {['#ff6058', '#ffbd2e', '#28ca42'].map((c, k) => (
                    <div key={c} style={{ position: 'absolute', left: 36 + k * 52, top: 32, width: 28, height: 28, borderRadius: '50%', background: c }} />
                  ))}
                  <div
                    style={{
                      position: 'absolute', left: 0, top: 0, width: '100%', height: 88, textAlign: 'center',
                      font: `600 32px/88px ${FONT}`, color: '#77809b',
                    }}
                  >
                    {d.title}
                  </div>
                </div>
                {/* 命令行：逐字点亮 + 尾随光标 */}
                <div style={{ position: 'absolute', left: 48, top: 128, font: `600 38px/1 ${MONO}, "Microsoft YaHei UI", sans-serif`, color: '#9dffcf', whiteSpace: 'pre' }}>
                  {Array.from(d.cmd, (ch, c) => (
                    <span key={c} style={{ opacity: c < n ? 1 : 0 }}>{ch}</span>
                  ))}
                  <span
                    style={{
                      color: '#9dffcf', opacity: caretOp, display: 'inline-block',
                      transform: `translateX(${(d.cmd.length - n) * -0.4}px)`,
                    }}
                  >
                    ▌
                  </span>
                </div>
                {/* 输出行：命令敲完后逐行错峰滑入 */}
                {d.out.map((o, k) => {
                  const ou = seg(t, TYPE[i] + 0.1 + k * 0.022, TYPE[i] + 0.145 + k * 0.022, outCubic);
                  return (
                    <div
                      key={k}
                      style={{
                        position: 'absolute', left: 48, top: 208 + k * 64,
                        font: `500 36px/1 ${MONO}, "Microsoft YaHei UI", sans-serif`,
                        color: k === 0 ? '#c9d3ea' : '#7f8aa6',
                        whiteSpace: 'pre', opacity: ou,
                        transform: `translateX(${lerp(ou, -28, 0)}px)`,
                      }}
                    >
                      {o}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// SCENE_LEN - DESIGN = 30f 末站真静止（第三站输出 0.955×180≈172f 进完 + settle）
export const S6_HOLD = SCENE_LEN - DESIGN;
