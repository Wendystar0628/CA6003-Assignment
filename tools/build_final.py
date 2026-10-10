"""Assemble the self-contained final notebook (Stage S11a).

    .venv/Scripts/python tools/build_final.py                      # build only (no outputs), FAST wording
    .venv/Scripts/python tools/build_final.py --execute            # build + execute in a temp workspace (FAST)
    .venv/Scripts/python tools/build_final.py --execute --mode FINAL
    .venv/Scripts/python tools/build_final.py --out some/dir/x.ipynb --sections 00,01

What it does
  1. Front matter: title, group/members and video placeholders, contribution table template,
     GenAI declaration (rendered from governance/genai_log.csv), reading guide, run-mode and
     runtime note, table of contents (generated from the headings of the assembled notebook).
  2. Setup (section 0.0): recreates src/*.py, config/variable_spec.csv, the governance inputs and the
     few stored artefacts the sections read, in a workspace folder next to the notebook, then makes
     the 16 raw NHANES files available (local copy if found, else download from CDC) and verifies the
     inlined MANIFEST. A reader needs the .ipynb only.
  3. Sections: notebooks/sections/NN_*.py (jupytext percent) in order. The duplicated per-section
     bootstrap cell is dropped (one global bootstrap in Setup; every section starts from a clean
     namespace via new_section()); sub-headings are renumbered N.M under the section's own §N.
  4. Appendix: merged decision register, pre-registration text + SHA-256, hypothesis scoreboard,
     references, build record.
  5. Optional execution with nbclient (NB_MODE FAST|FINAL) in a clean temp directory (never in the
     repository checkout), output scrubbing, runtime per section, validation.

The builder only reads the repository; it writes the notebook (and, when executing, runtime_log.md).
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import jupytext
import nbformat
from nbformat import v4

ROOT = Path(__file__).resolve().parents[1]
SECTIONS_DIR = ROOT / "notebooks" / "sections"
FINAL_DIR = ROOT / "notebooks" / "final"
OUT_NAME = "CA6003_NHANES_Diabetes.ipynb"

# ----------------------------------------------------------------------------- inputs to inline
# Source modules: every src/*.py is inlined (the section scripts import whatever exists).
SRC_FILES = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "src").glob("*.py"))
# Text inputs read by the sections / modules before (or without) being re-created by an earlier section.
TEXT_INPUTS = [
    "requirements.txt",
    "config/variable_spec.csv",
    "data/nhanes_2021_2023/MANIFEST.sha256",
    "governance/README.md",
    "governance/S1_scope.md",
    "governance/datasheet.md",
    "governance/dua_checklist.md",
    "governance/devlog.md",
    "governance/hypotheses.md",       # SHA-256 is checked against the pre-registration lock (S6)
    "governance/label_freeze.md",
    "governance/genai_log.csv",
]
REGISTER_GLOB = "governance/register/S*.csv"
# Stored artefacts that a section reads BEFORE the section that creates it has run, or that cannot be
# recomputed without git history. Everything else under results/ is produced by the notebook itself.
SEED_RESULTS = [
    "results/S2/minimisation_report.csv",    # read in §1 (data minimisation), recomputed in §2
    "results/S2/minimisation_columns.csv",
    "results/S6/prereg_lock.json",           # git-history record of the pre-registration lock (S6 fallback without git)
]
CODEBOOK_DIR = "data/nhanes_2021_2023/codebooks"

BOOTSTRAP_LINES = [
    re.compile(r"^import sys, pathlib\s*$"),
    re.compile(r"^_here = pathlib\.Path\.cwd\(\)\s*$"),
    re.compile(r"^ROOT = next\(p for p in \[_here, \*_here\.parents\] if \(p / \"src\" / \"config\.py\"\)\.exists\(\)\)\s*$"),
    re.compile(r"^sys\.path\.insert\(0, str\(ROOT\)\)\s*$"),
    re.compile(r"^from src import config as C, plots, results_io as R\s*$"),
]
ABS_PATH = re.compile(r"[A-Za-z]:[\\/]+(?:Study|Users|ADMINI~1|AppData|Windows|Program)[\\/]", re.I)
ABS_PATH_ANY = re.compile(r"(?<![\w/])[A-Za-z]:[\\/][^\s\"'<>|)\]]*|(?<![\w.])/(?:Users|home|tmp|var/folders)/[^\s\"'<>|)\]]*")


# ----------------------------------------------------------------------------- small helpers
def read_text(rel: str) -> str:
    """Repository file as LF-normalised text (hash-critical files must not depend on the checkout's EOL)."""
    return (ROOT / rel).read_bytes().decode("utf-8").replace("\r\n", "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def md(src: str, *, tags: list[str] | None = None):
    c = v4.new_markdown_cell(src.strip("\n"))
    if tags:
        c.metadata["tags"] = tags
    return c


def code(src: str, *, tags: list[str] | None = None, hide: bool = False):
    c = v4.new_code_cell(src.strip("\n"))
    meta = c.metadata
    if tags:
        meta["tags"] = tags
    if hide:
        meta["jupyter"] = {"source_hidden": True}
    return c


def md_escape(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def md_table(df_rows: list[list[str]], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(md_escape(x) for x in row) + " |" for row in df_rows]
    return "\n".join(lines)


def raw_literal(text: str) -> str | None:
    """Return a raw triple-quoted literal that evaluates to `text`, or None if that is impossible."""
    if "'''" in text or "\r" in text or text.endswith("\\") or "\x00" in text:
        return None
    lit = "r'''" + text + "'''"
    try:
        if ast.literal_eval(lit) == text:
            return lit
    except SyntaxError:
        return None
    return None


# ----------------------------------------------------------------------------- setup cells
def file_cell(rel: str, text: str):
    """Cell that recreates one repository file inside the workspace."""
    if rel.endswith(".py"):
        # %%writefile keeps the module readable as code; EOL conversion is harmless for Python.
        return code(f"%%writefile {rel}\n{text.rstrip(chr(10))}\n", tags=["setup-file"], hide=True)
    lit = raw_literal(text)
    if lit is None:
        blob = base64.b64encode(text.encode("utf-8")).decode("ascii")
        body = f"write_text({rel!r}, __import__('base64').b64decode({blob!r}).decode('utf-8'))"
    else:
        body = f"write_text({rel!r}, {lit})"
    return code(body, tags=["setup-file"], hide=True)


def codebook_cell() -> tuple[object, int, int]:
    cb = ROOT / CODEBOOK_DIR
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(cb.glob("*.htm")):
            info = zipfile.ZipInfo(p.name, date_time=(2026, 10, 10, 0, 0, 0))   # fixed timestamp: reproducible blob
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    blob = base64.b64encode(buf.getvalue()).decode("ascii")
    sha = hashlib.sha256(buf.getvalue()).hexdigest()
    lines = [blob[i:i + 110] for i in range(0, len(blob), 110)]
    src = (
        "# CDC codebooks (HTML) of the 16 files, compressed; they document variable meaning and coding and are\n"
        "# read by the specification checks. Provenance: CDC/NCHS NHANES 2021-2023 data documentation, saved 2026-10-10.\n"
        f"CODEBOOKS_SHA256 = {sha!r}\n"
        "CODEBOOKS_B64 = (\n" + "\n".join(f'    "{ln}"' for ln in lines) + "\n)\n"
        "import base64, hashlib, io, zipfile\n"
        "_blob = base64.b64decode(CODEBOOKS_B64)\n"
        "assert hashlib.sha256(_blob).hexdigest() == CODEBOOKS_SHA256, 'codebook archive is damaged'\n"
        "with zipfile.ZipFile(io.BytesIO(_blob)) as _z:\n"
        "    _z.extractall('data/nhanes_2021_2023/codebooks')\n"
        "print(len(list(Path('data/nhanes_2021_2023/codebooks').glob('*.htm'))), 'codebooks written to data/nhanes_2021_2023/codebooks')"
    )
    return code(src, tags=["setup-file"], hide=True), len(blob), len(list(cb.glob("*.htm")))


WORKSPACE_MD = """## 0.0 Self-contained workspace
**Why.** This file is the only deliverable, so it has to carry everything the analysis needs: the helper modules, the single variable specification, the governance texts that the sections read and hash-check, and the manifest of the raw data. A reader should be able to run it from an empty folder.

**What.** The next cells (1) create a workspace folder `ca6003_workspace/` next to the notebook (override with the environment variable `CA6003_WORKSPACE`) and make it the working directory, so nothing outside it is touched; (2) write the repository files into it (the file cells are collapsed: they are verbatim copies of `src/*.py`, `config/variable_spec.csv` and the governance inputs); (3) import the project modules; (4) make the 16 NHANES files available: a local copy of `data/nhanes_2021_2023/raw` is used if one exists above the notebook, otherwise the files are downloaded from the CDC site, and every file is verified against the SHA-256 manifest. A hash mismatch is reported as a warning, not hidden."""

WORKSPACE_CODE = '''\
import os, sys, time, pathlib
from pathlib import Path

NB_MODE = os.environ.get("NB_MODE", "FAST").upper()
assert NB_MODE in {"FAST", "FINAL"}, "NB_MODE must be FAST or FINAL"
NB_START = time.time()
START_DIR = Path.cwd()                                   # where the notebook was opened
WORKSPACE = Path(os.environ.get("CA6003_WORKSPACE", "ca6003_workspace"))
if not WORKSPACE.is_absolute():
    WORKSPACE = START_DIR / WORKSPACE
for sub in ("src", "config", "governance/register", "data/nhanes_2021_2023/raw", "data/nhanes_2021_2023/codebooks",
            "results", "figures",
            "notebooks/sections", "tools"):          # placeholders only: section 0 lists them in its layout table
    (WORKSPACE / sub).mkdir(parents=True, exist_ok=True)
os.chdir(WORKSPACE)                                      # all relative paths below are inside the workspace
os.environ["CA6003_ROOT"] = str(WORKSPACE)               # read by src/config.py
os.environ["NB_MODE"] = NB_MODE

def write_text(rel, text):
    """Write a text file with LF line endings and UTF-8 (hash-checked files must be byte-exact)."""
    p = Path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))
    return p

print(f"NB_MODE = {NB_MODE}  ({'full protocol: 5x5 CV, B=1000' if NB_MODE == 'FINAL' else 'fast mode for re-running: 5x2 CV, B=100'})")
print("workspace:", WORKSPACE.name + "/", "- Python", sys.version.split()[0])'''

BOOTSTRAP_CODE = '''\
# Global bootstrap (the only one): make the written modules importable and define the shared handles.
sys.path.insert(0, str(WORKSPACE))
from src import config as C, plots, results_io as R
ROOT = C.ROOT
assert ROOT == WORKSPACE.resolve(), "src.config found a different root"
assert C.NB_MODE == NB_MODE

_KEEP = {"C", "plots", "R", "ROOT", "WORKSPACE", "START_DIR", "NB_MODE", "NB_START", "new_section", "write_text",
         "os", "sys", "pathlib", "Path", "time", "In", "Out", "get_ipython", "exit", "quit", "open"}

def new_section():
    """Start a section from a clean namespace.

    Every section was written to run on its own: it re-loads the cohort and reads upstream results from
    results/. Clearing the namespace between sections makes that true here as well (no hidden state, no name
    clashes across sections) and releases memory."""
    import gc
    import matplotlib.pyplot as plt
    ip = get_ipython()
    for name in list(ip.user_ns):
        if name not in _KEEP and not name.startswith("_") and name not in ip.user_ns_hidden:
            del ip.user_ns[name]
    plt.close("all")
    gc.collect()

print("project modules imported from", C.ROOT.name + "/src;", "mode", C.NB_MODE, "- CV", f"{C.CV_SPLITS}x{C.CV_REPEATS}", "- B", C.N_BOOT)'''

DATA_CODE = '''\
# Raw data: use a local copy if one exists (workspace, the notebook's folder or any parent folder, or the folder named by
# CA6003_DATA_SRC); otherwise download from CDC. Either way every file is verified against MANIFEST.sha256.
import shutil
import pandas as pd
from IPython.display import display
from src import nhanes_io

def find_local_raw():
    cands = []
    if os.environ.get("CA6003_DATA_SRC"):
        cands.append(Path(os.environ["CA6003_DATA_SRC"]))
    cands += [d / "data" / "nhanes_2021_2023" / "raw" for d in (START_DIR, *START_DIR.parents)]
    for d in cands:
        if d.is_dir() and d.resolve() != C.RAW_DIR.resolve() and all((d / f"{n}.xpt").exists() for n in C.NHANES_FILES):
            return d
    return None

missing = [n for n in C.NHANES_FILES if not (C.RAW_DIR / f"{n}.xpt").exists()]
src_dir = find_local_raw() if missing else None
if src_dir is not None:
    for n in missing:
        shutil.copy2(src_dir / f"{n}.xpt", C.RAW_DIR / f"{n}.xpt")
    print(f"copied {len(missing)} files from a local data folder")
elif missing:
    print(f"no local copy: downloading {len(missing)} files from {C.CDC_BASE_URL} (about 13 MB) ...")
status = nhanes_io.ensure_raw_data(download=True)
source = "local copy" if src_dir is not None else ("download from CDC" if status["downloaded"] else "already in workspace")
tbl = pd.DataFrame({"file": [f"{n}.xpt" for n in C.NHANES_FILES],
                    "MiB": [round((C.RAW_DIR / f"{n}.xpt").stat().st_size / 2**20, 2) for n in C.NHANES_FILES],
                    "sha256_ok": [n in status["verified"] for n in C.NHANES_FILES]})
display(tbl.T)
print(f"{len(status['verified'])}/{status['n_files']} files verified against MANIFEST.sha256 ({source});",
      "mismatched:", status["mismatched"] or "none")'''

RESULTS_ARTEFACT_NOTE = """**So what.** The workspace now holds exactly the repository files the analysis depends on, the raw data are present and hash-verified, and every later section starts by calling `new_section()`, which clears the namespace so each section depends only on files (never on hidden variables). Three small stored artefacts (`results/S2/minimisation_*.csv`, `results/S6/prereg_lock.json`) are shipped inside this notebook because a section reads them before the section that regenerates them has run, or because they record git history that a single `.ipynb` cannot reproduce; the pre-registration lock is shown with its commit and timestamp in §6."""


def setup_cells(section_no: int) -> list:
    cells = [md(WORKSPACE_MD), code(WORKSPACE_CODE, tags=["setup"])]
    cells.append(md("**Files written into the workspace** (collapsed; each cell is a verbatim copy of the repository file named in its first line)."))
    for rel in SRC_FILES:
        cells.append(file_cell(rel, read_text(rel)))
    for rel in TEXT_INPUTS:
        cells.append(file_cell(rel, read_text(rel)))
    for p in sorted((ROOT).glob(REGISTER_GLOB), key=lambda p: int(p.stem[1:])):
        cells.append(file_cell(p.relative_to(ROOT).as_posix(), read_text(p.relative_to(ROOT).as_posix())))
    for rel in SEED_RESULTS:
        if (ROOT / rel).exists():
            cells.append(file_cell(rel, read_text(rel)))
    cb_cell, _, _ = codebook_cell()
    cells.append(cb_cell)
    cells.append(code(BOOTSTRAP_CODE, tags=["setup"]))
    cells.append(code(DATA_CODE, tags=["setup"]))
    cells.append(md(RESULTS_ARTEFACT_NOTE))
    return cells


# ----------------------------------------------------------------------------- section handling
def load_section(path: Path):
    nb = jupytext.read(path)
    cells = []
    for c in nb.cells:
        n = v4.new_markdown_cell(c.source) if c.cell_type == "markdown" else v4.new_code_cell(c.source)
        cells.append(n)
    return cells


def strip_bootstrap(cells: list, name: str) -> list:
    out, removed = [], 0
    for c in cells:
        if c.cell_type == "code" and "_here = pathlib.Path.cwd()" in c.source:
            kept = []
            for line in c.source.split("\n"):
                if any(p.match(line) for p in BOOTSTRAP_LINES):
                    removed += 1
                else:
                    kept.append(line)
            c.source = "\n".join(kept).strip("\n")
            if not c.source.strip():
                continue
        out.append(c)
    if removed != len(BOOTSTRAP_LINES):
        print(f"WARN {name}: removed {removed} bootstrap lines (expected {len(BOOTSTRAP_LINES)})")
    return out


HEAD_RE = re.compile(r"^(#{2,3})\s+(.*?)\s*$")
PREFIX_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(?=\S)")
TITLE_RE = re.compile(r"^#\s+§(\d+)\s+(.*)$")


def renumber(cells: list, sec_no: int, name: str, preset_idx: set[int] | None = None) -> None:
    """Renumber '##'/'###' headings to N.M / N.M.k. Explicit local numbers are kept (cross-references such as
    '§6.5' or '§4.10' in the prose stay valid); unnumbered headings continue after the highest number used."""
    seen: set[int] = set(preset_idx or set())
    sub_count: dict[int, int] = {}
    cur_m = None
    for c in cells:
        if c.cell_type != "markdown":
            continue
        lines, fence = c.source.split("\n"), False
        for i, line in enumerate(lines):
            if line.lstrip().startswith("```"):
                fence = not fence
            if fence:
                continue
            m = HEAD_RE.match(line)
            if not m:
                continue
            level, text = len(m.group(1)), m.group(2)
            pm = PREFIX_RE.match(text)
            prefix = pm.group(1) if pm else None
            title = text[pm.end():] if pm else text
            if level == 2:
                if prefix is not None:
                    parts = prefix.split(".")
                    idx = int(parts[-1]) if (len(parts) == 1 or int(parts[0]) == sec_no) else None
                else:
                    idx = None
                if idx is None or idx in seen:
                    idx = (max(seen) + 1) if seen else 1
                seen.add(idx)
                cur_m = idx
                sub_count[cur_m] = 0
                lines[i] = f"## {sec_no}.{idx} {title}"
            else:
                if cur_m is None:
                    cur_m = (max(seen) + 1) if seen else 1
                    seen.add(cur_m)
                    sub_count[cur_m] = 0
                k = None
                if prefix is not None:
                    parts = prefix.split(".")
                    if len(parts) == 2 and int(parts[0]) == cur_m:
                        k = int(parts[1])
                if k is None or k <= sub_count[cur_m]:
                    k = sub_count[cur_m] + 1
                sub_count[cur_m] = k
                lines[i] = f"### {sec_no}.{cur_m}.{k} {title}"
        c.source = "\n".join(lines)


def section_number(cells: list, path: Path) -> tuple[int, str]:
    first = cells[0].source.split("\n")[0]
    m = TITLE_RE.match(first)
    if not m:
        raise SystemExit(f"{path.name}: first cell must start with '# §N Title', got {first!r}")
    return int(m.group(1)), first[2:]


# ----------------------------------------------------------------------------- front matter
def genai_table() -> str:
    import csv
    rows = list(csv.DictReader((ROOT / "governance" / "genai_log.csv").open(encoding="utf-8", newline="")))
    header = ["Date", "Tool (version)", "Purpose", "Data shared", "Output used in", "Human verification"]
    body = [[r["date"], r["tool_version"], r["purpose"], r["data_shared"], r["output_used_in"], r["human_verification"]]
            for r in rows]
    return md_table(body, header)


def front_matter(args, n_sections: int, runtime_marker: str) -> list:
    commit = git("rev-parse", "--short", "HEAD") or "unknown"
    dirty = " (working tree had uncommitted changes)" if git("status", "--porcelain", "--", "src", "notebooks/sections", "governance", "config") else ""
    cells = []
    cells.append(md(
        "# Who Gets Labelled Diabetic? Labels, Features and Preparation Choices in NHANES 2021–2023\n\n"
        "**CA6003 Best Practices in Data Governance, Preparation and Analytics** · NTU MSc AI · group project\n\n"
        "A data-centric study of adult diabetes identification with the public NHANES August 2021 – August 2023 files. "
        "Machine learning is used as *evidence about the data*, not as the goal: only basic interpretable models "
        "(L2 logistic regression with splines, a shallow decision tree) are used, and the question is what data-preparation "
        "decisions change. **There is no LLM or complex model anywhere in the analysis pipeline.**"))
    cells.append(md(
        "## Group and video\n\n"
        "| Item | Entry |\n|---|---|\n"
        "| Group number | **[TODO: group no.]** |\n"
        "| Members | **[TODO: names and student IDs]** |\n"
        "| Video (public YouTube, group number in title) | **[TODO: video link]** |\n"
        "| Notebook file | `" + OUT_NAME + "` (this file is the only code deliverable; it recreates everything it needs) |\n"))
    cells.append(md(
        "## Contribution table\n\n"
        "*Template: the team fills in one row per member (sections owned, role, video segment). "
        "The section list below is the structure of this notebook.*\n\n"
        + md_table([["[TODO]", "[TODO: e.g. data profiling lead]", "[TODO: §2]", "[TODO: 0:00–1:30]"],
                    ["[TODO]", "[TODO]", "[TODO]", "[TODO]"],
                    ["[TODO]", "[TODO]", "[TODO]", "[TODO]"],
                    ["[TODO]", "[TODO]", "[TODO]", "[TODO]"]],
                   ["Member", "Role", "Sections", "Video segment"])))
    cells.append(md(
        "## Generative-AI declaration\n\n"
        "**No LLM or complex model is part of the analysis pipeline.** Generative AI was used as a *development aid* "
        "(planning, drafting code and documentation, cross-auditing). The log below lists every use: tool and version, purpose, "
        "what data was shared, where the output was used and how it was verified. **All numbers reported in this notebook are "
        "recomputed in this notebook** from the raw public-use NHANES files and checked by `assert` statements against the "
        "verified reference values; nothing is copied from a model's output. The log is maintained in `governance/genai_log.csv` "
        "(rendered here verbatim).\n\n" + genai_table()))
    cells.append(md(
        "## Reading guide\n\n"
        "- **Structure.** §0 prepares the workspace and checks the environment; §1–§2 state the question, the governance rules and the data audit; "
        "the later sections follow the data lifecycle (EDA and fallacies, labels and bias, preparation design, experiments, fairness, robustness, synthesis). "
        "The appendix holds the merged decision register, the pre-registration text and the references.\n"
        "- **Every analysis step has three parts:** a *Why* paragraph (the question and the method), the code, and a *So what* paragraph "
        "(the concrete numbers that code printed and what they mean). Each number in the text is produced by a code cell and asserted.\n"
        "- **Numbering.** Headings are `§N` (section) and `N.M` (item). Cross-references such as “§6.5” point to these headings.\n"
        "- **Independent sections.** Each section starts from a clean namespace (`new_section()`), re-loads the cohort and reads upstream results from `results/`, "
        "so it can be re-run on its own after §0.\n"
        "- **Collapsed cells.** The cells in §0.0 that write the helper modules and inputs are collapsed; they are verbatim copies of the project files.\n"
        "- **Decision register.** Decisions are labelled `DR-<stage>-<nn>` in the text and listed in full in Appendix A.1 with evidence and self-check verdicts.\n"
        "- **Verdict vocabulary.** Hypotheses end as *supported*, *refuted*, *equivalent*, *inconclusive* or *mixed*; the margins (SESOI) were fixed in advance."))
    if args.mode == "FINAL" and args.execute:
        mode_text = ("**Stored outputs: FINAL mode** (`NB_MODE=FINAL`: 5×5 repeated cross-validation, 1,000 bootstrap replicates, 500 coefficient "
                     "bootstrap replicates, 100 permutations). Re-running with the default `NB_MODE=FAST` (5×2 CV, B = 100, 20 permutations) "
                     "takes a few minutes and reproduces every figure and table with wider Monte-Carlo error; the asserted reference values hold in both modes.")
    elif args.execute:
        mode_text = ("**Stored outputs: FAST mode** (`NB_MODE=FAST`, the default: 5×2 repeated CV, B = 100, 20 permutations). "
                     "Set the environment variable `NB_MODE=FINAL` before starting Jupyter to run the full protocol (5×5 CV, B = 1,000).")
    else:
        mode_text = ("**This file has no stored outputs.** Run it top to bottom. The default mode is FAST (5×2 repeated CV, B = 100, 20 permutations); "
                     "set `NB_MODE=FINAL` before starting Jupyter for the full protocol (5×5 CV, B = 1,000, 500 coefficient replicates, 100 permutations).")
    cells.append(md(
        "## Run mode and runtime\n\n" + mode_text + "\n\n"
        "The notebook needs Python 3.12 with the packages pinned in the requirements shown in §0.2, and internet access only if the "
        "raw files are not already in a `data/nhanes_2021_2023/raw/` folder above the notebook (then about 13 MB are downloaded from the CDC site and verified by SHA-256). "
        "It creates a `ca6003_workspace/` folder next to the notebook and writes nothing outside it.\n\n"
        + runtime_marker))
    cells.append(md("## Contents\n\n@@TOC@@", tags=["toc"]))
    return cells


RUNTIME_PLACEHOLDER = "*Runtime table: filled in when the notebook is executed by `tools/build_final.py --execute`.*"


def make_toc(cells: list) -> str:
    lines = []
    for c in cells:
        if c.cell_type != "markdown":
            continue
        fence = False
        for line in c.source.split("\n"):
            if line.lstrip().startswith("```"):
                fence = not fence
            if fence:
                continue
            m1 = re.match(r"^#\s+(§\S+|Appendix)\s+(.*)$", line)
            m2 = re.match(r"^##\s+((?:\d+|A)\.\d+)\s+(.*)$", line)
            if m1:
                title = f"{m1.group(1)} {m1.group(2)}"
                lines.append(f"- **[{title}](#{quote(title.replace(' ', '-'), safe='-§–')})**")
            elif m2:
                title = f"{m2.group(1)} {m2.group(2)}"
                lines.append(f"    - [{title}](#{quote(title.replace(' ', '-'), safe='-§–')})")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- appendix
REFERENCES = [
    "Araneta, M. R. G., Kanaya, A. M., Hsu, W. C., et al. (2015). Optimum BMI cut points to screen Asian Americans for type 2 diabetes. *Diabetes Care*, 38(5), 814–820.",
    "Bang, H., Edwards, A. M., Bomback, A. S., et al. (2009). Development and validation of a patient self-assessment score for diabetes risk. *Annals of Internal Medicine*, 151(11), 775–783.",
    "Cicchetti, D. V., & Feinstein, A. R. (1990). High agreement but low kappa: II. Resolving the paradoxes. *Journal of Clinical Epidemiology*, 43(6), 551–558.",
    "Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.",
    "Gebru, T., Morgenstern, J., Vecchione, B., et al. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92. https://arxiv.org/abs/1803.09010",
    "Groenwold, R. H. H., White, I. R., Donders, A. R. T., et al. (2012). Missing covariate data in clinical research: when and when not to use the missing-indicator method for analysis. *CMAJ*, 184(11), 1265–1269.",
    "Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a receiver operating characteristic (ROC) curve. *Radiology*, 143(1), 29–36.",
    "Hardt, M., Price, E., & Srebro, N. (2016). Equality of opportunity in supervised learning. *Advances in Neural Information Processing Systems*, 29.",
    "Kamiran, F., & Calders, T. (2012). Data preprocessing techniques for classification without discrimination. *Knowledge and Information Systems*, 33(1), 1–33.",
    "Klein, R. J., & Schoenborn, C. A. (2001). Age adjustment using the 2000 projected U.S. population. *Healthy People Statistical Notes*, 20. National Center for Health Statistics.",
    "Korn, E. L., & Graubard, B. I. (1998). Confidence intervals for proportions with small expected number of positive counts estimated from survey data. *Survey Methodology*, 24(2), 193–201.",
    "Nadeau, C., & Bengio, Y. (2003). Inference for the generalization error. *Machine Learning*, 52(3), 239–281.",
    "National Center for Health Statistics. NHANES August 2021 – August 2023: data files, codebooks and survey documentation. https://wwwn.cdc.gov/nchs/nhanes/ ; analytic guidance on weighting: https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx",
    "National Center for Health Statistics. Data Brief No. 516, prevalence of diabetes among adults in the United States, August 2021 – August 2023. https://www.cdc.gov/nchs/products/databriefs/db516.htm",
    "National Center for Health Statistics. Data User Agreement. https://www.cdc.gov/nchs/policy/data-user-agreement.html",
    "Ojala, M., & Garriga, G. C. (2010). Permutation tests for studying classifier performance. *Journal of Machine Learning Research*, 11, 1833–1863.",
    "Parker, J. D., Talih, M., Malec, D. J., et al. (2017). National Center for Health Statistics data presentation standards for proportions. *Vital and Health Statistics*, Series 2, No. 175.",
    "Phipson, B., & Smyth, G. K. (2010). Permutation p-values should never be zero: calculating exact p-values when permutations are randomly drawn. *Statistical Applications in Genetics and Molecular Biology*, 9(1), Article 39.",
    "Rao, J. N. K., & Wu, C. F. J. (1988). Resampling inference with complex survey data. *Journal of the American Statistical Association*, 83(401), 231–241.",
    "Rule, A., Birmingham, A., Zuniga, C., et al. (2019). Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks. *PLoS Computational Biology*, 15(7), e1007007.",
    "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLoS ONE*, 10(3), e0118432.",
    "Westreich, D., & Greenland, S. (2013). The Table 2 fallacy: presenting and interpreting confounder and modifier coefficients. *American Journal of Epidemiology*, 177(4), 292–298.",
]

REGISTER_CODE = '''\
new_section()
import pandas as pd
from IPython.display import HTML, display

parts = sorted((C.GOVERNANCE_DIR / "register").glob("S*.csv"), key=lambda p: int(p.stem[1:]))
register = pd.concat([pd.read_csv(p).assign(source=p.name) for p in parts], ignore_index=True)
assert register["dr_id"].is_unique, register[register["dr_id"].duplicated()]
register.drop(columns="source").to_csv(C.GOVERNANCE_DIR / "decision_register.csv", index=False, lineterminator="\\n")

by_stage = (register.groupby("stage", sort=False)
            .agg(decisions=("dr_id", "count"),
                 PASS=("check_verdict", lambda s: int((s == "PASS").sum())),
                 PASS_FIX=("check_verdict", lambda s: int((s == "PASS-FIX").sum())),
                 other=("check_verdict", lambda s: int((~s.isin(["PASS", "PASS-FIX"])).sum()))))
display(by_stage.T)
print(f"{len(register)} decisions from {len(parts)} stage fragments; merged table saved as governance/decision_register.csv")

show = register[["dr_id", "type", "finding", "evidence_value", "decision", "alternatives_rejected", "hyp_id", "check_verdict"]].fillna("")
css = ("<style>.dr td,.dr th{text-align:left;vertical-align:top;font-size:12px;padding:3px 6px;max-width:340px;white-space:normal}"
       ".dr{border-collapse:collapse}.dr tr:nth-child(even){background:rgba(127,127,127,.10)}</style>")
display(HTML(css + show.to_html(index=False, classes="dr", border=0, escape=True)))'''

PREREG_CODE = '''\
import hashlib, re
from IPython.display import Markdown, display

hyp_path = C.GOVERNANCE_DIR / "hypotheses.md"
hyp_bytes = hyp_path.read_bytes()
print("governance/hypotheses.md  SHA-256:", hashlib.sha256(hyp_bytes).hexdigest())
print("file timestamp (UTC) of the copy in this workspace is not evidence; the lock commit and its timestamp are shown in section 6.11.")
display(Markdown(hyp_bytes.decode("utf-8")))'''

SCOREBOARD_CODE = '''\
import pandas as pd
from IPython.display import display

for rel in ("results/S10/scoreboard.csv", "results/S7/scoreboard.csv"):
    p = C.ROOT / rel
    if p.exists():
        sb = pd.read_csv(p)
        print(rel, "-", len(sb), "rows")
        display(sb)
        break
else:
    print("no scoreboard available (run section 7 first)")'''


def appendix_cells(section_files: list[Path], section_sha: dict[str, str]) -> list:
    cells = [md("# Appendix A: Registers, pre-registration and references"),
             md("## A.1 Decision register\n"
                "**Why.** Every decision that shaped the data or the analysis has a row with its evidence, the alternatives that were rejected "
                "and a self-check verdict (a re-computation of the evidence in the notebook). The per-stage fragments `governance/register/S*.csv` "
                "are merged here into one table.", tags=["appendix"]),
             code(REGISTER_CODE),
             md("**So what.** The table shows all decisions in one place; the summary above it counts them per stage and per self-check verdict. "
                "A decision without a PASS or PASS-FIX verdict would be visible as `other` and has to be justified in the text of its section."),
             md("## A.2 Pre-registration text\n"
                "**Why.** The hypotheses, their margins and their falsifiers were written before the ablation results existed. The full text is reproduced here "
                "with its SHA-256 so that the file used in the analysis can be compared with the locked version (the lock record is shown in §6.11)."),
             code(PREREG_CODE),
             md("## A.3 Hypothesis scoreboard\n"
                "**Why.** One table that lists, for each pre-registered hypothesis, its verdict and the evidence used. It is produced by the experiment "
                "section and (when available) updated by the synthesis section."),
             code(SCOREBOARD_CODE),
             md("## A.4 References\n\n" + "\n".join(f"- {r}" for r in REFERENCES))]
    commit = git("rev-parse", "HEAD") or "unknown"
    rows = [[f"notebooks/sections/{p.name}", section_sha[p.name][:16]] for p in section_files]
    rows += [[rel, sha256_text(read_text(rel))[:16]] for rel in SRC_FILES]
    cells.append(md("## A.5 Build record\n\n"
                    f"Assembled by `tools/build_final.py` from repository commit `{commit[:12]}`. "
                    "Inlined files and section scripts (first 16 hex digits of the SHA-256 of the LF-normalised text):\n\n"
                    + md_table(rows, ["file", "sha256 (16)"])))
    return cells


# ----------------------------------------------------------------------------- assembly
def assemble(args) -> tuple[nbformat.NotebookNode, list[Path]]:
    section_files = sorted(SECTIONS_DIR.glob("[0-9][0-9]_*.py"))
    if args.sections:
        wanted = {s.strip() for s in args.sections.split(",")}
        section_files = [p for p in section_files if p.name[:2] in wanted]
    if not section_files:
        raise SystemExit("no section scripts found")
    body, seen_nos, section_sha = [], [], {}
    for i, path in enumerate(section_files):
        cells = strip_bootstrap(load_section(path), path.name)
        no, title = section_number(cells, path)
        if seen_nos and no <= seen_nos[-1]:
            print(f"WARN {path.name}: section number §{no} is not greater than the previous §{seen_nos[-1]}")
        seen_nos.append(no)
        section_sha[path.name] = sha256_text(read_text(path.relative_to(ROOT).as_posix()))
        renumber(cells, no, path.name, preset_idx={0} if i == 0 else None)
        for c in cells:
            c.metadata["tags"] = [f"sec-{no}"] + ([t for t in c.metadata.get("tags", [])])
        if i == 0:
            # title + intro markdown, then the generated setup, then the remaining cells
            k = next((j for j, c in enumerate(cells) if c.cell_type == "code"), len(cells))
            gen = setup_cells(no)
            for c in gen:
                c.metadata["tags"] = [f"sec-{no}"] + c.metadata.get("tags", [])
            body += cells[:k] + gen + cells[k:]
        else:
            start = code("new_section()", tags=[f"sec-{no}", "section-start"])
            body += [cells[0], start] + cells[1:]
    appendix = appendix_cells(section_files, section_sha)
    for c in appendix:
        c.metadata["tags"] = ["appendix"] + [t for t in c.metadata.get("tags", []) if t != "appendix"]
    front = front_matter(args, len(section_files), RUNTIME_PLACEHOLDER)
    cells = front + body + appendix
    toc = make_toc(cells)
    for c in cells:
        if c.cell_type == "markdown" and "@@TOC@@" in c.source:
            c.source = c.source.replace("@@TOC@@", toc)
    nb = v4.new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["title"] = "CA6003 NHANES diabetes - final notebook"
    # deterministic, unique cell ids
    for n, c in enumerate(nb.cells):
        c["id"] = f"c{n:04d}"
    return nb, section_files


# ----------------------------------------------------------------------------- execution
def scrub(text: str) -> tuple[str, int]:
    new, n = ABS_PATH_ANY.subn("<path>", text)
    return new, n


def scrub_outputs(nb) -> int:
    total = 0
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        for o in c.get("outputs", []):
            keys = ["text"] if o.output_type == "stream" else (["traceback", "evalue"] if o.output_type == "error" else [])
            for k in keys:
                v = o.get(k)
                if isinstance(v, list):
                    res = [scrub(x) for x in v]
                    o[k] = [r[0] for r in res]
                    total += sum(r[1] for r in res)
                elif isinstance(v, str):
                    o[k], n = scrub(v)
                    total += n
            data = o.get("data")
            if data:
                for mt in ("text/plain", "text/html", "text/markdown"):
                    if mt in data and isinstance(data[mt], str):
                        data[mt], n = scrub(data[mt])
                        total += n
    return total


def execute(nb, mode: str, workdir: Path, timeout: int, download: bool):
    if sys.platform == "win32":  # zmq/tornado need a selector loop on Windows (same as tools/run_section.py)
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    from nbclient import NotebookClient
    os.environ["NB_MODE"] = mode
    os.environ.pop("CA6003_ROOT", None)
    os.environ["CA6003_WORKSPACE"] = str(workdir / "ca6003_workspace")
    raw = ROOT / "data" / "nhanes_2021_2023" / "raw"
    if download:
        os.environ.pop("CA6003_DATA_SRC", None)
    elif raw.is_dir():
        os.environ["CA6003_DATA_SRC"] = str(raw)
    workdir.mkdir(parents=True, exist_ok=True)
    client = NotebookClient(nb, timeout=timeout, kernel_name="python3", record_timing=True,
                            resources={"metadata": {"path": str(workdir)}})
    t0 = time.time()
    client.execute()
    return time.time() - t0


def section_runtimes(nb) -> dict[str, float]:
    out: dict[str, float] = {}
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        ex = c.metadata.get("execution") or {}
        a, b = ex.get("iopub.execute_input") or ex.get("shell.execute_reply.started"), ex.get("shell.execute_reply")
        if not (a and b):
            continue
        dt = (datetime.fromisoformat(b.replace("Z", "+00:00")) - datetime.fromisoformat(a.replace("Z", "+00:00"))).total_seconds()
        tag = next((t for t in c.metadata.get("tags", []) if t.startswith("sec-") or t == "appendix"), "other")
        key = "Appendix" if tag == "appendix" else ("§" + tag[4:] if tag.startswith("sec-") else tag)
        out[key] = out.get(key, 0.0) + dt
    return out


def finish_runtime_cell(nb, mode: str, runtimes: dict[str, float], total: float) -> str:
    def fmt(s):
        return f"{int(s // 60)} min {s % 60:02.0f} s" if s >= 60 else f"{s:.0f} s"
    rows = [[k, fmt(v)] for k, v in runtimes.items()] + [["**Total (kernel wall time)**", f"**{fmt(total)}**"]]
    table = md_table(rows, ["Section", f"Run time, stored outputs ({mode})"])
    for c in nb.cells:
        if c.cell_type == "markdown" and RUNTIME_PLACEHOLDER in c.source:
            c.source = c.source.replace(RUNTIME_PLACEHOLDER, table + "\n\n*Measured on the machine that produced the stored outputs; "
                                        "cell timings include model fitting and bootstrap loops.*")
    return table


# ----------------------------------------------------------------------------- validation
def validate(nb, path: Path, executed: bool) -> list[str]:
    problems: list[str] = []
    nbformat.validate(nb)
    for i, c in enumerate(nb.cells):
        txt = c.source
        m = ABS_PATH.search(txt)
        if m:
            problems.append(f"cell {i}: absolute path in source near {txt[max(0, m.start() - 20):m.end() + 20]!r}")
    ecs = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
    if executed:
        if ecs != list(range(1, len(ecs) + 1)):
            problems.append("execution_count is not sequential 1..n")
        for i, c in enumerate(nb.cells):
            if c.cell_type != "code":
                continue
            for o in c.get("outputs", []):
                if o.output_type == "error":
                    problems.append(f"cell {i}: error output {o.get('ename')}")
                blob = json.dumps({k: v for k, v in o.items() if k != "data"}, default=str)
                m = ABS_PATH.search(blob)
                if m:
                    problems.append(f"cell {i}: absolute path in output near {blob[max(0, m.start() - 20):m.end() + 20]!r}")
    else:
        if any(e is not None for e in ecs):
            problems.append("unexecuted build has execution counts")
    return problems


def size_report(path: Path, nb) -> str:
    total = path.stat().st_size
    img = 0
    for c in nb.cells:
        for o in c.get("outputs", []) if c.cell_type == "code" else []:
            for mt, v in (o.get("data") or {}).items():
                if mt.startswith("image/"):
                    img += len(v) if isinstance(v, str) else len(json.dumps(v))
    n_code = sum(c.cell_type == "code" for c in nb.cells)
    return (f"size {total / 2**20:.2f} MB (images {img / 2**20:.2f} MB), {len(nb.cells)} cells "
            f"({n_code} code, {len(nb.cells) - n_code} markdown)")


def run_check_repo(path: Path) -> str:
    try:
        rel_ok = path.resolve().is_relative_to(ROOT)
    except Exception:  # noqa: BLE001
        rel_ok = False
    if not rel_ok:
        return "check_repo skipped (output outside the repository)"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_repo.py"), str(path)], cwd=ROOT, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip().replace("\n", " | ")


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(FINAL_DIR / OUT_NAME), help="output notebook path")
    ap.add_argument("--execute", action="store_true", help="execute the notebook (nbclient) and store the outputs")
    ap.add_argument("--mode", default=os.environ.get("NB_MODE", "FAST"), choices=["FAST", "FINAL"])
    ap.add_argument("--sections", default="", help="comma-separated section prefixes to include, e.g. 00,01,02 (development)")
    ap.add_argument("--workdir", default="", help="execution directory (default: a fresh temp directory)")
    ap.add_argument("--keep-workdir", action="store_true")
    ap.add_argument("--download", action="store_true", help="when executing, do not offer the local raw data (tests the CDC download path)")
    ap.add_argument("--timeout", type=int, default=7200, help="per-cell timeout in seconds")
    ap.add_argument("--no-runtime-log", action="store_true")
    args = ap.parse_args()

    out = Path(args.out).resolve()
    t0 = time.time()
    nb, section_files = assemble(args)
    print(f"assembled {len(nb.cells)} cells from {len(section_files)} sections: " + ", ".join(p.name[:2] for p in section_files))
    if "course" in out.parts:
        raise SystemExit("refusing to write into course/")
    executed = False
    if args.execute:
        workdir = Path(args.workdir).resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="ca6003_nb_"))
        if ROOT == workdir or ROOT in workdir.parents:
            raise SystemExit("refusing to execute inside the repository checkout (use a temp directory)")
        print(f"executing in {workdir} (NB_MODE={args.mode}) ...")
        try:
            wall = execute(nb, args.mode, workdir, args.timeout, args.download)
        except Exception as e:  # noqa: BLE001
            failed = out.with_suffix(".failed.ipynb")
            scrub_outputs(nb)
            nbformat.write(nb, failed)
            print(f"FAIL execution: {type(e).__name__}: {str(e)[:3000]}\npartial notebook: {failed}")
            return 1
        executed = True
        n_scr = scrub_outputs(nb)
        runtimes = section_runtimes(nb)
        finish_runtime_cell(nb, args.mode, runtimes, wall)
        for c in nb.cells:
            c.metadata.pop("execution", None)
        nb.metadata["language_info"] = {"name": "python", "version": sys.version.split()[0]}
        print(f"executed in {wall:.0f} s ({args.mode}); scrubbed {n_scr} absolute-path strings from outputs")
        for k, v in runtimes.items():
            print(f"   {k:<10} {v:7.1f} s")
        if not args.keep_workdir and not args.workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        if not args.no_runtime_log and out.parent == FINAL_DIR:
            log = FINAL_DIR / "runtime_log.md"
            head = "# Runtime log\n\nWritten by `tools/build_final.py --execute`. One line per executed build.\n\n| date (UTC) | mode | sections | total (s) | per section (s) |\n|---|---|---|---|---|\n"
            line = (f"| {datetime.now(timezone.utc):%Y-%m-%d %H:%M} | {args.mode} | {len(section_files)} | {wall:.0f} | "
                    + ", ".join(f"{k} {v:.0f}" for k, v in runtimes.items()) + " |\n")
            log.write_text((log.read_text(encoding="utf-8") if log.exists() else head) + line, encoding="utf-8")
    problems = validate(nb, out, executed)
    out.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, out)
    print(f"wrote {out}")
    print(size_report(out, nb))
    print("check_repo:", run_check_repo(out))
    for p in problems:
        print("PROBLEM", p)
    print(f"build {'FAILED' if problems else 'OK'} ({time.time() - t0:.0f} s total)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
