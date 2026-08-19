#!/usr/bin/env python3
"""STEP 4 — note & trigger descriptives.

Streams notes once. Per admission: note counts by type (DS/RR/AR), Tier A trigger
set, Tier C flag, and (discharge) the section each triggering hit fell in.
Reports co-occurrence, which triggers drive the recovery zone, and Tier C by cell.
Aggregate only; no note text. Writes frag_step4.md.

Run: python scripts/note_triggers.py
"""
import bisect
import os
import re
from collections import Counter, defaultdict

import pandas as pd
import duckdb

from scripts.note_phenotype import (
    _iter_hits, TRIGGERS, _tokenize, _anatomical, _context, SENT_SPLIT, SCREEN, NOTE,
)

FRAG = os.path.join(os.environ.get("SCRATCH", "/tmp"), "frag_step4.md")
HEADER_RE = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9 /,()'-]{1,45}?):")
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

frame = con.execute(
    "SELECT hadm_id, code_positive, note_b FROM read_parquet('data/processed/aim1a_frame.parquet')"
).fetchdf()
locked_hadm = set(frame.hadm_id.astype("int64"))

trigA = defaultdict(set)         # hadm -> set of Tier A trigger names
tierC = set()                    # hadm with a Tier C hit
ntype = defaultdict(lambda: Counter())   # hadm -> Counter(note_type)
sections = Counter()             # (discharge) section -> n note-positive-discharge hits


def discharge_sections(text):
    """(trigger, section) for affirmed Tier A hits in a discharge note (faithful loop)."""
    hstarts, hlabels = [], []
    for m in HEADER_RE.finditer(text):
        hstarts.append(m.start()); hlabels.append(" ".join(m.group(1).split()).upper())
    out = []
    last = 0
    spans = []
    for m in SENT_SPLIT.finditer(text):
        spans.append((last, text[last:m.start()])); last = m.end()
    spans.append((last, text[last:]))
    for off, seg in spans:
        slow = seg.lower()
        if not any(s in slow for s in SCREEN):
            continue
        hits = []
        for name, rgx, tier, scope in TRIGGERS:
            if tier != "A":
                continue
            for mm in rgx.finditer(seg):
                hits.append((mm.start(), mm.end(), name, scope))
        if not hits:
            continue
        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        kept = []
        for h in hits:
            if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
                continue
            kept.append(h)
        toks = _tokenize(slow); words = [w for w, _ in toks]; starts = [s for _, s in toks]
        for cstart, cend, name, scope in kept:
            ti = bisect.bisect_right(starts, cstart) - 1
            if ti < 0:
                ti = 0
            if scope != "none":
                ok, _o, _r = _anatomical(words, ti, strict=(scope == "strict"))
                if not ok:
                    continue
            fl = _context(words, ti)
            if fl["family"] or fl["negated"] or fl["hedged"]:
                continue
            pos = off + cstart
            sec = hlabels[bisect.bisect_right(hstarts, pos) - 1] if hstarts and pos >= hstarts[0] else "<preamble>"
            out.append((name, sec))
    return out


