# %% [markdown]
# # Who gets labelled diabetic? A data-centric study of NHANES 2021–2023
#
# ## The three questions we set out to answer — before touching any model
# In this project, machine learning is an instrument for measuring data quality, not the goal. Before we trained any model, we suspected three hidden traps in the data:
#
# 1. **Trap 1: A high AUC may be leakage, not skill.** What looks like a great screening model may just be memorising post-diagnosis information that would never be available at a real screening visit.
# 2. **Trap 2: The label itself is biased.** "Told by a doctor you have diabetes" measures access to healthcare, not just disease — uninsured people are systematically under-diagnosed, and a model trained on this label will reproduce that gap.
# 3. **Trap 3: Hours of pre-processing may not improve AUC at all.** If systematic cleaning only changes model interpretability, fairness and robustness — but barely moves the score — is that work worth doing?
#
# Every section that follows answers one of these questions. We use only basic interpretable models (L2 logistic regression, depth-3 decision tree), lock all hypotheses before experiments, and evaluate the holdout set exactly once.
#
# ---
#
# ## §1 Problem and governance
#
# This section states what is asked, of whom, and under which rules: use case, training target, the two evaluation populations, the feature-availability rule, research questions and hypotheses, and the obligations that come with the data. The text lives in `governance/S1_scope.md`, `governance/hypotheses.md` and `governance/datasheet.md`; the notebook renders it and **recomputes every number it contains** from the raw files.

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Markdown, display

from src import labels as L, survey as S

pd.set_option("display.width", 150, "display.max_colwidth", 80, "display.max_rows", 80)
GOV = C.GOVERNANCE_DIR
SCOPE_MD = (GOV / "S1_scope.md").read_text(encoding="utf-8")
HYP_MD = (GOV / "hypotheses.md").read_text(encoding="utf-8")
DATASHEET_MD = (GOV / "datasheet.md").read_text(encoding="utf-8")


