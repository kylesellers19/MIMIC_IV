#!/usr/bin/env python3
"""Shared configuration encoding the researcher's locked decisions.

These are fixed for the project; scripts import from here so no decision is
re-made ad hoc. (Kahn et al. 2016 DQ framework is applied in the analysis
scripts; this module only encodes definitions.)

Locked decisions
----------------
* Grain: ADMISSION (hadm_id).
* Zero-diagnosis admissions: EXCLUDED  -> analysis population = admissions
  having >=1 diagnosis row (545,497 of 546,028).
* Race: value recorded at that admission; the non-informative categories are
  kept as an EXPLICIT category (not missing).
* Diagnosis count: distinct (seq_num, icd_version).
* Age at admission: anchor_age + year(admittime) - anchor_year  (anchor_age is
  capped at 91 for ages >=89 in MIMIC-IV; the cap propagates).
* Lab analytes: blood/serum itemids only (below). GGT is searched and reported
  but NOT used until approved.
"""

DATA = "data/raw/hosp"

# Pre-specified MASLD code set (version-aware, dotless, trimmed).
MASLD_PREDICATE = (
    "((icd_version=10 AND trim(icd_code) IN ('K760','K7581')) "
    " OR (icd_version=9  AND trim(icd_code) IN ('5718','5719')))"
)

# Blood/serum lab analytes -> single approved itemid each.
LAB_ITEMIDS = {
    "ALT":                  50861,
    "AST":                  50878,
    "Platelets":            51265,
    "Triglycerides":        51000,
    "HDL":                  50904,
    "HbA1c":                50852,
    "Glucose":              50931,
    "Albumin":              50862,
    "Bilirubin_total":      50885,
    "Alkaline_phosphatase": 50863,
}

# Non-informative race categories (kept as an EXPLICIT stratum, per decision).
RACE_NONINFORMATIVE = [
    "UNKNOWN", "OTHER", "UNABLE TO OBTAIN",
    "PATIENT DECLINED TO ANSWER", "MULTIPLE RACE/ETHNICITY",
]


def analysis_admissions_sql(data=DATA):
    """Admissions with >=1 diagnosis row (zero-dx EXCLUDED), with code status,
    recomputed age, and length of stay. Grain = hadm_id."""
    return f"""
    WITH dx AS (
      SELECT hadm_id,
             count(DISTINCT (seq_num, icd_version)) AS n_dx,
             max(CASE WHEN {MASLD_PREDICATE} THEN 1 ELSE 0 END) AS masld
      FROM read_csv('{data}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}})
      GROUP BY hadm_id
    )
    SELECT a.hadm_id, a.subject_id,
           dx.masld::BOOLEAN                         AS code_positive,
           dx.n_dx                                   AS n_diagnoses,
           p.anchor_age + year(a.admittime) - p.anchor_year AS age_at_admit,
           p.gender, a.race, a.insurance, a.language, a.marital_status,
           a.admission_type, a.admission_location, a.discharge_location,
           a.hospital_expire_flag,
           a.admittime, a.dischtime, a.deathtime, a.edregtime, a.edouttime,
           p.dod, p.anchor_year_group,
           date_diff('second', a.admittime, a.dischtime)/86400.0 AS los_days
    FROM read_csv_auto('{data}/admissions.csv.gz') a
    JOIN dx USING (hadm_id)                       -- inner join => zero-dx excluded
    JOIN read_csv_auto('{data}/patients.csv.gz') p USING (subject_id)
    """


def lab_itemid_csv():
    return ",".join(str(i) for i in LAB_ITEMIDS.values())
