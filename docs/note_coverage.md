# Note Coverage Window — MIMIC-IV-Note 2.2 vs hosp v3.1

**Question resolved:** empirically, which analysis-population admissions have a
linked clinical note, and what analysable window does that imply. This fills the
PENDING row in [Table 0](tables/table0.md).

Linkage is by `hadm_id` (admission grain). No note text was read — only
`subject_id`, `hadm_id`, and `length(text)`. Reproducers: `scripts/note_schema.py`,
`scripts/note_coverage.py`.

## Note tables (scale)

| table | notes | distinct subj | distinct hadm | NULL hadm_id |
|---|--:|--:|--:|--:|
| discharge | 331,793 | 145,914 | 331,793 | 0 |
| radiology | 2,321,355 | 237,427 | 309,670 | 1,176,597 (50.7%) |

discharge = one `DS` note per admission. radiology = `RR` (2.30M) + `AR` addenda
(25,720). Discharge text is large (median 9,847 chars, p95 18,619, max 60,381 ≈
~15k tokens) → long-context handling required; radiology is short (median 781).

## Coverage of the 545,497 analysis admissions

| population | ≥1 discharge | ≥1 radiology | either | neither |
|---|--:|--:|--:|--:|
| All (n=545,497) | 331,604 (60.8%) | 309,444 (56.7%) | **373,992 (68.6%)** | 171,505 (31.4%) |
| Code-positive (n=9,143) | 5,552 (60.7%) | 4,826 (52.8%) | **5,740 (62.8%)** | 3,403 (37.2%) |

Subject-level (any admission with a note), n=223,291 analysis subjects:
either **161,119 (72.2%)**; code-positive subjects either 3,675 (65.9%).

## The window is temporal and hard-edged

| anchor_year_group | n adm | discharge % | radiology % | either % |
|---|--:|--:|--:|--:|
| 2008–2010 | 227,398 | 65.8 | 64.5 | 76.4 |
| 2011–2013 | 114,842 | 67.5 | 61.3 | 75.1 |
| 2014–2016 | 91,038 | 67.5 | 60.1 | 74.0 |
| 2017–2019 | 69,805 | 61.6 | 54.0 | 66.8 |
| **2020–2022** | **42,414** | **0.0** | **0.0** | **0.0** |

**MIMIC-IV-Note 2.2 covers admissions through ~2019; the 2020–2022 group has
ZERO notes** (it postdates the note release built against MIMIC-IV 2.2). The
analysable window is therefore **anchor_year_group 2008–2019**.

Two caveats within the window: (1) coverage is **not** 100% even in covered years
(~74–76% either-note in 2008–2016) — short observation stays, in-hospital deaths,
and transfers often lack a discharge summary; (2) the code-positive breakdown
shows the same cliff (2020–2022 = 0%).

## Differential loss — an Aim 1c threat

**By coding status:** code-positive admissions retain **62.8%** either-note vs
**68.6%** overall — a **5.8-point** differential. Cause: code-positive admissions
are over-represented in the uncovered 2020–2022 window (1,137/9,143 = 12.4% of
code-positive vs 42,414/545,497 = 7.8% overall). Requiring a note therefore drops
**37.2% of code-positive** admissions vs 31.4% overall.

**By insurance (either-note %, code− vs code+):** Medicare 74.0 vs **62.1**
(11.9-pt gap), Private 66.5 vs 66.8 (none), Medicaid 60.6 vs 57.2. Medicare
code-positive admissions lose the most.

**By race (either-note %, code− vs code+):** gaps vary and small cells are noisy,
but several strata show large code-positive coverage deficits, e.g. UNABLE TO
OBTAIN 40.3→26.2, UNKNOWN 70.4→56.9, ASIAN 59.8→49.2, HISPANIC/LATINO – CUBAN
67.7→37.5, BLACK/CAPE VERDEAN 64.7→46.9. A few go the other way (HISPANIC OR
LATINO 74.3→90.0). Direction is inconsistent but the magnitude in several groups
is large enough to bias 1c subgroup estimates.

**Implication:** the note restriction is **not missing-completely-at-random** — it
removes code-positive admissions and certain payer/demographic strata
preferentially. Aim 1c (equity audit of differential recovery) must account for
this (e.g., restrict to the 2008–2019 window before analysis, and/or model the
note-availability selection), or the "recovery" it measures will be confounded by
who happens to fall in the note-covered window.

## Outpatient radiology (NULL hadm_id) — preserved, not discarded

**1,176,597 radiology notes (50.7%) have NULL `hadm_id`** — outpatient imaging,
**not** linkage failures. They span **188,882 distinct subjects, of whom 117,163
are in the analysis population**. Because incidental steatosis on outpatient
imaging is central to this study, these are retained; they can be linked to
patients by `subject_id` (+ time), not to a specific admission by `hadm_id`.

## What the analysis population becomes

Requiring **≥1 linked note (discharge OR radiology)** reduces the analysis
population from **545,497 → 373,992 admissions** (−171,505), of which **5,740 are
MASLD code-positive** (down from 9,143) and 368,252 code-negative;
**161,119 distinct subjects**. Restricting to discharge notes only would give
331,604 admissions. Either way the **effective study window is 2008–2019**, and
the restriction is **differential by coding status and by insurance/race** — a
documented threat to Aim 1c, not a neutral filter.
