#!/usr/bin/env python3
"""Descriptive tables from the locked analytic frame (admission grain).

Decisions come from scripts/masld_config.py (grain=admission, zero-dx excluded,
race non-informative kept explicit, dx count = distinct (seq_num, icd_version),
blood/serum itemids, GGT 50927). This is a NUMBERS-CHECK pass: denominators will
change once the note-coverage window exists.

Grouping is parameterized: set GROUP_SPEC. Now = code_status (code+/code-).
Later add a 'cell_2x2' grouping and every table regenerates unchanged.

Outputs MARKDOWN + CSV to docs/tables/ (aggregates only; no patient-level rows).
Run: python scripts/make_tables.py
"""
import os
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, MASLD_PREDICATE, LAB_ITEMIDS

OUTDIR = os.environ.get("TABLES_OUTDIR", "docs/tables")
POP_PARQUET = os.environ.get("POP_PARQUET")   # if set, restrict to these hadm_ids
SUPPRESS_N = 11           # our own threshold (see footnotes); suppress 0<n<11
os.makedirs(OUTDIR, exist_ok=True)
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

ANALYTE_IDS = dict(LAB_ITEMIDS); ANALYTE_IDS["GGT"] = 50927   # 53093 omitted
SUPPRESSED = []           # (table, row, group)

# ----------------------------------------------------------------- grouping
def grouping_code_status(df):
    s = pd.Series(np.where(df.code_positive, "code-positive", "code-negative"),
                  index=df.index)
    return s, ["code-positive", "code-negative"]

GROUPINGS = {"code_status": grouping_code_status}
GROUP_SPEC = "code_status"       # <-- change this one argument to regenerate

