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

# %% [markdown]
# ## 4 Cost of a blanket recode
#
# **Why.** A common shortcut is `df.replace([7, 9, 77, 99, 777, 999, 7777, 9999], np.nan)` across the whole table. It is also the "minimal" arm M0 of the experiments in Stage S6. The cost has to be measured rather than assumed. Every value the shortcut removes from a continuous measure is a valid measurement, because those variables have no refusal codes. Examples are a diastolic pressure of 77 mmHg, a weight of 99 kg and an HbA1c of 7.0 %. The damage is counted on the fixed cohort of 5,730 adults in three arms:
#
# - **per-variable**: codebook codes only;
# - **blanket**: the shortcut;
# - **questionnaire-only**: the shortcut restricted to the six questionnaire items where it is harmless.
#
# The effect on the labels is counted as well.

# %%
coh_none = io.build_cohort(sentinels="none")
DERIVED = ["bp_sys_mean", "bp_dia_mean", "whtr", "age_top", "pir_top", "pir_miss", "preg_unknown", "race", "sex"]
coh_blank = io.build_cohort(sentinels="blanket")
codes = list(io.BLANKET_CODES)
dmg = pd.DataFrame({"var": io.CONTINUOUS_CANDIDATES})
dmg["valid_cells_destroyed"] = [int(coh_none[v].isin(codes).sum()) for v in dmg["var"]]
dmg["lost_in_blanket_cohort"] = [int(coh_none[v].notna().sum() - coh_blank[v].notna().sum()) for v in dmg["var"]]
dmg["values_hit"] = [", ".join(f"{io._num(k)}:{n}" for k, n in coh_none.loc[coh_none[v].isin(codes), v].value_counts().sort_index().items()) for v in dmg["var"]]
assert (dmg["valid_cells_destroyed"] == dmg["lost_in_blanket_cohort"]).all()
assert (spec.set_index("var").loc[list(io.CONTINUOUS_CANDIDATES), "sentinel_codes"].groupby(level=0).first() == "").all()
dmg = dmg.sort_values("valid_cells_destroyed", ascending=False).reset_index(drop=True)
display(dmg)
dmg.to_csv(OUT / "blanket_damage.csv", index=False, lineterminator="\n")
n_destroyed = int(dmg["valid_cells_destroyed"].sum())

# same 20 variables in the full merged file (secondary scope)
full_none = io.load_merged(sentinels="none")
n_destroyed_full = int(sum(full_none[v].isin(codes).sum() for v in io.CONTINUOUS_CANDIDATES))

# labels
a1c_pos = coh_none["LBXGH"] >= C.HBA1C_DIABETES
a1c_pos_blank = coh_blank["LBXGH"] >= C.HBA1C_DIABETES
lost_pos = int((a1c_pos & ~a1c_pos_blank).sum())
lost_values = coh_none.loc[a1c_pos & ~a1c_pos_blank, "LBXGH"].value_counts().to_dict()
self_dm = coh["DIQ010"] == 1
l_comb = self_dm | a1c_pos
l_comb_blank = self_dm | a1c_pos_blank
flips = int((l_comb & ~l_comb_blank).sum())

# questionnaire-only arm: genuine codes in the six questionnaire items
q_arm = pd.Series({v: int(coh_none[v].isin(io.sentinel_map(spec)[v]).sum()) for v in io.QUESTIONNAIRE_ITEMS})
n_q = int(q_arm.sum())

# blanket on every numeric column: genuine codes vs valid values
_, aud_blank = io.apply_sentinels(coh_none.drop(columns=DERIVED), spec, mode="blanket")
smap = io.sentinel_map(spec)
aud_blank["genuine"] = [int(coh_none[v].isin(smap.get(v, [])).sum()) for v in aud_blank["var"]]
aud_blank["valid_destroyed"] = aud_blank["n_recoded"] - aud_blank["genuine"]
n_blank_all, n_blank_genuine = int(aud_blank["n_recoded"].sum()), int(aud_blank["genuine"].sum())
other_valid = aud_blank[(aud_blank["valid_destroyed"] > 0) & ~aud_blank["var"].isin(io.CONTINUOUS_CANDIDATES)].sort_values("valid_destroyed", ascending=False)

