# %% [markdown]
# # §6 Preparation design
#
# This section turns the findings of §3–§5 into **fourteen switchable preparation steps** (P01–P14),
# groups them into **six reporting blocks** (B1–B6) and fixes the **arms** that §7 compares:
#
# * **M0** – the naive analyst: every column except id/design/label, blanket recode of 7/9/77/99/…,
#   median imputation, one-hot encoding, logistic regression. Leakage included.
# * **M1** – M0 plus the availability rule only (P03). The *naive-minimal* baseline: it keeps the blanket
#   "7/9 = missing" recode that a naive analyst would use (P02 off), so its training label and some feature cells
#   carry the damage measured in §3; evaluation labels are always the clean ones. A comparison with the
#   codebook recode switched on (M1c = M1 + P02) is given in §9 (post-audit corrections).
# * **S** – all steps on (P14 WHtR stays a separate arm).
#
# The headline "minimal vs systematic" comparison is **M1 vs S** (same model); **M0 → M1 is the
# leak gate**. The block hypotheses are locked here (§6.11), before any ablation.

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import hashlib, json, subprocess, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from IPython.display import display
import textwrap

from src import nhanes_io as io, labels as L, prep as P, evalkit as ek

pd.set_option("display.width", 160, "display.max_columns", 30, "display.max_colwidth", 80)
OUT = C.RESULTS_DIR / "S6"
OUT.mkdir(parents=True, exist_ok=True)
S6 = {}

# %% [markdown]
# ## 1 Inputs
# **Why.** Every preparation decision must happen *inside* the model pipeline so that it is refitted in
# each training fold. The pipeline therefore receives the **raw** cohort (XPT artefact not repaired,
# no sentinel recode) and the naive column set. The frozen evaluation label `L_comb` comes from the
# per-variable cohort (§5). Descriptive design statistics below use the **training part** only: the
# 20 % hold-out (label × race stratified, `evalkit.make_holdout`, created once and persisted) is not
# used by any statistic in §6 and is kept out of all fitting; it is scored once, in §9.11 (the internal
# hold-out check). Note that the §4/§5 diagnostics, which ran before the split existed, used all 5,730 adults.

# %%
# Load the raw (unrepaired) and the cleaned cohort, split off the persisted hold-out and build the naive
# Tier 1 / Tier 2 feature frames. Produces S6['inputs']; the hold-out rows are not used in this section.
raw = P.raw_cohort()
clean = L.add_labels(io.build_cohort())
# Guard: raw and cleaned cohorts must be row-aligned, or the frozen label would attach to the wrong person.
assert (raw["SEQN"].to_numpy() == clean["SEQN"].to_numpy()).all()
# The 20 % hold-out is created once and persisted (evalkit.make_holdout); all statistics below use train rows.
train_idx, test_idx = ek.make_holdout(clean)
# reset_index so positional indexing matches the NumPy label arrays used in later cells.
raw_tr, clean_tr = raw.iloc[train_idx].reset_index(drop=True), clean.iloc[train_idx].reset_index(drop=True)
# Naive feature frames before any preparation step: Tier 2 is the wider of the two feature tiers.
X1, X2 = P.raw_feature_frame(raw, 1), P.raw_feature_frame(raw, 2)
X1_tr, X2_tr = X1.iloc[train_idx].reset_index(drop=True), X2.iloc[train_idx].reset_index(drop=True)
# Variable specification table: role, admissibility and dtype per column.
spec = P._spec_by_var()
# Count columns per (role, admissibility): shows what a naive analyst would hand to the model.
roles = spec.loc[X2.columns, ["role", "admissible", "dtype"]].value_counts(["role", "admissible"]).rename("n_columns")
print(f"cohort {len(raw):,} rows; training part {len(train_idx):,}, hold-out {len(test_idx):,} (not used here)")
print(f"naive feature frame: Tier 1 {X1.shape[1]} columns, Tier 2 {X2.shape[1]} columns")
print(roles.to_string())
S6["inputs"] = dict(n_cohort=len(raw), n_train=len(train_idx), n_holdout=len(test_idx),
                    n_raw_cols_t1=X1.shape[1], n_raw_cols_t2=X2.shape[1])

# %% [markdown]
# **So what.** A naive analyst hands the model 52 (Tier 1) or 54 (Tier 2) columns, and the role table shows
# what that includes: leakage items (glucose, treatment, age at diagnosis, DIQ160/DIQ180),
# audit-only variables (race, insurance, usual place of care), side and optional variables. Only the rows
# with admissibility T1/T2 pass the availability rule (§1.3); everything else is a trap that M0 keeps on
# purpose.

# %% [markdown]
# ## 2 Step catalogue
# **Why.** Each step has to be traceable to evidence and must say whether it learns from the data
# (then it is fitted in-fold) and whether it could ever see the label (none may).