# ----------------------------------------------------------------- build frame
def build_frame():
    frame_parquet = os.environ.get("FRAME_PARQUET")
    if frame_parquet:
        # Load a pre-built (e.g. cleaned) frame directly; skip raw recomputation.
        df = con.execute(f"SELECT * FROM read_parquet('{frame_parquet}')").fetchdf()
        g1 = r"'^\s*(\d+)\s*/\s*(\d+)'"
        bpstat = con.execute(f"""
          SELECT count(*),
                 count(*) FILTER (WHERE regexp_matches(result_value,'^\\s*\\d+\\s*/\\s*\\d+\\s*$')),
                 count(*) FILTER (WHERE nullif(try_cast(regexp_extract(result_value,{g1},2) AS INT),0) IS NULL
                                  AND regexp_matches(result_value,'^\\s*\\d+\\s*/\\s*\\d+\\s*$'))
          FROM read_csv_auto('{DATA}/omr.csv.gz') WHERE result_name='Blood Pressure'
        """).fetchone()
        print(f"[frame] loaded {len(df):,} admissions from {frame_parquet}")
        return df, bpstat

    con.execute(f"""
    CREATE TEMP VIEW base AS
    WITH dx AS (
      SELECT hadm_id,
             count(DISTINCT (seq_num, icd_version)) AS n_diagnoses,
             max(CASE WHEN {MASLD_PREDICATE} THEN 1 ELSE 0 END) AS masld,
             min(icd_version) AS minv, max(icd_version) AS maxv
      FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}})
      GROUP BY hadm_id
    )
    SELECT a.hadm_id, a.subject_id,
           (dx.masld=1) AS code_positive,
           dx.n_diagnoses,
           LEAST(p.anchor_age + year(a.admittime) - p.anchor_year, 91) AS age,
           p.gender, a.race, a.insurance, a.language, a.marital_status,
           a.admission_type, a.admission_location,
           a.hospital_expire_flag,
           date_diff('second', a.admittime, a.dischtime)/86400.0 AS los_days,
           CASE WHEN dx.minv=9 AND dx.maxv=9 THEN 'ICD-9 only'
                WHEN dx.minv=10 AND dx.maxv=10 THEN 'ICD-10 only'
                ELSE 'Both' END AS icd_era
    FROM read_csv_auto('{DATA}/admissions.csv.gz') a
    JOIN dx USING (hadm_id)
    JOIN read_csv_auto('{DATA}/patients.csv.gz') p USING (subject_id)
    """)
    df = con.execute("SELECT * FROM base").fetchdf()

    if POP_PARQUET:
        keep = con.execute(
            f"SELECT DISTINCT hadm_id FROM read_parquet('{POP_PARQUET}')"
        ).fetchdf().hadm_id
        before = len(df)
        df = df[df.hadm_id.isin(set(keep))].reset_index(drop=True)
        print(f"[restricted] {POP_PARQUET}: {before:,} -> {len(df):,} admissions")

    # per-admission first lab value (hadm_id-linked, earliest charttime)
    ids = ",".join(str(i) for i in ANALYTE_IDS.values())
    lab = con.execute(f"""
      SELECT hadm_id, itemid, arg_min(valuenum, charttime) AS first_val
      FROM read_csv_auto('{DATA}/labevents.csv.gz')
      WHERE itemid IN ({ids}) AND hadm_id IS NOT NULL
        AND valuenum IS NOT NULL AND charttime IS NOT NULL
      GROUP BY hadm_id, itemid
    """).fetchdf()
    id2name = {v: k for k, v in ANALYTE_IDS.items()}
    piv = lab.pivot(index="hadm_id", columns="itemid", values="first_val")
    piv.columns = [f"lab_{id2name[c]}" for c in piv.columns]
    df = df.merge(piv, left_on="hadm_id", right_index=True, how="left")

    # omr subject-level summary (no hadm_id in omr); BP parsed, dbp zeros excluded
    g1 = r"'^\s*(\d+)\s*/\s*(\d+)'"
    omr = con.execute(f"""
      SELECT subject_id,
        median(CASE WHEN result_name IN ('BMI (kg/m2)','BMI')
                    THEN try_cast(result_value AS DOUBLE) END) AS omr_BMI,
        bool_or(result_name IN ('BMI (kg/m2)','BMI')
                AND try_cast(result_value AS DOUBLE) IS NOT NULL) AS has_BMI,
        median(CASE WHEN result_name='Blood Pressure'
                    THEN try_cast(regexp_extract(result_value,{g1},1) AS INT) END) AS omr_SBP,
        bool_or(result_name='Blood Pressure'
                AND try_cast(regexp_extract(result_value,{g1},1) AS INT) IS NOT NULL) AS has_SBP,
        median(CASE WHEN result_name='Blood Pressure'
                    THEN nullif(try_cast(regexp_extract(result_value,{g1},2) AS INT),0) END) AS omr_DBP,
        bool_or(result_name='Blood Pressure'
                AND nullif(try_cast(regexp_extract(result_value,{g1},2) AS INT),0) IS NOT NULL) AS has_DBP
      FROM read_csv_auto('{DATA}/omr.csv.gz')
      GROUP BY subject_id
    """).fetchdf()
    df = df.merge(omr, on="subject_id", how="left")
    for c in ["has_BMI", "has_SBP", "has_DBP"]:
        df[c] = df[c].fillna(False)

    # BP parse diagnostics (reported in Table 2 footnote)
    bpstat = con.execute(f"""
      SELECT count(*) tot,
             count(*) FILTER (WHERE regexp_matches(result_value,'^\\s*\\d+\\s*/\\s*\\d+\\s*$')) ok,
             count(*) FILTER (WHERE nullif(try_cast(regexp_extract(result_value,{g1},2) AS INT),0) IS NULL
                              AND regexp_matches(result_value,'^\\s*\\d+\\s*/\\s*\\d+\\s*$')) dbp_zero
      FROM read_csv_auto('{DATA}/omr.csv.gz') WHERE result_name='Blood Pressure'
    """).fetchone()
    return df, bpstat

# ----------------------------------------------------------------- stat helpers
def med_iqr(s):
    s = s.dropna()
    if len(s) == 0:
        return "-"
    if 0 < len(s) < SUPPRESS_N:
        return "<11*"
    return f"{s.median():.1f} [{s.quantile(.25):.1f}, {s.quantile(.75):.1f}]"

def smd_cont(a, b):
    a, b = a.dropna(), b.dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return np.nan if d == 0 else (a.mean() - b.mean()) / d

def smd_bin(p1, p2):
    d = np.sqrt((p1*(1-p1) + p2*(1-p2)) / 2)
    return np.nan if d == 0 else (p1 - p2) / d

