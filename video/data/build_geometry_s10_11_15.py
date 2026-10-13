"""Aggregate geometry for scenes 10, 11 and 15 of the explainer video (histogram bins, Simpson cell flags).

Writes video/data/hist_geometry.json in the schema of the other video data files.
Aggregates only: bin edges and counts, plus one flag per Simpson comparison. No individual rows are stored
(NHANES data user agreement).

Populations are those of the notebooks:
  HbA1c        analysis cohort io.build_cohort() (N = 5,730), notebooks/sections/02_profiling.py (Tukey fence)
  triglycerides valid fasting subsample WTSAF2YR > 0 (n = 2,820), notebooks/sections/03_eda.py section 4.10;
                Yeo-Johnson via scipy.stats.yeojohnson (the skew_table.csv method)
  Simpson      results/S4/simpson_scan.csv (224 comparisons, 6 flips)

Every stored value that appears in a scene is asserted against video/data/*.json before writing.

Run:  .venv/Scripts/python video/data/build_geometry_s10_11_15.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src import config as C            # noqa: E402
from src import nhanes_io as io        # noqa: E402

OUT = Path(__file__).resolve().parent / "hist_geometry.json"
MINUS = "\u2212"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load(name):
    return json.loads((OUT.parent / name).read_text(encoding="utf-8"))


iqr, vs, simp = load("iqr_fence.json"), load("vif_skew.json"), load("simpson.json")
V = lambda d, k: d["items"][k]["value"]     # noqa: E731

items: dict[str, dict] = {}


def add(id_, label, value, display, source, kind="derived"):
    items[id_] = {"value": value, "label": label, "display": display, "kind": kind, "source": source, "key": None, "csv": None}


def close(a, b, tol):
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------- HbA1c histogram (scene 10)
coh = io.build_cohort()
a1c = coh["LBXGH"].astype(float)
assert len(a1c) == 5730 and a1c.notna().all()
q1, q3 = a1c.quantile([0.25, 0.75])
lo_f, hi_f = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
flag = (a1c < lo_f) | (a1c > hi_f)
n_fl, n_pos = int(flag.sum()), int((flag & (a1c >= C.HBA1C_DIABETES)).sum())
assert close(hi_f, V(iqr, "fence"), 1e-9) and n_fl == V(iqr, "flagged") and n_pos == V(iqr, "flagged_pos")
n_hi, n_lo = int((a1c > hi_f).sum()), int((a1c < lo_f).sum())
assert n_hi == n_pos and n_lo == n_fl - n_pos                  # every value above the fence is diabetic; the rest lie below the lower fence
edges = np.round(np.arange(3.0, 17.4 + 1e-9, 0.2), 1)           # 0.2-point bins; the cohort ranges 3.2-17.1
cnt, _ = np.histogram(a1c, bins=edges)
assert cnt.sum() == len(a1c)
add("a1c_fence_lower", "1.5 × IQR fence (lower)", float(lo_f), f"{lo_f:.1f} %", "derived: Q1 − 1.5·IQR of LBXGH, analysis cohort (02_profiling.py iqr_fence)")
add("a1c_flagged_high", "Flagged values above the upper fence", n_hi, f"{n_hi:,}", "derived: count of LBXGH > upper fence; equals flagged_pos (asserted)")
add("a1c_flagged_low", "Flagged values below the lower fence", n_lo, f"{n_lo:,}", "derived: flagged − flagged_pos (asserted equal to the count below the lower fence)")
add("a1c_cut", "HbA1c diabetes threshold", float(C.HBA1C_DIABETES), f"{C.HBA1C_DIABETES:.1f} %", "definition: config.HBA1C_DIABETES", kind="definition")

# ---------------------------------------------------------------- triglycerides (scene 11)
fast = coh[C.WEIGHT_FASTING].fillna(0) > 0
tg = coh.loc[fast, "LBXTLG"].dropna().astype(float)
sk_raw = float(stats.skew(tg))
yj, lam = stats.yeojohnson(tg)
sk_yj = float(stats.skew(yj))
assert len(tg) == V(vs, "skew_tg_n") and close(sk_raw, V(vs, "skew_tg"), 1e-9) and close(sk_yj, V(vs, "skew_tg_yj"), 1e-9)
raw_edges = np.arange(0, tg.max() + 25, 25.0)                   # 25 mg/dL bins, as figures/S4_triglyceride_skew.png
raw_cnt, _ = np.histogram(tg, bins=raw_edges)
yj_edges = np.linspace(float(yj.min()), float(yj.max()), 41)
yj_cnt, _ = np.histogram(yj, bins=yj_edges)
assert raw_cnt.sum() == len(tg) and yj_cnt.sum() == len(tg)
add("tg_raw_max", "Largest fasting triglyceride value (mg/dL)", float(tg.max()), f"{tg.max():.0f}", "derived: max LBXTLG, fasting subsample")
add("tg_yj_lambda", "Yeo-Johnson lambda", float(lam), f"{lam:.2f}", "derived: scipy.stats.yeojohnson (equals S4 skew_table yj_lambda)")

# ---------------------------------------------------------------- Simpson matrix (scene 15)
sc = pd.read_csv(ROOT / "results/S4/simpson_scan.csv")
assert len(sc) == V(simp, "n_comparisons") == 224 and int(sc["flip"].sum()) == V(simp, "n_flips") == 6
strat = list(dict.fromkeys(sc["stratifier"]))
combos = list(dict.fromkeys(zip(sc["exposure"], sc["reference"], sc["outcome"])))
cells = [{"row": combos.index((r.exposure, r.reference, r.outcome)), "col": strat.index(r.stratifier),
          "flip": bool(r.flip), "role": r.role} for r in sc.itertuples()]

groups = {
    "a1c_hist": {"edges": [float(e) for e in edges], "counts": [int(c) for c in cnt], "bin_width": 0.2},
    "tg_raw_hist": {"edges": [float(e) for e in raw_edges], "counts": [int(c) for c in raw_cnt], "bin_width": 25.0, "unit": "mg/dL"},
    "tg_yj_hist": {"edges": [float(e) for e in yj_edges], "counts": [int(c) for c in yj_cnt], "scale": "Yeo-Johnson"},
    "simpson_cells": {"cols": strat, "n_rows": len(combos), "cells": cells},
}
doc = {
    "_meta": {
        "file": "video/data/hist_geometry.json", "visual": "HbA1c histogram, triglyceride histograms, Simpson matrix", "scenes": "10, 11, 15",
        "generated_by": "video/data/build_geometry_s10_11_15.py (aggregates only: bin edges and counts; no individual rows)",
        "notes": ["Triglyceride scene uses the Yeo-Johnson transform (skew −0.009, as the plan says); figures/S4_triglyceride_skew.png shows the log transform (0.60).",
                  "All 23 flagged HbA1c values that are not diabetic lie below the lower fence; all 519 diabetic ones lie above the upper fence."],
    },
    "items": items, "intervals": {}, "groups": groups,
}
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", OUT, f"| a1c bins {len(cnt)}, tg raw bins {len(raw_cnt)}, yj bins {len(yj_cnt)}, simpson cells {len(cells)}, lambda {lam:.3f}")
