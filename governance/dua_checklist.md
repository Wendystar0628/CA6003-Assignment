# Data use checklist: NCHS Data User Agreement, disclosure controls, weights and presentation standards

Notebook §2. Scope: NHANES August 2021 – August 2023 public-use files (suffix `_L`), 16 files listed in `data/nhanes_2021_2023/README.md`.
Sources: NCHS Data User Agreement <https://www.cdc.gov/nchs/policy/data-user-agreement.html>; DEMO_L documentation <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm>; NHANES weighting tutorial <https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx>; cycle overview <https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/overviewbrief.aspx?Cycle=2021-2023>.

## 1 Data User Agreement obligations

| # | Obligation | How this project complies | Check |
|---|---|---|---|
| 1 | Use the data for statistical reporting and analysis only | Estimation of prevalence, label agreement and model performance at population level; no decisions about individuals | [x] |
| 2 | Make no attempt to learn the identity of any person or establishment | No identifying fields are loaded; quasi-identifiers that are not needed (country of birth `DMDBORN4`, years in the US `DMDYRUSR`, military service `DMQMILIZ`, household reference-person fields) are dropped by the loader (`results/S2/minimisation_report.csv`) | [x] |
| 3 | Do not link the data with other individual-level data sets | No linkage. External validation uses published aggregates only (NCHS Data Brief 516; Bang et al. 2009 summary figures). Consequence: an external validation on other micro-data is not possible and is not attempted | [x] |
| 4 | Do not study or try to undo the disclosure-control methods | Top-coding and masked design variables are taken as given, documented (section 2) and flagged; never reverse-engineered | [x] |
| 5 | Report any inadvertent discovery of identity to NCHS and do not use or disclose it | Nothing of the kind is expected; the rule is recorded so that any team member knows the procedure | [x] |

Derived rule: no participant-level rows are shared with GenAI tools or committed outside `data/nhanes_2021_2023/raw/` (the unmodified CDC files). `data/interim/` is git-ignored. See `governance/genai_log.csv`.

## 2 Disclosure controls present in the public files

Recorded in `config/variable_spec.csv` (`top_code`, `note`) and turned into flags by `nhanes_io.build_cohort()`.

| Control | Variable | Handling in this project |
|---|---|---|
| Age top-coded at 80 ("80 years of age and over") | `RIDAGEYR` | `age_top` flag (321 cohort members, computed in §3.6) |
| Income-to-poverty ratio top-coded at 5 | `INDFMPIR` | `pir_top` flag (1,282, 22.4 %); missing ratio flagged `pir_miss` (734, 12.8 %) |
| Household size top-coded at 7 | `DMDHHSIZ` | column not loaded (minimisation) |
| Pregnancy status only for women 20–44 | `RIDEXPRG` | cohort excludes `RIDEXPRG = 1` (37); `RIDEXPRG = 3` "cannot ascertain" (21) kept, flagged `preg_unknown` |
| Masked variance units: 15 strata, 30 PSUs | `SDMVSTRA`, `SDMVPSU` | delete-one-PSU jackknife, national df = 15 (`src/survey.py`, checked in §4.2) |

## 3 Weight selection

The weight is chosen by the smallest sub-sample whose variables enter an analysis (NHANES weighting tutorial).

| Weight | Sub-sample | Used for | Zero / missing meaning |
|---|---|---|---|
| `WTINT2YR` | interviewed (11,933) | descriptions of interview-only variables | – |
| `WTMEC2YR` | MEC-examined (8,860) | descriptions involving BMX or BPXO only | 0 = not examined (3,073 rows; stored as 5.4e-79 in the XPT) |
| `WTPH2YR` | phlebotomy (from `GHB_L`) | every cohort analysis using HbA1c or lipids: weighted descriptions and the weighted-fit ablation (P12) | 0 = no blood sample (449 rows in `GHB_L`); positive for all 5,730 cohort members |
| `WTSAF2YR` | fasting sub-sample (from `GLU_L`) | NCHS DB516 replication and sensitivity label SL5 only | 0 = fasting non-response (635 rows in `GLU_L`); missing outside the sub-sample |

Rules: zero weights are converted to missing before any weighted computation (`nhanes_io.zero_weights_to_nan`). Sub-populations are never analysed by deleting rows; out-of-domain weights are set to 0 so that the design is kept, and the domain df is the number of strata containing domain observations. The duplicate `WTPH2YR` columns in `TCHOL_L` / `HDL_L` and `WTSAF2YR` in `TRIGLY_L` are identical on common SEQN and are not loaded.

Cycle facts that limit inference: interview response rate 34.6 %, examination response rate 25.7 % (NCHS overview); no oversampling of race/ethnicity or income groups in this cycle; NCHS advises against pooling this cycle with earlier ones, so no pooling is done.

## 4 Presentation standards (NCHS, Parker et al. 2017)

Every survey-weighted proportion reported anywhere in the project is checked against these rules; failures are shown with a flag, not hidden.

| Rule | Threshold | Action |
|---|---|---|
| Sample size | n < 30 | suppress or flag "exploratory" |
| Effective sample size | n_eff < 30 | suppress or flag |
| Confidence-interval width (proportions, Korn–Graubard 95 % CI) | width >= 0.30 | flag "exploratory, does not meet NCHS standard" |
| Domain degrees of freedom | df < 8 | flag as unstable |
| Small groups | NH Asian (315 in cohort, 50 `L_comb` positives) | always exploratory, CI reported, never a headline |

Implemented in `src/survey.py` (`nchs_flags`, `korn_graubard_ci`, `domain_df`).

## 5 Provenance and integrity

- Raw XPT files are unmodified CDC downloads (2026-10-10), tracked in git as binary; `MANIFEST.sha256` (LF line endings) fixes their SHA-256 digests. `nhanes_io.ensure_raw_data()` re-hashes all 16 files at the start of each section run; `scripts/download_nhanes.py --force` re-fetches them from CDC.
- Codebooks (`data/nhanes_2021_2023/codebooks/*.htm`) are the only source for value codes; `nhanes_io.verify_spec()` asserts that every sentinel code in the specification appears in the codebook as "Refused" or "Don't know".

## 6 Sign-off

| Item | Status |
|---|---|
| DUA obligations 1–5 mapped to project practice | done |
| Disclosure controls recorded in spec and flagged in cohort | done |
| Weight map and zero-weight semantics | done |
| Presentation standards wired into `survey.py` | done (§4.2, §4.5) |
| Hash verification at every run | done (§0.4, §2.1) |