print(f"valid cells destroyed in the cohort (20 continuous candidates): {n_destroyed:,}; same 20 variables in the full file: {n_destroyed_full:,}")
print(f"HbA1c positives lost: {lost_pos}/{int(a1c_pos.sum())} ({lost_pos / a1c_pos.sum():.1%}); values {lost_values}")
print(f"L_comb positives flipped to negative: {flips}/{int(l_comb.sum())}")
print(f"questionnaire-only arm: {n_q} genuine codes {q_arm.to_dict()}")
print(f"blanket over all numeric columns of the cohort: {n_blank_all:,} cells recoded, of which genuine refusal/don't-know {n_blank_genuine:,}")
display(other_valid[["var", "n_recoded", "genuine", "valid_destroyed", "by_code"]].head(12))

assert n_destroyed == 1496 and n_destroyed_full == 2472
assert lost_pos == 29 and int(a1c_pos.sum()) == 721 and lost_values == {7.0: 28, 9.0: 1}
assert flips == 6 and int(l_comb.sum()) == 971
assert n_q == 57 and q_arm.to_dict() == {"HIQ011": 9, "HUQ030": 1, "BPQ020": 4, "BPQ080": 34, "SMQ020": 7, "DMDEDUC2": 2}

# %%
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
d = dmg[dmg["valid_cells_destroyed"] > 0].iloc[::-1]
col = [OI["vermillion"] if v == "LBXGH" else OI["orange"] for v in d["var"]]
a1.barh(d["var"], d["valid_cells_destroyed"], color=col)
for y, n in enumerate(d["valid_cells_destroyed"]):
    a1.text(n + 3, y, str(n), va="center", fontsize=8)
a1.set_xlabel("valid measurements set to missing (cohort, N = 5,730)")
a1.set_title(f"Blanket recode wipes {n_destroyed:,} valid values", loc="left")
bars = [("valid values destroyed\n(20 continuous measures)", n_destroyed, OI["orange"]),
        ("genuine refusal / don't know\n(6 questionnaire items)", n_q, OI["blue"])]
a2.bar([b[0] for b in bars], [b[1] for b in bars], color=[b[2] for b in bars], width=0.6)
for x, b in enumerate(bars):
    a2.text(x, b[1] + 25, f"{b[1]:,}", ha="center", fontsize=10)
a2.set_ylabel("cells"); a2.set_ylim(0, n_destroyed * 1.25); a2.tick_params(axis="x", labelsize=9)
a2.set_title("Harm versus benefit", loc="left")
a2.text(0.98, 0.95, f"HbA1c 7.0 / 9.0 lost: {lost_pos} of {int(a1c_pos.sum())} A1c positives ({lost_pos / a1c_pos.sum():.1%})\n"
        f"L_comb flips: {flips} of {int(l_comb.sum())}", transform=a2.transAxes, ha="right", va="top", fontsize=9,
        bbox=dict(boxstyle="round", fc="white", ec=OI["grey"]))
fig.tight_layout()
f_blank = plots.savefig(fig, "S3_blanket_recode_damage",
                        caption=f"Left: valid measurements removed by a blanket recode of 7/9/77/99/777/999/7777/9999 in the cohort, by variable "
                                f"({n_destroyed:,} in total; HbA1c in red). Right: the shortcut destroys {n_destroyed:,} valid values to clean {n_q} genuine "
                                f"refusal/don't-know answers in the questionnaire items; it removes {lost_pos}/{int(a1c_pos.sum())} HbA1c-defined positives, "
                                f"of which {flips} of {int(l_comb.sum())} L_comb positives flip.")
plt.show(); print("saved", f_blank)

