"""Check the slide materials against results/S10/numbers_on_slides.csv (Stage S11b).

Run from anywhere:   .venv/Scripts/python slides/check_numbers.py
Exit code 0 = all checks pass; 1 = at least one error (warnings do not fail the run).

What is checked
  Storyboard (slides/storyboard.md), per slide block `### <id> · <title>`:
    * required fields (type, time, figure, takeaway, notes, numbers used, footer, claims);
    * title is a noun phrase of at most 6 words (no sentence punctuation or finite-verb cue words;
      the title slide of type `title` is exempt from the word limit);
    * takeaway (the one-line caption or the body) has at most 15 words (template slides exempt);
    * notes have at most 60 words and at most 2.2 words per budgeted second, and contain no ': '
      (Marp would parse such an HTML comment as a directive instead of a presenter note);
    * the figure and its caption file exist (`figures/*.png` or `slides/figures/*.png`); claim ids
      exist in governance/claims.csv;
    * every section mark in a footer (§3.2, §10.2.1) exists as a heading of the assembled notebook
      notebooks/final/CA6003_NHANES_Diabetes.ipynb (skipped with a warning if the notebook is missing);
    * time ranges are consecutive and the total is within the 11:40 cap;
    * every `numbers used` row (`<segment> · <label> = <value>`) exists in numbers_on_slides.csv
      with exactly that printed value;
    * every digit token in title, takeaway, notes and footer matches a declared row of that
      slide within rounding (tolerance = half a unit of the last written decimal), and every
      declared row is used at least once.
  Deck (slides/deck.md): the same extraction applied independently to each Marp slide, plus a
  sync check against the storyboard (id order, title, figure path, caption, footer, notes) and
  the 15-word body limit and one-image-per-slide rule.

Number sources
  * results/S10/numbers_on_slides.csv (rows `<segment> · <label> = <value>`);
  * JSON_ROWS below: the cross-validation sample sizes (4,584 training adults, 127 screening positives)
    and the DB516 fasting-subsample size, read from results/metrics_S4.json and metrics_S7.json because
    they are not in the CSV. They are declared in `numbers used` exactly like CSV rows.
  * Footers are checked like titles, captions and notes: every digit token in a footer must match a
    declared row of that slide.

Matching rules for a digit token
  * an explicit sign (+, -, minus sign) must agree with the sign of the value; an unsigned token
    is compared with the absolute value (prose such as "a drop of 0.131" stays valid);
  * a token with % is compared with value*100 for rows printed with %, and with the raw value for rows
    whose label ends in (%);
  * integers may be written with thousands separators (5,730);
  * numbers that occur in a CSV label (6.5 in "HbA1c < 6.5", 25 in "BMI < 25", 3 years) are
    treated as definitional constants and are always allowed;
  * not extracted: identifiers with a letter before the digit (M1, L2, E-ALL, DB516, CA6003, C01,
    V3.1, H2c), section marks (§7), years (2021-23), "Tier 1", "3×3", and clock times.
Spelled-out numbers (ten, two) are NOT checked, so data numbers must be written as digits.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides"
NUMBERS_CSV = ROOT / "results" / "S10" / "numbers_on_slides.csv"
CLAIMS_CSV = ROOT / "governance" / "claims.csv"
STORYBOARD = SLIDES / "storyboard.md"
DECK = SLIDES / "deck.md"
NOTEBOOK = ROOT / "notebooks" / "final" / "CA6003_NHANES_Diabetes.ipynb"

# (slide_id, label, results file, key path in the JSON file, printed format)
JSON_ROWS = [
    ("V7", "training part adults", "results/metrics_S7.json", "splits.n_train", "{:,.0f}"),
    ("V7", "training part E-SCREEN positives", "results/metrics_S7.json", "splits.n_pos_escreen", "{:,.0f}"),
    ("V1", "DB516 fasting subsample n", "results/metrics_S4.json", "design.n_fasting_pos", "{:,.0f}"),
    ("V7", "hold-out E-SCREEN positives", "results/metrics_S9.json", "holdout.metrics[arm=S&tier=1&pop=E-SCREEN].n_pos", "{:,.0f}"),
]

CAP_SECONDS = 11 * 60 + 40
TITLE_MAX_WORDS = 6
BODY_MAX_WORDS = 15
NOTES_MAX_WORDS = 60
WORDS_PER_SECOND = 2.2

errors: list[str] = []
warnings: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


# --------------------------------------------------------------------------- numbers table
def norm_sign(s: str) -> str:
    return s.replace("−", "-").replace("–", "-")


def to_float(s: str) -> float:
    return float(norm_sign(s).replace(",", "").replace("%", "").replace("+", ""))


def load_numbers():
    rows = {}
    definitional: list[float] = []
    with open(NUMBERS_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows[(r["slide_id"], r["label"])] = r
            for m in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w])", r["label"]):
                definitional.append(float(m.group(1)))
    for sid, label, rel, key, fmt in JSON_ROWS:
        node = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for k in key.split("."):
            m = re.match(r"(\w+)\[(.+)\]$", k)          # list lookup: name[field=value&field=value]
            if m:
                node = node[m.group(1)]
                want = dict(kv.split("=") for kv in m.group(2).split("&"))
                node = next(r for r in node if all(str(r[f]) == v for f, v in want.items()))
            else:
                node = node[k]
        rows[(sid, label)] = dict(slide_id=sid, label=label, value=fmt.format(float(node)), value_raw=str(float(node)),
                                  source_key=f"{rel}:{key}")
    return rows, sorted(set(definitional))


def candidates(row, pct: bool) -> list[float]:
    """Numeric readings of a CSV row that a slide token could stand for."""
    raw = float(row["value_raw"])
    shown = row["value"]
    out = [raw]
    if shown.strip().endswith("%"):
        out = [raw * 100] if pct else [raw * 100, raw]
    elif pct and row["label"].rstrip().endswith("(%)"):
        out = [raw]
    elif pct:
        out = []
    return out


# --------------------------------------------------------------------------- token extraction
EXEMPT = [
    r"\bTier\s*\d\b",
    r"\b3\s*[×x]\s*3\b",
    r"\b(?:19|20)\d\d(?:\s*[–-]\s*\d\d)?\b",
    r"\b\d{1,2}:\d\d\b",
    r"\bGroup\s*\[?\w*\]?",
]
TOKEN = re.compile(
    r"(?<![\w.§#–-])([+\-−])?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(%)?"
)


def extract_tokens(text: str):
    t = text
    for pat in EXEMPT:
        t = re.sub(pat, " ", t)
    out = []
    for m in TOKEN.finditer(t):
        sign, whole, frac, pct = m.group(1), m.group(2), m.group(3) or "", m.group(4)
        s = f"{sign or ''}{whole}{frac}{pct or ''}"
        val = float(whole.replace(",", "") + frac)
        out.append(dict(text=s, sign=norm_sign(sign) if sign else "", value=val,
                        dec=len(frac) - 1 if frac else 0, pct=bool(pct)))
    return out


def token_matches(tok, row) -> bool:
    for c in candidates(row, tok["pct"]):
        if tok["sign"] == "+" and c < -1e-9:
            continue
        if tok["sign"] == "-" and c > 1e-9:
            continue
        if abs(abs(c) - tok["value"]) <= 0.5 * 10 ** (-tok["dec"]) + 1e-9:
            return True
    return False


def check_slide_numbers(where, fields: dict, declared: list, rows, definitional):
    """fields: name -> text. declared: list of CSV rows. Return the number of tokens verified."""
    used = [False] * len(declared)
    n_tok = 0
    for name, text in fields.items():
        for tok in extract_tokens(text):
            n_tok += 1
            hit = False
            for i, row in enumerate(declared):
                if token_matches(tok, row):
                    used[i] = True
                    hit = True
            if hit:
                continue
            if not tok["pct"] and tok["sign"] == "" and any(
                    abs(tok["value"] - d) <= 0.5 * 10 ** (-tok["dec"]) + 1e-9 for d in definitional):
                continue  # definitional constant that appears in a CSV label
            err(where, f"number '{tok['text']}' in {name} matches no declared row of numbers_on_slides.csv")
    for flag, row in zip(used, declared):
        if not flag:
            err(where, f"declared row '{row['slide_id']} · {row['label']}' ({row['value']}) is not used in the slide text")
    return n_tok


# --------------------------------------------------------------------------- section marks
def notebook_sections() -> set[str] | None:
    """Section numbers (3, 3.2, 10.2.1) that exist as headings of the assembled notebook."""
    if not NOTEBOOK.exists():
        return None
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    found: set[str] = set()
    for c in nb["cells"]:
        if c["cell_type"] != "markdown":
            continue
        for line in "".join(c["source"]).splitlines():
            m = re.match(r"#{1,3} (?:§)?(\d+(?:\.\d+)*)", line)
            if m:
                found.add(m.group(1))
    return found


def check_section_marks(where: str, footer: str, sections) -> None:
    if sections is None:
        return
    for m in re.finditer(r"§(\d+(?:\.\d+)*)", footer):
        if m.group(1) not in sections:
            err(where, f"footer cites §{m.group(1)}, which is not a heading of the assembled notebook")


# --------------------------------------------------------------------------- word counts
def words(text: str) -> int:
    return sum(1 for w in text.split() if re.search(r"[A-Za-z0-9]", w))


def title_ok(where, title, max_words=TITLE_MAX_WORDS):
    n = words(title)
    if n > max_words:
        err(where, f"title has {n} words (max {max_words})")
    if re.search(r"[.!?:;]$", title) or re.search(r"\b(is|are|was|were|has|have|can|will|does|do|shows?|means?)\b", title, re.I):
        err(where, f"title looks like a sentence: '{title}'")


# --------------------------------------------------------------------------- storyboard parsing
HEAD = re.compile(r"^### (V\d+(?:\.\d+)?) · (.+)$")
FIELD = re.compile(r"^- \*\*([a-z ]+)\*\*: ?(.*)$")
NUMROW = re.compile(r"^(V\d+) · (.+) = (.+)$")


def parse_storyboard():
    slides, cur = [], None
    for line in STORYBOARD.read_text(encoding="utf-8").splitlines():
        m = HEAD.match(line)
        if m:
            cur = dict(id=m.group(1), title=m.group(2).strip(), f={})
            slides.append(cur)
            continue
        if line.startswith("## "):
            cur = None
        if cur is not None:
            fm = FIELD.match(line)
            if fm:
                cur["f"][fm.group(1)] = fm.group(2).strip()
    return slides


def time_range(s: str):
    m = re.match(r"(\d+) s \((\d+):(\d\d)–(\d+):(\d\d)\)$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)) * 60 + int(m.group(3)), int(m.group(4)) * 60 + int(m.group(5))


# --------------------------------------------------------------------------- deck parsing
def parse_deck():
    text = DECK.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        err("deck", "missing Marp front matter")
        return []
    front = m.group(1)
    for key in ("marp: true", "size: 16:9", "paginate: true"):
        if key not in front:
            err("deck", f"front matter lacks '{key}'")
    body = text[m.end():]
    parts = re.split(r"\n---\n", body)
    slides = []
    for p in parts:
        cls = re.search(r"<!--\s*_class:\s*(\S+)([^>]*?)-->", p)
        foot = re.search(r"<!--\s*_footer:\s*\"(.*?)\"\s*-->", p)
        if not cls:
            err("deck", "a slide has no '_class' marker; cannot identify it")
            continue
        sid = cls.group(1)
        sid = sid.replace("_", ".")
        types = (cls.group(2) or "").split()
        comments = re.findall(r"<!--(.*?)-->", p, re.S)
        notes = [c.strip() for c in comments if not re.match(r"\s*_(class|footer)\s*:", c)]
        stripped = re.sub(r"<!--.*?-->", "", p, flags=re.S)
        lines = [l for l in stripped.splitlines() if l.strip()]
        title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")
        imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
        rest = [l for l in lines if not l.startswith("# ") and not l.startswith("![")]
        bullets = [l[2:].strip() for l in rest if l.startswith("- ")]
        paras = [l.strip() for l in rest if not l.startswith("- ") and not l.startswith("|")]
        tables = [l for l in rest if l.startswith("|")]
        slides.append(dict(id=sid, types=types, footer=foot.group(1) if foot else None, title=title,
                           imgs=imgs, bullets=bullets, paras=paras, tables=tables, notes=notes))
    return slides


# --------------------------------------------------------------------------- main
def main() -> int:
    rows, definitional = load_numbers()
    claim_ids = {r["claim_id"] for r in csv.DictReader(open(CLAIMS_CSV, encoding="utf-8", newline=""))}
    sb = parse_storyboard()
    sections = notebook_sections()
    if sections is None:
        warn("notebook", "assembled notebook not found; section marks not checked")
    n_checked = 0
    if not sb:
        err("storyboard", "no slide blocks found")

    # ---------------- storyboard
    clock = 0
    ids_sb = []
    sb_by_id = {}
    for s in sb:
        sid, f = s["id"], s["f"]
        where = f"storyboard {sid}"
        ids_sb.append(sid)
        sb_by_id[sid] = s
        for key in ("type", "time", "figure", "takeaway", "notes", "numbers used", "footer", "claims"):
            if key not in f:
                err(where, f"missing field '{key}'")
        if any(k not in f for k in ("type", "time", "takeaway", "notes", "numbers used", "footer", "figure")):
            continue
        title_ok(where, s["title"], 99 if f["type"] == "title" else TITLE_MAX_WORDS)
        typ = f["type"]
        if typ not in ("figure", "text", "template", "title"):
            err(where, f"unknown type '{typ}'")
        # time
        tr = time_range(f["time"])
        if tr is None:
            err(where, f"cannot parse time '{f['time']}'")
            sec = 0
        else:
            sec, a, b = tr
            if a != clock or b - a != sec:
                err(where, f"time range {f['time']} is not consecutive (expected start {clock // 60}:{clock % 60:02d})")
            clock = b
        # caption/body
        if typ != "template" and words(f["takeaway"]) > BODY_MAX_WORDS:
            err(where, f"takeaway has {words(f['takeaway'])} words (max {BODY_MAX_WORDS})")
        # notes
        nw = words(f["notes"])
        if nw > NOTES_MAX_WORDS:
            err(where, f"notes have {nw} words (max {NOTES_MAX_WORDS})")
        if sec and nw > WORDS_PER_SECOND * sec:
            err(where, f"notes have {nw} words, more than {WORDS_PER_SECOND} words per second for {sec} s")
        if ": " in f["notes"]:
            err(where, "notes contain ': ' (would be parsed as a Marp directive)")
        # figure
        if typ == "figure":
            m = re.match(r"`((?:slides/)?figures/[^`]+\.png)`$", f["figure"])
            if not m:
                err(where, "figure field must be a figures/*.png or slides/figures/*.png path in backticks")
            else:
                png = ROOT / m.group(1)
                if not png.exists():
                    err(where, f"figure file missing: {m.group(1)}")
                if not png.with_suffix(".txt").exists():
                    err(where, f"figure caption file missing: {png.with_suffix('.txt').name}")
        elif f["figure"] != "none":
            err(where, "non-figure slide must have figure = none")
        # claims
        if f["claims"] != "none":
            for c in re.split(r",\s*", f["claims"]):
                if re.match(r"C\d\d-C\d\d$", c):
                    continue
                if c not in claim_ids:
                    err(where, f"claim '{c}' not in governance/claims.csv")
        # declared numbers
        declared = []
        if f["numbers used"] != "none":
            for item in f["numbers used"].split(" | "):
                nm = NUMROW.match(item.strip())
                if not nm:
                    err(where, f"cannot parse numbers-used item '{item}'")
                    continue
                key = (nm.group(1), nm.group(2))
                row = rows.get(key)
                if row is None:
                    err(where, f"'{nm.group(1)} · {nm.group(2)}' is not in numbers_on_slides.csv")
                    continue
                if norm_sign(row["value"]) != norm_sign(nm.group(3)):
                    err(where, f"'{key[1]}' printed as {nm.group(3)} but the CSV value is {row['value']}")
                declared.append(row)
        s["declared"] = declared
        check_section_marks(where, f["footer"], sections)
        n_checked += check_slide_numbers(where, {"title": s["title"], "takeaway": f["takeaway"],
                                                  "notes": f["notes"], "footer": f["footer"]},
                                         declared, rows, definitional)
        if re.search(r"\[TEAM TO FILL[^\]]*\]", f["footer"] + f["takeaway"]):
            warn(where, "placeholder to be filled by the team")

    total = clock
    if total > CAP_SECONDS:
        err("storyboard", f"total {total // 60}:{total % 60:02d} exceeds the 11:40 cap")

    # ---------------- deck
    dk = parse_deck()
    ids_dk = [d["id"] for d in dk]
    if ids_sb != ids_dk:
        err("deck", f"slide ids differ from storyboard: storyboard {ids_sb} / deck {ids_dk}")
    for d in dk:
        sid = d["id"]
        where = f"deck {sid}"
        s = sb_by_id.get(sid)
        if s is None or "declared" not in s:
            continue
        f = s["f"]
        typ = f["type"]
        if len(d["imgs"]) > 1:
            err(where, f"{len(d['imgs'])} images on one slide (rule: one figure per slide)")
        if typ == "figure":
            if len(d["imgs"]) != 1:
                err(where, "figure slide has no image")
            else:
                rel = d["imgs"][0]
                if not (SLIDES / rel).resolve().exists():
                    err(where, f"image path does not resolve from slides/: {rel}")
                want = f["figure"].strip("`")
                want_rel = "../" + want if want.startswith("figures/") else want.replace("slides/", "", 1)
                if want_rel != rel:
                    err(where, f"image {rel} differs from storyboard figure {f['figure']}")
        elif d["imgs"]:
            err(where, "text/template/title slide must not carry an image")
        # title / footer / notes sync
        if d["title"] != s["title"]:
            err(where, f"title '{d['title']}' differs from storyboard '{s['title']}'")
        if d["footer"] != f["footer"]:
            err(where, "footer differs from storyboard")
        if len(d["notes"]) != 1:
            err(where, f"expected one presenter-notes comment, found {len(d['notes'])}")
            notes = " ".join(d["notes"])
        else:
            notes = d["notes"][0]
        if " ".join(notes.split()) != " ".join(f["notes"].split()):
            err(where, "speaker notes differ from storyboard")
        if ": " in notes:
            err(where, "notes contain ': '")
        title_ok(where, d["title"], 99 if typ == "title" else TITLE_MAX_WORDS)
        # caption / body
        if typ == "figure":
            cap = " ".join(d["paras"])
        elif typ == "title":
            cap = " ".join(d["paras"])
        elif typ == "text":
            cap = " · ".join(d["bullets"])
        else:
            cap = ""
        if typ != "template":
            if " ".join(cap.split()) != " ".join(f["takeaway"].split()):
                err(where, f"caption/body '{cap}' differs from storyboard takeaway")
            if words(cap) > BODY_MAX_WORDS:
                err(where, f"body has {words(cap)} words (max {BODY_MAX_WORDS})")
        else:
            warn(where, "template slide: contribution table and GenAI line to be completed by the team")
        body_text = cap if typ != "template" else " ".join(d["paras"] + d["tables"])
        n_checked += check_slide_numbers(where, {"title": d["title"], "body": body_text, "notes": notes,
                                                  "footer": d["footer"] or ""},
                                         s["declared"], rows, definitional)

    # ---------------- report
    print(f"storyboard slides: {len(sb)}; deck slides: {len(dk)}")
    print(f"planned time: {total // 60}:{total % 60:02d} (target 11:20, cap 11:40)")
    print(f"digit tokens verified against numbers_on_slides.csv: {n_checked}")
    for w_ in warnings:
        print("WARNING", w_)
    if errors:
        for e in errors:
            print("ERROR", e)
        print(f"FAILED with {len(errors)} error(s)")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