def smd_multi(s1, s0):
    s1, s0 = s1.fillna("Missing"), s0.fillna("Missing")
    cats = sorted(set(s1) | set(s0))
    if len(cats) < 2:
        return np.nan
    p1 = np.array([(s1 == c).mean() for c in cats])[:-1]
    p2 = np.array([(s0 == c).mean() for c in cats])[:-1]
    def cov(P):
        S = -np.outer(P, P); S[np.diag_indices(len(P))] = P*(1-P); return S
    S = (cov(p1) + cov(p2)) / 2
    try:
        return float(np.sqrt(max((p1-p2) @ np.linalg.pinv(S) @ (p1-p2), 0)))
    except np.linalg.LinAlgError:
        return np.nan

def n_pct(n, denom, table, rowlabel, group):
    if 0 < n < SUPPRESS_N:
        SUPPRESSED.append((table, rowlabel, group))
        return "<11*"
    return f"{n:,} ({100*n/denom:.1f})"

def fmt_smd(x):
    return "" if (x is None or (isinstance(x, float) and np.isnan(x))) else f"{x:+.3f}"

# ----------------------------------------------------------------- rendering
def to_md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    return "\n".join(out)

def write(name, df, title, footnotes):
    df.to_csv(f"{OUTDIR}/{name}.csv", index=False)
    md = f"# {title}\n\n{to_md(df)}\n\n" + "\n".join(f"- {f}" for f in footnotes) + "\n"
    with open(f"{OUTDIR}/{name}.md", "w") as fh:
        fh.write(md)
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)
    print(to_md(df))
    for f in footnotes:
        print(f"  ^ {f}")


# ----------------------------------------------------------------- row helpers
def cont_rows(rows, df, masks, groups, col, label, table):
    g0, g1 = groups[0], groups[1]
    r = {"Characteristic": label}
    for g in groups:
        r[g] = med_iqr(df.loc[masks[g], col])
    r["Overall"] = med_iqr(df[col])
    r["SMD"] = fmt_smd(smd_cont(df.loc[masks[g0], col], df.loc[masks[g1], col]))
    rows.append(r)
    m = {"Characteristic": "  Missing, n (%)", "SMD": ""}
    for g in groups:
        m[g] = n_pct(int(df.loc[masks[g], col].isna().sum()), int(masks[g].sum()),
                     table, f"{label}/missing", g)
    m["Overall"] = n_pct(int(df[col].isna().sum()), len(df), table, f"{label}/missing", "Overall")
    rows.append(m)


def cat_rows(rows, df, masks, groups, col, label, table):
    g0, g1 = groups[0], groups[1]
    h = {"Characteristic": label, "SMD": fmt_smd(smd_multi(
        df.loc[masks[g0], col], df.loc[masks[g1], col]))}
    for g in groups:
        h[g] = ""
    h["Overall"] = ""
    rows.append(h)
    for lv in df[col].value_counts(dropna=True).index.tolist():
        r = {"Characteristic": f"  {lv}", "SMD": ""}
        for g in groups:
            r[g] = n_pct(int((df.loc[masks[g], col] == lv).sum()), int(masks[g].sum()),
                         table, f"{label}={lv}", g)
        r["Overall"] = n_pct(int((df[col] == lv).sum()), len(df), table, f"{label}={lv}", "Overall")
        rows.append(r)
    if df[col].isna().any():
        r = {"Characteristic": "  Missing", "SMD": ""}
        for g in groups:
            r[g] = n_pct(int(df.loc[masks[g], col].isna().sum()), int(masks[g].sum()),
                         table, f"{label}=Missing", g)
        r["Overall"] = n_pct(int(df[col].isna().sum()), len(df), table, f"{label}=Missing", "Overall")
        rows.append(r)


def binary_row(rows, df, masks, groups, col, posval, label, table):
    g0, g1 = groups[0], groups[1]
    r = {"Characteristic": label, "SMD": ""}
    for g in groups:
        sub = df.loc[masks[g], col]
        r[g] = n_pct(int((sub == posval).sum()), len(sub), table, label, g)
    r["Overall"] = n_pct(int((df[col] == posval).sum()), len(df), table, label, "Overall")
    r["SMD"] = fmt_smd(smd_bin((df.loc[masks[g0], col] == posval).mean(),
                               (df.loc[masks[g1], col] == posval).mean()))
    rows.append(r)


