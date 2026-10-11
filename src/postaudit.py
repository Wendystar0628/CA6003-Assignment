"""Post-audit checks (POST-LOCK) for the six methodological issues of the external review (§9.12).

Every function here is a *transparent post-lock analysis*: it re-uses the project's own functions
(``prep``, ``evalkit``, ``fairness``, ``robustness``) read-only, never changes a locked verdict, the
primary pipeline or a stored result of §3-§9, and never fits or scores a hold-out row. Only
``holdout_design_check`` reads hold-out *membership* (the SEQN list in ``results/splits/holdout.json``),
and only to count how many hold-out rows entered the §4 diagnostics.

One function per issue:

1. ``holdout_design_check``  - §4 linearity / interaction tests, VIF and skewness on the training part
   only, compared with the stored full-cohort results; hold-out overlap of the §4 samples.
2. ``nested_c``              - C chosen inside each outer fold (first repeat of the stored folds).
3. ``ratio_outer_bootstrap`` - outer patient bootstrap of the B3-b and H2b(c) BMI SD ratios (a sampling
   interval, unlike the Monte Carlo interval of §7.11).
4. ``weighted_reweighing``   - Kamiran-Calders weights from survey-weighted counts (WTPH2YR), so group and
   label are exactly independent in the fitted weighting; EOD and AUC as in §8.8.
5. ``converged_m1_coefs``    - coefficient bootstrap of M1 at the exact optimum (newton-cholesky) and of
   M1 + scaling (P09), on the stored §7.11 resamples.
6. ``m1c_arm``               - M1c = M1 + P02 (codebook sentinel recode, correct training label) on the
   stored folds, paired with S and M1 by the §7 comparison engine.

Sizes follow the run mode (``SIZES``) and are deliberately small: these are *approximate* post-lock
checks (FINAL about 3-5 minutes on 28 cores, FAST under a minute), not re-runs of the protocol.
"""
from __future__ import annotations

import json
import time
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from . import config as C
from . import evalkit as ek
from . import fairness as F
from . import nhanes_io as io
from . import prep as P
from . import robustness as RB

SEED_TAG = "postaudit"
#: run-mode sizes (approximate post-lock checks, kept light): outer / inner bootstrap of the SD ratios,
#: coefficient-bootstrap B (every refit's solver iterations are counted), and the number of outer folds used for nested C (the first repeat of the stored folds)
SIZES = {
    "FINAL": dict(outer=30, inner=100, coef_b=200, nested_folds=5),
    "FAST": dict(outer=5, inner=15, coef_b=30, nested_folds=5),
}
C_GRID = RB.C_GRID                       # the a-priori grid of §7.3: 0.01, 0.1, 1, 10
LIN_VARS = {"RIDAGEYR": "age", "BMXBMI": "BMI", "BMXWAIST": "waist", "bp_sys_mean": "SBP (mean)",
            "LBDHDD": "HDL", "LBXTC": "total cholesterol", "INDFMPIR": "PIR"}
#: variables splined by P13 (DR-S4-10): age and BMI in Tier 1, plus HDL and TC in Tier 2
SPLINED = ("RIDAGEYR", "BMXBMI", "LBDHDD", "LBXTC")
VIF_SETS = {"raw_anthropometry": ["BMXWT", "BMXHT", "BMXBMI", "BMXWAIST", "BMXHIP", "BMXARMC"],
            "bp_readings": ["BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3"],
            "bp_means": ["bp_sys_mean", "bp_dia_mean"]}
SKEW_VARS = ("BMXBMI", "bp_sys_mean", "LBDHDD", "BMXWAIST", "LBXTC")


def sizes() -> dict:
    """Sizes of the current run mode."""
    return SIZES[C.NB_MODE]


def seed(*tags) -> int:
    """Seed derived from SEED_MASTER and the post-audit tag."""
    return ek.derive_seed(C.SEED_MASTER, SEED_TAG, *tags)


def n_jobs_default() -> int:
    import os
    if os.environ.get("POSTAUDIT_NJOBS"):          # e.g. to leave cores free while other sections run
        return max(1, int(os.environ["POSTAUDIT_NJOBS"]))
    return max(1, min(24, (os.cpu_count() or 2) - 4))


def _stored_oof(arm: str, tier: int = 1, model: str = "lr") -> pd.DataFrame:
    """Stored §7 out-of-fold predictions of one arm on the folds of this run mode (FAST = first repeats)."""
    oof = pd.read_parquet(C.RESULTS_DIR / "oof_predictions.parquet", columns=["arm", "tier", "model", "repeat", "fold", "row", "prob"])
    g = oof[(oof["arm"] == arm) & (oof["tier"] == tier) & (oof["model"] == model) & (oof["repeat"] < C.CV_REPEATS)]
    return g[["repeat", "fold", "row", "prob"]].astype({"prob": float}).reset_index(drop=True)


def _cv_parallel(make_pipe, X, y, folds, fit_params=None, n_jobs=1) -> pd.DataFrame:
    """``evalkit.cv_predict`` parallelised over folds (identical fits, identical output frame)."""
    n = len(y)
    y = np.asarray(y)

    def one(rf, tr, te):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = clone(make_pipe())
            m.fit(ek._take(X, tr), y[tr], **ek._slice_fit_params(fit_params, tr, n))
        return pd.DataFrame({"repeat": rf[0], "fold": rf[1], "row": te, "prob": ek._positive_proba(m, ek._take(X, te))})

    parts = Parallel(n_jobs=n_jobs)(delayed(one)(rf, tr, te) for rf, (tr, te) in zip(ek._fold_repeats(folds, n), folds))
    return pd.concat(parts, ignore_index=True).astype({"repeat": "int16", "fold": "int16", "row": "int64"})


def _cmp(ctx, oof_a, oof_b, pop, seed_):
    """Paired ΔAUC A - B with the §7 engine (``robustness.compare``): E-ALL wider of corrected t and
    paired bootstrap, E-SCREEN paired bootstrap only."""
    if pop == "E-ALL":
        return RB.compare(oof_a, oof_b, ctx.y, ctx.folds, use_t=True, seed_=seed_)
    return RB.compare(oof_a, oof_b, ctx.y_esc, ctx.folds, mask=ctx.esc, use_t=False, seed_=seed_)


