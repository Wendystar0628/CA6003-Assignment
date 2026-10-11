# S1 Scope: problem, populations, availability rule and governance

Status: drafted in §1, target frozen at the end of §5 (`target-freeze`). §1 of the notebook recomputes every number below from the raw files and asserts it. Literature points are stated only at the strength that was checked against a primary source (see "Literature checks" at the end).

## Research question and use case

**Question.** Can adult diabetes (diagnosed or undiagnosed) be identified from non-glycaemic information that is available at a clinical contact, how much of that ability survives in the population that screening is actually meant for, and how do data-preparation decisions change the answer?

**Use case.** A screening aid applied to an adult *before any glucose test*. A feature is allowed into a model only if it can be obtained at that moment. The models are deliberately basic and interpretable (L2 logistic regression with splines; a shallow decision tree for thresholds and leakage probing); the model is used as a *measuring instrument* for the data, not as the product.

**Not in scope.** Complex or LLM-based models; causal estimation; linkage with external individual-level data (forbidden by the data user agreement); pooling NHANES cycles; firm conclusions about the small Asian subgroup.

## Analysis cohort and target

| Item | Definition |
|---|---|
| Cohort | NHANES August 2021 to August 2023, adults aged 20 or older, examined (RIDSTATR = 2), HbA1c observed, not pregnant; N = 5,730 (funnel 11,933 to 7,809 to 6,064 to 5,767 to 5,730) |
| Training target (frozen) | `L_comb` = self-reported physician diagnosis (DIQ010 = 1) or HbA1c >= 6.5 %; 971 positives (16.9 % unweighted, 14.0 % with WTPH2YR) |
| Borderline | DIQ010 = 3 is coded negative and flagged (213 in the cohort); counting it positive is sensitivity label SL3 |

## Evaluation populations

Of the 971 positives of `L_comb`, 819 (84 %) had already reported a diagnosis. A high AUC on the whole cohort therefore mostly measures how well the model recognises people who are *already known* to have diabetes and carry the traces of that contact. Two co-primary populations are reported:

| Population | Rows | Positive class | Meaning |
|---|---|---|---|
| **E-ALL** | all 5,730 | `L_comb` (971) | recognising diabetes in the cohort, including known cases |
| **E-SCREEN** | 4,911 with DIQ010 != 1 | HbA1c >= 6.5 % (152 positives, 4,759 negatives) | finding diabetes in people not known to have it |

The ADA-lite baseline is compared **only on E-SCREEN**, matching the outcome of Bang 2009 (undiagnosed diabetes). The gap between E-ALL and E-SCREEN performance is itself a headline finding: the label composition inflates the apparent screening value.

## Feature-availability rule

A feature is admissible only if all hold: (1) it can be obtained at the screening moment by questionnaire, basic physical measurement or, for Tier 2, a lipid panel from the same visit; (2) it is not a diagnostic criterion; (3) it is not a consequence of diagnosis (medication, age at diagnosis, tests ordered because of diabetes); (4) it is not derived from the target. Leakage is decided by this rule and never by impression of a single variable.

* **Tier 1 (T1)**: demographics, BMI, waist or waist-to-height ratio (WHtR), mean blood pressure, BPQ020, BPQ080, SMQ020, physical activity.
* **Tier 2 (T2)**: T1 plus total cholesterol and HDL.
* Race is **not** a model input by default; insurance (HIQ011) and usual place of care (HUQ030) are audit variables only.
* BPQ020 (told hypertension) and BPQ080 (told high cholesterol) are admissible but are, like DIQ160 and DIQ180, traces of earlier contact with health care; a separate **T1-minus-care** ablation arm removes both and is reported on E-ALL and E-SCREEN.

### Variable availability

The authoritative per-variable record is `config/variable_spec.csv` (§2); §1.3 compares the two and asserts that they agree.

