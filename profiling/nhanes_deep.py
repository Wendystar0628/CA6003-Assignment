import sys
import os
import numpy as np
import pandas as pd

pd.set_option("display.width", 220)
raw = sys.argv[1]


def load(name, cols=None):
    d = pd.read_sas(os.path.join(raw, f"{name}.xpt"), format="xport")
    d = d.mask(d.abs() < 1e-70, 0.0) if cols is None else d[["SEQN"] + cols].mask(d[["SEQN"] + cols].abs() < 1e-70, 0.0)
    return d


demo = load("DEMO_L", ["RIDSTATR", "RIAGENDR", "RIDAGEYR", "RIDRETH3", "DMDEDUC2", "INDFMPIR", "WTINT2YR",
                       "WTMEC2YR", "SDMVPSU", "SDMVSTRA", "DMDBORN4"])
print("tiny XPT values (5.4e-79) in raw DEMO INDFMPIR:",
      int((pd.read_sas(os.path.join(raw, "DEMO_L.xpt"), format="xport")["INDFMPIR"].between(0, 1e-70, inclusive="right")).sum()))
ghb = load("GHB_L", ["LBXGH", "WTPH2YR"])
diq = load("DIQ_L", ["DIQ010", "DIQ160", "DIQ050", "DIQ070"])
bmx = load("BMX_L", ["BMXWT", "BMXHT", "BMXBMI", "BMXWAIST", "BMXHIP", "BMXARMC"])
bp = load("BPXO_L", ["BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3"])
tc = load("TCHOL_L", ["LBXTC"])
hdl = load("HDL_L", ["LBDHDD"])
tg = load("TRIGLY_L", ["LBXTLG", "LBDLDL"])
glu = load("GLU_L", ["LBXGLU"])
hiq = load("HIQ_L", ["HIQ011"])
huq = load("HUQ_L", ["HUQ030", "HUQ010"])

df = demo
for t in [ghb, diq, bmx, bp, tc, hdl, tg, glu, hiq, huq]:
    df = df.merge(t, on="SEQN", how="left")
RACE = {1: "Mexican Am", 2: "Other Hisp", 3: "NH White", 4: "NH Black", 6: "NH Asian", 7: "Other/Multi"}
df["race"] = df["RIDRETH3"].map(RACE)

print("\n== Coverage funnel")
print("DEMO participants:", len(df))
print("Interview+exam (RIDSTATR=2):", (df["RIDSTATR"] == 2).sum())
print("Has HbA1c:", df["LBXGH"].notna().sum(), "| age>=20 with HbA1c:", (df["LBXGH"].notna() & (df["RIDAGEYR"] >= 20)).sum())
print("Fasting subsample glucose:", df["LBXGLU"].notna().sum())
print("Age top-coded at 80:", (df["RIDAGEYR"] == 80).sum())
print("INDFMPIR missing:", df["INDFMPIR"].isna().sum(), "| ==5 (top-coded):", (df["INDFMPIR"] == 5).sum(), "| ==0:", (df["INDFMPIR"] == 0).sum())

ad = df[(df["RIDAGEYR"] >= 20)].copy()
ex = ad[ad["RIDSTATR"] == 2].copy()
print("\n== Adults 20+:", len(ad), "| examined:", len(ex))
print("HbA1c missing among examined adults by race:")
print(ex.groupby("race")["LBXGH"].apply(lambda s: s.isna().mean()).round(3).to_string())
ex["pir_q"] = pd.cut(ex["INDFMPIR"], [-0.01, 1, 2, 3.5, 5], labels=["<1", "1-2", "2-3.5", "3.5-5"])
print("HbA1c missing by income-poverty ratio band (NaN band = PIR missing):")
print(ex.groupby(ex["pir_q"].astype(str))["LBXGH"].apply(lambda s: s.isna().mean()).round(3).to_string())

# ---- label construction ----
L = ex[ex["LBXGH"].notna() & ex["DIQ010"].isin([1, 2, 3])].copy()
L["self_report_dm"] = (L["DIQ010"] == 1).astype(int)
L["a1c_dm"] = (L["LBXGH"] >= 6.5).astype(int)
print("\n== Self-report diagnosis vs measured HbA1c>=6.5 (adults, examined)")
print(pd.crosstab(L["self_report_dm"], L["a1c_dm"], margins=True).to_string())
diag = L[L["self_report_dm"] == 1]
print("Among self-reported diabetics: share with HbA1c<6.5 =", round((diag["LBXGH"] < 6.5).mean(), 3))
print("  of those, on insulin or pills:",
      round(((diag["LBXGH"] < 6.5) & ((diag["DIQ050"] == 1) | (diag["DIQ070"] == 1))).sum() / (diag["LBXGH"] < 6.5).sum(), 3))
L["undiagnosed"] = ((L["a1c_dm"] == 1) & (L["self_report_dm"] == 0)).astype(int)
high = L[L["a1c_dm"] == 1]
print("\n== Share UNDIAGNOSED among those with HbA1c>=6.5 (unweighted), by group")
print("by race:"); print(high.groupby("race")["undiagnosed"].agg(["count", "mean"]).round(3).to_string())
print("by insurance (HIQ011 1=covered 2=not):"); print(high.groupby("HIQ011")["undiagnosed"].agg(["count", "mean"]).round(3).to_string())
print("by routine place of care (HUQ030 1=yes 2=no 3=>1 place):"); print(high.groupby("HUQ030")["undiagnosed"].agg(["count", "mean"]).round(3).to_string())

