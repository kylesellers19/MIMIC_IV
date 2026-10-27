#!/usr/bin/env python3
"""DIAGNOSTIC: what the sentence selection in scripts/liver_sentences.py leaves out.

--anatomy-only measures the original anatomy test alone; the default measures the current selection
(anatomy, liver heading, liver disease term, unnamed steatosis).

The extractor keeps a (rejoined) sentence only if a token contains "hepat" or starts with "liver".
A sentence that states steatosis without naming the organ ("NAFLD", "NASH cirrhosis", "Diffuse
steatosis.", "Increased echogenicity consistent with fatty infiltration." under a LIVER: heading)
never reaches the model. This counts those sentences and the admissions that have them, and checks
the frozen rule's positive admissions (note_b) against what the kept units contain.

Same scope and linkage as liver_sentences.run(): DEV+TEST admissions, discharge and inpatient
radiology by hadm_id, outpatient radiology by subject within -365/+30 days.

PRIVACY: counts only. No text is printed or written.
USAGE: scripts/run0919_env.sh diagnostics/llm_review_audit/filter_misses.py
"""
import re
import sys
import time
from collections import Counter, defaultdict

import duckdb
import pandas as pd

sys.path.insert(0, ".")
import scripts.liver_sentences as LS
from scripts.liver_sentences import (FRAME, HEADER_RE, NOTE, anatomy_hits, build_admission_set,
                                     rejoin_wrapped_lines, section_spans, sentence_spans, category_at,
                                     selection_reason)
from scripts.note_phenotype import COMPETING_ORGANS, _tokenize

# Steatosis statements, grouped so the misses can be read by kind. Word boundaries keep NASH from
# matching Nashville and MASH from matching mashed.
KINDS = [
    ("abbreviation (NAFLD/NASH/MASLD/MASH/NAFL/MAFLD)", re.compile(r"\b(?:nafld|nash|masld|mash|nafl|mafld)\b")),
    ("steatosis / steatotic", re.compile(r"steato")),
    ("fatty infiltration / fatty change / fatty liver", re.compile(r"fatty (?:infiltration|change|liver)")),
    ("echogenicity / attenuation", re.compile(r"echogenic|attenuation")),
]


def kinds_of(low):
    return [name for name, rx in KINDS if rx.search(low)]


def heading_before(heads, pos):
    """Label of the nearest heading at or before pos, upper-cased, or ''."""
    lab = ""
    for start, label in heads:
        if start > pos:
            break
        lab = label
    return lab


def scan_note(text):
    """-> (kinds in kept liver sentences, Counter of (kind, section, context) for dropped sentences).
    context: 'other organ named' when a frozen-rule competing organ is in the sentence, else
    'under a liver heading' when the nearest heading names the liver, else 'no organ named'."""
    if not text:
        return set(), Counter()
    low_all = text.lower()
    if not any(rx.search(low_all) for _, rx in KINDS):
        return set(), Counter()
    secs = section_spans(text)
    heads = [(m.start(), " ".join(m.group(1).strip().upper().split())) for m in HEADER_RE.finditer(text)]
    src = rejoin_wrapped_lines(text)
    kept_kinds, missed = set(), Counter()
    for s, e in sentence_spans(src):
        frag = src[s:e]
        k = kinds_of(frag.lower())
        if not k:
            continue
        if selection_reason(frag, heading_before(heads, s), anatomy_hits(frag)[1]):
            kept_kinds.update(k)
        else:
            words = {w for w, _ in _tokenize(frag.lower())}
            lab = heading_before(heads, s)
            ctx = ("other organ named" if words & COMPETING_ORGANS else
                   "under a liver heading" if ("LIVER" in lab or "HEPAT" in lab) else "no organ named")
            for name in k:
                missed[(name, category_at(secs, s), ctx)] += 1
    return kept_kinds, missed