# %%
# Collect the evidence numbers cited in the step catalogue from the stored §4/§5 results, so the text
# cannot drift from the analysis, then write and sanity-check results/S6/step_catalogue.csv.
S4dir = C.RESULTS_DIR / "S4"
vif4 = pd.read_csv(S4dir / "vif_table.csv")
lin4 = pd.read_csv(S4dir / "linearity_tests.csv").set_index("variable")
sk4 = pd.read_csv(S4dir / "skew_table.csv")
# Stored AUC results of the Asian-BMI analysis (§5.5), used for the P14 evidence.
auc5 = R.load_section("S5")["asian_bmi"]["auc"]
# VIF of the raw anthropometry set, indexed by variable.
vraw = vif4[vif4["set"] == "raw_anthropometry"].set_index("variable")["vif"]
vbp, vbm = vif4.loc[vif4["set"] == "bp_readings", "vif"], vif4.loc[vif4["set"] == "bp_means", "vif"]
sk_bmi = sk4.query("variable == 'BMXBMI' and subsample == 'cohort'")["skew_raw"].iloc[0]
sk_tg = sk4[(sk4["variable"] == "LBXTLG") & sk4["subsample"].str.startswith("fasting")]["skew_raw"].iloc[0]
# AUC gain of waist-to-height ratio over BMI, per non-Hispanic group (P14 evidence).
gain = {g: auc5[f"NH {g}|WHtR \u2212 BMI (paired)"]["auc"] for g in ("Asian", "White")}
# Evidence strings per step; the data-driven ones are built from stored numbers, not typed by hand.
ev = {
    "P04": f"§4.9: 6 BP readings VIF {vbp.min():.1f}-{vbp.max():.1f} vs means {vbm.max():.1f}; PA skip pattern",
    "P05": f"§4.9: weight VIF {vraw['BMXWT']:.1f}, BMI {vraw['BMXBMI']:.1f}; keep BMI + waist",
    "P06": f"cohort: PIR missing {raw['INDFMPIR'].isna().mean():.1%}; MNAR-suspect list",
    "P08": f"§4.10: |skew| > 1 (BMI {sk_bmi:.2f}, TG {sk_tg:.2f} fasting)",
    "P11": f"prevalence {clean['L_comb'].mean():.1%}; balanced weights",
    "P13": "§4.11: RCS LR chi2 " + ", ".join(f"{lab} {lin4.loc[v, 'chi2']:.1f}" for v, lab in
                                           (("RIDAGEYR", "age"), ("BMXBMI", "BMI"), ("LBDHDD", "HDL"), ("LBXTC", "TC"))),
    "P14": f"§5.5: WHtR-BMI AUC gain Asian {gain['Asian']:+.3f} vs White {gain['White']:+.3f}",
}
catalogue = pd.DataFrame([
    ("P01", "xpt_zero_fix", "B1", "stateless", "§3.1: zero stored as 5.4e-79; mask() keeps NaN"),
    ("P02", "sentinel_by_var", "B1", "stateless", "§3.4: blanket recode wipes valid values; off = blanket (M0)"),
    ("P03", "admissibility", "B2", "stateless", "§1.3 availability rule; spec column `admissible`"),
    ("P04", "aggregate", "B3", "stateless", ev["P04"]),
    ("P05", "prune", "B3", "fitted in-fold (X)", ev["P05"]),
    ("P06", "missing_indicator", "B4", "stateless", ev["P06"]),
    ("P07", "topcode_flag", "B4", "stateless", "§3.6: age top-coded 80, PIR 5"),
    ("P08", "yeo_johnson", "B5", "fitted in-fold (X)", ev["P08"]),
    ("P09", "scale", "B5", "fitted in-fold (X)", "L2 penalty is scale dependent; unscaled fits fail to converge"),
    ("P10", "rare_categories", "B5", "fitted in-fold (X)", "levels < 2 % grouped as infrequent"),
    ("P11", "class_weight", "B6a", "estimator", ev["P11"]),
    ("P12", "survey_weight", "B6b", "estimator", "§4.1: WTPH2YR for HbA1c cohort; mean 1"),
    ("P13", "splines", "B5", "fitted in-fold (X)", ev["P13"]),
    ("P14", "whtr", "(arm)", "stateless", ev["P14"]),
], columns=["step", "name", "block", "learns from", "evidence"])
# Catalogue order must equal the step registry in src/prep.py, so the table cannot omit or reorder a step.
assert list(catalogue["step"]) == list(P.STEPS)
# Block labels must match prep.STEP_BLOCK; P14 is its own arm, not a block, hence the (arm) exception.
assert all(P.STEP_BLOCK[s] == b or b == "(arm)" for s, b in zip(catalogue["step"], catalogue["block"]))
catalogue.to_csv(OUT / "step_catalogue.csv", index=False)
display(catalogue)

# %% [markdown]
# **So what.** Seven steps are stateless, five are fitted on the training fold's **features** only, and two act
# on the estimator. No step uses the label – §6.10 tests this with a random label. Two steps are
# *switches* rather than on/off toggles because M0 already does something at that point: P02 (off = blanket
# recode) and P10 (off = plain one-hot).

# %% [markdown]
# ## 3 B1 integrity: XPT zeros and sentinel codes
# **Why.** §3.1 and §3.4 showed that the XPT reader turns stored zeros into 5.4e-79 and that a blanket recode destroys
# valid measurements – including HbA1c 7.0 % and 9.0 % before the naive label is formed. P01/P02 repair both.

