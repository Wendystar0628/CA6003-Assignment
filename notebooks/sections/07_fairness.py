# %% [markdown]
# # §8 Fairness and the 3 × 3 Label Matrix
#
# §5 showed that the label and one feature are measured unevenly across groups: self-report misses the 152
# undiagnosed people, who are more often uninsured or without a usual place of care, and BMI under-reads adiposity in
# Asian adults. This section checks whether those biases **carry over into the model**:
#
# 1. **Group audit** (§8.1–§8.5) – error rates of arm S by race, insurance, access, income and sex at one threshold, with
#    bootstrap intervals, small-cell suppression and a permutation baseline.
# 2. **3 × 3 label matrix** (§8.6–§8.7, pre-registered H3) – one pipeline trained on three labels and scored on three
#    kinds of diabetes, plus an access-proxy audit arm.
# 3. **Mitigation** (§8.8–§8.12) – reweighing, the WHtR fix (P14-b), group thresholds, the trade-off and calibration.
#
# Everything uses the out-of-fold predictions of the **training part** on the §7 folds; the hold-out is not read. Race,
# insurance and access never enter a prediction model (§1 availability rule): they are audit variables only.

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import json, os, time, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import nhanes_io as io, labels as L, prep as P, evalkit as ek, survey as SV, fairness as F

from IPython.display import display
pd.set_option("display.width", 150, "display.max_columns", 30, "display.max_colwidth", 60)


def show(df, digits=3):
    """Display a table as HTML (long text wraps; keeps the text output narrow)."""
    display(df.style.hide(axis="index").format(precision=digits, na_rep="")
            .set_properties(**{"text-align": "left", "white-space": "normal"}))

OUT = C.RESULTS_DIR / "S8"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTHONWARNINGS", "ignore::UserWarning")
N_JOBS = min(12, max(1, (os.cpu_count() or 2) - 2))
N_PERM_GROUP = 200          # group-label permutations for the fairness null (§8.3)
SPEC = C.SPEC_FIXED
GAP, GAP_SUB = C.SESOI["group_tpr_gap"], C.SESOI["group_tpr_gap_substantive"]
AUC_SESOI = C.SESOI["roc_auc"]
T_START = time.time()
S8 = {"mode": C.NB_MODE, "cv": f"{C.CV_SPLITS}x{C.CV_REPEATS}", "n_boot": C.N_BOOT, "n_perm_group": N_PERM_GROUP,
      "spec": SPEC}
print(f"mode {C.NB_MODE}: {C.CV_SPLITS}x{C.CV_REPEATS} CV, B = {C.N_BOOT}, {N_PERM_GROUP} group permutations, {N_JOBS} workers")

# %% [markdown]
# ## 0 Setup
# **Why.** The audit must evaluate exactly the predictions that §7 judged. The stored hold-out split and folds are
# re-verified, the OOF file is checked against the folds, and one fold of arm S is refitted to prove that a refit
# reproduces the stored predictions, so the new arms below (other labels, reweighing) are paired with S on equal terms.

# %%
# Re-verify the stored hold-out split, folds and OOF file, then refit one fold of arm S to prove that a refit
# reproduces the stored predictions. Reads results/oof_predictions.parquet and the §7 metrics; writes nothing.
# raw: input of every arm (no XPT repair, no sentinel recode; the pipeline cleans inside each fold).
raw = P.raw_cohort()
# clean: the cleaned cohort with the labels added.
clean = L.add_labels(io.build_cohort())
# Guard: raw and clean must list the same participants in the same order.
assert (raw["SEQN"].to_numpy() == clean["SEQN"].to_numpy()).all()
# Stored stratified hold-out; only the training part (tr) is used here, the hold-out is never read.
tr, te = ek.make_holdout(clean)
raw_tr = raw.iloc[tr].reset_index(drop=True)
cl = clean.iloc[tr].reset_index(drop=True)
# Tier 1 feature frame: the admissible variables of the availability rule.
X1 = P.raw_feature_frame(raw_tr, 1)
# y: the frozen combined label L_comb on the training part.
y = cl["L_comb"].to_numpy().astype(int)
# E-SCREEN: membership flag of the screening use-case population and its own label.
esc = cl["in_escreen"].eq(1).to_numpy()
y_esc = cl["y_escreen"].fillna(0).astype(int).to_numpy()
# 3 x 3 stratum of each row: stratifies the CV folds and defines the label-matrix columns (§8.6).
strat = cl["stratum_3x3"].astype(str).to_numpy()
# Same repeated stratified folds as §7; their hash is compared with the stored one below.
folds = ek.make_folds(y, strat)
n = len(y)
# Per-fold test and training sizes, needed by the Nadeau-Bengio corrected t-test (§8.8).
n_test_fold, n_train_fold = n / C.CV_SPLITS, n - n / C.CV_SPLITS
# Audit-group labels per row (race, insurance, low access, income band, sex): audit variables only.
grp = F.audit_groups(cl)
# The stored §7 metrics supply the regularisation constant C0 and the folds hash.
S7m = R.load_section("S7")
C0 = float(S7m["C0"]["C0"])
# Guard: the folds rebuilt here are those §7 used (hash prefix); FAST mode uses fewer repeats, so skipped.
assert folds.hash[:16] == S7m["splits"]["folds_hash"][:16] or C.NB_MODE == "FAST"

# Stored out-of-fold probabilities of every arm, tier and model from §7.
oof_all = pd.read_parquet(C.RESULTS_DIR / "oof_predictions.parquet")
oof_all = oof_all[oof_all["repeat"] < C.CV_REPEATS]          # FAST folds = first 2 repeats of the FINAL folds
# Guards: no hold-out participant appears in the OOF file, and every OOF participant is in the training part.
assert not set(oof_all["SEQN"]) & set(clean["SEQN"].iloc[te]) and set(oof_all["SEQN"]) <= set(cl["SEQN"])   # no hold-out row
# Guard: the row-to-SEQN mapping of the OOF file equals the training-part order (rows are aligned).
assert (oof_all.drop_duplicates("row").set_index("row")["SEQN"].sort_index().to_numpy() == cl["SEQN"].to_numpy()).all()
OOF = {}
# Index the OOF predictions by (arm, tier, model) for quick lookup.
for (a, t, m), g in oof_all.groupby(["arm", "tier", "model"], observed=True):
    OOF[(a, int(t), m)] = g[["repeat", "fold", "row", "prob"]].astype({"prob": float}).reset_index(drop=True)
# every stored (repeat, fold) test set equals the stored fold file
s_oof = OOF[("S", 1, "lr")]
for i, (_, te_i) in enumerate(folds):
    r_, f_ = i // folds.n_splits, i % folds.n_splits
    assert np.array_equal(np.sort(s_oof.query("repeat == @r_ and fold == @f_")["row"].to_numpy()), te_i)
PM = {k: ek.mean_oof(v, n) for k, v in OOF.items()}            # repeat-averaged OOF probability per row

# Arm S configuration, its fitted preprocessing parameters and the survey weights used in training.
cfgS = P.ARMS["S"]
fpS = P.fit_params(cfgS, raw_tr)
w_svy = P.survey_weights(raw_tr)
# Refit arm S on fold 0 only and compare with the stored predictions for the same test rows.
tr0, te0 = folds[0]
# Same C0 and survey weights as in the stored run.
m0 = P.build_pipeline(cfgS, 1, C_=C0).fit(X1.iloc[tr0], y[tr0], model__sample_weight=w_svy[tr0])
refit = m0.predict_proba(X1.iloc[te0])[:, 1]
# Stored fold-0 predictions of arm S, aligned to the test rows te0.
stored = s_oof.query("repeat == 0 and fold == 0").set_index("row").loc[te0, "prob"].to_numpy()
max_dev = float(np.abs(refit - stored).max())
# Guard: the refit reproduces storage to float32 precision (1e-5 tolerance).
assert max_dev < 1e-5, max_dev
assert np.array_equal(P.training_label(raw_tr, cfgS), y)        # arm S trains on the frozen L_comb
print(f"training part {n:,} rows, {y.sum()} L_comb positives; E-SCREEN {esc.sum():,} rows, {y_esc[esc].sum()} positives")
print(f"folds {folds.n_splits}x{folds.n_repeats}, hash {folds.hash[:16]}...; C0 = {C0}; OOF runs loaded: {len(OOF)}")
print(f"refit of arm S, repeat 0 fold 0 vs stored OOF: max |dp| = {max_dev:.2e} (float32 storage)")
S8["setup"] = dict(n_train=n, n_pos=int(y.sum()), n_escreen=int(esc.sum()), n_pos_escreen=int(y_esc[esc].sum()),
                   folds_hash=folds.hash, C0=C0, refit_max_abs_diff=max_dev)

# %% [markdown]
# **So what.** Refitting arm S reproduces the stored predictions to float32 precision, so every new arm here is a
# paired comparison with the S predictions of §7. The training part holds 4,584 adults; E-SCREEN has only 127 positives.

# %% [markdown]
# ## 1 Audit groups
# **Why.** Without race or income oversampling in this cycle, several groups have only a few dozen cases. Five
# attributes are audited: race (NH Asian separate, always exploratory), insurance (HIQ011), **low access** (uninsured
# *or* no usual place of care, HUQ030 – the measures §5 linked to being undiagnosed), income band (PIR < 1.3 / 1.3–3.49 /
# ≥ 3.5 / missing) and sex; the reference is the largest or most advantaged group. NCHS small-cell rule: a group with
# n < 30 or fewer than 30 positives is shown, but no verdict is drawn on its gap.
#
# **Ecological-fallacy caveat.** A lower TPR for a group says that the model misses a larger share of that group's
# cases; it says nothing about any individual's risk, nor that group membership causes the difference.

# %%
# Group sizes and small-cell status per audit attribute (NCHS rule: n < 30 or positives < 30).
# Defines pop_of(); writes results/S8/group_sizes.csv.
def pop_of(name):
    """(label vector, evaluation mask) of an evaluation population."""
    if name == "E-ALL":
        return y, np.ones(n, bool)
    if name == "E-SCREEN":
        return y_esc, esc
    raise ValueError(name)

# One row per group on E-ALL and E-SCREEN; 'ref' marks the reference group.
size_rows = []
for attr in F.ATTRIBUTES:
    for lv in F.LEVELS[attr]:
        m = grp[attr].eq(lv).to_numpy()
        size_rows.append({"attribute": attr, "group": lv, "ref": lv == F.REFERENCE[attr], "n": int(m.sum()),
                          "pos_eall": int(y[m].sum()), "n_escreen": int((m & esc).sum()), "pos_escreen": int(y_esc[m & esc].sum()),
                          # cell_status returns 'present' or 'suppress' by the small-cell rule.
                          "status_eall": F.cell_status(int(m.sum()), int(y[m].sum())),
                          "status_escreen": F.cell_status(int((m & esc).sum()), int(y_esc[m & esc].sum()))})
    # Participants with unknown group membership (for example missing income) are counted separately.
    size_rows.append({"attribute": attr, "group": "(unknown)", "n": int(grp[attr].isna().sum())})
sizes = pd.DataFrame(size_rows)
sizes.to_csv(OUT / "group_sizes.csv", index=False)
show(sizes)
n_supp = {p: int((sizes[f"status_{p}"] == "suppress").sum()) for p in ("eall", "escreen")}
print(f"\nsuppressed groups (n < 30 or positives < 30): E-ALL {n_supp['eall']}, E-SCREEN {n_supp['escreen']} "
      f"of {int(sizes['status_eall'].notna().sum())}")
S8["group_sizes"] = sizes.to_dict("records")
S8["n_suppressed"] = n_supp

# %% [markdown]
# **So what.** On E-ALL every group passes the 30-positive rule, NH Asian adults with only 40 positives (exploratory).
# On E-SCREEN 10 of 16 groups fall below 30 positives, so their gaps are numbers only. That is itself a governance
# finding: a fairness audit of the screening use case needs more data than NHANES 2021–23 provides.

# %% [markdown]
# ## 2 Group metrics at the fixed threshold
# **Why.** Equal opportunity (Hardt et al. 2016) asks whether people *with* diabetes are found at the same rate in each
# group. One threshold is fixed for everybody: specificity 0.80 on all negatives of the population (no group thresholds,
# §8.10). Per group: TPR, FPR, selection rate, PPV, within-group AUC and observed-to-expected ratio (O:E). Intervals come
# from a bootstrap stratified by group × label with the threshold **re-estimated in every replicate**. Arm S is
# class-weighted, so its O:E is far below 1 everywhere; only O:E differences between groups are informative here
# (absolute calibration: §8.12).

# %%
# Bootstrap audit engine: group metrics at the fixed specificity-0.80 threshold, with cached results.
# Defines audit() and tables(); prints the E-ALL group-metrics table for arm S.
AUD = {}   # (attr, pop, tier, arms) -> (point, boot, codes, mask)

