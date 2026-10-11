"""Convert a section script (jupytext percent .py) to a notebook and execute it.

Usage (from repo root, with the project venv):
    .venv/Scripts/python tools/run_section.py notebooks/sections/03_eda.py
    .venv/Scripts/python tools/run_section.py notebooks/sections/03_eda.py --mode FINAL
    .venv/Scripts/python tools/run_section.py --all

The executed notebook is written to notebooks/executed/<name>.ipynb. Exit code 1 on
any cell error, so the command doubles as the section's run-all check.

The notebook metadata records the run (nb.metadata["ca6003"]): mode, seconds, UTC time, the SHA-256 of the
section source and of the inputs it may read (src/*.py, config/variable_spec.csv, governance/*.md|csv,
requirements.txt), all LF-normalised. `tools/build_final.py --assemble --from-executed NN` checks these before it
reuses the outputs in the release notebook.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import jupytext
import nbformat
from nbclient import NotebookClient

if sys.platform == "win32":  # zmq/tornado need a selector loop on Windows
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ROOT / "notebooks" / "sections"
EXECUTED = ROOT / "notebooks" / "executed"


def sha256_lf(p: Path) -> str:
    """SHA-256 of the file as LF-normalised UTF-8 text (same convention as tools/build_final.py)."""
    return hashlib.sha256(p.read_bytes().decode("utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest()


def input_hashes() -> dict[str, str]:
    files = [*sorted((ROOT / "src").glob("*.py")), ROOT / "config" / "variable_spec.csv", ROOT / "requirements.txt",
             *sorted((ROOT / "governance").glob("*.md")), *sorted((ROOT / "governance").glob("*.csv"))]
    return {f.relative_to(ROOT).as_posix(): sha256_lf(f) for f in files if f.is_file()}


def run(path: Path, mode: str, timeout: int) -> float:
    source_sha, inputs = sha256_lf(path), input_hashes()      # taken before the run: what this execution saw
    nb = jupytext.read(path)
    nb.metadata.setdefault("kernelspec", {"name": "python3", "display_name": "Python 3", "language": "python"})
    os.environ["NB_MODE"] = mode
    os.environ["CA6003_ROOT"] = str(ROOT)
    t0 = time.time()
    client = NotebookClient(nb, timeout=timeout, kernel_name="python3",
                            resources={"metadata": {"path": str(ROOT / "notebooks")}})
    client.execute()
    secs = time.time() - t0
    nb.metadata["ca6003"] = {"mode": mode, "seconds": round(secs, 1),
                             "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                             "section": path.name, "source_sha256": source_sha,
                             "python": sys.version.split()[0], "inputs_sha256": inputs}
    EXECUTED.mkdir(parents=True, exist_ok=True)
    out = EXECUTED / (path.stem + ".ipynb")
    nbformat.write(nb, out)
    return secs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--mode", default=os.environ.get("NB_MODE", "FAST"), choices=["FAST", "FINAL"])
    ap.add_argument("--timeout", type=int, default=3600)
    args = ap.parse_args()
    paths = sorted(SECTIONS.glob("[0-9][0-9]_*.py")) if args.all else [Path(p).resolve() for p in args.paths]
    if not paths:
        ap.error("give section paths or --all")
    for p in paths:
        try:
            secs = run(p, args.mode, args.timeout)
            print(f"OK   {p.name:<32} {args.mode} {secs:6.1f}s")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {p.name}: {type(e).__name__}: {str(e)[:2000]}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
