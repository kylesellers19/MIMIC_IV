-- dq_referential_integrity.sql   (STEP 2)
-- Read-only. Counts keys that fail to join across tables, to quantify how many
-- cases an inner join would silently drop (which could bias the 2x2).
--
-- Run: duckdb < sql/dq_referential_integrity.sql

CREATE OR REPLACE TEMP VIEW adm AS
  SELECT subject_id, hadm_id
  FROM read_csv_auto('data/raw/hosp/admissions.csv.gz');
CREATE OR REPLACE TEMP VIEW dx AS
  SELECT subject_id, hadm_id
  FROM read_csv_auto('data/raw/hosp/diagnoses_icd.csv.gz');
CREATE OR REPLACE TEMP VIEW pat AS
  SELECT subject_id
  FROM read_csv_auto('data/raw/hosp/patients.csv.gz');

SELECT '--- (1) hadm_id in diagnoses_icd NOT in admissions ---' AS check;
SELECT count(*) AS dx_rows_orphaned,
       count(DISTINCT hadm_id) AS distinct_hadm_orphaned
FROM dx WHERE hadm_id NOT IN (SELECT hadm_id FROM adm);

SELECT '--- (2) hadm_id null in diagnoses_icd ---' AS check;
SELECT count(*) AS dx_rows_null_hadm FROM dx WHERE hadm_id IS NULL;

SELECT '--- (3) admissions with ZERO diagnosis rows (hadm in adm NOT in dx) ---' AS check;
SELECT count(*) AS admissions_without_dx
FROM adm WHERE hadm_id NOT IN (SELECT hadm_id FROM dx WHERE hadm_id IS NOT NULL);

SELECT '--- (4) subject_id in admissions NOT in patients ---' AS check;
SELECT count(DISTINCT subject_id) AS adm_subjects_missing_from_patients
FROM adm WHERE subject_id NOT IN (SELECT subject_id FROM pat);

SELECT '--- (5) subject_id in patients NOT in admissions (no hosp admission) ---' AS check;
SELECT count(DISTINCT subject_id) AS patients_without_admission
FROM pat WHERE subject_id NOT IN (SELECT subject_id FROM adm);

SELECT '--- (6) totals for context ---' AS check;
SELECT (SELECT count(DISTINCT hadm_id) FROM adm) AS adm_hadm,
       (SELECT count(DISTINCT hadm_id) FROM dx)  AS dx_hadm,
       (SELECT count(DISTINCT subject_id) FROM pat) AS n_patients,
       (SELECT count(DISTINCT subject_id) FROM adm) AS adm_subjects;
