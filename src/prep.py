"""Toggleable data-preparation steps, arms and reporting blocks (stage S6).

Contract (docs/architecture.md §3) - signatures are binding:

    STEPS = ("P01", ..., "P14")
    BLOCKS = {"B1": ["P01","P02"], "B2": ["P03"], "B3": ["P04","P05"], "B4": ["P06","P07"],
              "B5": ["P08","P09","P10","P13"], "B6a": ["P11"], "B6b": ["P12"]}
    ARMS: dict[str, dict[str, bool]]
    raw_feature_frame(cohort, tier) -> DataFrame
    build_pipeline(cfg, tier, model="lr") -> sklearn.pipeline.Pipeline
    model_kwargs(cfg) -> dict

Design
------
* The pipeline input is the RAW cohort (``raw_cohort()``: XPT artefact NOT repaired, NO
  sentinel recode), restricted by :func:`raw_feature_frame` to every column a naive analyst
  would feed to a model (everything except the id, design/weight columns and the two columns
  that define the label, DIQ010 and LBXGH).  Every preparation decision therefore happens
  INSIDE the pipeline and is refitted in each training fold (scikit-learn "common pitfalls").
* Each step P01-P14 is wrapped in :class:`Toggle` (disabled = identity) or :class:`Switch`
  (disabled = the naive M0 behaviour, enabled = the systematic choice).  Only two steps need a
  Switch, because M0 itself already does *something* there: P02 (M0 = blanket recode of
  7/9/77/99/... in every numeric column) and P10 (M0 = plain one-hot encoding of every
  low-cardinality column).  Hence ``cfg`` all-False reproduces the naive arm M0 exactly
  (asserted in notebook 05 against an independently written naive pipeline).
* Steps P01-P04, P06, P07, P14 are stateless (never look at y and learn nothing from the
  training data); P05, P08, P09, P10, P13 and the base imputer are fitted in-fold on X only;
  no step reads y (asserted with a random y in notebook 05).
* P11 (class weights) and P12 (survey weights) act on the estimator, see :func:`model_kwargs`
  and :func:`fit_params`.
* The TRAINING label of an arm is built from the arm's own sentinel handling
  (:func:`training_label`): with P02 off the blanket recode wipes HbA1c values 7.0 and 9.0 before
  the label is formed, exactly as a naive analyst would.  Evaluation always uses the frozen
  L_comb (``labels.add_labels`` on the per-variable cohort).

Step catalogue (block in brackets)
----------------------------------
P01 [B1] xpt_zero_fix      x.mask(|x| < 1e-10 & notna, 0)  (never ``where``: NaN stays NaN)
P02 [B1] sentinel_by_var   codebook refusal/don't-know codes per variable (off: blanket recode)
P03 [B2] admissibility     keep only spec columns admissible for the tier (S1 availability rule)
P04 [B3] aggregate         mean of the 3 SBP / DBP / pulse readings; physical activity as weekly
                           minutes (frequency x unit x duration; 0 when frequency is 0 - the
                           duration items are skipped by design, a structural not a random gap)
P05 [B3] prune             iterative VIF > 10 pruning, fitted in-fold; BMI and waist (or WHtR) kept
P06 [B4] missing_indicator ``<col>_missing`` for MNAR-suspect columns (MNAR_SUSPECT)
P07 [B4] topcode_flag      age_top (RIDAGEYR == 80), pir_top (INDFMPIR == 5)
P08 [B5] yeo_johnson       Yeo-Johnson on continuous columns with |skew| > 1 in the training fold
P09 [B5] scale             StandardScaler on all non-categorical columns
P10 [B5] rare_categories   OneHotEncoder(min_frequency=0.02, handle_unknown="infrequent_if_exist")
P11 [B6a] class_weight     class_weight="balanced"
P12 [B6b] survey_weight    sample_weight = WTPH2YR normalised to mean 1
P13 [B5] splines           SplineTransformer(**config.SPLINE_KW) for age, BMI (+ HDL, TC in Tier 2)
P14 [--] whtr              WHtR = BMXWAIST / BMXHT replaces waist (default off; S8 / L4 arm)
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PowerTransformer, SplineTransformer, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from . import config as C
from . import nhanes_io as io

# =============================================================================
# constants
# =============================================================================
STEPS = tuple(f"P{i:02d}" for i in range(1, 15))
BLOCKS = {"B1": ["P01", "P02"], "B2": ["P03"], "B3": ["P04", "P05"], "B4": ["P06", "P07"],
          "B5": ["P08", "P09", "P10", "P13"], "B6a": ["P11"], "B6b": ["P12"]}
STEP_NAMES = {
    "P01": "xpt_zero_fix", "P02": "sentinel_by_var", "P03": "admissibility", "P04": "aggregate",
    "P05": "prune", "P06": "missing_indicator", "P07": "topcode_flag", "P08": "yeo_johnson",
    "P09": "scale", "P10": "rare_categories", "P11": "class_weight", "P12": "survey_weight",
    "P13": "splines", "P14": "whtr",
}
STEP_BLOCK = {s: b for b, ss in BLOCKS.items() for s in ss} | {"P14": "P14"}
#: arm-level option outside P01-P14: drop the care-contact items (T1-minus-care arm)
OPTIONS = ("NO_CARE",)
CARE_ITEMS = ("BPQ020", "BPQ080")

#: columns removed from the naive frame: id, design, weights, label-defining columns
NON_FEATURES = ("SEQN", C.STRATA, C.PSU, C.WEIGHT_INTERVIEW, C.WEIGHT_MEC, C.WEIGHT_PHLEB,
                C.WEIGHT_FASTING, "DIQ010", "LBXGH")
#: S1 availability rule, explicit list (asserted against the spec in notebook 05)
P03_EXCLUDED = ("LBXGLU", "LBXGH", "DIQ050", "DIQ070", "DID040", "DID060", "DIQ160", "DIQ180",
                "RIDRETH3", "HIQ011", "HUQ030")
TIER2_ONLY = ("LBXTC", "LBDHDD")
SPLINE_COLS = {1: ("RIDAGEYR", "BMXBMI"), 2: ("RIDAGEYR", "BMXBMI", "LBDHDD", "LBXTC")}
PRUNE_KEEP = ("BMXBMI", "BMXWAIST", "whtr")
VIF_MAX = 10.0
SKEW_MAX = 1.0
#: P06 - columns whose missingness is plausibly informative (refusal / exam not possible)
MNAR_SUSPECT = ("INDFMPIR", "BMXWAIST", "bp_sys_mean", "LBXTC")
RARE_MIN_FREQ = 0.02
PA_UNIT_PER_WEEK = {"D": 7.0, "W": 1.0, "M": 7.0 / 30.4375, "Y": 7.0 / 365.25}
PA_ITEMS = {"pa_mod_min_wk": ("PAD790Q", "PAD790U", "PAD800"),
            "pa_vig_min_wk": ("PAD810Q", "PAD810U", "PAD820")}
BP_GROUPS = {"bp_sys_mean": io.BP_SYS, "bp_dia_mean": io.BP_DIA,
             "pulse_mean": ("BPXOPLS1", "BPXOPLS2", "BPXOPLS3")}


@lru_cache(maxsize=1)
def _spec() -> pd.DataFrame:
    return io.load_spec()


@lru_cache(maxsize=1)
def _spec_by_var() -> pd.DataFrame:
    inc = io.included(_spec())
    return inc.drop_duplicates("var").set_index("var")


def categorical_columns() -> frozenset:
    """Spec variables with dtype 'categorical' (+ the string unit columns)."""
    s = _spec_by_var()
    return frozenset(s.index[s["dtype"].eq("categorical")])


def _is_cat(X: pd.DataFrame, c: str) -> bool:
    return c in categorical_columns() or X[c].dtype == object


# =============================================================================
# configurations and arms
# =============================================================================
def make_cfg(on=(), *, no_care: bool = False) -> dict[str, bool]:
    """cfg dict with the given steps (or blocks) switched on; all other steps off."""
    on = set(on)
    for b in [x for x in on if x in BLOCKS]:
        on |= set(BLOCKS[b])
    bad = on - set(STEPS) - set(BLOCKS)
    assert not bad, bad
    cfg = {s: s in on for s in STEPS}
    cfg["NO_CARE"] = bool(no_care)
    return cfg


ALL_OFF = make_cfg()
S_STEPS = [s for s in STEPS if s != "P14"]


def _without(blocks) -> dict:
    off = {s for b in blocks for s in BLOCKS[b]}
    return make_cfg([s for s in S_STEPS if s not in off])


#: cumulative path M0 -> +B2 (=M1) -> +B1 -> +B3 -> +B4 -> +B5 -> +B6a -> +B6b (=S)
CUMULATIVE = ("M0", "M1", "cum+B1", "cum+B3", "cum+B4", "cum+B5", "cum+B6a", "S")
_CUM_ORDER = ("B2", "B1", "B3", "B4", "B5", "B6a", "B6b")

ARMS: dict[str, dict[str, bool]] = {
    "M0": ALL_OFF,
    "M1": make_cfg(["P03"]),
    "S": make_cfg(S_STEPS),
}
for _i, _name in enumerate(CUMULATIVE[2:-1], start=2):
    ARMS[_name] = make_cfg(_CUM_ORDER[:_i])
for _b in BLOCKS:
    ARMS[f"S-{_b}"] = _without([_b])
ARMS["T1-minus-care"] = make_cfg(S_STEPS, no_care=True)
ARMS["S-linear"] = make_cfg([s for s in S_STEPS if s != "P13"])
#: coefficient-stability companion of S-linear without B3 (hypothesis B3b): BMI unsplined in both
ARMS["S-linear-B3"] = make_cfg([s for s in S_STEPS if s not in ("P13", "P04", "P05")])
ARMS["S+WHtR"] = make_cfg(S_STEPS + ["P14"])
assert ARMS["cum+B6a"] == make_cfg(_CUM_ORDER[:6]) and make_cfg(_CUM_ORDER) == ARMS["S"]
LOBO = tuple(f"S-{b}" for b in BLOCKS)


def arm_table() -> pd.DataFrame:
    """Arms x steps matrix (1 = on) with block labels - the M0/M1/S design table."""
    rows = {a: {**{s: int(c[s]) for s in STEPS}, "NO_CARE": int(c["NO_CARE"])} for a, c in ARMS.items()}
    return pd.DataFrame(rows).T


# =============================================================================
# data
# =============================================================================
def raw_cohort() -> pd.DataFrame:
    """The 5,730-row cohort with RAW values (no XPT repair, no sentinel recode); input of every arm."""
    return io.build_cohort(io.load_merged(fix=False, sentinels="none"), sentinels="none", fix=False)


def raw_feature_frame(cohort: pd.DataFrame, tier: int) -> pd.DataFrame:
    """Columns entering M0 for the tier (incl. leakage traps, race and insurance).

    All spec-included raw columns except id, survey design / weights and the label-defining
    DIQ010 and LBXGH.  Tier 1 also drops the Tier-2-only lipids (LBXTC, LBDHDD); every other
    trap column (glucose, treatment, age at diagnosis, DIQ160/180, triglycerides, LDL,
    MCQ, insurance, race, ...) stays, because a naive analyst would keep it.
    """
    assert tier in (1, 2), tier
    raw_cols = [c for c in _spec_by_var().index if c in cohort.columns]
    drop = set(NON_FEATURES) | (set(TIER2_ONLY) if tier == 1 else set())
    return cohort[[c for c in raw_cols if c not in drop]].copy()


def admissible_columns(tier: int) -> list[str]:
    """Spec features admissible for the tier (T1, or T1 + T2)."""
    s = _spec_by_var()
    ok = {"T1"} if tier == 1 else {"T1", "T2"}
    return [v for v in s.index if s.loc[v, "admissible"] in ok and s.loc[v, "role"] == "feature"]


def training_label(cohort: pd.DataFrame, cfg: dict) -> np.ndarray:
    """L_comb as the arm would construct it from its own sentinel handling.

    P02 on: per-variable codebook codes (= the frozen label).  P02 off: blanket recode first,
    so HbA1c 7.0 / 9.0 become NaN and those people lose their HbA1c-based positive status.
    """
    mode = "per_variable" if cfg.get("P02") else "blanket"
    sub = cohort[["DIQ010", "LBXGH"]]
    sub, _ = io.apply_sentinels(sub, _spec(), mode=mode)
    y = sub["DIQ010"].eq(1) | sub["LBXGH"].ge(C.HBA1C_DIABETES)
    return y.fillna(False).astype(int).to_numpy()


def survey_weights(cohort: pd.DataFrame) -> np.ndarray:
    """WTPH2YR normalised to mean 1 over the rows given (P12)."""
    w = cohort[C.WEIGHT_PHLEB].to_numpy(float)
    assert np.isfinite(w).all() and (w > 0).all(), "WTPH2YR must be positive in the cohort"
    return w / w.mean()


# =============================================================================
# generic wrappers
# =============================================================================
class _Frame(BaseEstimator, TransformerMixin):
    """DataFrame-in / DataFrame-out transformer base; records output column names."""

    def _finish_fit(self, X):
        self.feature_names_out_ = list(self.transform(X.iloc[:3]).columns)
        return self

    def fit(self, X, y=None):
        return self._finish_fit(X)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_out_, dtype=object)


class Toggle(_Frame):
    """Wrap a step; ``enabled=False`` makes it the identity (fits nothing, changes nothing)."""

    def __init__(self, step=None, enabled: bool = True):
        self.step = step
        self.enabled = enabled

    def fit(self, X, y=None):
        if self.enabled:
            self.step_ = clone(self.step).fit(X, y)
        self.feature_names_out_ = list(self.step_.feature_names_out_) if self.enabled else list(X.columns)
        return self

    def transform(self, X):
        return self.step_.transform(X) if self.enabled else X


class Switch(_Frame):
    """Choose between the systematic step (``enabled``) and the naive M0 step (disabled)."""

    def __init__(self, on=None, off=None, enabled: bool = True):
        self.on = on
        self.off = off
        self.enabled = enabled

    def fit(self, X, y=None):
        self.step_ = clone(self.on if self.enabled else self.off).fit(X, y)
        self.feature_names_out_ = list(self.step_.feature_names_out_)
        return self

    def transform(self, X):
        return self.step_.transform(X)


# =============================================================================
# steps
# =============================================================================
class XptZeroFix(_Frame):
    """P01: SAS XPT stores 0 as 5.4e-79; ``mask`` keeps NaN as NaN (``where`` would not)."""

    def transform(self, X):
        out = X.copy()
        num = out.select_dtypes("number").columns
        x = out[num]
        out[num] = x.mask((x.abs() < C.XPT_ZERO_EPS) & x.notna(), 0.0)
        return out


class Sentinels(_Frame):
    """P02: refusal / don't-know codes -> NaN; mode "per_variable" (codebook) or "blanket" (M0)."""

    def __init__(self, mode: str = "per_variable"):
        self.mode = mode

    def transform(self, X):
        return io.apply_sentinels(X, _spec(), mode=self.mode)[0]


