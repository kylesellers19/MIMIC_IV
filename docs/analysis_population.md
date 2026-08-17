# Locked Analysis Population — MASLD / MIMIC-IV

Aggregate-only. Reproducer: `scripts/lock_population.py`. Materialized covariate
table (credentialed, gitignored): `data/processed/analysis_population.parquet`
(373,992 rows × 22 cols).

## Definition

**Locked analysis population = admissions (grain = hadm_id) in the analysis
population with ≥1 linked clinical note (discharge OR radiology, by hadm_id).**

- N admissions **373,992** · N subjects **161,119**
- code-positive **5,740** · code-negative **368,252**
- Sensitivity (pre-specified): discharge-only → 331,604 adm / 145,817 subj /
  5,552 code-positive. **Not primary** — radiology-only admissions are retained
  because incidental imaging steatosis is a core mechanism of the study.

## There is no admission-year window (key finding)

Coverage by **derived admission year** (`year(admittime)`, per-admission) is flat
at **~67–70% across 2110–2207**, tapering only in the sparse tail (2208 53% →
2213–2214 0%, together ~1,100 admissions). **The note missingness is not a
temporal window at the admission level.** The earlier "2008–2019 window" was an
artifact of `anchor_year_group`, a per-patient bucket: uncovered patients' shifted
admittimes scatter across all admission years, diluting each year to ~68% rather
than forming a cliff. Per instruction, the window is defined empirically at
admission level — and empirically there isn't one.

## Two exclusions

Because there is no admission-year window, the release-lineage exclusion is
**patient-level** (a subject is in Note 2.2 or not). Among multi-admission
subjects, has-note is all-or-nothing for **66.2%** — dominant but not sole, so
encounter-level missingness is also real.

| Exclusion | Mechanism | Admissions | Subjects |
|---|---|--:|--:|
| (a) Release-lineage | Subject absent from Note 2.2 entirely (external to encounter/coder) | 100,029 | 62,172 |
| (b) Encounter-level | Subject has notes on other admissions, but this admission has none | 71,476 | — |
| **Total removed** | | **171,505** | |

(a) includes **all 42,412** anchor-2020–2022 admissions **plus ~57.6k** from
earlier anchor groups (v3.1 hosp patients simply not in Note 2.2):
2008–2010 22,111 · 2011–2013 13,228 · 2014–2016 11,322 · 2017–2019 10,956 ·
2020–2022 42,412.

### (b) is a selection threat (differential)

Encounter-level no-note, among note-release patients:
- **By coding status:** code+ 21.3% vs code− 16.0% (**SMD +0.138**).
- **By admission_type:** EU OBSERVATION 31.5%, DIRECT OBSERVATION 25.6%,
  OBSERVATION ADMIT 21.2% vs EW EMER. 6.1%, DIRECT EMER. 4.8% — i.e. **short
  observation stays** that don't generate a discharge summary.
- **LOS:** no-note median 1.60 d vs 3.03 d (SMD −0.174); **LOS<1 d 41.2% vs 17.2%**.
- **By insurance:** No charge 70.4%, Medicaid 23.7%, Medicare 14.8%, Private 13.5%.
- **By race (n≥500):** highest in several Hispanic/White-European strata (~26–27%),
  lowest UNKNOWN 4.5%.

Both exclusions are differential by coding status and demographics — the note
restriction is **not** a neutral filter; Aim 1c must account for it.

## Effect on descriptive SMDs (full → locked population)

Regenerated via `POP_PARQUET=… make_tables.py`. **The race differential SURVIVES;
the lab-availability differentials survive for LFTs but shrink for the
short-stay-driven analytes** — i.e. partly (not wholly) artifacts of the removed
uncovered/short-stay admissions.

| Variable | full-pop SMD | locked SMD | note |
|---|--:|--:|---|
| Race | +0.326 | **+0.307** | survives — not a window artifact |
| Insurance | +0.175 | +0.235 | grew |
| Admission type | +0.406 | +0.337 | shrank (obs stays partly removed) |
| Length of stay | +0.180 | +0.112 | shrank (short stays removed) |
| Distinct diagnoses | +0.679 | +0.545 | shrank, still large |
| Age | −0.032 | −0.187 | moved (code+ now clearly younger) |
| Availability: ALT/AST/ALP/bilirubin | ~+0.58–0.60 | **~+0.47** | survive strongly |
| Availability: albumin | +0.470 | +0.348 | shrank |
| Availability: glucose | +0.319 | +0.129 | largely collapsed |
| Availability: platelets | +0.261 | +0.106 | largely collapsed |
| Availability: HbA1c / triglycerides | +0.106 / +0.108 | +0.047 / +0.058 | shrank |

## What the analysis population becomes

**373,992 admissions / 161,119 subjects (5,740 code-positive, 368,252
code-negative)**, defined solely by note presence (no temporal window imposed;
the ~1,100-admission sparse tail is negligible and not cut). All downstream
tables (Table 1–S1) are regenerated on this population; Table 0 records the flow.