def audit(attr, pop="E-ALL", tier=1, arms=("S",), weights="simple", preds=None):
    """Run the bootstrap engine for one attribute / population / tier and a tuple of arms (paired)."""
    key = (attr, pop, tier, tuple(arms), weights)
    if key in AUD and preds is None:
        return AUD[key]
    yy, m = pop_of(pop)
    lv = F.LEVELS[attr]
    # codes: integer group index per evaluated row (population mask applied).
    codes = F.encode(grp[attr], lv)[m]
    # Predictions of the requested arms stacked (arms are paired: same rows, same bootstrap replicates).
    Pm = np.vstack([(PM[(a, tier, "lr")] if preds is None or a not in preds else preds[a])[m] for a in arms])
    # Point estimates; the threshold is set at specificity 0.80 on the population's negatives.
    point = F.boot_engine(yy[m], Pm, codes, len(lv))
    # Seed derived from the master seed and the audit identity: reproducible and distinct per audit.
    seed = ek.derive_seed(C.SEED_MASTER, "S8", attr, pop, tier, weights)
    # Bootstrap weights come in three resampling schemes, selected by `weights`.
    if weights == "simple":          # label-stratified: group size and group positives fixed (TPR, FPR, EOD)
        W = F.stratified_counts(np.char.add(codes.astype(str), np.char.add("|", yy[m].astype(str))), C.N_BOOT, seed)
    elif weights == "group":         # group-stratified only: observed cases vary (O:E, calibration)
        W = F.stratified_counts(codes.astype(str), C.N_BOOT, seed)
    else:
        # Cluster resampling of the survey PSUs within strata (Rao-Wu style), respecting the design.
        W = F.psu_counts(cl.loc[m, [C.STRATA, C.PSU]].reset_index(drop=True), C.N_BOOT, seed)
    # Replicates of every metric; the engine re-estimates the threshold inside each replicate.
    boot = F.boot_engine(yy[m], Pm, codes, len(lv), W)
    out = (point, boot, codes, m)
    # Cache only the default (stored) predictions; custom `preds` arms are never cached.
    if preds is None:
        AUD[key] = out
    return out

# For one population / tier / arm: group-metric and EOD tables, stacked over all audit attributes.
def tables(pop="E-ALL", tier=1, arm="S"):
    gt, et = [], []
    for attr in F.ATTRIBUTES:
        point, boot, _, _ = audit(attr, pop, tier, (arm,))
        g = F.group_table(point, boot, F.LEVELS[attr], attribute=attr)
        e = F.eod_table(point, boot, F.LEVELS[attr], F.REFERENCE[attr], attribute=attr)
        # Prefix population and tier so that tables from different runs can be concatenated.
        g.insert(0, "pop", pop); g.insert(1, "tier", tier)
        e.insert(0, "pop", pop); e.insert(1, "tier", tier)
        gt.append(g); et.append(e)
    return pd.concat(gt, ignore_index=True), pd.concat(et, ignore_index=True)

t0 = time.time()
# Main audit: E-ALL, Tier 1 (the admissible inputs), arm S.
GT1, ET1 = tables("E-ALL", 1)
# The shared threshold is identical for every attribute, so read it from the first audit.
thr_eall = float(audit("race")[0]["thr"][0, 0])
# Independent evalkit computation of overall recall and threshold, used as a cross-check.
rec_check, thr_check = ek.recall_at_specificity(y, PM[("S", 1, "lr")])
# Guard: the engine's pooled TPR (group TPRs weighted by group positives) equals the evalkit recall.
assert abs(audit("race")[0]["tpr"][0, 0].dot(audit("race")[0]["n_pos"][0, 0]) / y.sum() - rec_check) < 1e-12
cols_show = ["attribute", "group", "n", "n_pos", "tpr", "tpr_lo", "tpr_hi", "fpr", "sel", "ppv", "auc", "auc_lo", "auc_hi", "oe", "status", "flags"]
print(f"E-ALL, Tier 1, arm S: threshold {thr_eall:.4f} (specificity 0.80 on {int((y == 0).sum())} negatives); "
      f"overall TPR {rec_check:.3f}; {time.time() - t0:.1f} s")
show(GT1[cols_show], 3)

# %% [markdown]
# **So what.** At one shared threshold the model finds about two thirds of all cases, but not evenly: the lowest TPRs
# belong to NH Asian adults, the highest income band, the low-access group and the uninsured; the highest to the lowest
# income band. In NH Asian, low-access and uninsured adults low TPR comes with low FPR: their whole score distribution
# sits lower. Within-group AUCs overlap widely (about 0.78–0.87), so the gaps come from where each group's scores lie
# relative to the shared threshold, not from worse ranking.

# %% [markdown]
# ## 3 Gaps and permutation baseline
# **Why.** A gap is only interesting if it is larger than what random group labels would produce. Two checks are
# combined: (i) the equal-opportunity difference EOD = TPR_group − TPR_reference with its bootstrap CI, flagged at
# |EOD| ≥ 0.05 (SESOI) and called **substantive** only if |EOD| ≥ 0.10 *and* its CI excludes 0; (ii) a group-label
# permutation null: group labels are shuffled 200 times (sizes kept, threshold fixed) and the observed max |EOD| over
# the reportable groups is compared with the null distribution of that maximum. The maximum is the right statistic
# because with six race groups the largest of five gaps is expected to look sizeable even by chance.

# %%
# Group-label permutation null for the largest TPR gap, plus the substantive-gap listing.
# Defines permutation_block(); prints EOD, permutation and substantive-gap tables for E-ALL.
# For each attribute: observed max |EOD| over reportable groups versus n_perm shuffles of the group labels.
def permutation_block(pop="E-ALL", tier=1, arm="S", preds=None):
    rows, nulls = [], {}
    yy, m = pop_of(pop)
    for attr in F.ATTRIBUTES:
        point, boot, codes, mm = audit(attr, pop, tier, (arm,), preds=preds)
        lv = F.LEVELS[attr]
        ref = lv.index(F.REFERENCE[attr])
        # ok: groups with enough cases to report (small-cell rule); only these enter the maximum.
        ok = [g for g in range(len(lv)) if F.cell_status(int(point["n"][0, 0, g]), int(point["n_pos"][0, 0, g])) == "present"]
        p_ = (PM[(arm, tier, "lr")] if preds is None else preds[arm])[mm]
        thr = np.nextafter(point["thr"][0, 0], np.inf)        # engine: positive if p > v  <=>  p >= nextafter(v)
        # Need the reference group and at least one comparison group, otherwise no maximum can be formed.
        if ref not in ok or len(ok) < 2:
            rows.append({"pop": pop, "tier": tier, "attribute": attr, "n_groups_eligible": len(ok) - (ref in ok),
                         "observed_max_eod": np.nan, "null_q95": np.nan, "p_value": np.nan, "note": "reference or all groups suppressed"})
            continue
        # Shuffle group labels n_perm times (sizes kept, threshold fixed); null = distribution of max |EOD|.
        res = F.eod_permutation(yy[mm], p_, codes, len(lv), ref, thr, eligible=ok, n_perm=N_PERM_GROUP,
                                seed=ek.derive_seed(C.SEED_MASTER, "S8", "perm", attr, pop, tier))
        tp = point["tpr"][0, 0]
        # Guard: the permutation routine's observed statistic equals the largest TPR gap from the engine.
        assert abs(res["observed"] - max(abs(tp[g] - tp[ref]) for g in ok if g != ref)) < 1e-12
        nulls[attr] = res["null"]
        rows.append({"pop": pop, "tier": tier, "attribute": attr, "n_groups_eligible": len(ok) - 1,
                     "observed_max_eod": res["observed"], "null_mean": res["null_mean"], "null_q95": res["null_q95"],
                     "p_value": res["p_value"], "note": ""})
    return pd.DataFrame(rows), nulls

PERM1, NULL1 = permutation_block("E-ALL", 1)
print("Equal-opportunity differences, E-ALL, Tier 1 (reference in column 'ref'):")
show(ET1[["attribute", "group", "ref", "eod", "eod_lo", "eod_hi", "fpr_diff", "flag_0.05", "substantive", "verdict_status"]], 3)
print("\nPermutation null of max |EOD| (reportable groups only):")
show(PERM1, 3)
# Substantive: |EOD| >= 0.10 and CI excludes 0; only reportable (non-suppressed) groups count.
sub1 = ET1[ET1["substantive"] & ET1["verdict_status"].eq("reportable")]
print(f"\nsubstantive gaps (|EOD| >= {GAP_SUB}, CI excludes 0, reportable): {len(sub1)}")
for r_ in sub1.itertuples():
    print(f"   {r_.attribute}: {r_.group} EOD {r_.eod:+.3f}")

# %% [markdown]
# **So what.** Three attributes have a largest gap beyond the 95th percentile of the permutation null: **race** (NH Asian,
# EOD about −0.18, CI excluding 0 – substantive but exploratory, 40 positives), **income** (the lowest band found *more*
# often than the highest, EOD about +0.19) and **low access** (EOD about −0.09; its own CI includes 0, so borderline).
# Insurance and sex show nothing beyond chance. Race, insurance and access are not inputs, so every gap must travel
# through correlated features; the next table asks which.

# %%
# Decompose the TPR gaps into routes: diagnosed vs undiagnosed cases, care traces, age, BMI, coefficients.
# Writes results/S8/gap_decomposition.csv.
# hitS: True if the prediction reaches the shared specificity-0.80 threshold.
pS = PM[("S", 1, "lr")]
hitS = pS >= thr_check
dec = []
for attr in F.ATTRIBUTES:
    for lv in F.LEVELS[attr]:
        # m: the group's positives; dx / ud: those with / without a self-reported diagnosis (L_self).
        m = grp[attr].eq(lv).to_numpy() & (y == 1)
        dx = m & (cl["L_self"].to_numpy() == 1)
        ud = m & (cl["L_self"].to_numpy() == 0)
        dec.append({"attribute": attr, "group": lv, "n_pos": int(m.sum()), "share_diagnosed": dx.sum() / m.sum(),
                    "mean_age": cl.loc[m, "RIDAGEYR"].mean(), "mean_bmi": cl.loc[m, "BMXBMI"].mean(),
                    # care_trace: told of hypertension (BPQ020) or high cholesterol (BPQ080).
                    "care_trace": (cl.loc[m, "BPQ020"].eq(1) | cl.loc[m, "BPQ080"].eq(1)).mean(),
                    "tpr": hitS[m].mean(), "tpr_diagnosed": hitS[dx].mean(), "tpr_undiagnosed": hitS[ud].mean() if ud.sum() else np.nan})
DEC = pd.DataFrame(dec)
DEC.to_csv(OUT / "gap_decomposition.csv", index=False)
show(DEC, 3)
# Group-level correlations over the 16 groups: does TPR follow share diagnosed, care traces or age?
r_dx = float(np.corrcoef(DEC["share_diagnosed"], DEC["tpr"])[0, 1])
r_age = float(np.corrcoef(DEC["mean_age"], DEC["tpr"])[0, 1])
r_care = float(np.corrcoef(DEC["care_trace"], DEC["tpr"])[0, 1])
# Pooled TPR for diagnosed versus undiagnosed positives.
tpr_dx_all = hitS[(y == 1) & (cl["L_self"].to_numpy() == 1)].mean()
tpr_ud_all = hitS[(y == 1) & (cl["L_self"].to_numpy() == 0)].mean()
print(f"\nall positives: TPR diagnosed {tpr_dx_all:.3f} vs undiagnosed {tpr_ud_all:.3f}")
print(f"across the 16 groups, correlation of TPR with share diagnosed {r_dx:.2f}, with care-trace share {r_care:.2f}, "
      f"with mean age {r_age:.2f}")
# which inputs carry the routes? arm S refitted on the whole training part (per-SD coefficients, dummies vs base level)
fullS = P.build_pipeline(cfgS, 1, C_=C0).fit(X1, y, model__sample_weight=w_svy)
coefS = pd.Series(fullS[-1].coef_[0], index=fullS[:-1].get_feature_names_out())
# Candidate routes: income, education, hypertension / cholesterol, waist, hip and BMI inputs.
route_cols = [c for c in coefS.index if c.startswith(("INDFMPIR", "DMDEDUC2", "BPQ020", "BPQ080", "BMXWAIST", "BMXHIP", "BMXBMI"))]
print("\narm S coefficients of the route variables (scaled inputs):")
display(coefS[route_cols].round(3))
S8["gap_decomposition"] = dict(table=DEC.round(4).to_dict("records"), tpr_diagnosed=tpr_dx_all, tpr_undiagnosed=tpr_ud_all,
                               r_tpr_share_diagnosed=r_dx, r_tpr_care_trace=r_care, r_tpr_mean_age=r_age,
                               route_coefficients=coefS[route_cols].round(4).to_dict())

