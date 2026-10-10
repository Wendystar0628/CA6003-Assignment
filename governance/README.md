# Governance artefacts

This folder holds the audit trail of the project: what was decided, why, with which AI assistance, and in which order. Columns of every table follow `docs/development_process.md` section 7.2. Nothing here contains participant-level data.

| File | Purpose | Owner (stage) | Written by |
|---|---|---|---|
| `S1_scope.md` | Research question, use case, evaluation populations (E-ALL / E-SCREEN), feature-availability rule, ADA-lite mapping, novelty statement, governance obligations | S1 | hand-edited, read by `01_scope_governance.py` |
| `hypotheses.md` | Hypotheses H1a-H4b with metric, direction, magnitude, SESOI, falsifier, `prior_exposure`, weights. Locked (SHA-256 + tag `prereg-lock`) in S6 | S1 draft, S6 lock | hand-edited |
| `register/<S>.csv` | Decision-register fragments, one per stage (`dr_id, stage, date, type, finding, evidence_ref, evidence_value, decision, alternatives_rejected, hyp_id, status, check_verdict, check_note, loop_ref, change_request, commit`). `tools/build_final.py` merges them into `decision_register.csv` | each stage | stage owner |
| `decision_register.csv` | Merged register (generated in S11, do not edit by hand) | S11 | `tools/build_final.py` |
| `claims.csv` | Final claims with evidence grade, robustness and falsifier | S10 | synthesis |
| `genai_log.csv` | GenAI declaration (HR5): tool and version, purpose, data shared, where the output is used, how a human verified it | all | append-only |
| `devlog.md` | One entry per working session: what was done, commits, next steps | all | append-only |

## Conventions

- **Register verdicts** use `check_verdict` in `PASS`, `PASS-FIX`, `FAIL`; a check means re-computing a number, never only re-reading it.
- **`prior_exposure`** in `hypotheses.md`: `analysis_seen` (the data were analysed before the hypothesis was written), `descriptive_seen` (a descriptive pattern was seen), `none` (genuine pre-registration, only S7/S8 experiments).
- **After a freeze** (tags `scope-freeze`, `target-freeze`, `prereg-lock`, `exp-freeze`, `content-freeze`) only `fix` commits are allowed and each needs a `change_request` row.
- **GenAI log**: never list participant-level data as shared. Append a row when a new tool, model or purpose enters the project.
- **Dates** are ISO 8601; free text is English.
