// Font files for ffmpeg (libass captions, drawtext placeholder label).
// The scenes load IBM Plex Sans from Google Fonts in Chrome; libass needs local font files, so this
// converts the @fontsource/ibm-plex-sans WOFF files (latin subset, npm dependency) to plain TTF in
// video/out/fonts/ (git-ignored). WOFF 1.0 is the sfnt tables, each zlib-compressed.
//   import { ensureFonts } from './fonts.mjs';  const { dir, regular, medium } = ensureFonts();
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { inflateSync } from 'node:zlib';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(here, 'node_modules', '@fontsource', 'ibm-plex-sans', 'files');
export const FONT_DIR = path.resolve(here, '..', 'out', 'fonts');
const WEIGHTS = { regular: 400, medium: 500, semibold: 600 };

/** WOFF 1.0 -> sfnt (TTF/OTF) buffer. */
export function woffToSfnt(buf) {
  if (buf.toString('ascii', 0, 4) !== 'wOFF') throw new Error('not a WOFF 1.0 file');
  const flavor = buf.readUInt32BE(4), n = buf.readUInt16BE(12);
  const tables = [];
  for (let i = 0; i < n; i++) {
    const o = 44 + i * 20;
    const tag = buf.readUInt32BE(o), off = buf.readUInt32BE(o + 4), comp = buf.readUInt32BE(o + 8);
    const orig = buf.readUInt32BE(o + 12), sum = buf.readUInt32BE(o + 16);
    const raw = buf.subarray(off, off + comp);
    tables.push({ tag, sum, data: comp < orig ? inflateSync(raw) : Buffer.from(raw) });
  }
  let pow = 1, log = 0;
  while (pow * 2 <= n) { pow *= 2; log++; }
  const head = Buffer.alloc(12 + 16 * n);
  head.writeUInt32BE(flavor, 0); head.writeUInt16BE(n, 4);
  head.writeUInt16BE(pow * 16, 6); head.writeUInt16BE(log, 8); head.writeUInt16BE(n * 16 - pow * 16, 10);
  let offset = head.length;
  const parts = [head];
  tables.forEach((t, i) => {
    const r = 12 + i * 16;
    head.writeUInt32BE(t.tag, r); head.writeUInt32BE(t.sum, r + 4);
    head.writeUInt32BE(offset, r + 8); head.writeUInt32BE(t.data.length, r + 12);
    const pad = (4 - (t.data.length % 4)) % 4;
    parts.push(t.data, Buffer.alloc(pad));
    offset += t.data.length + pad;
  });
  return Buffer.concat(parts);
}

/** Convert once; returns { dir, regular, medium, semibold } (absolute TTF paths). */
export function ensureFonts() {
  if (!existsSync(SRC)) throw new Error('Missing @fontsource/ibm-plex-sans: run "npm install" in video/render');
  mkdirSync(FONT_DIR, { recursive: true });
  const out = { dir: FONT_DIR };
  for (const [k, w] of Object.entries(WEIGHTS)) {
    const dst = path.join(FONT_DIR, `IBMPlexSans-${w}.ttf`);
    if (!existsSync(dst)) writeFileSync(dst, woffToSfnt(readFileSync(path.join(SRC, `ibm-plex-sans-latin-${w}-normal.woff`))));
    out[k] = dst;
  }
  return out;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) console.log(ensureFonts());
