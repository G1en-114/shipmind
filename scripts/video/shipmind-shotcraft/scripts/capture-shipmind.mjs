import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(here, '../public/textures/live');
const layoutPath = path.resolve(here, '../src/live-layout.json');
const browser = await puppeteer.launch({
  executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  headless: true,
  args: ['--no-sandbox', '--disable-gpu'],
});
const page = await browser.newPage();
await page.setViewport({width: 1920, height: 1080, deviceScaleFactor: 2});
fs.mkdirSync(outDir, {recursive: true});

const pages = [
  {
    name: 'overview', path: '/?theme=light#overview', wait: 6500,
    boxes: [
      ['ai', '.ai-panel'], ['situation', '.situation-panel'], ['alerts', '.alerts-panel'],
      ['acoustic', '.acoustic-panel'], ['gauge', '.visual-panel'], ['radar', '.radar-stage'],
      ['route', '.route-strip'], ['console', '.ai-console'],
    ],
    cutouts: [
      ['overview-ai', '.ai-panel'], ['overview-situation', '.situation-panel'],
      ['overview-acoustic', '.acoustic-panel'], ['overview-gauge', '.visual-panel'],
      ['overview-radar', '.radar-stage'], ['overview-route', '.route-strip'], ['overview-console', '.ai-console'],
    ],
  },
  {
    name: 'reports', path: '/?theme=light#reports', wait: 2600,
    boxes: [['trajectory', '.trajectory-panel'], ['report', '.report-panel']],
    cutouts: [['reports-trajectory', '.trajectory-panel'], ['reports-report', '.report-panel']],
  },
  {
    name: 'about', path: '/?theme=light#about', wait: 900,
    boxes: [['opening', '.about-opening'], ['capabilities', '.capability-table'], ['deployment', '.deployment-section']],
    cutouts: [['about-opening', '.about-opening'], ['about-capabilities', '.capability-table']],
  },
];

const pageBox = async (el) => el.evaluate((e) => {
  const r = e.getBoundingClientRect();
  return {x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height};
});
const layout = {pageW: 1920, scale: 2};

for (const pg of pages) {
  await page.goto(`http://127.0.0.1:8894${pg.path}`, {waitUntil: 'domcontentloaded'});
  await page.evaluate(() => document.fonts.ready);
  await new Promise((r) => setTimeout(r, pg.wait));
  const pageH = await page.evaluate(() => document.documentElement.scrollHeight);
  const entry = {pageH, boxes: {}, cutouts: []};
  layout[pg.name] = entry;
  await page.screenshot({path: path.join(outDir, `${pg.name}-full.png`), fullPage: true});
  for (const [key, selector] of pg.boxes) {
    const el = await page.$(selector);
    entry.boxes[key] = el ? await pageBox(el) : null;
  }
  for (const [name, selector] of pg.cutouts) {
    const el = await page.$(selector);
    if (!el) continue;
    const bb = await pageBox(el);
    const file = `${name}.png`;
    await el.screenshot({path: path.join(outDir, file), omitBackground: false});
    entry.cutouts.push({file, ...bb});
  }
  console.log(`captured ${pg.name} ${pageH}px`);
}
fs.writeFileSync(layoutPath, JSON.stringify(layout, null, 2));
await browser.close();
console.log(layoutPath);
