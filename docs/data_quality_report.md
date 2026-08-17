# Data Quality & Descriptive Report — MIMIC-IV hosp (MASLD phenotyping)

**Scope.** Data quality assessment and descriptive characterization of the
structured MIMIC-IV v3.1 hosp tables (`admissions`, `patients`, `diagnoses_icd`,
`omr`, `labevents`, `d_labitems`, `d_icd_diagnoses`), plus the coded-positive
MASLD set defined in [`sql/masld_coded.sql`](../sql/masld_coded.sql)
(4 pre-specified codes, version-aware): **5,580 subjects / 9,143 admissions**.

**This report surfaces problems and describes the data. It makes no cleaning or
phenotype decisions.** All queries were read-only; nothing under `data/raw/` was
modified and no `.csv.gz` was decompressed. Reproducers:
`scripts/dq_audit.py`, `sql/dq_referential_integrity.sql`, `sql/dq_race.sql` +
`scripts/dq_race.py`, `scripts/table1.py`, `scripts/metabolic_coverage.py`.

---

## Part 1 — Findings

### 1.1 Missingness (Step 1)
- **No hidden empty-strings or whitespace-only values** in any VARCHAR column of
  the four tables (0 across the board). The NULL-vs-empty distinction does not
  bite here; blanks were coerced to NULL by the reader.
- Notable NULL rates:
  - `admissions.discharge_location` **27.4%** · `edregtime`/`edouttime` **30.6%**
    (non-ED admissions) · `marital_status` **2.5%** · `insurance` **1.7%** ·
    `language` 0.14% · `admission_location` 1 row · `admit_provider_id` 4 rows.
  - `admissions.deathtime` 97.8% and `patients.dod` 89.5% — expected (deaths only).
- `diagnoses_icd` and `omr` have no NULLs.

### 1.2 Categorical value content (Step 1)
- `race`: 30+ categories (see §1.6). ~7.3% of admissions sit in non-informative
  buckets — `OTHER` 3.6%, `UNKNOWN` 2.5%, `UNABLE TO OBTAIN` 0.6%,
  `PATIENT DECLINED TO ANSWER` 0.4%, `MULTIPLE RACE/ETHNICITY` 0.1%.
- `insurance`: Medicare 44.8% · Private 31.8% · Medicaid 19.1% · Other 2.6% ·
  NULL 1.7% · No charge 0.08%.
- `marital_status`: MARRIED/SINGLE/WIDOWED/DIVORCED + 2.5% NULL (no "UNKNOWN" level).
- `language`: English 90.2%, then a long tail; explicit `Other` 0.25% + NULL 0.14%.
- `admission_type`: 9 values incl. observation variants; `discharge_location`
  NULL (27.4%) is effectively its second-largest level.
- `gender`: F/M only, clean.

### 1.3 Numeric ranges (Step 1)
- `anchor_age`: 18–91, median 48; **max 91 is the MIMIC age cap** (ages ≥89 are
  collapsed), not a real maximum. No negatives.
- `hospital_expire_flag`: 0/1, mean 0.02. `seq_num`: 1–39. No negatives anywhere.

### 1.4 Duplicates (Step 1)
- **0 full-duplicate rows** in all four tables.
- `admissions`: **0 duplicate `(subject_id, hadm_id)`** — `hadm_id` is a clean key.
- `diagnoses_icd`: **116 "duplicate" `(subject_id, hadm_id, seq_num)` groups**,
  but 0 full-duplicate rows. Cause: **dual-coded admissions** — the same
  `seq_num` appears once as ICD-9 and once as ICD-10 for the same stay. The true
  unique key is **`(subject_id, hadm_id, seq_num, icd_version)`**.

### 1.5 Referential integrity (Step 2)
- **Clean linkage:** 0 diagnosis rows with a `hadm_id` absent from `admissions`;
  0 NULL `hadm_id` in `diagnoses_icd`; 0 admission `subject_id` absent from
  `patients`.
- **531 admissions have zero diagnosis rows** (546,028 admissions vs 545,497 with
  diagnoses). An inner join on diagnoses drops these; they are code-negative by
  construction.
- **141,175 of 364,627 `patients` have no hospital admission** (only 223,452 do).
  `patients` is the all-modules population (ED-only etc.), not the admitted
  population.

