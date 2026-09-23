---
name: ShipMind 智舷
description: 浅色、克制的船端值班台，以观测和证据支撑研判。
colors:
  bg: "#f5f5f7"
  sidebar: "rgba(255,255,255,.86)"
  surface: "#ffffff"
  raised: "#f5f5f7"
  line: "#e5e5ea"
  text: "#1d1d1f"
  muted: "#6e6e73"
  accent: "#0071e3"
  teal: "#5ac8fa"
  warning: "#ff9500"
  danger: "#ff3b30"
  primary-text: "#ffffff"
  primary-hover: "#0077ed"
  nav-selected: "#e8e8ed"
  target-selected: "#eaf3ff"
  target-border: "#9bc7ff"
  range-selected: "#f0f7ff"
  alarm-bg: "#fff0ef"
  watch-bg: "#fff7e6"
  normal-bg: "#edf9f0"
  error-bg: "#fff0ef"
  error-text: "#c9342b"
  error-border: "#ffb8b3"
typography:
  headline:
    fontFamily: '"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif'
    fontSize: "28px"
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "-.025em"
  title:
    fontFamily: '"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif'
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.45
  body:
    fontFamily: '"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: '"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif'
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.6
  display-read:
    fontFamily: '"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif'
    fontSize: "42px"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "-.03em"
  body-read:
    fontFamily: '"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif'
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.9
  measurement:
    fontFamily: "Consolas,monospace"
    fontSize: "32px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  badge: "4px"
  compact: "5px"
  button: "6px"
  nav: "7px"
  inset: "8px"
  panel: "14px"
spacing:
  xs: "4px"
  sm: "8px"
  compact: "12px"
  md: "16px"
  panel-gap: "20px"
  section: "24px"
  page: "32px"
  read-section: "40px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.primary-text}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "9px 15px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.button}"
    padding: "9px 15px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.panel}"
  navigation-item:
    textColor: "{colors.muted}"
    rounded: "{rounded.nav}"
    padding: "12px 14px"
  navigation-selected:
    backgroundColor: "{colors.nav-selected}"
    textColor: "{colors.accent}"
  badge-neutral:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.muted}"
    rounded: "{rounded.badge}"
    padding: "3px 7px"
  search-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.inset}"
    padding: "7px 8px 7px 17px"
---

# Design System: ShipMind 智舷

## Overview

**Creative North Star: “清晰的值班台”**

这是对当前代码的设计归档：浅灰画布、白色分组面板、系统字体、细边界与单一蓝色操作色，形成便于持续查看观测的仪器界面。中文是主要工作语言，数字、单位、来源和状态构成阅读骨架。

Operate 场景强调紧凑对照，Read 场景通过行距、留白和行宽延长阅读节奏。两者共享字体和色板；介绍与手册不另造视觉品牌。此描述来自现有实现，不代表另行通过的效果图方案。

**Key Characteristics:**

- 轻色分层，以留白、边界和轻微阴影划分数据区域。
- Apple 蓝指向操作和选中状态，绿/橙/红只承载语义状态。
- 数值等宽，正文使用本地系统中文字体，不依赖外部字体服务。

## Colors

色值以 frontmatter 为准，与 `web/static/app.css` 的已实现取值对应。

### Primary

Apple 蓝 `accent` 用于主按钮、当前导航、选中筛选、读数与焦点；悬停主按钮使用 `primary-hover`。白色 `primary-text` 确保蓝色按钮上的文字清楚。

### Secondary

浅蓝 `teal` 用于辅助数据；绿色表示正常连接，橙色 `warning` 表示需关注，红色 `danger` 表示严重告警或失败。告警底色分别使用 `normal-bg`、`watch-bg`、`alarm-bg`。读取失败另用 `error-bg`、`error-text`、`error-border`，不可混同业务告警。

### Neutral

`sidebar` 是最深的导航与原始输出背景，`bg` 是工作空间，`surface` 托住面板，`raised` 标示内层区域。`line` 划定边界；`text` 承载主要内容，`muted` 承载解释与单位。

**The 状态可读 Rule.** 颜色同时配合状态文字、图形或选中标记；单靠色点不能表达分析是否成功。

## Typography

Operate 与 Read 均使用 `Segoe UI`、`Microsoft YaHei`、`PingFang SC`、无衬线后备的系统字体栈。时刻、测量值、耗时及原始输出使用 `Consolas` 与等宽后备；全局开启等宽数字。

