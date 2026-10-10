# %% [markdown]
# # §4 Exploratory Analysis and Analytical Fallacies (Stage S4)
#
# This section answers three questions before any model is fitted:
#
# 1. **Which weight and which variance method give population numbers we can trust?** We validate
#    our survey toolkit (`src/survey.py`) against an official NCHS publication (Data Brief 516).
# 2. **Which descriptive contrasts are artefacts?** Unweighted vs weighted prevalence, crude vs
#    age-standardised group differences, a systematic Simpson scan and a DAG that says which
#    variables may be adjusted for and which must not be.
# 3. **What does the data structure imply for the algorithm?** Redundancy, collinearity, skewness,
#    non-linearity and interactions are quantified and turned into a "data → algorithm" (DAJ) table
#    that S6–S7 cite.
#
# | § | Item | Artefact |
# |---|---|---|
# | 4.1 | Survey design and weights map | `results/S4/weights_map.md` |
# | 4.2 | Variance engine check | – |
# | 4.3 | External anchor: NCHS Data Brief 516 | `results/S4/db516_replication.csv`, `figures/S4_db516_forest.png` |
# | 4.4 | Weighted vs unweighted prevalence | `figures/S4_age_structure.png` |
# | 4.5 | Age standardisation | `results/S4/std_prev_table.csv` |
# | 4.6 | Insurance: attenuation, not reversal | `figures/S4_crude_vs_std.png` |
# | 4.7 | Simpson scan | `results/S4/simpson_scan.csv` |
# | 4.8 | Causal structure (DAG) | `figures/S4_dag.png` |
# | 4.9 | Redundancy and collinearity | `results/S4/vif_table.csv`, `figures/S4_spearman_clustermap.png` |
# | 4.10 | Skewness | `results/S4/skew_table.csv` |
# | 4.11 | Linearity | `results/S4/linearity_tests.csv`, `figures/S4_binned_logodds.png` |
# | 4.12 | Interactions and power | `results/S4/interaction_tests.csv` |
# | 4.13 | Data → algorithm (DAJ) table | `results/S4/daj_table.csv` |
# | 4.14 | Self-check and decision register | `governance/register/S4.csv` |
#
# All population estimates use the delete-one-PSU jackknife; every proportion carries its
# domain degrees of freedom, a Korn–Graubard interval and the NCHS presentation flags.

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from src import nhanes_io as io, survey as S, labels as L

pd.set_option("display.width", 160, "display.max_columns", 30)
RNG_SEEDS = np.random.SeedSequence(C.SEED_MASTER).spawn(8)   # one child stream per random step
OUT: dict = {}            # every reported number -> results/metrics_S4.json
REG: list[dict] = []      # decision-register rows -> governance/register/S4.csv
S4_DIR = C.RESULTS_DIR / "S4"
S4_DIR.mkdir(parents=True, exist_ok=True)
TODAY = "2026-10-11"


def reg(dr_id, type_, finding, evidence_ref, evidence_value, decision, alternatives_rejected,
        check_verdict="PASS", check_note="", hyp_id="", status="final", loop_ref=""):
    """Append one decision-register row (columns per process doc §7.2)."""
    REG.append({"dr_id": dr_id, "stage": "S4", "date": TODAY, "type": type_, "finding": finding,
                "evidence_ref": evidence_ref, "evidence_value": evidence_value, "decision": decision,
                "alternatives_rejected": alternatives_rejected, "hyp_id": hyp_id, "status": status,
                "check_verdict": check_verdict, "check_note": check_note, "loop_ref": loop_ref,
                "change_request": "", "commit": ""})


def pct(x, d=1):
    return f"{100 * x:.{d}f}"


def md_table(df: pd.DataFrame) -> str:
    """Minimal Markdown table (no extra dependency)."""
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return chr(10).join(lines)


coh = L.add_labels(io.build_cohort())
assert len(coh) == io.COHORT_N == 5730
print(f"cohort: {len(coh):,} adults, L_comb positives {int(coh.L_comb.sum())}")

# %% [markdown]
# ## 4.1 Survey design and weights map
# **Why.** NHANES is a stratified, clustered, unequal-probability sample. Each data component was
# collected on a different subsample and carries its own weight; using the wrong weight (or none)
# changes the population the numbers describe. The variance must reflect the 15 masked strata ×
# 2 PSUs, which leaves only **15 design degrees of freedom** however many people are sampled.

# %%
WEIGHTS_MAP = pd.DataFrame([
    ("Interview (questionnaires: DIQ, BPQ, HIQ, HUQ, SMQ, PAQ, INQ)", C.WEIGHT_INTERVIEW, "all interviewed", "interview-only descriptives"),
    ("MEC examination (BMX, BPXO)", C.WEIGHT_MEC, "examined", "exam-only descriptives"),
    ("Phlebotomy analytes (GHB = HbA1c, TCHOL, HDL)", C.WEIGHT_PHLEB, "examined + blood drawn", "**cohort analyses (contain HbA1c)**"),
    ("Fasting analytes (GLU, TRIGLY/LDL)", C.WEIGHT_FASTING, "morning fasting subsample, 8–24 h fast", "**DB516 replication, triglycerides, LDL**"),
], columns=["component", "weight", "subsample", "used here for"])
WEIGHTS_MAP["positive in cohort"] = [int((coh[w].fillna(0) > 0).sum()) for w in WEIGHTS_MAP.weight]
print(WEIGHTS_MAP.to_string(index=False))

design = coh.groupby(C.STRATA)[C.PSU].nunique()
n_strata, n_psu = design.size, int(design.sum())
DF_DESIGN = S.design_df(coh)
print(f"\nstrata = {n_strata}, PSUs = {n_psu}, design df = #PSU - #strata = {DF_DESIGN}")
assert (n_strata, n_psu, DF_DESIGN) == (15, 30, 15)
print(f"fasting rows with WTSAF2YR = 0 (fasted outside 8-24 h or no specimen) inside the cohort: "
      f"{int(((coh.WTSAF2YR == 0)).sum())}")

