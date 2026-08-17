-- analysis_population.sql
-- Canonical analysis population encoding the locked decisions:
--   * grain = admission (hadm_id)
--   * zero-diagnosis admissions EXCLUDED (inner join to diagnoses)
--   * diagnosis count = distinct (seq_num, icd_version)
--   * age = anchor_age + year(admittime) - anchor_year  (91 cap noted)
--   * code-positive = version-aware pre-specified MASLD code set
-- Read-only. Run: duckdb < sql/analysis_population.sql
-- Result: 545,497 admissions (9,143 code-positive / 536,354 code-negative).

CREATE OR REPLACE TEMP VIEW analysis_admissions AS
WITH dx AS (
  SELECT hadm_id,
         count(DISTINCT (seq_num, icd_version)) AS n_diagnoses,
         max(CASE WHEN
              (icd_version=10 AND trim(icd_code) IN ('K760','K7581'))
           OR (icd_version=9  AND trim(icd_code) IN ('5718','5719'))
             THEN 1 ELSE 0 END) AS masld
  FROM read_csv('data/raw/hosp/diagnoses_icd.csv.gz', types={'icd_code':'VARCHAR'})
  GROUP BY hadm_id
)
SELECT a.hadm_id, a.subject_id,
       dx.masld::BOOLEAN AS code_positive,
       dx.n_diagnoses,
       p.anchor_age + year(a.admittime) - p.anchor_year AS age_at_admit,
       p.gender, a.race, a.insurance, a.language, a.marital_status,
       a.admission_type, a.admission_location, a.discharge_location,
       a.hospital_expire_flag,
       a.admittime, a.dischtime, a.deathtime, a.edregtime, a.edouttime,
       p.dod, p.anchor_year_group,
       date_diff('second', a.admittime, a.dischtime)/86400.0 AS los_days
FROM read_csv_auto('data/raw/hosp/admissions.csv.gz') a
JOIN dx USING (hadm_id)
JOIN read_csv_auto('data/raw/hosp/patients.csv.gz') p USING (subject_id);

SELECT count(*) AS analysis_admissions,
       sum(code_positive::INT) AS code_positive,
       count(*) - sum(code_positive::INT) AS code_negative
FROM analysis_admissions;