| variable | file | meaning | admissible | reason |
|---|---|---|---|---|
| LBXGH | GHB_L | HbA1c | N | part of the target (diagnostic criterion) |
| LBXGLU | GLU_L | fasting plasma glucose | N | diagnostic criterion; fasting subsample only |
| DIQ010 | DIQ_L | doctor-diagnosed diabetes | N | part of the target |
| DIQ050 | DIQ_L | taking insulin | N | consequence of diagnosis |
| DIQ070 | DIQ_L | taking diabetic pills | N | consequence of diagnosis; also asked of undiagnosed respondents |
| DID040 | DIQ_L | age at diagnosis | N | consequence of diagnosis |
| DID060 | DIQ_L | duration of insulin use | N | consequence of diagnosis |
| DIQ160 | DIQ_L | told prediabetes | N | consequence of a glucose test; care-contact trace |
| DIQ180 | DIQ_L | blood sugar tested in past 3 years | N | consequence of care contact |
| LBXTLG | TRIGLY_L | triglycerides | N | fasting subsample only; side analysis |
| LBDLDL | TRIGLY_L | LDL cholesterol | N | derived from TC, HDL and triglycerides; fasting subsample only |
| RIDRETH3 | DEMO_L | race and ethnicity | N | audit and fairness variable, not a default predictor |
| HIQ011 | HIQ_L | health insurance | N | audit variable (access to care) |
| HUQ030 | HUQ_L | usual place of care | N | audit variable (access to care) |
| RIDAGEYR | DEMO_L | age (top-coded at 80) | T1 | known at any contact |
| RIAGENDR | DEMO_L | sex | T1 | known at any contact |
| INDFMPIR | DEMO_L | income-to-poverty ratio (top-coded at 5) | T1 | interview item; 12.8 % missing |
| DMDEDUC2 | DEMO_L | education | T1 | interview item |
| BMXBMI | BMX_L | body mass index | T1 | basic measurement |
| BMXWAIST | BMX_L | waist circumference | T1 | basic measurement |
| whtr | derived | waist / height | T1 | basic measurement; replaces waist in the WHtR arm |
| bp_sys_mean | BPXO_L | mean systolic blood pressure of up to 3 readings | T1 | basic measurement |
| bp_dia_mean | BPXO_L | mean diastolic blood pressure of up to 3 readings | T1 | basic measurement |
| BPQ020 | BPQ_L | told high blood pressure | T1 | questionnaire; care-contact trace |
| BPQ080 | BPQ_L | told high cholesterol | T1 | questionnaire; care-contact trace |
| SMQ020 | SMQ_L | smoked 100 cigarettes in life | T1 | questionnaire |
| PAD790Q | PAQ_L | physical activity (recreational, weekly minutes derived) | T1 | questionnaire |
| LBXTC | TCHOL_L | total cholesterol | T2 | same-visit lipid panel |
| LBDHDD | HDL_L | HDL cholesterol | T2 | same-visit lipid panel |

Raw weight, height, hip and arm circumference are available but removed as structurally redundant with BMI and waist (VIF 95.7 and 97.6, §4.9). That is a *preparation* decision, not an availability decision.

## ADA-lite baseline

This cycle has no questions on family history of diabetes or gestational diabetes (checked in the MCQ_L and DIQ_L variable lists). The baseline is therefore called **ADA-lite: a reduced version missing 2 items**, never a reproduction of the ADA risk score.

| Item (Bang 2009) | NHANES 2021-23 | Status |
|---|---|---|
| Age | RIDAGEYR | available |
| Sex | RIAGENDR | available |
| History of hypertension | BPQ020 | available |
| Body mass index | BMXBMI (measured) | available |
| Physical activity | PAQ leisure-time items; inactive = no moderate and no vigorous sessions (PAD790Q = PAD810Q = 0) | available |
| Family history of diabetes | none in MCQ_L or DIQ_L | **missing** |
| Gestational diabetes | none in the 2021-23 files | **missing** |

Comparison on E-SCREEN: AUC as primary metric and recall at a fixed specificity as secondary (§7.6). Only the figures in the abstract of Bang et al. (2009) are used (cut-off >= 5 points: sensitivity 79 %, specificity 67 %; checked in §9.8.3). AUC values of 0.79 or 0.83 that circulate in secondary sources were not verified against the full text and are not used. The outcome there is fasting glucose >= 126 mg/dL, not HbA1c, so the comparison is qualitative.

## Research questions

| RQ | Question | Hypotheses |
|---|---|---|
| RQ1 | Labels as measurement: what do self-report and HbA1c each measure, and who is missed by each? | H1a, H1b |
| RQ2 | Rules and preparation: how much does the availability rule (leakage) and systematic preparation change performance and stability, in E-ALL and in E-SCREEN? | H2a, H2b, H2c |
| RQ3 | The 3 x 3 label matrix: how does the training label (self-report, HbA1c, combined) change who is detected? | H3 |
| RQ4 | Measurement bias of BMI in Asian adults and the WHtR repair | H4a, H4b |

