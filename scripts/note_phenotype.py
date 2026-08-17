#!/usr/bin/env python3
"""FROZEN note-based hepatic-steatosis phenotype rule for MASLD / MIMIC-IV.

VERSION = "1.0.0"  ·  FROZEN_DATE = "2026-08-17"

This rule is FROZEN prior to 2x2 construction and chart adjudication (Aim 1a
must be non-circular). Development on the full corpus is expected; iteration
against the gold standard is NOT permitted after this freeze.

Design (see docs/note_phenotype_spec.md for full documentation & citations):
  * Three-tier approved lexicon (A definite / B imaging-sign sensitivity /
    C hedged-A reported separately).
  * Mandatory anatomical scoping (VA/VACS-style) with per-organ suppression
    accounting.
  * Context assertion via a ConText reimplementation (Harkema et al. 2009),
    which extends NegEx (Chapman et al. 2001): negation, historical
    (temporality), family (experiencer), hedged (hypothetical -> Tier C).
  * Outpatient radiology linked by subject_id within a lookback-dominant window.

TEXT-HANDLING: aggregate outputs only; no raw note text is printed or written.

Run:  python scripts/note_phenotype.py            # behavior report on locked pop
Import: from scripts.note_phenotype import classify_note, VERSION
"""
import bisect
import os
import re
from collections import Counter, defaultdict

import pandas as pd
import duckdb

VERSION = "1.0.0"
FROZEN_DATE = "2026-08-17"

NOTE = "data/raw/note"
POP = "data/processed/analysis_population.parquet"
OUTPATIENT_WINDOWS = {"primary": (365, 30), "sensitivity": (90, 30)}  # (days_before, days_after)

# ===========================================================================
# LEXICON (approved). (name, compiled_regex, tier, self_anatomical)
# self_anatomical=True -> trigger is inherently hepatic; skip anatomical scoping.
# ===========================================================================
def _rx(p):
    return re.compile(p, re.IGNORECASE)

TRIGGERS = [
    # Tier A — specific phrases / spelled-out (inherently hepatic)
    ("hepatic steatosis",              _rx(r"\bhepatic steatosis\b"), "A", True),
    ("fatty liver",                    _rx(r"\bfatty liver\b"), "A", True),
    ("nonalcoholic fatty liver",       _rx(r"\bnon[- ]?alcoholic fatty liver( disease)?\b"), "A", True),
    ("nonalcoholic steatohepatitis",   _rx(r"\bnon[- ]?alcoholic steatohepat\w*\b"), "A", True),
    ("metabolic dysfunction-associated", _rx(r"\bmetabolic dysfunction[- ]associated\b"), "A", True),
    # Tier A — abbreviations (inherently hepatic)
    ("NAFLD", _rx(r"\bnafld\b"), "A", True),
    ("NASH",  _rx(r"\bnash\b"), "A", True),
    ("MASLD", _rx(r"\bmasld\b"), "A", True),
    ("MASH",  _rx(r"\bmash\b"), "A", True),
    ("NAFL",  _rx(r"\bnafl\b"), "A", True),
    # Tier A — phrases requiring anatomical scoping
    ("fatty infiltration", _rx(r"\bfatty infiltration\b"), "A", False),
    ("fatty change",       _rx(r"\bfatty change\b"), "A", False),
    ("fatty sparing",      _rx(r"\bfatty sparing\b"), "A", False),
    ("focal fat",          _rx(r"\bfocal fat\b"), "A", False),
    # Tier A — stems requiring scoping
    ("steatohepatitis", _rx(r"\bsteatohepatit\w*\b"), "A", False),
    ("steatosis",       _rx(r"\bsteatosis\b"), "A", False),
    ("steatotic",       _rx(r"\bsteatotic\b"), "A", False),
    # Tier A — bare "fatty" (scoping-only per approved rule)
    ("fatty (bare)", _rx(r"\bfatty\b"), "A", False),
    # Tier B — imaging signs (sensitivity only)
    ("increased hepatic echogenicity", _rx(r"\bincreased hepatic echogenicity\b"), "B", True),
    ("echogenic liver",                _rx(r"\bechogenic liver\b"), "B", True),
    ("increased echogenicity",         _rx(r"\bincreased echogenicity\b"), "B", False),
    ("decreased hepatic attenuation",  _rx(r"\bdecreased hepatic attenuation\b"), "B", True),
    ("low attenuation",                _rx(r"\blow attenuation\b"), "B", False),
]
# fast substring pre-screen (skip notes with no possible trigger)
SCREEN = ("steato", "fatty", "nafld", "nash", "masld", "mash", "nafl",
          "echogenic", "attenuation", "metabolic dysfunction")

