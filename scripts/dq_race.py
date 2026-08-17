#!/usr/bin/env python3
"""STEP 3 — Race/ethnicity characterization (drives Aim 1c). Read-only.

Prints: verbatim race value counts; count + 20-patient sample of subjects whose
race differs across their own admissions; and race x {admission_type, insurance}
cross-tabs (pandas crosstab for readable wide output). No categories collapsed.

Run from project root with ./.venv active:
    python scripts/dq_race.py
"""
import pandas as pd
import duckdb

pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 240)

con = duckdb.connect()
adm = con.execute(
    "SELECT subject_id, hadm_id, race, admission_type, insurance "
    "FROM read_csv_auto('data/raw/hosp/admissions.csv.gz')"
).fetchdf()

print("=" * 70)
print("STEP 3 — RACE / ETHNICITY")
print("=" * 70)

# (2a) subjects with inconsistent race
per_subj = adm.groupby("subject_id")["race"].nunique()
n_incons = int((per_subj > 1).sum())
n_multi = int((adm.groupby("subject_id")["hadm_id"].nunique() > 1).sum())
print(f"\nSubjects with >1 distinct race across their admissions: {n_incons:,}")
print(f"  (context: {n_multi:,} subjects have >1 admission; "
      f"{len(per_subj):,} subjects total in admissions)")

# (2b) sample of 20 most-divergent
incons_ids = per_subj[per_subj > 1].index
sub = adm[adm.subject_id.isin(incons_ids)]
sample = (sub.groupby("subject_id")
          .agg(n_distinct_race=("race", "nunique"),
               n_admissions=("hadm_id", "nunique"),
               race_values=("race", lambda s: sorted(set(s))))
          .sort_values(["n_distinct_race", "subject_id"], ascending=[False, True])
          .head(20))
print("\n20 subjects with divergent race (most distinct values first):")
for sid, r in sample.iterrows():
    print(f"  {sid}  n_adm={r.n_admissions}  {r.race_values}")

# (3) cross-tabs
print("\n--- (3a) race x admission_type ---")
ct1 = pd.crosstab(adm.race, adm.admission_type, margins=True, margins_name="TOTAL")
ct1 = ct1.sort_values("TOTAL", ascending=False)
print(ct1.to_string())

print("\n--- (3b) race x insurance ---")
ct2 = pd.crosstab(adm.race, adm.insurance, margins=True, margins_name="TOTAL")
ct2 = ct2.sort_values("TOTAL", ascending=False)
print(ct2.to_string())

# row-normalized insurance mix per race (what collapsing would blur)
print("\n--- (3c) race x insurance, row-normalized % (payer mix per race) ---")
ct2n = pd.crosstab(adm.race, adm.insurance, normalize="index").round(3) * 100
ct2n = ct2n.reindex(ct1.index.drop("TOTAL"))
print(ct2n.to_string())
