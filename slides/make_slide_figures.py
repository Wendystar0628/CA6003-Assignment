"""Slide versions of the notebook figures (S11b): simplified, large fonts, 200 dpi.

Run from anywhere:   .venv/Scripts/python slides/make_slide_figures.py

Reads only stored results (results/*.json, results/S*/*.csv); nothing is refitted and no raw data are
opened. The Okabe-Ito palette and the SESOI constants come from src/config.py. Every figure is saved to
slides/figures/<name>.png with a one-line caption file <name>.txt next to it (same convention as
figures/). Every text element must be at least 14 pt (asserted in `save`).

Figures
  S3_governance_quality     governance controls and the data-quality matrix        (slide V2.1)
  S4_redundancy_vif         variance inflation factors and |rho| >= 0.7 clusters   (slide V4.1; stands in for the clustermap)
  S7_coef_forest            BMI coefficient spread, scaled L2 against unscaled     (slide V4.2; left panel of the notebook figure)
  S4_dag                    reduced causal graph for race -> diabetes              (slide V5.2)
  S8_group_tpr              sensitivity by race group, E-ALL and E-SCREEN          (slide V6.5)
  S4_binned_logodds         decile log-odds of age, BMI and total cholesterol      (slide V7.1)
  S10_scoreboard_forest     S minus M1: AUC and Brier, with post-lock variants     (slide V7.2)
  S6_arm_matrix             arms M0, M1, S against preparation blocks              (slide V1.4)
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.text import Text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config as C  # noqa: E402  (palette and SESOI only)

OI = C.OKABE_ITO
RES = ROOT / "results"
OUT = ROOT / "slides" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
DPI = 200
MIN_PT = 14

plt.rcParams.update({
    "font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14, "xtick.labelsize": 14,
    "ytick.labelsize": 14, "legend.fontsize": 14, "figure.titlesize": 16,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
    "legend.frameon": False, "font.family": "DejaVu Sans",
})


def jload(name: str) -> dict:
    return json.loads((RES / name).read_text(encoding="utf-8"))


def save(fig, name: str, caption: str) -> None:
    """Save a figure, check that every visible text is >= MIN_PT, write the caption file."""
    fig.canvas.draw()
    small = sorted({(t.get_text()[:40], round(t.get_fontsize(), 1)) for t in fig.findobj(Text)
                    if t.get_visible() and t.get_text().strip() and t.get_fontsize() < MIN_PT})
    assert not small, f"{name}: text below {MIN_PT} pt: {small}"
    fig.savefig(OUT / f"{name}.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    (OUT / f"{name}.txt").write_text(caption, encoding="utf-8")
    plt.close(fig)
    print("saved", f"slides/figures/{name}.png")


# --------------------------------------------------------------------------------------------- V2.1
def fig_governance() -> None:
    qm = pd.read_csv(RES / "S3" / "quality_matrix.csv").set_index("dimension")
    s1 = jload("metrics_S1.json")
    mini = s1["minimisation"]
    shorts = {"pass": ("pass", OI["green"], "white"),
              "pass with flags": ("pass with flags", OI["sky"], "black"),
              "not assessable": ("not assessable", OI["grey"], "white"),
              "pass for measures, limited for label": ("measures pass, label limited", OI["yellow"], "black"),
              "limited": ("limited", OI["orange"], "black")}
    dims = list(qm.index)
    assert len(dims) == 7 and set(qm["verdict"]) <= set(shorts), set(qm["verdict"])

    fig = plt.figure(figsize=(12.4, 5.6))
    axl = fig.add_axes([0.0, 0.0, 0.47, 1.0]); axr = fig.add_axes([0.50, 0.0, 0.50, 1.0])
    for ax in (axl, axr):
        ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    axl.text(0.0, 0.965, "Governance controls", fontsize=16, fontweight="bold", va="center")
    items = [
        ("NCHS data user agreement", "statistics only, no linkage, no re-identification"),
        ("Data minimisation", f"{mini['dropped']} of {mini['raw_columns']} raw columns dropped"),
        ("Disclosure controls", "top-codes flagged, never undone"),
        ("Sensitive attributes", "race, insurance, access: audit only, never features"),
    ]
    h, gap, y0 = 0.19, 0.035, 0.87
    for i, (head, body) in enumerate(items):
        y = y0 - i * (h + gap)
        axl.add_patch(FancyBboxPatch((0.0, y - h), 1.0, h, boxstyle="round,pad=0.0,rounding_size=0.02",
                                     fc="#eef3f8", ec=OI["blue"], lw=1.6))
        axl.text(0.03, y - 0.045, head, fontsize=15, fontweight="bold", va="top", color="#0b3954")
        axl.text(0.03, y - 0.105, "\n".join(textwrap.wrap(body, 40)), fontsize=14, va="top")
    axr.text(0.0, 0.965, "Data-quality verdict per dimension", fontsize=16, fontweight="bold", va="center")
    h, gap, y0 = 0.1, 0.02, 0.89
    for i, d in enumerate(dims):
        y = y0 - i * (h + gap)
        label, fc, tc = shorts[qm.loc[d, "verdict"]]
        axr.text(0.0, y - h / 2, d.replace(" (ISO/IEC 25012)", "*"), fontsize=14, va="center")
        axr.add_patch(FancyBboxPatch((0.37, y - h), 0.63, h, boxstyle="round,pad=0.0,rounding_size=0.015",
                                     fc=fc, ec="none"))
        axr.text(0.685, y - h / 2, label, fontsize=14, va="center", ha="center", color=tc, fontweight="bold")
    axr.text(0.0, -0.03, "* ISO/IEC 25012 credibility; other dimensions follow DAMA UK",
             fontsize=14, va="center", color="#52606d")
    save(fig, "S3_governance_quality",
         "Governance controls and data-quality verdict per dimension (DAMA UK dimensions plus ISO/IEC 25012 credibility). "
         "Source: results/S3/quality_matrix.csv and results/metrics_S1.json; full table in notebook section 3.9.")


# --------------------------------------------------------------------------------------------- V4.1
def fig_redundancy() -> None:
    vif = pd.read_csv(RES / "S4" / "vif_table.csv")
    s4 = jload("metrics_S4.json")
    raw = vif[vif["set"] == "raw_anthropometry"].set_index("variable")["vif"]
    names = {"BMXBMI": "BMI", "BMXWT": "weight", "BMXHT": "height", "BMXHIP": "hip", "BMXWAIST": "waist",
             "BMXARMC": "arm circ."}
    rows = [(names[k], v, OI["vermillion"] if v > 10 else OI["blue"]) for k, v in raw.sort_values(ascending=False).items()]
    bp = vif[vif["set"] == "bp_readings"]["vif"]; bpm = vif[vif["set"] == "bp_means"]["vif"]
    rows += [("6 BP readings\n(largest)", bp.max(), OI["vermillion"] if bp.max() > 10 else OI["blue"]),
             ("BP means\n(2 variables)", bpm.max(), OI["green"])]
    fig, (ax, axr) = plt.subplots(1, 2, figsize=(12.4, 5.6), gridspec_kw={"width_ratios": [1.15, 1]})
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.62)
    for yi, r in zip(y, rows):
        ax.text(r[1] + 1.5, yi, f"{r[1]:.1f}", va="center", fontsize=14)
    ax.axvline(10, color="black", lw=1.2, ls="--")
    ax.text(11.5, y.max() + 0.62, "VIF 10", fontsize=14, va="bottom")
    ax.set_yticks(y, [r[0] for r in rows]); ax.set_xlim(0, 118); ax.set_ylim(-0.6, y.max() + 1.15)
    ax.set_xlabel("variance inflation factor"); ax.set_title("Redundancy is structural", loc="left")
    ax.grid(axis="y", visible=False)
    axr.axis("off"); axr.set_xlim(0, 1); axr.set_ylim(0, 1)
    axr.text(0.0, 0.97, "Clusters with |ρ| ≥ 0.7", fontsize=16, fontweight="bold", va="center")
    kinds = [("Body size", OI["blue"]), ("Systolic BP", OI["sky"]), ("Diastolic BP", OI["sky"]), ("Cholesterol", OI["orange"])]
    clusters = {"BMI": 0, "SBP 1": 1, "DBP 1": 2, "TC": 3}
    ordered = [None] * 4
    for cl in s4["redundancy"]["clusters_rho07"]:
        ordered[clusters[cl[0]] if cl[0] in clusters else clusters[next(k for k in clusters if k in cl)]] = cl
    assert all(ordered), ordered
    top, h, gap = 0.88, 0.16, 0.04
    for i, ((kname, kcol), cl) in enumerate(zip(kinds, ordered)):
        yy = top - i * (h + gap)
        axr.add_patch(FancyBboxPatch((0.0, yy - h), 1.0, h, boxstyle="round,pad=0.0,rounding_size=0.02",
                                     fc="#f4f6f8", ec=kcol, lw=2))
        axr.text(0.03, yy - 0.04, kname, fontsize=14, fontweight="bold", va="top")
        txt = ", ".join(cl).replace("*", "")
        axr.text(0.03, yy - 0.105, textwrap.shorten(txt, 44, placeholder=" …"), fontsize=14, va="top")
    axr.text(0.0, -0.02, f"log BMI = log weight − 2 log height (r = {s4['redundancy']['r_logbmi_logw_2logh']:.5f})",
             fontsize=14, va="center", color="#52606d")
    fig.tight_layout()
    save(fig, "S4_redundancy_vif",
         "Left: variance inflation factors of the raw anthropometry set and of the six blood-pressure readings against their means "
         "(dashed line = pruning threshold). Right: clusters with absolute Spearman correlation of at least 0.7 (average linkage). "
         "Source: results/S4/vif_table.csv and results/metrics_S4.json; the full clustered heatmap is figures/S4_spearman_clustermap.png.")


# --------------------------------------------------------------------------------------------- V4.2
def fig_coef() -> None:
    ct = pd.read_csv(RES / "S7" / "coef_stability.csv").set_index("arm")
    r3 = jload("metrics_S7.json")["coef_stability"]["ratio_B3"]
    rows = [("scaled L2,\nno pruning", "S-linear-B3", OI["blue"]), ("scaled L2,\npruned", "S-linear", OI["blue"]),
            ("unscaled,\nno pruning", "cum+B1", OI["grey"]), ("unscaled,\npruned", "cum+B3", OI["grey"])]
    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    ypos = [0, 1, 2.6, 3.6]
    for yv, (lab, arm, col) in zip(ypos, rows):
        r = ct.loc[arm]
        ax.errorbar(r["bmi_coef_per_sd"], yv, xerr=[[r["bmi_coef_per_sd"] - r["bmi_q_low"]], [r["bmi_q_high"] - r["bmi_coef_per_sd"]]],
                    fmt="o", color=col, capsize=6, ms=11, lw=3)
        ax.text(1.32, yv, f"SD {r['bmi_sd_per_sd']:.2f}", va="center", fontsize=14, color=col if col != OI["grey"] else "#52606d")
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(ypos, [r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(-0.35, 1.6)
    ax.set_xlabel("BMI coefficient per SD of BMI (log-odds), 95 % bootstrap interval")
    ax.grid(axis="y", visible=False)
    ax.text(0.62, 0.5, f"SD ratio {r3['ratio']:.2f} [{r3['lo']:.2f}, {r3['hi']:.2f}]\nbelow the 2.0 target: refuted",
            ha="left", va="center", fontsize=14, color=OI["blue"], fontweight="bold")
    ax.set_title("BMI coefficient spread over bootstrap refits", loc="left")
    fig.tight_layout()
    save(fig, "S7_coef_forest",
         "BMI coefficient per SD across bootstrap refits of four arms (point = full-data fit, bar = 2.5 to 97.5 percentile; SD = spread across refits). "
         "Blue arms use the scaled L2 pipeline, grey arms are the earlier unscaled steps. Source: results/S7/coef_stability.csv; "
         "the right panel of figures/S7_coef_forest.png (22 coefficients) is not stored in results and is not redrawn here.")


# --------------------------------------------------------------------------------------------- V5.2
def fig_dag() -> None:
    adj = pd.read_csv(RES / "S4" / "dag_adjustment_sets.csv").set_index("question")
    assert adj.loc["Race → diabetes (§4.5)", "adjustment set"] == "{Age, Sex}" and bool(adj.loc["Race → diabetes (§4.5)", "valid (back-door)"])
    assert not bool(adj.loc["… + BMI", "valid (back-door)"])
    pos = {"Age": (0, 2.6), "Race/\nancestry": (0, 1.0), "Sex": (0, -0.6), "SES": (2.5, 2.4),
           "Adiposity": (3.3, 0.5), "BMI": (5.0, -0.7), "Diabetes": (6.2, 1.9)}
    col = {"Age": OI["sky"], "Race/\nancestry": OI["sky"], "Sex": OI["sky"], "SES": OI["sky"],
           "Adiposity": OI["grey"], "BMI": OI["orange"], "Diabetes": OI["grey"]}
    edges = [("Race/\nancestry", "SES", 0), ("Age", "Adiposity", 0.0), ("Age", "Diabetes", -0.12), ("Sex", "Adiposity", 0),
             ("Sex", "Diabetes", 0.1), ("SES", "Adiposity", 0), ("SES", "Diabetes", 0), ("Adiposity", "Diabetes", 0),
             ("Race/\nancestry", "Diabetes", 0.0)]
    med = [("Race/\nancestry", "Adiposity", 0.0), ("Adiposity", "BMI", 0.0), ("Race/\nancestry", "BMI", 0.32)]
    fig, ax = plt.subplots(figsize=(11.4, 5.6))
    ax.set_xlim(-0.9, 7.1); ax.set_ylim(-1.6, 3.6); ax.set_aspect("equal"); ax.axis("off")
    R = 0.62

    def arrow(a, b, rad, color, lw, ls="-", z=1):
        ax.add_patch(FancyArrowPatch(pos[a], pos[b], connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>", mutation_scale=22,
                                     color=color, lw=lw, ls=ls, shrinkA=48, shrinkB=48, zorder=z))
    for a, b, rad in edges:
        arrow(a, b, rad, "#555555", 1.8)
    for a, b, rad in med:
        arrow(a, b, rad, OI["vermillion"], 3.2, ls=(0, (4, 2.5)), z=2)
    for n, (x, y) in pos.items():
        ax.add_patch(plt.Circle((x, y), R, fc=col[n], ec="black", lw=1.2, zorder=3))
        ax.text(x, y, n, ha="center", va="center", fontsize=14, zorder=4, color="white" if col[n] == OI["grey"] else "black")
    ax.text(3.9, 3.35, "Adjust race for {Age, Sex}; BMI is a mediator, never an adjuster", ha="center", fontsize=16, fontweight="bold")
    ax.text(-0.9, -1.45, "dashed = race → adiposity → BMI mediator path · orange = measured · grey = latent", ha="left", fontsize=14, color=OI["vermillion"])
    save(fig, "S4_dag",
         "Reduced causal graph for race and diabetes (subgraph of the 15-node graph in notebook section 4.8; grey = latent, orange = measured). "
         "Back-door adjustment set {Age, Sex} is valid; adding measured BMI is not, because BMI lies on the race-adiposity-BMI path. "
         "Source: results/S4/dag_adjustment_sets.csv.")


# --------------------------------------------------------------------------------------------- V6.5
def fig_group_tpr() -> None:
    ea = pd.read_csv(RES / "S8" / "group_metrics_eall_t1.csv"); es = pd.read_csv(RES / "S8" / "group_metrics_escreen_t1.csv")
    eod = pd.read_csv(RES / "S8" / "eod_eall_t1.csv").set_index(["attribute", "group"])
    ea = ea[ea["attribute"] == "race"].set_index("group"); es = es[es["attribute"] == "race"].set_index("group")
    order = ["NH White", "NH Black", "NH Asian", "Mexican American", "Other Hispanic", "Other/Multi"]
    ref = "NH White"
    lab = {"NH White": "NH White (ref.)", "Other/Multi": "Other / multi"}
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.5), sharey=True)
    for ax, df, name in ((axes[0], ea, "E-ALL"), (axes[1], es, "E-SCREEN")):
        overall = float((df["tpr"] * df["n_pos"]).sum() / df["n_pos"].sum())      # race groups partition the positives
        for i, g in enumerate(order):
            r = df.loc[g]; sup = r["status"] == "suppress"
            colr = OI["grey"] if sup else (OI["blue"] if g == ref else OI["vermillion"])
            ax.errorbar(r["tpr"], i, xerr=[[r["tpr"] - r["tpr_lo"]], [r["tpr_hi"] - r["tpr"]]], fmt="o", color=colr,
                        mfc="white" if sup else colr, capsize=5, ms=11, lw=2.6)
        ax.axvline(overall, color="black", lw=1.2, ls="--")
        ax.set_xlim(0, 1); ax.set_xlabel("TPR at specificity 0.80")
        ax.set_title(f"{name} (overall TPR {overall:.2f})", loc="left")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(order)), [f"{lab.get(g, g)}  (n+ {int(ea.loc[g, 'n_pos'])})" for g in order])
    axes[0].invert_yaxis()
    e = eod.loc[("race", "NH Asian")]
    axes[0].text(0.02, 2.5, f"gap to White {e['eod']:+.2f}\n[{e['eod_lo']:+.2f}, {e['eod_hi']:+.2f}]".replace("-", "−"),
                 va="center", fontsize=14, color=OI["vermillion"], fontweight="bold")
    fig.text(0.99, 0.0, "hollow grey: fewer than 30 positives, shown but not interpreted", ha="right", va="bottom", fontsize=14, color="#52606d")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    save(fig, "S8_group_tpr",
         "True-positive rate at specificity 0.80 by race group for arm S (Tier 1, training-part out-of-fold predictions), with 95 % bootstrap intervals; "
         "n+ = number of positives; dashed line = overall TPR. Hollow grey points have fewer than 30 positives. The annotation gives the equal-opportunity "
         "difference of NH Asian against NH White on E-ALL. Source: results/S8/group_metrics_*_t1.csv and eod_eall_t1.csv; "
         "the full 16-group version is figures/S8_group_tpr.png.")


# --------------------------------------------------------------------------------------------- V7.1
def fig_logodds() -> None:
    s4 = jload("metrics_S4.json")
    bl, lin = s4["binned_logodds"], s4["linearity"]
    spec = [("RIDAGEYR", "Age, years", "Age"), ("BMXBMI", "BMI, kg/m²", "BMI"), ("LBXTC", "Total cholesterol, mg/dL", "Total cholesterol")]
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 5.2))
    for ax, (k, xl, nm) in zip(axes, spec):
        x = np.array(bl[k]["median"]); lo = np.array(bl[k]["logodds"]); n = np.array(bl[k]["n"])
        p = 1 / (1 + np.exp(-lo)); se = np.sqrt(1 / (n * p) + 1 / (n * (1 - p)))
        w = 1 / se ** 2; b, a = np.polyfit(x, lo, 1, w=np.sqrt(w))
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, a + b * xs, color=OI["orange"], lw=3, ls="--", label="straight line")
        ax.plot(x, lo, color=OI["blue"], lw=2.4, alpha=0.9)
        ax.errorbar(x, lo, yerr=1.96 * se, fmt="o", color="black", capsize=4, ms=7, lw=1.8, zorder=3, label="decile log-odds")
        ax.set_xlabel(xl); ax.set_title(f"{nm}\nbend test χ² = {lin[k]['chi2']:.1f}", loc="left")
        ax.xaxis.set_major_locator(plt.MaxNLocator(4)); ax.yaxis.set_major_locator(plt.MaxNLocator(5))
    axes[0].set_ylabel("log-odds of the label")
    axes[0].legend(loc="lower right")
    fig.tight_layout()
    save(fig, "S4_binned_logodds",
         "Observed log-odds of the combined label by decile of age, BMI and total cholesterol (points with 95 % Wald intervals, blue line joins the deciles) "
         "against a straight line weighted through them. Panel titles give the likelihood-ratio chi-square (2 df) of the 4-knot spline against a linear term, "
         "adjusted. Source: results/metrics_S4.json (binned_logodds, linearity); HDL cholesterol panel and the fitted spline curves are in figures/S4_binned_logodds.png.")


# --------------------------------------------------------------------------------------------- V7.2
def fig_scoreboard() -> None:
    pl = pd.read_csv(RES / "S7" / "postlock_m1_sensitivity.csv")
    stored, exact, scaled = "M1 stored (lbfgs, max_iter 5,000)", "M1 exact optimum (newton-cholesky)", "M1 + scaling only (P09)"

    def row(variant, a, metric):
        r = pl[(pl["variant"] == variant) & (pl["a"] == a) & (pl["pop"] == "E-ALL") & (pl["metric"] == metric)].iloc[0]
        return r["est"], r["lo"], r["hi"], r["verdict_equivalence"]
    vcol = {"supported": OI["green"], "refuted": OI["vermillion"], "inconclusive": OI["grey"], "equivalent": OI["blue"]}
    auc_rows = [("S − M1 (locked test)", row(stored, "S", "roc_auc")), ("S without class weights − M1", row(stored, "S-B6a", "roc_auc")),
                ("S − M1 at exact optimum", row(exact, "S", "roc_auc")), ("S − (M1 + scaling)", row(scaled, "S", "roc_auc"))]
    br_rows = [("S − M1", row(stored, "S", "brier")), ("S w/o class\nweights − M1", row(stored, "S-B6a", "brier"))]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.6, 5.4), gridspec_kw={"width_ratios": [1.45, 1]})
    for ax_, rows_, band, lim in ((ax, auc_rows, C.SESOI["roc_auc"], (-0.012, 0.024)), (ax2, br_rows, C.SESOI["brier"], (-0.012, 0.095))):
        for i, (lab, (est, lo, hi, v)) in enumerate(rows_):
            ax_.errorbar(est, i, xerr=[[est - lo], [hi - est]], fmt="o", color=vcol[v], capsize=6, ms=11, lw=3)
            ax_.text(hi + (lim[1] - lim[0]) * 0.025, i, f"{est:+.3f}", va="center", fontsize=14, color="black")
        ax_.axvspan(-band, band, color=OI["sky"], alpha=0.2, lw=0); ax_.axvline(0, color="black", lw=1)
        ax_.set_xlim(lim); ax_.invert_yaxis(); ax_.set_yticks(range(len(rows_)), [r[0] for r in rows_]); ax_.grid(axis="y", visible=False)
    ax.set_xticks([-0.01, 0, 0.01, 0.02]); ax2.set_xticks([0, 0.025, 0.05, 0.075]); ax2.set_ylim(1.6, -0.6)
    ax.set_title("AUC difference, E-ALL", loc="left"); ax.set_xlabel("ΔROC-AUC (95 % CI)")
    ax2.set_title("Brier difference, E-ALL", loc="left"); ax2.set_xlabel("ΔBrier (95 % CI), lower is better")
    fig.text(0.99, 0.0, "colour = verdict: green supported, red refuted, grey inconclusive · shaded band = ±SESOI", ha="right", va="bottom", fontsize=14, color="#52606d")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    save(fig, "S10_scoreboard_forest",
         "Paired cross-validated difference of arm S against M1 on E-ALL (training part, 5x5 CV; shaded band = smallest effect of interest). Left: AUC for the locked "
         "comparison, S without class weights, and two post-lock variants of M1 (exact optimum; scaling only). Right: Brier score, where the deterioration comes from class weights. "
         "Colours are the equivalence-rule verdicts. Source: results/S7/postlock_m1_sensitivity.csv.")


# --------------------------------------------------------------------------------------------- V1.4
def fig_arm_matrix() -> None:
    arms = pd.read_csv(RES / "S6" / "arm_table.csv", index_col=0)
    cat = pd.read_csv(RES / "S6" / "step_catalogue.csv").set_index("step")
    s6 = jload("metrics_S6.json")["arms"]
    blocks = [("B1", "B1  integrity"), ("B2", "B2  availability rule"), ("B3", "B3  redundancy"), ("B4", "B4  missingness"),
              ("B5", "B5  representation"), ("B6a", "B6a  class weights"), ("B6b", "B6b  survey weights")]
    steps = {b: [s for s in cat.index if cat.loc[s, "block"] == b and s in arms.columns] for b, _ in blocks}
    use = ["M0", "M1", "S"]
    heads = {"M0": "M0\nnaive", "M1": "M1\navailability\nrule only", "S": "S\nsystematic"}
    cw = 2.0
    fig, ax = plt.subplots(figsize=(10.6, 5.6))
    ax.set_xlim(-4.6, len(use) * cw + 0.1); ax.set_ylim(-1.9, len(blocks) + 1.9); ax.axis("off"); ax.invert_yaxis()
    for j, a in enumerate(use):
        ax.text(j * cw + cw / 2, -0.95, heads[a], ha="center", va="center", fontsize=15, fontweight="bold")
    for i, (b, nm) in enumerate(blocks):
        ax.text(-0.1, i + 0.5, nm, ha="right", va="center", fontsize=15)
        for j, a in enumerate(use):
            on = bool(arms.loc[a, steps[b]].all())
            ax.add_patch(FancyBboxPatch((j * cw + 0.06, i + 0.06), cw - 0.12, 0.88, boxstyle="round,pad=0,rounding_size=0.08",
                                        fc=OI["blue"] if on else "#eceff1", ec="white", lw=2))
            ax.text(j * cw + cw / 2, i + 0.5, "on" if on else "off", ha="center", va="center", fontsize=14, color="white" if on else "#6b7785")
    yb = len(blocks) + 0.5
    ax.text(-0.1, yb, "Tier-1 features", ha="right", va="center", fontsize=15, fontweight="bold")
    for j, a in enumerate(use):
        ax.text(j * cw + cw / 2, yb, str(s6[a]["n_features_t1"]), ha="center", va="center", fontsize=16, fontweight="bold")
    ax.text(-4.5, len(blocks) + 1.5, "M0 → M1 isolates leakage", fontsize=15, color=OI["vermillion"], fontweight="bold", va="center")
    ax.text(0.4, len(blocks) + 1.5, "M1 → S isolates systematic preparation", fontsize=15, color=OI["blue"], fontweight="bold", va="center")
    save(fig, "S6_arm_matrix",
         "The three main experimental arms against the preparation blocks (blue = every step of the block is on) and the width of the Tier-1 design matrix. "
         "Source: results/S6/arm_table.csv, step_catalogue.csv and metrics_S6.json; all 19 arms and 15 steps are in figures/S6_arm_matrix.png.")


if __name__ == "__main__":
    for f in (fig_governance, fig_redundancy, fig_coef, fig_dag, fig_group_tpr, fig_logodds, fig_scoreboard, fig_arm_matrix):
        f()