# %% [markdown]
# **So what.** On the same 5,730 adults, the blanket recode destroys **1,496 valid measurements** across the 20 continuous candidates. Most fall on diastolic pressure and pulse, where 77 and 99 are ordinary readings. Over the whole release the same 20 variables lose 2,472 values, a secondary count. The harm reaches the label:
#
# - All 29 HbA1c values it removes are 7.0 % (28) or 9.0 % (1), so every one is a true diabetic value. That is **29 of the 721 HbA1c-defined positives (4.0 %)** lost.
# - Under the frozen `L_comb` only **6 of 971** positives flip, because the other 23 also report a diagnosis. Self-report hides the error, which makes it easy to miss.
#
# Applied to every numeric column, the shortcut also wipes categorical codes that are real categories. Examples are `RIDRETH3 = 7` (the 363 multiracial adults disappear as a group), 380 moderate-activity frequencies of 7 sessions (`PAD790Q`) and age 77.
#
# The benefit side is small. Restricting the shortcut to the six questionnaire items cleans just **57** genuine codes, so the shortcut's harm exceeds its gain by a factor of about 26. **Decision (DR-S3-02, evidence):** the per-variable map is the systematic arm. The blanket recode is kept only as the deliberately naive M0 arm in Stage S6, where its cost becomes measurable in model terms.

# %%
M3["blanket_recode"] = {
    "valid_cells_destroyed_cohort": n_destroyed, "valid_cells_destroyed_full_file_same_20_vars": n_destroyed_full,
    "candidates": list(io.CONTINUOUS_CANDIDATES),
    "per_variable": dict(zip(dmg["var"], dmg["valid_cells_destroyed"].astype(int))),
    "a1c_positives_lost": lost_pos, "a1c_positives": int(a1c_pos.sum()), "a1c_lost_share": lost_pos / int(a1c_pos.sum()),
    "l_comb_flips": flips, "l_comb_positives": int(l_comb.sum()),
    "questionnaire_only_cells": n_q, "questionnaire_only_per_item": q_arm.to_dict(),
    "all_numeric_recoded": n_blank_all, "all_numeric_genuine": n_blank_genuine,
    "ridreth3_7_destroyed": int(aud_blank.set_index("var").loc["RIDRETH3", "valid_destroyed"]),
}

# %% [markdown]
# ## 5 Consistency checks
#
# **Why.** Internal consistency tests the data against facts that must hold: BMI is weight / height², systolic pressure exceeds diastolic, and pulse pressure and waist-to-height ratio stay within plausible bounds. Questions asked only of a sub-group (skip patterns) define who *can* have a value. That matters for leakage: a variable asked only of diagnosed people is a disguised label.

# %%
bmx = io.load_file("BMX_L")[0]
v = bmx.dropna(subset=["BMXWT", "BMXHT", "BMXBMI"])
bmi_diff = (v["BMXWT"] / (v["BMXHT"] / 100) ** 2 - v["BMXBMI"]).abs()
bpx = io.load_file("BPXO_L")[0]
chk = [["BMI = weight / height^2: valid triples (BMX_L)", len(v), "max |diff| = %.3f; > 0.1: %d" % (bmi_diff.max(), (bmi_diff > 0.1).sum())]]
pp_rows = []
for src_name, df in [("BPXO_L file", bpx), ("cohort", coh)]:
    for i in (1, 2, 3):
        s, dd = df[f"BPXOSY{i}"], df[f"BPXODI{i}"]
        pp = s - dd
        pp_rows.append({"population": src_name, "reading": i, "valid": int((s.notna() & dd.notna()).sum()),
                        "SBP <= DBP": int((s <= dd).sum()), "pulse pressure < 20": int((pp < 20).sum()),
                        "pulse pressure > 100": int((pp > 100).sum())})
pp_tab = pd.DataFrame(pp_rows)
whtr_gt1 = int((coh["whtr"] > 1).sum())
chk.append(["Waist-to-height ratio > 1 (cohort)", int(coh["whtr"].notna().sum()), f"{whtr_gt1} flagged"])
chk = pd.DataFrame(chk, columns=["check", "n", "result"])
display(chk); display(pp_tab)

