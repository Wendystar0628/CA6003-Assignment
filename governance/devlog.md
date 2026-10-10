# Development log

One entry per working session, newest last. Template:

```
## YYYY-MM-DD - <session title> (<stage(s)>)
- Done: <what was completed>
- Commits: <n> (<first hash>..<last hash>)
- Key numbers: <recomputed numbers that matter>
- Open / next: <issues, next steps>
```

## 2026-10-11 - Scope and governance documents (S0, S1)
- Done: setup section (`00_setup.py`: environment table, run mode, seed derivation, raw-data integrity against `MANIFEST.sha256`, repository layout); governance folder (README, GenAI log, devlog, register fragments S0 and S1); scope document `S1_scope.md`; draft `hypotheses.md` (H1a-H4b with `prior_exposure` markers; ownership passes to S6); section `01_scope_governance.py` (research question, availability rule, E-ALL versus E-SCREEN, hypotheses table, ADA-lite mapping, novelty statement, DUA obligations, disclosure controls, minimisation, response rates).
- Key numbers recomputed from the raw files: funnel 11,933 -> 7,809 -> 6,064 -> 5,767 -> 5,730; L_comb 971 (819 already self-reported = 84.3%, 721 by HbA1c); E-SCREEN 152 positives against 4,759 negatives; weighted prevalence 14.0% (WTPH2YR) against 16.9% unweighted.
- Data modules landed during the session: `01_scope_governance.py` now builds the cohort with `nhanes_io.build_cohort()`, uses `labels.add_labels` and `survey.weighted_prop`, cross-checks the S1 availability table against `config/variable_spec.csv` (0 disagreements on 26 shared variables) and renders `results/S2/minimisation_report.csv` (175 raw columns, 78 kept, 97 dropped).
- Commits (scope-gov): 9 (governance README/GenAI log/devlog, setup section, register S0, S1 scope document, hypotheses draft, section 1, register S1, setup re-run, minimisation update).
- Open / next: ownership of `hypotheses.md` has passed to `modeling` (S6); the H1a interval (24.9-61.2 vs KG 24.8-62.7) is reconciled in S5 (DR-S1-13); response rates 34.6 % / 25.7 % are NCHS-published and cannot be recomputed from the files; Bang 2009 AUC (0.79 vs 0.83) still to verify.
