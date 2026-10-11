"""Assemble the self-contained final notebook (Stage S11a).

    .venv/Scripts/python tools/build_final.py                      # build only (no outputs), FAST wording
    .venv/Scripts/python tools/build_final.py --execute            # build + execute in a temp workspace (FAST)
    .venv/Scripts/python tools/build_final.py --execute --mode FINAL
    .venv/Scripts/python tools/build_final.py --out some/dir/x.ipynb --sections 00,01
    .venv/Scripts/python tools/build_final.py --validate-only NOTEBOOK   # checks + remaining [TEAM TO FILL] entries
    .venv/Scripts/python tools/build_final.py --fill-team NOTEBOOK       # team cells from notebooks/final/team.json
    .venv/Scripts/python tools/build_final.py --assemble --from-executed 06,07   # incremental FINAL release (see README)

What it does
  1. Front matter: title (shared with the video), executive Summary (numbers read from
     results/final_metrics.json and re-asserted in A.5), brief-requirement checklist with § links,
     group / members / video and contribution table ([TEAM TO FILL] entries from team.json), short
     GenAI declaration, reading guide with the marker's path, run mode and runtime, contents.
     § links are written as @@H:<n>/<title prefix>@@ and resolved against the assembled headings.
  2. Setup (section 0.0): recreates src/*.py, config/variable_spec.csv, the governance inputs and the
     few stored artefacts the sections read, in a workspace folder next to the notebook, then makes
     the 16 raw NHANES files available (local copy if found, else download from CDC) and verifies the
     inlined MANIFEST. A reader needs the .ipynb only.
  3. Sections: notebooks/sections/NN_*.py (jupytext percent) in order. The duplicated per-section
     bootstrap cell is dropped (one global bootstrap in Setup; every section starts from a clean
     namespace via new_section()); sub-headings are renumbered N.M under the section's own §N; a
     "(Stage Sk)" suffix is dropped from the § heading and a "Section lead" line is added under it.
  4. Appendix: A.1 merged decision register, A.2 locked pre-registration text + SHA-256 + glossary,
     A.3 pointer to the §10 scoreboard, A.4 references (only those cited; citations are checked both
     ways), A.5 FINAL_REF check, A.6 build record, A.7 GenAI use log.
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
import tokenize
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
# Stored artefacts that cannot be recomputed from a single notebook (git history), or that a section reads before
# the section that creates it has run. Everything else under results/ is produced by the notebook itself.
SEED_RESULTS = [
    "results/S6/prereg_lock.json",           # git-history record of the pre-registration lock (S6 fallback without git)
    "results/S9/exp_freeze_record.json",     # git-history record of the exp-freeze tag (S9 hold-out gate without git)
    "results/S9/holdout_log.json",           # the one-shot hold-out run (done once, after exp-freeze): log ...
    "results/S9/holdout_metrics.csv",        # ... per-arm metrics ...
    "results/S9/holdout_pairs.csv",          # ... and paired differences; FAST displays them, FINAL must reproduce them
]

# Section files that hold two stages: the part from the heading `at` onwards becomes its own section `§no title`
# (same namespace: no new_section() between the parts, the code is unchanged). `head_title` retitles the first part;
# `head_map` renames headings of the first part (so its single item is N.1, not N.0).
SPLITS = {
    "02_profiling.py": dict(at="## 1 XPT read artefact", no=3, title="Data profiling and quality audit",
                            head_title="Data provenance, specification and minimisation",
                            head_map={"## 0 Provenance, specification and minimisation (Stage S2 checks)":
                                      "## 1 Provenance, specification and minimisation"},
                            intro=("This section continues §2 in the same workspace state (the helper functions and result "
                                   "dictionaries defined there are reused; no `new_section()` in between). It holds the nine audit "
                                   "items listed at the start of §2 (§3.1–§3.9) and the decision register of §2 and §3.")),
}
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


def source_commit() -> str:
    """Commit the notebook is built from: the checkout's HEAD, or CA6003_SOURCE_COMMIT for a `git archive` export
    (which has no .git); 'unknown' otherwise."""
    return os.environ.get("CA6003_SOURCE_COMMIT") or git("rev-parse", "HEAD") or "unknown"


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
            "results", "figures"):
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

RESULTS_ARTEFACT_NOTE = """**So what.** The workspace now holds exactly the repository files the analysis depends on, the raw data are present and hash-verified, and every later section starts by calling `new_section()`, which clears the namespace so each section depends only on files (never on hidden variables). A few small stored artefacts are shipped inside this notebook because they record events that a single `.ipynb` cannot reproduce: the git history of the pre-registration lock (`results/S6/prereg_lock.json`, shown with its commit and timestamp in §6.11) and of the experiment freeze (`results/S9/exp_freeze_record.json`), and the one-shot hold-out evaluation that was run once after that freeze (`results/S9/holdout_log.json`, `holdout_metrics.csv`, `holdout_pairs.csv`). §9.11 re-executes that evaluation in FINAL mode and asserts that it reproduces the logged numbers; in FAST mode it displays them without refitting."""


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


def split_section(cells: list, no: int, cfg: dict, name: str) -> list[tuple[int, list, bool]]:
    """Split one section file into two consecutive sections at the markdown heading cfg['at'] (see SPLITS)."""
    k = next((j for j, c in enumerate(cells) if c.cell_type == "markdown"
              and any(line.strip().startswith(cfg["at"]) for line in c.source.split("\n"))), None)
    if k is None:
        raise SystemExit(f"{name}: split heading {cfg['at']!r} not found")
    if cfg["no"] != no + 1:
        raise SystemExit(f"{name}: split section must be §{no + 1}, got §{cfg['no']}")
    head, tail = cells[:k], cells[k:]
    lines = head[0].source.split("\n")
    lines[0] = f"# §{no} {cfg['head_title']}"
    head[0].source = "\n".join(lines)
    for c in head:
        if c.cell_type == "markdown":
            for old, new in cfg.get("head_map", {}).items():
                c.source = c.source.replace(old, new)
    title = v4.new_markdown_cell(f"# §{cfg['no']} {cfg['title']}\n\n{cfg['intro']}")
    return [(no, head, True), (cfg["no"], [title] + tail, False)]


def section_number(cells: list, path: Path) -> tuple[int, str]:
    first = cells[0].source.split("\n")[0]
    m = TITLE_RE.match(first)
    if not m:
        raise SystemExit(f"{path.name}: first cell must start with '# §N Title', got {first!r}")
    return int(m.group(1)), first[2:]


# ----------------------------------------------------------------------------- front matter
# One title for the notebook and the video.
TITLE = "Who Gets Labelled Diabetic? Basic Models as Instruments on NHANES 2021–2023"

# Team entries. Everything the team still has to complete carries the marker FILL; `--validate-only` lists what is left.
# The entries live in notebooks/final/team.json (optional; defaults below). `--fill-team NOTEBOOK` re-renders only the
# team cells and the "Section lead" lines of an existing (executed) notebook from that file; code cells stay untouched.
FILL = "[TEAM TO FILL]"
FILL_RE = re.compile(r"\[TEAM TO FILL[^\]]*\]")
TEAM_FILE = FINAL_DIR / "team.json"
N_MEMBERS = 4
SECTION_NOS = list(range(0, 11))
MEMBER_FIELDS = {
    "name": "[TEAM TO FILL: name]",
    "matric": "[TEAM TO FILL: matric no.]",
    "role": "[TEAM TO FILL: role]",
    "sections_led": "[TEAM TO FILL: § list]",
    "decisions": "[TEAM TO FILL: DR ids]",
    "video_segment": "[TEAM TO FILL: mm:ss–mm:ss]",
}
LEAD_LINE = "**Section lead:** "
LEAD_RE = re.compile(r"^\*\*Section lead:\*\* .*$", re.M)


def load_team() -> dict:
    team = {"group_number": "[TEAM TO FILL: group no.]", "video_url": "[TEAM TO FILL: public YouTube link]",
            "members": [dict(MEMBER_FIELDS) for _ in range(N_MEMBERS)],
            "section_leads": {str(n): "[TEAM TO FILL: member name]" for n in SECTION_NOS}}
    if TEAM_FILE.exists():
        user = json.loads(TEAM_FILE.read_text(encoding="utf-8"))
        for k in ("group_number", "video_url"):
            if str(user.get(k, "")).strip():
                team[k] = str(user[k]).strip()
        if user.get("members"):
            team["members"] = [{f: (str(m.get(f, "")).strip() or d) for f, d in MEMBER_FIELDS.items()} for m in user["members"]]
        for n, v in (user.get("section_leads") or {}).items():
            if str(v).strip():
                team["section_leads"][str(n)] = str(v).strip()
        team["collaboration"] = [str(x).strip() for x in user.get("collaboration") or [] if str(x).strip()]
        team["genai_workflow"] = [str(x).strip() for x in user.get("genai_workflow") or [] if str(x).strip()]
    return team


def em(x: str) -> str:
    """Bold a placeholder so it cannot be missed."""
    return FILL_RE.sub(lambda m: f"**{m.group(0)}**", md_escape(x))


def team_table(rows: list[list[str]], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(em(x) for x in row) + " |" for row in rows]
    return "\n".join(lines)


def title_md(team: dict, run: str) -> str:
    facts = [["Group", team["group_number"]],
             ["Members", ", ".join(m["name"] for m in team["members"]) + " (roles under *Team and contributions*)"],
             ["Video (public YouTube)", team["video_url"]],
             ["Data", "NHANES August 2021 – August 2023 public-use files (CDC/NCHS), 16 files, verified by SHA-256"],
             ["Models", "L2 logistic regression with splines; depth-3 decision tree; no LLM or complex model in the pipeline"],
             ["Outputs", run]]
    return (f"# {TITLE}\n\n"
            "**CA6003 Best Practices in Data Governance, Preparation and Analytics** · NTU MSc AI · group project\n\n"
            "A data-centric study of adult diabetes identification. Machine learning is used as *evidence about the data*, "
            "not as the goal: basic interpretable models measure what data-preparation and labelling decisions change.\n\n"
            + team_table(facts, ["Item", "Entry"]))


def team_md(team: dict) -> str:
    open_items = bool(FILL_RE.search(json.dumps(team, ensure_ascii=False)))
    note = ("> **To the team:** complete every **[TEAM TO FILL: …]** entry before submission: edit "
            "`notebooks/final/team.json`, run `tools/build_final.py --fill-team <notebook>` (only markdown changes), "
            "then `--validate-only <notebook>` to list what is left.\n\n") if open_items else ""
    return ("## Team and contributions\n\n" + note
            + team_table([[m["name"], m["matric"], m["role"], m["sections_led"], m["video_segment"]] for m in team["members"]],
                         ["Member", "Matric no.", "Role", "Leads (reviews)", "Video"])
            + "\n\n" + team_table([[m["name"], m["decisions"]] for m in team["members"]],
                                    ["Member", "Decisions (register, Appendix A.1)"])
            + ("\n\n**How the work was shared.**\n\n" + "\n".join(f"- {x}" for x in team["collaboration"])
               if team.get("collaboration") else ""))


def genai_md(team: dict) -> str:
    workflow = ("\n\n" + " ".join(team["genai_workflow"])) if team.get("genai_workflow") else ""
    return ("## Generative-AI declaration\n\n"
            "No LLM or other complex model is part of the analysis pipeline; generative AI was a development aid only.\n\n"
            + md_table([["Claude (Anthropic): Opus and Sonnet models, chat and command line",
                         "Drafting the analysis design, code and text; reviewing statistics and consistency",
                         "Every number is recomputed from the raw NHANES files by the code in this notebook and asserted; "
                         "independent re-implementation audits of key results; external replication of NCHS Data Brief 516 "
                         "(@@H:4/External anchor@@, @@H:9/External validity@@); full change history in git"],
                        ["Codex (OpenAI), 12 October 2026",
                         "Revising the team records; 28 automated evidence checks",
                         "Each check compares a raw-data recomputation or a stored result with its source "
                         "(`governance/team_verification.json`)"]],
                       ["Tool", "Purpose", "How verified"])
            + workflow
            + "\n\nNo participant-level record was entered into any prompt."
            + "\n\nDated log with tool versions and the data shared: @@A:A.7 Generative-AI use log~Appendix A.7@@.")


# Executive summary: every number is read from the stored FINAL results (results/final_metrics.json) at build time and
# re-asserted against the executed notebook in Appendix A.5 (the same paths are in REF_SPECS).
SUMMARY_MAX_WORDS = 250


def summary_md() -> tuple[str, int]:
    fm = json.loads((ROOT / "results" / "final_metrics.json").read_text(encoding="utf-8"))

    def g(sec: str, path: str):
        return dig_path(fm[sec], path)

    def n(sec, path):                      # count
        return f"{int(round(float(g(sec, path)))):,}"

    def a(sec, path, signed=False):        # AUC-scale number
        v = float(g(sec, path))
        return f"{v:+.3f}".replace("-", "−") if signed else f"{v:.3f}"

    def ci(sec, base, lo="lo", hi="hi"):
        return f"[{a(sec, base + '.' + lo, True)}, {a(sec, base + '.' + hi, True)}]"

    def pct(sec, path, d=1):
        return f"{100 * float(g(sec, path)):.{d}f}"

    def v(sec, path):
        return str(g(sec, path))

    ho = "holdout.metrics[arm=S&tier=1&pop={}].roc_auc"
    pp = "h2b.pure_preparation[pop=E-ALL&metric={}].diff"
    rd = "undiagnosed_inequality.risk_differences_pp.uninsured - insured"
    text = (
        "## Summary\n\n"
        "**Question.** What do data-preparation decisions change in a basic, interpretable diabetes model, "
        "and does a high AUC mean it finds *undiagnosed* cases?\n\n"
        f"**Cohort.** NHANES 2021–2023: {n('S1', 'n_cohort')} examined, non-pregnant adults aged 20+ with HbA1c; "
        f"{n('S1', 'labels.L_comb')} positive by self-report or HbA1c ≥ 6.5 % (weighted {pct('S1', 'prevalence_comb.weighted')} %, "
        f"95 % CI {pct('S1', 'prevalence_comb.ci_low')}–{pct('S1', 'prevalence_comb.ci_high')}), {n('S1', 'e_screen.positives')} of them undiagnosed.\n\n"
        f"1. **Recognition, not screening.** Prepared model: AUC {a('S7', 'headline.auc_S_eall_T1')} on all adults, "
        f"{a('S7', 'headline.auc_S_escreen_T1')} on adults without a diagnosis (gap {a('S7', 'headline.eall_minus_escreen_S_T1.est', True)} "
        f"{ci('S7', 'headline.eall_minus_escreen_S_T1')}). Without care-contact items the first falls "
        f"({a('S7', 'headline.minus_care_eall.est', True)}), the second rises ({a('S7', 'headline.minus_care_escreen.est', True)}); "
        f"recall {float(g('S8', 'gap_decomposition.tpr_diagnosed')):.2f} (diagnosed) vs "
        f"{float(g('S8', 'gap_decomposition.tpr_undiagnosed')):.2f} (undiagnosed).\n"
        f"2. **Leakage and naive cleaning.** Inadmissible items (treatment, diagnosis history, glucose testing) lift AUC from "
        f"{a('S7', 'headline.auc_M1_eall_T1')} to {a('S7', 'headline.auc_M0_eall_T1')}; a depth-3 tree splits on age at diagnosis, median-imputed to "
        f"{float(g('S7', 'tree_m0.did040_fill')):.0f} for the {pct('S7', 'tree_m0.did040_missing_share', 0)} % never asked. "
        f"*Non-obvious profiling finding:* a blanket “7/9 = missing” recode deletes {n('S3', 'blanket_recode.valid_cells_destroyed_cohort')} "
        f"valid cells, including HbA1c 7.0 % and 9.0 %, losing {n('S3', 'blanket_recode.a1c_positives_lost')} of "
        f"{n('S3', 'blanket_recode.a1c_positives')} HbA1c-positive adults.\n"
        f"3. **Label and measurement bias.** {n('S5', 'masking.below_6_5')} of {n('S5', 'masking.self_reported')} self-reported "
        f"diabetics ({pct('S5', 'masking.below_6_5_share')} %) have HbA1c below 6.5 % ({n('S5', 'masking.below_6_5_on_med')} on medication); uninsured adults with high "
        f"HbA1c are {float(g('S5', rd + '.rd_pp')):+.1f} pp ({float(g('S5', rd + '.ci_low_pp')):.1f} to "
        f"{float(g('S5', rd + '.ci_high_pp')):.1f}) more often undiagnosed.\n\n"
        f"**Minimal vs systematic, same L2 logistic regression:** ΔAUC {a('S7', 'headline.S_minus_M1_T1_eall.est', True)} "
        f"{ci('S7', 'headline.S_minus_M1_T1_eall')}, {v('S10', 'h2b.subs.(a) AUC.verdict')} (margin ±0.01); "
        f"Brier worsens ({a('S10', 'h2b.subs.(b) Brier.est', True)}, {v('S10', 'h2b.subs.(b) Brier.verdict')}) from class weights "
        f"(without them ΔAUC {a('S10', pp.format('roc_auc'), True)}, ΔBrier {a('S10', pp.format('brier'), True)}).\n\n"
        f"**Internal hold-out (n = {n('S9', 'holdout.log.n_test')}):** leak gate "
        f"{a('S9', 'holdout.pairs[comparison=M1 T1 - M0 T1&pop=E-ALL].est', True)}; recognition gap of the same direction and size "
        f"({a('S9', ho.format('E-ALL') + ' MINUS ' + ho.format('E-SCREEN'), True)} vs {a('S7', 'headline.eall_minus_escreen_S_T1.est', True)}), "
        f"not separately testable with {n('S9', 'holdout.metrics[arm=S&tier=1&pop=E-SCREEN].n_pos')} screening positives; "
        f"{n('S9', 'holdout.n_flag_2se')} of {n('S10', 'holdout.n_rows')} metrics > 2 SE below cross-validation.\n\n"
        "*Numbers re-asserted in Appendix A.5.*")
    return text, word_count(text)


def word_count(markdown: str) -> int:
    """Words a reader sees: headings, emphasis markers, link targets and table rules removed."""
    t = re.sub(r"\]\([^)]*\)", "]", markdown)
    t = re.sub(r"@@H:[^@]*@@", "§x.y", t)
    t = re.sub(r"@@A:[^~@]*~([^@]*)@@", r"\1", t)
    t = re.sub(r"[#*|>`\[\]]", " ", t)
    t = re.sub(r"^-{3,}$|\|?-{3,}\|", " ", t, flags=re.M)
    return len([w for w in t.split() if re.search(r"[\w%§]", w)])


# Brief requirement -> where it is satisfied. @@H:<n>/<title prefix>@@ tokens become links after assembly (resolve_links).
CHECKLIST = [
    ("Non-obvious finding from profiling / EDA", "@@H:3/Cost of a blanket recode@@; @@H:7/Leak gate@@"),
    ("Profiling, cleaning, validation, transformation", "@@H:3/Data-quality dimension matrix@@; @@H:6/Step catalogue@@"),
    ("Bias, outliers, integrity: cause, mitigation, impact", "@@H:3/Outliers@@; @@H:5/Who is undiagnosed@@; @@H:8/3 × 3 label matrix@@"),
    ("EDA fallacies (correlation vs causation, Simpson)", "@@H:4/Simpson scan@@; @@H:4/Causal structure@@"),
    ("Redundancy, multicollinearity, skewness", "@@H:4/Redundancy and collinearity@@; @@H:4/Skewness@@"),
    ("Minimal vs systematic, same basic model", "@@H:7/Cumulative path@@; @@H:10/Hypothesis scoreboard@@"),
    ("Improvements and deteriorations explained", "@@H:10/Improvements and deteriorations@@"),
    ("Governance: DUA, minimisation, pre-registration", "@@H:1/Data user agreement@@; @@H:6/Hypotheses and pre-registration lock@@"),
    ("GenAI declaration", "@@A:Generative-AI declaration~below@@; @@A:A.7 Generative-AI use log~Appendix A.7@@"),
    ("Reproducibility", "@@H:0/Self-contained workspace@@; @@A:A.5 Reference check (FINAL_REF)~Appendix A.5@@"),
]

# Marker's path: the subsections that carry the argument, in reading order.
MARKERS_PATH = [
    ("3/Cost of a blanket recode", "a routine recode deletes valid HbA1c values (profiling finding)"),
    ("4/Simpson scan", "which sign flips are real and which are mediator artefacts"),
    ("5/Treatment masking", "self-report and HbA1c disagree"),
    ("7/Leak gate", "inadmissible items inflate AUC; the tree splits on an imputed age-at-diagnosis constant"),
    ("7/E-ALL vs E-SCREEN", "recognition of known cases vs screening value"),
    ("8/3 × 3 label matrix", "who is missed under each label; the undiagnosed are hardest whatever the label"),
    ("10/Hypothesis scoreboard", "every verdict, including refuted and inconclusive"),
    ("10/Improvements and deteriorations", "what each preparation block helped or hurt"),
]


def run_line(mode, seconds=None, cores=None) -> str:
    """One line on the stored outputs (mode, measured runtime) for the title table."""
    if not mode:
        return "none stored: run top to bottom (default `NB_MODE=FAST`, about 10 min; `NB_MODE=FINAL` about 30 min)"
    t = ""
    if seconds:
        t = f", {int(seconds // 60)} min {seconds % 60:02.0f} s" + (f" on {cores} logical cores" if cores else "")
    return f"stored from a full {mode} run{t}; a default `NB_MODE=FAST` re-run takes about 10 min (sizes in §0.2)"


def guide_md() -> str:
    path = "\n".join(f"{i}. @@H:{p}@@ – {why}" for i, (p, why) in enumerate(MARKERS_PATH, 1))
    return ("## How to read and run\n\n"
            f"**Marker's path** – the {len(MARKERS_PATH)} subsections that carry the argument:\n\n" + path + "\n\n"
            "- **Each step** has a *Why* paragraph, the code, and a *So what* paragraph with the numbers that code printed; "
            "every quoted number is asserted.\n"
            "- **Labels.** `§N.M` are headings; `DR-Sk-nn` are decisions (Appendix A.1), Stage Sk = §k; verdicts are "
            "*supported*, *refuted*, *equivalent*, *inconclusive* or *mixed* against margins fixed in advance.\n"
            "- **Running.** Python 3.12 with the pinned packages (§0.1). The notebook writes only to a `ca6003_workspace/` "
            "folder next to it and downloads the raw files from the CDC (about 12 MB, hash-checked) if no local copy exists.\n\n"
            "**Contents** (§0–§10 and Appendix A)\n\n@@TOC@@")


FRONT_TAGS = {"front-title", "front-summary", "front-checklist", "front-team", "front-genai", "front-guide",
              "front-group", "front-contrib", "front-runmode", "toc"}          # the last four: earlier layouts


def front_matter(args, n_sections: int, run: str) -> tuple[list, dict]:
    team = load_team()
    summary, n_words = summary_md()
    cells = [
        md(title_md(team, run), tags=["team", "front-title"]),
        md(summary, tags=["front-summary"]),
        md("## Brief requirements and where they are met\n\n"
           + md_table([[r, w] for r, w in CHECKLIST], ["Requirement (assignment brief)", "Where"]), tags=["front-checklist"]),
        md(team_md(team), tags=["team", "front-team"]),
        md(genai_md(team), tags=["team", "front-genai"]),
        md(guide_md(), tags=["front-guide"]),
    ]
    stats = {"summary_words": n_words, "genai_words": word_count(cells[4].source)}
    return cells, stats


def inject_lead(cell, no: int, team: dict) -> None:
    """Add the 'Section lead' line under the '# §N' heading of a section's first cell."""
    lead = team["section_leads"].get(str(no), FILL)
    line = LEAD_LINE + em(lead)
    if LEAD_RE.search(cell.source):
        cell.source = LEAD_RE.sub(lambda _: line, cell.source, count=1)
    else:
        head, _, rest = cell.source.partition("\n")
        cell.source = head + "\n\n" + line + ("\n\n" + rest.lstrip("\n") if rest.strip() else "")
    tags = cell.metadata.get("tags", [])
    if "section-lead" not in tags:
        cell.metadata["tags"] = tags + ["section-lead"]