rule = ("Rule: when variables from several components are combined, use the weight of the smallest "
        "subsample involved (fasting < phlebotomy < MEC < interview).")
md = ["# Weights map (S4)", "", md_table(WEIGHTS_MAP), "", rule, "",
      f"Design: {n_strata} strata x 2 PSUs = {n_psu} PSUs; design df = {DF_DESIGN}. "
      "Variance: delete-one-PSU jackknife (JKn); domains by zeroing weights; domain df = number of "
      "strata containing domain observations; df < 8 flagged as unstable (NCHS)."]
(S4_DIR / "weights_map.md").write_text("\n".join(md) + "\n", encoding="utf-8")
WEIGHTS_MAP.to_csv(S4_DIR / "weights_map.csv", index=False)
OUT["design"] = {"n_strata": n_strata, "n_psu": n_psu, "df": DF_DESIGN,
                 "n_wtph_pos": int((coh.WTPH2YR > 0).sum()),
                 "n_fasting_pos": int((coh.WTSAF2YR.fillna(0) > 0).sum())}

# %% [markdown]
# **So what.** Every cohort row has a phlebotomy weight (`WTPH2YR` > 0), so it is the weight for all
# cohort descriptives and for the weighted ablation arm; the fasting weight `WTSAF2YR` is reserved
# for analyses that involve fasting glucose, triglycerides or LDL. Note that fasting participants who
# did not meet the 8–24 h criterion carry `WTSAF2YR = 0` and must be excluded from fasting analyses
# even though their glucose value is present (see §4.10 for the consequence). With 15 design df, a
# t-quantile of 2.13 (not 1.96) applies to every full-sample interval.

# %% [markdown]
# ## 4.2 Variance engine check
# **Why.** The jackknife is the backbone of every interval in the project, so it is checked twice
# before use: (a) against an independent variance method – Taylor linearisation of the ratio
# estimator – and (b) on domains, where the correct approach is to zero the weights outside the
# domain rather than drop rows, and where the degrees of freedom shrink to the number of strata
# that contain the domain.

# %%
def taylor_se_ratio(df, y, weight, domain=None):
    """Taylor-linearised SE of a weighted domain mean (with-replacement PSU approximation)."""
    yv = df[y].to_numpy(float) if isinstance(y, str) else np.asarray(y, float)
    dm = np.ones(len(df), bool) if domain is None else np.asarray(domain, bool)
    w = df[weight].fillna(0).to_numpy(float) * dm * ~np.isnan(yv)
    y0 = np.nan_to_num(yv)
    p = np.dot(w, y0) / w.sum()
    z = w * (y0 - p) / w.sum()
    tot = pd.DataFrame({"h": df[C.STRATA].to_numpy(), "i": df[C.PSU].to_numpy(), "z": z}).groupby(["h", "i"]).z.sum()
    var = 0.0
    for _, g in tot.groupby(level=0):
        nh = len(g)
        var += nh / (nh - 1) * ((g - g.mean()) ** 2).sum()
    return p, np.sqrt(var)


checks = []
asian = coh.race.eq("NH Asian").to_numpy()
undx_dom = coh.L_A1c.eq(1).to_numpy()
for name, y, dom in [("L_comb, all adults", "L_comb", None),
                     ("L_comb, NH Asian", "L_comb", asian),
                     ("undiagnosed share, HbA1c>=6.5", "in_escreen", undx_dom),
                     ("undiagnosed share, Asian HbA1c>=6.5", "in_escreen", undx_dom & asian)]:
    jk = S.weighted_prop(coh, y, weight=C.WEIGHT_PHLEB, domain=dom)
    p_t, se_t = taylor_se_ratio(coh, y, C.WEIGHT_PHLEB, dom)
    checks.append({"estimate": name, "n": jk["n"], "p": jk["est"], "se_jk": jk["se"], "se_taylor": se_t,
                   "ratio": jk["se"] / se_t, "domain_df": jk["df"], "kg_low": jk["kg_low"],
                   "kg_high": jk["kg_high"], "flags": ",".join(jk["nchs_flags"]) or "–"})
checks = pd.DataFrame(checks)
print(checks.round(4).to_string(index=False))
assert np.allclose(checks.ratio, 1, atol=0.02), "jackknife and Taylor SEs disagree"

# zero-weighting vs dropping rows: identical point estimate, but dropping hides which strata are empty
drop = coh[undx_dom & asian]
print(f"\nAsian undiagnosed domain: {len(drop)} rows in {drop[C.STRATA].nunique()} strata / "
      f"{drop[[C.STRATA, C.PSU]].drop_duplicates().shape[0]} PSUs -> domain df = "
      f"{S.domain_df(coh, undx_dom & asian)} (flag df<8: {S.domain_df(coh, undx_dom & asian) < C.NCHS_MIN_DF})")
OUT["variance_check"] = checks.drop(columns="flags").to_dict("records")
OUT["asian_undx_domain_df"] = S.domain_df(coh, undx_dom & asian)

# %% [markdown]
# **So what.** The jackknife and Taylor standard errors agree to within 2 % on the full sample and on
# small domains (the ratio column), so the jackknife can be trusted for non-linear statistics where no
# Taylor formula is at hand (standardised differences, κ, AUC). The Asian-undiagnosed domain lives in
# only 8 strata: its df is 8, right at the NCHS instability threshold, which is why S5 reports it as
# exploratory. Dropping the rows would have given the same point estimate but silently treated the
# empty strata as if they did not exist in the design.

