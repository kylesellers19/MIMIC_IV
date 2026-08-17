-- dq_race.sql   (STEP 3)
-- Read-only, no category collapsing. Race/ethnicity as recorded, to see what
-- collapsing would cost before deciding how (Aim 1c).
--
-- Run: duckdb < sql/dq_race.sql

CREATE OR REPLACE TEMP VIEW adm AS
  SELECT subject_id, hadm_id, race, admission_type, insurance
  FROM read_csv_auto('data/raw/hosp/admissions.csv.gz');

-- (1) Full verbatim value counts for race
SELECT '--- (1) race verbatim value counts ---' AS section;
SELECT race, count(*) AS n_admissions,
       round(100.0*count(*)/sum(count(*)) OVER (), 2) AS pct
FROM adm GROUP BY race ORDER BY n_admissions DESC;

-- (2) Subjects with INCONSISTENT race across their own admissions
SELECT '--- (2a) count of subjects with >1 distinct race value ---' AS section;
SELECT count(*) AS subjects_inconsistent_race
FROM (SELECT subject_id FROM adm GROUP BY subject_id
      HAVING count(DISTINCT race) > 1);

SELECT '--- (2b) sample of 20 such subjects (most divergent first) ---' AS section;
SELECT subject_id,
       count(DISTINCT race) AS n_distinct_race,
       count(*)             AS n_admissions,
       list(DISTINCT race)  AS race_values
FROM adm
GROUP BY subject_id
HAVING count(DISTINCT race) > 1
ORDER BY n_distinct_race DESC, subject_id
LIMIT 20;

-- (3) Cross-tabs (long form here; pivoted for display in scripts/dq_race.py)
SELECT '--- (3a) race x admission_type (long form) ---' AS section;
SELECT race, admission_type, count(*) AS n
FROM adm GROUP BY race, admission_type ORDER BY race, admission_type;

SELECT '--- (3b) race x insurance (long form) ---' AS section;
SELECT race, insurance, count(*) AS n
FROM adm GROUP BY race, insurance ORDER BY race, insurance;