class DropColumns(_Frame):
    """Drop a fixed list of columns (those present)."""

    def __init__(self, columns=()):
        self.columns = columns

    def transform(self, X):
        return X.drop(columns=[c for c in self.columns if c in X.columns])


class Admissibility(_Frame):
    """P03: keep only spec features admissible for the tier (S1 availability rule).

    Non-spec (derived) columns are kept; spec columns with admissible "N" (leakage, label
    components, cohort filters, audit-only race / insurance, optional and side variables) and
    out-of-tier columns are dropped.
    """

    def __init__(self, tier: int = 1):
        self.tier = tier

    def transform(self, X):
        spec_vars = set(_spec_by_var().index)
        keep = set(admissible_columns(self.tier))
        return X[[c for c in X.columns if c not in spec_vars or c in keep]]


class Aggregate(_Frame):
    """P04: mean of repeated BP / pulse readings; physical activity as weekly minutes.

    Weekly minutes = frequency x (times per week of the unit) x minutes per occasion; a
    frequency of 0 gives 0 minutes (the duration item is skipped by design for these people,
    so its NaN is structural, not missing).  Source columns are replaced.
    """

    def transform(self, X):
        out = X.copy()
        for new, cols in BP_GROUPS.items():
            cols = [c for c in cols if c in out.columns]
            if cols:
                out[new] = out[cols].mean(axis=1, skipna=True)
                out = out.drop(columns=cols)
        for new, (q, u, m) in PA_ITEMS.items():
            if not {q, u, m} <= set(out.columns):
                continue
            freq, unit, mins = out[q], out[u], out[m]
            per_week = freq * unit.map(PA_UNIT_PER_WEEK).astype(float)
            val = per_week * mins
            val = val.mask(freq.eq(0), 0.0)
            out[new] = val
            out = out.drop(columns=[q, u, m])
        return out


