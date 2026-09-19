# Aim 1a loose ends — Phase 4.3–4.6 (run_2026-09-19)

Scripts: `scripts/run0919_loose_ends_43_44.py`, `scripts/run0919_cohort_flow.py`, `scripts/run0919_avail_windows.py`. Results: `docs/run_2026-09-19/results/loose_ends_43_44.json`, `cohort_flow.json`, `avail_windows.json`. The primary definition is unchanged throughout; these are pre-specified sensitivity analyses (registry S8, S9, S10 in `docs/analysis_plan_prespecified.md`).

## 4.3 Discharge-summary-only population

Pre-specified at the population lock and never run as a 2×2. Restricts to admissions with a linked discharge summary (the population that a discharge-note-only phenotype would see).

Discharge-only population: **331,604 admissions / 145,817 subjects / 5,552 code-positive** (matches the population-lock sensitivity line: 331,604 / 145,817 / 5,552).

| population / variant | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− | recovery share % | corroboration share % |
| --- | --: | --: | --: | --: | --: | --: |
| full population, (a) inpatient-linked | 4,805 | 13,612 | 935 | 354,640 | 73.91 | 83.71 |
| discharge-only, (a) inpatient-linked | 4,751 | 12,952 | 801 | 313,100 | 73.16 | 85.57 |
| full population, (b) PRIMARY −365/+30 | 5,027 | 22,799 | 713 | 345,453 | 81.93 | 87.58 |
| discharge-only, (b) −365/+30 | 4,938 | 21,134 | 614 | 304,918 | 81.06 | 88.94 |

Restricting to admissions with a discharge summary removes radiology-only admissions; the recovery share moves by under one point under (b) and the corroboration share rises slightly, because code-positive admissions without a discharge summary are disproportionately note-negative.

## 4.4 Hedged (Tier C) mentions counted as positive

Tier C = a lexicon match under a hedge cue ("may represent", "cannot exclude" …). The frozen rule flags these and reports them separately; a hedged imaging finding can be a true positive, so this variant counts any Tier C hit as note-positive. Inpatient-linked hits and outpatient radiology within the window are both included (under (b)); the earlier Tier C table in `docs/predefinition_descriptives.md` counted inpatient-linked notes only, which is why its per-cell counts are smaller.

| population / variant | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− | recovery share % | corroboration share % |
| --- | --: | --: | --: | --: | --: | --: |
| (a) primary | 4,805 | 13,612 | 935 | 354,640 | 73.91 | 83.71 |
| (a) Tier C counted positive | 4,824 | 13,970 | 916 | 354,282 | 74.33 | 84.04 |
| (b) primary | 5,027 | 22,799 | 713 | 345,453 | 81.93 | 87.58 |
| (b) Tier C counted positive | 5,048 | 23,353 | 692 | 344,899 | 82.23 | 87.94 |

Admissions added by counting Tier C positive: (a) 377; (b) 575. Any-Tier-C by primary cell under (b): A 233 of 5,027; B 879 of 22,799; C 21 of 713; D 554 of 345,453.

Consistency check: rebuilding the primary note status from the per-note index reproduces the frozen frame exactly (inpatient Tier A: True, mismatches 0; definition (b): True).

## 4.5 Cohort-flow reconciliation (exact counts)

| step | admissions | subjects |
| --- | --: | --: |
| All admissions (MIMIC-IV v3.1 hosp) | 546,028 | 223,452 |
| − zero-diagnosis admissions | −531 | |
| = analysis population | 545,497 | 223,291 |
| − note-coverage restriction, part (i): subject absent from the note module entirely (release lineage) | −100,029 | |
| − part (ii): subject has notes on other admissions, none linked to this one (encounter level) | −71,476 | |
| = locked analysis population | 373,992 | 161,119 |

Parts (i) + (ii) = 171,505 = the subtraction-derived 171,505 (sum check: True). Locked population equals CLEAN_POP row count: True.

**On the 'covered window' framing.** The run file asked for the split as (i) admissions outside the note module's covered window and (ii) admissions inside the window with no linked note. The project's population-lock analysis (`docs/analysis_population.md`, `docs/tables/table0.md`) found **no admission-year window** — coverage is flat across derived admission years — and decomposed the exclusion by *subject lineage* instead, as above. The nearest window-like quantity is the per-patient `anchor_year_group`: coverage by group is 2008 - 2010: 76.38%, 2011 - 2013: 75.15%, 2014 - 2016: 73.97%, 2017 - 2019: 66.84%, 2020 - 2022: 0.0%. Of the removed admissions, 42,413 have anchor group 2020–2022 (all but one admission in that group) and 129,092 have earlier anchor groups. Both framings are reported; the lineage split is the one the flow table uses.