def run(table, is_disch):
    reader = con.execute(
        f"SELECT hadm_id, note_type, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            h = d["hadm_id"][k]
            if h is None or int(h) not in locked_hadm:
                continue
            hh = int(h); txt = d["text"][k]
            ntype[hh][d["note_type"][k]] += 1
            posA = set(); hasC = False
            for hit in _iter_hits(txt):
                if hit["disp"] == "positive" and hit["tier"] == "A":
                    posA.add(hit["name"])
                elif hit["disp"] == "tierC":
                    hasC = True
            if posA:
                trigA[hh] |= posA
                if is_disch:
                    for _name, sec in discharge_sections(txt):
                        sections[sec] += 1
            if hasC:
                tierC.add(hh)


print("classifying discharge ..."); run("discharge", True)
print("classifying radiology ..."); run("radiology", False)

# ---- assemble ----
frame["trigset"] = frame.hadm_id.map(lambda h: frozenset(trigA.get(int(h), set())))
frame["ntrig"] = frame.trigset.map(len)
frame["tierC"] = frame.hadm_id.map(lambda h: int(h) in tierC)
frame["cell"] = frame.apply(lambda r: ("code+" if r.code_positive else "code-") +
                            ("/note+" if r.note_b else "/note-"), axis=1)
nt = pd.DataFrame([{"hadm_id": h, "DS": c.get("DS", 0), "RR": c.get("RR", 0), "AR": c.get("AR", 0)}
                   for h, c in ntype.items()])

L = []
def w(s=""): L.append(s)
w("## Step 4 — Note & trigger descriptives\n")
w("### Notes per admission by type (linked notes)\n")
w("| type | % admissions with ≥1 | median | p95 |")
w("| --- | --: | --: | --: |")
Nlinked = len(nt)
for t in ["DS", "RR", "AR"]:
    w(f"| {t} | {100*(nt[t]>0).mean():.1f}% | {nt[t].median():.0f} | {nt[t].quantile(.95):.0f} |")
w("")

npos = frame[frame.note_b]
w("### Section of triggering hit (discharge, among note-positive) — top 12\n")
w("| section | hits |"); w("| --- | --: |")
tot_sec = sum(sections.values())
for sec, n in sections.most_common(12):
    w(f"| {sec} | {n:,} ({100*n/tot_sec:.1f}%) |")
w("")

w("### Tier A triggers per note-positive admission\n")
w(f"- 1 trigger: {int((npos.ntrig==1).sum()):,} ({100*(npos.ntrig==1).mean():.1f}%); "
  f"2: {int((npos.ntrig==2).sum()):,}; 3+: {int((npos.ntrig>=3).sum()):,}.\n")

# co-occurrence (top pairs)
pair = Counter()
for s in npos.trigset:
    ss = sorted(s)
    for i in range(len(ss)):
        for j in range(i+1, len(ss)):
            pair[(ss[i], ss[j])] += 1
w("### Top Tier A trigger co-occurrences (admissions with both)\n")
w("| trigger A | trigger B | n |"); w("| --- | --- | --: |")
for (a, b), n in pair.most_common(12):
    w(f"| {a} | {b} | {n:,} |")
w("")

# triggers driving recovery zone vs code+/note+
rz = frame[frame.cell == "code-/note+"]; cc = frame[frame.cell == "code+/note+"]
freq_rz = Counter(); freq_cc = Counter()
for s in rz.trigset:
    freq_rz.update(s)
for s in cc.trigset:
    freq_cc.update(s)
w("### Which triggers drive the recovery zone (code−/note+) vs code+/note+\n")
w(f"Recovery-zone n={len(rz):,}, code+/note+ n={len(cc):,}. Trigger presence %:\n")
w("| trigger | recovery-zone % | code+/note+ % |")
w("| --- | --: | --: |")
for t, _ in freq_rz.most_common(14):
    w(f"| {t} | {100*freq_rz[t]/len(rz):.1f}% | {100*freq_cc.get(t,0)/len(cc):.1f}% |")
solo = rz[rz.ntrig == 1]
solo_top = Counter(next(iter(s)) for s in solo.trigset if len(s) == 1).most_common(5)
w(f"\n**Fragility check:** {100*(rz.ntrig==1).mean():.1f}% of recovery-zone admissions rest "
  f"on a SINGLE trigger; the most common single drivers: "
  + ", ".join(f"{t} ({n:,})" for t, n in solo_top) + ".\n")

w("### Tier C (hedged) distribution across 2×2 cells\n")
w("| cell | n | with Tier C hit | % |")
w("| --- | --: | --: | --: |")
for cell in ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]:
    g = frame[frame.cell == cell]
    w(f"| {cell} | {len(g):,} | {int(g.tierC.sum()):,} | {100*g.tierC.mean():.2f}% |")
w("")

os.makedirs(os.path.dirname(FRAG), exist_ok=True)
with open(FRAG, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {FRAG}")
print(f"recovery-zone single-trigger: {100*(rz.ntrig==1).mean():.1f}%  "
      f"top RZ trigger: {freq_rz.most_common(1)}")
