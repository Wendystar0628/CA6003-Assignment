# Video scenes: kit, scenes, renderer

Animated chart scenes for the CA6003 explainer video. The specification is `docs/video_plan.md`: §4 has the storyboard and narration per scene, §6 the visual system, §7 the signature visuals, and §8 the pipeline. Each scene is an HTML/SVG page whose state is a pure function of time *t*. The renderer captures it frame by frame in the system Chrome and encodes it with ffmpeg.

## Folder structure

```text
video/
├── kit/
│   ├── tokens.css       colour roles, type, grid, depth layers, fixed stage regions (§6)
│   └── kit.js           timeline, easing, M1–M12 helpers, SVG marks, chrome, audit (window.Kit)
├── scenes/
│   ├── _template.html   skeleton for a new scene (files starting with "_" are never rendered)
│   └── s18_leak_gate.html   reference scene: scene 18, visual 4 "Leak gate"
├── data/                numbers for the scenes, written by data/build_data.py (never typed into a scene)
├── render/
│   ├── package.json     playwright-core only; uses the installed Chrome, downloads no browser
│   ├── render.mjs       one scene -> out/<name>.mp4 + out/<name>_last.png
│   ├── render_all.mjs   every scene in scenes/
│   ├── snap.mjs         still frames at chosen times, for checking a build step
│   ├── serve.mjs        local preview server
│   └── compose_example.md   ffmpeg: camera clip into the camera slot, concatenation
└── out/                 renders (git keeps only *_last.png)
```

## Setup

```bash
cd video/render && npm install        # installs playwright-core only
```

