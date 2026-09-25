// ShipMind promo — visual & motion tokens (from DESIGN-SPEC.md)
// Apple-minimal: warm light space, deep contrast scenes, one subject per shot.
import { Easing } from 'remotion';

export const BG = '#f5f5f7';
export const SURFACE = '#ffffff';
export const INK = '#1d1d1f';
export const MUTED = '#6e6e73';
export const FAINT = '#98989d';
export const BLUE = '#0071e3';
export const BLUE_DEEP = '#005bb8';
export const DARK = '#08090c';

export const FONT =
  '"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "PingFang SC", sans-serif';
export const MONO =
  '"Cascadia Mono", Consolas, "Courier New", monospace';

// brand axes: low-to-medium energy, serious & premium — 精致高端 preset
// (main move ~42–48f, bezier(0.4,0,0.6,1), no comic bounce).
export const EASE_SETTLE = Easing.bezier(0.4, 0, 0.6, 1);
export const EASE_POP = Easing.bezier(0.2, 1.25, 0.3, 1); // rise with overshoot (hero 命门)
export const EASE_RESEAT = Easing.bezier(0.4, 0, 0.3, 1.05);
export const EASE_OUTCUBIC = Easing.out(Easing.cubic);
export const EASE_INOUTCUBIC = Easing.inOut(Easing.cubic);
export const EASE_PAGECAM = Easing.bezier(0.33, 0, 0.15, 1); // PageCam default
