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
    "combine_verdicts", "coef_bootstrap", "permutation_auc",
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
