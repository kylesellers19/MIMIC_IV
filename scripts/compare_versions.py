#!/usr/bin/env python3
"""STEP 3 — v1.0.0 vs v1.1.0 behavior comparison on the locked population.

Computes per-admission Tier A status under THREE configs in one pass so the
change decomposes cleanly:
  (1) FROZEN v1.0.0  = v1.0.0 triggers + original (buggy substring) context
  (2) v1.0.0 triggers + FIXED token context  (isolates the negation fix)
  (3) v1.1.0 FINAL   = v1.1.0 triggers + fixed context
Reports v1.1.0 source/trigger/suppression + both outpatient windows, and net
gained/lost vs frozen v1.0.0 with code-status split (to show how the revision
moves the recovery zone — NOT validation). No accuracy metrics. Aggregate only.

Run: python scripts/compare_versions.py
"""
import bisect
from collections import Counter

import pandas as pd
import duckdb

from scripts.note_phenotype import (
    TRIGGERS, _rx, _tokenize, _anatomical, _context, SENT_SPLIT, SCREEN,
    NOTE, POP, VERSION, OUTPATIENT_WINDOWS,
    NEG_PRE, NEG_POST, PSEUDO_NEG, HEDGE, HIST, FAMILY, TERMINATION,
)

PROMOTED = {"fatty replacement", "fatty deposition", "fatty degeneration",
            "fatty metamorphosis", "fatty infiltrate"}
V110 = list(TRIGGERS)
V100 = []
for name, rx, tier, scope in TRIGGERS:
    if name in PROMOTED:
        continue
    if name == "fatty infiltration":
        scope = "standard"
    V100.append((name, rx, tier, scope))
V100.append(("fatty (bare)", _rx(r"\bfatty\b"), "A", "standard"))


# ---- original v1.0.0 (buggy substring) context, to reproduce the frozen rule ----
def _pp_v100(low, phrases):
    out = []
    for ph in phrases:
        s = 0
        while True:
            i = low.find(ph, s)
            if i < 0:
                break
            out.append((i, i + len(ph))); s = i + 1
    return out


def _context_v100(words, starts, sent_low, hit_ti):
    term_idx = sorted(j for j, w in enumerate(words) if w in TERMINATION)
    seg_lo = max([j for j in term_idx if j < hit_ti], default=-1) + 1
    seg_hi = min([j for j in term_idx if j > hit_ti], default=len(words))

    def cti(phrases):
        idxs = []
        for cs, ce in _pp_v100(sent_low, phrases):
            ti = bisect.bisect_right(starts, cs) - 1
            if 0 <= ti < len(words):
                idxs.append((ti, cs, ce))
        return idxs

    pseudo = _pp_v100(sent_low, PSEUDO_NEG)
    fl = {"negated": False, "family": False, "historical": False, "hedged": False}
    for ti, cs, ce in cti(NEG_PRE):
        if seg_lo <= ti < hit_ti and not any(a <= cs < b for a, b in pseudo):
            fl["negated"] = True
    for ti, cs, ce in cti(NEG_POST):
        if hit_ti < ti < seg_hi:
            fl["negated"] = True
    for ti, cs, ce in cti(HEDGE):
        if seg_lo <= ti <= seg_hi and (ti < hit_ti or sent_low[cs:ce] in
                                       ("versus", "differential includes", "differential diagnosis")):
            fl["hedged"] = True
    for ti, cs, ce in cti(HIST):
        if seg_lo <= ti < hit_ti:
            fl["historical"] = True
    for ti, cs, ce in cti(FAMILY):
        if ti < hit_ti:
            fl["family"] = True
    return fl


def classify(text, triggers, buggy):
    res = {"a": False, "b": False, "c": False, "trig": set(),
           "anat": Counter(), "excl": Counter()}
    if text is None:
        return res
    low = text.lower()
    if not any(s in low for s in SCREEN):
        return res
    for seg in SENT_SPLIT.split(text):
        slow = seg.lower()
        if not any(s in slow for s in SCREEN):
            continue
        hits = []
        for name, rgx, tier, scope in triggers:
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
                ok, organ, reason = _anatomical(words, ti, strict=(scope == "strict"))
                if not ok:
                    res["anat"][organ or "ambiguous"] += 1
                    continue
            f = _context_v100(words, starts, slow, ti) if buggy else _context(words, ti)
            if f["family"]:
                res["excl"]["family"] += 1; continue
            if f["negated"]:
                res["excl"]["negation"] += 1; continue
            if f["hedged"]:
                res["c"] = True; continue
            if f["historical"]:
                res["excl"]["historical"] += 1
            if tier == "A":
                res["a"] = True
            else:
                res["b"] = True
            res["trig"].add(name)
    return res


con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
pop = con.execute(
    f"SELECT hadm_id, subject_id, code_positive, admittime FROM read_parquet('{POP}')"
).fetchdf()
locked_hadm = set(pop.hadm_id.astype("int64"))
locked_subj = set(pop.subject_id.astype("int64"))
code_pos = dict(zip(pop.hadm_id.astype("int64"), pop.code_positive))

