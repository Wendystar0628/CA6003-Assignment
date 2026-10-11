# Datasheet: NHANES 2021–2023 adult diabetes analysis cohort

Format: Gebru et al. (2021), *Datasheets for Datasets*, CACM 64(12):86–92 (<https://arxiv.org/abs/1803.09010>). The datasheet describes two things: the **source data** (NHANES August 2021 – August 2023 public-use files, produced by NCHS) and the **derived analysis cohort** (N = 5,730), produced by `src/nhanes_io.build_cohort()` in this repository. All counts below are recomputed in §1–§3 of the notebook and stored in `results/metrics_S1.json` – `results/metrics_S3.json`.

## Summary

| Item | Content |
|---|---|
| Source | NCHS/CDC NHANES public-use files, August 2021 – August 2023 (suffix `_L`), 16 files, downloaded 2026-10-10, SHA-256 verified |
| Ethics and consent | Collected by NCHS under NCHS Ethics Review Board approval (Protocol #2021-05, listed for NHANES 2021–2022 on the NCHS ERB page <https://www.cdc.gov/nchs/nhanes/about/erb.html>, accessed 2026-10-11) with documented informed consent of participants |
| Terms of use | NCHS Data User Agreement: statistical analysis only, no re-identification, no linkage, no study of disclosure controls |
| Instances | one row per participant; cohort N = 5,730 adults (20+, examined, HbA1c observed, not pregnant) from 11,933 |
| Variables | 175 raw columns, 78 kept after minimisation; definitions in `config/variable_spec.csv` |
| Label | `L_comb` = self-reported diagnosis or HbA1c >= 6.5 %: 971 positives (16.9 % unweighted, 14.0 % weighted); 84.3 % already diagnosed |
| Sampling | complex multistage design, 15 masked strata / 30 PSUs; no oversampling in this cycle; response 34.6 % (interview), 25.7 % (examination) |
| Known gaps | HbA1c missing for 4.9 % of examined adults (not MCAR); income missing 12.8 %; top-coding at age 80 and income ratio 5 |
| Intended use | teaching and research on data governance and label measurement; population-level estimates; basic models as measuring instruments |
| Not intended | clinical decisions about individuals, a deployable screening tool, causal claims, firm subgroup conclusions, linkage |

## 1 Motivation

- **Purpose of the source data.** NHANES measures the health and nutrition of the US civilian non-institutionalised population by interview, physical examination and laboratory tests, to produce national prevalence estimates.
- **Purpose of the derived cohort.** To study whether adult diabetes, including undiagnosed diabetes, can be identified from non-glycaemic information available at a screening visit, how much of that ability survives in a genuine screening population, and how data-preparation choices change what a model says about the data.
- **Creator and funding.** Source: National Center for Health Statistics (NCHS), CDC. Derived cohort: this project (MSc coursework, CA6003), no external funding.

## 2 Composition

- **Instances.** One row per participant (`SEQN`). Source: 11,933 participants in `DEMO_L`; other files are subsets of `DEMO_L` (SEQN unique in every file).
- **Sample funnel to the cohort** (asserted in code):

  | Step | n |
  |---|---|
  | `DEMO_L` participants | 11,933 |
  | Age >= 20 | 7,809 |
  | Interviewed and MEC-examined (`RIDSTATR = 2`) | 6,064 |
  | HbA1c measured | 5,767 |
  | Not pregnant (`RIDEXPRG != 1`) | 5,730 |

- **Cohort composition (unweighted).** 3,144 women / 2,586 men; median age 58 (IQR 40–68), 321 top-coded at 80. Race/ethnicity (`RIDRETH3`): NH White 3,408, NH Black 676, Other Hispanic 582, Mexican American 386, Other/multiracial 363, NH Asian 315. The sample is older than the weighted population (60+ is 46.2 % unweighted versus 31.4 % weighted, §1.10), so unweighted rates are not population rates.
- **Variables.** 16 files, 175 raw columns; 78 kept after minimisation (`results/S2/minimisation_report.csv`); per-variable definitions in `config/variable_spec.csv` (universe, valid range, refusal / don't-know codes, top codes, role, admissibility tier, codebook link).
- **Label.** No single ground truth exists. The training target `L_comb` = self-reported diagnosis (`DIQ010 = 1`) or HbA1c >= 6.5 % has 971 positives (16.9 % unweighted, 14.0 % WTPH2YR-weighted). Self-report and HbA1c measure different things (treatment masking, undiagnosed cases); see §5.
- **Missing data.** HbA1c is missing for 297 of 6,064 examined adults (4.9 %), not completely at random (§3.7 missingness model). Income-to-poverty ratio missing for 734 cohort members (12.8 %). Fasting measures (glucose, triglycerides, LDL) exist only for the fasting sub-sample. Refusal / don't-know codes are recoded per variable from the codebook, never with a blanket rule (§3.4 shows that a blanket rule destroys 1,496 valid cohort cells).
- **Confidential or sensitive content.** Health, income and race/ethnicity are sensitive. The files are de-identified public-use data with NCHS disclosure controls (top-coding, masked design units); see `governance/dua_checklist.md`.
- **Sub-populations.** NH Asian adults (315; 50 `L_comb` positives) and uninsured adults are small; estimates for them are exploratory under the NCHS presentation standards.

## 3 Collection process

- **Acquisition.** Household interview (CAPI), Mobile Examination Center (MEC) examination and laboratory analysis of blood specimens; fasting sub-sample for glucose and triglycerides.
- **Sampling.** Complex, multistage probability sample; masked design with 15 strata and 30 PSUs. In this cycle there is no oversampling of race/ethnicity or income groups.
- **Time frame.** August 2021 – August 2023 (one post-pandemic cycle). No other cycle is pooled, so temporal drift cannot be assessed.
- **Response.** Interview response 34.6 %, examination response 25.7 % (NCHS cycle overview). Survey weights adjust for non-response only through known covariates; health-related non-participation cannot be excluded.
- **Consent and ethics.** Collected by NCHS under the approval of the NCHS Ethics Review Board (Protocol #2021-05 for NHANES 2021–2022, <https://www.cdc.gov/nchs/nhanes/about/erb.html>) with documented informed consent; re-use is governed by the NCHS Data User Agreement.

## 4 Preprocessing, cleaning and labelling

Performed in `src/nhanes_io.py`, every step recorded in the decision register (`governance/register/S2.csv`, `S3.csv`):

1. **Integrity.** SHA-256 of each raw XPT checked against `MANIFEST.sha256` before every run.
2. **XPT zero artefact.** pandas reads a stored 0 as 5.397605e-79 (16^-65): 13,676 cells in 9 files (DEMO, GHB, GLU, TCHOL, HDL, TRIGLY, INQ, SMQ, PAQ). Repaired with `x.mask((|x| < 1e-10) & x.notna(), 0.0)`, which keeps NaN as NaN.
3. **Minimisation.** Only spec-included columns are kept (78 of 175).
4. **Sentinels.** Codes described as "Refused" / "Don't know" in the codebook are set to missing for that variable only (e.g. 7/9, 77/99, 777/999, 7777/9999). Continuous laboratory and examination measures have no such codes. `DIQ010 = 3` (borderline) and `HUQ030 = 3` (more than one place of care) are legitimate categories and kept.
5. **Zero weights.** `WTMEC2YR = 0` (not examined) and `WTPH2YR = 0` (no blood sample) are set to missing before weighting.
6. **Derived columns.** Mean of available BP readings, waist-to-height ratio, top-code and missingness flags, readable race and sex.
7. **Outliers.** Flagged (physiological limits, robust z), never deleted.
8. **Labels.** `L_self`, `L_A1c`, `L_comb`, E-SCREEN and the 3x3 strata are defined in `src/labels.py` (§5).

The raw files are kept unmodified; all cleaning is code and can be re-run.

## 5 Uses

- **Intended.** Teaching and research on data governance, label measurement and data preparation; population-level descriptive statistics with survey weights; basic interpretable models (L2 logistic regression with splines, depth-3 tree) evaluated as measuring instruments.
- **Not intended.** Clinical decisions about individuals; a deployable screening tool; causal claims; inference about small subgroups beyond exploratory statements; linkage with other individual-level data (forbidden by the DUA).
- **Known risks.** The label reflects access to diagnosis; BMI under-represents adiposity risk in Asian adults; low response rates limit representativeness. Any model trained on this cohort inherits these biases (§5, §8).

## 6 Distribution

- Source data: public, from <https://wwwn.cdc.gov/nchs/nhanes/> (files under `.../Public/2021/DataFiles/`), downloaded 2026-10-10; redistributed here unmodified for reproducibility, with the DUA conditions attached.
- Derived cohort: not distributed as a file; it is regenerated by `nhanes_io.build_cohort()`. Only aggregate results are published.

## 7 Maintenance

- Maintainer: the project team (repository `main` branch).
- CDC occasionally re-releases files; a changed hash is reported by `ensure_raw_data()` and must be investigated before numbers are compared.
- Errata and changes to the variable specification go through the decision register (`change_request` column); the variable scope is frozen at the `scope-freeze` tag after §3.
