/* Shared geometry for the Label split (signature visual 6), used by scenes 16 and 17.
   Not a scene (the leading "_" keeps it out of the renderer). Loaded with <script src="_label_venn.js">.

   Two circles with areas proportional to n (told by a doctor 819, HbA1c >= 6.5 % 721). The centre distance is solved so the
   lens area is proportional to the stored overlap (569). One dot per person is laid on a hexagonal lattice inside each of the
   three regions (569 both, 250 told only, 152 HbA1c only). Every count comes from video/data/label_split.json. */
(function (global) {
  'use strict';

  function lensArea(r1, r2, d) {
    const a = r1 * r1 * Math.acos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1));
    const b = r2 * r2 * Math.acos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2));
    const c = 0.5 * Math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2));
    return a + b - c;
  }

  /** build(K, data, {cx, cy, R}) -> geometry, region dots and region outlines (all in panel px). */
  function build(K, data, o) {
    const nBoth = K.val(data, 'both'), nSelf = K.val(data, 'self'), nA1c = K.val(data, 'a1c');
    const nOnlySelf = K.val(data, 'self_only'), nOnlyA1c = K.val(data, 'a1c_only');
    const rL = o.R, rR = o.R * K.val(data, 'circle_ratio');        // area ~ n (radius ratio 0.938 is stored)
    const target = (nBoth / nSelf) * Math.PI * rL * rL;
    let lo = Math.abs(rL - rR) + 1e-6, hi = rL + rR - 1e-6;
    for (let i = 0; i < 80; i++) { const mid = (lo + hi) / 2; if (lensArea(rL, rR, mid) > target) lo = mid; else hi = mid; }
    const d = (lo + hi) / 2;
    const width = d + rL + rR;
    const xL = o.cx - width / 2 + rL, xR = xL + d, y = o.cy;
    const x0 = xL + (d * d + rL * rL - rR * rR) / (2 * d), h = Math.sqrt(rL * rL - (x0 - xL) * (x0 - xL));
    const top = [x0, y - h], bot = [x0, y + h];
    const f = (v) => v.toFixed(2);
    // told-only crescent (left) and HbA1c-only crescent (right), as closed outlines
    const pathSelf = `M${f(top[0])} ${f(top[1])} A${f(rL)} ${f(rL)} 0 ${x0 > xL ? 1 : 0} 0 ${f(bot[0])} ${f(bot[1])} A${f(rR)} ${f(rR)} 0 ${x0 > xR ? 1 : 0} 1 ${f(top[0])} ${f(top[1])} Z`;
    const pathA1c = `M${f(bot[0])} ${f(bot[1])} A${f(rR)} ${f(rR)} 0 ${x0 < xR ? 1 : 0} 0 ${f(top[0])} ${f(top[1])} A${f(rL)} ${f(rL)} 0 ${x0 < xL ? 1 : 0} 1 ${f(bot[0])} ${f(bot[1])} Z`;

    const inL = (px, py, m) => Math.hypot(px - xL, py - y) <= rL - m;
    const inR = (px, py, m) => Math.hypot(px - xR, py - y) <= rR - m;
    const outL = (px, py, m) => Math.hypot(px - xL, py - y) >= rL + m;
    const outR = (px, py, m) => Math.hypot(px - xR, py - y) >= rR + m;
    const regions = {
      both: { n: nBoth, test: (px, py, m) => inL(px, py, m) && inR(px, py, m) },
      self: { n: nOnlySelf, test: (px, py, m) => inL(px, py, m) && outR(px, py, m) },
      a1c: { n: nOnlyA1c, test: (px, py, m) => inR(px, py, m) && outL(px, py, m) },
    };
    // largest pitch for which every region holds its n dots; the n points nearest the region centre are kept
    const lattice = (p) => {
      const pts = [], rows = Math.ceil((rL + 20) / (p * 0.866));
      for (let j = -rows; j <= rows; j++) {
        for (let i = -Math.ceil((width + 40) / p); i <= Math.ceil((width + 40) / p); i++) pts.push([o.cx + i * p + (j % 2 ? p / 2 : 0), y + j * p * 0.866]);
      }
      return pts;
    };
    let pitch = 26, chosen = null;
    for (; pitch > 8; pitch -= 0.25) {
      const pts = lattice(pitch), m = pitch * 0.5, res = {};
      let ok = true;
      for (const [k, r] of Object.entries(regions)) {
        const inside = pts.filter(([px, py]) => r.test(px, py, m));
        if (inside.length < r.n) { ok = false; break; }
        const cxr = inside.reduce((s, q) => s + q[0], 0) / inside.length, cyr = inside.reduce((s, q) => s + q[1], 0) / inside.length;
        inside.sort((a, b) => Math.hypot(a[0] - cxr, a[1] - cyr) - Math.hypot(b[0] - cxr, b[1] - cyr));
        res[k] = inside.slice(0, r.n);
      }
      if (ok) { chosen = res; break; }
    }
    if (!chosen) throw new Error('Venn dots do not fit');
    const centre = (pts) => [pts.reduce((s, q) => s + q[0], 0) / pts.length, pts.reduce((s, q) => s + q[1], 0) / pts.length];
    return {
      xL, xR, y, rL, rR, d, top, bot, pitch, dotR: pitch * 0.34,
      dots: chosen, centres: { both: centre(chosen.both), self: centre(chosen.self), a1c: centre(chosen.a1c) },
      pathSelf, pathA1c, counts: { nBoth, nSelf, nA1c, nOnlySelf, nOnlyA1c },
      bbox: { x0: xL - rL, x1: xR + rR, y0: y - rL, y1: y + rL },
    };
  }

  global.LabelVenn = { build };
})(window);
