"""Robustness and credibility checks (stage S9).

Everything in this module operates on the TRAINING part of the cohort (the 80 % left after
``evalkit.make_holdout``) except the explicitly named hold-out helpers at the end, which are
only called after the ``exp-freeze`` tag exists (docs/development_process.md S9 step 6).

Public API
----------
Context and specifications
    load_context(C0=None) -> Context
        raw / labelled cohort, hold-out indices, training part, raw feature frames per tier,
        labels (L_comb, SL1-SL5, E-SCREEN), stored folds of the current run mode, frozen C0.
    Spec(arm, tier, model, C, depth, impute, weighted, label, extra, rows, ipw)
        one cross-validated run: a prep.ARMS configuration plus the S9 variations.
    make_pipe(spec, C0) -> sklearn Pipeline (prep.build_pipeline + overrides)
    spec_inputs(ctx, spec) -> (X, y_train, sample_weight, row_mask)

Folds
    seed_folds(strat, seed, n_splits, n_repeats) -> evalkit.Folds   (in memory, not persisted)
    group_folds(strat, groups, seed, n_splits, n_repeats) -> Folds  (StratifiedGroupKFold)
    subset_folds(folds, mask) -> Folds                               (restrict to rows, keep pairing)

Running and comparing
    run_many(ctx, specs, folds, n_jobs, cache) -> {name: OOF frame}
    compare(oof_a, oof_b, y, folds, mask=None, w=None, use_t=True, seed, n_boot) -> dict
        S7 comparison engine: fold-level Nadeau-Bengio corrected t and paired, label-stratified
        bootstrap on the repeat-averaged OOF vector; the wider interval is used (E-ALL);
        bootstrap only for E-SCREEN (use_t=False).  Optional design / IPW weights ``w``.
    equivalence_verdict(lo, hi, sesoi) -> locked H2b(a) rule (supported = equivalent)
    auc_ci(y, p, mask, seed, n_boot) -> (auc, lo, hi)

Negative / positive controls
    permutation_null(ctx, spec, folds, n_perm, seed, n_jobs) -> evalkit.permutation_auc dict
    signal_feature(y, auc, seed) -> synthetic N(d*y, 1) column with population AUC ``auc``
    tree_features_used(ctx, spec, folds, C0, feature) -> per-fold root / usage of a column

Leak hunt (L3)
    single_feature_scan(frame, y, folds, cat_cols, mask) -> AUC per variable (OOF target
        encoding for categorical variables, oriented AUC = max(AUC, 1 - AUC))
    missing_indicator_scan(frame, y, mask) -> AUC of every ``is_missing`` indicator
    contribution_importance(pipe, X) -> SD of each base variable's linear-predictor share
    base_variable(column) -> spec variable a design column comes from
    availability_proof(variables, tier) -> table with source, instrument, spec reason, PASS/FAIL

Missing HbA1c (MNAR) sensitivity
    examined_population() -> examined, non-pregnant adults incl. those without HbA1c
    missingness_design(df) -> the S3 missingness-model design (same covariates)
    observation_model(ex) -> statsmodels Logit of "HbA1c observed"
    delta_prevalence(...) / delta_auc(...) -> delta-adjusted (pattern-mixture) estimates

Hold-out (after exp-freeze only)
    tag_exists(name), head_commit(), holdout_frames(ctx), fit_full(ctx, spec, C0),
    holdout_scores(y, p, thr, mask, seed, n_boot)

All randomness comes from ``evalkit.derive_seed(config.SEED_MASTER, "S9", ...)``.
"""
from __future__ import annotations

import functools
import hashlib
import json
import subprocess
import warnings
from dataclasses import dataclass, field, replace
from typing import Callable

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.experimental import enable_iterative_imputer  # noqa: F401 - activates IterativeImputer
from sklearn.impute import IterativeImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedGroupKFold

from . import config as C
from . import evalkit as ek
from . import labels as L
from . import nhanes_io as io
from . import prep as P

__all__ = [
    "Context", "load_context", "Spec", "make_pipe", "spec_inputs", "seed_folds", "group_folds",
    "subset_folds", "run_many", "compare", "equivalence_verdict", "auc_ci", "permutation_null",
    "signal_feature", "tree_features_used", "single_feature_scan", "missing_indicator_scan",
    "contribution_importance", "base_variable", "availability_proof", "examined_population",
    "missingness_design", "observation_model", "delta_prevalence", "delta_auc", "tag_exists",
    "head_commit", "holdout_frames", "fit_full", "holdout_scores", "IterativeImpute",
]

ADMISSIBLE_ARMS = ("M1", "S")
C_GRID = (0.01, 0.1, 1.0, 10.0)
PERM_NULL_BAND = (0.495, 0.505)
L3_T1_EALL_AUC = 0.90
L3_SINGLE_FEATURE_AUC = 0.75
AGE_EXEMPT = ("RIDAGEYR",)
POS_CONTROL_AUC = 0.60
SEED_TAG = "S9"


def seed(*tags) -> int:
    """Seed derived from SEED_MASTER and the S9 tag (``evalkit.derive_seed``)."""
    return ek.derive_seed(C.SEED_MASTER, SEED_TAG, *tags)


