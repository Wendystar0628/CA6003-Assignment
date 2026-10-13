// Render every scene in video/scenes/ (files starting with "_" are templates/tests and are skipped).
//   node video/render/render_all.mjs [--jobs 2] [--fps 30] [--crf 18] [--only s03_cohort_funnel,s04_dua_minimisation]
//                                    [--block 1]   (the block's scenes from video/timeline/timeline.json)
// One browser and one static server; N pages render in parallel. Prints seconds and audit count per scene.
import { chromium } from 'playwright-core';
import { readdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startServer } from './static_server.mjs';
import { renderScene, parseArgs, CHROME_ARGS } from './render.mjs';
import { prepare } from './prepare.mjs';
import { loadTimeline } from '../subtitles/build_subs.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const videoRoot = path.resolve(here, '..');
const argv = process.argv.slice(2);
let jobs = 2, only = null, block = null;
const rest = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--jobs') jobs = Number(argv[++i]);
  else if (argv[i] === '--only') only = argv[++i].split(',').map((s) => s.replace(/\.html$/, ''));
  else if (argv[i] === '--block') block = Number(argv[++i]);
  else rest.push(argv[i]);
}
const base = parseArgs(rest);
prepare();
let scenes = readdirSync(path.join(videoRoot, 'scenes')).filter((f) => f.endsWith('.html') && !f.startsWith('_'));
if (block != null) {
  const tl = loadTimeline();
  const b = tl.blocks.find((x) => x.n === block);
  if (!b) { console.error(`no block ${block} in timeline.json`); process.exit(2); }
  const files = b.scenes.map((n) => tl.scenes.find((s) => s.n === n).file);
  const missing = files.filter((f) => !existsSync(path.join(videoRoot, 'scenes', f + '.html')));
  if (missing.length) console.warn(`block ${block}: scene file(s) not found, skipped: ${missing.join(', ')}`);
  only = files.filter((f) => !missing.includes(f));
}
scenes = scenes.filter((f) => !only || only.includes(path.basename(f, '.html'))).sort();

const t0 = Date.now();
const server = await startServer(videoRoot);
const browser = await chromium.launch({ executablePath: base.chrome, headless: true, args: CHROME_ARGS });
const queue = [...scenes];
const results = [];
async function worker() {
  while (queue.length) {
    const f = queue.shift();
    const name = path.basename(f, '.html');
    try {
      results.push(await renderScene({ ...base, scene: path.join(videoRoot, 'scenes', f), out: path.join(videoRoot, 'out', name) }, { server, browser, quiet: true, prepared: true }));
    } catch (e) {
      console.error(`[${name}] FAILED: ${e.message}`);
      results.push({ name, failed: true });
    }
  }
}
await Promise.all(Array.from({ length: Math.max(1, jobs) }, worker));
await browser.close();
server.server.close();

console.log('\nscene                          frames   seconds   audit');
for (const r of results.sort((a, b) => a.name.localeCompare(b.name))) {
  console.log(r.failed
    ? `${r.name.padEnd(30)}  FAILED`
    : `${r.name.padEnd(30)}  ${String(r.frames).padStart(6)}  ${r.seconds.toFixed(1).padStart(8)}   ${r.issues.length ? r.issues.length + ' issue(s)' : 'ok'}`);
}
console.log(`total ${((Date.now() - t0) / 1000).toFixed(1)} s for ${results.length} scene(s), ${jobs} job(s)`);
if (results.some((r) => r.failed)) process.exit(1);
