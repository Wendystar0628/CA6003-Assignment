# Code Architecture and Team Protocol

Companion to `docs/development_process.md` (the *what/why*); this file fixes the *how*: layout, module contracts, conventions, ownership and the multi-agent working protocol. Methodology, numbers and decisions in the process document are binding.

## 1. Layout

```
config/variable_spec.csv        single source of truth for variables (S2)
src/                            importable helpers (package `src`)
  config.py                     paths, seeds, CV/bootstrap sizes, SESOI, weights   [lead]
  plots.py                      Okabe–Ito style, savefig()                           [lead]
  results_io.py                 results/metrics_<S>.json per section, collect()     [lead]
  nhanes_io.py                  load / fix XPT / sentinels / cohort (S2–S3)
  survey.py                     weights, PSU jackknife, KG CIs, standardisation (S4)
  labels.py                     label definitions, E-SCREEN, 3x3 strata, SL1–SL7 (S5)
  prep.py                       toggleable preparation steps, arms, blocks (S6)
  evalkit.py                    splits, metrics, corrected t, bootstrap, permutation (S7)
  fairness.py                   group metrics, 3x3 matrix, mitigation (S8)
  robustness.py                 negative controls, seeds, sensitivity, leak hunt (S9)
notebooks/sections/NN_*.py      jupytext percent scripts = sections of the final notebook
notebooks/executed/NN_*.ipynb   executed sections (tools/run_section.py)
notebooks/final/                assembled, executed deliverable (S11)
governance/                     register/<S>.csv fragments, hypotheses.md, claims.csv, docs
results/                        metrics_<S>.json, tables (csv/parquet), splits
figures/                        <S>_<name>.png (+ .txt caption)
tools/                          run_section.py, check_repo.py, build_final.py (S11)
slides/                         storyboard and slide assets (S11)
```

## 2. Section notebooks

| File | Stage | Content |
|---|---|---|
| `00_setup.py` | S0 | environment check, versions, seeds, data integrity (MANIFEST) |
| `01_scope_governance.py` | S1–S2 | question, availability rule, E-ALL/E-SCREEN, hypotheses summary, DUA, minimisation, variable spec |
| `02_profiling.py` | S3 | funnel, XPT artefact, sentinel audit & blanket-recode cost, consistency, missingness, outliers, DQ matrix |
| `03_eda.py` | S4 | weights, DB516 replication, standardisation, Simpson scan, DAG, VIF, skewness, linearity, DAJ table |
| `04_labels_bias.py` | S5 | label audit, treatment masking, undiagnosed inequality, Asian BMI vs WHtR, representation, label freeze |
| `05_prep_design.py` | S6 | arms M0/M1/S, steps P01–P14, blocks B1–B6, hypotheses lock |
| `06_experiments.py` | S7 | baselines, block ablation, E-ALL vs E-SCREEN, coefficient stability |
| `07_fairness.py` | S8 | group metrics, 3x3 label matrix, WHtR & reweighing arms |
| `08_robustness.py` | S9 | permutation, seeds, sensitivity table, leak hunt, one-shot hold-out |
| `09_synthesis.py` | S10 | scoreboard, claims, “what ML says about the data”, limitations, ethics |

Rules:
- Percent format (`# %%` code, `# %% [markdown]` text). First cell is markdown `# §N Title (Stage Sx)`; every analysis step follows **Why → What → So what** (markdown – code – markdown with the concrete numbers).
- Standard bootstrap cell (copy verbatim):
  ```python
  import sys, pathlib
  _here = pathlib.Path.cwd()
  ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
  sys.path.insert(0, str(ROOT))
  from src import config as C, plots, results_io as R
  ```