# =============================================================================
# context
# =============================================================================
@dataclass
class Context:
    """Everything a S9 analysis needs about the training part (hold-out kept aside)."""
    raw: pd.DataFrame
    clean: pd.DataFrame
    train_idx: np.ndarray
    test_idx: np.ndarray
    raw_tr: pd.DataFrame
    cl: pd.DataFrame
    X: dict
    labels: pd.DataFrame
    strat: np.ndarray
    folds: ek.Folds
    C0: float
    extras: pd.DataFrame = field(default_factory=pd.DataFrame)
    subsets: dict = field(default_factory=dict)
    ipw: np.ndarray | None = None

    @property
    def n(self) -> int:
        return len(self.cl)

    @property
    def y(self) -> np.ndarray:
        return self.labels["L_comb"].to_numpy()

    @property
    def esc(self) -> np.ndarray:
        return self.labels["in_escreen"].to_numpy(bool)

    @property
    def y_esc(self) -> np.ndarray:
        return self.labels["y_escreen"].to_numpy()


def load_context(C0: float | None = None) -> Context:
    """Training part, labels and stored folds exactly as S7 used them (asserted)."""
    raw = P.raw_cohort()
    clean = L.add_labels(io.build_cohort())
    assert (raw["SEQN"].to_numpy() == clean["SEQN"].to_numpy()).all()
    tr, te = ek.make_holdout(clean)
    raw_tr = raw.iloc[tr].reset_index(drop=True)
    cl = clean.iloc[tr].reset_index(drop=True)
    X = {t: P.raw_feature_frame(raw_tr, t) for t in (1, 2)}
    sl = L.sensitivity_labels(cl)
    labels = pd.DataFrame({
        "L_comb": cl["L_comb"].astype(int), "L_self": cl["L_self"].astype(int), "L_A1c": cl["L_A1c"].astype(int),
        **{c: sl[c] for c in L.SL_COLS},
        "in_escreen": cl["in_escreen"].astype(int), "y_escreen": cl["y_escreen"].fillna(0).astype(int),
    })
    strat = cl["stratum_3x3"].astype(str).to_numpy()
    folds = ek.make_folds(labels["L_comb"].to_numpy(), strat)
    if C0 is None:
        C0 = float(json.loads((C.RESULTS_DIR / "metrics_S7.json").read_text(encoding="utf-8"))["C0"]["C0"])
    return Context(raw=raw, clean=clean, train_idx=tr, test_idx=te, raw_tr=raw_tr, cl=cl, X=X, labels=labels,
                   strat=strat, folds=folds, C0=float(C0), extras=pd.DataFrame(index=cl.index))


# =============================================================================
# specifications and pipelines
# =============================================================================
@dataclass(frozen=True)
class Spec:
    """One cross-validated run.

    ``arm``      key of ``prep.ARMS`` (M0, M1, S, T1-minus-care, ...)
    ``tier``     1 or 2
    ``model``    "lr" or "tree"; ``depth`` overrides the tree depth (default config.TREE_MAX_DEPTH)
    ``C``        inverse L2 strength (None = frozen C0)
    ``impute``   "median" (shared base imputer) or "iterative" (IterativeImputer, numeric columns)
    ``weighted`` None = the arm's own P12 setting; True / False forces survey-weighted / unweighted fit
    ``label``    "arm" = prep.training_label of the arm (P02 decides the naive label); otherwise a
                 column of ``Context.labels`` (L_comb, SL1-SL5) used by every arm
    ``extra``    names of ``Context.extras`` columns appended to the raw frame (noise, signal, race)
    ``rows``     name of a ``Context.subsets`` row mask (complete cases, fasting subsample)
    ``ipw``      multiply the fit weights by ``Context.ipw`` (inverse probability of HbA1c observed)
    """
    arm: str = "S"
    tier: int = 1
    model: str = "lr"
    C: float | None = None
    depth: int | None = None
    impute: str = "median"
    weighted: bool | None = None
    label: str = "arm"
    extra: tuple = ()
    rows: str | None = None
    ipw: bool = False

    def cfg(self) -> dict:
        cfg = dict(P.ARMS[self.arm])
        if self.weighted is not None:
            cfg["P12"] = bool(self.weighted)
        return cfg


class IterativeImpute(P.Impute):
    """Sensitivity alternative to the median imputer: ``IterativeImputer`` (BayesianRidge chained
    equations, deterministic posterior mean) on numeric columns, most-frequent for categorical ones.
    Fitted in-fold on X only, like the base imputer it replaces."""

    def __init__(self, max_iter: int = 10, random_state: int = C.SEED_MASTER):
        self.max_iter = max_iter
        self.random_state = random_state

    def fit(self, X, y=None):
        super().fit(X)
        self.num_ = [c for c in X.columns if c not in self.cat_ and pd.api.types.is_numeric_dtype(X[c])]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.it_ = IterativeImputer(max_iter=self.max_iter, random_state=self.random_state,
                                        keep_empty_features=True).fit(X[self.num_].to_numpy(float))
        return self._finish_fit(X)

    def transform(self, X):
        out = X.fillna({c: v for c, v in self.fill_.items() if c in self.cat_ and c in X.columns})
        if self.num_:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                out[self.num_] = self.it_.transform(X[self.num_].to_numpy(float))
        return out


