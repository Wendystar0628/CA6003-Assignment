// Captions from the narration in video/timeline/timeline.json.
//   node video/subtitles/build_subs.mjs [--timeline path] [--overrides path] [--out-dir dir] [--quiet]
// Writes (default into video/subtitles/):
//   full.srt, full.ass              whole film (YouTube .srt; .ass for burning in)
//   block_<n>.srt, block_<n>.ass    per member block, times relative to the block start
//   words.json                      word clock per scene (scene-local seconds); the kit reads it for
//                                   Kit.cueAt() so animation cues and captions share one clock
//   captions.json                   caption chunks per scene (the kit's ?captions=1 preview)
// Until the recordings exist, each word gets a time proportional to its estimated syllables across
// the scene's speaking window [silentLead + leadIn, (speechEnd | duration) - leadOut], plus short
// pauses at punctuation and at {pause s} tokens. Re-time per scene in overrides.json (see README).
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadTeam, fillNames } from '../render/team.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const VIDEO = path.resolve(here, '..');
export const DEFAULT_TIMELINE = path.join(VIDEO, 'timeline', 'timeline.json');
export const DEFAULT_OVERRIDES = path.join(here, 'overrides.json');

/* ---------------- caption style: the subtitle zone (mirrors Kit.GRID.captions) ---------------- */
export const ZONE = { x: 96, y: 872, w: 1272, h: 116 };          // stage px; bottom-left strip of the panel
export const STYLE = {
  // IBM Plex Sans 500 at 34 px CSS: libass sizes fonts by ascent+descent (1.3 em for Plex), so 34 px -> 44
  font: 'IBM Plex Sans Medium', size: 44, cssPx: 34, lineHeight: 42, lineChars: 42, maxLines: 2, fadeMs: 100,
  minDur: 1.0, maxDur: 6.0, maxCps: 17,
  ink: '#15202B', outline: '#FFFFFF', outlineW: 2,
  marginL: ZONE.x, marginR: 1920 - (ZONE.x + ZONE.w), marginV: 1080 - (ZONE.y + ZONE.h) + 14,  // last baseline ~ y 974
};
const PAUSE = { comma: 0.15, clause: 0.3, sentence: 0.4, maxShare: 0.3 };