- Sections must run standalone in order (each re-loads the cohort via `nhanes_io.build_cohort()` – a few seconds – and reads upstream artefacts from `results/`). No hidden state, no absolute paths.
- Every reported number is computed in the section and stored with `R.save_section("Sx", {...})`. Never type numbers by hand into markdown without a code cell that prints them (assert against expected values where the process doc gives them, with a tolerance).
- Figures: `plots.savefig(fig, "S4_db516_forest", caption="...")`.
- Runtime: FAST mode (default) ≤ ~1 min per section where possible; FINAL mode is used for the final executed notebook. Read sizes from `config` (`C.CV_REPEATS`, `C.N_BOOT`, …), never hard-code them.
- Run check: `.venv/Scripts/python tools/run_section.py notebooks/sections/NN_x.py` must print `OK`.

## 3. Module contracts (signatures are binding; add helpers freely, change these only via the lead)

### `nhanes_io.py` (S2–S3)
```python
COHORT_N: int = 5730
ensure_raw_data(download: bool = True) -> dict            # verify MANIFEST, fetch missing from CDC
read_xpt(name: str) -> pd.DataFrame                       # raw pandas.read_sas, NO fixes
fix_xpt(df) -> tuple[pd.DataFrame, int]                   # mask(|x|<1e-10 & notna -> 0), returns n_fixed
load_spec() -> pd.DataFrame                               # config/variable_spec.csv
apply_sentinels(df, spec=None, mode="per_variable"|"blanket") -> tuple[pd.DataFrame, pd.DataFrame]  # (clean, audit)
load_merged(files=None, *, fix=True, sentinels="per_variable") -> pd.DataFrame   # DEMO-left-joined on SEQN
build_cohort(df=None, *, sentinels="per_variable") -> pd.DataFrame
    # adults >=20, RIDSTATR==2, LBXGH notna, RIDEXPRG!=1 -> 5,730 rows (assert)
    # derived: bp_sys_mean, bp_dia_mean (mean of available readings 1-3), whtr = BMXWAIST/BMXHT,
    #          age_top (RIDAGEYR==80), pir_top (INDFMPIR==5), pir_miss, race (labelled RIDRETH3), sex
funnel() -> pd.DataFrame                                  # step, n
```

### `survey.py` (S4)
```python
US2000_3BAND = {"20-39": 0.3966, "40-59": 0.3718, "60+": 0.2316}
jackknife(df, stat_fn, *, weight, strata=C.STRATA, psu=C.PSU) -> dict  # est, se, df, ci_low, ci_high (t_df)
weighted_mean(x, w) -> float
weighted_prop(df, y, *, weight, domain=None) -> dict      # est + JK se/ci + n + n_eff + df + KG ci + nchs_flags
korn_graubard_ci(p, n_eff, df, alpha=0.05) -> tuple
domain_df(df, mask, strata=C.STRATA, psu=C.PSU) -> int    # number of strata containing domain observations (doc §7.1)
age_standardise(df, y, group, *, weight, std=US2000_3BAND) -> pd.DataFrame   # rates + JK CI per group
std_difference(df, y, group, a, b, *, weight, std=US2000_3BAND) -> dict      # crude & standardised diff with JK CI
kish_deff(w) -> float
nchs_flags(n, n_eff, ci_width, df) -> list[str]
```

### `labels.py` (S5)
```python
add_labels(cohort) -> pd.DataFrame
    # L_self (DIQ010==1), L_A1c (LBXGH>=6.5), L_comb, borderline (DIQ010==3),
    # stratum_3x3 in {"D_uncontrolled","D_controlled","Undiagnosed","NonDiabetic"},
    # in_escreen (DIQ010!=1), y_escreen (LBXGH>=6.5 within E-SCREEN)
sensitivity_labels(cohort) -> pd.DataFrame                # SL1..SL5 columns (SL6/SL7 are procedures)
confusion(cohort, *, weight=None) -> pd.DataFrame
```