# ---- weights ----
print("\n== Sample composition: unweighted vs MEC-weighted share by race (examined adults with HbA1c)")
w = L["WTMEC2YR"]
comp = pd.DataFrame({"unweighted": L["race"].value_counts(normalize=True),
                     "weighted": L.groupby("race")["WTMEC2YR"].sum() / w.sum()})
print(comp.round(3).to_string())


def wmean(g, col, wcol="WTMEC2YR"):
    return np.average(g[col], weights=g[wcol]) if g[wcol].sum() > 0 else np.nan


print("\n== Diabetes prevalence (self-report OR A1c>=6.5): unweighted vs weighted, by race")
L["any_dm"] = ((L["self_report_dm"] == 1) | (L["a1c_dm"] == 1)).astype(int)
prev = pd.DataFrame({
    "n": L.groupby("race").size(),
    "unweighted": L.groupby("race")["any_dm"].mean(),
    "weighted": L.groupby("race").apply(lambda g: wmean(g, "any_dm")),
    "median_age": L.groupby("race")["RIDAGEYR"].median(),
})
print(prev.round(3).to_string())
print("overall unweighted", round(L["any_dm"].mean(), 3), "weighted", round(wmean(L, "any_dm"), 3))

# age-standardised (to overall age distribution, 3 bands)
L["age_band"] = pd.cut(L["RIDAGEYR"], [19, 39, 59, 80], labels=["20-39", "40-59", "60+"])
std_w = L["age_band"].value_counts(normalize=True)
rates = L.pivot_table(index="age_band", columns="race", values="any_dm", aggfunc="mean", observed=False)
print("\n== Age-specific prevalence by race (unweighted)")
print(rates.round(3).to_string())
print("age-standardised:", (rates.mul(std_w, axis=0).sum()).round(3).to_dict())

# ---- BMI x race (Asian BMI measurement bias) ----
L["bmi_cat"] = pd.cut(L["BMXBMI"], [0, 23, 25, 27.5, 30, 100], labels=["<23", "23-25", "25-27.5", "27.5-30", "30+"])
print("\n== Diabetes prevalence by BMI category x race (unweighted)")
print(L.pivot_table(index="bmi_cat", columns="race", values="any_dm", aggfunc="mean", observed=False).round(3).to_string())
dm = L[L["any_dm"] == 1]
print("\nAmong diabetics: median BMI and share with BMI<25 by race")
print(dm.groupby("race")["BMXBMI"].agg(median="median", lt25=lambda s: (s < 25).mean()).round(3).to_string())

# ---- multicollinearity / skew ----
cols = ["BMXWT", "BMXHT", "BMXBMI", "BMXWAIST", "BMXHIP", "BMXARMC", "BPXOSY1", "BPXOSY2", "BPXOSY3",
        "BPXODI1", "LBXTC", "LBDLDL", "LBDHDD", "LBXTLG", "LBXGLU", "LBXGH", "INDFMPIR", "RIDAGEYR"]
X = L[cols]
print("\n== Pearson correlation (selected pairs)")
c = X.corr()
pairs = [("BMXWT", "BMXBMI"), ("BMXWT", "BMXWAIST"), ("BMXBMI", "BMXWAIST"), ("BMXWAIST", "BMXHIP"),
         ("BMXBMI", "BMXARMC"), ("BPXOSY1", "BPXOSY2"), ("BPXOSY2", "BPXOSY3"), ("LBXTC", "LBDLDL"),
         ("LBXGLU", "LBXGH"), ("LBXTLG", "LBDHDD")]
for a, b in pairs:
    print(f"  {a} ~ {b}: {c.loc[a, b]:.3f}  (n={X[[a, b]].dropna().shape[0]})")
print("\n== Skewness")
print(X.skew().round(2).to_string())

# VIF on anthropometrics
from numpy.linalg import inv
A = L[["BMXWT", "BMXHT", "BMXBMI", "BMXWAIST", "BMXHIP", "BMXARMC"]].dropna()
R = np.corrcoef(A.values, rowvar=False)
print("\n== VIF anthropometrics:", dict(zip(A.columns, np.round(np.diag(inv(R)), 1))))

# ---- legit values that equal 'sentinel' numbers ----
print("\n== Legit measurements that collide with sentinel codes (would be wiped by blanket recode)")
for col, vals in [("LBXGLU", [77, 99]), ("BPXODI1", [77, 99]), ("BMXWT", [77, 99]), ("BMXWAIST", [77, 99]), ("LBDLDL", [77, 99])]:
    print(f"  {col}: " + ", ".join(f"{v} -> {int((df[col] == v).sum())}" for v in vals))
print("  DIQ010 in (7,9):", int(df["DIQ010"].isin([7, 9]).sum()), "| DMDEDUC2 in (7,9):", int(df["DMDEDUC2"].isin([7, 9]).sum()))
print("  WTMEC2YR == 0 (interview-only):", int((df["WTMEC2YR"] == 0).sum()))
