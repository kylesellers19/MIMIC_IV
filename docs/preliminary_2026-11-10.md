# Exploratory analyses, 10 November 2026

> **PRELIMINARY and exploratory (analysis-plan amendments l–o, registry S19–S22).** Nothing here is validated against chart review. Every number is written by the script named in each section into `docs/run_2026-11-10/results/`. Counts from 1 to 10 appear as <11, and a share that would reveal one is withheld.

The amendments were committed before any of these analyses was computed (`docs/analysis_plan_prespecified.md` §6; commit in `docs/run_2026-11-10/STATE.json`, `phase3_commit`). None of them changes a primary analysis. All four use the frozen keyword rule for the note axis; section 1 also repeats one table with the language-model phenotype on the dev/test notes subsample.

## 1. Fibrosis index by cell (amendment l, S19)

Written by `scripts/run1110_fib4_by_cell.py` into `docs/run_2026-11-10/results/fib4_by_cell.json`.

- **Measure:** FIB-4 = age x AST / (platelets x sqrt(ALT)). Age is the age at admission, as in Table 3.
- **Cutoffs:** below 1.3 (low), above 2.67 (high).
- **Cells:** definition (b), as in `docs/aim1a_crosstab.md`. A = coded and in notes, B = in notes only, C = coded only, D = neither.
- **Intervals:** subject-cluster bootstrap, 500 replicates, 95% percentile.

### Primary: first result of each admission

| Cell | Admissions | FIB-4 computable | Median [IQR] | Below 1.3 | 1.3–2.67 | Above 2.67 |
| --- | --: | --: | --: | --: | --: | --: |
| A · coded, in notes | 5,027 | 64.2% (62.4–65.8) | 3.1 [1.42, 6.51] | 22.2% (20.2–24.2) | 22.9% (21.1–24.7) | 54.9% (52.3–57.7) |
| B · not coded, in notes | 22,799 | 61.5% (60.6–62.3) | 2.34 [1.17, 5.33] | 28.5% (27.4–29.5) | 26.1% (25.2–27.0) | 45.4% (44.3–46.6) |
| C · coded, not in notes | 713 | 46.7% (43.2–50.6) | 2.41 [1.38, 4.64] | 21.6% (17.3–25.8) | 33.9% (28.5–39.2) | 44.4% (39.4–49.9) |
| D · neither | 345,453 | 37.5% (37.3–37.7) | 1.77 [1.01, 3.34] | 35.7% (35.3–36.2) | 31.8% (31.5–32.2) | 32.4% (32.0–32.8) |

The three right-hand columns are shares of the admissions with a computable FIB-4, not of all admissions.

### Sensitivity analyses

Each row repeats the primary table under one change. Shown: the computable share, the median, and the share above 2.67.

| Analysis | Cell | Admissions kept | FIB-4 computable | Median [IQR] | Below the low cutoff | Above 2.67 |
| --- | --- | --: | --: | --: | --: | --: |
| 1 · low cutoff 2.0 at age 65 and over | A | 5,027 | 64.2% (62.4–65.8) | 3.1 [1.42, 6.51] | 26.8% (24.7–28.9) | 54.9% (52.3–57.7) |
|  | B | 22,799 | 61.5% (60.6–62.3) | 2.34 [1.17, 5.33] | 34.1% (32.9–35.1) | 45.4% (44.3–46.6) |
|  | C | 713 | 46.7% (43.2–50.6) | 2.41 [1.38, 4.64] | 30.0% (25.3–34.5) | 44.4% (39.4–49.9) |
|  | D | 345,453 | 37.5% (37.3–37.7) | 1.77 [1.01, 3.34] | 46.9% (46.5–47.3) | 32.4% (32.0–32.8) |
| 2 · last result of the admission | A | 5,027 | 64.2% (62.4–65.8) | 2.35 [1.1, 5.56] | 30.5% (28.1–32.6) | 46.0% (43.1–48.9) |
|  | B | 22,799 | 61.6% (60.6–62.3) | 1.77 [0.96, 3.9] | 37.2% (36.1–38.2) | 35.3% (34.2–36.5) |
|  | C | 713 | 46.7% (43.2–50.6) | 1.95 [1.12, 3.8] | 32.1% (27.2–36.8) | 37.2% (32.2–43.5) |
|  | D | 345,453 | 37.5% (37.3–37.7) | 1.56 [0.9, 2.82] | 41.3% (40.8–41.7) | 26.8% (26.4–27.2) |
| 3 · excluding AST or ALT above 200 U/L, and alcohol, viral, other-etiology or cirrhosis flags | A | 2,954 | 47.9% (45.9–49.9) | 1.55 [0.88, 2.72] | 41.1% (37.8–44.3) | 25.7% (23.1–28.5) |
|  | B | 14,778 | 49.6% (48.7–50.6) | 1.47 [0.87, 2.56] | 44.0% (42.6–45.4) | 23.5% (22.2–24.8) |
|  | C | 517 | 36.0% (32.1–40.4) | 1.86 [1.16, 3.23] | 28.5% (22.1–34.5) | 32.8% (26.5–39.4) |
|  | D | 298,565 | 33.3% (33.0–33.5) | 1.54 [0.91, 2.6] | 41.2% (40.8–41.7) | 23.9% (23.5–24.2) |
| 4 · most recent outpatient values, 365 days before admission | A | 5,027 | 81.3% (79.9–82.6) | 2.04 [0.98, 4.76] | 35.5% (33.0–37.8) | 42.5% (39.8–45.1) |
|  | B | 22,799 | 78.5% (77.8–79.1) | 1.69 [0.95, 3.56] | 38.6% (37.5–39.7) | 32.8% (31.7–33.9) |
|  | C | 713 | 71.2% (67.9–74.8) | 1.65 [0.96, 2.94] | 37.4% (33.3–42.2) | 27.8% (23.7–31.7) |
|  | D | 345,453 | 54.7% (54.4–55.0) | 1.51 [0.92, 2.56] | 42.0% (41.6–42.5) | 23.5% (23.1–23.9) |

