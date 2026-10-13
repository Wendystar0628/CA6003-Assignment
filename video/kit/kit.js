/* =====================================================================
   CA6003 explainer video · scene kit (dependency-free)
   Spec: docs/video_plan.md §6 (visual system), §7 (signature visuals), §8 (pipeline).

   Contract
   --------
   A scene calls Kit.createScene({...}). The kit registers
       window.SCENE = { duration, layout, number, cues, seek(t), audit(), ready }
       window.SCENE_READY  (Promise -> {duration, layout, fontsOK})
   seek(t) renders the exact state at time t as a pure function of t: no CSS
   transitions, no timers, no randomness. Live preview drives seek() from
   requestAnimationFrame; the renderer calls seek(i / fps) for every frame.

   URL parameters:  ?t=12.3   seek to a time and hold
                    ?play=1   autoplay (from ?t or 0)
                    ?static=1 render the final frame (reduced motion)
                    ?render=1 renderer mode (no HUD, no keyboard, no autoplay)
                    ?hud=0    hide the preview HUD
                    ?alpha=1  transparent camera slot (render.mjs --alpha, for compositing)
   Preview keys:    Space play/pause · ←/→ ±1 s (Shift: ±1 frame)
                    N / PageDown next cue step · P / PageUp previous · Home / End
   ===================================================================== */