# %% [markdown]
# **So what.** Three routes produce the gaps:
#
# * **Label route.** Diagnosed cases are found far more often than undiagnosed ones (TPR about 0.70 vs 0.52, printed),
#   and a group's TPR rises with its share of diagnosed cases with care traces – the access imprint of §5, reproduced.
# * **Measurement route.** NH Asian cases are as old as White cases but much leaner (mean BMI about 26 vs 34); BMI and
#   waist push their scores down, so they are missed more even when diagnosed.
# * **Direct route.** Income has a negative and low education a positive coefficient: the model uses SES as a risk
#   marker, which explains the income gaps.
#
# The race and access gaps are mostly **label and measurement bias transmitted through the features**, so reweighing
# is unlikely to remove them, while WHtR targets one route directly (§8.8–§8.9).

# %%
# Figure 8-1: group TPR forest plots (E-ALL and E-SCREEN) and the permutation-null histograms.
# Saves figures S8_group_tpr and S8_permutation_null; adds the metrics to the section dict.
plots.set_style()
def tpr_panel(ax, GT, ET, title, overall):
    """Point-range of group TPRs; returns y labels (attribute: group)."""
    ylabels, ypos, k = [], [], 0
    for attr in F.ATTRIBUTES:
        g = GT[GT["attribute"] == attr]
        for _, r in g.iterrows():
            # Suppressed cells are drawn hollow grey, the reference group blue, comparison groups vermillion.
            sup = r["status"] == "suppress"
            col = C.OKABE_ITO["grey"] if sup else (C.OKABE_ITO["blue"] if r["group"] == F.REFERENCE[attr] else C.OKABE_ITO["vermillion"])
            ax.errorbar(r["tpr"], -k, xerr=[[r["tpr"] - r["tpr_lo"]], [r["tpr_hi"] - r["tpr"]]], fmt="o",
                        color=col, mfc="white" if sup else col, capsize=3, ms=8, lw=1.8)
            e = ET[(ET["attribute"] == attr) & (ET["group"] == r["group"])]
            # A star marks a substantive, reportable gap (|EOD| >= 0.10, CI excludes 0).
            if len(e) and bool(e["substantive"].iloc[0]) and e["verdict_status"].iloc[0] == "reportable":
                ax.annotate("*", (r["tpr_hi"], -k), xytext=(4, -6), textcoords="offset points", fontsize=18, color="black")
            ax.annotate(f"n+ {int(r['n_pos'])}", (0.01, -k), xytext=(0, 4), textcoords="offset points", fontsize=10, color="dimgrey")
            ylabels.append(f"{attr}: {r['group']}")
            ypos.append(-k)
            k += 1
        # Extra vertical space between attribute blocks.
        k += 0.6
    # Dashed line = overall TPR of the population.
    ax.axvline(overall, color="black", lw=0.8, ls="--")
    ax.set_yticks(ypos); ax.set_yticklabels(ylabels, fontsize=12)
    ax.tick_params(axis="x", labelsize=11)
    ax.set_xlabel("TPR at specificity 0.80 (95 % CI)", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.set_xlim(0, 1)

# E-SCREEN tables are needed for the right panel (computed in §8.4, re-used there)
GTs, ETs = tables("E-SCREEN", 1)
# E-SCREEN overall recall at specificity 0.80 on its own negatives.
rec_s, _ = ek.recall_at_specificity(y_esc[esc], PM[("S", 1, "lr")][esc])
fig, axes = plt.subplots(1, 2, figsize=(14, 10.5))
tpr_panel(axes[1], GTs, ETs, f"E-SCREEN (overall TPR {rec_s:.2f})", rec_s)
axes[1].tick_params(labelleft=False)
tpr_panel(axes[0], GT1, ET1, f"E-ALL (overall TPR {rec_check:.2f})", rec_check)
fig.suptitle("Sensitivity by group at one shared threshold (arm S, Tier 1)\n"
             "blue = reference · red = comparison · hollow grey = suppressed (< 30) · * substantive gap (|EOD| ≥ 0.10, CI excl. 0)", fontsize=14)
fig.tight_layout()
f81 = plots.savefig(fig, "S8_group_tpr", caption="F8-1. TPR at specificity 0.80 by audit group for arm S (Tier 1) on E-ALL "
                    "and E-SCREEN, stratified bootstrap 95 % CI with the threshold re-estimated per replicate; dashed line = "
                    "overall TPR; hollow grey markers are suppressed cells (n < 30 or fewer than 30 positives).")
plt.show()

# Permutation panels, one per attribute: observed max |EOD| (red) against the null 95th percentile (dotted).
fig, axes = plt.subplots(1, len(F.ATTRIBUTES), figsize=(15, 2.8), sharey=True)
for ax, attr in zip(axes, F.ATTRIBUTES):
    row = PERM1.set_index("attribute").loc[attr]
    if attr in NULL1:
        ax.hist(NULL1[attr], bins=25, color=C.OKABE_ITO["sky"], edgecolor="white")
        ax.axvline(row["observed_max_eod"], color=C.OKABE_ITO["vermillion"], lw=2, label="observed")
        ax.axvline(row["null_q95"], color="black", ls=":", lw=1, label="null 95th pct")
        ax.set_title(f"{attr}\np = {row['p_value']:.3f}", fontsize=10)
    ax.set_xlabel("max |EOD|")
axes[0].set_ylabel("permutations"); axes[0].legend(fontsize=8)
fig.suptitle("Group-label permutation null of the largest TPR gap (E-ALL, arm S, 200 permutations)", fontsize=11, y=1.08)
f81b = plots.savefig(fig, "S8_permutation_null", caption="F8-1b. Null distribution of max |TPR_g - TPR_ref| over the reportable "
                     "groups when group labels are permuted 200 times (threshold fixed), with the observed value (red) "
                     "and the null 95th percentile (dotted). E-ALL, arm S, Tier 1.")
plt.show()
# Keep the E-ALL Tier 1 results for the metrics file.
S8["group_metrics_eall_t1"] = GT1.round(5).to_dict("records")
S8["eod_eall_t1"] = ET1.round(5).to_dict("records")
S8["permutation_eall_t1"] = PERM1.round(5).to_dict("records")
S8["threshold_eall_t1"] = thr_eall
S8["overall_tpr_eall_t1"] = rec_check

# %% [markdown]
# **So what.** The left panel is the audit in one picture: NH Asian adults and the highest income band fall clearly
# below the overall TPR, the lowest income band lies above it; on E-SCREEN almost every group is suppressed. In the
# permutation panel the observed maximum gap lies beyond the null's 95th percentile for race, income and low access, and
# inside it for insurance and sex.

# %% [markdown]
# ## 4 E-SCREEN
# **Why.** The same audit on the use-case population (specificity 0.80 on E-SCREEN negatives; read in §8.11).

# %%
# Same group audit on the use-case population E-SCREEN (specificity 0.80 on its own negatives).
# Reuses audit(); the tables are stored in the section dict for the Outputs cell.
PERMs, NULLs = permutation_block("E-SCREEN", 1)
print(f"E-SCREEN, Tier 1, arm S: overall TPR {rec_s:.3f}")
show(GTs[cols_show], 3)
print()
show(ETs[["attribute", "group", "ref", "eod", "eod_lo", "eod_hi", "flag_0.05", "substantive", "verdict_status"]], 3)
print()
show(PERMs, 3)
# reportable: enough cases for a verdict (not suppressed by the small-cell rule).
rep_s = ETs[ETs["verdict_status"].eq("reportable")]
print(f"\nreportable E-SCREEN gaps: {len(rep_s)} of {len(ETs)}; substantive among them: {int(rep_s['substantive'].sum())}")
S8["group_metrics_escreen_t1"] = GTs.round(5).to_dict("records")
S8["eod_escreen_t1"] = ETs.round(5).to_dict("records")
S8["permutation_escreen_t1"] = PERMs.round(5).to_dict("records")
S8["overall_tpr_escreen_t1"] = rec_s


# %% [markdown]
# ## 5 Tier 2 summary
# **Why.** Does adding total and HDL cholesterol (Tier 2) change the gaps? (read in §8.11)

# %%
# Tier 2 (adds total and HDL cholesterol): do the group gaps change?
# Compares EOD and permutation results between the two tiers.
GT2, ET2 = tables("E-ALL", 2)
PERM2, _ = permutation_block("E-ALL", 2)
# Join Tier 1 and Tier 2 EOD per group (suffix _t2) to read them side by side.
cmp_t = (ET1.set_index(["attribute", "group"])[["eod", "eod_lo", "eod_hi", "verdict_status"]]
         .join(ET2.set_index(["attribute", "group"])[["eod", "eod_lo", "eod_hi"]], rsuffix="_t2"))
# Change of the signed EOD when the lipids are added.
cmp_t["delta_t2_t1"] = cmp_t["eod_t2"] - cmp_t["eod"]
display(cmp_t.round(3))
summ = PERM1.set_index("attribute")[["observed_max_eod", "p_value"]].join(
    PERM2.set_index("attribute")[["observed_max_eod", "p_value"]], rsuffix="_t2")
print("\nmax |EOD| (reportable groups) and permutation p, Tier 1 vs Tier 2:")
display(summ.round(3))
# Largest absolute shift of any group's EOD between the tiers.
max_shift = float(cmp_t["delta_t2_t1"].abs().max())
print(f"largest change of any EOD from Tier 1 to Tier 2: {max_shift:.3f}")
S8["tier2_summary"] = dict(eod=ET2.round(5).to_dict("records"), permutation=PERM2.round(5).to_dict("records"),
                           max_abs_eod_shift=max_shift)


# %% [markdown]
# ## 6 3 × 3 label matrix
# **Why.** RQ3 asks whether the *label* decides who the model misses. H3 is a genuine pre-registration
# (`prior_exposure = none`): the identical arm-S pipeline (same folds, steps, C0 and weights) is trained on `L_self`,
# `L_A1c` and the union `L_comb` and scored on three kinds of diabetes – **D-uncontrolled** (self-report and HbA1c ≥ 6.5),
# **D-controlled** (self-report, HbA1c < 6.5: treatment masking) and **Undiagnosed** (HbA1c ≥ 6.5, no diagnosis). Each
# cell is recall at specificity 0.80 on the common non-diabetic negatives. Locked prediction: `L_self` misses Undiagnosed
# most, `L_A1c` misses D-controlled most, `L_comb` has the smallest worst-cell gap; differences below 0.05 are
# equivalent. "Misses most" is read **column-wise** (coded in `fairness.h3_elements` before the matrix was viewed);
# contrasts are paired bootstrap differences judged at SESOI 0.05.

# %%
# 3 x 3 label matrix: arm S trained on each of three labels, scored on three kinds of diabetes (H3).
# Refits arm S on L_self and L_A1c over the same folds; the L_comb row reuses the stored OOF predictions.
LABELS3 = ("L_self", "L_A1c", "L_comb")
# One label vector per training label (training part).
YL = {lab: cl[lab].to_numpy().astype(int) for lab in LABELS3}
# Guard: the L_comb vector is the frozen label that arm S was trained on.
assert np.array_equal(YL["L_comb"], y)
from joblib import Parallel, delayed
t0 = time.time()
# Factory for a fresh arm-S pipeline with the stored C0.
mk_S = lambda: P.build_pipeline(cfgS, 1, C_=C0)
# Refit on the two other labels in parallel; same folds and fit parameters as S, so the rows are paired.
new = Parallel(n_jobs=2)(delayed(ek.cv_predict)(mk_S, X1, YL[lab], folds, fit_params=fpS) for lab in ("L_self", "L_A1c"))
# The L_comb row is the stored arm-S OOF; no refit is needed.
OOF3 = {"L_self": new[0], "L_A1c": new[1], "L_comb": OOF[("S", 1, "lr")]}
PM3 = {lab: ek.mean_oof(OOF3[lab], n) for lab in LABELS3}
# cnt: size of each 3 x 3 stratum in the training part, compared with the frozen full-cohort counts.
cnt = pd.Series(strat).value_counts()
full = L.strata_counts(clean)
print(f"refitted arm S on L_self and L_A1c: {2 * len(folds)} fits, {time.time() - t0:.0f} s")
print("training-part strata (share of the frozen full-cohort counts):")
print("   " + ", ".join(f"{k} {int(cnt[k])} ({cnt[k] / full[k]:.2f})" for k in L.STRATA_3X3))
# Guard: the stratified hold-out leaves about 80 % of each stratum in the training part (0.75-0.85).
assert all(0.75 < cnt[k] / full[k] < 0.85 for k in L.STRATA_3X3)
# Recall at specificity 0.80 on the common non-diabetic negatives, per training label and stratum.
LM = F.label_matrix(strat, PM3, n_boot=C.N_BOOT, seed=ek.derive_seed(C.SEED_MASTER, "S8", "3x3"))
cells = LM["cells"]
# consistency: L_comb row, Undiagnosed column = E-SCREEN recall of arm S (same positives, same negatives)
assert abs(LM["recall"].loc["L_comb", "Undiagnosed"] - rec_s) < 1e-12
print("\nrecall at specificity 0.80 on the common NonDiabetic negatives (rows: training label):")
display(LM["recall"].round(3))
print("\nROC-AUC against the common negatives:")
display(LM["auc"].round(3))
print()
show(cells[["train_label", "stratum", "n_pos", "recall", "recall_lo", "recall_hi", "auc", "auc_lo", "auc_hi"]], 3)
# Locked H3 elements (E1-E3) as paired bootstrap contrasts; coded before the matrix was viewed.
H3E = F.h3_elements(LM)
print("\npre-registered contrasts (predicted sign: negative):")
show(H3E, 3)
# row-wise reading (secondary): in which stratum does each training label have its lowest recall?
roww = LM["recall"].idxmin(axis=1).to_dict()
print(f"\nrow-wise reading (secondary): lowest-recall stratum per training label {roww}")
# Worst-cell gap per training label: largest recall shortfall against the best label in any stratum.
gaps = F._worst_gap(LM["point"]["tpr"][0])
print("worst-cell gap per training label:", dict(zip(LABELS3, np.round(gaps, 3))))

# %%
# Combine the H3 element verdicts, save the tables and draw the label-matrix heat maps.
# Writes results/S8/label_matrix_cells.csv and h3_contrasts.csv; saves figure S8_label_matrix.
# Each H3 element (E1-E3) combines the verdicts of its contrasts.
elem_v = {}
for el, g in H3E.groupby("element"):
    elem_v[el] = ek.combine_verdicts(g["verdict"].tolist())
# H3 overall combines the three element verdicts.
h3_v = ek.combine_verdicts(list(elem_v.values()))
if H3E["reversed_ci_excl_0"].any():                       # locked falsifier
    h3_v = "refuted"
print(f"H3 element verdicts {elem_v} -> H3 {h3_v}")
cells.to_csv(OUT / "label_matrix_cells.csv", index=False)
H3E.to_csv(OUT / "h3_contrasts.csv", index=False)
S8["label_matrix"] = dict(cells=cells.round(5).to_dict("records"), recall=LM["recall"].round(5).to_dict(),
                          auc=LM["auc"].round(5).to_dict(), contrasts=H3E.round(5).to_dict("records"),
                          element_verdicts=elem_v, verdict=h3_v, row_wise_min=roww,
                          worst_gap=dict(zip(LABELS3, gaps.round(5))), strata_train=cnt.to_dict())

fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})
# Left: recall at specificity 0.80; right: ROC-AUC (secondary). Cells show estimate (95 % CI).
for ax, (mat, key, ttl) in zip(axes, [(LM["recall"], "recall", "Recall at specificity 0.80"), (LM["auc"], "auc", "ROC-AUC (secondary)")]):
    # Colour scale: recall from 0, AUC from 0.5 (chance level).
    im = ax.imshow(mat.to_numpy(), cmap="Blues", vmin=0 if key == "recall" else 0.5, vmax=1)
    for i, lab in enumerate(LABELS3):
        for j, st in enumerate(F.POS_STRATA):
            r = cells[(cells["train_label"] == lab) & (cells["stratum"] == st)].iloc[0]
            v = mat.loc[lab, st]
            # White text on dark cells for legibility; the switch point differs by metric.
            ax.text(j, i, f"{v:.2f}\n({r[key + '_lo']:.2f}–{r[key + '_hi']:.2f})", ha="center", va="center",
                    fontsize=9, color="white" if v > (0.6 if key == "recall" else 0.8) else "black")
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{s}\n(n={int(cnt[s])})" for s in F.POS_STRATA], fontsize=9)
    ax.set_yticks(range(3)); ax.set_yticklabels([f"trained on {l}" for l in LABELS3])
    ax.set_title(ttl); ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.046)