The renderer needs Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe` (override with `CHROME_PATH` or `--chrome`), and `ffmpeg` on PATH.

## Preview a scene

Scenes read `../data/*.json` with `fetch()`, which Chrome blocks on `file://` pages. Serve the folder instead:

```bash
node video/render/serve.mjs            # http://127.0.0.1:8130/scenes/s18_leak_gate.html
# or: npx http-server video -p 8130
```

| URL parameter | Effect |
|---|---|
| `?play=1` | autoplay from 0 (or from `?t`) |
| `?t=12.3` | seek to 12.3 s and hold |
| `?static=1` | final frame (reduced motion); also the default when the OS asks for reduced motion |
| `?hud=0` | hide the small time readout |

Keys: **Space** plays and pauses. **← / →** step 1 s (with **Shift**, 1 frame). **N / PageDown** plays through the next build step and holds; this is the step mode for the live fallback in §8.3. **P / PageUp** jumps back one step. **Home / End**.

The stage is 1920×1080 and scales down to fit the window. Fonts come from Google Fonts, with fallback stacks if you are offline.

## Render

```bash
node video/render/render.mjs video/scenes/s18_leak_gate.html            # -> video/out/leak_gate.mp4 + s18_leak_gate_last.png
node video/render/render.mjs video/scenes/s18_leak_gate.html --fps 30 --out video/out/leak_gate --crf 18
node video/render/render.mjs video/scenes/s18_leak_gate.html --from 18 --to 23   # partial range
node video/render/render.mjs video/scenes/<scene>.html --alpha       # transparent camera slot -> <name>_alpha.mov
node video/render/render_all.mjs --jobs 3                            # all scenes, seconds per scene
node video/render/snap.mjs video/scenes/s18_leak_gate.html 5.6 16 20.1   # stills -> video/out/<name>_at_<t>.png
```

The renderer opens the page at 1920×1080 with deviceScaleFactor 1 and waits for fonts and data. For each frame *i* it calls `SCENE.seek(i / fps)`, captures a PNG, and streams the PNGs into ffmpeg: H.264, yuv420p, CRF 18, BT.709 tags. The final frame is also saved as `<name>_last.png`. After rendering, it prints the kit **audit** of the last frame: text under 28 px, overlapping text, text outside the panel, anything over the camera slot, and a title running into the trap bar. Fix every audit line before you commit.

A 34 s scene takes about 33 s to render, close to real time.

## Write a new scene

1. Copy `scenes/_template.html` to `scenes/<name>.html`.
2. Fill in the config from §3 and §4: `number`, `duration`, `layout`, `speaker`, `title` (no more than 6 words), `attribution` when presenting someone else's work, `trap`, `source`, `chapterCard` and `lowerThird` only where §4 calls for them, and `legendMoment` only on the first use of a colour (§6.2 table).
3. Set `data:` to the scene's file in `data/`. Read numbers with `Kit.item(data, id)`: use `.value` for geometry and `.display` for text. Use `Kit.interval(data, id)` for est / lo / hi and the `[lo, hi]` string. Never type a number into a scene.
4. In `setup(ctx)`, build every element once in `ctx.fig` (the paper panel SVG, `ctx.W × ctx.H`). Put the elements you will update on `ctx.S`.
5. In `render(t, ctx)`, set every element from `t` alone, using the M-helpers and the `CUES` table. Every element gets its state on every call. Do not use timers, CSS transitions or randomness.
6. Put the cue times in `CUES`, one per narration phrase. Replace the estimates with the times marked on the recorded take (§8.3 step 5).
7. Check the scene with `snap.mjs` at each step, then render it, read `out/<name>_last.png`, and fix every audit line.

```js
Kit.createScene({
  number: 21, name: 'prep_band', duration: 33, layout: 'R', speaker: 'D',
  title: 'Does preparation pay?', trap: 'gain', source: '§10.3 · S10_scoreboard',
  chapterCard: { at: 0, title: 'Does preparation pay?', item: 'Trap 3 · §10' },
  data: '../data/prep_band.json', cues: { axis: 1.6, point: 6.0 },
  setup(ctx) { /* build once */ },
  render(t, ctx) { /* pure function of t */ },
});
```

## Rules from §6 every scene must follow

- **One relation per scene.** Write down what "the viewer can point at ___". Anything unrelated stays off screen. Use one visual verb per scene: reveal, compare, split or shrink.
- **Numbers appear only when spoken,** never before the word. Screen-only numbers (intervals, secondary notes) come in narration pauses. Show at most 1 main and 2 secondary numbers at a time. The main number is ≥ 96 px (kit: 136 px).
- **Colour roles are fixed.** Each colour has one meaning:

  | Colour | Meaning | Paired shape |
  |---|---|---|
  | Indigo (structure) | current position only, never inside a chart | — |
  | Red | harmed or leaked data | always hatched, with the triangle |
  | Teal | Systematic (S) only | solid |
  | Blue | Screening group | hollow square |
  | Grey | reference baseline: Minimal (M1), All adults | solid circle |

  Feedback uses ink shapes only: a solid check, a dashed box with "?", or a cross. Anything without a semantic meaning is ink. In one chart, colour encodes one variable.
- **Text is ≥ 28 px.** Only the source tag and the legend row use 24 px. Each screen has 1 title (≤ 6 words) and at most 3 annotations (≤ 5 words each). Names follow the naming table (§6.6).
- **Draw intervals.** Every effect size gets a whisker, beside the neutral ±0.01 SESOI band where relevant. If the AUC axis does not start at 0, label it "axis starts at 0.5" (`Kit.axis(..., { truncated })`).
- **No gratuitous motion.** Use only M1–M12, emphasise in place, and move one thing at a time. Leave ≥ 1.5 s of stillness between actions. Motion fills ≤ 40 % of the scene. No fly-ins, bounces, typewriter effects or stamps. M9 push-in is capped at 1.25× and used only in scenes 8 and 17.
- **The final frame must read on its own.** It is the thumbnail and the frame the viewer sees when the narration moves on. Check `_last.png`.

## Kit API (window.Kit)

**Timeline and maths**

- `createScene(cfg)` registers `window.SCENE = {duration, layout, number, cues, seek(t), audit()}` and `window.SCENE_READY`.
- `ease.enter`, `ease.morph`, `ease.linear`, `ease.count`
- `cubicBezier(x1, y1, x2, y2)`
- `progress(t, start, dur, ease)`
- `tween(t, start, dur, from, to, ease = morph)`
- `appear(t, at, dur = 0.3)`
- `clamp`, `lerp`, `mixColor(a, b, p)`
- `fmt(v, decimals, {sign, thousands})`: uses the U+2212 minus sign.
- `fmtInterval(lo, hi, d)`

**Motion helpers.** Each is a pure function of *t* and uses the §6.4 timings by default (`Kit.T`).

| Helper | Returns |
|---|---|
| `M1_axisDraw(t, start, {nTicks})` | `{line, tick(i), labels, done}` |
| `M2_barGrow(t, start, {index})` | grow 0..1 |
| `M3_focus(t, start, end)` | `{outline, others}` |
| `M4_whiskerBand(t, start)` | `{dot, whisker, band, pulse}` |
| `M4_static(t, at)` | same shape, for every scene except 21 |
| `M5_funnel(t, start, levels)` | `[{narrow, ghost}]` |
| `M6_morph(t, start)` | p |
| `M7_strike(t, start)` | `{line, label}` |
| `M8_valueChange(t, start, from, to)` | `{length, value, fill, p}` |
| `M9_pushIn(t, start, {scale ≤ 1.25, hold ≥ 2})` | `{scale, transform(ox, oy)}` |
| `M10_count(t, start, from, to)` | value |
| `M11_arrow(t, start)` | `{arrow, label}` |
| `M12_dissolve(t, start)` | p |
| `M12_chapterCard(t, start)` | visible |

**SVG and marks.** Each mark returns an object with `update(state)`.

- `scaleLinear(domain, range)`
- `axis(parent, scale, {orient, at, ticks, format, grid, title, truncated})`
- `bar(parent, {scale, base, x|y, width, orient, styles: ['leak', 'reference']})`: `update({value, grow, mix})`
- `dotWhisker(parent, scale, {at, est, lo, hi, role, shape, pulseEnd})`
- `sesoiBand(parent, scale, {lo, hi, from, to})`
- `callout(parent, {x, y, size: 'main'|'second', interval, label, layout})`: `update({text|value, number, interval, label, fill})`
- `strike(parent, textEl, {color: 'ink'|'leak'})`
- `focusRing(parent, box)`
- `arrow(parent, {x1, y1, x2, y2, label})`
- `feedback(parent, {kind: 'supported'|'inconclusive'|'refuted', x, y, size, label})`
- `warnTriangle`, `hatchPattern`, `icon`, `swatchSVG`, `radiusForArea`
- `svg`, `text`, `op`, `textWidth`

**Data**

- `item(data, id)`, `val`, `disp`
- `interval(data, id)`: returns `{est, lo, hi, display, bracket}`
- `pick(data, ...paths)`

**Chrome.** The kit builds these from the config: the title band (with an M12 dissolve between titles), the trap bar, the attribution tag, the paper panel, the camera slot, the badges, the lower-third, the bottom bar (source tag and legend row), the legend chip, the chapter card, and the codebook grid motif.

If the attribution tag does not fit beside the title, it moves under the camera in layout R.
