"""Design-based survey estimation for NHANES 2021-23 (stage S4).

Variance: delete-one-PSU jackknife (JKn). The 2021-23 design has 15 masked
variance strata (SDMVSTRA) with 2 PSUs each (SDMVPSU), so the design degrees of
freedom are #PSU - #strata = 30 - 15 = 15 and Wald intervals use t_15.

For PSU *i* in stratum *h* the replicate weight is 0 for that PSU, the other PSUs
of stratum *h* are multiplied by n_h / (n_h - 1) (= 2 here) and all other strata
are unchanged. With theta_(hi) the replicate estimate and theta the full-sample
estimate,

    v(theta) = sum_h (n_h - 1) / n_h * sum_i (theta_(hi) - theta)^2 .

Domain (subpopulation) estimation is done by zeroing the weights outside the
domain - never by dropping rows - so every replicate keeps the full design and
empty-in-a-PSU domains are handled correctly.

Presentation follows the NCHS data presentation standards for proportions
(Parker et al. 2017): Korn-Graubard intervals with a degrees-of-freedom
adjusted effective sample size, and an estimate is flagged when n < 30, the
effective n < 30, the absolute CI width >= 0.30, or the CI width is in (0.05, 0.30)
with relative width > 130 %; df < 8 or 0 events trigger review. Domain degrees of
freedom follow the NCHS rule: (number of PSUs containing domain observations) -
(number of strata containing domain observations).

Age standardisation uses the US 2000 standard population collapsed to three
bands (20-39, 40-59, 60+), the NCHS convention for adult diabetes estimates.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats

from . import config as C

US2000_3BAND = {"20-39": 0.3966, "40-59": 0.3718, "60+": 0.2316}
AGE_BANDS_3 = [(20, 39, "20-39"), (40, 59, "40-59"), (60, 200, "60+")]

ArrayLike = "np.ndarray | pd.Series"


# --------------------------------------------------------------------------- basics
def weighted_mean(x, w) -> float:
    """Weighted mean of `x` ignoring NaN in `x` (their weight is dropped)."""
    x = np.asarray(x, dtype=float)
    w = np.asarray(w, dtype=float)
    ok = ~np.isnan(x) & (w > 0)
    sw = w[ok].sum()
    return float(np.dot(w[ok], x[ok]) / sw) if sw > 0 else float("nan")


def kish_deff(w) -> float:
    """Kish design effect due to unequal weighting: n * sum(w^2) / (sum w)^2 (= 1 + CV_w^2)."""
    w = np.asarray(w, dtype=float)
    w = w[w > 0]
    return float(len(w) * np.sum(w ** 2) / np.sum(w) ** 2) if len(w) else float("nan")


def kish_neff(w) -> float:
    """Kish effective sample size (sum w)^2 / sum(w^2) over positive weights."""
    w = np.asarray(w, dtype=float)
    w = w[w > 0]
    return float(np.sum(w) ** 2 / np.sum(w ** 2)) if len(w) else 0.0


def _as_mask(df: pd.DataFrame, spec) -> np.ndarray:
    """Turn a column name, boolean Series/array or None into a boolean numpy mask."""
    if spec is None:
        return np.ones(len(df), dtype=bool)
    if isinstance(spec, str):
        spec = df[spec]
    arr = np.asarray(spec)
    if arr.dtype != bool:
        arr = pd.Series(arr).fillna(0).astype(float).to_numpy() != 0
    return arr


def _as_values(df: pd.DataFrame, y) -> np.ndarray:
    """Outcome as float array (NaN kept). Accepts a column name or array-like."""
    if isinstance(y, str):
        y = df[y]
    return pd.Series(np.asarray(y)).astype(float).to_numpy()


# --------------------------------------------------------------------------- design
def design_df(df: pd.DataFrame, strata: str = C.STRATA, psu: str = C.PSU) -> int:
    """Design degrees of freedom: #PSU - #strata (= 15 for NHANES 2021-23)."""
    n_psu = df[[strata, psu]].drop_duplicates().shape[0]
    return int(n_psu - df[strata].nunique())


