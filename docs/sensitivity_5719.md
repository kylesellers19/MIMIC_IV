# Sensitivity — ICD-9 571.9 in the code-positive set (Phase 4.1, run_2026-09-19)

Produced by `scripts/run0919_sens_5719.py`; every number below is read from `docs/run_2026-09-19/results/sens_5719.json`. **The primary definition is unchanged.** This page computes what would change if 571.9 were dropped; the decision is Kyle's (see `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`).

## Background

The 2021 expert-panel consensus on administrative coding for fatty liver research (Hagström et al., Hepatology 2021;74(1):474–482, doi:10.1002/hep.31726, PMID 33486773) lists ICD-9 571.8 and ICD-10 K76.0 for the disease overall and ICD-10 K75.8 for steatohepatitis with no ICD-9 equivalent. This project's K75.81 is the ICD-10-CM subdivision of K75.8, so it is consistent with that table. ICD-9 571.9 ("unspecified chronic liver disease without mention of alcohol") is **not** in the consensus table but **is** in this project's pre-specified code set (`sql/masld_coded.sql`).

## How much of the code-positive set rests on 571.9 alone

- Admissions code-positive **solely** through 571.9 (no K76.0, K75.81 or 571.8 on the same admission): **40** admissions, 38 subjects.
- Admissions carrying 571.9 at all: 42.
- Code-positive count: 5,740 now → 5,700 with 571.9 removed.

## Where the solely-571.9 admissions fall, and the 2×2 with 571.9 removed

| definition | variant | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− | recovery share % | corroboration share % |
| --- | --- | --: | --: | --: | --: | --: | --: |
| (a) v1.1.0 inpatient | current | 4,805 | 13,612 | 935 | 354,640 | 73.91 | 83.71 |
| (a) v1.1.0 inpatient | 571.9 removed | 4,798 | 13,619 | 902 | 354,673 | 73.95 | 84.18 |
| (b) PRIMARY −365/+30 | current | 5,027 | 22,799 | 713 | 345,453 | 81.93 | 87.58 |
| (b) PRIMARY −365/+30 | 571.9 removed | 5,015 | 22,811 | 685 | 345,481 | 81.98 | 87.98 |
| (c) −90/+30 | current | 4,908 | 17,851 | 832 | 350,401 | 78.43 | 85.51 |
| (c) −90/+30 | 571.9 removed | 4,899 | 17,860 | 801 | 350,432 | 78.47 | 85.95 |
| (d) v1.0.0 inpatient | current | 4,850 | 22,443 | 890 | 345,809 | 82.23 | 84.49 |
| (d) v1.0.0 inpatient | 571.9 removed | 4,843 | 22,450 | 857 | 345,842 | 82.26 | 84.96 |

Solely-571.9 admissions by cell (they move A→B or C→D when the code is dropped):

| definition | in A (would move to B) | in C (would move to D) |
| --- | --: | --: |
| (a) v1.1.0 inpatient | 7 | 33 |
| (b) PRIMARY −365/+30 | 12 | 28 |
| (c) −90/+30 | 9 | 31 |
| (d) v1.0.0 inpatient | 7 | 33 |

## Effect on the 400-chart sample

- Sampled charts that would change cell: **1–10** (A→B: 0; C→D: 1–10). Counts below 11 are written as a range; the exact values are in the untracked private folder.
- Revised allocation and weights if 571.9 were dropped (definition b; weight = N_pop(cell)/n_sample(cell)):

| cell | current n | current weight | revised n | revised weight |
| --- | --: | --: | --: | --: |
| code+/note+ | 80 | 62.8375 | 80 | 62.6875 |
| code-/note+ | 150 | 151.9933 | 150 | 152.0733 |
| code+/note- | 70 | 10.1857 | 66 | 10.3788 |
| code-/note- | 100 | 3454.53 | 104 | 3321.9327 |

## What this means

Dropping 571.9 changes the code-positive count by well under one percent and moves the recovery and corroboration shares by a few hundredths to a few tenths of a point. The practical stake is not the 2×2 but the sample: a handful of already-drawn charts would change cell, and with them their sampling weights. Because weights are fixed at sampling time, this must be settled **before adjudication begins**. The decision and its options are in the decisions file.