def _s7_seed(a, b, pop):
    """Bootstrap seed of the §7 comparison engine for the pair (a, b), Tier 1, ROC-AUC."""
    return ek.derive_seed(C.SEED_MASTER, "S7", a, b, 1, "roc_auc", pop)


def _ci(r, k=4):
    return f"{r['est']:+.{k}f} [{r['lo']:+.{k}f}, {r['hi']:+.{k}f}]"


# =============================================================================
# 1. Hold-out design check (issue 1)
# =============================================================================
def _rcs_basis(x, q=(0.05, 0.35, 0.65, 0.95)):
    """Harrell restricted cubic spline basis, identical to §4.11 (``03_eda.py``)."""
    x = np.asarray(x, float)
    t = np.quantile(x, q)
    k = len(t)
    p3 = lambda u: np.maximum(u, 0) ** 3  # noqa: E731
    nl = [(p3(x - t[j]) - p3(x - t[k - 2]) * (t[k - 1] - t[j]) / (t[k - 1] - t[k - 2])
           + p3(x - t[k - 1]) * (t[k - 2] - t[j]) / (t[k - 1] - t[k - 2])) / (t[k - 1] - t[0]) ** 2 for j in range(k - 2)]
    return np.column_stack([x] + nl), t


def _linearity(d: pd.DataFrame) -> pd.DataFrame:
    """§4.11 likelihood-ratio tests (4-knot RCS vs linear, others linear, sex adjusted, complete cases)."""
    import statsmodels.api as sm
    lin = d.dropna(subset=list(LIN_VARS)).reset_index(drop=True)
    lin["female"] = (lin["sex"] == "Female").astype(float)
    y = lin["L_comb"].to_numpy(float)
    fit = lambda X: sm.Logit(y, sm.add_constant(X)).fit(disp=0)  # noqa: E731
    rows = []
    for v in LIN_VARS:
        others = lin[[o for o in LIN_VARS if o != v] + ["female"]].to_numpy(float)
        b, _ = _rcs_basis(lin[v])
        chi2 = 2 * (fit(np.column_stack([b, others])).llf - fit(np.column_stack([b[:, :1], others])).llf)
        rows.append(dict(variable=v, n=len(lin), n_events=int(y.sum()), chi2=chi2, p=stats.chi2.sf(chi2, 2)))
    return pd.DataFrame(rows)


def _interactions(d: pd.DataFrame) -> pd.DataFrame:
    """§4.12 interaction tests: specs A (primary), B (minimal) and C (splines) x 4 terms."""
    import statsmodels.formula.api as smf
    ren = {"RIDAGEYR": "age", "BMXBMI": "bmi", "BMXWAIST": "waist", "bp_sys_mean": "sbp", "LBDHDD": "hdl", "LBXTC": "tc", "INDFMPIR": "pir"}
    lin = d.dropna(subset=list(LIN_VARS)).reset_index(drop=True)
    lin["female"] = (lin["sex"] == "Female").astype(float)
    inter = lin.rename(columns=ren).copy()
    inter["race6"] = pd.Categorical(inter["race"].astype(str), categories=list(io.RACE_ORDER))
    inter["asian"] = (inter["race"] == "NH Asian").astype(float)
    for v in ("age", "bmi"):
        Bv, _ = _rcs_basis(inter[v])
        inter[f"{v}_s1"], inter[f"{v}_s2"] = Bv[:, 1], Bv[:, 2]
    bm = d.dropna(subset=["BMXBMI"]).rename(columns={"RIDAGEYR": "age", "BMXBMI": "bmi"}).copy()
    bm["female"] = (bm["sex"] == "Female").astype(float)
    bm["race6"] = pd.Categorical(bm["race"].astype(str), categories=list(io.RACE_ORDER))
    bm["asian"] = (bm["race"] == "NH Asian").astype(float)
    specs = {"A_primary": (inter, "age + female + race6 + bmi + waist + sbp + hdl + tc + pir"),
             "B_minimal": (bm, "age + female + race6 + bmi"),
             "C_splines": (inter, "age + age_s1 + age_s2 + bmi + bmi_s1 + bmi_s2 + female + race6")}
    terms = {"race_x_bmi": "race6:bmi", "asian_x_bmi": "asian:bmi", "age_x_bmi": "age:bmi", "sex_x_bmi": "female:bmi"}
    rows = []
    for s, (dd, base) in specs.items():
        m0 = smf.logit(f"L_comb ~ {base}", dd).fit(disp=0)
        for t, e in terms.items():
            m1 = smf.logit(f"L_comb ~ {base} + {e}", dd).fit(disp=0)
            chi = 2 * (m1.llf - m0.llf)
            rows.append(dict(term=t, spec=s, n=len(dd), p=stats.chi2.sf(chi, int(m1.df_model - m0.df_model))))
    return pd.DataFrame(rows)


def _vif(d: pd.DataFrame) -> pd.DataFrame:
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    rows = []
    for s, cols in VIF_SETS.items():
        x = d[cols].dropna()
        X = sm.add_constant(x.to_numpy(float))
        rows += [dict(set=s, variable=c, vif=variance_inflation_factor(X, i + 1), n=len(x)) for i, c in enumerate(cols)]
    return pd.DataFrame(rows)