diq_raw = io.read_xpt("DIQ_L")
univ = []
for var in ("DIQ050", "DIQ070"):
    ans = diq_raw[var].notna()
    g = diq_raw.loc[ans]
    univ.append({"var": var, "answered": int(ans.sum()),
                 "DIQ010=1": int((g["DIQ010"] == 1).sum()), "DIQ010=3": int((g["DIQ010"] == 3).sum()),
                 "DIQ010=2 & DIQ160=1": int(((g["DIQ010"] == 2) & (g["DIQ160"] == 1)).sum()),
                 "other": int((~((g["DIQ010"].isin([1, 3])) | ((g["DIQ010"] == 2) & (g["DIQ160"] == 1)))).sum())})
univ = pd.DataFrame(univ)
display(univ)
coh_dia = coh[coh["DIQ070"] == 1]
d070 = {"self-reported diabetes": int((coh_dia["DIQ010"] == 1).sum()), "borderline": int((coh_dia["DIQ010"] == 3).sum()),
        "no diabetes (told prediabetes)": int((coh_dia["DIQ010"] == 2).sum())}
print("cohort, DIQ070 = 1 (takes oral glucose-lowering medication):", d070)
consistency = pd.concat([chk.assign(kind="arithmetic"), pp_tab.assign(kind="blood pressure")], ignore_index=True)
consistency.to_csv(OUT / "consistency_checks.csv", index=False, lineterminator="\n")

assert len(v) == 8471 and bmi_diff.max() <= 0.05 + 1e-9 and (bmi_diff > 0.1).sum() == 0
assert pp_tab["SBP <= DBP"].sum() == 0 and whtr_gt1 == 4
assert univ.loc[0, ["answered", "DIQ010=1", "other"]].tolist() == [1081, 1081, 0]
assert univ.loc[1, ["DIQ010=1", "DIQ010=3", "DIQ010=2 & DIQ160=1", "other"]].tolist() == [1081, 282, 918, 0]

# %% [markdown]
# **So what.** The arithmetic holds:
#
# - BMI recomputed from weight and height matches the published value for all 8,471 valid triples (largest difference 0.050, which is rounding; none above 0.1).
# - No reading has systolic ≤ diastolic pressure.
# - Implausible pulse pressures are rare: below 20 mmHg in 5/2/3 cohort readings and 12/8/11 file readings; above 100 mmHg in 34/39/29 cohort readings. They are flagged, not changed, because a wide pulse pressure is plausible in older adults with stiff arteries.
# - Four cohort members have a waist-to-height ratio above 1. They are flagged.
#
# The skip patterns matter more. `DIQ050` (insulin) is answered only by the 1,081 people who report diabetes, so it is a pure proxy of the label. `DIQ070` (oral medication) is also asked of 282 borderline respondents and of 918 non-diabetic respondents who were told they have prediabetes. Within the cohort, 41 non-diabetic and 44 borderline adults take glucose-lowering medication (metformin for prediabetes). **Decision (DR-S3-06):** `DIQ050`/`DIQ070` are inadmissible as features (`admissible = N`). The treatment-aware sensitivity label in S5 may use them only inside this documented universe, and it must exclude prediabetes medication.

# %%
M3["consistency"] = {"bmi_triples": len(v), "bmi_max_abs_diff": float(bmi_diff.max()), "bmi_diff_gt_0_1": int((bmi_diff > 0.1).sum()),
                     "sbp_le_dbp": int(pp_tab["SBP <= DBP"].sum()),
                     "pp_lt20_cohort": pp_tab.query("population == 'cohort'")["pulse pressure < 20"].tolist(),
                     "pp_gt100_cohort": pp_tab.query("population == 'cohort'")["pulse pressure > 100"].tolist(),
                     "pp_lt20_file": pp_tab.query("population == 'BPXO_L file'")["pulse pressure < 20"].tolist(),
                     "pp_gt100_file": pp_tab.query("population == 'BPXO_L file'")["pulse pressure > 100"].tolist(),
                     "whtr_gt1": whtr_gt1, "diq050_universe": univ.iloc[0].drop("var").to_dict(),
                     "diq070_universe": univ.iloc[1].drop("var").to_dict(), "cohort_diq070_yes": d070}

