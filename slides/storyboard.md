# Storyboard for the 12-minute video (S11b)

Plan for the slide deck in `slides/deck.md`. Target 11:20, hard cap 11:40, container limit 12:00. Presenter assignment is decided by the team and is not planned here. Every number comes from `results/S10/numbers_on_slides.csv` and is verified by `slides/check_numbers.py`.

## Story spine

Models are used as measuring instruments. Each finding is something the instrument revealed about the data, not a model score. The three headline findings come from `results/S10/headline_findings.csv`; the headline non-obvious finding is recognition versus screening.

| Finding | What the instrument revealed | Slides |
|---|---|---|
| F1 Leakage and naive cleaning | Skip-logic items and sentinel recoding create performance and destroy valid data | V2.1, V3.1, V3.2 |
| F2 Fallacies and measurement of performance | Age confounding, honest uncertainty, mediator trap; redundancy and skewness diagnostics | V4.1 to V4.3, V5.1, V5.2 |
| F3 Label and measurement bias | Treatment masking, undiagnosed gap, 3×3 matrix, Asian BMI and WHtR | V6.1 to V6.5 |
| Headline: AUC measures recognition, not screening | E-ALL against E-SCREEN with the care-trace reversal, confirmed on the hold-out | V7.3, V7.4, V8.1 |

## Timing

| Segment | Window | Budget (s) | Slides | Rubric hook |
|---|---|---|---|---|
| V1 Scope and design | 0:00–1:30 | 90 | 5 | RB1 |
| V2 Cost of naive cleaning | 1:30–2:15 | 45 | 1 | RB1 |
| V3 Leakage gate | 2:15–3:30 | 75 | 2 | RB1, HR4 |
| V4 Redundancy and skewness | 3:30–4:30 | 60 | 3 | RB3 |
| V5 Fallacies | 4:30–6:00 | 90 | 2 | RB3 |
| V6 Label and measurement bias | 6:00–8:30 | 150 | 5 | RB4 |
| V7 Experiments synthesis | 8:30–10:15 | 105 | 5 | RB4, HR1, HR2, HR3, HR4 |
| V8 Conclusions, limitations, ethics, GenAI | 10:15–11:20 | 65 | 3 | RB2, HR5 |
| Total | 0:00–11:20 | 680 | 26 | cap 11:40 leaves a 20 s reserve |

Speaker notes are sized at about 2.2 words per second, so a slide's notes fit its budget.

## Slides

Field legend. `type` is figure, text, template or title. `takeaway` is the one-line caption under the figure, at most 15 words. `numbers used` lists `segment · label = value` rows of `numbers_on_slides.csv`. Titles are noun phrases of at most six words.

### V0 · NHANES Diabetes Models as Instruments
- **type**: title
- **time**: 10 s (0:00–0:10)
- **figure**: none
- **takeaway**: Machine-learning models as measuring instruments on NHANES 2021–23 adult diabetes data.
- **notes**: We treat basic machine-learning models as measuring instruments. The question is what they reveal about the data, not how well they score.
- **numbers used**: none
- **footer**: CA6003 Data Governance · Group [N] · NHANES 2021–23
- **claims**: none

### V1.1 · Cohort Funnel
- **type**: figure
- **time**: 25 s (0:10–0:35)
- **figure**: `figures/S3_funnel.png`
- **takeaway**: 11,933 participants reduce to 5,730 analysed adults.
- **notes**: We keep adults who were interviewed, examined, HbA1c-measured and not pregnant. Response was 34.6% for the interview and 25.7% for the examination, so survey weights matter. Public-use files only, plus an availability rule for model features.
- **numbers used**: V1 · adults in DEMO_L = 11,933 | V1 · analytic cohort = 5,730 | V1 · interview response rate = 34.6% | V1 · examination response rate = 25.7%
- **footer**: n = 11,933 → 5,730 · unweighted counts · §2
- **claims**: none

### V1.2 · Label Composition
- **type**: figure
- **time**: 20 s (0:35–0:55)
- **figure**: `figures/S1_label_composition.png`
- **takeaway**: 84% of 971 positives already carry a diagnosis; 152 are undiagnosed.
- **notes**: The label combines self-report and HbA1c, giving 971 positives and a weighted prevalence of 14.0%. Most already know. Only 152 are undiagnosed, and they form the screening population, E-SCREEN, used later.
- **numbers used**: V1 · L_comb positives = 971 | V1 · share of positives already diagnosed = 84% | V1 · E-SCREEN positives = 152 | V1 · weighted prevalence L_comb = 14.0%
- **footer**: n = 971 positives · unweighted · §1
- **claims**: none

