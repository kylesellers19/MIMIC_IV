#!/usr/bin/env python3
"""STEP 4 — COMPLETENESS, differential (Kahn et al. 2016 DQ framework).

Tests whether missingness differs between code-positive and code-negative
admissions (binary SMD), and across race and insurance categories (rate tables).
Extends to metabolic-data availability (BMI/ALT/HbA1c/Triglycerides/HDL), the
most likely MNAR-and-coding-linked completeness threat.

MNAR-threat-to-Aim-1c flag: missingness predicts coding (|SMD|>=0.1) AND varies
across race OR insurance by >=10 percentage points.

Read-only; reports proportions and SMDs (no p-values), changes nothing.
Run: python scripts/completeness_differential.py
"""
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, LAB_ITEMIDS, analysis_admissions_sql

pd.set_option("display.width", 200); pd.set_option("display.max_rows", 60)
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# analysis population (admission grain, zero-dx excluded)
con.execute(f"CREATE TEMP VIEW ap AS {analysis_admissions_sql()}")
adm = con.execute("""
  SELECT hadm_id, subject_id, code_positive, race, insurance,
         marital_status, language, discharge_location, admission_location
  FROM ap
""").fetchdf()

# subject-level presence of metabolic data
metab_ids = {k: LAB_ITEMIDS[k] for k in ["ALT", "HbA1c", "Triglycerides", "HDL"]}
lab_ids = ",".join(str(v) for v in metab_ids.values())
lab_pres = con.execute(f"""
  SELECT DISTINCT subject_id, itemid
  FROM read_csv_auto('{DATA}/labevents.csv.gz')
  WHERE itemid IN ({lab_ids})
""").fetchdf()
bmi_subj = con.execute(f"""
  SELECT DISTINCT subject_id FROM read_csv_auto('{DATA}/omr.csv.gz')
  WHERE result_name IN ('BMI (kg/m2)','BMI')
""").fetchdf()

adm["miss_BMI"] = ~adm.subject_id.isin(set(bmi_subj.subject_id))
for name, iid in metab_ids.items():
    have = set(lab_pres[lab_pres.itemid == iid].subject_id)
    adm[f"miss_{name}"] = ~adm.subject_id.isin(have)
# categorical covariates: missing = NULL
CAT = ["insurance", "marital_status", "language", "discharge_location", "admission_location"]
for c in CAT:
    adm[f"miss_{c}"] = adm[c].isna()

MISS_COLS = [f"miss_{c}" for c in CAT] + \
            ["miss_BMI", "miss_ALT", "miss_HbA1c", "miss_Triglycerides", "miss_HDL"]

pos = adm[adm.code_positive]; neg = adm[~adm.code_positive]


def smd_binary(p1, p2):
    d = np.sqrt((p1*(1-p1) + p2*(1-p2)) / 2)
    return np.nan if d == 0 else (p1 - p2) / d


def rate_by(group_col, miss_col, min_n=500):
    g = adm.groupby(group_col)[miss_col].agg(["mean", "size"])
    g = g[g["size"] >= min_n]
    return g["mean"] * 100


print("=" * 78)
print("STEP 4 — DIFFERENTIAL COMPLETENESS")
print(f"analysis admissions={len(adm):,}  code+={len(pos):,}  code-={len(neg):,}")
print("=" * 78)
print(f"\n{'covariate':22s} {'miss% all':>9s} {'miss% code+':>11s} {'miss% code-':>11s} "
      f"{'SMD':>7s} {'race rng':>9s} {'ins rng':>8s}  flag")

rows = []
for mc in MISS_COLS:
    name = mc.replace("miss_", "")
    p_all = adm[mc].mean(); p1 = pos[mc].mean(); p0 = neg[mc].mean()
    smd = smd_binary(p1, p0)
    race_rates = rate_by("race", mc); ins_rates = rate_by("insurance", mc)
    race_rng = (race_rates.max() - race_rates.min()) if len(race_rates) else np.nan
    ins_rng = (ins_rates.max() - ins_rates.min()) if len(ins_rates) else np.nan
    mnar = (abs(smd) >= 0.1) and ((race_rng >= 10) or (ins_rng >= 10))
    flag = "  <== MNAR-threat-1c" if mnar else ""
    print(f"{name:22s} {p_all*100:8.2f}% {p1*100:10.2f}% {p0*100:10.2f}% "
          f"{smd:+7.3f} {race_rng:8.1f} {ins_rng:7.1f}{flag}")
    rows.append((name, race_rates, ins_rates, mnar))

# detail: race/insurance breakdown for flagged covariates
print("\n" + "=" * 78)
print("DETAIL — missing% by race / insurance for FLAGGED covariates")
print("=" * 78)
for name, race_rates, ins_rates, mnar in rows:
    if not mnar:
        continue
    print(f"\n### {name}  — missing% by race (n>=500), sorted:")
    print(race_rates.sort_values(ascending=False).round(1).to_string())
    print(f"### {name}  — missing% by insurance:")
    print(ins_rates.sort_values(ascending=False).round(1).to_string())