fig.suptitle(f"3 × 3 label matrix (arm S, Tier 1, training part; {int(cnt['NonDiabetic'])} common negatives) – H3: {h3_v}", fontsize=11)
fig.tight_layout()
f82 = plots.savefig(fig, "S8_label_matrix", caption="F8-2. 3x3 label matrix: arm S trained on L_self, L_A1c or L_comb "
                    "(identical folds, steps and C0) and scored on D-uncontrolled, D-controlled and Undiagnosed cases against "
                    "the common NonDiabetic negatives. Left: recall at specificity 0.80 with 95 % stratified bootstrap CI "
                    "(thresholds re-estimated per replicate); right: ROC-AUC.")
plt.show()

# %% [markdown]
# **So what.** Every element of the locked pattern points the predicted way, but the differences are small (at most
# about 0.06) and every paired CI includes 0 while reaching beyond ±0.05, so H3 is **inconclusive**. The row-wise reading
# tells the stronger story: *whatever* the training label, the Undiagnosed column is the hardest, and the AUCs agree.
# Undiagnosed people lack the care traces and treatment-era profile the features pick up, so changing the label shifts
# recall by only a few points. The label shapes *what the model claims to measure* (§5) more than *whom this feature set
# can find*.

# %% [markdown]
# ## 7 Access-proxy audit arm
# **Why.** If the self-report label carries the access imprint of §5, a model trained on `L_self` should learn that
# *lacking access lowers the chance of "having diabetes"* – an artefact of who gets diagnosed – while one trained on
# HbA1c (which needs no doctor) should not. The audit arm adds **uninsured** (HIQ011 = 2) and **no usual place of care**
# (HUQ030 = 2) to the arm-S pipeline and fits it on each label; per-SD coefficients are bootstrapped with the same seed
# for every label, so label differences are paired. This arm is an **audit instrument only**.

# %%
# Access-proxy audit arm: arm S plus uninsured / no-usual-place features, coefficients bootstrapped per label.
# Audit instrument only. Writes results/S8/access_audit_coefs.csv and access_audit_diffs.csv.
t0 = time.time()
# Factory for the audit pipeline: arm S plus the two access dummies.
mk_acc = lambda: F.access_pipeline(cfgS, 1, C_=C0)
# Guard: both access features survive in the pipeline's feature names (else coefficients would be missing).
assert set(F.ACCESS_FEATURES) <= set(mk_acc()[:-1].fit(X1.iloc[:500], y[:500]).get_feature_names_out())
# Same seed for every label: identical bootstrap resamples, so label differences are paired.
seed_acc = ek.derive_seed(C.SEED_MASTER, "S8", "access_audit")
# Bootstrapped per-SD coefficients for each training label.
CB = {lab: ek.coef_bootstrap(mk_acc, X1, YL[lab], n_boot=C.N_BOOT_COEF, seed=seed_acc, fit_params=fpS, n_jobs=N_JOBS)
      for lab in LABELS3}
# SD of a binary feature, sqrt(p (1 - p)): converts a per-SD coefficient into a yes-versus-no odds ratio.
sd_bin = {f: float(np.sqrt(grp[f].fillna(0).mean() * (1 - grp[f].fillna(0).mean()))) for f in F.ACCESS_FEATURES}
acc_rows = []
for f in F.ACCESS_FEATURES:
    for lab in LABELS3:
        s_ = CB[lab].summary.loc[f]
        acc_rows.append({"feature": f, "label": lab, "coef_per_sd": s_["coef"], "lo": s_["q_low"], "hi": s_["q_high"],
                         "boot_sd": s_["sd"], "OR_yes_vs_no": np.exp(s_["coef"] / sd_bin[f]),
                         "OR_lo": np.exp(s_["q_low"] / sd_bin[f]), "OR_hi": np.exp(s_["q_high"] / sd_bin[f])})
ACC = pd.DataFrame(acc_rows)
# Paired differences between training labels: coefficient difference, CI from the paired bootstrap.
diff_rows = []
for f in F.ACCESS_FEATURES:
    for a, b in (("L_self", "L_comb"), ("L_self", "L_A1c"), ("L_comb", "L_A1c")):
        d = CB[a].coefs[f].to_numpy() - CB[b].coefs[f].to_numpy()
        e, lo, hi, se = F.summarise(CB[a].summary.loc[f, "coef"] - CB[b].summary.loc[f, "coef"], d)
        diff_rows.append({"feature": f, "contrast": f"{a} - {b}", "diff_per_sd": e, "lo": lo, "hi": hi,
                          "ci_excludes_0": bool(lo > 0 or hi < 0)})
ACCD = pd.DataFrame(diff_rows)
print(f"access audit arm: {len(LABELS3)} labels x (1 + {C.N_BOOT_COEF}) fits, {time.time() - t0:.0f} s")
show(ACC, 3)
print("\npaired differences of the per-SD coefficient between training labels:")
show(ACCD, 3)
ACC.to_csv(OUT / "access_audit_coefs.csv", index=False)
ACCD.to_csv(OUT / "access_audit_diffs.csv", index=False)
S8["access_audit"] = dict(coefs=ACC.round(5).to_dict("records"), diffs=ACCD.round(5).to_dict("records"),
                          n_boot=C.N_BOOT_COEF, sd_binary=sd_bin)

# %% [markdown]
# **So what.** The access imprint appears where the label requires a doctor. Trained on self-report, both access features
# get negative coefficients – no usual place of care *lowers* predicted risk (odds ratio about 0.5, CI excluding 0) –
# although §4 showed the insured–uninsured prevalence gap is age confounding. Trained on HbA1c the coefficients are small
# with CIs including 0, and the union label sits next to HbA1c. The paired self-report minus union differences (about
# −0.10 per SD) have CIs that just include 0: suggestive, not established. A self-report model would **score people with
# poor access as lower risk because they were never diagnosed** – a feedback loop that supports the union label and
# keeping access out of the model.

# %% [markdown]
# ## 8 Reweighing
# **Why.** Reweighing (Kamiran & Calders 2012) gives each training row the weight w(g, y) = P(g)·P(y) / P(g, y), making
# group and label independent in the weighted data. It is applied inside every training fold on top of arm S's survey
# weights, so the comparison with S is paired. Race (pre-specified) and, as extensions, insurance and low access are
# reweighed. ΔAUC uses the §7.4.1 engine; gap changes are paired bootstrap differences of EOD.

# %%
# Reweighing (Kamiran-Calders) inside every training fold, compared with arm S on the same folds.
# Defines fold_auc() and compare_auc(); writes results/S8/reweighing_auc.csv and reweighing_eod.csv.
from joblib import parallel_config
from sklearn.metrics import roc_auc_score
from scipy import stats as sstats

# AUC of each (repeat, fold) test set, optionally restricted to a population; feeds the corrected t-test.
def fold_auc(oof, pop="E-ALL"):
    yy, m = pop_of(pop)
    out = {}
    for (r, f), g in oof.groupby(["repeat", "fold"]):
        rows = g["row"].to_numpy()
        k = m[rows]
        out[(r, f)] = roc_auc_score(yy[rows][k], g["prob"].to_numpy()[k])
    return pd.Series(out)

def compare_auc(oof_a, oof_b, pop="E-ALL", tag=""):
    """Paired ΔAUC A - B with the S7 engine: on E-ALL the estimate is the fold-mean paired difference and the interval the
    wider of corrected t and paired bootstrap; on E-SCREEN the pooled-OOF difference with its paired bootstrap interval."""
    yy, m = pop_of(pop)
    # Paired bootstrap of the pooled-OOF AUC difference A - B; both arms share the same resamples.
    pa, pb = ek.mean_oof(oof_a, n), ek.mean_oof(oof_b, n)
    bs = ek.paired_bootstrap(yy, pa, pb, "roc_auc", n_boot=C.N_BOOT, eval_mask=m,
                             seed=ek.derive_seed(C.SEED_MASTER, "S8", "dauc", tag, pop))
    row = dict(pop=pop, diff_pooled=bs["diff"], boot_lo=bs["ci_low"], boot_hi=bs["ci_high"])
    est, lo, hi, se, interval = bs["diff"], bs["ci_low"], bs["ci_high"], bs["se"], "bootstrap"
    # Minimum detectable difference: (z at 97.5 % + z at 80 %) * SE: two-sided 5 % alpha, 80 % power.
    mdd = (sstats.norm.ppf(0.975) + sstats.norm.ppf(0.8)) * se
    if pop == "E-ALL":
        # Nadeau-Bengio corrected resampled t on the per-fold paired AUC differences; the correction
        # allows for the overlap of training sets across folds.
        ct = ek.corrected_t((fold_auc(oof_a) - fold_auc(oof_b)).to_numpy(), n_train_fold, n_test_fold)
        row.update(t_lo=ct["ci_low"], t_hi=ct["ci_high"])
        est = ct["mean"]
        # Report the wider of the corrected-t and bootstrap intervals (the conservative choice).
        if ct["ci_high"] - ct["ci_low"] >= hi - lo:
            lo, hi, se, interval = ct["ci_low"], ct["ci_high"], ct["se_corr"], "corrected_t"
        # The power quantile uses the corrected-t degrees of freedom instead of the normal quantile.
        mdd = (sstats.t.ppf(0.975, ct["df"]) + sstats.t.ppf(0.80, ct["df"])) * se
    row.update(est=est, lo=lo, hi=hi, se=se, interval=interval, mdd=mdd)
    return row