class WHtR(_Frame):
    """P14: waist-to-height ratio replaces waist circumference (height kept)."""

    def transform(self, X):
        out = X.copy()
        if {"BMXWAIST", "BMXHT"} <= set(out.columns):
            pos = list(out.columns).index("BMXWAIST")
            whtr = out["BMXWAIST"] / out["BMXHT"]
            out = out.drop(columns=["BMXWAIST"])
            out.insert(pos, "whtr", whtr)
        return out


def _continuous(X: pd.DataFrame, exclude=()) -> list[str]:
    """Numeric, non-categorical columns with more than two distinct values."""
    return [c for c in X.columns if c not in exclude and not _is_cat(X, c)
            and pd.api.types.is_numeric_dtype(X[c]) and X[c].nunique(dropna=True) > 2]


def vif_table(X: pd.DataFrame) -> pd.Series:
    """VIF_j = diag(R^-1) of the correlation matrix (median-imputed columns)."""
    Z = X.apply(lambda s: s.fillna(s.median()))
    Z = Z.loc[:, Z.std(ddof=0) > 0]
    R = np.corrcoef(Z.to_numpy(float), rowvar=False)
    return pd.Series(np.diag(np.linalg.pinv(R)), index=Z.columns)


class VIFPrune(_Frame):
    """P05: iteratively drop the continuous column with the largest VIF while VIF > ``vif_max``.

    Fitted in-fold (X only). Columns in ``keep`` (BMI and waist / WHtR) are never dropped.
    ``dropped_`` lists the removed columns with the VIF at removal.
    """

    def __init__(self, vif_max: float = VIF_MAX, keep=PRUNE_KEEP):
        self.vif_max = vif_max
        self.keep = keep

    def fit(self, X, y=None):
        cols = _continuous(X)
        dropped = []
        while len(cols) > 1:
            v = vif_table(X[cols])
            cand = v.drop([c for c in self.keep if c in v.index])
            if cand.empty or cand.max() <= self.vif_max:
                break
            worst = cand.idxmax()
            dropped.append((worst, float(cand.max())))
            cols.remove(worst)
        self.dropped_ = dropped
        return self._finish_fit(X)

    def transform(self, X):
        return X.drop(columns=[c for c, _ in self.dropped_ if c in X.columns])


