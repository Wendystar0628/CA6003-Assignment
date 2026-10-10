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
