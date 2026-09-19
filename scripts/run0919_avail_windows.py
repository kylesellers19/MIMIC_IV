#!/usr/bin/env python3
"""run_2026-09-19 Phase 4.6 — laboratory- and imaging-availability differentials by race and insurance under both
outpatient windows (−365/+30 and −90/+30). Availability = in-admission result OR outpatient result within the window.
Writes docs/run_2026-09-19/results/avail_windows.json."""
import json, os, sys
import duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.getcwd())
from scripts.masld_config import CLEAN_POP, LOCKED_POP, LAB_ITEMIDS
IDX = "data/processed/run_2026-09-19_notes_index"; OL = "data/processed/run_2026-09-19_outpt_labs.parquet"
WIN = {"365/30": (365, 30), "90/30": (90, 30)}
ANALYTES = ["ALT", "AST", "HbA1c", "Triglycerides", "HDL", "Platelets", "Glucose"]
con = duckdb.connect(); con.execute("SET memory_limit='16GB'")
df = con.execute(f"""SELECT c.hadm_id, c.subject_id, c.code_positive, c.race, c.insurance, l.admittime,
                     {', '.join(f'c.miss_lab_{a}' for a in ANALYTES)}
                     FROM read_parquet('{CLEAN_POP}') c JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""").fetchdf()
df["insurance"] = df.insurance.fillna("(missing)")
labs = con.execute(f"SELECT subject_id, itemid, charttime FROM read_parquet('{OL}')").fetchdf()
inv = {v: k for k, v in LAB_ITEMIDS.items()}; labs["analyte"] = labs.itemid.map(inv)
labs = labs[labs.analyte.isin(ANALYTES)]
rad = con.execute(f"SELECT subject_id, charttime, liver_incl FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NULL").fetchdf()
rad = rad[rad.subject_id.isin(set(df.subject_id))]
ri = con.execute(f"SELECT hadm_id, max(liver_incl::INT) AS liv_inp, 1 AS any_inp FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
df = df.merge(ri, on="hadm_id", how="left").fillna({"liv_inp": 0, "any_inp": 0})
adm = df[["hadm_id", "subject_id", "admittime"]].copy(); adm["admittime"] = pd.to_datetime(adm.admittime)
def in_window(events, before, after, timecol="charttime"):
    m = adm.merge(events, on="subject_id", how="inner")
    d = (pd.to_datetime(m[timecol]) - m.admittime).dt.total_seconds() / 86400.0
    return m[(d >= -before) & (d <= after)]
def smd_bin(p1, p0):
    d = np.sqrt((p1 * (1 - p1) + p0 * (1 - p0)) / 2); return float((p1 - p0) / d) if d > 0 else None
res = {"windows": {}, "note": "availability = in-admission result OR outpatient result within the window; imaging = any radiology / liver-inclusive radiology, inpatient-linked OR outpatient within the window"}
for wname, (b, a) in WIN.items():
    lw = in_window(labs, b, a)
    avail = {}
    for an in ANALYTES:
        s = set(lw[lw.analyte == an].hadm_id)
        avail[an] = (~df[f"miss_lab_{an}"].astype(bool)) | df.hadm_id.isin(s)
    rw = in_window(rad, b, a)
    avail["any_imaging"] = df.any_inp.astype(bool) | df.hadm_id.isin(set(rw.hadm_id))
    avail["liver_imaging"] = df.liv_inp.astype(bool) | df.hadm_id.isin(set(rw[rw.liver_incl].hadm_id))
    out = {"overall_pct": {k: round(100 * float(v.mean()), 2) for k, v in avail.items()},
           "smd_code_pos_vs_neg": {k: round(smd_bin(float(v[df.code_positive].mean()), float(v[~df.code_positive].mean())), 3) for k, v in avail.items()},
           "by_race": {}, "by_insurance": {}}
    for var, key in [("race", "by_race"), ("insurance", "by_insurance")]:
        for lev, g in df.groupby(var):
            if len(g) < 11: continue
            idx = g.index; rest = df.index.difference(idx)
            row = {"n": int(len(g))}
            for k, v in avail.items():
                p1 = float(v.loc[idx].mean()); p0 = float(v.loc[rest].mean())
                row[k] = {"pct": round(100 * p1, 1), "smd_vs_rest": round(smd_bin(p1, p0), 3) if smd_bin(p1, p0) is not None else None}
            out[key][str(lev)] = row
    res["windows"][wname] = out
# did the differential shrink? max |SMD| across strata per measure, per window
shrink = {}
for var in ["by_race", "by_insurance"]:
    shrink[var] = {}
    for k in ANALYTES + ["any_imaging", "liver_imaging"]:
        m365 = max(abs(r[k]["smd_vs_rest"]) for r in res["windows"]["365/30"][var].values() if r[k]["smd_vs_rest"] is not None)
        m90 = max(abs(r[k]["smd_vs_rest"]) for r in res["windows"]["90/30"][var].values() if r[k]["smd_vs_rest"] is not None)
        shrink[var][k] = {"max_abs_smd_90_30": round(m90, 3), "max_abs_smd_365_30": round(m365, 3), "shrinks_when_widened": bool(m365 < m90)}
res["max_abs_smd_comparison"] = shrink
json.dump(res, open("docs/run_2026-09-19/results/avail_windows.json", "w"), indent=1)
print(json.dumps({"overall": {w: res["windows"][w]["overall_pct"] for w in WIN}, "shrink": shrink}, indent=1))
