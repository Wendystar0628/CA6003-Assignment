"""NHANES 2021-23 (`_L`) loading, XPT repair, sentinel recoding and cohort construction (S2-S3).

Contract (docs/architecture.md §3) – signatures are binding:

    COHORT_N = 5730
    ensure_raw_data(download=True) -> dict
    read_xpt(name) -> DataFrame                         raw pandas.read_sas, no value fixes
    fix_xpt(df) -> (DataFrame, n_fixed)                 |x| < 1e-10 and notna -> 0.0 (NaN stays NaN)
    load_spec() -> DataFrame                            config/variable_spec.csv
    apply_sentinels(df, spec=None, mode=...) -> (clean, audit)
    load_merged(files=None, *, fix=True, sentinels="per_variable") -> DataFrame
    build_cohort(df=None, *, sentinels="per_variable") -> DataFrame   (5,730 rows, asserted)
    funnel() -> DataFrame                               step, n

Design notes
- `config/variable_spec.csv` is the single source of truth: which columns are kept
  (``use_tier != "excluded"``), the per-variable refusal/don't-know codes
  (``sentinel_codes``, parsed from the CDC codebooks) and roles.
- The XPT "zero artefact": pandas reads a stored 0 as 5.397605e-79 (= 16**-65). The
  repair uses ``mask`` (never ``where``) so that NaN stays NaN.
- Cohort membership is decided on the un-recoded values, so the cohort is the same
  5,730 people under every sentinel mode; only the column values differ. This is what
  lets S3/S6 measure the damage of a blanket recode on a fixed population.
"""
from __future__ import annotations

import hashlib
import html
import re
import urllib.request
import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C

COHORT_N: int = 5730
FUNNEL_EXPECTED = (11933, 7809, 6064, 5767, 5730)

#: codes a naive cleaner treats as missing everywhere (S3 blanket arm, S6 M0)
BLANKET_CODES = (7, 9, 77, 99, 777, 999, 7777, 9999)

#: 20 continuous candidates on which the blanket-recode damage is measured (S3 §4)
CONTINUOUS_CANDIDATES = (
    "RIDAGEYR", "INDFMPIR",
    "BMXWT", "BMXHT", "BMXBMI", "BMXWAIST", "BMXHIP", "BMXARMC",
    "BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3",
    "BPXOPLS1", "BPXOPLS2", "BPXOPLS3",
    "LBXGH", "LBXTC", "LBDHDD",
)
#: questionnaire items of the "questionnaire-only" intermediate recode arm (S3 §4)
QUESTIONNAIRE_ITEMS = ("HIQ011", "HUQ030", "BPQ020", "BPQ080", "SMQ020", "DMDEDUC2")

BP_SYS = ("BPXOSY1", "BPXOSY2", "BPXOSY3")
BP_DIA = ("BPXODI1", "BPXODI2", "BPXODI3")
WEIGHTS = (C.WEIGHT_INTERVIEW, C.WEIGHT_MEC, C.WEIGHT_PHLEB, C.WEIGHT_FASTING)
DESIGN = (C.STRATA, C.PSU)

RACE_LABELS = {1: "Mexican American", 2: "Other Hispanic", 3: "NH White",
               4: "NH Black", 6: "NH Asian", 7: "Other/Multi"}
RACE_ORDER = ("NH White", "NH Black", "NH Asian", "Mexican American", "Other Hispanic", "Other/Multi")
SEX_LABELS = {1: "Male", 2: "Female"}

SENTINEL_MODES = ("per_variable", "blanket", "none")


# ---------------------------------------------------------------------------
# raw files and integrity
# ---------------------------------------------------------------------------
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest() -> dict[str, str]:
    out = {}
    for line in C.MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.lstrip("*")] = digest
    return out