# %% [markdown]
# ## 6 Top-coding
#
# **Why.** Disclosure control caps age at 80 and the income-to-poverty ratio at 5. A capped value is a bound rather than a measurement. A model that treats "80" as exactly 80 years, or that loses the 12.8 % of people with no income ratio, misreads the data. Two questions decide the treatment: how many people sit at each cap, and whether the cap hides a change in risk.

# %%
coh["L_comb"] = l_comb.astype(int)
age_top, pir_top, pir_miss = int(coh["age_top"].sum()), int(coh["pir_top"].sum()), int(coh["pir_miss"].sum())
prev_80 = coh.loc[coh["RIDAGEYR"] == 80, "L_comb"].mean()
prev_7079 = coh.loc[coh["RIDAGEYR"].between(70, 79), "L_comb"].mean()
top = pd.DataFrame([
    ["age_top (RIDAGEYR = 80)", age_top, age_top / len(coh)],
    ["pir_top (INDFMPIR = 5)", pir_top, pir_top / len(coh)],
    ["pir_miss (INDFMPIR missing)", pir_miss, pir_miss / len(coh)],
], columns=["flag", "n", "share"])
display(top)
print(f"L_comb prevalence (unweighted): age 80 group {prev_80:.1%}, ages 70-79 {prev_7079:.1%}")
assert (age_top, pir_top, pir_miss) == (321, 1282, 734)
assert close(prev_80, 0.262, 0.001) and close(prev_7079, 0.254, 0.001)

# %% [markdown]
# **So what.** 321 adults (5.6 %) are capped at age 80, and 1,282 (22.4 %) at an income ratio of 5. Another 734 (12.8 %) have no income ratio at all. The age cap hides little: unweighted `L_comb` prevalence is 26.2 % in the capped group against 25.4 % at ages 70–79, so risk has flattened by then. Age standardisation in 60+ bands is unaffected.
#
# The income variable is both capped and incomplete. **Decision (DR-S3-05):** keep the values and carry the flags `age_top`, `pir_top` and `pir_miss` next to them. Whether the flags enter the model is tested as ablation block B4 (P07 top-code flags, P06 missing indicator) in Stage S6.

# %%
M3["top_coding"] = {"age_top": age_top, "pir_top": pir_top, "pir_top_share": pir_top / len(coh),
                    "pir_miss": pir_miss, "pir_miss_share": pir_miss / len(coh),
                    "prev_age80": float(prev_80), "prev_age70_79": float(prev_7079)}

# %% [markdown]
# ## 7 Missing-data mechanism for HbA1c
#
# **Why.** The cohort keeps only examined adults *with* an HbA1c value. If missingness depended on diabetes itself, the label would be biased in a way no weighting could repair. Rubin's taxonomy cannot be settled from the data:
#
# - MCAR can be rejected by showing that missingness depends on observed covariates.
# - MAR versus MNAR depends on the unobserved values and cannot be tested.
#
# A logistic model for the missingness indicator among the 6,064 examined adults shows who is missing. It is unweighted because it describes the sample rather than the population. Little's MCAR test is not used: it assumes multivariate normality, and it can only reject MCAR, which the logit already does more informatively.

# %%
mrg = io.load_merged(sentinels="per_variable")
ex = mrg[(mrg["RIDAGEYR"] >= C.ADULT_MIN_AGE) & (mrg["RIDSTATR"] == 2)].copy()
y_miss = ex["LBXGH"].isna().astype(int)
race_ex = ex["RIDRETH3"].map(io.RACE_LABELS)
Xm = pd.DataFrame({"age (per 10 y)": ex["RIDAGEYR"] / 10, "female": (ex["RIAGENDR"] == 2).astype(int)}, index=ex.index)
for r in ["NH Black", "NH Asian", "Mexican American", "Other Hispanic", "Other/Multi"]:
    Xm[r] = (race_ex == r).astype(int)