### V1.3 · NCHS Replication Check
- **type**: figure
- **time**: 15 s (0:55–1:10)
- **figure**: `figures/S4_db516_forest.png`
- **takeaway**: Survey code reproduces NCHS total prevalence, 15.79 versus 15.8 percent published.
- **notes**: Before modelling, our survey code reproduces the published NCHS figures, 15.79 versus 15.8 percent. Diagnosed 11.30 and undiagnosed 4.49 match too. Our own 14.0% differs only by label definition.
- **numbers used**: V7 · DB516 total reproduced (%) = 15.79 | V7 · DB516 diagnosed reproduced (%) = 11.30 | V7 · DB516 undiagnosed reproduced (%) = 4.49 | V1 · weighted prevalence L_comb = 14.0% | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · weighted (WTPH2YR) · §4
- **claims**: C23

### V1.4 · Experimental Arm Design
- **type**: figure
- **time**: 20 s (1:10–1:30)
- **figure**: `figures/S6_arm_matrix.png`
- **takeaway**: M0 is naive, M1 applies the availability rule, S adds systematic preparation.
- **notes**: Three arms, one model family. M0 is naive and leaky. M1 applies only the availability rule. S adds every systematic preparation step. M0 against M1 measures leakage. M1 against S measures what systematic preparation adds.
- **numbers used**: V1 · analytic cohort = 5,730
- **footer**: design diagram · n = 5,730 · §6
- **claims**: none

### V2.1 · Cost of Naive Cleaning
- **type**: figure
- **time**: 45 s (1:30–2:15)
- **figure**: `figures/S3_blanket_recode_damage.png`
- **takeaway**: Blanket recoding destroys 1,496 valid cells, including 29 HbA1c positives.
- **notes**: Recoding questionnaire sentinel codes to missing looks like routine cleaning. It destroys 1,496 valid cells, including 29 of 721 HbA1c-positive labels. Our union label absorbs most of it, only 6 of 971 positives flip. Cleaning is itself a modelling decision.
- **numbers used**: V2 · valid cells destroyed by blanket recode = 1,496 | V2 · HbA1c positives lost = 29 | V2 · HbA1c positives = 721 | V2 · L_comb label flips = 6 | V1 · L_comb positives = 971 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · unweighted · §2
- **claims**: C03

### V3.1 · Leakage Gate
- **type**: figure
- **time**: 45 s (2:15–3:00)
- **figure**: `figures/S7_leak_gate.png`
- **takeaway**: Removing leakage drops E-ALL AUC from 0.961 to 0.828.
- **notes**: The naive model M0 reaches AUC 0.961 on all adults. Remove treatment and skip-logic items and M1 falls to 0.828, a drop of 0.131, interval minus 0.148 to minus 0.114. That excess was leakage, not insight. Among the undiagnosed the drop is smaller, minus 0.072.
- **numbers used**: V3 · AUC M0 E-ALL = 0.961 | V3 · AUC M1 E-ALL = 0.828 | V3 · leak gate dAUC = -0.131 | V3 · leak gate CI low = -0.148 | V3 · leak gate CI high = -0.114 | V3 · leak gate dAUC E-SCREEN = -0.072 | V1 · analytic cohort = 5,730 | V1 · E-SCREEN positives = 152
- **footer**: n = 5,730 (E-ALL), 152 positives (E-SCREEN) · unweighted · §7
- **claims**: C01

### V3.2 · Median Imputation Artefact
- **type**: figure
- **time**: 30 s (3:00–3:30)
- **figure**: `figures/S7_tree_m0.png`
- **takeaway**: Median imputation turns 86% missing age at diagnosis into a constant 50.
- **notes**: Why does it leak? The naive tree splits on a treatment item, then on age at diagnosis. That item is 86% missing and median-imputed to 50, so the tree separates diagnosed people from imputed rows. On the undiagnosed, tree AUC is 0.633 for M0 against 0.701 for M1.
- **numbers used**: V3 · DID040 missing share = 86% | V3 · DID040 imputed value = 50 | V3 · tree AUC E-SCREEN M0 = 0.633 | V3 · tree AUC E-SCREEN M1 = 0.701 | V1 · analytic cohort = 5,730 | V1 · E-SCREEN positives = 152
- **footer**: n = 5,730 (E-ALL), 152 positives (E-SCREEN) · unweighted · §7
- **claims**: C02