def holdout_design_check(ctx) -> dict:
    """Issue 1. The §4 design diagnostics ran on all 5,730 adults, before the split existed.

    Counts the hold-out rows (and positives) inside the §4 samples, then re-runs the §4 linearity and
    interaction tests, the VIF and the skewness on the **training part only** and compares each decision
    with the stored full-cohort result (``results/S4``). Hold-out rows are only counted, never modelled.
    """
    t0 = time.time()
    coh = ctx.clean
    in_ho = np.zeros(len(coh), bool)
    in_ho[ctx.test_idx] = True
    y = coh["L_comb"].to_numpy(int)
    lin_mask = coh[list(LIN_VARS)].notna().all(axis=1).to_numpy()
    overlap = pd.DataFrame([
        dict(sample="cohort (labels, binned age)", n=len(coh), n_holdout=int(in_ho.sum()), holdout_pos=int(y[in_ho].sum())),
        dict(sample="§4.11 linearity / §4.12 interactions A, C (complete cases, 7 predictors)", n=int(lin_mask.sum()),
             n_holdout=int((lin_mask & in_ho).sum()), holdout_pos=int(y[lin_mask & in_ho].sum())),
        dict(sample="§4.12 interaction spec B (BMI present)", n=int(coh["BMXBMI"].notna().sum()),
             n_holdout=int((coh["BMXBMI"].notna().to_numpy() & in_ho).sum()), holdout_pos=int(y[coh["BMXBMI"].notna().to_numpy() & in_ho].sum())),
    ])
    overlap["holdout_share"] = overlap["n_holdout"] / overlap["n"]
    # --- training part only (ctx.cl = the 4,584 training rows of the same cohort)
    tr = ctx.cl
    lin_full = pd.read_csv(C.RESULTS_DIR / "S4" / "linearity_tests.csv").set_index("variable")
    lin_tr = _linearity(tr).set_index("variable")
    lin_tab = pd.DataFrame({"chi2_full": lin_full["chi2"], "p_full": lin_full["p"], "chi2_train": lin_tr["chi2"], "p_train": lin_tr["p"]})
    lin_tab["nonlinear_full"] = lin_tab["p_full"] < 0.05
    lin_tab["nonlinear_train"] = lin_tab["p_train"] < 0.05
    lin_tab["same_class"] = lin_tab["nonlinear_full"] == lin_tab["nonlinear_train"]
    lin_tab["splined_P13"] = lin_tab.index.isin(SPLINED)
    lin_tab = lin_tab.reset_index()
    int_full = pd.read_csv(C.RESULTS_DIR / "S4" / "interaction_tests.csv")
    int_tr = _interactions(tr)
    int_tab = int_full[["term", "spec", "p"]].rename(columns={"p": "p_full"}).merge(int_tr[["term", "spec", "p"]].rename(columns={"p": "p_train"}), on=["term", "spec"])
    int_tab["same_class"] = (int_tab["p_full"] < 0.05) == (int_tab["p_train"] < 0.05)
    vif_full = pd.read_csv(C.RESULTS_DIR / "S4" / "vif_table.csv")
    vif_tab = vif_full[["set", "variable", "vif"]].rename(columns={"vif": "vif_full"}).merge(
        _vif(tr)[["set", "variable", "vif"]].rename(columns={"vif": "vif_train"}), on=["set", "variable"])
    vif_tab["same_class_gt10"] = (vif_tab["vif_full"] > 10) == (vif_tab["vif_train"] > 10)
    sk_full = pd.read_csv(C.RESULTS_DIR / "S4" / "skew_table.csv")
    sk_full = sk_full[sk_full["subsample"] == "cohort"].set_index("variable")["skew_raw"]
    skew_tab = pd.DataFrame([dict(variable=v, skew_full=float(sk_full[v]), skew_train=float(stats.skew(tr[v].dropna()))) for v in SKEW_VARS])
    # decision invariance: every splined variable stays non-linear; no unsplined variable crosses into a new
    # class that the design used (waist and SBP are not splined either way); interactions: count of same
    # classifications; VIF: the >10 class of weight and BMI (in-fold pruning, DR-S4-08) unchanged
    spl = lin_tab[lin_tab["splined_P13"]]
    out = dict(
        overlap=overlap, linearity=lin_tab, interactions=int_tab, vif=vif_tab, skew=skew_tab,
        n_holdout=int(in_ho.sum()), cohort_holdout_pos=int(y[in_ho].sum()),
        lin_sample_n=int(lin_mask.sum()), lin_sample_holdout=int((lin_mask & in_ho).sum()),
        lin_sample_holdout_pos=int(y[lin_mask & in_ho].sum()),
        splined_still_nonlinear=bool(spl["nonlinear_train"].all()),
        nl_same_class=int(lin_tab["same_class"].sum()), nl_n=len(lin_tab),
        nl_changed=lin_tab.loc[~lin_tab["same_class"], "variable"].tolist(),
        interactions_same_class=int(int_tab["same_class"].sum()), interactions_n=len(int_tab),
        interactions_changed=[f"{r.spec} {r.term} (p {r.p_full:.3f} -> {r.p_train:.3f})" for r in int_tab[~int_tab["same_class"]].itertuples()],
        vif_same_class=int(vif_tab["same_class_gt10"].sum()), vif_n=len(vif_tab),
        vif_weight_bmi_train=[float(vif_tab.query("set == 'raw_anthropometry' and variable == @v")["vif_train"].iloc[0]) for v in ("BMXWT", "BMXBMI")],
        max_abs_skew_change=float((skew_tab["skew_full"] - skew_tab["skew_train"]).abs().max()),
    )
    # a design decision changes only if a splined variable loses its non-linearity, or a detected interaction
    # that the design acted on appears (none was acted on: DR-S4-11 adds no interaction term)
    out["decision_changed"] = (not out["splined_still_nonlinear"]) or (out["vif_same_class"] < out["vif_n"])
    out["seconds"] = time.time() - t0
    return out


# =============================================================================
# 2. Nested C (issue 2)
# =============================================================================
def _inner_score(cfg, X1, ylab, w_all, trn, a, b, c):
    """Inner-fold ROC-AUC (survey-weighted for S) of one C on a design prepared on the outer-training rows.

    Mirror of the §7.3 choice inside one outer fold: the preparation is fitted on the outer-training rows once
    (as §7.3 fitted it on the whole training part), then each inner fold refits only the logistic model."""
    warnings.simplefilter("ignore")
    Xtr, ytr = X1.iloc[trn], ylab[trn]
    wtr = None if w_all is None else w_all[trn]
    design = P.build_pipeline(cfg, 1)[:-1].fit_transform(Xtr)
    m = P.make_model(cfg, "lr", c)
    m.fit(design.iloc[a], ytr[a], sample_weight=None if wtr is None else wtr[a])
    return float(roc_auc_score(ytr[b], m.predict_proba(design.iloc[b])[:, 1], sample_weight=None if wtr is None else wtr[b]))


def _refit_score(cfg, X1, ylab, w_all, trn, tst, c):
    warnings.simplefilter("ignore")
    wtr = None if w_all is None else w_all[trn]
    pipe = P.build_pipeline(cfg, 1, C_=c)
    pipe.fit(X1.iloc[trn], ylab[trn], **({} if wtr is None else {"model__sample_weight": wtr}))
    return pipe.predict_proba(X1.iloc[tst])[:, 1]