# %%
# Quantify the B1 damage on the Tier-1 training frame: stored-zero artefacts, valid values wiped by the
# blanket recode and label flips. Reads raw/clean cohorts; writes S6['B1'] and asserts frozen counts.
x_fixed = P.XptZeroFix().transform(X1_tr)
# Numeric columns only: XPT zeros are float artefacts.
num = X1_tr.select_dtypes("number")
# Artefact = a non-zero value smaller than C.XPT_ZERO_EPS in absolute size (the reader stores 0 as ~5e-79).
art = ((num.abs() < C.XPT_ZERO_EPS) & num.notna() & (num != 0)).sum()
n_artefact = int(art.sum())
agg_off = P.Aggregate().transform(P.Sentinels("per_variable").transform(X1_tr))  # P01 off, P04 on
agg_on = P.Aggregate().transform(P.Sentinels("per_variable").transform(x_fixed))
# Cells that are NaN only because the XPT zero was not repaired: 'zero sessions' failed an equality test.
pa_lost = int((agg_on["pa_mod_min_wk"].eq(0) & agg_off["pa_mod_min_wk"].isna()).sum())
pv = P.Sentinels("per_variable").transform(x_fixed)
# Blanket recode turns every 7/9/77/99/... into NaN, including values that are genuine measurements.
bl = P.Sentinels("blanket").transform(x_fixed)
# Valid under the per-variable rules but NaN under the blanket recode = valid values destroyed.
wiped = (bl.isna() & pv.notna()).sum()
wiped = wiped[wiped > 0].sort_values(ascending=False)
# Naive label: all steps off, so the HbA1c cut-off is applied after the blanket recode.
y_naive_all = P.training_label(raw, P.ALL_OFF)
# Frozen evaluation label (per-variable cohort), used as the reference.
y_true_all = clean["L_comb"].to_numpy()
# Number of people whose naive label differs from the frozen L_comb label.
flips = int((y_naive_all != y_true_all).sum())
# HbA1c-positive people whose HbA1c is a blanket code (e.g. 7.0 or 9.0 %), hence lost by the naive recode.
a1c_lost = int((clean["L_A1c"].eq(1) & raw["LBXGH"].isin(io.BLANKET_CODES)).sum())
print(f"P01: {n_artefact:,} artefact cells (0 < |x| < 1e-10) in the Tier-1 training frame: {art[art > 0].to_dict()}")
print(f"P01 x P04: without the fix, 'frequency == 0' fails, so {pa_lost:,} non-exercisers get NaN instead of 0 weekly minutes")
print(f"P02: blanket recode wipes {int(wiped.sum()):,} valid values in {len(wiped)} feature columns (training part):")
print(wiped.head(12).to_string())
print(f"label: L_comb positives per-variable {y_true_all.sum()}, naive {y_naive_all.sum()}; "
      f"{a1c_lost} HbA1c positives lost, {flips} L_comb labels flip (whole cohort)")
# Guard: these counts are fixed by the cohort build; a change means the cohort or label logic has moved.
assert flips == 6 and a1c_lost == 29 and y_true_all.sum() == 971
S6["B1"] = dict(n_artefact_cells_train_t1=n_artefact, artefact_by_column=art[art > 0].to_dict(), pa_zero_lost_without_p01=pa_lost, n_blanket_wiped_train_t1=int(wiped.sum()),
                wiped_by_column=wiped.to_dict(), label_flips=flips, a1c_positives_lost=a1c_lost,
                naive_lcomb_pos=int(y_naive_all.sum()))

# %% [markdown]
# **So what.** Without P01 every equality test on zero fails, so the "0 sessions → 0 minutes" rule silently turns the
# printed non-exercisers into missing values; the blanket recode costs the naive label 29 HbA1c-based positives (6 not
# rescued by self-report), consistent with §3.4. Expected AUC effect: small (B1).

# %% [markdown]
# ## 4 B2 admissibility (availability rule)
# **Why.** The use case is screening *before any glucose test*, so a feature is admissible only if it exists at that
# moment (§1.3); the rule is applied from the specification.

# %%
# Which columns does the P03 availability rule remove, per tier? Compares the rule with the specification
# table and writes results/S6/p03_excluded.csv. Asserts the rule drops every item listed in §1.3.
rows = []
for tier, X in ((1, X1), (2, X2)):
    # Columns that survive P03; the rest are recorded with role and reason.
    kept = P.Admissibility(tier).transform(X).columns
    for c in X.columns:
        if c not in kept:
            rows.append({"tier": tier, "column": c, "role": spec.loc[c, "role"],
                         "admissible": spec.loc[c, "admissible"], "reason": spec.loc[c, "admiss_reason"][:70]})
p03 = pd.DataFrame(rows)
p03.to_csv(OUT / "p03_excluded.csv", index=False)
excl_t1 = set(p03.loc[p03["tier"] == 1, "column"])
# Every column the §1.3 list names must really be dropped (checks the code against the spec).
missing_from_rule = [v for v in P.P03_EXCLUDED if v in X1.columns and v not in excl_t1]
assert not missing_from_rule, missing_from_rule
# LBXGH (HbA1c) defines the label, so it is not in the feature frame at all rather than dropped by P03.
assert set(P.P03_EXCLUDED) - set(X1.columns) == {"LBXGH"}  # LBXGH defines the label, never a feature
# P03 must never drop an admissible column: every removed item is flagged inadmissible ('N') in the spec.
assert (p03["admissible"] == "N").all()
kept_t1 = sorted(P.Admissibility(1).transform(X1).columns)
print(f"P03 removes {len(excl_t1)} of {X1.shape[1]} Tier-1 columns; kept ({len(kept_t1)}):")
print(textwrap.fill(", ".join(kept_t1), width=110, initial_indent="  ", subsequent_indent="  "))
print(p03[p03["tier"] == 1].groupby("role")["column"].apply(list).to_string())
S6["B2"] = dict(n_excluded_t1=len(excl_t1), n_kept_t1=len(kept_t1), kept_t1=kept_t1,
                excluded_t1=sorted(excl_t1))