### V4.1 · Redundancy Clusters
- **type**: figure
- **time**: 20 s (3:30–3:50)
- **figure**: `figures/S4_spearman_clustermap.png`
- **takeaway**: Variance inflation factors reach 95.7 for weight and 97.6 for BMI.
- **notes**: Redundancy is structural. Weight and BMI have variance inflation factors of 95.7 and 97.6, and waist and WHtR cluster with them. Collinear blocks need pruning or penalisation before any coefficient is interpreted.
- **numbers used**: V4 · VIF weight = 95.7 | V4 · VIF BMI = 97.6 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · pairwise Spearman, unweighted · §4
- **claims**: none

### V4.2 · Unstable BMI Coefficient
- **type**: figure
- **time**: 20 s (3:50–4:10)
- **figure**: `figures/S7_coef_forest.png`
- **takeaway**: BMI coefficient spread without pruning: 2.87-fold unscaled, 1.36 inside scaled L2.
- **notes**: Redundancy destabilises explanation, not prediction. Without pruning, the bootstrap spread of the BMI coefficient is 2.87 times larger in unscaled models and 1.36 times inside scaled L2. Prediction barely moves.
- **numbers used**: V4 · BMI coefficient SD ratio before/after pruning (unscaled) = 2.87 | V4 · BMI coefficient SD ratio inside scaled L2 = 1.36 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · unweighted, bootstrap refits · §7
- **claims**: none

### V4.3 · Skewness and Outlier Fences
- **type**: figure
- **time**: 20 s (4:10–4:30)
- **figure**: `figures/S4_triglyceride_skew.png`
- **takeaway**: Triglyceride skewness is 6.62 against 1.22 for BMI; a log transform tames it.
- **notes**: Fasting triglycerides have skew 6.62, BMI 1.22. Heavy right tails need a transform, not trimming. A Tukey fence on HbA1c would instead delete diagnostic values.
- **numbers used**: V4 · skew triglycerides (fasting) = 6.62 | V4 · skew BMI = 1.22
- **footer**: fasting subsample · unweighted · §4
- **claims**: none

### V5.1 · Age Standardisation
- **type**: figure
- **time**: 50 s (4:30–5:20)
- **figure**: `figures/S4_crude_vs_std.png`
- **takeaway**: Insurance gap shrinks from +5.3 to +0.7 pp; the Asian–White sign flip stays uncertain.
- **notes**: The crude insurance gap is 5.3 points. After age standardisation it is 0.7. Older adults are more often insured and diabetic, so this is confounding, not a reversal. For Asian versus White, minus 0.8 flips to plus 2.1, but both intervals include zero. We report uncertainty, not a finding.
- **numbers used**: V5 · insurance gap crude (pp) = +5.3 | V5 · insurance gap standardised (pp) = +0.7 | V5 · Asian-White crude (pp) = -0.8 | V5 · Asian-White standardised (pp) = +2.1 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · weighted, jackknife CI · §4
- **claims**: C11, C12

### V5.2 · BMI as Mediator
- **type**: figure
- **time**: 40 s (5:20–6:00)
- **figure**: `figures/S4_dag.png`
- **takeaway**: Consistent with BMI as mediator: 6 Simpson sign flips in 224 comparisons.
- **notes**: Our DAG places BMI between race and diabetes, a mediator, not a confounder. A scan of 224 stratified comparisons finds 6 Simpson sign flips, and most involve mediator stratifiers. Adjusting for a mediator removes part of the effect we want to describe, so we do not.
- **numbers used**: V5 · Simpson sign flips = 6 | V5 · Simpson comparisons = 224 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · weighted · §4
- **claims**: C13

