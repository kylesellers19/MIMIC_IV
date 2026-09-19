#!/usr/bin/env python3
"""run_2026-09-19 Phase 7 — structured feature table for Aim 1b (time-bounded at discharge; no post-discharge information;
never the phenotype codes, the full Charlson, or any note-rule output). Reuses the project's derivations:
drug classes and CMRF criteria from scripts/cmrf.py (lists imported by exec, logic re-applied identically),
etiology flags from data/processed/cmrf.parquet, charlson_noliver from Phase 4.2, labs from run0919_lab_features.py.
Writes data/processed/run_2026-09-19_features.parquet (untracked) and docs/run_2026-09-19/results/feature_classification.json
(feature -> clinical | availability; the leakage audit)."""
import json, os, sys, re
import duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP, LOCKED_POP, LAB_ITEMIDS
IDX = "data/processed/run_2026-09-19_notes_index"; RX = "data/raw/hosp/prescriptions.csv.gz"
OUT = "data/processed/run_2026-09-19_features.parquet"
src = open("scripts/cmrf.py").read(); ns = {"pd": pd, "re": re}
i0 = src.index("INSULIN = "); i1 = src.index("def match"); i2 = src.index("\n\n", i1)
exec(src[i0:i2], ns)          # drug lists + match(), unchanged
match = ns["match"]; RTFILTER = "(route IS NULL OR (upper(route) NOT LIKE '%EYE%' AND upper(route) NOT IN ('OU','OS','OD')))"
con = duckdb.connect(); con.execute("SET memory_limit='20GB'")
pop = con.execute(f"""SELECT c.*, l.admittime, l.dischtime, l.admit_year FROM read_parquet('{CLEAN_POP}') c JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""").fetchdf()
con.register("lh", pop[["hadm_id"]])
# ---- medications (orders started before discharge) ----
ds = con.execute(f"SELECT DISTINCT lower(drug) AS drug FROM read_csv_auto('{RX}') SEMI JOIN lh USING (hadm_id) WHERE drug IS NOT NULL AND {RTFILTER}").fetchdf()
fl = ds.drug.map(match).apply(pd.Series); d2c = pd.concat([ds, fl], axis=1); con.register("d2c", d2c)
medh = con.execute(f"""SELECT p.hadm_id, max(insulin::INT) insulin, max(metformin::INT) metformin, max(oral_ad::INT) oral_ad, max(bb::INT) bb,
   max(htn_qual::INT) htn_qual, max(htn_excl::INT) htn_excl, max(lipid::INT) lipid, count(*) AS n_rx_orders, count(DISTINCT lower(p.drug)) AS n_rx_distinct
   FROM read_csv_auto('{RX}') p JOIN d2c ON lower(p.drug)=d2c.drug SEMI JOIN lh ON p.hadm_id=lh.hadm_id WHERE {RTFILTER} GROUP BY p.hadm_id""").fetchdf()
nrx = con.execute(f"SELECT hadm_id, count(*) AS n_rx_orders_all FROM read_csv_auto('{RX}') SEMI JOIN lh USING (hadm_id) GROUP BY hadm_id").fetchdf()
# ---- CMRF code flags (same SQL as cmrf.py; none of these are the phenotype codes) ----
codes = con.execute(f"""WITH d AS (SELECT hadm_id, trim(icd_code) code, icd_version FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
  SELECT hadm_id,
    max(((icd_version=10 AND (code LIKE 'E66%' OR code LIKE 'Z683%' OR code LIKE 'Z684%')) OR (icd_version=9 AND code LIKE '2780%'))::INT) ow_code,
    max(((icd_version=10 AND (code LIKE 'E11%' OR code='R7303')) OR (icd_version=9 AND (code LIKE '250%' OR code LIKE '7902%')))::INT) dg_code,
    max(((icd_version=10 AND regexp_matches(code,'^I1[0-6]')) OR (icd_version=9 AND regexp_matches(code,'^40[1-5]')))::INT) htn_code,
    max(((icd_version=10 AND (code LIKE 'E781%' OR code LIKE 'E782%')) OR (icd_version=9 AND code='2721'))::INT) tg_code,
    max(((icd_version=10 AND code='E786') OR (icd_version=9 AND code='2725'))::INT) hdl_code
  FROM d SEMI JOIN lh USING (hadm_id) GROUP BY hadm_id""").fetchdf()
