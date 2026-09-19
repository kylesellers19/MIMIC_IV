#!/usr/bin/env python3
"""run_2026-09-19 Phase 3 stage 1 — one streaming pass over all notes, producing a per-note index
(flags and lengths only, NO text). Feeds Phase 3 text assembly, Phase 4.3 (discharge-only) and
Phase 4.4 (Tier C counted positive). Resumable: a table whose output exists is skipped.

Per note: note_id, hadm_id, subject_id, charttime, n_chars, a_pos, b_pos, c_hedged, n_pos, n_hist,
n_tierC, n_neg, liver_incl (radiology only, from radiology_detail exam_name — the imaging-denominator rule).
Row-level exceptions are counted by class; no message or value is logged.
"""
import os, sys, time, json
from collections import Counter
import duckdb, pandas as pd
sys.path.insert(0, os.getcwd())
from scripts.note_phenotype import _iter_hits, NOTE

OUT = "data/processed/run_2026-09-19_notes_index"
MOD = r"(\bCT\b|\bCTA\b|\bMR\b|\bMRI\b|\bUS\b|U\.S|ULTRASOUND|SONO)"
REGION = r"(ABD|LIVER|HEPAT|\bRUQ\b|BILIARY|GALLBLADDER)"

def flags(txt):
    a = b = c = False; npos = nhist = ntc = nneg = 0
    for h in _iter_hits(txt):
        d = h["disp"]
        if d == "positive":
            npos += 1; nhist += int(bool(h.get("historical")))
            if h["tier"] == "A": a = True
            else: b = True
        elif d == "tierC": c = True; ntc += 1
        elif d == "negation": nneg += 1
    return a, b, c, npos, nhist, ntc, nneg

def run(table):
    out = f"{OUT}/{table}.parquet"
    if os.path.exists(out):
        print(f"[{table}] exists — skip", flush=True); return
    con = duckdb.connect(); con.execute("SET memory_limit='20GB'")
    liver = None
    if table == "radiology":
        det = con.execute(f"""SELECT note_id, max((regexp_matches(upper(field_value),'{MOD}') AND regexp_matches(upper(field_value),'{REGION}'))::INT) AS liver
                              FROM read_csv_auto('{NOTE}/radiology_detail.csv.gz') WHERE field_name='exam_name' GROUP BY note_id""").fetchdf()
        liver = dict(zip(det.note_id, det.liver.astype(bool)))
        print(f"[{table}] exam_name rows for {len(liver):,} notes", flush=True)
    reader = con.execute(f"SELECT note_id, hadm_id, subject_id, charttime, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')").fetch_record_batch(5000)
    rows = []; exc = Counter(); n = 0; t0 = time.time()
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            n += 1
            try:
                txt = d["text"][k] or ""
                a, b, c, npos, nhist, ntc, nneg = flags(txt)
                rows.append((d["note_id"][k], d["hadm_id"][k], d["subject_id"][k], d["charttime"][k], len(txt),
                             a, b, c, npos, nhist, ntc, nneg,
                             bool(liver.get(d["note_id"][k], False)) if liver is not None else None))
            except Exception as e:
                exc[type(e).__name__] += 1
        if n % 100000 < 5000:
            print(f"[{table}] {n:,} notes  {time.time()-t0:,.0f}s", flush=True)
    df = pd.DataFrame(rows, columns=["note_id","hadm_id","subject_id","charttime","n_chars","a_pos","b_pos","c_hedged",
                                     "n_pos","n_hist","n_tierC","n_neg","liver_incl"])
    df["hadm_id"] = df["hadm_id"].astype("Int64"); df["subject_id"] = df["subject_id"].astype("Int64")
    df["charttime"] = pd.to_datetime(df["charttime"])
    con.register("df", df); con.execute(f"COPY df TO '{out}' (FORMAT parquet)")
    print(f"[{table}] wrote {len(df):,} rows in {time.time()-t0:,.0f}s; exceptions by class: {dict(exc)}", flush=True)

if __name__ == "__main__":
    for t in ["discharge", "radiology"]:
        run(t)
    print("DONE", flush=True)