# ----------------------------------------------------------------------------- heading links
H_TOKEN = re.compile(r"@@H:([^@]+)@@")
A_TOKEN = re.compile(r"@@A:([^@]+)@@")


def anchor(title: str) -> str:
    return "#" + quote(title.replace(" ", "-"), safe="-§–")


def heading_index(cells: list) -> list[tuple[str, str, str]]:
    """(section number, item number, title) for every '## N.M' / '### N.M.k' heading of the assembled notebook."""
    out = []
    for c in cells:
        if c.cell_type != "markdown":
            continue
        fence = False
        for line in c.source.split("\n"):
            if line.lstrip().startswith("```"):
                fence = not fence
            if fence:
                continue
            m = re.match(r"^#{2,3}\s+(\d+)((?:\.\d+)+)\s+(.*?)\s*$", line)
            if m:
                out.append((m.group(1), m.group(1) + m.group(2), m.group(3)))
    return out


def resolve_links(cells: list, partial: bool) -> list[str]:
    """Replace @@H:n/title prefix@@ by a link '[§n.m](#anchor)'. Returns problems (unresolved or ambiguous tokens)."""
    idx = heading_index(cells)
    problems = []

    def repl(m):
        spec = m.group(1)
        sec, _, prefix = spec.partition("/") if "/" in spec else ("", "", spec)
        hits = [(num, t) for s, num, t in idx if (not sec or s == sec) and t.lower().startswith(prefix.lower())]
        if len(hits) > 1:                      # prefer the shallowest heading (N.M over N.M.k)
            depth = min(num.count(".") for num, _ in hits)
            hits = [h for h in hits if h[0].count(".") == depth]
        if len(hits) != 1:
            if not partial:
                problems.append(f"heading link {spec!r}: {len(hits)} matches")
            return f"§{sec}" if sec else prefix
        num, t = hits[0]
        return f"[§{num}]({anchor(f'{num} {t}')})"

    titles = set()
    for c in cells:
        if c.cell_type == "markdown":
            titles.update(m.group(1) for m in re.finditer(r"^#{1,3}\s+(.*?)\s*$", c.source, re.M))

    def repl_a(m):
        title, _, label = m.group(1).partition("~")
        if title not in titles and not partial:
            problems.append(f"heading link {title!r}: heading not found")
        return f"[{label or title}]({anchor(title)})"

    for c in cells:
        if c.cell_type == "markdown" and "@@" in c.source:
            c.source = A_TOKEN.sub(repl_a, H_TOKEN.sub(repl, c.source))
    return problems


