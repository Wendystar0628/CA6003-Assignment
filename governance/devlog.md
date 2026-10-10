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
- Open / next: switch the data-dependent cells to `nhanes_io` / `labels` / `config/variable_spec.csv` once those modules are announced; ownership of `hypotheses.md` passes to `modeling` (S6) before the pre-registration lock.
