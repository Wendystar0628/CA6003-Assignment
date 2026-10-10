# %% [markdown]
# # §5 Labels and Bias Audit (Stage S5)
#
# Skeleton – content follows in subsequent commits:
# 1. Three labels and their agreement
# 2. Treatment masking
# 3. Meaning of "undiagnosed"
# 4. Undiagnosed inequality
# 5. Asian BMI measurement bias
# 6. Representation and response
# 7. HbA1c missingness bias
# 8. Decision gate L2 and target freeze

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import numpy as np
import pandas as pd

from src import labels as L

# %% [markdown]
# ## Label logic self-test
# **Why.** The label definitions are imported by every later stage, so they are checked on a
# small synthetic frame whose correct answer is known by construction before touching real data.

# %%
_s = pd.DataFrame({
    "DIQ010": [1, 1, 2, 2, 3, 3, np.nan, 2],
    "LBXGH": [7.0, 6.0, 6.5, 5.0, 6.8, 5.5, 6.6, 5.9],
    "DIQ160": [np.nan, np.nan, 1, 2, np.nan, np.nan, np.nan, 1],
    "DIQ050": [1, 2] + [np.nan] * 6,
    "DIQ070": [2, 1, np.nan, np.nan, 1, np.nan, np.nan, 1],
    "LBXGLU": [np.nan, 130, 90, 127, 100, np.nan, np.nan, 80],
    "WTSAF2YR": [0, 1, 1, 1, 1, 0, 1, 1],
})
_d = L.add_labels(_s)
_sl = L.sensitivity_labels(_d)
assert _d["L_comb"].tolist() == [1, 1, 1, 0, 1, 0, 1, 0]
assert _d["y_escreen"].sum() == 3 and _d["y_escreen"].isna().sum() == 2
assert _sl["SL4"].tolist() == [1, 1, 1, 0, 1, 0, 1, 0]   # pills of borderline/prediabetic rows do not count
assert _sl["SL5"].notna().sum() == 5
print("labels self-test OK")
