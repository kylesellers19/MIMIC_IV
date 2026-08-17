#!/usr/bin/env python3
"""STEP 2 — PLAUSIBILITY tests, atemporal (Kahn et al. 2016 DQ framework).

Per lab analyte and omr measure: min, p0.1, p1, p50, p99, p99.9, max; plus
counts of IMPOSSIBLE values (negative / zero-where-impossible) reported
SEPARATELY from merely EXTREME values (outside a plausible physiologic range but
positive). Bounds and sources are stated below. Read-only; nothing deleted.

Reference intervals: Tietz Clinical Guide to Laboratory Tests, 4th ed.
Marker cutoffs: ADA Standards of Care (glucose, HbA1c); NCEP ATP III (lipids).
BMI: WHO. Plausibility ceilings: pragmatic physiologic maxima.

Run: python scripts/plausibility_atemporal.py
"""
import duckdb
from scripts.masld_config import DATA, LAB_ITEMIDS

con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# name -> (unit, impossible_predicate_on_x, plausible_low, plausible_high,
#          reference_interval_text, source)
LAB_LIMITS = {
    "ALT":                  ("IU/L", "x < 0", 0, 10000, "7-56", "Tietz"),
    "AST":                  ("IU/L", "x < 0", 0, 10000, "10-40", "Tietz"),
    "Platelets":            ("K/uL", "x < 0", 0, 2000, "150-450", "Tietz"),
    "Triglycerides":        ("mg/dL", "x < 0", 0, 10000, "<150", "NCEP ATP III"),
    "HDL":                  ("mg/dL", "x < 0", 0, 200, ">40", "NCEP ATP III"),
    "HbA1c":                ("%", "x < 0", 2, 20, "4.0-5.6", "ADA"),
    "Glucose":              ("mg/dL", "x <= 0", 10, 2000, "70-100 (fasting)", "ADA/Tietz"),
    "Albumin":              ("g/dL", "x < 0", 0.5, 7, "3.5-5.0", "Tietz"),
    "Bilirubin_total":      ("mg/dL", "x < 0", 0, 75, "0.1-1.2", "Tietz"),
    "Alkaline_phosphatase": ("IU/L", "x < 0", 0, 5000, "40-130", "Tietz"),
}

PROBES = "[0.001, 0.01, 0.5, 0.99, 0.999]"


print("=" * 72)
print("2a. LAB ANALYTES — atemporal plausibility")
print("=" * 72)
for name, (unit, imp, lo, hi, ref, src) in LAB_LIMITS.items():
    itemid = LAB_ITEMIDS[name]
    label_src = (f"read_csv_auto('{DATA}/labevents.csv.gz') WHERE itemid={itemid}")
    # wrap so the inner WHERE composes
    r = con.execute(f"""
      WITH t AS (SELECT valuenum AS v FROM read_csv_auto('{DATA}/labevents.csv.gz')
                 WHERE itemid={itemid} AND valuenum IS NOT NULL)
      SELECT count(*), min(v), max(v), quantile_cont(v,{PROBES}),
             count(*) FILTER (WHERE {imp.replace('x','v')}),
             count(*) FILTER (WHERE NOT ({imp.replace('x','v')}) AND (v<{lo} OR v>{hi}))
      FROM t
    """).fetchone()
    n, mn, mx, quant, impossible, extreme = r
    p001, p01, p50, p99, p999 = quant
    print(f"\n{name}  [{unit}]  ref {ref} ({src})   plausible [{lo}, {hi}]")
    print(f"    n={n:,}  min={mn:g}  p0.1={p001:g}  p1={p01:g}  p50={p50:g}  "
          f"p99={p99:g}  p99.9={p999:g}  max={mx:g}")
    print(f"    IMPOSSIBLE ({imp}): {impossible:,}   "
          f"EXTREME (positive, outside plausible): {extreme:,}")

print("\n" + "=" * 72)
print("2b. omr MEASURES — atemporal plausibility")
print("=" * 72)
# BMI/Weight/Height parse directly; BP split into systolic/diastolic.
OMR = {
    "BMI (kg/m2)":     ("try_cast(result_value AS DOUBLE)", "kg/m2", "v<=0", 10, 100, "18.5-24.9", "WHO"),
    "Weight (Lbs)":    ("try_cast(result_value AS DOUBLE)", "lb", "v<=0", 50, 1000, "-", "pragmatic"),
    "Height (Inches)": ("try_cast(result_value AS DOUBLE)", "in", "v<=0", 24, 90, "-", "pragmatic"),
}
for rn, (expr, unit, imp, lo, hi, ref, src) in OMR.items():
    r = con.execute(f"""
      WITH t AS (SELECT {expr} AS v FROM read_csv_auto('{DATA}/omr.csv.gz')
                 WHERE result_name='{rn}' AND {expr} IS NOT NULL)
      SELECT count(*), min(v), max(v), quantile_cont(v,{PROBES}),
             count(*) FILTER (WHERE {imp}),
             count(*) FILTER (WHERE NOT ({imp}) AND (v<{lo} OR v>{hi}))
      FROM t
    """).fetchone()
    n, mn, mx, quant, impossible, extreme = r
    p001, p01, p50, p99, p999 = quant
    print(f"\n{rn}  [{unit}]  ref {ref} ({src})   plausible [{lo}, {hi}]")
    print(f"    n={n:,}  min={mn:g}  p0.1={p001:g}  p1={p01:g}  p50={p50:g}  "
          f"p99={p99:g}  p99.9={p999:g}  max={mx:g}")
    print(f"    IMPOSSIBLE ({imp}): {impossible:,}   EXTREME: {extreme:,}")

# Blood pressure: systolic/diastolic split
for part, idx, lo, hi in [("Systolic", 1, 50, 300), ("Diastolic", 2, 20, 200)]:
    r = con.execute(f"""
      WITH t AS (
        SELECT try_cast(regexp_extract(result_value,'^\\s*(\\d+)\\s*/\\s*(\\d+)',{idx}) AS INTEGER) AS v
        FROM read_csv_auto('{DATA}/omr.csv.gz') WHERE result_name='Blood Pressure')
      SELECT count(*) FILTER (WHERE v IS NOT NULL), min(v), max(v),
             quantile_cont(v,{PROBES}) FILTER (WHERE v IS NOT NULL),
             count(*) FILTER (WHERE v<=0),
             count(*) FILTER (WHERE v>0 AND (v<{lo} OR v>{hi}))
      FROM t
    """).fetchone()
    n, mn, mx, quant, impossible, extreme = r
    p001, p01, p50, p99, p999 = quant
    print(f"\nBlood Pressure - {part}  [mmHg]   plausible [{lo}, {hi}]")
    print(f"    n={n:,}  min={mn:g}  p0.1={p001:g}  p1={p01:g}  p50={p50:g}  "
          f"p99={p99:g}  p99.9={p999:g}  max={mx:g}")
    print(f"    IMPOSSIBLE (<=0): {impossible:,}   EXTREME: {extreme:,}")