def make_pipe(spec: Spec, C0: float):
    """``prep.build_pipeline`` for the spec's configuration with the S9 overrides applied."""
    pipe = P.build_pipeline(spec.cfg(), spec.tier, spec.model, C_=spec.C if spec.C is not None else C0,
                            seed=C.SEED_MASTER)
    if spec.model == "tree" and spec.depth is not None:
        pipe.set_params(model__max_depth=int(spec.depth))
    if spec.impute == "iterative":
        pipe.set_params(impute=IterativeImpute())
    elif spec.impute != "median":
        raise ValueError(spec.impute)
    return pipe


def spec_inputs(ctx: Context, spec: Spec):
    """(X, training label, fit sample weights or None, row mask) for a spec on the training part."""
    X = ctx.X[spec.tier]
    if spec.extra:
        X = pd.concat([X, ctx.extras[list(spec.extra)]], axis=1)
    cfg = spec.cfg()
    if spec.label == "arm":
        y = P.training_label(ctx.raw_tr, cfg)
    else:
        y = ctx.labels[spec.label].to_numpy(dtype=float)
    sw = P.survey_weights(ctx.raw_tr) if cfg.get("P12") else None
    if spec.ipw:
        assert ctx.ipw is not None, "Context.ipw not set"
        sw = (np.ones(ctx.n) if sw is None else sw) * ctx.ipw
        sw = sw / sw.mean()
    mask = np.ones(ctx.n, bool) if spec.rows is None else np.asarray(ctx.subsets[spec.rows], bool)
    mask = mask & ~np.isnan(np.asarray(y, dtype=float))
    return X, np.asarray(y, dtype=float), sw, mask


# =============================================================================
# folds
# =============================================================================
def _as_folds(fold_id: np.ndarray, n_splits: int, seed_: int) -> ek.Folds:
    folds = ek.Folds(ek._folds_from_ids(fold_id, n_splits))
    folds.n_splits, folds.n_repeats, folds.n, folds.seed = n_splits, fold_id.shape[0], fold_id.shape[1], int(seed_)
    folds.hash, folds.path = ek._folds_hash(fold_id, n_splits, fold_id.shape[0], int(seed_)), None
    folds.fold_id = fold_id
    return folds


def fold_id_matrix(folds) -> np.ndarray:
    """(n_repeats x n) fold-assignment matrix of a Folds list."""
    if getattr(folds, "fold_id", None) is not None:
        return folds.fold_id
    fid = np.full((folds.n_repeats, folds.n), -1, dtype=np.int16)
    for i, (_, te) in enumerate(folds):
        fid[i // folds.n_splits, te] = i % folds.n_splits
    return fid


def seed_folds(strat, seed_: int, n_splits: int = C.CV_SPLITS, n_repeats: int = C.CV_REPEATS) -> ek.Folds:
    """Repeated stratified K-fold with another integer seed (robustness seeds; not persisted).

    Same construction as ``evalkit.make_folds`` (rare strata merged), only the seed differs."""
    codes = ek._collapse_rare(pd.Series(strat).astype(str), n_splits).to_numpy()
    n = len(codes)
    rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=int(seed_))
    fid = np.full((n_repeats, n), -1, dtype=np.int16)
    for i, (_, te) in enumerate(rskf.split(np.zeros(n), codes)):
        fid[i // n_splits, te] = i % n_splits
    assert (fid >= 0).all()
    return _as_folds(fid, n_splits, seed_)


def group_folds(strat, groups, seed_: int, n_splits: int = C.CV_SPLITS, n_repeats: int = C.CV_REPEATS) -> ek.Folds:
    """Repeated ``StratifiedGroupKFold``: whole survey clusters (strata x PSU) stay in one fold."""
    codes = ek._collapse_rare(pd.Series(strat).astype(str), n_splits).to_numpy()
    groups = np.asarray(groups)
    n = len(codes)
    fid = np.full((n_repeats, n), -1, dtype=np.int16)
    for r in range(n_repeats):
        sgk = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=ek.derive_seed(seed_, "rep", r))
        for f, (_, te) in enumerate(sgk.split(np.zeros(n), codes, groups)):
            fid[r, te] = f
    assert (fid >= 0).all()
    return _as_folds(fid, n_splits, seed_)


def subset_folds(folds, mask) -> ek.Folds:
    """Restrict every fold to the rows in ``mask`` (positions re-indexed 0..m-1); pairing is kept."""
    mask = np.asarray(mask, bool)
    fid = fold_id_matrix(folds)[:, mask]
    out = _as_folds(fid, folds.n_splits, folds.seed)
    out.hash = hashlib.sha256((folds.hash + hashlib.sha256(mask.tobytes()).hexdigest()).encode()).hexdigest()
    return out


# =============================================================================
# running
# =============================================================================
def _oof_one(spec: Spec, C0: float, X: pd.DataFrame, y: np.ndarray, sw, folds_list, n_splits: int) -> pd.DataFrame:
    parts = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i, (tr, te) in enumerate(folds_list):
            pipe = make_pipe(spec, C0)
            kw = {} if sw is None else {"model__sample_weight": sw[tr]}
            pipe.fit(X.iloc[tr], y[tr].astype(int), **kw)
            parts.append(pd.DataFrame({"repeat": i // n_splits, "fold": i % n_splits, "row": te,
                                       "prob": ek._positive_proba(pipe, X.iloc[te])}))
    return pd.concat(parts, ignore_index=True)


