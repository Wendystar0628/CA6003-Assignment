// Render every scene in video/scenes/ (files starting with "_" are templates and are skipped).
//   node video/render/render_all.mjs [--jobs 2] [--fps 30] [--crf 18] [--only leak_gate,funnel]
// One browser and one static server; N pages render in parallel. Prints seconds per scene.
import { chromium } from 'playwright-core';
import { readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startServer } from './static_server.mjs';
import { renderScene, parseArgs, CHROME_ARGS } from './render.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const videoRoot = path.resolve(here, '..');
const argv = process.argv.slice(2);
let jobs = 2, only = null;
const rest = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--jobs') jobs = Number(argv[++i]);
  else if (argv[i] === '--only') only = argv[++i].split(',');
  else rest.push(argv[i]);
}
const base = parseArgs(rest);
const scenes = readdirSync(path.join(videoRoot, 'scenes'))
  .filter((f) => f.endsWith('.html') && !f.startsWith('_'))
  .filter((f) => !only || only.includes(path.basename(f, '.html')))
  .sort();

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
      results.push(await renderScene({ ...base, scene: path.join(videoRoot, 'scenes', f), out: path.join(videoRoot, 'out', name) }, { server, browser, quiet: true }));
    } catch (e) {
      console.error(`[${name}] FAILED: ${e.message}`);
      results.push({ name, failed: true });
    }
  }
}
await Promise.all(Array.from({ length: Math.max(1, jobs) }, worker));
await browser.close();
server.server.close();

console.log('\nscene                       frames   seconds   audit');
for (const r of results.sort((a, b) => a.name.localeCompare(b.name))) {
  console.log(r.failed
    ? `${r.name.padEnd(26)}  FAILED`
    : `${r.name.padEnd(26)}  ${String(r.frames).padStart(6)}  ${r.seconds.toFixed(1).padStart(8)}   ${r.issues.length ? r.issues.length + ' issue(s)' : 'ok'}`);
}
console.log(`total ${((Date.now() - t0) / 1000).toFixed(1)} s for ${results.length} scene(s), ${jobs} job(s)`);
if (results.some((r) => r.failed)) process.exit(1);