# Reweighed attributes and, for each, the group whose gap is expected to narrow.
RW_TARGET = {"race": "NH Asian", "insurance": "uninsured", "low_access": "low access"}
OOF_RW, RW_W, RW_ROWS, RW_EOD = {}, {}, [], []
t0 = time.time()
# max_nbytes=None disables joblib's memory-mapping of large arrays.
with parallel_config(max_nbytes=None):
    for attr in RW_TARGET:
        gvals = grp[attr].to_numpy(dtype=object)
        # Reweighing weight w(g, y) = P(g) P(y) / P(g, y) per training row.
        w_rw = F.reweighing_weights(gvals, y)
        RW_W[attr] = w_rw
        # Refit arm S per fold with weight = survey weight x reweighing weight; returns OOF predictions.
        OOF_RW[attr] = F.cv_predict_reweighed(mk_S, X1, y, folds, gvals, base_weight=w_svy, n_jobs=N_JOBS)
print(f"reweighing arms: {len(RW_TARGET)} x {len(folds)} fits, {time.time() - t0:.0f} s")
for attr, w_rw in RW_W.items():
    lv = grp[attr].fillna("(unknown)")
    # One weight per (group, label) cell: weights are constant within a cell, so take the first.
    tab = pd.DataFrame({"g": lv, "y": y, "w": w_rw}).groupby(["g", "y"])["w"].first().unstack()
    print(f"\n{attr}: reweighing weights w(g, y) on the training part (range {w_rw.min():.3f}-{w_rw.max():.3f})")
    display(tab.round(3).rename(columns={0: "w(y=0)", 1: "w(y=1)"}))
    # Repeat-averaged OOF probability of the reweighed arm.
    PMx = ek.mean_oof(OOF_RW[attr], n)
    # Compare with S on both populations; the verdict applies the locked AUC SESOI to the interval.
    for pop in ("E-ALL", "E-SCREEN"):
        r = compare_auc(OOF_RW[attr], OOF[("S", 1, "lr")], pop, tag=f"rw_{attr}")
        r.update(arm=f"S+RW({attr})", w_min=w_rw.min(), w_max=w_rw.max(),
                 verdict_auc=ek.verdict(r["lo"], r["hi"], AUC_SESOI, "+", r["est"]))
        RW_ROWS.append(r)
    # Paired audit of S and the reweighed arm (index 1), used for the change of EOD.
    point, boot, codes, mm = audit(attr, "E-ALL", 1, ("S", "RW"), preds={"RW": PMx})
    lvls = F.LEVELS[attr]
    ref = lvls.index(F.REFERENCE[attr])
    # For each non-reference group: change of EOD and of |EOD| (reweighed minus S) with paired bootstrap CIs.
    for g_i, g_nm in enumerate(lvls):
        if g_i == ref:
            continue
        # EOD = TPR_group - TPR_reference for each arm; bootstrap replicates are paired across arms.
        eod_pt = point["tpr"][0, :, g_i] - point["tpr"][0, :, ref]
        eod_bt = boot["tpr"][:, :, g_i] - boot["tpr"][:, :, ref]
        e, lo, hi, _ = F.summarise(eod_pt[1] - eod_pt[0], eod_bt[:, 1] - eod_bt[:, 0])
        # Change of |EOD|: negative means the gap narrows.
        ea, alo, ahi, _ = F.summarise(abs(eod_pt[1]) - abs(eod_pt[0]), np.abs(eod_bt[:, 1]) - np.abs(eod_bt[:, 0]))
        RW_EOD.append({"arm": f"S+RW({attr})", "attribute": attr, "group": g_nm, "eod_S": eod_pt[0], "eod_RW": eod_pt[1],
                       "d_eod": e, "d_eod_lo": lo, "d_eod_hi": hi, "d_abs_eod": ea, "d_abs_lo": alo, "d_abs_hi": ahi,
                       "target": g_nm == RW_TARGET[attr]})
RWT = pd.DataFrame(RW_ROWS)
RWE = pd.DataFrame(RW_EOD)
print("\nΔAUC reweighed arm − S:")
show(RWT[["arm", "pop", "est", "lo", "hi", "interval", "mdd", "w_min", "w_max", "verdict_auc"]], 4)
print("\nchange of equal-opportunity differences (reweighed − S), E-ALL:")
show(RWE, 3)
RWT.to_csv(OUT / "reweighing_auc.csv", index=False)
RWE.to_csv(OUT / "reweighing_eod.csv", index=False)
S8["reweighing"] = dict(auc=RWT.round(5).to_dict("records"), eod=RWE.round(5).to_dict("records"),
                        weight_range={a: [float(w.min()), float(w.max())] for a, w in RW_W.items()})

# %% [markdown]
# **So what.** Reweighing is an instructive null. Race weights range 0.70–1.16 (NH Black cases down-weighted most), yet every ΔAUC interval lies inside ±0.01. The gaps do not close either: race reweighing leaves the NH Asian gap
# where it was and *widens* the NH Black gap (CI excluding 0), because it removes the prevalence difference that made
# Black cases easier to find. Insurance and low-access reweighing narrow their gaps by about 0.04–0.05 with CIs including
# 0. Reweighing acts on the label–group association; the gaps of §8.3 come from features and from the diagnosis
# component of the label.

# %% [markdown]
# ## 9 WHtR measurement fix (P14-b)
# **Why.** §5 found that BMI under-reads adiposity in Asian adults (WHtR − BMI single-feature AUC gain +0.137 Asian vs
# +0.049 White), and §8.3 found Asian cases missed most because they are leaner. Arm S+WHtR replaces waist by
# waist-to-height ratio (P14, locked in §6, `prior_exposure = descriptive_seen`). Locked prediction **P14-b**: Asian TPR
# rises by at least 0.05 (falsifier: upper CI bound below 0.05), with a smaller White change. With 40 Asian positives
# clustered in few PSUs, a simple and a **PSU-cluster (Rao–Wu) bootstrap** are both computed; the wider decides.

# %%
# P14-b: replace waist by waist-to-height ratio (arm S+WHtR) and test the NH Asian TPR change against arm S.
# Computes simple and PSU-cluster bootstrap CIs per quantity and prints the table.
# Paired audits of S and S+WHtR for race under both resampling schemes.
pW = PM[("S+WHtR", 1, "lr")]
res = {}
for wt in ("simple", "psu"):
    point, boot, codes, mm = audit("race", "E-ALL", 1, ("S", "S+WHtR"), weights=wt)
    res[wt] = (point, boot)
# Level indices of the target group (NH Asian) and the control group (NH White).
lv = F.LEVELS["race"]
iA, iW = lv.index("NH Asian"), lv.index("NH White")
whtr_rows = []
# Add one table row: estimate plus simple and PSU-cluster CIs; the reported interval is the wider of the two.
def add_whtr(name, pt_fn):
    row = {"quantity": name}
    for wt in ("simple", "psu"):
        point, boot = res[wt]
        # pt_fn maps a point-estimate (or replicate) dict to the quantity of interest.
        e, lo, hi, se = F.summarise(pt_fn(point)[0], pt_fn(boot))
        bvals = np.asarray(pt_fn(boot), float)
        row.update({"est": e, f"{wt}_lo": lo, f"{wt}_hi": hi, f"{wt}_se": se, f"{wt}_boot_mean": float(np.nanmean(bvals))})
    # The wider interval decides: conservative with ~40 Asian positives clustered in few PSUs.
    wide = "psu" if (row["psu_hi"] - row["psu_lo"]) >= (row["simple_hi"] - row["simple_lo"]) else "simple"
    row.update(lo=row[f"{wide}_lo"], hi=row[f"{wide}_hi"], interval=wide)
    whtr_rows.append(row)
    return row
r_tA = add_whtr("TPR NH Asian, S", lambda d: d["tpr"][:, 0, iA])
r_tA2 = add_whtr("TPR NH Asian, S+WHtR", lambda d: d["tpr"][:, 1, iA])
r_tW = add_whtr("TPR NH White, S", lambda d: d["tpr"][:, 0, iW])
r_tW2 = add_whtr("TPR NH White, S+WHtR", lambda d: d["tpr"][:, 1, iW])
r_dA = add_whtr("ΔTPR NH Asian", lambda d: d["tpr"][:, 1, iA] - d["tpr"][:, 0, iA])
r_dW = add_whtr("ΔTPR NH White", lambda d: d["tpr"][:, 1, iW] - d["tpr"][:, 0, iW])
r_dd = add_whtr("ΔTPR Asian − ΔTPR White", lambda d: (d["tpr"][:, 1, iA] - d["tpr"][:, 0, iA]) - (d["tpr"][:, 1, iW] - d["tpr"][:, 0, iW]))
r_eod = add_whtr("Δ|EOD| Asian vs White", lambda d: np.abs(d["tpr"][:, 1, iA] - d["tpr"][:, 1, iW]) - np.abs(d["tpr"][:, 0, iA] - d["tpr"][:, 0, iW]))
r_auc = add_whtr("ΔAUC overall", lambda d: d["auc_all"][:, 1] - d["auc_all"][:, 0])
r_aA = add_whtr("ΔAUC within NH Asian", lambda d: d["auc"][:, 1, iA] - d["auc"][:, 0, iA])
r_aW = add_whtr("ΔAUC within NH White", lambda d: d["auc"][:, 1, iW] - d["auc"][:, 0, iW])
r_h4 = add_whtr("ΔAUC Asian − ΔAUC White (H4b, model level)", lambda d: (d["auc"][:, 1, iA] - d["auc"][:, 0, iA]) - (d["auc"][:, 1, iW] - d["auc"][:, 0, iW]))
WH = pd.DataFrame(whtr_rows)
show(WH[["quantity", "est", "simple_lo", "simple_hi", "simple_boot_mean", "psu_lo", "psu_hi", "psu_boot_mean", "interval"]], 3)
# E-SCREEN (secondary; NH Asian has 11 positives -> suppressed, numbers only)
pt_s, bt_s, _, _ = audit("race", "E-SCREEN", 1, ("S", "S+WHtR"))
dA_s = F.summarise(pt_s["tpr"][0, 1, iA] - pt_s["tpr"][0, 0, iA], bt_s["tpr"][:, 1, iA] - bt_s["tpr"][:, 0, iA])
print(f"\nE-SCREEN (suppressed, {int(pt_s['n_pos'][0, 0, iA])} Asian positives): ΔTPR NH Asian {dA_s[0]:+.3f} ({dA_s[1]:+.3f}, {dA_s[2]:+.3f})")
# P14-a (AUC change) was judged in §7; read it back so that P14 can combine parts (a) and (b).
p14a = next(r for r in S7m["scoreboard_detail"] if r["hyp_id"] == "P14" and r["sub"] == "(a) AUC" and r["pop"] == "E-ALL" and r["tier"] == 1)
print(f"P14-a from §7 (E-ALL, corrected t): ΔAUC {p14a['est']:+.4f} ({p14a['lo']:+.4f}, {p14a['hi']:+.4f}) -> {p14a['verdict']}")

# %%
# Apply the locked verdict rules for P14-b, P14 and H4b and draw the WHtR figure.
# Writes results/S8/whtr_p14b.csv; saves figure S8_whtr_asian_white.
# P14-b: the NH Asian TPR gain is judged against the +0.05 SESOI (GAP).
v_p14b = ek.verdict(r_dA["lo"], r_dA["hi"], GAP, "+", r_dA["est"])
v_p14b = "refuted" if (v_p14b == "equivalent" or r_dA["hi"] < GAP) else v_p14b     # locked falsifier
# White control: the White change should be smaller in size than the Asian change.
control_ok = abs(r_dW["est"]) < abs(r_dA["est"])
# P14 overall combines part (a), AUC unchanged, and part (b), the Asian gain.
v_p14 = ek.combine_verdicts([p14a["verdict"], v_p14b])
# H4b at model level: supported if the CI lies above 0 and the estimate reaches the AUC SESOI;
# refuted if the CI lies wholly below 0.
v_h4b_model = ("supported" if (r_h4["lo"] > 0 and r_h4["est"] >= AUC_SESOI) else
               "refuted" if r_h4["hi"] < 0 else "inconclusive")
