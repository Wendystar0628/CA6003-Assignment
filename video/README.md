# Video scenes: kit v2, timeline, captions, renderer

Animated scenes for the CA6003 explainer video. The plan is `docs/video_plan.md` (scene table, titles, narration, layout). Each scene is an HTML/SVG page whose state is a pure function of time *t*. The renderer captures it frame by frame in the system Chrome and encodes it with ffmpeg. Each member block is then put together with that member's camera take in a fixed picture-in-picture (PiP) slot, with captions burned in.

## Folder structure

```text
video/
├── kit/
│   ├── tokens.css         colour roles, type, the one stage grid, chrome classes
│   └── kit.js             window.Kit: timeline, names, word clock, M1–M12, marks, chrome, page helpers, audit
├── timeline/
│   └── timeline.json      THE source for scene order, files, durations, speaker, section, narration
├── subtitles/
│   ├── build_subs.mjs     narration -> captions (.srt/.ass) + word clock (words.json)
│   ├── overrides.json     per-scene re-timing and per-block take offsets (edit after recording)
│   └── full.srt|ass, block_<n>.srt|ass, words.json, captions.json   (generated; committed)
├── scenes/
│   ├── _template.html     skeleton for a new scene (files starting with "_" are never rendered)
│   ├── _kit_v2_demo.html  kit test page (?variant=team | reflection | closing)
│   └── s01_hook_team.html … s26_close.html   (names from timeline.json)
├── data/                  numbers for the scenes (build_data.py) + team_names.json (generated)
├── render/
│   ├── render.mjs         one scene -> out/<file>.mp4 + out/<file>_last.png, audit every 1 s
│   ├── render_all.mjs     all scenes, or one block (--block n)
│   ├── snap.mjs           still frames at chosen times (--captions previews the captions)
│   ├── compose_block.mjs  block n: concat + PiP take + burned captions -> out/block_<n>.mp4
│   ├── compose_film.mjs   blocks 1–4 -> out/film.mp4 (+ film.srt), loudness -16 LUFS
│   ├── prepare.mjs        refreshes team_names.json and the captions before any render
│   ├── team.mjs           names from notebooks/final/team.json ("[Name]" placeholders)
│   ├── fonts.mjs          IBM Plex Sans TTFs for libass (from @fontsource, into out/fonts/)
│   ├── serve.mjs          local preview server
│   └── compose_example.md the ffmpeg commands behind compose_block, by hand
├── takes/                 camera takes block_<n>.mp4 (git-ignored)
└── out/                   renders (git keeps only *_last.png)
```

## Setup

```bash
cd video/render && npm install        # playwright-core (uses the installed Chrome) + @fontsource/ibm-plex-sans
```

