"""Section-scoped results storage.

Each section writes ONLY its own file `results/metrics_<section>.json`, so parallel
work never collides. `collect()` merges them into `results/final_metrics.json`,
the single source for every number shown on slides.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import config as C

SECTIONS = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11")


def _clean(obj):
    """Make numpy / pandas objects JSON-serialisable; NaN -> None."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(obj, np.ndarray):
        return _clean(obj.tolist())
    if hasattr(obj, "to_dict"):
        return _clean(obj.to_dict())
    return obj


def section_path(section: str) -> Path:
    assert section in SECTIONS, section
    return C.RESULTS_DIR / f"metrics_{section}.json"


def save_section(section: str, payload: dict) -> Path:
    """Overwrite the section's metrics file with `payload` (+ meta)."""
    data = {
        "_meta": {
            "section": section,
            "nb_mode": C.NB_MODE,
            "seed_master": C.SEED_MASTER,
            "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        **_clean(payload),
    }
    path = section_path(section)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    return path


def update_section(section: str, **items) -> Path:
    """Merge keys into the section's metrics file (create if missing)."""
    data = load_section(section, missing_ok=True)
    data.pop("_meta", None)
    data.update(items)
    return save_section(section, data)


def load_section(section: str, *, missing_ok: bool = False) -> dict:
    path = section_path(section)
    if not path.exists():
        if missing_ok:
            return {}
        raise FileNotFoundError(f"{path} – run section {section} first")
    return json.loads(path.read_text(encoding="utf-8"))


def collect() -> dict:
    """Merge all section files into results/final_metrics.json and return it."""
    merged = {}
    for s in SECTIONS:
        if section_path(s).exists():
            merged[s] = load_section(s)
    out = C.RESULTS_DIR / "final_metrics.json"
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return merged
