#!/usr/bin/env python3
"""DIAGNOSTIC: how often a kept liver unit loses a fat/steatosis word to a line break.

WHY
    SENT_SPLIT (the frozen rule's splitter, reused by scripts/liver_sentences.py) breaks on every
    newline, and MIMIC notes are hard-wrapped near 80 characters, so most kept "sentences" are line
    fragments. A statement split across lines keeps only the line naming the liver; a fat word on the
    neighbouring line is dropped before the model sees anything.

WHAT IT MEASURES, COUNTS ONLY
    For every liver unit in the dev/test notes, the enclosing REJOINED sentence: line breaks inside a
    sentence are ignored, and a sentence ends at . ; ! ? followed by whitespace, a blank line, or a
    heading (liver_sentences.HEADER_RE). Rejoined spans are clipped to WINDOW characters either side.
    Flags per unit: fat word in the unit; fat word in the rejoined sentence (SCREEN substrings from the
    frozen rule). Merged by sentence id onto the 155,136-row extraction and the 500-sentence pilot.

PRIVACY
    No text is printed or written. Per-unit flags (sid only) go to data/processed/llm_review/audit/.

USAGE
    scripts/run0919_env.sh diagnostics/llm_unclear_audit/split_sentences.py            # line-based units
    scripts/run0919_env.sh diagnostics/llm_unclear_audit/split_sentences.py --rejoin   # rejoined units
"""
import argparse
import bisect
import glob
import re
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, ".")
from scripts.liver_sentences import HEADER_RE, NOTE, SUBSAMPLE, extract_from_note
from scripts.note_phenotype import SCREEN

D = "data/processed/llm_review"
WINDOW = 300
PUNCT_BREAK = re.compile(r"(?<=[.;!?])\s+")
BLANK_LINE = re.compile(r"\n[ \t]*\n")


def has_fat(s):
    s = s.lower()
    return any(w in s for w in SCREEN)


def cut_points(text):
    cuts = {0, len(text)}
    cuts.update(m.end() for m in PUNCT_BREAK.finditer(text))
    cuts.update(m.end() for m in BLANK_LINE.finditer(text))
    cuts.update(m.start() for m in HEADER_RE.finditer(text))
    return sorted(cuts)


def flags_for_note(text, note_key, rejoin):
    units = extract_from_note(text, note_key, rejoin=rejoin)
    if not units:
        return []
    cuts = cut_points(text)
    out = []
    for u in units:
        s, e = u["char_start"], u["char_end"]
        a = cuts[bisect.bisect_right(cuts, s) - 1]
        b = cuts[bisect.bisect_left(cuts, e)]
        a, b = max(a, s - WINDOW), min(b, e + WINDOW)
        joined = text[a:b]
        out.append({"sid": u["sid"], "unit_fat": has_fat(u["text"]), "joined_fat": has_fat(joined),
                    "unit_is_whole_sentence": " ".join(joined.split()) == " ".join(u["text"].split())})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rejoin", action="store_true"); rejoin = ap.parse_args().rejoin
    tag = "_rejoined" if rejoin else ""
    t0 = time.time()
    con = duckdb.connect()
    con.execute("SET memory_limit='12GB'")
    sc = con.execute(f"SELECT hadm_id, subject_id FROM read_parquet('{SUBSAMPLE}') "
                     "WHERE partition IN ('DEV','TEST')").fetchdf()
    hadms, subs = set(sc.hadm_id.astype("int64")), set(sc.subject_id.astype("int64"))
    rows = []
    for table, is_disch in (("discharge", True), ("radiology", False)):
        reader = con.execute(f"SELECT note_id, hadm_id, subject_id, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')").fetch_record_batch(4000)
        for batch in reader:
            d = batch.to_pydict()
            for k in range(len(d["text"])):
                h, sj = d["hadm_id"][k], d["subject_id"][k]
                inpatient = h is not None and int(h) in hadms
                outpatient = (not is_disch) and h is None and sj is not None and int(sj) in subs
                if inpatient or outpatient:
                    rows.extend(flags_for_note(d["text"][k] or "", d["note_id"][k], rejoin))
        print(f"  scanned {table} ({time.time() - t0:.0f}s)", flush=True)
    f = pd.DataFrame(rows).drop_duplicates("sid")
    f.to_parquet(f"{D}/audit/split_flags{tag}.parquet", index=False)

    ext = pd.read_parquet(f"{D}/liver_sentences_devtest_cap160{tag}.parquet", columns=["hadm_id", "sid", "note_type"])
    m = ext.merge(f, on="sid", how="left")
    print(f"\nextraction rows {len(m):,} | matched to a flag {m.unit_fat.notna().sum():,}")
    m = m.dropna(subset=["unit_fat"])
    lost = m.joined_fat & ~m.unit_fat
    print(f"unit is a whole sentence (no line break inside its sentence): {int(m.unit_is_whole_sentence.sum()):,} ({100 * m.unit_is_whole_sentence.mean():.1f}%)")
    print(f"unit has a fat/steatosis word itself:                        {int(m.unit_fat.sum()):,}")
    print(f"unit lacks one but its rejoined sentence has one:              {int(lost.sum()):,}")
    print(f"  by note type: {m[lost].note_type.value_counts().to_dict()}")
    a_unit = set(m.hadm_id[m.unit_fat]); a_join = set(m.hadm_id[m.joined_fat])
    print(f"admissions with a fat word in a kept unit:            {len(a_unit):,}")
    print(f"admissions with a fat word in a liver unit's sentence: {len(a_join):,}  (+{len(a_join - a_unit):,} only via the neighbouring line)")

    if rejoin:
        return
    from scripts.llm_sentence_review import text_key
    p = pd.read_parquet(f"{D}/pilot500_input.parquet", columns=["sid", "text"])
    p["key"] = [text_key(t) for t in p.text]
    v = []
    for tag in ("v1", "v2"):
        s = pd.concat([pd.read_parquet(x) for x in sorted(glob.glob(f"{D}/pilot500_gemma4_{tag}/shards/*.parquet"))])
        v.append(s[["key", "answer"]].rename(columns={"answer": tag}))
    pm = p.drop(columns="text").merge(f, on="sid").merge(v[0], on="key").merge(v[1], on="key")
    pm["fat word only on neighbouring line"] = pm.joined_fat & ~pm.unit_fat
    print(f"\npilot units matched: {len(pm)}")
    for tag, lab in (("v1", "old prompt"), ("v2", "new prompt")):
        print(f"\nfat word only on neighbouring line x {lab} answer")
        print(pd.crosstab(pm["fat word only on neighbouring line"], pm[tag], margins=True).to_string())


if __name__ == "__main__":
    main()
