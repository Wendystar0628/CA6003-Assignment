# %% [markdown]
# # §2 Data profiling and quality audit (Stages S2–S3)
#
# This section works out where the data can be trusted and where they cannot, and turns each finding into a recorded decision. It starts by re-checking the provenance and specification work of Stage S2 (hashes, codebook-derived specification, minimisation). The Stage S3 audit follows in nine numbered items:
#
# 1. XPT read artefact and zero-weight semantics
# 2. Completeness, uniqueness and the sample funnel
# 3. Per-variable sentinel map
# 4. Cost of a blanket recode
# 5. Consistency checks
# 6. Top-coding
# 7. Missing-data mechanism for HbA1c
# 8. Outliers: a three-layer rule
# 9. Data-quality dimension matrix
#
# Each item follows the same pattern: *why* the check is needed, the code that computes it, and *so what*, giving the computed numbers and the decision they support. Numbers that the process document fixes (§8) are asserted with a tolerance. Every number is stored in `results/metrics_S2.json` / `results/metrics_S3.json`, tables in `results/S3/`, and the decisions in `governance/register/S2.csv` and `S3.csv`.

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
from IPython.display import display

from src import nhanes_io as io

pd.set_option("display.width", 160, "display.max_colwidth", 70, "display.max_rows", 80)
OI = C.OKABE_ITO
OUT = C.RESULTS_DIR / "S3"
OUT.mkdir(parents=True, exist_ok=True)
(C.RESULTS_DIR / "S2").mkdir(parents=True, exist_ok=True)
TODAY = "2026-10-11"
REGISTER_COLS = ["dr_id", "stage", "date", "type", "finding", "evidence_ref", "evidence_value", "decision",
                 "alternatives_rejected", "hyp_id", "status", "check_verdict", "check_note", "loop_ref",
                 "change_request", "commit"]
M2, M3 = {}, {}   # metrics stored for S2 and S3


def close(a, b, tol=0.0):
    """Assert helper: |a - b| <= tol."""
    return abs(float(a) - float(b)) <= tol


def write_register(stage, rows):
    reg = pd.DataFrame(rows)
    for c in REGISTER_COLS:
        if c not in reg:
            reg[c] = ""
    reg = reg[REGISTER_COLS]
    reg.to_csv(C.GOVERNANCE_DIR / "register" / f"{stage}.csv", index=False, lineterminator="\n")
    return reg


# %% [markdown]
# ## 0 Provenance, specification and minimisation (Stage S2 checks)
#
# **Why.** An audit is only as good as its inputs. Three things are checked before any profiling:
#
# - the raw files are the unmodified CDC files (SHA-256 against `MANIFEST.sha256`);
# - the variable specification `config/variable_spec.csv` agrees with the CDC codebooks and with the columns actually present in the XPT files, because every sentinel code must have a traceable source;
# - the loader keeps only what the purpose needs (data minimisation, GDPR Art. 5(1)(c)).

# %%
integrity = io.ensure_raw_data(download=False)
print(f"raw files verified against MANIFEST.sha256: {len(integrity['verified'])}/{integrity['n_files']}; mismatched: {integrity['mismatched']}")
assert integrity["mismatched"] == [] and len(integrity["verified"]) == 16

spec = io.load_spec()
problems = io.verify_spec(spec)
print("verify_spec problems:", problems or "none")
assert problems == []

inc = io.included(spec)
role_tab = (inc[inc["var"] != "SEQN"].groupby(["role", "admissible"]).size().unstack(fill_value=0))
display(role_tab)
tier_tab = spec[spec["var"] != "SEQN"].groupby("use_tier").size().rename("variables").to_frame()
display(tier_tab)