# %% [markdown]
# ## 4.3 External anchor: NCHS Data Brief 516
# **Why.** An internal check cannot detect a wrong *definition* or a wrong *weight*. Re-deriving an
# official estimate from the same public files can: if our cohort logic, fasting weight, jackknife,
# Korn–Graubard interval and age standardisation are all correct, we must land on NCHS Data Brief 516
# (Gwira et al. 2024, Tables 1–2). DB516 definitions: adults ≥ 20, non-pregnant, fasting subsample
# (`WTSAF2YR` > 0, 8–24 h fast); diagnosed = DIQ010 = 1; undiagnosed = not diagnosed and
# (fasting glucose ≥ 126 mg/dL or HbA1c ≥ 6.5 %); total = diagnosed + undiagnosed; age adjustment to
# the US 2000 standard with 20–39 / 40–59 / 60+. Note the fasting weight, **not** `WTPH2YR`.

# %%
# NCHS Data Brief 516, Tables 1-2 (external reference values, transcribed from
# https://www.cdc.gov/nchs/products/databriefs/db516.htm). Percent (95% CI).
NCHS = pd.DataFrame([
    # measure, group, kind, n, est, lo, hi
    ("total", "All", "crude", 2938, 15.8, 13.6, 18.2), ("total", "All", "age-adj", 2938, 14.3, 12.1, 16.7),
    ("total", "Men", "crude", 1306, 18.0, 15.7, 20.4), ("total", "Men", "age-adj", 1306, 16.6, 14.0, 19.4),
    ("total", "Women", "crude", 1632, 13.7, 11.0, 16.7), ("total", "Women", "age-adj", 1632, 12.2, 9.9, 14.8),
    ("diagnosed", "All", "crude", 2938, 11.3, 9.3, 13.5), ("diagnosed", "All", "age-adj", 2938, 10.1, 8.3, 12.1),
    ("diagnosed", "Men", "crude", 1306, 12.9, 11.0, 15.0), ("diagnosed", "Men", "age-adj", 1306, 11.7, 9.9, 13.7),
    ("diagnosed", "Women", "crude", 1632, 9.7, 7.3, 12.7), ("diagnosed", "Women", "age-adj", 1632, 8.6, 6.7, 10.9),
    ("undiagnosed", "All", "crude", 2938, 4.5, 3.3, 5.9), ("undiagnosed", "All", "age-adj", 2938, 4.2, 2.9, 5.7),
    ("undiagnosed", "Men", "crude", 1306, 5.1, 3.6, 6.9), ("undiagnosed", "Men", "age-adj", 1306, 4.9, 3.3, 6.9),
    ("undiagnosed", "Women", "crude", 1632, 3.9, 2.8, 5.3), ("undiagnosed", "Women", "age-adj", 1632, 3.5, 2.4, 5.1),
    ("total", "20-39", "crude", 688, 3.6, 2.0, 5.9), ("total", "40-59", "crude", 861, 17.7, 14.7, 21.0),
    ("total", "60+", "crude", 1389, 27.3, 23.0, 31.9),
    ("diagnosed", "20-39", "crude", 688, 2.2, 1.1, 4.0), ("diagnosed", "40-59", "crude", 861, 12.1, 10.0, 14.5),
    ("diagnosed", "60+", "crude", 1389, 20.5, 16.2, 25.3),
    ("undiagnosed", "20-39", "crude", 688, 1.3, 0.5, 3.0), ("undiagnosed", "40-59", "crude", 861, 5.6, 3.3, 8.9),
    ("undiagnosed", "60+", "crude", 1389, 6.8, 5.3, 8.5),
], columns=["measure", "group", "kind", "n_nchs", "nchs", "nchs_low", "nchs_high"])

fast = coh.copy()
fast_dom = (fast[C.WEIGHT_FASTING].fillna(0) > 0) & fast.LBXGLU.notna()
fast["diagnosed"] = fast.L_self.astype(float)
fast["undiagnosed"] = ((fast.L_self == 0) & ((fast.LBXGLU >= L.FPG_CUT) | (fast.LBXGH >= L.A1C_CUT))).astype(float)
fast["total"] = ((fast.diagnosed == 1) | (fast.undiagnosed == 1)).astype(float)
fast["All"] = "All"
fast["age3"] = S.age_band(fast.RIDAGEYR).to_numpy()
fast["sexg"] = fast.sex.map({"Male": "Men", "Female": "Women"})
# the SL5 label of labels.py is the same NCHS definition - cross-check
assert (L.sensitivity_labels(fast)["SL5"][fast_dom] == fast.loc[fast_dom, "total"]).all()

rows = []
for measure in ["total", "diagnosed", "undiagnosed"]:
    for gcol in ["All", "sexg"]:
        t = S.age_standardise(fast, measure, gcol, weight=C.WEIGHT_FASTING, domain=fast_dom)
        for _, r in t.iterrows():
            rows.append((measure, r.group, "crude", r.n, r.crude, r.crude_kg_low, r.crude_kg_high, r.crude_low, r.crude_high, r.df))
            rows.append((measure, r.group, "age-adj", r.n, r["std"], r.std_kg_low, r.std_kg_high, r.std_low, r.std_high, r.df))
    for band in ["20-39", "40-59", "60+"]:
        r = S.weighted_prop(fast, measure, weight=C.WEIGHT_FASTING, domain=fast_dom & (fast.age3 == band))
        rows.append((measure, band, "crude", r["n"], r["est"], r["kg_low"], r["kg_high"], r["ci_low"], r["ci_high"], r["df"]))