class MissingIndicator(_Frame):
    """P06: binary ``<col>_missing`` for MNAR-suspect columns (added before imputation)."""

    def __init__(self, columns=MNAR_SUSPECT):
        self.columns = columns

    def transform(self, X):
        out = X.copy()
        for c in self.columns:
            if c in out.columns:
                out[f"{c}_missing"] = out[c].isna().astype(float)
        return out


class TopcodeFlags(_Frame):
    """P07: disclosure top-codes become explicit flags (age 80+, PIR 5+)."""

    def transform(self, X):
        out = X.copy()
        if "RIDAGEYR" in out:
            out["age_top"] = out["RIDAGEYR"].eq(80).astype(float)
        if "INDFMPIR" in out:
            out["pir_top"] = out["INDFMPIR"].eq(5).astype(float)
        return out


class Impute(_Frame):
    """Base imputation shared by all arms: median (numeric) / most frequent (categorical)."""

    def fit(self, X, y=None):
        self.cat_ = [c for c in X.columns if _is_cat(X, c)]
        self.fill_ = {}
        for c in X.columns:
            s = X[c]
            if c in self.cat_:
                m = s.mode(dropna=True)
                self.fill_[c] = m.iloc[0] if len(m) else "missing"
            else:
                med = s.median()
                self.fill_[c] = 0.0 if pd.isna(med) else med
        return self._finish_fit(X)

    def transform(self, X):
        return X.fillna({c: v for c, v in self.fill_.items() if c in X.columns})


