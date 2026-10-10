# CA6003 Group Assignment – Who Gets Labelled Diabetic?

NTU MSc AI · CA6003 Best Practices in Data Governance, Preparation and Analytics

A data-centric study of adult diabetes identification using **NHANES Aug 2021 – Aug 2023** (CDC/NCHS public-use files). Following the assignment brief, machine learning is used as *evidence*, not the goal: only basic interpretable models (logistic regression, shallow decision tree) are used, and the focus is on what data preparation decisions change.

## Project in one paragraph

We use a simple model as a measurement instrument to audit three layers of the data:

- **Labels**: self-reported diagnosis vs measured HbA1c, treatment masking, and undiagnosed cases.
- **Features**: BMI vs waist-to-height ratio for Asian adults.
- **Sample**: survey weights and a low response rate.

We then compare minimally vs systematically prepared data with the same model. Key design choices:

- A feature-availability rule that defines leakage.
- Two co-primary evaluation populations: the full cohort and the screening-relevant undiagnosed group.
- Pre-registered paired ablations.
- External validation against NCHS Data Brief 516.

## Repository layout

| Path | Content |
|---|---|
| `docs/development_process.md` | End-to-end development process: stages S0–S12, feedback loops, freezes, roles, per-stage plans (Chinese) |
| `docs/topic_brief.html` | Topic-selection brief shown to the team (bilingual) |
| `data/nhanes_2021_2023/` | Raw XPT files (`raw/`, 16 files, ~13 MB), CDC `codebooks/`, data notes (`README.md`), `MANIFEST.sha256` |
| `scripts/download_nhanes.py` | Verifies local files against `MANIFEST.sha256`; re-downloads from CDC with `--force` |
| `profiling/` | First-pass profiling scripts and outputs |
| `notebooks/` | Member notebooks and the final assembled notebook (to come) |
| `src/` | Shared helpers: `nhanes_io.py`, `survey.py`, `prep.py`, `evalkit.py` (to come) |
| `config/` | `variable_spec.csv`, the single source of truth for variables (to come) |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python scripts/download_nhanes.py   # optional: verify hashes (data already included)
python -I profiling/nhanes_deep.py data/nhanes_2021_2023/raw
```

## Data governance

- Raw data are the unmodified CDC public-use files (downloaded 2026-10-10), included for reproducibility; integrity is recorded in `MANIFEST.sha256` and the original source is https://wwwn.cdc.gov/nchs/nhanes/.
- Use follows the [NCHS Data User Agreement](https://www.cdc.gov/nchs/policy/data-user-agreement.html): statistical analysis only, no re-identification, and no linkage to other individual-level data.
- Course materials (brief, group list) are kept local only.

## Status

| Date | Milestone |
|---|---|
| 2026-10-10 | Data downloaded and profiled; topic chosen (NHANES) |
| 2026-10-11 | Development process designed and cross-audited (`docs/development_process.md`) |
| 2026-10-18 12:00 | Submission deadline (notebook + ≤12-min video) |

## GenAI use

Planning, profiling scripts and the development-process document were drafted with Claude (Anthropic) and cross-audited. All numbers must be reproduced in the team's own notebooks. Details will be declared in the final notebook.
