// The finished film: concatenate out/block_1..4.mp4 (made by compose_block.mjs), normalise loudness.
//   node video/render/compose_film.mjs [--blocks 1,2,3,4] [--out video/out/film.mp4]
// Video is stream-copied (all blocks share codec settings); audio gets loudnorm -16 LUFS, true peak
// -1 dBTP. The YouTube captions file is copied next to it: out/film.srt (= video/subtitles/full.srt).
import { spawnSync } from 'node:child_process';
import { existsSync, writeFileSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadTimeline } from '../subtitles/build_subs.mjs';
import { probeDuration } from './compose_block.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const VIDEO = path.resolve(here, '..');
const a = process.argv.slice(2);
let blocks = null, out = path.join(VIDEO, 'out', 'film.mp4');
for (let i = 0; i < a.length; i++) {
  if (a[i] === '--blocks') blocks = a[++i].split(',').map(Number);
  else if (a[i] === '--out') out = path.resolve(a[++i]);
}
const tl = loadTimeline();
blocks = blocks || tl.blocks.map((b) => b.n);
const files = blocks.map((n) => path.join(VIDEO, 'out', `block_${n}.mp4`));
const missing = files.filter((f) => !existsSync(f));
if (missing.length) { console.error('missing: ' + missing.map((f) => path.relative(process.cwd(), f)).join(', ') + ' (run compose_block.mjs <n>)'); process.exit(1); }
const list = path.join(VIDEO, 'out', 'list_film.txt');
writeFileSync(list, files.map((f) => `file '${path.basename(f)}'`).join('\n') + '\n');
const r = spawnSync('ffmpeg', ['-hide_banner', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/list_film.txt',
  '-c:v', 'copy', '-af', 'loudnorm=I=-16:TP=-1:LRA=11', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart',
  path.relative(VIDEO, out).split(path.sep).join('/')], { cwd: VIDEO, stdio: 'inherit' });
if (r.status !== 0) process.exit(1);
if (blocks.length === tl.blocks.length) copyFileSync(path.join(VIDEO, 'subtitles', 'full.srt'), out.replace(/\.mp4$/, '.srt'));
console.log(`film: ${blocks.length} block(s) -> ${path.relative(process.cwd(), out)} (${probeDuration(out).toFixed(2)} s; timeline ${tl.total} s)`);
