"""Fairness audit, 3x3 label matrix and mitigation arms (stage S8).

Everything here works on out-of-fold (OOF) predictions of the TRAINING part of the cohort
(the 20 % hold-out is never read) and on the stored CV folds of ``evalkit``.  No function
fits a model except the explicit CV helpers (:func:`cv_predict_reweighed`,
:func:`access_pipeline`), which refit inside every training fold exactly like
``evalkit.cv_predict``.

Contents
--------
Audit groups
    :func:`audit_groups` - race (NH Asian kept separate, exploratory), insurance (HIQ011),
    low access (uninsured OR no usual place of care, HUQ030), income band (PIR), sex.
    :data:`REFERENCE` gives the reference level of each attribute.
Bootstrap engine
    :func:`boot_engine` evaluates k prediction vectors on one weight vector per replicate:
    threshold at specificity ``config.SPEC_FIXED`` (0.80) on the negatives, then per group
    TPR, FPR, selection rate, PPV, ROC-AUC and observed-to-expected ratio, and the overall
    AUC.  Replicate weights come from :func:`stratified_counts` (simple bootstrap, rows
    resampled within group x label strata) or :func:`psu_counts` (Rao-Wu PSU-cluster bootstrap,
    ``survey.rao_wu_weights``).  The threshold is re-estimated in every replicate, so its
    uncertainty propagates into every group metric and gap.
Group metrics and gaps
    :func:`group_table` (point estimates + percentile CIs + small-cell status),
    :func:`eod_table` (equal-opportunity difference TPR_g - TPR_ref, 0.05 flag, 0.10
    "substantive" if the CI excludes 0), :func:`eod_permutation` (group-label permutation
    null of max |EOD|).
3x3 label matrix
    :func:`label_matrix` (recall at specificity 0.80 on the common non-diabetic negatives,
    AUC per cell) and :func:`h3_elements` (pre-registered ordering of hypothesis H3).
Mitigation
    :func:`reweighing_weights` (Kamiran & Calders 2012; partial once multiplied by survey weights), :func:`cv_predict_reweighed`,
    :func:`access_pipeline` (audit-only arm with insurance / usual-place features).

Small cells
-----------
A group is *suppressed* for verdicts when n < 30 or the number of positives (the TPR
denominator) is < 30 (``config.NCHS_MIN_N``), following the NCHS presentation standard
(Parker et al. 2017).  Suppressed estimates are still printed, but no gap verdict is drawn.
A TPR whose 95 % CI is 0.30 wide or more is labelled exploratory (``ci_width>=0.30``).

References
----------
Hardt, Price & Srebro (2016) arXiv:1610.02413 (equal opportunity);  Kamiran & Calders (2012)
Knowl. Inf. Syst. 33:1-33, doi:10.1007/s10115-011-0463-8 (reweighing);  Rao & Wu (1988) JASA
83:231-241 (rescaled bootstrap);  Parker et al. (2017) NCHS Vital Health Stat 2(175)
(presentation standards);  Efron & Tibshirani (1993) (percentile bootstrap);  Ojala & Garriga
(2010) JMLR 11:1833-1863 and Phipson & Smyth (2010) (permutation p-values).
"""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.pipeline import Pipeline

from . import config as C
from . import survey

__all__ = [
    "ATTRIBUTES", "REFERENCE", "LEVELS", "audit_groups", "encode", "stratified_counts", "psu_counts",
    "boot_engine", "summarise", "group_table", "eod_table", "eod_permutation", "label_matrix",
    "h3_elements", "reweighing_weights", "cv_predict_reweighed", "AccessFeatures", "access_pipeline",
    "cell_status",
]

# =============================================================================
# 1. Audit groups
# =============================================================================
ATTRIBUTES = ("race", "insurance", "low_access", "income", "sex")
REFERENCE = {"race": "NH White", "insurance": "insured", "low_access": "usual access",
             "income": "PIR >= 3.5", "sex": "Male"}
