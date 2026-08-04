#!/usr/bin/env python3
"""Aim 1a seed / data sanity check for MASLD phenotyping on MIMIC-IV.

Queries the gzipped hosp CSVs directly with DuckDB (in-memory, no import) and:
  (4) counts diagnoses_icd rows and lists distinct icd_version values;
  (5) counts patients carrying each MASLD-relevant ICD code.

Everything is parameterized on DATA_DIR — point it at the demo now, swap in the
credentialed `.../hosp` directory later. File format (.csv.gz) is identical, so
no other change is needed.

Run from project root with the venv active:
    python scripts/sanity_check_icd.py
"""
import os

import duckdb

# --- swap this one line when the credentialed data arrives --------------------
DATA_DIR = os.environ.get(
    "DATA_DIR",
    "test files/mimic-iv-clinical-database-demo-2.2/hosp",
)
# -----------------------------------------------------------------------------

# MIMIC stores ICD codes WITHOUT dots: K76.0->K760, K75.81->K7581,
# 571.8->5718, 571.9->5719. icd_version (9 vs 10) disambiguates the code space.
MASLD_CODES = """
  VALUES (10, 'K760',  'ICD-10 K76.0  Fatty liver, NEC'),
         (10, 'K7581', 'ICD-10 K75.81 NASH'),
         (9,  '5718',  'ICD-9  571.8  Other chronic nonalcoholic liver dz'),
         (9,  '5719',  'ICD-9  571.9  Unspecified chronic liver dz')
"""


def main() -> None:
    con = duckdb.connect()  # in-memory; files are queried in place

    def view(name: str) -> None:
        con.execute(
            f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv_auto("
            f"'{DATA_DIR}/{name}.csv.gz', "
            "types={'icd_code':'VARCHAR','icd_version':'INTEGER'})"
        )

    view("diagnoses_icd")
    view("d_icd_diagnoses")

    print(f"DATA_DIR = {DATA_DIR}\n")

    print("=== (4) diagnoses_icd: row count, patient count, versions ===")
    con.sql(
        "SELECT count(*) AS n_rows, count(DISTINCT subject_id) AS n_patients "
        "FROM diagnoses_icd"
    ).show()
    con.sql(
        "SELECT icd_version, count(*) AS n_rows "
        "FROM diagnoses_icd GROUP BY icd_version ORDER BY icd_version"
    ).show()

    print("=== (5) MASLD-relevant codes: patients carrying each (Aim 1a seed) ===")
    # n_patients uses COUNT(DISTINCT subject_id) so a code present in the
    # dictionary but carried by no patient reports 0 (n_rows may show the
    # single LEFT JOIN row — expected, not a data row).
    con.sql(
        f"""
        WITH masld(icd_version, icd_code, label) AS ({MASLD_CODES})
        SELECT m.label, m.icd_version, m.icd_code, d.long_title,
               count(DISTINCT dx.subject_id) AS n_patients
        FROM masld m
        LEFT JOIN diagnoses_icd dx
               ON dx.icd_code = m.icd_code AND dx.icd_version = m.icd_version
        LEFT JOIN d_icd_diagnoses d
               ON d.icd_code = m.icd_code AND d.icd_version = m.icd_version
        GROUP BY 1, 2, 3, 4
        ORDER BY m.icd_version DESC, m.icd_code
        """
    ).show(max_width=200)


if __name__ == "__main__":
    main()