# %% [markdown]
# **So what.** P03 removes the glucose test, treatment and diagnosis history (leakage) and the audit-only race, insurance
# and access items; the explicit §1.3 list is contained (asserted). The care traces BPQ020/BPQ080 stay, and the
# **T1-minus-care** arm removes them so §7 can measure "being known to the health system".

# %% [markdown]
# ## 5 B3 redundancy: aggregation and pruning
# **Why.** §4.9 found the six BP readings and the weight–height–BMI formula collinear, and the activity block has a skip
# pattern: non-exercisers are never asked a session length, so median imputation would give them one.

# %%
# Show why B3 is needed: the physical-activity skip pattern and the VIF of the continuous Tier-1 inputs before
# and after in-fold pruning. Writes results/S6/vif_in_pipeline.csv and S6['B3'].
xpv = P.Sentinels("per_variable").transform(P.XptZeroFix().transform(X1_tr))
# Skip pattern: zero sessions means the duration was never asked, so it is NaN by design, not unknown.
skip_mod = int((xpv["PAD790Q"].eq(0) & xpv["PAD800"].isna()).sum())
skip_vig = int((xpv["PAD810Q"].eq(0) & xpv["PAD820"].isna()).sum())
# Median that a naive imputer would hand to these non-exercisers.
med_mod = float(xpv["PAD800"].median())
agg = P.Aggregate().transform(P.Admissibility(1).transform(xpv))
# Run only P01-P04 (repair, admissibility, aggregation) so the VIFs reflect the pipeline's own inputs.
pre = Pipeline(P.preprocessor_steps(P.make_cfg(["P01", "P02", "P03", "P04"]), 1)).fit_transform(X1_tr)
# Continuous columns only: VIF is undefined for one-hot dummies.
cont = P._continuous(pre)
vif_before = P.vif_table(pre[cont]).sort_values(ascending=False)
# Fit the in-fold pruning step once on the training part; dropped_ lists the removed columns.
pr = P.VIFPrune().fit(pre)
# Recompute VIF on the surviving continuous columns to confirm the pruning worked.
vif_after = P.vif_table(pr.transform(pre)[[c for c in cont if c not in dict(pr.dropped_)]]).sort_values(ascending=False)
# VIF among the six raw BP readings, to compare with the BP means made by P04.
raw6 = P.vif_table(xpv[list(io.BP_SYS) + list(io.BP_DIA)])
vif_tab = pd.DataFrame({"vif_before_prune": vif_before, "vif_after_prune": vif_after}).round(2)
vif_tab.to_csv(OUT / "vif_in_pipeline.csv")
print(f"PA skip pattern: {skip_mod:,} with 0 moderate sessions and no duration (naive median would impute {med_mod:.0f} min); "
      f"{skip_vig:,} for vigorous")
print(f"weekly moderate minutes: median {agg['pa_mod_min_wk'].median():.0f}, share 0 = {agg['pa_mod_min_wk'].eq(0).mean():.1%}")
print(f"6 raw BP readings: VIF {raw6.min():.1f}-{raw6.max():.1f}")
print(f"P05 drops: {pr.dropped_}")
display(vif_tab)
S6["B3"] = dict(pa_skip_moderate=skip_mod, pa_skip_vigorous=skip_vig, pa_naive_median_minutes=med_mod,
                vif_bp_raw_min=float(raw6.min()), vif_bp_raw_max=float(raw6.max()),
                p05_dropped={c: v for c, v in pr.dropped_},
                vif_max_after=float(vif_after.max()))

# %% [markdown]
# **So what.** These VIFs are computed on the training part with *all* continuous Tier-1 inputs together, so they differ
# from §4.9's block-wise cohort VIFs: the BP means sit at about 2.3, and in-fold pruning (threshold 10, BMI and waist
# protected) removes **weight** only (BMI VIF 62 → 9.7). Weekly minutes turn the skip gap into a true zero for about a
# fifth of the training part. B3 expects the same AUC but a more stable BMI coefficient.

# %% [markdown]
# ## 6 B4 missingness: indicators and top-codes
# **Why.** A missing-value indicator only helps when missingness is informative (Groenwold et al. 2012); the table
# relates candidate missingness to the label in the training part (descriptive, hence `descriptive_seen` for B4).

# %%
# Relate candidate missingness to the label (descriptive only) to decide whether a missing indicator (P06)
# can help. Writes results/S6/mnar_candidates.csv and S6['B4'].
agg2 = P.Aggregate().transform(P.Admissibility(2).transform(
    P.Sentinels("per_variable").transform(P.XptZeroFix().transform(X2_tr))))
# Label of the training part; used here only to describe prevalence, never to fit anything.
ytr = clean_tr["L_comb"].to_numpy()
mrows = []
# MNAR_SUSPECT = columns whose missingness might itself carry signal (missing not at random).
for c in P.MNAR_SUSPECT:
    # m is True where the value is missing; prevalence is compared between missing and observed rows.
    m = agg2[c].isna().to_numpy()
    mrows.append({"column": c, "n_missing": int(m.sum()), "share_missing": m.mean(),
                  "prev_if_missing": ytr[m].mean() if m.any() else np.nan, "prev_if_observed": ytr[~m].mean()})