Analysis 3 removes these shares of each cell before anything is computed: A 41.2%; B 35.2%; C 27.5%; D 13.6%.

### Replicate with the language-model phenotype

Dev/test notes subsample only (29,980 admissions). First result of each admission.

| Group | Admissions | FIB-4 computable | Median [IQR] | Below 1.3 | 1.3–2.67 | Above 2.67 |
| --- | --: | --: | --: | --: | --: | --: |
| Coded, LLM-positive | 425 | 60.7% (55.0–67.0) | 2.71 [1.47, 6.7] | 21.3% (15.4–28.4) | 28.7% (22.4–36.1) | 50.0% (39.0–59.7) |
| Uncoded, LLM-positive | 1,827 | 61.0% (58.4–63.9) | 2.35 [1.17, 5.87] | 28.1% (24.8–31.3) | 26.5% (23.4–29.4) | 45.5% (41.8–49.2) |

**Limitations.** FIB-4 is validated in outpatients. Acute illness raises AST and lowers platelets, so an inpatient value overstates fibrosis risk; analyses 2, 3 and 4 show how far the figures move when that is partly removed. FIB-4 can be computed for different shares of each cell, so the cells are compared on differently selected admissions. Admissions are not independent: one patient can contribute several. The cells rest on the frozen keyword rule, which has not been checked against chart review. Nothing here says who has fibrosis.

## 2. Later outcomes after an uncoded mention (amendment m, S20)

Written by `scripts/run1110_later_outcomes.py` into `docs/run_2026-11-10/results/later_outcomes.json`. Grain: subject. Intervals: Wilson 95%. No survival model.

- **Index:** the subject's earliest admission in which the notes are positive under definition (b).
- **Group U:** the index admission has no MASLD code, and no earlier admission has one.
- **Group C:** the index admission has a MASLD code.
- **A later admission** is any admission of the analysis population that begins after the index admission began.
- **Days** run from the index discharge to the start of the first later admission that carries the flag.

| Step | Subjects |
| --- | --: |
| With a note-positive admission | 15,001 |
| Index uncoded but coded earlier (in neither group) | 46 |
| Excluded: cirrhosis or HCC flag at or before index | 1,956 |
| Excluded: died during the index admission | 259 |
| Group U | 10,727 |
| Group C | 2,013 |

| Measure | Group U (uncoded at index) | Group C (coded at index) |
| --- | --: | --: |
| Subjects with a later admission | 55.2% (54.2–56.1) | 46.5% (44.3–48.7) |
| Of those, a later cirrhosis flag | 8.4% (7.7–9.1) | 8.3% (6.7–10.3) |
| Days to the first later cirrhosis flag, median [IQR] | 527 [132, 1,301] | 521 [85, 1,103] |
| Of those, a later HCC flag | 0.5% (0.4–0.7) | withheld |
| Days to the first later HCC flag, median [IQR] | 826 [190, 2,324] | — |
| Of those, later given a MASLD code | 11.6% (10.8–12.4) | not applicable |
| Days to the first coded admission, median [IQR] | 480 [110, 1,262] | not applicable |
| Admissions after the index and before the first coded one, median [IQR] | 1 [0, 2] | not applicable |