def run_many(ctx: Context, specs: dict, folds=None, *, n_jobs: int = 1, cache: dict | None = None) -> dict:
    """Out-of-fold predictions for every named spec (parallel over specs).

    Rows of each OOF frame are positions inside the spec's row mask (``Spec.rows``), on the
    folds restricted to that mask.  ``cache`` (dict) re-uses runs keyed by (spec, folds hash).
    """
    folds = ctx.folds if folds is None else folds
    cache = {} if cache is None else cache
    todo, out = {}, {}
    for name, sp in specs.items():
        key = (sp, folds.hash)
        if key in cache:
            out[name] = cache[key]
        else:
            todo[name] = sp
    jobs = []
    for name, sp in todo.items():
        X, y, sw, mask = spec_inputs(ctx, sp)
        f = folds if mask.all() else subset_folds(folds, mask)
        jobs.append((name, sp, X[mask].reset_index(drop=True) if not mask.all() else X, y[mask],
                     None if sw is None else sw[mask], list(f), f.n_splits))
    res = Parallel(n_jobs=n_jobs)(delayed(_oof_one)(sp, ctx.C0, X, y, sw, fl, ns) for _, sp, X, y, sw, fl, ns in jobs)
    for (name, sp, *_), oof in zip(jobs, res):
        cache[(sp, folds.hash)] = oof
        out[name] = oof
    return out


def spec_folds(ctx: Context, spec: Spec, folds=None):
    """Folds (restricted to the spec's rows if needed) and the row mask."""
    folds = ctx.folds if folds is None else folds
    _, _, _, mask = spec_inputs(ctx, spec)
    return (folds if mask.all() else subset_folds(folds, mask)), mask


# =============================================================================
# comparison engine (mirrors notebook 06, section "Comparison engine")
# =============================================================================
def equivalence_verdict(lo: float, hi: float, sesoi: float = C.SESOI["roc_auc"]) -> str:
    """Locked rule for equivalence claims (H2b-a): supported if the CI lies inside (-SESOI, SESOI),
    refuted if it lies wholly beyond +-SESOI, otherwise inconclusive."""
    return "supported" if (lo > -sesoi and hi < sesoi) else ("refuted" if (lo >= sesoi or hi <= -sesoi) else "inconclusive")


def _fold_auc(oof: pd.DataFrame, y, mask, w=None) -> pd.Series:
    vals = {}
    for (r, f), g in oof.groupby(["repeat", "fold"], sort=True):
        rows = g["row"].to_numpy()
        keep = mask[rows]
        yy = y[rows][keep]
        if len(np.unique(yy)) < 2:
            continue
        vals[(r, f)] = roc_auc_score(yy, g["prob"].to_numpy()[keep], sample_weight=None if w is None else w[rows][keep])
    return pd.Series(vals)


def weighted_paired_bootstrap(y, pa, pb, w, mask, *, n_boot: int, seed_: int) -> dict:
    """Paired, label-stratified bootstrap of a weighted AUC difference (weights travel with rows)."""
    sel = np.flatnonzero(mask)
    y, pa, pb, w = np.asarray(y)[sel].astype(int), pa[sel], pb[sel], np.asarray(w, float)[sel]
    rng = np.random.default_rng(seed_)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        i = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        boot[b] = roc_auc_score(y[i], pa[i], sample_weight=w[i]) - roc_auc_score(y[i], pb[i], sample_weight=w[i])
    ma, mb = roc_auc_score(y, pa, sample_weight=w), roc_auc_score(y, pb, sample_weight=w)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return dict(diff=ma - mb, ci_low=float(lo), ci_high=float(hi), se=float(boot.std(ddof=1)), metric_a=ma, metric_b=mb,
                n_eval=len(y), n_pos=len(pos), boot=boot)


def compare(oof_a: pd.DataFrame, oof_b: pd.DataFrame, y, folds, *, mask=None, w=None, use_t: bool = True,
            seed_: int = C.SEED_MASTER, n_boot: int = C.N_BOOT, sesoi: float = C.SESOI["roc_auc"]) -> dict:
    """Paired ROC-AUC difference A - B with the S7 rules.

    Bootstrap: paired, label-stratified, on the repeat-averaged OOF vectors (``evalkit.paired_bootstrap``;
    a weighted variant when ``w`` is given).  Corrected t (``use_t``): fold-level AUC differences,
    ``evalkit.corrected_t`` with the mean fold sizes.  The wider interval decides; the 80 %-power
    minimal detectable difference (MDD) is reported.  Verdicts: ``h2b`` = locked equivalence rule,
    ``sesoi_class`` = ``evalkit.verdict`` for a positive direction (equivalent / supported / ...).
    """
    y = np.asarray(y).astype(int)
    n = len(y)
    m = np.ones(n, bool) if mask is None else np.asarray(mask, bool)
    pa, pb = ek.mean_oof(oof_a, n), ek.mean_oof(oof_b, n)
    if w is None:
        bs = ek.paired_bootstrap(y, pa, pb, "roc_auc", n_boot=n_boot, seed=seed_, eval_mask=m)
    else:
        bs = weighted_paired_bootstrap(y, pa, pb, w, m, n_boot=n_boot, seed_=seed_)
    row = dict(auc_a=bs["metric_a"], auc_b=bs["metric_b"], diff_pooled=bs["diff"], boot_lo=bs["ci_low"],
               boot_hi=bs["ci_high"], boot_se=bs["se"], n_eval=bs["n_eval"], n_pos=bs["n_pos"])
    est, lo, hi, se, interval = bs["diff"], bs["ci_low"], bs["ci_high"], bs["se"], "bootstrap"
    mdd = (stats.norm.ppf(0.975) + stats.norm.ppf(0.80)) * se
    if use_t:
        d = (_fold_auc(oof_a, y, m, w) - _fold_auc(oof_b, y, m, w)).dropna().to_numpy()
        n_te = float(np.mean([len(te) for _, te in folds]))
        n_tr = float(np.mean([len(tr) for tr, _ in folds]))
        ct = ek.corrected_t(d, n_tr, n_te)
        row.update(t_mean=ct["mean"], t_lo=ct["ci_low"], t_hi=ct["ci_high"], t_se=ct["se_corr"], J=ct["J"])
        if (ct["ci_high"] - ct["ci_low"]) >= (bs["ci_high"] - bs["ci_low"]):
            est, lo, hi, se, interval = ct["mean"], ct["ci_low"], ct["ci_high"], ct["se_corr"], "corrected_t"
            mdd = (stats.t.ppf(0.975, ct["df"]) + stats.t.ppf(0.80, ct["df"])) * se
    row.update(est=est, lo=lo, hi=hi, se=se, interval=interval, mdd=mdd,
               h2b=equivalence_verdict(lo, hi, sesoi), sesoi_class=ek.verdict(lo, hi, sesoi, "+", est))
    return row


