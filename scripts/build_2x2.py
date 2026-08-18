#!/usr/bin/env python3
"""STEP 1 — Aim 1a 2x2: code status x note status on the cleaned locked population.

Streams notes once, classifies under v1.1.0 (frozen classify_note) and v1.0.0
(reconstructed: v1.0.0 triggers + original substring context, faithful to the
note-phenotype-v1.0.0 tag). Links inpatient (hadm_id) + outpatient radiology
(subject_id, windows). Note-positive = Tier A definite. Writes a per-admission
cell frame (credentialed, gitignored) and prints the four 2x2 versions.

Run: python scripts/build_2x2.py
"""
import bisect
from collections import Counter

import numpy as np
import pandas as pd
import duckdb

from scripts.note_phenotype import (
    classify_note, TRIGGERS, _rx, _tokenize, _anatomical, SENT_SPLIT, SCREEN,
    NOTE, TERMINATION, NEG_PRE, NEG_POST, PSEUDO_NEG, HEDGE, HIST, FAMILY, VERSION,
)
from scripts.masld_config import DATA, CLEAN_POP, LOCKED_POP, MASLD_PREDICATE

OUT_FRAME = "data/processed/aim1a_frame.parquet"
WIN = {"primary": (365, 30), "sens": (90, 30)}

# ---- v1.0.0 reconstruction (triggers + original substring context) ----
PROMOTED = {"fatty replacement", "fatty deposition", "fatty degeneration",
            "fatty metamorphosis", "fatty infiltrate"}
V100 = []
for name, rx, tier, scope in TRIGGERS:
    if name in PROMOTED:
        continue
    if name == "fatty infiltration":
        scope = "standard"
    V100.append((name, rx, tier, scope))
V100.append(("fatty (bare)", _rx(r"\bfatty\b"), "A", "standard"))


def _pp(low, phrases):
    out = []
    for ph in phrases:
        s = 0
        while True:
            i = low.find(ph, s)
            if i < 0:
                break
            out.append((i, i + len(ph))); s = i + 1
    return out


def _ctx_v100(words, starts, low, hit_ti):
    term = sorted(j for j, w in enumerate(words) if w in TERMINATION)
    lo = max([j for j in term if j < hit_ti], default=-1) + 1
    hi = min([j for j in term if j > hit_ti], default=len(words))

    def cti(ph):
        out = []
        for cs, ce in _pp(low, ph):
            ti = bisect.bisect_right(starts, cs) - 1
            if 0 <= ti < len(words):
                out.append((ti, cs, ce))
        return out
    pseudo = _pp(low, PSEUDO_NEG)
    f = {"neg": False, "fam": False, "hed": False}
    for ti, cs, ce in cti(NEG_PRE):
        if lo <= ti < hit_ti and not any(a <= cs < b for a, b in pseudo):
            f["neg"] = True
    for ti, cs, ce in cti(NEG_POST):
        if hit_ti < ti < hi:
            f["neg"] = True
    for ti, cs, ce in cti(HEDGE):
        if lo <= ti <= hi and (ti < hit_ti or low[cs:ce] in
                               ("versus", "differential includes", "differential diagnosis")):
            f["hed"] = True
    for ti, cs, ce in cti(FAMILY):
        if ti < hit_ti:
            f["fam"] = True
    return f


def tierA_v100(text):
    """True iff any affirmed Tier A positive under frozen v1.0.0."""
    if text is None:
        return False
    low = text.lower()
    if not any(s in low for s in SCREEN):
        return False
    for seg in SENT_SPLIT.split(text):
        slow = seg.lower()
        if not any(s in slow for s in SCREEN):
            continue
        hits = []
        for name, rgx, tier, scope in V100:
            for m in rgx.finditer(seg):
                hits.append((m.start(), m.end(), name, tier, scope))
        if not hits:
            continue
        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        kept = []
        for h in hits:
            if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
                continue
            kept.append(h)
        toks = _tokenize(slow); words = [w for w, _ in toks]; starts = [s for _, s in toks]
        for cstart, cend, name, tier, scope in kept:
            ti = bisect.bisect_right(starts, cstart) - 1
            if ti < 0:
                ti = 0
            if scope != "none":
                ok, _o, _r = _anatomical(words, ti, strict=(scope == "strict"))
                if not ok:
                    continue
            f = _ctx_v100(words, starts, slow, ti)
            if f["fam"] or f["neg"] or f["hed"]:
                continue
            if tier == "A":
                return True
    return False


con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
clean = con.execute(f"SELECT * FROM read_parquet('{CLEAN_POP}')").fetchdf()
locked = con.execute(
    f"SELECT hadm_id, admittime, has_dc, has_rad FROM read_parquet('{LOCKED_POP}')"
).fetchdf()
pop = clean.merge(locked, on="hadm_id", how="left")
locked_hadm = set(pop.hadm_id.astype("int64"))
locked_subj = set(pop.subject_id.astype("int64"))

note_a = set(); note_d = set(); outp = []