class YeoJohnson(_Frame):
    """P08: Yeo-Johnson (standardize=False) on continuous columns with |skew| > ``skew_max`` (in-fold)."""

    def __init__(self, skew_max: float = SKEW_MAX, exclude=()):
        self.skew_max = skew_max
        self.exclude = exclude

    def fit(self, X, y=None):
        cols = _continuous(X, exclude=self.exclude)
        sk = {c: float(stats.skew(X[c].to_numpy(float), nan_policy="omit")) for c in cols}
        self.skew_ = sk
        self.cols_ = [c for c, s in sk.items() if abs(s) > self.skew_max]
        self.pt_ = PowerTransformer(method="yeo-johnson", standardize=False).fit(X[self.cols_]) if self.cols_ else None
        return self._finish_fit(X)

    def transform(self, X):
        out = X.copy()
        if self.cols_:
            out[self.cols_] = self.pt_.transform(X[self.cols_])
        return out


class Splines(_Frame):
    """P13: B-spline basis (``config.SPLINE_KW``) replaces each listed column (fitted in-fold)."""

    def __init__(self, columns=()):
        self.columns = columns

    def fit(self, X, y=None):
        self.st_ = {c: SplineTransformer(**C.SPLINE_KW).fit(X[[c]]) for c in self.columns if c in X.columns}
        return self._finish_fit(X)

    def transform(self, X):
        out = X.copy()
        for c, st in self.st_.items():
            basis = st.transform(X[[c]])
            pos = list(out.columns).index(c)
            out = out.drop(columns=[c])
            for k in range(basis.shape[1]):
                out.insert(pos + k, f"{c}_sp{k}", basis[:, k])
        return out


