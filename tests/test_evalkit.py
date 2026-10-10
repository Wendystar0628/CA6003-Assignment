"""Plain-assert tests for src/evalkit.py.

Run from the repository root:  .venv/Scripts/python tests/test_evalkit.py
(no pytest needed; every ``test_*`` function is called by the runner at the bottom).
"""
from __future__ import annotations

import sys
import tempfile
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.dummy import DummyClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from src import config as C  # noqa: E402
from src import evalkit as ek  # noqa: E402


# ----------------------------------------------------------------------------- helpers
def synth(n=1200, p=4, seed=0, signal=1.0):
    """Synthetic binary data: logistic signal on the first two columns, prevalence ~ 0.2."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, p))
    eta = -1.6 + signal * (1.2 * X[:, 0] + 0.8 * X[:, 1])
    y = (rng.random(n) < 1 / (1 + np.exp(-eta))).astype(int)
    return pd.DataFrame(X, columns=[f"x{i}" for i in range(p)]), y


def lr_pipe():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=C.LR_MAX_ITER))


def cohort_frame(n=500, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "SEQN": np.arange(130000, 130000 + n),
        "L_comb": (rng.random(n) < 0.17).astype(int),
        "race": rng.choice(["NHW", "NHB", "Hisp", "NHA", "Other"], n, p=[.4, .2, .2, .12, .08]),
    })


# ----------------------------------------------------------------------------- splits
def test_holdout_roundtrip():
    coh = cohort_frame()
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "splits" / "holdout.json"
        tr, te = ek.make_holdout(coh, seed=7, path=f)
        assert f.exists()
        assert len(tr) + len(te) == len(coh) and not set(tr) & set(te)
        assert abs(len(te) / len(coh) - 0.2) < 0.01
        # stratification: label x race proportions preserved in the test part
        key = coh.L_comb.astype(str) + coh.race
        share_all = key.value_counts(normalize=True)
        share_te = key.iloc[te].value_counts(normalize=True).reindex(share_all.index).fillna(0)
        assert (share_all - share_te).abs().max() < 0.02
        # second call loads, does not re-split (even with another seed -> warning only)
        tr2, te2 = ek.make_holdout(coh, seed=7, path=f)
        assert (tr == tr2).all() and (te == te2).all()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _, te3 = ek.make_holdout(coh, seed=8, path=f)
            assert any("ignored" in str(x.message) for x in w)
        assert (te == te3).all()
        # hash is the SHA-256 of the sorted test SEQNs
        import hashlib, json
        meta = json.loads(f.read_text())
        want = hashlib.sha256("\n".join(map(str, sorted(coh.SEQN.iloc[te]))).encode()).hexdigest()
        assert meta["sha256_test_seqn"] == want
        # tampering with the file is detected
        meta["test_seqn"][0] += 1
        f.write_text(json.dumps(meta))
        try:
            ek.make_holdout(coh, seed=7, path=f)
            raise AssertionError("tampering not detected")
        except ValueError:
            pass
        # a changed cohort is detected
        f.unlink()
        ek.make_holdout(coh, seed=7, path=f)
        try:
            ek.make_holdout(coh.iloc[:-5], seed=7, path=f)
            raise AssertionError("cohort change not detected")
        except ValueError:
            pass


def test_holdout_deterministic():
    coh = cohort_frame()
    with tempfile.TemporaryDirectory() as d:
        a = ek.make_holdout(coh, seed=3, path=Path(d) / "a.json")
        b = ek.make_holdout(coh, seed=3, path=Path(d) / "b.json")
        c = ek.make_holdout(coh, seed=4, path=Path(d) / "c.json")
    assert (a[1] == b[1]).all() and not (a[1] == c[1]).all()


def test_folds_persist_and_partition():
    X, y = synth(600)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "folds_FAST.npz"
        folds = ek.make_folds(y, y, n_splits=5, n_repeats=2, seed=11, path=f)
        assert f.exists() and len(folds) == 10 and folds.n_splits == 5
        for r in range(2):  # each row in exactly one test fold per repeat
            tests = np.concatenate([folds[r * 5 + k][1] for k in range(5)])
            assert np.array_equal(np.sort(tests), np.arange(len(y)))
        for tr, te in folds:
            assert not set(tr) & set(te) and len(tr) + len(te) == len(y)
            assert abs(y[te].mean() - y.mean()) < 0.03  # stratified
        again = ek.make_folds(y, y, n_splits=5, n_repeats=2, seed=11, path=f)
        assert again.hash == folds.hash
        assert all((a[1] == b[1]).all() for a, b in zip(folds, again))
        for bad in (dict(n_splits=4, n_repeats=2, seed=11), dict(n_splits=5, n_repeats=2, seed=12)):
            try:
                ek.make_folds(y, y, path=f, **bad)
                raise AssertionError("parameter mismatch not detected")
            except ValueError:
                pass
        try:
            ek.make_folds(1 - y, y, n_splits=5, n_repeats=2, seed=11, path=f)
            raise AssertionError("different y not detected")
        except ValueError:
            pass


# ----------------------------------------------------------------------------- metrics
def test_dummy_auc_half():
    X, y = synth(800)
    folds = ek.make_folds(y, y, n_splits=5, n_repeats=2, seed=1, path=Path(tempfile.mkdtemp()) / "f.npz")
    oof = ek.cv_predict(lambda: DummyClassifier(strategy="prior"), X, y, folds)
    # a constant score has AUC exactly 0.5 (all ties) and PR-AUC = prevalence
    m = ek.metric_suite(y, np.full(len(y), 0.2))
    assert m["roc_auc"] == 0.5, m["roc_auc"]
    assert abs(m["pr_auc"] - y.mean()) < 1e-12
    assert np.isnan(m["cal_slope"])                     # constant score: slope undefined
    # per-fold: the prior-only model is constant within each fold -> AUC exactly 0.5
    # (the pooled OOF vector is NOT constant: fold priors differ slightly, giving AUC ~ 0.5 - eps)
    fm = ek.fold_metrics(oof, y)
    assert (fm["roc_auc"] == 0.5).all() and len(fm) == 10


def test_perfect_predictor():
    rng = np.random.default_rng(0)
    y = (rng.random(400) < 0.3).astype(int)
    p = np.where(y == 1, 0.9, 0.1)
    m = ek.metric_suite(y, p)
    assert m["roc_auc"] == 1.0 and m["pr_auc"] == 1.0
    assert m["recall_at_spec"] == 1.0 and m["balanced_accuracy"] == 1.0
    assert abs(m["brier"] - 0.01) < 1e-12
    assert abs(m["prevalence"] - y.mean()) < 1e-12 and m["n"] == 400


def test_metric_suite_matches_sklearn_and_calibration():
    X, y = synth(2000, seed=3)
    folds = ek.make_folds(y, y, n_splits=5, n_repeats=1, seed=1, path=Path(tempfile.mkdtemp()) / "f.npz")
    oof = ek.cv_predict(lr_pipe, X, y, folds)
    p = oof.sort_values("row").prob.to_numpy()
    m = ek.metric_suite(y, p)
    assert abs(m["roc_auc"] - roc_auc_score(y, p)) < 1e-12
    assert abs(m["pr_auc"] - average_precision_score(y, p)) < 1e-12
    assert abs(m["brier"] - brier_score_loss(y, p)) < 1e-12
    # a correctly specified logistic model, evaluated out of fold, is well calibrated
    assert 0.85 < m["cal_slope"] < 1.15 and abs(m["cal_intercept"]) < 0.2 and abs(m["cal_citl"]) < 0.2
    # overconfident predictions -> slope < 1; underconfident -> slope > 1
    lp = np.log(p / (1 - p))
    over = 1 / (1 + np.exp(-3 * lp))
    under = 1 / (1 + np.exp(-0.4 * lp))
    assert ek.metric_suite(y, over)["cal_slope"] < 0.5 and ek.metric_suite(y, under)["cal_slope"] > 1.5
    assert abs(ek.metric_suite(y, over)["cal_slope"] - m["cal_slope"] / 3) < 0.12
    # explicit threshold is used verbatim
    mt = ek.metric_suite(y, p, threshold=0.5)
    assert mt["threshold"] == 0.5
    pred = p >= 0.5
    assert abs(mt["balanced_accuracy"] - 0.5 * (pred[y == 1].mean() + (~pred[y == 0]).mean())) < 1e-12
    # weights: all-ones weights reproduce the unweighted metrics
    mw = ek.metric_suite(y, p, w=np.ones(len(y)))
    for k in ("roc_auc", "pr_auc", "brier", "recall_at_spec", "balanced_accuracy"):
        assert abs(mw[k] - m[k]) < 1e-9, k


def test_recall_at_specificity_toy():
    # 10 negatives with scores .01..0.10, 4 positives
    y = np.array([0] * 10 + [1] * 4)
    p = np.array([.01, .02, .03, .04, .05, .06, .07, .08, .09, .10, .05, .085, .5, .9])
    rec, thr = ek.recall_at_specificity(y, p, 0.80)
    # k = 8 -> v_8 = .08 ; thr = smallest score > .08 = .085 ; positives >= .085: .085,.5,.9
    assert thr == 0.085 and abs(rec - 0.75) < 1e-12
    assert (p[y == 0] < thr).mean() >= 0.80
    rec90, thr90 = ek.recall_at_specificity(y, p, 0.90)       # k = 9 -> v = .09 -> thr = .10
    assert thr90 == 0.10 and abs(rec90 - 0.5) < 1e-12
    # negative subset: only the 5 lowest negatives define the threshold
    mask = np.r_[np.ones(5, bool), np.zeros(9, bool)]
    rec_s, thr_s = ek.recall_at_specificity(y, p, 0.80, neg_mask=mask)  # k=4 -> v=.04 -> thr=.05
    assert thr_s == 0.05 and rec_s == 1.0
    # ties are handled conservatively (specificity >= spec)
    y2 = np.array([0] * 10 + [1] * 2)
    p2 = np.array([.1] * 10 + [.1, .9])
    r2, t2 = ek.recall_at_specificity(y2, p2, 0.8)
    assert t2 == 0.9 and r2 == 0.5
    # nothing above v_k -> infinite threshold, zero recall
    r3, t3 = ek.recall_at_specificity(np.array([0, 0, 1]), np.array([.5, .6, .1]), 0.8)
    assert np.isinf(t3) and r3 == 0.0
    # weighted: heavy weight on the top negative moves the threshold past it
    w = np.r_[np.ones(9), 100, np.ones(4)]
    _, thr_w = ek.recall_at_specificity(y, p, 0.80, w=w)
    assert thr_w == 0.5


def test_cv_predict_sample_weight():
    X, y = synth(900, seed=5)
    folds = ek.make_folds(y, y, n_splits=3, n_repeats=2, seed=2, path=Path(tempfile.mkdtemp()) / "f.npz")
    mk = lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    base = ek.cv_predict(mk, X, y, folds)
    assert len(base) == 2 * len(y) and set(base.columns) == {"repeat", "fold", "row", "prob"}
    assert base.groupby(["repeat", "row"]).size().max() == 1       # one prediction per row per repeat
    ones = ek.cv_predict(mk, X, y, folds, fit_params={"logisticregression__sample_weight": np.ones(len(y))})
    assert np.allclose(base.prob, ones.prob, atol=1e-8)
    # weights are sliced per fold: reproduce fold 0 manually with non-trivial weights
    w = np.where(y == 1, 5.0, 1.0)
    ww = ek.cv_predict(mk, X, y, folds, fit_params={"logisticregression__sample_weight": w})
    tr, te = folds[0]
    manual = mk().fit(X.iloc[tr], y[tr], logisticregression__sample_weight=w[tr]).predict_proba(X.iloc[te])[:, 1]
    got = ww[(ww.repeat == 0) & (ww.fold == 0)].sort_values("row")
    assert np.array_equal(got.row.to_numpy(), np.sort(te)) and np.allclose(got.prob.to_numpy(), manual[np.argsort(te)])
    assert ww.prob.mean() > base.prob.mean() + 0.05                # up-weighting positives raises probabilities
    # a fresh estimator per fold: factory is called once per fold
    calls = []
    ek.cv_predict(lambda: (calls.append(1), mk())[1], X, y, folds)
    assert len(calls) == len(folds)
    # numpy input and metadata-free fold lists work too
    plain = [(tr, te) for tr, te in folds]
    again = ek.cv_predict(mk, X.to_numpy(), y, plain)
    assert (again.repeat.to_numpy() == base.repeat.to_numpy()).all() and np.allclose(again.prob, base.prob)


def test_fold_metrics_eval_mask_and_thresholds():
    X, y = synth(1500, seed=9)
    folds = ek.make_folds(y, y, n_splits=5, n_repeats=2, seed=3, path=Path(tempfile.mkdtemp()) / "f.npz")
    oof = ek.cv_predict(lr_pipe, X, y, folds)
    fm = ek.fold_metrics(oof, y)
    assert list(fm[["repeat", "fold"]].itertuples(index=False, name=None)) == [(r, f) for r in range(2) for f in range(5)]
    assert fm["n"].sum() == 2 * len(y)
    mask = X["x2"].to_numpy() > 0                                  # arbitrary sub-population
    fms = ek.fold_metrics(oof, y, eval_mask=mask)
    assert fms["n"].sum() == 2 * mask.sum()
    # repeat-level pooled metrics
    rm = ek.repeat_metrics(oof, y)
    assert len(rm) == 2 and (rm["n"] == len(y)).all()
    # honest threshold (other folds) gives balanced accuracy <= optimistic same-data Youden on average
    same = ek.fold_metrics(oof, y, threshold="same")
    assert fm["balanced_accuracy"].mean() <= same["balanced_accuracy"].mean() + 1e-12
    d = ek.paired_fold_diffs(fm, same, "roc_auc")
    assert d.shape == (10,) and np.allclose(d, 0)


# ----------------------------------------------------------------------------- runner
def main():
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    t0 = time.time()
    for name, fn in tests:
        t = time.time()
        fn()
        print(f"  ok  {name}  ({time.time() - t:.1f}s)")
    print(f"OK - {len(tests)} tests passed in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
