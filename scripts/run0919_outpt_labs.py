#!/usr/bin/env python3
"""run_2026-09-19 Phase 4.6 stage 1 — extract OUTPATIENT (hadm_id NULL) results for the ten approved analytes
for locked-population subjects: subject_id, itemid, charttime only. Writes data/processed/run_2026-09-19_outpt_labs.parquet (untracked)."""
import os, sys, time
import duckdb
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP, lab_itemid_csv
OUT = "data/processed/run_2026-09-19_outpt_labs.parquet"
if os.path.exists(OUT):
    print("exists — skip"); sys.exit()
t0 = time.time(); con = duckdb.connect(); con.execute("SET memory_limit='16GB'")
con.execute(f"""COPY (SELECT l.subject_id, l.itemid, l.charttime FROM read_csv('{DATA}/labevents.csv.gz', types={{'hadm_id':'BIGINT','itemid':'INTEGER','subject_id':'BIGINT'}}) l
                 WHERE l.hadm_id IS NULL AND l.itemid IN ({lab_itemid_csv()}) AND l.valuenum IS NOT NULL
                   AND l.subject_id IN (SELECT DISTINCT subject_id FROM read_parquet('{CLEAN_POP}')))
                TO '{OUT}' (FORMAT parquet)""")
n = con.execute(f"SELECT count(*), count(DISTINCT subject_id) FROM read_parquet('{OUT}')").fetchone()
print(f"rows {n[0]:,} subjects {n[1]:,} in {time.time()-t0:,.0f}s")