mnar = pd.DataFrame(mrows).round(3)
mnar.to_csv(OUT / "mnar_candidates.csv", index=False)
# Top-codes: age is censored at 80 and the income-to-poverty ratio (PIR) at 5 in the public files.
n_age80 = int(xpv["RIDAGEYR"].eq(80).sum()); n_pir5 = int(xpv["INDFMPIR"].eq(5).sum())
print(mnar.to_string(index=False))
print(f"top-codes in training part: age 80 = {n_age80}, PIR 5 = {n_pir5}")
S6["B4"] = dict(mnar=mnar.set_index("column").to_dict("index"), n_age_top=n_age80, n_pir_top=n_pir5)

# %% [markdown]
# **So what.** Missing waist is informative (prevalence 29.8 % vs 16.4 %), missing income almost not (17.4 % vs 16.9 %), so
# the calibration benefit predicted for B4 is less likely than drafted; top-code flags treat "80+" and "5+" as categories.

# %% [markdown]
# ## 7 B5 representation: skewness, splines, scaling, rare levels
# **Why.** §4.10–§4.11 found right skew and curved relations for age and BMI (HDL/TC in Tier 2); splines keep the
# model a GLM, and Yeo-Johnson is fitted in-fold on columns with |skew| > 1 that are not splined.

# %%
# Fit the B5 representation steps on the training part (no model): skewness before and after Yeo-Johnson,
# spline settings and rare category levels. Writes S6['B5'].
pre_s = Pipeline(P.preprocessor_steps(P.make_cfg(["P01", "P02", "P03", "P04", "P05", "P06", "P07"]), 2)[:-1]).fit_transform(X2_tr)   # before encoding
# Yeo-Johnson (P08) is fitted on non-splined columns; spline columns are excluded from the power transform.
yj = P.YeoJohnson(exclude=P.SPLINE_COLS[2]).fit(pre_s)
skew = pd.Series(yj.skew_).round(2).sort_values(key=abs, ascending=False)
# Refit and transform to check that skewness is removed after P08.
after = P.YeoJohnson(exclude=P.SPLINE_COLS[2]).fit(pre_s).transform(pre_s)
skew_after = {c: float(pd.Series(after[c]).skew()) for c in yj.cols_}
# Categorical columns are the only ones P10 can group.
cat_cols = [c for c in pre_s.columns if P._is_cat(pre_s, c)]
# Rare level = category with a relative frequency below P.RARE_MIN_FREQ (the 2 % rule of P10).
rare = {c: [str(k) for k, v in pre_s[c].value_counts(normalize=True).items() if v < P.RARE_MIN_FREQ] for c in cat_cols}
rare = {c: v for c, v in rare.items() if v}
# Same check with the aggregation step P04 switched off, to show that P04 is what removes the rare levels.
pre_nop4 = Pipeline(P.preprocessor_steps(P.make_cfg(["P01", "P02", "P03", "P05", "P06", "P07"]), 2)[:-1]).fit_transform(X2_tr)
rare_nop4 = {c: [f"{k} ({v:.1%})" for k, v in pre_nop4[c].value_counts(normalize=True).items() if v < P.RARE_MIN_FREQ]
             for c in pre_nop4.columns if P._is_cat(pre_nop4, c)}
rare_nop4 = {c: v for c, v in rare_nop4.items() if v}
print("training-fold skewness (Tier 2, before P08):"); print(skew.to_string())
print(f"P08 transforms {yj.cols_}; skewness after: { {k: round(v, 2) for k, v in skew_after.items()} }")
print("P13 splines:", "; ".join(f"Tier {k}: {', '.join(v)}" for k, v in P.SPLINE_COLS.items()))
print("    settings:", ", ".join(f"{k}={v}" for k, v in C.SPLINE_KW.items()))
print(f"P10 levels below {P.RARE_MIN_FREQ:.0%} with P04 on: {rare or 'none'}")
print(f"P10 levels below {P.RARE_MIN_FREQ:.0%} with P04 off:")
for c_, v_ in rare_nop4.items():
    print(textwrap.fill(f"{c_}: {', '.join(v_)}", width=110, initial_indent="  ", subsequent_indent="    "))
S6["B5"] = dict(skew=skew.to_dict(), yj_columns=yj.cols_, skew_after_yj=skew_after,
                spline_cols={k: list(v) for k, v in P.SPLINE_COLS.items()}, spline_kw=C.SPLINE_KW, rare_levels=rare, rare_levels_without_p04=rare_nop4)

# %% [markdown]
# **So what.** Only activity minutes and hip circumference exceed |skew| = 1 once BMI is splined, and Yeo-Johnson makes
# them nearly symmetric; P10 is inert in S (no rare level with P04 on), and P08/P09 must leave tree predictions
# unchanged (§6.10).

# %% [markdown]
# ## 8 B6 class and survey weights
# **Why.** `class_weight='balanced'` (P11) trades calibration for sensitivity at threshold 0.5; survey weights (P12,
# WTPH2YR) make the fit target the population (60+: 46.2 % of the sample vs 31.4 % weighted, §1.10).

