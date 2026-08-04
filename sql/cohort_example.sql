-- cohort_example.sql
-- Template: extract a MASLD-candidate cohort from MIMIC-IV gzipped CSVs and
-- materialize filtered slices to Parquet under data/processed/.
--
-- Run with the CLI from the project root:
--   duckdb < sql/cohort_example.sql
--
-- NOTE: ICD codes below are a starting point, NOT a validated MASLD phenotype.
-- Refine the code lists / add lab + metabolic criteria for your study.

-- Paths are relative to the project root.
SET memory_limit = '24GB';

-- Convenience views over the compressed source tables (no data copied).
CREATE OR REPLACE VIEW diagnoses_icd AS
  SELECT * FROM read_csv(
    'data/raw/mimiciv/hosp/diagnoses_icd.csv.gz',
    types = {'icd_code': 'VARCHAR', 'icd_version': 'INTEGER',
             'subject_id': 'BIGINT', 'hadm_id': 'BIGINT'}
  );

CREATE OR REPLACE VIEW patients AS
  SELECT * FROM read_csv_auto('data/raw/mimiciv/hosp/patients.csv.gz');

-- 1. Cohort: subjects with a fatty-liver / steatohepatitis diagnosis code.
--    K70-K77 covers liver disease; K75.81 (NASH) and K76.0 (fatty liver) are
--    most relevant. ICD-9 571.5 / 571.8 are legacy equivalents.
COPY (
  SELECT DISTINCT subject_id
  FROM diagnoses_icd
  WHERE (icd_version = 10 AND (icd_code LIKE 'K760%' OR icd_code LIKE 'K7581%'))
     OR (icd_version = 9  AND icd_code IN ('5715', '5718', '5719'))
) TO 'data/processed/cohort_ids.parquet' (FORMAT parquet);

-- 2. Cohort demographics (small table — fine to keep whole, filtered to cohort).
COPY (
  SELECT p.*
  FROM patients p
  SEMI JOIN read_parquet('data/processed/cohort_ids.parquet') c
    ON p.subject_id = c.subject_id
) TO 'data/processed/cohort_patients.parquet' (FORMAT parquet);

-- 3. Big-table slice: labs for cohort subjects only (never materializes full table).
COPY (
  SELECT l.*
  FROM read_csv_auto('data/raw/mimiciv/hosp/labevents.csv.gz') l
  SEMI JOIN read_parquet('data/processed/cohort_ids.parquet') c
    ON l.subject_id = c.subject_id
) TO 'data/processed/cohort_labevents.parquet' (FORMAT parquet);

-- Quick sanity check.
SELECT
  (SELECT count(*) FROM read_parquet('data/processed/cohort_ids.parquet'))       AS n_subjects,
  (SELECT count(*) FROM read_parquet('data/processed/cohort_labevents.parquet')) AS n_lab_rows;
