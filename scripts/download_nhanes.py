"""Download the NHANES Aug 2021 – Aug 2023 public-use files used in this project.

Raw data are not committed to git (data minimisation; the source is CDC/NCHS).
Run from the repository root:

    python scripts/download_nhanes.py            # download missing files, verify hashes
    python scripts/download_nhanes.py --force    # re-download everything

Use of the data is governed by the NCHS Data User Agreement:
https://www.cdc.gov/nchs/policy/data-user-agreement.html
"""
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles"
FILES = [
    "DEMO_L", "GHB_L", "GLU_L", "BMX_L", "BPXO_L", "TCHOL_L", "HDL_L", "TRIGLY_L",
    "DIQ_L", "BPQ_L", "MCQ_L", "INQ_L", "HIQ_L", "HUQ_L", "SMQ_L", "PAQ_L",
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "nhanes_2021_2023"
RAW_DIR = DATA_DIR / "raw"
CODEBOOK_DIR = DATA_DIR / "codebooks"
MANIFEST = DATA_DIR / "MANIFEST.sha256"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {}
    entries = {}
    for line in MANIFEST.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        entries[name.lstrip("*")] = digest
    return entries


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=300) as resp, tmp.open("wb") as out:
        out.write(resp.read())
    tmp.replace(dest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    args = parser.parse_args()

    expected = load_manifest()
    mismatches = 0
    for name in FILES:
        xpt = RAW_DIR / f"{name}.xpt"
        if args.force or not xpt.exists():
            print(f"downloading {name}.xpt")
            fetch(f"{BASE_URL}/{name}.xpt", xpt)
        htm = CODEBOOK_DIR / f"{name}.htm"
        if args.force or not htm.exists():
            print(f"downloading {name}.htm")
            fetch(f"{BASE_URL}/{name}.htm", htm)

        digest = sha256(xpt)
        want = expected.get(xpt.name)
        if want is None:
            print(f"  {xpt.name}: no manifest entry")
        elif digest != want:
            # CDC occasionally re-releases files; warn rather than fail.
            mismatches += 1
            print(f"  WARNING {xpt.name}: sha256 differs from MANIFEST (file may have been re-released)")

    print(f"done: {len(FILES)} files in {RAW_DIR}, {mismatches} hash mismatch(es)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