LEVELS = {
    "race": ("NH White", "NH Black", "NH Asian", "Mexican American", "Other Hispanic", "Other/Multi"),
    "insurance": ("insured", "uninsured"),
    "low_access": ("usual access", "low access"),
    "income": ("PIR >= 3.5", "PIR 1.3-3.49", "PIR < 1.3", "PIR missing"),
    "sex": ("Male", "Female"),
}
#: groups whose results are always exploratory (small, no oversampling in 2021-23)
EXPLORATORY = {("race", "NH Asian")}


def audit_groups(clean: pd.DataFrame) -> pd.DataFrame:
    """Audit / stratification attributes for every row of the per-variable cohort.

    * ``race``: labelled RIDRETH3 (NH Asian separate).
    * ``insurance``: HIQ011 1 = insured, 2 = uninsured; refused / don't know -> NaN.
    * ``low_access``: "low access" if uninsured OR no usual place of care (HUQ030 = 2);
      "usual access" if insured AND a usual place (HUQ030 = 1 or 3, "more than one place");
      NaN if neither condition can be decided.  Same coding as S5 (``uninsured``,
      ``no_usual_place``).
    * ``income``: family income-to-poverty ratio bands <1.3 / 1.3-3.49 / >=3.5 (NCHS bands; 1.3 is
      the SNAP eligibility line) and an explicit "PIR missing" group (12.8 % of the cohort).
    * ``sex``: Male / Female.

    These columns are audit variables only (S1 availability rule): they never enter the
    prediction model of arm S.
    """
    out = pd.DataFrame(index=clean.index)
    out["race"] = clean["race"].astype(object)
    ins = clean["HIQ011"]
    out["insurance"] = np.select([ins.eq(2), ins.eq(1)], ["uninsured", "insured"], None)
    unins = np.select([ins.eq(2), ins.eq(1)], [1.0, 0.0], np.nan)
    hu = clean["HUQ030"]
    noplace = np.select([hu.eq(2), hu.isin([1, 3])], [1.0, 0.0], np.nan)
    low = np.where((unins == 1) | (noplace == 1), "low access",
                   np.where((unins == 0) & (noplace == 0), "usual access", None))
    out["low_access"] = low
    pir = clean["INDFMPIR"]
    out["income"] = np.select([pir.isna(), pir < 1.3, pir < 3.5, pir >= 3.5],
                              ["PIR missing", "PIR < 1.3", "PIR 1.3-3.49", "PIR >= 3.5"], None)
    out["sex"] = clean["sex"].astype(object)
    out["uninsured"] = unins
    out["no_usual_place"] = noplace
    return out.replace({None: np.nan})


def encode(values, levels: Sequence[str]) -> np.ndarray:
    """Integer codes 0..G-1 in the order of ``levels``; -1 for missing / unknown levels."""
    s = pd.Series(np.asarray(values, dtype=object))
    m = {lv: i for i, lv in enumerate(levels)}
    return s.map(m).fillna(-1).astype(int).to_numpy()


def cell_status(n: int, n_pos: int) -> str:
    """'suppress' if n < 30 or positives < 30 (NCHS minimum sample size), else 'present'."""
    return "suppress" if (n < C.NCHS_MIN_N or n_pos < C.NCHS_MIN_N) else "present"


# =============================================================================
# 2. Bootstrap replicate weights
# =============================================================================
def stratified_counts(strata, n_boot: int, seed: int) -> np.ndarray:
    """Simple stratified bootstrap as count weights, shape (n_boot, n).

    Rows are resampled with replacement *within* each stratum (e.g. group x label), so the
    number of positives of every group is fixed across replicates (essential for groups with
    30-60 positives).  Count weights are equivalent to resampling rows.
    """
    strata = pd.Series(np.asarray(strata, dtype=object)).astype(str).to_numpy()
    n = len(strata)
    rng = np.random.default_rng(seed)
    flat = []
    rows = np.arange(n_boot)
    for s in np.unique(strata):
        mem = np.flatnonzero(strata == s)
        draws = mem[rng.integers(0, len(mem), (n_boot, len(mem)))]
        flat.append((rows[:, None] * n + draws).ravel())
    W = np.bincount(np.concatenate(flat), minlength=n_boot * n).reshape(n_boot, n)
    return W.astype(float)


