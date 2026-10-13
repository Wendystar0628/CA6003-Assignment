/* =====================================================================
   CA6003 explainer video · scene kit v2 (dependency-free)
   Spec: docs/video_redesign.md §2 (single layout, PiP, keep-out, footer), §3 (progress bar,
   titles, page types), §6.1 (kit); DECISIONS_v2 (captions, names, no letter codes).

   Contract
   --------
   A scene calls Kit.createScene({...}). The kit registers
       window.SCENE = { duration, number, cues, seek(t), audit(), ready }
       window.SCENE_READY  (Promise -> {duration, number, fontsOK})
   seek(t) renders the exact state at time t as a pure function of t: no CSS
   transitions, no timers, no randomness. Live preview drives seek() from
   requestAnimationFrame; the renderer calls seek(i / fps) for every frame.

   Shared sources (loaded before setup):
       ../timeline/timeline.json   scene order, durations, speaker, section (progress bar, name tag)
       ../data/team_names.json     member names from notebooks/final/team.json ("[Name]" placeholders)
       ../subtitles/words.json     word clock of the narration (Kit.cueAt), from build_subs.mjs

   URL parameters:  ?t=12.3   seek to a time and hold
                    ?play=1   autoplay (from ?t or 0)
                    ?static=1 render the final frame (reduced motion)
                    ?render=1 renderer mode (no HUD, no keyboard, no autoplay)
                    ?hud=0    hide the preview HUD
                    ?captions=1  preview the captions in the caption zone (never in renders)
   Preview keys:    Space play/pause · ←/→ ±1 s (Shift: ±1 frame)
                    N / PageDown next cue step · P / PageUp previous · Home / End
   ===================================================================== */
