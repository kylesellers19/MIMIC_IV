#!/usr/bin/env python3
"""STEP 4 — Table 1: MASLD-coded admissions vs all other admissions. Read-only.

Grain = admission (hadm_id). Reports median [IQR] for continuous variables,
n (%) for categorical, and standardized mean differences (NOT p-values):
  * continuous  -> SMD from means/SDs
  * binary      -> proportion SMD
  * categorical -> Yang & Dalton multinomial SMD (as in tableone / cobalt)
Missing values in categorical vars are kept as an explicit 'Missing' level so
differential missingness is visible in the SMD.

Run from project root with ./.venv active:
    python scripts/table1.py
"""
import numpy as np
import pandas as pd
import duckdb

pd.set_option("display.width", 200)

DATA = "data/raw/hosp"
con = duckdb.connect()
con.execute("SET memory_limit='24GB';")

con.execute(f"""
CREATE TEMP VIEW masld_hadm AS
  SELECT DISTINCT hadm_id
  FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}})
  WHERE (icd_version=10 AND trim(icd_code) IN ('K760','K7581'))
     OR (icd_version=9  AND trim(icd_code) IN ('5718','5719'));
""")

df = con.execute(f"""
SELECT
  a.hadm_id,
  (a.hadm_id IN (SELECT hadm_id FROM masld_hadm)) AS is_masld,
  p.anchor_age,
  p.gender,
  a.race, a.insurance, a.language, a.marital_status, a.admission_type,
  a.hospital_expire_flag,
  date_diff('second', a.admittime, a.dischtime)/86400.0 AS los_days,
  coalesce(d.n_dx, 0) AS n_diagnoses
FROM read_csv_auto('{DATA}/admissions.csv.gz') a
JOIN read_csv_auto('{DATA}/patients.csv.gz') p USING (subject_id)
LEFT JOIN (SELECT hadm_id, count(*) AS n_dx
           FROM read_csv_auto('{DATA}/diagnoses_icd.csv.gz') GROUP BY hadm_id) d
       USING (hadm_id)
""").fetchdf()

g1 = df[df.is_masld]       # coded-positive
g0 = df[~df.is_masld]      # rest
n1, n0 = len(g1), len(g0)
print(f"MASLD-coded admissions: {n1:,}   |   other admissions: {n0:,}\n")


def smd_cont(a, b):
    a, b = a.dropna(), b.dropna()
    m1, m2, s1, s2 = a.mean(), b.mean(), a.std(ddof=1), b.std(ddof=1)
    denom = np.sqrt((s1**2 + s2**2) / 2)
    return np.nan if denom == 0 else (m1 - m2) / denom


def smd_binary(p1, p2):
    denom = np.sqrt((p1*(1-p1) + p2*(1-p2)) / 2)
    return np.nan if denom == 0 else (p1 - p2) / denom


def smd_multinomial(s1, s0):
    # proportion vectors over the union of categories (NaN -> 'Missing')
    s1 = s1.fillna("Missing"); s0 = s0.fillna("Missing")
    cats = sorted(set(s1.unique()) | set(s0.unique()))
    p1 = np.array([(s1 == c).mean() for c in cats])
    p2 = np.array([(s0 == c).mean() for c in cats])
    if len(cats) < 2:
        return np.nan
    P1, P2 = p1[:-1], p2[:-1]                      # drop last -> nonsingular
    def cov(P):
        S = -np.outer(P, P)
        S[np.diag_indices(len(P))] = P * (1 - P)
        return S
    S = (cov(P1) + cov(P2)) / 2
    T = (P1 - P2)
    try:
        val = float(T @ np.linalg.pinv(S) @ T)
        return np.sqrt(max(val, 0))
    except np.linalg.LinAlgError:
        return np.nan


def med_iqr(s):
    s = s.dropna()
    return f"{s.median():.1f} [{s.quantile(.25):.1f}, {s.quantile(.75):.1f}]"


def show_cont(name, col):
    smd = smd_cont(g1[col], g0[col])
    print(f"{name}")
    print(f"    coded : {med_iqr(g1[col])}    other : {med_iqr(g0[col])}    SMD={smd:+.3f}")


def show_binary(name, col, positive):
    p1 = (g1[col] == positive).mean(); p0 = (g0[col] == positive).mean()
    smd = smd_binary(p1, p0)
    print(f"{name} (= {positive})")
    print(f"    coded : {p1*100:5.1f}%    other : {p0*100:5.1f}%    SMD={smd:+.3f}")


def show_cat(name, col, top=None):
    smd = smd_multinomial(g1[col], g0[col])
    c1 = g1[col].fillna("Missing").value_counts()
    c0 = g0[col].fillna("Missing").value_counts()
    print(f"{name}    (multinomial SMD={smd:+.3f})")
    order = c0.index if top is None else c0.index[:top]
    for c in order:
        v1 = c1.get(c, 0); v0 = c0.get(c, 0)
        print(f"    {str(c)[:42]:42s} coded {v1:6,} ({v1/n1*100:4.1f}%)   "
              f"other {v0:8,} ({v0/n0*100:4.1f}%)")
    if top is not None and len(c0.index) > top:
        print(f"    ... (+{len(c0.index)-top} more {col} categories; SMD uses all)")


print("=" * 70); print("TABLE 1"); print("=" * 70)
print("\n-- Continuous: median [IQR] --")
show_cont("anchor_age (years)", "anchor_age")
show_cont("length of stay (days)", "los_days")
show_cont("diagnoses per admission (n)", "n_diagnoses")

print("\n-- Binary --")
show_binary("gender", "gender", "M")
show_binary("hospital_expire_flag", "hospital_expire_flag", 1)

print("\n-- Categorical: n (%) --")
show_cat("admission_type", "admission_type")
show_cat("insurance", "insurance")
show_cat("marital_status", "marital_status")
show_cat("language", "language", top=6)
show_cat("race", "race", top=8)

# LOS data-quality flags
neg = int((df.los_days < 0).sum()); zero = int((df.los_days == 0).sum())
print(f"\nLOS flags: negative={neg:,}  zero={zero:,}  "
      f"max={df.los_days.max():.1f}d  (coded max={g1.los_days.max():.1f}d)")