# %%
# Describe the two B6 weights on the training part: balanced class weights (P11) and survey weights (P12).
# Writes S6['B6']; nothing is fitted here.
w = P.survey_weights(raw_tr)
# Kish effective sample size (sum w)^2 / sum w^2; design effect = n / n_eff (information lost to weighting).
kish = float(w.sum() ** 2 / (w ** 2).sum())
# Balanced weights give each class a total weight of 0.5, so a positive counts 0.5 / prevalence times.
print(f"training prevalence of L_comb: {ytr.mean():.3f}; balanced weights: positives x{0.5 / ytr.mean():.2f}, negatives x{0.5 / (1 - ytr.mean()):.2f}")
print(f"WTPH2YR / mean: min {w.min():.2f}, max {w.max():.2f}; Kish effective n {kish:,.0f} of {len(w):,} (deff {len(w) / kish:.2f})")
S6["B6"] = dict(train_prevalence=float(ytr.mean()), w_min=float(w.min()), w_max=float(w.max()),
                kish_neff=kish, kish_deff=len(w) / kish)

# %% [markdown]
# **So what.** Class weights multiply each positive by about 3, so the Brier score should worsen at equal AUC (B6a);
# survey weights cut the effective sample by about a third, so B6b expects at most a small unweighted-AUC loss.

# %% [markdown]
# ## 9 Arms
# **Why.** The comparison logic must be fixed before results exist: the cumulative path
# M0 → +B2 (= M1) → +B1 → +B3 → +B4 → +B5 → +B6a → +B6b (= S), leave-one-block-out arms S−Bk (the primary
# block evidence), T1-minus-care, S-linear (splines off), S-linear-B3 (its coefficient-stability companion) and S+WHtR.

# %%
# Build the arm table (which steps are on in each experimental arm) and count the design-matrix width of
# every arm per tier. Only preprocessing is fitted here, never a model. Writes results/S6/arm_table.csv.
arms = P.arm_table()
arms.to_csv(OUT / "arm_table.csv")
# nfeat[(arm, tier)] = number of columns after the arm's preprocessing, fitted on the training part.
nfeat = {}
for a, cfg in P.ARMS.items():
    for t, X in ((1, X1_tr), (2, X2_tr)):
        nfeat[(a, t)] = Pipeline(P.preprocessor_steps(cfg, t)).fit_transform(X).shape[1]
# Reshape (arm, tier) pairs into one row per arm with a column per tier.
nfeat = pd.Series(nfeat).unstack().rename(columns={1: "n_features_T1", 2: "n_features_T2"})
display(arms.join(nfeat))
S6["arms"] = {a: {**{k: bool(v) for k, v in c.items()}, "n_features_t1": int(nfeat.loc[a, "n_features_T1"]),
                  "n_features_t2": int(nfeat.loc[a, "n_features_T2"])} for a, c in P.ARMS.items()}

# Heat map of arms (rows) by preparation steps (columns): blue = step switched on.
fig, ax = plt.subplots(figsize=(9.5, 6.2))
mat = arms[list(P.STEPS) + ["NO_CARE"]]
# Two-colour map: light grey for off (0), Okabe-Ito blue for on (1); colour-blind safe.
ax.imshow(mat.to_numpy(), cmap=plt.matplotlib.colors.ListedColormap(["#f2f2f2", C.OKABE_ITO["blue"]]), aspect="auto")
ax.set_xticks(range(mat.shape[1]), [f"{s}\n{P.STEP_BLOCK.get(s, 'opt')}" for s in mat.columns], fontsize=8)
ax.set_yticks(range(mat.shape[0]), [f"{a}  ({nfeat.loc[a, 'n_features_T1']} feat.)" for a in mat.index], fontsize=8)
ax.grid(False)
ax.set_title("Arms × preparation steps (blue = on; Tier-1 design-matrix width in brackets)")
plots.savefig(fig, "S6_arm_matrix", caption="Which preparation steps are switched on in each experimental arm (blue). "
              "M0 = naive with leakage, M1 = availability rule only, S = all steps; S-Bk = leave-one-block-out.")
plt.show()

# %% [markdown]
# **So what.** M0 feeds 88 columns (Tier 1) to the model, M1 46 and S 42. S is *narrower* than M1 although it adds
# spline bases, indicators and flags, because aggregation and pruning remove redundant columns. Every arm
# differs from its comparator in exactly the steps named in its label, which is what makes the paired
# differences in §7 interpretable.

# %% [markdown]
# ## 10 Pipeline assertions
# **Why.** The ablation is only meaningful if the switches do what they claim. Four checks:
# (a) all switches off reproduces an independently written naive M0; (b) P08/P09 do not change a tree's
# predictions; (c) no preparation step reads the label; (d) a disabled Toggle is exactly the identity.

# %%
# Four assertions about the switch machinery: M0 equivalence, tree invariance to P08/P09, no step reads y,
# and the identity of a disabled Toggle. Any failure stops the notebook. Writes S6['assertions'].
checks = {}
for t, X in ((1, X1_tr), (2, X2_tr)):
    # (a) With every switch off, the switch machinery must reproduce an independently written naive M0.
    y0 = P.training_label(raw_tr, P.ALL_OFF)
    with warnings.catch_warnings():
        # Unscaled logistic fits warn about convergence; that is expected for M0 and not what is tested here.
        warnings.simplefilter("ignore")
        # a = switchable pipeline with all steps off; b = independent reference implementation.
        a = P.build_pipeline(P.ALL_OFF, t).fit(X, y0).predict_proba(X)[:, 1]
        b = P.naive_m0_reference(t, X).fit(X, y0).predict_proba(X)[:, 1]
    checks[f"m0_equiv_T{t}_maxabs"] = float(np.abs(a - b).max())
    # Tolerance 1e-9: both fits are deterministic, so only floating-point noise is allowed.
    assert checks[f"m0_equiv_T{t}_maxabs"] < 1e-9

