#!/usr/bin/env python3
"""PySpark pipeline, Step 1 cross-check: row counts of the 12 raw files as DuckDB reads them, beside Spark's.

DuckDB is the reader of the version-of-record pipeline; read_csv_auto is called exactly as scripts/masld_config.py
and scripts/note_schema.py call it. Spark's counts come from data/spark/ingest/<table>/_source.json, written by
`make spark-ingest`. Where the two readers agree, the count can go into ingest.expected_rows in
conf/spark_local.yaml as an independent check on the Spark parse.

Counts only: no row, value or note text is selected or printed. DuckDB error messages can quote the line that failed,
so on an error only the exception class is printed.

Run with the September environment, which has DuckDB:
    scripts/run0919_env.sh scripts/spark_duckdb_counts.py
Exit: 0 all 12 agree · 1 otherwise
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
INGEST = ROOT / "data/spark/ingest"
# table -> module folder. Must equal masld_spark.schemas.TABLES (tests/spark/test_duckdb_counts.py checks it).
FILES = {
    "admissions": "hosp", "patients": "hosp", "diagnoses_icd": "hosp", "d_icd_diagnoses": "hosp",
    "labevents": "hosp", "d_labitems": "hosp", "omr": "hosp", "prescriptions": "hosp",
    "discharge": "note", "discharge_detail": "note", "radiology": "note", "radiology_detail": "note",
}


def spark_rows(table):
    try:
        return json.loads((INGEST / table / "_source.json").read_text())["rows"]
    except (OSError, ValueError, KeyError):
        return None


def fmt(v):
    if v is None:
        return "—"
    return "<11" if 0 < v < 11 else f"{v:,}"


def main():
    import duckdb
    con = duckdb.connect()
    con.execute("SET memory_limit='16GB'")
    print(f"{'table':<18}{'duckdb':>14}{'spark':>14}  agree  seconds", flush=True)
    agreed = {}
    for table, module in FILES.items():
        path = RAW / module / f"{table}.csv.gz"
        t0 = time.time()
        try:
            d = con.execute(f"SELECT count(*) FROM read_csv_auto('{path}')").fetchone()[0]
            note = ""
        except Exception as e:   # noqa: BLE001 — class only; the message can quote a line
            d, note = None, f"  DuckDB error ({type(e).__name__})"
        s = spark_rows(table)
        ok = d is not None and d == s
        if ok:
            agreed[table] = d
        print(f"{table:<18}{fmt(d):>14}{fmt(s):>14}  {'yes' if ok else 'NO':<5}  {time.time() - t0:7.1f}{note}", flush=True)
    print(f"\n{len(agreed)} of {len(FILES)} tables agree.")
    if len(agreed) == len(FILES):
        print("All agree. ingest.expected_rows for conf/spark_local.yaml:")
        print("  expected_rows:")
        for table, rows in agreed.items():
            print(f"    {table}: {rows}")
    return 0 if len(agreed) == len(FILES) else 1


if __name__ == "__main__":
    sys.exit(main())