def nested_c(ctx, *, n_jobs: int | None = None, n_folds: int | None = None) -> dict:
    """Issue 2. C0 = 0.1 was chosen once on all training rows (§7.3), not inside the outer folds.

    Approximate nested check on the first repeat of the stored folds (5 outer folds): inside every outer fold
    C is chosen from the same a-priori grid by inner 5-fold ROC-AUC on the outer-training rows only (the
    §7.3 procedure moved inside the fold), the arm is refitted with that C and the outer-test rows are scored.
    S and M1 are compared with the stored fixed-C0 predictions on the same folds."""
    t0 = time.time()
    n_jobs = n_jobs or n_jobs_default()
    n_folds = n_folds or sizes()["nested_folds"]
    X1, n = ctx.X[1], ctx.n
    folds = ek.Folds(list(ctx.folds)[:n_folds])
    folds.n_splits = ctx.folds.n_splits
    rep_fold = ek._fold_repeats(ctx.folds, n)[:n_folds]
    ARM = {}
    for arm in ("S", "M1"):
        cfg = P.ARMS[arm]
        ARM[arm] = (cfg, P.training_label(ctx.raw_tr, cfg).astype(int), P.survey_weights(ctx.raw_tr) if cfg.get("P12") else None)
    jobs = []
    for arm, (cfg, ylab, w_all) in ARM.items():
        for k, (trn, _) in enumerate(folds):
            inner = StratifiedKFold(5, shuffle=True, random_state=seed("nested", arm, k))
            for i, (a, b) in enumerate(inner.split(np.zeros(len(trn)), ylab[trn])):
                for c in C_GRID:
                    jobs.append(((arm, k, i, c), (cfg, X1, ylab, w_all, trn, a, b, c)))
    # slow M1 fits (iteration limit) first
    jobs.sort(key=lambda j: j[0][0] != "M1")
    sc = dict(zip([k for k, _ in jobs], Parallel(n_jobs=n_jobs)(delayed(_inner_score)(*a) for _, a in jobs)))
    cst = {(arm, k): float(C_GRID[int(np.argmax([np.mean([sc[(arm, k, i, c)] for i in range(5)]) for c in C_GRID]))])
           for arm in ARM for k in range(len(folds))}
    inner_auc = {f"{arm}|{k}": {str(c): round(float(np.mean([sc[(arm, k, i, c)] for i in range(5)])), 5) for c in C_GRID}
                 for arm in ARM for k in range(len(folds))}
    ref_jobs = [((arm, k), (ARM[arm][0], X1, ARM[arm][1], ARM[arm][2], trn, tst, cst[(arm, k)]))
                for arm in ARM for k, (trn, tst) in enumerate(folds)]
    probs = dict(zip([k for k, _ in ref_jobs], Parallel(n_jobs=n_jobs)(delayed(_refit_score)(*a) for _, a in ref_jobs)))
    nested, stored, max_dev = {}, {}, {}
    for arm in ARM:
        parts, devs = [], []
        st = _stored_oof(arm)
        st = st[st["repeat"] == 0]
        for k, (trn, tst) in enumerate(folds):
            rr, ff = rep_fold[k]
            parts.append(pd.DataFrame({"repeat": rr, "fold": ff, "row": tst, "prob": probs[(arm, k)]}))
            if cst[(arm, k)] == ctx.C0:   # same C as stored -> the refit must reproduce the stored predictions
                b_ = st[(st["fold"] == ff)].set_index("row")["prob"].reindex(tst).to_numpy()
                devs.append(float(np.abs(probs[(arm, k)] - b_).max()))
        nested[arm] = pd.concat(parts, ignore_index=True)
        stored[arm] = st.reset_index(drop=True)
        max_dev[arm] = max(devs) if devs else None
    pooled = lambda oof: float(roc_auc_score(ctx.y, ek.mean_oof(oof, n)))  # noqa: E731

    def _d(oa, ob, tag):
        return RB.compare(oa, ob, ctx.y, folds, use_t=True, seed_=seed("nested", "dauc", tag))

    d_st, d_ne = _d(stored["S"], stored["M1"], "stored"), _d(nested["S"], nested["M1"], "nested")
    tab = pd.DataFrame([
        dict(estimate=f"stored, C0 = {ctx.C0:g} for all folds", S_auc=pooled(stored["S"]), M1_auc=pooled(stored["M1"]),
             S_folds_C0=f"{len(folds)}/{len(folds)}", M1_folds_C0=f"{len(folds)}/{len(folds)}",
             dauc=d_st["est"], dauc_lo=d_st["lo"], dauc_hi=d_st["hi"], interval=d_st["interval"], h2b_rule=d_st["h2b"]),
        dict(estimate="nested: C chosen inside each outer fold", S_auc=pooled(nested["S"]), M1_auc=pooled(nested["M1"]),
             S_folds_C0=f"{sum(cst[('S', k)] == ctx.C0 for k in range(len(folds)))}/{len(folds)}",
             M1_folds_C0=f"{sum(cst[('M1', k)] == ctx.C0 for k in range(len(folds)))}/{len(folds)}",
             dauc=d_ne["est"], dauc_lo=d_ne["lo"], dauc_hi=d_ne["hi"], interval=d_ne["interval"], h2b_rule=d_ne["h2b"]),
    ])
    return dict(table=tab, n_folds=len(folds), folds_used=f"repeat 0 of the stored folds ({len(folds)} outer folds)",
                cstar={arm: [cst[(arm, k)] for k in range(len(folds))] for arm in ARM}, inner_auc=inner_auc,
                max_dev_when_C0=max_dev,
                S_auc_stored=float(tab.loc[0, "S_auc"]), S_auc_nested=float(tab.loc[1, "S_auc"]),
                S_auc_change=float(tab.loc[1, "S_auc"] - tab.loc[0, "S_auc"]),
                M1_auc_stored=float(tab.loc[0, "M1_auc"]), M1_auc_nested=float(tab.loc[1, "M1_auc"]),
                S_folds_C0=int(sum(cst[("S", k)] == ctx.C0 for k in range(len(folds)))),
                M1_folds_C0=int(sum(cst[("M1", k)] == ctx.C0 for k in range(len(folds)))),
                dauc_stored=dict(est=d_st["est"], lo=d_st["lo"], hi=d_st["hi"], verdict=d_st["h2b"]),
                dauc_nested=dict(est=d_ne["est"], lo=d_ne["lo"], hi=d_ne["hi"], verdict=d_ne["h2b"]),
                seconds=time.time() - t0)