ours = pd.DataFrame(rows, columns=["measure", "group", "kind", "n", "est", "kg_low", "kg_high", "jk_low", "jk_high", "df"])
ours[["est", "kg_low", "kg_high", "jk_low", "jk_high"]] *= 100
DB516 = NCHS.merge(ours, on=["measure", "group", "kind"], how="left")
DB516["diff_pp"] = DB516.est - DB516.nchs
DB516["ci_overlap"] = (DB516.kg_low <= DB516.nchs_high) & (DB516.kg_high >= DB516.nchs_low)
DB516["kg_matches_nchs_ci"] = ((DB516.kg_low.round(1) - DB516.nchs_low).abs() <= 0.1) & \
                              ((DB516.kg_high.round(1) - DB516.nchs_high).abs() <= 0.1)
DB516.to_csv(S4_DIR / "db516_replication.csv", index=False)
print(DB516[["measure", "group", "kind", "n", "n_nchs", "est", "kg_low", "kg_high", "nchs", "nchs_low",
             "nchs_high", "diff_pp"]].round(2).to_string(index=False))

assert (DB516.n == DB516.n_nchs).all(), "sample sizes differ from NCHS"
assert DB516.diff_pp.abs().max() <= 0.1 + 1e-9 and DB516.ci_overlap.all()
head = DB516.query("group == 'All'").set_index(["measure", "kind"])
print(f"\nheadline: total {head.loc[('total','crude'),'est']:.2f}% "
      f"(JK t15 {head.loc[('total','crude'),'jk_low']:.2f}, {head.loc[('total','crude'),'jk_high']:.2f}; "
      f"KG {head.loc[('total','crude'),'kg_low']:.2f}, {head.loc[('total','crude'),'kg_high']:.2f}); "
      f"diagnosed {head.loc[('diagnosed','crude'),'est']:.2f}; undiagnosed {head.loc[('undiagnosed','crude'),'est']:.2f}; "
      f"age-adjusted {head.loc[('total','age-adj'),'est']:.2f}/{head.loc[('diagnosed','age-adj'),'est']:.2f}/"
      f"{head.loc[('undiagnosed','age-adj'),'est']:.2f}")
print(f"max |diff| over {len(DB516)} published estimates = {DB516.diff_pp.abs().max():.3f} pp; "
      f"KG interval equals the published CI (to 0.1 pp) in {int(DB516.kg_matches_nchs_ci.sum())}/{len(DB516)} rows")

# %% [markdown]
# The process document quotes 15.78 / 11.29 / 4.48 on *n* = 2,940. That variant keeps two fasting
# adults without an HbA1c result (counted as non-diabetic); NCHS's *n* = 2,938 excludes them. The next
# cell reproduces both so the 0.01 pp difference is explained rather than hidden.

# %%
full = io.zero_weights_to_nan(io.load_merged())
v_dom = (full.RIDAGEYR >= C.ADULT_MIN_AGE) & (full.RIDEXPRG != 1) & (full[C.WEIGHT_FASTING].fillna(0) > 0)
dx = full.DIQ010.eq(1)
und = ~dx & (full.LBXGLU.ge(L.FPG_CUT) | full.LBXGH.ge(L.A1C_CUT))
variant = {}
for nm, y in [("total", dx | und), ("diagnosed", dx), ("undiagnosed", und)]:
    r = S.weighted_prop(full, y.astype(float), weight=C.WEIGHT_FASTING, domain=v_dom)
    variant[nm] = {"n": r["n"], "est": 100 * r["est"], "jk_low": 100 * r["ci_low"], "jk_high": 100 * r["ci_high"]}
print(pd.DataFrame(variant).T.round(2))
print("rows in the 2,940 variant without HbA1c:", int((v_dom & full.LBXGH.isna()).sum()))

OUT["db516"] = {"n": int(head.loc[("total", "crude"), "n"]),
                "total": head.loc[("total", "crude"), "est"], "total_jk_ci": [head.loc[("total", "crude"), "jk_low"], head.loc[("total", "crude"), "jk_high"]],
                "total_kg_ci": [head.loc[("total", "crude"), "kg_low"], head.loc[("total", "crude"), "kg_high"]],
                "diagnosed": head.loc[("diagnosed", "crude"), "est"], "undiagnosed": head.loc[("undiagnosed", "crude"), "est"],
                "age_adj": [head.loc[(m, "age-adj"), "est"] for m in ["total", "diagnosed", "undiagnosed"]],
                "max_abs_diff_pp": DB516.diff_pp.abs().max(), "n_estimates": len(DB516),
                "kg_matches_published_ci": int(DB516.kg_matches_nchs_ci.sum()),
                "variant_n2940": variant}

# %%
fig, axes = plt.subplots(1, 3, figsize=(12, 5.2), sharey=True)
for ax, measure in zip(axes, ["total", "diagnosed", "undiagnosed"]):
    d = DB516[DB516.measure == measure].reset_index(drop=True)
    labels_ = [f"{g} ({'age-adj.' if k == 'age-adj' else 'crude'})" for g, k in zip(d.group, d.kind)]
    yy = np.arange(len(d))[::-1]
    ax.errorbar(d.nchs, yy + 0.15, xerr=[d.nchs - d.nchs_low, d.nchs_high - d.nchs], fmt="s", ms=5,
                color=C.OKABE_ITO["grey"], capsize=2, label="NCHS DB516 (published)")
    ax.errorbar(d.est, yy - 0.15, xerr=[d.est - d.kg_low, d.kg_high - d.est], fmt="o", ms=5,
                color=C.OKABE_ITO["blue"], capsize=2, label="this replication (JK + Korn–Graubard)")
    ax.set_yticks(yy, labels_)
    ax.set_title(measure.capitalize())
    ax.set_xlabel("Prevalence, % (95% CI)")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="lower center", ncol=2, fontsize=9)
fig.suptitle(f"Replication of NCHS Data Brief 516 (fasting subsample, n = 2,938, WTSAF2YR): "
             f"max |difference| = {DB516.diff_pp.abs().max():.2f} pp over {len(DB516)} estimates", fontsize=11)