min_files, min_cols = io.minimisation_report(spec)
min_files.to_csv(C.RESULTS_DIR / "S2" / "minimisation_report.csv", index=False, lineterminator="\n")
min_cols.to_csv(C.RESULTS_DIR / "S2" / "minimisation_columns.csv", index=False, lineterminator="\n")
display(min_files[["file", "use_tier", "rows", "cols_raw", "cols_kept", "cols_dropped"]])
n_raw, n_kept, n_drop = (int(min_files[c].sum()) for c in ("cols_raw", "cols_kept", "cols_dropped"))
print(f"columns: raw {n_raw}, kept {n_kept}, dropped {n_drop}; every dropped column has a reason:",
      bool(min_cols.loc[min_cols["decision"] == "drop", "reason"].str.len().gt(0).all()))
assert n_raw == len(spec) == 175 and n_kept + n_drop == n_raw
assert min_cols.loc[min_cols["decision"] == "drop", "reason"].str.len().gt(0).all()

n_sentinel_vars = len(io.sentinel_map(spec))
cont_inc = inc[(inc["dtype"] == "continuous") & inc["file"].isin(["BMX_L", "BPXO_L", "GHB_L", "TCHOL_L", "HDL_L", "GLU_L", "TRIGLY_L"])]
print(f"included variables with codebook refusal/don't-know codes: {n_sentinel_vars}; "
      f"continuous lab/exam measures with such codes: {int((cont_inc['sentinel_codes'] != '').sum())} of {len(cont_inc)}")
assert (cont_inc["sentinel_codes"] == "").all() and len(cont_inc) == 21 and n_sentinel_vars == 25

# %% [markdown]
# **So what.** All 16 raw files match their recorded hashes, so every number below comes from the CDC release dated 2026-10-10. The specification has one row for each of the 175 raw columns, and `verify_spec` finds no disagreement with the codebooks or the XPT headers. The loader keeps 78 columns and drops 97. Each dropped column has a stated reason: child-only items, country of birth and years in the US (quasi-identifiers), military service, household reference-person fields, SI-unit duplicates, unrelated MCQ items and duplicate weight columns.
#
# 25 included variables carry codebook refusal or don't-know codes, and all of them are questionnaire items. None of the 21 continuous laboratory and examination measures has such a code. The per-variable sentinel map therefore leaves every measurement untouched; item 4 shows why this matters.

# %%
M2.update({
    "raw_files_verified": len(integrity["verified"]), "hash_mismatches": len(integrity["mismatched"]),
    "spec_rows": len(spec), "spec_problems": len(problems),
    "minimisation": {"cols_raw": n_raw, "cols_kept": n_kept, "cols_dropped": n_drop,
                     "per_file": min_files.set_index("file")[["cols_raw", "cols_kept", "cols_dropped"]].to_dict("index")},
    "use_tier_counts": tier_tab["variables"].to_dict(),
    "role_admissible": {f"{r}|{a}": int(v) for (r, a), v in role_tab.stack().items() if v},
    "n_sentinel_variables": n_sentinel_vars,
})

# %% [markdown]
# ## 1 XPT read artefact and zero-weight semantics
#
# **Why.** When pandas reads a SAS transport (XPT) file, a stored zero comes back as 5.397605e-79 (= 16⁻⁶⁵). This is a floating-point artefact of the reader, not a SAS missing-value code. Left in place it creates a spurious minimum and breaks `== 0` tests such as "zero weight" or "no activity". The repair has to keep NaN as NaN. `x.where(|x| >= 1e-10, 0)` is the tempting one-liner, but it also turns every NaN into 0, because NaN fails the comparison.

# %%
art = io.xpt_artefact_audit()
art_file = art.groupby("file")["n_artefact"].sum().reindex(C.NHANES_FILES)
art_vars = art[art["n_artefact"] > 0].sort_values(["file", "n_artefact"], ascending=[True, False])
display(art_vars.reset_index(drop=True))
n_art = int(art_file.sum())
files_hit = art_file[art_file > 0].index.tolist()
print(f"artefact cells: {n_art:,} in {len(files_hit)} files {files_hit}; clean files: {art_file[art_file == 0].index.tolist()}")
art.to_csv(OUT / "xpt_artefacts.csv", index=False, lineterminator="\n")