def ensure_raw_data(download: bool = True) -> dict:
    """Verify the 16 raw XPT files against MANIFEST.sha256; fetch missing ones from CDC.

    Returns ``{"n_files", "verified", "mismatched", "downloaded", "sha256"}``. A hash
    mismatch is reported (CDC occasionally re-releases files) but does not raise; the
    S0/S3 notebooks assert ``mismatched == []``.
    """
    manifest = _manifest()
    verified, mismatched, downloaded, digests = [], [], [], {}
    for name in C.NHANES_FILES:
        path = C.RAW_DIR / f"{name}.xpt"
        if not path.exists():
            if not download:
                raise FileNotFoundError(f"{path.name} missing and download=False")
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".xpt.part")
            with urllib.request.urlopen(f"{C.CDC_BASE_URL}/{name}.xpt", timeout=300) as r:
                tmp.write_bytes(r.read())
            tmp.replace(path)
            downloaded.append(name)
        digest = _sha256(path)
        digests[path.name] = digest
        if manifest.get(path.name) == digest:
            verified.append(name)
        else:
            mismatched.append(name)
            warnings.warn(f"{path.name}: sha256 differs from MANIFEST.sha256", stacklevel=2)
    return {"n_files": len(C.NHANES_FILES), "verified": verified, "mismatched": mismatched,
            "downloaded": downloaded, "sha256": digests}


def read_xpt(name: str) -> pd.DataFrame:
    """Read one raw XPT file exactly as pandas returns it (no value repairs).

    Character columns are decoded (latin-1) to ``str``; numeric values are untouched,
    so the 5.4e-79 zero artefact is still present.
    """
    name = name.removesuffix(".xpt")
    return pd.read_sas(C.RAW_DIR / f"{name}.xpt", format="xport", encoding="latin-1")