Xm["PIR (per unit)"] = ex["INDFMPIR"].fillna(ex["INDFMPIR"].mean())
Xm["PIR missing"] = ex["INDFMPIR"].isna().astype(int)
Xm["BMI (per unit)"] = ex["BMXBMI"].fillna(ex["BMXBMI"].mean())
Xm["BMI missing"] = ex["BMXBMI"].isna().astype(int)
Xm["uninsured"] = (ex["HIQ011"] == 2).astype(int)
Xm["no usual place of care"] = (ex["HUQ030"] == 2).astype(int)
Xm["self-reported diabetes"] = (ex["DIQ010"] == 1).astype(int)
Xm["told hypertension"] = (ex["BPQ020"] == 1).astype(int)
fit = sm.Logit(y_miss, sm.add_constant(Xm)).fit(disp=0)
ci = fit.conf_int()
or_tab = pd.DataFrame({"OR": np.exp(fit.params), "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]), "p": fit.pvalues}).drop("const")
auc_miss = roc_auc_score(y_miss, fit.predict())
miss_rate = ex.assign(m=y_miss, race=race_ex).groupby("race")["m"].agg(["size", "mean"]).rename(columns={"size": "n", "mean": "missing_share"})
print(f"examined adults {len(ex):,}; HbA1c missing {int(y_miss.sum())} ({y_miss.mean():.1%}); LLR p = {fit.llr_pvalue:.1e}; AUC = {auc_miss:.3f}")
display(or_tab.round(3)); display(miss_rate.round(3))
or_tab.to_csv(OUT / "missingness_or.csv", lineterminator="\n")

assert len(ex) == 6064 and int(y_miss.sum()) == 297
assert fit.llr_pvalue < 1e-10 and close(auc_miss, 0.65, 0.005)
assert close(or_tab.loc["NH Black", "OR"], 1.85, 0.01) and close(or_tab.loc["NH Black", "ci_low"], 1.35, 0.01) and close(or_tab.loc["NH Black", "ci_high"], 2.54, 0.01)
assert close(or_tab.loc["PIR (per unit)", "OR"], 0.82, 0.01) and close(or_tab.loc["age (per 10 y)", "OR"], 0.89, 0.01)
assert close(or_tab.loc["BMI missing", "OR"], 2.6, 0.06) and close(or_tab.loc["self-reported diabetes", "OR"], 1.15, 0.01)

# %%
ot = or_tab.iloc[::-1]
fig, ax = plt.subplots(figsize=(7, 5.2))
sig = (ot["ci_low"] > 1) | (ot["ci_high"] < 1)
ax.errorbar(ot["OR"], range(len(ot)), xerr=[ot["OR"] - ot["ci_low"], ot["ci_high"] - ot["OR"]], fmt="none", ecolor=OI["grey"], capsize=3)
ax.scatter(ot["OR"], range(len(ot)), color=[OI["vermillion"] if s else OI["blue"] for s in sig], zorder=3)
ax.axvline(1, color="black", lw=0.8)
ax.set_xscale("log"); ax.set_yticks(range(len(ot)), ot.index)
ax.set_xlabel("odds ratio of missing HbA1c (95 % CI, log scale)")
ax.set_title("Who lacks an HbA1c value among examined adults", loc="left")
f_miss = plots.savefig(fig, "S3_missing_hba1c_or",
                       caption=f"Unweighted logistic model for missing HbA1c among {len(ex):,} examined adults ({int(y_miss.sum())} missing). "
                               f"Odds ratios with 95 % Wald CIs; red = CI excludes 1. LLR p = {fit.llr_pvalue:.1e}, AUC = {auc_miss:.2f}. Reference: NH White.")
plt.show(); print("saved", f_miss)

# %% [markdown]
# **So what.** 297 of 6,064 examined adults (4.9 %) lack HbA1c, and missingness clearly depends on observed covariates (likelihood-ratio p = 2.8 × 10⁻¹¹, AUC 0.65). Data are **not MCAR**. Associations with missing HbA1c:
#
# | Covariate | OR (95 % CI) |
# |---|---|
# | Non-Hispanic Black | 1.85 (1.35, 2.54) |
# | Income ratio, per unit | 0.82 |
# | Age, per 10 years | 0.89 |
# | Missing BMI | 2.6 (typically an incomplete examination) |
# | Self-reported diabetes | 1.15 (0.82, 1.63) |
#
# Self-reported diabetes, the closest observable stand-in for the outcome, shows no association.
#
# The correct wording is narrow. **Given these covariates there is no evidence against MAR, and MNAR cannot be tested with these data.** **Decision (DR-S3-04):** this wording is used everywhere. WTPH2YR already contains NCHS's blood-sample non-response adjustment. A delta-adjustment / inverse-probability-weighting sensitivity analysis for MNAR is assigned to Stage S9. The model is descriptive and is not used for population inference.

# %%
M3["missingness"] = {"examined_adults": len(ex), "a1c_missing": int(y_miss.sum()), "a1c_missing_share": float(y_miss.mean()),
                     "llr_p": float(fit.llr_pvalue), "auc": float(auc_miss),
                     "odds_ratios": {k: {kk: float(vv) for kk, vv in r.items()} for k, r in or_tab.iterrows()},
                     "missing_share_by_race": miss_rate["missing_share"].to_dict(),
                     "wording": "not MCAR; no evidence against MAR given covariates; MNAR untestable (sensitivity in S9)"}

# %% [markdown]
# ## 8 Outliers: a three-layer rule
#
# **Why.** Extreme values in clinical data are often the signal itself: a very high HbA1c *is* diabetes. A rule that deletes values outside 1.5 × IQR therefore removes cases, not errors. The project uses three layers:
#
# 1. hard physiological limits, which only flag;
# 2. a robust z-score (median and MAD, |z| > 3.5), which only flags;
# 3. human review of whatever both layers flag.
#
# The harm of the blind alternative is measured directly on HbA1c and on a joint fence over five predictors.

# %%
LIMITS = {"BMXBMI": (12, 70), "bp_sys_mean": (70, 260), "bp_dia_mean": (30, 150), "LBXTC": (60, 500), "LBDHDD": (10, 200), "LBXGH": (3, 18)}
def robust_z(s):
    med = s.median(); mad = (s - med).abs().median()
    return 0.6745 * (s - med) / mad
out_rows = []
for var, (lo, hi) in LIMITS.items():
    s = coh[var]
    hard = (s < lo) | (s > hi)
    rz = robust_z(s).abs() > 3.5
    out_rows.append({"var": var, "valid": int(s.notna().sum()), "min": s.min(), "max": s.max(), "limits": f"{lo}-{hi}",
                     "layer1_outside_limits": int(hard.sum()), "layer2_robust_z_gt_3.5": int(rz.sum()),
                     "both_layers": int((hard & rz).sum())})
outl = pd.DataFrame(out_rows)
display(outl)
outl.to_csv(OUT / "outlier_flags.csv", index=False, lineterminator="\n")
review = int(outl["both_layers"].sum())
print(f"layer 3 (manual review queue): {review} values flagged by both layers")

def iqr_fence(s):
    q1, q3 = s.quantile([0.25, 0.75]); i = q3 - q1
    return (s < q1 - 1.5 * i) | (s > q3 + 1.5 * i), q1 - 1.5 * i, q3 + 1.5 * i

a1c = coh["LBXGH"]
fl, lo_f, hi_f = iqr_fence(a1c)
n_fl, n_fl_pos = int(fl.sum()), int((fl & (a1c >= C.HBA1C_DIABETES)).sum())
JOINT = ["BMXBMI", "BMXWAIST", "BPXOSY1", "LBXTC", "LBDHDD"]
joint = np.zeros(len(coh), bool)
for c_ in JOINT:
    joint |= iqr_fence(coh[c_])[0].to_numpy()
la1c = (a1c >= C.HBA1C_DIABETES)
prev_del, prev_keep = la1c[joint].mean(), la1c[~joint].mean()
print(f"HbA1c 1.5xIQR fence: [{lo_f:.2f}, {hi_f:.2f}] flags {n_fl} rows, {n_fl_pos} of them A1c >= 6.5 ({n_fl_pos / la1c.sum():.0%} of {int(la1c.sum())} positives)")
print(f"joint fence on {JOINT}: deletes {int(joint.sum())} rows ({joint.mean():.1%}); A1c-positive share deleted {prev_del:.1%} vs kept {prev_keep:.1%}")
assert close(hi_f, 6.8, 1e-9) and n_fl == 542 and n_fl_pos == 519
assert outl.set_index("var").loc["BMXBMI", "layer1_outside_limits"] == 2 and outl.set_index("var").loc["LBXGH", "layer2_robust_z_gt_3.5"] == 462 and review == 1
assert int(joint.sum()) == 512 and close(prev_del, 0.172, 0.001) and close(prev_keep, 0.121, 0.001)

# %%
fig, ax = plt.subplots(figsize=(8, 4))
bins = np.arange(3.0, 17.6, 0.1)
ax.hist(a1c[~fl], bins=bins, color=OI["blue"], label=f"kept by the fence ({len(coh) - n_fl:,})")
ax.hist(a1c[fl], bins=bins, color=OI["vermillion"], label=f"flagged as 'outlier' ({n_fl}; {n_fl_pos} have HbA1c >= 6.5)")
ytop = ax.get_ylim()[1]
ax.axvline(hi_f, color="black", ls="--", lw=1); ax.text(hi_f + 0.1, ytop * 0.45, f"IQR fence {hi_f:.1f}", fontsize=9)
ax.axvline(C.HBA1C_DIABETES, color=OI["green"], ls=":", lw=1.5); ax.text(C.HBA1C_DIABETES - 0.1, ytop * 0.45, "diagnostic\nthreshold 6.5", ha="right", fontsize=9)
ax.set_xlim(3.5, 14); ax.set_xlabel("HbA1c (%)"); ax.set_ylabel("adults")
ax.set_title(f"A 1.5xIQR rule would delete {n_fl_pos / la1c.sum():.0%} of the diabetic HbA1c values", loc="left")
ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.98))
f_iqr = plots.savefig(fig, "S3_iqr_fence_harm",
                      caption=f"HbA1c distribution in the cohort (N = {len(coh):,}). A 1.5xIQR fence (upper bound {hi_f:.1f} %) flags {n_fl} values; "
                              f"{n_fl_pos} of them are at or above the diagnostic threshold of 6.5 %, i.e. {n_fl_pos / la1c.sum():.0%} of the {int(la1c.sum())} HbA1c-defined cases.")
