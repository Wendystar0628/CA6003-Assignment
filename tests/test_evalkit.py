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
