// Compose one member block: scenes in timeline order + the member's camera take in the fixed PiP slot
// + burned-in captions.
//   node video/render/compose_block.mjs <n> [--take video/takes/block_<n>.mp4] [--take-offset s]
//        [--render] [--no-subs] [--out video/out/block_<n>.mp4] [--timeline path] [--crf 18]
// Steps
//   1. prepare(): team names and subtitles are refreshed (video/subtitles/block_<n>.ass)
//   2. concat video/out/<file>.mp4 for the block's scenes (timeline.json order) -> out/scenes_block_<n>.mp4
//      (--render first renders scenes whose mp4 is missing)
//   3. overlay the take, scaled and centre-cropped to 384x216, at x 1416, y 748 (Kit.GRID.camera);
//      the take's audio becomes the block audio. Without a take: a neutral grey "camera" placeholder
//      and silent audio. The 1 px hairline and the name tag are already in the scene renders.
//   4. burn the captions with libass (ass filter, IBM Plex Sans from out/fonts/) and encode
//      H.264 CRF 18 yuv420p BT.709 + AAC 192 kbit/s 48 kHz -> out/block_<n>.mp4
// Take offset (seconds into the take where the block starts): --take-offset, else overrides.json
// "takes": {"<n>": {"offset": s}}, else 0.
import { spawnSync } from 'node:child_process';
import { existsSync, writeFileSync, readFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { prepare } from './prepare.mjs';
import { ensureFonts } from './fonts.mjs';
import { loadTimeline, writeAll, DEFAULT_TIMELINE, DEFAULT_OVERRIDES } from '../subtitles/build_subs.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const VIDEO = path.resolve(here, '..');
export const PIP = { x: 1416, y: 748, w: 384, h: 216 };   // mirrors Kit.GRID.camera
const rel = (p) => path.relative(VIDEO, p).split(path.sep).join('/');   // ffmpeg runs with cwd = video/

function ff(args, label) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-y', '-loglevel', 'error', ...args], { cwd: VIDEO, stdio: ['ignore', 'inherit', 'inherit'] });
  if (r.status !== 0) throw new Error(`ffmpeg failed (${label}): ffmpeg ${args.join(' ')}`);
}
export function probeDuration(file) {
  const r = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nk=1:nw=1', file], { encoding: 'utf8' });
  return Number(r.stdout.trim());
}
const hasAudio = (file) => spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', file], { encoding: 'utf8' }).stdout.trim() !== '';

