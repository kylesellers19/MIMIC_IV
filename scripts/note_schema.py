#!/usr/bin/env python3
"""STEP 4 — schema & scale for the four MIMIC-IV-Note tables.

Queries the gzips in place. NEVER selects or prints note text: for tables with a
`text` column, only length(text) (computed in DuckDB) is transferred, alongside
small id/type columns. One scan per table.

Run: python scripts/note_schema.py
"""
import time
import numpy as np
import pandas as pd
import duckdb

NOTE = "data/raw/note"
FILES = ["discharge", "discharge_detail", "radiology", "radiology_detail"]
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")


def describe(path):
    rows = con.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{path}')").fetchall()
    return [(r[0], r[1]) for r in rows]


for name in FILES:
    path = f"{NOTE}/{name}.csv.gz"
    print("\n" + "=" * 72 + f"\n{name}\n" + "=" * 72)
    t0 = time.perf_counter()
    schema = describe(path)
    cols = [c for c, _ in schema]
    has_text = "text" in cols

    if has_text:
        # single scan: small columns + length(text) only (NO text transferred)
        sel = ["subject_id", "hadm_id"]
        if "note_type" in cols: sel.append("note_type")
        if "note_seq" in cols: sel.append("note_seq")
        sel.append("length(text) AS tlen")
        df = con.execute(
            f"SELECT {', '.join(sel)} FROM read_csv_auto('{path}')"
        ).fetchdf()
        elapsed = time.perf_counter() - t0
        n = len(df)
        print(f"  rows       : {n:,}")
        print(f"  columns ({len(schema)}): " + ", ".join(f"{c}:{t}" for c, t in schema))
        print(f"  scan time  : {elapsed:,.1f} s")
        print(f"  distinct subject_id : {df.subject_id.nunique():,}")
        print(f"  distinct hadm_id    : {df.hadm_id.nunique():,}")
        print(f"  NULL hadm_id        : {int(df.hadm_id.isna().sum()):,} "
              f"({100*df.hadm_id.isna().mean():.1f}%)")
        if "note_type" in cols:
            print("  note_type value counts:")
            for v, c in df.note_type.value_counts(dropna=False).items():
                print(f"      {v!r}: {c:,}")
        if "note_seq" in cols:
            print(f"  note_seq: min={df.note_seq.min()} max={df.note_seq.max()} "
                  f"distinct={df.note_seq.nunique()}")
            print("  note_seq value counts (top 10):")
            for v, c in df.note_seq.value_counts().head(10).sort_index().items():
                print(f"      {v}: {c:,}")
        q = df.tlen.quantile([0, .5, .95, 1.0])
        print(f"  text length (chars): min={int(q[0])}  median={int(q[.5])}  "
              f"p95={int(q[.95])}  max={int(q[1.0]):,}")
    else:
        n = con.execute(f"SELECT count(*) FROM read_csv_auto('{path}')").fetchone()[0]
        elapsed = time.perf_counter() - t0
        print(f"  rows       : {n:,}")
        print(f"  columns ({len(schema)}): " + ", ".join(f"{c}:{t}" for c, t in schema))
        print(f"  scan time  : {elapsed:,.1f} s")