class Scale(_Frame):
    """P09: StandardScaler on every non-categorical column (in-fold)."""

    def fit(self, X, y=None):
        self.cols_ = [c for c in X.columns if not _is_cat(X, c)]
        self.sc_ = StandardScaler().fit(X[self.cols_]) if self.cols_ else None
        return self._finish_fit(X)

    def transform(self, X):
        out = X.copy()
        if self.cols_:
            out[self.cols_] = self.sc_.transform(X[self.cols_])
        return out


class OneHot(_Frame):
    """Categorical encoding; numeric columns first (input order), then the dummy columns.

    ``rare=False`` (M0): ``OneHotEncoder(handle_unknown="ignore")``.
    ``rare=True`` (P10): ``min_frequency=0.02, handle_unknown="infrequent_if_exist"``.
    """

    def __init__(self, rare: bool = False):
        self.rare = rare

    def fit(self, X, y=None):
        self.cat_ = [c for c in X.columns if _is_cat(X, c)]
        kw = (dict(min_frequency=RARE_MIN_FREQ, handle_unknown="infrequent_if_exist") if self.rare
              else dict(handle_unknown="ignore"))
        self.enc_ = OneHotEncoder(sparse_output=False, **kw).fit(self._cats(X)) if self.cat_ else None
        return self._finish_fit(X)

    def _cats(self, X):
        return X[self.cat_].astype(str)

    def transform(self, X):
        num = X[[c for c in X.columns if c not in self.cat_]]
        if not self.cat_:
            return num
        dummies = pd.DataFrame(self.enc_.transform(self._cats(X)), index=X.index,
                               columns=self.enc_.get_feature_names_out(self.cat_))
        return pd.concat([num, dummies], axis=1)


# =============================================================================
# pipeline
# =============================================================================
def model_kwargs(cfg: dict) -> dict:
    """Estimator-level settings of P11 / P12.

    ``class_weight``: "balanced" if P11 else None.  ``sample_weight``: True if P12, i.e. the
    caller passes ``fit_params(cfg, cohort)`` (WTPH2YR / mean) to ``fit``.
    """
    return {"class_weight": "balanced" if cfg.get("P11") else None, "sample_weight": bool(cfg.get("P12"))}