TARGET_ORGANS = {"liver", "hepatic", "hepatis"}
COMPETING_ORGANS = {"pancreas", "pancreatic", "gallbladder", "marrow", "omentum",
                    "omental", "mesenteric", "mesentery", "spleen", "splenic",
                    "renal", "kidney", "breast", "thymus", "thymic"}
SCOPE_TOKENS = 10

# ---- ConText lexicons (Harkema 2009 / Chapman 2001 style) ----
NEG_PRE = ["no evidence of", "no evidence for", "no sign of", "no signs of",
           "no findings of", "without evidence of", "negative for", "absence of",
           "free of", "no", "without", "denies", "denied", "deny", "not"]
NEG_POST = ["is negative", "are negative", "not seen", "not identified",
            "not appreciated", "ruled out", "unremarkable", "resolved"]
PSEUDO_NEG = ["no increase", "no significant change", "no interval change",
              "no change", "no new", "not necessarily", "not excluded",
              "cannot be excluded", "cannot exclude", "gram negative", "no evidence of interval"]
HEDGE = ["may represent", "may reflect", "cannot be excluded", "cannot exclude",
         "could represent", "could reflect", "concerning for", "suggestive of",
         "suspicious for", "question of", "questionable", "differential includes",
         "differential diagnosis", "possibly", "possible", "versus", "rule out",
         "r/o", "evaluate for", "worrisome for"]
HIST = ["history of", "hx of", "h/o", "status post", "s/p", "previously",
        "prior", "remote", "in the past", "years ago"]
FAMILY = ["family history of", "family hx", "fh of", "fh:", "maternal", "paternal",
          "mother", "father", "sister", "brother", "sibling", "parents",
          "grandmother", "grandfather", "aunt", "uncle"]
TERMINATION = ["but", "however", "although", "though", "yet", "except",
               "aside from", "nevertheless", "otherwise"]

TOKEN_RE = re.compile(r"[a-z0-9'/]+")
SENT_SPLIT = re.compile(r"[\n\r]+|(?<=[.;!?])\s+")


def _tokenize(s):
    return [(m.group(0), m.start()) for m in TOKEN_RE.finditer(s)]


def _phrase_positions(low, phrases):
    """Return list of (char_start, char_end) for any phrase occurrence."""
    out = []
    for ph in phrases:
        start = 0
        while True:
            i = low.find(ph, start)
            if i < 0:
                break
            out.append((i, i + len(ph)))
            start = i + 1
    return out


def _anatomical(words, hit_ti):
    """Return (pass:bool, organ_if_suppressed:str|None)."""
    lo, hi = max(0, hit_ti - SCOPE_TOKENS), min(len(words), hit_ti + SCOPE_TOKENS + 1)
    # nearest target and nearest competing within sentence (search whole sentence for comps)
    dt = None
    for j, w in enumerate(words):
        if w in TARGET_ORGANS:
            d = abs(j - hit_ti)
            if dt is None or d < dt:
                dt = d
    dc = None; corg = None
    for j, w in enumerate(words):
        if w in COMPETING_ORGANS:
            d = abs(j - hit_ti)
            if dc is None or d < dc:
                dc = d; corg = w
    comp_in_sent = dc is not None
    has_target10 = dt is not None and dt <= SCOPE_TOKENS
    nearest_competing = comp_in_sent and (dt is None or dc < dt)
    if nearest_competing:
        return False, corg
    if has_target10:
        return True, None
    if not comp_in_sent:
        return True, None
    return False, corg  # target not within 10, competing present but not nearest -> ambiguous