fig.tight_layout(rect=(0, 0.06, 1, 1))
plots.savefig(fig, "S4_db516_forest",
              caption="Our design-based estimates (blue, Korn-Graubard 95% CI) against the published NCHS "
                      "Data Brief 516 values (grey) for total, diagnosed and undiagnosed diabetes, crude and "
                      "age-adjusted, overall, by sex and by age group.")
plt.show()

reg("DR-S4-01", "method", "NHANES 2021-23 has 15 strata x 2 PSUs (df = 15); every cohort row has WTPH2YR > 0; "
    "jackknife SE agrees with Taylor linearisation (ratio within 2%).",
    "results/S4/weights_map.md; §4.2", f"df = {DF_DESIGN}; JK/Taylor SE ratio {checks.ratio.min():.3f}-{checks.ratio.max():.3f}",
    "WTPH2YR for all cohort analyses and the weighted ablation; WTSAF2YR for fasting analytes and DB516; "
    "delete-one-PSU jackknife with domain df = strata containing the domain; NCHS flags (n, n_eff < 30, "
    "KG width >= 0.30, df < 8).",
    "Unweighted analysis (describes the sample, not the population); WTMEC2YR for HbA1c (ignores blood-draw "
    "non-response); Taylor-only variance (no formula for kappa/AUC/standardised differences).",
    check_note="re-computed in §4.2")
reg("DR-S4-02", "validation", "Survey toolkit reproduces NCHS Data Brief 516 on the fasting subsample.",
    "results/S4/db516_replication.csv; figures/S4_db516_forest.png",
    f"total {head.loc[('total','crude'),'est']:.2f}% vs 15.8; diagnosed {head.loc[('diagnosed','crude'),'est']:.2f} vs 11.3; "
    f"undiagnosed {head.loc[('undiagnosed','crude'),'est']:.2f} vs 4.5; max |diff| {DB516.diff_pp.abs().max():.2f} pp over {len(DB516)} estimates",
    "Use src/survey.py (JK + KG + 3-band US 2000 standardisation) for every population number in S4-S9.",
    "Accept the toolkit on internal checks only (cannot detect wrong definitions or weights).",
    check_note=f"n = 2,938 equals NCHS; the process-doc figure 15.78 comes from an n = 2,940 variant with 2 missing HbA1c")

# %% [markdown]
# **So what.** All 27 published DB516 estimates (overall, by sex, by age; crude and age-adjusted) are
# reproduced within 0.1 pp, with exactly NCHS's sample size of 2,938, and our Korn–Graubard intervals
# coincide with the published asymmetric intervals – evidence that NCHS itself uses the KG interval
# and that our cohort filter, fasting weight, jackknife and standardisation are right. The symmetric
# jackknife-*t* interval for the total (13.53, 18.03) is the Wald version of the same uncertainty.
# This is the external anchor for every weighted number later in the project.

# %% [markdown]
# ## 4.4 Weighted vs unweighted prevalence
# **Why.** The cohort's raw share of `L_comb` positives describes the *sample*, which over-represents
# older adults. Because NCHS used a different definition (fasting glucose as well), our cohort number
# is also not expected to equal DB516's 15.8 %. Both gaps need to be explained, not ignored.

# %%
w_ph = coh[C.WEIGHT_PHLEB].to_numpy(float)
unw = coh.L_comb.mean()
wp = S.weighted_prop(coh, "L_comb", weight=C.WEIGHT_PHLEB)
kish = S.kish_deff(w_ph)
coh["age3"] = S.age_band(coh.RIDAGEYR).to_numpy()
bands = list(S.US2000_3BAND)
share_s = coh.age3.value_counts(normalize=True).reindex(bands)
share_w = pd.Series({b: w_ph[coh.age3 == b].sum() / w_ph.sum() for b in bands})
rate_unw = coh.groupby("age3").L_comb.mean().reindex(bands)
rate_w = {b: S.weighted_prop(coh, "L_comb", weight=C.WEIGHT_PHLEB, domain=coh.age3 == b) for b in bands}
unw_age_reweighted = float((rate_unw * share_w).sum())     # sample rates, population age mix
explained = (unw - unw_age_reweighted) / (unw - wp["est"])
AGE_TAB = pd.DataFrame({"sample share": share_s, "weighted share": share_w, "unweighted rate": rate_unw,
                        "weighted rate": [rate_w[b]["est"] for b in bands],
                        "kg_low": [rate_w[b]["kg_low"] for b in bands], "kg_high": [rate_w[b]["kg_high"] for b in bands]})
print((AGE_TAB * 100).round(1))
print(f"\nL_comb unweighted {pct(unw, 2)}% vs WTPH2YR-weighted {pct(wp['est'], 2)}% "
      f"(JK {pct(wp['ci_low'])}-{pct(wp['ci_high'])}, KG {pct(wp['kg_low'])}-{pct(wp['kg_high'])}, df {wp['df']})")
print(f"sample rates re-weighted to the population age mix: {pct(unw_age_reweighted, 2)}% -> age structure explains "
      f"{100 * explained:.0f}% of the {100 * (unw - wp['est']):.2f} pp gap")
print(f"Kish deff (unequal weights) = {kish:.3f}; Kish n_eff = {S.kish_neff(w_ph):,.0f}; "
      f"full design effect for L_comb = {wp['deff']:.2f}")
