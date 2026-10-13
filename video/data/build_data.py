"""Build the data files for the animated chart scenes of the explainer video.

Reads ONLY stored results (results/metrics_S*.json, results/S*/*.csv, results/S10/numbers_on_slides.csv,
config/variable_spec.csv, governance/*, figures/*.txt, one executed-notebook output). No model is fitted.
Writes one JSON per visual into video/data/ and regenerates video/data/SOURCES.md.

Item schema (every JSON): {"_meta": {...}, "items": {id: item}, "intervals": {...}, "groups": {...}}
    item = {value, label, display, fmt, scale, unit, kind, source, key, csv}
      value    full-precision stored number (or string for non-numeric items)
      label    text used on screen (plan 6.6 naming table: Screening group / All adults / Naive (M0) / ...)
      display  value as it is shown on screen (format spec applied to value * scale, unicode minus, unit appended)
      fmt      Python format spec that produced `display`; scale = 100 turns a stored fraction into per cent
      kind     stored | stored-csv | derived | definition | figure-text | notebook-output
      source   human-readable origin: "file :: key path"
      key      source key in the numbers_on_slides.csv dialect (SEC:path), or null
      csv      {"slide_id", "label"} of the matching numbers_on_slides.csv row, or null (not yet audited)

Run:  .venv/Scripts/python video/data/build_data.py
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent
MINUS = "−"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# ----------------------------------------------------------------------------------------------------------
# Stored results
# ----------------------------------------------------------------------------------------------------------
M: dict[str, dict] = {}
for n in range(11):
    M[f"S{n}"] = json.loads((RES / f"metrics_S{n}.json").read_text(encoding="utf-8"))
FM = json.loads((RES / "final_metrics.json").read_text(encoding="utf-8"))
for sec, d in M.items():
    assert FM[sec] == d, f"final_metrics.json[{sec}] differs from metrics_{sec}.json"
for sec in ("S7", "S8", "S9", "S10"):
    assert M[sec]["mode"] == "FINAL", (sec, M[sec]["mode"])
SNAPSHOT = M["S10"]["_meta"]["written_utc"]

_SPLIT = re.compile(r"\.(?![^\[]*\])")


def _match(v, want: str) -> bool:
    try:
        return abs(float(v) - float(want)) < 1e-9
    except (TypeError, ValueError):
        return str(v) == want


def get(key: str):
    """Resolve 'S7:path.to[k=v&k2=v2].value' (same dialect as numbers_on_slides.csv); '[0]' indexes a list."""
    sec, path = key.split(":", 1)
    d = M[sec]
    for seg in _SPLIT.split(path):
        m = re.fullmatch(r"([^\[]*)(?:\[(.*)\])?", seg)
        name, filt = m.group(1), m.group(2)
        if name:
            d = d[name]
        if filt is not None:
            if "=" not in filt:
                d = d[int(filt)]
            else:
                conds = [c.split("=", 1) for c in filt.split("&")]
                hits = [x for x in d if all(_match(x.get(k), v) for k, v in conds)]
                assert len(hits) == 1, f"{key}: {len(hits)} records match [{filt}]"
                d = hits[0]
    return d


def read_csv(path: str) -> list[dict]:
    with open(ROOT / path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def csv_row(path: str, **flt) -> dict:
    hits = [r for r in read_csv(path) if all(r[k] == v for k, v in flt.items())]
    assert len(hits) == 1, f"{path} {flt}: {len(hits)} rows"
    return hits[0]


NOS = read_csv("results/S10/numbers_on_slides.csv")
NOS_BY_KEY: dict[str, list[dict]] = {}
for r in NOS:
    NOS_BY_KEY.setdefault(r["source_key"], []).append(r)

SPEC = {r["var"]: r for r in read_csv("config/variable_spec.csv")}

# ----------------------------------------------------------------------------------------------------------
# Formatting helpers
# ----------------------------------------------------------------------------------------------------------
_NUM = re.compile(r"[-+]?\d[\d,]*\.?\d*")


def num(s: str) -> float:
    """First number in a display string ('+23.2 pp', '5,730', '14.0 %', '−0.131')."""
    t = s.replace(MINUS, "-").replace(" ", "")
    m = _NUM.search(t)
    assert m, s
    return float(m.group(0).replace(",", ""))


def decimals(s: str) -> int:
    t = s.replace(MINUS, "-")
    m = _NUM.search(t.replace(" ", ""))
    tok = m.group(0)
    return len(tok.split(".")[1]) if "." in tok else 0


def fmt_value(v, spec: str, scale: float = 1.0, unit: str = "") -> str:
    s = format(v * scale, spec)
    if float(s.replace(",", "")) == 0:  # never print a signed zero ("-0.000")
        s = s.lstrip("+-")
        if spec.startswith("+"):
            s = s  # plain zero, no sign
    return s.replace("-", MINUS) + unit


class Item(dict):
    pass


class VFile:
    def __init__(self, name: str, visual: str, scenes: str):
        self.name, self.visual, self.scenes = name, visual, scenes
        self.items: dict[str, Item] = {}
        self.intervals: dict[str, dict] = {}
        self.groups: dict[str, object] = {}
        self.notes: list[str] = []

    def add(self, id_: str, label: str, *, key: str | None = None, value=None, fmt: str | None = ".0f",
            scale: float = 1.0, unit: str = "", source: str | None = None, kind: str | None = None,
            plan: str | None = None, display: str | None = None, show: bool = True, note: str | None = None):
        assert id_ not in self.items, f"{self.name}: duplicate id {id_}"
        if key is not None:
            assert value is None
            value = get(key)
            sec, path = key.split(":", 1)
            source = f"results/metrics_{sec}.json :: {path}"
            kind = kind or "stored"
        assert value is not None and source and kind, (self.name, id_)
        if isinstance(value, bool):
            value = bool(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert math.isfinite(float(value)), (self.name, id_)
            value = float(value) if not float(value).is_integer() or fmt not in (".0f", ",.0f") else int(value)
        if display is None:
            assert fmt is not None, (self.name, id_)
            display = fmt_value(value, fmt, scale, unit)
        it = Item(value=value, label=label, display=display, fmt=fmt, scale=scale, unit=unit, kind=kind,
                  source=source, key=key, csv=None)
        if note:
            it["note"] = note
        if not show:
            it["on_screen"] = False
        it["_plan"] = plan  # stripped before writing
        self.items[id_] = it
        return it

    def interval(self, id_: str, label: str, est: str, lo: str, hi: str):
        e, l, h = self.items[est], self.items[lo], self.items[hi]
        self.intervals[id_] = dict(label=label, est=est, lo=lo, hi=hi,
                                   display=f"{e['display']} [{l['display']}, {h['display']}]")

    def d(self, id_: str) -> str:
        return self.items[id_]["display"]


FILES: list[VFile] = []


def new_file(name, visual, scenes) -> VFile:
    f = VFile(name, visual, scenes)
    FILES.append(f)
    return f


def pct_fmt(spec=".1f"):
    return dict(fmt=spec, scale=100.0, unit=" %")


PP = dict(fmt="+.1f", unit=" pp")
AUC3 = dict(fmt=".3f")
DAUC = dict(fmt="+.3f")
CNT = dict(fmt=",.0f")

# ----------------------------------------------------------------------------------------------------------
# funnel.json  (visual 2, scenes 3-4, 28)
# ----------------------------------------------------------------------------------------------------------
fn = new_file("funnel", "Cohort funnel", "3, 28")
FUN_KEYS = [
    ("n_demo", "S1:funnel.DEMO_L participants", "Participants", "NHANES 2021–23 participants", "11,933"),
    ("n_age20", "S1:funnel.Age >= 20", "Age ≥ 20", "Adults aged 20 or older", "7,809"),
    ("n_exam", "S1:funnel.Interviewed and MEC-examined (RIDSTATR = 2)", "Examined", "Interviewed and examined", "6,064"),
    ("n_a1c", "S1:funnel.HbA1c measured (LBXGH present)", "HbA1c measured", "HbA1c result available", "5,767"),
    ("n_cohort", "S1:funnel.Not pregnant (RIDEXPRG != 1)", "All adults", "Not pregnant = analytic cohort", "5,730"),
]
for id_, key, short, longer, plan in FUN_KEYS:
    # the cohort bar is read from S1:n_cohort (the audited CSV key); the funnel key must agree
    fn.add(id_, short, key="S1:n_cohort" if id_ == "n_cohort" else key, plan=plan, **CNT)
assert fn.items["n_cohort"]["value"] == get("S1:funnel.Not pregnant (RIDEXPRG != 1)") == get("S1:e_all.rows") == get("S3:funnel.Not pregnant (RIDEXPRG != 1)")
stages, prev = [], None
dropped_why = ["under 20", "not examined", "HbA1c missing", "pregnant"]
for i, (id_, key, short, longer, plan) in enumerate(FUN_KEYS):
    st = dict(item=id_, label=short, long_label=longer, stored_stage=key.split(".", 1)[1])
    if prev is not None:
        dv = fn.items[prev]["value"] - fn.items[id_]["value"]
        did = f"dropped_{i}"
        fn.add(did, f"Dropped: {dropped_why[i - 1]}", value=dv, source=f"derived: {prev} − {id_}", kind="derived", **CNT)
        st["dropped_item"] = did
    stages.append(st)
    prev = id_
assert fn.items["dropped_3"]["value"] == get("S3:missingness.a1c_missing") == 297
fn.groups["stages"] = stages
fn.add("prev_w", "Positive, weighted to US adults", key="S1:prevalence_comb.weighted", plan="14.0 %", **pct_fmt())
fn.add("prev_lo", "Weighted prevalence, CI low", key="S1:prevalence_comb.ci_low", **pct_fmt())
fn.add("prev_hi", "Weighted prevalence, CI high", key="S1:prevalence_comb.ci_high", **pct_fmt())
fn.interval("prev_ci", "Weighted prevalence of the combined label (95 % CI, jackknife)", "prev_w", "prev_lo", "prev_hi")
fn.add("prev_unw", "Positive, unweighted", key="S1:prevalence_comb.unweighted", **pct_fmt())
fn.add("pos_eall", "Positives, All adults", key="S1:labels.L_comb", plan="971", **CNT)
fn.add("pos_self", "Self-reported diagnosis", key="S1:labels.L_self", plan="819", **CNT)
fn.add("pos_a1c", "HbA1c ≥ 6.5 %", key="S3:blanket_recode.a1c_positives", plan="721", **CNT)
assert fn.items["pos_a1c"]["value"] == get("S1:labels.L_A1c")
fn.add("n_screen", "Screening group (not yet diagnosed)", key="S1:e_screen.rows", plan="4,911", **CNT)
fn.add("pos_screen", "Screening group positives", key="S1:e_screen.positives", plan="152", **CNT)
fn.add("resp_interview", "Interview response rate", key="S1:response_rates.interview", **pct_fmt())
fn.add("resp_mec", "Examination response rate", key="S1:response_rates.mec", **pct_fmt())
fn.add("a1c_cut", "HbA1c diagnostic threshold", value=6.5, fmt=".1f", unit=" %", kind="definition",
       source="definition: src/labels.py A1C_CUT = config.HBA1C_DIABETES (6.5 %)", plan="6.5 %")
fn.groups["label_definition"] = "positive = self-reported diagnosis OR HbA1c ≥ 6.5 % (src/labels.py: L_comb)"

# ----------------------------------------------------------------------------------------------------------
# blanket_recode.json  (visual 3, scenes 8-9, 14)
# ----------------------------------------------------------------------------------------------------------
PLAIN_VAR = {
    "BPXODI1": "Diastolic BP (reading 1)", "BPXODI2": "Diastolic BP (reading 2)", "BPXODI3": "Diastolic BP (reading 3)",
    "BPXOSY1": "Systolic BP (reading 1)", "BPXOSY2": "Systolic BP (reading 2)", "BPXOSY3": "Systolic BP (reading 3)",
    "BPXOPLS1": "Pulse (reading 1)", "BPXOPLS2": "Pulse (reading 2)", "BPXOPLS3": "Pulse (reading 3)",
    "RIDAGEYR": "Age", "BMXWAIST": "Waist circumference", "LBDHDD": "HDL cholesterol", "LBXGH": "HbA1c",
    "BMXHIP": "Hip circumference", "BMXWT": "Weight", "LBXTC": "Total cholesterol", "BMXHT": "Height",
    "INDFMPIR": "Income-to-poverty ratio", "BMXBMI": "BMI", "BMXARMC": "Arm circumference",
    # questionnaire items hit by the blanket rule (genuine refused / don't-know codes)
    "HIQ011": "Health insurance", "HUQ030": "Usual place of care", "BPQ020": "Told high blood pressure",
    "BPQ080": "Told high cholesterol", "SMQ020": "Smoked 100+ cigarettes", "DMDEDUC2": "Education",
}
# every name must belong to a variable of config/variable_spec.csv
assert all(v in SPEC for v in PLAIN_VAR), [v for v in PLAIN_VAR if v not in SPEC]
FAMILY = {"BPXODI": "Diastolic BP", "BPXOSY": "Systolic BP", "BPXOPL": "Pulse"}

br = new_file("blanket_recode", "The struck 7.0", "8, 9, 14")
br.add("destroyed", "Valid cells destroyed", key="S3:blanket_recode.valid_cells_destroyed_cohort", plan="1,496", **CNT)
br.add("genuine", "Genuine codes caught", key="S3:blanket_recode.questionnaire_only_cells", plan="57", **CNT)
br.add("harm_gain", "Harm per genuine code caught", value=get("S3:blanket_recode.valid_cells_destroyed_cohort")
       / get("S3:blanket_recode.questionnaire_only_cells"), fmt=".0f", unit="×", kind="derived",
       source="derived: valid_cells_destroyed_cohort / questionnaire_only_cells (notebook §3.4: 'about 26-fold')",
       note="1,496 / 57 = 26.2")
br.add("a1c_lost", "HbA1c positives erased", key="S3:blanket_recode.a1c_positives_lost", plan="29", **CNT)
br.add("a1c_pos", "HbA1c positives", key="S3:blanket_recode.a1c_positives", plan="721", **CNT)
br.add("a1c_lost_share", "Share of HbA1c positives erased", key="S3:blanket_recode.a1c_lost_share", **pct_fmt())
br.add("flips", "Flipped to negative (combined label)", key="S3:blanket_recode.l_comb_flips", plan="6", **CNT)
br.add("lcomb_pos", "Combined-label positives", key="S3:blanket_recode.l_comb_positives", **CNT)
hit = csv_row("results/S3/blanket_damage.csv", var="LBXGH")["values_hit"]
hits = {k.strip(): int(v) for k, v in (p.split(":") for p in hit.split(","))}
assert hits == {"7": 28, "9": 1}, hits
br.add("a1c_lost_7_0", "HbA1c values of exactly 7.0 % erased", value=hits["7"], fmt=".0f", kind="stored-csv",
       source="results/S3/blanket_damage.csv :: var=LBXGH → values_hit '7:28, 9:1'", plan="28")
br.add("a1c_lost_9_0", "HbA1c values of exactly 9.0 % erased", value=hits["9"], fmt=".0f", kind="stored-csv",
       source="results/S3/blanket_damage.csv :: var=LBXGH → values_hit '7:28, 9:1'", plan="1")
assert hits["7"] + hits["9"] == br.items["a1c_lost"]["value"]
assert br.items["a1c_pos"]["value"] == get("S3:blanket_recode.a1c_positives")
per_var = get("S3:blanket_recode.per_variable")
assert sum(per_var.values()) == br.items["destroyed"]["value"], sum(per_var.values())
damage = {r["var"]: r["values_hit"] for r in read_csv("results/S3/blanket_damage.csv")}
pv_list = []
for var, n_ in per_var.items():
    iid = f"var_{var}"
    br.add(iid, PLAIN_VAR[var], key=f"S3:blanket_recode.per_variable.{var}", **CNT)
    pv_list.append(dict(item=iid, var=var, name=PLAIN_VAR[var], values_hit=damage[var] or None,
                        zero=bool(n_ == 0), spec_note=SPEC[var]["note"]))
br.groups["per_variable"] = pv_list  # stored order = descending damage
fam: dict[str, int] = {}
for var, n_ in per_var.items():
    f_ = FAMILY.get(var[:6])
    if f_:
        fam[f_] = fam.get(f_, 0) + n_
fam_ids = []
for name_, v_ in sorted(fam.items(), key=lambda kv: -kv[1]):
    iid = "family_" + name_.split()[0].lower() + ("_" + name_.split()[1].lower() if len(name_.split()) > 1 else "")
    br.add(iid, f"{name_} (3 readings)", value=v_, fmt=",.0f", kind="derived",
           source="derived: sum of per_variable damage over the three readings")
    fam_ids.append(iid)
br.groups["families"] = fam_ids
gen = get("S3:blanket_recode.questionnaire_only_per_item")
assert sum(gen.values()) == br.items["genuine"]["value"]
gl = []
for var, n_ in gen.items():
    iid = f"code_{var}"
    br.add(iid, PLAIN_VAR[var], key=f"S3:blanket_recode.questionnaire_only_per_item.{var}", **CNT)
    gl.append(dict(item=iid, var=var, name=PLAIN_VAR[var]))
br.groups["genuine_codes_per_item"] = gl
br.groups["rule"] = "Rule: 7, 9, 77, 99 → missing, in every column (illustrative cell values 77 and 99 on the slide are examples)"
br.groups["note_562"] = ("S3:sentinel_audit.cells_recoded_cohort = 562 counts the genuine codes recoded by the variable-by-variable rule "
                         "over all 25 sentinel variables; the video's 57 is the narrower 'questionnaire_only_cells' (items the blanket rule "
                         "catches correctly). Do not mix the two.")

# ----------------------------------------------------------------------------------------------------------
# leak_gate.json  (visual 4, scene 18, 27)    -- schema agreed with vkit: {"items": {...}}
# ----------------------------------------------------------------------------------------------------------
lg = new_file("leak_gate", "Leak gate", "18, 26, 27")
lg.add("auc_m0_eall", "Naive (M0)", key="S7:headline.auc_M0_eall_T1", plan="0.961", **AUC3)
lg.add("auc_m1_eall", "Minimal (M1)", key="S7:headline.auc_M1_eall_T1", plan="0.828", **AUC3)
lg.add("diff_eall", "Paired difference, All adults", key="S7:leak_gate.T1_E-ALL.est", plan="−0.131", **DAUC)
lg.add("diff_eall_lo", "Paired difference CI low", key="S7:leak_gate.T1_E-ALL.lo", plan="−0.148", **DAUC)
lg.add("diff_eall_hi", "Paired difference CI high", key="S7:leak_gate.T1_E-ALL.hi", plan="−0.114", **DAUC)
lg.interval("diff_eall_ci", "Minimal (M1) − Naive (M0), All adults, paired across folds", "diff_eall", "diff_eall_lo", "diff_eall_hi")
lg.add("diff_escreen", "Screening group", key="S7:leak_gate.T1_E-SCREEN.est", plan="−0.072", **DAUC)
lg.add("diff_escreen_lo", "Screening group CI low", key="S7:leak_gate.T1_E-SCREEN.lo", **DAUC)
lg.add("diff_escreen_hi", "Screening group CI high", key="S7:leak_gate.T1_E-SCREEN.hi", **DAUC)
lg.interval("diff_escreen_ci", "Minimal (M1) − Naive (M0), Screening group", "diff_escreen", "diff_escreen_lo", "diff_escreen_hi")
lg.add("bars_gap_rounded", "Gap between the two rounded bars", value=round(0.961 - 0.828, 3), fmt=".3f", kind="derived",
       source="derived: 0.961 − 0.828 (rounded bar labels)", plan="0.133",
       note="Plan scene 18: two bars subtract to 0.133; the slide labels the 0.131 as 'paired'.")
lg.add("bars_gap_unrounded", "Gap between the two bars, unrounded", value=get("S7:headline.auc_M0_eall_T1") - get("S7:headline.auc_M1_eall_T1"),
       fmt=".3f", kind="derived", source="derived: auc_M0_eall_T1 − auc_M1_eall_T1",
       note="0.1322 pooled vs 0.1308 mean of paired fold differences (stored 'est').")
lg.add("axis_start", "AUC axis starts at", value=0.5, fmt=".1f", kind="definition", source="definition: AUC of a coin flip")
# the three item groups removed by the availability rule (governance/claims.csv C01 wording; variables from results/S1/availability_rule.csv)
avail = {r["variable"]: r for r in read_csv("results/S1/availability_rule.csv")}
REMOVED = [
    ("removed_treatment", "treatment", ["DIQ050", "DIQ070", "DID060"], "taking insulin; taking diabetic pills; duration of insulin use"),
    ("removed_history", "diagnosis history", ["DID040"], "age at diagnosis"),
    ("removed_glucose", "glucose testing", ["LBXGLU", "DIQ160", "DIQ180"],
     "fasting glucose; told prediabetes (consequence of a glucose test); blood sugar tested in past 3 years"),
]
for id_, lab, vars_, desc in REMOVED:
    assert all(avail[v]["admissible"] == "N" for v in vars_), vars_
    it = lg.add(id_, lab, value=len(vars_), fmt=".0f", kind="stored-csv",
                source=f"results/S1/availability_rule.csv :: admissible=N for {', '.join(vars_)}; group wording from governance/claims.csv C01",
                note=desc)
    it["variables"] = vars_
    it["variable_reasons"] = {v: avail[v]["reason"] for v in vars_}
lg.groups["removed_order"] = [r[0] for r in REMOVED]
assert "treatment, diagnosis history, glucose testing" in (ROOT / "governance/claims.csv").read_text(encoding="utf-8")
lg.notes.append("Grouping of variables into the three claim words is ours (C01 names the groups, availability_rule.csv names the variables).")

# ----------------------------------------------------------------------------------------------------------
# tree.json  (visual 5, scene 19)
# ----------------------------------------------------------------------------------------------------------
tr = new_file("tree", "Tree and the 50", "19")
roots = get("S7:tree_roots.M0")
assert roots["variable"] == "DIQ070" and roots["role"] == "leak" and roots["level2"] == ["DIQ180_2.0", "DID040"]
tr.add("root_variable", "Root split: taking diabetes pills?", key="S7:tree_roots.M0.variable", fmt=None, display="taking diabetes pills?")
tr.add("root_feature", "Root feature (design-matrix column)", key="S7:tree_roots.M0.root_feature", fmt=None, display=roots["root_feature"])
tr.add("root_role", "Root role in the availability rule", key="S7:tree_roots.M0.role", fmt=None, display="leaked treatment item")
tr.add("root_threshold", "Root threshold (0/1 indicator)", key="S7:tree_roots.M0.threshold", fmt=".2f")
tr.add("level2_left", "Second-level split, left branch", value=roots["level2"][0], fmt=None, display="blood-glucose test in past 3 years",
       kind="stored", source="results/metrics_S7.json :: tree_roots.M0.level2[0] (DIQ180_2.0)")
tr.add("level2_right", "Second-level split, right branch", value=roots["level2"][1], fmt=None, display="age at diabetes diagnosis",
       kind="stored", source="results/metrics_S7.json :: tree_roots.M0.level2[1] (DID040)")
tr.add("did040_missing", "Age at diagnosis: never asked", key="S7:tree_m0.did040_missing_share", plan="86 %", **pct_fmt(".0f"))
tr.add("did040_fill", "Imputed with the median", key="S7:tree_m0.did040_fill", plan="50", fmt=".0f")
cap = (ROOT / "figures/S7_tree_m0.txt").read_text(encoding="utf-8")
mt = re.search(r"splits at ([\d.]+) / ([\d.]+) on age at diagnosis", cap)
assert mt, cap
thr_lo, thr_hi = float(mt.group(1)), float(mt.group(2))
assert thr_lo < tr.items["did040_fill"]["value"] < thr_hi
for id_, lab, v_ in (("did040_split_lo", "Split just below the imputed value", thr_lo), ("did040_split_hi", "Split just above the imputed value", thr_hi)):
    tr.add(id_, lab, value=v_, fmt=".1f", kind="figure-text", source="figures/S7_tree_m0.txt (figure caption; thresholds are not in metrics_S7.json)")
# full node structure from the executed notebook output (export_text of the depth-3 tree); not stored under results/
nb = json.loads((ROOT / "notebooks/executed/06_experiments.ipynb").read_text(encoding="utf-8"))
tree_txt = None
for c in nb["cells"]:
    for o in c.get("outputs", []):
        t = "".join(o.get("text", []))
        if t.lstrip().startswith("|--- taking diabetic pills"):
            tree_txt = t
assert tree_txt, "tree export_text output not found in notebooks/executed/06_experiments.ipynb"
stack: list[tuple[int, dict]] = []
root_node = {"children": []}
for line in tree_txt.splitlines():
    m = re.match(r"^((?:\|   )*)\|--- (.*)$", line)
    if not m:
        continue
    depth = len(m.group(1)) // 4
    txt = m.group(2)
    mw = re.match(r"weights: \[([\d.]+), ([\d.]+)\] class: (\d)", txt)
    node = {"test": None, "children": []}
    ma = re.match(r"(.*): no (<=|>)\s+0\.50$", txt)
    if ma:  # sklearn splits on the 'no' indicator: '<= 0.50' means the answer is yes
        node["question"] = ma.group(1)
        node["answer"] = "yes" if ma.group(2) == "<=" else "no"
    parent = root_node if depth == 0 else stack[depth - 1][1]
    if mw:
        parent["leaf"] = dict(n_no_diabetes=float(mw.group(1)), n_diabetes=float(mw.group(2)), predicted_class=int(mw.group(3)))
        continue
    node["test"] = txt
    parent["children"].append(node)
    stack = stack[:depth] + [(depth, node)]
leaf_n = sum(1 for _ in re.finditer(r"weights:", tree_txt))
assert root_node["children"][0]["test"].startswith("taking diabetic pills: no <= 0.50") and len(root_node["children"]) == 2
assert "age at diabetes diagnosis <= 49.50" in tree_txt and "age at diabetes diagnosis <= 50.50" in tree_txt
tr.groups["nodes"] = dict(source="notebooks/executed/06_experiments.ipynb (export_text of the depth-3, min-leaf-50 tree on the M0 frame, training part); "
                                 "not stored under results/", n_leaves=leaf_n, tree=root_node["children"])
tr.notes.append("Thresholds 49.5 / 50.5 and the node structure are not in results/metrics_S7.json; they come from the figure caption and the executed notebook.")

# ----------------------------------------------------------------------------------------------------------
# label_split.json  (visual 6, scene 16-17)
# ----------------------------------------------------------------------------------------------------------
ls = new_file("label_split", "Label split", "16, 17")
ls.add("both", "Doctor-told and HbA1c ≥ 6.5 %", key="S1:strata_3x3.D_uncontrolled", plan="569", **CNT)
ls.add("self_only", "Doctor-told, HbA1c below 6.5 %", key="S1:strata_3x3.D_controlled", plan="250", **CNT)
ls.add("a1c_only", "HbA1c ≥ 6.5 %, not told", key="S1:strata_3x3.Undiagnosed", plan="152", **CNT)
ls.add("neither", "Neither", key="S1:strata_3x3.NonDiabetic", **CNT)
ls.add("self", "Told by a doctor", key="S1:labels.L_self", plan="819", **CNT)
ls.add("a1c", "HbA1c ≥ 6.5 %", key="S3:blanket_recode.a1c_positives", plan="721", **CNT)
assert ls.items["a1c"]["value"] == get("S1:labels.L_A1c")
ls.add("union", "Positive (either)", key="S1:labels.L_comb", plan="971", **CNT)
ls.add("masked", "Told, but HbA1c below 6.5 %", key="S5:masking.below_6_5", plan="250", **CNT)
ls.add("masked_med", "On insulin or pills", key="S5:masking.below_6_5_on_med", plan="165", **CNT)
ls.add("masked_untreated", "Untreated", key="S5:masking.below_6_5_untreated", **CNT)
ls.add("masked_share", "Share of told whose HbA1c is below 6.5 %", key="S5:masking.below_6_5_share", **pct_fmt())
ls.add("kappa_unw", "Cohen's kappa, unweighted", key="S5:labels.agreement_unweighted.kappa", plan="0.70", fmt=".2f")
ls.add("kappa_w", "Cohen's kappa, survey-weighted", key="S5:labels.agreement_weighted.kappa.est", fmt=".2f")
ls.add("kappa_w_lo", "Cohen's kappa, survey-weighted, CI low", key="S5:labels.agreement_weighted.kappa.ci_low", fmt=".2f")
ls.add("kappa_w_hi", "Cohen's kappa, survey-weighted, CI high", key="S5:labels.agreement_weighted.kappa.ci_high", fmt=".2f")
ls.interval("kappa_w_ci", "Cohen's kappa, survey-weighted (95 % CI)", "kappa_w", "kappa_w_lo", "kappa_w_hi")
ls.add("circle_ratio", "Radius ratio of the two circles (HbA1c / told)", value=math.sqrt(get("S1:labels.L_A1c") / get("S1:labels.L_self")),
       fmt=".3f", kind="derived", source="derived: sqrt(L_A1c / L_self); plan section 7 item 6 (0.938)", plan="0.938")
assert ls.items["both"]["value"] + ls.items["self_only"]["value"] == ls.items["self"]["value"]
assert ls.items["both"]["value"] + ls.items["a1c_only"]["value"] == ls.items["a1c"]["value"]
assert ls.items["both"]["value"] + ls.items["self_only"]["value"] + ls.items["a1c_only"]["value"] == ls.items["union"]["value"]
assert ls.items["masked_med"]["value"] + ls.items["masked_untreated"]["value"] == ls.items["masked"]["value"] == ls.items["self_only"]["value"]
assert get("S5:labels.confusion.self1_a1c1") == ls.items["both"]["value"]
ls.notes.append("kappa is an agreement score, not '70 percent agree' (plan scene 16).")

# ----------------------------------------------------------------------------------------------------------
# undiagnosed.json  (visual 7, scene 17)
# ----------------------------------------------------------------------------------------------------------
ud = new_file("undiagnosed", "Who is undiagnosed", "17")
RD = "S5:undiagnosed_inequality.risk_differences_pp."
ud.add("rd_uninsured", "Uninsured − insured", key=RD + "uninsured - insured.rd_pp", plan="+23.2", **PP)
ud.add("rd_uninsured_lo", "CI low", key=RD + "uninsured - insured.ci_low_pp", plan="6.2", fmt=".1f")
ud.add("rd_uninsured_hi", "CI high", key=RD + "uninsured - insured.ci_high_pp", plan="40.1", fmt=".1f")
ud.interval("rd_uninsured_ci", "Undiagnosed share among HbA1c ≥ 6.5 %: uninsured − insured (pp, 95 % CI)", "rd_uninsured", "rd_uninsured_lo", "rd_uninsured_hi")
PR = "S5:undiagnosed_inequality.proportions."
ud.add("n_uninsured", "Uninsured with HbA1c ≥ 6.5 % (n)", key=PR + "uninsured.n", plan="49", **CNT)
ud.add("events_uninsured", "Uninsured, undiagnosed (n)", key=PR + "uninsured.n_events", **CNT)
ud.add("share_uninsured", "Uninsured: undiagnosed share", key=PR + "uninsured.est", **pct_fmt())
ud.add("n_insured", "Insured with HbA1c ≥ 6.5 % (n)", key=PR + "insured.n", **CNT)
ud.add("events_insured", "Insured, undiagnosed (n)", key=PR + "insured.n_events", **CNT)
ud.add("share_insured", "Insured: undiagnosed share", key=PR + "insured.est", **pct_fmt())
ud.add("rd_noplace", "No usual place of care − usual place", key=RD + "no usual place - usual place.rd_pp", **PP)
ud.add("rd_noplace_lo", "CI low", key=RD + "no usual place - usual place.ci_low_pp", fmt=".1f")
ud.add("rd_noplace_hi", "CI high", key=RD + "no usual place - usual place.ci_high_pp", fmt=".1f")
ud.interval("rd_noplace_ci", "No usual place − usual place (pp, 95 % CI)", "rd_noplace", "rd_noplace_lo", "rd_noplace_hi")
ud.add("rd_asian", "NH Asian − NH White", key=RD + "NH Asian - NH White.rd_pp", **PP)
ud.add("rd_asian_lo", "CI low", key=RD + "NH Asian - NH White.ci_low_pp", fmt=".1f")
ud.add("rd_asian_hi", "CI high", key=RD + "NH Asian - NH White.ci_high_pp", fmt=".1f")
ud.interval("rd_asian_ci", "NH Asian − NH White (pp, 95 % CI)", "rd_asian", "rd_asian_lo", "rd_asian_hi")
ud.add("or_uninsured", "Adjusted odds ratio, uninsured (age, sex, income)", key="S5:undiagnosed_inequality.adjusted_logit.uninsured.OR", fmt=".2f")
ud.add("undiagnosed_n", "Undiagnosed adults with HbA1c ≥ 6.5 %", key="S5:undiagnosed_meaning.undiagnosed", **CNT)
ud.groups["flags"] = {g: dict(n=get(PR + f"{g}.n"), nchs_status=get(PR + f"{g}.nchs_status"), flags=get(PR + f"{g}.flags"))
                      for g in ("uninsured", "insured", "no usual place", "usual place", "NH Asian", "NH White")}
ud.notes.append("Association, exploratory; the uninsured estimate does not meet the NCHS reliability standard (n = 49, CI width 0.39).")

# ----------------------------------------------------------------------------------------------------------
# recognition.json  (visual 8, scene 23)
# ----------------------------------------------------------------------------------------------------------
rc = new_file("recognition", "All adults vs Screening group", "23")
rc.add("auc_eall", "All adults", key="S7:headline.auc_S_eall_T1", plan="0.836", **AUC3)
rc.add("auc_escreen", "Screening group", key="S7:headline.auc_S_escreen_T1", plan="0.781", **AUC3)
rc.add("gap", "Gap", key="S7:headline.eall_minus_escreen_S_T1.est", plan="+0.055", **DAUC)
rc.add("gap_lo", "Gap CI low", key="S7:headline.eall_minus_escreen_S_T1.lo", plan="0.028", **AUC3)
rc.add("gap_hi", "Gap CI high", key="S7:headline.eall_minus_escreen_S_T1.hi", plan="0.086", **AUC3)
rc.interval("gap_ci", "All adults − Screening group, Systematic (S) AUC", "gap", "gap_lo", "gap_hi")
rc.add("known_share", "Positives already diagnosed", key="S1:labels.known_share_of_comb", plan="84 %", **pct_fmt(".0f"))
rc.add("screen_share", "Positives in the Screening group", value=1 - get("S1:labels.known_share_of_comb"), fmt=".0f", scale=100, unit=" %",
       kind="derived", source="derived: 1 − known_share_of_comb (= S5:labels.self_missed_share)")
assert abs(rc.items["screen_share"]["value"] - get("S5:labels.self_missed_share")) < 1e-12
assert abs(get("S1:labels.known_share_of_comb") - 1 + get("S1:e_screen.positives") / get("S1:labels.L_comb")) < 1e-12
rc.add("pos_eall", "Positives, All adults", key="S1:labels.L_comb", **CNT)
rc.add("pos_screen", "Positives, Screening group", key="S1:e_screen.positives", **CNT)
rc.add("axis_start", "AUC axis starts at", value=0.5, fmt=".1f", kind="definition", source="definition: AUC of a coin flip")

# ----------------------------------------------------------------------------------------------------------
# prep_band.json  (visual 9, scenes 21, 26, 27)
# ----------------------------------------------------------------------------------------------------------
pb = new_file("prep_band", "Preparation against the band", "21, 26, 27")
pb.add("d_auc", "Systematic (S) − Minimal (M1)", key="S7:headline.S_minus_M1_T1_eall.est", plan="+0.008", **DAUC)
pb.add("d_auc_lo", "CI low", key="S7:headline.S_minus_M1_T1_eall.lo", plan="0.000", **AUC3)
pb.add("d_auc_hi", "CI high", key="S7:headline.S_minus_M1_T1_eall.hi", plan="0.016", **AUC3)
pb.interval("d_auc_ci", "AUC change, All adults, paired across folds", "d_auc", "d_auc_lo", "d_auc_hi")
pb.add("mdd", "Smallest detectable difference", key="S7:headline.S_minus_M1_T1_eall.mdd", plan="0.011", **AUC3)
pb.add("sesoi", "Margin fixed in advance (+/-)", key="S7:scoreboard_detail[hyp_id=H2b&sub=(a) AUC&role=primary&pop=E-ALL&tier=1].sesoi",
       plan="0.01", fmt=".2f", note="hypotheses.md H2b: absolute delta AUC below 0.01")
pb.add("verdict", "Locked verdict", key="S7:scoreboard_detail[hyp_id=H2b&sub=(a) AUC&role=primary&pop=E-ALL&tier=1].verdict", fmt=None,
       display="inconclusive")
pb.add("d_auc_c", "Systematic (S) − Minimal-with-P02 (M1c), post-audit", key="S10:h2b.postaudit.S_minus_M1c_eall.est", **DAUC)
pb.add("d_auc_c_lo", "CI low", key="S10:h2b.postaudit.S_minus_M1c_eall.lo", **DAUC)
pb.add("d_auc_c_hi", "CI high", key="S10:h2b.postaudit.S_minus_M1c_eall.hi", **DAUC)
pb.interval("d_auc_c_ci", "Post-audit row: S − M1c, All adults", "d_auc_c", "d_auc_c_lo", "d_auc_c_hi")
pb.add("d_auc_c_verdict", "Post-audit verdict", key="S10:h2b.postaudit.S_minus_M1c_eall.verdict", fmt=None, display="inconclusive")
pb.add("d_auc_screen", "Screening group: S − M1", key="S7:scoreboard_detail[hyp_id=H2b&sub=(a) AUC&role=secondary&pop=E-SCREEN&tier=1].est", **DAUC)
pb.add("d_auc_screen_lo", "CI low", key="S7:scoreboard_detail[hyp_id=H2b&sub=(a) AUC&role=secondary&pop=E-SCREEN&tier=1].lo", **DAUC)
pb.add("d_auc_screen_hi", "CI high", key="S7:scoreboard_detail[hyp_id=H2b&sub=(a) AUC&role=secondary&pop=E-SCREEN&tier=1].hi", **DAUC)
pb.interval("d_auc_screen_ci", "AUC change, Screening group", "d_auc_screen", "d_auc_screen_lo", "d_auc_screen_hi")
pb.add("axis_min", "Difference axis, minimum", value=-0.04, fmt="+.2f", kind="definition", source="definition: plan scene 21 (axis −0.04 … +0.04, reused in scene 24)")
pb.add("axis_max", "Difference axis, maximum", value=0.04, fmt="+.2f", kind="definition", source="definition: plan scene 21")

# ----------------------------------------------------------------------------------------------------------
# care_flip.json  (visual 10, scene 24)
# ----------------------------------------------------------------------------------------------------------
cf = new_file("care_flip", "Care traces flip", "24")
cf.add("eall", "All adults", key="S7:headline.minus_care_eall.est", plan="−0.016", **DAUC)
cf.add("eall_lo", "CI low", key="S7:headline.minus_care_eall.lo", **DAUC)
cf.add("eall_hi", "CI high", key="S7:headline.minus_care_eall.hi", **DAUC)
cf.interval("eall_ci", "AUC change without care traces, All adults", "eall", "eall_lo", "eall_hi")
cf.add("escreen", "Screening group", key="S7:headline.minus_care_escreen.est", plan="+0.019", **DAUC)
cf.add("escreen_lo", "CI low", key="S7:headline.minus_care_escreen.lo", plan="0.004", **AUC3)
cf.add("escreen_hi", "CI high", key="S7:headline.minus_care_escreen.hi", plan="0.034", **AUC3)
cf.interval("escreen_ci", "AUC change without care traces, Screening group", "escreen", "escreen_lo", "escreen_hi")
cf.add("verdict_eall", "Locked verdict, All adults", key="S7:scoreboard_detail[hyp_id=H2c&sub=(ii) minus care, E-ALL&role=primary].verdict", fmt=None, display="supported")
cf.add("verdict_escreen", "Locked verdict, Screening group", key="S7:scoreboard_detail[hyp_id=H2c&sub=(ii) minus care, E-SCREEN&role=primary].verdict", fmt=None, display="inconclusive")
cf.add("sesoi", "Margin fixed in advance (+/-)", key="S7:scoreboard_detail[hyp_id=H2c&sub=(ii) minus care, E-SCREEN&role=primary].sesoi", fmt=".2f")
care = [v for v, r in avail.items() if r["admissible"] == "T1" and "care-contact trace" in r["reason"]]
assert care == ["BPQ020", "BPQ080"], care
REMOVED_CARE = [("BPQ020", "told high blood pressure"), ("BPQ080", "told high cholesterol")]
for v, lab in REMOVED_CARE:
    it = cf.add(f"removed_{v}", lab, value=1, fmt=".0f", kind="stored-csv",
                source=f"results/S1/availability_rule.csv :: variable={v}, reason '{avail[v]['reason']}'")
    it["variable"] = v
cf.groups["removed_order"] = [f"removed_{v}" for v, _ in REMOVED_CARE]
cf.notes.append("The Screening-group lower bound 0.004 lies inside the +/-0.01 band (verdict inconclusive); do not pulse it.")

# ----------------------------------------------------------------------------------------------------------
# tpr_100.json  (visual 11, scene 20)
# ----------------------------------------------------------------------------------------------------------
tp = new_file("tpr_100", "100 diabetics", "20")
tp.add("tpr_diag", "Already diagnosed", key="S8:gap_decomposition.tpr_diagnosed", plan="0.70", fmt=".2f")
tp.add("tpr_undx", "Screening group", key="S8:gap_decomposition.tpr_undiagnosed", plan="0.52", fmt=".2f")
tp.add("per100_diag", "Flagged per 100 already diagnosed", value=get("S8:gap_decomposition.tpr_diagnosed") * 100, fmt=".0f", kind="derived",
       source="derived: round(tpr_diagnosed * 100); illustration per 100, not actual counts", plan="70")
tp.add("per100_undx", "Flagged per 100 in the Screening group", value=get("S8:gap_decomposition.tpr_undiagnosed") * 100, fmt=".0f", kind="derived",
       source="derived: round(tpr_undiagnosed * 100); illustration per 100, not actual counts", plan="52")
tp.add("per100_gap", "Positions that differ per 100", value=round(get("S8:gap_decomposition.tpr_diagnosed") * 100) - round(get("S8:gap_decomposition.tpr_undiagnosed") * 100),
       fmt=".0f", kind="derived", source="derived: 70 − 52", plan="18")
tp.add("spec", "Specificity of the shared cut-off", key="S8:spec", plan="0.80", fmt=".2f")
tp.add("n_diag_train", "Diagnosed positives behind the 0.70 (training part)", value=get("S8:label_matrix.strata_train.D_uncontrolled") + get("S8:label_matrix.strata_train.D_controlled"),
       fmt=",.0f", kind="derived", source="derived: S8:label_matrix.strata_train D_uncontrolled + D_controlled")
tp.add("n_undx_train", "Screening-group positives behind the 0.52 (training part)", key="S8:label_matrix.strata_train.Undiagnosed", **CNT)
assert tp.items["n_diag_train"]["value"] + tp.items["n_undx_train"]["value"] == get("S8:setup.n_pos") == 777
assert tp.items["n_undx_train"]["value"] == get("S8:setup.n_pos_escreen")
assert abs(get("S8:gap_decomposition.tpr_undiagnosed") - get("S8:overall_tpr_escreen_t1")) < 1e-12
tp.groups["label"] = "one shared cut-off · specificity 0.80 · rates per 100"
tp.notes.append("Per-100 dots are the rates 0.70 and 0.52 scaled; they are not people counts.")

# ----------------------------------------------------------------------------------------------------------
# brier.json  (scene 22)
# ----------------------------------------------------------------------------------------------------------
bs = new_file("brier", "Calibration and Brier", "22")
HB = "S7:scoreboard_detail[hyp_id=H2b&sub=(b) Brier&role=primary]"
CB = "S7:scoreboard_detail[hyp_id=B6a&sub=(b) Brier&role=primary]"
bs.add("d_brier", "Systematic (S) − Minimal (M1), Brier", key=HB + ".est", plan="+0.074", **DAUC)
bs.add("d_brier_lo", "CI low", key=HB + ".lo", **DAUC)
bs.add("d_brier_hi", "CI high", key=HB + ".hi", **DAUC)
bs.interval("d_brier_ci", "Brier change, S − M1, All adults (positive = worse)", "d_brier", "d_brier_lo", "d_brier_hi")
bs.add("d_brier_cw", "Class weights alone (S − S without weights), Brier", key=CB + ".est", plan="+0.076", **DAUC)
bs.add("d_brier_cw_lo", "CI low", key=CB + ".lo", **DAUC)
bs.add("d_brier_cw_hi", "CI high", key=CB + ".hi", **DAUC)
bs.interval("d_brier_cw_ci", "Brier change from class weights alone", "d_brier_cw", "d_brier_cw_lo", "d_brier_cw_hi")
PA = "S7:pure_preparation_S_B6a_vs_M1[pop=E-ALL&metric={m}]"
bs.add("nocw_auc", "S without class weights vs M1, AUC", key=PA.format(m="roc_auc") + ".diff", plan="+0.007", **DAUC)
bs.add("nocw_auc_lo", "CI low", key=PA.format(m="roc_auc") + ".lo", **DAUC)
bs.add("nocw_auc_hi", "CI high", key=PA.format(m="roc_auc") + ".hi", **DAUC)
bs.interval("nocw_auc_ci", "AUC change, S without class weights vs M1", "nocw_auc", "nocw_auc_lo", "nocw_auc_hi")
bs.add("nocw_brier", "S without class weights vs M1, Brier", key=PA.format(m="brier") + ".diff", plan="−0.002", **DAUC)
bs.add("nocw_brier_lo", "CI low", key=PA.format(m="brier") + ".lo", **DAUC)
bs.add("nocw_brier_hi", "CI high", key=PA.format(m="brier") + ".hi", **DAUC)
bs.interval("nocw_brier_ci", "Brier change, S without class weights vs M1", "nocw_brier", "nocw_brier_lo", "nocw_brier_hi")
PL = "S7:postlock_m1_sensitivity.rows[variant=M1 stored (lbfgs, max_iter 5,000)&a={a}&pop=E-ALL&metric=brier]"
bs.add("brier_m1", "Minimal (M1)", key=PL.format(a="S") + ".value_variant", fmt=".3f")
bs.add("brier_s", "Systematic (S)", key=PL.format(a="S") + ".value_a", fmt=".3f")
bs.add("brier_s_nocw", "S without class weights", key=PL.format(a="S-B6a") + ".value_a", fmt=".3f")
cal = {(r["arm"], r["pop"]): r for r in read_csv("results/S7/calibration.csv")}
for arm_, aid in (("M1", "m1"), ("S", "s"), ("S-B6a", "s_nocw")):
    r = cal[(arm_, "E-ALL")]
    nm = {"m1": "Minimal (M1)", "s": "Systematic (S)", "s_nocw": "S without class weights"}[aid]
    bs.add(f"slope_{aid}", f"{nm}: calibration slope", value=float(r["cal_slope"]), fmt=".2f", kind="stored-csv",
           source=f"results/S7/calibration.csv :: arm={arm_}, pop=E-ALL → cal_slope")
    bs.add(f"citl_{aid}", f"{nm}: calibration-in-the-large", value=float(r["cal_citl"]), fmt="+.2f", kind="stored-csv",
           source=f"results/S7/calibration.csv :: arm={arm_}, pop=E-ALL → cal_citl")
    bs.add(f"meanp_{aid}", f"{nm}: mean predicted risk", value=float(r["mean_p"]), fmt=".1f", scale=100, unit=" %", kind="stored-csv",
           source=f"results/S7/calibration.csv :: arm={arm_}, pop=E-ALL → mean_p")
bs.add("prevalence", "Observed prevalence (training part)", value=float(cal[("S", "E-ALL")]["prevalence"]), fmt=".1f", scale=100, unit=" %", kind="stored-csv",
       source="results/S7/calibration.csv :: arm=S, pop=E-ALL → prevalence")
# difference of the pooled arm Briers vs mean of the paired fold differences: close, not identical (4e-4)
assert abs(bs.items["brier_s"]["value"] - bs.items["brier_m1"]["value"] - bs.items["d_brier"]["value"]) < 1e-3
assert abs(float(cal[("S", "E-ALL")]["brier"]) - bs.items["brier_s"]["value"]) < 1e-6
bs.notes.append("0.074 is S − M1 (from minimal to systematic); 0.076 is S − S-without-class-weights. Never swap them.")

# ----------------------------------------------------------------------------------------------------------
# age_std.json  (scene 6)
# ----------------------------------------------------------------------------------------------------------
ag = new_file("age_std", "Age confounding", "6")
SI = "S4:standardisation.insured_uninsured."
ag.add("crude", "Insured − uninsured, crude", key=SI + "crude", plan="+5.3", **PP)
ag.add("crude_lo", "CI low", key=SI + "crude_ci[0]", plan="1.8", fmt="+.1f")
ag.add("crude_hi", "CI high", key=SI + "crude_ci[1]", plan="8.8", fmt="+.1f")
ag.interval("crude_ci", "Crude gap (pp, 95 % CI)", "crude", "crude_lo", "crude_hi")
ag.add("std", "Insured − uninsured, age-standardised", key=SI + "std", plan="+0.7", **PP)
ag.add("std_lo", "CI low", key=SI + "std_ci[0]", plan="−2.6", fmt="+.1f")
ag.add("std_hi", "CI high", key=SI + "std_ci[1]", plan="3.9", fmt="+.1f")
ag.interval("std_ci", "Age-standardised gap (pp, 95 % CI)", "std", "std_lo", "std_hi")
ag.add("attenuation", "Share of the gap explained by age", key=SI + "attenuation_share", **pct_fmt(".0f"))
ag.add("older_uninsured", "Uninsured aged 60+", key=SI + "uninsured_share_60plus", fmt=".0f", unit=" %")
ag.add("older_insured", "Insured aged 60+", key=SI + "insured_share_60plus", fmt=".0f", unit=" %")
ag.notes.append("Supports 'the insured are older' (plan scene 6) with a stored number: 34 % of insured vs 10 % of uninsured adults are 60 or older.")

# ----------------------------------------------------------------------------------------------------------
# db516.json  (scene 5)
# ----------------------------------------------------------------------------------------------------------
db = new_file("db516", "NCHS replication", "5")
rows516 = read_csv("results/S4/db516_replication.csv")
for meas, nm in (("total", "Total"), ("diagnosed", "Diagnosed"), ("undiagnosed", "Undiagnosed")):
    r = csv_row("results/S4/db516_replication.csv", measure=meas, group="All", kind="crude")
    db.add(f"{meas}_ours", f"{nm}: ours", key=f"S4:db516.{meas}", fmt=".2f", unit=" %", plan={"total": "15.79", "diagnosed": "11.30", "undiagnosed": "4.49"}[meas])
    assert abs(float(r["est"]) - db.items[f"{meas}_ours"]["value"]) < 1e-9
    db.add(f"{meas}_nchs", f"{nm}: NCHS Data Brief 516", value=float(r["nchs"]), fmt=".1f", unit=" %", kind="stored-csv",
           source=f"results/S4/db516_replication.csv :: measure={meas}, group=All, kind=crude → nchs (published value)",
           plan={"total": "15.8", "diagnosed": "11.3", "undiagnosed": "4.5"}[meas])
db.add("n_estimates", "Published estimates compared", key="S4:db516.n_estimates", plan="27", **CNT)
db.add("max_gap", "Largest absolute difference", key="S4:db516.max_abs_diff_pp", plan="0.044", fmt=".3f", unit=" pp")
db.add("within_ci", "Estimates inside the published interval (Korn–Graubard CI)", key="S4:db516.kg_matches_published_ci", fmt=".0f",
       note="24 of 27: this is why the plan says 'match closely', never '27 / 27 reproduced'")
db.add("ci_overlap", "Estimates whose intervals overlap the published interval", key="S9:external.db516.ci_overlap", fmt=".0f")
db.add("n_adults", "Fasting adults used", key="S4:db516.n", **CNT)
assert len(rows516) == db.items["n_estimates"]["value"] == get("S9:external.db516.n_estimates") == 27
assert abs(max(abs(float(r["diff_pp"])) for r in rows516) - db.items["max_gap"]["value"]) < 1e-9
assert sum(r["kg_matches_nchs_ci"] == "True" for r in rows516) == db.items["within_ci"]["value"] == 24
db.groups["rows"] = [dict(measure=m, ours=f"{m}_ours", nchs=f"{m}_nchs") for m in ("total", "diagnosed", "undiagnosed")]

# ----------------------------------------------------------------------------------------------------------
# iqr_fence.json  (scene 10)
# ----------------------------------------------------------------------------------------------------------
iq = new_file("iqr_fence", "IQR fence", "10")
iq.add("fence", "1.5 × IQR fence (upper)", key="S3:outliers.a1c_iqr_fence_upper", plan="6.8", fmt=".1f", unit=" %")
iq.add("flagged", "Values beyond the fence", key="S3:outliers.a1c_iqr_flagged", plan="542", **CNT)
iq.add("flagged_pos", "Of those, diabetic (HbA1c ≥ 6.5 %)", key="S3:outliers.a1c_iqr_flagged_positive", plan="519", **CNT)
iq.add("flagged_other", "Of those, not diabetic", value=542 - 519, fmt=",.0f", kind="derived", source="derived: flagged − flagged_positive")
iq.add("flagged_pos_share", "Share of flagged values that are diabetic", value=get("S3:outliers.a1c_iqr_flagged_positive") / get("S3:outliers.a1c_iqr_flagged"),
       fmt=".0f", scale=100, unit=" %", kind="derived", source="derived: flagged_positive / flagged")
iq.add("pos_beyond_share", "Share of HbA1c positives beyond the fence", key="S3:outliers.a1c_iqr_positive_share", **pct_fmt(".0f"))
iq.add("rule", "Textbook rule multiplier", value=1.5, fmt=".1f", kind="definition", source="definition: Tukey rule, notebook §3", plan="1.5")
assert iq.items["flagged"]["value"] - iq.items["flagged_pos"]["value"] == iq.items["flagged_other"]["value"]
assert abs(get("S3:outliers.a1c_iqr_flagged_positive") / get("S3:blanket_recode.a1c_positives") - get("S3:outliers.a1c_iqr_positive_share")) < 1e-12

# ----------------------------------------------------------------------------------------------------------
# vif_skew.json  (scene 11, 12)
# ----------------------------------------------------------------------------------------------------------
vs = new_file("vif_skew", "VIF and skewness", "11, 12")
VR = "S4:vif.raw_anthropometry."
vs.add("vif_weight", "Weight", key=VR + "BMXWT", plan="95.7", fmt=".1f")
vs.add("vif_bmi", "BMI", key=VR + "BMXBMI", plan="97.6", fmt=".1f")
vs.add("vif_height", "Height", key=VR + "BMXHT", fmt=".1f")
vs.add("vif_waist", "Waist circumference", key=VR + "BMXWAIST", fmt=".1f")
vs.add("vif_hip", "Hip circumference", key=VR + "BMXHIP", fmt=".1f")
vs.add("vif_arm", "Arm circumference", key=VR + "BMXARMC", fmt=".1f")
bp_ids = []
for var in ("BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3"):
    vs.add(f"vif_{var}", PLAIN_VAR[var], key=f"S4:vif.bp_readings.{var}", fmt=".1f")
    bp_ids.append(f"vif_{var}")
vs.groups["bp_readings"] = bp_ids
vs.add("vif_bp_min", "Six BP readings, lowest VIF", value=min(vs.items[i]["value"] for i in bp_ids), fmt=".1f", kind="derived",
       source="derived: min over S4:vif.bp_readings", plan="8.8")
vs.add("vif_bp_max", "Six BP readings, highest VIF", value=max(vs.items[i]["value"] for i in bp_ids), fmt=".1f", kind="derived",
       source="derived: max over S4:vif.bp_readings", plan="11.7")
vs.add("vif_bp_mean_sys", "Mean systolic BP", key="S4:vif.bp_means.bp_sys_mean", fmt=".1f", plan="1.6")
vs.add("vif_threshold", "VIF reference line", value=10, fmt=".0f", kind="definition", source="definition: VIF > 10 'severe' (§4)", plan="10")
vs.add("skew_tg", "Fasting triglycerides, raw skewness", key="S4:skew.LBXTLG|fasting (WTSAF2YR > 0).raw", plan="6.62", fmt=".2f")
vs.add("skew_tg_log", "Fasting triglycerides, after log", key="S4:skew.LBXTLG|fasting (WTSAF2YR > 0).log", fmt=".2f")
vs.add("skew_tg_yj", "Fasting triglycerides, after Yeo-Johnson", key="S4:skew.LBXTLG|fasting (WTSAF2YR > 0).yj", plan="−0.009", fmt="+.3f")
vs.add("skew_tg_n", "Fasting subsample (n)", key="S4:skew.LBXTLG|fasting (WTSAF2YR > 0).n", plan="2,820", **CNT)
vs.add("skew_bmi", "BMI, raw skewness", key="S4:skew.BMXBMI|cohort.raw", fmt=".2f")
vs.add("skew_threshold", "Skewness rule (|skew| above)", value=1, fmt=".0f", kind="definition", source="definition: S6 step P08 evidence '|skew| > 1' (results/S6/step_catalogue.csv)")
steps = read_csv("results/S6/step_catalogue.csv")
assert "|skew| > 1" in [r for r in steps if r["step"] == "P08"][0]["evidence"]
assert vs.items["vif_BPXOSY2"]["value"] > 11.7 and vs.items["vif_bp_max"]["display"] == "11.7"
vs.notes.append("Plan 'VIF 8.8–11.7' for BP readings is the pooled-cohort S4 value; S6 stores 8.68–11.70 on the training part only (not used).")

# ----------------------------------------------------------------------------------------------------------
# hypotheses.json  (scene 7, 26)
# ----------------------------------------------------------------------------------------------------------
hy = new_file("hypotheses", "Hypotheses", "7, 26")
sb = M["S10"]["scoreboard"]
prior = {}
for r in sb:
    prior[r["prior_exposure"]] = prior.get(r["prior_exposure"], 0) + 1
hy.add("n_total", "Hypotheses locked", key="S6:hypotheses.n_total", **CNT)
hy.add("prereg_n", "Genuine pre-registrations (prior exposure none)", value=prior["none"], fmt=".0f", kind="derived",
       source="derived: count of S10:scoreboard rows with prior_exposure = none", plan="6")
hy.add("prereg_supported", "Supported", key="S10:verdict_counts_prereg_none.supported", plan="3", **CNT)
hy.add("prereg_inconclusive", "Inconclusive", key="S10:verdict_counts_prereg_none.inconclusive", plan="3", **CNT)
hy.add("prereg_refuted", "Refuted", key="S10:verdict_counts_prereg_none.refuted", **CNT)
hy.add("all_supported", "All 17: supported", key="S10:verdict_counts.supported", **CNT)
hy.add("all_inconclusive", "All 17: inconclusive", key="S10:verdict_counts.inconclusive", **CNT)
hy.add("all_mixed", "All 17: mixed", key="S10:verdict_counts.mixed", **CNT)
hy.add("all_refuted", "All 17: refuted", key="S10:verdict_counts.refuted", **CNT)
for k_, v_ in prior.items():
    hy.add(f"prior_{k_}", f"Prior exposure: {k_}", value=v_, fmt=".0f", kind="derived", source="derived: count of S10:scoreboard rows by prior_exposure")
hy.add("sub_supported", "Sub-claims (locked): supported", key="S10:subclaim_verdict_counts.locked.supported", **CNT)
hy.add("sub_inconclusive", "Sub-claims (locked): inconclusive", key="S10:subclaim_verdict_counts.locked.inconclusive", **CNT)
hy.add("sub_refuted", "Sub-claims (locked): refuted", key="S10:subclaim_verdict_counts.locked.refuted", **CNT)
assert hy.items["prereg_n"]["value"] == sum(get(f"S10:verdict_counts_prereg_none.{v}") for v in ("supported", "refuted", "equivalent", "inconclusive", "mixed")) == 6
assert sum(prior.values()) == hy.items["n_total"]["value"] == 17
assert sum(get(f"S10:verdict_counts.{v}") for v in ("supported", "refuted", "equivalent", "inconclusive", "mixed")) == 17
hy.groups["prereg_ids"] = [r["hyp_id"] for r in sb if r["prior_exposure"] == "none"]
hy.notes.append("Never say '10 of 17 confirmed': most supported verdicts are for hypotheses with prior exposure (analysis_seen).")

# ----------------------------------------------------------------------------------------------------------
# holdout.json  (scene 25)
# ----------------------------------------------------------------------------------------------------------
ho = new_file("holdout", "Hold-out and post-audit", "25")
HM = "S9:holdout.metrics[arm={a}&tier=1&pop={p}]"
ho.add("n", "Hold-out adults", key="S9:holdout.log.n_test", plan="1,146", **CNT)
ho.add("pos_eall", "Positives, All adults", key=HM.format(a="S", p="E-ALL") + ".n_pos", **CNT)
ho.add("n_screen", "Screening group in the hold-out", key=HM.format(a="S", p="E-SCREEN") + ".n", **CNT)
ho.add("pos_screen", "Screening-group positives", key=HM.format(a="S", p="E-SCREEN") + ".n_pos", plan="25", **CNT)
ho.add("auc_s_eall", "Systematic (S), All adults", key=HM.format(a="S", p="E-ALL") + ".roc_auc", plan="0.851", **AUC3)
ho.add("auc_s_escreen", "Systematic (S), Screening group", key=HM.format(a="S", p="E-SCREEN") + ".roc_auc", plan="0.791", **AUC3)
ho.add("auc_m0_eall", "Naive (M0), All adults", key=HM.format(a="M0", p="E-ALL") + ".roc_auc", **AUC3)
ho.add("auc_m1_eall", "Minimal (M1), All adults", key=HM.format(a="M1", p="E-ALL") + ".roc_auc", **AUC3)
ho.add("gap_s", "Hold-out gap All adults − Screening group (not shown)", key="S10:holdout.gap_S_eall_minus_escreen", fmt="+.3f", show=False,
       note="Do not show (plan scene 25): only 25 Screening-group positives, claims C25")
ho.add("postaudit_n", "Issues raised by the external review, checked", value=len(get("S9:postaudit.summary")), fmt=".0f", kind="derived",
       source="derived: len(S9:postaudit.summary) (6 rows; register DR-S9-16 … DR-S9-21)", plan="6")
ho.add("withdrawn_n", "Sub-claims withdrawn as not testable after the audit", value=len(get("S10:withdrawn_subclaims")), fmt=".0f", kind="derived",
       source="derived: len(S10:withdrawn_subclaims)")
ho.add("n_executions_log", "Hold-out executions in results/S9/holdout_log.json", value=json.loads((RES / "S9/holdout_log.json").read_text(encoding="utf-8"))["n_executions"],
       fmt=".0f", kind="stored-csv", source="results/S9/holdout_log.json :: n_executions (first scoring run)")
assert ho.items["pos_screen"]["value"] == 25 and ho.items["n"]["value"] == get("S6:inputs.n_holdout") == 1146
assert ho.items["n_executions_log"]["value"] == 1
ho.groups["timeline"] = ["hypotheses locked (SHA-256)", "experiments frozen", "hold-out: scored once"]
ho.notes.append("metrics_S9 holdout.log shows n_executions = 2 (FINAL-mode re-run that reproduces the single evaluation run); results/S9/holdout_log.json shows 1.")
ho.notes.append("Two sub-claims (B3-b, H2b-c) were withdrawn as 'not testable' after the audit although the locked verdict table is unchanged; "
                "'changed no locked verdict' needs that nuance if challenged.")

# ----------------------------------------------------------------------------------------------------------
# minimisation.json  (scene 4)
# ----------------------------------------------------------------------------------------------------------
mn = new_file("minimisation", "Data minimisation", "4")
mn.add("raw", "Columns in the 16 source files", key="S1:minimisation.raw_columns", plan="175", **CNT)
mn.add("kept", "Columns kept", key="S1:minimisation.kept", plan="78", **CNT)
mn.add("dropped", "Columns dropped", key="S1:minimisation.dropped", **CNT)
assert (get("S2:minimisation.cols_raw"), get("S2:minimisation.cols_kept"), get("S2:minimisation.cols_dropped")) == (175, 78, 97)
assert get("S1:minimisation.raw_columns") - get("S1:minimisation.kept") == get("S1:minimisation.dropped") == 97
mn.add("files_verified", "Raw files verified by SHA-256", key="S2:raw_files_verified", **CNT)
mn.add("hash_mismatches", "Hash mismatches", key="S2:hash_mismatches", **CNT)
mn.add("lock_sha", "hypotheses.md SHA-256 (locked)", key="S6:hypotheses.lock.sha256", fmt=None, display=get("S6:hypotheses.lock.sha256")[:12] + "…")
mn.groups["per_file"] = [dict(file=k, raw=v["cols_raw"], kept=v["cols_kept"], dropped=v["cols_dropped"]) for k, v in get("S2:minimisation.per_file").items()]
assert sum(x["raw"] for x in mn.groups["per_file"]) == 175 and sum(x["kept"] for x in mn.groups["per_file"]) == 78

# ----------------------------------------------------------------------------------------------------------
# arms.json  (extra: scenes 12-13)  and  simpson.json (extra: scene 15)
# ----------------------------------------------------------------------------------------------------------
ar = new_file("arms", "Preparation steps and arms", "12, 13")
ar.add("n_steps", "Preparation steps", value=len(steps), fmt=".0f", kind="stored-csv", source="results/S6/step_catalogue.csv :: number of rows (P01 … P14)", plan="14")
assert [r["step"] for r in steps] == [f"P{i:02d}" for i in range(1, 15)]
for arm_, lab, plan_ in (("M0", "Naive (M0)", "88"), ("M1", "Minimal (M1)", "46"), ("S", "Systematic (S)", "42")):
    ar.add(f"cols_{arm_}", f"{lab}: design columns", key=f"S6:arms.{arm_}.n_features_t1", plan=plan_, **CNT)
    ar.groups.setdefault("toggles", {})[arm_] = [p for p in (f"P{i:02d}" for i in range(1, 15)) if get(f"S6:arms.{arm_}.{p}")]
assert ar.groups["toggles"]["M0"] == [] and ar.groups["toggles"]["M1"] == ["P03"] and len(ar.groups["toggles"]["S"]) == 13
ar.notes.append("Arm S switches on P01–P13; P14 (waist-to-height) is a separate arm in S6, although the storyboard lights all fourteen cards.")
ar.groups["steps"] = [dict(step=r["step"], name=r["name"], block=r["block"], evidence=r["evidence"]) for r in steps]

sp = new_file("simpson", "Simpson scan", "15")
sp.add("n_comparisons", "Comparisons scanned", key="S4:simpson.n_comparisons", plan="224", **CNT)
sp.add("n_flips", "Sign flips", key="S4:simpson.n_flips", plan="6", **CNT)
sp.add("dag_bmi_valid", "Adjusting for BMI is valid", key="S4:dag.bmi_adjustment_valid", fmt=None, display="no (mediator)")


# ----------------------------------------------------------------------------------------------------------
# Audit 1: storyboard value vs stored value at display precision
# ----------------------------------------------------------------------------------------------------------
mismatch, precision_notes = [], []
for f in FILES:
    for id_, it in f.items.items():
        plan = it["_plan"]
        if plan is None or not isinstance(it["value"], (int, float)):
            continue
        d = decimals(plan)
        stored = it["value"] * it["scale"]
        if round(stored, d) != num(plan):
            mismatch.append((f.name, id_, plan, it["display"], stored))
        elif d != decimals(it["display"]):
            precision_notes.append((f.name, id_, plan, it["display"]))

# ----------------------------------------------------------------------------------------------------------
# Audit 2: every displayed value that has a numbers_on_slides.csv row must match it
# ----------------------------------------------------------------------------------------------------------
n_csv_checked = 0
for f in FILES:
    for id_, it in f.items.items():
        key = it["key"]
        if key and key in NOS_BY_KEY and isinstance(it["value"], (int, float)):
            for row in NOS_BY_KEY[key]:
                raw = float(row["value_raw"])
                assert abs(raw - it["value"]) <= 1e-9 * max(1.0, abs(raw)), (f.name, id_, raw, it["value"])
                cs = row["value"]
                scale_csv = 100.0 if cs.strip().endswith("%") else 1.0
                dd = decimals(it["display"])
                shown = num(it["display"])
                assert round(it["value"] * it["scale"], dd) == shown, (f.name, id_, it["display"])
                assert round(raw * scale_csv, decimals(cs)) == num(cs), (f.name, id_, cs)
                if decimals(cs) == dd:
                    assert num(cs) == shown, (f.name, id_, "display", it["display"], "csv", cs)
                else:
                    # different precision: the coarser display must still be the rounding of the finer CSV value
                    k = min(dd, decimals(cs))
                    assert round(num(cs), k) == round(shown, k), (f.name, id_, it["display"], cs)
                it["csv"] = dict(slide_id=row["slide_id"], label=row["label"], csv_value=cs)
                n_csv_checked += 1
                break
print(f"numbers_on_slides.csv: {n_csv_checked} displayed values re-checked against their CSV row (raw equal, display equal at precision)")

# ----------------------------------------------------------------------------------------------------------
# Write JSON
# ----------------------------------------------------------------------------------------------------------
for f in FILES:
    items = {}
    for id_, it in f.items.items():
        d = {k: v for k, v in it.items() if not k.startswith("_")}
        items[id_] = d
    doc = {
        "_meta": {
            "file": f"video/data/{f.name}.json",
            "visual": f.visual,
            "scenes": f.scenes,
            "generated_by": "video/data/build_data.py (reads stored results only; no model fitting)",
            "results_snapshot_utc": SNAPSHOT,
            "naming": {"E-ALL": "All adults", "E-SCREEN": "Screening group", "M0": "Naive (M0)", "M1": "Minimal (M1)", "S": "Systematic (S)"},
            "notes": f.notes,
        },
        "items": items,
    }
    if f.intervals:
        doc["intervals"] = f.intervals
    if f.groups:
        doc["groups"] = f.groups
    (OUT / f"{f.name}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

# ----------------------------------------------------------------------------------------------------------
# SOURCES.md
# ----------------------------------------------------------------------------------------------------------
def md(s) -> str:
    return str(s).replace("|", "\\|")


L: list[str] = []
L.append("# Video data sources\n")
L.append("Generated by `video/data/build_data.py` from stored results only (no model fitting). Do not edit by hand; re-run the script.\n")
L.append(f"Results snapshot: `results/metrics_S10.json` written {SNAPSHOT}. Each JSON has `items` keyed by short ids; every item holds "
         "`value`, `label` (on screen), `display`, `fmt`/`scale`/`unit`, `kind`, `source`, `key`, `csv`.\n")
L.append("- `kind`: `stored` (metrics_S*.json), `stored-csv` (a CSV or log under results/), `derived` (arithmetic on stored values), "
         "`definition` (constant, not data), `figure-text` / `notebook-output` (stored only in a caption or executed notebook).")
L.append("- `key` uses the `numbers_on_slides.csv` dialect (`S7:headline.auc_M0_eall_T1`); `csv` names the matching CSV row, or is `null` when the value is not yet audited.")
L.append("- Negative numbers are printed with the typographic minus (U+2212).\n")
L.append(f"Audit run: {n_csv_checked} displayed values that have a `numbers_on_slides.csv` row were re-checked (raw value equal, display equal at display precision).\n")

L.append("## Storyboard versus stored values\n")
if mismatch:
    L.append("Mismatches at display precision (the stored value wins):\n")
    L.append("| file | item | storyboard | stored display | stored value |\n|---|---|---|---|---|")
    for m in mismatch:
        L.append(f"| {m[0]} | {m[1]} | {md(m[2])} | {md(m[3])} | {m[4]} |")
else:
    L.append("No storyboard number differs from its stored value at the storyboard's own precision "
             f"({sum(1 for f in FILES for it in f.items.values() if it['_plan'] is not None)} storyboard-used items compared).\n")
L.append("")
if precision_notes:
    L.append("Same value, different number of decimals (the display here follows the stored precision rule of the item):\n")
    for m in precision_notes:
        L.append(f"- {m[0]}.{m[1]}: storyboard `{m[2]}`, display `{m[3]}`")
    L.append("")
L.append("Wording and rounding points to keep in mind (all stored, none is a number mismatch):\n")
L.append("- Scene 18: the two bars (0.961, 0.828) subtract to 0.133 as printed, 0.132 unrounded; the stored paired mean is 0.131. Label the 0.131 'paired'.")
L.append("- Scene 5: 24 of 27 estimates lie inside the published interval (`db516.within_ci`); S9 reports 27 of 27 overlapping. Say 'match closely'.")
L.append("- Scene 8: 57 is `questionnaire_only_cells`; the 562 in `S3:sentinel_audit` is a different count (all genuine codes recoded by the by-variable rule).")
L.append("- Scene 19: the root is a treatment item (`DIQ070`, taking diabetes pills); `DID040` (age at diagnosis) is a second-level split on the right branch, left branch splits on `DIQ180`.")
L.append("- Scene 25: `holdout.n_executions_log` is 1 in `results/S9/holdout_log.json`, 2 in `metrics_S9` (FINAL re-run reproduces the first). "
         "Two sub-claims were withdrawn as not testable after the audit (`holdout.withdrawn_n`); the locked verdict table is unchanged.")
L.append("- Scene 13: arm S switches on P01–P13; P14 is a separate arm (`arms.notes`).\n")

for f in FILES:
    L.append(f"## {f.name}.json\n")
    L.append(f"Visual: {f.visual} · scenes {f.scenes}\n")
    L.append("| id | label (on screen) | display | value | kind | source | in CSV |")
    L.append("|---|---|---|---|---|---|---|")
    for id_, it in f.items.items():
        v = it["value"]
        vs_ = f"{v:.6g}" if isinstance(v, float) else str(v)
        csvmark = f"{it['csv']['slide_id']}" if it["csv"] else ("n/a" if it["kind"] == "definition" else "no")
        L.append(f"| {id_} | {md(it['label'])} | {md(it['display'])} | {md(vs_)} | {it['kind']} | {md(it['source'])} | {csvmark} |")
    if f.intervals:
        L.append("")
        L.append("Intervals: " + "; ".join(f"`{k}` = {md(v['display'])}" for k, v in f.intervals.items()))
    for n_ in f.notes:
        L.append(f"\nNote: {n_}")
    L.append("")

L.append("## Values NOT in numbers_on_slides.csv\n")
L.append("### Used in the storyboard (to be added to the `NUM` list of `notebooks/sections/09_synthesis.py` and re-audited)\n")
L.append("| file | id | display | kind | source |\n|---|---|---|---|---|")
used_missing = []
for f in FILES:
    for id_, it in f.items.items():
        if it["_plan"] is not None and not it["csv"] and it["kind"] != "definition":
            used_missing.append((f.name, id_))
            L.append(f"| {f.name} | {id_} | {md(it['display'])} | {it['kind']} | {md(it['source'])} |")
L.append("")
L.append("### Definitions and external reference values used on screen (constants, not data)\n")
for f in FILES:
    for id_, it in f.items.items():
        if it["kind"] == "definition":
            L.append(f"- {f.name}.{id_}: {md(it['display'])} ({md(it['source'])})")
L.append("")
L.append("### Extra stored values supplied for convenience (not in the storyboard)\n")
L.append("Intervals' CI bounds, absolute Brier scores, second-level groups, per-variable damage etc. Not audited by the CSV; "
         "all resolve from stored keys at build time.\n")
extra = [(f.name, id_) for f in FILES for id_, it in f.items.items()
         if it["_plan"] is None and not it["csv"] and it["kind"] != "definition"]
L.append(", ".join(f"`{a}.{b}`" for a, b in extra))
L.append("")
(OUT / "SOURCES.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")

print(f"wrote {len(FILES)} JSON files + SOURCES.md to {rel(OUT)}")
for f in FILES:
    print(f"  {f.name}.json: {len(f.items)} items, {len(f.intervals)} intervals")
print(f"storyboard mismatches: {len(mismatch)}")
for m in mismatch:
    print("   MISMATCH", m)
for m in precision_notes:
    print("   precision", m)
print(f"storyboard-used items not in numbers_on_slides.csv: {len(used_missing)}")