# H4b primary verdict is the single-feature test of §5 (stored); the model-level result is secondary.
s5_h4b = R.load_section("S5")["hypotheses"]["H4b"]["verdict"]
# 'mixed' only when both verdicts are decisive and disagree; otherwise the §5 verdict stands.
v_h4b = "mixed" if (s5_h4b in ("supported", "refuted") and v_h4b_model in ("supported", "refuted") and v_h4b_model != s5_h4b) else s5_h4b
print(f"P14-b: ΔTPR NH Asian {r_dA['est']:+.3f} ({r_dA['lo']:+.3f}, {r_dA['hi']:+.3f}; {r_dA['interval']} interval) -> {v_p14b}; "
      f"White control |Δ| smaller: {control_ok}")
print(f"P14 overall (a: {p14a['verdict']}, b: {v_p14b}) -> {v_p14}")
print(f"H4b model level: {r_h4['est']:+.3f} ({r_h4['lo']:+.3f}, {r_h4['hi']:+.3f}) -> {v_h4b_model}; S5 single-feature verdict "
      f"{s5_h4b} -> H4b {v_h4b}")
WH.to_csv(OUT / "whtr_p14b.csv", index=False)
S8["whtr"] = dict(table=WH.round(5).to_dict("records"), p14b_verdict=v_p14b, p14_verdict=v_p14, white_control_smaller=control_ok,
                  p14a_from_S7={k: p14a[k] for k in ("est", "lo", "hi", "verdict")}, h4b_model_verdict=v_h4b_model,
                  h4b_s5_verdict=s5_h4b, h4b_verdict=v_h4b, escreen_dtpr_asian=list(dA_s[:3]))

fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1, 1.2]})
# Left panel: TPR of NH Asian and NH White under S (waist) and S+WHtR, simple-bootstrap CI.
ax = axes[0]
for j, (nm, a, b) in enumerate([("NH Asian", r_tA, r_tA2), ("NH White", r_tW, r_tW2)]):
    for k_, (r_, col, lab) in enumerate([(a, C.OKABE_ITO["grey"], "S (waist)"), (b, C.OKABE_ITO["orange"], "S+WHtR")]):
        x = j + (k_ - 0.5) * 0.25
        ax.errorbar(x, r_["est"], yerr=[[r_["est"] - r_["simple_lo"]], [r_["simple_hi"] - r_["est"]]], fmt="o", color=col,
                    capsize=3, label=lab if j == 0 else None)
ax.set_xticks([0, 1]); ax.set_xticklabels([f"NH Asian\n({int(res['simple'][0]['n_pos'][0, 0, iA])} cases)",
                                            f"NH White\n({int(res['simple'][0]['n_pos'][0, 0, iW])} cases)"])
ax.set_ylabel("TPR at specificity 0.80"); ax.set_ylim(0, 1); ax.legend(loc="lower right")
ax.set_title("Sensitivity by arm (simple bootstrap CI)")
# Right panel: paired changes with both bootstrap CIs; dotted line = the +0.05 gain.
ax = axes[1]
qs = ["ΔTPR NH Asian", "ΔTPR NH White", "ΔTPR Asian − ΔTPR White", "ΔAUC overall"]
for i, q in enumerate(qs):
    r_ = WH.set_index("quantity").loc[q]
    for k_, (wt, col) in enumerate([("simple", C.OKABE_ITO["blue"]), ("psu", C.OKABE_ITO["vermillion"])]):
        ax.errorbar(r_["est"], -i + (k_ - 0.5) * 0.25, xerr=[[r_["est"] - r_[f"{wt}_lo"]], [r_[f"{wt}_hi"] - r_["est"]]],
                    fmt="o", color=col, capsize=3, label=("simple bootstrap" if wt == "simple" else "PSU (Rao–Wu) bootstrap") if i == 0 else None)
ax.axvline(0, color="black", lw=0.8); ax.axvline(GAP, color="black", lw=0.8, ls=":")
ax.set_yticks([-i for i in range(len(qs))]); ax.set_yticklabels(qs)
ax.set_xlabel("difference S+WHtR − S (dotted: pre-registered +0.05)"); ax.legend(fontsize=8, loc="lower right")
ax.set_title(f"P14-b: {v_p14b}")
fig.tight_layout()
f83 = plots.savefig(fig, "S8_whtr_asian_white", caption="F8-3. WHtR measurement fix (arm S+WHtR vs S, E-ALL, Tier 1): TPR at "
                    "specificity 0.80 for NH Asian and NH White adults (left) and the paired changes with simple stratified and "
                    "PSU-cluster (Rao-Wu) bootstrap 95 % CIs (right); dotted line = pre-registered minimum gain of 0.05.")
plt.show()

# %% [markdown]
# **So what.** The fix moves the right group in the right direction, but by little: NH Asian sensitivity rises by +0.025
# – one more case of 40 – against +0.013 for White adults, with overall AUC unchanged (P14-a). The PSU interval runs from
# about −0.04 to +0.07, so P14-b is **inconclusive**. At model level the single-feature WHtR advantage (H4b) largely
# disappears: the model already contains waist, height and BMI. WHtR is not adopted as a new preparation step.

# %% [markdown]
# ## 10 Group-specific thresholds
# **Why.** A group-specific threshold (Hardt et al. 2016) is **not** implemented (DR-S8-02: it needs race at prediction
# time and equalises TPR by "levelling down"); its instability with about 40 Asian cases is quantified here.

# %%
# Counterfactual group threshold: the NH Asian cut-off that would match the NH White TPR (not adopted).
# Quantifies its false-positive cost and its instability by bootstrap.
# Returns (Asian threshold with weighted TPR equal to the White TPR, Asian FPR there, White TPR).
def asian_threshold(w=None):
    # w: optional bootstrap counts used as weights; default equal weights.
    w = np.ones(n) if w is None else w
    a_pos, a_neg = (grp["race"].eq("NH Asian").to_numpy() & (y == 1)), (grp["race"].eq("NH Asian").to_numpy() & (y == 0))
    w_pos = (grp["race"].eq("NH White").to_numpy() & (y == 1))
    # Positives caught by the shared threshold.
    hit = pS >= thr_check
    tpr_w = np.average(hit[w_pos], weights=w[w_pos])
    # Sort the Asian case scores and carry their weights along.
    s_ = np.sort(pS[a_pos]); ww = w[a_pos][np.argsort(pS[a_pos])]
    cum = np.cumsum(ww[::-1])[::-1] / ww.sum()          # share of Asian cases at or above each score
    # Highest sorted score whose upper tail still reaches the White TPR.
    k = np.flatnonzero(cum >= tpr_w - 1e-12).max()
    t_a = s_[k]
    fpr_a = np.average(pS[a_neg] >= t_a, weights=w[a_neg])
    return t_a, fpr_a, tpr_w
t_a, fpr_a, tpr_w = asian_threshold()
# Bootstrap counts stratified by race x label give percentile CIs for the Asian threshold and FPR.
Wst = F.stratified_counts((grp["race"].astype(str) + "|" + pd.Series(y).astype(str)).to_numpy(), C.N_BOOT, ek.derive_seed(C.SEED_MASTER, "S8", "gthr"))
bt = np.array([asian_threshold(Wst[b])[:2] for b in range(len(Wst))])
# Asian FPR at the shared threshold, from the E-ALL group table.
fpr_overall_a = float(GT1.set_index(["attribute", "group"]).loc[("race", "NH Asian"), "fpr"])
GTHR = dict(threshold_overall=thr_check, threshold_asian=t_a, threshold_asian_ci=list(np.percentile(bt[:, 0], [2.5, 97.5])),
            fpr_asian_at_own=fpr_a, fpr_asian_at_own_ci=list(np.percentile(bt[:, 1], [2.5, 97.5])), fpr_asian_at_shared=fpr_overall_a,
            tpr_white=tpr_w)
print(f"shared threshold {thr_check:.3f}; Asian threshold matching the White TPR ({tpr_w:.3f}): {t_a:.3f} "
      f"(95 % CI {GTHR['threshold_asian_ci'][0]:.3f}-{GTHR['threshold_asian_ci'][1]:.3f})")
print(f"Asian FPR: {fpr_overall_a:.3f} at the shared threshold -> {fpr_a:.3f} at the group threshold "
      f"(95 % CI {GTHR['fpr_asian_at_own_ci'][0]:.3f}-{GTHR['fpr_asian_at_own_ci'][1]:.3f})")
S8["group_threshold_counterfactual"] = GTHR


# %% [markdown]
# ## 11 Fairness–performance trade-off
# **Why.** A mitigation is worth adopting only if it narrows its target gap without costing discrimination: ΔAUC vs the
# change in the target group's |TPR gap|, with a "no practical change" box of |ΔAUC| < 0.01 and |Δ gap| < 0.05.

# %%
# Fairness-performance trade-off: ΔAUC against the change of the targeted group's |TPR gap| per arm.
# Writes results/S8/tradeoff.csv; saves figure S8_tradeoff.
# ΔAUC of WHtR versus S, computed with the same engine as for the reweighing arms.
wh_auc = compare_auc(OOF[("S+WHtR", 1, "lr")], OOF[("S", 1, "lr")], "E-ALL", tag="whtr")
TO = []
for attr, tgt in RW_TARGET.items():
    # Reweighing arms: ΔAUC on E-ALL and Δ|EOD| of the targeted group.
    a = RWT[(RWT["arm"] == f"S+RW({attr})") & (RWT["pop"] == "E-ALL")].iloc[0]
    e = RWE[(RWE["arm"] == f"S+RW({attr})") & (RWE["group"] == tgt)].iloc[0]
    TO.append({"arm": f"S+RW({attr})", "target": tgt, "d_auc": a["est"], "d_auc_lo": a["lo"], "d_auc_hi": a["hi"],
               "d_abs_eod": e["d_abs_eod"], "d_abs_eod_lo": e["d_abs_lo"], "d_abs_eod_hi": e["d_abs_hi"]})
# WHtR arm: the target group is NH Asian.
TO.append({"arm": "S+WHtR", "target": "NH Asian", "d_auc": wh_auc["est"], "d_auc_lo": wh_auc["lo"], "d_auc_hi": wh_auc["hi"],
           "d_abs_eod": r_eod["est"], "d_abs_eod_lo": r_eod["lo"], "d_abs_eod_hi": r_eod["hi"]})
TO = pd.DataFrame(TO)
# 'No practical change' box: both CIs entirely inside |ΔAUC| < SESOI and |Δ gap| < 0.05.
TO["in_no_change_box"] = (TO["d_auc_lo"] > -AUC_SESOI) & (TO["d_auc_hi"] < AUC_SESOI) & (TO["d_abs_eod_lo"] > -GAP) & (TO["d_abs_eod_hi"] < GAP)
show(TO, 4)
TO.to_csv(OUT / "tradeoff.csv", index=False)
S8["tradeoff"] = TO.round(5).to_dict("records")

fig, ax = plt.subplots(figsize=(7.5, 5))
# Grey rectangle = the no-practical-change box.
ax.add_patch(plt.Rectangle((-AUC_SESOI, -GAP), 2 * AUC_SESOI, 2 * GAP, color=C.OKABE_ITO["grey"], alpha=0.15, lw=0))
cols = [C.OKABE_ITO["blue"], C.OKABE_ITO["green"], C.OKABE_ITO["purple"], C.OKABE_ITO["orange"]]
for (_, r), col in zip(TO.iterrows(), cols):
    ax.errorbar(r["d_auc"], r["d_abs_eod"], xerr=[[r["d_auc"] - r["d_auc_lo"]], [r["d_auc_hi"] - r["d_auc"]]],
                yerr=[[r["d_abs_eod"] - r["d_abs_eod_lo"]], [r["d_abs_eod_hi"] - r["d_abs_eod"]]], fmt="o", color=col,
                capsize=3, ms=7, label=f"{r['arm']} – gap of {r['target']}")
ax.axhline(0, color="black", lw=0.7); ax.axvline(0, color="black", lw=0.7)
ax.set_xlabel("ΔAUC vs S, E-ALL (95 % CI)")
ax.set_ylabel("change of |TPR gap| of the targeted group (95 % CI)\nnegative = gap narrows")
ax.set_xlim(-0.03, 0.03)
ax.legend(fontsize=8, loc="upper left")
ax.set_title("Fairness–performance trade-off of the mitigation arms\n(grey box: |ΔAUC| < 0.01 and |Δ gap| < 0.05)")
f85 = plots.savefig(fig, "S8_tradeoff", caption="F8-5. Fairness-performance plane for the mitigation arms (Tier 1): ΔAUC "
                    "against arm S on E-ALL (wider of corrected-t and paired-bootstrap CI) versus the change in the absolute "
                    "TPR gap of the targeted group at specificity 0.80 (paired stratified bootstrap); grey box = no practical change.")