def psu_counts(design: pd.DataFrame, n_boot: int, seed: int) -> np.ndarray:
    """Rao-Wu PSU-cluster bootstrap multipliers, shape (n_boot, n).

    ``survey.rao_wu_weights`` with unit base weights: in each stratum one of the two PSUs is
    drawn (m_h = n_h - 1) and its rows get multiplier 2, the other PSU 0.  The estimator stays
    unweighted (the protocol's primary metrics are unweighted); only the resampling respects the
    clustering of NHANES rows in PSUs, which widens intervals when outcomes cluster.
    """
    return survey.rao_wu_weights(design, np.ones(len(design)), n_boot, seed=seed).T


# =============================================================================
# 3. Bootstrap engine
# =============================================================================
class _ArmPrep:
    """Score-dependent quantities that do not change across replicates (sort orders, ranks)."""

    def __init__(self, y, p, codes, G, neg_mask, auc_neg):
        self.p = p
        neg = np.flatnonzero((y == 0) & neg_mask)
        self.neg_order = neg[np.argsort(p[neg], kind="mergesort")]
        self.neg_sorted = p[self.neg_order]
        pos_all = np.flatnonzero(y == 1)
        self.auc_parts = []
        for g in list(range(G)) + [None]:          # None = overall AUC
            pos = pos_all if g is None else pos_all[codes[pos_all] == g]
            if g is None or auc_neg == "all":
                ng = self.neg_order
            else:
                ng = self.neg_order[codes[self.neg_order] == g]
            ps = p[ng]
            left = np.searchsorted(ps, p[pos], "left")
            right = np.searchsorted(ps, p[pos], "right")
            self.auc_parts.append((pos, ng, left, right))

    def threshold(self, w, spec):
        cw = np.cumsum(w[self.neg_order])
        tot = cw[-1]
        if tot <= 0:
            return np.nan
        i = min(int(np.searchsorted(cw / tot, spec - 1e-12, "left")), len(cw) - 1)
        return self.neg_sorted[i]

    def aucs(self, w):
        out = []
        for pos, ng, left, right in self.auc_parts:
            wn = w[ng]
            cw = np.concatenate([[0.0], np.cumsum(wn)])
            wp = w[pos]
            den = wp.sum() * cw[-1]
            if den <= 0:
                out.append(np.nan)
                continue
            num = np.dot(wp, cw[left] + 0.5 * (cw[right] - cw[left]))
            out.append(num / den)
        return np.array(out)