RUNTIME_PLACEHOLDER = "@@RUNTIME@@"


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
                lines.append(f"- [{title}](#{quote(title.replace(' ', '-'), safe='-§–')})")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- appendix
# (alias regex that detects a citation in the notebook text, or None = first author's surname; reference text).
# A.4 lists only references that are cited somewhere in the assembled notebook (sections, inlined modules, registers,
# pre-registration text); `citation_report` lists citations without a reference and references never cited.
REFERENCES = [
    (r"American Diabetes Association|\bADA\b[^\n]{0,60}\bBMI\b[^\n]{0,12}\b23\b|\bBMI\b[^\n]{0,6}(?:≥|>=|from|of)\s?23\b",
     "American Diabetes Association Professional Practice Committee (2024). 2. Diagnosis and classification of diabetes: Standards of Care in Diabetes – 2024. *Diabetes Care*, 47(Suppl. 1), S20–S42."),
    (None, "Araneta, M. R. G., Kanaya, A. M., Hsu, W. C., et al. (2015). Optimum BMI cut points to screen Asian Americans for type 2 diabetes. *Diabetes Care*, 38(5), 814–820."),
    (None, "Bang, H., Edwards, A. M., Bomback, A. S., et al. (2009). Development and validation of a patient self-assessment score for diabetes risk. *Annals of Internal Medicine*, 151(11), 775–783."),
    (r"Fairlearn", "Bird, S., Dudík, M., Edgar, R., et al. (2020). *Fairlearn: A toolkit for assessing and improving fairness in AI* (Technical Report MSR-TR-2020-32). Microsoft."),
    (None, "Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1–3."),
    (None, "Chouldechova, A. (2017). Fair prediction with disparate impact: A study of bias in recidivism prediction instruments. *Big Data*, 5(2), 153–163."),
    (None, "Cicchetti, D. V., & Feinstein, A. R. (1990). High agreement but low kappa: II. Resolving the paradoxes. *Journal of Clinical Epidemiology*, 43(6), 551–558."),
    (r"Cohen['’]s (?:κ|kappa)", "Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37–46."),
    (r"\bCox\b[^\n]{0,20}1958", "Cox, D. R. (1958). Two further applications of a model for binary regression. *Biometrika*, 45(3–4), 562–565."),
    (r"\bDAMA\b", "DAMA UK Working Group (2013). *The six primary dimensions for data quality assessment*. DAMA UK."),
    (None, "Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall."),
    (r"Gebru|[Dd]atasheets? for datasets", "Gebru, T., Morgenstern, J., Vecchione, B., et al. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92."),
    (None, "Groenwold, R. H. H., White, I. R., Donders, A. R. T., et al. (2012). Missing covariate data in clinical research: when and when not to use the missing-indicator method for analysis. *CMAJ*, 184(11), 1265–1269."),
    (r"Gwira|Data Brief (?:No\.? ?)?516|\bDB ?516\b",
     "Gwira, J. A., Fryar, C. D., & Gu, Q. (2024). Prevalence of total, diagnosed, and undiagnosed diabetes in adults: United States, August 2021 – August 2023. *NCHS Data Brief*, No. 516. National Center for Health Statistics. https://www.cdc.gov/nchs/products/databriefs/db516.htm"),
    (None, "Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a receiver operating characteristic (ROC) curve. *Radiology*, 143(1), 29–36."),
    (None, "Hardt, M., Price, E., & Srebro, N. (2016). Equality of opportunity in supervised learning. *Advances in Neural Information Processing Systems*, 29."),
    (None, "Harrell, F. E., Jr. (2015). *Regression Modeling Strategies* (2nd ed.). Springer."),
    (r"ISO/IEC 25012", "ISO/IEC (2008). *ISO/IEC 25012:2008 Software engineering – Software product Quality Requirements and Evaluation (SQuaRE) – Data quality model*. International Organization for Standardization."),
    (None, "Kamiran, F., & Calders, T. (2012). Data preprocessing techniques for classification without discrimination. *Knowledge and Information Systems*, 33(1), 1–33."),
    (None, "Kish, L. (1965). *Survey Sampling*. Wiley."),
    (None, "Klein, R. J., & Schoenborn, C. A. (2001). Age adjustment using the 2000 projected U.S. population. *Healthy People Statistical Notes*, 20. National Center for Health Statistics."),
    (r"Korn[-–\s&and]+Graubard", "Korn, E. L., & Graubard, B. I. (1998). Confidence intervals for proportions with small expected number of positive counts estimated from survey data. *Survey Methodology*, 24(2), 193–201."),
    (None, "Lakens, D. (2017). Equivalence tests: A practical primer for t tests, correlations, and meta-analyses. *Social Psychological and Personality Science*, 8(4), 355–362."),
    (r"Landis[-–\s&and]+Koch", "Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174."),
    (r"Little['’]s MCAR|\bLittle\b[^\n]{0,4}\(?1988", "Little, R. J. A. (1988). A test of missing completely at random for multivariate data with missing values. *Journal of the American Statistical Association*, 83(404), 1198–1202."),
    (None, "Manski, C. F. (2003). *Partial Identification of Probability Distributions*. Springer."),
    (None, "Nadeau, C., & Bengio, Y. (2003). Inference for the generalization error. *Machine Learning*, 52(3), 239–281."),
    (r"wwwn\.cdc\.gov/nchs/nhanes|NHANES (?:analytic|tutorial|survey documentation|documentation)|codebooks?",
     "National Center for Health Statistics. NHANES August 2021 – August 2023: data files, codebooks and survey documentation. https://wwwn.cdc.gov/nchs/nhanes/ ; analytic guidance on weighting: https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx"),
    (r"Data User Agreement|\bDUA\b", "National Center for Health Statistics. Data User Agreement. https://www.cdc.gov/nchs/policy/data-user-agreement.html"),
    (r"Okabe", "Okabe, M., & Ito, K. (2008). *Color Universal Design (CUD): How to make figures and presentations that are friendly to colorblind people*. J*Fly. https://jfly.uni-koeln.de/color/"),
    (r"O['’]Brien", "O'Brien, R. M. (2007). A caution regarding rules of thumb for variance inflation factors. *Quality & Quantity*, 41(5), 673–690."),
    (None, "Newcombe, R. G. (1998). Interval estimation for the difference between independent proportions: comparison of eleven methods. *Statistics in Medicine*, 17(8), 873–890."),
    (None, "Ojala, M., & Garriga, G. C. (2010). Permutation tests for studying classifier performance. *Journal of Machine Learning Research*, 11, 1833–1863."),
    (r"Parker|presentation standards", "Parker, J. D., Talih, M., Malec, D. J., et al. (2017). National Center for Health Statistics data presentation standards for proportions. *Vital and Health Statistics*, Series 2, No. 175."),
    (None, "Phipson, B., & Smyth, G. K. (2010). Permutation p-values should never be zero: calculating exact p-values when permutations are randomly drawn. *Statistical Applications in Genetics and Molecular Biology*, 9(1), Article 39."),
    (None, "Ransohoff, D. F., & Feinstein, A. R. (1978). Problems of spectrum and bias in evaluating the efficacy of diagnostic tests. *New England Journal of Medicine*, 299(17), 926–930."),
    (r"Rao[-–\s&and]+Wu", "Rao, J. N. K., & Wu, C. F. J. (1988). Resampling inference with complex survey data. *Journal of the American Statistical Association*, 83(401), 231–241."),
    (None, "Rubin, D. B. (1976). Inference and missing data. *Biometrika*, 63(3), 581–592."),
    (r"Rule et al|Ten simple rules", "Rule, A., Birmingham, A., Zuniga, C., et al. (2019). Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks. *PLoS Computational Biology*, 15(7), e1007007."),
    (None, "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLoS ONE*, 10(3), e0118432."),
    (None, "Simonsohn, U., Simmons, J. P., & Nelson, L. D. (2020). Specification curve analysis. *Nature Human Behaviour*, 4(11), 1208–1214."),
    (r"Westreich|Table 2 fallacy", "Westreich, D., & Greenland, S. (2013). The Table 2 fallacy: presenting and interpreting confounder and modifier coefficients. *American Journal of Epidemiology*, 177(4), 292–298."),
    (r"WHO Expert Consultation|\bWHO\b(?!LE)", "WHO Expert Consultation (2004). Appropriate body-mass index for Asian populations and its implications for policy and intervention strategies. *The Lancet*, 363(9403), 157–163."),
    (None, "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association*, 22(158), 209–212."),
    (r"Yeo[-–\s&and]+Johnson", "Yeo, I.-K., & Johnson, R. A. (2000). A new family of power transformations to improve normality or symmetry. *Biometrika*, 87(4), 954–959."),
    (None, "Youden, W. J. (1950). Index for rating diagnostic tests. *Cancer*, 3(1), 32–35."),
]
# Named methods / sources that need a reference even when no year is given next to them.
NAMED_CITATIONS = [r"\bHarrell\b", r"\bRubin\b", r"Little['’]s MCAR", r"\bManski\b", r"\bKish\b", r"Yeo[-–]Johnson",
                   r"Landis[-–]Koch", r"\bDAMA\b", r"ISO/IEC \d+", r"Fairlearn", r"Ransohoff", r"Korn[-–]Graubard",
                   r"Rao[-–]Wu", r"Nadeau[-–]Bengio", r"\bGebru\b", r"Data User Agreement", r"Data Brief (?:No\.? ?)?516",
                   r"\bWHO\b(?!LE)", r"Table 2 fallacy", r"\bLakens\b", r"\bYouden\b", r"\bBenjamini\b", r"\bHolm\b",
                   r"\bBonferroni\b", r"Okabe", r"\bTRIPOD\b", r"\bSteyerberg\b", r"\bVan Calster\b", r"\bPearl\b",
                   r"\bHernán\b", r"\bBreiman\b", r"\bFirth\b", r"\bPlatt\b", r"\bHosmer\b", r"\bDeLong\b", r"\bNewcombe\b",
                   r"\bWilson\b", r"Cohen['’]s (?:κ|kappa)", r"spectrum bias", r"\bADA\b[^\n]{0,60}\bBMI\b[^\n]{0,12}\b23\b"]