**Limitations.** Only returns to this hospital are observed, so every figure is a floor: a patient diagnosed or coded elsewhere counts as never diagnosed or coded. The two groups differ in more than coding, and nothing here adjusts for it. Follow-up length differs by patient and is not modelled. The cirrhosis and HCC flags come from diagnosis codes. A flag at a later admission can describe disease that was already present at index but not coded. The index rests on the frozen keyword rule, unchecked against chart review.

## 3. Coding by period (amendment n, S21)

Written by `scripts/run1110_icd_era.py` into `docs/run_2026-11-10/results/icd_era.json`.

- **Measure:** among note-positive admissions, the share with no MASLD code, B ÷ (A + B).
- **Intervals:** subject-cluster bootstrap, 500 replicates, 95% percentile.
- **Second column:** the same share with ICD-9 571.9 removed from the code set (S7).

### By the patient's anchor year group

| Anchor year group | Note-positive admissions | Share uncoded | Share uncoded, 571.9 removed |
| --- | --: | --: | --: |
| 2008 - 2010 | 11,995 | 84.5% (83.4–85.5) | 84.5% (83.4–85.6) |
| 2011 - 2013 | 6,414 | 81.0% (79.6–82.5) | 81.1% (79.7–82.5) |
| 2014 - 2016 | 5,358 | 79.6% (78.1–81.3) | 79.7% (78.2–81.4) |
| 2017 - 2019 | 4,059 | 79.0% (77.1–80.5) | 79.0% (77.1–80.5) |
| 2020 - 2022 | 0 | not reported | not reported |

### By the ICD version of the admission's diagnoses

| ICD version | Note-positive admissions | Share uncoded | Share uncoded, 571.9 removed |
| --- | --: | --: | --: |
| Both | 0 | not reported | not reported |
| ICD-10 only | 12,890 | 79.2% (78.1–80.2) | 79.2% (78.1–80.2) |
| ICD-9 only | 14,936 | 84.3% (83.4–85.2) | 84.4% (83.5–85.3) |

All note-positive admissions (27,826): 81.9% (81.2–82.7); with 571.9 removed, 82.0% (81.3–82.7). A stratum is reported when it has at least 11 note-positive admissions.

**Limitations.** The anchor year group is a three-year window assigned once per patient. It is not the calendar year of the admission, and a patient's admissions can fall years after it. Period and ICD version move together, so neither table isolates one from the other. Case mix, note volume and imaging use also changed over these years. The note axis is the frozen keyword rule, unchecked against chart review.

## 4. Documentation funnel where the liver was imaged (amendment o, S22)

Written by `scripts/run1110_imaging_funnel.py` into `docs/run_2026-11-10/results/imaging_funnel.json`.

- **Population:** imaging-observed admissions (S3): at least one liver-inclusive study, linked to the admission or in the outpatient window of 365 days before to 30 days after admission.
- **Rule-positive** means the frozen keyword rule fires in that document.
- **Intervals:** subject-cluster bootstrap, 500 replicates, 95% percentile.

| Stage | Admissions | Share of the stage above |
| --- | --: | --: |
| 1 · Imaging-observed | 138,603 of 373,992 | 37.1% (36.8–37.3) |
| 2 · A radiology report is rule-positive | 20,364 of 138,603 | 14.7% (14.3–15.1) |
| 3 · The discharge summary is also rule-positive | 8,081 of 20,364 | 39.7% (38.7–40.7) |

| Stage 4 · coded share | Admissions coded | Share coded |
| --- | --: | --: |
| Discharge summary rule-positive (stage 3 yes) | 2,560 of 8,081 | 31.7% (30.4–33.1) |
| Discharge summary not rule-positive (stage 3 no) | 349 of 12,283 | 2.8% (2.5–3.2) |

### Stage 2 split by where the positive radiology report sits

| Source of the positive report | Share of stage 2 | Discharge summary also positive | Coded, summary positive | Coded, summary not positive |
| --- | --: | --: | --: | --: |
| A report linked to the admission | 47.7% (46.8–48.6) | 61.4% (60.2–62.4) | 25.9% (24.6–27.2) | 3.7% (3.1–4.4) |
| Outpatient-window reports only | 52.3% (51.4–53.2) | 19.9% (18.7–21.0) | 47.9% (45.3–50.5) | 2.5% (2.1–2.8) |

**Limitations.** A rule-positive report is a keyword match, not a confirmed finding, and the rule has not been checked against chart review. An outpatient-window report can be up to a year old, so its absence from the discharge summary is not an omission in itself. The funnel is restricted to admissions where the liver was imaged, which is a selected group. The stages describe documents; they do not say why a finding was not carried forward or not coded.