def boot_engine(y, P, codes, G: int, W: np.ndarray | None = None, *, spec: float = C.SPEC_FIXED,
                neg_mask=None, auc_neg: str = "group") -> dict:
    """Evaluate k score vectors per replicate weight vector.

    Parameters
    ----------
    y : (n,) 0/1 outcome of the evaluation population.
    P : (k, n) or (n,) predicted probabilities (k arms, paired: same rows, same weights).
    codes : (n,) group code 0..G-1, -1 = unknown group (still used for the threshold).
    W : (B, n) replicate weights (counts or multipliers) or None (point estimate only, w = 1).
    spec : specificity defining the threshold on the negatives (``neg_mask`` restricts them).
    auc_neg : "group" - AUC_g compares group positives with group negatives; "all" - with all
        negatives (3x3 label matrix: each stratum against the common non-diabetic negatives).

    Rule (identical to ``evalkit.recall_at_specificity``): with v the weighted spec-quantile of
    the negative scores, a row is called positive when p > v.

    Returns a dict of arrays with leading shape (B,) (B = 1 if W is None):
    ``thr`` (B, k); ``tpr``, ``fpr``, ``sel``, ``ppv``, ``auc``, ``oe``, ``n``, ``n_pos`` (B, k, G);
    ``auc_all`` (B, k).  Undefined values (no positives / negatives in a replicate) are NaN.
    """
    y = np.asarray(y).astype(int)
    P = np.atleast_2d(np.asarray(P, dtype=float))
    codes = np.asarray(codes, dtype=int)
    n = len(y)
    k = P.shape[0]
    neg_mask = np.ones(n, bool) if neg_mask is None else np.asarray(neg_mask, bool)
    W = np.ones((1, n)) if W is None else np.atleast_2d(np.asarray(W, dtype=float))
    B = W.shape[0]
    preps = [_ArmPrep(y, P[a], codes, G, neg_mask, auc_neg) for a in range(k)]
    known = codes >= 0
    cidx = codes[known]
    out = {key: np.full((B, k, G), np.nan) for key in ("tpr", "fpr", "sel", "ppv", "auc", "oe", "n", "n_pos")}
    out["thr"] = np.full((B, k), np.nan)
    out["auc_all"] = np.full((B, k), np.nan)
    yk = y[known]

    def bc(weights):
        return np.bincount(cidx, weights=weights, minlength=G)

    with np.errstate(invalid="ignore", divide="ignore"):
        for b in range(B):
            w = W[b]
            wk = w[known]
            n_g = bc(wk)
            pos_g = bc(wk * yk)
            neg_g = bc(wk * (1 - yk))
            for a in range(k):
                v = preps[a].threshold(w, spec)
                hit = (P[a] > v).astype(float)[known]
                out["thr"][b, a] = v
                out["tpr"][b, a] = bc(wk * yk * hit) / pos_g
                out["fpr"][b, a] = bc(wk * (1 - yk) * hit) / neg_g
                sel_w = bc(wk * hit)
                out["sel"][b, a] = sel_w / n_g
                out["ppv"][b, a] = bc(wk * yk * hit) / sel_w
                out["oe"][b, a] = pos_g / bc(wk * P[a][known])
                au = preps[a].aucs(w)
                out["auc"][b, a] = au[:G]
                out["auc_all"][b, a] = au[G]
                out["n"][b, a] = n_g
                out["n_pos"][b, a] = pos_g
    return out


