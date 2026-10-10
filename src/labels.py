"""Label definitions, evaluation populations and sensitivity labels (Stage S5).

Pure column logic on the analysis cohort (one row per adult, `nhanes_io.build_cohort()`).
No I/O, no fitting: every function takes a DataFrame and returns new columns or a
small table, so S6–S9 can import the *same* definitions that S5 audits and freezes.

Frozen target (docs/development_process.md §2, S5 step 8)
    L_comb = (DIQ010 == 1) or (LBXGH >= 6.5)          adults >=20, examined, non-pregnant

Columns added by `add_labels`
    L_self        DIQ010 == 1 (doctor-diagnosed diabetes); borderline (3), "No" (2),
                  "Don't know"/refused/missing -> 0
    L_A1c         LBXGH >= 6.5 (HbA1c, %)
    L_comb        L_self | L_A1c                              (the frozen training target)
    borderline    DIQ010 == 3 (told "borderline"); flag only, negative in L_self/L_comb
    on_med        insulin (DIQ050 == 1) or diabetic pills (DIQ070 == 1) among L_self
    stratum_3x3   D_uncontrolled (L_self & L_A1c) | D_controlled (L_self & ~L_A1c)
                  | Undiagnosed (~L_self & L_A1c) | NonDiabetic (~L_self & ~L_A1c)
    in_escreen    DIQ010 != 1  (screening population: not known to have diabetes)
    y_escreen     LBXGH >= 6.5 inside E-SCREEN, NaN outside (borderline stays in E-SCREEN)

Sensitivity labels (`sensitivity_labels`)
    SL1  L_A1c only
    SL2  L_self only
    SL3  L_comb with borderline counted positive
    SL4  treatment-aware: L_A1c or (L_self and on insulin/pills). Medication answers are
         used only inside the true DIQ070 universe (DIQ010 = 1, or 3, or 2 with DIQ160 = 1);
         pills reported by borderline / prediabetic respondents (probably metformin for
         prediabetes) do NOT make a case.
    SL5  NCHS DB516 definition on the fasting subsample: L_self or LBXGH >= 6.5 or
         LBXGLU >= 126 mg/dL; NaN outside the fasting subsample (WTSAF2YR > 0 & LBXGLU
         observed). Analyse with WTSAF2YR.
    SL6  (procedure) 3x3 label matrix: train on {L_self, L_A1c, L_comb}, evaluate recall
         at specificity 0.80 per stratum_3x3 column vs the common NonDiabetic negatives.
    SL7  (procedure) permutation negative control: train on a permuted L_comb.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

A1C_CUT = C.HBA1C_DIABETES          # 6.5 %
FPG_CUT = 126.0                     # mg/dL, NCHS / ADA fasting plasma glucose
STRATA_3X3 = ("D_uncontrolled", "D_controlled", "Undiagnosed", "NonDiabetic")
POSITIVE_STRATA = STRATA_3X3[:3]
LABEL_COLS = ("L_self", "L_A1c", "L_comb")
SL_COLS = ("SL1", "SL2", "SL3", "SL4", "SL5")

# Expected counts in the 5,730-row cohort (process doc §8 / S5 step 1); used by asserts.
EXPECTED_CONFUSION = {(0, 0): 4759, (0, 1): 152, (1, 0): 250, (1, 1): 569}


# --------------------------------------------------------------------------------------
# core labels
# --------------------------------------------------------------------------------------
def _eq(s: pd.Series, value) -> pd.Series:
    """Boolean `s == value` with NaN -> False."""
    return s.eq(value).fillna(False).astype(bool)


def diq070_universe(df: pd.DataFrame) -> pd.Series:
    """Rows that were actually asked DIQ070 (diabetic pills).

    CAPI skip pattern of DIQ_L: DIQ010 = 1 (diagnosed), or DIQ010 = 3 (borderline),
    or DIQ010 = 2 with DIQ160 = 1 (told prediabetes).
    """
    d010, d160 = df["DIQ010"], df.get("DIQ160", pd.Series(np.nan, index=df.index))
    return _eq(d010, 1) | _eq(d010, 3) | (_eq(d010, 2) & _eq(d160, 1))


def add_labels(cohort: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `cohort` with the frozen labels, flags and evaluation strata.

    Requires DIQ010 and LBXGH (LBXGH must be observed: the cohort requires HbA1c).
    DIQ050 / DIQ070 are optional (on_med is NaN-safe and 0 when absent).
    """
    df = cohort.copy()
    if df["LBXGH"].isna().any():
        raise ValueError("add_labels expects the HbA1c cohort (LBXGH observed for every row)")
    l_self = _eq(df["DIQ010"], 1)
    l_a1c = df["LBXGH"].ge(A1C_CUT)
    df["L_self"] = l_self.astype("int8")
    df["L_A1c"] = l_a1c.astype("int8")
    df["L_comb"] = (l_self | l_a1c).astype("int8")
    df["borderline"] = _eq(df["DIQ010"], 3).astype("int8")

    ins = _eq(df["DIQ050"], 1) if "DIQ050" in df else pd.Series(False, index=df.index)
    pills = _eq(df["DIQ070"], 1) if "DIQ070" in df else pd.Series(False, index=df.index)
    df["on_med"] = (l_self & (ins | pills)).astype("int8")

    stratum = np.select(
        [l_self & l_a1c, l_self & ~l_a1c, ~l_self & l_a1c],
        ["D_uncontrolled", "D_controlled", "Undiagnosed"],
        default="NonDiabetic",
    )
    df["stratum_3x3"] = pd.Categorical(stratum, categories=list(STRATA_3X3))

    df["in_escreen"] = (~l_self).astype("int8")
    df["y_escreen"] = np.where(~l_self, l_a1c.astype(float), np.nan)
    return df