assert abs(unw - 0.1695) < 5e-4 and abs(wp["est"] - 0.140) < 5e-4 and abs(kish - 1.55) < 0.01
OUT["prevalence"] = {"unweighted": unw, "weighted": wp["est"], "weighted_jk_ci": [wp["ci_low"], wp["ci_high"]],
                     "weighted_kg_ci": [wp["kg_low"], wp["kg_high"]], "kish_deff": kish, "design_deff": wp["deff"],
                     "share_60plus_sample": share_s["60+"], "share_60plus_weighted": share_w["60+"],
                     "share_20_39_sample": share_s["20-39"], "share_20_39_weighted": share_w["20-39"],
                     "unweighted_age_reweighted": unw_age_reweighted, "gap_explained_by_age": explained}

# %%
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
x = np.arange(3)
a1.bar(x - 0.2, share_s * 100, 0.4, label="sample (unweighted)", color=C.OKABE_ITO["orange"])
a1.bar(x + 0.2, share_w * 100, 0.4, label="population (WTPH2YR)", color=C.OKABE_ITO["blue"])
a1.set_xticks(x, bands); a1.set_ylabel("Share of adults, %"); a1.set_xlabel("Age band")
a1.set_title("The sample is older than the population"); a1.legend()
yr = AGE_TAB["weighted rate"] * 100
a2.errorbar(x, yr, yerr=[yr - AGE_TAB.kg_low * 100, AGE_TAB.kg_high * 100 - yr], fmt="o", capsize=4,
            color=C.OKABE_ITO["blue"], label="weighted rate (KG 95% CI)")
a2.plot(x, AGE_TAB["unweighted rate"] * 100, "s", color=C.OKABE_ITO["orange"], label="unweighted rate")
a2.set_xticks(x, bands); a2.set_ylabel("L_comb prevalence, %"); a2.set_xlabel("Age band")
a2.set_title("…and prevalence rises steeply with age"); a2.legend()
fig.suptitle(f"Unweighted {pct(unw)}% vs weighted {pct(wp['est'])}%: age structure explains "
             f"{100 * explained:.0f}% of the gap", fontsize=11)
fig.tight_layout()
plots.savefig(fig, "S4_age_structure",
              caption="Left: age distribution of the cohort vs the weighted population. Right: L_comb prevalence "
                      "by age band (weighted with Korn-Graubard CI, and unweighted).")
plt.show()

# %% [markdown]
# **So what.** 46 % of the cohort is 60+ against 31 % of the population, and prevalence in that band
# is about seven times that of 20–39-year-olds, so the unweighted 16.95 % overstates the population
# prevalence of 14.0 % (12.4–15.6). Re-weighting the sample's own age-specific rates to the population
# age mix closes most of the gap, i.e. the bias is mainly an age-structure effect. The remaining
# difference to DB516's 15.8 % is definitional (our cohort label has no fasting-glucose criterion,
# and uses the phlebotomy not the fasting sample) – not an error. The Kish design effect of 1.55 means
# 5,730 unequally weighted adults carry the information of about 3,700 equally weighted ones; the full
# design effect including clustering is larger still, which is why all CIs use the jackknife. For
# modelling, this motivates the weighted ablation arm (block B6) rather than silently ignoring weights.

# %% [markdown]
# ## 4.5 Age standardisation
# **Why.** Groups with different age structures cannot be compared on crude prevalence, because age
# is the strongest determinant of diabetes. Direct standardisation applies each group's age-specific
# rates to one common age distribution. We use the US 2000 standard population in the three NCHS
# bands; the band weights are derived here from the 5-year "standard million" (Klein & Schoenborn
# 2001) rather than taken on trust, and a 6-band standard and an internal (cohort) standard are
# sensitivity analyses.

# %%
# US 2000 standard population per million, 5-year groups from age 20 (Klein & Schoenborn 2001, Table 2)
US2000_5Y = {"20-24": 66478, "25-29": 64529, "30-34": 71044, "35-39": 80762, "40-44": 81851, "45-49": 72118,
             "50-54": 62716, "55-59": 48454, "60-64": 38793, "65-69": 34264, "70-74": 31773, "75-79": 26999,
             "80-84": 17842, "85+": 15508}
lo_of = {k: int(k.rstrip("+").split("-")[0]) for k in US2000_5Y}
def collapse(cuts):
    out = {}
    for lab, (lo, hi) in cuts.items():
        out[lab] = sum(v for k, v in US2000_5Y.items() if lo <= lo_of[k] <= hi)
    tot = sum(out.values())
    return {k: v / tot for k, v in out.items()}
STD3 = collapse({"20-39": (20, 39), "40-59": (40, 59), "60+": (60, 200)})
STD6 = collapse({"20-29": (20, 29), "30-39": (30, 39), "40-49": (40, 49), "50-59": (50, 59), "60-69": (60, 69), "70+": (70, 200)})
print("3-band weights derived:", {k: round(v, 4) for k, v in STD3.items()}, "| survey.US2000_3BAND:", S.US2000_3BAND)
assert all(abs(STD3[k] - S.US2000_3BAND[k]) < 1e-4 for k in STD3)
STD_INT = {b: float(share_w[b]) for b in bands}            # internal standard: the weighted cohort itself
print("6-band weights:", {k: round(v, 4) for k, v in STD6.items()})

coh["insurance"] = coh.HIQ011.map({1: "insured", 2: "uninsured"})
coh["usual_care"] = coh.HUQ030.map({1: "has usual place", 3: "has usual place", 2: "no usual place"})
std_tabs = []
for gcol in ["race", "sex", "insurance", "usual_care"]:
    t = S.age_standardise(coh, "L_comb", gcol, weight=C.WEIGHT_PHLEB)
    t.insert(0, "grouping", gcol)
    std_tabs.append(t)
STD_TAB = pd.concat(std_tabs, ignore_index=True)
STD_TAB["kg_width"] = STD_TAB.crude_kg_high - STD_TAB.crude_kg_low
STD_TAB["nchs_flags"] = [",".join(S.nchs_flags(r.n, S._design_neff(r.crude, r.crude_se, r.n), r.kg_width, r.df)) or ""
                         for r in STD_TAB.itertuples()]
