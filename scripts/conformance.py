#!/usr/bin/env python3
"""STEP 1 — CONFORMANCE tests (Kahn et al. 2016 DQ framework).

Kahn subclasses exercised here:
  * value conformance      (lab non-numeric text; units; omr numeric parsing)
  * relational conformance (labevents.hadm_id vs admissions)

Read-only. Reports; never coerces or deletes.
Run from project root with ./.venv active:
    python scripts/conformance.py
"""
import pandas as pd
import duckdb
from scripts.masld_config import DATA, LAB_ITEMIDS

pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# analytes to profile: the 10 approved + GGT candidate (flagged)
ANALYTES = dict(LAB_ITEMIDS)
ANALYTES_GGT = {"GGT_candidate": 50927, "GGT_candidate_dup": 53093}
ALL = {**ANALYTES, **ANALYTES_GGT}
itemid_csv = ",".join(str(i) for i in ALL.values())
id2name = {v: k for k, v in ALL.items()}

# Pull just the analyte rows from labevents once (10+2 itemids -> small).
lab = con.execute(f"""
  SELECT itemid, value, valuenum, valueuom, hadm_id
  FROM read_csv_auto('{DATA}/labevents.csv.gz')
  WHERE itemid IN ({itemid_csv})
""").fetchdf()
lab["analyte"] = lab.itemid.map(id2name)

print("=" * 72)
print("1a. VALUE CONFORMANCE — non-numeric lab values (valuenum IS NULL & value present)")
print("=" * 72)
for name in ALL:
    sub = lab[lab.analyte == name]
    nonnum = sub[(sub.valuenum.isna()) & (sub.value.notna())]
    tag = "  [CANDIDATE, not approved]" if name.startswith("GGT") else ""
    print(f"\n{name} (itemid {ALL[name]}){tag}: "
          f"{len(sub):,} rows | non-numeric-with-text: {len(nonnum):,}")
    vc = nonnum.value.value_counts().head(20)
    for val, n in vc.items():
        print(f"     {n:6,}  [{val}]")

print("\n" + "=" * 72)
print("1b. VALUE CONFORMANCE — units (valueuom) per analyte")
print("=" * 72)
for name in ALL:
    sub = lab[lab.analyte == name]
    vc = sub.valueuom.fillna("<NULL>").value_counts()
    flag = "   <-- >1 UNIT IN USE" if vc[vc.index != "<NULL>"].shape[0] > 1 else ""
    print(f"\n{name}{flag}")
    for u, n in vc.items():
        print(f"     {n:8,}  [{u}]")

print("\n" + "=" * 72)
print("1c. RELATIONAL CONFORMANCE — labevents.hadm_id vs admissions (ALL labevents)")
print("=" * 72)
rel = con.execute(f"""
  WITH adm AS (SELECT DISTINCT hadm_id FROM read_csv_auto('{DATA}/admissions.csv.gz'))
  SELECT
    count(*)                                              AS total_lab_rows,
    count(*) FILTER (WHERE l.hadm_id IS NULL)             AS null_hadm_outpatient,
    count(*) FILTER (WHERE l.hadm_id IS NOT NULL
                     AND a.hadm_id IS NULL)               AS orphan_hadm
  FROM read_csv_auto('{DATA}/labevents.csv.gz') l
  LEFT JOIN adm a USING (hadm_id)
""").fetchone()
print(f"  total labevents rows          : {rel[0]:,}")
print(f"  hadm_id NULL (outpatient labs) : {rel[1]:,}  ({100*rel[1]/rel[0]:.1f}%)")
print(f"  hadm_id present but NOT in admissions (orphan): {rel[2]:,}")

print("\n" + "=" * 72)
print("1d. VALUE CONFORMANCE — omr result_value numeric parsing")
print("=" * 72)
OMR_TYPES = ["BMI (kg/m2)", "Weight (Lbs)", "Height (Inches)", "Blood Pressure"]
for rn in OMR_TYPES:
    df = con.execute(f"""
      SELECT result_value,
             (try_cast(result_value AS DOUBLE) IS NOT NULL) AS parses
      FROM read_csv_auto('{DATA}/omr.csv.gz')
      WHERE result_name = '{rn}'
    """).fetchdf()
    n = len(df); ok = int(df.parses.sum())
    print(f"\n{rn}: {n:,} rows | parses as numeric: {ok:,} ({100*ok/n:.1f}%)")
    bad = df[~df.parses].result_value.value_counts().head(20)
    if len(bad):
        print("   non-parsing examples (value | count):")
        for v, c in bad.items():
            print(f"     {c:6,}  [{v}]")
    else:
        print("   (all parse)")

# Blood Pressure format: show it is systolic/diastolic in one string
print("\nBlood Pressure raw format sample (systolic/diastolic in one string):")
bp = con.execute(f"""
  SELECT result_value, count(*) n
  FROM read_csv_auto('{DATA}/omr.csv.gz')
  WHERE result_name='Blood Pressure' GROUP BY 1 ORDER BY n DESC LIMIT 8
""").fetchdf()
print(bp.to_string(index=False))
bp_fmt = con.execute(f"""
  SELECT
    count(*) AS n,
    count(*) FILTER (WHERE regexp_matches(result_value, '^\\s*\\d+\\s*/\\s*\\d+\\s*$')) AS sd_format
  FROM read_csv_auto('{DATA}/omr.csv.gz') WHERE result_name='Blood Pressure'
""").fetchone()
print(f"  matches systolic/diastolic 'NNN/NNN' format: {bp_fmt[1]:,} / {bp_fmt[0]:,} "
      f"({100*bp_fmt[1]/bp_fmt[0]:.1f}%)")
