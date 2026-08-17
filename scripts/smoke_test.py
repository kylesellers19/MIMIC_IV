#!/usr/bin/env python3
"""DuckDB feasibility smoke test for the MIMIC-IV hosp module.

Queries the 7 gzipped hosp CSVs *in place* via read_csv_auto — nothing is ever
decompressed to disk. For each table it reports the column schema (cheap sample
via DESCRIBE), the exact row count (a full streaming scan of the gzip), and the
wall-clock time. Plus: diagnoses_icd distinct subject/hadm + icd_version split,
and the admissions admittime span. Peak process memory is reported at the end.

The point: confirm labevents.csv.gz (~2.4 GB compressed) is scannable in bounded
memory on this machine before designing a pipeline around it. COUNT(*) streams,
so a flat peak-memory number here means "scannable" — heavier ops (joins,
group-bys that build hash tables) will use more.

Run from project root with ./.venv active:
    python scripts/smoke_test.py
"""
import os
import resource
import time

import duckdb

# Read-only source dir; override with DATA_DIR if the layout ever moves.
DATA_DIR = os.environ.get("DATA_DIR", "data/raw/hosp")

TABLES = [
    "patients",
    "admissions",
    "d_icd_diagnoses",
    "d_labitems",
    "diagnoses_icd",
    "omr",
    "labevents",  # ~2.4 GB compressed — the feasibility target, scanned last
]


def path(table: str) -> str:
    return f"{DATA_DIR}/{table}.csv.gz"


def peak_rss_gb() -> float:
    # macOS: ru_maxrss is in bytes. (Linux would be kilobytes.)
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3


def main() -> None:
    con = duckdb.connect()
    con.execute("SET memory_limit = '24GB';")  # guardrail on a 32 GB box

    print(f"DATA_DIR = {DATA_DIR}\n")
    grand_t0 = time.perf_counter()

    for table in TABLES:
        p = path(table)
        t0 = time.perf_counter()

        # Schema first — DESCRIBE only sniffs a sample, so this is fast even for labevents.
        schema = con.execute(
            f"DESCRIBE SELECT * FROM read_csv_auto('{p}')"
        ).fetchall()  # rows of (column_name, column_type, null, key, default, extra)

        # Exact row count — this is the full streaming scan of the gzip.
        n_rows = con.execute(
            f"SELECT count(*) FROM read_csv_auto('{p}')"
        ).fetchone()[0]

        elapsed = time.perf_counter() - t0
        cols = ", ".join(f"{c[0]}:{c[1]}" for c in schema)
        print(f"=== {table} ===")
        print(f"  rows      : {n_rows:,}")
        print(f"  columns   : {len(schema)}")
        print(f"  schema    : {cols}")
        print(f"  scan time : {elapsed:,.2f} s")
        print(f"  peak RSS  : {peak_rss_gb():.3f} GB")
        print()

    # --- diagnoses_icd specifics ---------------------------------------------
    dx = path("diagnoses_icd")
    print("=== diagnoses_icd: grain & version breakdown ===")
    con.sql(
        f"""
        SELECT count(DISTINCT subject_id) AS distinct_subjects,
               count(DISTINCT hadm_id)    AS distinct_hadm
        FROM read_csv_auto('{dx}',
             types={{'subject_id':'BIGINT','hadm_id':'BIGINT'}})
        """
    ).show()
    con.sql(
        f"""
        SELECT icd_version, count(*) AS n_rows
        FROM read_csv_auto('{dx}', types={{'icd_version':'INTEGER'}})
        GROUP BY icd_version ORDER BY icd_version
        """
    ).show()

    # --- admissions date span ------------------------------------------------
    adm = path("admissions")
    print("=== admissions: admittime span ===")
    con.sql(
        f"""
        SELECT min(admittime) AS min_admittime,
               max(admittime) AS max_admittime
        FROM read_csv_auto('{adm}')
        """
    ).show()

    total = time.perf_counter() - grand_t0
    print(f"total wall-clock : {total:,.2f} s")
    print(f"final peak RSS   : {peak_rss_gb():.3f} GB")


if __name__ == "__main__":
    main()