def _context(words, starts, sent_low, hit_ti, hit_char):
    """Return dict of flags: negated, family, historical, hedged."""
    # termination token indices
    term_idx = sorted(j for j, w in enumerate(words) if w in TERMINATION)
    seg_lo = max([j for j in term_idx if j < hit_ti], default=-1) + 1
    seg_hi = min([j for j in term_idx if j > hit_ti], default=len(words))

    def cue_token_indices(phrases):
        idxs = []
        for cs, ce in _phrase_positions(sent_low, phrases):
            ti = bisect.bisect_right(starts, cs) - 1
            if 0 <= ti < len(words):
                idxs.append((ti, cs, ce))
        return idxs

    pseudo_spans = _phrase_positions(sent_low, PSEUDO_NEG)
    def in_pseudo(cs):
        return any(a <= cs < b for a, b in pseudo_spans)

    flags = {"negated": False, "family": False, "historical": False, "hedged": False}
    # negation (pre, forward): cue before hit in segment, not pseudo
    for ti, cs, ce in cue_token_indices(NEG_PRE):
        if seg_lo <= ti < hit_ti and not in_pseudo(cs):
            flags["negated"] = True
    for ti, cs, ce in cue_token_indices(NEG_POST):
        if hit_ti < ti < seg_hi:
            flags["negated"] = True
    # hedge (pre, forward) — 'versus'/'differential' allowed either side in segment
    for ti, cs, ce in cue_token_indices(HEDGE):
        if seg_lo <= ti <= seg_hi:
            if ti < hit_ti or sent_low[cs:ce] in ("versus", "differential includes",
                                                  "differential diagnosis"):
                flags["hedged"] = True
    # historical (pre)
    for ti, cs, ce in cue_token_indices(HIST):
        if seg_lo <= ti < hit_ti:
            flags["historical"] = True
    # family (experiencer) — sentence-level, before hit
    for ti, cs, ce in cue_token_indices(FAMILY):
        if ti < hit_ti:
            flags["family"] = True
    return flags


def classify_note(text):
    """Classify one note. Returns aggregate flags/counters only (no text).
    Keys: a_pos, b_pos, c_hedged (bool); triggers (set of positive trigger names);
          excl (Counter: negation/family/historical); anat (Counter organ->n)."""
    res = {"a_pos": False, "b_pos": False, "c_hedged": False,
           "triggers": set(), "excl": Counter(), "anat": Counter()}
    if text is None:
        return res
    low = text.lower()
    if not any(s in low for s in SCREEN):
        return res

    for seg in SENT_SPLIT.split(text):
        slow = seg.lower()
        if not any(s in slow for s in SCREEN):
            continue
        # collect raw hits in this sentence
        hits = []
        for name, rgx, tier, self_anat in TRIGGERS:
            for m in rgx.finditer(seg):
                hits.append((m.start(), m.end(), name, tier, self_anat))
        if not hits:
            continue
        # dedup overlaps: keep longer spans (more specific)
        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        kept = []
        for h in hits:
            if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
                continue
            kept.append(h)

        toks = _tokenize(slow)
        words = [w for w, _ in toks]; starts = [s for _, s in toks]
        for cstart, cend, name, tier, self_anat in kept:
            hit_ti = bisect.bisect_right(starts, cstart) - 1
            if hit_ti < 0:
                hit_ti = 0
            # anatomical scoping
            if not self_anat:
                ok, organ = _anatomical(words, hit_ti)
                if not ok:
                    res["anat"][organ or "ambiguous"] += 1
                    continue
            # context assertion
            f = _context(words, starts, slow, hit_ti, cstart)
            if f["family"]:
                res["excl"]["family"] += 1
                continue
            if f["negated"]:
                res["excl"]["negation"] += 1
                continue
            if f["hedged"]:
                res["c_hedged"] = True
                res["triggers"].add(name + " [C]")
                continue
            # affirmed positive
            if f["historical"]:
                res["excl"]["historical"] += 1  # flagged, NOT excluded
            if tier == "A":
                res["a_pos"] = True
            else:
                res["b_pos"] = True
            res["triggers"].add(name)
    return res