AUTHOR_YEAR = re.compile(r"\b([A-Z][A-Za-z'’\-–]+)(?:,?\s+(?:&|and)\s+[A-Z][A-Za-z'’\-]+|\s+et\s+al\.?)?,?\s+\(?((?:19|20)\d\d)\b")
NOT_AUTHORS = {"Aug", "August", "NHANES", "The", "US", "In", "Since", "January", "October", "November", "September",
               "Cycle", "Stage", "Python", "Release", "Version", "Data", "Brief", "Standard", "Census", "Population", "UTC"}


def ref_alias(alias: str | None, text: str) -> re.Pattern:
    return re.compile(alias if alias else r"\b" + re.escape(re.split(r"[,(]", text, 1)[0].strip()) + r"\b")


def ref_key(text: str) -> tuple[str, str]:
    m = re.search(r"\((\d{4})\)", text)
    return (text[:m.start()] if m else text.split(".")[0]), (m.group(1) if m else "")


def citation_report(cells: list) -> dict:
    """Cited-but-missing and never-cited references, from the text of the assembled notebook (A.4 excluded)."""
    corpus = "\n".join(c.source for c in cells if "references" not in c.metadata.get("tags", []))
    keys = [ref_key(t) for _, t in REFERENCES]
    missing = set()
    for m in AUTHOR_YEAR.finditer(corpus):
        name, year = m.group(1), m.group(2)
        parts = [p for p in re.split(r"[-–]", name) if p]
        if name in NOT_AUTHORS or not parts:
            continue
        if not any(y == year and any(re.search(r"\b" + re.escape(p) + r"\b", authors) for p in parts) for authors, y in keys):
            missing.add(f"{m.group(0).strip()}")
    for pat in NAMED_CITATIONS:          # a named method needs a reference at one of its mentions at least
        hits = list(re.finditer(pat, corpus))
        covered = any(ref_alias(a, t).search(m.group(0)) or ref_alias(a, t).search(corpus[max(0, m.start() - 40):m.end() + 40])
                      for m in hits for a, t in REFERENCES)
        if hits and not covered:
            missing.add(hits[0].group(0))
    cited = [t for a, t in REFERENCES if ref_alias(a, t).search(corpus)]
    never = [t.split("(")[0].strip() for a, t in REFERENCES if t not in cited]
    return {"cited": cited, "missing": sorted(missing), "never_cited": never}

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

# Reference numbers: (id, section, dotted path in results/metrics_<S>.json, tolerance FAST, tolerance FINAL).
# `--make-final-ref` stores the values of a FINAL run in notebooks/final/final_ref.json; the appendix cell asserts
# every run against them. Deterministic counts have tolerance 0; Monte-Carlo quantities get a margin that is wide
# enough for 5x2 CV / B = 100 but far below the effect sizes interpreted in the text.
REF_SPECS = [
    ("cohort_n", "S1", "n_cohort", 0, 0),
    ("L_comb_positives", "S1", "labels.L_comb", 0, 0),
    ("prevalence_weighted", "S1", "prevalence_comb.weighted", 1e-6, 1e-6),
    ("S7_auc_M0_eall_T1", "S7", "headline.auc_M0_eall_T1", 0.02, 0.005),
    ("S7_auc_M1_eall_T1", "S7", "headline.auc_M1_eall_T1", 0.02, 0.005),
    ("S7_auc_S_eall_T1", "S7", "headline.auc_S_eall_T1", 0.02, 0.005),
    ("S7_auc_S_escreen_T1", "S7", "headline.auc_S_escreen_T1", 0.04, 0.01),
    ("S7_leak_gate_est", "S7", "headline.leak_gate_T1_eall.est", 0.03, 0.01),
    ("S7_S_minus_M1_est", "S7", "headline.S_minus_M1_T1_eall.est", 0.015, 0.005),
    # S8 fairness: counts exact; group TPRs and calibration within Monte-Carlo / fold error
    ("S8_escreen_positives_train", "S8", "setup.n_pos_escreen", 0, 0),
    ("S8_tpr_eall_T1", "S8", "overall_tpr_eall_t1", 0.03, 0.005),
    ("S8_tpr_undiagnosed", "S8", "gap_decomposition.tpr_undiagnosed", 0.05, 0.01),
    ("S8_worst_cell_gap_Lcomb", "S8", "label_matrix.worst_gap.L_comb", 0.03, 0.005),
    ("S8_calibration_slope", "S8", "calibration.overall.slope", 0.05, 0.01),
    # S9 robustness: deterministic checks exact; the one-shot hold-out is stored (FAST) or reproduced exactly (FINAL)
    ("S9_permutation_null_mean_S", "S9", "permutation.S.null_mean", 0.005, 0.005),
    ("S9_sensitivity_same_verdict", "S9", "sensitivity.eall_same_verdict", 1, 0),
    ("S9_db516_max_abs_diff_pp", "S9", "external.db516.max_abs_diff_pp", 1e-6, 1e-6),
    ("S9_prevalence_ipw", "S9", "mnar.prevalence[weighting=WTMEC2YR x IPW].est", 1e-5, 1e-5),
    ("S9_strongest_admissible_auc", "S9", "leak_hunt.strongest_admissible.auc", 0.01, 0.001),
    ("S9_holdout_auc_S_eall", "S9", "holdout.metrics[arm=S&tier=1&pop=E-ALL].roc_auc", 0, 0),
    ("S9_holdout_auc_S_escreen", "S9", "holdout.metrics[arm=S&tier=1&pop=E-SCREEN].roc_auc", 0, 0),
    ("S9_holdout_auc_M1_eall", "S9", "holdout.metrics[arm=M1&tier=1&pop=E-ALL].roc_auc", 0, 0),
    ("S9_holdout_auc_M0_eall", "S9", "holdout.metrics[arm=M0&tier=1&pop=E-ALL].roc_auc", 0, 0),
    ("S9_holdout_S_minus_M1_eall", "S9", "holdout.pairs[comparison=S T1 - M1 T1&pop=E-ALL].est", 0, 0),
    ("S9_holdout_rows_2se_below_cv", "S9", "holdout.n_flag_2se", 0, 0),
    # S10 synthesis: ledger sizes and the verdict count
    ("S10_claims", "S10", "claims.n", 0, 0),
    ("S10_headline_claims", "S10", "claims.n_headline", 0, 0),
    ("S10_limitations", "S10", "limitations.n", 0, 0),
    ("S10_verdicts_supported", "S10", "verdict_counts.supported", 1, 0),
    ("S10_holdout_rows_2se_below_cv", "S10", "holdout.n_flag_2se", 0, 0),
    # numbers quoted in the front-matter Summary (read from results/final_metrics.json at build time)
    ("summary_undiagnosed", "S1", "e_screen.positives", 0, 0),
    ("summary_prevalence_ci_low", "S1", "prevalence_comb.ci_low", 1e-6, 1e-6),
    ("summary_prevalence_ci_high", "S1", "prevalence_comb.ci_high", 1e-6, 1e-6),
    ("summary_blanket_cells_destroyed", "S3", "blanket_recode.valid_cells_destroyed_cohort", 0, 0),
    ("summary_blanket_a1c_positives_lost", "S3", "blanket_recode.a1c_positives_lost", 0, 0),
    ("summary_masking_below_6_5", "S5", "masking.below_6_5", 0, 0),
    ("summary_self_reported", "S5", "masking.self_reported", 0, 0),
    ("summary_undiagnosed_rd_uninsured_pp", "S5", "undiagnosed_inequality.risk_differences_pp.uninsured - insured.rd_pp", 1e-6, 1e-6),
    ("summary_eall_minus_escreen_S", "S7", "headline.eall_minus_escreen_S_T1.est", 0.02, 0.005),
    ("summary_minus_care_eall", "S7", "headline.minus_care_eall.est", 0.01, 0.003),
    ("summary_minus_care_escreen", "S7", "headline.minus_care_escreen.est", 0.02, 0.005),
    ("summary_did040_fill", "S7", "tree_m0.did040_fill", 0, 0),
    ("summary_did040_missing_share", "S7", "tree_m0.did040_missing_share", 1e-6, 1e-6),
    ("summary_tpr_diagnosed", "S8", "gap_decomposition.tpr_diagnosed", 0.05, 0.01),
    ("summary_h2b_brier", "S10", "h2b.subs.(b) Brier.est", 0.01, 0.003),
    ("summary_pure_prep_auc", "S10", "h2b.pure_preparation[pop=E-ALL&metric=roc_auc].diff", 0.015, 0.005),
    ("summary_pure_prep_brier", "S10", "h2b.pure_preparation[pop=E-ALL&metric=brier].diff", 0.003, 0.001),
    ("summary_holdout_M1_minus_M0", "S9", "holdout.pairs[comparison=M1 T1 - M0 T1&pop=E-ALL].est", 0, 0),
    ("summary_holdout_n_test", "S9", "holdout.log.n_test", 0, 0),
    ("summary_holdout_rows", "S10", "holdout.n_rows", 0, 0),
    ("summary_holdout_gap_S", "S9", "holdout.metrics[arm=S&tier=1&pop=E-ALL].roc_auc MINUS holdout.metrics[arm=S&tier=1&pop=E-SCREEN].roc_auc", 0, 0),
    ("summary_holdout_escreen_positives", "S9", "holdout.metrics[arm=S&tier=1&pop=E-SCREEN].n_pos", 0, 0),
]
FINAL_REF_FILE = FINAL_DIR / "final_ref.json"