# demonstrate the NaN-preservation requirement on one affected file
paq = io.read_xpt("PAQ_L")
fixed, n_fixed = io.fix_xpt(paq)
num = paq.select_dtypes("number")
wrong = num.where(num.abs() >= C.XPT_ZERO_EPS, 0.0)   # the tempting `where` version: NaN fails the test -> 0
nan_before, nan_after, nan_wrong = int(num.isna().sum().sum()), int(fixed[num.columns].isna().sum().sum()), int(wrong.isna().sum().sum())
residual = int(io._artefact_mask(fixed).to_numpy().sum())
print(f"PAQ_L: fixed {n_fixed:,} cells; NaN before {nan_before:,}, after mask-fix {nan_after:,}, after where-fix {nan_wrong:,}; residual 0<|x|<1e-10: {residual}")
assert nan_after == nan_before and residual == 0 and nan_wrong < nan_before

# whole-project check: all files repaired, NaN count unchanged
tot_fixed = 0
for f in C.NHANES_FILES:
    raw = io.read_xpt(f)
    fx, k = io.fix_xpt(raw)
    tot_fixed += k
    assert io._artefact_mask(fx).to_numpy().sum() == 0
    assert fx.select_dtypes("number").isna().sum().sum() == raw.select_dtypes("number").isna().sum().sum()
assert n_art == tot_fixed == 13676 and len(files_hit) == 9

# %% [markdown]
# Several of the repaired zeros have a meaning defined in the codebook. A zero weight marks a participant outside that weight's sub-sample, so it must become missing before any weighted calculation:

# %%
demo = io.load_file("DEMO_L", minimise=False)[0]
ghb = io.load_file("GHB_L", minimise=False)[0]
glu = io.load_file("GLU_L", minimise=False)[0]
zw = pd.DataFrame([
    ["WTMEC2YR = 0", int((demo["WTMEC2YR"] == 0).sum()), "not MEC-examined", int((demo["RIDSTATR"] == 1).sum())],
    ["WTPH2YR = 0 (GHB_L)", int((ghb["WTPH2YR"] == 0).sum()), "no blood sample provided", None],
    ["WTSAF2YR = 0 (GLU_L)", int((glu["WTSAF2YR"] == 0).sum()), "fasting sub-sample non-response", None],
], columns=["condition", "n", "codebook meaning", "cross-check: RIDSTATR = 1 (interview only)"])
display(zw)
coh = io.build_cohort()
zero_in_cohort = int((coh["WTPH2YR"] == 0).sum())
print(f"cohort rows with WTPH2YR = 0: {zero_in_cohort}; WTPH2YR missing: {int(coh['WTPH2YR'].isna().sum())}")
assert zw.loc[0, "n"] == 3073 == zw.loc[0, "cross-check: RIDSTATR = 1 (interview only)"]
assert zw.loc[1, "n"] == 449 and zero_in_cohort == 0

# %% [markdown]
# **So what.** The artefact affects 13,676 cells in 9 of the 16 files: DEMO, GHB, GLU, TCHOL, HDL, TRIGLY, INQ, SMQ and PAQ. BMX, BPXO, DIQ, BPQ, MCQ, HIQ and HUQ are clean. Most of the affected cells are weights or frequencies whose true value is 0. Examples are the 3,073 zero exam weights and the 4,413 people with zero vigorous-activity sessions (`PAD810Q`).
#
# On `PAQ_L` the `mask` repair keeps the NaN count unchanged. The `where` version would silently turn the missing cells into zeros, which reads as "no physical activity" for people who never answered. After the repair no value with 0 < |x| < 10⁻¹⁰ remains in any file.
#
# The zero weights carry meaning. The 3,073 rows with `WTMEC2YR = 0` are exactly the 3,073 interview-only participants (`RIDSTATR = 1`), and `WTPH2YR = 0` marks the 449 people without a blood sample. Every cohort member has a positive `WTPH2YR`. **Decision (DR-S3-01):** repair the artefact with `mask` at load time (`nhanes_io.fix_xpt`). Zero weights become NaN before any weighted analysis (`nhanes_io.zero_weights_to_nan`).

