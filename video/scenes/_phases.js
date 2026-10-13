/* Layout phases inside one scene (docs/video_plan.md §6.3).
   The kit builds the stage chrome once for a single layout (cfg.layout). Some storyboard scenes
   change layout while they run: 01 (S -> R) and 08 (F -> R -> X). This helper re-positions the
   kit's own DOM (panel, camera slot, title band, lower-third, bottom bar, badge column) as a pure
   function of t, so every frame is still deterministic and the kit audit still runs on the last
   frame. It never edits kit files. Files starting with "_" are not rendered as scenes.

   Usage in a scene:
     setup(ctx)  { ctx.PH = Phases.create(ctx, [{ at: 0, layout: 'S' }, { at: 15, layout: 'R' }]); ... }
     render(t,ctx){ const L = ctx.PH.apply(t); ... }
   cfg.layout must be the layout of the LAST phase (the kit builds the badge column, the legend-chip
   geometry and the final-frame audit for it). */
(function (global) {
  'use strict';
  const K = global.Kit, G = K.GRID;
  const LT = { R: { left: 1344, top: 462, width: 480 }, X: { left: 96, top: 820 }, S: { left: 48, top: 860 }, F: { left: 96, top: 820 } };

  function create(ctx, schedule) {
    const ui = ctx.ui, fig = ctx.fig;
    const alpha = document.documentElement.classList.contains('kit-alpha');
    const bg = ui.stage.querySelector('.kit-stagebg');
    const bottom = ui.source ? ui.source.parentElement : null;
    const rightcol = ui.badges ? ui.badges.parentElement : null;
    const sched = schedule.slice().sort((a, b) => a.at - b.at);
    const W = G.W, H = G.H;

    function layoutAt(t) {
      let L = sched[0].layout;
      for (const s of sched) if (t >= s.at - 1e-9) L = s.layout;
      return L;
    }
    function px(v) { return v + 'px'; }

    function apply(t) {
      const L = layoutAt(t), P = G.panel[L], C = G.camera[L], TB = G.titleBand[L];
      if (ui.titleBand) {
        ui.titleBand.style.display = TB ? '' : 'none';
        if (TB) { ui.titleBand.style.left = px(TB.x); ui.titleBand.style.width = px(TB.w); }
        if (ui.trapbar) ui.trapbar.style.display = (L === 'R' || L === 'X') ? '' : 'none';
        if (ui.attrib && ui.attrib.parentElement === ui.titleBand) ui.attrib.style.display = TB ? '' : 'none';
      }
      if (ui.panel) {
        ui.panel.style.display = P ? '' : 'none';
        if (P) {
          Object.assign(ui.panel.style, { left: px(P.x), top: px(P.y), width: px(P.w), height: px(P.h) });
          fig.setAttribute('width', P.w); fig.setAttribute('height', P.h); fig.setAttribute('viewBox', `0 0 ${P.w} ${P.h}`);
        }
      }
      Object.assign(ui.camera.style, { left: px(C.x), top: px(C.y), width: px(C.w), height: px(C.h) });
      if (rightcol) rightcol.style.display = L === 'R' ? '' : 'none';
      if (ui.lowerThird) {
        const p = LT[L];
        Object.assign(ui.lowerThird.style, { left: px(p.left), top: px(p.top), width: p.width ? px(p.width) : 'auto' });
      }
      if (bottom) {
        bottom.style.display = L === 'F' ? 'none' : '';
        if (L === 'S') { bottom.style.left = px(1008); bottom.style.width = px(816); } else { bottom.style.left = px(G.bottom.x); bottom.style.width = px(G.bottom.w); }
      }
      if (alpha && bg) {
        // transparent camera hole follows the layout; F is a fully transparent stage
        bg.style.display = L === 'F' ? 'none' : '';
        bg.style.clipPath = L === 'F' ? '' : `polygon(evenodd, 0 0, ${W}px 0, ${W}px ${H}px, 0 ${H}px, 0 0, ${C.x}px ${C.y}px, ${C.x + C.w}px ${C.y}px, ${C.x + C.w}px ${C.y + C.h}px, ${C.x}px ${C.y + C.h}px, ${C.x}px ${C.y}px)`;
      }
      return L;
    }
    return { apply, layoutAt };
  }

  /** Stage-coordinate rect of a DOM element (independent of the preview scale). */
  function stageRect(el, stage) {
    const s = stage.getBoundingClientRect(), r = el.getBoundingClientRect(), k = s.width / G.W;
    return { x: (r.left - s.left) / k, y: (r.top - s.top) / k, w: r.width / k, h: r.height / k };
  }

  global.Phases = { create, stageRect };
})(window);