def auc_ci(y, p, mask=None, *, seed_: int = C.SEED_MASTER, n_boot: int = C.N_BOOT) -> tuple[float, float, float]:
    """AUC with a label-stratified percentile bootstrap CI (paired against a constant 0.5, as in S7)."""
    y = np.asarray(y).astype(int)
    b = ek.paired_bootstrap(y, p, np.full(len(y), 0.5), "roc_auc", n_boot=n_boot, eval_mask=mask, seed=seed_)
    return b["metric_a"], b["ci_low"] + 0.5, b["ci_high"] + 0.5


# =============================================================================
# negative and positive controls
# =============================================================================
def permutation_null(ctx: Context, spec: Spec, folds=None, *, n_perm: int = C.N_PERM, seed_: int, n_jobs: int = 1) -> dict:
    """Label-permutation null of the mean per-fold AUC (``evalkit.permutation_auc``) for one arm.

    Detects *procedural* leakage only (e.g. preprocessing fitted on test rows, label-derived
    weights): features stay with their rows, so feature leakage passes this test unnoticed."""
    folds = ctx.folds if folds is None else folds
    X, y, sw, mask = spec_inputs(ctx, spec)
    assert mask.all(), "permutation test runs on the full training part"
    fp = None if sw is None else {"model__sample_weight": sw}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ek.permutation_auc(functools.partial(make_pipe, spec, ctx.C0), X, y.astype(int), folds, n_perm=n_perm,
                                  seed=seed_, fit_params=fp, n_jobs=n_jobs)


def signal_feature(y, auc: float = POS_CONTROL_AUC, *, seed_: int) -> np.ndarray:
    """Synthetic positive control z = d * y + N(0, 1) with d = sqrt(2) * Phi^-1(auc).

    For two unit-variance normal classes separated by d the population ROC-AUC is Phi(d / sqrt 2),
    so the column has a known AUC (default 0.60) by construction."""
    d = np.sqrt(2.0) * stats.norm.ppf(auc)
    rng = np.random.default_rng(seed_)
    return d * np.asarray(y, float) + rng.standard_normal(len(y))


