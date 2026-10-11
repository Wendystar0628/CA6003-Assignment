# %% [markdown]
# # §0 Setup
#
# This section checks the foundations every later number depends on, so that a failure shows up here and not as a silent difference at the end.
#
# | Check | Why it exists |
# |---|---|
# | Environment | Library versions change results (solver defaults, spline code). |
# | Run mode | FAST re-runs quickly; FINAL is the protocol behind the stored outputs. |
# | Seeds | One master seed, one named stream per random consumer. |
# | Data integrity | A hash check proves no raw file was edited, truncated or re-encoded. |
# | Layout and freezes | Where every artefact lives, and the order in which results were frozen. |

# %%
import sys, pathlib
_here = pathlib.Path.cwd()
ROOT = next(p for p in [_here, *_here.parents] if (p / "src" / "config.py").exists())
sys.path.insert(0, str(ROOT))
from src import config as C, plots, results_io as R

import hashlib, importlib.metadata as md, platform
import numpy as np
import pandas as pd
from IPython.display import Markdown, display

pd.set_option("display.width", 140, "display.max_colwidth", 90)
print("repository root (relative checks only):", ROOT.name)

# %% [markdown]
# ## Software environment
#
# **Why.** The pinned versions in `requirements.txt` were resolved once; the table compares them with what is actually running. A mismatch is not necessarily an error, but it has to be visible.

# %%
PINNED = {}
for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
    line = line.split("#")[0].strip()
    if "==" in line:
        name, ver = line.split("==")
        PINNED[name.strip().lower()] = ver.strip()

PACKAGES = ["numpy", "pandas", "scipy", "scikit-learn", "statsmodels", "matplotlib",
            "seaborn", "pyarrow", "networkx", "PyYAML", "jupytext", "nbclient"]
rows = []
for pkg in PACKAGES:
    try:
        installed = md.version(pkg)
    except md.PackageNotFoundError:
        installed = "missing"
    pinned = PINNED.get(pkg.lower(), "-")
    rows.append({"package": pkg, "pinned": pinned, "installed": installed,
                 "status": "ok" if pinned in ("-", installed) else "differs"})
