# Phase 6 — reference-standard machinery: notes for the lead

Written by `scripts/run0919_phase6_docs.py` (`phase6_notes()`); numbers are read from the results JSONs named in each section. Test line: `29 passed in 1.42s`.

## 6.1 Estimator and precision forecast

**Purpose.** Turn a completed adjudication file into the headline Aim 1a number (of adjudicated steatosis-positive admissions, the population-weighted share that codes missed) with honest uncertainty, plus the note rule's PPV and sensitivity and reviewer agreement — before any chart is reviewed, so the arithmetic is fixed in advance and its precision is known.

**What was done.** `scripts/aim1a_estimator.py` (joins reviewer forms to the master key by review_id inside the script; outputs aggregates only), `tests/test_aim1a_estimator.py`, `scripts/run0919_precision_forecast.py` → `results/aim1a_precision_forecast.json` and `docs/aim1a_precision_forecast.md`. Bootstrap = multinomial redraw of each cell's (positive, negative, insufficient) counts, which is exactly what resampling rows within a cell gives for these statistics; linearized (delta-method) SE with per-cell variance shares and a logit-scale interval; Cohen's kappa (binary; Insufficient excluded and counted negative) and weighted kappa (linear and quadratic) on the four ordinal levels from pre-consensus rows; by-cell Wilson intervals; by-stratum estimates for any `--group-col` when the stratum has ≥ 11 adjudicated charts.

**Results.** Hand target (x = 76/128/35/1): under-capture 81.698%, PPV 87.08%, sensitivity 86.409% — exact. Reference row (PPV_B = 0.85) closed form [79.06, 81.65, 83.67, 85.28, 87.72] = expected [79.06, 81.65, 83.67, 85.28, 87.72]: match True. Simulated means match the exact expectation of the estimator within 1.94 MC standard errors (largest scenario); the exact expectation sits up to 0.52 points below the plug-in closed form (Jensen; the estimator is concave in x_D). Bootstrap coverage 63.2–65.1% at 1 positive per 100 in D, 91.5–92.8% at ≥ 3; cell D carries 91.8–97.1% of the variance once D ≥ 3 per 100; one extra D positive shifts the estimate by 0.85–3.1 points.

**Checks passed.** `29 passed in 1.42s` (hand targets exact; Insufficient two ways; bootstrap SD vs linearized SE within 10%; kappa on a hand-computed 2×2 = 0.4; end-to-end run on synthetic forms with a synthetic key recovers the hand target, excludes an unresolved disagreement, applies the <11 rule, and emits no identifier).

**Deviations.** (1) The run file says the simulated mean must match the closed form within MC error; it matches the *exact expectation* within MC error and the closed form only to within the Jensen bias (< 0.6 points), which is a property of the ratio estimator, reported in the doc rather than hidden. (2) The linearized normal interval can exceed 100% when x_D ≤ 1; the JSON also carries a logit-scale interval.

**What Kyle should look at.** The D = 1 rows of `docs/aim1a_precision_forecast.md` (coverage collapses when no positive is seen in D) → `phase6_decisions.md` P6-05; the Insufficient handling (P6-01); the disagreement-resolution mechanism (P6-02).

## 6.2 Packet specification and feasibility

**Purpose.** Confirm, against the data, that every element criteria §1 promises can actually be assembled for the 400 sampled admissions, say what MIMIC cannot supply, and size the reading burden per cell.

**What was done.** `scripts/run0919_packet_feasibility.py` → `results/packet_feasibility.json`; `docs/adjudication/packet_specification.md` written by `scripts/run0919_phase6_docs.py`. Notes come from the per-note index (no text read); labs, omr and prescriptions via DuckDB filters on the raw .csv.gz.

**Results (n = 400).** Discharge summary present 89.2%; any radiology 95.8% (liver-inclusive 60.5%); ≥ 1 prescription 92.5%; BMI in window 71.5%, BP 66.8%. Labs: platelets and glucose ≈ 84% / 83%, ALT/AST ≈ 52%, HbA1c 6.0%, HDL 6.8%. Discharge summary median 9,515 chars (p95 19,627); radiology reports median 5 (p95 18); per-cell table in the doc. Not suppliable: quantified alcohol, biopsy as a structured source, waist circumference, coded diagnoses (stripped by design).

**Checks passed.** All 420 charts (400 + 20 training) found in the locked population with admittime; per-cell n = 80/150/70/100.

**Deviations.** None. Tier 1: the in-admission lab definition (hadm_id-linked OR same subject with charttime inside the stay) is recorded in the JSON; it differs from hadm_id-only by < 1 point per analyte.

**What Kyle should look at.** §3 of the packet specification (not suppliable) against criteria §6a–6c; the by-cell discharge-summary availability (cell A is near-complete, C and D lower), which bears on how often 'Insufficient information' will be chosen.

## 6.3 Adjudication instrument

**Purpose.** A blank form reviewers can fill without ever seeing cell, weight or double-review status.

