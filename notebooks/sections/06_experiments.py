# %% [markdown]
# # §7 Experiments and Block Ablation (Stage S7)
#
# Here the model is used as a **measuring instrument** for the data-preparation decisions of §6. One
# estimator (L2 logistic regression with C frozen) is applied to every arm on the same stored folds, and
# each block is judged against its locked hypothesis with paired intervals. Results are reported on two
# populations with equal weight:
#
# * **E-ALL** – everyone in the training part, label `L_comb` (84 % of the positives already know they have
#   diabetes);
# * **E-SCREEN** – people *not* told they have diabetes, positive = HbA1c ≥ 6.5 % (the screening use case).
#
# The 20 % hold-out is **not** evaluated here; its single use belongs to S9 after `exp-freeze`.
#
# Contents: 1 splits · 2 data-justified model choice · 3 C0 · 4 arms run · 5 leak gate · 6 baselines on
# E-SCREEN · 7 cumulative path · 8 leave-one-block-out · 9 E-ALL vs E-SCREEN · 10 PR and calibration ·
# 11 coefficient stability · 12 verdicts · 13 storage

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import json, time, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from scipy import stats

from src import nhanes_io as io, labels as L, prep as P, evalkit as ek

pd.set_option("display.width", 170, "display.max_columns", 30, "display.max_colwidth", 70)
OUT = C.RESULTS_DIR / "S7"
OUT.mkdir(parents=True, exist_ok=True)
N_JOBS = min(12, max(1, (__import__("os").cpu_count() or 2) - 2))
S7 = {"mode": C.NB_MODE, "cv": f"{C.CV_SPLITS}x{C.CV_REPEATS}", "n_boot": C.N_BOOT, "n_boot_coef": C.N_BOOT_COEF}
T_START = time.time()
print(f"mode {C.NB_MODE}: {C.CV_SPLITS}x{C.CV_REPEATS} CV, B = {C.N_BOOT}, coefficient bootstrap B = {C.N_BOOT_COEF}, {N_JOBS} workers")

# %% [markdown]
# ## 1 Splits
# **Why.** Every arm must be scored on identical folds, otherwise paired differences mix model effects with
# split noise. The hold-out (label × race stratified, 20 %) and the repeated stratified folds are generated
# once by `evalkit`, stored with SHA-256 hashes and re-verified on every run. Folds are stratified on the
# four 3 × 3 strata (uncontrolled / controlled / undiagnosed / non-diabetic) so that each fold holds a fair
# share of the 152 undiagnosed cases that define E-SCREEN.

# %%
raw = P.raw_cohort()
clean = L.add_labels(io.build_cohort())
assert (raw["SEQN"].to_numpy() == clean["SEQN"].to_numpy()).all()
tr, te = ek.make_holdout(clean)
raw_tr = raw.iloc[tr].reset_index(drop=True)
cl = clean.iloc[tr].reset_index(drop=True)
X = {1: P.raw_feature_frame(raw_tr, 1), 2: P.raw_feature_frame(raw_tr, 2)}
y = cl["L_comb"].to_numpy()
esc = cl["in_escreen"].eq(1).to_numpy()
y_esc = cl["y_escreen"].fillna(0).astype(int).to_numpy()   # only scored inside the E-SCREEN mask
strat = cl["stratum_3x3"].astype(str).to_numpy()
folds = ek.make_folds(y, strat)
n = len(y)
n_test_fold = n / C.CV_SPLITS
n_train_fold = n - n_test_fold
hold = json.loads((C.RESULTS_DIR / "splits" / "holdout.json").read_text(encoding="utf-8"))
print(f"training part {n:,} rows ({y.sum()} L_comb positives); hold-out {len(te):,} rows - not evaluated in S7")
print(f"E-SCREEN in training part: {esc.sum():,} rows, {y_esc[esc].sum()} positives (HbA1c >= 6.5, not diagnosed)")
print(f"folds: {len(folds)} = {folds.n_splits} x {folds.n_repeats}, hash {folds.hash[:16]}..., file {folds.path.name}")
print(f"hold-out test SEQN SHA-256 {hold['sha256_test_seqn'][:16]}...")
per_fold = pd.DataFrame([{"fold": i, "n_test": len(t), "pos_eall": int(y[t].sum()), "pos_escreen": int(y_esc[t][esc[t]].sum())}
                         for i, (_, t) in enumerate(folds)])
