import sys
import glob
import os
import pandas as pd

pd.set_option("display.width", 220)
raw = sys.argv[1]
SENT = [7, 9, 77, 99, 777, 999, 7777, 9999, 77777, 99999, 666, 6666]
for f in sorted(glob.glob(os.path.join(raw, "*.xpt"))):
    d = pd.read_sas(f, format="xport")
    name = os.path.basename(f)
    print(f"\n######## {name}: shape={d.shape}, SEQN unique={d['SEQN'].is_unique}")
    rows = []
    for c in d.columns:
        if c == "SEQN":
            continue
        s = d[c]
        sent = {str(k): int((s == k).sum()) for k in SENT if (s == k).sum() > 0} if s.dtype.kind in "fi" else {}
        rows.append({"col": c, "missing": round(s.isna().mean(), 3), "nunique": s.nunique(),
                     "min": s.min() if s.dtype.kind in "fi" else "", "max": s.max() if s.dtype.kind in "fi" else "",
                     "sentinel_hits": sent})
    print(pd.DataFrame(rows).to_string(index=False))