def tree_features_used(ctx: Context, spec: Spec, folds, feature: str) -> pd.DataFrame:
    """Fit the spec's tree on every training fold (and once on the whole part, ``fold = -1``);
    report the root split and whether ``feature`` is used anywhere in the tree."""
    X, y, sw, _ = spec_inputs(ctx, spec)
    rows = []
    sets = [(-1, np.arange(ctx.n))] + [(i, tr) for i, (tr, _) in enumerate(folds)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i, tr in sets:
            pipe = make_pipe(spec, ctx.C0)
            pipe.fit(X.iloc[tr], y[tr].astype(int), **({} if sw is None else {"model__sample_weight": sw[tr]}))
            names = list(pipe[:-1].get_feature_names_out())
            used = {names[j] for j in pipe[-1].tree_.feature if j >= 0}
            rows.append(dict(fold=i, root=names[pipe[-1].tree_.feature[0]], n_split_features=len(used),
                             uses_feature=feature in used))
    return pd.DataFrame(rows)


# =============================================================================
# leak hunt
# =============================================================================
def _oriented(a: float) -> float:
    return max(a, 1.0 - a)


def single_feature_scan(frame: pd.DataFrame, y, folds, *, cat_cols=(), mask=None) -> pd.DataFrame:
    """Univariate ROC-AUC of every column of ``frame`` (rows in ``mask``).

    Numeric columns: rank AUC on the non-missing rows (no fitting).  Categorical columns: out-of-fold
    target-mean encoding on the folds of the first repeat (missing = its own level), then AUC, so the
    encoding never sees the labels it is scored on.  ``auc_oriented`` = max(AUC, 1 - AUC)."""
    y = np.asarray(y).astype(int)
    m = np.ones(len(y), bool) if mask is None else np.asarray(mask, bool)
    first = [f for i, f in enumerate(folds) if i < folds.n_splits]
    rows = []
    for c in frame.columns:
        s = frame[c]
        if c in cat_cols or s.dtype == object:
            lvl = s.astype(str).where(s.notna(), "missing").to_numpy()
            enc = np.full(len(y), np.nan)
            for tr, te in first:
                g = pd.Series(y[tr]).groupby(lvl[tr]).mean()
                enc[te] = pd.Series(lvl[te]).map(g).fillna(y[tr].mean()).to_numpy()
            ok = m & ~np.isnan(enc)
            score, kind = enc, "categorical (OOF target encoding)"
        else:
            score = s.to_numpy(float)
            ok = m & ~np.isnan(score)
            kind = "numeric"
        yy = y[ok]
        a = roc_auc_score(yy, score[ok]) if len(np.unique(yy)) == 2 else np.nan
        rows.append(dict(variable=c, kind=kind, n_obs=int(ok.sum()), coverage=float(ok.sum() / m.sum()),
                         auc=a, auc_oriented=_oriented(a) if np.isfinite(a) else np.nan,
                         direction="higher = positive" if a >= 0.5 else "lower = positive"))
    return pd.DataFrame(rows).sort_values("auc_oriented", ascending=False).reset_index(drop=True)


def missing_indicator_scan(frame: pd.DataFrame, y, *, mask=None) -> pd.DataFrame:
    """AUC of the ``is_missing`` indicator of every column with partial missingness (skip-pattern check)."""
    y = np.asarray(y).astype(int)
    m = np.ones(len(y), bool) if mask is None else np.asarray(mask, bool)
    rows = []
    for c in frame.columns:
        ind = frame[c].isna().to_numpy()[m]
        if 0 < ind.sum() < len(ind):
            a = roc_auc_score(y[m], ind.astype(float))
            rows.append(dict(variable=c, n_missing=int(ind.sum()), share_missing=float(ind.mean()),
                             prev_if_missing=float(y[m][ind].mean()), prev_if_present=float(y[m][~ind].mean()),
                             auc=a, auc_oriented=_oriented(a)))
    return pd.DataFrame(rows).sort_values("auc_oriented", ascending=False).reset_index(drop=True)


#: derived design columns -> their source spec variables
DERIVED_SOURCES = {
    "bp_sys_mean": ("BPXOSY1", "BPXOSY2", "BPXOSY3"), "bp_dia_mean": ("BPXODI1", "BPXODI2", "BPXODI3"),
    "pulse_mean": ("BPXOPLS1", "BPXOPLS2", "BPXOPLS3"), "pa_mod_min_wk": ("PAD790Q", "PAD790U", "PAD800"),
    "pa_vig_min_wk": ("PAD810Q", "PAD810U", "PAD820"), "age_top": ("RIDAGEYR",), "pir_top": ("INDFMPIR",),
    "whtr": ("BMXWAIST", "BMXHT"),
}


def base_variable(col: str) -> str:
    """Spec variable (or derived column name) a design column comes from.

    Strips spline (``_sp<k>``), missing-indicator (``_missing``) and one-hot (``_<level>``) suffixes."""
    import re
    c = re.sub(r"_sp\d+$", "", str(col))
    c = re.sub(r"_missing$", "", c)
    if c in DERIVED_SOURCES or c in P._spec_by_var().index:
        return c
    for v in sorted(list(P._spec_by_var().index) + list(DERIVED_SOURCES), key=len, reverse=True):
        if c.startswith(v + "_"):
            return v
    return c


def contribution_importance(pipe, X: pd.DataFrame) -> pd.DataFrame:
    """Importance of each base variable in a fitted linear pipeline: the standard deviation (over
    rows of ``X``) of that variable's share of the linear predictor, sum_j x_ij * beta_j over its
    design columns (spline bases, dummies and missing indicator grouped together)."""
    D = pipe[:-1].transform(X)
    beta = np.asarray(pipe[-1].coef_, float).ravel()
    contrib = D.to_numpy(float) * beta
    groups: dict[str, list[int]] = {}
    for j, c in enumerate(D.columns):
        groups.setdefault(base_variable(c), []).append(j)
    rows = [dict(variable=v, sd_contribution=float(contrib[:, idx].sum(axis=1).std()), n_columns=len(idx),
                 columns=";".join(str(D.columns[j]) for j in idx)) for v, idx in groups.items()]
    return pd.DataFrame(rows).sort_values("sd_contribution", ascending=False).reset_index(drop=True)


INSTRUMENT = {
    "DEMO_L": "household interview (demographics)", "BMX_L": "MEC body measures (tape / scale)",
    "BPXO_L": "MEC oscillometric blood pressure", "BPQ_L": "interview questionnaire (blood pressure & cholesterol)",
    "SMQ_L": "interview questionnaire (smoking)", "PAQ_L": "interview questionnaire (physical activity)",
    "TCHOL_L": "same-visit lipid panel (non-glycaemic)", "HDL_L": "same-visit lipid panel (non-glycaemic)",
}


def availability_proof(variables, tier: int = 1) -> pd.DataFrame:
    """Point-of-care availability proof for design variables.

    For every variable (derived ones are traced to their source items): source file, instrument,
    spec role / admissibility / reason.  PASS requires every source item to be a ``feature`` that
    is admissible in the tier (T1, or T1/T2 for Tier 2) - i.e. obtainable before any glycaemic test
    and neither a diagnostic criterion nor a consequence of diagnosis (S1 availability rule)."""
    spec = P._spec_by_var()
    ok_tiers = {"T1"} if tier == 1 else {"T1", "T2"}
    rows = []
    for v in variables:
        src = DERIVED_SOURCES.get(v, (v,))
        info = [spec.loc[s] if s in spec.index else None for s in src]
        passed = all(i is not None and i["role"] == "feature" and i["admissible"] in ok_tiers for i in info)
        first = info[0]
        reason = "" if first is None else str(first["admiss_reason"])
        rows.append(dict(variable=v, sources=",".join(src),
                         file="" if first is None else first["file"],
                         instrument="" if first is None else INSTRUMENT.get(first["file"], first["file"]),
                         admissible=",".join(sorted({str(i["admissible"]) for i in info if i is not None})),
                         care_contact=any(s in P.CARE_ITEMS for s in src),
                         reason=reason, verdict="PASS" if passed else "FAIL"))
    return pd.DataFrame(rows)


# =============================================================================
# missing HbA1c: inverse-probability weights and delta adjustment
# =============================================================================
def examined_population() -> pd.DataFrame:
    """Examined (RIDSTATR = 2), non-pregnant adults >= 20 with or without HbA1c (per-variable sentinels).

    This is the population the 5,730-row complete-case cohort is drawn from; ``a1c_observed`` flags
    the cohort members."""
    mrg = io.load_merged(sentinels="per_variable")
    ex = mrg[(mrg["RIDAGEYR"] >= C.ADULT_MIN_AGE) & (mrg["RIDSTATR"] == 2) & (mrg["RIDEXPRG"] != 1)].copy()
    ex["a1c_observed"] = ex["LBXGH"].notna().astype(int)
    ex = io.add_derived(ex)
    return ex.sort_values("SEQN").reset_index(drop=True)


def missingness_design(ex: pd.DataFrame) -> pd.DataFrame:
    """Covariates of the S3 missing-HbA1c logit (notebook 02, section 7), unchanged."""
    race = ex["RIDRETH3"].map(io.RACE_LABELS)
    Xm = pd.DataFrame({"age (per 10 y)": ex["RIDAGEYR"] / 10, "female": (ex["RIAGENDR"] == 2).astype(int)}, index=ex.index)
    for r in ["NH Black", "NH Asian", "Mexican American", "Other Hispanic", "Other/Multi"]:
        Xm[r] = (race == r).astype(int)
    Xm["PIR (per unit)"] = ex["INDFMPIR"].fillna(ex["INDFMPIR"].mean())
    Xm["PIR missing"] = ex["INDFMPIR"].isna().astype(int)
    Xm["BMI (per unit)"] = ex["BMXBMI"].fillna(ex["BMXBMI"].mean())
    Xm["BMI missing"] = ex["BMXBMI"].isna().astype(int)
    Xm["uninsured"] = (ex["HIQ011"] == 2).astype(int)
    Xm["no usual place of care"] = (ex["HUQ030"] == 2).astype(int)
    Xm["self-reported diabetes"] = (ex["DIQ010"] == 1).astype(int)
    Xm["told hypertension"] = (ex["BPQ020"] == 1).astype(int)
    return Xm


def observation_model(ex: pd.DataFrame):
    """Unweighted logit of P(HbA1c observed | S3 covariates); returns the statsmodels fit."""
    import statsmodels.api as sm
    return sm.Logit(ex["a1c_observed"].to_numpy(), sm.add_constant(missingness_design(ex))).fit(disp=0)


def _expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def _logit(p, eps=1e-9):
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def delta_prevalence(y_obs, w, missing_self, p_mar_missing, w_missing, deltas) -> pd.DataFrame:
    """Delta-adjusted (pattern-mixture) weighted prevalence of L_comb in the examined population.

    Observed rows contribute their label.  A row without HbA1c is positive if diabetes was
    self-reported; otherwise its probability of HbA1c >= 6.5 is the MAR prediction shifted by delta
    on the logit scale (delta = log odds ratio missing vs observed at equal covariates).  Manski-type
    bounds set every undetermined row to 0 (lower) or 1 (upper)."""
    y_obs, w, w_m = np.asarray(y_obs, float), np.asarray(w, float), np.asarray(w_missing, float)
    ms, pm = np.asarray(missing_self, bool), np.asarray(p_mar_missing, float)
    tot = w.sum() + w_m.sum()
    base = (w * y_obs).sum() + w_m[ms].sum()
    rows = []
    for d in deltas:
        p = _expit(_logit(pm) + d)
        rows.append(dict(delta=float(d), odds_ratio=float(np.exp(d)), prevalence=float((base + (w_m[~ms] * p[~ms]).sum()) / tot)))
    out = pd.DataFrame(rows)
    out.attrs["manski_low"] = float(base / tot)
    out.attrs["manski_high"] = float((base + w_m[~ms].sum()) / tot)
    out.attrs["complete_case"] = float((w * y_obs).sum() / w.sum())
    return out


def delta_auc(y_obs, pa_obs, pb_obs, missing_self, p_mar_missing, pa_m, pb_m, deltas, *, n_draw: int, seed_: int,
              obs_mask=None, miss_mask=None) -> pd.DataFrame:
    """Delta-adjusted AUC(A) - AUC(B) when the people without HbA1c are added to the evaluation set.

    Labels of undetermined missing rows are drawn ``n_draw`` times from Bernoulli(expit(logit p_MAR + delta));
    self-reported missing rows are positive.  ``obs_mask`` / ``miss_mask`` restrict the population
    (e.g. E-SCREEN).  Also returns the two Manski labelings (all undetermined negative / positive)."""
    rng = np.random.default_rng(seed_)
    om = np.ones(len(y_obs), bool) if obs_mask is None else np.asarray(obs_mask, bool)
    mm = np.ones(len(pa_m), bool) if miss_mask is None else np.asarray(miss_mask, bool)
    yo, ms, pm = np.asarray(y_obs, int)[om], np.asarray(missing_self, bool)[mm], np.asarray(p_mar_missing, float)[mm]
    pa = np.concatenate([np.asarray(pa_obs)[om], np.asarray(pa_m)[mm]])
    pb = np.concatenate([np.asarray(pb_obs)[om], np.asarray(pb_m)[mm]])
    ra, rb = stats.rankdata(pa), stats.rankdata(pb)

    def auc_rows(Y):
        npos = Y.sum(axis=1)
        nneg = Y.shape[1] - npos
        fa = ((ra * Y).sum(axis=1) - npos * (npos + 1) / 2) / (npos * nneg)
        fb = ((rb * Y).sum(axis=1) - npos * (npos + 1) / 2) / (npos * nneg)
        return fa, fb

    rows = []
    for d in deltas:
        p = np.where(ms, 1.0, _expit(_logit(pm) + d))
        ym = (rng.random((n_draw, len(p))) < p).astype(int)
        Y = np.concatenate([np.broadcast_to(yo, (n_draw, len(yo))), ym], axis=1)
        fa, fb = auc_rows(Y)
        diff = fa - fb
        rows.append(dict(delta=float(d), scenario="delta", auc_a=float(fa.mean()), auc_b=float(fb.mean()),
                         diff=float(diff.mean()), diff_lo=float(np.percentile(diff, 2.5)),
                         diff_hi=float(np.percentile(diff, 97.5))))
    for name, fill in (("manski_all_negative", 0), ("manski_all_positive", 1)):
        ym = np.where(ms, 1, fill)[None, :]
        Y = np.concatenate([yo[None, :], ym], axis=1)
        fa, fb = auc_rows(Y)
        rows.append(dict(delta=np.nan, scenario=name, auc_a=float(fa[0]), auc_b=float(fb[0]), diff=float(fa[0] - fb[0]),
                         diff_lo=np.nan, diff_hi=np.nan))
    return pd.DataFrame(rows)


# =============================================================================
# hold-out helpers (call only after the exp-freeze tag exists)
# =============================================================================
def tag_exists(name: str) -> bool:
    """True if the git tag exists in the repository (False if git is unavailable)."""
    try:
        out = subprocess.run(["git", "tag", "-l", name], cwd=C.ROOT, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() == name
    except Exception:  # noqa: BLE001 - no git (e.g. a grader's copy of the notebook)
        return False


def head_commit(ref: str = "HEAD") -> str | None:
    try:
        out = subprocess.run(["git", "rev-list", "-n", "1", ref], cwd=C.ROOT, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def holdout_frames(ctx: Context):
    """(raw test rows, labelled test rows, {tier: raw feature frame}) of the stored hold-out."""
    raw_te = ctx.raw.iloc[ctx.test_idx].reset_index(drop=True)
    cl_te = ctx.clean.iloc[ctx.test_idx].reset_index(drop=True)
    return raw_te, cl_te, {t: P.raw_feature_frame(raw_te, t) for t in (1, 2)}


def fit_full(ctx: Context, spec: Spec):
    """Fit a spec on the whole training part; returns the fitted pipeline."""
    X, y, sw, mask = spec_inputs(ctx, spec)
    assert mask.all()
    pipe = make_pipe(spec, ctx.C0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipe.fit(X, y.astype(int), **({} if sw is None else {"model__sample_weight": sw}))
    return pipe


def holdout_scores(y, p, thr: float, *, mask=None, seed_: int, n_boot: int = C.N_BOOT) -> dict:
    """Hold-out metrics for one score vector: AUC with bootstrap CI and SE, PR-AUC, Brier, calibration
    slope / CITL, and recall + specificity at the training-derived threshold ``thr``."""
    y = np.asarray(y).astype(int)
    m = np.ones(len(y), bool) if mask is None else np.asarray(mask, bool)
    yy, pp = y[m], np.asarray(p, float)[m]
    ms = ek.metric_suite(yy, pp)
    b = ek.paired_bootstrap(yy, pp, np.full(len(yy), 0.5), "roc_auc", n_boot=n_boot, seed=seed_)
    call = pp >= thr
    return dict(n=int(len(yy)), n_pos=int(yy.sum()), prevalence=float(yy.mean()), roc_auc=ms["roc_auc"],
                auc_lo=b["ci_low"] + 0.5, auc_hi=b["ci_high"] + 0.5, auc_se=b["se"], pr_auc=ms["pr_auc"],
                brier=ms["brier"], cal_slope=ms["cal_slope"], cal_citl=ms["cal_citl"], threshold=float(thr),
                recall_at_thr=float(call[yy == 1].mean()), spec_at_thr=float((~call[yy == 0]).mean()))


def sha256_ints(values) -> str:
    """SHA-256 of sorted integers, one per line (same convention as ``evalkit.make_holdout``)."""
    return hashlib.sha256("\n".join(str(int(v)) for v in sorted(values)).encode()).hexdigest()
