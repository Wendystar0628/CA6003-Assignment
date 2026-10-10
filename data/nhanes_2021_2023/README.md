# NHANES August 2021 – August 2023 (public-use files, suffix `_L`)

## Provenance
- Source: CDC / NCHS, https://wwwn.cdc.gov/nchs/nhanes/ – files from `.../Public/2021/DataFiles/`
- Use governed by the NCHS Data User Agreement (statistical use only, no re-identification)
- Downloaded: 2026-10-10
- `raw/` (not in git – run `python scripts/download_nhanes.py`; integrity checked against `MANIFEST.sha256`): 16 SAS XPT files – DEMO, GHB (HbA1c), GLU (fasting glucose), BMX (body measures), BPXO (blood pressure),
  TCHOL, HDL, TRIGLY (triglycerides/LDL), DIQ (diabetes questionnaire), BPQ, MCQ, INQ (income), HIQ (insurance),
  HUQ (healthcare access), SMQ (smoking), PAQ (physical activity). Join key: `SEQN`
- `codebooks/`: matching CDC codebooks (.htm) – check value codes here before recoding

## Profiling results (see `../../profiling/`)

> Note: numbers below are the first profiling pass. Several were corrected by the cross-audit; `docs/development_process.md` §8 is authoritative (e.g. Asian vs White standardised difference is NOT significant; blanket-recode damage = 1,496 cells in the cohort).
| Area | Finding |
|---|---|
| Coverage funnel | 11,933 participants -> 8,860 examined -> 6,715 with HbA1c (5,767 adults 20+); fasting glucose only in a 3,672 subsample |
| Label integrity | Self-report (DIQ010) vs measured HbA1c>=6.5 disagree: 152 undiagnosed; 30.5% of self-reported diabetics have HbA1c<6.5 (66% of them on insulin/pills, i.e. treatment masks the measurement) |
| Label bias (access to care) | Share undiagnosed among HbA1c>=6.5: uninsured 36.7% vs insured 19.9%; no routine place of care 41.5% vs 19.9% |
| Confounding by age | Diabetes prevalence crude: NH Asian 15.9% vs NH White 14.5%; age-standardised: 18.0% vs 13.6% (median age 51 vs 60) |
| BMI measurement bias | Among diabetics, 48% of NH Asian have BMI<25 vs 7% of NH White (median BMI 24.9 vs 32.7); prevalence at BMI 23-25: Asian 19.0% vs White 4.2% |
| Survey weights | Unweighted adult prevalence 16.8% vs MEC-weighted 13.8%; 3,073 interview-only rows have exam weight 0 |
| Sentinel collisions | Codes 7/9/77/99/777/999 vary by variable; blanket recoding would wipe valid data (131 fasting glucose = 99 mg/dL, 235 diastolic BP = 77) |
| File-format artifact | Zeros in XPT are read by pandas as 5.4e-79 (e.g. 100 rows of INDFMPIR) – must be cleaned |
| Top-coding | Age top-coded at 80 (525); income-to-poverty ratio top-coded at 5 (2,149), missing for 2,041 |
| MNAR | HbA1c missing among examined adults: NH Black 9.3% vs NH White 4.0%; PIR<1 7.7% vs PIR 3.5-5 2.8% |
| Multicollinearity | VIF: weight 95.9, BMI 97.9, height 21.6 (BMI = wt/ht^2); SBP readings r = 0.94; total chol ~ LDL r = 0.94 (LDL derived from TC) |
| Leakage risk | Fasting glucose ~ HbA1c r = 0.81 (both are diagnostic criteria); insulin/pill questions only asked of diagnosed people |
| Skewness | triglycerides 6.2, fasting glucose 4.5, HbA1c 3.7 |
