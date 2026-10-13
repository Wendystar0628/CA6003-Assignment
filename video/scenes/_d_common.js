/* Shared helpers for scenes 19-28 (C's last scenes and D's segment). Files starting with "_" are never rendered.
   Everything here is geometry or plumbing; no number is typed in a scene. */
const DC = (function () {
  const K = Kit;

  /** Synchronous JSON read for a second data file (createScene loads only one). */
  function loadSync(url) {
    const x = new XMLHttpRequest();
    x.open('GET', url, false);
    x.send();
    if (x.status !== 200) throw new Error('Cannot load ' + url + ' (HTTP ' + x.status + ')');
    return JSON.parse(x.responseText);
  }

  /** Paper-coloured halo behind SVG text so it stays legible over lines and gridlines. */
  function halo(el, w = 9) {
    Object.assign(el.style, { paintOrder: 'stroke', stroke: '#fff', strokeWidth: w + 'px', strokeLinejoin: 'round' });
    return el;
  }

  /** Replace the text of title i (so titles that contain numbers come from the data files). */
  function setTitle(ctx, i, text) { ctx.ui.titles[i].el.textContent = text; }

  /** Signed number text from a stored value, with the typographic minus. */
  const signed = (v, d = 3) => K.fmt(v, d, { sign: true });

  /** The shared AUC-difference axis of scenes 21 and 24 (same scale, same band, same rows).
   *  Axis from prep_band.axis_min .. axis_max, ±SESOI band from prep_band.sesoi. */
  function diffAxis(parent, data, o = {}) {
    const lo = K.val(data, 'axis_min'), hi = K.val(data, 'axis_max'), sesoi = K.val(data, 'sesoi');
    const G = { x0: 110, x1: 900, band: [330, 520], at: 548 };
    const x = K.scaleLinear([lo, hi], [G.x0, G.x1]);
    const ax = K.axis(parent, x, {
      orient: 'bottom', at: G.at, ticks: [lo, lo / 2, 0, hi / 2, hi],
      format: (v) => (v === 0 ? '0.00' : K.fmt(v, 2, { sign: true })),
    });
    const band = K.sesoiBand(parent, x, { lo: -sesoi, hi: sesoi, from: G.band[0], to: G.band[1] });
    const zero = K.svg('line', { x1: x(0), x2: x(0), y1: G.band[0], y2: G.at, stroke: K.mixColor(K.C.ink, '#ffffff', 0.55), 'stroke-width': 2 }, parent);   // 0 = no change
    const title = K.text(parent, { x: (G.x0 + G.x1) / 2, y: G.at + 98, text: o.title || '', anchor: 'middle', cls: 'kit-t-min' });
    return { x, ax, band, zero, title, G, sesoi };
  }

  /** Layout S bottom bar is only 816 px wide and the full legend row overflows it (kit audit "off stage").
   *  Keep only the legend items this scene uses. keep: array of LEGEND keys. */
  function fitLegend(ctx, keep) {
    const items = ctx.ui.legendItems || {};
    Object.keys(items).forEach((k) => { if (!keep.includes(k)) items[k].remove(); });
  }

  /** Full-screen camera phase (layout F, §6.3) inside a scene authored in layout R:
   *  between `from` and `to` only the camera (full frame) and the lower-third remain; everything else is hidden.
   *  Call from setup (prepare) and from render (apply). With --alpha the stage is transparent, so the portrait shows through. */
  function cameraPhase(ctx) {
    const ui = ctx.ui, keep = [ui.camera, ui.lowerThird, ui.card].filter(Boolean);
    const rect = { left: ui.camera.style.left, top: ui.camera.style.top, width: ui.camera.style.width, height: ui.camera.style.height };
    const others = [...ui.stage.children].filter((e) => !keep.includes(e) && e !== ui.attrib);
    if (ui.lowerThird) Object.assign(ui.lowerThird.style, { left: '96px', top: '820px', width: 'auto' });   // F position (§6.3)
    return {
      apply(t, from, to) {
        const inF = t >= from && t < to;
        others.forEach((e) => { e.style.display = inF ? 'none' : ''; });
        if (ui.attrib) ui.attrib.style.display = inF ? 'none' : '';
        Object.assign(ui.camera.style, inF ? { left: '0px', top: '0px', width: '1920px', height: '1080px' } : rect);
        return inF;
      },
    };
  }

  /** M3-like focus on a group: opacity helper (others dim to 25 %). */
  const dimTo = (a) => K.lerp(1, 0.25, K.clamp(a));

  return { loadSync, halo, setTitle, signed, diffAxis, dimTo, fitLegend, cameraPhase };
})();
