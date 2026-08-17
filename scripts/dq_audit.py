#!/usr/bin/env python3
"""STEP 1 — Data quality audit of the structured MIMIC-IV hosp tables.

Read-only: queries the gzipped CSVs in place, writes nothing, decides nothing.
For admissions, patients, diagnoses_icd, omr it reports:
  * per-column missingness: NULL, literal empty-string (''), whitespace-only
    (these three are distinct; empties/whitespace evade an IS NULL filter)
  * verbatim value-frequency tables for the requested categorical columns
  * numeric summaries (min/max/mean/median/p1/p99, negatives, implausible)
  * duplicate-row and duplicate-key checks

Run from project root with ./.venv active:
    python scripts/dq_audit.py
"""
import duckdb

DATA = "data/raw/hosp"

# icd_code forced to VARCHAR so it is never sniffed as numeric.
SRC = {
    "patients":      f"read_csv_auto('{DATA}/patients.csv.gz')",
    "admissions":    f"read_csv_auto('{DATA}/admissions.csv.gz')",
    "diagnoses_icd": (f"read_csv_auto('{DATA}/diagnoses_icd.csv.gz', "
                      "types={'icd_code':'VARCHAR'})"),
    "omr":           f"read_csv_auto('{DATA}/omr.csv.gz')",
}

CATEGORICAL = {
    "admissions": ["admission_type", "admission_location", "discharge_location",
                   "insurance", "language", "marital_status", "race"],
    "patients":   ["gender", "anchor_year_group"],
}

NUMERIC = {
    "patients":      ["anchor_age", "anchor_year"],
    "diagnoses_icd": ["seq_num"],
    "admissions":    ["hospital_expire_flag"],
}

con = duckdb.connect()
con.execute("SET memory_limit='24GB';")


def columns(table):
    rows = con.execute(f"DESCRIBE SELECT * FROM {SRC[table]}").fetchall()
    return [(r[0], r[1]) for r in rows]  # (name, type)


def missingness(table):
    cols = columns(table)
    parts = ["count(*) AS n"]
    for name, typ in cols:
        parts.append(f"sum((\"{name}\" IS NULL)::INT) AS null__{name}")
        if typ == "VARCHAR":
            parts.append(f"sum((\"{name}\" = '')::INT) AS empty__{name}")
            parts.append(
                f"sum(("
                f"\"{name}\" IS NOT NULL AND \"{name}\" <> '' "
                f"AND trim(\"{name}\") = '')::INT) AS ws__{name}"
            )
    q = f"SELECT {', '.join(parts)} FROM {SRC[table]}"
    row = con.execute(q).fetchdf().iloc[0].to_dict()
    n = int(row["n"])
    print(f"\n### {table}  (n = {n:,} rows)")
    print(f"{'column':22s} {'type':10s} {'null':>10s} {'null%':>7s} "
          f"{'empty':>8s} {'wspace':>8s}")
    for name, typ in cols:
        nulls = int(row[f"null__{name}"])
        empt = int(row.get(f"empty__{name}", 0) or 0)
        wsp = int(row.get(f"ws__{name}", 0) or 0)
        emp_s = f"{empt:,}" if typ == "VARCHAR" else "-"
        ws_s = f"{wsp:,}" if typ == "VARCHAR" else "-"
        print(f"{name:22s} {typ:10s} {nulls:>10,} {100*nulls/n:>6.2f}% "
              f"{emp_s:>8s} {ws_s:>8s}")


def categoricals(table):
    for col in CATEGORICAL.get(table, []):
        print(f"\n### {table}.{col}  — verbatim value counts (brackets reveal spacing)")
        df = con.execute(
            f"SELECT '[' || coalesce(\"{col}\", '<NULL>') || ']' AS value, "
            f"count(*) AS n, round(100.0*count(*)/sum(count(*)) OVER (), 2) AS pct "
            f"FROM {SRC[table]} GROUP BY 1 ORDER BY n DESC"
        ).fetchdf()
        with_opt = df.to_string(index=False)
        print(with_opt)


def numerics(table):
    cols = NUMERIC.get(table, [])
    if not cols:
        return
    print(f"\n### {table} — numeric summaries")
    for col in cols:
        r = con.execute(
            f"""SELECT
                  min("{col}") AS min, max("{col}") AS max,
                  round(avg("{col}"),2) AS mean,
                  quantile_cont("{col}",0.5) AS median,
                  quantile_cont("{col}",0.01) AS p1,
                  quantile_cont("{col}",0.99) AS p99,
                  sum(("{col}" < 0)::INT) AS n_negative,
                  sum(("{col}" IS NULL)::INT) AS n_null
                FROM {SRC[table]}"""
        ).fetchone()
        print(f"  {col:20s} min={r[0]} max={r[1]} mean={r[2]} median={r[3]} "
              f"p1={r[4]} p99={r[5]} negatives={r[6]:,} nulls={r[7]:,}")


def duplicates():
    print("\n### duplicate checks")
    for table in ["patients", "admissions", "diagnoses_icd", "omr"]:
        total, distinct = con.execute(
            f"SELECT (SELECT count(*) FROM {SRC[table]}), "
            f"(SELECT count(*) FROM (SELECT DISTINCT * FROM {SRC[table]}))"
        ).fetchone()
        print(f"  {table:16s} excess full-duplicate rows: {total - distinct:,} "
              f"(of {total:,})")

    dup_adm = con.execute(
        f"SELECT count(*) FROM (SELECT subject_id, hadm_id, count(*) c "
        f"FROM {SRC['admissions']} GROUP BY 1,2 HAVING c > 1)"
    ).fetchone()[0]
    print(f"  admissions      duplicate (subject_id, hadm_id) groups: {dup_adm:,}")

    dup_dx = con.execute(
        f"SELECT count(*) FROM (SELECT subject_id, hadm_id, seq_num, count(*) c "
        f"FROM {SRC['diagnoses_icd']} GROUP BY 1,2,3 HAVING c > 1)"
    ).fetchone()[0]
    print(f"  diagnoses_icd   duplicate (subject_id, hadm_id, seq_num) groups: {dup_dx:,}")


def main():
    print("=" * 70)
    print("STEP 1 — DATA QUALITY AUDIT")
    print("=" * 70)
    for table in ["admissions", "patients", "diagnoses_icd", "omr"]:
        missingness(table)
    for table in ["admissions", "patients"]:
        categoricals(table)
    for table in ["patients", "diagnoses_icd", "admissions"]:
        numerics(table)
    duplicates()


if __name__ == "__main__":
    main()