def fasting_mask(df: pd.DataFrame) -> pd.Series:
    """Fasting subsample: positive fasting weight and an observed plasma glucose."""
    if "LBXGLU" not in df or C.WEIGHT_FASTING not in df:
        return pd.Series(False, index=df.index)
    return df[C.WEIGHT_FASTING].fillna(0).gt(0) & df["LBXGLU"].notna()


def sensitivity_labels(cohort: pd.DataFrame) -> pd.DataFrame:
    """SL1..SL5 as columns (index aligned with `cohort`); SL6/SL7 are procedures.

    SL5 is NaN outside the fasting subsample (see `fasting_mask`).
    """
    df = cohort if {"L_self", "L_A1c", "L_comb"} <= set(cohort.columns) else add_labels(cohort)
    l_self = df["L_self"].astype(bool)
    l_a1c = df["L_A1c"].astype(bool)
    univ = diq070_universe(df)
    ins = _eq(df["DIQ050"], 1) if "DIQ050" in df else pd.Series(False, index=df.index)
    pills = _eq(df["DIQ070"], 1) if "DIQ070" in df else pd.Series(False, index=df.index)
    treated_dm = l_self & univ & (ins | pills)

    out = pd.DataFrame(index=df.index)
    out["SL1"] = l_a1c.astype("int8")
    out["SL2"] = l_self.astype("int8")
    out["SL3"] = (df["L_comb"].astype(bool) | df["borderline"].astype(bool)).astype("int8")
    out["SL4"] = (l_a1c | treated_dm).astype("int8")
    fm = fasting_mask(df)
    sl5 = l_self | l_a1c | (df["LBXGLU"].ge(FPG_CUT) if "LBXGLU" in df else False)
    out["SL5"] = np.where(fm, sl5.astype(float), np.nan)
    return out


# --------------------------------------------------------------------------------------
# agreement statistics
# --------------------------------------------------------------------------------------
def _weights(df: pd.DataFrame, weight) -> np.ndarray:
    """None -> ones; column name -> that column; array-like -> as is (NaN -> 0)."""
    if weight is None:
        return np.ones(len(df))
    w = df[weight].to_numpy(float) if isinstance(weight, str) else np.asarray(weight, dtype=float)
    return np.nan_to_num(w)


def confusion(cohort: pd.DataFrame, *, weight=None,
              rows: str = "L_self", cols: str = "L_A1c") -> pd.DataFrame:
    """2x2 table rows x cols (default self-report x HbA1c); counts or weighted sums.

    `weight` is None (counts), a column name or a weight vector (e.g. a jackknife
    replicate). Index/columns are 0/1 named after the label columns.
    """
    df = cohort if rows in cohort else add_labels(cohort)
    w = _weights(df, weight)
    r = df[rows].astype(int).to_numpy()
    c = df[cols].astype(int).to_numpy()
    tab = np.zeros((2, 2))
    for i in (0, 1):
        for j in (0, 1):
            tab[i, j] = w[(r == i) & (c == j)].sum()
    out = pd.DataFrame(tab, index=pd.Index([0, 1], name=rows), columns=pd.Index([0, 1], name=cols))
    return out.astype(int) if weight is None else out


def agreement_from_table(tab) -> dict:
    """Agreement statistics from a 2x2 table [[a00, a01], [a10, a11]] (rows = rater A).

    kappa      Cohen's kappa
    pa, na     positive / negative specific agreement (Cicchetti & Feinstein 1990)
    sens, ppv  sensitivity and PPV of rater A (rows) against rater B (cols)
    """
    t = np.asarray(tab, dtype=float)
    n = t.sum()
    a, b, c, d = t[1, 1], t[1, 0], t[0, 1], t[0, 0]   # both+, A+B-, A-B+, both-
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / n**2
    return {
        "n": n,
        "po": po,
        "kappa": (po - pe) / (1 - pe),
        "pa": 2 * a / (2 * a + b + c),
        "na": 2 * d / (2 * d + b + c),
        "sens": a / (a + c),
        "ppv": a / (a + b),
    }


def agreement(df: pd.DataFrame, weight=None, *,
              rows: str = "L_self", cols: str = "L_A1c") -> dict:
    """`agreement_from_table(confusion(...))` – convenient as a jackknife statistic."""
    return agreement_from_table(confusion(df, weight=weight, rows=rows, cols=cols).to_numpy())


AGREEMENT_KEYS = ("kappa", "pa", "na", "sens", "ppv")


def agreement_vector(df: pd.DataFrame, w) -> np.ndarray:
    """[kappa, PA, NA, sens, PPV] – signature `stat_fn(df, w)` for `survey.jackknife`."""
    a = agreement(df, w)
    return np.array([a[k] for k in AGREEMENT_KEYS])


def strata_counts(df: pd.DataFrame) -> dict:
    """Counts per 3x3 evaluation stratum (requires `add_labels`)."""
    vc = df["stratum_3x3"].value_counts()
    return {k: int(vc.get(k, 0)) for k in STRATA_3X3}


def check_frozen_counts(df: pd.DataFrame) -> None:
    """Assert the frozen label counts of process doc §8 (5,730-row cohort)."""
    tab = confusion(df)
    got = {(i, j): int(tab.loc[i, j]) for i in (0, 1) for j in (0, 1)}
    assert got == EXPECTED_CONFUSION, got
    assert int(df["L_comb"].sum()) == 971
    assert int(df["y_escreen"].sum()) == 152