You need Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe` (override with `CHROME_PATH` or `--chrome`), and `ffmpeg`/`ffprobe` with libass on PATH.

## Commands

```bash
node video/subtitles/build_subs.mjs                    # captions + word clock (runs automatically before renders)
node video/render/serve.mjs                            # preview: http://127.0.0.1:8130/scenes/<file>.html?play=1
node video/render/snap.mjs video/scenes/<file>.html 2 9.5 last --captions   # stills -> out/<file>_at_<t>.png
node video/render/render.mjs video/scenes/<file>.html  # -> out/<file>.mp4 + _last.png, audit every 1 s
node video/render/render_all.mjs --block 1 --jobs 3    # all scenes of block 1 (or every scene without --block)
node video/render/compose_block.mjs 1                  # -> out/block_1.mp4 (placeholder PiP if no take)
node video/render/compose_block.mjs 1 --take video/takes/block_1.mp4 --take-offset 2.4 --render
node video/render/compose_film.mjs                     # -> out/film.mp4 + out/film.srt
```

Preview URL parameters: `?play=1`, `?t=12.3`, `?static=1` (final frame), `?hud=0`, `?captions=1` (draws the captions in the caption zone; `?captions=outline` also outlines the zone). Keys: **Space** play/pause, **← / →** ±1 s (with **Shift**, ±1 frame), **N / P** next and previous cue step, **Home / End**. The HUD shows scene time and film time.

## The stage grid (one layout for the whole film)

Stage 1920×1080 px. `Kit.GRID` mirrors these values. The figure panel has its own coordinates, with origin (96, 224); `ctx.fig` is 1728×764.

| Region | Stage x | Stage y | Panel coordinates | Notes |
|---|---|---|---|---|
| Progress bar | 96–1824 | 40–74 | — | 7 sections, plain words, 24 px; indigo fill on the current section only |
| Main title | 96–1824 | 96–160 | — | Source Serif 4, 64 px, one line, the topic |
| Subtitle + credit | 96–1824 | 172–206 | — | 34 px subtitle; credit 28 px right-aligned ("Analysis by <Name>") |
| Figure panel | 96–1824 | 224–988 | 0–1728 × 0–764 | white paper |
| — main area | 96–1368 | 224–872 | x 0–1272, y 0–648 | text pages start at panel x 48 |
| — side area | 1392–1824 | 224–632 | x 1296–1728, y 0–408 | |
| Name tag | 1416–1800 | 656–740 | — | "Presented by <Name>" / role; whole film |
| PiP (camera) | 1416–1800 | 748–964 | — | 384×216, 1 px hairline outside |
| **Keep-out** | 1392–1824 | 632–988 | x ≥ 1296, y ≥ 408 | no content (PiP + name tag + 24 px) |
| **Caption zone** | 96–1368 | 872–988 | x 0–1272, y ≥ 648 | no content; captions are bottom-centred here |
| Footer | 96–1824 | 1000–1028 | — | legend row (left, 24 px), "Notebook section N.M" (right, 24 px) |

The audit fails any figure element, card text or legend chip that enters the keep-out or the caption zone.

## Names (no letter codes)

- Names come from `notebooks/final/team.json` (`members[].name`; an optional `video_name` overrides the name for the video). `render/team.mjs` writes `video/data/team_names.json`, which the scenes read. Every render refreshes it.
- A placeholder name (a single letter, empty, "Member A", "<A>", "TEAM TO FILL", or a bracketed name) is shown as **"[Name]"**. The letters A–D are never rendered.
- **Speakers are member indices 0–3** (0 governance, 1 quality, 2 labels, 3 modelling), never letters.
- Tokens in every chrome string and in the narration:
  - `<Name>` is this scene's speaker;
  - `<Name:i>` is member *i*;
  - `{role}` / `{role:i}` is the role line;
  - `{group}` is the group number ("[no.]" until it is filled in).
  
  For text you build yourself in a scene, use `Kit.name(i)` or `Kit.names('Analysis by <Name:2>')`.
- The audit fails if any rendered text is a bare A–D, contains "<A>", "C's", a standalone B, C or D, or "A" after a person word ("Member A", "by A", "presented by A"). The article "A" ("A basic model") is fine. To exempt a text, use `cfg.auditAllow: ['exact text' | /regex/]`.

## Timeline, captions and the word clock

- **`timeline/timeline.json`** is the only place for scene order, file, duration, speaker, section, `silentLead` (title card, block-start page or chapter card before the narration), `speechEnd` and the narration (with `<Name>` tokens and `{pause s}` reading pauses). Start times are derived. The kit reads it for the progress bar (a pure function of film time), the name tag and the default duration. Put the measured durations in after recording.
- **`subtitles/build_subs.mjs`** turns the narration into captions:
  - chunking: at most 2 lines of at most 42 characters, breaking at punctuation and phrase boundaries, never after "the", "of" and similar words, and never inside compounds such as "class weights";
  - timing: each word is timed in proportion to its estimated syllables across the speaking window `[silentLead + 0.3, (speechEnd | duration) − 0.5]`, with short pauses at punctuation and at `{pause}`;
  - cue length is 1.0–6.0 s, with a 0.1 s fade;
  - it writes `full.srt` (YouTube), `full.ass`, `block_<n>.srt|ass` (block-relative), `words.json` and `captions.json`, and prints reading-speed warnings (> 17 cps).
- **Caption style** (ASS, libass): IBM Plex Sans Medium, 34 px on screen (ASS `Fontsize 44`, because libass sizes fonts by ascent+descent), ink `#15202B`, 2 px white outline, no plate. Bottom-centred in the caption zone, with the last baseline at about y 974.
- **Re-timing** in `subtitles/overrides.json`, per scene: `speechStart`, `speechEnd`, `pauses: [{after: 'phrase', dur}]`, `shift`, or explicit `chunks: [{start, end, lines?}]`. Take offsets per block go in `takes: {"1": {"offset": 2.4}}`.
- **Cues follow the same clock.** A cue can be a narration phrase, and the kit resolves it from `words.json`:

  ```js
  cues: { axis: 0.6, bars: 'Our cohort', value: ['5,730', 0.1], second: { phrase: 'the 0.961', nth: 2, end: true } }
  ```

  `Kit.cueAt([scene,] 'phrase', {nth, end, offset})` returns the scene time. When the captions are re-timed, the animation moves with them. A missing phrase stops the scene with an error.