The hypotheses (metric, direction, magnitude, SESOI, falsifier, `prior_exposure`, weights) are in `governance/hypotheses.md`. Only the experimental hypotheses of §7/§8 claim genuine pre-registration; the others carry the exposure level honestly.

## Novelty statement

This project does not claim to discover that Asian adults develop diabetes at lower BMI, or that undiagnosed diabetes is linked to limited contact with health care; both are established. Its contribution is a combination applied to the 2021-2023 NHANES cycle with fixed basic models: an audit of the label as a measurement, a feature-availability rule that defines leakage, the quantified cost of blanket data cleaning, design-aware evaluation, and pre-registered paired ablations, triangulated against the published NCHS Data Brief 516 and a reduced ADA risk baseline. We have not found this integration in the literature we consulted.

## Governance

### Data user agreement obligations

| Obligation (NCHS DUA) | How the project complies |
|---|---|
| Use for statistical reporting and analysis only | Only population-level estimation and model evaluation; no individual-level decisions |
| No attempt to identify any person or establishment | No identifying fields are used; no external lookup |
| No linkage with other data sets that could identify individuals | External validation is against published aggregates only (DB516, Bang 2009) |
| No study of disclosure-control methods | Top-coding is taken as given and documented, never probed |
| Presentation standards for survey estimates | Flag n < 30, effective n < 30, 95 % CI width >= 0.30, domain df < 8 as exploratory |

### Disclosure controls already in the files

Age is top-coded at 80, income-to-poverty ratio at 5, household size at 7; pregnancy status is given only for women aged 20-44; variance units are masked (15 strata, 30 PSUs). They are recorded as `top_code` and `note` in the variable specification, and `age_top`, `pir_top` and `pir_miss` indicators are kept so that top-coding is not silently treated as a measurement.

### Data minimisation

Only variables listed as `include` in the specification are retained; the loader drops the other columns immediately and writes `results/S2/minimisation_report.csv` (columns kept and dropped per file). Excluded groups (child-only items, country of birth and years of residence, military service, unrelated MCQ items) are listed with a reason. Reference points: GDPR Article 5(1)(b)-(c) (purpose limitation, data minimisation) as the standard of good practice. The Singapore PDPA has a Purpose Limitation Obligation (section 18) and a Retention Limitation Obligation (section 25) but no obligation named "data minimisation"; we apply the stricter GDPR principle.

### Survey weights and representativeness

| Analysis | Weight |
|---|---|
| interview-only variables | WTINT2YR |
| variables from the examination | WTMEC2YR |
| anything using HbA1c or lipids, including this cohort | WTPH2YR |
| fasting subsample, DB516 replication | WTSAF2YR |

Variance by delete-one-PSU jackknife (national df = 15; subdomain df = number of strata containing the domain). The 2021-2023 cycle has an interview response rate of 34.6 % and an examination response rate of 25.7 %, and it has no oversampling by race and ethnicity or by income, which earlier cycles used (small subgroups such as Asian adults are therefore thin); weights correct for known covariates only and do not remove non-response bias that depends on health status. NCHS advises against pooling with other cycles; this project does not.

## Plausibility checks

No target interval for performance is set in advance. The leak hunt (§9.9) is triggered only for admissible arms (M1, S): T1 AUC above 0.90 on E-ALL, or any admissible single feature (age excepted) with AUC above 0.75.

## Literature checks

* Bang et al. (2009): the abstract figures (cut-off >= 5, sensitivity 79 %, specificity 67 %) are used; the AUC is not used (§9.8.3). The item points of the score are applied as described in §7.6.
* NCHS presentation standards (Parker et al. 2017): the project applies a simplified rule set (n < 30, effective n < 30, 95 % CI width >= 0.30, domain df < 8 lead to a flag; see `governance/dua_checklist.md`, section 4). It is not a full implementation of the standard, which also has relative-width and complementary-proportion criteria.
* ADA-lite activity item: defined as "no leisure-time moderate or vigorous activity", matching the yes/no question of the published score, not a minutes threshold.