def md_section(text, heading):
    """Body of the markdown section whose heading line contains `heading` (until the next heading of the same or higher level)."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if re.match(r"#+\s", l) and heading.lower() in l.lower())
    level = len(re.match(r"#+", lines[start]).group())
    body = []
    for l in lines[start + 1:]:
        m = re.match(r"(#+)\s", l)
        if m and len(m.group(1)) <= level:
            break
        body.append(l)
    return "\n".join(body).strip()


def md_table(text, heading=None):
    """First pipe table (after `heading` if given) as a DataFrame of strings."""
    body = md_section(text, heading) if heading else text
    rows = [l for l in body.splitlines() if l.strip().startswith("|")]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, data = cells[0], [c for c in cells[2:] if len(c) == len(cells[0])]
    return pd.DataFrame(data, columns=header)


def to_md(df):
    """DataFrame as a markdown pipe table (rendered by display(Markdown(...)); avoids wide text output)."""
    rows = [list(map(str, df.columns))] + [[str(v) for v in r] for r in df.itertuples(index=False)]
    return "\n".join(["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])] + ["| " + " | ".join(r) + " |" for r in rows[1:]])


# %% [markdown]
# ## Analysis cohort
#
# **Why.** Every count below must come from the same cohort that later sections model. The shared loader `nhanes_io.build_cohort()` builds it: adults aged 20 or older, examined, HbA1c observed, not pregnant. The funnel is asserted step by step.

# %%
# Build the analysis cohort with the shared loader that every later section uses, and assert the funnel. Reads
# the raw NHANES files through src.nhanes_io; produces `cohort` and `funnel` (rows left after each step).
from src import nhanes_io

cohort = nhanes_io.build_cohort()
funnel = nhanes_io.funnel()
display(funnel)
# Pin the cohort size and every funnel step: a change in the inclusion rules or the raw files fails here,
# before any statistic below is computed on a different population.
assert len(cohort) == 5730
assert funnel["n"].tolist() == [11933, 7809, 6064, 5767, 5730]

# %% [markdown]
# **So what.** The cohort has 5,730 adults, reached through the funnel 11,933 → 7,809 → 6,064 → 5,767 → 5,730 (asserted). Everything that follows is computed on these rows.

# %% [markdown]
# ## Research question and use case
#
# **Why.** A result is only interpretable relative to the decision it would support, so the question is tied to one use case.
#
# > *Can adult diabetes (diagnosed or undiagnosed) be identified from non-glycaemic information available at a clinical contact; how much of that ability survives in the population screening is meant for; and how do data-preparation decisions change the answer?*
#
# The use case is a **screening aid applied before any glucose test**; the basic models (L2 logistic regression with splines, a depth-3 tree as a probe) are measuring instruments for the data, not the product. Out of scope: complex or LLM-based models, causal estimation, record linkage (forbidden by the DUA), pooling cycles and firm conclusions about small subgroups.

# %% [markdown]
# ## Feature-availability rule
#
# **Why.** One rule decides leakage for every variable: a feature is admissible only if it is available **at the screening moment** (questionnaire, basic measurement or, in Tier 2, a same-visit lipid panel) **and** is not a diagnostic criterion, a consequence of diagnosis or derived from the target. BPQ020 and BPQ080 ("told high blood pressure / cholesterol") pass the rule but are traces of earlier care, like DIQ160 and DIQ180; they stay admissible and get their own ablation arm (T1-minus-care).
#
# The table is read from `governance/S1_scope.md` and must agree with the codebook-built `config/variable_spec.csv` on every shared variable.

# %%
# Read the feature-availability table from governance/S1_scope.md and check it against hard requirements and
# against the codebook-built variable specification. Produces `rule`, `counts`, `spec`, `care`; asserts the
# rule.
rule = md_table(SCOPE_MD, "Variable availability")
# `tier` mirrors `admissible` (N / T1 / T2); it is dropped again before display and before the table is saved.
rule["tier"] = rule["admissible"]
display(rule.drop(columns="tier"))

# Hard requirements of the rule (governance/S1_scope.md, feature-availability rule)
# N = never admissible. These are the diagnostic criteria (HbA1c, glucose), the diagnosis itself, its
# treatments and consequences, and the prediabetes / glucose-test items: all are the target or derived from
# it.
MUST_BE_N = ["LBXGH", "LBXGLU", "DIQ010", "DIQ050", "DIQ070", "DID040", "DID060", "DIQ160", "DIQ180"]
MUST_BE_T1 = ["RIDAGEYR", "RIAGENDR", "BMXBMI", "BMXWAIST", "whtr", "bp_sys_mean", "bp_dia_mean", "BPQ020", "BPQ080", "SMQ020"]
MUST_BE_T2 = ["LBXTC", "LBDHDD"]
# Index by variable so each list above can be checked with one lookup per variable.
adm = rule.set_index("variable")["admissible"]
# Leakage guard: a leakage variable marked admissible in the markdown table stops the notebook here.
assert all(adm[v] == "N" for v in MUST_BE_N), "leakage variable marked admissible"
assert all(adm[v] == "T1" for v in MUST_BE_T1)
assert all(adm[v] == "T2" for v in MUST_BE_T2)
# Governance guard: no row may be classified without a written reason.
assert all(rule["reason"].str.len() > 0), "every variable needs a reason"

# Count variables per class; reindex fixes the order N, T1, T2 and keeps empty classes visible.
counts = rule["admissible"].value_counts().reindex(["N", "T1", "T2"]).rename("variables")
display(counts.to_frame())
# Pin the class sizes quoted in the So-what below; a changed table has to be re-read before the text is
# trusted.
assert counts.tolist() == [14, 13, 2], counts.tolist()

# Cross-check with the variable specification.
# The rule table (written by hand) and variable_spec.csv (built from the CDC codebooks) must agree on every
# variable they share; any disagreement is listed and fails the assert.
spec = pd.read_csv(C.VARIABLE_SPEC)
spec_adm = spec.set_index("var")["admissible"].astype(str)
shared = [v for v in rule["variable"] if v in spec_adm.index]
diff = [(v, adm[v], spec_adm[v]) for v in shared if adm[v] != spec_adm[v]]
print(f"variable_spec.csv: {len(spec)} variables; {len(shared)} shared with the rule table; disagreements: {diff if diff else 'none'}")
assert not diff
SPEC_STATUS = {"n_spec": len(spec), "n_shared": len(shared), "disagreements": len(diff)}
display(pd.crosstab(spec["role"], spec["admissible"]).rename_axis(index="role (spec)", columns="admissible"))
leak = spec[spec["role"] == "leak"][["var", "file", "admiss_reason"]]
display(leak)
# No variable whose role is leak or label may be admissible in any tier.
assert (spec.loc[spec["role"].isin(["leak", "label"]), "admissible"] == "N").all(), "leak or label variable admitted"
# Race, insurance and usual place of care are audit variables: used to check fairness, never as model inputs.
assert set(spec.loc[spec["role"] == "audit", "var"]) == {"RIDRETH3", "HIQ011", "HUQ030"}
# Admissible variables flagged as traces of earlier care. They pass the rule but get their own ablation arm
# (T1-minus-care) because they may reflect contact with the health system rather than risk.
care = spec[(spec["admissible"] != "N") & spec["admiss_reason"].astype(str).str.contains("care-contact")]["var"].tolist()
print("admissible but flagged as care-contact traces (T1-minus-care arm):", care)
assert set(care) == {"BPQ020", "BPQ080"}

# %% [markdown]
# **So what.** The rule rejects 14 variables: nine glycaemic or diagnosis-related items (HbA1c, fasting glucose, the diagnosis itself, its treatments and consequences, "told prediabetes", "glucose tested"), two fasting-subsample lipids, and race, insurance and usual place of care, which stay audit variables only. It admits 13 Tier-1 inputs and 2 Tier-2 lipids. The codebook-based variable specification (§2) agrees on every shared variable and flags exactly BPQ020 and BPQ080 as care-contact traces. Because the decision is made by rule, any reviewer can re-derive it.

# %% [markdown]
# ## Evaluation populations
#
# **Why.** The frozen target is `L_comb` = self-reported physician diagnosis **or** HbA1c ≥ 6.5 %. If most positives were already diagnosed, a high AUC would mostly mean "recognises people who have a diagnosis and the health-care footprint that comes with it", which is not screening value. The composition of the positive class is therefore computed before any model is fitted, and two populations are made co-primary:
#
# - **E-ALL**: the whole cohort, label `L_comb`.
# - **E-SCREEN**: people without a reported diagnosis (DIQ010 ≠ 1); positive = HbA1c ≥ 6.5 %.

# %%
# Attach the labels (L_self, L_A1c, L_comb, E-SCREEN membership, 3 x 3 strata) and tabulate the two evaluation
# populations. Everything is counted from the cohort rows; no model is fitted here. Asserts the label counts
# and the weighted prevalence against the values quoted in the text.
c = L.add_labels(cohort)

n = len(c)
# L_self = self-reported physician diagnosis, L_A1c = HbA1c >= 6.5 %, L_comb = either of the two.
n_self, n_a1c, n_comb = int(c["L_self"].sum()), int(c["L_A1c"].sum()), int(c["L_comb"].sum())
n_escr = int(c["in_escreen"].sum())
# E-SCREEN positives are undiagnosed people with HbA1c >= 6.5 %: the only positives a screening aid can find.
n_escr_pos = int(((c["in_escreen"] == 1) & (c["L_A1c"] == 1)).sum())
n_escr_neg = n_escr - n_escr_pos
# Share of the L_comb positives who already knew their diagnosis: what E-ALL rewards a model for recognising.
share_known = n_self / n_comb
# Diagnosis (yes/no) x HbA1c (>= 6.5 or not) strata, in the fixed order given by L.STRATA_3X3.
strata = c["stratum_3x3"].value_counts().reindex(L.STRATA_3X3).astype(int)

pop = pd.DataFrame([
    ["E-ALL", n, n_comb, n - n_comb, "L_comb"],
    ["E-SCREEN", n_escr, n_escr_pos, n_escr_neg, "HbA1c >= 6.5 among DIQ010 != 1"],
], columns=["population", "rows", "positives", "negatives", "positive class"])
display(pop)
print(f"L_self {n_self}, L_A1c {n_a1c}, L_comb {n_comb}; already self-reported share of L_comb = {share_known:.1%}")
display(strata.rename("rows").to_frame())

# Unweighted prevalence versus design-based prevalence with the blood-sample weight WTPH2YR (HbA1c comes from
# the blood draw). The weighted interval uses survey degrees of freedom (PSUs - strata, see the disclosure
# table).
prev_u = n_comb / n
prev_w = S.weighted_prop(c, "L_comb", weight=C.WEIGHT_PHLEB)
print(f"prevalence of L_comb: unweighted {prev_u:.1%}; WTPH2YR-weighted {prev_w['est']:.1%} "
      f"(95% CI {prev_w['ci_low']:.1%} to {prev_w['ci_high']:.1%}, df {prev_w['df']})")

# Pin the label counts, the E-SCREEN split and the stratum sizes (the So-what text quotes them) and the
# prevalences; the tolerances only absorb rounding to the digits printed in the text.
assert (n_self, n_a1c, n_comb) == (819, 721, 971)
assert (n_escr_pos, n_escr_neg) == (152, 4759)
assert strata.tolist() == [569, 250, 152, 4759]
assert abs(share_known - 0.843) < 0.001
assert abs(prev_u - 0.169) < 0.001 and abs(prev_w["est"] - 0.140) < 0.001

# %%
# Figure: composition of the L_comb positives (left) and positives per population (right). Reads only the
# counts computed above; writes the figure with its caption through plots.savefig.
plots.set_style()
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), gridspec_kw={"width_ratios": [1, 1]})
# Colour-blind-safe Okabe-Ito palette from the project config.
ok = C.OKABE_ITO
# Panel 1: who the 971 positives are
ax = axes[0]
parts = [("diagnosed, HbA1c >= 6.5", strata["D_uncontrolled"], ok["blue"]),
         ("diagnosed, HbA1c < 6.5 (controlled)", strata["D_controlled"], ok["sky"]),
         ("not diagnosed, HbA1c >= 6.5", strata["Undiagnosed"], ok["vermillion"])]
# Stacked horizontal bar: the three strata are drawn one after the other; `left` is where the next one starts.
left = 0
for lab, v, col in parts:
    ax.barh(0, v, left=left, color=col, label=f"{lab}: {v}")
    left += v
ax.set_yticks([]); ax.set_xlabel(f"persons with L_comb = 1 (n = {n_comb})")
ax.set_title(f"E-ALL positives: {share_known:.0%} already diagnosed", loc="left")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), fontsize=8)
# Panel 2: E-SCREEN
ax = axes[1]
# Right panel: how few positives remain once the already-diagnosed are removed.
ax.bar(["E-ALL", "E-SCREEN"], [n_comb, n_escr_pos], color=[ok["blue"], ok["vermillion"]])
for i, v in enumerate([n_comb, n_escr_pos]):
    # Count label placed just above each bar (offset of 15 positives).
    ax.text(i, v + 15, str(v), ha="center")
ax.set_ylabel("positives"); ax.set_ylim(0, n_comb * 1.12); ax.set_title("Positives per population", loc="left")
fig.tight_layout()
f_comp = plots.savefig(fig, "S1_label_composition",
                       caption=f"Composition of the {n_comb} L_comb positives. {n_self} ({share_known:.1%}) already reported a diagnosis; "
                               f"only {n_escr_pos} are undiagnosed with HbA1c >= 6.5 and form the E-SCREEN positive class.")
plt.show(); print("saved", f_comp)

# %% [markdown]
# **So what.** Of the 971 positives, 819 (84.3 %) had already reported a diagnosis; only 152 are undiagnosed. E-ALL therefore rewards recognising known patients, while E-SCREEN (152 positives, 4,759 negatives) is where a screening aid has something to find. Prevalence is 16.9 % unweighted but 14.0 % weighted, mainly because older adults are over-represented in the sample. The E-ALL – E-SCREEN performance gap is reported as a finding in its own right. With 152 positives, many E-SCREEN contrasts will be *inconclusive*; that is stated in advance.

# %% [markdown]
# ## Research questions and hypotheses
#
# **Why.** Four questions organise the project; each hypothesis has a metric, direction, magnitude, smallest effect of interest (SESOI), falsifier and an honest record of whether the data had been seen. They are read from `governance/hypotheses.md`, locked in §6.11 before any ablation.
#
# | RQ | Question |
# |---|---|
# | RQ1 | **Labels as measurement.** What do self-report and HbA1c each measure, and who is missed by each? |
# | RQ2 | **Rules and preparation.** How much do the availability rule (leakage) and systematic preparation change performance and stability, on E-ALL and on E-SCREEN? |
# | RQ3 | **3 × 3 label matrix.** How does the training label change who is detected? |
# | RQ4 | **Measurement bias.** Does BMI under-detect diabetes in Asian adults, and does waist-to-height ratio repair it? |

# %%
# Read the hypothesis table from governance/hypotheses.md and check that it is complete and well formed.
# Governance guard: every hypothesis carries a metric, a direction, a smallest effect of interest (SESOI), a
# falsifier and an honest record of whether the data had been seen before the hypothesis was written.
hyp = md_table(HYP_MD, "Hypothesis table")
display(hyp[["hyp_id", "rq_or_block", "statement", "prior_exposure"]])

# Allowed values for prior exposure: the pattern was seen in analysis, seen only descriptively, or not at all.
ALLOWED_EXPOSURE = {"analysis_seen", "descriptive_seen", "none"}
FIELDS = ["metric", "direction", "magnitude", "sesoi", "falsifier", "prior_exposure", "weights"]
# Exactly these eight hypotheses, in this order, so none can be added or dropped silently.
assert hyp["hyp_id"].tolist() == ["H1a", "H1b", "H2a", "H2b", "H2c", "H3", "H4a", "H4b"]
assert set(hyp["prior_exposure"]) <= ALLOWED_EXPOSURE
# No empty cell in any required field (an empty falsifier would make a hypothesis unfalsifiable).
assert (hyp[FIELDS].apply(lambda col: col.str.len() > 0)).all().all(), "every hypothesis needs all fields"
expo = hyp["prior_exposure"].value_counts().reindex(sorted(ALLOWED_EXPOSURE)).fillna(0).astype(int)
display(expo.rename("hypotheses").to_frame())
# Map each hypothesis to its research question by pulling `RQn` out of the block label.
rq_map = hyp.assign(rq=hyp["rq_or_block"].str.extract(r"(RQ\d)")[0]).groupby("rq")["hyp_id"].apply(list)
display(rq_map.rename("hypotheses").to_frame())

# %% [markdown]
# **So what.** Eight hypotheses cover the four questions (H1a, H1b → RQ1; H2a–H2c → RQ2; H3 → RQ3; H4a, H4b → RQ4), each with all seven fields. Four are `analysis_seen` (the pattern was observed in pilot profiling), one is `descriptive_seen`, and only the three experimental ones (H2b, H2c, H3) are genuine pre-registrations. §3–§5 therefore present confirmations of observed patterns, never pre-registered tests.

# %% [markdown]
# ## ADA-lite baseline
#
# **Why.** A published risk score is the natural yardstick for a simple model, but this cycle lacks two of the seven items of Bang et al. 2009 (family history of diabetes, gestational diabetes). Calling the result "the ADA score" would overstate it. The baseline is therefore **ADA-lite, a reduced version missing 2 items**, compared on E-SCREEN only, because Bang's outcome is undiagnosed diabetes. The absence of the two items is checked in the CDC codebooks, not assumed.

# %%
# Show the ADA-lite item table and verify in the CDC codebooks that the two missing items really are absent.
# Reads governance/S1_scope.md and the MCQ_L / DIQ_L codebook pages; asserts zero hits for the missing items.
ada = md_table(SCOPE_MD, "ADA-lite baseline")
display(Markdown(to_md(ada)))
n_avail = int((ada["Status"] == "available").sum())
n_miss = int(ada["Status"].str.contains("missing").sum())
print(f"ADA-lite items available: {n_avail} of {len(ada)}; missing: {n_miss}")
# Five of the seven Bang et al. 2009 items exist in this cycle, two do not: hence 'ADA-lite'.
assert (n_avail, n_miss) == (5, 2)


# Plain lower-case text of one CDC codebook page: HTML tags stripped, whitespace collapsed (for term search).
def codebook_text(stem):
    t = (C.CODEBOOK_DIR / f"{stem}.htm").read_text(encoding="utf-8", errors="ignore")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).lower()


# Count how often each search term occurs in each codebook; the absence is evidence, not an assumption.
evidence = []
for stem in ["MCQ_L", "DIQ_L"]:
    t = codebook_text(stem)
    for term in ["family history", "blood relative", "gestational"]:
        evidence.append({"codebook": stem, "search term": term, "hits": t.count(term)})
    # 'during pregnancy' occurs in the wording of DIQ010 ("Other than during pregnancy ...") and is not a gestational-diabetes item
    evidence.append({"codebook": stem, "search term": "during pregnancy", "hits": t.count("during pregnancy")})
ev = pd.DataFrame(evidence)
display(ev)
# Show the context of 'during pregnancy' so a reader can see it is not a gestational-diabetes question.
ctx = [codebook_text("DIQ_L")[max(0, m.start() - 60): m.end() + 80] for m in re.finditer("during pregnancy", codebook_text("DIQ_L"))]
print("context of 'during pregnancy' in DIQ_L:")
for t in ctx[:2]:
    print("  ...", t.strip()[:120], "...")
# Zero hits for family history, blood relative and gestational: the two items are not in the data.
assert ev.query("`search term` in ['family history','blood relative','gestational']")["hits"].sum() == 0

# %% [markdown]
# **So what.** Five of the seven items exist (age, sex, hypertension history, measured BMI, leisure-time activity); family history and gestational diabetes do not occur in the MCQ_L or DIQ_L codebooks (zero hits per search term), and the only pregnancy wording in DIQ_L is the exclusion clause of the diagnosis question. The baseline is therefore called ADA-lite. Only the verified abstract figures of Bang et al. (2009) are used, qualitatively (§9.8.3); no published AUC is used.

# %% [markdown]
# ## Novelty statement
#
# **Why.** A contribution should be stated at the strength the evidence supports. The statement below says what is *combined*, not what is "first". It is read from `governance/S1_scope.md`, and the cell asserts that it contains no priority or superlative words.

# %%
# Check the novelty statement for priority claims. Reads governance/S1_scope.md; asserts that no word from the
# forbidden list occurs, so the text claims a combination of methods and never a 'first' or 'best'.
novelty = md_section(SCOPE_MD, "Novelty statement")
display(Markdown("> " + novelty))
# Priority and superlative words that a contribution statement must not use.
FORBIDDEN = ["first", "novel", "best", "optimal", "state-of-the-art", "unprecedented", "never before", "pioneer"]
# Whole-word, case-insensitive match (\b), so that e.g. 'bestow' would not trigger 'best'.
hits = [w for w in FORBIDDEN if re.search(rf"\b{re.escape(w)}\b", novelty, flags=re.I)]
assert not hits, hits
print("novelty statement: no priority or superlative words;", len(novelty.split()), "words")

# %% [markdown]
# ## Data user agreement and disclosure controls
#
# **Why.** NHANES public-use files are released under the NCHS Data User Agreement. Compliance is part of the method: it forbids some analyses (linkage with other individual-level data) and shapes others (how small groups are reported). The datasheet summary (Gebru et al. 2021 format) states provenance, ethics approval and consent; the table maps each obligation to what the project does.

# %%
# Show the datasheet summary and the Data User Agreement obligations, and check that the ethics approval and
# consent statements are in the datasheet. Reads governance/datasheet.md and governance/S1_scope.md.
display(Markdown(md_section(DATASHEET_MD, "Summary")))
# Guard: the datasheet must name the NCHS ethics protocol and informed consent, not just assume them.
assert "Protocol #2021-05" in DATASHEET_MD and "informed consent" in DATASHEET_MD
dua = md_table(SCOPE_MD, "Data user agreement obligations")
display(dua)
# Five DUA obligations are tracked; a changed table has to be reviewed against the actions listed in it.
assert len(dua) == 5

# %% [markdown]
# NCHS already applies disclosure controls to the public files. The project does not probe them; it makes their footprint visible so that a top-coded value is never mistaken for a measurement. The counts are computed on the cohort.

# %%
# Count the cohort rows hit by NCHS disclosure controls (top-coding, masked design variables) and compare them
# with what the loader and the models do about each. Reads the cohort and the public DEMO_L file; no model
# fit. Age 80 is the top code of RIDAGEYR (everyone older is recorded as 80).
age_top = int((c["RIDAGEYR"] == 80).sum())
# Income-to-poverty ratio is top-coded at 5; the 1e-9 tolerance guards the float comparison.
pir_top = int((c["INDFMPIR"] >= 5 - 1e-9).sum())
pir_na = int(c["INDFMPIR"].isna().sum())
# household size and pregnancy status are minimised away from the cohort; their disclosure footprint is read from the public DEMO_L file
# Read the raw SAS transport file, because these two columns are no longer in the minimised cohort.
demo_raw = pd.read_sas(C.RAW_DIR / "DEMO_L.xpt", format="xport")
hh_max = float(demo_raw["DMDHHSIZ"].max())
preg_known = demo_raw[demo_raw["RIDEXPRG"].notna()]
# Masked variance units: PSUs are nested in strata, so design df = PSUs - strata (30 - 15 = 15, asserted
# below). This is the df used for survey t-quantiles and for the delete-one-PSU jackknife in the other
# sections.
strata_n = int(c[C.STRATA].nunique())
psu_n = int(c.groupby(C.STRATA)[C.PSU].nunique().sum())

# One row per disclosure control: what it is, how many rows it touches, and how the project handles it.
dc = pd.DataFrame([
    ["Age top-coded at 80 (RIDAGEYR == 80)", age_top, f"{age_top / n:.1%} of cohort", "indicator age_top"],
    ["Income-to-poverty ratio top-coded at 5 (INDFMPIR)", pir_top, f"{pir_top / n:.1%} of cohort", "indicator pir_top"],
    ["Income-to-poverty ratio missing", pir_na, f"{pir_na / n:.1%} of cohort", "indicator pir_miss"],
    ["Household size, maximum value in DEMO_L (top-coded at 7)", hh_max, "dropped by minimisation", "documented in spec note"],
    ["Pregnancy status recorded only for women aged 20-44", f"{preg_known['RIDAGEYR'].min():.0f}-{preg_known['RIDAGEYR'].max():.0f}", f"{len(preg_known)} women in DEMO_L", "pregnant women excluded by the cohort rule"],
    ["Masked variance strata / PSUs", f"{strata_n} / {psu_n}", f"design df = {psu_n - strata_n}", "delete-one-PSU jackknife"],
], columns=["control", "value", "context", "handling"])
display(dc)
# Pin the counts quoted in the So-what; pregnancy status is recorded for women aged 20-44 only, which the last
# assert confirms.
assert (age_top, pir_top, pir_na) == (321, 1282, 734)
assert (strata_n, psu_n) == (15, 30) and hh_max == 7
assert preg_known["RIDAGEYR"].between(20, 44).all()

# %% [markdown]
# **So what.** Ethics approval and consent come from NCHS, and the DUA obligations are met by design. 321 adults (5.6 %) are top-coded at age 80 and 1,282 (22.4 %) at an income ratio of 5, with 734 (12.8 %) missing, so indicators are kept next to the values. Masked variance units (15 strata, 30 PSUs) give 15 jackknife degrees of freedom; nothing tries to undo these controls.

# %% [markdown]
# ## Data minimisation
#
# **Why.** Collecting or keeping more than the purpose needs is a governance risk even with public data (purpose limitation and data minimisation, e.g. GDPR Art. 5(1)(b)–(c); the Singapore PDPA has a purpose-limitation obligation). The loader keeps only columns that the variable specification keeps (`use_tier` other than `excluded`); `nhanes_io.minimisation_report` lists what was kept and dropped per file and per column.

# %%
# List, per NHANES file and per column, what the loader keeps and what it drops (data minimisation). Reads the
# variable specification; asserts the totals quoted in the So-what below.
mrep, mcols = nhanes_io.minimisation_report(spec)
display(mrep[["file", "use_tier", "cols_raw", "cols_kept", "cols_dropped"]])
tot_raw, tot_kept, tot_drop = (int(mrep[k].sum()) for k in ["cols_raw", "cols_kept", "cols_dropped"])
# Bookkeeping check: every raw column is either kept or dropped, never lost.
assert tot_raw == tot_kept + tot_drop
assert (tot_raw, tot_kept, tot_drop) == (175, 78, 97), "text of the so-what cell must be updated"
print(f"{tot_raw} raw columns in 16 files: {tot_kept} kept ({tot_kept / tot_raw:.0%}), {tot_drop} dropped ({tot_drop / tot_raw:.0%})")
# Examples of dropped quasi-identifiers and unrelated items, shown with the reason recorded for each.
examples = ["DMDBORN4", "DMDYRUSR", "DMQMILIZ", "DMDHHSIZ", "MCQ010"]
display(mcols[mcols["var"].isin(examples)][["file", "var", "decision", "reason"]])
# The per-column report and the per-file totals must describe the same dropped columns.
assert (mcols["decision"] == "drop").sum() == tot_drop
MIN_STATUS = {"raw_columns": tot_raw, "kept": tot_kept, "dropped": tot_drop}

# %% [markdown]
# **So what.** Of 175 raw columns in the 16 files, 78 are kept and 97 (55 %) are dropped because they have no analytic role: quasi-identifiers (country of birth, years of residence), military service, household details, comment codes and unrelated MCQ items. Each dropped column has a stated reason, and the loader discards them right after reading, so downstream code cannot use them by accident.

# %% [markdown]
# ## Response rates and representativeness
#
# **Why.** Survey weights make the sample resemble the US civilian non-institutionalised population *as far as known covariates allow*. They cannot repair non-response that depends on health. The 2021–2023 cycle has a low response and no oversampling of specific groups, which limits both generalisation and subgroup analysis.

# %%
# Compare the sample with the weighted population and report response rates and the Kish design effect. The
# response rates come from the NCHS cycle overview (they cannot be computed from the files), so they are typed
# in with their source; the age structure and the design effect are computed from the cohort.
RESP = pd.DataFrame([
    ["Interview response rate", "34.6 %", "NCHS cycle overview (not computable from the files)"],
    ["Examination (MEC) response rate", "25.7 %", "NCHS cycle overview (not computable from the files)"],
    ["Oversampling by race/ethnicity or income", "none in this cycle", "NCHS cycle overview; earlier cycles oversampled"],
], columns=["item", "value", "source"])
display(RESP)

# Age bands, unweighted versus weighted by WTPH2YR: the gap shows which group is over-sampled.
w = c[C.WEIGHT_PHLEB]
bands = S.age_band(c["RIDAGEYR"]).values
tab = pd.DataFrame({"unweighted": pd.Series(bands).value_counts(normalize=True),
                    "WTPH2YR-weighted": pd.Series(w.values).groupby(bands).sum() / w.sum()}).loc[["20-39", "40-59", "60+"]]
display((tab * 100).round(1))
# Kish design effect = 1 + CV^2 of the weights; effective sample size = n / deff (information lost to unequal
# weights).
deff = S.kish_deff(w)
print(f"Kish design effect of the weights: {deff:.2f}; effective sample size {S.kish_neff(w):.0f} of {n}")
# Asian adults are the group of RQ4; the count shows how thin that subgroup is.
n_asian = int((c['RIDRETH3'] == 6).sum())
n_asian_pos = int(((c['RIDRETH3'] == 6) & (c['L_comb'] == 1)).sum())
print(f"Asian adults in cohort: {n_asian}, of whom {n_asian_pos} with L_comb")
# Pin the figures quoted in the So-what (Asian subgroup size, 60+ shares, design effect).
assert (n_asian, n_asian_pos) == (315, 50)
assert abs(tab.loc["60+", "unweighted"] - 0.462) < 0.001 and abs(tab.loc["60+", "WTPH2YR-weighted"] - 0.314) < 0.001
assert abs(deff - 1.55) < 0.01

# Figure: age structure of the sample versus the weighted population.
fig, ax = plt.subplots(figsize=(5.6, 3.3))
x = np.arange(3)
ax.bar(x - 0.2, tab["unweighted"] * 100, 0.4, color=C.OKABE_ITO["orange"], label="sample (unweighted)")
ax.bar(x + 0.2, tab["WTPH2YR-weighted"] * 100, 0.4, color=C.OKABE_ITO["blue"], label="population (WTPH2YR)")
ax.set_xticks(x, tab.index); ax.set_xlabel("age band (years)"); ax.set_ylabel("share of adults (%)")
ax.set_title("Older adults are over-represented in the sample", loc="left"); ax.legend()
f_age = plots.savefig(fig, "S1_sample_vs_weighted_age",
                      caption=f"Age structure of the {n} cohort adults, unweighted versus WTPH2YR-weighted. 60+ is {tab.loc['60+','unweighted']:.1%} of the sample "
                              f"but {tab.loc['60+','WTPH2YR-weighted']:.1%} of the weighted population; Kish design effect {deff:.2f}.")
plt.show(); print("saved", f_age)

# %% [markdown]
# **So what.** Adults aged 60+ are 46.2 % of the sample but 31.4 % of the weighted population, so unweighted figures overstate prevalence (16.9 % vs 14.0 %); the Kish design effect of 1.55 leaves the 5,730 adults with the information of roughly 3,700 simple-random-sample adults. Response is low (34.6 % interview, 25.7 % examination) and nothing is oversampled, so subgroups such as Asian adults (315, 50 with `L_comb`) are thin and reported as exploratory. Weights adjust for known covariates only; health-dependent participation (§5.6) remains a stated limitation.

# %% [markdown]
# ## Outputs
#
# Decisions of this section (`governance/register/S1.csv`, with self-check verdicts) and the stored results (`results/metrics_S1.json`, `results/S1/`).

# %%
# Check the decision-register fragment for this section and store its numbers for later sections and the video.
# Reads governance/register/S1.csv; writes results/metrics_S1.json and two small tables under results/S1.
reg_path = GOV / "register" / "S1.csv"
reg = pd.read_csv(reg_path)
display(reg[["dr_id", "type", "decision", "hyp_id", "check_verdict"]])
# Every decision recorded for this section must have passed its self-check.
assert reg["check_verdict"].isin(["PASS", "PASS-FIX"]).all()

# Everything later sections quote from here is stored once, so they read it instead of recomputing it.
payload = {
    "n_cohort": n,
    "funnel": dict(zip(funnel["step"], funnel["n"])),
    "labels": {"L_self": n_self, "L_A1c": n_a1c, "L_comb": n_comb, "known_share_of_comb": share_known},
    "e_all": {"rows": n, "positives": n_comb},
    "e_screen": {"rows": n_escr, "positives": n_escr_pos, "negatives": n_escr_neg},
    "strata_3x3": strata.to_dict(),
    "prevalence_comb": {"unweighted": prev_u, "weighted": prev_w["est"],
                        "ci_low": prev_w["ci_low"], "ci_high": prev_w["ci_high"], "df": prev_w["df"]},
    "kish_deff": deff,
    "age60_share": {"sample": float(tab.loc["60+", "unweighted"]), "weighted": float(tab.loc["60+", "WTPH2YR-weighted"])},
    "disclosure": {"age_top": age_top, "pir_top": pir_top, "pir_missing": pir_na, "strata": strata_n, "psu": psu_n},
    "availability_rule": {"n_rule_rows": len(rule), "by_tier": counts.to_dict(), "spec": SPEC_STATUS},
    "ada_lite": {"items": len(ada), "available": n_avail, "missing": n_miss},
    "hypotheses": {"n": len(hyp), "prior_exposure": expo.to_dict()},
    "minimisation": MIN_STATUS,
    "response_rates": {"interview": 0.346, "mec": 0.257, "source": "NCHS cycle overview"},
}
# Write results/metrics_S1.json (the payload above); the two tables below go to results/S1.
R.save_section("S1", payload)
(C.RESULTS_DIR / "S1").mkdir(exist_ok=True)
rule.drop(columns="tier").to_csv(C.RESULTS_DIR / "S1" / "availability_rule.csv", index=False)
pop.to_csv(C.RESULTS_DIR / "S1" / "evaluation_populations.csv", index=False)
print("saved results/metrics_S1.json; S1 OK")
