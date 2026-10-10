# Label freeze (freeze point 2, tag `target-freeze`)

Stage S5 · decision DR-S5-01 (target), DR-S5-09 (evaluation populations), DR-S5-10 (sensitivity labels) · loop L2.
Evidence: `notebooks/sections/04_labels_bias.py` §5.1–§5.8, `results/metrics_S5.json`, `results/S5/*.csv`.

Every definition below is **executable**: it names the function in `src/labels.py` that implements it, and
section §5.8 recomputes the counts in the JSON block at the end of this file and asserts that they are equal.
If code and document ever disagree, the notebook fails.

## 1 Status and honesty statement

- The L2 decision gate (C1–C4) was evaluated **after** looking at the data (S3–S5). It is a documented judgement,
  not a pre-registered test (`prior_exposure = analysis_seen`). Only the S7/S8 experiment hypotheses are
  pre-registered (`governance/hypotheses.md`, `prereg-lock`).
- After this freeze, any change to the definitions below requires a decision-register row with a
  `change_request`, re-opening L2 (at most one round) and a `fix` commit.

## 2 Population

Adults aged ≥ 20, interviewed and MEC-examined (`RIDSTATR == 2`), HbA1c observed (`LBXGH` not missing), not
pregnant (`RIDEXPRG != 1`): **N = 5,730** (`nhanes_io.build_cohort()`, per-variable sentinel recoding, XPT zero
artefact repaired). Analysis weight `WTPH2YR`; variance by delete-one-PSU jackknife (15 strata, df = 15).

## 3 Frozen training target

| Name | Definition | Code | Positives |
|---|---|---|---|
| `L_self` | `DIQ010 == 1` (doctor-diagnosed diabetes). Borderline (3), No (2), Don't know / refused / missing → 0 | `labels.add_labels` | 819 |
| `L_A1c` | `LBXGH >= 6.5` (HbA1c, %) | `labels.add_labels` | 721 |
| **`L_comb`** (**frozen target**) | `L_self OR L_A1c` | `labels.add_labels` | **971** (16.9 %; WTPH2YR-weighted 14.0 %) |
| `borderline` | `DIQ010 == 3`; **negative** in `L_self` / `L_comb`, kept as a flag | `labels.add_labels` | 213 (36 with HbA1c ≥ 6.5) |

Gate result (post-hoc, §5.8, `results/S5/l2_gate.csv`):

| Criterion | Result |
|---|---|
| C1 each single instrument misses a material share of the union | PASS: `L_self` misses 152/971 = 15.7 %, `L_A1c` misses 250/971 = 25.7 %; κ = 0.70, PA 0.74, NA 0.96 |
| C2 no admissible feature is a target component | PASS: LBXGH, DIQ010, DIQ050, DIQ070, DID040, DID060, DIQ160, DIQ180, LBXGLU are non-admissible in `config/variable_spec.csv` |
| C3 ≥ 500 positives, ≥ 40 in the smallest reported group | PASS: 971; NH Asian 50 under `L_comb`, exactly 40 under `L_A1c` (Asian results descriptive only) |
| C4 borderline coding | PASS: negative and flagged; borderline-positive variant = SL3 (1,148 positives) |

## 4 Evaluation populations

**E-ALL** – all 5,730 adults, outcome `L_comb`.

**E-SCREEN** (co-primary) – adults who do **not** report diagnosed diabetes:

```python
d = labels.add_labels(nhanes_io.build_cohort())
escreen = d[d["in_escreen"] == 1]          # in_escreen = (DIQ010 != 1); 4,911 adults
y = escreen["y_escreen"]                   # = (LBXGH >= 6.5); 152 positives, 4,759 negatives
```

Borderline respondents (DIQ010 = 3) stay in E-SCREEN with their HbA1c outcome and are flagged
(`borderline == 1`); 36 of them are positive. Rows outside E-SCREEN have `y_escreen = NaN`, so they cannot be
scored by accident. Reason: 84 % of `L_comb` positives (819/971) are already diagnosed, so E-ALL largely
measures recognition of known disease; E-SCREEN matches the screening use case (process doc §1.3).

## 5 3×3 label matrix (SL6)

`labels.add_labels` → column `stratum_3x3`:

| Stratum | Definition | n |
|---|---|---|
| `D_uncontrolled` | `L_self == 1 and L_A1c == 1` | 569 |
| `D_controlled` | `L_self == 1 and L_A1c == 0` (treatment masking) | 250 |
| `Undiagnosed` | `L_self == 0 and L_A1c == 1` (= E-SCREEN positives) | 152 |
| `NonDiabetic` | `L_self == 0 and L_A1c == 0` (common negatives) | 4,759 |

Procedure (S8): rows = training label ∈ {`L_self`, `L_A1c`, `L_comb`}; columns = the three positive strata; for
each cell, recall of that stratum against the common 4,759 `NonDiabetic` negatives at the threshold giving
specificity 0.80 on those negatives (`C.SPEC_FIXED`); ROC-AUC secondary. Pre-registered shape: `L_self` misses
`Undiagnosed` most, `L_A1c` misses `D_controlled` most, `L_comb` has the smallest worst-cell gap; differences
< 0.05 are reported as equivalent.

## 6 Sensitivity labels SL1–SL7

`labels.sensitivity_labels(d)` returns SL1–SL5 as columns aligned with the cohort; SL6 and SL7 are procedures.

| Label | Executable definition | Weight | Positives |
|---|---|---|---|
| SL1 | `L_A1c` | WTPH2YR | 721 |
| SL2 | `L_self` | WTPH2YR | 819 |
| SL3 | `L_comb OR borderline` | WTPH2YR | 1,148 |
| SL4 | `L_A1c OR (L_self AND diq070_universe AND (DIQ050 == 1 OR DIQ070 == 1))`; DIQ070 universe = `DIQ010 == 1`, or `DIQ010 == 3`, or (`DIQ010 == 2` and `DIQ160 == 1`). Pills reported by borderline (44) or prediabetic (41) respondents – plausibly metformin for prediabetes – do **not** create a case | WTPH2YR | 886 |
| SL5 | NCHS definition: `L_self OR LBXGH >= 6.5 OR LBXGLU >= 126`, only on the fasting subsample (`WTSAF2YR > 0` and `LBXGLU` observed; `labels.fasting_mask`), NaN elsewhere | WTSAF2YR | 565 of 2,938 |
| SL6 | 3×3 label matrix (section 5) | – | – |
| SL7 | Permutation negative control: train on `L_comb` permuted within the training folds (`C.N_PERM` permutations); expected ROC-AUC ≈ 0.5 (S9) | – | – |

Use in later stages: S8 runs SL6; S9 re-evaluates the selected arm under SL1–SL5 and runs SL7.

## 7 Frozen counts (machine-checked by §5.8)

```json
{"N": 5730, "L_comb": 971, "L_self": 819, "L_A1c": 721, "strata_3x3": {"D_uncontrolled": 569, "D_controlled": 250, "Undiagnosed": 152, "NonDiabetic": 4759}, "escreen_positives": 152, "escreen_negatives": 4759, "escreen_borderline_positive": 36, "SL_positives": {"SL1": 721, "SL2": 819, "SL3": 1148, "SL4": 886, "SL5": 565}, "SL5_n": 2938}
```