export async function composeBlock(n, o = {}) {
  const timelineFile = o.timeline ? path.resolve(o.timeline) : DEFAULT_TIMELINE;
  prepare({ quiet: true });
  let subsDir = path.join(VIDEO, 'subtitles');
  if (o.timeline) {   // test timelines get their own caption files
    subsDir = path.join(VIDEO, 'out', 'subs_' + path.basename(timelineFile, '.json'));
    writeAll({ timeline: timelineFile, outDir: subsDir });
  }
  const tl = loadTimeline(timelineFile);
  const block = tl.blocks.find((b) => b.n === Number(n));
  if (!block) throw new Error(`no block ${n} in ${rel(timelineFile)}`);
  const scenes = block.scenes.map((k) => tl.scenes.find((s) => s.n === k));
  const outDir = path.join(VIDEO, 'out');
  mkdirSync(outDir, { recursive: true });

  // 1. scene renders
  const files = scenes.map((s) => path.join(outDir, s.file + '.mp4'));
  const missing = scenes.filter((s, i) => !existsSync(files[i]));
  if (missing.length && o.render) {
    const { renderScene } = await import('./render.mjs');
    for (const s of missing) await renderScene({ scene: path.join(VIDEO, 'scenes', s.file + '.html'), fps: tl.fps || 30, crf: 18, auditStep: 1 }, { prepared: true });
  } else if (missing.length) {
    throw new Error(`block ${n}: scene render(s) missing: ${missing.map((s) => 'out/' + s.file + '.mp4').join(', ')} (render them, or pass --render)`);
  }
  scenes.forEach((s, i) => {
    const d = probeDuration(files[i]);
    if (Math.abs(d - s.duration) > 1.5 / (tl.fps || 30)) console.warn(`[block ${n}] ${s.file}.mp4 is ${d.toFixed(2)} s, timeline says ${s.duration} s (captions follow the timeline)`);
  });

  // 2. concat (same codec settings -> stream copy)
  const list = path.join(outDir, `list_block_${n}.txt`);
  writeFileSync(list, files.map((f) => `file '${path.basename(f)}'`).join('\n') + '\n');
  const concat = path.join(outDir, `scenes_block_${n}.mp4`);
  ff(['-f', 'concat', '-safe', '0', '-i', rel(list), '-c', 'copy', rel(concat)], 'concat');
  const DUR = block.duration;

  // 3. PiP source: the member's take, or a placeholder
  let take = o.take ? path.resolve(o.take) : path.join(VIDEO, 'takes', `block_${n}.mp4`);
  if (!existsSync(take)) take = null;
  let offset = o.takeOffset;
  if (offset == null && existsSync(DEFAULT_OVERRIDES)) {
    const ov = JSON.parse(readFileSync(DEFAULT_OVERRIDES, 'utf8'));
    offset = ov.takes && ov.takes[String(n)] && ov.takes[String(n)].offset;
  }
  offset = offset || 0;
  const fonts = ensureFonts();
  const inputs = ['-i', rel(concat)];
  let camChain, audioMap;
  if (take) {
    inputs.push('-ss', String(offset), '-t', String(DUR), '-i', take);
    camChain = `[1:v]fps=${tl.fps || 30},scale=${PIP.w}:${PIP.h}:force_original_aspect_ratio=increase,crop=${PIP.w}:${PIP.h},setsar=1,setpts=PTS-STARTPTS[cam]`;
    if (hasAudio(take)) audioMap = ['-map', '1:a:0'];
    else { inputs.push('-f', 'lavfi', '-t', String(DUR), '-i', 'anullsrc=r=48000:cl=stereo'); audioMap = ['-map', '2:a:0']; }
  } else {
    inputs.push('-f', 'lavfi', '-t', String(DUR), '-i', `color=c=0xC9CFD5:s=${PIP.w}x${PIP.h}:r=${tl.fps || 30}`);
    inputs.push('-f', 'lavfi', '-t', String(DUR), '-i', 'anullsrc=r=48000:cl=stereo');
    camChain = `[1:v]drawtext=fontfile=${rel(fonts.regular)}:text=camera:fontsize=24:fontcolor=0x15202B@0.6:x=(w-tw)/2:y=(h-th)/2,setsar=1[cam]`;
    audioMap = ['-map', '2:a:0'];
  }
  const ass = path.join(subsDir, `block_${n}.ass`);
  const subs = o.subs === false ? '' : `,ass=${rel(ass)}:fontsdir=${rel(fonts.dir)}`;
  const graph = `${camChain};[0:v][cam]overlay=x=${PIP.x}:y=${PIP.y}:eof_action=pass${subs},format=yuv420p[v]`;
  const out = path.resolve(o.out || path.join(outDir, `block_${n}.mp4`));
  ff([...inputs, '-filter_complex', graph, '-map', '[v]', ...audioMap, '-t', String(DUR),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', String(o.crf || 18), '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', rel(out)], 'compose');
  const got = probeDuration(out);
  console.log(`block ${n}: ${scenes.length} scene(s), ${DUR} s -> ${path.relative(process.cwd(), out)} (${got.toFixed(2)} s; PiP ${take ? 'take ' + path.basename(take) + ' from ' + offset + ' s' : 'placeholder'}; captions ${o.subs === false ? 'off' : rel(ass)})`);
  return { out, duration: got, take, scenes: scenes.map((s) => s.file) };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const a = process.argv.slice(2), o = {};
  let n = null;
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--take') o.take = a[++i];
    else if (a[i] === '--take-offset') o.takeOffset = Number(a[++i]);
    else if (a[i] === '--render') o.render = true;
    else if (a[i] === '--no-subs') o.subs = false;
    else if (a[i] === '--out') o.out = a[++i];
    else if (a[i] === '--timeline') o.timeline = a[++i];
    else if (a[i] === '--crf') o.crf = Number(a[++i]);
    else n = a[i];
  }
  if (n == null) { console.error('usage: node compose_block.mjs <block 1-4> [--take file] [--take-offset s] [--render] [--no-subs] [--out file] [--timeline file]'); process.exit(2); }
  composeBlock(n, o).catch((e) => { console.error(e.message || e); process.exit(1); });
}