def avail_cell(n, denom, table, label, group):
    if 0 < n < SUPPRESS_N:
        SUPPRESSED.append((table, label, group))
        return "<11*"
    return f"{100*n/denom:.1f}% ({n:,})"


# ----------------------------------------------------------------- tables
def table0(df):
    a = con.execute(f"SELECT count(*), count(DISTINCT subject_id) "
                    f"FROM read_csv_auto('{DATA}/admissions.csv.gz')").fetchone()
    z = con.execute(f"""SELECT count(*), count(DISTINCT subject_id)
        FROM read_csv_auto('{DATA}/admissions.csv.gz') a
        WHERE a.hadm_id NOT IN (
          SELECT hadm_id FROM read_csv('{DATA}/diagnoses_icd.csv.gz',
                 types={{'icd_code':'VARCHAR'}}) GROUP BY hadm_id)""").fetchone()
    cp = df[df.code_positive]; cn = df[~df.code_positive]
    rows = [
        {"Step": "All admissions (MIMIC-IV v3.1 hosp)", "Admissions (n)": f"{a[0]:,}",
         "Distinct subjects (n)": f"{a[1]:,}"},
        {"Step": "− Admissions with zero diagnosis rows (excluded)",
         "Admissions (n)": f"−{z[0]:,}", "Distinct subjects (n)": f"({z[1]:,} affected)"},
        {"Step": "= Analysis population", "Admissions (n)": f"{len(df):,}",
         "Distinct subjects (n)": f"{df.subject_id.nunique():,}"},
        {"Step": "  · MASLD code-positive", "Admissions (n)": f"{len(cp):,}",
         "Distinct subjects (n)": f"{cp.subject_id.nunique():,}"},
        {"Step": "  · MASLD code-negative", "Admissions (n)": f"{len(cn):,}",
         "Distinct subjects (n)": f"{cn.subject_id.nunique():,}"},
        {"Step": "− Note-coverage restriction", "Admissions (n)": "PENDING",
         "Distinct subjects (n)": "PENDING"},
    ]
    write("table0", pd.DataFrame(rows), "Table 0 — Cohort derivation / flow counts", [
        "Grain = admission (hadm_id). Zero-diagnosis admissions excluded per locked decision.",
        "Distinct-subject counts overlap across code+/code− (a subject may have both coded and "
        "uncoded admissions), so 5,580 + 221,396 > 223,291.",
        "Note-coverage restriction is a PENDING placeholder; all denominators below change once "
        "MIMIC-IV-Note is in place.",
    ])


def table1(df, masks, groups):
    rows = []
    cont_rows(rows, df, masks, groups, "age", "Age at admission, median [IQR] †", "T1")
    cat_rows(rows, df, masks, groups, "gender", "Sex, n (%)", "T1")
    cat_rows(rows, df, masks, groups, "race", "Race (as recorded), n (%)", "T1")
    cat_rows(rows, df, masks, groups, "insurance", "Insurance, n (%)", "T1")
    cat_rows(rows, df, masks, groups, "language", "Language, n (%)", "T1")
    cat_rows(rows, df, masks, groups, "marital_status", "Marital status, n (%)", "T1")
    cat_rows(rows, df, masks, groups, "admission_type", "Admission type, n (%)", "T1")
    cat_rows(rows, df, masks, groups, "admission_location", "Admission location, n (%)", "T1")
    cont_rows(rows, df, masks, groups, "los_days", "Length of stay (days), median [IQR]", "T1")
    binary_row(rows, df, masks, groups, "hospital_expire_flag", 1,
               "In-hospital death, n (%)", "T1")
    cont_rows(rows, df, masks, groups, "n_diagnoses",
              "Distinct diagnoses, median [IQR]", "T1")
    cat_rows(rows, df, masks, groups, "icd_era", "ICD version era, n (%)", "T1")
    cols = ["Characteristic"] + groups + ["Overall", "SMD"]
    write("table1", pd.DataFrame(rows)[cols], "Table 1 — Cohort characteristics", [
        "† Age = anchor_age + year(admittime) − anchor_year, capped at 91. MIMIC collapses ages "
        "≥89 to 91, so the upper tail is NOT a true distribution.",
        "Continuous: median [IQR]. Categorical: n (%) within group. SMD compares "
        f"{groups[0]} vs {groups[1]}; multinomial SMD (Yang–Dalton) for categoricals.",
        "Admissions cluster within subjects (100,163 subjects have >1 admission); SMDs are "
        "descriptive and do NOT account for clustering.",
        f"Cells with 0<n<{SUPPRESS_N} suppressed as '<11*' (our own threshold; not a PhysioNet "
        "or HIPAA rule — no DUA cell-size rule could be verified in local files).",
    ])