A_frozen = set(); A_v100fix = set(); A_v110 = set(); AB_v110 = set(); C_v110 = set()
dcA = set(); radA = set()
trig110 = Counter(); anat110 = Counter(); excl110 = Counter()
outp_pos = []


def run(table, is_disch):
    reader = con.execute(
        f"SELECT hadm_id, subject_id, charttime, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            h = d["hadm_id"][k]; subj = d["subject_id"][k]; txt = d["text"][k]
            if h is not None and int(h) in locked_hadm:
                hh = int(h)
                if classify(txt, V100, True)["a"]:
                    A_frozen.add(hh)
                if classify(txt, V100, False)["a"]:
                    A_v100fix.add(hh)
                r1 = classify(txt, V110, False)
                if r1["a"]:
                    A_v110.add(hh); (dcA if is_disch else radA).add(hh)
                if r1["a"] or r1["b"]:
                    AB_v110.add(hh)
                if r1["c"]:
                    C_v110.add(hh)
                trig110.update(r1["trig"]); anat110.update(r1["anat"]); excl110.update(r1["excl"])
            elif (not is_disch) and h is None and subj is not None and int(subj) in locked_subj:
                if classify(txt, V110, False)["a"]:
                    outp_pos.append((int(subj), d["charttime"][k]))


print(f"compare_versions: frozen v1.0.0 vs v{VERSION}")
print("scanning discharge ..."); run("discharge", True)
print("scanning radiology ..."); run("radiology", False)

N = len(pop)
def pc(x):
    return f"{x:,} ({100*x/N:.1f}%)"
def split(s):
    cp = sum(1 for h in s if code_pos.get(h)); return cp, len(s) - cp

print("\n== Tier A definite (inpatient-linked) ==")
print(f"  (1) FROZEN v1.0.0                : {pc(len(A_frozen))}   [freeze reported 27,293]")
print(f"  (2) v1.0.0 triggers + neg-FIX    : {pc(len(A_v100fix))}")
print(f"  (3) v1.1.0 FINAL                 : {pc(len(A_v110))}")
print(f"  Tier A+B v1.1.0: {pc(len(AB_v110))}   Tier C v1.1.0: {pc(len(C_v110))}")

print("\n== decomposition ==")
print(f"  negation fix alone (2 vs 1): +{len(A_v100fix - A_frozen):,} / "
      f"-{len(A_frozen - A_v100fix):,} admissions")
print(f"  trigger changes (3 vs 2)   : +{len(A_v110 - A_v100fix):,} / "
      f"-{len(A_v100fix - A_v110):,} admissions")

lost = A_frozen - A_v110; gained = A_v110 - A_frozen
lcp, lcn = split(lost); gcp, gcn = split(gained)
print("\n== NET CHANGE vs FROZEN v1.0.0 (code split — not validation) ==")
print(f"  LOST   (v1.0.0+, v1.1.0−): {len(lost):,}  (code+ {lcp:,} / code− {lcn:,})")
print(f"  GAINED (v1.0.0−, v1.1.0+): {len(gained):,}  (code+ {gcp:,} / code− {gcn:,})")

print("\n== v1.1.0 SOURCE of Tier A ==")
print(f"  discharge only {len(dcA-radA):,} · radiology only {len(radA-dcA):,} · both {len(dcA&radA):,}")
print("\n== v1.1.0 TRIGGERS (positive, top 25) ==")
for name, c in trig110.most_common(25):
    print(f"    {name:34s} {c:,}")
print("\n== v1.1.0 SUPPRESSED / EXCLUDED ==")
print(f"  negation {excl110.get('negation',0):,} · family {excl110.get('family',0):,} · "
      f"historical(flagged) {excl110.get('historical',0):,}")
for organ, c in anat110.most_common():
    print(f"    anat {organ:16s} {c:,}")
print(f"  anatomical TOTAL: {sum(anat110.values()):,}")

print("\n== v1.1.0 OUTPATIENT windows ==")
op = pd.DataFrame(outp_pos, columns=["subject_id", "charttime"])
op["charttime"] = pd.to_datetime(op["charttime"])
adm = pop[["hadm_id", "subject_id", "admittime"]].copy()
adm["admittime"] = pd.to_datetime(adm["admittime"])
for wn, (before, after) in OUTPATIENT_WINDOWS.items():
    m = adm.merge(op, on="subject_id", how="inner")
    dt = (m.charttime - m.admittime).dt.total_seconds() / 86400.0
    addh = set(m[(dt >= -before) & (dt <= after)].hadm_id.astype("int64"))
    newpos = [h for h in addh if h not in A_v110]
    ncp = sum(1 for h in newpos if code_pos.get(h))
    print(f"  {wn} (−{before}/+{after}d): +{len(newpos):,} (code+ {ncp:,} / code− {len(newpos)-ncp:,}); "
          f"new Tier A total {len(A_v110)+len(newpos):,}")
