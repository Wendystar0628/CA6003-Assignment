"""Evaluation toolkit (stage S7): splits, metrics, paired comparisons, resampling.

Design rules (docs/development_process.md sections 1.7, 7.1, S7, S9):

* The 20 % hold-out is created ONCE (stratified on label x race), persisted with its
  SEQN lists and a SHA-256 of the sorted test SEQNs, and only verified afterwards.
* CV folds are generated ONCE per run mode (``FAST`` 5x2 / ``FINAL`` 5x5) with an
  integer seed, persisted with a hash, and shared by every arm.
* Paired comparisons are reported with two intervals: the Nadeau-Bengio corrected
  resampled t (fold level) and a paired, label-stratified bootstrap on pooled
  out-of-fold (OOF) predictions; the more conservative one is used for verdicts.
* Verdict vocabulary: supported / refuted / equivalent / inconclusive (+ ``mixed``
  decided at hypothesis level by :func:`combine_verdicts`).

Conventions
-----------
``y`` is a 0/1 array, ``p`` a predicted probability of class 1, a "positive" call
means ``p >= threshold``.  All row indices are *positional* (0..n-1 in the order of
the cohort / design matrix handed to the function).  Differences are always
``A - B`` (for Brier a negative difference therefore favours A).

References
----------
Hanley & McNeil (1982) Radiology 143:29-36 (AUC);  Saito & Rehmsmeier (2015) PLoS ONE
10:e0118432 (PR-AUC);  Brier (1950) Mon. Weather Rev. 78:1-3;  Cox (1958) Biometrika
45:562-565 (calibration slope / intercept);  Youden (1950) Cancer 3:32-35;
Nadeau & Bengio (2003) Mach. Learn. 52:239-281, doi:10.1023/A:1024068626366;
Efron & Tibshirani (1993) An Introduction to the Bootstrap;  Lakens (2017) Soc. Psychol.
Pers. Sci. 8:355-362 (equivalence testing);  Ojala & Garriga (2010) JMLR 11:1833-1863
(permutation tests);  Phipson & Smyth (2010) Stat. Appl. Genet. Mol. Biol. 9:39
(permutation p-values are never zero).
"""
from __future__ import annotations

import hashlib
import json
import warnings
import zlib
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split

from . import config as C

SPLITS_DIR = C.RESULTS_DIR / "splits"

__all__ = [
    "derive_seed", "make_holdout", "make_folds", "Folds", "cv_predict", "mean_oof",
    "metric_suite", "recall_at_specificity", "fold_metrics", "repeat_metrics",
    "paired_fold_diffs", "corrected_t", "paired_bootstrap", "verdict",
    "combine_verdicts", "coef_bootstrap", "CoefBootstrap", "permutation_auc",
]


# =============================================================================
# 1. Seeds and splits
# =============================================================================
def derive_seed(seed: int = C.SEED_MASTER, *tags) -> int:
    """Derive a reproducible 32-bit integer seed from ``seed`` and string/int tags.

    Uses ``np.random.SeedSequence([seed, crc32(tag)...])`` so that every consumer
    (folds, bootstraps, permutations, robustness seeds) gets an independent stream
    while the whole project stays reproducible from ``SEED_MASTER``.
    """
    keys = [int(seed)] + [t if isinstance(t, int) else zlib.crc32(str(t).encode()) for t in tags]
    return int(np.random.SeedSequence(keys).generate_state(1)[0])


def _sha256_ints(values) -> str:
    return hashlib.sha256("\n".join(str(int(v)) for v in sorted(values)).encode()).hexdigest()


def _collapse_rare(strat: pd.Series, min_count: int) -> pd.Series:
    """Merge strata with fewer than ``min_count`` members into one 'rare' stratum."""
    counts = strat.map(strat.value_counts())
    out = strat.where(counts >= min_count, "rare")
    if (out == "rare").sum() and (out == "rare").sum() < min_count:  # still too small -> merge into largest
        out = out.where(out != "rare", strat.value_counts().index[0])
    return out