# %%
M3["xpt_artefact"] = {"cells": n_art, "files": files_hit, "n_files": len(files_hit),
                      "per_file": {k: int(v) for k, v in art_file.items() if v},
                      "paq_nan_before": nan_before, "paq_nan_after_mask": nan_after, "paq_nan_after_where": nan_wrong}
M3["zero_weights"] = {"WTMEC2YR_0": int(zw.loc[0, "n"]), "WTPH2YR_0": int(zw.loc[1, "n"]),
                      "WTSAF2YR_0": int(zw.loc[2, "n"]), "cohort_WTPH2YR_0": zero_in_cohort}

# %% [markdown]
# ## 2 Completeness, uniqueness and the sample funnel
#
# **Why.** A left join on `SEQN` is only safe if `SEQN` is unique in every file and every file's participants are a subset of `DEMO_L`. Otherwise rows are duplicated or silently lost. The cohort definition is the first measurement decision of the project. Its funnel is asserted so that a change in any step fails loudly.

# %%
uniq = []
demo_ids = set(demo["SEQN"])
for f in C.NHANES_FILES:
    ids = io.read_xpt(f)["SEQN"]
    uniq.append({"file": f, "rows": len(ids), "seqn_unique": ids.is_unique, "subset_of_DEMO": set(ids) <= demo_ids})
uniq = pd.DataFrame(uniq)
display(uniq)
assert uniq["seqn_unique"].all() and uniq["subset_of_DEMO"].all()

fun = io.funnel()
display(fun)
assert tuple(fun["n"]) == io.FUNNEL_EXPECTED
preg3 = int(coh["preg_unknown"].sum())
print(f"cohort N = {len(coh):,}; RIDEXPRG = 3 (cannot ascertain) kept and flagged: {preg3}")
assert preg3 == 21

fig, ax = plt.subplots(figsize=(7, 2.8))
ax.barh(fun["step"][::-1], fun["n"][::-1], color=[OI["grey"]] * 4 + [OI["blue"]])
for y, (n, d) in enumerate(zip(fun["n"][::-1], fun["dropped"][::-1])):
    ax.text(n + 120, y, f"{n:,}" + (f"   (-{d:,})" if d else ""), va="center", fontsize=9)
ax.set_xlabel("participants"); ax.set_xlim(0, 14000)
ax.set_title("From 11,933 NHANES participants to the 5,730-adult cohort", loc="left")
f_funnel = plots.savefig(fig, "S3_funnel", caption="Sample funnel: DEMO_L participants -> age >= 20 -> interviewed and examined -> HbA1c measured -> not pregnant (N = 5,730). Numbers in brackets are the rows removed at each step.")
plt.show(); print("saved", f_funnel)

# %% [markdown]
# **So what.** `SEQN` is unique in all 16 files, and each file is a subset of `DEMO_L`, so the left join neither duplicates nor drops anyone. The funnel reproduces the specification exactly: 11,933 → 7,809 (age ≥ 20) → 6,064 (examined) → 5,767 (HbA1c present) → 5,730 (pregnant women removed). The largest selective step is the examination (1,745 adults lost). Together with the 25.7 % examination response rate it limits representativeness, which is why the quality matrix in item 9 rates credibility separately. The 297 examined adults without HbA1c are studied in item 7. The 21 women whose pregnancy status could not be ascertained are kept and flagged (`preg_unknown`), so a sensitivity analysis can drop them.

# %%
M3["funnel"] = dict(zip(fun["step"], fun["n"].astype(int)))
M3["uniqueness"] = {"files_seqn_unique": int(uniq["seqn_unique"].sum()), "files_subset_of_demo": int(uniq["subset_of_DEMO"].sum())}
M3["preg_unknown_kept"] = preg3

# %% [markdown]
# ## 3 Per-variable sentinel map
#
# **Why.** NHANES codes "Refused" and "Don't know" differently in each variable: 7/9, 77/99, 777/999 or 7777/9999. Continuous laboratory and examination measures have no such codes at all; their codebook lists only a range of values and "Missing". The sentinel map is therefore taken from each variable's codebook entry, never from a global list. Two kinds of check make it auditable:
#
# - Every recoded code is traceable to the codebook: for each variable, the number of rows recoded in the raw file must equal the frequency the CDC codebook prints for that code.
# - Codes that look like sentinels but are real categories are kept. Examples are `DIQ010 = 3` (borderline) and `HUQ030 = 3` (more than one place of care).

