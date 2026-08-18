#!/usr/bin/env python3
"""Execute docs/cleaning_spec.md against the locked population (Steps 2-5).

Governing principle: NULL implausible values, never drop rows. Row count stays
373,992. Reuses make_tables.build_frame for the identical analytic frame, applies
approved physiological-possibility bounds, adds flags + missingness indicators,
runs the differential-nulling check, and materializes analysis_population_clean.parquet
(the uncleaned parquet is preserved). Aggregate reporting only.

Run: python scripts/clean_population.py
"""
import os
os.environ["POP_PARQUET"] = "data/processed/analysis_population.parquet"  # restrict build_frame

import numpy as np
import pandas as pd
import duckdb
from scripts.make_tables import build_frame
from scripts.masld_config import DATA, LAB_ITEMIDS

OUT = "data/processed/analysis_population_clean.parquet"
N_EXPECT = 373_992

# approved bounds: impossible if value < lo or > hi (glucose also <=0)
LAB_BOUNDS = {
    "ALT": (0, 50000), "AST": (0, 50000), "Platelets": (0, 5000),
    "Triglycerides": (0, 20000), "HDL": (0, 200), "HbA1c": (0, 20),
    "Glucose": (0, 3000), "Albumin": (0, 7), "Bilirubin_total": (0, 100),
    "Alkaline_phosphatase": (0, 20000), "GGT": (0, 20000),
}
OMR_BOUNDS = {"BMI": (8, 120), "SBP": (40, 300), "DBP": (20, 200)}
CAT_MISSING = ["insurance", "marital_status", "language",
               "discharge_location", "admission_location"]

con = duckdb.connect(); con.execute("SET memory_limit='24GB'")


def lab_impossible(name, s):
    lo, hi = LAB_BOUNDS[name]
    imp = (s < lo) | (s > hi)
    if name == "Glucose":
        imp = imp | (s <= 0)
    return imp & s.notna()


