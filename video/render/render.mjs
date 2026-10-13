// Frame-exact scene renderer.
//   node video/render/render.mjs <scene.html> [--fps 30] [--out video/out/<name>] [--crf 18]
//                                [--from s] [--to s] [--frames] [--alpha] [--chrome <path>]
// Opens the scene at 1920x1080 (deviceScaleFactor 1) in the system Chrome (no browser download),
// waits for fonts and data, calls SCENE.seek(i / fps) for every frame, captures each frame as a
// PNG and streams the PNGs into ffmpeg -> <out>.mp4 (H.264, yuv420p, CRF 18, BT.709 tags) and
// writes <out>_last.png (final frame, for checks and thumbnails). --frames also keeps every PNG
// in <out>_frames/. --alpha renders the camera slot transparent and writes <out>_alpha.mov
// (PNG codec, RGBA) for compositing over the camera clip. Prints the kit audit of the final frame.
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startServer } from './static_server.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const videoRoot = path.resolve(here, '..');
const DEFAULT_CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
export const CHROME_ARGS = ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none'];

export function parseArgs(argv) {
  const a = { fps: 30, crf: 18, frames: false, chrome: DEFAULT_CHROME };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--fps') a.fps = Number(argv[++i]);
    else if (k === '--out') a.out = argv[++i];
    else if (k === '--crf') a.crf = Number(argv[++i]);
    else if (k === '--from') a.from = Number(argv[++i]);
    else if (k === '--to') a.to = Number(argv[++i]);
    else if (k === '--frames') a.frames = true;
    else if (k === '--alpha') a.alpha = true;
    else if (k === '--chrome') a.chrome = argv[++i];
    else rest.push(k);
  }
  a.scene = rest[0];
  return a;
}

export async function renderScene(opts, shared = {}) {
  const t0 = Date.now();
  const scenePath = path.resolve(opts.scene);
  const rel = path.relative(videoRoot, scenePath).split(path.sep).join('/');
  if (rel.startsWith('..')) throw new Error(`Scene must live under ${videoRoot}`);
  const name = path.basename(scenePath, '.html');
  const out = path.resolve(opts.out || path.join(videoRoot, 'out', name));
  mkdirSync(path.dirname(out), { recursive: true });

  const server = shared.server || await startServer(videoRoot);
  const browser = shared.browser || await chromium.launch({ executablePath: opts.chrome || DEFAULT_CHROME, headless: true, args: CHROME_ARGS });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, reducedMotion: 'no-preference' });
  const page = await context.newPage();
  const logs = [];
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) logs.push(`[${m.type()}] ${m.text()}`); });
  page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`));
  try {
    const cdp = await context.newCDPSession(page);
    if (opts.alpha) await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
    await page.goto(`http://${server.host}:${server.port}/${rel}?render=1${opts.alpha ? '&alpha=1' : ''}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.SCENE_READY, null, { timeout: 30000 });
    const info = await page.evaluate(() => window.SCENE_READY);
    if (!info.fontsOK) console.warn(`[${name}] fonts missing (${info.fontsMissing.join(', ')}); fallback stack used`);
    const fps = opts.fps || 30;
    const from = Math.max(0, opts.from || 0);
    const to = Math.min(info.duration, opts.to != null ? opts.to : info.duration);
    const first = Math.round(from * fps);
    const n = Math.max(1, Math.round(to * fps) - first);

    const ffArgs = opts.alpha
      ? ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
        '-c:v', 'png', '-pix_fmt', 'rgba', '-an', out + '_alpha.mov']
      : ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', String(opts.crf ?? 18), '-pix_fmt', 'yuv420p',
      '-vf', 'scale=in_range=full:out_range=tv:out_color_matrix=bt709',
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
      '-movflags', '+faststart', '-an', out + '.mp4'];
    const ff = spawn('ffmpeg', ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
    const ffDone = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));
    const write = (buf) => new Promise((res) => (ff.stdin.write(buf) ? res() : ff.stdin.once('drain', res)));
    if (opts.frames) mkdirSync(out + '_frames', { recursive: true });

    let last = null;
    for (let i = 0; i < n; i++) {
      const t = (first + i) / fps;
      // seek, then wait one animation frame so the new state is painted before capture
      await page.evaluate((tt) => { window.SCENE.seek(tt); return new Promise((r) => requestAnimationFrame(() => r())); }, t);
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, optimizeForSpeed: true });
      last = Buffer.from(data, 'base64');
      await write(last);
      if (opts.frames) writeFileSync(path.join(out + '_frames', String(first + i).padStart(5, '0') + '.png'), last);
      if (!shared.quiet && i % (fps * 5) === 0) process.stdout.write(`\r[${name}] frame ${i + 1}/${n}`);
    }
    ff.stdin.end();
    await ffDone;
    if (!opts.alpha) writeFileSync(out + '_last.png', last);
    const issues = await page.evaluate(() => window.SCENE.audit());
    const secs = (Date.now() - t0) / 1000;
    if (!shared.quiet) process.stdout.write('\n');
    console.log(`[${name}] ${n} frames @ ${fps} fps -> ${path.relative(process.cwd(), out)}${opts.alpha ? '_alpha.mov' : '.mp4 + _last.png'} in ${secs.toFixed(1)} s`);
    console.log(`[${name}] audit of the last frame: ` + (issues.length ? '\n  - ' + issues.join('\n  - ') : 'no issues'));
    if (logs.length) console.log(`[${name}] console:\n  ` + logs.join('\n  '));
    return { name, frames: n, seconds: secs, issues, out };
  } finally {
    await context.close();
    if (!shared.browser) await browser.close();
    if (!shared.server) server.server.close();
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.scene) {
    console.error('usage: node render.mjs <scene.html> [--fps 30] [--out video/out/<name>] [--crf 18] [--from s] [--to s] [--frames]');
    process.exit(2);
  }
  if (!existsSync(opts.scene)) { console.error('scene not found: ' + opts.scene); process.exit(2); }
  renderScene(opts).catch((e) => { console.error(e); process.exit(1); });
}