def fit_params(cfg: dict, cohort: pd.DataFrame) -> dict:
    """``fit`` keyword arguments for the pipeline (P12 survey weights) or {}."""
    return {"model__sample_weight": survey_weights(cohort)} if cfg.get("P12") else {}


def make_model(cfg: dict, model: str = "lr", C_: float = 1.0, seed: int = C.SEED_MASTER):
    kw = model_kwargs(cfg)
    if model == "lr":
        return LogisticRegression(C=C_, max_iter=C.LR_MAX_ITER, class_weight=kw["class_weight"])
    if model == "tree":
        return DecisionTreeClassifier(max_depth=C.TREE_MAX_DEPTH, min_samples_leaf=C.TREE_MIN_LEAF,
                                      class_weight=kw["class_weight"], random_state=seed)
    raise ValueError(model)


def preprocessor_steps(cfg: dict, tier: int) -> list[tuple[str, object]]:
    """Ordered (name, transformer) list of the preparation part of the pipeline."""
    cfg = {**ALL_OFF, **cfg}
    spl = SPLINE_COLS[tier]
    return [
        ("p01", Toggle(XptZeroFix(), cfg["P01"])),
        ("p02", Switch(Sentinels("per_variable"), Sentinels("blanket"), cfg["P02"])),
        ("p03", Toggle(Admissibility(tier), cfg["P03"])),
        ("no_care", Toggle(DropColumns(CARE_ITEMS), cfg["NO_CARE"])),
        ("p04", Toggle(Aggregate(), cfg["P04"])),
        ("p14", Toggle(WHtR(), cfg["P14"])),
        ("p05", Toggle(VIFPrune(), cfg["P05"])),
        ("p06", Toggle(MissingIndicator(), cfg["P06"])),
        ("p07", Toggle(TopcodeFlags(), cfg["P07"])),
        ("impute", Impute()),
        ("p08", Toggle(YeoJohnson(exclude=spl if cfg["P13"] else ()), cfg["P08"])),
        ("p13", Toggle(Splines(spl), cfg["P13"])),
        ("p09", Toggle(Scale(), cfg["P09"])),
        ("p10", Switch(OneHot(rare=True), OneHot(rare=False), cfg["P10"])),
    ]


def build_pipeline(cfg: dict, tier: int, model: str = "lr", *, C_: float = 1.0,
                   seed: int = C.SEED_MASTER) -> Pipeline:
    """Full arm pipeline: preparation steps (Toggle/Switch per cfg) + estimator ``model``.

    ``model`` is "lr" (``LogisticRegression(C=C_, max_iter=5000)``) or "tree" (depth 3,
    min_samples_leaf 50).  Input: :func:`raw_feature_frame` of the raw cohort.  P12 survey
    weights are passed at fit time via :func:`fit_params`.
    """
    return Pipeline(preprocessor_steps(cfg, tier) + [("model", make_model(cfg, model, C_, seed))])


def transform_only(cfg: dict, tier: int, X: pd.DataFrame, y=None) -> pd.DataFrame:
    """Design matrix produced by the preparation part (fitted on X) - for inspection."""
    pipe = Pipeline(preprocessor_steps(cfg, tier))
    return pipe.fit(X, y).transform(X)