plt.show()

# %% [markdown]
# **So what – screening audit and mitigation nulls (§8.4, §8.5, §8.10, §8.11).** On E-SCREEN only the sex contrast is
# reportable: undiagnosed women are found less often than men (EOD about −0.17, CI includes 0, permutation p about
# 0.09); race gaps rest on 11–24 positives ("not measurable", not "fair"). Tier 2 lipids move every gap by less than its
# CI. An Asian-specific threshold matching the White TPR would raise Asian false positives by about 40 % and is itself
# unstable. All four mitigations cost no AUC, and none demonstrably helps (gap changes −0.05 to +0.02, intervals wider
# than ±0.05): "cheap, harmless, not shown to help".

# %% [markdown]
# ## 12 Within-group calibration
# **Why.** Calibration within groups (a predicted 20 % meaning 20 % in every group) is a second fairness criterion that
# cannot in general hold together with equal sensitivity when prevalences differ (Chouldechova 2017). Arm S is
# class-weighted, so absolute calibration is checked on **S−B6a**, its AUC-equivalent sibling without class weights: O:E
# (group-stratified bootstrap, so the number of cases varies), calibration-in-the-large (CITL) and slope.

# %%
# Within-group calibration of S-B6a (arm S without class weights): O:E, calibration-in-the-large, slope.
# Writes results/S8/group_calibration.csv; saves figure S8_group_calibration.
# S-B6a keeps the true prevalence scale, so absolute calibration is interpretable (arm S is class-weighted).
pC = PM[("S-B6a", 1, "lr")]
cal_rows = []
for attr in F.ATTRIBUTES:
    # Group-stratified bootstrap (weights='group'): the number of observed cases varies, as O:E requires.
    point, boot, codes, mm = audit(attr, "E-ALL", 1, ("S-B6a", "S"), weights="group")
    lvls = F.LEVELS[attr]
    # Overall O:E of arm S, used to express each group's O:E of S relative to it.
    oe_all_S = y.sum() / pS.sum()
    for g_i, g_nm in enumerate(lvls):
        m = grp[attr].eq(g_nm).to_numpy()
        # Calibration slope, intercept and calibration-in-the-large (CITL) within the group.
        slope, icpt, citl = ek._calibration(y[m], pC[m])
        e, lo, hi, _ = F.summarise(point["oe"][0, 0, g_i], boot["oe"][:, 0, g_i])
        cal_rows.append({"attribute": attr, "group": g_nm, "n": int(m.sum()), "n_pos": int(y[m].sum()),
                         "mean_pred": pC[m].mean(), "observed": y[m].mean(), "oe": e, "oe_lo": lo, "oe_hi": hi,
                         "citl": citl, "slope": slope, "oe_S_relative": point["oe"][0, 1, g_i] / oe_all_S})
CAL = pd.DataFrame(cal_rows)
# A CI that excludes 1 marks a group that is mis-calibrated in the large.
CAL["oe_ci_excludes_1"] = (CAL["oe_lo"] > 1) | (CAL["oe_hi"] < 1)
slope_all, _, citl_all = ek._calibration(y, pC)
print(f"S-B6a overall: O:E {y.sum() / pC.sum():.3f}, CITL {citl_all:+.3f}, slope {slope_all:.3f}")
show(CAL, 3)
CAL.to_csv(OUT / "group_calibration.csv", index=False)
S8["calibration"] = dict(table=CAL.round(5).to_dict("records"), overall=dict(oe=float(y.sum() / pC.sum()), citl=citl_all, slope=slope_all),
                         groups_oe_ci_excl_1=CAL.loc[CAL["oe_ci_excludes_1"], ["attribute", "group", "oe"]].round(3).to_dict("records"))

fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1, 1.3]})
ax = axes[0]
for g_nm, col in zip(F.LEVELS["race"], plots.PALETTE):
    m = grp["race"].eq(g_nm).to_numpy()
    # Fewer quantile bins for small groups (< 600 rows) keep the bins populated.
    nb = 5 if m.sum() < 600 else 10
    # duplicates='drop' merges identical bin edges.
    q = pd.qcut(pC[m], nb, labels=False, duplicates="drop")
    d_ = pd.DataFrame({"p": pC[m], "y": y[m], "q": q}).groupby("q").mean()
    ax.plot(d_["p"], d_["y"], "o-", color=col, label=f"{g_nm} (n={int(m.sum())})", ms=4)
# Diagonal = perfect calibration.
ax.plot([0, 0.7], [0, 0.7], color="black", lw=0.8, ls="--")
ax.set_xlabel("mean predicted probability (S−B6a, quantile bins)"); ax.set_ylabel("observed share with diabetes")
ax.set_title("Calibration curves by race"); ax.legend(fontsize=7)
ax = axes[1]
k = 0; yt, yl = [], []
for attr in F.ATTRIBUTES:
    for _, r in CAL[CAL["attribute"] == attr].iterrows():
        ax.errorbar(r["oe"], -k, xerr=[[r["oe"] - r["oe_lo"]], [r["oe_hi"] - r["oe"]]], fmt="o",
                    color=C.OKABE_ITO["vermillion"] if r["oe_ci_excludes_1"] else C.OKABE_ITO["blue"], capsize=2)
        yt.append(-k); yl.append(f"{attr}: {r['group']}"); k += 1
    k += 0.5
ax.axvline(1, color="black", lw=0.8, ls="--")
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=8)
ax.set_xlabel("observed / expected cases (S−B6a, 95 % bootstrap CI); red = CI excludes 1")
ax.set_title("Calibration-in-the-large by group")
fig.tight_layout()
f84 = plots.savefig(fig, "S8_group_calibration", caption="F8-4. Within-group calibration of arm S-B6a (arm S without class "
                    "weights, AUC-equivalent): calibration curves by race (quantile bins) and observed/expected ratio by audit "
                    "group with stratified bootstrap 95 % CI (E-ALL, Tier 1, training part OOF).")
plt.show()

# %% [markdown]
# **So what.** S−B6a is well calibrated overall (O:E about 1.02, slope about 0.98) and across insurance, access, income and
# sex, but **not across race**: it under-predicts for NH Black, NH Asian (O:E about 1.35) and Mexican American adults
# (CIs excluding 1) and over-predicts for NH White adults. A race-blind score averages over groups whose prevalence
# differs at the same feature values – the second face of the Asian TPR gap. Correcting it would need race as an input
# or race-specific recalibration, excluded for the reasons of §8.10; it is a limitation for any individual use.
# %% [markdown]
# ## 13 Verdicts
# **Why.** Each locked hypothesis tested here gets one verdict from its locked rule (`evalkit.verdict` with the SESOI
# of `config.SESOI`, sub-claims combined by `evalkit.combine_verdicts`). H3 is a genuine pre-registration; P14-b and H4b
# were written after a descriptive look. The gap flags of §8.3–§8.4 are audit findings, listed separately.

# %%
# Collect the locked verdicts (H3, P14, H4b) in one scoreboard; list substantive audit gaps separately.
# Writes results/S8/scoreboard.csv.
# Substantive, reportable gaps are audit flags, not hypotheses.
sub_eall = ET1[ET1["substantive"] & ET1["verdict_status"].eq("reportable")]
sub_escr = ETs[ETs["substantive"] & ETs["verdict_status"].eq("reportable")]
# One row per locked sub-claim; the evidence strings are built from computed values, not typed.
SB8 = pd.DataFrame([
    dict(hyp_id="H3", prior_exposure="none", sub="E1 L_self misses Undiagnosed most", verdict=elem_v["E1"],
         evidence="; ".join(f"{r.contrast} {r.est:+.3f} ({r.lo:+.3f}, {r.hi:+.3f})" for r in H3E[H3E.element == "E1"].itertuples())),
    dict(hyp_id="H3", prior_exposure="none", sub="E2 L_A1c misses D_controlled most", verdict=elem_v["E2"],
         evidence="; ".join(f"{r.contrast} {r.est:+.3f} ({r.lo:+.3f}, {r.hi:+.3f})" for r in H3E[H3E.element == "E2"].itertuples())),
    dict(hyp_id="H3", prior_exposure="none", sub="E3 L_comb smallest worst-cell gap", verdict=elem_v["E3"],
         evidence="; ".join(f"{r.contrast} {r.est:+.3f} ({r.lo:+.3f}, {r.hi:+.3f})" for r in H3E[H3E.element == "E3"].itertuples())),
    dict(hyp_id="H3", prior_exposure="none", sub="overall", verdict=h3_v, evidence="combine_verdicts(E1-E3); falsifier: any contrast reversed with CI excluding 0"),
    dict(hyp_id="P14", prior_exposure="descriptive_seen", sub="(a) |ΔAUC| < 0.01 (from S7)", verdict=p14a["verdict"],
         evidence=f"ΔAUC {p14a['est']:+.4f} ({p14a['lo']:+.4f}, {p14a['hi']:+.4f}), corrected t"),
    dict(hyp_id="P14", prior_exposure="descriptive_seen", sub="(b) NH Asian ΔTPR ≥ +0.05", verdict=v_p14b,
         evidence=f"ΔTPR {r_dA['est']:+.3f} ({r_dA['lo']:+.3f}, {r_dA['hi']:+.3f}), {r_dA['interval']} interval; White ΔTPR {r_dW['est']:+.3f}"),
    dict(hyp_id="P14", prior_exposure="descriptive_seen", sub="overall", verdict=v_p14, evidence="combine_verdicts(a, b)"),
    dict(hyp_id="H4b", prior_exposure="descriptive_seen", sub="single feature (S5)", verdict=s5_h4b,
         evidence=R.load_section("S5")["hypotheses"]["H4b"]["estimate"]),
    dict(hyp_id="H4b", prior_exposure="descriptive_seen", sub="model level (S8, secondary)", verdict=v_h4b_model,
         evidence=f"ΔAUC_Asian − ΔAUC_White {r_h4['est']:+.4f} ({r_h4['lo']:+.4f}, {r_h4['hi']:+.4f})"),
    dict(hyp_id="H4b", prior_exposure="descriptive_seen", sub="overall", verdict=v_h4b,
         evidence="S5 primary; a decisive contradicting S8 model-level verdict would make it mixed"),
])
# Guard: every verdict belongs to the allowed vocabulary C.VERDICTS.
assert set(SB8["verdict"]) <= set(C.VERDICTS)
show(SB8)
print("\naudit flags (not hypotheses): substantive reportable gaps")
for nm_, d_ in (("E-ALL", sub_eall), ("E-SCREEN", sub_escr)):
    print(f"  {nm_}: " + ("; ".join(f"{r.attribute} {r.group} {r.eod:+.3f} [{r.eod_lo:+.3f}, {r.eod_hi:+.3f}]" for r in d_.itertuples()) or "none"))
SB8.to_csv(OUT / "scoreboard.csv", index=False)
S8["scoreboard"] = {h: g.set_index("sub")["verdict"].to_dict() for h, g in SB8.groupby("hyp_id")}
S8["verdicts"] = {"H3": h3_v, "P14": v_p14, "P14b": v_p14b, "H4b": v_h4b, "H4b_model_level": v_h4b_model}
S8["substantive_gaps"] = {"E-ALL": sub_eall[["attribute", "group", "eod", "eod_lo", "eod_hi"]].round(4).to_dict("records"),
                          "E-SCREEN": sub_escr[["attribute", "group", "eod", "eod_lo", "eod_hi"]].round(4).to_dict("records")}

# %% [markdown]
# **So what.** No fairness experiment produces a decisive verdict, and each "inconclusive" is specific: **H3** – all
# three orderings point the right way, but the label shifts recall by at most about 0.06 against CIs about ±0.07 wide;
# **P14** – WHtR is harmless (a) and moves Asian sensitivity the predicted way, but its +0.025 neither confirms nor
# excludes +0.05 (b); **H4b** – the single-feature WHtR advantage (§5, supported) does not transfer to the model. The
# decisive results are audit findings: a substantive NH Asian sensitivity gap beyond the permutation null
# (exploratory), SES-driven income gaps, an access imprint under self-report, and race-level miscalibration of a
# race-blind model. A FAST re-run can move the borderline audit items across their thresholds.

# %% [markdown]
# ## 14 Outputs
# **Why.** Every decision goes into the §8 decision register with evidence computed above (no value typed by hand), and
# every number into `results/metrics_S8.json` and `results/S8/`, from which §10 and the slides read.