def run(table, is_disch):
    reader = con.execute(
        f"SELECT hadm_id, subject_id, charttime, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            h = d["hadm_id"][k]; subj = d["subject_id"][k]; txt = d["text"][k]
            if h is not None and int(h) in locked_hadm:
                if classify_note(txt)["a_pos"]:
                    note_a.add(int(h))
                if tierA_v100(txt):
                    note_d.add(int(h))
            elif (not is_disch) and h is None and subj is not None and int(subj) in locked_subj:
                if classify_note(txt)["a_pos"]:
                    outp.append((int(subj), d["charttime"][k]))


print(f"build_2x2 (rule v{VERSION}); classifying ...")
print("  discharge ..."); run("discharge", True)
print("  radiology ..."); run("radiology", False)

pop["note_a"] = pop.hadm_id.isin(note_a)          # (a) v1.1.0 inpatient
pop["note_d"] = pop.hadm_id.isin(note_d)          # (d) v1.0.0 inpatient
op = pd.DataFrame(outp, columns=["subject_id", "charttime"])
op["charttime"] = pd.to_datetime(op["charttime"])
pop["admittime"] = pd.to_datetime(pop["admittime"])
for wn, (before, after) in WIN.items():
    m = pop[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
    dt = (m.charttime - m.admittime).dt.total_seconds() / 86400.0
    add = set(m[(dt >= -before) & (dt <= after)].hadm_id.astype("int64"))
    pop[f"note_{'b' if wn=='primary' else 'c'}"] = pop.note_a | pop.hadm_id.isin(add)

# MASLD seq_num for code+ admissions (Step 2)
seq = con.execute(f"""
  SELECT hadm_id, min(seq_num) AS masld_min_seq
  FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}})
  WHERE {MASLD_PREDICATE} GROUP BY hadm_id
""").fetchdf()
pop = pop.merge(seq, on="hadm_id", how="left")
pop["masld_principal"] = (pop.masld_min_seq == 1)

# persist frame (credentialed, gitignored)
keep_cols = (["hadm_id", "subject_id", "code_positive", "note_a", "note_b", "note_c", "note_d",
              "age", "gender", "race", "insurance", "language", "admission_type", "los_days",
              "n_diagnoses", "has_dc", "has_rad", "masld_min_seq", "masld_principal"]
             + [c for c in pop.columns if c.startswith("miss_lab_") or c in
                ("has_BMI", "has_SBP", "has_DBP")])
pop_out = pop[keep_cols].copy()
con.register("f", pop_out); con.execute(f"COPY f TO '{OUT_FRAME}' (FORMAT parquet)")
print(f"\nwrote {OUT_FRAME}: {len(pop_out):,} rows, {len(keep_cols)} cols")

# ---- Step 1 output: four 2x2 versions ----
N = len(pop)
def cells(nt):
    cp = pop.code_positive.astype(bool); nt = pop[nt].astype(bool)
    return {"code+/note+": int((cp & nt).sum()), "code-/note+": int((~cp & nt).sum()),
            "code+/note-": int((cp & ~nt).sum()), "code-/note-": int((~cp & ~nt).sum())}
def subj_cells(notecol):
    g = pop.groupby("subject_id").agg(c=("code_positive", "max"), n=(notecol, "max"))
    cp = g.c.astype(bool); nt = g.n.astype(bool)
    return {"code+/note+": int((cp & nt).sum()), "code-/note+": int((~cp & nt).sum()),
            "code+/note-": int((cp & ~nt).sum()), "code-/note-": int((~cp & ~nt).sum())}, len(g)

CONF = [("a", "v1.1.0 inpatient-linked"), ("b", "v1.1.0 + outpatient 365/30  [PRIMARY]"),
        ("c", "v1.1.0 + outpatient 90/30  (sensitivity)"), ("d", "v1.0.0 inpatient-linked")]
print("\n" + "=" * 74 + "\nSTEP 1 — 2x2 (admission grain, n and % of population)\n" + "=" * 74)
for key, label in CONF:
    c = cells(f"note_{key}")
    print(f"\n({key}) {label}   N={N:,}")
    for cell, n in c.items():
        print(f"    {cell:12s} {n:>8,} ({100*n/N:5.2f}%)")
print("\n" + "=" * 74 + "\nSTEP 1 — 2x2 (SUBJECT grain; code+/note+ = ANY admission code+/note+)\n" + "=" * 74)
for key, label in CONF:
    c, ns = subj_cells(f"note_{key}")
    print(f"\n({key}) {label}   subjects={ns:,}")
    for cell, n in c.items():
        print(f"    {cell:12s} {n:>8,} ({100*n/ns:5.2f}%)")

# primary vs v1.0.0 difference (recovery zone)
rb = cells("note_b")["code-/note+"]; rd = cells("note_d")["code-/note+"]
print(f"\nRecovery zone (code-/note+): primary(b)={rb:,}  v1.0.0(d)={rd:,}  "
      f"difference={rb-rd:+,} ({100*(rb-rd)/rd:+.1f}% vs v1.0.0)")