LAB_AVAIL = [
    ("ALT", "lab_ALT"), ("AST", "lab_AST"), ("AST/ALT ratio", "_ratio"),
    ("Platelets", "lab_Platelets"), ("Albumin", "lab_Albumin"),
    ("Total bilirubin", "lab_Bilirubin_total"), ("Alk phosphatase", "lab_Alkaline_phosphatase"),
    ("GGT", "lab_GGT"), ("Glucose", "lab_Glucose"), ("HbA1c", "lab_HbA1c"),
    ("Triglycerides", "lab_Triglycerides"), ("HDL", "lab_HDL"),
    ("BMI", "has_BMI"), ("Systolic BP", "has_SBP"), ("Diastolic BP", "has_DBP"),
]


def _avail_series(df, key):
    if key == "_ratio":
        return df["lab_AST"].notna() & df["lab_ALT"].notna()
    if key.startswith("has_"):
        return df[key].astype(bool)
    return df[key].notna()


def _value_series(df, name):
    if name == "AST/ALT ratio":
        return df["lab_AST"] / df["lab_ALT"]
    m = {"BMI": "omr_BMI", "Systolic BP": "omr_SBP", "Diastolic BP": "omr_DBP"}
    if name in m:
        return df[m[name]]
    key = dict(LAB_AVAIL)[name]
    return df[key]


def table2(df, masks, groups):
    g0, g1 = groups[0], groups[1]
    # Panel A — availability, sorted by |SMD| desc
    panelA = []
    for name, key in LAB_AVAIL:
        av = _avail_series(df, key)
        p1 = av[masks[g0]].mean(); p0 = av[masks[g1]].mean()
        smd = smd_bin(p1, p0)
        row = {"Panel": "A: availability", "Analyte": name, "SMD": fmt_smd(smd), "_abs": abs(smd)}
        for g in groups:
            n = int(av[masks[g]].sum())
            row[g] = avail_cell(n, int(masks[g].sum()), "T2A", name, g)
        row["Overall"] = avail_cell(int(av.sum()), len(df), "T2A", name, "Overall")
        panelA.append(row)
    panelA.sort(key=lambda r: -r["_abs"])
    for r in panelA:
        del r["_abs"]
    # Panel B — values among available (conditional)
    panelB = []
    for name, key in LAB_AVAIL:
        av = _avail_series(df, key); val = _value_series(df, name).where(av)
        row = {"Panel": "B: value (among available)", "Analyte": name, "SMD": ""}
        for g in groups:
            row[g] = med_iqr(val[masks[g]])
        row["Overall"] = med_iqr(val)
        panelB.append(row)
    cols = ["Panel", "Analyte"] + groups + ["Overall", "SMD"]
    out = pd.DataFrame(panelA + panelB)[cols]
    write("table2", out, "Table 2 — Laboratory & anthropometric characteristics", [
        "Panel A (availability) is a RESULT: differential availability by coding status. "
        "Sorted by |SMD| descending. Availability indicator SMD is a proportion SMD.",
        "Labs are linked per-admission by hadm_id (a result recorded during that admission). "
        "omr (BMI, BP) has no hadm_id and is summarized at SUBJECT level (median across the "
        "subject's readings), attached to each admission — patient-level context, not per-encounter.",
        "Panel B is CONDITIONAL on availability, and availability differs between groups (Panel A), "
        "so these medians are NOT directly comparable across groups.",
        "Blood Pressure parsed from the non-atomic 'NNN/NNN' string; 907 diastolic-zero readings "
        "excluded (DQ item P2). BP parse diagnostics printed to terminal.",
        f"Cells with 0<n<{SUPPRESS_N} suppressed as '<11*' (our own threshold).",
    ])