# =============================================================================
# 3. Outer patient bootstrap of the SD ratios (issue 3)
# =============================================================================
#: M1 enters at its exact optimum (newton-cholesky): the stored lbfgs fit stops at the iteration limit (issue 5)
#: and 30 x 100 such fits would take far longer than the rest of the post-audit together
RATIO_ARMS = {"S-linear": ("S-linear", {}), "S-linear-B3": ("S-linear-B3", {}),
              "M1 newton-cholesky": ("M1", {"model__solver": "newton-cholesky"})}


def _bmi_coef_chunk(cfg, params, C0, Xb, yb, fpb, idx_rows):
    """BMI coefficient of the final estimator for each inner resample in ``idx_rows`` (raw design units)."""
    warnings.simplefilter("ignore")
    n = len(yb)
    out = []
    for idx in idx_rows:
        pipe = P.build_pipeline(cfg, 1, C_=C0).set_params(**params)
        pipe.fit(Xb.iloc[idx], yb[idx], **ek._slice_fit_params(fpb, idx, n))
        names = [str(s) for s in pipe[:-1].get_feature_names_out()]
        out.append(float(pipe[-1].coef_.ravel()[names.index("BMXBMI")]) if "BMXBMI" in names else np.nan)
    return out


def ratio_outer_bootstrap(ctx, *, n_outer: int | None = None, n_inner: int | None = None, n_jobs: int | None = None,
                          chunk: int = 25) -> dict:
    """Issue 3. The §7.11 ratio interval re-draws the stored bootstrap replicates (Monte Carlo error only).

    Outer bootstrap over patients: draw the training part with replacement ``n_outer`` times; in each outer
    sample run the §7.11 coefficient bootstrap (``n_inner`` refits) for S-linear, S-linear-B3 and M1 at its
    exact optimum; the spread of the ratios across outer samples is an approximate sampling interval (it also
    holds some Monte Carlo noise from the inner B, estimated and reported)."""
    t0 = time.time()
    sz = sizes()
    n_outer, n_inner = n_outer or sz["outer"], n_inner or sz["inner"]
    n_jobs = n_jobs or n_jobs_default()
    X1, raw_tr, n = ctx.X[1], ctx.raw_tr, ctx.n
    tasks, meta = [], {}
    for k in range(n_outer):
        rng = np.random.default_rng(seed("outer", k))
        idx_o = rng.integers(0, n, n)
        Xb = X1.iloc[idx_o].reset_index(drop=True)
        rawb = raw_tr.iloc[idx_o].reset_index(drop=True)
        inner = rng.integers(0, n, (n_inner, n))
        for name, (arm, params) in RATIO_ARMS.items():
            cfg = P.ARMS[arm]
            yb = P.training_label(rawb, cfg).astype(int)
            fpb = P.fit_params(cfg, rawb)
            # per-SD scale of BMI in the prepared design of this outer sample (as in §7.11)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sd_bmi = float(P.build_pipeline(cfg, 1, C_=ctx.C0)[:-1].fit_transform(Xb)["BMXBMI"].std(ddof=0))
            meta[(k, name)] = sd_bmi
            for s in range(0, n_inner, chunk):
                tasks.append(((k, name), (cfg, params, ctx.C0, Xb, yb, fpb, inner[s:s + chunk])))
    res = Parallel(n_jobs=n_jobs)(delayed(_bmi_coef_chunk)(*a) for _, a in tasks)
    coefs: dict = {}
    for (key, _), r in zip(tasks, res):
        coefs.setdefault(key, []).extend(r)
    sd = {key: float(np.nanstd(np.asarray(v) * meta[key], ddof=1)) for key, v in coefs.items()}
    per = pd.DataFrame([dict(outer=k, **{f"sd_{nm}": sd[(k, nm)] for nm in RATIO_ARMS}) for k in range(n_outer)])
    per["ratio_B3"] = per["sd_S-linear-B3"] / per["sd_S-linear"]
    per["ratio_H2b_c_converged"] = per["sd_M1 newton-cholesky"] / per["sd_S-linear"]
    cs7 = json.loads((C.RESULTS_DIR / "metrics_S7.json").read_text(encoding="utf-8"))["coef_stability"]
    stored = {"ratio_B3": cs7["ratio_B3"], "ratio_H2b_c_converged": None}
    summ, rows = {}, []
    thr = C.SESOI["coef_sd_ratio"]
    for col, label in (("ratio_B3", "B3-b: S-linear-B3 / S-linear"),
                       ("ratio_H2b_c_converged", "H2b(c): M1 at exact optimum / S-linear")):
        r = per[col].to_numpy()
        q025, q50, q975 = np.percentile(r, [2.5, 50, 97.5])
        sd_out = float(r.std(ddof=1))
        # Monte Carlo SD of a ratio of two SDs estimated from n_inner draws each: ratio * sqrt(1 / (n_inner - 1))
        sd_mc = float(np.mean(r) * np.sqrt(1.0 / (n_inner - 1)))
        sd_samp = float(np.sqrt(max(sd_out ** 2 - sd_mc ** 2, 0.0)))
        st = stored[col]
        point = st["ratio"] if st else float(np.median(r))
        d = dict(comparison=label, point=point, mc_lo=st["lo"] if st else np.nan, mc_hi=st["hi"] if st else np.nan,
                 outer_q025=q025, outer_median=q50, outer_q975=q975, sd_outer=sd_out, sd_mc_inner=sd_mc, sd_sampling=sd_samp,
                 p_below_2=float((r < thr).mean()), p_le_1=float((r <= 1).mean()),
                 interval_contains_1=bool(q025 <= 1 <= q975), interval_contains_2=bool(q025 <= thr <= q975))
        summ[col] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in d.items()}
        rows.append(d)
    return dict(table=pd.DataFrame(rows), per_outer=per, n_outer=n_outer, n_inner=n_inner, seconds=time.time() - t0, **summ)


# =============================================================================
# 4. Weighted reweighing (issue 4)
# =============================================================================
def reweighing_weights_weighted(groups, y, w) -> np.ndarray:
    """Kamiran-Calders weights from survey-WEIGHTED shares: w(g, y) = P_w(g) P_w(y) / P_w(g, y).

    Multiplied by the survey weights w, group and label are exactly independent in the fitted weighting.
    Unknown groups (NaN) form their own group, as in ``fairness.reweighing_weights``."""
    g = pd.Series(np.asarray(groups, dtype=object)).fillna("__missing__").astype(str).to_numpy()
    d = pd.DataFrame({"g": g, "y": np.asarray(y).astype(int), "w": np.asarray(w, float)})
    W = d["w"].sum()
    pg = d.groupby("g")["w"].transform("sum") / W
    py = d.groupby("y")["w"].transform("sum") / W
    pgy = d.groupby(["g", "y"])["w"].transform("sum") / W
    return (pg * py / pgy).to_numpy(float)