REFCHECK_CODE = '''new_section()
import json, re
import pandas as pd
from IPython.display import display

FINAL_REF = @@REF@@

def dig(d, path):
    """Value at a dotted path; a list element is selected with key[field=value&field=value] (values compared as text);
    'path_a MINUS path_b' is the difference of two values."""
    if " MINUS " in path:
        a, b = path.split(" MINUS ")
        return float(dig(d, a)) - float(dig(d, b))
    for part in re.findall(r"[^.\\[]+(?:\\[[^\\]]*\\])?", path):
        key, _, sel = part.partition("[")
        d = d[key]
        if sel:
            conds = [c.split("=", 1) for c in sel.rstrip("]").split("&")]
            hits = [x for x in d if all(str(x.get(f)) == v for f, v in conds)]
            assert len(hits) == 1, f"{path}: {len(hits)} matches for [{sel}"
            d = hits[0]
    return d

rows = []
for r in FINAL_REF:
    met = R.load_section(r["section"], missing_ok=True)
    if not met:                      # section not run in this (partial) session
        continue
    try:
        val = float(dig(met, r["path"]))
    except (KeyError, TypeError, AssertionError):
        val = float("nan")
    tol = r["tol_final"] if C.IS_FINAL else r["tol_fast"]
    ok = abs(val - r["value"]) <= tol + 1e-12
    rows.append({"quantity": r["id"], "reference (FINAL)": r["value"], f"this run ({C.NB_MODE})": val, "tolerance": tol, "within": ok})
ref_table = pd.DataFrame(rows)
display(ref_table.round(4))
bad = ref_table[~ref_table["within"]]
assert bad.empty, f"values outside the tolerance of the FINAL reference:\\n{bad}"
print(f"{len(ref_table)} reference quantities reproduced within tolerance ({C.NB_MODE} mode)")'''


def refcheck_cells() -> list:
    if not FINAL_REF_FILE.exists():
        return []
    ref = json.loads(FINAL_REF_FILE.read_text(encoding="utf-8"))
    literal = "[\n" + "".join(f"    {json.dumps(r)},\n" for r in ref["entries"]) + "]"
    return [md("## A.5 Reference check (FINAL_REF)\n"
               "**Why.** The stored outputs come from the FINAL protocol. A reader who re-runs the faster FAST mode should obtain the same "
               "headline numbers up to Monte-Carlo error. The reference values below are the FINAL numbers; each run is compared with them "
               "within a tolerance chosen far below the effect sizes interpreted in the text (counts must match exactly). The hold-out values "
               "(§9.11) have tolerance 0 in both modes: FAST displays the stored one-shot results and FINAL must reproduce them exactly."),
            code(REFCHECK_CODE.replace("@@REF@@", literal)),
            md("**So what.** If the table shows every quantity inside its tolerance, the notebook reproduces the numbers reported in the text and "
               "the video; a failure here means that a package version or the data changed the analysis and the narrative must be re-checked.")]


def dig_path(d, path: str):
    """Same path syntax as `dig` in the notebook cell: dotted keys, list element by key[field=value&field=value],
    'path_a MINUS path_b' for a difference."""
    if " MINUS " in path:
        a, b = path.split(" MINUS ")
        return float(dig_path(d, a)) - float(dig_path(d, b))
    for part in re.findall(r"[^.\[]+(?:\[[^\]]*\])?", path):
        key, _, sel = part.partition("[")
        d = d[key]
        if sel:
            conds = [c.split("=", 1) for c in sel.rstrip("]").split("&")]
            hits = [x for x in d if all(str(x.get(f)) == v for f, v in conds)]
            assert len(hits) == 1, f"{path}: {len(hits)} matches for [{sel}"
            d = hits[0]
    return d