def domain_df(df: pd.DataFrame, mask, strata: str = C.STRATA, psu: str = C.PSU, *,
              method: str = "nchs") -> int:
    """Degrees of freedom for a domain (subpopulation).

    method="nchs" (default): #PSUs containing domain observations minus #strata
    containing domain observations (NCHS / NHANES reliability guidance). A stratum in
    which the domain occupies only one of its two PSUs therefore adds no df.
    method="strata": number of strata containing domain observations (a simpler
    approximation that equals the NCHS rule only when the domain occupies both PSUs
    of every stratum it touches; kept for comparison).
    """
    m = _as_mask(df, mask)
    sub = df.loc[m, [strata, psu]]
    n_strata = sub[strata].nunique()
    if method == "strata":
        return int(n_strata)
    if method != "nchs":
        raise ValueError(f"unknown method {method!r}")
    return int(sub.drop_duplicates().shape[0] - n_strata)


def replicate_weights(df: pd.DataFrame, weight: str | np.ndarray, *, strata: str = C.STRATA,
                      psu: str = C.PSU) -> tuple[np.ndarray, np.ndarray]:
    """JKn replicate weights.

    Returns (W, factor): W has shape (n_rows, R) with one column per deleted PSU,
    factor[r] = (n_h - 1) / n_h for the stratum of replicate r.
    """
    w = df[weight].to_numpy(dtype=float) if isinstance(weight, str) else np.asarray(weight, dtype=float)
    w = np.nan_to_num(w, nan=0.0)
    s = df[strata].to_numpy()
    p = df[psu].to_numpy()
    cols, factor = [], []
    for h in np.unique(s):
        in_h = s == h
        psus = np.unique(p[in_h])
        nh = len(psus)
        if nh < 2:
            continue  # singleton stratum contributes no variance
        for i in psus:
            wr = w.copy()
            wr[in_h & (p == i)] = 0.0
            wr[in_h & (p != i)] *= nh / (nh - 1)
            cols.append(wr)
            factor.append((nh - 1) / nh)
    return np.column_stack(cols), np.asarray(factor)


def jackknife(df: pd.DataFrame, stat_fn: Callable[[pd.DataFrame, np.ndarray], float | np.ndarray], *,
              weight: str | np.ndarray, strata: str = C.STRATA, psu: str = C.PSU,
              df_override: int | None = None, alpha: float = 0.05) -> dict:
    """Delete-one-PSU jackknife for any statistic `stat_fn(df, w)`.

    `stat_fn` receives the full data frame and a weight vector (full-sample or
    replicate) and returns a scalar or a 1-D array. Returns est, se, df, ci_low,
    ci_high (t-based, df = #PSU - #strata unless `df_override`) and the replicate
    estimates (`reps`). Array statistics give arrays in every field.
    """
    w = df[weight].to_numpy(dtype=float) if isinstance(weight, str) else np.asarray(weight, dtype=float)
    w = np.nan_to_num(w, nan=0.0)
    est = np.asarray(stat_fn(df, w), dtype=float)
    W, factor = replicate_weights(df, w, strata=strata, psu=psu)
    reps = np.array([np.asarray(stat_fn(df, W[:, r]), dtype=float) for r in range(W.shape[1])])
    var = np.tensordot(factor, (reps - est) ** 2, axes=(0, 0))
    se = np.sqrt(var)
    dfree = design_df(df, strata, psu) if df_override is None else int(df_override)
    t = stats.t.ppf(1 - alpha / 2, dfree)
    out = {"est": est, "se": se, "df": dfree, "ci_low": est - t * se, "ci_high": est + t * se, "reps": reps}
    if est.ndim == 0:
        out = {k: (float(v) if k not in ("reps", "df") else v) for k, v in out.items()}
    return out


# --------------------------------------------------------------------------- proportions
def korn_graubard_ci(p: float, n_eff: float, df: int, alpha: float = 0.05, *,
                     n: int | None = None) -> tuple[float, float]:
    """Korn-Graubard (1998) interval for a design-based proportion.

    Clopper-Pearson interval evaluated at the degrees-of-freedom adjusted
    effective sample size n_df = n_eff * (t_{n-1} / t_df)^2 (NCHS standards,
    Parker et al. 2017). When `n` (the unweighted domain size) is given the
    effective sample size is capped at n (design effect < 1 is not credited)
    and t_{n-1} uses it; otherwise t_{n_eff-1}.
    """
    if not np.isfinite(p) or not np.isfinite(n_eff) or n_eff <= 0:
        return (float("nan"), float("nan"))
    if n is not None:
        n_eff = min(n_eff, n)
        nref = n
    else:
        nref = n_eff
    tq = 1 - alpha / 2
    n_df = n_eff * (stats.t.ppf(tq, max(nref - 1, 1)) / stats.t.ppf(tq, max(df, 1))) ** 2
    x = p * n_df
    lo = 0.0 if x <= 0 else float(stats.beta.ppf(alpha / 2, x, n_df - x + 1))
    hi = 1.0 if x >= n_df else float(stats.beta.ppf(tq, x + 1, n_df - x))
    return lo, hi


