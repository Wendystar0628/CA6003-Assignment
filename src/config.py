"""Project-wide constants and paths (single source of truth for parameters).

Every section and module imports from here; never hard-code paths, seeds or
thresholds elsewhere. Values follow docs/development_process.md §7.1.
"""
from __future__ import annotations

import os
from pathlib import Path


def _find_root() -> Path:
    """Repository root = first parent containing `src/config.py` (works from notebooks/ too)."""
    env = os.environ.get("CA6003_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent
    for cand in [here.parent, *here.parents]:
        if (cand / "src" / "config.py").exists():
            return cand
    return Path.cwd()


ROOT = _find_root()
DATA_DIR = ROOT / "data" / "nhanes_2021_2023"
RAW_DIR = DATA_DIR / "raw"
CODEBOOK_DIR = DATA_DIR / "codebooks"
MANIFEST = DATA_DIR / "MANIFEST.sha256"
INTERIM_DIR = ROOT / "data" / "interim"
CONFIG_DIR = ROOT / "config"
VARIABLE_SPEC = CONFIG_DIR / "variable_spec.csv"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
GOVERNANCE_DIR = ROOT / "governance"

CDC_BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles"
NHANES_FILES = [
    "DEMO_L", "GHB_L", "GLU_L", "BMX_L", "BPXO_L", "TCHOL_L", "HDL_L", "TRIGLY_L",
    "DIQ_L", "BPQ_L", "MCQ_L", "INQ_L", "HIQ_L", "HUQ_L", "SMQ_L", "PAQ_L",
]

# ---- run mode -------------------------------------------------------------
# FAST: quick run for graders (<= ~5 min). FINAL: full protocol, outputs saved in notebook.
NB_MODE = os.environ.get("NB_MODE", "FAST").upper()
assert NB_MODE in {"FAST", "FINAL"}, NB_MODE
IS_FINAL = NB_MODE == "FINAL"

# ---- randomness -------------------------------------------------------------
SEED_MASTER = 20261011
N_ROBUSTNESS_SEEDS = 10

# ---- splitting / CV -----------------------------------------------------------
HOLDOUT_FRAC = 0.20
CV_SPLITS = 5
CV_REPEATS = 5 if IS_FINAL else 2
N_BOOT = 1000 if IS_FINAL else 100
N_BOOT_COEF = 500 if IS_FINAL else 100
N_PERM = 100 if IS_FINAL else 20

# ---- decision thresholds (SESOI) --------------------------------------------
SESOI = {
    "roc_auc": 0.01,
    "pr_auc": 0.02,
    "brier": 0.005,
    "coef_sd_ratio": 2.0,
    "group_tpr_gap": 0.05,
    "group_tpr_gap_substantive": 0.10,
}
VERDICTS = ("supported", "refuted", "equivalent", "inconclusive", "mixed")
SPEC_FIXED = 0.80  # specificity at which recall / TPR are reported

# ---- survey design -------------------------------------------------------------
WEIGHT_INTERVIEW = "WTINT2YR"
WEIGHT_MEC = "WTMEC2YR"
WEIGHT_PHLEB = "WTPH2YR"      # cohort analyses (HbA1c / lipids)
WEIGHT_FASTING = "WTSAF2YR"   # fasting subsample, DB516 replication
STRATA = "SDMVSTRA"
PSU = "SDMVPSU"
NCHS_CI_WIDTH_MAX = 0.30
NCHS_MIN_DF = 8
NCHS_MIN_N = 30

# ---- cohort definition ------------------------------------------------------------
ADULT_MIN_AGE = 20
HBA1C_DIABETES = 6.5
XPT_ZERO_EPS = 1e-10

# ---- models ------------------------------------------------------------------------
LR_MAX_ITER = 5000
TREE_MAX_DEPTH = 3
TREE_MIN_LEAF = 50
SPLINE_KW = dict(n_knots=4, degree=3, knots="quantile", extrapolation="linear", include_bias=False)

# ---- figures -----------------------------------------------------------------------
FIG_DPI = 110
OKABE_ITO = {
    "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
    "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#7F7F7F",
}

for _d in (INTERIM_DIR, RESULTS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)