plt.show(); print("saved", f_iqr)

# %% [markdown]
# **So what.** The hard limits flag almost nothing: 2 BMI values. The robust z-score layer already shows the problem with statistical rules on clinical data. It flags 462 HbA1c values, which are the diabetic tail, so it may only flag and never delete. Only one value is flagged by both layers and goes to manual review. Two results show what blind deletion would cost:
#
# - **HbA1c fence.** The upper fence is 6.8 %. It flags 542 rows, and 519 of them have HbA1c ≥ 6.5 %. Deleting them would remove **72 % of all HbA1c-defined diabetes cases**, so the "outliers" are the outcome.
# - **Joint predictor fence.** A fence over five predictors (BMI, waist, first SBP reading, total cholesterol, HDL) deletes 512 rows (8.9 %). The deleted group has an HbA1c-positive share of 17.2 % against 12.1 % among those kept, so the deletion shifts the label distribution.
#
# **Decision (DR-S3-03):** keep every value. Layers 1–2 only add flags, and layer 3 reviews the few values flagged by both layers. Skewness is handled as an ablation in Stage S6 (block B5: Yeo-Johnson; winsorising as an alternative arm), not by deleting values.

# %%
M3["outliers"] = {"layer_table": outl.set_index("var")[["layer1_outside_limits", "layer2_robust_z_gt_3.5", "both_layers"]].to_dict("index"),
                  "manual_review": review,
                  "a1c_iqr_fence_upper": float(hi_f), "a1c_iqr_flagged": n_fl, "a1c_iqr_flagged_positive": n_fl_pos,
                  "a1c_iqr_positive_share": n_fl_pos / int(la1c.sum()),
                  "joint_fence_vars": JOINT, "joint_fence_deleted": int(joint.sum()), "joint_fence_share": float(joint.mean()),
                  "joint_fence_prev_deleted": float(prev_del), "joint_fence_prev_kept": float(prev_keep)}