### 1.6 Race / ethnicity (Step 3)
- Recorded **per admission**, and **not stable per person**: **11,900 subjects**
  have >1 distinct `race` across their own admissions (11.9% of the 100,163 with
  multiple admissions). Two mechanisms are mixed: hierarchy artifacts
  (`HISPANIC OR LATINO` ↔ `HISPANIC/LATINO - PUERTO RICAN`) and genuinely
  conflicting races (e.g. ASIAN/BLACK/HISPANIC/WHITE across one subject's stays).
- Payer mix varies sharply by race group (row-normalized `race`×`insurance`),
  e.g. `WHITE - RUSSIAN` 71.9% Medicare vs `HISPANIC/LATINO - DOMINICAN` 53.2%
  Medicaid — structure that category-collapsing would blur.

### 1.7 Table 1 — coded-positive vs rest (Step 4)
Admission grain; SMDs (not p-values); |SMD|>0.1 flags imbalance.

| Variable | Coded (n=9,143) | Other (n=536,885) | SMD |
|---|---|---|---|
| Diagnoses per admission, median [IQR] | 16 [11, 22] | 10 [6, 16] | **+0.68** |
| admission_type (multinomial) | see below | | **+0.41** |
| race (multinomial) | see below | | **+0.33** |
| language (multinomial) | Spanish 6.8% | Spanish 3.3% | **+0.20** |
| marital_status (multinomial) | | | **+0.19** |
| Length of stay, days, median [IQR] | 3.7 [1.9, 6.9] | 2.8 [1.1, 5.6] | **+0.18** |
| insurance (multinomial) | Private 36.8% | Private 31.7% | **+0.17** |
| anchor_age, median [IQR] | 57 [46, 65] | 58 [43, 72] | −0.10 |
| gender = M | 50.7% | 47.9% | +0.06 |
| hospital_expire_flag | 2.2% | 2.2% | +0.005 |

- **Diagnoses-per-admission is the dominant imbalance (SMD 0.68):** coded-positive
  admissions are far more comorbid/heavily documented. Consistent with MASLD
  appearing as a trailing code on long problem lists; a major confounder for 1b/1c.
- **race (SMD 0.33):** coded-positive **under-represent BLACK/AFRICAN AMERICAN
  (8.3% vs 13.9%)**, over-represent HISPANIC/LATINO–PUERTO RICAN (5.0% vs 1.9%) —
  the Aim 1c signal, visible before any modeling.
- `admission_type`: coded skew to OBSERVATION ADMIT (25.7% vs 15.3%) and
  SURGICAL SAME DAY (13.2% vs 7.8%).
- **LOS data-quality anomalies: 175 admissions with negative LOS** (dischtime <
  admittime), 5 zero, max 515.6 days.

### 1.8 Metabolic context of the coded cohort (Step 5)
Denominator = 5,580 coded-positive subjects.

**omr (outpatient vitals/anthropometrics)** — coverage of coded subjects:
Blood Pressure 81.1% · Weight (Lbs) 78.0% · BMI (kg/m2) 76.1% · Height (Inches)
75.9%. **`result_name` is fragmented**: `BMI (kg/m2)` (76.1%) is distinct from a
plain `BMI` (17.5%); same for `Weight (Lbs)`/`Weight` and `Height (Inches)`/
`Height`, and BP splits into Sitting/Standing/Lying. A single-string filter
undercounts. `eGFR` present but negligible (0.4%).

**labevents** — coded-subject coverage (≥1 result):

| Analyte | Coverage | Itemid-match caveat |
|---|---|---|
| Platelets | 99.9% | 51265 (+ near-empty dup 53189) |
| Glucose | 99.8% | match spans 13 itemids across blood/urine/CSF/ascites/… |
| Bilirubin | 98.1% | 16 itemids incl. neonatal, urine dipstick |
| ALT | 96.5% | 50861 (+ dup 53084) |
| AST | 96.5% | 50878 (+ dup 53088) |
| Alkaline phosphatase | 96.0% | match incl. **Leukocyte ALP 51241 (hematology, not serum)** |
| Albumin | 93.8% | 21 itemids incl. **urine microalbumin & albumin/creatinine** |
| HbA1c | 67.6% | 50852 / 50854 (Absolute A1c) / 51631 (Glycated Hb) |
| Triglycerides | 66.7% | 6 itemids incl. ascites/pleural/CSF/joint/stool |
| HDL | 61.3% | match incl. **Cholesterol Ratio (Total/HDL) 50903, a ratio** |

- LFTs, glucose, platelets, albumin: excellent coverage. Lipid/glycemic panel
  (HbA1c, triglycerides, HDL): moderate (60–68%) — outpatient/elective labs not
  drawn every admission. **No analyte < 10%; none flagged unusable.**
- The blood assays dominate the coverage numbers, so multi-fluid contamination
  inflates only marginally — but the itemid sets are not yet clean (see 2.10).

---

## Part 2 — Decisions required (options + what's at stake; no recommendation)

**1. Analysis grain & cohort denominator.** `patients` (364,627) ⊋ admitted
subjects (223,452) ⊋ … ; admission grain (546,028) vs subject grain.
*Options:* anchor the study population on admitted-subjects, on all `patients`,
or on admissions. *At stake:* the 2×2 denominator and every rate computed from it.

**2. Zero-diagnosis admissions (531).** They carry no ICD codes, so are
code-negative by construction and dropped by an inner join on diagnoses.
*Options:* include as code-negative, or exclude as un-codeable encounters.
*At stake:* composition of the code-negative cell and the ICD-miss denominator.

**3. Dual-coding key & diagnosis counts.** `(subject_id, hadm_id, seq_num)` is
non-unique; some admissions carry both ICD-9 and ICD-10 rows, inflating
"diagnoses per admission" (the largest Table 1 imbalance). *Options:* count
distinct `(seq_num, version)`, dedupe to one version per admission, or count raw
rows. *At stake:* the diagnosis-count covariate and any seq_num-position logic.

**4. Non-informative race categories (~7.3%).** `UNKNOWN`, `OTHER`,
`UNABLE TO OBTAIN`, `PATIENT DECLINED`, `MULTIPLE RACE/ETHNICITY`. *Options:*
treat as missing, keep as an explicit category, or exclude from 1c subgroup
analyses. *At stake:* which patients are analyzable in the equity audit and how
"unknown-race" bias is handled.

**5. Per-subject race assignment (11,900 inconsistent subjects).** Race varies
across a subject's admissions. *Options:* most-recent, modal, most-specific
(deepest hierarchy), or ever-mentioned. *At stake:* which 1c subgroup each of
these subjects is counted in.

**6. Race granularity / collapsing.** 30+ hierarchical categories. *Options:*
analyze at full granularity (low power in small cells), collapse to top-level
groups (WHITE/BLACK/HISPANIC/ASIAN/…), or a custom scheme. *At stake:* 1c
statistical power vs resolution; the payer-mix structure in §1.6 is what
collapsing would blur.

**7. Missing categorical covariates.** `discharge_location` 27.4%, `marital_status`
2.5%, `insurance` 1.7%, `language` 0.14% NULL. *Options:* missing-indicator
category, complete-case, or imputation. *At stake:* differential missingness —
part of the insurance/marital SMDs is driven by the "Missing" level itself.

**8. Age cap at 91.** All ages ≥89 collapse to 91. *Options:* use `anchor_age`
as-is, top-code/bin the elderly, or derive age-at-admission
(`anchor_age + year(admittime) − anchor_year`, still capped). *At stake:* the age
covariate and any elderly subgroup.

**9. Length-of-stay anomalies.** 175 negative LOS, 5 zero, max 515.6 days.
*Options:* drop non-positive LOS, winsorize the upper tail, or keep raw.
*At stake:* LOS as covariate/outcome and its SMD.

**10. labevents analyte itemid sets.** Label search over-matches: HDL includes a
ratio (50903); Alk phos includes leukocyte ALP (51241); Albumin/Bilirubin/
Glucose/Triglycerides span urine/CSF/ascites/etc. and neonatal variants.
*Options:* restrict to blood/serum primary assays (e.g. ALT 50861, AST 50878,
Platelets 51265, Triglycerides 51000, HDL 50904, HbA1c 50852, Glucose 50931,
Albumin 50862, Bilirubin-total 50885, Alk phos 50863), or keep broader sets.
*At stake:* validity of each analyte as a metabolic feature (the printed itemid
lists in `scripts/metabolic_coverage.py` output are the material to verify).

**11. omr `result_name` fragmentation.** BMI/Weight/Height and BP each appear
under multiple strings. *Options:* union the synonymous names before computing
coverage/features, or use the dominant string only. *At stake:* true
anthropometric/BP coverage (unioning raises BMI coverage above the 76.1% single
-string figure).

**12. Lipid/glycemic ascertainment (60–68% coverage).** Triglycerides, HDL, HbA1c
are missing for ~1/3 of coded subjects. *Options:* define the metabolic criterion
tolerant of missing labs, require them (shrinking the ascertainable cohort), or
substitute omr/vitals + diagnosis-code proxies. *At stake:* how the "metabolic
dysfunction" half of the MASLD definition is operationalized and its missingness.

---

*End of report. No data cleaned, no phenotype decisions made.*