def _rates(g, y, w, levels) -> dict:
    """Weighted positive rate (%) per named group."""
    out = {}
    for lv in levels:
        m = g == lv
        out[lv] = 100 * float(np.average(y[m], weights=w[m])) if m.any() and w[m].sum() > 0 else np.nan
    return out


def weighted_reweighing(ctx, *, n_jobs: int | None = None) -> dict:
    """Issue 4. §8.8 multiplied unweighted-count reweighing weights by the survey weights.

    (a) group positive rates in the training rows of fold 0 under four weightings, and the spread across all
    folds; (b) the corrected arm (survey x weighted-count weights) refitted on the stored folds for race,
    insurance and low access, with EOD and ΔAUC exactly as in §8.8, next to the as-run arm (re-run here and
    asserted against the stored §8 numbers in FINAL)."""
    t0 = time.time()
    n_jobs = n_jobs or n_jobs_default()
    X1, y, n = ctx.X[1], ctx.y.astype(int), ctx.n
    grp = F.audit_groups(ctx.cl)
    w_svy = P.survey_weights(ctx.raw_tr)
    cfgS = P.ARMS["S"]
    C0 = ctx.C0
    mk_S = lambda: P.build_pipeline(cfgS, 1, C_=C0)  # noqa: E731
    # --- (a) independence of group and label in the fitted weighting
    rate_rows, spread_rows = [], []
    for attr in ("race", "insurance", "low_access"):
        gv = grp[attr].to_numpy(dtype=object)
        lv = F.LEVELS[attr]
        spreads = {"survey only": [], "as fitted (unweighted-count RW x survey)": [], "corrected (weighted-count RW x survey)": []}
        for k, (trn, _) in enumerate(ctx.folds):
            gt, yt, ws = gv[trn], y[trn], w_svy[trn]
            asf = ws * F.reweighing_weights(gt, yt)
            cor = ws * reweighing_weights_weighted(gt, yt, ws)
            W = {"none": np.ones(len(trn)), "survey only": ws, "as fitted (unweighted-count RW x survey)": asf,
                 "corrected (weighted-count RW x survey)": cor}
            for nm, ww in W.items():
                rt = _rates(gt, yt, ww, lv)
                if nm in spreads:
                    vals = [v for v in rt.values() if np.isfinite(v)]
                    spreads[nm].append(max(vals) - min(vals))
                if k == 0:
                    rate_rows += [dict(attribute=attr, weighting=nm, group=g_, pos_rate_pct=v) for g_, v in rt.items()]
        for nm, s in spreads.items():
            spread_rows.append(dict(attribute=attr, weighting=nm, spread_pp_mean=float(np.mean(s)), spread_pp_max=float(np.max(s))))
    rates = pd.DataFrame(rate_rows)
    spread = pd.DataFrame(spread_rows)
    # --- (b) refit: as-run and corrected arms
    oofS = _stored_oof("S")
    pS = ek.mean_oof(oofS, n)
    s8 = json.loads((C.RESULTS_DIR / "metrics_S8.json").read_text(encoding="utf-8"))["reweighing"]
    s8_eod = pd.DataFrame(s8["eod"]).set_index(["attribute", "group"])
    eod_rows, auc_rows, max_dev_asrun = [], [], 0.0
    for attr in ("race", "insurance", "low_access"):
        gv = grp[attr].to_numpy(dtype=object)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            oof_run = F.cv_predict_reweighed(mk_S, X1, y, ctx.folds, gv, base_weight=w_svy, n_jobs=n_jobs)

            def one(rf, trn, tst):
                warnings.simplefilter("ignore")
                ww = w_svy[trn] * reweighing_weights_weighted(gv[trn], y[trn], w_svy[trn])
                m = clone(mk_S())
                m.fit(ek._take(X1, trn), y[trn], model__sample_weight=ww / ww.mean())
                return pd.DataFrame({"repeat": rf[0], "fold": rf[1], "row": tst, "prob": ek._positive_proba(m, ek._take(X1, tst))})

            parts = Parallel(n_jobs=n_jobs)(delayed(one)(rf, a, b) for rf, (a, b) in zip(ek._fold_repeats(ctx.folds, n), ctx.folds))
        oof_fix = pd.concat(parts, ignore_index=True)
        p_run, p_fix = ek.mean_oof(oof_run, n), ek.mean_oof(oof_fix, n)
        for nm, oo in (("as run (§8.8)", oof_run), ("corrected (weighted counts)", oof_fix)):
            for pop in ("E-ALL", "E-SCREEN"):
                r = _cmp(ctx, oo, oofS, pop, ek.derive_seed(C.SEED_MASTER, "S8", "dauc", f"rw_{attr}" + ("" if nm.startswith("as") else "_weighted"), pop))
                auc_rows.append(dict(attribute=attr, arm=nm, pop=pop, auc_arm=r["auc_a"], auc_S=r["auc_b"], dauc=r["est"], lo=r["lo"], hi=r["hi"],
                                     interval=r["interval"], verdict_auc=ek.verdict(r["lo"], r["hi"], C.SESOI["roc_auc"], "+", r["est"])))
        # EOD at the shared specificity-0.80 threshold, paired label-stratified bootstrap with the §8 seed
        lv = F.LEVELS[attr]
        codes = F.encode(grp[attr], lv)
        Pm = np.vstack([pS, p_run, p_fix])
        point = F.boot_engine(y, Pm, codes, len(lv))
        W = F.stratified_counts(np.char.add(codes.astype(str), np.char.add("|", y.astype(str))), C.N_BOOT,
                                ek.derive_seed(C.SEED_MASTER, "S8", attr, "E-ALL", 1, "simple"))
        boot = F.boot_engine(y, Pm, codes, len(lv), W)
        ref = lv.index(F.REFERENCE[attr])
        for gi, gname in enumerate(lv):
            if gi == ref:
                continue
            ept = point["tpr"][0, :, gi] - point["tpr"][0, :, ref]
            ebt = boot["tpr"][:, :, gi] - boot["tpr"][:, :, ref]
            e_s, slo, shi, _ = F.summarise(ept[0], ebt[:, 0])
            d_run = F.summarise(ept[1] - ept[0], ebt[:, 1] - ebt[:, 0])
            d_fix = F.summarise(ept[2] - ept[0], ebt[:, 2] - ebt[:, 0])
            d_fr = F.summarise(ept[2] - ept[1], ebt[:, 2] - ebt[:, 1])
            if (attr, gname) in s8_eod.index:
                max_dev_asrun = max(max_dev_asrun, abs(float(s8_eod.loc[(attr, gname), "eod_RW"]) - float(ept[1])))
            eod_rows.append(dict(attribute=attr, group=gname, target=gname == {"race": "NH Asian", "insurance": "uninsured", "low_access": "low access"}[attr],
                                 eod_S=float(ept[0]), eod_asrun=float(ept[1]), eod_corrected=float(ept[2]),
                                 d_eod_asrun=d_run[0], d_eod_asrun_lo=d_run[1], d_eod_asrun_hi=d_run[2],
                                 d_eod_corrected=d_fix[0], d_eod_corrected_lo=d_fix[1], d_eod_corrected_hi=d_fix[2],
                                 corrected_minus_asrun=d_fr[0], corrected_minus_asrun_lo=d_fr[1], corrected_minus_asrun_hi=d_fr[2]))
    eod = pd.DataFrame(eod_rows)
    auc = pd.DataFrame(auc_rows)
    e_ = eod.set_index(["attribute", "group"])
    sp = spread.set_index(["attribute", "weighting"])
    return dict(rates_fold0=rates, spread=spread, eod=eod, auc=auc, max_dev_asrun_vs_stored=float(max_dev_asrun),
                race_spread_pp=dict(survey=float(sp.loc[("race", "survey only"), "spread_pp_mean"]),
                                    as_fitted=float(sp.loc[("race", "as fitted (unweighted-count RW x survey)"), "spread_pp_mean"]),
                                    corrected=float(sp.loc[("race", "corrected (weighted-count RW x survey)"), "spread_pp_max"])),
                eod_nh_black=dict(asrun=float(e_.loc[("race", "NH Black"), "eod_asrun"]), corrected=float(e_.loc[("race", "NH Black"), "eod_corrected"])),
                eod_nh_asian=dict(asrun=float(e_.loc[("race", "NH Asian"), "eod_asrun"]), corrected=float(e_.loc[("race", "NH Asian"), "eod_corrected"])),
                d_eod_nh_black_corrected=dict(est=float(e_.loc[("race", "NH Black"), "d_eod_corrected"]), lo=float(e_.loc[("race", "NH Black"), "d_eod_corrected_lo"]),
                                              hi=float(e_.loc[("race", "NH Black"), "d_eod_corrected_hi"])),
                max_abs_dauc_corrected=float(auc.loc[auc["arm"].str.startswith("corrected"), "dauc"].abs().max()),
                seconds=time.time() - t0)