def main():
    df, _ = build_frame()
    assert len(df) == N_EXPECT, f"frame is {len(df)}, expected {N_EXPECT}"
    print(f"frame loaded: {len(df):,} admissions\n")
    report = {"labs": [], "omr": [], "temporal": [], "indicators": [], "diff": []}

    # ---------------- STEP 2: labs ----------------
    print("=" * 70 + "\nSTEP 2a — labs: null impossible, retain extreme-real\n" + "=" * 70)
    lab_names = list(LAB_ITEMIDS) + ["GGT"]
    nulled_lab = {}
    for name in lab_names:
        col = f"lab_{name}"
        if col not in df.columns:
            continue
        s = df[col]
        imp = lab_impossible(name, s)
        n_have = int(s.notna().sum()); n_imp = int(imp.sum())
        max_nulled = float(s[imp].max()) if n_imp else None
        max_ret = float(s[s.notna() & ~imp].max()) if (s.notna() & ~imp).any() else None
        nulled_lab[name] = imp.values.copy()
        df.loc[imp, col] = np.nan
        lo, hi = LAB_BOUNDS[name]
        report["labs"].append((name, n_have, n_imp, max_nulled, max_ret, f"[{lo},{hi}]"))
        print(f"  {name:22s} have={n_have:>9,}  nulled(impossible)={n_imp:>3}  "
              f"max_nulled={max_nulled}  max_retained={max_ret}")

    # C1 non-numeric value strings (report only, no coercion)
    idcsv = ",".join(str(i) for i in LAB_ITEMIDS.values())
    c1 = con.execute(f"""
      SELECT count(*) FROM read_csv_auto('{DATA}/labevents.csv.gz')
      WHERE itemid IN ({idcsv}) AND valuenum IS NULL AND value IS NOT NULL
    """).fetchone()[0]
    print(f"  [C1] non-numeric `value` w/ null valuenum (left as-is, not coerced): {c1}")

    # ---------------- STEP 2: omr (recompute with cleaning at reading level) ------
    print("\n" + "=" * 70 + "\nSTEP 2b — omr: parse BP, null impossible, drop dbp-zeros & post-dod\n" + "=" * 70)
    g1 = r"'^\s*(\d+)\s*/\s*(\d+)'"
    lo_bmi, hi_bmi = OMR_BOUNDS["BMI"]; lo_s, hi_s = OMR_BOUNDS["SBP"]; lo_d, hi_d = OMR_BOUNDS["DBP"]
    # reading-level null counts + BP parse failures
    counts = con.execute(f"""
      WITH o AS (
        SELECT r.subject_id, r.chartdate, r.result_name, r.result_value, p.dod
        FROM read_csv_auto('{DATA}/omr.csv.gz') r
        LEFT JOIN read_csv_auto('{DATA}/patients.csv.gz') p USING (subject_id)
      )
      SELECT
        count(*) FILTER (WHERE result_name IN ('BMI (kg/m2)','BMI')) AS bmi_n,
        count(*) FILTER (WHERE result_name IN ('BMI (kg/m2)','BMI')
                 AND (try_cast(result_value AS DOUBLE) < {lo_bmi}
                      OR try_cast(result_value AS DOUBLE) > {hi_bmi})) AS bmi_null,
        count(*) FILTER (WHERE result_name='Weight (Lbs)'
                 AND (try_cast(result_value AS DOUBLE) < 50
                      OR try_cast(result_value AS DOUBLE) > 1500)) AS wt_null,
        count(*) FILTER (WHERE result_name='Height (Inches)'
                 AND (try_cast(result_value AS DOUBLE) < 20
                      OR try_cast(result_value AS DOUBLE) > 108)) AS ht_null,
        count(*) FILTER (WHERE result_name='Blood Pressure') AS bp_n,
        count(*) FILTER (WHERE result_name='Blood Pressure'
                 AND NOT regexp_matches(result_value,'^\\s*\\d+\\s*/\\s*\\d+\\s*$')) AS bp_parsefail,
        count(*) FILTER (WHERE result_name='Blood Pressure'
                 AND try_cast(regexp_extract(result_value,{g1},2) AS INT)=0) AS dbp_zero,
        count(*) FILTER (WHERE result_name IN ('BMI (kg/m2)','BMI','Blood Pressure',
                 'Weight (Lbs)','Height (Inches)') AND dod IS NOT NULL AND chartdate > dod) AS postdod
      FROM o
    """).fetchone()
    print(f"  BMI readings={counts[0]:,}  nulled(out-of-range)={counts[1]:,}")
    print(f"  Weight nulled(out-of-range)={counts[2]:,}   Height nulled={counts[3]:,}")
    print(f"  BP readings={counts[4]:,}  parse-failures={counts[5]:,} "
          f"({100*counts[5]/counts[4]:.3f}%)  diastolic-zeros nulled={counts[6]:,}")
    print(f"  [T5] omr readings after dod (excluded): {counts[7]:,}")
    report["omr"] = counts

    # cleaned subject-level omr features (bounds + dbp!=0 + chartdate<=dod)
    omr = con.execute(f"""
      WITH o AS (
        SELECT r.subject_id, r.chartdate, r.result_name, r.result_value, p.dod
        FROM read_csv_auto('{DATA}/omr.csv.gz') r
        LEFT JOIN read_csv_auto('{DATA}/patients.csv.gz') p USING (subject_id)
      ),
      v AS (
        SELECT subject_id,
          CASE WHEN result_name IN ('BMI (kg/m2)','BMI')
               AND try_cast(result_value AS DOUBLE) BETWEEN {lo_bmi} AND {hi_bmi}
               AND (dod IS NULL OR chartdate <= dod)
               THEN try_cast(result_value AS DOUBLE) END AS bmi,
          CASE WHEN result_name='Blood Pressure'
               AND try_cast(regexp_extract(result_value,{g1},1) AS INT) BETWEEN {lo_s} AND {hi_s}
               AND (dod IS NULL OR chartdate <= dod)
               THEN try_cast(regexp_extract(result_value,{g1},1) AS INT) END AS sbp,
          CASE WHEN result_name='Blood Pressure'
               AND nullif(try_cast(regexp_extract(result_value,{g1},2) AS INT),0) BETWEEN {lo_d} AND {hi_d}
               AND (dod IS NULL OR chartdate <= dod)
               THEN try_cast(regexp_extract(result_value,{g1},2) AS INT) END AS dbp
        FROM o
      )
      SELECT subject_id, median(bmi) AS omr_BMI, bool_or(bmi IS NOT NULL) AS has_BMI,
             median(sbp) AS omr_SBP, bool_or(sbp IS NOT NULL) AS has_SBP,
             median(dbp) AS omr_DBP, bool_or(dbp IS NOT NULL) AS has_DBP
      FROM v GROUP BY subject_id
    """).fetchdf()
    # record which omr features change to null after cleaning (for Step 4)
    old = df[["subject_id", "omr_BMI", "omr_SBP", "omr_DBP"]].copy()
    df = df.drop(columns=["omr_BMI", "has_BMI", "omr_SBP", "has_SBP", "omr_DBP", "has_DBP"])
    df = df.merge(omr, on="subject_id", how="left")
    for c in ["has_BMI", "has_SBP", "has_DBP"]:
        df[c] = df[c].fillna(False)
    old = old.merge(df[["subject_id", "omr_BMI", "omr_SBP", "omr_DBP"]].drop_duplicates("subject_id"),
                    on="subject_id", suffixes=("_old", "_new"))
    nulled_omr = {m: (old[f"omr_{m}_old"].notna() & old[f"omr_{m}_new"].isna())
                  for m in ["BMI", "SBP", "DBP"]}

    # ---------------- STEP 2: temporal ----------------
    print("\n" + "=" * 70 + "\nSTEP 2c — temporal\n" + "=" * 70)
    tmp = con.execute(f"""
      SELECT a.hadm_id, a.admittime, a.dischtime, a.deathtime, a.discharge_location, p.dod
      FROM read_csv_auto('{DATA}/admissions.csv.gz') a
      JOIN read_csv_auto('{DATA}/patients.csv.gz') p USING (subject_id)
    """).fetchdf()
    df = df.merge(tmp, on="hadm_id", how="left")
    df["admittime"] = pd.to_datetime(df.admittime); df["dischtime"] = pd.to_datetime(df.dischtime)
    df["deathtime"] = pd.to_datetime(df.deathtime); df["dod"] = pd.to_datetime(df.dod)
    neg_los = df.admittime > df.dischtime
    df["flag_neg_los"] = neg_los
    df.loc[neg_los, "los_days"] = np.nan          # T1: null LOS, keep admission/timestamps
    df["flag_death_after_disch"] = df.deathtime.notna() & (
        (df.deathtime < df.admittime) | (df.deathtime > df.dischtime))   # T2
    df["flag_disch_after_dod"] = df.dod.notna() & (df.dischtime.dt.normalize() > df.dod)  # T3
    print(f"  [T1] neg-LOS admissions -> los_days nulled: {int(neg_los.sum()):,}")
    print(f"  [T2] deathtime outside stay -> flagged (no null): {int(df.flag_death_after_disch.sum()):,}")
    print(f"  [T3] dischtime after dod   -> flagged (no null): {int(df.flag_disch_after_dod.sum()):,}")

    # T4: labs outside admission window — concentration check (do NOT null)
    t4 = con.execute(f"""
      WITH a AS (SELECT hadm_id, admittime, dischtime
                 FROM read_csv_auto('{DATA}/admissions.csv.gz')),
      oow AS (
        SELECT l.hadm_id
        FROM read_csv_auto('{DATA}/labevents.csv.gz') l JOIN a USING (hadm_id)
        WHERE l.hadm_id IS NOT NULL AND (l.charttime < a.admittime OR l.charttime > a.dischtime)
      )
      SELECT count(*) AS n_oow, count(DISTINCT hadm_id) AS n_hadm,
             (SELECT count(DISTINCT hadm_id) FROM a) AS n_all
      FROM oow
    """).fetchone()
    print(f"  [T4] labs outside window: {t4[0]:,} rows across {t4[1]:,} admissions "
          f"({100*t4[1]/t4[2]:.1f}% of admissions) -> spread, not concentrated (do NOT null)")
    report["t4"] = t4

    # ---------------- STEP 3: missingness indicators ----------------
    print("\n" + "=" * 70 + "\nSTEP 3 — missingness indicators\n" + "=" * 70)
    ind_cols = []
    for name in lab_names:
        col = f"lab_{name}"
        if col in df.columns:
            df[f"miss_{col}"] = df[col].isna(); ind_cols.append(f"miss_{col}")
    for m in ["BMI", "SBP", "DBP"]:
        df[f"miss_omr_{m}"] = df[f"omr_{m}"].isna(); ind_cols.append(f"miss_omr_{m}")
    df["miss_los_days"] = df["los_days"].isna(); ind_cols.append("miss_los_days")
    for c in CAT_MISSING:
        df[f"miss_{c}"] = df[c].isna(); ind_cols.append(f"miss_{c}")
    print(f"  created {len(ind_cols)} indicator columns:")
    print("   " + ", ".join(ind_cols))
    report["indicators"] = ind_cols

    # ---------------- STEP 4: differential-nulling check ----------------
    print("\n" + "=" * 70 + "\nSTEP 4 — differential nulling (SMD by code status; range by race/insurance)\n" + "=" * 70)
    def smd_bin(p1, p0):
        d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
        return np.nan if d == 0 else (p1 - p0) / d
    cp = df.code_positive.values
    print(f"  {'variable':22s} {'nulled':>7s} {'null%code+':>10s} {'null%code-':>10s} {'SMD':>7s} {'race rng':>9s} {'ins rng':>8s}")
    def diff_row(label, nulled_mask, denom_mask):
        nulled_mask = np.asarray(nulled_mask); denom_mask = np.asarray(denom_mask)
        tot = int(nulled_mask.sum())
        d1 = denom_mask & cp; d0 = denom_mask & ~cp
        p1 = nulled_mask[d1].mean() if d1.sum() else 0.0
        p0 = nulled_mask[d0].mean() if d0.sum() else 0.0
        smd = smd_bin(p1, p0) if tot else 0.0
        rr = df.assign(_n=nulled_mask, _d=denom_mask)
        def rng(col):
            g = rr[rr._d].groupby(col)["_n"].agg(["mean", "size"])
            g = g[g["size"] >= 200]
            return (g["mean"].max() - g["mean"].min()) * 100 if len(g) else 0.0
        rrng = rng("race"); irng = rng("insurance")
        flag = "  <== differential" if (tot >= 20 and abs(smd) >= 0.1) else ""
        print(f"  {label:22s} {tot:>7,} {p1*100:>9.3f}% {p0*100:>9.3f}% {smd:>+7.3f} "
              f"{rrng:>8.1f} {irng:>7.1f}{flag}")
        report["diff"].append((label, tot, smd, rrng, irng))
    # labs: nulled-by-cleaning vs had-a-value-before-cleaning
    for name in nulled_lab:
        col = f"lab_{name}"
        nulled = nulled_lab[name]
        have = nulled | df[col].notna().values
        diff_row(f"lab_{name}", nulled, have)
    # omr: map subject-level nulled flag onto admissions
    subj_nulled = {m: dict(zip(old.subject_id, nulled_omr[m].values)) for m in ["BMI", "SBP", "DBP"]}
    for m in ["BMI", "SBP", "DBP"]:
        nulled = df.subject_id.map(subj_nulled[m]).fillna(False).values.astype(bool)
        have = nulled | df[f"omr_{m}"].notna().values
        diff_row(f"omr_{m}", nulled, have)

    # ---------------- STEP 5: materialize ----------------
    print("\n" + "=" * 70 + "\nSTEP 5 — materialize\n" + "=" * 70)
    df = df.drop(columns=["admittime", "dischtime", "deathtime", "dod"])  # keep frame light; reversible via raw
    assert len(df) == N_EXPECT, f"row count {len(df)} != {N_EXPECT}"
    con.register("clean_df", df)
    con.execute(f"COPY clean_df TO '{OUT}' (FORMAT parquet)")
    print(f"  wrote {OUT}: rows={len(df):,} cols={len(df.columns)}")
    print(f"  ASSERT row count == {N_EXPECT}: PASS")


if __name__ == "__main__":
    main()