def table3(df, masks, groups):
    g0, g1 = groups[0], groups[1]
    comp = df["lab_AST"].notna() & df["lab_Platelets"].notna() & df["lab_ALT"].notna()
    fib4 = (df["age"] * df["lab_AST"]) / (df["lab_Platelets"] * np.sqrt(df["lab_ALT"]))
    fib4 = fib4.where(comp & (df["lab_ALT"] > 0) & (df["lab_Platelets"] > 0))
    rows = []
    r = {"Characteristic": "All 4 FIB-4 components present, n (%)", "SMD":
         fmt_smd(smd_bin(comp[masks[g0]].mean(), comp[masks[g1]].mean()))}
    for g in groups:
        r[g] = n_pct(int(comp[masks[g]].sum()), int(masks[g].sum()), "T3", "computable", g)
    r["Overall"] = n_pct(int(comp.sum()), len(df), "T3", "computable", "Overall")
    rows.append(r)
    rr = {"Characteristic": "FIB-4 among computable, median [IQR]", "SMD": ""}
    for g in groups:
        rr[g] = med_iqr(fib4[masks[g]])
    rr["Overall"] = med_iqr(fib4)
    rows.append(rr)
    strata = [("FIB-4 <1.3 (low), n (%)", fib4 < 1.3),
              ("FIB-4 1.3–2.67 (indeterminate), n (%)", (fib4 >= 1.3) & (fib4 <= 2.67)),
              ("FIB-4 >2.67 (high), n (%)", fib4 > 2.67)]
    for lab, cond in strata:
        r = {"Characteristic": "  " + lab, "SMD": ""}
        denomg = {g: int((comp & masks[g]).sum()) for g in groups}
        for g in groups:
            r[g] = n_pct(int((cond & masks[g]).sum()), max(denomg[g], 1), "T3", lab, g)
        r["Overall"] = n_pct(int(cond.sum()), max(int(comp.sum()), 1), "T3", lab, "Overall")
        rows.append(r)
    cols = ["Characteristic"] + groups + ["Overall", "SMD"]
    write("table3", pd.DataFrame(rows)[cols], "Table 3 — FIB-4", [
        "FIB-4 = (age × AST) / (Platelets × √ALT). Three of four inputs (AST, platelets, ALT) are "
        "differentially missing, so computability itself differs by group (first row + SMD).",
        "FIB-4 median and strata are computed ONLY among computable admissions — a differentially "
        "selected subset — so the comparison is NOT unbiased.",
        "Strata percentages use the computable-in-group denominator.",
        "Age capped at 91 (see Table 1); AST/ALT/platelets = first result per admission (hadm_id).",
    ])


def table4():
    q = f"""
    WITH d AS (SELECT subject_id, hadm_id, seq_num, trim(icd_code) code, icd_version
               FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
    SELECT icd_version, code,
           count(*) AS n_rows,
           count(DISTINCT hadm_id) AS n_admissions,
           count(DISTINCT subject_id) AS n_subjects,
           quantile_cont(seq_num,0.5) AS med_seq,
           quantile_cont(seq_num,0.25) AS q1_seq,
           quantile_cont(seq_num,0.75) AS q3_seq,
           round(100.0*count(*) FILTER (WHERE seq_num=1)/count(*),1) AS pct_principal
    FROM d
    WHERE (icd_version=10 AND code IN ('K760','K7581'))
       OR (icd_version=9  AND code IN ('5718','5719'))
    GROUP BY icd_version, code ORDER BY icd_version DESC, code
    """
    t = con.execute(q).fetchdf()
    titles = {("K760", 10): "Fatty liver, NEC", ("K7581", 10): "NASH",
              ("5718", 9): "Other chronic nonalcoholic liver dz",
              ("5719", 9): "Unspecified chronic liver dz w/o alcohol"}
    rows = []
    for _, r in t.iterrows():
        rows.append({
            "ICD version": int(r.icd_version), "Code": r.code,
            "Description": titles.get((r.code, int(r.icd_version)), ""),
            "n admissions": f"{int(r.n_admissions):,}",
            "n subjects": f"{int(r.n_subjects):,}",
            "seq_num median [IQR]": f"{r.med_seq:.0f} [{r.q1_seq:.0f}, {r.q3_seq:.0f}]",
            "% principal (seq=1)": f"{r.pct_principal}",
        })
    write("table4", pd.DataFrame(rows), "Table 4 — Coded cohort composition (by code & version)", [
        "Principal diagnosis = seq_num 1. Counts are diagnosis rows within the analysis grain; "
        "an admission may appear under >1 code.",
    ])


