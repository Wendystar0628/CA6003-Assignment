# CA6003 Group Assignment – Who Gets Labelled Diabetic?

NTU MSc AI · CA6003 Best Practices in Data Governance, Preparation and Analytics

A data-centric study of adult diabetes identification using **NHANES Aug 2021 – Aug 2023** (CDC/NCHS public-use files). Following the assignment brief, machine learning is used as *evidence*, not the goal: only basic interpretable models (L2 logistic regression with splines, depth-3 decision tree) are used, and the focus is on what data preparation and labelling decisions change.

## Deliverable

**`notebooks/final/CA6003_NHANES_Diabetes.ipynb`** – one self-contained notebook (executed FINAL run stored). It recreates its own workspace (code, variable specification, governance inputs), loads the raw data from `data/` or downloads it from CDC, verifies all file hashes, and runs every stage end to end. Default mode FAST (≈5 min on a 28-thread desktop); FINAL reproduces the stored results (≈25 min).

## Headline findings

| Finding | Evidence (FINAL; hold-out confirms) |
|---|---|
| A whole-sample AUC measures recognition of already-diagnosed diabetes, not screening value | S: 0.836 on all adults vs 0.781 on the not-yet-diagnosed screening group (gap +0.055 [0.028, 0.086]); hold-out 0.851 vs 0.791 |
| "Told by a doctor" items are care traces | removing them costs 0.016 AUC on all adults but gains +0.019 [0.004, 0.034] on the screening group |
| Leakage and naive cleaning | availability rule lowers AUC by 0.131 (leakage via skip patterns and a median-imputed age-at-diagnosis); blanket sentinel recoding destroys 1,496 valid values |
| Labels are measurements | self-report vs HbA1c κ = 0.70; 30.5 % of self-reported diabetics are masked by treatment; uninsured adults are more often undiagnosed (+23.2 pp) |
| External validity | NCHS Data Brief 516 replicated (15.79 / 11.30 / 4.49 % vs 15.8 / 11.3 / 4.5 %) |

## Process

`docs/development_process.md` (Chinese) defines stages S0–S12, feedback loops, freezes and the git policy; `docs/architecture.md` the code architecture. Freeze tags:

| Tag | Meaning |
|---|---|
| `scope-freeze` | variable specification, cohort (N = 5,730) and data-quality audit fixed |
| `target-freeze` | training label, screening population, 3×3 strata and sensitivity labels fixed |
| `prereg-lock` | hypotheses locked (SHA-256 in commit) before any experiment result |
| `exp-freeze` | experiment configuration fixed; hold-out evaluated once afterwards |

## Repository layout

| Path | Content |
|---|---|
| `notebooks/final/` | release notebook, build record, reference values, builder README |
| `notebooks/sections/` | section sources (jupytext percent) – the notebook is assembled from these |
| `notebooks/executed/` | executed section notebooks (development record) |
| `src/` | `config`, `nhanes_io`, `survey`, `labels`, `prep`, `evalkit`, `fairness`, `robustness`, `plots`, `results_io` |
| `config/variable_spec.csv` | single source of truth for variables (codebook-derived sentinels, roles, admissibility) |
| `governance/` | decision register fragments, hypotheses (locked), claims ledger, limitations, DUA checklist, datasheet, GenAI log |
| `results/` | per-section metrics (`metrics_S*.json`), tables, splits, out-of-fold predictions, `final_metrics.json` |
| `figures/` | all figures with captions |
| `slides/` | 12-minute storyboard, Marp deck, number check |
| `data/nhanes_2021_2023/` | unmodified CDC files (`raw/`), codebooks, `MANIFEST.sha256` |
| `tools/` | section runner, release builder, repository hygiene check |

## Reproduce

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python scripts/download_nhanes.py                                   # verify data hashes
python tools/build_final.py --execute                               # FAST build in a temp dir
python tools/build_final.py --execute --mode FINAL                  # FINAL build
```

## Data governance

- Raw data are the unmodified CDC public-use files (downloaded 2026-10-10); integrity is recorded in `MANIFEST.sha256`; source https://wwwn.cdc.gov/nchs/nhanes/.
- Use follows the [NCHS Data User Agreement](https://www.cdc.gov/nchs/policy/data-user-agreement.html): statistical analysis only, no re-identification, no linkage to other individual-level data; only aggregates are presented.
- Course materials (brief, group list) are kept local only.

## GenAI use

The analysis pipeline contains no LLM or complex model. Planning, code and text were developed with Claude (Anthropic) as a development aid under the developer's direction, with independent cross-audits; all numbers are recomputed in the notebook and the full commit history documents the process. Details are declared in the notebook front matter and `governance/genai_log.csv`.