# =============================================================================
# 5. Converged M1 coefficient bootstrap (issue 5)
# =============================================================================
def _m1_variant(name):
    cfg = dict(P.ARMS["M1"])
    params = {}
    if name == "M1 exact optimum (newton-cholesky)":
        params = {"model__solver": "newton-cholesky"}
    elif name == "M1 + scaling only (P09)":
        cfg["P09"] = True
    return cfg, params


ANTHRO = ("BMXBMI", "BMXWT", "BMXHT", "BMXWAIST")


def _coef_iter_chunk(cfg, params, C0, X, y, idx_rows):
    """Anthropometric coefficients and solver iterations of one refit per resample in ``idx_rows``."""
    warnings.simplefilter("ignore")
    out = []
    for idx in idx_rows:
        pipe = P.build_pipeline(cfg, 1, C_=C0).set_params(**params)
        pipe.fit(X.iloc[idx], y[idx])
        names = [str(s) for s in pipe[:-1].get_feature_names_out()]
        co = pipe[-1].coef_.ravel()
        out.append(({c: float(co[names.index(c)]) for c in ANTHRO if c in names}, int(np.max(pipe[-1].n_iter_))))
    return out


def converged_m1_coefs(ctx, *, n_boot: int | None = None, n_jobs: int | None = None, chunk: int = 10) -> dict:
    """Issue 5. The §7.11 M1 bootstrap stops at the iteration limit in almost every refit.

    Re-runs the M1 coefficient bootstrap on the first ``n_boot`` resamples of §7.11 (same seed, so the same
    patients) for three variants: M1 as fitted (lbfgs, iteration limit), M1 at the exact optimum
    (newton-cholesky) and M1 + scaling only (P09). Every refit's solver iterations are counted. Ratios are
    taken against the stored S-linear BMI SD of §7.11 (descriptive, no verdict)."""
    t0 = time.time()
    n_boot = n_boot or sizes()["coef_b"]
    n_jobs = n_jobs or n_jobs_default()
    X1, n = ctx.X[1], ctx.n
    ylab = P.training_label(ctx.raw_tr, P.ARMS["M1"]).astype(int)
    seed_m1 = ek.derive_seed(C.SEED_MASTER, "S7", "coef", "M1")
    # the first n_boot rows of the §7.11 resampling matrix (the generator fills it row by row)
    idx_all = np.random.default_rng(seed_m1).integers(0, n, (n_boot, n))
    cs7 = json.loads((C.RESULTS_DIR / "metrics_S7.json").read_text(encoding="utf-8"))["coef_stability"]
    sd_sl = float(cs7["table"]["S-linear"]["bmi_sd_per_sd"])
    st_m1 = cs7["table"]["M1"]
    variants = ("M1 stored (lbfgs, max_iter 5,000)", "M1 exact optimum (newton-cholesky)", "M1 + scaling only (P09)")
    tasks = [(v, s) for v in variants for s in range(0, n_boot, chunk)]
    # slow chunks (lbfgs at the iteration limit) first, so the pool stays balanced
    tasks.sort(key=lambda t: not t[0].startswith("M1 stored"))
    res = Parallel(n_jobs=n_jobs)(delayed(_coef_iter_chunk)(*_m1_variant(v), ctx.C0, X1, ylab, idx_all[s:s + chunk]) for v, s in tasks)
    got = {v: [] for v in variants}
    for (v, s), r in sorted(zip(tasks, res), key=lambda t: (t[0][0], t[0][1])):
        got[v].extend(r)
    rows, conv = [], {}
    for v in variants:
        cfg, params = _m1_variant(v)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            full = P.build_pipeline(cfg, 1, C_=ctx.C0).set_params(**params).fit(X1, ylab)
            sd_bmi = float(P.build_pipeline(cfg, 1, C_=ctx.C0)[:-1].fit_transform(X1)["BMXBMI"].std(ddof=0))
        names = [str(s) for s in full[:-1].get_feature_names_out()]
        fco = {c: float(full[-1].coef_.ravel()[names.index(c)]) for c in ANTHRO if c in names}
        mat = pd.DataFrame([g[0] for g in got[v]])
        its = np.array([g[1] for g in got[v]])
        x = mat["BMXBMI"].to_numpy() * sd_bmi
        flips = {c: float(np.mean(np.sign(mat[c].to_numpy()) != np.sign(fco[c]))) for c in mat.columns}
        conv[v] = dict(n_checked=int(len(its)), at_limit=int((its >= C.LR_MAX_ITER).sum()), max_iter_seen=int(its.max()),
                       median_iter=float(np.median(its)), full_fit_iter=int(np.max(full[-1].n_iter_)))
        rows.append(dict(variant=v, bmi_coef_per_sd=fco["BMXBMI"] * sd_bmi, bmi_sd_per_sd=float(np.std(x, ddof=1)),
                         q_low=float(np.percentile(x, 2.5)), q_high=float(np.percentile(x, 97.5)), sign_flip=flips["BMXBMI"],
                         max_flip_anthro=max(flips.values()), n_boot=int(len(x)), at_limit=f"{conv[v]['at_limit']}/{conv[v]['n_checked']}"))
    tab = pd.DataFrame(rows)
    tab["ratio_to_S_linear"] = tab["bmi_sd_per_sd"] / sd_sl
    t_ = tab.set_index("variant")
    st_, cv_, sc_ = variants
    return dict(table=tab, convergence=conv, sd_S_linear=sd_sl, n_boot=n_boot,
                stored_7_11=dict(bmi_sd_per_sd=float(st_m1["bmi_sd_per_sd"]), n_boot=int(st_m1["n_valid"]), ratio=float(cs7["ratio_H2b"]["ratio"])),
                sd_stored=float(t_.loc[st_, "bmi_sd_per_sd"]), sd_converged=float(t_.loc[cv_, "bmi_sd_per_sd"]), sd_scaled=float(t_.loc[sc_, "bmi_sd_per_sd"]),
                ratio_stored=float(t_.loc[st_, "ratio_to_S_linear"]), ratio_converged=float(t_.loc[cv_, "ratio_to_S_linear"]),
                ratio_scaled=float(t_.loc[sc_, "ratio_to_S_linear"]),
                flip_stored=float(t_.loc[st_, "sign_flip"]), flip_converged=float(t_.loc[cv_, "sign_flip"]),
                share_at_limit_stored=conv[st_]["at_limit"] / conv[st_]["n_checked"],
                full_coef_reproduced=bool(abs(t_.loc[st_, "bmi_coef_per_sd"] - float(st_m1["bmi_coef_per_sd"])) < 1e-4),
                seconds=time.time() - t0)


