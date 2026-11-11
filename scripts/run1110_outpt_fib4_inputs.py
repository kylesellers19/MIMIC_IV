#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 (amendment l, sensitivity 4) — outpatient FIB-4 inputs.

For every admission of the analysis population: the most recent OUTPATIENT (hadm_id IS NULL) AST, ALT and
platelet value in the 365 days before admission, approved itemids only. One pass over labevents.
Writes data/processed/run_2026-11-10_outpt_fib4.parquet (untracked; values, no rows printed).
Same windowing as scripts/run0919_lab_features.py used for HbA1c, triglycerides and HDL.
"""
import os, sys, time
import duckdb
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP, LOCKED_POP, LAB_ITEMIDS

OUT = "data/processed/run_2026-11-10_outpt_fib4.parquet"
if os.path.exists(OUT):
    print("exists — skip"); sys.exit()
t0 = time.time()
con = duckdb.connect(); con.execute("SET memory_limit='10GB'"); con.execute("SET threads=6")
ids = {k: LAB_ITEMIDS[k] for k in ("AST", "ALT", "Platelets")}
case = " ".join(f"WHEN {v} THEN '{k}'" for k, v in ids.items())
con.execute(f"""CREATE TEMP TABLE pop AS SELECT c.hadm_id, c.subject_id, l.admittime
                FROM read_parquet('{CLEAN_POP}') c JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""")
con.execute(f"""CREATE TEMP TABLE ev AS
  SELECT l.subject_id, CASE l.itemid {case} END AS analyte, l.charttime, l.valuenum
  FROM read_csv('{DATA}/labevents.csv.gz', types={{'hadm_id':'BIGINT','itemid':'INTEGER','subject_id':'BIGINT','valuenum':'DOUBLE'}}) l
  WHERE l.itemid IN ({",".join(str(v) for v in ids.values())}) AND l.valuenum IS NOT NULL AND l.hadm_id IS NULL
    AND l.subject_id IN (SELECT subject_id FROM pop)""")
print(f"outpatient events loaded {time.time()-t0:,.0f}s", flush=True)
con.execute(f"""COPY (
  SELECT hadm_id,
         max(CASE WHEN analyte='AST' THEN v END) AS out_AST, max(CASE WHEN analyte='ALT' THEN v END) AS out_ALT,
         max(CASE WHEN analyte='Platelets' THEN v END) AS out_Platelets
  FROM (SELECT p.hadm_id, e.analyte, arg_max(e.valuenum, e.charttime) AS v
        FROM ev e JOIN pop p ON e.subject_id = p.subject_id
        WHERE e.charttime < p.admittime AND e.charttime >= p.admittime - INTERVAL 365 DAY
        GROUP BY p.hadm_id, e.analyte)
  GROUP BY hadm_id) TO '{OUT}' (FORMAT parquet)""")
n = con.execute(f"SELECT count(*) FROM read_parquet('{OUT}')").fetchone()[0]
print(f"wrote {n:,} admissions with at least one outpatient value in {time.time()-t0:,.0f}s", flush=True)