(function (global) {
  'use strict';

  const SVGNS = 'http://www.w3.org/2000/svg';
  const FPS = 30;

  /* ------------------------------------------------------------------ *
   * 1. Geometry (mirrors tokens.css) and constants
   * ------------------------------------------------------------------ */
  /** One layout for the whole film. Stage px unless noted; `fig.*` are panel coordinates. */
  const GRID = {
    W: 1920, H: 1080, marginX: 96, gutter: 24,
    progress: { x: 96, y: 40, w: 1728, h: 34, pad: 32, gap: 16, ruleY: 30, ruleH: 4 },
    title: { x: 96, y: 96, w: 1728, h: 64 },
    subtitle: { x: 96, y: 172, w: 1728, h: 34 },
    panel: { x: 96, y: 224, w: 1728, h: 764 },
    nametag: { x: 1416, y: 656, w: 384, h: 84 },
    camera: { x: 1416, y: 748, w: 384, h: 216 },        // PiP; 1 px hairline drawn outside
    keepOut: { x: 1392, y: 632, w: 432, h: 356 },       // PiP + name tag + 24 px: no content
    captions: { x: 96, y: 872, w: 1272, h: 116 },       // burned-in captions: no content
    bottom: { x: 96, y: 1000, w: 1728, h: 28 },
    fig: {                                              // panel coordinates (origin 96, 224)
      W: 1728, H: 764,
      main: { x: 0, y: 0, w: 1272, h: 648 },            // full-height main area, above the caption zone
      side: { x: 1296, y: 0, w: 432, h: 408 },          // upper side area beside the keep-out
      keepOut: { x: 1296, y: 408, w: 432, h: 356 },
      captions: { x: 0, y: 648, w: 1272, h: 116 },
      left: 48,                                         // text pages start at panel x 48
    },
  };

  /** Colour roles. Read from CSS so tokens.css stays the single source. */
  const C = {};
  ['structure', 'leak', 'leak-tint', 'systematic', 'systematic-tint', 'screen', 'screen-tint',
    'reference', 'ink', 'line', 'band', 'stage', 'paper', 'paper-edge', 'pip-empty'].forEach((k) => {
    Object.defineProperty(C, k.replace(/-(\w)/g, (_, c) => c.toUpperCase()), {
      enumerable: true,
      get: () => getComputedStyle(document.documentElement).getPropertyValue('--' + k).trim(),
    });
  });

  /** Legend: first scene of each semantic colour, chip text (2-3 s), footer row text. */
  const LEGEND = [
    { key: 'reference', first: 3, chip: 'grey = reference: all adults', row: 'reference baseline' },
    { key: 'leak', first: 8, chip: 'red = harmed or leaked data', row: 'harmed or leaked data' },
    { key: 'systematic', first: 12, chip: 'teal = systematic preparation', row: 'Systematic preparation' },
    { key: 'screen', first: 16, chip: 'blue = not-yet-diagnosed adults', row: 'Not-yet-diagnosed adults' },
  ];

  /** Motion timings. Every M-helper uses these as defaults. */
  const T = {
    M1: { dur: 0.6, tickStagger: 0.03, tickDur: 0.2, labelDur: 0.3 },
    M2: { dur: 0.7, stagger: 0.12 },
    M3: { dur: 0.4, dim: 0.25 },
    M4: { dot: 0.3, whisker: 0.5, band: 0.6, pulse: 0.4 },
    M5: { step: 0.5, pause: 0.4, ghost: 0.2 },
    M6: { dur: 0.9 },
    M7: { dur: 0.25, labelDur: 0.3, maxPerScene: 3 },
    M8: { dur: 0.8 },
    M9: { push: 0.9, hold: 2.0, pull: 0.6, maxScale: 1.25 },
    M10: { dur: 0.8 },
    M11: { arrow: 0.4, label: 0.3 },
    M12: { dissolve: 0.4, card: 1.2 },
    appear: 0.3,          // label / interval fade
    gap: 1.5,             // minimum still time between two actions
    legendHold: 2.5,      // legend chip visible 2-3 s
    legendCollapse: 0.4,  // then folds into the footer legend row
    subtitleDelay: 0.3,   // a new subtitle fades in 0.3 s after its title
    titleCard: 2.0,
  };

  /** Shared sources, filled by createScene before setup(). */
  const STATE = { timeline: null, team: null, words: null, captions: null, scene: null, speaker: 0 };

  /* ------------------------------------------------------------------ *
   * 2. Easing, tween, small maths
   * ------------------------------------------------------------------ */
  /** cubicBezier(x1, y1, x2, y2) -> ease(p). Newton + bisection, CSS-equivalent. */
  function cubicBezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (u) => ((ax * u + bx) * u + cx) * u;
    const sy = (u) => ((ay * u + by) * u + cy) * u;
    const dx = (u) => (3 * ax * u + 2 * bx) * u + cx;
    return function (p) {
      if (p <= 0) return 0;
      if (p >= 1) return 1;
      let u = p;
      for (let i = 0; i < 8; i++) {
        const e = sx(u) - p;
        if (Math.abs(e) < 1e-7) return sy(u);
        const d = dx(u);
        if (Math.abs(d) < 1e-6) break;
        u -= e / d;
      }
      let lo = 0, hi = 1; u = p;
      for (let i = 0; i < 40; i++) {
        const v = sx(u);
        if (Math.abs(v - p) < 1e-7) break;
        if (v < p) lo = u; else hi = u;
        u = (lo + hi) / 2;
      }
      return sy(u);
    };
  }

  /** Easing functions (§6.4). */
  const ease = {
    /** Entrances: cubic-bezier(.2, 0, 0, 1). */
    enter: cubicBezier(0.2, 0, 0, 1),
    /** Morphs, value changes, push-ins: cubic-bezier(.4, 0, .2, 1). */
    morph: cubicBezier(0.4, 0, 0.2, 1),
    /** Data-driven continuous quantities. */
    linear: (p) => Math.max(0, Math.min(1, p)),
    /** M10 count: linear start, decelerates at the end (C1-continuous at p = 0.7). */
    count: (p) => {
      p = Math.max(0, Math.min(1, p));
      const s = 1 / 0.85;
      if (p < 0.7) return s * p;
      const q = (p - 0.7) / 0.3;
      return 0.7 * s + 0.15 * s * (1 - (1 - q) * (1 - q));
    },
  };

  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;

  /** Eased progress 0..1 of a move that starts at `start` and lasts `dur`. */
  function progress(t, start, dur, fn = ease.linear) {
    if (dur <= 0) return t >= start ? 1 : 0;
    return fn(clamp((t - start) / dur));
  }

  /** tween(t, start, dur, from, to, ease) -> value at time t. Default ease: morph. */
  function tween(t, start, dur, from, to, fn = ease.morph) {
    return lerp(from, to, progress(t, start, dur, fn));
  }

  /** Fade used for labels, intervals and static appearances (0.3 s, linear). */
  function appear(t, at, dur = T.appear) { return progress(t, at, dur, ease.linear); }

  function hexToRgb(h) {
    h = h.replace('#', '');
    if (h.length === 3) h = h.split('').map((c) => c + c).join('');
    const n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  /** Mix two hex colours (p = 0 -> a, 1 -> b). */
  function mixColor(a, b, p) {
    const A = hexToRgb(a), B = hexToRgb(b);
    const c = A.map((v, i) => Math.round(lerp(v, B[i], clamp(p))));
    return '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
  }

  /** Number format: true minus sign (U+2212), fixed decimals, optional plus. */
  function fmt(v, decimals = 3, opts = {}) {
    const s = Math.abs(v).toFixed(decimals);
    const zero = Number(s) === 0;
    const sign = v < 0 && !zero ? '−' : (opts.sign && v > 0 && !zero ? '+' : '');
    let body = s;
    if (opts.thousands) {
      const [i, f] = s.split('.');
      body = i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f ? '.' + f : '');
    }
    return sign + body;
  }
  /** "[lo, hi]" with true minus signs. */
  function fmtInterval(lo, hi, decimals = 3) { return '[' + fmt(lo, decimals) + ', ' + fmt(hi, decimals) + ']'; }

  /* ------------------------------------------------------------------ *
   * 3. Motion vocabulary M1-M12 (§6.4). Pure functions of t.
   *    Each returns plain numbers in 0..1 (or values); scenes apply them.
   * ------------------------------------------------------------------ */

  /** M1 axis draw — introduces the object. Line 0.6 s; ticks staggered 30 ms;
   *  tick labels fade in over 0.3 s once the line is complete.
   *  -> { line, tick(i), labels, done } */
  function M1_axisDraw(t, start, o = {}) {
    const d = Object.assign({}, T.M1, o);
    const line = progress(t, start, d.dur, ease.enter);
    const tick = (i) => progress(t, start + i * d.tickStagger, d.tickDur, ease.enter);
    const labels = progress(t, start + d.dur, d.labelDur, ease.linear);
    return { line, tick, labels, done: t >= start + d.dur + d.labelDur };
  }

  /** M2 bar grows from the baseline — a state appears. 0.7 s, bars staggered 120 ms.
   *  -> grow 0..1 (value labels are separate: they follow the narration). */
  function M2_barGrow(t, start, o = {}) {
    const d = Object.assign({}, T.M2, o);
    return progress(t, start + (o.index || 0) * d.stagger, d.dur, ease.enter);
  }

  /** M3 focus: 2 px ink outline (offset 4 px) on the focus, everything else to 25 %.
   *  0.4 s in; restores 0.4 s after `end`. -> { outline 0..1, others opacity 1..0.25 } */
  function M3_focus(t, start, end = Infinity, o = {}) {
    const d = Object.assign({}, T.M3, o);
    const a = progress(t, start, d.dur, ease.morph) * (1 - progress(t, end, d.dur, ease.morph));
    return { outline: a, others: lerp(1, d.dim, a) };
  }

  /** M4 whisker + SESOI band — uncertainty. Dot 0.3 s -> whisker 0.5 s -> band 0.6 s,
   *  then the endpoint that crosses the band edge pulses once (0.4 s).
   *  Animated in scene 21 only; elsewhere use M4_static(). -> { dot, whisker, band, pulse } */
  function M4_whiskerBand(t, start, o = {}) {
    const d = Object.assign({}, T.M4, o);
    const t1 = start + d.dot, t2 = t1 + d.whisker, t3 = t2 + d.band;
    return {
      dot: progress(t, start, d.dot, ease.enter),
      whisker: progress(t, t1, d.whisker, ease.morph),
      band: progress(t, t2, d.band, ease.enter),
      pulse: Math.sin(Math.PI * progress(t, t3, d.pulse, ease.linear)),
    };
  }
  /** M4 static form (all scenes except 21): the interval appears at once with a 0.3 s fade. */
  function M4_static(t, at) { const a = appear(t, at); return { dot: a, whisker: a, band: a, pulse: 0, opacity: a }; }

  /** M5 funnel narrowing — state change. Each level 0.5 s, 0.4 s still between levels;
   *  the part that drops out becomes an ink ghost fading to 20 %.
   *  -> array of { narrow 0..1, ghost opacity 1..0.2 } */
  function M5_funnel(t, start, levels, o = {}) {
    const d = Object.assign({}, T.M5, o);
    return Array.from({ length: levels }, (_, i) => {
      const p = progress(t, start + i * (d.step + d.pause), d.step, ease.morph);
      return { narrow: p, ghost: lerp(1, d.ghost, p) };
    });
  }

  /** M6 set split or morph — state change. 0.9 s, morph ease. Circle areas ∝ n
   *  (see Kit.radiusForArea). -> p 0..1 */
  function M6_morph(t, start, o = {}) {
    return progress(t, start, (o.dur != null ? o.dur : T.M6.dur), ease.morph);
  }

  /** M7 strike — marks a removal. Line 0.25 s, then label 0.3 s.
   *  Colour carries meaning: red = valid values wrongly deleted (harmed data),
   *  ink = items removed on purpose. At most 3 strikes per scene.
   *  -> { line 0..1, label 0..1 } */
  function M7_strike(t, start, o = {}) {
    const d = Object.assign({}, T.M7, o);
    return { line: progress(t, start, d.dur, ease.enter), label: progress(t, start + d.dur, d.labelDur, ease.linear) };
  }

  /** M8 in-place value change — state change, replaces any number "crack" effect.
   *  0.8 s; bar length eases (morph), the number counts linearly, the fill cross-fades;
   *  all at the same time and nothing changes position.
   *  -> { length (eased value), value (linear count), fill 0..1, p } */
  function M8_valueChange(t, start, from, to, o = {}) {
    const dur = o.dur != null ? o.dur : T.M8.dur;
    const p = progress(t, start, dur, ease.morph);
    const c = progress(t, start, dur, ease.linear);
    return { length: lerp(from, to, p), value: lerp(from, to, c), fill: p, p };
  }

  /** M9 push-in — focus, used twice in the whole film (scenes 8 and 17).
   *  Push 0.9 s, hold >= 2 s, pull back 0.6 s. Scale is capped at 1.25.
   *  -> { scale, transform(ox, oy) } */
  function M9_pushIn(t, start, o = {}) {
    const d = Object.assign({}, T.M9, o);
    const target = Math.min(o.scale != null ? o.scale : d.maxScale, d.maxScale);
    if (o.scale > d.maxScale && global.console) console.warn('M9_pushIn: scale capped at ' + d.maxScale);
    const hold = Math.max(d.hold, T.M9.hold);
    const pin = progress(t, start, d.push, ease.morph);
    const pout = progress(t, start + d.push + hold, d.pull, ease.morph);
    const scale = 1 + (target - 1) * (pin - pout);
    return { scale, transform: (ox, oy) => `translate(${ox}px, ${oy}px) scale(${scale}) translate(${-ox}px, ${-oy}px)` };
  }

  /** M10 count — a continuous quantity. 0.8 s, linear start, slows at the end. -> value */
  function M10_count(t, start, from, to, o = {}) {
    return lerp(from, to, progress(t, start, (o.dur != null ? o.dur : T.M10.dur), ease.count));
  }

  /** M11 callout arrow — focus. Arrow draws in 0.4 s, label fades 0.3 s. One arrow at a time.
   *  -> { arrow 0..1, label 0..1 } */
  function M11_arrow(t, start, o = {}) {
    const d = Object.assign({}, T.M11, o);
    return { arrow: progress(t, start, d.arrow, ease.enter), label: progress(t, start + d.arrow, d.label, ease.linear) };
  }

  /** M12 dissolve — transition. 0.4 s cross-fade. -> p (outgoing 1 - p, incoming p) */
  function M12_dissolve(t, start, o = {}) {
    return progress(t, start, (o.dur != null ? o.dur : T.M12.dissolve), ease.linear);
  }
  /** M12 chapter card — transition. Static 1.2 s card, then a cut. -> visible boolean */
  function M12_chapterCard(t, start = 0, o = {}) {
    const dur = o.dur != null ? o.dur : T.M12.card;
    return t >= start && t < start + dur;
  }

  /* ------------------------------------------------------------------ *
   * 4. DOM / SVG primitives
   * ------------------------------------------------------------------ */
  function h(tag, attrs = {}, children = []) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null) continue;
      if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v;
      else if (k === 'html') e.innerHTML = v; else if (k === 'style') Object.assign(e.style, v);
      else e.setAttribute(k, v);
    }
    [].concat(children).forEach((c) => c != null && e.append(c));
    return e;
  }
  /** svg(tag, attrs, parent) — create an SVG element. attrs.text sets textContent. */
  function svg(tag, attrs = {}, parent = null) {
    const e = document.createElementNS(SVGNS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null) continue;
      if (k === 'text') e.textContent = v; else if (k === 'class') e.setAttribute('class', v);
      else if (k === 'style') Object.assign(e.style, v); else e.setAttribute(k, v);
    }
    if (parent) parent.appendChild(e);
    return e;
  }
  /** text(parent, {x, y, text, cls, anchor, fill, weight, size}) — SVG text. */
  function text(parent, o) {
    const e = svg('text', {
      x: o.x, y: o.y, class: o.cls || 'kit-t-note', 'text-anchor': o.anchor || 'start',
      'font-weight': o.weight, 'dominant-baseline': o.baseline,
    }, parent);
    if (o.size) e.style.fontSize = o.size + 'px';
    if (o.fill) e.style.fill = o.fill;   // inline style: class rules would beat a fill attribute
    e.textContent = o.text == null ? '' : o.text;
    return e;
  }
  /** Set opacity (and hide at 0 so it never catches the eye or the audit). */
  function op(el, v) {
    if (!el) return;
    v = clamp(v);
    el.style.opacity = String(v);
    el.style.visibility = v <= 0.001 ? 'hidden' : 'visible';
  }
  /** Width of an SVG text element (fonts must be loaded). */
  function textWidth(el) { try { return el.getComputedTextLength(); } catch (e) { return el.getBBox().width; } }

  let uid = 0;
  const nextId = (p) => `${p}-${++uid}`;

  /* ------------------------------------------------------------------ *
   * 5. Patterns, icons, feedback shapes
   * ------------------------------------------------------------------ */
  /** Semantic hatch for red (§6.2, §6.7): 45° red stripes on the pale red tint.
   *  Adds <pattern id> to `defs`, returns the id. */
  function hatchPattern(defs, id = 'kit-hatch-leak', o = {}) {
    const size = o.size || 14, w = o.stroke || 3.5;
    const p = svg('pattern', { id, patternUnits: 'userSpaceOnUse', width: size, height: size, patternTransform: 'rotate(45)' }, defs);
    svg('rect', { width: size, height: size, fill: C.leakTint }, p);
    svg('rect', { x: 0, y: 0, width: w, height: size, fill: C.leak }, p);
    return id;
  }

  /** Line icons (ink, drawn with currentColor). 40x40 viewBox. */
  const ICONS = {
    bucket: '<path d="M8 11h24l-3 17H11z"/><path d="M11 11c0-7 18-7 18 0"/><path d="M22 31.5c0 2.2-1 4-2 4s-2-1.8-2-4c0-1.6 2-3.5 2-3.5s2 1.9 2 3.5z"/>',
    ruler: '<rect x="3.5" y="13" width="33" height="14" rx="1.5"/><path d="M9 13v6M15 13v4M21 13v6M27 13v4M33 13v6"/>',
    balance: '<path d="M20 6v27M12 34h16M7 11h26"/><path d="M7 11l-4.5 11M7 11l4.5 11M33 11l-4.5 11M33 11l4.5 11"/><path d="M2 22h10a5 4 0 0 1-10 0zM28 22h10a5 4 0 0 1-10 0z"/>',
    triangle: '<path d="M20 5L37 34H3z"/><path d="M20 15v9"/><circle cx="20" cy="29" r="1.2" fill="currentColor"/>',
  };
  function iconSVG(name, size = 40, color = 'currentColor', strokeWidth = 2.5) {
    return `<svg viewBox="0 0 40 40" width="${size}" height="${size}" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;
  }
  /** Draw an icon into an SVG parent at (x, y) with the given size. */
  function icon(parent, name, o = {}) {
    const size = o.size || 40;
    const g = svg('g', { transform: `translate(${o.x || 0},${o.y || 0}) scale(${size / 40})`, fill: 'none', stroke: o.color || C.ink,
      'stroke-width': o.strokeWidth || 2.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, parent);
    g.innerHTML = ICONS[name];
    if (name === 'triangle') g.querySelector('circle').setAttribute('fill', o.color || C.ink);
    return g;
  }
  /** Warning triangle that always accompanies red (non-colour encoding). */
  function warnTriangle(parent, o = {}) { return icon(parent, 'triangle', { x: o.x, y: o.y, size: o.size || 28, color: C.leak, strokeWidth: 3 }); }

  /** Legend swatch markup (24 px): grey solid circle, red hatch square, teal solid square, blue hollow square. */
  function swatchSVG(key, size = 24) {
    const id = nextId('kit-sw');
    const body = {
      reference: `<circle cx="12" cy="12" r="9" fill="${C.reference}"/>`,
      leak: `<defs><pattern id="${id}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)"><rect width="6" height="6" fill="${C.leakTint}"/><rect width="2" height="6" fill="${C.leak}"/></pattern></defs><rect x="2.5" y="2.5" width="19" height="19" fill="url(#${id})" stroke="${C.leak}" stroke-width="2"/>`,
      systematic: `<rect x="3" y="3" width="18" height="18" fill="${C.systematic}"/>`,
      screen: `<rect x="4" y="4" width="16" height="16" fill="#fff" stroke="${C.screen}" stroke-width="3"/>`,
    }[key];
    return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true">${body}</svg>`;
  }

  /** Feedback shapes (§6.2): ink only, never a hue.
   *  kind 'supported' = solid check, 'inconclusive' = dashed box + "?", 'refuted' = cross.
   *  feedback(parent, {kind, x, y (top-left), size, label}) -> { g, update(opacity) } */
  function feedback(parent, o) {
    const s = o.size || 48, g = svg('g', { transform: `translate(${o.x},${o.y})` }, parent);
    if (o.kind === 'supported') {
      svg('circle', { cx: s / 2, cy: s / 2, r: s / 2, fill: C.ink }, g);
      svg('path', { d: `M${s * 0.27} ${s * 0.52} L${s * 0.44} ${s * 0.68} L${s * 0.74} ${s * 0.36}`, fill: 'none', stroke: '#fff',
        'stroke-width': s * 0.11, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g);
    } else if (o.kind === 'inconclusive') {
      svg('rect', { x: 1.5, y: 1.5, width: s - 3, height: s - 3, fill: 'none', stroke: C.ink, 'stroke-width': 3, 'stroke-dasharray': '7 5' }, g);
      text(g, { x: s / 2, y: s / 2 + s * 0.2, text: '?', anchor: 'middle', cls: 'kit-sans', size: Math.round(s * 0.62), weight: 600, fill: C.ink });
    } else if (o.kind === 'refuted') {
      svg('path', { d: `M${s * 0.2} ${s * 0.2} L${s * 0.8} ${s * 0.8} M${s * 0.8} ${s * 0.2} L${s * 0.2} ${s * 0.8}`, stroke: C.ink,
        'stroke-width': s * 0.12, 'stroke-linecap': 'round' }, g);
    } else throw new Error('feedback kind must be supported | inconclusive | refuted');
    let label = null;
    if (o.label) label = text(g, { x: s + 16, y: s / 2 + 12, text: o.label, cls: o.labelCls || 'kit-t-note' });
    return { g, label, update(a) { op(g, a); } };
  }

  /* ------------------------------------------------------------------ *
   * 6. Scales, axes and marks
   * ------------------------------------------------------------------ */
  /** scaleLinear([d0, d1], [r0, r1]) -> s(v); s.invert(px); s.domain; s.range; s.ticks(step) */
  function scaleLinear(domain, range) {
    const [d0, d1] = domain, [r0, r1] = range;
    const s = (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
    s.invert = (px) => d0 + ((px - r0) / (r1 - r0)) * (d1 - d0);
    s.domain = domain; s.range = range;
    s.ticks = (step) => {
      const out = [], lo = Math.min(d0, d1), hi = Math.max(d0, d1);
      for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + 1e-9; v += step) out.push(Math.round(v / step) * step);
      return out.map((v) => Number(v.toFixed(10)));
    };
    return s;
  }

  /** axis(parent, scale, opts) — axis with ticks, labels, optional title and the
   *  truncation label. Draws progressively via update(M1 state).
   *  opts: orient 'left'|'bottom', at (x for left, y for bottom), ticks [values],
   *        format (v -> string), tickLen 10, grid {from, to} (gridlines across the plot),
   *        title {text, x, y, anchor}, truncated {text: 'axis starts at 0.5', x, y, anchor}
   *        (also draws a break mark below the baseline). */
  function axis(parent, scale, o = {}) {
    const g = svg('g', { class: 'kit-axis' }, parent);
    const orient = o.orient || 'left', at = o.at || 0, tl = o.tickLen || 10;
    const ticks = o.ticks || scale.ticks(0.1), f = o.format || ((v) => fmt(v, 1));
    const [r0, r1] = scale.range;
    const ext = o.truncated ? 26 : 0;   // extra stub below the baseline for the break mark
    const gridG = svg('g', {}, g);
    const grid = (o.grid ? ticks.filter((v) => v !== scale.domain[0]) : []).map((v) => orient === 'left'
      ? svg('line', { x1: o.grid.from, x2: o.grid.to, y1: scale(v), y2: scale(v), stroke: C.line, 'stroke-width': 1 }, gridG)
      : svg('line', { y1: o.grid.from, y2: o.grid.to, x1: scale(v), x2: scale(v), stroke: C.line, 'stroke-width': 1 }, gridG));
    const p0 = orient === 'left' ? [at, r0 + ext] : [r0 - ext, at];
    const p1 = orient === 'left' ? [at, r1] : [r1, at];
    const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
    const line = svg('line', { x1: p0[0], y1: p0[1], x2: p1[0], y2: p1[1], stroke: C.ink, 'stroke-width': 2, 'stroke-dasharray': `${len} ${len}` }, g);
    const tickEls = ticks.map((v) => orient === 'left'
      ? svg('line', { x1: at - tl, x2: at, y1: scale(v), y2: scale(v), stroke: C.ink, 'stroke-width': 2 }, g)
      : svg('line', { y1: at, y2: at + tl, x1: scale(v), x2: scale(v), stroke: C.ink, 'stroke-width': 2 }, g));
    const labG = svg('g', {}, g);
    ticks.forEach((v) => orient === 'left'
      ? text(labG, { x: at - tl - 8, y: scale(v) + 10, text: f(v), anchor: 'end', cls: 'kit-t-tick' })
      : text(labG, { x: scale(v), y: at + tl + 34, text: f(v), anchor: 'middle', cls: 'kit-t-tick' }));
    let brk = null, note = null, title = null;
    if (o.truncated) {
      // break mark: two short parallel slashes across the stub below the baseline
      const bx = orient === 'left' ? at : r0 - ext / 2, by = orient === 'left' ? r0 + ext / 2 : at;
      brk = svg('g', { stroke: C.ink, 'stroke-width': 2 }, g);
      const d = orient === 'left'
        ? `M${bx - 9} ${by - 1} L${bx + 9} ${by - 7} M${bx - 9} ${by + 6} L${bx + 9} ${by}`
        : `M${bx - 4} ${by + 9} L${bx + 2} ${by - 9} M${bx + 3} ${by + 9} L${bx + 9} ${by - 9}`;
      svg('rect', orient === 'left' ? { x: bx - 10, y: by - 6, width: 20, height: 9, fill: '#fff', stroke: 'none' }
        : { x: bx - 4, y: by - 10, width: 9, height: 20, fill: '#fff', stroke: 'none' }, brk);
      svg('path', { d, fill: 'none' }, brk);
      const tr = Object.assign({ text: 'axis starts at ' + f(scale.domain[0]) }, o.truncated === true ? {} : o.truncated);
      note = text(g, { x: tr.x != null ? tr.x : at, y: tr.y != null ? tr.y : r0 + ext + 44, text: tr.text, anchor: tr.anchor || 'start', cls: 'kit-t-min' });
    }
    if (o.title) title = text(g, { x: o.title.x, y: o.title.y, text: o.title.text, anchor: o.title.anchor || 'start', cls: o.title.cls || 'kit-t-min' });
    const api = {
      g, line, ticks: tickEls, labels: labG, note, title, grid,
      /** update(M1 state) */
      update(m) {
        line.setAttribute('stroke-dashoffset', String(len * (1 - m.line)));
        tickEls.forEach((el, i) => op(el, m.tick(i)));
        grid.forEach((el, i) => op(el, m.tick(i + 1) * 1));
        op(labG, m.labels); op(note, m.labels); op(title, m.labels); op(brk, m.labels);
      },
    };
    return api;
  }

  const BAR_STYLES = {
    leak: () => ({ fill: 'url(#kit-hatch-leak)', stroke: C.leak, sw: 2 }),
    reference: () => ({ fill: C.reference, stroke: C.reference, sw: 0 }),
    systematic: () => ({ fill: C.systematic, stroke: C.systematic, sw: 0 }),
    screen: () => ({ fill: C.screenTint, stroke: C.screen, sw: 3 }),
    ink: () => ({ fill: '#FFFFFF', stroke: C.ink, sw: 2 }),
  };
  /** bar(parent, {scale, base, x, width, orient 'v'|'h', styles: ['leak', 'reference']})
   *  Two stacked rects allow the M8 fill cross-fade (styles[0] -> styles[1]).
   *  update({value, grow 0..1 (M2), mix 0..1 (M8 fill), opacity}) */
  function bar(parent, o) {
    const g = svg('g', { class: 'kit-bar' }, parent);
    const styles = (o.styles || [o.style || 'ink']).map((k) => BAR_STYLES[k]());
    const rects = styles.map((s) => svg('rect', { fill: s.fill, stroke: s.stroke, 'stroke-width': s.sw }, g));
    const orient = o.orient || 'v', base = o.base != null ? o.base : o.scale.domain[0];
    return {
      g, rects,
      update(u) {
        const grow = u.grow == null ? 1 : u.grow, v = base + (u.value - base) * grow;
        const a = o.scale(base), b = o.scale(v);
        rects.forEach((r, i) => {
          const inset = styles[i].sw / 2;
          if (orient === 'v') {
            r.setAttribute('x', o.x + inset); r.setAttribute('width', Math.max(0, o.width - 2 * inset));
            r.setAttribute('y', Math.min(a, b) + inset); r.setAttribute('height', Math.max(0, Math.abs(a - b) - inset));
          } else {
            r.setAttribute('y', o.y + inset); r.setAttribute('height', Math.max(0, o.width - 2 * inset));
            r.setAttribute('x', Math.min(a, b)); r.setAttribute('width', Math.max(0, Math.abs(a - b) - inset));
          }
          const mix = u.mix || 0;
          op(r, rects.length === 1 ? 1 : (i === 0 ? 1 - mix : mix));
        });
        op(g, (u.opacity == null ? 1 : u.opacity) * (grow > 0 ? 1 : 0));
      },
    };
  }

  /** dotWhisker(parent, scale, {orient 'h'|'v', at (cross-axis px), est, lo, hi,
   *  shape 'circle'|'square'|'hollowSquare', role 'reference'|'systematic'|'screen'|'ink'|'leak',
   *  size 20, cap 18, pulseEnd 'lo'|'hi'})
   *  update({dot, whisker, pulse}) — use with M4_whiskerBand or M4_static. */
  function dotWhisker(parent, scale, o) {
    const g = svg('g', { class: 'kit-dotwhisker' }, parent);
    const col = { reference: C.reference, systematic: C.systematic, screen: C.screen, ink: C.ink, leak: C.leak }[o.role || 'ink'];
    const hv = (o.orient || 'h') === 'h', at = o.at, size = o.size || 20, cap = o.cap || 18;
    const P = (v, off = 0) => (hv ? [scale(v), at + off] : [at + off, scale(v)]);
    const wl = svg('line', { stroke: col, 'stroke-width': 3, 'stroke-linecap': 'butt' }, g);
    const caps = [o.lo, o.hi].map(() => svg('line', { stroke: col, 'stroke-width': 3 }, g));
    const pulse = svg('circle', { r: 0, fill: 'none', stroke: col, 'stroke-width': 2 }, g);
    const [cx, cy] = P(o.est);
    let dot;
    const shape = o.shape || (o.role === 'screen' ? 'hollowSquare' : 'circle');
    if (shape === 'circle') dot = svg('circle', { cx, cy, r: size / 2, fill: col }, g);
    else if (shape === 'square') dot = svg('rect', { x: cx - size / 2, y: cy - size / 2, width: size, height: size, fill: col }, g);
    else dot = svg('rect', { x: cx - size / 2 + 1.5, y: cy - size / 2 + 1.5, width: size - 3, height: size - 3, fill: '#fff', stroke: col, 'stroke-width': 3 }, g);
    return {
      g, dot,
      update(u) {
        const w = u.whisker == null ? 1 : u.whisker;
        const lo = lerp(o.est, o.lo, w), hi = lerp(o.est, o.hi, w);
        const [x1, y1] = P(lo), [x2, y2] = P(hi);
        wl.setAttribute('x1', x1); wl.setAttribute('y1', y1); wl.setAttribute('x2', x2); wl.setAttribute('y2', y2);
        [lo, hi].forEach((v, i) => {
          const [a1, b1] = P(v, -cap / 2), [a2, b2] = P(v, cap / 2);
          const c = caps[i]; c.setAttribute('x1', a1); c.setAttribute('y1', b1); c.setAttribute('x2', a2); c.setAttribute('y2', b2);
          op(c, w >= 0.999 ? 1 : 0);
        });
        op(wl, w > 0 ? 1 : 0);
        op(dot, u.dot == null ? 1 : u.dot);
        const pv = u.pulse || 0;
        if (o.pulseEnd && pv > 0) {
          const [px, py] = P(o.pulseEnd === 'lo' ? o.lo : o.hi);
          pulse.setAttribute('cx', px); pulse.setAttribute('cy', py); pulse.setAttribute('r', 6 + 10 * pv);
        }
        op(pulse, pv);
        if (u.opacity != null) op(g, u.opacity);
      },
    };
  }

  /** sesoiBand(parent, scale, {lo -0.01, hi 0.01, from, to (cross-axis extent), orient 'h'})
   *  Neutral grey band with dashed edges (never a semantic colour). update(opacity) */
  function sesoiBand(parent, scale, o) {
    const g = svg('g', { class: 'kit-sesoi' }, parent);
    const lo = o.lo != null ? o.lo : -0.01, hi = o.hi != null ? o.hi : 0.01, hv = (o.orient || 'h') === 'h';
    const a = scale(lo), b = scale(hi);
    if (hv) {
      svg('rect', { x: Math.min(a, b), y: o.from, width: Math.abs(b - a), height: o.to - o.from, fill: C.band }, g);
      [a, b].forEach((x) => svg('line', { x1: x, x2: x, y1: o.from, y2: o.to, stroke: C.line, 'stroke-width': 2, 'stroke-dasharray': '6 5' }, g));
    } else {
      svg('rect', { y: Math.min(a, b), x: o.from, height: Math.abs(b - a), width: o.to - o.from, fill: C.band }, g);
      [a, b].forEach((y) => svg('line', { y1: y, y2: y, x1: o.from, x2: o.to, stroke: C.line, 'stroke-width': 2, 'stroke-dasharray': '6 5' }, g));
    }
    return { g, update(v) { op(g, v); } };
  }

  /** callout(parent, {x, y (number baseline), anchor, size 'main'|'second', decimals, sign,
   *  value, interval [lo, hi] | "[lo, hi]", label, layout 'stack'|'inline', fill})
   *  Mono tabular number; the interval fades in 0.3 s after the number; one 28 px label line.
   *  update({value | text, number, interval, label, fill}) — opacities 0..1; `text` prints verbatim. */
  function callout(parent, o) {
    const g = svg('g', { class: 'kit-callout' }, parent);
    const main = (o.size || 'main') === 'main';
    const num = text(g, { x: o.x, y: o.y, anchor: o.anchor || 'start', cls: main ? 'kit-t-main' : 'kit-t-second', fill: o.fill });
    const lineGap = main ? 60 : 54;
    let iv = null, lab = null, y = o.y;
    if (o.interval) {
      const ivText = typeof o.interval === 'string' ? o.interval : fmtInterval(o.interval[0], o.interval[1], o.decimals != null ? o.decimals : 3);
      iv = text(g, { x: o.x, y: (y += lineGap), anchor: o.anchor || 'start', cls: 'kit-t-interval', text: ivText });
    }
    if (o.label) lab = text(g, { x: o.x, y: (y += 44), anchor: o.anchor || 'start', cls: 'kit-t-min', text: o.label });
    const d = o.decimals != null ? o.decimals : 3;
    function place() {
      if (o.layout === 'inline' && iv) {
        iv.setAttribute('x', o.x + textWidth(num) + 16); iv.setAttribute('y', o.y);
        if (lab) lab.setAttribute('y', o.y + 44);
      }
    }
    return {
      g, num, interval: iv, label: lab,
      update(u) {
        num.textContent = u.text != null ? u.text : fmt(u.value != null ? u.value : o.value, d, { sign: o.sign });
        if (u.fill) num.style.fill = u.fill;
        op(num, u.number == null ? 1 : u.number);
        if (iv) op(iv, u.interval == null ? 0 : u.interval);
        if (lab) op(lab, u.label == null ? 0 : u.label);
        place();
      },
    };
  }

  /** strike(parent, target, {color 'ink'|'leak', pad 6}) — M7 strike line through an
   *  SVG text element (or a {x, y, w} box). update(M7 state). */
  function strike(parent, target, o = {}) {
    let x, y, w;
    if (target instanceof SVGElement) {
      const b = target.getBBox();
      x = b.x; w = b.width; y = b.y + b.height * 0.56;
    } else ({ x, y, w } = target);
    const pad = o.pad != null ? o.pad : 6;
    const col = o.color === 'leak' ? C.leak : C.ink;
    const ln = svg('line', { x1: x - pad, y1: y, x2: x - pad, y2: y, stroke: col, 'stroke-width': o.width || 3.5, 'stroke-linecap': 'round' }, parent);
    return { line: ln, update(m) { ln.setAttribute('x2', x - pad + (w + 2 * pad) * m.line); op(ln, m.line > 0 ? 1 : 0); } };
  }

  /** Focus outline (M3): 2 px ink rect offset 4 px around a box. update(M3 state). */
  function focusRing(parent, box) {
    const r = svg('rect', { x: box.x - 4, y: box.y - 4, width: box.w + 8, height: box.h + 8, rx: 4, fill: 'none', stroke: C.ink, 'stroke-width': 2 }, parent);
    return { el: r, update(m) { op(r, m.outline); } };
  }

  /** Circle radius so that area ∝ n (M6). */
  const radiusForArea = (n, nRef, rRef) => rRef * Math.sqrt(n / nRef);

  /** Straight callout arrow (M11). update(M11 state) */
  function arrow(parent, o) {
    const g = svg('g', {}, parent);
    const len = Math.hypot(o.x2 - o.x1, o.y2 - o.y1);
    const ln = svg('line', { x1: o.x1, y1: o.y1, x2: o.x2, y2: o.y2, stroke: C.ink, 'stroke-width': 3, 'stroke-dasharray': `${len} ${len}` }, g);
    const ang = Math.atan2(o.y2 - o.y1, o.x2 - o.x1), hs = 14;
    const head = svg('path', { d: `M${o.x2} ${o.y2} L${o.x2 - hs * Math.cos(ang - 0.45)} ${o.y2 - hs * Math.sin(ang - 0.45)} L${o.x2 - hs * Math.cos(ang + 0.45)} ${o.y2 - hs * Math.sin(ang + 0.45)} Z`, fill: C.ink }, g);
    const lab = o.label ? text(g, Object.assign({ cls: 'kit-t-min' }, o.label)) : null;
    return { g, update(m) { ln.setAttribute('stroke-dashoffset', len * (1 - m.arrow)); op(head, m.arrow >= 0.999 ? 1 : 0); op(ln, m.arrow > 0 ? 1 : 0); op(lab, m.label); } };
  }

  /* ------------------------------------------------------------------ *
   * 7. Timeline, names and the word clock
   * ------------------------------------------------------------------ */
  const PLACEHOLDER = '[Name]';

  /** Timeline with derived start/end per scene and section. Set by createScene. */
  function indexTimeline(tl) {
    let t = 0;
    tl.byNumber = {};
    tl.scenes.forEach((s) => { s.start = t; t += s.duration; s.end = t; tl.byNumber[s.n] = s; });
    tl.total = t;
    tl.sections.forEach((sec) => {
      const sc = tl.scenes.filter((s) => s.section === sec.n);
      sec.start = sc.length ? Math.min(...sc.map((s) => s.start)) : null;
      sec.end = sc.length ? Math.max(...sc.map((s) => s.end)) : null;
    });
    return tl;
  }

  /** Member index from a number or a legacy letter key (the letter itself is never shown). */
  function memberIndex(v) {
    if (v == null) return null;
    if (typeof v === 'number') return v;
    const i = 'ABCD'.indexOf(String(v).toUpperCase());
    return i >= 0 ? i : null;
  }

  /** Display name of member i: the team.json name, or "[Name]" while it is a placeholder. */
  function name(i) {
    const m = STATE.team && STATE.team.members && STATE.team.members[i];
    return m && m.name ? m.name : PLACEHOLDER;
  }
  /** Member record: { index, name, role, roleKey, owns, presents }. */
  function member(i) {
    const meta = (STATE.timeline && STATE.timeline.members || []).find((m) => m.index === i) || {};
    return Object.assign({ index: i }, meta, { name: name(i) });
  }
  /** Replace <Name> (this scene's speaker), <Name:i> (member i, 0-based), {role}, {group}. */
  function names(str, speaker = STATE.speaker) {
    if (str == null) return str;
    return String(str)
      .replace(/<Name(?::(\d))?>/g, (_, i) => name(i != null ? Number(i) : speaker))
      .replace(/\{role(?::(\d))?\}/g, (_, i) => member(i != null ? Number(i) : speaker).role || '')
      .replace(/\{group\}/g, (STATE.team && STATE.team.group) || '[no.]');
  }

  function sceneInfo(n) { return STATE.timeline && STATE.timeline.byNumber[n == null ? STATE.scene : n]; }

  /** One token -> comparable key: lower case, no punctuation ("5,730" -> "5730", "don't" -> "dont", "0.961." -> "0.961"). */
  const normWord = (s) => String(s).toLowerCase().replace(/[^a-z0-9<>:.%]+/g, '').replace(/\.(?!\d)|(?<!\d)\./g, '');
  /** Word clock of a scene: [{w (narration token), t (as captioned), s, e}] in scene seconds. */
  function words(n) {
    const sc = STATE.words && STATE.words.scenes && STATE.words.scenes[n == null ? STATE.scene : n];
    if (!sc) throw new Error(`No word clock for scene ${n == null ? STATE.scene : n}: run "node video/subtitles/build_subs.mjs"`);
    return sc.words;
  }
  /** cueAt([scene,] phrase, {nth = 1, end = false, offset = 0}) -> scene time (s) at which the
   *  narration phrase starts (or ends, with end: true). Matches the narration tokens (with <Name>
   *  tokens) or the captioned text, ignoring case and punctuation. Throws if the phrase is missing. */
  function cueAt(a, b, c) {
    let n = STATE.scene, phrase = a, o = b || {};
    if (typeof a === 'number') { n = a; phrase = b; o = c || {}; }
    const W = words(n);
    const P = String(phrase).split(/\s+/).map(normWord).filter(Boolean);
    const nth = o.nth || 1;
    for (const key of ['w', 't']) {
      const toks = W.map((x) => normWord(x[key]));
      let seen = 0;
      for (let i = 0; i + P.length <= toks.length; i++) {
        if (P.every((p, k) => toks[i + k] === p)) {
          if (++seen === nth) return +((o.end ? W[i + P.length - 1].e : W[i].s) + (o.offset || 0)).toFixed(3);
        }
      }
    }
    throw new Error(`cueAt: phrase not found in scene ${n}: "${phrase}"`);
  }
  /** Resolve a cues table: numbers stay; 'phrase' | ['phrase', offset] | {phrase, offset, end, nth} -> seconds. */
  function resolveCues(cues) {
    const out = {};
    for (const [k, v] of Object.entries(cues || {})) {
      if (typeof v === 'number' || v == null) out[k] = v;
      else if (typeof v === 'string') out[k] = cueAt(v);
      else if (Array.isArray(v)) out[k] = typeof v[0] === 'string' ? cueAt(v[0], { offset: v[1] || 0 }) : v;
      else if (typeof v === 'object' && v.phrase) out[k] = cueAt(v.phrase, v);
      else out[k] = v;
    }
    return out;
  }

  /* ------------------------------------------------------------------ *
   * 8. Stage chrome: motif, progress bar, title + subtitle (+ credit), panel,
   *    name tag + PiP, footer (legend row, notebook pointer), legend chip,
   *    full-frame cards (title, chapter, closing)
   * ------------------------------------------------------------------ */
  /** Questionnaire / codebook grid: 1 px ink lines, <= 4 % opacity, only in the outer margins. Static. */
  function motif() {
    const W = GRID.W, H = GRID.H, id = nextId('kit-motif');
    const cols = [72, 144, 48, 96, 192, 60, 120, 84, 168, 36, 108];
    let xs = [], x = 0, i = 0;
    while (x < W) { xs.push(x); x += cols[i++ % cols.length]; }
    let lines = '';
    for (let y = 0; y <= H; y += 24) lines += `<line x1="0" x2="${W}" y1="${y + 0.5}" y2="${y + 0.5}"/>`;
    xs.forEach((x) => { lines += `<line y1="0" y2="${H}" x1="${x + 0.5}" x2="${x + 0.5}"/>`; });
    const m = GRID.marginX, my = 40;
    const html = `<svg class="kit-motif" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true">
      <defs>
        <linearGradient id="${id}-t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <linearGradient id="${id}-b" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <linearGradient id="${id}-l" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <linearGradient id="${id}-r" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <mask id="${id}-m" maskUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}">
          <rect x="0" y="0" width="${W}" height="${my}" fill="url(#${id}-t)"/>
          <rect x="0" y="${H - my}" width="${W}" height="${my}" fill="url(#${id}-b)"/>
          <rect x="0" y="0" width="${m}" height="${H}" fill="url(#${id}-l)"/>
          <rect x="${W - m}" y="0" width="${m}" height="${H}" fill="url(#${id}-r)"/>
        </mask>
      </defs>
      <g mask="url(#${id}-m)" stroke="${C.ink}" stroke-width="1" opacity="0.04">${lines}</g>
    </svg>`;
    const wrap = h('div', { html });
    return wrap.firstElementChild;
  }

  const NO_POINTER_PAGES = new Set(['blockstart', 'title', 'chapter', 'closing', 'card']);

  /** "7.5" -> "Notebook section 7.5"; "4.7–4.8" or "1.1, 3.2" -> "Notebook sections ..."; full strings pass. */
  function pointerText(p) {
    if (p == null || p === false || p === '') return null;
    const s = String(p).trim();
    if (/^notebook/i.test(s)) return s;
    return (/[–,-]| and /.test(s) ? 'Notebook sections ' : 'Notebook section ') + s;
  }

  /** Phases: [{at, title, subtitle, page, pointer, credit}], each field inherited from cfg when omitted. */
  function normPhases(cfg) {
    let list;
    if (Array.isArray(cfg.phases)) list = cfg.phases;
    else if (Array.isArray(cfg.title)) list = cfg.title.map((x) => ({ at: x.at, title: x.text != null ? x.text : x.title, subtitle: x.subtitle }));
    else list = [{ at: 0 }];
    const base = {
      title: typeof cfg.title === 'string' ? cfg.title : null,
      subtitle: cfg.subtitle != null ? cfg.subtitle : null,
      page: cfg.page || 'evidence',
      pointer: cfg.pointer !== undefined ? cfg.pointer : null,
      credit: cfg.credit != null ? cfg.credit : null,
    };
    return list.map((p) => {
      const o = { at: p.at || 0 };
      for (const k of Object.keys(base)) o[k] = p[k] !== undefined ? p[k] : base[k];
      return o;
    }).sort((a, b) => a.at - b.at);
  }

  /** Runs of equal text for one field: [{from, to, text, el}] — a change dissolves (M12), equal text holds. */
  function runsOf(phases, get) {
    const runs = [];
    phases.forEach((p) => {
      const text = get(p);
      const last = runs[runs.length - 1];
      if (last && last.text === text) return;
      runs.push({ from: p.at, text });
    });
    return runs;
  }
  function runOpacity(t, runs, k, delay = 0, fadeFirst = null) {
    const r = runs[k], next = runs[k + 1];
    if (!r.el) return 0;
    const pin = k === 0 ? (fadeFirst != null ? appear(t, fadeFirst, T.M12.dissolve) : 1) : M12_dissolve(t, r.from + delay);
    const pout = next ? M12_dissolve(t, next.from + (next.text ? delay : 0)) : 0;
    return pin * (1 - pout);
  }

  function buildChrome(cfg, stage) {
    const ui = { stage };
    const spk = STATE.speaker;
    const bg = h('div', { class: 'kit-stagebg' });
    if (cfg.grid !== false) bg.append(motif());
    stage.append(bg);

    // --- progress bar (seven sections, plain words)
    const tl = STATE.timeline;
    if (tl && cfg.progress !== false) {
      const bar = h('div', { class: 'kit-progress' });
      const segs = tl.sections.map((sec) => {
        const fill = h('div', { class: 'kit-progress-fill' });
        const rule = h('div', { class: 'kit-progress-rule' }, [fill]);
        const label = h('div', { class: 'kit-progress-label', text: sec.label });
        const el = h('div', { class: 'kit-progress-seg' }, [label, rule]);
        bar.append(el);
        return { n: sec.n, label: sec.label, el, labelEl: label, rule, fill, sec };
      });
      stage.append(bar);
      ui.progress = { el: bar, segs };
    }

    // --- title and subtitle rows (phases dissolve with M12)
    const phases = ui.phases = normPhases(cfg);
    const band = h('div', { class: 'kit-title-band' });
    const sub = h('div', { class: 'kit-subrow' });
    const mk = (runs, parent, cls) => runs.forEach((r) => { if (r.text) { r.el = h('div', { class: cls, text: r.text }); parent.append(r.el); } });
    ui.runs = {
      title: runsOf(phases, (p) => (p.title ? names(p.title) : null)),
      subtitle: runsOf(phases, (p) => (p.subtitle ? names(p.subtitle) : null)),
      credit: runsOf(phases, (p) => (p.credit ? names(p.credit) : null)),
      pointer: runsOf(phases, (p) => (NO_POINTER_PAGES.has(p.page) ? null : pointerText(p.pointer))),
    };
    mk(ui.runs.title, band, 'kit-title');
    mk(ui.runs.subtitle, sub, 'kit-subtitle');
    mk(ui.runs.credit, sub, 'kit-credit');
    stage.append(band, sub);
    ui.titleBand = band; ui.subRow = sub;
    ui.titles = ui.runs.title.filter((r) => r.el).map((r) => ({ el: r.el, at: r.from, text: r.text }));   // legacy shape

    // --- paper panel: SVG figure + an HTML layer for text pages
    const P = GRID.panel;
    const panel = h('div', { class: 'kit-panel' });
    const fig = svg('svg', { width: P.w, height: P.h, viewBox: `0 0 ${P.w} ${P.h}`, class: 'kit-figure' });
    const defs = svg('defs', {}, fig);
    hatchPattern(defs);
    const figHTML = h('div', { class: 'kit-figure-html' });
    panel.append(fig, figHTML);
    if (cfg.panel === false) panel.style.display = 'none';
    stage.append(panel);
    Object.assign(ui, { panel, fig, defs, figHTML, P });

    // --- footer: legend row (left) + notebook pointer (right)
    const bar = h('div', { class: 'kit-bottombar' });
    const row = h('div', { class: 'kit-legendrow' });
    ui.legendItems = {};
    const moment = cfg.legendMoment && cfg.legendMoment.key;
    const showLegend = cfg.legend === false ? [] : LEGEND.filter((l) => (cfg.number >= l.first && cfg.number < 900) || l.key === moment || (cfg.legend || []).includes(l.key));
    showLegend.forEach((l) => {
      const it = h('div', { class: 'kit-legend-item', html: swatchSVG(l.key) });
      it.append(h('span', { text: l.row }));
      row.append(it);
      ui.legendItems[l.key] = it;
    });
    const pointer = h('div', { class: 'kit-pointer' });
    ui.runs.pointer.forEach((r) => { if (r.text) { r.el = h('span', { text: r.text, style: { position: 'absolute', right: '0' } }); pointer.append(r.el); } });
    Object.assign(pointer.style, { position: 'relative', height: '28px', minWidth: '1px' });
    bar.append(row, pointer);
    stage.append(bar);
    ui.legendRow = row; ui.pointer = pointer; ui.bottom = bar;

    // --- legend chip (first use of a semantic colour): panel top-right, 2-3 s, folds into the row
    if (cfg.legendMoment) {
      const lm = cfg.legendMoment, def = LEGEND.find((l) => l.key === lm.key);
      const chip = h('div', { class: 'kit-legendchip', html: swatchSVG(lm.key, 32) });
      chip.append(h('span', { text: def.chip }));
      stage.append(chip);
      ui.chip = chip;
    }

    // --- full-frame cards (under the PiP, the name tag and, on chapter cards, the progress bar)
    const cards = (cfg.cards || []).slice();
    if (cfg.chapterCard) cards.push(Object.assign({ type: 'chapter' }, cfg.chapterCard, { title: cfg.chapterCard.title }));
    ui.cards = cards.map((c) => buildCard(c, cfg));
    ui.cards.forEach((c) => stage.append(c.el));

    // --- name tag + PiP slot (always on top, whole film)
    const m = member(spk);
    ui.nametagName = h('div', { class: 'kit-nametag-name', text: names(cfg.nametag && cfg.nametag.line1 || 'Presented by <Name>') });
    ui.nametagRole = h('div', { class: 'kit-nametag-role', text: names(cfg.nametag && cfg.nametag.line2 || m.role || '') });
    ui.nametag = h('div', { class: 'kit-nametag' }, [ui.nametagName, ui.nametagRole]);
    ui.camera = h('div', { class: 'kit-camera' });
    stage.append(ui.nametag, ui.camera);

    // --- caption preview (?captions=1)
    if (STATE.captions) {
      ui.captions = h('div', { class: 'kit-captions' + (STATE.captionsOutline ? ' is-outline' : '') });
      stage.append(ui.captions);
    }
    return ui;
  }

  /** Full-frame cards. type 'title' | 'chapter' | 'closing'. Text passes through names(). */
  function buildCard(c, cfg) {
    const el = h('div', { class: 'kit-card' });
    const add = (cls, text, style) => { if (text == null || text === '') return null; const d = h('div', { class: cls, text: names(text), style }); el.append(d); return d; };
    const px = (v) => v + 'px';
    const sec = sceneInfo() && STATE.timeline.sections.find((s) => s.n === sceneInfo().section);
    const card = Object.assign({ at: 0 }, c);
    if (c.type === 'title') {
      card.until = c.until != null ? c.until : card.at + (c.dur || T.titleCard);
      card.progress = c.progress === true;
      add('kit-card-title', c.title, { left: px(192), top: px(330) });
      add('kit-card-sub', c.subtitle, { left: px(192), top: px(448) });
      add('kit-card-line', c.line, { left: px(192), top: px(516) });
      add('kit-card-small', c.small, { left: px(192), top: px(568) });
    } else if (c.type === 'chapter') {
      card.until = c.until != null ? c.until : card.at + (c.dur || T.M12.card);
      card.progress = c.progress !== false;
      add('kit-card-chapter', c.title != null ? c.title : sec && sec.label, { left: px(192), top: px(392) });
      add('kit-card-sub', c.scope != null ? c.scope : sec && sec.scope, { left: px(192), top: px(500) });
      add('kit-card-line', c.line != null ? c.line : (c.item != null ? c.item : 'Presented by <Name>'), { left: px(192), top: px(562) });
    } else if (c.type === 'closing') {
      card.until = c.until != null ? c.until : Infinity;
      card.progress = false;
      // everything above y 632 (clear of the PiP keep-out and the caption zone), centred on the stage
      const centre = { left: px(GRID.W / 2), transform: 'translateX(-50%)' };
      add('kit-card-close', c.title, Object.assign({ top: px(292) }, centre));
      add('kit-card-sub', c.subtitle, Object.assign({ top: px(436) }, centre));
      if (c.route !== false && STATE.timeline) {
        const route = h('div', { class: 'kit-card-route', style: Object.assign({ top: px(506) }, centre) });
        STATE.timeline.sections.forEach((s) => route.append(h('div', { text: s.label })));
        el.append(route);
        card.route = route;
      }
      add('kit-card-line', c.line, Object.assign({ top: px(584) }, centre));
      add('kit-card-source', c.source, { left: px(96), top: px(1002) });
    } else throw new Error('card type must be title | chapter | closing');
    card.el = el;
    return card;
  }

  /** Stage-coordinate rect of an element (independent of the preview scale). */
  function stageRect(el, stage) {
    const s = stage.getBoundingClientRect(), r = el.getBoundingClientRect(), k = s.width / GRID.W;
    return { x: (r.left - s.left) / k, y: (r.top - s.top) / k, w: r.width / k, h: r.height / k };
  }
  const scaleK = (ui) => ui.stage.getBoundingClientRect().width / GRID.W;

  /** Layout passes that need real font metrics (after fonts load). */
  function measureChrome(cfg, ui) {
    const k = scaleK(ui);
    // progress segments: width = label + 32, gap 16, left-aligned from x 96
    if (ui.progress) {
      let x = 0;
      ui.progress.segs.forEach((s) => {
        s.labelEl.style.fontWeight = '600';   // measure the semibold (current) width so the label never outgrows its segment
        const w = s.labelEl.getBoundingClientRect().width / k + GRID.progress.pad;
        s.labelEl.style.fontWeight = '';
        Object.assign(s.el.style, { left: x + 'px', width: w + 'px' });
        s.x = GRID.progress.x + x; s.w = w; s.y = GRID.progress.y;
        x += w + GRID.progress.gap;
      });
      ui.progress.width = x - GRID.progress.gap;
    }
    // name tag: shrink a long name to fit 356 px (audit flags anything under 28 px)
    [ui.nametagName, ui.nametagRole].forEach((el) => {
      const avail = GRID.nametag.w - 30, w = el.getBoundingClientRect().width / k;
      if (w > avail) el.style.fontSize = Math.max(22, Math.floor(28 * avail / w * 10) / 10) + 'px';
    });
    // legend chip geometry: start = panel top-right corner, end = its legend-row item
    if (ui.chip) {
      const P = GRID.panel, chipW = ui.chip.getBoundingClientRect().width / k;
      ui.chipFrom = { x: P.x + P.w - 24 - chipW, y: P.y + 24 };
      const item = ui.legendItems && ui.legendItems[cfg.legendMoment.key];
      ui.chipTo = item ? stageRect(item, ui.stage) : null;
      ui.chipW = chipW;
    }
  }

  function updateChrome(t, cfg, ui) {
    // cards
    let cardHidesProgress = false, cardOn = false;
    ui.cards.forEach((c) => {
      let v;
      if (c.type === 'chapter') v = t >= c.at && t < c.until ? 1 : 0;                                  // static, then a cut
      else if (c.type === 'title') v = t >= c.at && t < c.until ? 1 - M12_dissolve(t, c.until - T.M12.dissolve) : 0;
      else v = t >= c.at ? M12_dissolve(t, c.at) : 0;                                                  // closing: dissolves in
      op(c.el, v);
      if (v > 0.001) { cardOn = true; if (!c.progress) cardHidesProgress = true; }
    });
    ui.cardOn = cardOn;
    // progress bar: pure function of global time
    if (ui.progress) {
      const info = sceneInfo(), tl = STATE.timeline;
      const g = (info ? info.start : 0) + t, cur = cfg.section || (info && info.section) || 0;
      ui.progress.segs.forEach((s) => {
        const state = s.n < cur ? 'is-done' : s.n === cur ? 'is-current' : 'is-todo';
        if (s.state !== state) { s.el.className = 'kit-progress-seg ' + state; s.state = state; }
        const sec = s.sec, f = state === 'is-current' && sec.end > sec.start ? clamp((g - sec.start) / (sec.end - sec.start)) : 0;
        s.fill.style.width = (f * 100).toFixed(3) + '%';
        op(s.fill, state === 'is-current' ? 1 : 0);
      });
      let v = 1;
      if (cfg.progress && typeof cfg.progress === 'object') v = appear(t, cfg.progress.at || 0, cfg.progress.dur != null ? cfg.progress.dur : T.appear);
      if (cardHidesProgress) v = 0;
      if (tl) op(ui.progress.el, v);
    }
    // title, subtitle, credit, pointer phases
    const fadeFirst = cfg.titleFadeIn != null ? cfg.titleFadeIn : null;
    ui.runs.title.forEach((r, i) => op(r.el, runOpacity(t, ui.runs.title, i, 0, fadeFirst)));
    ui.runs.subtitle.forEach((r, i) => op(r.el, runOpacity(t, ui.runs.subtitle, i, T.subtitleDelay, fadeFirst != null ? fadeFirst + T.subtitleDelay : null)));
    ui.runs.credit.forEach((r, i) => op(r.el, runOpacity(t, ui.runs.credit, i, T.subtitleDelay)));
    ui.runs.pointer.forEach((r, i) => op(r.el, runOpacity(t, ui.runs.pointer, i)));
    // legend moment
    if (ui.chip) {
      const lm = cfg.legendMoment, hold = lm.hold || T.legendHold;
      const a = appear(t, lm.at), c = progress(t, lm.at + hold, T.legendCollapse, ease.morph);
      const item = ui.legendItems && ui.legendItems[lm.key];
      if (ui.chipTo) {
        const x = lerp(ui.chipFrom.x, ui.chipTo.x, c), y = lerp(ui.chipFrom.y, ui.chipTo.y, c);
        const sc = lerp(1, ui.chipTo.w / ui.chipW, c);
        Object.assign(ui.chip.style, { left: '0px', top: '0px', transform: `translate(${x}px, ${y}px) scale(${sc})` });
      }
      op(ui.chip, a * (1 - clamp((c - 0.5) * 2)));
      if (item) op(item, clamp((c - 0.5) * 2));
    }
    // caption preview
    if (ui.captions) {
      const caps = STATE.captions.scenes[STATE.scene] || [];
      const cur = caps.find((c) => t >= c.start && t < c.end);
      const key = cur ? cur.lines.join('\n') : '';
      if (ui.captions.dataset.key !== key) {
        ui.captions.dataset.key = key;
        ui.captions.replaceChildren(...(cur ? cur.lines.map((l) => h('div', { text: l })) : []));
      }
    }
  }

  /* ---- panel pages (HTML in the panel's main area; content stays at panel x <= 1272, y < 648) ---- */

  /** Team page: one role card per member (name / role / sections presented).
   *  teamCards(ctx, {x 48, y 96, w 1176, members [0..3], lines [third line per member]})
   *  -> { el, cards, update({opacity, focus: index|null, outline 0..1, others 0..1}) } (use M3_focus for outline/others) */
  function teamCards(ctx, o = {}) {
    const x = o.x != null ? o.x : GRID.fig.left, y = o.y != null ? o.y : 96, w = o.w != null ? o.w : GRID.fig.main.w - 2 * GRID.fig.left;
    const list = o.members || [0, 1, 2, 3];
    const el = h('div', { class: 'kit-team', style: { left: x + 'px', top: y + 'px', width: w + 'px' } });
    const cards = list.map((i, k) => {
      const m = member(i);
      const third = o.lines && o.lines[k] != null ? o.lines[k] : m.presents;
      const card = h('div', { class: 'kit-rolecard' }, [
        h('div', { class: 'kit-rolecard-name', text: m.name }),
        h('div', { class: 'kit-rolecard-role', text: m.role || '' }),
        third ? h('div', { class: 'kit-rolecard-line', text: names(third, i) }) : null,
      ]);
      el.append(card);
      return { el: card, index: i };
    });
    ctx.ui.figHTML.append(el);
    return {
      el, cards,
      update(u = {}) {
        op(el, u.opacity == null ? 1 : u.opacity);
        cards.forEach((c) => {
          const focused = u.focus != null && c.index === u.focus;
          c.el.style.outlineWidth = focused ? (2 * (u.outline == null ? 1 : u.outline)).toFixed(2) + 'px' : '0px';
          c.el.style.opacity = String(u.focus == null || focused ? 1 : (u.others == null ? T.M3.dim : u.others));
        });
      },
    };
  }

  /** Block-start page: "Presented by <Name> · <role>" (56 px serif), "Owns: ..." (28 px, 60 % ink),
   *  then one row per section this member presents: {name, topics}.
   *  blockStart(ctx, {member (default speaker), owns, sections: [{name, topics}]})
   *  -> { update({head, owns, rows}) } opacities 0..1 (M12 fades: head at the name, rows at the role). */
  function blockStart(ctx, o = {}) {
    const i = o.member != null ? o.member : STATE.speaker, m = member(i), x = GRID.fig.left, maxW = GRID.fig.main.w - x;
    const head = h('div', { class: 'kit-bs-head', text: names(o.head || 'Presented by <Name> · {role}', i), style: { left: x + 'px', top: '64px' } });
    const owns = h('div', { class: 'kit-bs-owns', text: 'Owns: ' + names(o.owns || m.owns || '', i), style: { left: x + 'px', top: '146px' } });
    const rows = (o.sections || []).map((s, k) => {
      const r = h('div', { class: 'kit-bs-row', style: { left: x + 'px', top: (226 + k * 56) + 'px' } });
      r.append(h('b', { text: names(s.name, i) }));
      if (s.topics) r.append(document.createTextNode(':  ' + names(s.topics, i)));
      return r;
    });
    ctx.ui.figHTML.append(head, owns, ...rows);
    const fit = () => {   // shrink the head line to the main area (long names)
      const k = scaleK(ctx.ui), w = head.getBoundingClientRect().width / k;
      if (w > maxW) head.style.fontSize = Math.max(40, Math.floor(56 * maxW / w)) + 'px';
    };
    ctx.ui.afterMeasure.push(fit);
    return {
      head, owns, rows,
      update(u = {}) {
        op(head, u.head == null ? 1 : u.head);
        op(owns, u.owns == null ? (u.head == null ? 1 : u.head) : u.owns);
        rows.forEach((r, k) => op(r, Array.isArray(u.rows) ? u.rows[k] : (u.rows == null ? 1 : u.rows)));
      },
    };
  }

  /** Reflection page ("Most unexpected finding"): one 40 px serif sentence (wraps, <= 2 lines),
   *  a small figure below (svg group in box {x 48, y 200, w 1176, h <= 380}), a 60 % ink hand-off line.
   *  reflection(ctx, {line, handoff, figureHeight})
   *  -> { g (svg group, translated to the box), box, update({line, figure, handoff}) } */
  function reflection(ctx, o = {}) {
    const x = GRID.fig.left, w = GRID.fig.main.w - 2 * x;
    const line = h('div', { class: 'kit-refl-line', text: names(o.line || ''), style: { left: x + 'px', top: '40px', width: w + 'px' } });
    const hand = o.handoff ? h('div', { class: 'kit-refl-handoff', text: names(o.handoff), style: { left: x + 'px', top: '596px' } }) : null;
    ctx.ui.figHTML.append(line);
    if (hand) ctx.ui.figHTML.append(hand);
    const box = { x, y: 200, w, h: Math.min(o.figureHeight || 380, 380) };
    const g = svg('g', { transform: `translate(${box.x},${box.y})` }, ctx.fig);
    return {
      line, handoff: hand, g, box,
      update(u = {}) { op(line, u.line == null ? 1 : u.line); op(g, u.figure == null ? 1 : u.figure); if (hand) op(hand, u.handoff == null ? 1 : u.handoff); },
    };
  }

  /** Progress-bar geometry for scenes that animate into it (agenda route -> bar):
   *  [{n, label, x, y, w}] in stage px (valid after setup; measured from the real labels). */
  function progressSegments(ctx) {
    const segs = ctx.ui.progress ? ctx.ui.progress.segs : [];
    return segs.map((s) => ({ n: s.n, label: s.label, x: s.x, y: s.y, w: s.w }));
  }

  /* ------------------------------------------------------------------ *
   * 9. Fonts, data, scene runner, preview controller, audit
   * ------------------------------------------------------------------ */
  const FONT_FAMILIES = ['Source Serif 4', 'IBM Plex Sans', 'IBM Plex Mono'];
  async function loadFonts(timeoutMs = 10000) {
    if (document.readyState !== 'complete') await new Promise((r) => addEventListener('load', r, { once: true }));
    const specs = ['600 64px "Source Serif 4"', '400 40px "Source Serif 4"', '400 34px "IBM Plex Sans"', '500 34px "IBM Plex Sans"',
      '600 34px "IBM Plex Sans"', '400 28px "IBM Plex Mono"', '500 28px "IBM Plex Mono"'];
    try {
      await Promise.race([Promise.all(specs.map((s) => document.fonts.load(s, '0123456789 Aa−'))), new Promise((r) => setTimeout(r, timeoutMs))]);
      await document.fonts.ready;
    } catch (e) { /* fall back to the stack */ }
    const loaded = new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family.replace(/["']/g, '')));
    const missing = FONT_FAMILIES.filter((f) => !loaded.has(f));
    if (missing.length) console.warn('Fonts not loaded, using fallback stack for: ' + missing.join(', '));
    return { ok: missing.length === 0, missing };
  }

  async function loadJSON(url, optional = false) {
    let res;
    try { res = await fetch(url, { cache: 'no-store' }); } catch (e) {
      if (optional) return null;
      throw new Error(`Cannot load ${url}. Browsers block fetch() on file:// pages: run "node video/render/serve.mjs" and open the scene over http.`);
    }
    if (!res.ok) { if (optional) return null; throw new Error(`Cannot load ${url}: HTTP ${res.status}`); }
    return res.json();
  }

  /** Read a value by trying several dotted paths (first hit wins). Throws if none exists. */
  function pick(data, ...paths) {
    for (const p of paths) {
      if (data && Object.prototype.hasOwnProperty.call(data, p)) return data[p];
      let cur = data, ok = true;
      for (const seg of p.split('.')) {
        if (cur != null && Object.prototype.hasOwnProperty.call(cur, seg)) cur = cur[seg]; else { ok = false; break; }
      }
      if (ok && cur !== undefined) return cur;
    }
    throw new Error('Data key not found: ' + paths.join(' | '));
  }

  /** Schema of video/data/*.json (written by video/data/build_data.py):
   *  { _meta, items: {id: {value, label, display, ...}}, intervals: {id: {est, lo, hi, display, label}}, groups }
   *  item(data, id) -> the item object (throws if missing). Use .value for geometry, .display for text. */
  function item(data, id) {
    const it = data && data.items && data.items[id];
    if (!it) throw new Error('Data item not found: ' + id + (data && data._meta ? ' in ' + data._meta.file : ''));
    return it;
  }
  const val = (data, id) => item(data, id).value;
  const disp = (data, id) => item(data, id).display;
  /** interval(data, id) -> {est, lo, hi (values), display, bracket "[lo, hi]", label} */
  function interval(data, id) {
    const iv = data && data.intervals && data.intervals[id];
    if (!iv) throw new Error('Data interval not found: ' + id);
    const lo = item(data, iv.lo), hi = item(data, iv.hi), est = item(data, iv.est);
    return { est: est.value, lo: lo.value, hi: hi.value, display: iv.display, label: iv.label,
      estDisplay: est.display, bracket: '[' + lo.display + ', ' + hi.display + ']' };
  }

  /** createScene(cfg) — the one entry point.
   *  cfg: { number (timeline scene n), name, duration (default: timeline), speaker (member index; default: timeline),
   *         section (default: timeline),
   *         title, subtitle, credit, pointer, page   — or phases: [{at, title, subtitle, credit, pointer, page}]
   *         page 'evidence' | 'blockstart' | 'reflection' | 'agenda' | 'closing' | 'team'  (blockstart hides the pointer)
   *         progress true | false | {at, dur}  (scene 01: false; scene 02: {at: <end of the route morph>})
   *         cards [{type: 'title'|'chapter'|'closing', at, until|dur, ...}], legendMoment {key, at, hold},
   *         legend [keys] | false, grid (motif, default true), titleFadeIn (s), nametag {line1, line2},
   *         auditAllow [regex | string] (texts exempt from the code / letter checks),
   *         data 'path.json', cues {name: seconds | 'phrase' | ['phrase', offset] | {phrase, offset, end, nth}} | (Kit) => {...},
   *         setup(ctx), render(t, ctx) }
   *  ctx: { fig, defs, figHTML, W, H, data, cues, ui, Kit, stage, info (timeline scene), speaker } */
  function createScene(cfg) {
    const params = new URLSearchParams(location.search);
    const scene = {
      number: cfg.number, name: cfg.name, duration: cfg.duration, fps: FPS,
      cues: {}, ready: false, t: 0,
      seek() { /* replaced once ready */ }, audit: () => [],
    };
    global.SCENE = scene;

    const viewport = h('div', { class: 'kit-viewport' });
    const scaler = h('div', { class: 'kit-scaler' });
    const stage = h('div', { class: 'kit-stage' });
    scaler.append(stage); viewport.append(scaler);
    const fit = () => { const k = Math.min(innerWidth / GRID.W, innerHeight / GRID.H); scaler.style.transform = k === 1 ? 'none' : `scale(${k})`; };

    global.SCENE_READY = (async () => {
      if (document.readyState === 'loading') await new Promise((r) => document.addEventListener('DOMContentLoaded', r, { once: true }));
      document.body.append(viewport);
      fit(); addEventListener('resize', fit);
      const base = cfg.paths || {};
      const [fonts, tl, team, wordsJSON, caps] = await Promise.all([
        loadFonts(),
        loadJSON(base.timeline || '../timeline/timeline.json'),
        loadJSON(base.team || '../data/team_names.json', true),
        loadJSON(base.words || '../subtitles/words.json', true),
        params.get('captions') === '1' || params.get('captions') === 'outline' ? loadJSON(base.captions || '../subtitles/captions.json', true) : null,
      ]);
      STATE.timeline = indexTimeline(tl);
      STATE.team = team || { group: '[no.]', members: [] };
      STATE.words = wordsJSON;
      STATE.captions = caps;
      STATE.captionsOutline = params.get('captions') === 'outline';
      STATE.scene = cfg.number;
      const info = sceneInfo(cfg.number);
      if (!info) console.warn(`scene ${cfg.number} is not in timeline.json: no progress fill, speaker from cfg`);
      const spk = memberIndex(cfg.speaker);
      STATE.speaker = spk != null ? spk : (info ? info.speaker : 0);
      if (cfg.duration == null) cfg.duration = info ? info.duration : 10;
      scene.duration = cfg.duration;
      if (info && Math.abs(info.duration - cfg.duration) > 1e-6) scene.durationMismatch = `duration ${cfg.duration} s differs from timeline.json (${info.duration} s)`;
      const cueSrc = typeof cfg.cues === 'function' ? cfg.cues(Kit) : cfg.cues;
      Object.assign(scene.cues, resolveCues(cueSrc));

      const ui = buildChrome(cfg, stage);
      ui.afterMeasure = [];
      const data = cfg.data ? await loadJSON(cfg.data) : null;
      const ctx = { fig: ui.fig, defs: ui.defs, figHTML: ui.figHTML, W: GRID.panel.w, H: GRID.panel.h, data, cues: scene.cues,
        ui, Kit, stage, info, speaker: STATE.speaker };
      if (cfg.setup) cfg.setup(ctx);
      measureChrome(cfg, ui);
      ui.afterMeasure.forEach((f) => f());
      scene.seek = function (t) {
        t = clamp(+t || 0, 0, cfg.duration);
        scene.t = t;
        updateChrome(t, cfg, ui);
        if (cfg.render) cfg.render(t, ctx);
        return t;
      };
      scene.audit = () => audit(stage, cfg, ui, scene);
      scene.fonts = fonts;
      scene.ready = true;
      startPreview(scene, params);
      return { duration: cfg.duration, number: cfg.number, fontsOK: fonts.ok, fontsMissing: fonts.missing };
    })().catch((err) => {
      console.error(err);
      if (!viewport.isConnected) document.body.append(viewport);
      stage.append(h('div', { class: 'kit-error', text: String(err.message || err) }));
      throw err;
    });
    return scene;
  }

  function startPreview(scene, params) {
    const D = scene.duration;
    if (params.get('render') === '1') { scene.seek(0); return; }
    const reduce = global.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    let t = params.has('t') ? clamp(parseFloat(params.get('t')) || 0, 0, D) : 0;
    let playing = params.get('play') === '1', stopAt = D, last = null;
    if (params.get('static') === '1' || (reduce && !playing && !params.has('t'))) { t = D; playing = false; }
    const hud = params.get('hud') === '0' ? null : h('div', { class: 'kit-hud' });
    if (hud) document.body.append(hud);
    const cueTimes = () => [...new Set(Object.values(scene.cues).flat().filter((v) => typeof v === 'number'))].sort((a, b) => a - b);
    const info = sceneInfo(scene.number);
    const mmss = (s) => Math.floor(s / 60) + ':' + (s % 60).toFixed(1).padStart(4, '0');
    const draw = () => {
      scene.seek(t);
      if (hud) hud.textContent = `scene ${scene.number ?? ''} · ${t.toFixed(2)} / ${D.toFixed(2)} s${info ? ' · film ' + mmss(info.start + t) : ''} · frame ${Math.round(t * FPS)} · ${playing ? 'playing' : 'paused'} · Space N/P ←/→`;
    };
    const loop = (now) => {
      if (!playing) { last = null; return; }
      if (last != null) t = Math.min(stopAt, t + (now - last) / 1000);
      last = now;
      if (t >= stopAt) { t = stopAt; playing = false; }
      draw();
      if (playing) requestAnimationFrame(loop);
    };
    const play = (until = D) => { if (t >= D) t = 0; stopAt = until; playing = true; last = null; requestAnimationFrame(loop); };
    addEventListener('keydown', (e) => {
      const k = e.key, step = e.shiftKey ? 1 / FPS : 1;
      if (k === ' ') { e.preventDefault(); if (playing) playing = false; else play(); }
      else if (k === 'ArrowRight') { playing = false; t = Math.min(D, t + step); }
      else if (k === 'ArrowLeft') { playing = false; t = Math.max(0, t - step); }
      else if (k === 'Home') { playing = false; t = 0; }
      else if (k === 'End') { playing = false; t = D; }
      else if (k === 'n' || k === 'N' || k === 'PageDown') {
        const c = cueTimes(), cur = c.filter((v) => v <= t + 1e-3).pop();
        const next = c.find((v) => v > t + 1e-3);
        if (cur == null && next != null) { t = next; }
        play(c.find((v) => v > Math.max(t, next ?? t) + 1e-3) ?? D);
        return;
      } else if (k === 'p' || k === 'P' || k === 'PageUp') { playing = false; const c = cueTimes().filter((v) => v < t - 1e-3); t = c.length ? c[c.length - 1] : 0; }
      else if (k === 'h' && hud) { hud.style.display = hud.style.display === 'none' ? '' : 'none'; return; }
      else return;
      draw();
    });
    draw();
    if (playing) play();
  }

  /* ---- audit ---- */
  const CODE_RE = /(^|[^\w-])(M0|M1|E-ALL|E-SCREEN|P\d{2}|B[1-6]|S-B6a|Trap|trap|S7_\w*|S10_\w*)(?![\w])/;
  const CODE_ALLOW = ['notebook: M0 · M1 · S'];
  /** Letter codes for people (A-D must never be rendered). Returns a reason or null. */
  function letterCode(text) {
    const s = text.trim();
    if (/^[A-D]$/.test(s)) return 'bare letter';
    if (/<\s*[A-D]\s*>/.test(s)) return '<letter>';
    if (/(^|[^\w])[A-D]['’]s(?!\w)/.test(s)) return "letter's";
    const bcd = /(^|[^\w'’-])([BCD])(?=$|[^\w'’-])/g;
    let m;
    while ((m = bcd.exec(s))) {
      const before = s.slice(0, m.index + m[1].length);
      if (!/(vitamin|hepatitis)\s*$/i.test(before)) return 'standalone ' + m[2];
    }
    const re = /(^|[^\w])(member|by|presented by|led by|speaker|from|for|with|and|to|next:?)\s+(A)(?=$|[^\w-])/gi;
    while ((m = re.exec(s))) {
      if (m[3] !== 'A') continue;
      const after = s.slice(m.index + m[0].length);
      if (!/^\s+[a-z]/.test(after)) return 'person letter A';
    }
    if (/(^|\s)A(?=\s*[·→|,;:)]|\s*$)/.test(s) && s.length > 1) return 'letter A as a label';
    return null;
  }
  const rectsHit = (r, z) => Math.min(r.x + r.w, z.x + z.w) - Math.max(r.x, z.x) > 0.5 && Math.min(r.y + r.h, z.y + z.h) - Math.max(r.y, z.y) > 0.5;

  /** audit() — checks the current frame. Returns a list of strings.
   *  · text < 28 px (24 px allowed only in the progress bar, legend row, pointer, .kit-t-foot, card source)
   *  · overlapping text; figure text outside the panel; anything off stage
   *  · any figure or card content in the PiP keep-out (incl. name tag) or in the caption zone
   *  · title wider than 1728 px; subtitle running into the credit
   *  · "§" anywhere; internal codes (M0, E-SCREEN, P03, Trap, ...); person letter codes A-D
   *  · the structure indigo anywhere outside the progress bar
   *  · duration different from timeline.json */
  function audit(stage, cfg, ui, scene) {
    const issues = [];
    const isVisible = (el) => {
      for (let e = el; e && e !== stage.parentElement; e = e.parentElement || e.parentNode) {
        if (!(e instanceof Element)) break;
        const cs = getComputedStyle(e);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.02) return false;
      }
      return true;
    };
    if (scene.durationMismatch) issues.push(scene.durationMismatch);
    const allow = (cfg.auditAllow || []).map((a) => (a instanceof RegExp ? a : new RegExp('^' + String(a).replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$')));
    const allowed = (txt) => CODE_ALLOW.includes(txt) || allow.some((re) => re.test(txt));
    const all = [...stage.querySelectorAll('*')].filter((e) => !e.closest('.kit-hud, .kit-captions, defs, pattern, mask, .kit-motif'));
    const textEls = all.filter((e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) && isVisible(e));
    const boxes = textEls.map((e) => ({ e, r: stageRect(e, stage), label: e.textContent.trim().slice(0, 40) }));
    const cardOnTop = ui.cardOn;

    // text size
    boxes.forEach(({ e, label }) => {
      const fs = parseFloat(getComputedStyle(e).fontSize);
      const small = e.closest('.kit-progress, .kit-legendrow, .kit-pointer, .kit-card-source, .kit-card-route') || e.matches('.kit-t-foot') || e.closest('.kit-t-foot');
      const floor = small ? 24 : 28;
      if (fs < floor - 0.01) issues.push(`font ${fs}px < ${floor}px: "${label}"`);
    });
    // overlapping text (skip pairs where a full-frame card covers one of them)
    const covered = (e) => cardOnTop && !e.closest('.kit-card, .kit-nametag, .kit-progress');
    const vis = boxes.filter((b) => !covered(b.e));
    for (let i = 0; i < vis.length; i++) {
      for (let j = i + 1; j < vis.length; j++) {
        const a = vis[i], b = vis[j];
        if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
        const ox = Math.min(a.r.x + a.r.w, b.r.x + b.r.w) - Math.max(a.r.x, b.r.x);
        const oy = Math.min(a.r.y + a.r.h, b.r.y + b.r.h) - Math.max(a.r.y, b.r.y);
        if (ox > 1 && oy > 1 && ox * oy > 6) issues.push(`overlap: "${a.label}" x "${b.label}" (${Math.round(ox)}x${Math.round(oy)} px)`);
      }
    }
    // figure text outside the panel; off stage
    const P = GRID.panel;
    boxes.filter((b) => b.e.closest('.kit-figure, .kit-figure-html')).forEach(({ r, label }) => {
      if (r.x < P.x - 0.5 || r.y < P.y - 0.5 || r.x + r.w > P.x + P.w + 0.5 || r.y + r.h > P.y + P.h + 0.5) issues.push(`outside panel: "${label}"`);
    });
    boxes.forEach(({ r, label }) => { if (r.x < -0.5 || r.y < -0.5 || r.x + r.w > GRID.W + 0.5 || r.y + r.h > GRID.H + 0.5) issues.push(`off stage: "${label}"`); });
    // keep-out (PiP + name tag) and caption zone: no figure content, no card text
    if (!cardOnTop || true) {
      const zones = [['PiP keep-out', GRID.keepOut], ['caption zone', GRID.captions]];
      const LEAF = 'text, rect, line, path, circle, ellipse, polygon, polyline, image, use';
      const content = [];
      if (!cardOnTop) {
        ui.fig.querySelectorAll(LEAF).forEach((e) => { if (!e.closest('defs, pattern, mask, clipPath, text text') && isVisible(e)) content.push(e); });
        ui.figHTML.querySelectorAll('*').forEach((e) => { if (isVisible(e)) content.push(e); });
      }
      ui.cards.forEach((c) => { if (parseFloat(c.el.style.opacity || '0') > 0.02 && c.el.style.visibility !== 'hidden') c.el.querySelectorAll('*').forEach((e) => content.push(e)); });
      if (ui.chip && isVisible(ui.chip)) content.push(ui.chip);
      zones.forEach(([nm, z]) => {
        const hits = [];
        content.forEach((e) => {
          const r = stageRect(e, stage);
          if (r.w < 0.5 && r.h < 0.5) return;
          if (rectsHit(r, z)) hits.push((e.textContent || '').trim().slice(0, 24) || '<' + e.tagName.toLowerCase() + '>');
        });
        if (hits.length) issues.push(`${hits.length} element(s) in the ${nm}: ${[...new Set(hits)].slice(0, 4).join(', ')}`);
      });
    }
    // title width; subtitle vs credit
    ui.runs.title.forEach((r) => { if (r.el && isVisible(r.el) && r.el.getBoundingClientRect().width / scaleK(ui) > GRID.title.w + 0.5) issues.push(`title wider than 1728 px: "${r.text}"`); });
    ui.runs.subtitle.forEach((r) => {
      if (!r.el || !isVisible(r.el)) return;
      const sw = stageRect(r.el, stage);
      ui.runs.credit.forEach((c) => {
        if (c.el && isVisible(c.el) && sw.x + sw.w > stageRect(c.el, stage).x - 48 + 0.5) issues.push(`subtitle runs into the credit (needs 48 px): "${r.text}"`);
      });
      if (sw.w > GRID.subtitle.w + 0.5) issues.push(`subtitle wider than 1728 px: "${r.text}"`);
    });
    // words: §, internal codes, person letter codes
    boxes.forEach(({ e, label }) => {
      if (covered(e)) return;
      const txt = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join('').trim();
      if (!txt || allowed(txt)) return;
      if (txt.includes('§')) issues.push(`"§" on screen: "${label}"`);
      const cm = CODE_RE.exec(txt);
      if (cm) issues.push(`internal code "${cm[2]}" on screen: "${label}"`);
      const lc = letterCode(txt);
      if (lc) issues.push(`member letter code (${lc}) on screen: "${label}" — use <Name:i> / Kit.name(i)`);
    });
    // structure indigo outside the progress bar
    const probe = h('div', { style: { color: 'var(--structure)', display: 'none' } });
    stage.append(probe);
    const indigo = getComputedStyle(probe).color;
    probe.remove();
    const indigoHits = [];
    all.forEach((e) => {
      if (e.closest('.kit-progress') || !isVisible(e) || covered(e)) return;
      const cs = getComputedStyle(e);
      const props = [cs.backgroundColor];
      if (e instanceof SVGElement) props.push(cs.fill, cs.stroke);
      if ([...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) props.push(cs.color);
      if (parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderLeftWidth) > 0) props.push(cs.borderTopColor, cs.borderLeftColor);
      if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) props.push(cs.outlineColor);
      if (props.includes(indigo)) indigoHits.push(e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : ''));
    });
    if (indigoHits.length) issues.push(`structure indigo outside the progress bar (${indigoHits.length}): ${[...new Set(indigoHits)].slice(0, 4).join(', ')}`);
    // name tag shrunk below 28 px
    [ui.nametagName, ui.nametagRole].forEach((el) => { const fs = parseFloat(el.style.fontSize || '28'); if (fs < 28) issues.push(`name tag text shrunk to ${fs}px to fit: "${el.textContent}" (use a shorter video_name in team.json)`); });
    if (ui.legendRow && ui.bottom && ui.legendRow.getBoundingClientRect().right > ui.pointer.getBoundingClientRect().left - 24 && ui.pointer.textContent) issues.push('legend row runs into the notebook pointer');
    return [...new Set(issues)];
  }

  /* ------------------------------------------------------------------ */
  const Kit = {
    GRID, C, T, LEGEND, FPS, PLACEHOLDER,
    get TIMELINE() { return STATE.timeline; },
    get TEAM() { return STATE.team; },
    get SPEAKER() { return STATE.speaker; },
    ease, cubicBezier, progress, tween, appear, clamp, lerp, mixColor, fmt, fmtInterval,
    M1_axisDraw, M2_barGrow, M3_focus, M4_whiskerBand, M4_static, M5_funnel, M6_morph, M7_strike,
    M8_valueChange, M9_pushIn, M10_count, M11_arrow, M12_dissolve, M12_chapterCard,
    h, svg, text, op, textWidth, icon, iconSVG, warnTriangle, swatchSVG, hatchPattern, feedback,
    scaleLinear, axis, bar, dotWhisker, sesoiBand, callout, strike, focusRing, arrow, radiusForArea,
    pick, item, val, disp, interval, loadJSON, createScene,
    name, names, member, sceneInfo, words, cueAt, resolveCues, letterCode,
    teamCards, blockStart, reflection, progressSegments, stageRect,
  };
  global.Kit = Kit;
})(window);