**Disagreements between existing docs (flagged, not resolved).**
- `docs/note_coverage.md` states "the window is temporal and hard-edged … analysable window is anchor_year_group 2008–2019", whereas `docs/analysis_population.md` and `docs/tables/table0.md` state there is no admission-year window and the 2020–2022 pattern is a per-patient release-lineage artifact. The later two agree with this recomputation; `note_coverage.md` is the earlier, superseded analysis and should be marked as such rather than silently edited.
- `docs/tables/table0.md` says release-lineage exclusion "includes all 42,412 anchor-2020–2022 admissions"; this recomputation finds 42,414 admissions in that group, of which 42,413 are removed — a one-admission discrepancy in a subtotal (the main flow counts agree exactly).

## 4.6 Availability differentials under both outpatient windows

Availability = an in-admission result OR an outpatient result within the window (−365/+30 or −90/+30 days of admission); imaging = any radiology report, and any liver-inclusive report, inpatient-linked or outpatient within the window. SMD = one-versus-rest standardized mean difference of the availability proportion. If the differential does not shrink when the window widens, that points to access rather than encounter type.

| measure | overall −90/+30 % | overall −365/+30 % | SMD code+ vs code−, −90/+30 | −365/+30 | max |SMD| across race, −90/+30 | −365/+30 | shrinks? | max |SMD| across insurance, −90/+30 | −365/+30 | shrinks? |
| --- | --: | --: | --: | --: | --: | --: | --- | --: | --: | --- |
| ALT | 65.69 | 73.11 | 0.439 | 0.54 | 0.304 | 0.272 | yes | 0.334 | 0.461 | no |
| AST | 65.44 | 72.57 | 0.442 | 0.55 | 0.299 | 0.251 | yes | 0.328 | 0.449 | no |
| HbA1c | 18.93 | 27.27 | 0.236 | 0.377 | 0.193 | 0.412 | no | 0.225 | 0.312 | no |
| Triglycerides | 16.09 | 27.47 | 0.183 | 0.288 | 0.16 | 0.444 | no | 0.077 | 0.292 | no |
| HDL | 14.25 | 26.46 | 0.127 | 0.24 | 0.177 | 0.453 | no | 0.076 | 0.313 | no |
| Platelets | 98.18 | 98.75 | -0.1 | 0.068 | 0.137 | 0.131 | yes | 0.34 | 0.264 | yes |
| Glucose | 96.61 | 97.52 | -0.059 | 0.089 | 0.18 | 0.163 | yes | 0.316 | 0.349 | no |
| any_imaging | 91.3 | 93.53 | 0.1 | 0.123 | 0.164 | 0.262 | no | 0.146 | 0.189 | no |
| liver_imaging | 31.57 | 37.06 | 0.605 | 0.736 | 0.257 | 0.277 | no | 0.123 | 0.183 | no |

For most measures the largest between-stratum differential does **not** shrink when the window widens from 90 to 365 days; for several it grows. Per-stratum availability percentages and SMDs for every race and insurance category under both windows are in the results JSON.

Insurance detail (availability %, −90/+30 → −365/+30):

| insurance | n | ALT | HbA1c | triglycerides | HDL | liver imaging |
| --- | --: | --- | --- | --- | --- | --- |
| (missing) | 5,193 | 49.6 → 51.7 | 13.2 → 14.9 | 13.4 → 15.7 | 11.7 → 14.2 | 27.2 → 28.6 |
| Medicaid | 63,027 | 68.7 → 76.3 | 19.0 → 28.6 | 15.3 → 26.7 | 13.3 → 25.3 | 33.4 → 39.4 |
| Medicare | 180,507 | 67.1 → 75.4 | 20.9 → 30.1 | 16.7 → 29.2 | 15.2 → 28.7 | 29.7 → 35.7 |
| No charge | 73 | 57.5 → 61.6 | 11.0 → 15.1 | 15.1 → 20.5 | 15.1 → 23.3 | 26.0 → 35.6 |
| Other | 9,970 | 61.4 → 66.9 | 16.8 → 22.0 | 15.4 → 23.0 | 13.4 → 21.5 | 32.7 → 36.5 |
| Private | 115,222 | 62.9 → 69.3 | 16.3 → 23.1 | 15.8 → 26.1 | 13.5 → 24.5 | 33.5 → 38.4 |