m = pop.merge(medh, on="hadm_id", how="left").merge(nrx, on="hadm_id", how="left").merge(codes, on="hadm_id", how="left")
for c in ["insulin", "metformin", "oral_ad", "bb", "htn_qual", "htn_excl", "lipid", "ow_code", "dg_code", "htn_code", "tg_code", "hdl_code"]:
    m[c] = m[c].fillna(0).astype(bool)
m["n_rx_orders"] = m.n_rx_orders_all.fillna(0).astype(int); m["n_rx_distinct"] = m.n_rx_distinct.fillna(0).astype(int)
male = m.gender == "M"
m["cmrf_overweight"] = m.ow_code | (m.omr_BMI >= 25)
m["cmrf_dysglycemia"] = m.dg_code | (m.lab_HbA1c >= 5.7) | (m.lab_Glucose >= 100) | m.oral_ad
m["cmrf_hypertension"] = m.htn_code | (m.omr_SBP >= 130) | (m.omr_DBP >= 85) | m.htn_qual
m["cmrf_hypertg"] = m.tg_code | (m.lab_Triglycerides >= 150) | m.lipid
m["cmrf_lowhdl"] = m.hdl_code | ((male & (m.lab_HDL <= 40)) | (~male & (m.lab_HDL <= 50))) | m.lipid
# ---- etiology + charlson_noliver + labs ----
et = con.execute("SELECT hadm_id, alcohol AS etio_alcohol, viral AS etio_viral, cirrhosis AS etio_cirrhosis, hcc AS etio_hcc, other_etio AS etio_other FROM read_parquet('data/processed/cmrf.parquet')").fetchdf()
ch = con.execute("SELECT hadm_id, charlson_noliver FROM read_parquet('data/processed/run_2026-09-19_charlson.parquet')").fetchdf()
labs = con.execute("SELECT * FROM read_parquet('data/processed/run_2026-09-19_lab_features.parquet')").fetchdf()
labs = labs[["hadm_id"] + [c for c in labs.columns if c != "hadm_id" and not c.endswith("_GGT") and "GGT" not in c]]
# ---- availability / volume from notes index (counts and lengths only) and imaging in window ----
dcn = con.execute(f"SELECT hadm_id, count(*) AS n_notes_dc, sum(n_chars) AS chars_dc FROM read_parquet('{IDX}/discharge.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
rdn = con.execute(f"SELECT hadm_id, count(*) AS n_notes_rad_inp, sum(n_chars) AS chars_rad_inp, max(liver_incl::INT) AS liver_imaging_inp FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
op = con.execute(f"SELECT subject_id, charttime, liver_incl FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NULL").fetchdf()
adm = m[["hadm_id", "subject_id", "admittime"]].copy(); adm["admittime"] = pd.to_datetime(adm.admittime)
mm = adm.merge(op[op.subject_id.isin(set(adm.subject_id))], on="subject_id", how="inner")
d = (pd.to_datetime(mm.charttime) - mm.admittime).dt.total_seconds() / 86400.0
# time-bounded at discharge: only outpatient reports BEFORE admission count as features (the -365 lookback); post-discharge reports are excluded
pre = mm[(d >= -365) & (d <= 0)]
n_rad_out_pre = pre.groupby("hadm_id").size().rename("n_notes_rad_out_pre365"); liv_out_pre = pre[pre.liver_incl].groupby("hadm_id").size().rename("liver_imaging_out_pre365")
X = (m.merge(et, on="hadm_id", how="left").merge(ch, on="hadm_id", how="left").merge(labs, on="hadm_id", how="left")
       .merge(dcn, on="hadm_id", how="left").merge(rdn, on="hadm_id", how="left")
       .merge(n_rad_out_pre, on="hadm_id", how="left").merge(liv_out_pre, on="hadm_id", how="left"))
for c in ["n_notes_dc", "chars_dc", "n_notes_rad_inp", "chars_rad_inp", "liver_imaging_inp", "n_notes_rad_out_pre365", "liver_imaging_out_pre365"]:
    X[c] = X[c].fillna(0).astype(int)
X["liver_imaging_any_pre"] = ((X.liver_imaging_inp > 0) | (X.liver_imaging_out_pre365 > 0)).astype(int)
for c in ["etio_alcohol", "etio_viral", "etio_cirrhosis", "etio_hcc", "etio_other"]:
    X[c] = X[c].fillna(False).astype(bool)
X["los_days"] = X.los_days.where(X.los_days >= 0)
X["age"] = X.age.astype(float)
for c in list(LAB_ITEMIDS):
    if c == "GGT": continue
    X[f"n_{c}"] = X.get(f"n_{c}", pd.Series(np.nan, index=X.index)).fillna(0).astype(int)
X["n_lab_results_total"] = sum(X[f"n_{c}"] for c in LAB_ITEMIDS if c != "GGT")
X["n_analytes_available"] = sum((~X[f"miss_lab_{c}"]).astype(int) for c in LAB_ITEMIDS if c != "GGT")
# ---- classification (leakage audit) ----
clinical = (["age", "gender", "admission_type", "admission_location", "icd_era", "los_days", "admit_year", "marital_status"]
            + [f"first_val_{c}" for c in LAB_ITEMIDS if c != "GGT"] + [f"last_val_{c}" for c in LAB_ITEMIDS if c != "GGT"]
            + ["pre365_HbA1c", "pre365_Triglycerides", "pre365_HDL", "omr_BMI", "omr_SBP", "omr_DBP",
               "cmrf_overweight", "cmrf_dysglycemia", "cmrf_hypertension", "cmrf_hypertg", "cmrf_lowhdl",
               "insulin", "metformin", "oral_ad", "bb", "htn_qual", "htn_excl", "lipid",
               "charlson_noliver", "etio_alcohol", "etio_viral", "etio_cirrhosis", "etio_hcc", "etio_other"])
availability = ([f"miss_lab_{c}" for c in LAB_ITEMIDS if c != "GGT"] + ["miss_omr_BMI", "miss_omr_SBP", "miss_omr_DBP", "miss_insurance", "miss_marital_status", "miss_language"]
                + [f"n_{c}" for c in LAB_ITEMIDS if c != "GGT"] + ["n_lab_results_total", "n_analytes_available", "n_diagnoses", "n_rx_orders", "n_rx_distinct",
                   "n_notes_dc", "chars_dc", "n_notes_rad_inp", "chars_rad_inp", "liver_imaging_inp", "n_notes_rad_out_pre365", "liver_imaging_out_pre365", "liver_imaging_any_pre", "has_BMI", "has_SBP", "has_DBP"])
clinical = [c for c in clinical if c in X.columns]; availability = [c for c in availability if c in X.columns]
excluded = {"code_positive": "phenotype code (label axis)", "race": "equity stratum (kept for subgroup reporting, not a feature)", "insurance": "equity stratum", "language": "equity stratum",
            "lab_GGT": "0.9% coverage — excluded", "miss_lab_GGT": "excluded with GGT", "hospital_expire_flag": "post-discharge/outcome information", "discharge_location": "discharge-time disposition (borderline; excluded as outcome-like)",
            "dischtime": "timestamp", "admittime": "timestamp", "flag_*": "cleaning flags", "lab_* (clean-pop single values)": "superseded by first/last in-admission values",
            "charlson (full)": "contains K76.0/571.x — leaks the code axis", "note rule outputs": "label source", "double-review / cell": "sampling design"}
feat = X[["hadm_id", "subject_id", "race", "insurance", "language"] + clinical + availability].copy()
for c in ["gender", "admission_type", "admission_location", "icd_era", "marital_status"]:
    feat[c] = feat[c].fillna("MISSING").astype(str)
con.register("feat", feat); con.execute(f"COPY feat TO '{OUT}' (FORMAT parquet)")
cls = {"clinical": clinical, "availability": availability, "excluded": excluded, "n_features": {"clinical": len(clinical), "availability": len(availability)}, "rows": int(len(feat))}
json.dump(cls, open("docs/run_2026-09-19/results/feature_classification.json", "w"), indent=1)
print(f"features: {len(clinical)} clinical + {len(availability)} availability; rows {len(feat):,}")