SUPPRESS_FLAGS = ("n<30", "n_eff<30", "ci_width>=0.30", "rel_ci_width>130%")
REVIEW_FLAGS = ("df<8", "events=0_or_all")


def nchs_flags(n: int, n_eff: float, ci_width: float, df: int, *, p: float | None = None,
               n_events: int | None = None) -> list[str]:
    """NCHS presentation flags for a proportion (Parker et al. 2017); empty list = present.

    Suppression criteria: n < 30; effective n < 30; absolute CI width >= 0.30; absolute
    CI width in (0.05, 0.30) with relative CI width (width / p) > 130 %.
    Review criteria (statistical review by a clearance official): df < 8; 0 events (or
    all events). Footnote: if p meets the criteria but its complement 1 - p has relative
    CI width > 130 %, p is shown with a note that the complement may be unreliable
    ("complement_rel_ci_width>130%"). `p` (and `n_events`) are optional so that the
    original four-argument call keeps working; without `p` the relative rules are skipped.
    """
    flags = []
    if n < C.NCHS_MIN_N:
        flags.append("n<30")
    if not np.isfinite(n_eff) or n_eff < C.NCHS_MIN_N:
        flags.append("n_eff<30")
    if not np.isfinite(ci_width) or ci_width >= C.NCHS_CI_WIDTH_MAX:
        flags.append("ci_width>=0.30")
    elif p is not None and np.isfinite(p) and 0.05 < ci_width < C.NCHS_CI_WIDTH_MAX:
        if p <= 0 or ci_width / p > 1.30:
            flags.append("rel_ci_width>130%")
        elif p >= 1 or ci_width / (1 - p) > 1.30:
            flags.append("complement_rel_ci_width>130%")
    if df < C.NCHS_MIN_DF:
        flags.append("df<8")
    if n_events is not None and (n_events == 0 or n_events == n):
        flags.append("events=0_or_all")
    return flags


def nchs_status(flags: list[str]) -> str:
    """Collapse NCHS flags into 'suppress', 'review' or 'present' (Parker et al. 2017)."""
    if any(f in SUPPRESS_FLAGS for f in flags):
        return "suppress"
    if any(f in REVIEW_FLAGS for f in flags):
        return "review"
    return "present"


def _ratio_fn(yv: np.ndarray, dm: np.ndarray) -> Callable[[pd.DataFrame, np.ndarray], float]:
    ok = dm & ~np.isnan(yv)
    y0 = np.where(ok, yv, 0.0)

    def f(_d, w):
        wd = w * ok
        s = wd.sum()
        return float(np.dot(wd, y0) / s) if s > 0 else float("nan")
    return f


def weighted_prop(df: pd.DataFrame, y, *, weight: str, domain=None, strata: str = C.STRATA,
                  psu: str = C.PSU, alpha: float = 0.05) -> dict:
    """Weighted proportion (or mean) of `y` in a domain with JK SE/CI and NCHS checks.

    Rows with missing `y` are treated as outside the domain (weight zeroed, row kept).
    Returns est, se, ci_low/ci_high (JK Wald, t with domain df), n (unweighted
    domain size with non-missing y), n_events, n_eff_kish, n_eff (design-based,
    p(1-p)/se^2 capped at n), df (domain df), kg_low/kg_high (Korn-Graubard),
    ci_width (KG), deff, nchs_flags and nchs_status (present / review / suppress).
    """
    yv = _as_values(df, y)
    dm = _as_mask(df, domain)
    ok = dm & ~np.isnan(yv)
    w = df[weight].to_numpy(dtype=float)
    ok &= np.nan_to_num(w) > 0
    jk = jackknife(df, _ratio_fn(yv, ok), weight=weight, strata=strata, psu=psu, alpha=alpha)
    ddf = domain_df(df, ok, strata, psu)
    p, se = jk["est"], jk["se"]
    t = stats.t.ppf(1 - alpha / 2, max(ddf, 1))
    n = int(ok.sum())
    n_events = int(np.nansum(yv[ok] > 0)) if n else 0
    var_srs = p * (1 - p) / n if n else np.nan
    n_eff_design = _design_neff(p, se, n)
    kg = korn_graubard_ci(p, n_eff_design, ddf, alpha, n=n)
    width = kg[1] - kg[0]
    return {
        "est": p, "se": se, "ci_low": p - t * se, "ci_high": p + t * se,
        "n": n, "n_events": n_events, "n_eff_kish": kish_neff(w[ok]), "n_eff": float(n_eff_design),
        "df": ddf, "kg_low": kg[0], "kg_high": kg[1], "ci_width": width,
        "deff": float(se ** 2 / var_srs) if var_srs and var_srs > 0 else float("nan"),
        "nchs_flags": (fl := nchs_flags(n, n_eff_design, width, ddf, p=p, n_events=n_events)),
        "nchs_status": nchs_status(fl),
    }


