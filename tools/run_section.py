"""Convert a section script (jupytext percent .py) to a notebook and execute it.

Usage (from repo root, with the project venv):
    .venv/Scripts/python tools/run_section.py notebooks/sections/03_eda.py
    .venv/Scripts/python tools/run_section.py notebooks/sections/03_eda.py --mode FINAL
    .venv/Scripts/python tools/run_section.py --all

The executed notebook is written to notebooks/executed/<name>.ipynb. Exit code 1 on
any cell error, so the command doubles as the section's run-all check.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
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


def run(path: Path, mode: str, timeout: int) -> float:
    nb = jupytext.read(path)
    nb.metadata.setdefault("kernelspec", {"name": "python3", "display_name": "Python 3", "language": "python"})
    os.environ["NB_MODE"] = mode
    os.environ["CA6003_ROOT"] = str(ROOT)
    t0 = time.time()
    client = NotebookClient(nb, timeout=timeout, kernel_name="python3",
                            resources={"metadata": {"path": str(ROOT / "notebooks")}})
    client.execute()
    EXECUTED.mkdir(parents=True, exist_ok=True)
    out = EXECUTED / (path.stem + ".ipynb")
    nbformat.write(nb, out)
    return time.time() - t0


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
