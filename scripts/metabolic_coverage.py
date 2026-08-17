#!/usr/bin/env python3
"""STEP 5 — Metabolic context of the coded-positive cohort. Read-only.

(A) omr result_name value counts + coverage among coded-positive subjects.
(B) labevents coverage of 10 analytes for the coded-positive cohort. Itemids are
    resolved by searching d_labitems label text; the matched (itemid, label,
    fluid, category) rows are PRINTED for verification before use. Coverage =
    % of coded-positive subjects with >=1 result. Match sets that span multiple
    fluids are flagged (they can inflate coverage).

Run from project root with ./.venv active:
    python scripts/metabolic_coverage.py
"""
import pandas as pd
import duckdb

pd.set_option("display.width", 200); pd.set_option("display.max_rows", 300)

DATA = "data/raw/hosp"
con = duckdb.connect()
con.execute("SET memory_limit='24GB';")

# Coded-positive subjects (version-aware, trimmed) -> temp table
con.execute(f"""
CREATE TEMP TABLE coded AS
  SELECT DISTINCT subject_id
  FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}})
  WHERE (icd_version=10 AND trim(icd_code) IN ('K760','K7581'))
     OR (icd_version=9  AND trim(icd_code) IN ('5718','5719'));
""")
N = con.execute("SELECT count(*) FROM coded").fetchone()[0]
print(f"coded-positive subjects (denominator) = {N:,}\n")

# ---------------------------------------------------------------- (A) omr
print("=" * 70); print("(A) omr result_name — overall + coded-positive coverage")
print("=" * 70)
omr = con.execute(f"""
  SELECT result_name,
         count(*)                        AS n_rows_overall,
         count(DISTINCT subject_id)       AS subj_overall,
         count(DISTINCT subject_id) FILTER (WHERE subject_id IN (SELECT subject_id FROM coded))
                                          AS subj_coded
  FROM read_csv_auto('{DATA}/omr.csv.gz')
  GROUP BY result_name ORDER BY n_rows_overall DESC
""").fetchdf()
omr["coded_coverage_%"] = (100 * omr.subj_coded / N).round(1)
print(omr.to_string(index=False))

# ---------------------------------------------------------------- (B) labevents
print("\n" + "=" * 70)
print("(B) labevents analyte itemid resolution + coded coverage")
print("=" * 70)

# label search patterns (ILIKE); broad on purpose so we can eyeball matches
ANALYTES = {
    "ALT":                  ["%alanine aminotransferase%"],
    "AST":                  ["%aspartate aminotransferase%", "%asparate aminotransferase%"],
    "Platelets":            ["%platelet count%"],
    "Triglycerides":        ["%triglyceride%"],
    "HDL":                  ["%hdl%"],
    "HbA1c":                ["%a1c%", "%glycated%"],
    "Glucose":              ["%glucose%"],
    "Albumin":              ["%albumin%"],
    "Bilirubin":            ["%bilirubin%"],
    "Alkaline phosphatase": ["%alkaline phosphatase%"],
}

dlab = con.execute(
    f"SELECT itemid, label, fluid, category FROM read_csv_auto('{DATA}/d_labitems.csv.gz')"
).fetchdf()

# resolve itemids per analyte
resolved = {}   # analyte -> list of itemids
print("\n--- matched itemids (VERIFY THESE) ---")
for analyte, pats in ANALYTES.items():
    mask = pd.Series(False, index=dlab.index)
    for p in pats:
        mask |= dlab.label.str.lower().str.contains(p.strip("%").lower(), na=False)
    hits = dlab[mask]
    resolved[analyte] = hits.itemid.tolist()
    fluids = hits.fluid.nunique()
    flag = "  <-- spans multiple fluids" if fluids > 1 else ""
    print(f"\n{analyte}: {len(hits)} itemid(s){flag}")
    for _, r in hits.iterrows():
        print(f"    {r.itemid:>6}  [{r.fluid}/{r.category}]  {r.label}")

# one labevents scan: rows for coded subjects & any matched itemid
all_itemids = sorted({i for ids in resolved.values() for i in ids})
itemid_csv = ",".join(str(i) for i in all_itemids)
lab = con.execute(f"""
  SELECT DISTINCT subject_id, itemid
  FROM read_csv_auto('{DATA}/labevents.csv.gz')
  WHERE itemid IN ({itemid_csv})
    AND subject_id IN (SELECT subject_id FROM coded)
""").fetchdf()

print("\n--- coded-positive coverage per analyte (>=1 result) ---")
rows = []
for analyte, ids in resolved.items():
    subj = lab[lab.itemid.isin(ids)].subject_id.nunique()
    rows.append((analyte, subj, round(100*subj/N, 1)))
cov = pd.DataFrame(rows, columns=["analyte", "n_coded_subj", "coverage_%"])
cov = cov.sort_values("coverage_%", ascending=False)
print(cov.to_string(index=False))

low = cov[cov["coverage_%"] < 10]
if len(low):
    print("\nFLAG — coverage < 10% (candidate 'too sparse to use', researcher decides):")
    print("  " + ", ".join(f"{r.analyte} ({r['coverage_%']}%)" for _, r in low.iterrows()))