# (b) Trees are invariant to monotone transforms, so P08 (power) and P09 (scale) must not change them.
ys = P.training_label(raw_tr, P.ARMS["S"])
tree_s = P.build_pipeline(P.ARMS["S"], 1, model="tree").fit(X1_tr, ys).predict_proba(X1_tr)[:, 1]
cfg_nt = {**P.ARMS["S"], "P08": False, "P09": False}
tree_n = P.build_pipeline(cfg_nt, 1, model="tree").fit(X1_tr, ys).predict_proba(X1_tr)[:, 1]
checks["tree_p08_p09_maxabs"] = float(np.abs(tree_s - tree_n).max())
# Exact equality, not a tolerance: monotone transforms leave tree splits and thus predictions unchanged.
assert checks["tree_p08_p09_maxabs"] == 0.0

# (c) Leakage guard: a preparation step must not read the label. Compare designs fitted with the true label
# and with a permuted label; a seed derived from the master seed keeps the permutation reproducible.
rng = np.random.default_rng(ek.derive_seed(C.SEED_MASTER, "S6", "random_y"))
y_rand = rng.permutation(ys)
for t, X in ((1, X1_tr), (2, X2_tr)):
    # Three arms: S and S+WHtR (all steps on, without and with P14) and M1 (availability rule only).
    for cfg_name in ("S", "S+WHtR", "M1"):
        pre = lambda: Pipeline(P.preprocessor_steps(P.ARMS[cfg_name], t))
        # za / zb = design matrices from fitting on the true / permuted label; they must be bit-identical.
        za, zb = pre().fit(X, ys).transform(X), pre().fit(X, y_rand).transform(X)
        assert za.columns.equals(zb.columns) and np.array_equal(za.to_numpy(float), zb.to_numpy(float), equal_nan=True)
checks["no_step_reads_y"] = True

# (d) A Toggle that is switched off must pass its input through untouched (same object, not a copy).
for name, step in [("P01", P.XptZeroFix()), ("P03", P.Admissibility(1)), ("P04", P.Aggregate()),
                   ("P05", P.VIFPrune()), ("P06", P.MissingIndicator()), ("P07", P.TopcodeFlags()),
                   ("P08", P.YeoJohnson()), ("P09", P.Scale()), ("P13", P.Splines(("RIDAGEYR",))), ("P14", P.WHtR())]:
    tog = P.Toggle(step, enabled=False).fit(X1_tr)
    assert tog.transform(X1_tr) is X1_tr
checks["disabled_toggle_is_identity"] = True
print(json.dumps(checks, indent=1))
S6["assertions"] = checks

# %% [markdown]
# **So what.** All four checks pass: (a) the switch machinery with everything off reproduces the naive M0 to machine
# precision (max |Δp| printed), so "M0" in §7 is the naive analyst and not an artefact of our code; (b) the tree
# arm is exactly invariant to P08/P09, as monotone transforms must be; (c) fitting the preparation on a permuted
# label gives bit-identical design matrices for S, S+WHtR and M1 – no step peeks at y; (d) disabled toggles
# return their input unchanged.

# %% [markdown]
# ## 11 Hypotheses and pre-registration lock
# **Why.** A block ablation tempts post-hoc storytelling. The block hypotheses (direction, magnitude, SESOI,
# falsifier and honest `prior_exposure`) and the verdict rules are therefore written to
# `governance/hypotheses.md` and locked by a dedicated commit **before** the first ablation result is
# committed. The lock is the file's SHA-256 recorded in that commit; git history shows the order. Besides the three
# exposure labels of §1.5, block hypotheses may carry `prototype_seen` = the pattern was seen in the pilot analysis.

# %%
# Parse the hypotheses table from governance/hypotheses.md, check its structure and verify the
# pre-registration lock via git history (lock commit, SHA-256, order versus the first ablation commit).
HYP = C.GOVERNANCE_DIR / "hypotheses.md"
text = HYP.read_text(encoding="utf-8")
# Table rows start with '| '; skip the header row and the markdown separator row.
rows = [l for l in text.splitlines() if l.startswith("| ") and not l.startswith("| hyp_id") and not l.startswith("|---")]
import re
# Split on pipes that are not escaped (backslash-pipe); keep the first 10 columns.
hyp = pd.DataFrame([[c.strip() for c in re.split(r"(?<!\\)\|", l.strip().strip("|"))][:10] for l in rows],
                   columns=["hyp_id", "rq_or_block", "statement", "metric", "direction", "magnitude", "sesoi",
                            "falsifier", "prior_exposure", "weights"])