def summarise(point: np.ndarray, boot: np.ndarray, alpha: float = 0.05) -> tuple:
    """(estimate, ci_low, ci_high, se) from a point value and its bootstrap replicates (NaN-aware)."""
    b = np.asarray(boot, dtype=float)
    b = b[np.isfinite(b)]
    if len(b) < 10:
        return float(point), np.nan, np.nan, np.nan
    lo, hi = np.percentile(b, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(point), float(lo), float(hi), float(b.std(ddof=1))


# =============================================================================
# 4. Group tables, gaps, permutation null
# =============================================================================
METRICS = ("tpr", "fpr", "sel", "ppv", "auc", "oe")


def group_table(point: dict, boot: dict, levels: Sequence[str], *, arm: int = 0, attribute: str = "",
                exploratory=EXPLORATORY) -> pd.DataFrame:
    """One row per group: n, positives, metrics with percentile CIs, small-cell status and flags."""
    rows = []
    for g, lv in enumerate(levels):
        n, npos = int(point["n"][0, arm, g]), int(point["n_pos"][0, arm, g])
        r = {"attribute": attribute, "group": lv, "n": n, "n_pos": npos, "status": cell_status(n, npos)}
        for m in METRICS:
            e, lo, hi, _ = summarise(point[m][0, arm, g], boot[m][:, arm, g])
            r.update({m: e, f"{m}_lo": lo, f"{m}_hi": hi})
        flags = []
        if r["status"] == "suppress":
            flags.append("n<30" if n < C.NCHS_MIN_N else "n_pos<30")
        if np.isfinite(r["tpr_hi"]) and r["tpr_hi"] - r["tpr_lo"] >= C.NCHS_CI_WIDTH_MAX:
            flags.append("ci_width>=0.30")
        if (attribute, lv) in exploratory:
            flags.append("exploratory")
        r["flags"] = ";".join(flags)
        rows.append(r)
    return pd.DataFrame(rows)


def eod_table(point: dict, boot: dict, levels: Sequence[str], ref: str, *, arm: int = 0,
              attribute: str = "", flag: float = C.SESOI["group_tpr_gap"],
              substantive: float = C.SESOI["group_tpr_gap_substantive"]) -> pd.DataFrame:
    """Equal-opportunity difference EOD_g = TPR_g - TPR_ref with bootstrap CI (paired replicates).

    ``flag_0.05``: |EOD| >= 0.05 (SESOI); ``substantive``: |EOD| >= 0.10 AND the CI excludes 0.
    ``verdict_status`` is "suppressed" when the group or the reference has n < 30 or fewer
    than 30 positives: numbers are shown, no gap verdict is drawn.  FPR differences
    (the second equalised-odds component) are reported alongside.
    """
    r_ = list(levels).index(ref)
    rows = []
    for g, lv in enumerate(levels):
        if g == r_:
            continue
        d_pt = point["tpr"][0, arm, g] - point["tpr"][0, arm, r_]
        d_bt = boot["tpr"][:, arm, g] - boot["tpr"][:, arm, r_]
        e, lo, hi, se = summarise(d_pt, d_bt)
        f_pt = point["fpr"][0, arm, g] - point["fpr"][0, arm, r_]
        fe, flo, fhi, _ = summarise(f_pt, boot["fpr"][:, arm, g] - boot["fpr"][:, arm, r_])
        st = [cell_status(int(point["n"][0, arm, i]), int(point["n_pos"][0, arm, i])) for i in (g, r_)]
        suppressed = "suppress" in st
        excl0 = np.isfinite(lo) and (lo > 0 or hi < 0)
        rows.append({
            "attribute": attribute, "group": lv, "ref": ref, "eod": e, "eod_lo": lo, "eod_hi": hi, "eod_se": se,
            "fpr_diff": fe, "fpr_diff_lo": flo, "fpr_diff_hi": fhi,
            "flag_0.05": bool(abs(e) >= flag), "ci_excludes_0": bool(excl0),
            "substantive": bool(abs(e) >= substantive and excl0),
            "verdict_status": "suppressed" if suppressed else "reportable",
        })
    return pd.DataFrame(rows)


def eod_permutation(y, p, codes, G: int, ref: int, threshold: float, *, eligible: Sequence[int] | None = None,
                    n_perm: int = 200, seed: int = C.SEED_MASTER) -> dict:
    """Group-label permutation null of max_g |TPR_g - TPR_ref|.

    The group labels of rows with a known group are shuffled ``n_perm`` times (group sizes kept);
    the threshold is the overall one and is unaffected.  Under H0 (TPR does not depend on the
    group) the observed max |EOD| is exchangeable with the null values.  ``eligible`` = non-
    reference group codes entering the maximum (default: all; pass the non-suppressed ones).
    p = (1 + #{null >= observed}) / (1 + n_perm).
    """
    y = np.asarray(y).astype(int)
    hit = (np.asarray(p) >= threshold).astype(float)
    codes = np.asarray(codes, int)
    known = np.flatnonzero(codes >= 0)
    elig = [g for g in (range(G) if eligible is None else eligible) if g != ref]

    def stat(c):
        pos = y[known] == 1
        cc = c[pos]
        tp = np.bincount(cc, weights=hit[known][pos], minlength=G)
        npos = np.bincount(cc, minlength=G)
        tpr = tp / np.maximum(npos, 1)
        return float(np.max(np.abs(tpr[elig] - tpr[ref]))) if elig else np.nan

    obs = stat(codes[known])
    rng = np.random.default_rng(seed)
    null = np.array([stat(rng.permutation(codes[known])) for _ in range(n_perm)])
    n_ge = int((null >= obs - 1e-12).sum())
    return {"observed": obs, "null": null, "null_q95": float(np.quantile(null, 0.95)),
            "null_mean": float(null.mean()), "p_value": (n_ge + 1) / (n_perm + 1), "n_perm": int(n_perm)}


# =============================================================================
# 5. 3x3 label matrix
# =============================================================================
POS_STRATA = ("D_uncontrolled", "D_controlled", "Undiagnosed")
NEG_STRATUM = "NonDiabetic"


def label_matrix(stratum, P: dict, *, n_boot: int, seed: int, spec: float = C.SPEC_FIXED) -> dict:
    """Recall at specificity ``spec`` (on the common NonDiabetic negatives) per training label x stratum.

    ``P`` maps training-label name -> repeat-averaged OOF probability (same rows).  Every cell
    uses the threshold of its row (training label) fixed on the NonDiabetic negatives; recall is
    the share of the stratum's members above it; AUC compares the stratum with ALL NonDiabetic
    negatives.  The bootstrap resamples within each of the four strata (stratum sizes fixed) and
    re-estimates the thresholds, using the SAME replicates for every row so that differences
    between training labels are paired.

    Returns ``{"labels", "point", "boot", "recall", "auc", "recall_ci", "auc_ci"}``; ``recall`` and
    ``auc`` are DataFrames (rows = training labels, columns = strata); ``*_ci`` are long tables.
    """
    stratum = np.asarray(stratum, dtype=object).astype(str)
    labels_ = list(P)
    y = (stratum != NEG_STRATUM).astype(int)
    codes = encode(stratum, POS_STRATA)
    Pm = np.vstack([P[k] for k in labels_])
    point = boot_engine(y, Pm, codes, 3, None, spec=spec, auc_neg="all")
    W = stratified_counts(stratum, n_boot, seed)
    boot = boot_engine(y, Pm, codes, 3, W, spec=spec, auc_neg="all")
    rec = pd.DataFrame(point["tpr"][0], index=labels_, columns=POS_STRATA)
    auc = pd.DataFrame(point["auc"][0], index=labels_, columns=POS_STRATA)
    rows = []
    for a, lab in enumerate(labels_):
        for g, st in enumerate(POS_STRATA):
            r = {"train_label": lab, "stratum": st, "n_pos": int(point["n_pos"][0, a, g]),
                 "n_neg": int(((y == 0)).sum())}
            for m in ("tpr", "auc"):
                e, lo, hi, se = summarise(point[m][0, a, g], boot[m][:, a, g])
                r.update({m: e, f"{m}_lo": lo, f"{m}_hi": hi, f"{m}_se": se})
            rows.append(r)
    return {"labels": labels_, "point": point, "boot": boot, "recall": rec, "auc": auc,
            "cells": pd.DataFrame(rows).rename(columns={"tpr": "recall", "tpr_lo": "recall_lo",
                                                        "tpr_hi": "recall_hi", "tpr_se": "recall_se"})}


def _worst_gap(R: np.ndarray) -> np.ndarray:
    """R (..., labels, strata) -> worst-cell shortfall per label: max_c (max_r' R[r', c] - R[r, c])."""
    best = np.nanmax(R, axis=-2, keepdims=True)
    return np.nanmax(best - R, axis=-1)


def h3_elements(lm: dict, sesoi: float = C.SESOI["group_tpr_gap"]) -> pd.DataFrame:
    """Pre-registered ordering of H3 as paired bootstrap contrasts with ``evalkit.verdict``.

    Reading of the locked statement used here (column-wise: which TRAINING label serves a stratum
    worst, holding stratum and negatives fixed):

    * E1 "self-report misses most undiagnosed cases": recall(L_self) < recall(L_A1c) and
      recall(L_self) < recall(L_comb) in the Undiagnosed column.
    * E2 "HbA1c-only misses most controlled diagnosed cases": recall(L_A1c) < recall(L_self) and
      recall(L_A1c) < recall(L_comb) in the D_controlled column.
    * E3 "combined label has the smallest worst-cell gap": with gap_r = max over strata of the
      shortfall of row r against the best row in that column, gap(L_comb) < gap(L_self) and
      gap(L_comb) < gap(L_A1c).

    Each contrast gets ``verdict(ci_low, ci_high, sesoi=0.05, direction="-")``: equivalent if the
    CI lies within +/-0.05 ("differences below 0.05 are reported as equivalent").
    """
    from . import evalkit as ek

    labs = lm["labels"]
    i = {k: labs.index(k) for k in ("L_self", "L_A1c", "L_comb")}
    cidx = {s: POS_STRATA.index(s) for s in POS_STRATA}
    Rp, Rb = lm["point"]["tpr"][0], lm["boot"]["tpr"]
    gp, gb = _worst_gap(Rp), _worst_gap(Rb)
    spec_ = [
        ("E1", "Undiagnosed: L_self - L_A1c", Rp[i["L_self"], cidx["Undiagnosed"]] - Rp[i["L_A1c"], cidx["Undiagnosed"]],
         Rb[:, i["L_self"], cidx["Undiagnosed"]] - Rb[:, i["L_A1c"], cidx["Undiagnosed"]]),
        ("E1", "Undiagnosed: L_self - L_comb", Rp[i["L_self"], cidx["Undiagnosed"]] - Rp[i["L_comb"], cidx["Undiagnosed"]],
         Rb[:, i["L_self"], cidx["Undiagnosed"]] - Rb[:, i["L_comb"], cidx["Undiagnosed"]]),
        ("E2", "D_controlled: L_A1c - L_self", Rp[i["L_A1c"], cidx["D_controlled"]] - Rp[i["L_self"], cidx["D_controlled"]],
         Rb[:, i["L_A1c"], cidx["D_controlled"]] - Rb[:, i["L_self"], cidx["D_controlled"]]),
        ("E2", "D_controlled: L_A1c - L_comb", Rp[i["L_A1c"], cidx["D_controlled"]] - Rp[i["L_comb"], cidx["D_controlled"]],
         Rb[:, i["L_A1c"], cidx["D_controlled"]] - Rb[:, i["L_comb"], cidx["D_controlled"]]),
        ("E3", "worst-cell gap: L_comb - L_self", gp[i["L_comb"]] - gp[i["L_self"]], gb[:, i["L_comb"]] - gb[:, i["L_self"]]),
        ("E3", "worst-cell gap: L_comb - L_A1c", gp[i["L_comb"]] - gp[i["L_A1c"]], gb[:, i["L_comb"]] - gb[:, i["L_A1c"]]),
    ]
    rows = []
    for el, name, pt, bt in spec_:
        e, lo, hi, se = summarise(pt, bt)
        v = ek.verdict(lo, hi, sesoi, "-", e)
        rows.append({"element": el, "contrast": name, "est": e, "lo": lo, "hi": hi, "se": se,
                     "predicted": "< 0", "verdict": v, "reversed_ci_excl_0": bool(lo > 0)})
    return pd.DataFrame(rows)


# =============================================================================
# 6. Mitigation: reweighing
# =============================================================================
def reweighing_weights(groups, y) -> np.ndarray:
    """Kamiran & Calders (2012) reweighing: w(g, y) = P(g) P(y) / P(g, y), empirical shares.

    The shares are UNWEIGHTED counts, so these weights alone make group and label independent
    in the unweighted training data.  If they are multiplied by survey weights afterwards (as
    :func:`cv_predict_reweighed` does), independence holds only partly in the weighted data;
    a version computed from survey-weighted counts is checked in the S9 post-audit corrections.
    Unknown groups
    (NaN) form their own group, so no row is dropped.  Weights have mean 1 by construction.
    """
    g = pd.Series(np.asarray(groups, dtype=object)).fillna("__missing__").astype(str).to_numpy()
    y = np.asarray(y).astype(int)
    df = pd.DataFrame({"g": g, "y": y})
    pg = df["g"].map(df["g"].value_counts(normalize=True))
    py = df["y"].map(df["y"].value_counts(normalize=True))
    pgy = df.groupby(["g", "y"])["y"].transform("size") / len(df)
    return (pg * py / pgy).to_numpy(float)


def cv_predict_reweighed(make_pipe, X, y, folds, groups, *, base_weight=None, n_jobs: int = 1) -> pd.DataFrame:
    """``evalkit.cv_predict`` with reweighing weights computed INSIDE each training fold.

    sample_weight = base_weight (e.g. normalised WTPH2YR of arm S, P12) x w(g, y) from the fold's
    training rows, renormalised to mean 1; passed to the final estimator as ``model__sample_weight``.
    w(g, y) comes from unweighted counts, so the product with the survey weights makes group and
    label only PARTLY independent (a partial reweighing; see :func:`reweighing_weights`).
    Returns ``repeat, fold, row, prob`` like ``evalkit.cv_predict``.
    """
    from joblib import Parallel, delayed

    from . import evalkit as ek

    y = np.asarray(y)
    n = len(y)
    base = np.ones(n) if base_weight is None else np.asarray(base_weight, float)
    groups = np.asarray(groups, dtype=object)
    labels_ = ek._fold_repeats(folds, n)

    def one(rf, tr, te):
        w = base[tr] * reweighing_weights(groups[tr], y[tr])
        w = w / w.mean()
        model = clone(make_pipe())
        model.fit(ek._take(X, tr), y[tr], model__sample_weight=w)
        return pd.DataFrame({"repeat": rf[0], "fold": rf[1], "row": te, "prob": ek._positive_proba(model, ek._take(X, te))})

    parts = Parallel(n_jobs=n_jobs)(delayed(one)(rf, tr, te) for rf, (tr, te) in zip(labels_, folds))
    return pd.concat(parts, ignore_index=True).astype({"repeat": "int16", "fold": "int16", "row": "int64"})


# =============================================================================
# 7. Access-proxy audit arm
# =============================================================================
class AccessFeatures(BaseEstimator, TransformerMixin):
    """Audit-only step: binary ``uninsured`` (HIQ011 = 2) and ``no_usual_place`` (HUQ030 = 2) columns.

    Inserted after the sentinel step (refused / don't know already NaN), before the
    availability filter P03, which drops the raw HIQ011 / HUQ030 but keeps derived columns.
    Missing answers stay NaN and are median-imputed by the base imputer like every column.
    """

    def fit(self, X, y=None):
        self.feature_names_out_ = list(self.transform(X.iloc[:3]).columns)
        return self

    def transform(self, X):
        out = X.copy()
        hi, hu = out["HIQ011"], out["HUQ030"]
        out["uninsured"] = np.select([hi.eq(2), hi.eq(1)], [1.0, 0.0], np.nan)
        out["no_usual_place"] = np.select([hu.eq(2), hu.isin([1, 3])], [1.0, 0.0], np.nan)
        return out

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_out_, dtype=object)


ACCESS_FEATURES = ("uninsured", "no_usual_place")


def access_pipeline(cfg: dict, tier: int = 1, *, C_: float = 1.0) -> Pipeline:
    """Arm-S pipeline plus the two access-to-care features (audit arm, never a model for use).

    Identical to ``prep.build_pipeline(cfg, tier, C_=C_)`` except that :class:`AccessFeatures`
    runs right after the sentinel step P02.
    """
    from . import prep as P

    steps = P.preprocessor_steps(cfg, tier)
    pos = [nm for nm, _ in steps].index("p02") + 1
    steps.insert(pos, ("access", AccessFeatures()))
    return Pipeline(steps + [("model", P.make_model(cfg, "lr", C_))])