### V6.1 · Treatment Masking
- **type**: figure
- **time**: 30 s (6:00–6:30)
- **figure**: `figures/S5_a1c_by_medication.png`
- **takeaway**: 250 self-reported diabetics (30.5%) have HbA1c below 6.5; treatment masks them.
- **notes**: Among self-reported diabetics, 250, or 30.5%, have HbA1c below 6.5, most of them on medication. An HbA1c-only label calls them negative. Treatment masks disease, so every label is a measurement with its own error.
- **numbers used**: V6 · self-reported with HbA1c < 6.5 = 250 | V6 · treatment masking share = 30.5% | V1 · L_comb positives = 971
- **footer**: n = 971 positives (self-reported subset) · unweighted · §5
- **claims**: C14

### V6.2 · Undiagnosed Risk Difference
- **type**: figure
- **time**: 35 s (6:30–7:05)
- **figure**: `figures/S5_undiagnosed_inequality.png`
- **takeaway**: Uninsured minus insured undiagnosed share: +23.2 pp [6.2, 40.1], exploratory.
- **notes**: Among adults with diabetes, uninsured adults are 23.2 percentage points more often undiagnosed, interval 6.2 to 40.1. The uninsured group is small, so this is exploratory. And 68% of the undiagnosed had a blood test within three years. That is a diagnosis gap, not only access.
- **numbers used**: V6 · undiagnosed RD uninsured - insured (pp) = +23.2 | V6 · undiagnosed RD CI low (pp) = 6.2 | V6 · undiagnosed RD CI high (pp) = 40.1 | V6 · undiagnosed with blood test in 3 years = 68% | V1 · L_comb positives = 971
- **footer**: n = 971 positives · weighted, jackknife CI · §5
- **claims**: C15, C16

### V6.3 · 3×3 Label Matrix
- **type**: figure
- **time**: 35 s (7:05–7:40)
- **figure**: `figures/S8_label_matrix.png`
- **takeaway**: Consistent with undiagnosed cases scoring worst: recall 0.50, 0.56, 0.52 by label.
- **notes**: We train on three labels and score each against three groups. Undiagnosed recall is lowest under every label, 0.50 self-report, 0.56 HbA1c, 0.52 combined, while controlled diabetes reaches 0.57. Changing the label barely helps. These features do not find the undiagnosed.
- **numbers used**: V6 · recall Undiagnosed, trained on L_self = 0.50 | V6 · recall Undiagnosed, trained on L_A1c = 0.56 | V6 · recall Undiagnosed, trained on L_comb = 0.52 | V6 · recall D-controlled, trained on L_A1c = 0.57 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 (training part) · unweighted · §8
- **claims**: C17

### V6.4 · Asian BMI versus WHtR
- **type**: figure
- **time**: 25 s (7:40–8:05)
- **figure**: `figures/S5_asian_bmi_whtr.png`
- **takeaway**: Consistent with BMI under-measuring Asian adiposity: AUC 0.573 against 0.714 for WHtR.
- **notes**: BMI cut-offs under-measure adiposity in Asian adults. 51.1% of Asian diabetics have BMI below 25, against 7.2% of White diabetics. Waist-to-height ratio ranks Asian cases better, AUC 0.714 against 0.573. Small subgroup, exploratory.
- **numbers used**: V6 · Asian AUC BMI = 0.573 | V6 · Asian AUC WHtR = 0.714 | V6 · Asian diabetics with BMI < 25 = 51.1% | V6 · White diabetics with BMI < 25 = 7.2%
- **footer**: NH Asian subsample (exploratory) · prevalence weighted, AUC unweighted · §5
- **claims**: C19

### V6.5 · Group TPR Gap
- **type**: figure
- **time**: 25 s (8:05–8:30)
- **figure**: `figures/S8_group_tpr.png`
- **takeaway**: Suggests a TPR gap for NH Asian adults, -0.184; exploratory.
- **notes**: At the same specificity, the model flags Asian adults with diabetes less often than White adults, a TPR gap of minus 0.184, with few positives. Calibration differs by race too. Observed over expected is 1.30 for Black and 0.88 for White adults.
- **numbers used**: V6 · NH Asian TPR gap (EOD) = -0.184 | V6 · O:E NH Black = 1.30 | V6 · O:E NH White = 0.88 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 (training part) · unweighted · §8
- **claims**: C18, C20