# Block-level hypotheses: B1..B6b, B2t and the P14 arm.
blocks_h = hyp[hyp["hyp_id"].str.match(r"^(B\d|P14)")]
# Guard: all nine block hypotheses must be present in the locked file.
assert set(blocks_h["hyp_id"]) >= {"B1", "B2", "B2t", "B3", "B4", "B5", "B6a", "B6b", "P14"}
# Guard: every hypothesis declares how much the authors had already seen (the allowed exposure labels only).
assert blocks_h["prior_exposure"].str.match(r"^(none|analysis_seen|descriptive_seen|prototype_seen)").all()
_show = blocks_h.assign(prior=blocks_h["prior_exposure"].str.split(" ").str[0], sesoi=blocks_h["sesoi"].str[:40])
display(_show[["hyp_id", "direction", "sesoi", "prior"]])
print("\nprior_exposure counts (all hypotheses):", hyp["prior_exposure"].str.split(" ").str[0].value_counts().to_dict())

# SHA-256 of the file as it is now; compared below with the hash recorded in the lock commit.
sha_now = hashlib.sha256(HYP.read_bytes()).hexdigest()
LOCK_FILE = OUT / "prereg_lock.json"
lock = None
# Look up the lock commit in git history; fails softly when git or the repository is unavailable.
try:
    # --fixed-strings: the marker contains parentheses, which must not be read as a regex.
    log = subprocess.run(["git", "log", "--format=%H%x1f%cI%x1f%B%x1e", "--grep=lock hypotheses.md (prereg-lock)",
                          "--fixed-strings", "--", "governance/hypotheses.md"],
                         cwd=C.ROOT, capture_output=True, text=True, check=True).stdout
    # Entries end with the record separator (0x1e); the oldest match (last in log order) is the lock.
    entries = [e.strip("\n") for e in log.split("\x1e") if e.strip()]
    if entries:
        h, ts, body = entries[-1].split("\x1f")
        # The commit message records the SHA-256 as a 64-character hexadecimal word.
        recorded = next(w for w in body.split() if len(w) == 64 and all(ch in "0123456789abcdef" for ch in w))
        # Re-hash the file as stored in the lock commit rather than trusting the message alone.
        locked_bytes = subprocess.run(["git", "show", f"{h}:governance/hypotheses.md"], cwd=C.ROOT,
                                      capture_output=True, check=True).stdout
        sha_locked = hashlib.sha256(locked_bytes).hexdigest()
        # Governance guard: the recorded hash must equal the real hash of the file at the lock commit.
        assert sha_locked == recorded, "hypotheses.md at the lock commit does not match the recorded SHA-256"
        # First ablation-results commit, used to prove the lock came earlier.
        first_exp = subprocess.run(["git", "log", "--reverse", "--format=%H %cI", r"--grep=^exp\(S7\)", "-E"],
                                   cwd=C.ROOT, capture_output=True, text=True).stdout.split("\n")[0].split()
        lock = dict(commit=h, timestamp=ts, sha256=sha_locked, first_exp_commit=first_exp[0] if first_exp else None,
                    first_exp_timestamp=first_exp[1] if first_exp else None)
        if first_exp:
            # Guard: the lock commit must precede the first ablation commit (hypotheses fixed first).
            assert subprocess.run(["git", "merge-base", "--is-ancestor", h, first_exp[0]], cwd=C.ROOT).returncode == 0, \
                "first exp(S7) commit does not descend from the lock commit"
        LOCK_FILE.write_text(json.dumps(lock, indent=1), encoding="utf-8")
# No git available (e.g. assembled notebook run elsewhere): fall back to the stored record below.
except (OSError, subprocess.CalledProcessError, StopIteration):
    pass
# Fallback: use the lock record stored with the results.
if lock is None and LOCK_FILE.exists():   # no git available (e.g. the assembled notebook): use the stored record
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
if lock:
    print(f"\nprereg-lock commit {lock['commit'][:12]}  at {lock['timestamp']}")
    print(f"SHA-256 at lock   {lock['sha256']}")
    print(f"SHA-256 now       {sha_now}  ({'unchanged' if sha_now == lock['sha256'] else 'post-lock amendments appended'})")
    print(f"first exp(S7) commit: {lock.get('first_exp_commit') or 'none yet'} {lock.get('first_exp_timestamp') or ''}")
else:
    print(f"\nNOT YET LOCKED – current SHA-256 {sha_now}")
S6["hypotheses"] = dict(n_total=len(hyp), block_ids=list(blocks_h["hyp_id"]), sha256_now=sha_now, lock=lock)

# %% [markdown]
# **So what.** Nine block-level hypotheses join the eight scope hypotheses. Only B2t, B6a and B6b are genuine
# pre-registrations (`none`); B1 rests on damage counted in §3.4/§6.3, B2 and B3 on an earlier pilot analysis, B4
# on the missingness table of §6.6, B5 on the linearity tests of §4.11 and P14 on the single-feature AUCs of §5.5 –
# all disclosed. The lock commit, its timestamp and the SHA-256 recomputed from that commit are printed above; §7
# results were committed only after it.

# %% [markdown]
# ## 12 Outputs
#
# Decisions of this section (`governance/register/S6.csv`) and the stored results (`results/metrics_S6.json`,
# `results/S6/`).

# %%
# Display the decisions register for this section and write the section results JSON.
reg = pd.read_csv(C.GOVERNANCE_DIR / "register" / "S6.csv")
display(reg[["dr_id", "type", "decision"]])
R.save_section("S6", S6)
print("saved results/metrics_S6.json")