### `prep.py` (S6)
```python
STEPS = ("P01", ..., "P14"); BLOCKS = {"B1": ["P01","P02"], "B2": ["P03"], "B3": ["P04","P05"],
          "B4": ["P06","P07"], "B5": ["P08","P09","P10","P13"], "B6a": ["P11"], "B6b": ["P12"]}
ARMS: dict[str, dict[str, bool]]                          # "M0", "M1", "S", "S-B1" ... (leave-one-block-out), "T1-minus-care", "S-linear", "S+WHtR"
raw_feature_frame(cohort, tier: int) -> pd.DataFrame      # columns entering M0 (incl. traps) for the tier
build_pipeline(cfg: dict[str, bool], tier: int, model: str = "lr") -> sklearn.pipeline.Pipeline
model_kwargs(cfg) -> dict                                 # class_weight / sample_weight handling (P11/P12)
```

### `evalkit.py` (S7)
```python
make_holdout(cohort, seed=C.SEED_MASTER) -> tuple[np.ndarray, np.ndarray]   # stratified label x race; persisted
make_folds(y, strat, *, n_splits=C.CV_SPLITS, n_repeats=C.CV_REPEATS, seed) -> list[tuple]; persisted
cv_predict(make_pipe, X, y, folds, *, fit_params=None) -> pd.DataFrame       # repeat, fold, row, prob
metric_suite(y, p, *, w=None) -> dict          # roc_auc, pr_auc, brier, recall_at_spec, balanced_acc, cal_slope, cal_intercept
recall_at_specificity(y, p, spec=C.SPEC_FIXED, neg_mask=None) -> float
fold_metrics(oof, y, eval_mask=None) -> pd.DataFrame
corrected_t(diffs, n_train, n_test, alpha=0.05) -> dict  # Nadeau–Bengio
paired_bootstrap(y, p_a, p_b, metric, *, n_boot=C.N_BOOT, seed, eval_mask=None) -> dict
verdict(ci_low, ci_high, sesoi, direction) -> str        # supported/refuted/equivalent/inconclusive
coef_bootstrap(make_pipe, X, y, *, n_boot=C.N_BOOT_COEF, seed) -> pd.DataFrame
```

`fairness.py` (S8) and `robustness.py` (S9) are defined by their owners and documented in their module docstrings.

## 4. Artefacts

- `config/variable_spec.csv` – columns per process doc §7.2 (owner: S2).
- `governance/register/<S>.csv` – decision-register fragment per stage, columns per §7.2; `tools/build_final.py` merges them into `governance/decision_register.csv`.
- `governance/hypotheses.md` – owner S6; other stages propose entries via message.
- `results/metrics_<S>.json` – one per section via `results_io`; `results/final_metrics.json` = `collect()`.
- `results/<S>/...` – section tables (csv/parquet); `results/splits/` – holdout ids and folds (S7).

## 5. Ownership

Each agent edits only the files it owns. To change a shared or foreign file, message its owner (or the lead for `config.py`, `plots.py`, `results_io.py`, `docs/*`, `tools/run_section.py`, `tools/check_repo.py`). Ownership is assigned in the agent briefs.

## 6. Git protocol for agents

- Work in the shared checkout on `main`. Never `git add -A`/`git add .`, never rewrite history, never push (the lead pushes), never touch `course/`.
- Commit after every medium-sized step (process doc §6): stage and commit only your own paths:
  ```bash
  git add <your paths> && git commit -m "<type>(S<n>): <summary>" -m "<body: what/why, key numbers, register ids>" -m "Co-Authored-By: Claude <Opus|Sonnet> 5.5 <noreply@anthropic.com>" -- <your paths>
  ```
  If git reports `index.lock`, wait 3–5 s and retry (other agents commit in parallel).
- Before committing: the section runs (`tools/run_section.py` → OK) and `tools/check_repo.py <paths>` → OK.
- Freeze commits with tags are made by the lead.

## 7. Communication protocol

- Agents are addressable by name with SendMessage. Use it to: announce that a contract function is ready, request a change in someone else's file, report a number that contradicts the process doc (§8 facts), or ask the lead (`main`) to arbitrate.
- Keep messages short and concrete (file, function, expected vs actual).
- If a verified number differs from the process doc by more than rounding, do not silently change the doc: report to the lead with the evidence.