**What was done.** `scripts/make_adjudication_template.py` → `docs/adjudication/adjudication_template.xlsx` (sheets README / sample / training / lists; openpyxl list validation on every categorical column, whole-number validation on minutes; ID column locked, sheet protection without password) and `docs/adjudication/data_dictionary.md`.

**Results.** 400 sample rows in master-key order (not reordered by cell), 20 training rows, 11 columns exactly as criteria §7.

**Checks passed.** `verify_commit_safe()` scans every cell of the workbook: no integer longer than 4 digits, no cell label, no 'double' token.

**Deviations.** 'Not applicable' added to temporality / 6a / 6b / 6c so that a skipped secondary question is distinguishable from a forgotten one (Tier 1). 6b uses the Draft 1 g/week bands → P6-04.

**What Kyle should look at.** Open the template once; check the option wording against the clinician's D1/D6 decisions before the training round.

## 6.4 Reviewer assignment

**Purpose.** Split the 400 charts between two reviewers with the double-review subset hidden and the order uninformative.

**What was done.** `scripts/assign_reviewers.py` (seed 20260921) → untracked `data/processed/adjudication/reviewer_assignment.parquet` and `form_reviewer1.xlsx` / `form_reviewer2.xlsx`; tracked `results/reviewer_assignment.json` and `docs/adjudication/reviewer_assignment.md`.

**Results.** 250 / 250 charts per reviewer, 100 shared, 500 adjudications; per-cell counts per reviewer in the doc; Spearman(order, cell) -0.01 / 0.038.

**Checks passed.** Exactly 250 each; every double-review ID on both forms; every single-review ID on exactly one; per-cell single-review split differs by ≤ 1; orders are permutations of 1..250; forms pass the commit-safety scan.

**Deviations.** None. Only two reviewers implemented; other values are refused so the design is re-derived deliberately.

**What Kyle should look at.** Nothing until reviewers are named; the doc says it is revisable.

## 6.5 Packet generator and dry run

**Purpose.** Build the per-chart packets exactly as criteria §1 allows, prove by automated checks that nothing else leaks, and leave no packets on disk.

**What was done.** `scripts/make_reviewer_packets.py --dryrun` → `results/packet_dryrun.json`; packets are plain text with delimited note blocks so checks can separate narrative from structured text; the dry-run directory was removed by `shutil.rmtree` after `assert path == os.path.abspath('data/processed/_packet_dryrun')` (removed: True).

**Results.** 420 of 420 files, exceptions none, median 21,127 bytes, load 81.2 s + generate 4.1 s. Structured-text leak checks: long titles 0, demographic labels 0, 8-digit integers 0, cell labels 0, markup 0, own identifiers 0; ICD-9-shaped numbers after removing value columns and signed day offsets 0; ICD-10-shaped tokens 20 (token table in the doc — drug-name fragments, to be grepped at final generation). Narrative-only hits: 'recovery' 65, markup 238, long titles <11, 8-digit 0, own identifiers 0.

**Checks passed.** Discharge text verbatim: 420/420 charts match the per-note index character count; `data/processed/_packet_dryrun/` absent after the run; nothing printed but counts.

**Deviations.** The raw regex (i) fires on lab values and signed day offsets by construction; the doc reports the raw count as specified and the refined counts beside it. Check (vii) (own hadm_id / subject_id / note_id substrings) was added beyond the six requested.

**What Kyle should look at.** The token table in packet_specification.md §5; the final-generation command in §6 (run only after the criteria are frozen and reviewers are credentialed).

## 6.6 Reviewer brief

**Purpose.** One page a clinician can read cold.

**What was done.** `docs/adjudication/reviewer_brief.md` templated by `scripts/run0919_phase6_docs.py` from `results/packet_feasibility.json`, `results/reviewer_assignment.json` and `results/reviewer_brief.json` (the hours arithmetic, with its assumptions, is stored there).

**Results.** Assuming 6 chars/word, 200–250 wpm and 5 min overhead: full read 18–21 min/chart → 74–87 h per reviewer for 250 charts; focused read (discharge summary + liver-inclusive radiology) 14–16 min → 58–67 h. Called rough in the brief; the training round measures the real figure.

**Checks passed.** No number in the brief is typed by hand.

**Deviations.** The earlier analyst guess in the criteria doc (10–18 min/chart) is below the full-read figure here because it predates the confirmed radiology volume; both are shown to the reviewer as rough.

**What Kyle should look at.** The DUA paragraph wording; whether the focused-read strategy is acceptable to the clinician (it changes what 'the packet was read' means).

## Housekeeping

Untracked outputs under `data/processed/adjudication/` (assignment parquet, two forms). No packets remain on disk. Nothing under `data/`, `models/` or `logs/` is tracked. No frozen artifact was touched; `scripts/masld_config.py` was not edited (all seeds used already exist there; the bootstrap and simulation seeds are constants in the new scripts). Tier 3 items: `phase6_decisions.md`. Blockers: none (`phase6_blockers.md`).
