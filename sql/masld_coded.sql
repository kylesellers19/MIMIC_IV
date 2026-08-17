-- masld_coded.sql
-- Coded-positive MASLD cohort from MIMIC-IV v3.1 hosp/diagnoses_icd.
-- Read-only: queries the gzipped CSVs in place, writes nothing.
--
-- Run from project root:
--   duckdb < sql/masld_coded.sql
--
-- PRE-SPECIFIED code set (do not expand here — a change is a protocol decision):
--   ICD-10:  K760  (K76.0  Fatty change of liver, NEC)
--            K7581 (K75.81 NASH)
--   ICD-9:   5718  (571.8  Other chronic nonalcoholic liver disease)
--            5719  (571.9  Unspecified chronic liver disease w/o mention of alcohol)
--
-- Correctness guards:
--   * trim(icd_code) — MIMIC pads codes with trailing spaces to a fixed width.
--   * version-aware — match on (icd_version, code) jointly; ICD-9 and ICD-10
--     code spaces overlap, so a code-only match yields false positives.

-- Normalized diagnosis rows (trailing spaces stripped, types forced).
CREATE OR REPLACE TEMP VIEW dx AS
  SELECT subject_id, hadm_id, seq_num,
         trim(icd_code) AS code, icd_version
  FROM read_csv('data/raw/hosp/diagnoses_icd.csv.gz',
       types = {'subject_id':'BIGINT','hadm_id':'BIGINT','seq_num':'INTEGER',
                'icd_code':'VARCHAR','icd_version':'INTEGER'});

-- Pre-specified target set (version, dotless code, human label).
CREATE OR REPLACE TEMP VIEW targets AS
  SELECT * FROM (VALUES
    (10, 'K760',  'ICD-10 K76.0  Fatty (change of) liver, NEC'),
    (10, 'K7581', 'ICD-10 K75.81 NASH'),
    (9,  '5718',  'ICD-9  571.8  Other chronic nonalcoholic liver disease'),
    (9,  '5719',  'ICD-9  571.9  Unspecified chronic liver disease w/o alcohol')
  ) AS t(icd_version, code, label);

-- Matched coded-positive diagnosis rows.
CREATE OR REPLACE TEMP VIEW matched AS
  SELECT d.subject_id, d.hadm_id, d.seq_num, d.code, d.icd_version, t.label
  FROM dx d
  JOIN targets t
    ON t.icd_version = d.icd_version
   AND t.code        = d.code;

-- Dictionary, normalized the same way, for the long_title eyeball check.
CREATE OR REPLACE TEMP VIEW dict AS
  SELECT trim(icd_code) AS code, icd_version, long_title
  FROM read_csv('data/raw/hosp/d_icd_diagnoses.csv.gz',
       types = {'icd_code':'VARCHAR','icd_version':'INTEGER','long_title':'VARCHAR'});

-- =====================================================================
-- (A) Eyeball: does each target code mean what we think? (dictionary title)
-- =====================================================================
SELECT '--- (A) target codes vs dictionary long_title ---' AS section;
SELECT t.icd_version, t.code, t.label, d.long_title
FROM targets t
LEFT JOIN dict d
  ON d.icd_version = t.icd_version AND d.code = t.code
ORDER BY t.icd_version DESC, t.code;

-- =====================================================================
-- (B) Overall coded-positive N, at both grains
-- =====================================================================
SELECT '--- (B) overall coded-positive counts ---' AS section;
SELECT count(*)                    AS matched_rows,
       count(DISTINCT subject_id)  AS distinct_subjects,
       count(DISTINCT hadm_id)     AS distinct_hadm
FROM matched;

-- =====================================================================
-- (C) Split by icd_version, at both grains
-- =====================================================================
SELECT '--- (C) coded-positive by icd_version ---' AS section;
SELECT icd_version,
       count(*)                   AS matched_rows,
       count(DISTINCT subject_id) AS distinct_subjects,
       count(DISTINCT hadm_id)    AS distinct_hadm
FROM matched
GROUP BY icd_version
ORDER BY icd_version;

-- =====================================================================
-- (D) By individual code, at both grains (with label)
-- =====================================================================
SELECT '--- (D) coded-positive by individual code ---' AS section;
SELECT icd_version, code, label,
       count(*)                   AS matched_rows,
       count(DISTINCT subject_id) AS distinct_subjects,
       count(DISTINCT hadm_id)    AS distinct_hadm
FROM matched
GROUP BY icd_version, code, label
ORDER BY icd_version DESC, code;

-- =====================================================================
-- (E) seq_num distribution — principal (seq_num=1) vs trailing
-- =====================================================================
SELECT '--- (E1) seq_num histogram for matched rows ---' AS section;
SELECT seq_num, count(*) AS matched_rows
FROM matched
GROUP BY seq_num
ORDER BY seq_num;

SELECT '--- (E2) principal vs trailing summary ---' AS section;
SELECT
  count(*)                                              AS matched_rows,
  count(*) FILTER (WHERE seq_num = 1)                   AS principal_rows,
  count(*) FILTER (WHERE seq_num > 1)                   AS trailing_rows,
  round(100.0 * count(*) FILTER (WHERE seq_num = 1)
        / count(*), 1)                                  AS pct_principal,
  min(seq_num)                                          AS min_seq,
  max(seq_num)                                          AS max_seq
FROM matched;