def main():
    LS.ANATOMY_ONLY = "--anatomy-only" in sys.argv
    print(f"selection measured: {'anatomy only' if LS.ANATOMY_ONLY else 'current (anatomy, liver heading, disease term, unnamed steatosis)'}")
    t0 = time.time()
    con = duckdb.connect()
    con.execute("SET memory_limit='12GB'")
    adm = build_admission_set(con, ["DEV", "TEST"])
    hadms, subs = set(adm.hadm_id.astype("int64")), set(adm.subject_id.astype("int64"))
    by_adm = defaultdict(lambda: [set(), Counter()])
    out_by_subject = defaultdict(list)
    missed_total = Counter()
    for table, is_disch in (("discharge", True), ("radiology", False)):
        reader = con.execute(f"SELECT hadm_id, subject_id, charttime, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')").fetch_record_batch(4000)
        for batch in reader:
            d = batch.to_pydict()
            for k in range(len(d["text"])):
                h, sj = d["hadm_id"][k], d["subject_id"][k]
                inpatient = h is not None and int(h) in hadms
                outpatient = (not is_disch) and h is None and sj is not None and int(sj) in subs
                if not (inpatient or outpatient):
                    continue
                kept, missed = scan_note(d["text"][k])
                if not kept and not missed:
                    continue
                ntype = "discharge" if is_disch else ("radiology_inpatient" if inpatient else "radiology_outpatient")
                for (name, sec, ctx), n in missed.items():
                    missed_total[(name, sec, ntype, ctx)] += n
                if inpatient:
                    by_adm[int(h)][0].update(kept); by_adm[int(h)][1].update(missed)
                else:
                    out_by_subject[int(sj)].append((d["charttime"][k], kept, missed))
        print(f"  scanned {table} ({time.time() - t0:.0f}s)", flush=True)
    adm["admittime"] = pd.to_datetime(adm["admittime"])
    for r in adm.itertuples(index=False):
        for ct, kept, missed in out_by_subject.get(int(r.subject_id), []):
            if ct is None:
                continue
            dt = (pd.Timestamp(ct) - r.admittime).total_seconds() / 86400.0
            if -365 <= dt <= 30:
                by_adm[int(r.hadm_id)][0].update(kept); by_adm[int(r.hadm_id)][1].update(missed)

    # sentence level
    t = pd.DataFrame([{"kind": k, "section": s, "note_type": n, "context": c, "sentences": v}
                      for (k, s, n, c), v in missed_total.items()])
    print("\nsentences with a steatosis term but no liver word (dropped by the anatomy filter):")
    print(t.pivot_table(index="kind", columns="note_type", values="sentences", aggfunc="sum", fill_value=0, margins=True).to_string())
    print("\n  by section:")
    print(t.pivot_table(index="kind", columns="section", values="sentences", aggfunc="sum", fill_value=0, margins=True).to_string())
    print("\n  by organ context:")
    print(t.pivot_table(index="kind", columns="context", values="sentences", aggfunc="sum", fill_value=0, margins=True).to_string())

    # admission level
    strong = [n for n, _ in KINDS[:3]]
    rows = []
    for h, (kept, missed) in by_adm.items():
        miss_kinds = {name for (name, _s, ctx) in missed if ctx != "other organ named"}
        rows.append({"hadm_id": h,
                     "kept_strong": bool(kept & set(strong)), "kept_any": bool(kept),
                     "missed_strong": bool(miss_kinds & set(strong)), "missed_abbrev": KINDS[0][0] in miss_kinds,
                     "missed_steato": KINDS[1][0] in miss_kinds})
    a = pd.DataFrame(rows)
    only = a[a.missed_strong & ~a.kept_strong]
    print(f"\nadmissions with a strong steatosis term (abbreviation, steato-, fatty infiltration/change);")
    print(f"dropped sentences naming a competing organ are not counted as misses:")
    print(f"  in a kept liver sentence                         {int(a.kept_strong.sum()):,}")
    print(f"  ONLY in sentences the filter drops               {len(only):,}")
    print(f"    of which an abbreviation is among the dropped  {int(only.missed_abbrev.sum()):,}")
    print(f"    of which steato- is among the dropped          {int(only.missed_steato.sum()):,}")

    fr = con.execute(f"SELECT hadm_id, note_b FROM read_parquet('{FRAME}')").fetchdf()
    fr = fr[fr.hadm_id.isin(hadms)].merge(a, on="hadm_id", how="left").fillna(False)
    pos = fr[fr.note_b.astype(bool)]
    print(f"\nfrozen note rule positive (note_b) among dev/test admissions: {len(pos):,}")
    print(f"  with a strong term in a kept liver sentence      {int(pos.kept_strong.astype(bool).sum()):,}")
    print(f"  with any steatosis/echo term in a kept sentence  {int(pos.kept_any.astype(bool).sum()):,}")
    print(f"  with a strong term ONLY in dropped sentences     {int((pos.missed_strong.astype(bool) & ~pos.kept_strong.astype(bool)).sum()):,}")
    print(f"  with no steatosis/echo term in any kept sentence {int((~pos.kept_any.astype(bool)).sum()):,}")
    print(f"\nruntime {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