# %%
# Build the §8 decision register: every evidence_value is an f-string over variables computed above.
# Writes governance/register/S8.csv.
# Register column order, shared by the other sections' registers.
REGISTER_COLS = ["dr_id", "stage", "date", "type", "finding", "evidence_ref", "evidence_value", "decision",
                 "alternatives_rejected", "hyp_id", "status", "check_verdict", "check_note", "loop_ref", "change_request", "commit"]
TODAY = "2026-10-11"
# Shorthands used by the evidence strings below.
eodA = ET1.set_index(["attribute", "group"]).loc[("race", "NH Asian")]
permr = PERM1.set_index("attribute")
rw_rng = {a: f"{w.min():.2f}-{w.max():.2f}" for a, w in RW_W.items()}
rw_auc = RWT[RWT["pop"] == "E-ALL"].set_index("arm")
cal_race = CAL[(CAL["attribute"] == "race") & CAL["oe_ci_excludes_1"]]
acc_d = ACCD.set_index(["feature", "contrast"])
sex_s = ETs.set_index("attribute").loc["sex"]
# Each dict is one decision-register row.
reg = [
    dict(dr_id="DR-S8-01", type="audit_design",
         finding="Group cells are small (no oversampling in 2021-23); E-SCREEN has 127 positives in the training part",
         evidence_ref="results/S8/group_sizes.csv", evidence_value=f"suppressed groups E-ALL {n_supp['eall']}/16, E-SCREEN {n_supp['escreen']}/16; NH Asian 40 positives (E-ALL)",
         decision="Audit race (NH Asian separate, exploratory), insurance, low access, income band, sex on training-part OOF; NCHS rule n<30 or positives<30 -> show, no gap verdict",
         alternatives_rejected="Pooling Asian with Other/Multi (hides the BMI measurement issue); verdicts on suppressed cells",
         status="decided", check_verdict="PASS", check_note="counts recomputed from the cohort and the stored split"),
    dict(dr_id="DR-S8-02", type="threshold",
         finding="One operating point is needed to compare groups; group thresholds need race at prediction time",
         evidence_ref="§8.2 and §8.10; results/metrics_S8.json group_threshold_counterfactual",
         evidence_value=f"shared threshold {thr_check:.3f} (spec 0.80, E-ALL); Asian threshold for White TPR {t_a:.3f} (CI {GTHR['threshold_asian_ci'][0]:.3f}-{GTHR['threshold_asian_ci'][1]:.3f}), Asian FPR {fpr_overall_a:.3f}->{fpr_a:.3f}",
         decision="Single threshold at overall specificity 0.80, re-estimated in each bootstrap replicate; no group-specific thresholds (race would be needed at prediction time)",
         alternatives_rejected="ThresholdOptimizer / equalised-odds post-processing (uses race at prediction, levelling down, unstable with ~40 cases)",
         status="decided", check_verdict="PASS", check_note="engine threshold equals evalkit.recall_at_specificity (asserted)"),
    dict(dr_id="DR-S8-03", type="finding",
         finding="Model reproduces label and measurement bias: NH Asian and income gaps exceed the permutation null on E-ALL",
         evidence_ref="results/S8/eod_eall_t1.csv; results/S8/permutation.csv; results/S8/gap_decomposition.csv; figures/S8_group_tpr.png",
         evidence_value=f"NH Asian EOD {eodA['eod']:+.3f} ({eodA['eod_lo']:+.3f}, {eodA['eod_hi']:+.3f}), race max|EOD| p {permr.loc['race', 'p_value']:.3f}; income p {permr.loc['income', 'p_value']:.3f}; TPR diagnosed {tpr_dx_all:.2f} vs undiagnosed {tpr_ud_all:.2f}",
         decision="Report gaps with CIs and permutation baseline; attribute them to routes (diagnosis/care traces, BMI, SES inputs); ecological-fallacy caveat; no claim about individual risk",
         alternatives_rejected="Reporting raw group differences without a null; interpreting group TPR as individual risk",
         hyp_id="", status="decided", check_verdict="PASS", check_note="NH Asian exploratory (40 positives)"),
    dict(dr_id="DR-S8-04", type="finding",
         finding="Screening-population (E-SCREEN) fairness cannot be audited by race, insurance or access at this sample size",
         evidence_ref="results/S8/eod_escreen_t1.csv",
         evidence_value=f"reportable E-SCREEN contrasts {len(rep_s)}/{len(ETs)}; female - male EOD {sex_s['eod']:+.3f} ({sex_s['eod_lo']:+.3f}, {sex_s['eod_hi']:+.3f}), permutation p {PERMs.set_index('attribute').loc['sex', 'p_value']:.3f}",
         decision="E-SCREEN group gaps shown as numbers only; the only reportable contrast (sex) reported with CI and permutation p; limitation for S10",
         alternatives_rejected="Pooling E-ALL and E-SCREEN (mixes the use cases)", status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-05", type="hypothesis_test",
         finding="3x3 label matrix: predicted ordering points the right way but differences are small; Undiagnosed is hardest for every label",
         evidence_ref="results/S8/label_matrix_cells.csv; results/S8/h3_contrasts.csv; figures/S8_label_matrix.png",
         evidence_value=f"recall Undiagnosed L_self {LM['recall'].loc['L_self', 'Undiagnosed']:.3f}, L_A1c {LM['recall'].loc['L_A1c', 'Undiagnosed']:.3f}, L_comb {LM['recall'].loc['L_comb', 'Undiagnosed']:.3f}; D_controlled L_A1c {LM['recall'].loc['L_A1c', 'D_controlled']:.3f}; elements {elem_v}",
         decision=f"H3 verdict {h3_v}; L_comb stays the frozen target", alternatives_rejected="Switching the training label after seeing the matrix",
         hyp_id="H3", status="decided", check_verdict="PASS", check_note="L_comb x Undiagnosed cell equals E-SCREEN recall of S (asserted)"),
    dict(dr_id="DR-S8-06", type="audit",
         finding="Trained on self-report, the model learns that poor access means lower risk; the label contrast points the same way",
         evidence_ref="results/S8/access_audit_coefs.csv; results/S8/access_audit_diffs.csv",
         evidence_value=f"no usual place under L_self {ACC.set_index(['feature', 'label']).loc[('no_usual_place', 'L_self'), 'coef_per_sd']:+.3f} ({ACC.set_index(['feature', 'label']).loc[('no_usual_place', 'L_self'), 'lo']:+.3f}, {ACC.set_index(['feature', 'label']).loc[('no_usual_place', 'L_self'), 'hi']:+.3f}); uninsured L_self - L_comb {acc_d.loc[('uninsured', 'L_self - L_comb'), 'diff_per_sd']:+.3f} ({acc_d.loc[('uninsured', 'L_self - L_comb'), 'lo']:+.3f}, {acc_d.loc[('uninsured', 'L_self - L_comb'), 'hi']:+.3f}); no usual place {acc_d.loc[('no_usual_place', 'L_self - L_comb'), 'diff_per_sd']:+.3f} ({acc_d.loc[('no_usual_place', 'L_self - L_comb'), 'lo']:+.3f}, {acc_d.loc[('no_usual_place', 'L_self - L_comb'), 'hi']:+.3f})",
         decision="Access features remain audit-only (P03); evidence supports the union label over self-report",
         alternatives_rejected="Adding insurance/usual place as predictors (would encode access to diagnosis)", status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-07", type="mitigation",
         finding="Race reweighing changes neither AUC nor the Asian gap and widens the NH Black gap",
         evidence_ref="results/S8/reweighing_auc.csv; results/S8/reweighing_eod.csv",
         evidence_value=f"w range race {rw_rng['race']}; dAUC {rw_auc.loc['S+RW(race)', 'est']:+.4f} ({rw_auc.loc['S+RW(race)', 'lo']:+.4f}, {rw_auc.loc['S+RW(race)', 'hi']:+.4f})",
         decision="Not adopted; reported as a null mitigation", alternatives_rejected="Race as a model feature (S9 sensitivity only)",
         status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-08", type="mitigation",
         finding="Insurance and low-access reweighing: AUC unchanged, targeted gaps narrow slightly with CIs including 0",
         evidence_ref="results/S8/reweighing_auc.csv; results/S8/reweighing_eod.csv; results/S8/tradeoff.csv",
         evidence_value=f"w range insurance {rw_rng['insurance']}, low access {rw_rng['low_access']}; dAUC {rw_auc.loc['S+RW(insurance)', 'est']:+.4f} / {rw_auc.loc['S+RW(low_access)', 'est']:+.4f}",
         decision="Not adopted (no demonstrated benefit); extension item complete", alternatives_rejected="Adopting on point estimates",
         status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-09", type="hypothesis_test",
         finding="WHtR raises NH Asian TPR in point estimate only; PSU-cluster interval crosses 0",
         evidence_ref="results/S8/whtr_p14b.csv; figures/S8_whtr_asian_white.png",
         evidence_value=f"Asian dTPR {r_dA['est']:+.3f} (simple {r_dA['simple_lo']:+.3f}, {r_dA['simple_hi']:+.3f}; PSU {r_dA['psu_lo']:+.3f}, {r_dA['psu_hi']:+.3f}); White {r_dW['est']:+.3f}; dAUC {r_auc['est']:+.4f}",
         decision=f"P14-b {v_p14b}, P14 {v_p14}; WHtR not adopted as a new preparation step; no return to the §6 design",
         alternatives_rejected="Adopting WHtR on the point estimate (post hoc)", hyp_id="P14", status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-10", type="hypothesis_test",
         finding="The single-feature WHtR advantage for Asian adults does not transfer to the multivariable model",
         evidence_ref="results/S8/whtr_p14b.csv", evidence_value=f"model-level dAUC Asian - White {r_h4['est']:+.4f} ({r_h4['lo']:+.4f}, {r_h4['hi']:+.4f})",
         decision=f"H4b stays {v_h4b} on the S5 single-feature test; S8 model-level result {v_h4b_model} reported as secondary",
         hyp_id="H4b", status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-11", type="finding",
         finding="Race-blind model is calibrated overall but not within race",
         evidence_ref="results/S8/group_calibration.csv; figures/S8_group_calibration.png",
         evidence_value=f"S-B6a O:E overall {y.sum() / pC.sum():.2f}; groups with CI excluding 1: {cal_race[['group', 'oe']].round(2).to_dict('records')}",
         decision="Reported as a limitation; no race-specific recalibration (same reasons as DR-S8-02)",
         alternatives_rejected="Race-specific recalibration", status="decided", check_verdict="PASS"),
    dict(dr_id="DR-S8-12", type="tradeoff",
         finding="No mitigation arm narrows its targeted gap demonstrably; none costs AUC",
         evidence_ref="results/S8/tradeoff.csv; figures/S8_tradeoff.png",
         evidence_value="; ".join(f"{r.arm}: dAUC {r.d_auc:+.4f} [{r.d_auc_lo:+.4f}, {r.d_auc_hi:+.4f}], d|gap| {r.d_abs_eod:+.3f} [{r.d_abs_eod_lo:+.3f}, {r.d_abs_eod_hi:+.3f}]" for r in TO.itertuples()),
         decision="No mitigation adopted; reported as 'cheap, harmless, not shown to help'", alternatives_rejected="Adopting the arm with the best point estimate",
         status="decided", check_verdict="PASS"),
]
# Fill missing columns with '' and enforce the schema's column order.
REG8 = pd.DataFrame(reg)
REG8["stage"], REG8["date"] = "S8", TODAY
for c in REGISTER_COLS:
    if c not in REG8:
        REG8[c] = ""
REG8 = REG8[REGISTER_COLS].fillna("")
REG8.to_csv(C.GOVERNANCE_DIR / "register" / "S8.csv", index=False, lineterminator="\n")
show(REG8[["dr_id", "type", "decision"]])

# %%
# Export all tables, figure names, runtime and verdicts.
# Writes results/S8/*.csv and results/metrics_S8.json.
for nm, df_ in {"group_metrics_eall_t1": GT1, "eod_eall_t1": ET1, "group_metrics_escreen_t1": GTs, "eod_escreen_t1": ETs,
                "group_metrics_eall_t2": GT2, "eod_eall_t2": ET2,
                "permutation": pd.concat([PERM1, PERMs, PERM2], ignore_index=True)}.items():
    df_.to_csv(OUT / f"{nm}.csv", index=False)
S8["figures"] = [f81, f81b, f82, f83, f84, f85]
S8["runtime_seconds"] = time.time() - T_START
R.save_section("S8", S8)
print(f"saved results/metrics_S8.json, {len(list(OUT.glob('*.csv')))} tables in results/S8, governance/register/S8.csv "
      f"({len(REG8)} rows); runtime {S8['runtime_seconds']:.0f} s ({C.NB_MODE})")
print(json.dumps(S8["verdicts"]))