def _artefact_mask(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes("number")
    return (num.abs() < C.XPT_ZERO_EPS) & num.notna() & (num != 0)


def fix_xpt(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Repair the XPT zero artefact: ``x.mask((|x| < 1e-10) & x.notna(), 0.0)``.

    Returns ``(fixed_copy, n_fixed)`` where ``n_fixed`` counts cells that actually
    changed (0 < |x| < 1e-10). NaN is preserved (``where`` would turn NaN into 0).
    """
    out = df.copy()
    num = out.select_dtypes("number").columns
    n_fixed = int(_artefact_mask(out).to_numpy().sum())
    x = out[num]
    out[num] = x.mask((x.abs() < C.XPT_ZERO_EPS) & x.notna(), 0.0)
    assert int(out[num].isna().to_numpy().sum()) == int(x.isna().to_numpy().sum()), "fix_xpt changed NaN count"
    return out, n_fixed


def xpt_artefact_audit(files=None) -> pd.DataFrame:
    """Per file x variable count of 0 < |x| < 1e-10 cells in the raw XPT (S3 §1)."""
    rows = []
    for name in files or C.NHANES_FILES:
        m = _artefact_mask(read_xpt(name))
        for var, n in m.sum().items():
            rows.append({"file": name, "var": var, "n_artefact": int(n)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# codebooks and variable spec
# ---------------------------------------------------------------------------
_BLOCK = re.compile(r'<h3 class="vartitle" id="([^"]+)">(.*?)</h3>(.*?)(?=<h3 class="vartitle"|\Z)', re.S)
_ROW = re.compile(r'<tr>\s*<td scope="row" class="values">(.*?)</td>\s*<td class="values">(.*?)</td>\s*'
                  r'<td class="values" align="right">(.*?)</td>', re.S)
_TARGET = re.compile(r"<dt>Target: </dt>\s*<dd>(.*?)</dd>", re.S)
SENTINEL_DESC = re.compile(r"^(?:refused|don'?t know)$", re.I)
TOPCODE_DESC = re.compile(r"(?:or more|or older|and over|greater than or equal)", re.I)


def _clean_text(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


@lru_cache(maxsize=None)
def parse_codebook(name: str) -> pd.DataFrame:
    """Parse a CDC codebook (.htm) into one row per (variable, code/value row).

    Columns: file, var (upper case, as in the XPT), anchor (codebook id), label,
    target, code, desc, count.
    """
    name = name.removesuffix(".htm")
    text = (C.CODEBOOK_DIR / f"{name}.htm").read_text(encoding="utf-8", errors="replace")
    rows = []
    for anchor, title, body in _BLOCK.findall(text):
        label = _clean_text(title).split(" - ", 1)[-1]
        target = " | ".join(_clean_text(t) for t in _TARGET.findall(body))
        values = _ROW.findall(body)
        if not values:
            rows.append(dict(file=name, var=anchor.upper(), anchor=anchor, label=label, target=target,
                             code=None, desc=None, count=None))
        for code, desc, cnt in values:
            cnt = _clean_text(cnt)
            rows.append(dict(file=name, var=anchor.upper(), anchor=anchor, label=label, target=target,
                             code=_clean_text(code), desc=_clean_text(desc),
                             count=int(cnt) if cnt.isdigit() else None))
    return pd.DataFrame(rows)


def codebook_table(files=None) -> pd.DataFrame:
    """All codebooks stacked (see `parse_codebook`)."""
    return pd.concat([parse_codebook(f) for f in files or C.NHANES_FILES], ignore_index=True)


def _num(s: str):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return int(v) if v.is_integer() else v


def spec_from_codebooks(files=None) -> pd.DataFrame:
    """Codebook-derived spec fields per (file, var).

    Returns var, file, label, universe, valid_min, valid_max, sentinel_codes, top_code,
    special_codes, has_range, codebook_url. ``sentinel_codes`` are exactly the codes
    whose value description is "Refused" or "Don't know"; continuous lab/exam measures
    only list "Range of Values" and "Missing", so they get none.
    """
    out = []
    for (file, var), g_all in codebook_table(files).groupby(["file", "var"], sort=False):
        head = g_all.iloc[0]
        g = g_all.dropna(subset=["code"])
        rng = g[g["desc"].eq("Range of Values")]
        lows, highs = [], []
        for c in rng["code"]:
            parts = [p.strip() for p in c.split(" to ")]
            if len(parts) == 2 and _num(parts[0]) is not None:
                lows.append(_num(parts[0]))
                highs.append(_num(parts[1]))
        sent = g[g["desc"].str.match(SENTINEL_DESC)]
        top = g[g["desc"].str.contains(TOPCODE_DESC) & g["code"].map(lambda c: _num(c) is not None)]
        other = g[~g.index.isin(rng.index) & ~g.index.isin(sent.index) & ~g["desc"].eq("Missing")]
        cat_codes = [_num(c) for c in other["code"] if _num(c) is not None]
        if lows:
            vmin, vmax = min(lows), max(highs)
            special = other[~other.index.isin(top.index)]
        else:
            vmin = min(cat_codes) if cat_codes else None
            vmax = max(cat_codes) if cat_codes else None
            special = other.iloc[0:0]
        out.append(dict(
            var=var, file=file, label=head["label"], universe=head["target"],
            valid_min=vmin, valid_max=vmax,
            sentinel_codes=";".join(str(_num(c)) for c in sent["code"]),
            top_code=";".join(str(_num(c)) for c in top["code"]),
            special_codes="; ".join(f"{c}={d}" for c, d in zip(special["code"], special["desc"])),
            has_range=bool(lows),
            codebook_url=f"{C.CDC_BASE_URL}/{file}.htm#{head['anchor']}",
        ))
    return pd.DataFrame(out)


def _codes(s) -> list:
    if s is None or (isinstance(s, float) and np.isnan(s)) or str(s).strip() == "":
        return []
    return [_num(c) for c in str(s).split(";") if c.strip()]


def load_spec() -> pd.DataFrame:
    """Read config/variable_spec.csv (one row per file x variable, incl. excluded columns)."""
    spec = pd.read_csv(C.VARIABLE_SPEC, dtype=str, keep_default_na=False)
    for col in ("valid_min", "valid_max"):
        spec[col] = pd.to_numeric(spec[col], errors="coerce")
    return spec


def included(spec: pd.DataFrame | None = None) -> pd.DataFrame:
    """Spec rows that the loader keeps (``use_tier != 'excluded'``)."""
    spec = load_spec() if spec is None else spec
    return spec[spec["use_tier"] != "excluded"]


def sentinel_map(spec: pd.DataFrame | None = None) -> dict[str, list]:
    """var -> list of codebook refusal/don't-know codes (included variables only)."""
    inc = included(spec)
    out = {}
    for var, s in zip(inc["var"], inc["sentinel_codes"]):
        codes = _codes(s)
        if codes:
            out[var] = codes
    return out


def verify_spec(spec: pd.DataFrame | None = None) -> list[str]:
    """Cross-check the spec against codebooks and XPT columns; returns a list of problems.

    Checks: every XPT column has exactly one spec row and vice versa; codebook-derived
    columns (sentinel_codes, top_code, valid range, url) equal a fresh codebook parse;
    every included variable has role, admissible, admiss_reason and use_tier.
    """
    spec = load_spec() if spec is None else spec
    problems = []
    cb = spec_from_codebooks().set_index(["file", "var"])
    for name in C.NHANES_FILES:
        cols = set(read_xpt(name).columns)
        s = set(spec.loc[spec["file"] == name, "var"])
        if cols != s:
            problems.append(f"{name}: XPT-only {sorted(cols - s)}, spec-only {sorted(s - cols)}")
    if spec.duplicated(["file", "var"]).any():
        problems.append("duplicate (file, var) rows")
    for _, r in spec.iterrows():
        key = (r["file"], r["var"])
        if key not in cb.index:
            problems.append(f"{key}: not in codebook")
            continue
        ref = cb.loc[key]
        if _codes(r["sentinel_codes"]) != _codes(ref["sentinel_codes"]):
            problems.append(f"{key}: sentinel_codes {r['sentinel_codes']!r} != codebook {ref['sentinel_codes']!r}")
        if _codes(r["top_code"]) != _codes(ref["top_code"]):
            problems.append(f"{key}: top_code {r['top_code']!r} != codebook {ref['top_code']!r}")
        if r["codebook_url"] != ref["codebook_url"]:
            problems.append(f"{key}: codebook_url mismatch")
        if r["use_tier"] != "excluded":
            for col in ("role", "admissible", "admiss_reason", "dtype"):
                if not str(r[col]).strip():
                    problems.append(f"{key}: empty {col}")
            if r["admissible"] not in ("N", "T1", "T2"):
                problems.append(f"{key}: admissible={r['admissible']!r}")
        elif not str(r["note"]).strip():
            problems.append(f"{key}: excluded without reason in note")
    # an included variable name must map to one sentinel definition
    inc = included(spec)
    for var, g in inc.groupby("var"):
        if g["sentinel_codes"].nunique() > 1:
            problems.append(f"{var}: conflicting sentinel codes across files")
    return problems


# ---------------------------------------------------------------------------
# sentinels
# ---------------------------------------------------------------------------
def apply_sentinels(df: pd.DataFrame, spec: pd.DataFrame | None = None,
                    mode: str = "per_variable") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recode refusal / don't-know codes to NaN.

    mode="per_variable": only the codes listed for that variable in the codebook
        (``sentinel_codes`` of the spec). Continuous measures have none, so e.g.
        LBXGH = 7.0 % or DBP = 77 mmHg stay valid.
    mode="blanket": the naive rule ``replace({7, 9, 77, 99, 777, 999, 7777, 9999}, NaN)``
        on every numeric column except identifiers, design variables and weights.
    mode="none": no recoding (audit is empty).

    Blank strings in character columns (codebook "< blank > = Missing") become NaN in
    every mode except "none". Returns ``(clean_copy, audit)``; audit has one row per
    recoded variable: var, mode, codes, n_nonmissing_before, n_recoded, by_code.
    """
    assert mode in SENTINEL_MODES, mode
    out = df.copy()
    rows = []
    if mode == "none":
        return out, pd.DataFrame(columns=["var", "mode", "codes", "n_nonmissing_before", "n_recoded", "by_code"])
    for col in out.columns:
        if out[col].dtype == object:
            blank = out[col].astype("string").str.strip().eq("").fillna(False).to_numpy(bool)
            if blank.any():
                out.loc[blank, col] = np.nan
    if mode == "per_variable":
        targets = {v: c for v, c in sentinel_map(spec).items() if v in out.columns}
    else:
        protected = {"SEQN", *DESIGN, *WEIGHTS}
        targets = {v: list(BLANKET_CODES) for v in out.select_dtypes("number").columns if v not in protected}
    for var, codes in targets.items():
        x = out[var]
        hit = x.isin(codes)
        n = int(hit.sum())
        by = x[hit].value_counts().sort_index()
        rows.append({"var": var, "mode": mode, "codes": ";".join(map(str, codes)),
                     "n_nonmissing_before": int(x.notna().sum()), "n_recoded": n,
                     "by_code": ";".join(f"{_num(k)}:{v}" for k, v in by.items())})
        if n:
            out[var] = x.mask(hit)
    return out, pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# merging and cohort
# ---------------------------------------------------------------------------
def load_file(name: str, *, fix: bool = True, spec: pd.DataFrame | None = None,
              minimise: bool = True) -> tuple[pd.DataFrame, int]:
    """One file, optionally repaired and reduced to the spec's included columns."""
    df = read_xpt(name)
    n_fixed = 0
    if fix:
        df, n_fixed = fix_xpt(df)
    if minimise:
        inc = included(spec)
        keep = inc.loc[inc["file"] == name, "var"].tolist()
        df = df[[c for c in df.columns if c in keep]]
    return df, n_fixed


def load_merged(files=None, *, fix: bool = True, sentinels: str = "per_variable",
                minimise: bool = True) -> pd.DataFrame:
    """Left-join the requested files onto DEMO_L by SEQN (11,933 rows).

    Columns are reduced to the spec's included variables (data minimisation); duplicate
    weight columns in TCHOL/HDL/TRIGLY are excluded in the spec. ``fix`` repairs the XPT
    zero artefact; ``sentinels`` in {"per_variable", "blanket", "none"}.
    ``df.attrs`` carries ``n_fixed`` (dict per file) and ``sentinel_audit`` as a list of
    plain dict records (never a DataFrame: pandas compares attrs with ``==`` in concat);
    use ``sentinel_audit_of(df)`` to get it back as a DataFrame.
    """
    spec = load_spec()
    files = list(files or C.NHANES_FILES)
    if "DEMO_L" in files:
        files.remove("DEMO_L")
    df, n0 = load_file("DEMO_L", fix=fix, spec=spec, minimise=minimise)
    n_fixed = {"DEMO_L": n0}
    for name in files:
        part, n = load_file(name, fix=fix, spec=spec, minimise=minimise)
        n_fixed[name] = n
        assert part["SEQN"].is_unique, name
        dup = [c for c in part.columns if c in df.columns and c != "SEQN"]
        part = part.drop(columns=dup)
        df = df.merge(part, on="SEQN", how="left", validate="one_to_one")
    df, audit = apply_sentinels(df, spec, mode=sentinels)
    df.attrs["n_fixed"] = n_fixed
    df.attrs["sentinel_audit"] = audit.to_dict("records")
    return df


def cohort_mask(df: pd.DataFrame) -> pd.Series:
    """Adults >= 20, interviewed + examined, HbA1c present, not pregnant (RIDEXPRG != 1)."""
    return ((df["RIDAGEYR"] >= C.ADULT_MIN_AGE) & (df["RIDSTATR"] == 2)
            & df["LBXGH"].notna() & (df["RIDEXPRG"] != 1))


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Derived columns: BP means, WHtR, top-code / missing flags, readable race and sex."""
    out = df.copy()
    out["bp_sys_mean"] = out[list(BP_SYS)].mean(axis=1, skipna=True)
    out["bp_dia_mean"] = out[list(BP_DIA)].mean(axis=1, skipna=True)
    out["whtr"] = out["BMXWAIST"] / out["BMXHT"]
    out["age_top"] = (out["RIDAGEYR"] == 80).astype(int)
    out["pir_top"] = (out["INDFMPIR"] == 5).astype(int)
    out["pir_miss"] = out["INDFMPIR"].isna().astype(int)
    out["preg_unknown"] = (out["RIDEXPRG"] == 3).astype(int)
    out["race"] = out["RIDRETH3"].map(RACE_LABELS)
    out["sex"] = out["RIAGENDR"].map(SEX_LABELS)
    return out


def build_cohort(df: pd.DataFrame | None = None, *, sentinels: str = "per_variable",
                 fix: bool = True) -> pd.DataFrame:
    """Analysis cohort (N = 5,730, asserted) with derived columns.

    Membership is evaluated on un-recoded values (``df`` should therefore come from
    ``load_merged(..., sentinels="none")`` if given); the requested sentinel mode is
    applied afterwards, so every mode yields the same 5,730 people.

    Derived: bp_sys_mean, bp_dia_mean (mean of available readings 1-3), whtr =
    BMXWAIST/BMXHT, age_top (RIDAGEYR == 80), pir_top (INDFMPIR == 5), pir_miss,
    preg_unknown (RIDEXPRG == 3, kept and flagged), race (labelled RIDRETH3), sex.
    """
    if df is None:
        df = load_merged(fix=fix, sentinels="none")
    coh = df.loc[cohort_mask(df)].copy()
    coh, audit = apply_sentinels(coh, mode=sentinels)
    coh = add_derived(coh).sort_values("SEQN").reset_index(drop=True)
    coh["SEQN"] = coh["SEQN"].astype(int)
    assert len(coh) == COHORT_N, f"cohort has {len(coh)} rows, expected {COHORT_N}"
    assert coh["SEQN"].is_unique
    coh.attrs["sentinel_audit"] = audit.to_dict("records")
    coh.attrs["sentinels"] = sentinels
    return coh


def funnel(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Sample funnel DEMO -> cohort as a table (step, n, dropped)."""
    if df is None:
        df = load_merged(files=["DEMO_L", "GHB_L"], sentinels="none")
    s1 = df["RIDAGEYR"] >= C.ADULT_MIN_AGE
    s2 = s1 & (df["RIDSTATR"] == 2)
    s3 = s2 & df["LBXGH"].notna()
    s4 = s3 & (df["RIDEXPRG"] != 1)
    steps = [("DEMO_L participants", len(df)), ("Age >= 20", int(s1.sum())),
             ("Interviewed and MEC-examined (RIDSTATR = 2)", int(s2.sum())),
             ("HbA1c measured (LBXGH present)", int(s3.sum())),
             ("Not pregnant (RIDEXPRG != 1)", int(s4.sum()))]
    out = pd.DataFrame(steps, columns=["step", "n"])
    out["dropped"] = (-out["n"].diff()).fillna(0).astype(int)
    return out


def sentinel_audit_of(df: pd.DataFrame) -> pd.DataFrame:
    """Sentinel audit attached by `load_merged` / `build_cohort`, as a DataFrame."""
    return pd.DataFrame(df.attrs.get("sentinel_audit", []))


def zero_weights_to_nan(df: pd.DataFrame, cols=WEIGHTS) -> pd.DataFrame:
    """Weight 0 means 'not examined' / 'no blood sample' (codebook) – set to NaN before weighting."""
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].mask(out[c] == 0)
    return out


def minimisation_report(spec: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Data-minimisation report from the spec (S2 §6).

    Returns ``(per_file, per_column)``: per file the raw rows/columns and the number of
    kept and dropped columns; per column the decision and its reason (``note`` for
    excluded columns, ``role``/``admiss_reason`` for kept ones).
    """
    spec = load_spec() if spec is None else spec
    files, cols = [], []
    for name in C.NHANES_FILES:
        raw = read_xpt(name)
        s = spec[spec["file"] == name]
        kept = s[s["use_tier"] != "excluded"]
        dropped = s[s["use_tier"] == "excluded"]
        tier = kept.loc[kept["var"] != "SEQN", "use_tier"]
        files.append({"file": name, "use_tier": tier.iloc[0] if len(tier) else "excluded",
                      "rows": len(raw), "cols_raw": raw.shape[1], "cols_kept": len(kept),
                      "cols_dropped": len(dropped),
                      "kept": " ".join(kept["var"]), "dropped": " ".join(dropped["var"])})
        for _, r in s.iterrows():
            keep = r["use_tier"] != "excluded"
            cols.append({"file": name, "var": r["var"], "decision": "keep" if keep else "drop",
                         "use_tier": r["use_tier"], "role": r["role"],
                         "reason": f"{r['role']}: {r['admiss_reason']}" if keep else r["note"]})
    return pd.DataFrame(files), pd.DataFrame(cols)
