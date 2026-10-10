# Weights map (S4)

| component | weight | subsample | used here for | positive in cohort |
|---|---|---|---|---|
| Interview (questionnaires: DIQ, BPQ, HIQ, HUQ, SMQ, PAQ, INQ) | WTINT2YR | all interviewed | interview-only descriptives | 5730 |
| MEC examination (BMX, BPXO) | WTMEC2YR | examined | exam-only descriptives | 5730 |
| Phlebotomy analytes (GHB = HbA1c, TCHOL, HDL) | WTPH2YR | examined + blood drawn | **cohort analyses (contain HbA1c)** | 5730 |
| Fasting analytes (GLU, TRIGLY/LDL) | WTSAF2YR | morning fasting subsample, 8–24 h fast | **DB516 replication, triglycerides, LDL** | 2938 |

Rule: when variables from several components are combined, use the weight of the smallest subsample involved (fasting < phlebotomy < MEC < interview).

Design: 15 strata x 2 PSUs = 30 PSUs; design df = 15. Variance: delete-one-PSU jackknife (JKn); domains by zeroing weights; domain df = (PSUs containing the domain) - (strata containing the domain) (NCHS rule); df < 8 flagged for review (NCHS).