STD_TAB.to_csv(S4_DIR / "std_prev_table.csv", index=False)
show = STD_TAB[["grouping", "group", "n", "df", "crude", "crude_kg_low", "crude_kg_high", "std", "std_low", "std_high", "nchs_flags"]].copy()
show[["crude", "crude_kg_low", "crude_kg_high", "std", "std_low", "std_high"]] *= 100
print(show.round(1).to_string(index=False))

# %%
CONTRASTS = [("race", "NH Asian", "NH White"), ("race", "NH Black", "NH White"),
             ("race", "Mexican American", "NH White"), ("insurance", "insured", "uninsured"),
             ("usual_care", "has usual place", "no usual place")]
diffs = []
for gcol, a, b in CONTRASTS:
    for sname, std in [("US2000 3-band", STD3), ("US2000 6-band", STD6), ("internal 3-band", STD_INT)]:
        d = S.std_difference(coh, "L_comb", gcol, a, b, weight=C.WEIGHT_PHLEB, std=std)
        diffs.append({"contrast": f"{a} − {b}", "standard": sname, "n_a": d["n_a"], "n_b": d["n_b"], "df": d["df"],
                      "crude": 100 * d["crude_diff"], "crude_low": 100 * d["crude_low"], "crude_high": 100 * d["crude_high"],
                      "std": 100 * d["std_diff"], "std_low": 100 * d["std_low"], "std_high": 100 * d["std_high"]})
DIFFS = pd.DataFrame(diffs)
DIFFS.to_csv(S4_DIR / "std_differences.csv", index=False)
print(DIFFS.round(1).to_string(index=False))

aw = DIFFS.query("contrast == 'NH Asian − NH White' and standard == 'US2000 3-band'").iloc[0]
iu = DIFFS.query("contrast == 'insured − uninsured' and standard == 'US2000 3-band'").iloc[0]
assert abs(aw.crude - (-0.8)) < 0.1 and abs(aw["std"] - 2.1) < 0.1 and abs(aw.crude_low + 5.1) < 0.1 and abs(aw.std_high - 6.8) < 0.1
assert abs(iu.crude - 5.3) < 0.1 and abs(iu["std"] - 0.7) < 0.1 and abs(iu.crude_low - 1.8) < 0.1 and abs(iu.std_high - 3.9) < 0.1
asian_std = STD_TAB.query("group == 'NH Asian'").iloc[0]; white_std = STD_TAB.query("group == 'NH White'").iloc[0]
print(f"\nNH Asian vs NH White: crude {aw.crude:+.1f} ({aw.crude_low:.1f}, {aw.crude_high:.1f}) -> "
      f"standardised {aw['std']:+.1f} ({aw.std_low:.1f}, {aw.std_high:.1f}) pp; standardised rates "
      f"{pct(asian_std['std'])}% vs {pct(white_std['std'])}% (README claim 18.0% vs 13.6% not reproducible)")
OUT["standardisation"] = {
    "std3": STD3, "std6": STD6,
    "asian_white": {"crude": aw.crude, "crude_ci": [aw.crude_low, aw.crude_high], "std": aw["std"], "std_ci": [aw.std_low, aw.std_high],
                    "std_rate_asian": 100 * asian_std["std"], "std_rate_white": 100 * white_std["std"],
                    "std6": DIFFS.query("contrast == 'NH Asian − NH White' and standard == 'US2000 6-band'")["std"].item(),
                    "internal": DIFFS.query("contrast == 'NH Asian − NH White' and standard == 'internal 3-band'")["std"].item()},
    "insured_uninsured": {"crude": iu.crude, "crude_ci": [iu.crude_low, iu.crude_high], "std": iu["std"], "std_ci": [iu.std_low, iu.std_high]}}

# %% [markdown]
# **So what.** The derived band weights match 0.3966 / 0.3718 / 0.2316 exactly, which settles the
# open verification item of the process document. NH Asian adults have a slightly *lower* crude
# prevalence than NH White adults (−0.8 pp, −5.1 to 3.5) but, being much younger, a *higher*
# age-standardised one (+2.1 pp, −2.6 to 6.8). Both intervals include zero and the 6-band and
# internal standards tell the same story, so the honest statement is "direction flips after age
# standardisation, magnitude unknown" – a demonstration of honest uncertainty, not a headline. The
# README's 18.0 % vs 13.6 % cannot be reproduced with any of the three standards and is withdrawn.

# %% [markdown]
# ## 4.6 Insurance: attenuation, not reversal
# **Why.** Insured adults show a clearly higher crude prevalence than uninsured adults. Before
# reading this as a health-care effect we need to know how much of it is age: almost everyone
# aged 65+ has Medicare, so insurance is a strong marker of age (Age → Medicare → Insurance), and
# age drives diabetes.

# %%
ins_age = (pd.crosstab(coh.insurance, coh.age3, values=w_ph, aggfunc="sum", normalize="index") * 100).reindex(columns=bands)
print("weighted age mix by insurance status (%):\n", ins_age.round(1))
band_diff = []
for b in bands:
    d = S.std_difference(coh, "L_comb", "insurance", "insured", "uninsured", weight=C.WEIGHT_PHLEB,
                         domain=coh.age3 == b)
    band_diff.append({"age band": b, "n_insured": d["n_a"], "n_uninsured": d["n_b"],
                      "diff_pp": 100 * d["crude_diff"], "low": 100 * d["crude_low"], "high": 100 * d["crude_high"]})
