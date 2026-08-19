#!/usr/bin/env python3
"""STEP 5 data — per-admission current vs historical Tier A note-positivity.

Two historical measures, per admission (inpatient-linked notes; no note text):
  * ConText temporality flag (the frozen rule's own 'historical' flag)
  * SECTION-based: hit fell in a PAST MEDICAL / SURGICAL HISTORY section (discharge)
Radiology hits count as current (impression). Writes a gitignored parquet.
Run: python scripts/note_historical.py
"""
import bisect
import re
import duckdb
from scripts.note_phenotype import (
    _iter_hits, TRIGGERS, _tokenize, _anatomical, _context, SENT_SPLIT, SCREEN, NOTE)
from scripts.masld_config import CLEAN_POP

OUT = "data/processed/note_historical.parquet"
HEADER_RE = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9 /,()'-]{1,45}?):")
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
locked = set(con.execute(f"SELECT hadm_id FROM read_parquet('{CLEAN_POP}')").fetchdf().hadm_id.astype("int64"))
pos_inp, cur_inp, pmh_hit, nonpmh_hit = set(), set(), set(), set()


def is_pmh(label):
    return label.startswith("PAST MEDICAL") or label.startswith("PAST SURGICAL") \
        or label in ("PMH", "PMHX", "PSH", "PAST HISTORY", "PAST ONCOLOGIC HISTORY")


def discharge_sections(text):
    """(section) list for affirmed Tier A hits in a discharge note."""
    hstarts, hlabels = [], []
    for m in HEADER_RE.finditer(text):
        hstarts.append(m.start()); hlabels.append(" ".join(m.group(1).split()).upper())
    out = []; last = 0; spans = []
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
                hits.append((mm.start(), mm.end(), scope))
        if not hits:
            continue
        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        kept = []
        for h in hits:
            if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
                continue
            kept.append(h)
        toks = _tokenize(slow); words = [w for w, _ in toks]; starts = [s for _, s in toks]
        for cstart, cend, scope in kept:
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
            sec = hlabels[bisect.bisect_right(hstarts, pos) - 1] if hstarts and pos >= hstarts[0] else "<pre>"
            out.append(sec)
    return out


def run(table, is_disch):
    reader = con.execute(
        f"SELECT hadm_id, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            h = d["hadm_id"][k]
            if h is None or int(h) not in locked:
                continue
            hh = int(h); txt = d["text"][k]
            for hit in _iter_hits(txt):
                if hit["disp"] == "positive" and hit["tier"] == "A":
                    pos_inp.add(hh)
                    if not hit["historical"]:
                        cur_inp.add(hh)
            if is_disch:
                for sec in discharge_sections(txt):
                    (pmh_hit if is_pmh(sec) else nonpmh_hit).add(hh)
            else:
                # radiology Tier A positive => current-section (impression)
                if any(hit["disp"] == "positive" and hit["tier"] == "A" for hit in _iter_hits(txt)):
                    nonpmh_hit.add(hh)


print("streaming discharge ..."); run("discharge", True)
print("streaming radiology ..."); run("radiology", False)
df = con.execute(f"SELECT hadm_id FROM read_parquet('{CLEAN_POP}')").fetchdf()
i = df.hadm_id.astype("int64")
df["pos_inp"] = i.isin(pos_inp); df["cur_inp"] = i.isin(cur_inp)
df["pmh_hit"] = i.isin(pmh_hit); df["nonpmh_hit"] = i.isin(nonpmh_hit)
con.register("h", df); con.execute(f"COPY h TO '{OUT}' (FORMAT parquet)")
print(f"wrote {OUT}: pos_inp={len(pos_inp):,} cur_inp={len(cur_inp):,} "
      f"pmh_hit={len(pmh_hit):,} nonpmh_hit={len(nonpmh_hit):,}")