# --------------------------------------------------------------------------- standardisation
def age_band(age, bands=AGE_BANDS_3) -> pd.Series:
    """Map ages to the labelled bands of `bands` (default 20-39 / 40-59 / 60+)."""
    a = pd.Series(np.asarray(age, dtype=float))
    out = pd.Series(pd.NA, index=a.index, dtype="object")
    for lo, hi, lab in bands:
        out[(a >= lo) & (a <= hi)] = lab
    return out


def _std_stat(yv: np.ndarray, gmask: list[np.ndarray], band: np.ndarray, std: dict):
    """Return stat_fn giving [crude_g..., standardised_g...] for each group mask."""
    labs = list(std)
    sw = np.array([std[k] for k in labs], dtype=float)
    sw = sw / sw.sum()
    y0 = np.nan_to_num(yv)
    valid = ~np.isnan(yv)
    bmasks = [band == k for k in labs]

    def f(_d, w):
        out_c, out_s = [], []
        for g in gmask:
            m = g & valid
            wg = w * m
            s = wg.sum()
            out_c.append(np.dot(wg, y0) / s if s > 0 else np.nan)
            rates = []
            for b in bmasks:
                wb = wg * b
                sb = wb.sum()
                rates.append(np.dot(wb, y0) / sb if sb > 0 else np.nan)
            out_s.append(float(np.dot(sw, rates)))
        return np.array(out_c + out_s, dtype=float)
    return f


def bands_from_std(std: dict) -> list[tuple[int, int, str]]:
    """Parse standard-population keys such as "20-39" or "60+" into (lo, hi, label) bands."""
    out = []
    for k in std:
        if k.endswith("+"):
            out.append((int(k[:-1]), 200, k))
        else:
            lo, hi = k.split("-")
            out.append((int(lo), int(hi), k))
    return out


def _prep_std(df, y, group, age, std=US2000_3BAND):
    yv = _as_values(df, y)
    band = age_band(df[age], bands_from_std(std)).fillna("").to_numpy(dtype=object)
    yv = np.where(band == "", np.nan, yv)
    g = df[group] if isinstance(group, str) else pd.Series(np.asarray(group), index=df.index)
    return yv, band, g


def age_standardise(df: pd.DataFrame, y, group, *, weight: str, std: dict = US2000_3BAND,
                    age: str = "RIDAGEYR", domain=None, strata: str = C.STRATA, psu: str = C.PSU,
                    alpha: float = 0.05) -> pd.DataFrame:
    """Crude and directly age-standardised rates of `y` per level of `group` with JK CIs.

    `group` is a column name or array (use a constant to get the overall rate);
    `domain` optionally restricts all groups further (weights zeroed outside).
    CIs use t with the domain df of each group.
    """
    yv, band, g = _prep_std(df, y, group, age, std)
    dm = _as_mask(df, domain)
    levels = [lv for lv in pd.unique(g.dropna())]
    try:
        levels = sorted(levels)
    except TypeError:
        pass
    gmask = [(g.to_numpy() == lv) & dm for lv in levels]
    jk = jackknife(df, _std_stat(yv, gmask, band, std), weight=weight, strata=strata, psu=psu)
    k = len(levels)
    rows = []
    for i, lv in enumerate(levels):
        m = gmask[i] & ~np.isnan(yv) & (np.nan_to_num(df[weight].to_numpy(float)) > 0)
        ddf = domain_df(df, m, strata, psu)
        t = stats.t.ppf(1 - alpha / 2, max(ddf, 1))
        c, cs = jk["est"][i], jk["se"][i]
        s, ss = jk["est"][k + i], jk["se"][k + i]
        n = int(m.sum())
        kc = korn_graubard_ci(c, _design_neff(c, cs, n), ddf, alpha, n=n)
        ks = korn_graubard_ci(s, _design_neff(s, ss, n), ddf, alpha, n=n)
        rows.append({"group": lv, "n": n, "n_events": int(np.nansum(yv[m] > 0)), "df": ddf,
                     "crude": c, "crude_se": cs, "crude_low": c - t * cs, "crude_high": c + t * cs,
                     "crude_kg_low": kc[0], "crude_kg_high": kc[1],
                     "std": s, "std_se": ss, "std_low": s - t * ss, "std_high": s + t * ss,
                     "std_kg_low": ks[0], "std_kg_high": ks[1]})
    return pd.DataFrame(rows)