- **Headline / Title：** 页面标题与面板标题使用 frontmatter 的层级；手机页面标题降至（24px），面板标题降至（16px）。
- **Operate：** 基础正文使用 `body`，实际解释多为（11–12px）；读数使用 `measurement`，保留单位与置信度在旁。紧凑元信息存在（9–10px）字号，不应继续缩小。
- **Read：** 介绍首屏使用 `display-read`，中屏降至（36px），手机降至（31px）。手册引言标题为（26px），手机为（21px）。引用正文使用 `body-read`；报告正文为（12px / 1.9）。
- **行宽：** 手册引言不超过（65ch），介绍开场不超过（60ch），边界说明不超过（75ch）。不使用装饰字体。

## Layout

桌面固定左导航宽（210px），工作区同步留出左边距；顶部栏高（72px）。主内容最大宽度（1680px），默认内边距（32px）。总览为（1.6fr / 至少 300px 的 1fr）双栏，间隔使用 `panel-gap`。面板标题内边距为（21px 23px 17px）。手册阅读区最大宽度（900px）。

响应式遵循当前 CSS 的实际断点：

- 最小（1550px）：导航宽（224px），雷达区高（360px），目标栏宽（195px）。
- 最大（1180px）：导航宽（184px），页面内边距（25px），总览比例变为（1.5fr / 至少 275px 的 1fr），间隔（16px）；目标信息下移，隐藏辅助快照说明。
- 最大（940px）：工作面板改单栏，隐藏自动刷新复选框和时钟；介绍与部署说明改单栏。态势专项页面仍保留主图与目标栏，直到手机断点。
- 最大（640px）：左导航变为宽（230px）的滑入菜单，从高（62px）的吸顶栏下方展开；工作区取消左边距，页面内边距（24px 16px）。雷达高（300px）、目标下移；表格允许内部横向滚动，最小内容宽（520px）。搜索提交按钮换行占满宽度，介绍流程变为两列。

## Elevation & Depth

静态面板不使用投影，以背景明暗和单像素边线区分层次。只有移动展开导航使用侧向阴影（`12px 0 28px #0004`），表示覆盖工作内容。普通控件的颜色、背景与边框变化为（160ms），曲线见 sidecar；没有装饰性雷达扫描。系统要求减少动态时关闭过渡、动画和滚动动画。

## Shapes

大面板使用 `panel` 圆角，小控件使用 `button`、`nav`、`badge`，内嵌图像与引用使用 `inset`。表格与正文主要依靠直线分隔，不把每段说明包进卡片。通用线框图标尺寸（20px），线宽（1.6），圆端点；导航与按钮按密度分别缩至（18px）和（16px）。

## Components

### Buttons

主操作为蓝色实心按钮，次操作使用浅灰底；默认最小高度（38px），手机刷新按钮（36px），小按钮（32px）。禁用状态透明度（0.45）并使用禁止光标；主按钮禁用时不应用悬停亮色。键盘焦点为蓝色轮廓（3px），偏移（2px）。

### Navigation

六项文字加图标导航统一使用 `navigation-item`；悬停用面板底，当前页使用 `navigation-selected` 与较重字重，并保留 `aria-current`。手机通过展开按钮进入侧栏，不将桌面六项压缩成难读的图标列。

### Chips / Filters

中性徽标表示数据类型；状态徽标带明确级别文字。量程为分段按钮，选中使用亮色文字及 `range-selected` 底色；文字标签页以底边线表示选择。手机量程最小高度（32px），文字标签和检索示例（36px）。

### Cards / Containers

面板以统一细边线和圆角收纳数据。标题附简短来源说明，局部错误在面板内显示，并将旧图像、图表和相关数据降至（0.32）透明度。加载、无结果和失败应分别使用清楚的文字，不伪造测量数值。

### Inputs / Fields

检索输入与提交按钮共享内嵌容器，透明输入底、亮色插入符和可见焦点。标签保持在输入框上方，示例作为独立按钮；查询结果保留来源、章节、可阅读引用与可展开的原始文本。

### Observation / Evidence

雷达画布与目标列表成对出现，目标按钮选中同时使用 `target-selected` 底色和 `target-border` 边框。量程与超量程提示保持可见。报告和轨迹用独立来源行；轨迹折叠项保留状态、耗时和原始输出。总览报告内部最大高度（300px），轨迹（390px）；报告专项视图取消正文高度限制。

## Do's and Don'ts

### Do:

- **Do** 复用已建立的字体、色板、圆角和分隔线；新增界面先判断是操作还是阅读场景。
- **Do** 让状态有文字、来源可查、键盘焦点可见，并保留 reduced-motion 支持。
- **Do** 在窄屏让阅读顺序自然下移，对宽表格使用内部滚动。

### Don't:

- **Don't** 把合成观测画成实时船舶遥测，或用装饰性航迹填补没有的数据。
- **Don't** 用正常状态颜色掩盖读取失败、待复核或历史数据来源。
- **Don't** 为介绍页额外引入外部字体、独立色板或重复的卡片墙。