### V7.1 · Algorithm Justification
- **type**: figure
- **time**: 15 s (8:30–8:45)
- **figure**: `figures/S4_binned_logodds.png`
- **takeaway**: Smooth non-linear signal justifies spline logistic regression and shallow trees.
- **notes**: The EDA justifies the algorithms. Log-odds bend, so spline logistic regression, with shallow trees as a transparent probe. Basic models only, no LLMs or complex models.
- **numbers used**: V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · unweighted · §4
- **claims**: none

### V7.2 · Minimal versus Systematic Preparation
- **type**: figure
- **time**: 30 s (8:45–9:15)
- **figure**: `figures/S10_scoreboard_forest.png`
- **takeaway**: Consistent with a small gain, S minus M1 ΔAUC +0.008 [+0.000, +0.016]; inconclusive.
- **notes**: Minimal M1 against systematic S, same model. The AUC gain is plus 0.008, interval 0.000 to 0.016, minimum detectable difference 0.011. Underpowered, so inconclusive. Calibration is a separate verdict. Class weights worsen Brier by 0.076 at unchanged AUC.
- **numbers used**: V7 · S - M1 dAUC = +0.008 | V7 · S - M1 CI low = +0.000 | V7 · S - M1 CI high = +0.016 | V7 · S - M1 MDD = 0.011 | V7 · class weights dBrier = +0.076 | V1 · analytic cohort = 5,730 | V1 · E-SCREEN positives = 152
- **footer**: n = 5,730 (E-ALL), 152 positives (E-SCREEN) · paired CV, unweighted · §7, §10
- **claims**: C05, C06

### V7.3 · Recognition versus Screening
- **type**: figure
- **time**: 35 s (9:15–9:50)
- **figure**: `figures/S10_recognition_vs_screening.png`
- **takeaway**: Whole-sample AUC overstates screening, 0.836 on E-ALL against 0.781 on E-SCREEN (gap +0.055).
- **notes**: Same predictions, two populations. Arm S scores 0.836 on all adults but 0.781 on the undiagnosed, a gap of 0.055. Whole-sample AUC measures recognition. Removing care-trace items lowers E-ALL by 0.016 yet raises E-SCREEN by 0.019. ADA-lite trails S by 0.055.
- **numbers used**: V7 · AUC S E-ALL = 0.836 | V7 · AUC S E-SCREEN = 0.781 | V7 · E-ALL minus E-SCREEN gap = +0.055 | V7 · minus care traces E-ALL = -0.016 | V7 · minus care traces E-SCREEN = +0.019 | V7 · S - ADA-lite E-SCREEN = +0.055 | V1 · analytic cohort = 5,730 | V1 · E-SCREEN positives = 152
- **footer**: n = 5,730 / 152 positives · unweighted · §10
- **claims**: C07, C08, C09

### V7.4 · Hold-Out Confirmation
- **type**: figure
- **time**: 15 s (9:50–10:05)
- **figure**: `figures/S9_holdout_vs_cv.png`
- **takeaway**: Hold-out shows cross-validated AUCs carry over, arm S 0.851 E-ALL, 0.791 E-SCREEN.
- **notes**: One shot, evaluated once. Arm S scores 0.851 on all adults and 0.791 on the undiagnosed, matching cross-validation. The leak gate holds too, M0 0.964 against M1 0.848.
- **numbers used**: V7 · hold-out AUC S E-ALL = 0.851 | V7 · hold-out AUC S E-SCREEN = 0.791 | V7 · hold-out AUC M0 E-ALL = 0.964 | V7 · hold-out AUC M1 E-ALL = 0.848
- **footer**: one-shot hold-out · unweighted · §9
- **claims**: C25

### V7.5 · Robustness Checks
- **type**: figure
- **time**: 10 s (10:05–10:15)
- **figure**: `figures/S9_robustness_summary.png`
- **takeaway**: Sub-verdicts survive seeds, specifications, weighting and missing-data scenarios.
- **notes**: Seeds, specification curves, weights and missing-data scenarios leave verdicts unchanged. Permuted labels give AUC 0.501.
- **numbers used**: V7 · permutation null mean (S) = 0.501 | V1 · analytic cohort = 5,730
- **footer**: n = 5,730 · unweighted · §9
- **claims**: C22