def tableS1(df, bpstat):
    N = len(df)
    tot_bp, ok_bp, dbp0 = bpstat
    rows = [
        ("Conformance · value", "Lab value non-numeric (valuenum null)", "~5", "≈0% (labevents)",
         "Treat as missing (already null)", "No"),
        ("Conformance · value (units)", "Multiple units per analyte", "0", "0%",
         "None needed", "n/a"),
        ("Conformance · relational", "labevents hadm_id null (outpatient)", "73,768,897",
         "46.6% (labevents)", "Keep; link by subject+window for outpatient labs", "No"),
        ("Conformance · value", "omr Blood Pressure non-atomic", f"{tot_bp:,}",
         "100% of BP rows", "Parse NNN/NNN into sbp/dbp", "Yes (this pass)"),
        ("Plausibility · atemporal", "Lab impossible values (glucose ≤0)", "3", "≈0%",
         "Null impossible; flag extremes", "No"),
        ("Plausibility · atemporal", "omr impossible (incl. 907 diastolic zeros)", "1,151",
         "row-level", "Null impossible; diastolic zeros excluded", "Partial (dbp zeros: Yes)"),
        ("Plausibility · temporal", "admittime > dischtime (neg LOS)", "175",
         f"{100*175/N:.3f}% (adm)", "Null/flag LOS", "No"),
        ("Plausibility · temporal", "deathtime outside stay", "771", f"{100*771/N:.3f}% (adm)",
         "Accept midnight artifact; flag", "No"),
        ("Plausibility · temporal", "dischtime after dod", "32", f"{100*32/N:.4f}% (adm)",
         "Flag; dod unreliable for these", "No"),
        ("Plausibility · temporal", "lab charttime outside admit window", "3,421,479",
         "4.04% (linked labs)", "Define window tolerance per feature", "No"),
        ("Plausibility · temporal", "omr chartdate after dod", "91", "row-level",
         "Null/flag", "No"),
        ("Completeness · differential", "MNAR metabolic covariates (BMI/ALT/HbA1c/TG/HDL/dischg)",
         "6 covariates", "structural", "Missing-indicators; missingness-tolerant criterion; "
         "1c sensitivity analysis", "No"),
        ("Conformance · value", "Age cap at 91 (≥89 collapsed)", "n/a", "upper tail",
         "Cap age at 91; footnote", "Yes (this pass)"),
    ]
    cols = ["Kahn category", "Test", "n affected", "% of population", "Proposed rule", "Applied"]
    out = pd.DataFrame(rows, columns=cols)
    write("tableS1", out, "Supplementary Table S1 — Data quality summary (Kahn 2016)", [
        "Rules per docs/cleaning_spec.md. 'Applied' refers to THIS descriptive pass only; the "
        "cleaning spec is otherwise not executed. Denominators noted inline.",
        f"BP parse success this pass: {ok_bp:,}/{tot_bp:,} ({100*ok_bp/tot_bp:.1f}%); "
        f"diastolic zeros excluded: {dbp0:,}.",
    ])


def main():
    df, bpstat = build_frame()
    g_series, groups = GROUPINGS[GROUP_SPEC](df)
    masks = {g: (g_series == g).values for g in groups}
    print(f"GROUP_SPEC = {GROUP_SPEC}  groups = {groups}  N = {len(df):,}")
    print(f"BP parse: {bpstat[1]:,}/{bpstat[0]:,} ok; diastolic zeros excluded: {bpstat[2]:,}")
    if not (POP_PARQUET or os.environ.get("FRAME_PARQUET")):
        table0(df)      # skip when restricted/framed; table0 maintained separately
    table1(df, masks, groups)
    table2(df, masks, groups)
    table3(df, masks, groups)
    table4()
    tableS1(df, bpstat)

    print("\n" + "=" * 78 + "\nSUPPRESSED CELLS (0<n<11)\n" + "=" * 78)
    if SUPPRESSED:
        for t, row, grp in SUPPRESSED:
            print(f"  [{t}] {row}  ({grp})")
    else:
        print("  none")


if __name__ == "__main__":
    main()