## Write a scene

1. Copy `scenes/_template.html` to `scenes/<file>.html`, using the file name from `timeline.json`.
2. Set `number`. The duration, speaker, section, progress fill and name tag come from the timeline.
3. Set `title` (the topic, about 5 words, no conclusion), `subtitle` (what the page shows), `pointer` (`'7.5'` becomes "Notebook section 7.5"; `'4.7–4.8'` and `'1.1, 3.2'` become "Notebook sections …"), and `credit` when you present someone else's work.
4. For scenes with several pages, use `phases: [{at, page, title, subtitle, credit, pointer}]`. Text that changes dissolves (M12); the subtitle follows 0.3 s later. A `page: 'blockstart'` phase hides the pointer.
5. Add `cards` for full-frame moments:
   - `{type: 'chapter', at: 0}`: 1.2 s, section label and scope from the timeline, "Presented by <Name>", progress bar visible;
   - `{type: 'title', at: 0, until: 1.5, title, subtitle, line, small}`: scene 01;
   - `{type: 'closing', at, title, subtitle, line, source}`: the seven-section route, all done.

   The PiP and the name tag stay on top of every card.
6. Use the page helpers inside the panel (HTML layer `ctx.figHTML`):
   - `Kit.teamCards(ctx)` → `update({opacity, focus, outline, others})` (use with `M3_focus`);
   - `Kit.blockStart(ctx, {sections: [{name, topics}]})` → `update({head, owns, rows})`;
   - `Kit.reflection(ctx, {line, handoff, figureHeight})` → `{g, box, update({line, figure, handoff})}`.
7. Set `progress`: `false` (scene 01), or `{at: s}` to fade the bar in (scene 02, after the agenda route morph). `Kit.progressSegments(ctx)` gives the bar's real segment boxes `[{n, label, x, y, w}]` to morph towards.
8. Use `legendMoment: {key, at}` on the first use of a colour. The scenes are reference 3, leak 8, systematic 12 and screen 16. The footer legend row shows the colours already introduced.
9. Build once in `setup(ctx)`. Set everything from `t` in `render(t, ctx)`: no timers, no CSS transitions, no randomness. Read numbers with `Kit.item(data, id)` (`.value` for geometry, `.display` for text) and `Kit.interval(data, id)`.
10. Check with `snap.mjs … --captions`, then render. Read `out/<file>_last.png` and fix every audit line.

## Audit (printed by render.mjs every second and on the last frame, by snap.mjs per still)

