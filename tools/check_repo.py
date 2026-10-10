"""Pre-commit hygiene check (docs/development_process.md §6.4).

    .venv/Scripts/python tools/check_repo.py [paths...]

Checks the given files (default: all staged files): no absolute local paths,
no files under course/, size < 50 MB, executed notebooks < 5 MB.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABS_PATH = re.compile(r"[A-Za-z]:[\\/]+(?:Study|Users|ADMINI~1|AppData)[\\/]", re.I)
TEXT_SUFFIX = {".py", ".md", ".csv", ".json", ".txt", ".ipynb", ".html", ".yaml", ".yml"}


def staged() -> list[Path]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True).stdout
    return [ROOT / p for p in out.split() if p]


def main(argv: list[str]) -> int:
    files = [Path(a).resolve() for a in argv] or staged()
    problems = []
    for f in files:
        if not f.exists():
            continue
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith("course/"):
            problems.append(f"{rel}: course materials must not be committed")
        size = f.stat().st_size
        if size > 50 * 2**20:
            problems.append(f"{rel}: {size/2**20:.1f} MB > 50 MB")
        if f.suffix == ".ipynb" and size > 5 * 2**20:
            problems.append(f"{rel}: notebook {size/2**20:.1f} MB > 5 MB (clear large outputs)")
        if f.suffix in TEXT_SUFFIX and size < 20 * 2**20:
            text = f.read_text(encoding="utf-8", errors="ignore")
            m = ABS_PATH.search(text)
            if m and rel != "tools/check_repo.py":
                problems.append(f"{rel}: absolute local path near '{text[max(0, m.start()-20):m.end()+20]!r}'")
    for p in problems:
        print("FAIL", p)
    print("check_repo:", "OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