(function (global) {
  'use strict';

  const SVGNS = 'http://www.w3.org/2000/svg';
  const FPS = 30;

  /* ------------------------------------------------------------------ *
   * 1. Geometry (mirrors tokens.css) and §6 constants
   * ------------------------------------------------------------------ */
  const GRID = {
    W: 1920, H: 1080, marginX: 96, marginY: 60, gutter: 24,
    title: { x: 96, y: 60, w: 1728, h: 90 },
    figure: { y: 168, h: 792 },                 // figure area y 168-960
    bottom: { x: 96, y: 984, w: 1728, h: 36 },  // bottom bar y 984-1020
    rightCol: { x: 1344, y: 168, w: 480, h: 792 },
    camera: {                                   // camera slot, per layout
      R: { x: 1344, y: 168, w: 480, h: 270 },
      X: { x: 1344, y: 690, w: 480, h: 270 },   // bottom-right safe area of the figure
      S: { x: 0, y: 0, w: 960, h: 1080 },       // portrait half, 8:9 crop
      F: { x: 0, y: 0, w: 1920, h: 1080 },
    },
    panel: {                                    // paper panel (layer 2) per layout
      R: { x: 96, y: 168, w: 1224, h: 792 },    // 1248 px figure column = 1224 panel + 24 gutter
      X: { x: 96, y: 168, w: 1728, h: 792 },    // leave the camera corner empty in the figure
      S: { x: 1008, y: 168, w: 816, h: 792 },
      F: null,
    },
    titleBand: {
      R: { x: 96, w: 1728 }, X: { x: 96, w: 1728 }, S: { x: 1008, w: 816 }, F: null,
    },
  };

  /** Colour roles (§6.2). Read from CSS so tokens.css stays the single source. */
  const C = {};
  ['structure', 'leak', 'leak-tint', 'systematic', 'systematic-tint', 'screen', 'screen-tint',
    'reference', 'ink', 'line', 'band', 'stage', 'paper', 'paper-edge'].forEach((k) => {
    Object.defineProperty(C, k.replace(/-(\w)/g, (_, c) => c.toUpperCase()), {
      enumerable: true,
      get: () => getComputedStyle(document.documentElement).getPropertyValue('--' + k).trim(),
    });
  });

  /** Members (§6.2 badges, lower-third). */
  const SPEAKERS = {
    A: { role: 'Governance & integration', sec: '§0–§2', short: '§0–2' },
    B: { role: 'Data quality & preparation', sec: '§3 §6 §9', short: '§3·6·9' },
    C: { role: 'Exploration, labels & bias', sec: '§4 §5 §8', short: '§4·5·8' },
    D: { role: 'Modelling & conclusions', sec: '§7 §10', short: '§7·10' },
  };

  /** Trap bar cells (§2.2): icon + label; the active one gets the structure underline. */
  const TRAPS = [
    { key: 'leak', label: 'Leak', icon: 'bucket' },
    { key: 'label', label: 'Label', icon: 'ruler' },
    { key: 'gain', label: 'Little gain', icon: 'balance' },
  ];

  /** Legend (§6.2 "legend moment"): first scene of each semantic colour, chip text, row text. */
  const LEGEND = [
    { key: 'reference', first: 3, chip: 'grey = reference: all adults, Minimal (M1)', row: 'reference baseline' },
    { key: 'leak', first: 8, chip: 'red = harmed or leaked data', row: 'harmed or leaked data' },
    { key: 'systematic', first: 12, chip: 'teal = Systematic preparation (S)', row: 'Systematic (S)' },
    { key: 'screen', first: 17, chip: 'blue = Screening group (not yet diagnosed)', row: 'Screening group' },
  ];

  /** Motion timings (§6.4). Every M-helper uses these as defaults. */
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
    appear: 0.3,          // label / interval fade (callout interval: 0.3 s after its number)
    gap: 1.5,             // minimum still time between two actions
    legendHold: 2.5,      // legend chip visible 2-3 s
    legendCollapse: 0.4,  // then folds into the bottom legend row
    lowerThird: 4.0,
  };

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
   * 7. Stage chrome: motif, title band, trap bar, panel, camera slot,
   *    right column (attribution, lower-third, badges), bottom bar,
   *    legend chip, chapter card.
   * ------------------------------------------------------------------ */
  /** Questionnaire / codebook grid (§6.5): 1 px ink lines, rows 24 px, unequal columns,
   *  <= 4 % opacity, only in the outer margins, fading linearly toward the content. Static. */
  function motif() {
    const W = GRID.W, H = GRID.H, id = nextId('kit-motif');
    const cols = [72, 144, 48, 96, 192, 60, 120, 84, 168, 36, 108];
    let xs = [], x = 0, i = 0;
    while (x < W) { xs.push(x); x += cols[i++ % cols.length]; }
    let lines = '';
    for (let y = 0; y <= H; y += 24) lines += `<line x1="0" x2="${W}" y1="${y + 0.5}" y2="${y + 0.5}"/>`;
    xs.forEach((x) => { lines += `<line y1="0" y2="${H}" x1="${x + 0.5}" x2="${x + 0.5}"/>`; });
    const m = GRID.marginX, my = GRID.marginY;
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

  function badgeEl(letter, current, size) {
    const b = h('div', { class: 'kit-badge' + (current ? ' is-current' : ''), text: letter });
    if (size) Object.assign(b.style, { width: size + 'px', height: size + 'px', fontSize: Math.max(28, Math.round(size * 0.52)) + 'px' });
    return b;
  }

  function buildChrome(cfg, stage) {
    const L = cfg.layout;
    const ui = { stage };
    // layer 1: stage colour + motif. In alpha mode the camera rectangle is cut out of it.
    const bg = h('div', { class: 'kit-stagebg' });
    if (cfg.grid !== false) bg.append(motif());
    stage.append(bg);
    if (document.documentElement.classList.contains('kit-alpha')) {
      const c = GRID.camera[L], W = GRID.W, H = GRID.H;
      bg.style.clipPath = `polygon(evenodd, 0 0, ${W}px 0, ${W}px ${H}px, 0 ${H}px, 0 0, ${c.x}px ${c.y}px, ${c.x + c.w}px ${c.y}px, ${c.x + c.w}px ${c.y + c.h}px, ${c.x}px ${c.y + c.h}px, ${c.x}px ${c.y}px)`;
    }

    // --- title band
    const tb = GRID.titleBand[L];
    if (tb && cfg.title !== false) {
      const band = h('div', { class: 'kit-title-band', style: { left: tb.x + 'px', width: tb.w + 'px' } });
      const titles = typeof cfg.title === 'string' ? [{ at: 0, text: cfg.title }] : (cfg.title || []);
      ui.titles = titles.map((tt) => { const e = h('div', { class: 'kit-title', text: tt.text }); band.append(e); return Object.assign({ el: e }, tt); });
      // trap bar (§2.2): from scene 2 to 25, or when cfg.trap names a cell
      const showTrap = cfg.trap === false ? false : (cfg.trap != null || (cfg.number >= 2 && cfg.number <= 25));
      if (showTrap && L !== 'S') {
        const bar = h('div', { class: 'kit-trapbar' });
        TRAPS.forEach((tr) => {
          const cell = h('div', { class: 'kit-trapcell', html: iconSVG(tr.icon, 40, C.ink) });
          cell.append(h('span', { text: tr.label }));
          if (cfg.trap === tr.key) cell.append(h('div', { class: 'kit-trap-rule' }));
          bar.append(cell);
        });
        band.append(bar);
        ui.trapbar = bar;
      }
      if (cfg.attribution) { ui.attrib = h('div', { class: 'kit-attrib', text: cfg.attribution }); band.append(ui.attrib); }
      stage.append(band);
      ui.titleBand = band;
    }

    // --- paper panel + figure SVG
    const P = GRID.panel[L];
    if (P) {
      const panel = h('div', { class: 'kit-panel', style: { left: P.x + 'px', top: P.y + 'px', width: P.w + 'px', height: P.h + 'px' } });
      const fig = svg('svg', { width: P.w, height: P.h, viewBox: `0 0 ${P.w} ${P.h}`, class: 'kit-figure' });
      const defs = svg('defs', {}, fig);
      hatchPattern(defs);
      panel.append(fig);
      stage.append(panel);
      Object.assign(ui, { panel, fig, defs, P });
    }

    // --- camera slot (flat white + hairline border; the camera clip is composited here later)
    const cam = GRID.camera[L];
    ui.camera = h('div', { class: 'kit-camera', style: { left: cam.x + 'px', top: cam.y + 'px', width: cam.w + 'px', height: cam.h + 'px' } });
    stage.append(ui.camera);

    // --- right column: badges (R only unless asked)
    const spk = cfg.speaker;
    if ((cfg.badges != null ? cfg.badges : L === 'R') && spk) {
      const col = h('div', { class: 'kit-rightcol' });
      const row = h('div', { class: 'kit-badges' });
      Object.keys(SPEAKERS).forEach((k) => row.append(h('div', { class: 'kit-badge-cell' }, [badgeEl(k, k === spk), h('div', { class: 'kit-badge-sec', text: SPEAKERS[k].short })])));
      col.append(row);
      stage.append(col);
      ui.badges = row;
    }

    // --- lower-third (only when the scene asks for it)
    if (cfg.lowerThird && spk) {
      const lt = cfg.lowerThird, info = SPEAKERS[spk];
      const el = h('div', { class: 'kit-lowerthird' }, [badgeEl(spk, true), h('div', {}, [
        h('div', { class: 'kit-lt-name', text: lt.name || 'Member ' + spk }),
        h('div', { class: 'kit-lt-role', text: lt.role || info.role }),
        h('div', { class: 'kit-lt-sec', text: lt.sec || info.sec }),
      ])]);
      const pos = { R: { left: 1344, top: 462, width: 480 }, X: { left: 96, top: 820 }, S: { left: 48, top: 860 }, F: { left: 96, top: 820 } }[L];
      Object.assign(el.style, { left: pos.left + 'px', top: pos.top + 'px', width: pos.width ? pos.width + 'px' : 'auto' });
      stage.append(el);
      ui.lowerThird = el;
    }

    // --- bottom bar: source tag (left) + persistent legend row (centre). No animation.
    const BB = L === 'S' ? { x: 1008, w: 816 } : { x: GRID.bottom.x, w: GRID.bottom.w };
    if (L !== 'F') {
      const bar = h('div', { class: 'kit-bottombar', style: { left: BB.x + 'px', width: BB.w + 'px' } });
      ui.source = h('div', { class: 'kit-source', text: cfg.source || '' });
      const row = h('div', { class: 'kit-legendrow' });
      ui.legendItems = {};
      const moment = cfg.legendMoment && cfg.legendMoment.key;
      LEGEND.filter((l) => cfg.number >= l.first || l.key === moment || (cfg.legend || []).includes(l.key)).forEach((l) => {
        const it = h('div', { class: 'kit-legend-item', html: swatchSVG(l.key) });
        it.append(h('span', { text: l.row }));
        row.append(it);
        ui.legendItems[l.key] = it;
      });
      bar.append(ui.source, row);
      stage.append(bar);
      ui.legendRow = row;
    }

    // --- legend chip (first use of a semantic colour): corner of the figure, 2-3 s, folds into the row
    if (cfg.legendMoment) {
      const lm = cfg.legendMoment, def = LEGEND.find((l) => l.key === lm.key);
      const chip = h('div', { class: 'kit-legendchip', html: swatchSVG(lm.key, 32) });
      chip.append(h('span', { text: def.chip }));
      stage.append(chip);
      ui.chip = chip;
    }

    // --- chapter card (on top of everything)
    if (cfg.chapterCard) {
      const cc = cfg.chapterCard;
      const card = h('div', { class: 'kit-chapter' }, [
        h('div', { class: 'kit-chapter-rule' }),
        h('div', { class: 'kit-chapter-title', text: cc.title }),
        h('div', { class: 'kit-chapter-item' }, [h('span', { text: cc.item || '' }), spk ? badgeEl(spk, true, 52) : null]),
      ]);
      stage.append(card);
      ui.card = card;
    }
    return ui;
  }

  /** Stage-coordinate rect of an element (independent of the preview scale). */
  function stageRect(el, stage) {
    const s = stage.getBoundingClientRect(), r = el.getBoundingClientRect(), k = s.width / GRID.W;
    return { x: (r.left - s.left) / k, y: (r.top - s.top) / k, w: r.width / k, h: r.height / k };
  }

  /** Layout passes that need real font metrics (after fonts load). */
  function measureChrome(cfg, ui) {
    // Attribution tag: in the title band right after the widest title (§6.2); if that would
    // run into the trap bar, it moves under the camera in the right column (R layout).
    if (ui.attrib) {
      const tw = Math.max(0, ...ui.titles.map((tt) => tt.el.getBoundingClientRect().width)) / (ui.stage.getBoundingClientRect().width / GRID.W);
      const aw = ui.attrib.getBoundingClientRect().width / (ui.stage.getBoundingClientRect().width / GRID.W);
      const limit = ui.trapbar ? GRID.titleBand[cfg.layout].w - ui.trapbar.getBoundingClientRect().width / (ui.stage.getBoundingClientRect().width / GRID.W) - 32 : GRID.titleBand[cfg.layout].w;
      if (tw + 32 + aw <= limit) {
        Object.assign(ui.attrib.style, { left: tw + 32 + 'px', bottom: '14px' });
      } else if (cfg.layout === 'R') {
        ui.stage.append(ui.attrib);
        const top = GRID.camera.R.y + GRID.camera.R.h + 24 + (ui.lowerThird ? 160 : 0);
        Object.assign(ui.attrib.style, { left: GRID.rightCol.x + 'px', top: top + 'px' });
        ui.attribMoved = true;
      } else {
        Object.assign(ui.attrib.style, { left: tw + 32 + 'px', bottom: '14px' });
        console.warn('attribution tag overlaps the trap bar in layout ' + cfg.layout);
      }
    }
    // Legend chip geometry: start = figure top-right corner, end = its legend-row item.
    if (ui.chip) {
      const P = ui.P || GRID.panel.R, chipW = ui.chip.getBoundingClientRect().width / (ui.stage.getBoundingClientRect().width / GRID.W);
      ui.chipFrom = { x: P.x + P.w - 24 - chipW, y: P.y + 24 };
      const item = ui.legendItems && ui.legendItems[cfg.legendMoment.key];
      ui.chipTo = item ? stageRect(item, ui.stage) : null;
      ui.chipW = chipW;
    }
  }

  function updateChrome(t, cfg, ui) {
    // chapter card: static 1.2 s, then a cut
    if (ui.card) ui.card.style.visibility = M12_chapterCard(t, cfg.chapterCard.at || 0) ? 'visible' : 'hidden';
    // titles: M12 dissolve between consecutive titles
    if (ui.titles && ui.titles.length) {
      ui.titles.forEach((tt, i) => {
        const pin = i === 0 ? 1 : M12_dissolve(t, tt.at);
        const next = ui.titles[i + 1];
        const pout = next ? M12_dissolve(t, next.at) : 0;
        op(tt.el, pin * (1 - pout));
      });
    }
    // lower-third: 4 s from its start, 0.4 s dissolve in and out
    if (ui.lowerThird) {
      const lt = cfg.lowerThird, at = lt.at || 0, dur = lt.dur || T.lowerThird;
      op(ui.lowerThird, M12_dissolve(t, at) * (1 - M12_dissolve(t, at + dur - T.M12.dissolve)));
    }
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
  }

  /* ------------------------------------------------------------------ *
   * 8. Fonts, data, scene runner, preview controller, audit
   * ------------------------------------------------------------------ */
  const FONT_FAMILIES = ['Source Serif 4', 'IBM Plex Sans', 'IBM Plex Mono'];
  async function loadFonts(timeoutMs = 10000) {
    if (document.readyState !== 'complete') await new Promise((r) => addEventListener('load', r, { once: true }));
    const specs = ['600 72px "Source Serif 4"', '400 34px "IBM Plex Sans"', '600 34px "IBM Plex Sans"',
      '400 28px "IBM Plex Mono"', '500 28px "IBM Plex Mono"'];
    try {
      await Promise.race([Promise.all(specs.map((s) => document.fonts.load(s, '0123456789 Aa−'))), new Promise((r) => setTimeout(r, timeoutMs))]);
      await document.fonts.ready;
    } catch (e) { /* fall back to the stack */ }
    const loaded = new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family.replace(/["']/g, '')));
    const missing = FONT_FAMILIES.filter((f) => !loaded.has(f));
    if (missing.length) console.warn('Fonts not loaded, using fallback stack for: ' + missing.join(', '));
    return { ok: missing.length === 0, missing };
  }

  async function loadJSON(url) {
    let res;
    try { res = await fetch(url, { cache: 'no-store' }); } catch (e) {
      throw new Error(`Cannot load ${url}. Browsers block fetch() on file:// pages: run "node video/render/serve.mjs" (or "npx http-server video") and open the scene over http.`);
    }
    if (!res.ok) throw new Error(`Cannot load ${url}: HTTP ${res.status}`);
    return res.json();
  }

  /** Read a value by trying several dotted paths (first hit wins). Throws if none exists,
   *  so a renamed key in the data file fails loudly instead of drawing a wrong number. */
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
   *  cfg: { number, name, duration, layout 'R'|'X'|'S'|'F', speaker 'A'..'D',
   *         title string | [{at, text}], attribution, trap 'leak'|'label'|'gain'|false,
   *         source, grid (motif, default true), chapterCard {at, title, item},
   *         lowerThird {at, dur, name, role, sec}, legendMoment {key, at, hold},
   *         data 'path.json', cues {name: seconds},
   *         setup(ctx), render(t, ctx) }
   *  ctx: { fig, defs, W, H, data, cues, ui, Kit } */
  function createScene(cfg) {
    cfg.layout = cfg.layout || 'R';
    const params = new URLSearchParams(location.search);
    if (params.get('alpha') === '1') document.documentElement.classList.add('kit-alpha');
    const scene = {
      number: cfg.number, name: cfg.name, duration: cfg.duration, layout: cfg.layout, fps: FPS,
      cues: Object.assign({}, cfg.cues || {}), ready: false, t: 0,
      seek() { /* replaced once ready */ }, audit: () => [],
    };
    global.SCENE = scene;

    const viewport = h('div', { class: 'kit-viewport' });
    const scaler = h('div', { class: 'kit-scaler' });
    const stage = h('div', { class: 'kit-stage', 'data-layout': cfg.layout });
    scaler.append(stage); viewport.append(scaler);
    const fit = () => { const k = Math.min(innerWidth / GRID.W, innerHeight / GRID.H); scaler.style.transform = k === 1 ? 'none' : `scale(${k})`; };

    global.SCENE_READY = (async () => {
      if (document.readyState === 'loading') await new Promise((r) => document.addEventListener('DOMContentLoaded', r, { once: true }));
      document.body.append(viewport);
      fit(); addEventListener('resize', fit);
      const fonts = await loadFonts();
      const ui = buildChrome(cfg, stage);
      const data = cfg.data ? await loadJSON(cfg.data) : null;
      const ctx = { fig: ui.fig, defs: ui.defs, W: ui.P ? ui.P.w : 0, H: ui.P ? ui.P.h : 0, data, cues: scene.cues, ui, Kit, stage };
      if (cfg.setup) cfg.setup(ctx);
      measureChrome(cfg, ui);
      scene.seek = function (t) {
        t = clamp(+t || 0, 0, cfg.duration);
        scene.t = t;
        updateChrome(t, cfg, ui);
        if (cfg.render) cfg.render(t, ctx);
        return t;
      };
      scene.audit = () => audit(stage, cfg, ui);
      scene.fonts = fonts;
      scene.ready = true;
      startPreview(scene, params);
      return { duration: cfg.duration, layout: cfg.layout, number: cfg.number, fontsOK: fonts.ok, fontsMissing: fonts.missing };
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
    const draw = () => {
      scene.seek(t);
      if (hud) hud.textContent = `scene ${scene.number ?? ''} · ${t.toFixed(2)} / ${D.toFixed(2)} s · frame ${Math.round(t * FPS)} · ${playing ? 'playing' : 'paused'} · Space N/P ←/→`;
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
        // step mode (fallback presentation, §8.3): play through the next build step and hold
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

  /** audit() — checks the current frame against §6.7 / the grid. Returns a list of strings.
   *  · visible text smaller than 28 px (except the source tag and the legend row)
   *  · visible text boxes that overlap each other
   *  · figure text outside the paper panel; anything over the camera slot */
  function audit(stage, cfg, ui) {
    const issues = [];
    const isVisible = (el) => {
      for (let e = el; e && e !== stage.parentElement; e = e.parentElement || e.parentNode) {
        if (!(e instanceof Element)) break;
        const cs = getComputedStyle(e);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.02) return false;
      }
      return true;
    };
    if (ui.card && ui.card.style.visibility === 'visible') return issues;  // chapter card frame
    const sel = 'text, .kit-title, .kit-attrib, .kit-trapcell span, .kit-badge, .kit-badge-sec, .kit-lt-name, .kit-lt-role, .kit-lt-sec, .kit-source, .kit-legend-item span, .kit-legendchip span';
    const els = [...stage.querySelectorAll(sel)].filter((e) => e.textContent.trim() && isVisible(e));
    const boxes = els.map((e) => ({ e, r: stageRect(e, stage), label: e.textContent.trim().slice(0, 32) }));
    boxes.forEach(({ e, label }) => {
      const fs = parseFloat(getComputedStyle(e).fontSize);
      const small = e.closest('.kit-source, .kit-legendrow');
      if (fs < 28 - 0.01 && !small) issues.push(`font ${fs}px < 28px: "${label}"`);
    });
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i], b = boxes[j];
        if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
        const ox = Math.min(a.r.x + a.r.w, b.r.x + b.r.w) - Math.max(a.r.x, b.r.x);
        const oy = Math.min(a.r.y + a.r.h, b.r.y + b.r.h) - Math.max(a.r.y, b.r.y);
        if (ox > 1 && oy > 1 && ox * oy > 6) issues.push(`overlap: "${a.label}" x "${b.label}" (${Math.round(ox)}x${Math.round(oy)} px)`);
      }
    }
    if (ui.P) {
      const P = ui.P;
      boxes.filter((b) => b.e.closest('.kit-figure')).forEach(({ r, label }) => {
        if (r.x < P.x - 0.5 || r.y < P.y - 0.5 || r.x + r.w > P.x + P.w + 0.5 || r.y + r.h > P.y + P.h + 0.5) issues.push(`outside panel: "${label}"`);
      });
    }
    const cam = GRID.camera[cfg.layout];
    if (cfg.layout === 'R' || cfg.layout === 'X') {
      boxes.forEach(({ r, label }) => {
        const ox = Math.min(r.x + r.w, cam.x + cam.w) - Math.max(r.x, cam.x), oy = Math.min(r.y + r.h, cam.y + cam.h) - Math.max(r.y, cam.y);
        if (ox > 0 && oy > 0) issues.push(`over camera slot: "${label}"`);
      });
    }
    boxes.forEach(({ r, label }) => {
      if (r.x < 0 || r.y < 0 || r.x + r.w > GRID.W || r.y + r.h > GRID.H) issues.push(`off stage: "${label}"`);
    });
    if (ui.legendRow && ui.legendRow.scrollWidth > ui.legendRow.clientWidth + 1) issues.push('legend row overflows the bottom bar');
    if (ui.titles) ui.titles.forEach((tt) => {
      const r = stageRect(tt.el, stage);
      if (ui.trapbar && r.x + r.w > stageRect(ui.trapbar, stage).x - 16) issues.push(`title runs into the trap bar: "${tt.text}"`);
    });
    return issues;
  }

  /* ------------------------------------------------------------------ */
  const Kit = {
    GRID, C, T, SPEAKERS, TRAPS, LEGEND, FPS,
    ease, cubicBezier, progress, tween, appear, clamp, lerp, mixColor, fmt, fmtInterval,
    M1_axisDraw, M2_barGrow, M3_focus, M4_whiskerBand, M4_static, M5_funnel, M6_morph, M7_strike,
    M8_valueChange, M9_pushIn, M10_count, M11_arrow, M12_dissolve, M12_chapterCard,
    h, svg, text, op, textWidth, icon, iconSVG, warnTriangle, swatchSVG, hatchPattern, feedback,
    scaleLinear, axis, bar, dotWhisker, sesoiBand, callout, strike, focusRing, arrow, radiusForArea,
    pick, item, val, disp, interval, loadJSON, createScene,
  };
  global.Kit = Kit;
})(window);