# =============================================================================
# 6. M1c = M1 + P02 (issue 6)
# =============================================================================
def m1c_arm(ctx, *, n_jobs: int | None = None) -> dict:
    """Issue 6. M1 keeps the blanket 7/9/77/99 recode (P02 off) in its features and training label.

    M1c switches the codebook (per-variable) recode on; it is refitted on the stored folds and paired with
    the stored S and M1 predictions with the §7 engine and §7 seeds. Evaluation labels are the frozen ones."""
    t0 = time.time()
    n_jobs = n_jobs or n_jobs_default()
    cfg = P.make_cfg(["P03", "P02"])
    y_naive = P.training_label(ctx.raw_tr, P.ARMS["M1"]).astype(int)
    y_good = P.training_label(ctx.raw_tr, cfg).astype(int)
    assert (y_good == ctx.y).all(), "M1c must train on the frozen L_comb"
    oof_c = _cv_parallel(lambda: P.build_pipeline(cfg, 1, C_=ctx.C0), ctx.X[1], y_good, ctx.folds, P.fit_params(cfg, ctx.raw_tr), n_jobs)
    oof = {"S": _stored_oof("S"), "M1": _stored_oof("M1"), "M1c": oof_c}
    rows = []
    for a, b in (("S", "M1"), ("S", "M1c"), ("M1c", "M1")):
        for pop in ("E-ALL", "E-SCREEN"):
            r = _cmp(ctx, oof[a], oof[b], pop, _s7_seed(a, b, pop))
            rows.append(dict(comparison=f"{a} - {b}", pop=pop, auc_a=r["auc_a"], auc_b=r["auc_b"], est=r["est"], lo=r["lo"], hi=r["hi"],
                             interval=r["interval"], mdd=r["mdd"], h2b_rule=r["h2b"]))
    tab = pd.DataFrame(rows)
    t_ = tab.set_index(["comparison", "pop"])
    pick = lambda c, p: {k: float(t_.loc[(c, p), k]) for k in ("est", "lo", "hi")} | {"verdict": t_.loc[(c, p), "h2b_rule"]}  # noqa: E731
    return dict(table=tab, label_flips_train=int((y_good != y_naive).sum()),
                auc_M1c_eall=float(t_.loc[("S - M1c", "E-ALL"), "auc_b"]), auc_M1c_escreen=float(t_.loc[("S - M1c", "E-SCREEN"), "auc_b"]),
                S_minus_M1=pick("S - M1", "E-ALL"), S_minus_M1c_eall=pick("S - M1c", "E-ALL"), S_minus_M1c_escreen=pick("S - M1c", "E-SCREEN"),
                M1c_minus_M1_eall=pick("M1c - M1", "E-ALL"), M1c_minus_M1_escreen=pick("M1c - M1", "E-SCREEN"),
                seconds=time.time() - t0)


# =============================================================================
# helpers for storage
# =============================================================================
def jsonable(obj):
    """Convert the nested results (DataFrames, numpy scalars) into JSON-serialisable objects."""
    if isinstance(obj, pd.DataFrame):
        return [jsonable(r) for r in obj.to_dict("records")]
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else round(float(obj), 6)
    if isinstance(obj, np.ndarray):
        return [jsonable(v) for v in obj.tolist()]
    return obj
