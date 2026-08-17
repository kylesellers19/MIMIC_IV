#!/usr/bin/env python3
"""STEP 5 — empirical note-coverage window for the analysis population.

Links the 545,497 analysis admissions (admission grain) to discharge and
radiology notes by hadm_id. No note text is read (only subject_id, hadm_id).
Reports coverage overall, by anchor_year_group, for the code-positive subset,
subject-level equivalents, and NULL-hadm_id radiology (outpatient imaging)
separately. Also race/insurance breakdowns for differential-loss assessment.

Run: python scripts/note_coverage.py
"""
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, analysis_admissions_sql

NOTE = "data/raw/note"
pd.set_option("display.width", 200)
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

con.execute(f"CREATE TEMP VIEW ap AS {analysis_admissions_sql()}")
ap = con.execute("""
  SELECT hadm_id, subject_id, code_positive, anchor_year_group, race, insurance
  FROM ap
""").fetchdf()

# note linkage keys only (no text)
disch = con.execute(f"SELECT subject_id, hadm_id FROM read_csv_auto('{NOTE}/discharge.csv.gz')").fetchdf()
rad = con.execute(f"SELECT subject_id, hadm_id FROM read_csv_auto('{NOTE}/radiology.csv.gz')").fetchdf()

disch_hadm = set(disch.hadm_id.dropna().astype("int64"))
rad_hadm = set(rad.hadm_id.dropna().astype("int64"))
ap["has_dc"] = ap.hadm_id.isin(disch_hadm)
ap["has_rad"] = ap.hadm_id.isin(rad_hadm)
ap["has_either"] = ap.has_dc | ap.has_rad
ap["has_neither"] = ~ap.has_either

N = len(ap)


def block(df, label):
    n = len(df)
    print(f"\n--- {label} (n={n:,} admissions) ---")
    for c, nm in [("has_dc", "≥1 discharge note"), ("has_rad", "≥1 radiology note"),
                  ("has_either", "either"), ("has_neither", "neither")]:
        k = int(df[c].sum())
        print(f"    {nm:20s}: {k:,} ({100*k/n:.1f}%)")


print("=" * 72 + "\nSTEP 5 — NOTE COVERAGE\n" + "=" * 72)
block(ap, "ALL analysis admissions")
block(ap[ap.code_positive], "CODE-POSITIVE admissions")

print("\n=== coverage by anchor_year_group (ALL) ===")
g = ap.groupby("anchor_year_group").agg(
    n=("hadm_id", "size"), dc=("has_dc", "mean"),
    rad=("has_rad", "mean"), either=("has_either", "mean"))
g[["dc", "rad", "either"]] = (g[["dc", "rad", "either"]] * 100).round(1)
print(g.to_string())

print("\n=== coverage by anchor_year_group (CODE-POSITIVE) ===")
gp = ap[ap.code_positive].groupby("anchor_year_group").agg(
    n=("hadm_id", "size"), dc=("has_dc", "mean"),
    rad=("has_rad", "mean"), either=("has_either", "mean"))
gp[["dc", "rad", "either"]] = (gp[["dc", "rad", "either"]] * 100).round(1)
print(gp.to_string())

print("\n=== SUBJECT-LEVEL (any admission with a note) ===")
subj = ap.groupby("subject_id")[["has_dc", "has_rad", "has_either"]].any()
subjp = ap[ap.code_positive].groupby("subject_id")[["has_dc", "has_rad", "has_either"]].any()
print(f"  analysis subjects: {len(subj):,}")
for c, nm in [("has_dc", "≥1 discharge"), ("has_rad", "≥1 radiology"), ("has_either", "either")]:
    print(f"    {nm:14s}: {int(subj[c].sum()):,} ({100*subj[c].mean():.1f}%)  | "
          f"code+ {int(subjp[c].sum()):,} ({100*subjp[c].mean():.1f}%)")

print("\n=== NULL-hadm_id radiology (outpatient imaging — NOT a linkage failure) ===")
rad_null = rad[rad.hadm_id.isna()]
ap_subj = set(ap.subject_id.unique())
rad_null_subj = set(rad_null.subject_id.dropna().astype("int64"))
print(f"  radiology notes with NULL hadm_id : {len(rad_null):,} "
      f"({100*len(rad_null)/len(rad):.1f}% of radiology)")
print(f"  distinct subjects (null-hadm rad) : {len(rad_null_subj):,}")
print(f"  of whom in analysis population    : {len(rad_null_subj & ap_subj):,}")

print("\n=== differential loss: % with EITHER note, by race (code+ vs code-) ===")
for grpcol in ["race", "insurance"]:
    tab = ap.groupby([grpcol, "code_positive"])["has_either"].mean().unstack() * 100
    cnt = ap.groupby(grpcol)["hadm_id"].size()
    tab = tab.assign(n=cnt).sort_values("n", ascending=False)
    tab = tab[cnt.reindex(tab.index) >= 500] if grpcol == "race" else tab
    print(f"\n  % EITHER note by {grpcol} (cols = code_positive False/True):")
    print(tab.round(1).to_string())

# save key totals for Table 0 update
either_n = int(ap.has_either.sum()); either_cp = int(ap[ap.code_positive].has_either.sum())
print("\n=== TABLE 0 PENDING-ROW INPUTS ===")
print(f"  analysis admissions WITH >=1 note (either): {either_n:,} "
      f"({100*either_n/N:.1f}%)  removed: {N-either_n:,}")
print(f"  code-positive WITH >=1 note: {either_cp:,} of 9,143 "
      f"({100*either_cp/9143:.1f}%)  removed: {9143-either_cp:,}")
print(f"  distinct subjects WITH >=1 note: {int(subj.has_either.sum()):,}")