def make_holdout(cohort: pd.DataFrame, seed: int = C.SEED_MASTER, *, label_col: str = "L_comb",
                 race_col: str = "race", id_col: str = "SEQN", frac: float = C.HOLDOUT_FRAC,
                 path: str | Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Create (once) or verify the stratified 20 % hold-out; return positional ``(train_idx, test_idx)``.

    Definition: ``sklearn.model_selection.train_test_split(test_size=frac,
    stratify=label x race, random_state=seed)`` on the cohort rows.  Strata with fewer
    than two members are merged into a 'rare' stratum (``train_test_split`` needs >= 2).

    Persistence (``results/splits/holdout.json`` unless ``path`` is given): seed, fraction,
    stratifier columns, the ``id_col`` (SEQN) lists of both parts and the SHA-256 of the
    sorted test SEQNs.  If the file already exists nothing is re-split: the stored hash
    and the cohort membership are verified (``ValueError`` on any mismatch, ``UserWarning``
    if ``seed``/``frac`` differ from the stored values) and the stored split is returned.
    The hold-out must be touched only once (S9, after exp-freeze).

    ``id_col`` falls back to the DataFrame index if the column is absent.
    """
    path = Path(path) if path is not None else SPLITS_DIR / "holdout.json"
    ids = (cohort[id_col] if id_col in cohort.columns else pd.Series(cohort.index, index=cohort.index)).to_numpy()
    if len(set(ids.tolist())) != len(ids):
        raise ValueError(f"{id_col} is not unique in the cohort")
    pos_of = {int(s): i for i, s in enumerate(ids)}

    if path.exists():
        meta = json.loads(path.read_text(encoding="utf-8"))
        test_ids, train_ids = meta["test_seqn"], meta["train_seqn"]
        if _sha256_ints(test_ids) != meta["sha256_test_seqn"]:
            raise ValueError(f"{path}: stored test SEQNs do not match their SHA-256 (file was edited)")
        if set(test_ids) & set(train_ids) or set(test_ids) | set(train_ids) != set(pos_of):
            raise ValueError(f"{path}: stored split does not partition the current cohort "
                             f"({len(test_ids) + len(train_ids)} stored vs {len(ids)} rows); "
                             "the cohort changed after the hold-out was created")
        if meta.get("seed") != int(seed) or abs(meta.get("frac", frac) - frac) > 1e-12:
            warnings.warn(f"hold-out exists with seed={meta.get('seed')}, frac={meta.get('frac')}; "
                          "arguments ignored, stored split returned")
        return (np.array(sorted(pos_of[s] for s in train_ids)), np.array(sorted(pos_of[s] for s in test_ids)))

    strat = cohort[label_col].astype(str) + "|" + cohort[race_col].astype(str)
    strat = _collapse_rare(strat.reset_index(drop=True), 2)
    idx = np.arange(len(cohort))
    tr, te = train_test_split(idx, test_size=frac, stratify=strat.to_numpy(), random_state=int(seed))
    tr, te = np.sort(tr), np.sort(te)
    meta = {
        "seed": int(seed), "frac": float(frac), "stratify": [label_col, race_col], "id_col": id_col,
        "n": int(len(ids)), "n_train": int(len(tr)), "n_test": int(len(te)),
        "sha256_test_seqn": _sha256_ints(ids[te]),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "train_seqn": sorted(int(s) for s in ids[tr]), "test_seqn": sorted(int(s) for s in ids[te]),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta), encoding="utf-8")
    return tr, te


class Folds(list):
    """List of ``(train_idx, test_idx)`` tuples (repeat-major order) with metadata.

    Attributes: ``n_splits``, ``n_repeats``, ``n``, ``seed``, ``hash`` (SHA-256 of the
    fold-assignment matrix and parameters), ``path`` (npz file or None).
    """
    n_splits: int
    n_repeats: int
    n: int
    seed: int
    hash: str
    path: Path | None

    def repeat_of(self, i: int) -> int:
        return i // self.n_splits

    def fold_of(self, i: int) -> int:
        return i % self.n_splits


def _folds_hash(fold_id: np.ndarray, n_splits: int, n_repeats: int, seed: int) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(fold_id, dtype=np.int16).tobytes())
    h.update(f"|{n_splits}|{n_repeats}|{seed}|{fold_id.shape}".encode())
    return h.hexdigest()


def _array_sha(a) -> str:
    return hashlib.sha256(pd.util.hash_array(pd.Series(a).astype(str).to_numpy()).tobytes()).hexdigest()


def _folds_from_ids(fold_id: np.ndarray, n_splits: int) -> list[tuple[np.ndarray, np.ndarray]]:
    out = []
    for r in range(fold_id.shape[0]):
        for f in range(n_splits):
            test = np.flatnonzero(fold_id[r] == f)
            train = np.flatnonzero(fold_id[r] != f)
            out.append((train, test))
    return out


def make_folds(y, strat=None, *, n_splits: int = C.CV_SPLITS, n_repeats: int = C.CV_REPEATS,
               seed: int = C.SEED_MASTER, mode: str | None = None,
               path: str | Path | None = None) -> Folds:
    """Repeated stratified K-fold indices, generated once and persisted.

    Definition: ``RepeatedStratifiedKFold(n_splits, n_repeats, random_state=seed)`` (integer
    seed, so the folds are identical on every call) stratified on ``strat`` (default: ``y``;
    pass e.g. label x race codes).  Returns a :class:`Folds` list ordered repeat-major, i.e.
    entry ``r * n_splits + f`` is fold ``f`` of repeat ``r``; every row is in exactly one
    test fold per repeat.

    Persistence: ``results/splits/folds_<FAST|FINAL>.npz`` (``mode`` defaults to
    ``config.NB_MODE``) holding the fold-assignment matrix (n_repeats x n), parameters,
    SHA-256 of ``y`` and ``strat``, and the folds hash.  If the file exists it is reused after
    verifying parameters, ``y``/``strat`` hashes and the folds hash (``ValueError`` otherwise;
    delete the file deliberately to regenerate).  Identical hashes across arms prove that all
    arms were compared on the same folds.
    """
    y = np.asarray(y)
    strat = y if strat is None else np.asarray(strat)
    n = len(y)
    mode = (mode or C.NB_MODE).upper()
    path = Path(path) if path is not None else SPLITS_DIR / f"folds_{mode}.npz"
    y_sha, s_sha = _array_sha(y), _array_sha(strat)

    if path.exists():
        z = np.load(path, allow_pickle=False)
        fold_id = z["fold_id"]
        stored = dict(n_splits=int(z["n_splits"]), n_repeats=int(z["n_repeats"]), seed=int(z["seed"]))
        want = dict(n_splits=n_splits, n_repeats=n_repeats, seed=int(seed))
        if stored != want:
            raise ValueError(f"{path}: stored folds {stored} differ from requested {want}")
        if fold_id.shape != (n_repeats, n) or str(z["y_sha"]) != y_sha or str(z["strat_sha"]) != s_sha:
            raise ValueError(f"{path}: stored folds were built for a different y/strat vector")
        if _folds_hash(fold_id, n_splits, n_repeats, int(seed)) != str(z["hash"]):
            raise ValueError(f"{path}: fold assignment does not match its stored hash")
    else:
        codes = _collapse_rare(pd.Series(strat).astype(str), n_splits).to_numpy()
        rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=int(seed))
        fold_id = np.full((n_repeats, n), -1, dtype=np.int16)
        for i, (_, test) in enumerate(rskf.split(np.zeros(n), codes)):
            fold_id[i // n_splits, test] = i % n_splits
        assert (fold_id >= 0).all()
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, fold_id=fold_id, n_splits=n_splits, n_repeats=n_repeats, seed=int(seed),
                 y_sha=y_sha, strat_sha=s_sha, hash=_folds_hash(fold_id, n_splits, n_repeats, int(seed)))

    folds = Folds(_folds_from_ids(fold_id, n_splits))
    folds.n_splits, folds.n_repeats, folds.n, folds.seed = n_splits, n_repeats, n, int(seed)
    folds.hash, folds.path = _folds_hash(fold_id, n_splits, n_repeats, int(seed)), path
    return folds


# =============================================================================
# 2. Cross-validated predictions
# =============================================================================
def _take(a, idx):
    return a.iloc[idx] if hasattr(a, "iloc") else np.asarray(a)[idx]


def _slice_fit_params(fit_params: dict | None, idx: np.ndarray, n: int) -> dict:
    """Slice every length-n array-like in ``fit_params`` to ``idx``; pass other values through."""
    out = {}
    for k, v in (fit_params or {}).items():
        if hasattr(v, "__len__") and not isinstance(v, str) and len(v) == n:
            out[k] = np.asarray(v)[idx]
        else:
            out[k] = v
    return out


def _fold_repeats(folds: Sequence, n: int) -> list[tuple[int, int]]:
    """(repeat, fold) label per entry; infers repeats from test-row coverage if no metadata."""
    if hasattr(folds, "n_splits"):
        return [(i // folds.n_splits, i % folds.n_splits) for i in range(len(folds))]
    labels, r, f, seen = [], 0, 0, 0
    for _, te in folds:
        labels.append((r, f))
        f, seen = f + 1, seen + len(te)
        if seen >= n:
            r, f, seen = r + 1, 0, 0
    return labels


def _positive_proba(model, X) -> np.ndarray:
    proba = model.predict_proba(X)
    classes = list(getattr(model, "classes_", [0, 1]))
    return proba[:, classes.index(1)]


def cv_predict(make_pipe: Callable, X, y, folds: Sequence, *, fit_params: dict | None = None) -> pd.DataFrame:
    """Out-of-fold predicted probabilities for every (repeat, fold).

    ``make_pipe`` is a zero-argument factory; a fresh, unfitted estimator is built (and
    ``sklearn.base.clone``d) for each fold, so nothing leaks between folds (preprocessing
    is fitted on the training part only).  ``fit_params`` such as
    ``{"logisticregression__sample_weight": w}`` are passed to ``fit``; every array-like of
    length ``len(y)`` is sliced to the fold's training rows.

    Returns a long DataFrame with columns ``repeat, fold, row, prob`` (``row`` = positional
    row of ``X``); each row appears once per repeat.
    """
    n = len(y)
    y = np.asarray(y)
    parts = []
    for (r, f), (tr, te) in zip(_fold_repeats(folds, n), folds):
        model = clone(make_pipe())
        model.fit(_take(X, tr), y[tr], **_slice_fit_params(fit_params, tr, n))
        parts.append(pd.DataFrame({"repeat": r, "fold": f, "row": te, "prob": _positive_proba(model, _take(X, te))}))
    return pd.concat(parts, ignore_index=True).astype({"repeat": "int16", "fold": "int16", "row": "int64"})


def mean_oof(oof: pd.DataFrame, n: int | None = None) -> np.ndarray:
    """Row-wise mean of the OOF probability over repeats (vector indexed by row position)."""
    s = oof.groupby("row")["prob"].mean()
    if n is not None:
        s = s.reindex(range(n))
    return s.to_numpy()


# =============================================================================
# 3. Metrics
# =============================================================================
def _clean_inputs(y, p, w=None):
    y = np.asarray(y).astype(int).ravel()
    p = np.asarray(p, dtype=float).ravel()
    w = None if w is None else np.asarray(w, dtype=float).ravel()
    if len(y) != len(p) or (w is not None and len(w) != len(y)):
        raise ValueError("y, p, w must have equal length")
    return y, p, w


def recall_at_specificity(y, p, spec: float = C.SPEC_FIXED, neg_mask=None, w=None) -> tuple[float, float]:
    """Recall (sensitivity) at a threshold giving specificity >= ``spec``; returns ``(recall, threshold)``.

    Definition: let N be the negatives (``y == 0``, optionally restricted to ``neg_mask``, e.g.
    the E-SCREEN negatives) and k = ceil(spec * |N|).  With v_k the k-th smallest negative
    score, the threshold is the smallest observed score strictly greater than v_k, and a
    case is called positive when ``p >= threshold``.  Then at least ``spec`` of N has
    ``p < threshold`` (ties are resolved conservatively, so specificity >= spec holds).
    Recall is TP / P over *all* positives.  With weights ``w`` the k-th smallest is the weighted
    quantile (smallest v whose weighted cumulative share of N is at least ``spec``).
    If no score exceeds v_k the threshold is +inf and recall 0.

    Returns ``(nan, nan)`` if there are no negatives or no positives.
    """
    y, p, w = _clean_inputs(y, p, w)
    negsel = y == 0
    if neg_mask is not None:
        negsel &= np.asarray(neg_mask, dtype=bool)
    pos = y == 1
    if negsel.sum() == 0 or pos.sum() == 0:
        return float("nan"), float("nan")
    neg_p = p[negsel]
    if w is None:
        v = np.sort(neg_p)[int(np.ceil(spec * len(neg_p) - 1e-12)) - 1]
    else:
        order = np.argsort(neg_p, kind="mergesort")
        cw = np.cumsum(w[negsel][order]) / w[negsel].sum()
        v = neg_p[order][min(np.searchsorted(cw, spec - 1e-12), len(cw) - 1)]
    above = p[p > v]
    thr = float(above.min()) if len(above) else float("inf")
    hit = p[pos] >= thr
    recall = float(np.average(hit, weights=None if w is None else w[pos]))
    return recall, thr


def _logit(p, eps=1e-6):
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def _calibration(y, p, w=None):
    """Logistic recalibration ``logit P(y=1) = a + b * logit(p)``; returns (slope b, intercept a, CITL).

    CITL (calibration-in-the-large) is the intercept of the model with the slope fixed at 1
    (offset ``logit(p)``).  NaN if p is (nearly) constant or the fit does not converge /
    separates perfectly.
    """
    import statsmodels.api as sm
    lp = _logit(p)
    if np.ptp(lp) < 1e-9 or len(np.unique(y)) < 2:
        return float("nan"), float("nan"), float("nan")
    kw = {} if w is None else {"freq_weights": w}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = sm.GLM(y, sm.add_constant(lp), family=sm.families.Binomial(), **kw).fit()
            citl = sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=lp, **kw).fit()
        a, b = float(fit.params[0]), float(fit.params[1])
        if not (np.isfinite(a) and np.isfinite(b)) or abs(b) > 1e3:
            return float("nan"), float("nan"), float("nan")
        return b, a, float(citl.params[0])
    except Exception:  # noqa: BLE001 - perfect separation etc.
        return float("nan"), float("nan"), float("nan")


def _youden_threshold(y, p, w=None) -> float:
    fpr, tpr, thr = roc_curve(y, p, sample_weight=w)
    return float(thr[np.argmax(tpr - fpr)])


def metric_suite(y, p, w=None, threshold: float | None = None) -> dict:
    """Standard metric set for one prediction vector.

    * ``roc_auc``: area under the ROC curve = P(score_pos > score_neg) + 0.5 P(tie)
      (Hanley & McNeil 1982), ``sklearn.metrics.roc_auc_score``.
    * ``pr_auc``: average precision, sum_n (R_n - R_{n-1}) P_n (Saito & Rehmsmeier 2015);
      the no-skill level equals the prevalence.
    * ``brier``: mean (p - y)^2 (Brier 1950); lower is better.
    * ``recall_at_spec``: sensitivity at specificity >= ``config.SPEC_FIXED`` (0.80) and the
      corresponding ``thr_at_spec`` (see :func:`recall_at_specificity`).
    * ``balanced_accuracy``: (sensitivity + specificity) / 2 at ``threshold``.
      **WARNING**: if ``threshold`` is None the Youden-J maximiser (Youden 1950) is computed on
      the SAME data that is being scored, which is optimistically biased.  For honest numbers
      pass a threshold derived from training data / other folds (see :func:`fold_metrics`).
    * ``cal_slope`` / ``cal_intercept``: coefficients (b, a) of the logistic recalibration
      ``logit P(y=1) = a + b * logit(p)`` fitted with statsmodels (Cox 1958); ideal b=1, a=0.
      ``cal_citl`` is the intercept with the slope fixed at 1 (calibration-in-the-large).
    * ``prevalence``: (weighted) share of positives; ``n``, ``n_pos``.

    ``w`` are optional sample weights (design weights); this gives point estimates only, no
    design-based variance.  Metrics that are undefined (one class only, constant scores)
    are returned as NaN rather than raising.
    """
    y, p, w = _clean_inputs(y, p, w)
    nan = float("nan")
    out = dict(n=int(len(y)), n_pos=int(y.sum()), prevalence=float(np.average(y, weights=w)))
    two = len(np.unique(y)) == 2
    out["roc_auc"] = float(roc_auc_score(y, p, sample_weight=w)) if two else nan
    out["pr_auc"] = float(average_precision_score(y, p, sample_weight=w)) if two else nan
    out["brier"] = float(np.average((p - y) ** 2, weights=w))
    out["recall_at_spec"], out["thr_at_spec"] = recall_at_specificity(y, p, C.SPEC_FIXED, w=w)
    if two:
        thr = _youden_threshold(y, p, w) if threshold is None else float(threshold)
        pred = p >= thr
        sens = np.average(pred[y == 1], weights=None if w is None else w[y == 1])
        spec = np.average(~pred[y == 0], weights=None if w is None else w[y == 0])
        out["balanced_accuracy"], out["threshold"] = float(0.5 * (sens + spec)), thr
    else:
        out["balanced_accuracy"], out["threshold"] = nan, nan
    out["cal_slope"], out["cal_intercept"], out["cal_citl"] = _calibration(y, p, w)
    return out


def _mask(eval_mask, n) -> np.ndarray:
    return np.ones(n, bool) if eval_mask is None else np.asarray(eval_mask, dtype=bool)


def fold_metrics(oof: pd.DataFrame, y, eval_mask=None, w=None, threshold="other_folds") -> pd.DataFrame:
    """Metric table with one row per ``(repeat, fold)`` of an OOF prediction frame.

    ``oof`` has columns ``repeat, fold, row, prob`` (:func:`cv_predict`); ``y`` is indexed by
    ``row``.  ``eval_mask`` (bool, length ``len(y)``) restricts evaluation to a sub-population
    such as E-SCREEN (rows outside the mask are dropped before every metric).

    ``threshold`` controls the balanced-accuracy cut-off:

    * ``"other_folds"`` (default): Youden threshold computed from the OOF predictions of the
      *other* folds of the same repeat (inside ``eval_mask``).  Those predictions never see
      this fold's labels, so the cut-off is not fitted on the labels being scored.
    * ``"same"``: Youden on the fold itself (optimistic; diagnostics only).
    * a float: fixed threshold.

    Output columns: repeat, fold, then the keys of :func:`metric_suite`.
    """
    y = np.asarray(y).astype(int)
    keep = _mask(eval_mask, len(y))
    oof = oof[keep[oof["row"].to_numpy()]]
    wv = None if w is None else np.asarray(w, dtype=float)
    rows = []
    for (r, f), g in oof.groupby(["repeat", "fold"], sort=True):
        idx = g["row"].to_numpy()
        thr = None
        if threshold == "other_folds":
            rest = oof[(oof["repeat"] == r) & (oof["fold"] != f)]
            ri = rest["row"].to_numpy()
            if len(np.unique(y[ri])) == 2:
                thr = _youden_threshold(y[ri], rest["prob"].to_numpy(), None if wv is None else wv[ri])
        elif threshold != "same":
            thr = float(threshold)
        m = metric_suite(y[idx], g["prob"].to_numpy(), None if wv is None else wv[idx], threshold=thr)
        rows.append({"repeat": int(r), "fold": int(f), **m})
    return pd.DataFrame(rows)


def repeat_metrics(oof: pd.DataFrame, y, eval_mask=None, w=None, threshold="other_repeats") -> pd.DataFrame:
    """Metric table per repeat on the pooled OOF vector (every row predicted once per repeat).

    Preferred for small sub-populations (E-SCREEN has only ~24 positives per fold): AUC etc. are
    computed on all positives of the repeat at once instead of on noisy single folds.
    ``threshold`` for balanced accuracy: ``"other_repeats"`` (default) = Youden threshold of the
    row-wise mean OOF probability of the *other* repeats (``"same"`` when only one repeat
    exists), ``"same"`` = Youden on the evaluated vector (optimistic), or a float.

    Note: pooling folds mixes models trained on slightly different data, so a no-information
    model (``DummyClassifier('prior')``) scores marginally below 0.5 here (its fold-wise prior
    is anti-correlated with the held-out prevalence) while per-fold AUC is exactly 0.5.
    """
    y = np.asarray(y).astype(int)
    keep = _mask(eval_mask, len(y))
    oof = oof[keep[oof["row"].to_numpy()]]
    wv = None if w is None else np.asarray(w, dtype=float)
    repeats = sorted(oof["repeat"].unique())
    rows = []
    for r in repeats:
        g = oof[oof["repeat"] == r]
        idx = g["row"].to_numpy()
        thr = None
        if threshold == "other_repeats" and len(repeats) > 1:
            rest = oof[oof["repeat"] != r].groupby("row")["prob"].mean()
            ri = rest.index.to_numpy()
            thr = _youden_threshold(y[ri], rest.to_numpy(), None if wv is None else wv[ri])
        elif threshold not in ("other_repeats", "same"):
            thr = float(threshold)
        m = metric_suite(y[idx], g["prob"].to_numpy(), None if wv is None else wv[idx], threshold=thr)
        rows.append({"repeat": int(r), **m})
    return pd.DataFrame(rows)


def paired_fold_diffs(fm_a: pd.DataFrame, fm_b: pd.DataFrame, metric: str = "roc_auc") -> np.ndarray:
    """Fold-level differences ``metric_A - metric_B`` aligned on (repeat, fold); input of :func:`corrected_t`."""
    a = fm_a.set_index(["repeat", "fold"])[metric]
    b = fm_b.set_index(["repeat", "fold"])[metric]
    if not a.index.equals(b.index):
        raise ValueError("fold tables are not aligned (different folds were used)")
    return (a - b).to_numpy()


# =============================================================================
# 4. Paired comparisons: corrected t, paired bootstrap, verdicts
# =============================================================================
def corrected_t(diffs, n_train: int, n_test: int, alpha: float = 0.05) -> dict:
    """Nadeau-Bengio (2003) corrected resampled t-test for J paired fold-level differences.

    With ``d_j`` the metric difference (A - B) on resample j (J = n_splits * n_repeats),
    mean ``d`` and sample variance ``s^2`` (ddof = 1):

        var_corr = (1/J + n_test/n_train) * s^2,      t = d / sqrt(var_corr),   df = J - 1.

    The naive variance ``s^2 / J`` ignores that the J train/test splits overlap and that the
    test sets of one repeat are dependent; the extra term ``n_test/n_train`` (= 1/(k-1) = 1/4
    for 5-fold CV) corrects this.  The CI is ``d +/- t_{1-alpha/2, J-1} * sqrt(var_corr)``
    and the p-value is two-sided.  ``n_train``/``n_test`` are the (mean) fold sizes.

    Returns a dict: mean, sd, se_corr, se_naive, t, df, p, ci_low, ci_high, J, ratio.
    A zero-variance sample returns t = +/-inf (p = 0) unless the mean is also 0 (t = 0, p = 1).
    """
    d = np.asarray(diffs, dtype=float)
    d = d[~np.isnan(d)]
    J = len(d)
    if J < 2:
        raise ValueError("need at least two paired differences")
    ratio = n_test / n_train
    mean, s2 = float(d.mean()), float(d.var(ddof=1))
    if s2 <= (1e-12 * max(abs(mean), 1e-12)) ** 2:  # numerically constant sample
        s2 = 0.0
    se_corr = float(np.sqrt((1.0 / J + ratio) * s2))
    df = J - 1
    tcrit = float(stats.t.ppf(1 - alpha / 2, df))
    if se_corr > 0:
        t = mean / se_corr
        p = float(2 * stats.t.sf(abs(t), df))
    else:
        t, p = (0.0, 1.0) if mean == 0 else (float(np.sign(mean) * np.inf), 0.0)
    return dict(mean=mean, sd=float(np.sqrt(s2)), se_corr=se_corr, se_naive=float(np.sqrt(s2 / J)),
                t=float(t), df=int(df), p=p, ci_low=mean - tcrit * se_corr, ci_high=mean + tcrit * se_corr,
                J=int(J), ratio=float(ratio))


def _auc_matrix(Y: np.ndarray, P: np.ndarray) -> np.ndarray:
    """Row-wise ROC-AUC for matrices Y, P of shape (B, n) via average ranks (ties handled)."""
    ranks = stats.rankdata(P, axis=1)
    npos = Y.sum(axis=1)
    nneg = Y.shape[1] - npos
    return ((ranks * Y).sum(axis=1) - npos * (npos + 1) / 2) / (npos * nneg)


def _brier_matrix(Y: np.ndarray, P: np.ndarray) -> np.ndarray:
    return ((P - Y) ** 2).mean(axis=1)


def _scalar_metric(name: str) -> Callable:
    table = {
        "roc_auc": lambda y, p: roc_auc_score(y, p),
        "pr_auc": lambda y, p: average_precision_score(y, p),
        "brier": lambda y, p: float(np.mean((p - y) ** 2)),
        "recall_at_spec": lambda y, p: recall_at_specificity(y, p, C.SPEC_FIXED)[0],
        "balanced_accuracy": lambda y, p: metric_suite(y, p)["balanced_accuracy"],
    }
    if name not in table:
        raise ValueError(f"unknown metric {name!r}; use one of {sorted(table)} or a callable f(y, p)")
    return table[name]


def paired_bootstrap(y, p_a, p_b, metric="roc_auc", *, n_boot: int = C.N_BOOT, seed: int = C.SEED_MASTER,
                     eval_mask=None, stratify: bool = True, alpha: float = 0.05) -> dict:
    """Paired percentile bootstrap of ``metric(y, p_a) - metric(y, p_b)`` on pooled OOF predictions.

    Rows (restricted to ``eval_mask`` if given, e.g. E-SCREEN) are resampled with replacement
    ``n_boot`` times; the SAME resampled rows are scored for models A and B, so the
    between-model correlation is preserved (paired design, Efron & Tibshirani 1993).  With
    ``stratify=True`` positives and negatives are resampled separately (fixed n_pos, n_neg),
    which keeps the event count constant - important for E-SCREEN with ~150 events.

    ``metric`` is ``"roc_auc"`` / ``"brier"`` (fully vectorised via ranks / matrix means),
    ``"pr_auc"`` / ``"recall_at_spec"`` / ``"balanced_accuracy"`` (looped) or a callable
    ``f(y, p) -> float``.  The difference is always A - B.

    Returns: ``diff`` (observed on the full evaluation set), ``mean_diff`` (bootstrap mean),
    ``se``, ``ci_low``/``ci_high`` (percentile ``alpha/2`` and ``1-alpha/2``), ``p`` (two-sided
    bootstrap p = min(1, 2 * (min(#{d* <= 0}, #{d* >= 0}) + 1) / (B + 1)); approximate, only
    indicative), ``boot`` (array of B differences), ``n_eval``, ``n_pos``, ``metric_a``, ``metric_b``.
    This captures sampling variability of the evaluation rows only, not training variability
    (that is what the fold-level corrected t adds).
    """
    y, p_a, _ = _clean_inputs(y, p_a)
    p_b = np.asarray(p_b, dtype=float).ravel()
    if len(p_b) != len(y):
        raise ValueError("p_a and p_b must have the length of y")
    sel = np.flatnonzero(_mask(eval_mask, len(y)))
    y, p_a, p_b = y[sel], p_a[sel], p_b[sel]
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    if len(pos) == 0 or len(neg) == 0:
        raise ValueError("evaluation set needs both classes")
    if stratify:
        idx = np.concatenate([rng.choice(pos, (n_boot, len(pos))), rng.choice(neg, (n_boot, len(neg)))], axis=1)
    else:
        idx = rng.integers(0, len(y), (n_boot, len(y)))
    Y = y[idx]
    fn = metric if callable(metric) else _scalar_metric(metric)
    if metric == "roc_auc" or metric == "brier":
        mat = _auc_matrix if metric == "roc_auc" else _brier_matrix
        ba, bb = mat(Y, p_a[idx]), mat(Y, p_b[idx])
    else:
        ba = np.array([fn(Y[b], p_a[idx[b]]) for b in range(n_boot)])
        bb = np.array([fn(Y[b], p_b[idx[b]]) for b in range(n_boot)])
    boot = ba - bb
    boot_ok = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot_ok, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    le, ge = (boot_ok <= 0).sum(), (boot_ok >= 0).sum()
    ma, mb = float(fn(y, p_a)), float(fn(y, p_b))
    return dict(diff=ma - mb, mean_diff=float(boot_ok.mean()), se=float(boot_ok.std(ddof=1)),
                ci_low=float(lo), ci_high=float(hi), p=float(min(1.0, 2 * (min(le, ge) + 1) / (len(boot_ok) + 1))),
                boot=boot, n_boot=int(n_boot), n_eval=int(len(y)), n_pos=int(len(pos)), metric_a=ma, metric_b=mb)


_UP = {"+", "up", "higher", "greater", "positive", "increase"}
_DOWN = {"-", "down", "lower", "less", "negative", "decrease"}


def verdict(ci_low: float, ci_high: float, sesoi: float, direction: str = "+", estimate: float | None = None) -> str:
    """Classify a difference from its confidence interval, the SESOI and the predicted direction.

    SESOI = smallest effect size of interest (``config.SESOI``).  ``direction`` is the
    hypothesised sign of the difference (``"+"``/"higher" or ``"-"``/"lower").  Rules are applied
    in this order (Lakens 2017, equivalence testing / minimum-effect logic):

    1. ``equivalent``    - the whole CI lies inside (-SESOI, +SESOI): any effect is practically negligible.
    2. ``supported``     - the CI excludes 0 on the hypothesised side AND the estimate is at least
                           SESOI in that direction (``estimate`` defaults to the CI midpoint).
    3. ``refuted``       - the CI excludes 0 on the opposite side (and is not equivalent, rule 1).
    4. ``inconclusive``  - everything else (CI contains 0 without being within the equivalence band,
                           or excludes 0 but with an effect that may be below SESOI).

    ``mixed`` is never returned here: it is a hypothesis-level statement obtained by combining
    metric-level verdicts with :func:`combine_verdicts`.
    """
    if ci_low > ci_high:
        raise ValueError("ci_low > ci_high")
    d = str(direction).lower()
    if d in _UP:
        sign = 1
    elif d in _DOWN:
        sign = -1
    else:
        raise ValueError(f"direction must be one of {sorted(_UP | _DOWN)}")
    if sesoi > 0 and ci_low > -sesoi and ci_high < sesoi:
        return "equivalent"
    lo, hi = (ci_low, ci_high) if sign == 1 else (-ci_high, -ci_low)  # re-orient so that "expected" is positive
    est = (ci_low + ci_high) / 2 if estimate is None else estimate
    est = sign * est
    if lo > 0 and est >= sesoi:
        return "supported"
    if hi < 0:
        return "refuted"
    return "inconclusive"


def combine_verdicts(verdicts: Sequence[str]) -> str:
    """Combine metric-level verdicts into one hypothesis-level verdict.

    * all equal -> that verdict;  a ``mixed`` input stays ``mixed``;
    * two or more different *decisive* verdicts (supported / refuted / equivalent) -> ``mixed``
      (e.g. AUC supported but Brier equivalent: the metrics disagree);
    * one decisive verdict plus ``inconclusive`` entries -> ``inconclusive`` (not every metric
      resolves the hypothesis);
    * empty input -> ``inconclusive``.
    """
    vs = [str(v).lower() for v in verdicts]
    bad = set(vs) - set(C.VERDICTS)
    if bad:
        raise ValueError(f"unknown verdicts {bad}")
    s = set(vs)
    if not s:
        return "inconclusive"
    if len(s) == 1:
        return vs[0]
    if "mixed" in s:
        return "mixed"
    decisive = s & {"supported", "refuted", "equivalent"}
    if len(decisive) >= 2:
        return "mixed"
    return "inconclusive"


# =============================================================================
# 5. Resampling diagnostics: coefficient bootstrap and permutation null
# =============================================================================
CoefBootstrap = namedtuple("CoefBootstrap", ["coefs", "summary"])


def _feature_names(model, X) -> list[str]:
    try:
        return [str(s) for s in model[:-1].get_feature_names_out()]
    except Exception:  # noqa: BLE001 - single-step pipeline or estimator without names
        pass
    if hasattr(X, "columns"):
        return [str(c) for c in X.columns]
    return [f"x{i}" for i in range(np.asarray(X).shape[1])]


def _final_coef(model) -> np.ndarray:
    est = model[-1] if hasattr(model, "steps") else model
    if not hasattr(est, "coef_"):
        raise TypeError(f"{type(est).__name__} has no coef_ (coef_bootstrap needs a linear model)")
    return np.asarray(est.coef_, dtype=float).ravel()


def _fit_coef(make_pipe, X, y, idx, fit_params, n) -> tuple[list[str], np.ndarray]:
    model = clone(make_pipe())
    model.fit(_take(X, idx), np.asarray(y)[idx], **_slice_fit_params(fit_params, idx, n))
    return _feature_names(model, X), _final_coef(model)


def coef_bootstrap(make_pipe: Callable, X, y, *, n_boot: int = C.N_BOOT_COEF, seed: int = C.SEED_MASTER,
                   fit_params: dict | None = None, n_jobs: int = 1, alpha: float = 0.05) -> CoefBootstrap:
    """Nonparametric bootstrap of the coefficients of a linear pipeline (stability diagnostic).

    Each of ``n_boot`` replicates draws n rows with replacement (``np.random.default_rng(seed)``),
    refits the WHOLE pipeline (imputation, scaling, encoding, model) on the resample and records
    the coefficients of the final estimator under the feature names given by
    ``pipeline[:-1].get_feature_names_out()``.  Columns absent in a resample (rare dummy levels)
    are NaN and ignored in the summaries.  ``fit_params`` (e.g. sample weights) are sliced to the
    resampled rows.  Efron & Tibshirani (1993), ch. 6.

    Returns ``CoefBootstrap(coefs, summary)``:

    * ``coefs``   - DataFrame (n_boot x n_features) of coefficients;
    * ``summary`` - DataFrame indexed by feature with ``coef`` (full-data fit), ``mean``, ``sd``
      (bootstrap standard error), ``q_low``/``q_high`` (percentile CI), ``sign_flip_rate`` (share
      of replicates whose sign differs from the full-data coefficient; 0 if that is exactly 0),
      ``ci_excludes_0`` and ``n_valid``.

    A large ``sd`` ratio between arms (``config.SESOI['coef_sd_ratio']`` = 2) or a high
    ``sign_flip_rate`` indicates collinearity-driven instability.  Not a hypothesis test.
    """
    from joblib import Parallel, delayed

    n = len(y)
    names, full = _fit_coef(make_pipe, X, y, np.arange(n), fit_params, n)
    idx = np.random.default_rng(seed).integers(0, n, (n_boot, n))
    y_arr = np.asarray(y)

    def one(b):
        if len(np.unique(y_arr[idx[b]])) < 2:
            return None
        nm, co = _fit_coef(make_pipe, X, y, idx[b], fit_params, n)
        return pd.Series(co, index=nm).reindex(names).to_numpy()

    rows = Parallel(n_jobs=n_jobs)(delayed(one)(b) for b in range(n_boot)) if n_jobs != 1 else [one(b) for b in range(n_boot)]
    mat = np.vstack([r for r in rows if r is not None])
    coefs = pd.DataFrame(mat, columns=names)
    sign = np.sign(full)
    flips = ((np.sign(mat) != sign) & (sign != 0)).sum(axis=0) / np.maximum((~np.isnan(mat)).sum(axis=0), 1)
    lo, hi = np.nanpercentile(mat, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0)
    summary = pd.DataFrame({
        "coef": full, "mean": np.nanmean(mat, axis=0), "sd": np.nanstd(mat, axis=0, ddof=1),
        "q_low": lo, "q_high": hi, "sign_flip_rate": flips,
        "ci_excludes_0": (lo > 0) | (hi < 0), "n_valid": (~np.isnan(mat)).sum(axis=0),
    }, index=pd.Index(names, name="feature"))
    return CoefBootstrap(coefs, summary)


def _mean_cv_auc(make_pipe, X, y, folds, fit_params, y_score=None) -> float:
    """Mean over folds of the per-fold ROC-AUC (labels ``y_score`` used for scoring, default ``y``)."""
    n = len(y)
    y = np.asarray(y)
    ys = y if y_score is None else np.asarray(y_score)
    aucs = []
    for tr, te in folds:
        model = clone(make_pipe())
        model.fit(_take(X, tr), y[tr], **_slice_fit_params(fit_params, tr, n))
        aucs.append(roc_auc_score(ys[te], _positive_proba(model, _take(X, te))))
    return float(np.mean(aucs))


def permutation_auc(make_pipe: Callable, X, y, folds: Sequence, *, n_perm: int = C.N_PERM,
                    seed: int = C.SEED_MASTER, fit_params: dict | None = None, n_jobs: int = 1) -> dict:
    """Label-permutation null distribution of the mean cross-validated ROC-AUC (negative control).

    Semantics follow ``sklearn.model_selection.permutation_test_score`` (Ojala & Garriga 2010):
    the *observed* statistic is the mean over all folds of the per-fold AUC; each of ``n_perm``
    replicates permutes ``y`` completely (training AND scoring labels, features and sample
    weights stay with their rows), refits on the SAME folds and records the mean per-fold AUC.
    Under H0 (no feature-label association, no procedural leakage) the null is centred on 0.5;
    a null mean outside [0.495, 0.505] signals a procedural problem (S9 acceptance criterion).

    p-value = (C + 1) / (n_perm + 1) with C = #{null >= observed} (Phipson & Smyth 2010: never 0).

    Returns: ``observed``, ``null`` (array), ``null_mean``, ``null_sd``, ``p_value``, ``n_perm``,
    ``n_ge`` (= C).  Cost: ``n_perm`` x ``len(folds)`` model fits.
    """
    from joblib import Parallel, delayed

    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    perms = [rng.permutation(len(y)) for _ in range(n_perm)]
    observed = _mean_cv_auc(make_pipe, X, y, folds, fit_params)

    def one(perm):
        yp = y[perm]
        return _mean_cv_auc(make_pipe, X, yp, folds, fit_params, y_score=yp)

    null = np.array(Parallel(n_jobs=n_jobs)(delayed(one)(p) for p in perms) if n_jobs != 1 else [one(p) for p in perms])
    n_ge = int((null >= observed).sum())
    return dict(observed=observed, null=null, null_mean=float(null.mean()), null_sd=float(null.std(ddof=1)) if n_perm > 1 else float("nan"),
                p_value=(n_ge + 1) / (n_perm + 1), n_perm=int(n_perm), n_ge=n_ge)
