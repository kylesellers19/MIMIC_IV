# Cleaning Execution — MIMIC-IV hosp (MASLD phenotyping)

Execution of [docs/cleaning_spec.md](cleaning_spec.md) against the **locked
analysis population** (373,992 admissions). Reproducer:
[`scripts/clean_population.py`](../scripts/clean_population.py). Output (credentialed,
gitignored): `data/processed/analysis_population_clean.parquet` (56 cols);
`analysis_population.parquet` (uncleaned) is **preserved** — the cleaning is
reversible and auditable.

**Governing principle applied:** implausible values were **nulled, never dropped.**
No rule deleted rows; **row count = 373,992** (asserted, PASS). Aggregate reporting
only; no note/patient-level content.

> **Scope note.** The spec's row-count estimates were computed on the full 545,497
> analysis population; this execution runs on the locked 373,992 subset, so temporal
> counts are correspondingly smaller (e.g. neg-LOS 89 here vs 175 spec).

## Step 2 — value-level corrections

### Labs (P1) — null impossible, retain extreme-but-real
Bounds (approved): physiological-possibility ceilings. Impossible → null; values
within bounds but outside typical reference were **retained** (extreme-but-real).

| Analyte | had value | nulled (impossible) | max nulled | max retained (kept) |
|---|--:|--:|--:|--:|
| ALT | 149,643 | 0 | – | 15,018 |
| AST | 150,077 | 0 | – | 28,275 |
| Platelets | 312,112 | 0 | – | 2,947 |
| Triglycerides | 29,146 | 0 | – | 10,440 |
| HDL | 21,114 | **3** | 244 | 167 |
| HbA1c | 30,024 | **1** | 22.0 | 19.4 |
| Glucose | 307,745 | **2** | 3,678 | 2,970 |
| Albumin | 109,879 | **1** | 7.1 | 6.8 |
| Bilirubin total | 146,509 | 0 | – | 60.5 |
| Alk phosphatase | 146,516 | 0 | – | 3,593 |
| GGT (descriptive) | 3,704 | 0 | – | 7,380 |

**7 impossible lab values nulled in total.** ALT/AST extremes (to 28,275) are
genuine critical-illness values and were kept.
**C1:** 5 non-numeric `value` strings with null `valuenum` — **left as-is, not
coerced** (report only).

### omr (P2/C4) — parse BP, null impossible, drop dbp-zeros & post-death
- **Blood Pressure parsed** `NNN/NNN` → sbp/dbp; **parse-failure rate 0.000%** (0 of 2,827,801).
- Reading-level nulls: **BMI 770**, Weight 687, Height 342 (out of possible ranges);
  **diastolic-zeros 907** nulled; **[T5] 216** post-`dod` readings excluded.
- Admission-feature effect (subject-median): omr_BMI nulled for **175** admissions,
  omr_SBP **3**, omr_DBP **4**.

### Temporal (T1–T5) — locked population
| Item | Action | Count |
|---|---|--:|
| T1 admittime > dischtime | `los_days` → null; admission & timestamps kept | **89** |
| T2 deathtime outside [admit,disch] | **flag** `flag_death_after_disch`; no null | **549** |
| T3 dischtime > dod | **flag** `flag_disch_after_dod`; no null | **8** |
| T4 lab charttime outside window | **NOT nulled**; concentration checked (below) | 3,421,479 |
| T5 omr chartdate > dod | readings excluded from omr features | 216 |

**T4 concentration check:** the 3.42M out-of-window labs are spread across **69,241
admissions (12.7% of admissions)** — **spread, not concentrated** in a few
admissions. This is consistent with a boundary artifact (pre-admission ED draws /
discharge-day results), not a data-integrity problem localized to specific stays;
per spec they are retained un-nulled.

## Step 3 — missingness indicators (20 created)
`miss_lab_{ALT,AST,Platelets,Triglycerides,HDL,HbA1c,Glucose,Albumin,Bilirubin_total,Alkaline_phosphatase,GGT}`,
`miss_omr_{BMI,SBP,DBP}`, `miss_los_days`,
`miss_{insurance,marital_status,language,discharge_location,admission_location}`.
These are **features** — the differential-completeness finding means availability
itself carries signal (Aim 1c).

## Step 4 — differential-nulling check (the check that matters)
Proportion nulled by coding status (SMD) and range across race/insurance. **No
variable shows materially differential nulling** (flag threshold: n≥20 nulled AND
|SMD|≥0.1 — none met).

| variable | nulled | null% code+ | null% code− | SMD | race range | ins range |
|---|--:|--:|--:|--:|--:|--:|
| lab_HDL | 3 | 0.000 | 0.014 | −0.017 | 0.3 | 0.1 |
| lab_HbA1c | 1 | 0.000 | 0.003 | −0.008 | 0.1 | 0.0 |
| lab_Glucose | 2 | 0.000 | 0.001 | −0.004 | 0.0 | 0.0 |
| lab_Albumin | 1 | 0.038 | 0.000 | +0.028 | 0.1 | 0.0 |
| omr_BMI | 175 | 0.098 | 0.060 | +0.013 | 0.3 | 0.0 |
| omr_SBP / omr_DBP | 3 / 4 | ~0 | ~0.001 | −0.005 | 0.1 | 0.0 |
| (all other labs) | 0 | – | – | 0.000 | 0.0 | 0.0 |

The nulling volume is tiny and does **not** track coding status, race, or insurance
— the cleaning did not interact with the study's documentation-quality axis.

## Step 5 — materialize
`data/processed/analysis_population_clean.parquet`, **373,992 rows (asserted)**,
56 columns (covariates + cleaned lab/omr features + temporal flags + 20 indicators).
Uncleaned parquet preserved. `data/` is gitignored — nothing stageable.

## Step 6 — table regeneration & movement
Cleaned tables regenerated into `docs/tables/clean/` (uncleaned locked tables kept
in `docs/tables/` for comparison).

- **Medians / IQRs: nothing moved.** Table 1 continuous (age, LOS, distinct
  diagnoses) and Table 2 Panel B lab medians are **identical** cleaned vs uncleaned
  — medians are robust to the handful of nulled impossibles, confirming the problem
  was a few isolated values, not a widespread one.
- **SMDs: negligible movement.** Availability SMDs shifted by ≤0.002 (BMI
  0.332→0.330, Albumin 0.348→0.347); all others unchanged.
- **FIB-4: byte-identical.** Computable 62.0% (code+) / 39.0% (code−), SMD +0.472;
  median 3.0 [1.4, 6.3] vs 1.8 [1.0, 3.5]; strata unchanged. Because ALT, AST, and
  platelets had **0 impossible values**, the FIB-4 inputs were untouched — the
  extreme aminotransferases driving high FIB-4 are physiologically real, not errors.

**Conclusion.** The cleaning corrects a small number of impossible values (7 labs,
~1,900 omr readings, 89 LOS) with no differential bias and no material change to the
robust descriptive statistics. Its value is for **means, feature construction, and
modeling** (where impossible values would dominate), and for making the correction
**visible as explicit missingness** rather than as dropped rows.