# %%
cb = io.codebook_table()
rows = []
for f in C.NHANES_FILES:
    part = io.load_file(f, spec=spec)[0]
    _, aud = io.apply_sentinels(part, spec, mode="per_variable")
    for _, a in aud.iterrows():
        codes = io._codes(a["codes"])
        cbv = cb[(cb["file"] == f) & (cb["var"] == a["var"])]
        cb_rows = cbv[cbv["code"].isin([str(c) for c in codes])]
        rows.append({"var": a["var"], "file": f, "codes": a["codes"],
                     "codebook_desc": " / ".join(cb_rows["desc"]),
                     "codebook_count": int(cb_rows["count"].sum()),
                     "recoded_file": int(a["n_recoded"])})
sent = pd.DataFrame(rows)
_, aud_coh = io.apply_sentinels(io.build_cohort(sentinels="none"), spec, mode="per_variable")
sent = sent.merge(aud_coh[["var", "n_recoded"]].rename(columns={"n_recoded": "recoded_cohort"}), on="var", how="left")
sent["traceable"] = sent["codebook_count"] == sent["recoded_file"]
display(sent)
sent.to_csv(OUT / "sentinel_audit.csv", index=False, lineterminator="\n")
assert sent["traceable"].all(), sent[~sent["traceable"]]
assert len(sent) == 25 and int(sent["recoded_file"].sum()) == 1047
assert sent["codebook_desc"].str.split(" / ").map(lambda d: all(x in ("Refused", "Don't know") for x in d)).all()

legit = pd.DataFrame([
    ["DIQ010 = 3", "Borderline", int((coh["DIQ010"] == 3).sum()), int((io.read_xpt("DIQ_L")["DIQ010"] == 3).sum())],
    ["HUQ030 = 3", "There is more than one place", int((coh["HUQ030"] == 3).sum()), int((io.read_xpt("HUQ_L")["HUQ030"] == 3).sum())],
    ["RIDRETH3 = 7", "Other race, including multi-racial", int((coh["RIDRETH3"] == 7).sum()), int((demo["RIDRETH3"] == 7).sum())],
], columns=["code", "meaning", "cohort", "file"])
display(legit)
assert legit.loc[0, "cohort"] == 213 and legit.loc[0, "file"] == 284
n_sent_coh = int(sent["recoded_cohort"].fillna(0).sum())
print(f"variables with codebook sentinels: {len(sent)}; cells recoded in the files: {int(sent['recoded_file'].sum()):,}; in the cohort: {n_sent_coh:,}")

# %% [markdown]
# **So what.** For each of the 25 variables with codebook sentinels, the number of recoded rows equals the frequency the codebook prints, so each recode is traceable to its CDC source. The map recodes 1,047 cells across the files and 562 in the cohort. The largest single item is `DIQ180` (prior blood test, 173 "don't know"), a label-audit variable rather than a predictor.
#
# The codes that look like sentinels but are categories stay untouched:
#
# - 213 borderline answers (`DIQ010 = 3`; 284 in the file);
# - 34 people with more than one usual place of care (`HUQ030 = 3`);
# - the 363 "Other race / multiracial" adults (`RIDRETH3 = 7`).
#
# **Decision (DR-S3-02):** recode refusal and don't-know codes per variable from the codebook (`apply_sentinels(mode="per_variable")`). There is no global list, and continuous measures are never recoded.

# %%
M3["sentinel_audit"] = {"n_variables": len(sent), "cells_recoded_files": int(sent["recoded_file"].sum()),
                        "cells_recoded_cohort": n_sent_coh, "all_traceable": bool(sent["traceable"].all()),
                        "legit_codes_cohort": dict(zip(legit["code"], legit["cohort"].astype(int)))}