def _design_neff(p: float, se: float, n: int) -> float:
    """Design-based effective sample size p(1-p)/se^2, capped at n (NCHS)."""
    if not np.isfinite(p) or not np.isfinite(se) or se <= 0:
        return float(n)
    return float(min(p * (1 - p) / se ** 2, n))


def std_difference(df: pd.DataFrame, y, group, a, b, *, weight: str, std: dict = US2000_3BAND,
                   age: str = "RIDAGEYR", domain=None, strata: str = C.STRATA, psu: str = C.PSU,
                   alpha: float = 0.05) -> dict:
    """Crude and age-standardised difference rate(a) - rate(b) with JK CIs.

    The difference is computed inside every replicate, so the SE accounts for the
    covariance of the two group estimates. df = domain df of (a or b).
    """
    yv, band, g = _prep_std(df, y, group, age, std)
    dm = _as_mask(df, domain)
    ga = (g.to_numpy() == a) & dm
    gb = (g.to_numpy() == b) & dm
    base = _std_stat(yv, [ga, gb], band, std)

    def f(d, w):
        r = base(d, w)
        return np.array([r[0] - r[1], r[2] - r[3], r[0], r[1], r[2], r[3]])
    pos = np.nan_to_num(df[weight].to_numpy(float)) > 0
    valid = ~np.isnan(yv) & pos
    ddf = domain_df(df, (ga | gb) & valid, strata, psu)
    jk = jackknife(df, f, weight=weight, strata=strata, psu=psu, df_override=ddf, alpha=alpha)
    e, s, lo, hi = jk["est"], jk["se"], jk["ci_low"], jk["ci_high"]
    return {
        "a": a, "b": b, "n_a": int((ga & valid).sum()), "n_b": int((gb & valid).sum()), "df": ddf,
        "rate_a_crude": e[2], "rate_b_crude": e[3], "rate_a_std": e[4], "rate_b_std": e[5],
        "crude_diff": e[0], "crude_se": s[0], "crude_low": lo[0], "crude_high": hi[0],
        "std_diff": e[1], "std_se": s[1], "std_low": lo[1], "std_high": hi[1],
    }


# --------------------------------------------------------------------------- bootstrap
def rao_wu_weights(df: pd.DataFrame, weight: str | np.ndarray, n_rep: int, *, seed: int,
                   strata: str = C.STRATA, psu: str = C.PSU) -> np.ndarray:
    """Rao-Wu rescaled bootstrap weights with m_h = n_h - 1 PSUs drawn per stratum.

    With m_h = n_h - 1 the rescaling factor reduces to w* = w * n_h/(n_h-1) * r_hi
    (r_hi = times PSU i was drawn), i.e. for 2-PSU strata one PSU is kept at double
    weight and the other is dropped. Returns an (n_rows, n_rep) matrix.
    """
    rng = np.random.default_rng(seed)
    w = df[weight].to_numpy(dtype=float) if isinstance(weight, str) else np.asarray(weight, dtype=float)
    w = np.nan_to_num(w)
    s = df[strata].to_numpy()
    p = df[psu].to_numpy()
    mult = np.ones((len(df), n_rep))
    for h in np.unique(s):
        in_h = s == h
        psus = np.unique(p[in_h])
        nh = len(psus)
        if nh < 2:
            continue
        draws = rng.integers(0, nh, size=(n_rep, nh - 1))
        counts = np.stack([(draws == j).sum(axis=1) for j in range(nh)], axis=1)  # n_rep x nh
        for j, i in enumerate(psus):
            mult[in_h & (p == i)] = counts[:, j] * nh / (nh - 1)
    return w[:, None] * mult