/* ---------------- syllable-based word weights ---------------- */
const DIGIT_SYL = [2, 1, 1, 1, 1, 1, 1, 2, 1, 1];
function intSyllables(s) {
  const d = s.replace(/[^0-9]/g, '');
  if (!d || /^0+$/.test(d)) return d ? 2 : 0;
  if (d.length === 4 && /^(19|20)/.test(d)) return 4;            // a year: "twenty twenty-one"
  const nz = d.split('').filter((c) => c !== '0').length;
  return nz * 2 + (d.length >= 4 ? 2 : 0) + (d.length >= 3 ? 1 : 0);
}
export function syllables(raw) {
  if (/^<Name(:\d)?>/.test(raw)) return 2;                      // names count 2, so real names do not move cues
  const w = raw.replace(/^[^\w<]+|[^\w%]+$/g, '').replace(/'s$/, '');
  if (!w) return 0;
  if (/^[0-9][0-9,]*(\.[0-9]+)?%?$/.test(w)) {
    const [i, f] = w.replace('%', '').split('.');
    let n = (f && /^0+$/.test(i) ? 0 : intSyllables(i));
    if (f) n += 1 + f.split('').reduce((a, c) => a + DIGIT_SYL[+c], 0);
    return n + (w.endsWith('%') ? 2 : 0);
  }
  return w.split(/[-–]/).reduce((sum, part) => {
    if (!part) return sum;
    if (/^[A-Z0-9]{2,4}$/.test(part) || /\d/.test(part)) return sum + part.length;   // AUC, CDC, L2, HbA1c
    const p = part.toLowerCase().replace(/[^a-z]/g, '');
    if (!p) return sum;
    let n = (p.match(/[aeiouy]+/g) || []).length;
    if (p.length > 2 && p.endsWith('e') && !p.endsWith('le') && n > 1) n--;
    return sum + Math.max(1, n);
  }, 0);
}
function punctPause(raw) {
  const t = raw.replace(/['"’”)\]]+$/, '');
  if (/[.?!]$/.test(t)) return PAUSE.sentence;
  if (/[;:]$/.test(t)) return PAUSE.clause;
  if (/,$/.test(t)) return PAUSE.comma;
  return 0;
}

/** Narration -> [{raw, extra pause}] ; {pause s} adds to the preceding word. */
export function tokenize(narration) {
  const words = [];
  for (const m of String(narration).matchAll(/\{pause\s+([\d.]+)\}|\S+/g)) {
    if (m[1] != null) { if (words.length) words[words.length - 1].extra += Number(m[1]); continue; }
    words.push({ raw: m[0], extra: 0 });
  }
  return words;
}

/** Word clock for one scene: [{raw, text, s, e}] (scene seconds). */
export function timeWords(scene, cfg, team, ov = {}) {
  const words = tokenize(scene.narration || '');
  const lead = scene.silentLead || 0;
  const start = ov.speechStart != null ? ov.speechStart : lead + cfg.leadIn;
  const end = ov.speechEnd != null ? ov.speechEnd : (scene.speechEnd != null ? scene.speechEnd : scene.duration) - cfg.leadOut;
  if (!(end > start)) throw new Error(`scene ${scene.n}: empty speaking window [${start}, ${end}]`);
  const W = end - start;
  // explicit pauses from overrides: {after: "phrase", dur}
  for (const p of ov.pauses || []) {
    const i = findPhrase(words.map((w) => w.raw), p.after, true);
    if (i < 0) throw new Error(`scene ${scene.n}: override pause phrase not found: "${p.after}"`);
    words[i].extra += p.dur;
  }
  const syl = words.map((w) => syllables(w.raw));
  // punctuation pauses between words; {pause s} also after the last word (reserves silence at the end)
  let pauses = words.map((w, i) => (i === words.length - 1 ? 0 : punctPause(w.raw)) + w.extra);
  const P = pauses.reduce((a, b) => a + b, 0);
  if (P > PAUSE.maxShare * W) pauses = pauses.map((p) => p * (PAUSE.maxShare * W) / P);
  const S = syl.reduce((a, b) => a + b, 0);
  const rate = (W - pauses.reduce((a, b) => a + b, 0)) / S;
  let t = start;
  return words.map((w, i) => {
    const s = t, e = s + syl[i] * rate;
    t = e + pauses[i];
    return { raw: w.raw, text: fillNames(w.raw, team, scene.speaker), s: +s.toFixed(3), e: +e.toFixed(3) };
  });
}

const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9<>:.%]+/g, '').replace(/\.(?!\d)|(?<!\d)\./g, '');   // same key as Kit.cueAt
/** Index of the first word of `phrase` in `raws` (or of its last word with last = true); -1 if absent. */
export function findPhrase(raws, phrase, last = false, nth = 1) {
  const W = raws.map((r) => norm(r)), P = String(phrase).split(/\s+/).map(norm).filter(Boolean);
  let seen = 0;
  for (let i = 0; i + P.length <= W.length; i++) {
    if (P.every((p, k) => W[i + k] === p)) {
      if (++seen === nth) return last ? i + P.length - 1 : i;
    }
  }
  return -1;
}

/* ---------------- chunking: <= 2 lines, <= 42 chars per line, natural breaks ---------------- */
const FUNCTION_WORDS = new Set(['a', 'an', 'the', 'of', 'to', 'and', 'or', 'in', 'on', 'for', 'with', 'by', 'at', 'from', 'as',
  'than', 'its', 'our', 'my', 'their', 'is', 'are', 'was', 'were', 'be', 'that', 'which', 'who', 'no', 'not', 'so', 'but', 'only', 'very', 'such',
  'all', 'each', 'every', 'both', 'two', 'one', 'we', 'i', 'they', 'would', 'will', 'can']);
// word pairs that should stay on one line (compounds and fixed phrases in the narration)
const KEEP = new Set(['class weights', 'two thirds', 'decision tree', 'data brief', 'data use', 'use agreement', 'spectrum bias',
  'far from', 'percentage points', 'logistic regression', "cohen's kappa", 'diagnostic threshold', 'times iqr', 'iqr rule',
  'what it', 'it reveals', 'same model', 'same folds', 'not yet', 'yet diagnosed', 'already diagnosed', 'research question',
  'question one', 'hold-out of', 'label by', 'inflation factors', 'variance inflation', 'would call', 'the result', 'result is', 'survey cycle', 'screening tool', 'no gain', 'no effect', 'thank you']);
const BREAK_BEFORE = new Set(['and', 'but', 'so', 'or', 'which', 'that', 'where', 'from', 'to', 'with', 'because', 'while', 'then', 'before', 'after', 'including', 'such', 'than', 'on', 'in', 'for']);
const UNITS = new Set(['percent', 'percentage', 'points', 'point', 'times']);
const bare = (t) => t.toLowerCase().replace(/[^a-z0-9]/g, '');

function breakCost(words, k) {      // cost of ending a line or chunk after word k
  if (k >= words.length - 1) return 0;
  const t = words[k].text.replace(/['"’”)\]]+$/, ''), nx = bare(words[k + 1].text);
  let c;
  if (/[.?!]$/.test(t)) c = 0;
  else if (/[;:]$/.test(t)) c = 0.5;
  else if (/,$/.test(t)) c = 1.5;
  else if (BREAK_BEFORE.has(nx)) c = 3;
  else c = 6;
  if (c >= 3 && FUNCTION_WORDS.has(bare(t))) c += 6;   // never end a line on 'the', 'of', ... (unless punctuated)
  if (UNITS.has(nx)) c += 8;
  if (/^\d/.test(bare(t)) && /^\d/.test(nx)) c += 2;
  if (nx === 'of') c += 3;
  if (c >= 3 && /^\d/.test(bare(t)) && /^[a-z]/.test(words[k + 1].text)) c += 3;   // keep "29 diabetic ..." together
  const pair = (words[k].text + ' ' + words[k + 1].text).toLowerCase().replace(/[^a-z0-9' -]/g, '');
  if (KEEP.has(pair)) c += 6;
  if (nx === 'and' && words[k + 2] && /[,;:.]$/.test(words[k + 2].text)) c += 4;   // "code / and text;"
  return c;
}
const join = (ws) => ws.map((w) => w.text).join(' ');

function bestLines(words, i, j, max) {
  const all = join(words.slice(i, j + 1));
  if (all.length <= max) return { lines: [all], cost: 0 };
  let best = null;
  for (let k = i; k < j; k++) {
    const a = join(words.slice(i, k + 1)), b = join(words.slice(k + 1, j + 1));
    if (a.length > max || b.length > max) continue;
    const cost = breakCost(words, k) + Math.abs(a.length - b.length) / 12 + (a.length > b.length + 12 ? 0.5 : 0)
      + (Math.min(a.length, b.length) < 12 && breakCost(words, k) >= 3 ? 4 : 0);
    if (!best || cost < best.cost) best = { lines: [a, b], cost };
  }
  return best;
}

export function chunkWords(words, max = STYLE.lineChars) {
  const n = words.length, best = Array(n + 1).fill(Infinity), from = Array(n + 1).fill(-1), info = Array(n + 1);
  best[0] = 0;
  for (let j = 1; j <= n; j++) {
    for (let i = j - 1; i >= 0; i--) {
      const L = bestLines(words, i, j - 1, max);
      if (!L) { if (join(words.slice(i, j)).length > 2 * max + 1) break; continue; }
      const text = L.lines.join(' '), dur = words[j - 1].e - words[i].s;
      const endCost = breakCost(words, j - 1), endsSentence = /[.?!]['"’”]?$/.test(words[j - 1].text);
      let c = 1.5 + 1.5 * endCost + (/[,;:.?!]['"’”]?$/.test(words[j - 1].text) || j === n ? 0 : 1) + L.cost;
      if (text.length < 16 && j < n) c += endsSentence ? 1.5 : 4;
      if (dur < 1.0) c += 4;
      if (dur > STYLE.maxDur - 0.3) c += (dur - STYLE.maxDur + 0.3) * 3;
      for (let k = i; k < j - 1; k++) if (/[.?!]['"’”]?$/.test(words[k].text)) c += 4;   // sentence end inside a chunk
      if (best[i] + c < best[j]) { best[j] = best[i] + c; from[j] = i; info[j] = L.lines; }
    }
  }
  const chunks = [];
  for (let j = n; j > 0; j = from[j]) {
    if (from[j] < 0) throw new Error('cannot fit caption: ' + join(words.slice(0, j)));
    chunks.unshift({ i: from[j], j: j - 1, lines: info[j] });
  }
  return chunks;
}

/** Caption chunks with times for one scene. */
export function sceneCaptions(scene, words, ov = {}) {
  const chunks = chunkWords(words).map((c) => ({ lines: c.lines, start: words[c.i].s, end: words[c.j].e + 0.15 }));
  chunks.forEach((c, k) => {
    const next = chunks[k + 1];
    if (next) {
      if (c.end - c.start < STYLE.minDur) c.end = Math.min(next.start, c.start + STYLE.minDur);
      if (next.start - c.end < 0.3) c.end = next.start;               // no flicker between captions
      c.end = Math.min(c.end, next.start);
    } else c.end = Math.min(scene.duration, Math.max(c.end + 0.25, c.start + STYLE.minDur));
  });
  if (ov.chunks) {
    if (ov.chunks.length !== chunks.length) throw new Error(`scene ${scene.n}: overrides.chunks has ${ov.chunks.length} entries, captions have ${chunks.length}`);
    ov.chunks.forEach((o, k) => { if (o.start != null) chunks[k].start = o.start; if (o.end != null) chunks[k].end = o.end; if (o.lines) chunks[k].lines = o.lines; });
  }
  const shift = ov.shift || 0;
  return chunks.map((c) => ({ lines: c.lines, start: +(c.start + shift).toFixed(3), end: +(c.end + shift).toFixed(3) }));
}

/* ---------------- whole timeline ---------------- */
export function loadTimeline(file = DEFAULT_TIMELINE) {
  const tl = JSON.parse(readFileSync(file, 'utf8'));
  let t = 0;
  tl.scenes.forEach((s) => { s.start = +t.toFixed(3); t += s.duration; });
  tl.total = +t.toFixed(3);
  for (const b of tl.blocks || []) {
    const sc = b.scenes.map((n) => tl.scenes.find((s) => s.n === n));
    if (sc.some((s) => !s)) throw new Error(`block ${b.n} lists a scene that is not in the timeline`);
    b.start = sc[0].start; b.duration = +sc.reduce((a, s) => a + s.duration, 0).toFixed(3);
  }
  return tl;
}

export function buildAll({ timeline = DEFAULT_TIMELINE, overrides = DEFAULT_OVERRIDES, team = loadTeam() } = {}) {
  const tl = loadTimeline(timeline);
  const ovAll = existsSync(overrides) ? JSON.parse(readFileSync(overrides, 'utf8')) : {};
  const cfg = Object.assign({ leadIn: 0.3, leadOut: 0.5 }, tl.subtitles || {});
  const scenes = {};
  for (const s of tl.scenes) {
    const ov = (ovAll.scenes || {})[String(s.n)] || {};
    const words = timeWords(s, cfg, team, ov);
    const captions = sceneCaptions(s, words, ov);
    scenes[s.n] = { n: s.n, file: s.file, block: s.block, start: s.start, duration: s.duration, words, captions };
  }
  return { tl, scenes };
}

/* ---------------- writers ---------------- */
const pad = (n, w = 2) => String(n).padStart(w, '0');
function srtTime(t) {
  const ms = Math.round(t * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, s = Math.floor(ms / 1000) % 60;
  return `${pad(h)}:${pad(m)}:${pad(s)},${pad(ms % 1000, 3)}`;
}
function assTime(t) {
  const cs = Math.round(t * 100), h = Math.floor(cs / 360000), m = Math.floor(cs / 6000) % 60, s = Math.floor(cs / 100) % 60;
  return `${h}:${pad(m)}:${pad(s)}.${pad(cs % 100)}`;
}
const assColor = (hex) => { const h = hex.replace('#', ''); return `&H00${h.slice(4, 6)}${h.slice(2, 4)}${h.slice(0, 2)}`.toUpperCase(); };
const assEscape = (s) => s.replace(/\\/g, '\\\\').replace(/\{/g, '\\{').replace(/\}/g, '\\}');

function cuesFor(scenes, list, origin) {
  return list.flatMap((n) => scenes[n].captions.map((c) => ({ start: scenes[n].start + c.start - origin, end: scenes[n].start + c.end - origin, lines: c.lines })));
}
export function toSRT(cues) {
  return cues.map((c, i) => `${i + 1}\n${srtTime(c.start)} --> ${srtTime(c.end)}\n${c.lines.join('\n')}\n`).join('\n');
}
export function toASS(cues, title = 'CA6003 captions') {
  const S = STYLE;
  const head = `[Script Info]
; Generated by video/subtitles/build_subs.mjs. Subtitle zone x ${ZONE.x}-${ZONE.x + ZONE.w}, y ${ZONE.y}-${ZONE.y + ZONE.h} (Kit.GRID.captions).
Title: ${title}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,${S.font},${S.size},${assColor(S.ink)},${assColor(S.ink)},${assColor(S.outline)},&H00000000,0,0,0,0,100,100,0,0,1,${S.outlineW},0,2,${S.marginL},${S.marginR},${S.marginV},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;
  return head + cues.map((c) => `Dialogue: 0,${assTime(c.start)},${assTime(c.end)},Caption,,0,0,0,,{\\fad(${S.fadeMs},${S.fadeMs})}${c.lines.map(assEscape).join('\\N')}`).join('\n') + '\n';
}

export function writeAll(opts = {}) {
  const outDir = opts.outDir || here;
  mkdirSync(outDir, { recursive: true });
  const { tl, scenes } = buildAll(opts);
  const all = tl.scenes.map((s) => s.n);
  const written = [];
  const put = (name, text) => { writeFileSync(path.join(outDir, name), text); written.push(name); };
  const full = cuesFor(scenes, all, 0);
  put('full.srt', toSRT(full));
  put('full.ass', toASS(full, 'CA6003 full film'));
  for (const b of tl.blocks || []) {
    const cues = cuesFor(scenes, b.scenes, b.start);
    put(`block_${b.n}.srt`, toSRT(cues));
    put(`block_${b.n}.ass`, toASS(cues, `CA6003 block ${b.n}`));
  }
  const words = { _meta: { written_by: 'video/subtitles/build_subs.mjs', times: 'scene-local seconds', raw: 'narration token (with <Name> tokens)', text: 'as captioned' }, scenes: {} };
  const caps = { _meta: { written_by: 'video/subtitles/build_subs.mjs', zone: ZONE, style: STYLE }, scenes: {} };
  for (const n of all) {
    const s = scenes[n];
    words.scenes[n] = { file: s.file, start: s.start, duration: s.duration, words: s.words.map((w) => ({ w: w.raw, t: w.text, s: w.s, e: w.e })) };
    caps.scenes[n] = s.captions;
  }
  put('words.json', JSON.stringify(words) + '\n');
  put('captions.json', JSON.stringify(caps, null, 1) + '\n');
  // sanity: line limits
  const long = full.flatMap((c) => c.lines).filter((l) => l.length > STYLE.lineChars);
  if (long.length) throw new Error('caption lines over ' + STYLE.lineChars + ' chars: ' + long.join(' | '));
  const warnings = [];
  for (const n of all) for (const c of scenes[n].captions) {
    const d = c.end - c.start, chars = c.lines.join(' ').length;
    if (chars / d > STYLE.maxCps) warnings.push(`scene ${n} ${c.start.toFixed(1)} s: ${(chars / d).toFixed(1)} chars/s > ${STYLE.maxCps}: "${c.lines.join(' ')}"`);
    if (d > STYLE.maxDur + 0.05) warnings.push(`scene ${n} ${c.start.toFixed(1)} s: ${d.toFixed(1)} s > ${STYLE.maxDur} s`);
  }
  return { tl, scenes, written, outDir, cues: full.length, warnings };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const a = process.argv.slice(2), opt = {};
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--timeline') opt.timeline = path.resolve(a[++i]);
    else if (a[i] === '--overrides') opt.overrides = path.resolve(a[++i]);
    else if (a[i] === '--out-dir') opt.outDir = path.resolve(a[++i]);
    else if (a[i] === '--quiet') opt.quiet = true;
  }
  const r = writeAll(opt);
  if (!opt.quiet) {
    if (r.warnings.length) {
      const show = process.argv.includes('--all-warnings') ? r.warnings : r.warnings.slice(0, 5);
      console.log([`${r.warnings.length} caption warning(s) (reading speed is set by the narration pace; re-time in overrides.json):`, ...show].join('\n  ')
        + (show.length < r.warnings.length ? `\n  ... (--all-warnings lists all)` : ''));
    }
    console.log(`${r.cues} captions, ${Object.keys(r.scenes).length} scenes, total ${r.tl.total} s -> ${path.relative(process.cwd(), r.outDir)}: ${r.written.join(', ')}`);
    for (const s of Object.values(r.scenes)) {
      const w = s.words.length, span = s.words.length ? s.words[s.words.length - 1].e - s.words[0].s : 0;
      console.log(`  scene ${String(s.n).padStart(2)}  ${String(w).padStart(3)} words  ${span.toFixed(1).padStart(5)} s speech  ${(w / span * 60 || 0).toFixed(0).padStart(3)} wpm  ${s.captions.length} captions`);
    }
  }
}