def make_final_ref() -> int:
    entries, modes = [], set()
    for id_, sec, path, tf, tfin in REF_SPECS:
        f = ROOT / "results" / f"metrics_{sec}.json"
        if not f.exists():
            print(f"skip {id_}: {f.name} missing")
            continue
        d = dig_path(json.loads(f.read_text(encoding="utf-8")), path)
        meta = json.loads(f.read_text(encoding="utf-8"))["_meta"]["nb_mode"]
        if tf > 1e-3 and meta != "FINAL":
            print(f"WARN {id_}: stored value comes from a {meta} run, not FINAL")
        modes.add(meta)
        entries.append({"id": id_, "section": sec, "path": path, "value": d, "tol_fast": tf, "tol_final": tfin})
    FINAL_REF_FILE.write_text(json.dumps({"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                          "source_modes": sorted(modes), "entries": entries}, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    print(f"wrote {FINAL_REF_FILE.relative_to(ROOT)} with {len(entries)} entries")
    return 0


# Internal names that occur in the locked pre-registration text (which cannot be edited after the lock). Only the
# entries whose pattern occurs in governance/hypotheses.md are shown.
PREREG_GLOSSARY = [
    (r"`scope-gov`|`modeling`", "`scope-gov`, `modeling`: the project's work-package labels for scope and governance (§1) and for "
                                 "preparation design and experiments (§6–§7) at the time of writing"),
    (r"\bS\d+\b", "S0–S12: project stages; Stage Sk is §k of this notebook (S11–S12 are assembly and video)"),
    (r"design[- ]phase|prototype", "design phase, prototype: the planning round before the section notebooks; its numbers are "
                                   "recomputed and asserted in §3–§5"),
    (r"development_process", "`docs/development_process.md`: the internal methods plan (not part of the submission)"),
    (r"prereg-lock|prereg-v1", "`prereg-lock`, `prereg-v1`: git tags of the lock commit (§6.11)"),
    (r"\bP\d\d\b|\bB[1-6]\b", "P01–P14: preparation steps; B1–B6: blocks of steps (§6.2)"),
    (r"evalkit|config\.", "`evalkit`, `config`: the modules `src/evalkit.py` and `src/config.py` written in §0.0"),
]


def prereg_glossary() -> str:
    text = read_text("governance/hypotheses.md")
    items = [g for pat, g in PREREG_GLOSSARY if re.search(pat, text)]
    return ("**Glossary for internal names in the locked text:** " + " · ".join(items) + ".") if items else ""


def genai_log_md() -> str:
    import csv
    rows = list(csv.DictReader((ROOT / "governance" / "genai_log.csv").open(encoding="utf-8", newline="")))
    body = [[r["date"], r["tool_version"], r["purpose"], r["data_shared"], r["output_used_in"], r["human_verification"]]
            for r in rows]
    return ("## A.7 Generative-AI use log\n\n"
            "Every use of a generative-AI tool during the project, in date order (the file `governance/genai_log.csv`, written into the "
            "workspace in §0.0 and counted in §10). The short declaration is in the front matter: "
            "@@A:Generative-AI declaration~Generative-AI declaration@@.\n\n"
            + md_table(body, ["Date", "Tool (version)", "Purpose", "Data shared", "Output used in", "Verification"]))


def appendix_cells(section_files: list[Path], section_sha: dict[str, str]) -> list:
    cells = [md("# Appendix A: Registers, pre-registration, references and GenAI log"),
             md("## A.1 Decision register\n"
                "**Why.** Every decision that shaped the data or the analysis has a row with its evidence, the alternatives that were rejected "
                "and a self-check verdict (a re-computation of the evidence in the notebook). The per-stage fragments `governance/register/S*.csv` "
                "are merged here into one table.", tags=["appendix"]),
             code(REGISTER_CODE),
             md("**So what.** The table shows all decisions in one place; the summary above it counts them per stage and per self-check verdict. "
                "A decision without a PASS or PASS-FIX verdict would be visible as `other` and has to be justified in the text of its section."),
             md("## A.2 Locked pre-registration text (shown verbatim; SHA-256 below)\n"
                "**Why.** The hypotheses, their margins and their falsifiers were written before the ablation results existed. The file is locked: "
                "it is reproduced here byte for byte with its SHA-256, so it can be compared with the locked version (the lock commit and "
                "its timestamp are shown in @@H:6/Hypotheses and pre-registration lock@@). Its wording is therefore not edited for this notebook.\n\n"
                + prereg_glossary()),
             code(PREREG_CODE),
             md("## A.3 Hypothesis scoreboard\n"
                "The scoreboard with every verdict, including the refuted and inconclusive ones, is in @@H:10/Hypothesis scoreboard@@; "
                "it is not repeated here."),
             md("## A.4 References\n\nEvery work cited in this notebook, including the docstrings of the modules written in §0.0.\n\n@@REFS@@",
                tags=["references"])]
    cells += refcheck_cells()
    commit = source_commit()
    rows = [[f"notebooks/sections/{p.name}", section_sha[p.name][:16]] for p in section_files]
    rows += [[rel, sha256_text(read_text(rel))[:16]] for rel in SRC_FILES]
    cells.append(md("## A.6 Build record\n\n"
                    f"Assembled by `tools/build_final.py` from repository commit `{commit[:12]}`. "
                    "Inlined files and section scripts (first 16 hex digits of the SHA-256 of the LF-normalised text):\n\n"
                    + md_table(rows, ["file", "sha256 (16)"])))
    cells.append(md(genai_log_md(), tags=["genai-log"]))
    return cells


# ----------------------------------------------------------------------------- assembly
STAGE_SUFFIX = re.compile(r"\s*\(Stages?\s+S\d+(?:\s*[–-]\s*S\d+)?\)\s*$")


def strip_stage_suffix(cell) -> None:
    """'# §4 Exploratory analysis (Stage S4)' -> '# §4 Exploratory analysis' (Stage Sk = §k is defined in the reading guide)."""
    head, sep, rest = cell.source.partition("\n")
    cell.source = STAGE_SUFFIX.sub("", head) + sep + rest


def assemble(args) -> tuple[nbformat.NotebookNode, list[Path], dict]:
    section_files = sorted(SECTIONS_DIR.glob("[0-9][0-9]_*.py"))
    if args.sections:
        wanted = {s.strip() for s in args.sections.split(",")}
        section_files = [p for p in section_files if p.name[:2] in wanted]
    if not section_files:
        raise SystemExit("no section scripts found")
    team = load_team()
    body, seen_nos, section_sha, file_sections = [], [], {}, {}
    for i, path in enumerate(section_files):
        cells = strip_bootstrap(load_section(path), path.name)
        no, title = section_number(cells, path)
        section_sha[path.name] = sha256_text(read_text(path.relative_to(ROOT).as_posix()))
        parts = [(no, cells, True)]
        if path.name in SPLITS:
            parts = split_section(cells, no, SPLITS[path.name], path.name)
        for no, cells, starts_file in parts:
            if seen_nos and no != seen_nos[-1] + 1:
                print(f"WARN {path.name}: section §{no} does not follow §{seen_nos[-1]} (numbering gap or repeat)")
            seen_nos.append(no)
            file_sections.setdefault(path.name, []).append(no)
            renumber(cells, no, path.name, preset_idx={0} if i == 0 else None)
            strip_stage_suffix(cells[0])
            inject_lead(cells[0], no, team)
            for c in cells:
                c.metadata["tags"] = [f"sec-{no}"] + ([t for t in c.metadata.get("tags", [])])
            if i == 0:
                # title + intro markdown, then the generated setup, then the remaining cells
                k = next((j for j, c in enumerate(cells) if c.cell_type == "code"), len(cells))
                gen = setup_cells(no)
                for c in gen:
                    c.metadata["tags"] = [f"sec-{no}"] + c.metadata.get("tags", [])
                body += cells[:k] + gen + cells[k:]
            elif starts_file:
                start = code("new_section()", tags=[f"sec-{no}", "section-start"])
                body += [cells[0], start] + cells[1:]
            else:                      # second part of a split file: same namespace, no new_section()
                body += cells
    if not args.sections and seen_nos != list(range(seen_nos[0], seen_nos[0] + len(seen_nos))):
        raise SystemExit(f"section numbers are not consecutive: {seen_nos}")
    appendix = appendix_cells(section_files, section_sha)
    for c in appendix:
        c.metadata["tags"] = ["appendix"] + [t for t in c.metadata.get("tags", []) if t != "appendix"]
    stored = args.execute or getattr(args, "assemble", False)          # the run line is filled in after the outputs exist
    front, info = front_matter(args, len(section_files), RUNTIME_PLACEHOLDER if stored else run_line(None))
    info["file_sections"] = file_sections
    info["section_sha"] = section_sha
    cells = front + body + appendix
    partial = bool(args.sections)
    info["problems"] = resolve_links(cells, partial)
    refs = citation_report(cells)
    info["citations"] = refs
    for c in cells:
        if c.cell_type == "markdown" and "@@REFS@@" in c.source:
            c.source = c.source.replace("@@REFS@@", "\n".join(f"- {r}" for r in refs["cited"]))
    toc = make_toc(cells)
    for c in cells:
        if c.cell_type == "markdown" and "@@TOC@@" in c.source:
            c.source = c.source.replace("@@TOC@@", toc)
    leftover = [i for i, c in enumerate(cells) if c.cell_type == "markdown"     # the run line is filled in after execution
                and re.search(r"@@[A-Z]+[:@]", c.source.replace(RUNTIME_PLACEHOLDER, ""))]
    if leftover:
        info["problems"].append(f"unresolved @@ tokens in cells {leftover}")
    nb = v4.new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["title"] = TITLE
    # deterministic, unique cell ids
    for n, c in enumerate(nb.cells):
        c["id"] = f"c{n:04d}"
    return nb, section_files, info


# ----------------------------------------------------------------------------- execution
# The checkout path itself (it contains spaces, where ABS_PATH_ANY stops): outputs of sections run in the repository
# (tools/run_section.py, used by --assemble) or warnings from the project's .venv must not keep a fragment of it.
ROOT_PATH = re.compile(r"(?i)" + r"[\\/]+".join(re.escape(part) for part in ROOT.as_posix().split("/")) + r"(?:[\\/][^\s\"'<>|)\]]*)?")


def scrub(text: str) -> tuple[str, int]:
    new, n0 = ROOT_PATH.subn("<path>", text)
    new, n = ABS_PATH_ANY.subn("<path>", new)
    return new, n0 + n


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


def slowest_cells(nb, k: int = 12) -> list[str]:
    """The k slowest code cells (seconds, section tag, first source line) - for runtime tuning."""
    rows = []
    for i, c in enumerate(nb.cells):
        ex = c.metadata.get("execution") or {} if c.cell_type == "code" else {}
        a, b = ex.get("iopub.execute_input") or ex.get("shell.execute_reply.started"), ex.get("shell.execute_reply")
        if a and b:
            dt = (datetime.fromisoformat(b.replace("Z", "+00:00")) - datetime.fromisoformat(a.replace("Z", "+00:00"))).total_seconds()
            tag = next((t for t in c.metadata.get("tags", []) if t.startswith("sec-") or t == "appendix"), "other")
            first = next((ln for ln in c.source.split("\n") if ln.strip() and not ln.startswith("#")), "")[:70]
            rows.append((dt, i, tag, first))
    return [f"   {dt:7.1f} s  cell {i:4d} {tag:<8} {first}" for dt, i, tag, first in sorted(rows, reverse=True)[:k]]


def finish_runtime_cell(nb, mode: str, runtimes: dict[str, float], total: float) -> str:
    """Write the stored-run line into the title table (per-section times go to build_record.json and runtime_log.md)."""
    line = run_line(mode, total, os.cpu_count())
    for c in nb.cells:
        if c.cell_type == "markdown" and RUNTIME_PLACEHOLDER in c.source:
            c.source = c.source.replace(RUNTIME_PLACEHOLDER, line)
    return line


# ----------------------------------------------------------------------------- validation
def validate(nb, path: Path, executed: bool) -> list[str]:
    problems: list[str] = []
    nbformat.validate(nb)
    for i, c in enumerate(nb.cells):
        txt = c.source
        m = ABS_PATH.search(txt)
        if m:
            problems.append(f"cell {i}: absolute path in source near {txt[max(0, m.start() - 20):m.end() + 20]!r}")
        if c.cell_type == "markdown" and re.search(r"@@[A-Z]+[:@]", txt):
            problems.append(f"cell {i}: unresolved @@ token")
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


def placeholders(nb) -> list[str]:
    """Team entries still to be filled in (a warning, not a failure: the team completes them before submission)."""
    out = []
    for i, c in enumerate(nb.cells):
        if c.cell_type != "markdown":
            continue
        lines = c.source.split("\n")
        head = next((ln for ln in lines if ln.startswith("#")), lines[0])[:50]
        for m in FILL_RE.finditer(c.source):
            out.append(f"cell {i} ({head}): {m.group(0)}")
    return out


def front_word_counts(nb) -> dict[str, int]:
    out = {}
    for c in nb.cells:
        tags = c.metadata.get("tags", [])
        tag = next((t for t in tags if t.startswith("front-")), None)
        if tag:
            out[tag[6:]] = word_count(c.source)
    return out


def fill_team(path: Path) -> int:
    """Re-render the team cells and the 'Section lead' lines of an existing notebook from notebooks/final/team.json.
    Code cells and outputs are untouched (asserted through the code-cell SHA-256)."""
    nb = nbformat.read(path, as_version=4)
    before = code_hash(nb)
    team = load_team()
    render = {"front-team": team_md, "front-genai": genai_md}
    n, problems = 0, []
    for c in nb.cells:
        tags = c.metadata.get("tags", [])
        for tag, fn in render.items():
            if tag in tags:
                new = md(fn(team))
                problems += resolve_links(list(nb.cells) + [new], partial=False)   # headings of this notebook
                c.source = new.source
                n += 1
        if "section-lead" in tags:
            no = next((t[4:] for t in tags if t.startswith("sec-")), None)
            if no is not None:
                inject_lead(c, int(no), team)
                n += 1
    assert code_hash(nb) == before, "code cells changed"
    for p in problems:
        print("PROBLEM", p)
    nbformat.write(nb, path)
    left = placeholders(nb)
    print(f"updated {n} markdown cells from {TEAM_FILE.name}; code-cell SHA-256 unchanged ({before[:16]})")
    print(f"{len(left)} placeholders left" + "".join(f"\n   {x}" for x in left))
    return 1 if problems else 0


def stored_run_line() -> str:
    rec = json.loads((FINAL_DIR / "build_record.json").read_text(encoding="utf-8"))
    if rec.get("stored_run_line"):                 # written by --assemble (the outputs do not come from one full run)
        return rec["stored_run_line"]
    mode = rec.get("stored_outputs_mode")
    run = (rec.get("runs") or {}).get(mode or "", {})
    return run_line(mode, run.get("runtime_seconds"), run.get("cores") or run.get("cpu_count"))


def refresh_front(path: Path) -> int:
    """Replace the front matter of an existing (executed) notebook with the current layout and text.
    Code cells and outputs are untouched (asserted through the code-cell SHA-256)."""
    nb = nbformat.read(path, as_version=4)
    before = code_hash(nb)
    k = 0
    while k < len(nb.cells) and FRONT_TAGS & set(nb.cells[k].metadata.get("tags", [])):
        k += 1
    front, info = front_matter(argparse.Namespace(mode="FINAL", execute=False), 0, stored_run_line())
    nb.cells = front + nb.cells[k:]
    problems = resolve_links(nb.cells, partial=False)
    toc = make_toc(nb.cells)
    for c in nb.cells:
        if c.cell_type == "markdown" and "@@TOC@@" in c.source:
            c.source = c.source.replace("@@TOC@@", toc)
    if info["summary_words"] > SUMMARY_MAX_WORDS:
        problems.append(f"summary has {info['summary_words']} words (> {SUMMARY_MAX_WORDS})")
    assert code_hash(nb) == before, "code cells changed"
    for p in problems:
        print("PROBLEM", p)
    nbformat.write(nb, path)
    print(f"front matter replaced: {k} old cells -> {len(front)} new cells; code-cell SHA-256 unchanged ({before[:16]})")
    print("front-matter words:", front_word_counts(nb))
    return 1 if problems else 0


def code_hash(nb) -> str:
    """SHA-256 over all code-cell sources (S12: after the video link is added only markdown may change)."""
    h = hashlib.sha256()
    for c in nb.cells:
        if c.cell_type == "code":
            h.update(c.source.encode("utf-8") + b"\n--cell--\n")
    return h.hexdigest()


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


# ----------------------------------------------------------------------------- incremental release (--assemble)
# The notebook is built from the current sources exactly as above; the code-cell outputs are then taken from
#   (a) notebooks/executed/<file>.ipynb for the files named in --from-executed (tools/run_section.py, release mode),
#   (b) the previous release (--base) for every other section, after a token check that its code is unchanged,
#   (c) the base, or a synthesised "Writing <path>" / Path(...) result, for the generated §0.0 file cells,
#   (d) a small fresh execution (workspace setup + appendix cells, current results/) for the appendix.
EXECUTED_DIR = ROOT / "notebooks" / "executed"
GEN_TAGS = {"setup", "setup-file", "section-start"}
BOOT_MODULES = {"config", "plots", "results_io"}           # imported by the global bootstrap: every section uses them
RUN_RECORDED = ("src/", "config/", "governance/", "requirements.txt")   # inputs whose hashes tools/run_section.py records
WRITEFILE_RE = re.compile(r"^%%writefile\s+(\S+)")
WRITETEXT_RE = re.compile(r"^write_text\((['\"])(.+?)\1")


class AssembleError(Exception):
    pass


def cell_kind(c) -> str:
    tags = set(c.metadata.get("tags", []))
    if tags & GEN_TAGS:
        return "gen"
    return "appendix" if "appendix" in tags else "section"


def cell_sec(c) -> int | None:
    t = next((t for t in c.metadata.get("tags", []) if t.startswith("sec-")), None)
    return int(t[4:]) if t else None


def code_tokens(src: str) -> list:
    """Comment-free token stream of a code cell (the tokenize check used for comment-only commits). Comments and
    blank lines are ignored; statement structure (NEWLINE/INDENT/DEDENT) and every code, string and number token
    count. IPython magic and shell lines are compared verbatim."""
    lines = src.split("\n")
    magic = [("MAGIC", ln.strip()) for ln in lines if ln.lstrip().startswith(("%", "!"))]
    body = "\n".join("pass" if ln.lstrip().startswith(("%", "!")) else ln for ln in lines) + "\n"
    toks = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(body).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.ENDMARKER):
                continue
            toks.append((t.type, "" if t.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT) else t.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return [("RAW", ln.rstrip()) for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    return toks + magic


def first_code_line(src: str) -> str:
    return next((ln.strip() for ln in src.split("\n") if ln.strip() and not ln.lstrip().startswith("#")), "")[:60]


def compare_code(new: list, old: list) -> str | None:
    """None if the two lists of code cells are pairwise token-identical, else the first difference."""
    for j, (a, b) in enumerate(zip(new, old)):
        if code_tokens(a.source) != code_tokens(b.source):
            return f"code cell {j + 1} of {len(new)} ({first_code_line(a.source)!r}) differs"
    if len(new) != len(old):
        return f"{len(new)} code cells now, {len(old)} before"
    return None


def src_imports(text: str) -> set[str]:
    """Project modules imported by a section or module (from src import a, b / from src.a import / from . import a)."""
    mods = set()
    for m in re.finditer(r"from\s+(?:src|\.)\s+import\s+(\([^)]*\)|[^\n]+)", text):
        for part in m.group(1).split("#")[0].strip("() ").split(","):
            name = part.strip().split()[0] if part.strip() else ""
            if name.isidentifier():
                mods.add(name)
    mods |= set(re.findall(r"from\s+(?:src)?\.(\w+)\s+import", text))
    mods |= set(re.findall(r"\bimport\s+src\.(\w+)", text))
    return mods


def section_deps(code_text: str) -> set[str]:
    """Inlined repository files a section can depend on: the project modules it imports (transitively, plus the
    bootstrap modules) and every inlined text input or stored artefact whose file name occurs in its code or in
    one of those modules."""
    texts = {p.stem: read_text(p.relative_to(ROOT).as_posix()) for p in (ROOT / "src").glob("*.py")}
    todo, mods = list(src_imports(code_text) | BOOT_MODULES), set()
    while todo:
        m = todo.pop()
        if m in mods or m not in texts:
            continue
        mods.add(m)
        todo += list(src_imports(texts[m]))
    deps = {f"src/{m}.py" for m in mods} | {"src/__init__.py"}
    corpus = code_text + "\n".join(texts[m] for m in mods)
    for rel in TEXT_INPUTS + SEED_RESULTS:
        if Path(rel).name in corpus:
            deps.add(rel)
    return deps


def gen_keys(cells: list) -> list[tuple]:
    """Stable key of each generated cell: ('file', path), ('codebooks',), ('setup', k) or ('start', §)."""
    keys, k = [], 0
    for c in cells:
        tags = c.metadata.get("tags", [])
        first = c.source.split("\n", 1)[0]
        if "section-start" in tags:
            keys.append(("start", cell_sec(c)))
        elif "setup-file" in tags:
            m = WRITEFILE_RE.match(first) or WRITETEXT_RE.match(first)
            keys.append(("file", m.group(m.lastindex)) if m else
                        (("codebooks",) if "CODEBOOKS_SHA256" in c.source else ("setup-file", first)))
        else:
            keys.append(("setup", k))
            k += 1
    return keys


def notebook_mode(nb) -> str | None:
    """NB_MODE printed by the workspace cell of an executed notebook."""
    for c in nb.cells:
        if c.cell_type == "code" and c.source.startswith("import os, sys, time, pathlib"):
            for o in c.get("outputs", []):
                m = re.search(r"NB_MODE = (\w+)", "".join(o.get("text", "")))
                if m:
                    return m.group(1)
    return None


def load_executed(name: str, mode: str):
    path = EXECUTED_DIR / (Path(name).stem + ".ipynb")
    rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    rerun = f"run `tools/run_section.py notebooks/sections/{name} --mode {mode}`"
    if not path.exists():
        raise AssembleError(f"{rel} does not exist: {rerun}")
    enb = nbformat.read(path, as_version=4)
    meta = enb.metadata.get("ca6003")
    if not meta:
        raise AssembleError(f"{rel} has no run record (written by an older tools/run_section.py, mode unknown): {rerun}")
    if meta.get("mode") != mode:
        raise AssembleError(f"{rel} was run in {meta.get('mode')} mode, the release is {mode}: {rerun}")
    cells = strip_bootstrap(list(enb.cells), name)
    return [c for c in cells if c.cell_type == "code"], meta, path


def local_date(utc: str | None) -> str:
    """Local calendar date of an ISO UTC timestamp (as git's %cs date of the base run)."""
    try:
        return datetime.fromisoformat(utc).astimezone().date().isoformat()
    except (TypeError, ValueError):
        return ""


def section_ranges(nos) -> str:
    groups: list[list[int]] = []
    for n in sorted(nos):
        if groups and n == groups[-1][1] + 1:
            groups[-1][1] = n
        else:
            groups.append([n, n])
    return ", ".join(f"§{a}" if a == b else (f"§{a}–§{b}" if b > a + 1 else f"§{a}, §{b}") for a, b in groups)


def base_provenance(base, base_path: Path, mode: str, nos: list[int]) -> dict[str, dict]:
    """Where the outputs of each section of the base notebook come from: inherited from an earlier assembly, else
    the full run recorded in build_record.json (commit at which the outputs were executed, per-section seconds)."""
    prev = (base.metadata.get("ca6003_build") or {}).get("sections")
    if prev:
        return {k: dict(v) for k, v in prev.items()}
    rec = {}
    if base_path.resolve() == (FINAL_DIR / OUT_NAME).resolve() and (FINAL_DIR / "build_record.json").exists():
        rec = json.loads((FINAL_DIR / "build_record.json").read_text(encoding="utf-8"))
    commit = ((rec.get("outputs_carried_over") or {}).get("outputs_executed_at_commit") or rec.get("source_commit")
              or git("log", "-1", "--format=%H", "--", str(base_path)) or "unknown")
    date = git("show", "-s", "--format=%cs", commit) if commit != "unknown" else ""
    secs = ((rec.get("runs") or {}).get(mode) or {}).get("per_section_seconds") or {}
    return {f"§{n}": {"source": "full run", "mode": mode, "commit": commit[:7], "date": date,
                      "seconds": secs.get(f"§{n}")} for n in nos}


def assembled_run_line(prov: dict[str, dict], mode: str) -> tuple[str, float]:
    groups: dict[str, list[int]] = {}
    for k, p in prov.items():
        if p["source"] == "section run":
            label = f"re-run section by section on {p['date']}"
        else:
            label = (f"from the full {p['mode']} run at commit {p['commit']}" + (f" ({p['date']})" if p.get("date") else ""))
        groups.setdefault(label, []).append(int(k[1:]))
    parts = [f"{section_ranges(nos)} {label}" for label, nos in sorted(groups.items(), key=lambda kv: min(kv[1]))]
    total = sum(p.get("seconds") or 0 for p in prov.values())
    unknown = [int(k[1:]) for k, p in prov.items() if p.get("seconds") is None and not p.get("run_shared_with")]
    t = (f"; section runtimes sum to {int(total // 60)} min {total % 60:02.0f} s"
         + (f" (none recorded for {section_ranges(unknown)})" if unknown else ""))
    return (f"stored from {mode} runs: " + "; ".join(parts) + t
            + "; a default `NB_MODE=FAST` re-run takes about 10 min (sizes in §0.2)"), total


def run_appendix(nb, mode: str, timeout: int) -> float:
    """Execute only the workspace setup (without the codebooks and the raw data) and the appendix code cells in a
    fresh temp workspace that holds a copy of the repository's results/; copy the appendix outputs into `nb`."""
    import copy
    setup = [c for c in nb.cells if c.cell_type == "code" and set(c.metadata.get("tags", [])) & {"setup", "setup-file"}
             and "CODEBOOKS_SHA256" not in c.source and c.source != DATA_CODE.strip("\n")]
    app = [c for c in nb.cells if c.cell_type == "code" and cell_kind(c) == "appendix"]
    mini = v4.new_notebook(cells=[copy.deepcopy(c) for c in setup + app])
    mini.metadata["kernelspec"] = nb.metadata["kernelspec"]
    work = Path(tempfile.mkdtemp(prefix="ca6003_app_"))
    try:
        shutil.copytree(ROOT / "results", work / "ca6003_workspace" / "results")
        wall = execute(mini, mode, work, timeout, download=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    for dst, src in zip(app, mini.cells[len(setup):]):
        dst.outputs = src.outputs
    return wall


def write_record(path: Path, rec_new: dict) -> None:
    """Write the build record; the clean-room runtimes (`runs`) and the previous record are kept."""
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    keep = {"runs": old["runs"], "runs_note": "runtimes of the last full clean-room executions (--execute)"} if old.get("runs") else {}
    previous = {k: v for k, v in old.items() if k not in ("runs", "runs_note", "previous_record")}
    rec = {**rec_new, **keep, "previous_record": previous}
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def assemble_release(args, out: Path) -> int:
    t0 = time.time()
    if args.sections or args.execute:
        raise SystemExit("--assemble builds the whole notebook: do not combine it with --sections or --execute")
    base_path = Path(args.base).resolve()
    base = nbformat.read(base_path, as_version=4)
    mode = notebook_mode(base)
    if mode != "FINAL":
        raise SystemExit(f"base {base_path.name}: stored outputs are from a {mode} run; a release base must be FINAL")
    nb, section_files, info = assemble(args)
    names = [p.name for p in section_files]
    wanted = {s.strip() for s in args.from_executed.split(",") if s.strip()}
    unknown = wanted - {n[:2] for n in names}
    if unknown:
        raise SystemExit(f"--from-executed: no section file starts with {sorted(unknown)}")
    print(f"assembled {len(nb.cells)} cells from {len(names)} sections; release mode {mode}; base {base_path.name}")
    problems = list(info["problems"])
    if info["summary_words"] > SUMMARY_MAX_WORDS:
        problems.append(f"summary has {info['summary_words']} words (> {SUMMARY_MAX_WORDS})")
    errors: list[str] = []

    # 1. generated cells: identical source -> base output; a changed or new file cell -> its standard output
    gen_new = [c for c in nb.cells if c.cell_type == "code" and cell_kind(c) == "gen"]
    gen_old = [c for c in base.cells if c.cell_type == "code" and cell_kind(c) == "gen"]
    old_by_key = dict(zip(gen_keys(gen_old), gen_old))
    path_cls = next((m.group(1) for c in gen_old for o in c.get("outputs", []) if o.output_type == "execute_result"
                     for m in [re.match(r"(\w*Path)\('", str((o.get("data") or {}).get("text/plain", "")))] if m),
                    "WindowsPath" if sys.platform == "win32" else "PosixPath")
    changed_files, synthesised, reused = set(), [], 0
    for key, c in zip(gen_keys(gen_new), gen_new):
        old = old_by_key.get(key)
        if old is not None and old.source == c.source:
            c.outputs, reused = old.outputs, reused + 1
        elif key[0] == "start" and c.source == "new_section()":
            c.outputs = []                                   # new_section() prints nothing
        elif key[0] == "file":
            if c.source.startswith("%%writefile"):           # IPython's own message in a fresh workspace
                c.outputs = [v4.new_output("stream", name="stdout", text=f"Writing {key[1]}\n")]
            else:                                            # write_text() returns the Path, shown as the cell result
                c.outputs = [v4.new_output("execute_result", data={"text/plain": f"{path_cls}('{key[1]}')"})]
            changed_files.add(key[1])
            synthesised.append(key[1] + (" (new)" if old is None else ""))
        else:
            errors.append(f"generated cell {key} ({first_code_line(c.source)!r}) differs from the base and its output "
                          "cannot be synthesised: build with --execute")

    # 2. sections: from the executed notebooks (--from-executed) or from the base
    def sec_code(cells, nos):
        return [c for c in cells if c.cell_type == "code" and cell_kind(c) == "section" and cell_sec(c) in nos]

    current = {rel: sha256_text(read_text(rel)) for rel in
               [p.relative_to(ROOT).as_posix() for p in (ROOT / "src").glob("*.py")] + TEXT_INPUTS if (ROOT / rel).exists()}
    prov = base_provenance(base, base_path, mode, sum(info["file_sections"].values(), []))
    sources, executed_meta, first_rerun = {}, {}, None
    for name in names:
        nos = info["file_sections"][name]
        tag = section_ranges(nos)
        new = sec_code(nb.cells, nos)
        deps = section_deps("\n".join(c.source for c in new))
        rerun = f"run `tools/run_section.py notebooks/sections/{name} --mode {mode}` and pass {name[:2]} to --from-executed"
        if name[:2] in wanted:
            try:
                donor, meta, epath = load_executed(name, mode)
            except AssembleError as e:
                errors.append(f"{tag}: {e}")
                continue
            diff = compare_code(new, donor)
            if diff:
                errors.append(f"{tag} ({name}): {diff} relative to {epath.name}: the section changed after its run; {rerun}")
                continue
            stale = sorted(d for d in deps if d.startswith(RUN_RECORDED) and d in current
                           and (meta.get("inputs_sha256") or {}).get(d) != current[d])
            if stale:
                errors.append(f"{tag} ({name}): {', '.join(stale)} changed after the run recorded in {epath.name}; {rerun}")
                continue
            first_rerun = first_rerun or tag
            same = meta.get("source_sha256") == info["section_sha"][name]
            sources[name] = {"from": f"notebooks/executed/{epath.name}", "mode": meta["mode"], "seconds": meta.get("seconds"),
                             "run_utc": meta.get("run_utc"),
                             "executed_sha256": hashlib.sha256(epath.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                             "section_sha256_at_run": meta.get("source_sha256"), "section_sha256_now": info["section_sha"][name],
                             "note": "section source unchanged since the run" if same else
                                     "section source changed after the run in comments/markdown only (code tokens verified)"}
            executed_meta[name] = meta
            for j, n in enumerate(nos):
                prov[f"§{n}"] = {"source": "section run", "mode": meta["mode"], "file": name,
                                 "date": local_date(meta.get("run_utc")), "seconds": meta.get("seconds") if j == 0 else None,
                                 **({"run_shared_with": f"§{nos[0]}"} if j else {})}
        else:
            donor = sec_code(base.cells, nos)
            diff = compare_code(new, donor)
            if diff:
                errors.append(f"section {tag} code changed ({name}: {diff} relative to the base): {rerun}")
                continue
            hit = sorted(deps & changed_files)
            if hit:
                errors.append(f"section {tag} ({name}) is taken from the base, but {', '.join(hit)} changed since the base run; {rerun}")
                continue
            if first_rerun:
                print(f"WARN {tag} is taken from the base but runs after the re-run {first_rerun}: if it reads their results, re-run it too")
            sources[name] = {"from": f"base ({base_path.name})"}
        for dst, src in zip(new, donor):
            dst.outputs = src.get("outputs", [])
    order = [n for n in names if n in executed_meta]
    for a, b in zip(order, order[1:]):
        if (executed_meta[a].get("run_utc") or "") > (executed_meta[b].get("run_utc") or ""):
            print(f"WARN {b} was run before {a}: if it reads results of {a}, run them again in file order")

    # 3. the appendix check reads results/: it must come from runs in the release mode
    for f in sorted((ROOT / "results").glob("metrics_S*.json")):
        m = json.loads(f.read_text(encoding="utf-8")).get("_meta", {}).get("nb_mode")
        if m != mode:
            errors.append(f"results/{f.name} was written by a {m} run; the release needs {mode} results")
    if errors:
        for e in errors:
            print("FAIL", e)
        print(f"assemble FAILED ({len(errors)} problems); nothing written")
        return 1

    # 4. appendix: execute (workspace setup + appendix cells) against the current results/
    print("executing the appendix cells in a temp workspace ...")
    try:
        app_secs = run_appendix(nb, mode, args.timeout)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL appendix execution: {type(e).__name__}: {str(e)[:3000]}")
        return 1

    # 5. renumber, scrub, run line, validate, write
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    for n, c in enumerate(code_cells, 1):
        c.execution_count = n
        for o in c.outputs:
            if o.output_type == "execute_result":
                o.execution_count = n
    n_scr = scrub_outputs(nb)
    line, total = assembled_run_line(prov, mode)
    for c in nb.cells:
        if c.cell_type == "markdown" and RUNTIME_PLACEHOLDER in c.source:
            c.source = c.source.replace(RUNTIME_PLACEHOLDER, line)
    nb.metadata["language_info"] = base.metadata.get("language_info", {"name": "python"})
    nb.metadata["ca6003_build"] = {"procedure": "assembled", "mode": mode, "sections": prov}
    problems += validate(nb, out, True)
    out.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, out)
    refcheck = next(("".join(o.get("text", "")).strip() for c in code_cells if cell_kind(c) == "appendix"
                     for o in c.outputs if "reference quantities" in "".join(o.get("text", ""))), "no FINAL_REF cell")
    print(f"wrote {out}")
    for name in names:
        print(f"   {section_ranges(info['file_sections'][name]):<10} {name:<26} <- {sources[name]['from']}")
    print(f"generated cells: {reused} reused from the base, synthesised: {synthesised or 'none'}")
    print(f"appendix executed in {app_secs:.0f} s: {refcheck}")
    print(f"scrubbed {n_scr} absolute-path strings from outputs")
    print("stored-run line:", line)
    print(size_report(out, nb))
    print("code-cell SHA-256:", code_hash(nb))
    print("check_repo:", run_check_repo(out))
    left = placeholders(nb)
    print(f"WARN {len(left)} team placeholders left (fill before submission; --validate-only lists them)" if left else "team placeholders: none left")

    def rel_or_name(p: Path) -> str:
        return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.name

    rec = {"notebook": rel_or_name(out), "stored_outputs_mode": mode, "source_commit": source_commit()[:7],
           "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "procedure": "assembled",
           "procedure_note": ("tools/build_final.py --assemble: notebook built from the current sources; the outputs of each "
                              "section come from its own run in the release mode (tools/run_section.py, repository context, "
                              "notebooks/executed) or from the base release after a comment-insensitive token check of its code "
                              "and of the inlined files it uses; changed workspace file cells get the standard write output; "
                              "the appendix cells are executed against the current results/"),
           "base": {"notebook": rel_or_name(base_path),
                    "sha256": hashlib.sha256(base_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()},
           "sections": sources, "section_provenance": prov,
           "generated_cells": {"reused_from_base": reused, "synthesised": synthesised},
           "appendix": {"executed_seconds": round(app_secs, 1), "final_ref": refcheck},
           "stored_run_line": line, "section_runtime_seconds_sum": round(total, 1),
           "code_cell_sha256": code_hash(nb),
           "notebook_sha256": hashlib.sha256(out.read_bytes().replace(b"\r\n", b"\n")).hexdigest() + " (LF line endings)",
           "front_matter_words": front_word_counts(nb), "team_placeholders_left": len(left),
           "validation": "OK" if not problems else problems}
    rec_path = FINAL_DIR / "build_record.json" if out == (FINAL_DIR / OUT_NAME).resolve() else out.with_suffix(".build_record.json")
    write_record(rec_path, rec)
    print(f"build record: {rec_path}")
    for p in problems:
        print("PROBLEM", p)
    print(f"assemble {'FAILED' if problems else 'OK'} ({time.time() - t0:.0f} s total)")
    return 1 if problems else 0


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
    ap.add_argument("--make-final-ref", action="store_true",
                    help="write notebooks/final/final_ref.json from results/metrics_*.json (run after a FINAL execution) and exit")
    ap.add_argument("--validate-only", metavar="NOTEBOOK", help="validate an existing notebook (schema, absolute paths, "
                    "execution counts, size, code-cell hash, remaining team placeholders) and exit")
    ap.add_argument("--fill-team", metavar="NOTEBOOK", help="re-render the team cells and section-lead lines of an existing "
                    "notebook from notebooks/final/team.json (code cells and outputs unchanged) and exit")
    ap.add_argument("--refresh-front", metavar="NOTEBOOK", help="replace the front matter of an existing notebook with the "
                    "current layout and text (code cells and outputs unchanged) and exit")
    ap.add_argument("--assemble", action="store_true", help="incremental release: build from the current sources and take the "
                    "outputs from per-section runs (--from-executed) and from the base release (no full re-execution)")
    ap.add_argument("--from-executed", default="", metavar="NN,NN", help="with --assemble: section file prefixes whose outputs "
                    "come from notebooks/executed/<file>.ipynb (tools/run_section.py in the release mode)")
    ap.add_argument("--base", default=str(FINAL_DIR / OUT_NAME), help="with --assemble: previous release notebook (FINAL outputs)")
    args = ap.parse_args()

    if args.make_final_ref:
        return make_final_ref()
    if args.validate_only:
        path = Path(args.validate_only).resolve()
        nb = nbformat.read(path, as_version=4)
        executed = any(c.get("execution_count") for c in nb.cells if c.cell_type == "code")
        problems = validate(nb, path, executed)
        print(size_report(path, nb))
        print("executed:", executed, "| code-cell SHA-256:", code_hash(nb))
        print("check_repo:", run_check_repo(path))
        print("front-matter words:", front_word_counts(nb))
        left = placeholders(nb)
        print(f"WARN {len(left)} team placeholders left (fill before submission)" if left else "team placeholders: none left")
        for x in left:
            print("   ", x)
        for p in problems:
            print("PROBLEM", p)
        print("validation", "FAILED" if problems else "OK")
        return 1 if problems else 0
    if args.fill_team:
        return fill_team(Path(args.fill_team).resolve())
    if args.refresh_front:
        return refresh_front(Path(args.refresh_front).resolve())

    out = Path(args.out).resolve()
    if args.assemble:
        if "course" in out.parts:
            raise SystemExit("refusing to write into course/")
        return assemble_release(args, out)
    t0 = time.time()
    nb, section_files, info = assemble(args)
    print(f"assembled {len(nb.cells)} cells from {len(section_files)} sections: " + ", ".join(p.name[:2] for p in section_files))
    print(f"front matter: summary {info['summary_words']} words (limit {SUMMARY_MAX_WORDS}), GenAI declaration {info['genai_words']} words")
    cit = info["citations"]
    print(f"references: {len(cit['cited'])} cited and listed in A.4; never cited (dropped): {cit['never_cited'] or 'none'}")
    print(f"citations without a reference: {cit['missing'] or 'none'}")
    if info["summary_words"] > SUMMARY_MAX_WORDS:
        info["problems"].append(f"summary has {info['summary_words']} words (> {SUMMARY_MAX_WORDS})")
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
            failed.parent.mkdir(parents=True, exist_ok=True)
            print("slowest cells so far:\n" + "\n".join(slowest_cells(nb)))
            scrub_outputs(nb)
            nbformat.write(nb, failed)
            print(f"FAIL execution: {type(e).__name__}: {str(e)[:3000]}\npartial notebook: {failed}")
            return 1
        executed = True
        n_scr = scrub_outputs(nb)
        runtimes = section_runtimes(nb)
        slow = slowest_cells(nb)
        finish_runtime_cell(nb, args.mode, runtimes, wall)
        for c in nb.cells:
            c.metadata.pop("execution", None)
        nb.metadata["language_info"] = {"name": "python", "version": sys.version.split()[0]}
        print(f"executed in {wall:.0f} s ({args.mode}); scrubbed {n_scr} absolute-path strings from outputs")
        for k, v in runtimes.items():
            print(f"   {k:<10} {v:7.1f} s")
        print("slowest cells:")
        print("\n".join(slow))
        if not args.keep_workdir and not args.workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        if not args.no_runtime_log and out.parent == FINAL_DIR:
            log = FINAL_DIR / "runtime_log.md"
            head = "# Runtime log\n\nWritten by `tools/build_final.py --execute`. One line per executed build.\n\n| date (UTC) | mode | sections | total (s) | per section (s) |\n|---|---|---|---|---|\n"
            line = (f"| {datetime.now(timezone.utc):%Y-%m-%d %H:%M} | {args.mode} | {len(section_files)} | {wall:.0f} | "
                    + ", ".join(f"{k} {v:.0f}" for k, v in runtimes.items()) + " |\n")
            log.write_text((log.read_text(encoding="utf-8") if log.exists() else head) + line, encoding="utf-8")
    problems = info["problems"] + validate(nb, out, executed)
    out.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, out)
    print(f"wrote {out}")
    print(size_report(out, nb))
    print("code-cell SHA-256:", code_hash(nb))
    print("check_repo:", run_check_repo(out))
    left = placeholders(nb)
    print(f"WARN {len(left)} team placeholders left (fill before submission; --validate-only lists them)" if left else "team placeholders: none left")
    for p in problems:
        print("PROBLEM", p)
    print(f"build {'FAILED' if problems else 'OK'} ({time.time() - t0:.0f} s total)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