band_diff = pd.DataFrame(band_diff)
print("\nage-specific insured − uninsured differences (pp):\n", band_diff.round(1).to_string(index=False))
print(f"\ninsured − uninsured: crude {iu.crude:+.1f} ({iu.crude_low:.1f}, {iu.crude_high:.1f}) -> "
      f"age-standardised {iu['std']:+.1f} ({iu.std_low:.1f}, {iu.std_high:.1f}) pp; "
      f"{100 * (1 - iu['std'] / iu.crude):.0f}% attenuation, same sign")
OUT["standardisation"]["insured_uninsured"].update({
    "attenuation_share": 1 - iu["std"] / iu.crude,
    "uninsured_share_60plus": ins_age.loc["uninsured", "60+"], "insured_share_60plus": ins_age.loc["insured", "60+"],
    "band_diffs": band_diff.to_dict("records")})

# %%
d3 = DIFFS[DIFFS.standard == "US2000 3-band"].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(8.5, 4.2))
yy = np.arange(len(d3))[::-1]
ax.errorbar(d3.crude, yy + 0.13, xerr=[d3.crude - d3.crude_low, d3.crude_high - d3.crude], fmt="o", capsize=3,
            color=C.OKABE_ITO["orange"], label="crude")
ax.errorbar(d3["std"], yy - 0.13, xerr=[d3["std"] - d3.std_low, d3.std_high - d3["std"]], fmt="s", capsize=3,
            color=C.OKABE_ITO["blue"], label="age-standardised (US 2000, 3 bands)")
ax.axvline(0, color="k", lw=0.8)
ax.set_yticks(yy, d3.contrast)
ax.set_xlabel("Difference in L_comb prevalence, percentage points (JK 95% CI)")
ax.set_title("Age standardisation: insurance gap attenuates, Asian–White gap changes sign within noise")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
fig.tight_layout()
plots.savefig(fig, "S4_crude_vs_std",
              caption="Crude and age-standardised prevalence differences (WTPH2YR, jackknife 95% CI, df = 15).")
plt.show()

reg("DR-S4-03", "method", "US 2000 standard collapsed to 20-39/40-59/60+ = 0.3966/0.3718/0.2316, re-derived from the 5-year standard million.",
    "results/S4/std_prev_table.csv; §4.5", "derived weights equal survey.US2000_3BAND to 1e-4",
    "Direct age standardisation (3-band US 2000) for every between-group prevalence comparison; 6-band and internal standards as sensitivity.",
    "Crude comparisons (confounded by age); internal-only standard (not comparable with NCHS).",
    check_note="re-derived in-notebook; also validated indirectly by the DB516 age-adjusted replication")
reg("DR-S4-04", "claim_change", "NH Asian vs NH White L_comb: crude -0.8 pp (-5.1, 3.5) -> standardised +2.1 pp (-2.6, 6.8); README 18.0% vs 13.6% not reproducible.",
    "results/S4/std_differences.csv; figures/S4_crude_vs_std.png",
    f"crude {aw.crude:+.1f} ({aw.crude_low:.1f}, {aw.crude_high:.1f}); std {aw['std']:+.1f} ({aw.std_low:.1f}, {aw.std_high:.1f}); std rates {pct(asian_std['std'])} vs {pct(white_std['std'])}%",
    "Withdraw the README 18.0/13.6 claim; report the Asian-White contrast only as an example of honest uncertainty (both CIs include 0).",
    "Headline 'Asians have higher diabetes prevalence' (not supported by the CI).",
    check_verdict="PASS-FIX", check_note="README figure corrected; numbers re-computed with three standards")
reg("DR-S4-05", "interpretation", "Insured - uninsured L_comb: crude +5.3 pp (1.8, 8.8) -> age-standardised +0.7 pp (-2.6, 3.9).",
    "results/S4/std_differences.csv; §4.6",
    f"crude {iu.crude:+.1f} ({iu.crude_low:.1f}, {iu.crude_high:.1f}); std {iu['std']:+.1f} ({iu.std_low:.1f}, {iu.std_high:.1f}); uninsured 60+ share {ins_age.loc['uninsured','60+']:.1f}% vs insured {ins_age.loc['insured','60+']:.1f}%",
    "Describe as age confounding (Age -> Medicare -> Insurance; Age -> diabetes) causing attenuation; never call it a reversal or Simpson's paradox.",
    "'Insurance reversal' wording of the first draft (sign does not flip).",
    check_verdict="PASS-FIX", check_note="wording corrected from 'reversal' to 'attenuation'")

# %% [markdown]
# **So what.** Only 10 % of uninsured adults are 60+, against a third of insured adults, because
# Medicare covers almost everyone over 65. Standardising to the US 2000 age mix shrinks the gap from
# +5.3 pp (1.8–8.8) to +0.7 pp (−2.6–3.9), an attenuation of almost 90 % with the **same sign**: this
# is age confounding, not a Simpson reversal. The age-specific differences are heterogeneous
# (about −1, +6 and −5 pp in the three bands, only the 40–59 one excluding zero), so no single
# "insurance effect" summarises them; the 6-band standard gives a very wide interval because few
# uninsured adults are 70+. By contrast, the *usual place of care* gap survives standardisation
# (+9.4 → +5.3 pp, CI excluding zero) – consistent with a detection pathway (care → diagnosis →
# self-reported diabetes) that S5 examines through the undiagnosed share. For modelling, access
# features must be read conditional on age, and fairness comparisons across insurance groups (S8)
# must control for age before attributing differences to access to care.

# %% [markdown]
# ## Save results and register

# %%
reg_df = pd.DataFrame(REG)
(C.GOVERNANCE_DIR / "register").mkdir(parents=True, exist_ok=True)
reg_df.to_csv(C.GOVERNANCE_DIR / "register" / "S4.csv", index=False)
R.save_section("S4", OUT)
print(f"register rows: {len(reg_df)}; metrics keys: {sorted(OUT)}")
