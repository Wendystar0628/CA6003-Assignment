"""Shared figure style and export (one look for notebook and slides)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg") if matplotlib.get_backend().lower() == "agg" else None
import matplotlib.pyplot as plt

from . import config as C

PALETTE = list(C.OKABE_ITO.values())


def set_style() -> None:
    """Apply the project style: Okabe–Ito colours, readable fonts, light grid."""
    plt.rcParams.update({
        "figure.dpi": C.FIG_DPI,
        "savefig.dpi": C.FIG_DPI,
        "axes.prop_cycle": matplotlib.cycler(color=PALETTE),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.frameon": False,
        "font.size": 10,
    })


def savefig(fig, name: str, *, caption: str | None = None) -> str:
    """Save a figure as figures/<name>.png and return the relative path.

    `name` should start with the section id, e.g. "S4_db516_forest".
    """
    path = C.FIGURES_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    if caption:
        (C.FIGURES_DIR / f"{name}.txt").write_text(caption, encoding="utf-8")
    return str(path.relative_to(C.ROOT)).replace("\\", "/")


set_style()
