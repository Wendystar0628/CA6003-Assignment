// Still frames at chosen times, for checking a build step without a full render.
//   node video/render/snap.mjs <scene.html> 1.0 5.5 20.2 [--out-dir video/out]
// Writes <out-dir>/<name>_at_<t>.png and prints the kit audit for each frame.
import { chromium } from 'playwright-core';
import path from 'node:path';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { startServer } from './static_server.mjs';
import { CHROME_ARGS } from './render.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const videoRoot = path.resolve(here, '..');
const argv = process.argv.slice(2);
let outDir = path.join(videoRoot, 'out');
const rest = [];
for (let i = 0; i < argv.length; i++) { if (argv[i] === '--out-dir') outDir = argv[++i]; else rest.push(argv[i]); }
const [scene, ...times] = rest;
if (!scene || !times.length) { console.error('usage: node snap.mjs <scene.html> <t> [<t> ...] [--out-dir dir]'); process.exit(2); }
const rel = path.relative(videoRoot, path.resolve(scene)).split(path.sep).join('/');
const name = path.basename(scene, '.html');
mkdirSync(outDir, { recursive: true });

const server = await startServer(videoRoot);
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: CHROME_ARGS });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.log('[pageerror] ' + e.message));
await page.goto(`http://${server.host}:${server.port}/${rel}?render=1`);
await page.waitForFunction(() => window.SCENE_READY);
await page.evaluate(() => window.SCENE_READY);
for (const ts of times) {
  const t = Number(ts);
  await page.evaluate((tt) => { window.SCENE.seek(tt); return new Promise((r) => requestAnimationFrame(() => r())); }, t);
  const file = path.join(outDir, `${name}_at_${t.toFixed(2)}.png`);
  writeFileSync(file, await page.screenshot({ type: 'png' }));
  const issues = await page.evaluate(() => window.SCENE.audit());
  console.log(`${path.relative(process.cwd(), file)}  audit: ${issues.length ? '\n  - ' + issues.join('\n  - ') : 'ok'}`);
}
await browser.close();
server.server.close();