### V8.1 · Conclusions
- **type**: text
- **time**: 25 s (10:15–10:40)
- **figure**: none
- **takeaway**: Leakage inflates AUC · Age confounds gaps · Labels mask cases · AUC measures recognition
- **notes**: Three findings and one headline. Leakage and naive cleaning inflate performance. Age and mediators create fallacies, and labels mask cases. The headline is that whole-sample AUC measures recognition, 0.836 versus 0.781 on the undiagnosed. Of the hypotheses, 10 are supported, 6 inconclusive, 1 mixed, across 25 graded claims.
- **numbers used**: V8 · claims in ledger = 25 | V8 · hypotheses supported = 10 | V8 · hypotheses inconclusive = 6 | V8 · hypotheses mixed = 1 | V7 · AUC S E-ALL = 0.836 | V7 · AUC S E-SCREEN = 0.781
- **footer**: 25 graded claims · weighted where stated · §10
- **claims**: C01-C25

### V8.2 · Limitations and Ethics
- **type**: text
- **time**: 20 s (10:40–11:00)
- **figure**: none
- **takeaway**: Observational US data · 152 screening positives · Subgroups exploratory · Not a clinical tool
- **notes**: Limits are observational US data, not Singapore, and only 152 screening positives, so subgroups are exploratory. Ethics. Public-use data, aggregates only, race used for audit and never as a feature. Not a clinical tool, and fairness is not certified.
- **numbers used**: V1 · E-SCREEN positives = 152
- **footer**: 152 screening positives · aggregates only · §10
- **claims**: none

### V8.3 · Contributions and GenAI
- **type**: template
- **time**: 20 s (11:00–11:20)
- **figure**: none
- **takeaway**: Contribution table and GenAI statement (template, team fills in).
- **notes**: Each member names their role and notebook sections on screen. For GenAI, Claude assisted planning, code drafting and audits under our direction. No LLM sits in the pipeline, and every number was recomputed and checked by us.
- **numbers used**: none
- **footer**: §0 contribution table · GenAI log in governance/genai_log.csv
- **claims**: none

## Cut priority (rehearsal loop L6)

Apply in order only if two consecutive rehearsals exceed 11:40, and stop as soon as the total fits.

| Order | Cut | Saves (s) | Where |
|---|---|---|---|
| 1 | Asian standardisation clause shortened to one sentence | 10 | V5.1 |
| 2 | 68% blood-test annotation | 5 | V6.2 |
| 3 | ADA-lite sentence | 5 | V7.3 |
| 4 | Governance detail (response rates, availability-rule wording, NCHS decomposition) | 10 | V1.1, V1.3 |

Reserve cuts beyond the process document, to be agreed by the team before use: calibration sentence in V6.5 (5 s) and the robustness slide V7.5 folded into V7.4 (10 s).

Never cut: leakage gate (V3.1, V3.2), redundancy and skewness (V4.1 to V4.3), minimal versus systematic (V7.2), label bias (V6.1 to V6.4), contributions (V8.3).

## Deviations from the process document

- Final numbers replace the prototype ones in `development_process.md`: leak gate 0.961 to 0.828 (not 0.96 to 0.86), triglyceride skewness 6.62, BMI coefficient SD ratios 2.87 and 1.36, variance inflation factors 95.7 and 97.6.
- The NCHS Data Brief 516 check sits in V1.3 because `governance/claims.csv` maps claim C23 to the scope segment. It counts as governance detail in the cut order.
- The insurance and Asian fallacies share one figure (`S4_crude_vs_std`, which shows both); the mediator DAG has its own slide.
- The skewness slide uses `S4_triglyceride_skew` (raw against log scale); the HbA1c outlier-fence figure `S3_iqr_fence_harm` is the optional backup visual.
- V7 adds the hold-out confirmation (V7.4) and a robustness slide (V7.5) from S10; the ADA-lite sentence sits in V7.3.
- Text slides (V0, V8.1, V8.2, V8.3) carry no figure.

## Rubric traceability

| Rubric item | Slide |
|---|---|
| RB3 redundancy, collinearity, skewness, fallacies | V4.1 to V4.3, V5.1, V5.2 |
| HR1 non-obvious pattern | V7.3 |
| HR2 minimal against systematic, same model | V7.2 |
| HR3 basic models only | V7.1 |
| HR4 improvements and deteriorations explained | V3.1, V7.2, V7.3 |
| HR5 GenAI declaration | V8.3 |
| HR6 under 12 minutes, all members on camera | recording checklist in README |