# ===========================================================================
# DRIVER — behavior report on the locked population (no accuracy metrics)
# ===========================================================================
def main():
    con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
    pop = con.execute(
        f"SELECT hadm_id, subject_id, code_positive, admittime FROM read_parquet('{POP}')"
    ).fetchdf()
    locked_hadm = set(pop.hadm_id.astype("int64"))
    locked_subj = set(pop.subject_id.astype("int64"))

    # per-admission accumulators
    adm = {h: {"dc_a": False, "dc_b": False, "rad_a": False, "rad_b": False,
               "c": False} for h in locked_hadm}
    trig = Counter(); excl = Counter(); anat = Counter()
    outp_pos = []  # (subject_id, charttime, a, b) for null-hadm radiology positives

    def run(table, is_disch):
        cols = "hadm_id, subject_id, charttime, text"
        reader = con.execute(
            f"SELECT {cols} FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
        ).fetch_record_batch(3000)
        n = 0
        for batch in reader:
            d = batch.to_pydict()
            for k in range(len(d["text"])):
                r = classify_note(d["text"][k])
                if not (r["a_pos"] or r["b_pos"] or r["c_hedged"]):
                    continue
                h = d["hadm_id"][k]
                linked = h is not None and int(h) in locked_hadm
                subj = d["subject_id"][k]
                if linked:
                    a = adm[int(h)]
                    if is_disch:
                        a["dc_a"] |= r["a_pos"]; a["dc_b"] |= r["b_pos"]
                    else:
                        a["rad_a"] |= r["a_pos"]; a["rad_b"] |= r["b_pos"]
                    a["c"] |= r["c_hedged"]
                    trig.update(r["triggers"]); excl.update(r["excl"]); anat.update(r["anat"])
                elif (not is_disch) and h is None and subj is not None and int(subj) in locked_subj:
                    if r["a_pos"] or r["b_pos"]:
                        outp_pos.append((int(subj), d["charttime"][k], r["a_pos"], r["b_pos"]))
                n += 1
        return n

    print(f"note_phenotype VERSION {VERSION} ({FROZEN_DATE}) — behavior on locked population")
    print("classifying discharge ..."); run("discharge", True)
    print("classifying radiology ..."); run("radiology", False)

    a = pd.DataFrame.from_dict(adm, orient="index")
    a.index.name = "hadm_id"; a = a.reset_index()
    a["inp_A"] = a.dc_a | a.rad_a
    a["inp_B"] = a.dc_b | a.rad_b
    a["inp_AB"] = a.inp_A | a.inp_B
    a = a.merge(pop[["hadm_id", "subject_id", "code_positive", "admittime"]], on="hadm_id")
    N = len(a)

    def pct(x):
        return f"{x:,} ({100*x/N:.1f}%)"
    print("\n== NOTE-POSITIVE (inpatient-linked notes) ==")
    print(f"  Tier A definite         : {pct(int(a.inp_A.sum()))}")
    print(f"  Tier A+B                 : {pct(int(a.inp_AB.sum()))}")
    print(f"  Tier C (hedged) group    : {pct(int(a.c.sum()))}")
    print("\n== SOURCE of Tier A positives ==")
    both = a.dc_a & a.rad_a; dconly = a.dc_a & ~a.rad_a; rdonly = a.rad_a & ~a.dc_a
    print(f"  discharge only: {int(dconly.sum()):,}  radiology only: {int(rdonly.sum()):,}  "
          f"both: {int(both.sum()):,}")
    print("\n== TRIGGERS fired (positive, top 25) ==")
    for name, c in trig.most_common(25):
        print(f"    {name:34s} {c:,}")
    print("\n== SUPPRESSED / EXCLUDED (hit-level, linked notes) ==")
    print(f"  negation : {excl.get('negation',0):,}")
    print(f"  family   : {excl.get('family',0):,}")
    print(f"  historical (flagged, NOT excluded): {excl.get('historical',0):,}")
    print("  anatomical scoping suppressed, per nearest organ:")
    for organ, c in anat.most_common():
        print(f"    {organ:14s} {c:,}")
    print(f"  anatomical TOTAL: {sum(anat.values()):,}")

    # outpatient windows
    print("\n== OUTPATIENT RADIOLOGY (null-hadm, subject-linked) ==")
    op = pd.DataFrame(outp_pos, columns=["subject_id", "charttime", "a", "b"])
    op["charttime"] = pd.to_datetime(op["charttime"])
    a["admittime"] = pd.to_datetime(a["admittime"])
    for wname, (before, after) in OUTPATIENT_WINDOWS.items():
        merged = a[["hadm_id", "subject_id", "admittime", "inp_A", "inp_AB"]].merge(
            op, on="subject_id", how="inner")
        dt = (merged.charttime - merged.admittime).dt.total_seconds() / 86400.0
        inwin = (dt >= -before) & (dt <= after)
        add_A = merged[inwin & merged.a].hadm_id.unique()
        newpos = a[a.hadm_id.isin(set(add_A)) & ~a.inp_A]
        print(f"  window {wname} (−{before}/+{after} d): "
              f"admissions gaining Tier A from outpatient rad: {len(newpos):,}  "
              f"(new outpatient-inclusive Tier A total: {int(a.inp_A.sum())+len(newpos):,})")

    if os.environ.get("EMIT_BEHAVIOR"):
        with open("docs/note_phenotype_behavior.txt", "w") as fh:
            fh.write(f"VERSION {VERSION} {FROZEN_DATE}\nN={N}\n"
                     f"TierA={int(a.inp_A.sum())} TierAB={int(a.inp_AB.sum())} "
                     f"TierC={int(a.c.sum())}\n")


if __name__ == "__main__":
    main()