print(per_fold.describe().loc[["min", "mean", "max"], ["n_test", "pos_eall", "pos_escreen"]].round(1).to_string())
S7["splits"] = dict(n_train=n, n_holdout=len(te), n_pos_eall=int(y.sum()), n_escreen=int(esc.sum()),
                    n_pos_escreen=int(y_esc[esc].sum()), folds_hash=folds.hash, folds_file=folds.path.name,
                    holdout_sha256=hold["sha256_test_seqn"], pos_escreen_per_fold_min=int(per_fold["pos_escreen"].min()))

# %% [markdown]
# **So what.** Each fold holds about 155 E-ALL positives but only about 24 E-SCREEN positives. That is why the
# protocol scores E-SCREEN on the pooled out-of-fold vector (paired bootstrap), not fold by fold, and why most
# E-SCREEN verdicts are expected to be inconclusive. The hold-out hash is printed so that S9 can prove it was
# untouched.

# %% [markdown]
# ## 2 Data-justified model choice
# **Why.** Only basic interpretable models are allowed (HR3). Within that constraint each modelling choice
# is tied to a diagnostic number from S4 (the DAJ table) – and the reason for *not* choosing an alternative.

# %%
S4dir = C.RESULTS_DIR / "S4"
lin = pd.read_csv(S4dir / "linearity_tests.csv")
inter = pd.read_csv(S4dir / "interaction_tests.csv")
daj = pd.read_csv(S4dir / "daj_table.csv")
vif4 = pd.read_csv(S4dir / "vif_table.csv")
print("S4 RCS linearity tests (4 knots vs linear, df 2):")
print(lin[["label", "n", "n_events", "chi2", "p", "nonlinear"]].round(4).to_string(index=False))
print("\nS4 interaction tests (primary spec A):")
print(inter[inter["spec"] == "A_primary"][["term", "chi2", "df", "p", "verdict"]].round(4).to_string(index=False))
sx = inter[inter["term"] == "sex_x_bmi"].set_index("spec")["p"].round(3).to_dict()
epv_den = {t: P.build_pipeline(P.ARMS["S"], t)[:-1].fit_transform(X[t]).shape[1] for t in (1, 2)}
epv = {t: round(y.sum() / k, 1) for t, k in epv_den.items()}
print(f"\nsex x BMI by spec: {sx}")
print(f"events per parameter in S: Tier 1 {y.sum()}/{epv_den[1]} = {epv[1]}, Tier 2 {y.sum()}/{epv_den[2]} = {epv[2]}")
print(f"imbalance: prevalence {y.mean():.3f} in the training part")
choice = pd.DataFrame([
    ("non-linearity", "age chi2 57.6, BMI 11.6, HDL 18.5, TC 41.8 (p < 0.01)", "L2 logistic regression + B-spline basis (P13)", "categorised bands (arbitrary cut-points, information loss); GAM / boosting (outside HR3)"),
    ("interactions", "race x BMI p 0.39, Asian x BMI p 0.93 (MDE 0.70 log-OR)", "no interaction terms; Asian BMI bias treated as a measurement issue (P14, S8)", "interaction terms add variance without detectable gain"),
    ("collinearity", "weight VIF 95.7, BMI 97.6; 6 BP readings 8.8-11.7", "aggregate + in-fold VIF pruning (P04/P05), L2 as second defence", "L1 (unstable selection among collinear columns, sensitivity only)"),
    ("sample size", f"{y.sum()} events / {epv_den[1]} parameters (EPV {epv[1]})", "unpenalised fit would be acceptable; mild L2 (C0) chosen by inner CV", "deep trees / ensembles (overfit, HR3)"),
    ("imbalance", f"prevalence {y.mean():.1%}", "no resampling; class_weight tested as block B6a", "SMOTE (breaks calibration and the survey design)"),
    ("thresholds / leakage", "clinical cut-points and leakage need inspection", "depth-3 tree (min leaf 50) as a probe only", "tree as main model (step functions, unstable)"),
], columns=["diagnostic", "evidence (S4 / S7)", "decision", "why not the alternative"])
choice.to_csv(OUT / "model_choice.csv", index=False)
print(choice.to_string(index=False))
S7["model_choice"] = dict(linearity=lin.set_index("label")[["chi2", "p"]].round(4).to_dict("index"),
                          sex_x_bmi_p_by_spec=sx, epv=epv, n_params=epv_den)

