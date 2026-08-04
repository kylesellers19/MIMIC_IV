#!/usr/bin/env python3
"""Materialize a MASLD-candidate cohort from MIMIC-IV gzipped CSVs to Parquet.

Pattern: scan the big compressed tables once to find cohort subject_ids, then
write filtered slices to data/processed/ for fast downstream joins. Nothing large
is held in memory — DuckDB streams the gzip and only keeps cohort rows.

Usage (from project root, with .venv active):
    python scripts/materialize_cohort.py

Adjust RAW paths and the ICD phenotype to match your data and study definition.
This is a runnable template, not a validated MASLD phenotype.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "mimiciv" / "hosp"
OUT = ROOT / "data" / "processed"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()  # in-memory engine; sources/sinks are files
    con.execute("SET memory_limit = '24GB';")

    diagnoses = (RAW / "diagnoses_icd.csv.gz").as_posix()
    labevents = (RAW / "labevents.csv.gz").as_posix()
    cohort_ids = (OUT / "cohort_ids.parquet").as_posix()
    cohort_labs = (OUT / "cohort_labevents.parquet").as_posix()

    # 1. Cohort subject_ids (refine the phenotype for your study).
    con.execute(
        f"""
        COPY (
          SELECT DISTINCT subject_id
          FROM read_csv('{diagnoses}',
                        types = {{'icd_code': 'VARCHAR', 'icd_version': 'INTEGER',
                                  'subject_id': 'BIGINT', 'hadm_id': 'BIGINT'}})
          WHERE (icd_version = 10 AND (icd_code LIKE 'K760%' OR icd_code LIKE 'K7581%'))
             OR (icd_version = 9  AND icd_code IN ('5715', '5718', '5719'))
        ) TO '{cohort_ids}' (FORMAT parquet);
        """
    )

    # 2. Filtered slice of a big table: labs for cohort subjects only.
    con.execute(
        f"""
        COPY (
          SELECT l.*
          FROM read_csv_auto('{labevents}') l
          SEMI JOIN read_parquet('{cohort_ids}') c ON l.subject_id = c.subject_id
        ) TO '{cohort_labs}' (FORMAT parquet);
        """
    )

    n_subj = con.execute(
        f"SELECT count(*) FROM read_parquet('{cohort_ids}')"
    ).fetchone()[0]
    n_labs = con.execute(
        f"SELECT count(*) FROM read_parquet('{cohort_labs}')"
    ).fetchone()[0]
    print(f"cohort subjects: {n_subj:,}")
    print(f"cohort lab rows: {n_labs:,}")
    print(f"written to: {OUT}")


if __name__ == "__main__":
    main()