env = pd.DataFrame(rows)
display(env)
print(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")

# The estimators and statistics used later must be importable: fail here, not in §7.
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import SplineTransformer
assert "missing" not in set(env["installed"]), env[env["installed"] == "missing"]
n_diff = int((env["status"] == "differs").sum())
print(f"{n_diff} package(s) differ from the pinned version" if n_diff else "all pinned versions match")

# %% [markdown]
# **So what.** Every package that later sections need is importable, and the table above records the exact versions behind the submitted numbers. Differences from the pins (if any) are listed, not hidden.

# %% [markdown]
# ## Run mode and derived sizes
#
# **Why.** Resampling counts dominate run time. `NB_MODE` (environment variable, default `FAST`) switches them together. The base sizes live in `src/config.py`; three sections reduce some of them further in FAST mode to keep a re-run short, and the second table lists those effective sizes exactly as the code uses them (each section also prints its sizes when it starts).

# %%
import os
modes = pd.DataFrame({
    "config setting": ["CV splits x repeats", "bootstrap replicates (N_BOOT)", "coefficient bootstrap (N_BOOT_COEF)",
                       "label permutations (N_PERM)", "robustness seeds (N_ROBUSTNESS_SEEDS)"],
    "FAST": ["5 x 2", 100, 100, 20, 10],
    "FINAL": ["5 x 5", 1000, 500, 100, 10],
    f"active ({C.NB_MODE})": [f"{C.CV_SPLITS} x {C.CV_REPEATS}", C.N_BOOT, C.N_BOOT_COEF, C.N_PERM, C.N_ROBUSTNESS_SEEDS],
})
display(modes)
expected = {"FAST": (2, 100, 100, 20), "FINAL": (5, 1000, 500, 100)}[C.NB_MODE]
assert (C.CV_REPEATS, C.N_BOOT, C.N_BOOT_COEF, C.N_PERM) == expected, "config sizes do not match the documented mode"

# Effective sizes where a section departs from (or adds to) the config values, as coded in that section.
EFFECTIVE = pd.DataFrame([
    ("§7.11", "coefficient bootstrap of the arms", 30, 500, "FAST override of N_BOOT_COEF"),
    ("§7.11.1", "bootstrap per arm and C (penalty check)", 20, 200, "exploratory"),
    ("§8.3", "group-label permutations (EOD null)", 200, 200, "fixed, not mode-dependent"),
    ("§8.7", "coefficient bootstrap (access audit)", 100, 500, "= N_BOOT_COEF"),
    ("§9.2.1", "label permutations (negative control)", 20, 100, "= N_PERM"),
    ("§9.2.2", "coefficient bootstrap (noise feature)", 30, 500, "FAST override of N_BOOT_COEF"),
    ("§9.3", "robustness seeds", 5, 10, "FAST override of N_ROBUSTNESS_SEEDS"),
    ("§9.5", "specification-curve specifications", 30, 60, "FAST uses C in {0.1, 10} only"),
], columns=["where", "resampling step", "FAST", "FINAL", "note"])
display(EFFECTIVE)
N_CPU = os.cpu_count() or 2
print(f"NB_MODE = {C.NB_MODE}; holdout fraction {C.HOLDOUT_FRAC:.0%}; SESOI ROC-AUC {C.SESOI['roc_auc']}")
print(f"logical CPU cores here: {N_CPU}; parallel workers: min(12, cores - 2) = {min(12, max(1, N_CPU - 2))} in §7-§8, "
      f"min(16, cores - 2) = {min(16, max(1, N_CPU - 2))} in §9")

# %% [markdown]
# **So what.** The config sizes agree with `config.py` (asserted). The stored outputs come from a FINAL run; FAST changes only Monte-Carlo precision, and the reference values of Appendix A.5 hold in both modes.
#
# **Runtime.** Measured on the development machine (28 logical cores; 12 workers in §7–§8, 16 in §9): FAST about 5 minutes, FINAL about 25 minutes (24 min 45 s for the stored run), almost all of it in §7 and §9. On a 4–8-core laptop we estimate roughly 10–25 minutes for FAST and 1–3 hours for FINAL (scaled from the worker count, not measured).

# %% [markdown]
# ## Seed derivation
#
# **Why.** One shared seed would couple every random step (an extra bootstrap call would move the folds). Each consumer instead gets `evalkit.derive_seed(SEED_MASTER, *tags)` – a `SeedSequence` of the master seed and `crc32` of its name – so its stream depends only on the master seed and its own name, on every machine.

# %%
from src import evalkit as ek

# Tags exactly as the later sections use them (section, purpose, ...).
TAGS = [("S5", "auc_bootstrap"), ("S6", "random_y"), ("S7", "C0"), ("S7", "H2c-i"), ("S7", "coef", "M1")]
seed_table = pd.DataFrame({
    "consumer tags": [" / ".join(t) for t in TAGS],
    "integer_seed": [ek.derive_seed(C.SEED_MASTER, *t) for t in TAGS],
})
display(seed_table)

# Properties the design relies on.
again = [ek.derive_seed(C.SEED_MASTER, *t) for t in TAGS]
assert again == seed_table["integer_seed"].tolist(), "derivation is not deterministic"
assert seed_table["integer_seed"].nunique() == len(TAGS), "two consumers share a seed"
assert ek.derive_seed(C.SEED_MASTER, "S7", "C0") != ek.derive_seed(C.SEED_MASTER + 1, "S7", "C0"), "master seed has no effect"
assert ek.derive_seed(C.SEED_MASTER, "S7", "a", "b") != ek.derive_seed(C.SEED_MASTER, "S7", "b", "a"), "tag order must matter"
# Ten tags of the same form give ten distinct robustness seeds (illustrative tags; §9 defines its own).
seeds_k = [ek.derive_seed(C.SEED_MASTER, "S9", "seed", k) for k in range(C.N_ROBUSTNESS_SEEDS)]
assert len(set(seeds_k)) == C.N_ROBUSTNESS_SEEDS
print(f"SEED_MASTER = {C.SEED_MASTER}; {len(TAGS)} example consumers, all distinct; "
      f"{C.N_ROBUSTNESS_SEEDS} illustrative robustness seeds, first three {seeds_k[:3]}")

# %% [markdown]
# **So what.** Master seed `20261011`; re-derivation is identical, consumers get distinct seeds, and changing the master seed or tag order changes them (asserted).

# %% [markdown]
# ## Data integrity
#
# **Why.** The 16 NHANES files in `data/nhanes_2021_2023/raw/` are unmodified CDC downloads (downloaded 2026-10-10). `MANIFEST.sha256` stores one SHA-256 per file; a single changed byte (an editor re-save, a line-ending conversion, a truncated download) changes the hash. The check runs twice, independently: with `hashlib` here and through the project loader.

# %%
def read_manifest(path):
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        entries[name.strip().lstrip("*")] = digest.lower()
    return entries

def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()

manifest = read_manifest(C.MANIFEST)
rows = []
for stem in C.NHANES_FILES:
    fname = f"{stem}.xpt"
    p = C.RAW_DIR / fname
    actual = sha256_of(p) if p.exists() else None
    rows.append({
        "file": fname,
        "size_kb": round(p.stat().st_size / 1024, 1) if p.exists() else None,
        "codebook": (C.CODEBOOK_DIR / f"{stem}.htm").exists(),
        "sha256_manifest": manifest.get(fname, "")[:12] + "...",
        "sha256_actual": (actual or "")[:12] + "...",
        "match": actual is not None and actual == manifest.get(fname),
    })
integrity = pd.DataFrame(rows)
display(integrity)

assert set(manifest) == {f"{s}.xpt" for s in C.NHANES_FILES}, "manifest and file list differ"
assert integrity["match"].all(), integrity[~integrity["match"]]
assert integrity["codebook"].all(), "codebook missing for a raw file"
print(f"{int(integrity['match'].sum())}/{len(integrity)} files match MANIFEST.sha256; "
      f"total {integrity['size_kb'].sum() / 1024:.1f} MB; every file has a CDC codebook")

# %%
# Second, independent route through the project loader.
from src import nhanes_io
status = nhanes_io.ensure_raw_data(download=False)
print("nhanes_io.ensure_raw_data(download=False) ->", status if len(str(status)) < 300 else "ok")

# %% [markdown]
# **So what.** All 16 raw files are byte-identical to the manifest and each has its codebook, so every later number traces back to the CDC public-use files of the August 2021 – August 2023 cycle. If this cell fails, nothing downstream should be trusted.

# %% [markdown]
# ## Repository layout and governance files
#
# **Why.** Every artefact has a fixed place; the cell checks that the governance files exist and that the register and GenAI-log headers match `governance/README.md`.

# %%
LAYOUT = pd.DataFrame([
    ("config/", "variable_spec.csv: single source of truth for variables", "S2"),
    ("src/", "importable modules (config, plots, results_io, nhanes_io, survey, labels, prep, evalkit, ...)", "S0-S9"),
    ("notebooks/sections/", "one jupytext percent script per section of the final notebook", "S0-S10"),
    ("notebooks/executed/", "executed section notebooks (tools/run_section.py)", "S0-S10"),
    ("governance/", "register fragments, hypotheses, claims, GenAI log, devlog, scope document", "S0-S10"),
    ("results/", "metrics_<S>.json per section and section tables", "S0-S10"),
    ("figures/", "<S>_<name>.png with captions", "S0-S10"),
    ("data/nhanes_2021_2023/", "raw XPT (read-only), codebooks, MANIFEST.sha256, data notes", "S2"),
    ("tools/", "run_section.py, check_repo.py, build_final.py", "S0, S11"),
], columns=["path", "content", "stage"])
# Paths a self-contained run (single notebook plus src/, config/, governance/, data/) must have;
# the others exist only in the full repository.
SELF_CONTAINED = ["src/", "config/", "governance/", "data/nhanes_2021_2023/"]
LAYOUT["exists"] = [(ROOT / p).exists() for p in LAYOUT["path"]]
LAYOUT["availability"] = np.where(LAYOUT["exists"], "present",
                                  np.where(LAYOUT["path"].isin(SELF_CONTAINED), "MISSING", "repository only"))
display(LAYOUT)
assert LAYOUT.loc[LAYOUT["path"].isin(SELF_CONTAINED), "exists"].all(), LAYOUT[LAYOUT["availability"] == "MISSING"]

REGISTER_COLS = ["dr_id", "stage", "date", "type", "finding", "evidence_ref", "evidence_value", "decision",
                 "alternatives_rejected", "hyp_id", "status", "check_verdict", "check_note", "loop_ref",
                 "change_request", "commit"]
GENAI_COLS = ["date", "tool_version", "purpose", "data_shared", "output_used_in", "human_verification"]

gov = C.GOVERNANCE_DIR
checks = []
for rel, cols in [("register/S0.csv", REGISTER_COLS), ("genai_log.csv", GENAI_COLS)]:
    df = pd.read_csv(gov / rel)
    checks.append({"artefact": f"governance/{rel}", "rows": len(df), "columns_ok": list(df.columns) == cols})
for rel in ["README.md", "devlog.md"]:
    checks.append({"artefact": f"governance/{rel}", "rows": None, "columns_ok": (gov / rel).exists()})
gov_check = pd.DataFrame(checks)
display(gov_check)
assert gov_check["columns_ok"].all(), gov_check
reg0 = pd.read_csv(gov / "register/S0.csv")
assert len(reg0) >= 1 and (pd.read_csv(gov / "genai_log.csv").shape[0] >= 1)
print(f"S0 acceptance: register rows = {len(reg0)}, GenAI log rows = {pd.read_csv(gov / 'genai_log.csv').shape[0]}")

# %% [markdown]
# **So what.** The headers match, so the register fragments merge into Appendix A.1 without manual repair.

# %% [markdown]
# ## Freeze order
#
# **Why.** After a freeze results may only be down-graded, never re-run until they look better; the tags let the history prove that the hypotheses preceded the ablations.

# %%
FREEZES = pd.DataFrame([
    ("scope-freeze", "end of S3", "variable scope and availability rule"),
    ("target-freeze", "end of S5", "label L_comb, populations E-ALL / E-SCREEN, 3x3 strata"),
    ("prereg-lock", "end of S6", "hypotheses.md (SHA-256 + timestamp), before the first ablation commit"),
    ("exp-freeze", "end of S9", "experiments; hold-out evaluated once afterwards"),
    ("content-freeze", "end of S11", "notebook, slides and claims"),
    ("submitted-v1", "S12", "submission"),
], columns=["tag", "when", "what is fixed"])
display(FREEZES)

# %%
payload = {
    "mode": C.NB_MODE,
    "seed_master": C.SEED_MASTER,
    "seed_mechanism": "evalkit.derive_seed: SeedSequence([SEED_MASTER, crc32(tag), ...])",
    "example_seeds": dict(zip(seed_table["consumer tags"], seed_table["integer_seed"])),
    "robustness_seeds": seeds_k,
    "n_raw_files_verified": int(integrity["match"].sum()),
    "raw_total_mb": round(float(integrity["size_kb"].sum() / 1024), 2),
    "n_package_differs": n_diff,
    "python": platform.python_version(),
    "packages": dict(zip(env["package"], env["installed"])),
}
R.save_section("S0", payload)
(ROOT / "results" / "S0").mkdir(exist_ok=True)
env.to_csv(ROOT / "results" / "S0" / "environment.csv", index=False)
print("saved results/metrics_S0.json")
print("S0 OK")