# %% [markdown]
# **So what.** Age, BMI and both lipids bend significantly, so the main model is a GLM with spline terms rather than
# a linear logit; the linear version stays as the ablation arm *S-linear*. Race × BMI and Asian × BMI are not
# detected (underpowered – "not detected" is not "absent"). One caveat is reported, not hidden: S4 found
# sex × BMI significant in its primary specification (p printed above) but not in the minimal or spline
# specifications; because the result depends on the specification, no interaction term is added and the point is
# listed as a limitation. With about 18 events per parameter, overfitting risk is modest; L2 mainly stabilises
# correlated anthropometrics. Note also a documented difference from the S4 DAJ wording: S4 suggested dropping
# weight, height, hip and arm a priori, while the locked S6 design applies an in-fold VIF > 10 rule, which removes
# only weight (§6.5); hip and arm therefore stay in S.

# %% [markdown]
# ## 3 Regularisation strength C0
# **Why.** HR2 requires the *same model* for minimal and systematic arms. C is therefore chosen once – by
# `LogisticRegressionCV(Cs=[0.01, 0.1, 1, 10])`, inner 5-fold ROC-AUC, on the S arm of Tier 1 with its class and
# survey weights – and then frozen for every arm. Choosing it on S favours S slightly (the other arms do not get
# their own tuning); M0 with its own C is an S9 sensitivity.

# %%
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold

cfgS = P.ARMS["S"]
design = P.build_pipeline(cfgS, 1)[:-1].fit_transform(X[1])
ylab = P.training_label(raw_tr, cfgS)
inner = StratifiedKFold(5, shuffle=True, random_state=ek.derive_seed(C.SEED_MASTER, "S7", "C0"))
with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    lrcv = LogisticRegressionCV(Cs=[0.01, 0.1, 1, 10], cv=inner, scoring="roc_auc", max_iter=C.LR_MAX_ITER,
                                class_weight="balanced", l1_ratios=(0.0,), use_legacy_attributes=False)
    lrcv.fit(design, ylab, sample_weight=P.survey_weights(raw_tr))
scores = np.asarray(lrcv.scores_).reshape(5, -1)   # (inner folds, Cs); l1_ratio fixed at 0 (pure L2)
C0 = float(np.ravel(lrcv.C_)[0])
cv_auc = pd.Series(scores.mean(axis=0).ravel()[:4], index=[0.01, 0.1, 1, 10]).round(4)
print("inner-CV ROC-AUC by C:"); print(cv_auc.to_string())
print(f"C0 = {C0} (frozen for all arms and tiers)")
S7["C0"] = dict(C0=C0, inner_cv_auc=cv_auc.to_dict())

# %% [markdown]
# **So what.** The inner-CV AUC is almost flat across C (differences in the third decimal), so the choice of C is not a
# lever for the results below; C0 is used for every arm. The flatness also limits the optimistic bias of tuning on S.