# =============================================================================
# independent naive reference (for the "all-False == M0" assertion)
# =============================================================================
def naive_m0_reference(tier: int, X: pd.DataFrame, C_: float = 1.0) -> Pipeline:
    """M0 written the way a naive analyst would, independently of the Toggle machinery.

    blanket ``replace({7,9,77,...}, NaN)`` -> median (numeric) / most-frequent (low-cardinality)
    imputation -> one-hot of columns with <= 10 distinct values -> LogisticRegression(C=1).
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import FunctionTransformer

    low_card = [c for c in X.columns if X[c].nunique(dropna=True) <= 10]
    num = [c for c in X.columns if c not in low_card]

    def blanket(df):
        df = df.copy()
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].replace(r"^\s*$", np.nan, regex=True)
            else:
                df[c] = df[c].mask(df[c].isin(io.BLANKET_CODES))
        df[low_card] = df[low_card].astype(str).where(df[low_card].notna(), np.nan)
        return df

    ct = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), num),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), low_card),
    ])
    return Pipeline([("blanket", FunctionTransformer(blanket)), ("ct", ct),
                     ("model", LogisticRegression(C=C_, max_iter=C.LR_MAX_ITER))])


# =============================================================================
# experiment helpers (S7)
# =============================================================================
def run_arm_cv(arm: str, tier: int, X: pd.DataFrame, cohort: pd.DataFrame, folds, *, C_: float = 1.0,
               model: str = "lr", cfg: dict | None = None) -> dict:
    """Out-of-fold predictions of one arm (``evalkit.cv_predict``) plus fit diagnostics.

    ``X`` = :func:`raw_feature_frame` of the training rows, ``cohort`` = the matching raw cohort rows
    (training label per the arm's P02 setting, WTPH2YR for P12).  Returns
    ``{"arm", "tier", "model", "oof", "n_convergence_warnings", "seconds", "n_pos_train_label"}``.
    """
    import time
    import warnings
    from sklearn.exceptions import ConvergenceWarning

    from . import evalkit as ek

    cfg = ARMS[arm] if cfg is None else cfg
    y = training_label(cohort, cfg)
    t0 = time.time()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", ConvergenceWarning)
        oof = ek.cv_predict(lambda: build_pipeline(cfg, tier, model, C_=C_), X, y, folds,
                            fit_params=fit_params(cfg, cohort))
    n_conv = sum(issubclass(x.category, ConvergenceWarning) for x in w)
    return dict(arm=arm, tier=tier, model=model, oof=oof, n_convergence_warnings=int(n_conv),
                seconds=time.time() - t0, n_pos_train_label=int(y.sum()))


#: ADA risk test items available in NHANES 2021-23 (family history and gestational diabetes are not asked)
ADA_ITEMS = ("ada_age", "ada_male", "ada_htn", "ada_inactive", "ada_bmi")


def ada_lite_items(clean: pd.DataFrame) -> pd.DataFrame:
    """Reduced ADA risk test (Bang et al. 2009) items from the per-variable cohort.

    age points 0/1/2/3 for <40 / 40-49 / 50-59 / >=60; male +1; told high blood pressure
    (BPQ020 = 1) +1; physically inactive +1 (no leisure-time moderate or vigorous activity,
    PAD790Q = 0 and PAD810Q = 0 - the ADA "physically active? no"); BMI points 0/1/2/3 for
    <25 / 25-29.9 / 30-39.9 / >=40.  Missing answers score 0 (flag columns ``*_missing``).
    The two missing items (family history, gestational diabetes) make this a reduced score.
    """
    d = pd.DataFrame(index=clean.index)
    age = clean["RIDAGEYR"]
    d["ada_age"] = np.select([age >= 60, age >= 50, age >= 40], [3, 2, 1], 0)
    d["ada_male"] = clean["RIAGENDR"].eq(1).astype(int)
    d["ada_htn"] = clean["BPQ020"].eq(1).astype(int)
    mod, vig = clean["PAD790Q"], clean["PAD810Q"]
    d["ada_inactive"] = (mod.eq(0) & vig.eq(0)).astype(int)
    bmi = clean["BMXBMI"]
    d["ada_bmi"] = np.select([bmi >= 40, bmi >= 30, bmi >= 25], [3, 2, 1], 0)
    d["ada_htn_missing"] = clean["BPQ020"].isna().astype(int)
    d["ada_inactive_missing"] = (mod.isna() | vig.isna()).astype(int)
    d["ada_bmi_missing"] = bmi.isna().astype(int)
    d["ada_score"] = d[list(ADA_ITEMS)].sum(axis=1)
    return d


def ada_lr_pipeline(C_: float = 1.0) -> Pipeline:
    """BL-ADAlite-LR: logistic regression on the one-hot ADA-lite items (same items, fitted weights)."""
    from sklearn.compose import ColumnTransformer

    ct = ColumnTransformer([("items", OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop="first"),
                             list(ADA_ITEMS))])
    return Pipeline([("ct", ct), ("model", LogisticRegression(C=C_, max_iter=C.LR_MAX_ITER))])