The audit flags:
- text smaller than 28 px; 24 px is allowed only in the progress bar, the legend row, the pointer, `.kit-t-foot` footnotes and the closing-card source line;
- overlapping text, figure text outside the panel, anything off stage;
- any content in the PiP keep-out (including the name tag) or in the caption zone;
- a title wider than 1728 px, or a subtitle running into the credit (48 px gap);
- "§" anywhere;
- internal codes: M0, M1, E-ALL, E-SCREEN, Pnn, B1–B6, S-B6a, Trap, S7_…, S10_… (the only exception is `notebook: M0 · M1 · S`);
- member letter codes;
- the structure indigo anywhere outside the progress bar;
- a name tag shrunk to fit a long name;
- a scene duration different from timeline.json.

## Rules every scene follows

- **One relation per scene,** with one visual verb: reveal, compare, split or shrink.
- **Numbers appear when spoken.** Keep to at most 1 main and 2 secondary numbers at a time.
- **Colour roles are fixed:**

  | Colour | Meaning | Shape |
  |---|---|---|
  | Indigo | current section on the progress bar only | — |
  | Red | harmed or leaked data | hatched + triangle |
  | Teal | systematic preparation | solid |
  | Blue | not-yet-diagnosed adults | hollow square |
  | Grey | reference: minimal preparation, all adults | solid circle |

  Feedback is ink only: a solid check, a dashed box with "?", or a cross.
- **Text** is at least 28 px; footnotes use `.kit-t-foot` (24 px). Use no internal codes and no "§"; the notebook pointer is the plain footer line.
- **Motion** uses only M1–M12. Leave at least 1.5 s of stillness between actions. Push-in (M9) is capped at 1.25× and stays out of the keep-out.
- **The final frame must read on its own.**

## Kit API (window.Kit)

| Group | Members |
|---|---|
| Timeline, names | `TIMELINE` (scenes with start/end, sections, members), `TEAM`, `SPEAKER`, `sceneInfo(n)`, `name(i)`, `names(str, speaker)`, `member(i)` → `{name, role, owns, presents}`, `PLACEHOLDER` |
| Word clock | `words(n)`, `cueAt([n,] phrase, {nth, end, offset})`, `resolveCues(obj)` |
| Grid, tokens | `GRID` (above), `C` (colour roles from CSS), `T` (timings), `LEGEND`, `FPS` |
| Maths | `ease.enter / morph / linear / count`, `cubicBezier`, `progress`, `tween`, `appear`, `clamp`, `lerp`, `mixColor`, `fmt(v, d, {sign, thousands})` (U+2212 minus), `fmtInterval` |
| Motion | `M1_axisDraw`, `M2_barGrow`, `M3_focus`, `M4_whiskerBand`, `M4_static`, `M5_funnel`, `M6_morph`, `M7_strike`, `M8_valueChange`, `M9_pushIn`, `M10_count`, `M11_arrow`, `M12_dissolve`, `M12_chapterCard` (unchanged from kit v1) |
| Marks | `scaleLinear`, `axis`, `bar`, `dotWhisker`, `sesoiBand`, `callout`, `strike`, `focusRing`, `arrow`, `feedback`, `warnTriangle`, `hatchPattern`, `swatchSVG`, `icon`, `radiusForArea`, `svg`, `h`, `text`, `op`, `textWidth`, `stageRect` |
| Pages | `teamCards`, `blockStart`, `reflection`, `progressSegments` |
| Data | `item`, `val`, `disp`, `interval`, `pick`, `loadJSON` |
| Scene | `createScene(cfg)` → `window.SCENE {duration, number, cues, seek(t), audit()}`, `window.SCENE_READY` |

`ctx` in `setup` and `render` contains: `fig` (panel SVG), `figHTML` (HTML layer), `W` 1728, `H` 764, `data`, `cues` (resolved seconds), `ui` (chrome elements, including `ui.progress.el` and `ui.camera`), `info` (timeline scene), `speaker`, `stage`.

**Removed in v2:**
- the right column and the A–D badges;
- the trap bar and its icons, and the "§" source tag (now the plain pointer);
- the lower-third;
- layouts F/S/X/R: `cfg.layout` is ignored and there is one layout;
- alpha renders (`--alpha`), and `_phases.js`-style layout switching.

`cfg.attribution` and `cfg.source` are no longer read; use `credit` and `pointer`.
