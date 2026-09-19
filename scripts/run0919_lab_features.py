#!/usr/bin/env python3
"""run_2026-09-19 Phase 7 feature prep — laboratory features from labevents (values; no patient rows printed).
In-admission: first and last valuenum per (hadm_id, analyte) restricted to charttime <= dischtime; result count.
Pre-admission outpatient: most recent value within 365 days before admittime for HbA1c, Triglycerides, HDL.
Writes data/processed/run_2026-09-19_lab_features.parquet (untracked)."""
import os, sys, time
import duckdb
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP, LOCKED_POP, LAB_ITEMIDS, lab_itemid_csv
OUT = "data/processed/run_2026-09-19_lab_features.parquet"
if os.path.exists(OUT): print("exists — skip"); sys.exit()
t0 = time.time(); con = duckdb.connect(); con.execute("SET memory_limit='20GB'")
case = " ".join(f"WHEN {v} THEN '{k}'" for k, v in LAB_ITEMIDS.items())
con.execute(f"""CREATE TEMP TABLE pop AS SELECT c.hadm_id, c.subject_id, l.admittime, l.dischtime FROM read_parquet('{CLEAN_POP}') c JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""")
con.execute(f"""CREATE TEMP TABLE ev AS
  SELECT l.subject_id, l.hadm_id, CASE l.itemid {case} END AS analyte, l.charttime, l.valuenum
  FROM read_csv('{DATA}/labevents.csv.gz', types={{'hadm_id':'BIGINT','itemid':'INTEGER','subject_id':'BIGINT','valuenum':'DOUBLE'}}) l
  WHERE l.itemid IN ({lab_itemid_csv()}) AND l.valuenum IS NOT NULL
    AND (l.hadm_id IN (SELECT hadm_id FROM pop) OR (l.hadm_id IS NULL AND l.subject_id IN (SELECT subject_id FROM pop)))""")
print(f"events loaded {time.time()-t0:,.0f}s", flush=True)
inadm = con.execute("""
  SELECT e.hadm_id, e.analyte, arg_min(e.valuenum, e.charttime) AS first_val, arg_max(e.valuenum, e.charttime) AS last_val, count(*) AS n
  FROM ev e JOIN pop p USING (hadm_id) WHERE e.charttime <= p.dischtime GROUP BY e.hadm_id, e.analyte""").fetchdf()
pre = con.execute("""
  SELECT p.hadm_id, e.analyte, arg_max(e.valuenum, e.charttime) AS pre_val
  FROM ev e JOIN pop p ON e.subject_id = p.subject_id AND e.hadm_id IS NULL
  WHERE e.analyte IN ('HbA1c','Triglycerides','HDL') AND e.charttime < p.admittime AND e.charttime >= p.admittime - INTERVAL 365 DAY
  GROUP BY p.hadm_id, e.analyte""").fetchdf()
wide = inadm.pivot(index="hadm_id", columns="analyte", values=["first_val", "last_val", "n"])
wide.columns = [f"{a}_{b}" for a, b in wide.columns]
pw = pre.pivot(index="hadm_id", columns="analyte", values="pre_val"); pw.columns = [f"pre365_{c}" for c in pw.columns]
feat = wide.join(pw, how="outer").reset_index()
con.register("feat", feat); con.execute(f"COPY feat TO '{OUT}' (FORMAT parquet)")
print(f"wrote {len(feat):,} admissions x {feat.shape[1]} cols in {time.time()-t0:,.0f}s", flush=True)
