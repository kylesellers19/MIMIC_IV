# Run log — run_2026-09-19

Append-only narrative for the autonomous run launched 2026-09-19 (branch `run/2026-09-19`).
Each phase is written as: Purpose → What was done → Results (aggregate) → Checks passed → Deviations → What Kyle should look at.
Every number here is produced by a script into a results file under `docs/run_2026-09-19/results/` or `docs/**/results/`; the producing script and file are named beside each table.

Parameters: TOTAL_BUDGET_HOURS=14, EMBED_BUDGET_HOURS=5, FINETUNE_BUDGET_HOURS=0, BOOTSTRAP_REPS=500, CELL_FLOOR=11,
SEED_TRAINING_DRAW=20260919, SEED_SPLIT=20260920, SEED_REVIEWER_ASSIGN=20260921, SEED_NOTES_SUBSAMPLE=20260922.

---

## Phase 0 — Preflight, integrity gate, inventory

**Purpose.** Before any analysis runs, confirm the environment is the one this run assumes: the frozen artifacts (note rule, ICD list, population, sample) are unchanged, the anchor numbers from earlier sessions reproduce exactly, tests pass, and the permissions the run will need (git, Python, network, background jobs) work while Kyle is still at the desk.

**What was done.** (filled in as steps complete)

- 16:13 UTC: `git status --short` clean; BASE_BRANCH = `main`. Python 3.14.4, DuckDB 1.5.4, pip 26.1.2.
- Permissions exercised: git (branch, commit), venv Python, pip, HTTPS HEAD to pypi.org / huggingface.co / eutils.ncbi.nlm.nih.gov (200 / 200 / 405 — the 405 is "HEAD not allowed", the host is reachable) → NETWORK=true; a trivial `nohup sleep 5` background job ran and was polled. `logs/` and `models/` were not git-ignored; both appended to `.gitignore`.
- **0.2 Frozen-artifact hashes** → `docs/run_2026-09-19/results/frozen_hashes_start.json` (script `scripts/run0919_integrity_gate.py`). The master key is `data/processed/aim1a_sample.parquet` itself (columns review_id, hadm_id, subject_id, cell, double_review, weight); no separate key file exists. Tags: `note-phenotype-v1.0.0`, `note-phenotype-v1.1.0`.
  - `git diff --quiet note-phenotype-v1.1.0 -- scripts/note_phenotype.py` **reports a difference**. Inspected: the only change since the tag is commit eee89ea (the 2×2 build), which replaced the hard-coded population path with `from scripts.masld_config import CLEAN_POP as POP` (2 lines added, 1 removed). Lexicon, context handling, and classifier logic are byte-identical to the tag. This is the CLEAN_POP repoint that this run file itself requires of every script, so it is recorded as a known post-tag change, not a rule change. The tag itself is untouched.
- **0.3 Integrity gate** → `docs/run_2026-09-19/results/integrity_gate.json`. All 14 checks pass: population 373,992 / 161,119; code-positive 5,740; all four 2×2 definitions (a)–(d) cell-for-cell; note-positive 27,826; recovery 81.9%; corroboration 87.6%; allocation 150/80/70/100; weights; every sampled chart's stored cell matches the frame under definition (b); 100 double-review flags. Imaging-observed 138,603 is confirmed against `docs/imaging_denominator.md` (no per-admission derivative is stored; it is re-derived in Phase 7 by the same exam-name rule). **DATA_GATE = passed.**
  - `pytest -q` initially collected **0 tests**: the project's test file `scripts/test_note_phenotype.py` is a plain script (23 synthetic cases), not pytest-discoverable. Run directly with the repo on `PYTHONPATH` it reports 23/23 passed. A thin wrapper `tests/test_note_rule_cases.py` (plus `tests/conftest.py`) parametrizes over the frozen file's CASES list by parsing it — the frozen file is not modified. `pytest -q` now reports 23 passed.
- **0.4 Inventory** (names/sizes only). `data/raw/` 4.9 GB (hosp: 8 tables; note: 4 tables; `ed/` is an empty directory — nothing to verify). `data/processed/` 33 MB: `aim1a_frame.parquet` (373,992 rows; per-admission code status, note_a–d, covariates, lab-availability flags), `aim1a_sample.parquet` (400 rows, master key), `analysis_population.parquet`, `analysis_population_clean.parquet`, `cmrf.parquet` (cmrf_ge1, alcohol, viral, other_etio, cirrhosis, hcc), `note_historical.parquet`. No `models/`. `docs/tables/*.csv` exist on disk but `*.csv` is globally git-ignored, so only the `.md` tables are tracked.
  - **Prompt A (criteria + packet spec + feasibility): verified-existing.** `docs/adjudication_criteria.md` holds DRAFT 1 with inline `[CLINICIAN]` flags and a collated D1–D8 table; `docs/reference_standard.md` §2 links to it; §1 of the criteria lists packet contents; a data-informed time estimate is present. What is *not* there: a field list confirmed against the data and per-cell reading burden — those are Phase 6.2. Phase 1.2 is therefore skipped.
  - **Prompt B (`docs/aim1b_structured.md`): not run. Prompt C (`docs/manuscript_methods_draft.md`): not run.**
- **0.5 Environment.** Python 3.14.4 (Homebrew), arm64 Apple M1 Max, 10 cores, 32 GB RAM, 711 GB free (≥15 GB → transformer part allowed). Only duckdb/pandas/numpy/pyarrow were installed; all other allow-listed packages installed one at a time into `.venv` (log `logs/run_2026-09-19/pip_install.log`, all OK). `requirements-run_2026-09-19.txt` written from `pip freeze`.
  - **LightGBM and XGBoost wheels link against `@rpath/libomp.dylib`, which is absent system-wide** (no Homebrew installs allowed). Both load correctly when `DYLD_LIBRARY_PATH` points at the libomp bundled inside the torch wheel (`.venv/.../torch/lib`). Tier 1: modeling scripts are launched through `scripts/run0919_env.sh`, which sets that variable. No system change.
  - **torch 2.11.0: MPS is built but `is_available()` is False on macOS 13.3.1** (this torch requires a newer macOS for MPS). TORCH_DEVICE = cpu. The Phase 3 pilot decides whether CPU throughput fits the embedding budget.
  - CatBoost 1.2.10, XGBoost, LightGBM, shap 0.52, scikit-learn 1.9.1, statsmodels 0.15, comorbidipy 0.8.0, transformers 5.17 all import.
- **Tier 1 decisions logged:** (i) tracked tables are Markdown + JSON under `docs/**/results/` because `*.csv` is git-ignored project-wide; (ii) pytest wrapper as above; (iii) libomp via DYLD_LIBRARY_PATH.

**Checks passed.** Gate 14/14; tests 23/23; tree clean at start; nothing under data/, models/, logs/ staged.

**Deviations.** None from the plan. Three environment notes above (tag diff explained, MPS unavailable, libomp workaround).

**What Kyle should look at.** `results/integrity_gate.json`; the note about the two-line post-tag change to `note_phenotype.py` (decide whether to re-tag as v1.1.1 later — no tag was created here).

## Phase 1 — Pre-specification commit

**Purpose.** The project's discipline is that definitions and expectations are committed before the numbers they govern exist, so nobody can later claim a hypothesis was written after seeing a result. The 7 September hypotheses lived only in chat; this phase puts them in the repository with a timestamp.

**What was done.** `docs/analysis_plan_prespecified.md` written with the seven hypotheses verbatim, a 14-row sensitivity registry (six existing, eight added by this run), the seven dated amendments (a)–(g) each carrying "no result from this analysis had been seen when it was added", and the run parameters. Committed as `e2a4e1e` (recorded in STATE.json as `phase1_commit`). No tag.

**Deviations.** 1.2 (Appendix A into the reference standard) skipped: Phase 0.4 found Draft 1 already stored in `docs/adjudication_criteria.md` with every `[CLINICIAN]` flag inline and linked from `docs/reference_standard.md` §2.

**What Kyle should look at.** The amendment list in §3 — especially (g), the covariate list for the exploratory GEE model, since it is now fixed.

## Phase 2 — Reviewer-training draw and subject-level splits with a gold holdout

**Purpose.** The 400 adjudicated charts will validate every model. If a model has seen those patients during training, even under silver labels, the validation is contaminated. So every subject who appears in the chart-review sample or the 20-chart training set is removed from all model fitting before any model exists. Splitting by subject (not admission) matters because one person can have many admissions; putting some in DEV and some in TEST would let the model memorize the person.

**What was done.** `scripts/run0919_phase2_splits.py`. (2.1) Twenty admissions drawn under definition (b) in proportion to the main sample (B 8 / A 4 / C 3 / D 5), excluding every subject with any admission in the 400-chart sample, seed 20260919, blinded IDs T001–T020 after a seeded shuffle; key at `data/processed/aim1a_training_key.parquet` (untracked); aggregate doc `docs/adjudication/training_draw.md`. (2.2) GOLD_SUBJECTS = subjects in the sample or the training set; their admissions form GOLD_HOLDOUT. Remaining subjects: 20% TEST, 80% DEV in five subject-level folds, seed 20260920. `data/processed/splits_v1.parquet` (untracked). Constants appended to `scripts/masld_config.py`.

**Results** (`docs/run_2026-09-19/results/phase2_splits.json`; doc `docs/aim1b_splits.md`).

| partition | admissions | subjects | silver prevalence % |
| --- | --: | --: | --: |
| GOLD_HOLDOUT | 2,865 | 411 | 40.52 |
| TEST | 75,124 | 32,142 | 7.22 |
| DEV | 296,003 | 128,566 | 7.18 |

GOLD_HOLDOUT prevalence is high by design (the sample over-draws note-positive cells). DEV and TEST prevalences agree to a tenth of a point, as expected from a random subject split.

**Checks passed.** Zero subject overlap between partitions and between folds (asserted); all 400 sampled and 20 training subjects are in GOLD_HOLDOUT (asserted); no training subject overlaps the sample (asserted).

**Deviations.** None.

**What Kyle should look at.** `docs/aim1b_splits.md`. The training-draw allocation is revisable.

## Phase 3 — Notes text preparation and background embedding job (stage 1 launched)

**Purpose.** The notes arm needs each admission's text in a form a transformer can read. Stage 1 is a single streaming pass over every note that records per-note flags and lengths only (no text) — it also serves Phases 4.3 and 4.4, which need per-note Tier C and discharge-linkage facts that no stored derivative holds. Stage 2 (subsample text assembly, masking, pilot, encoding) follows once the splits exist and stage 1 is done.

**What was done.** `scripts/run0919_notes_index.py` launched in the background (log `logs/run_2026-09-19/notes_index.log`; output `data/processed/run_2026-09-19_notes_index/`, untracked). Row-level exceptions are counted by class only.

## Phase 4 — Aim 1a loose ends

**Purpose.** Six pre-specified checks that were pending: whether one ICD-9 code (571.9) that the consensus table omits matters; whether the hand-written Charlson index is right and whether it leaks the code axis; two population/definition sensitivities (discharge-only; hedged mentions positive); exact cohort-flow counts; and whether availability gaps between groups shrink when the outpatient window widens (if they do not, the gap is about access, not encounter type).

**What was done.** Scripts `run0919_sens_5719.py`, `run0919_charlson_validation.py`, `run0919_loose_ends_43_44.py`, `run0919_cohort_flow.py`, `run0919_outpt_labs.py` + `run0919_avail_windows.py`. Docs `docs/sensitivity_5719.md`, `docs/charlson_validation.md`, `docs/aim1a_loose_ends.md`. Registry rows S7–S11 in the pre-specified plan now point to these outputs.

**Results (aggregate; results JSONs under `docs/run_2026-09-19/results/`).**
- 4.1 · 571.9: only 40 admissions (38 subjects) are code-positive solely through 571.9. Primary 2×2 with it removed: A 5,015 · B 22,811 · C 685 · D 345,481 (recovery 81.98% vs 81.93%; corroboration 87.98% vs 87.58%). Between 1 and 10 sampled charts would change cell (exact count in the private folder). → **D-01** in the decisions file.
- 4.2 · Charlson: the project's index and comorbidipy (Quan mapping, Charlson 1987 weights) agree on **100.0%** of 373,992 admissions. The leak is real: K76.0, 571.8 and 571.9 all fall in Quan's mild-liver category. The recovery-zone-vs-concordant SMD of −0.356 reproduces exactly under both implementations and **collapses to +0.004** once the two liver categories are removed — the entire comorbidity gap between the recovery zone and the concordant cell was the phenotype code itself. `charlson_noliver` is stored for modeling.
- 4.3 · Discharge-only population: 331,604 admissions; under (b) recovery 81.06%, corroboration 88.94%.
- 4.4 · Tier C positive: adds 575 admissions under (b); recovery 82.23%, corroboration 87.94%. The per-note index rebuilt the frozen frame's note status exactly (0 mismatches).
- 4.5 · Flow: 546,028 → −531 → 545,497 → −100,029 (subject absent from the note module) −71,476 (subject has notes elsewhere, none on this admission) → 373,992. The two parts sum to 171,505. The run file's "outside the covered window" framing does not apply: the project found no admission-year window; both framings are reported. Two doc disagreements flagged, not resolved: `note_coverage.md` (superseded window claim) vs `analysis_population.md`/`table0.md`; and a one-admission discrepancy in table0's 2020–2022 subtotal.
- 4.6 · Availability differentials: for most analytes and for imaging, the largest between-stratum |SMD| does **not** shrink when the window widens from 90 to 365 days (by insurance, ALT 0.334 → 0.461; HDL 0.076 → 0.313); the one exception is platelets by insurance. That points to access rather than encounter type; no further interpretation is offered.

**Checks passed.** 571.9 decomposition reproduces the 5,740 total; Charlson 100% agreement; index-vs-frame 0 mismatches; flow sum check true; locked count equals CLEAN_POP.

**Deviations.** Availability under a window includes outpatient laboratory results (hadm_id null) for the ten analytes — the run file did not say how "availability under a window" should treat labs; this is the natural reading and is stated in the doc (Tier 1).

**What Kyle should look at.** `docs/charlson_validation.md` §2–3 (the −0.356 was the code); `docs/sensitivity_5719.md`; the two flagged doc disagreements in `docs/aim1a_loose_ends.md` §4.5.

## Phase 5 — Aim 1c, level 1: equity of recovery at the computable stage

**Purpose.** Stratum-level recovery and corroboration shares had never been computed. This asks whether the gap between notes and codes is the same size in every group, with honest uncertainty: counts first, cluster-bootstrap intervals, floors instead of merging, and a plain statement where an interval is too wide to support a claim.

**What was done.** `scripts/run0919_aim1c_level1.py` (after the Phase 1 hash existed). Strata: race as recorded (33 levels, never collapsed), insurance, sex, language as recorded, age band. Subject-cluster bootstrap, 500 replicates, seed 20260919. Floors B ≥ 11 and A + C ≥ 11. A CI wider than 20 percentage points is marked as not supporting a claim (analyst threshold, stated in the doc). One-vs-rest SMD of the coding rate among note-positive admissions. Mechanism measures by stratum (ALT/HbA1c/triglyceride/HDL availability, liver-inclusive imaging in window, CMRF unascertainable). Sensitivity column with 571.9 removed. One exploratory GEE (covariates fixed in amendment g) — fit on all 27,826 note-positive admissions without restriction. Outputs `docs/aim1c_level1.md`, `docs/tables/aim1c_level1_<stratum>.md`, results JSON.

**Results (headline; see the doc for every stratum).** Recovery share is between about 73% and 88% in every analyzable stratum. Race: 33 of 33 levels analyzable, 21 with a CI narrow enough to support a claim; WHITE 82.4% (81.5–83.2), BLACK/AFRICAN AMERICAN 85.7% (84.1–87.1), HISPANIC/LATINO – PUERTO RICAN 72.6% (68.0–76.5; coding-rate SMD +0.23 vs rest). Insurance: Medicare 82.2, Private 80.2, Medicaid 83.6, Other 85.6 (all CIs ≤ 3 points wide). Sex: M 82.7, F 81.1. Language: 17 of 26 analyzable, 10 claim-supported; Spanish 77.8 (74.4–80.8). Age: 89+ corroboration 72.6% with a 32-point interval — reported as not supporting a claim. The direction is not uniform: some groups with thinner structured records have higher recovery shares (more of their documented steatosis is uncoded) and some lower.

**Checks passed.** Every stratum's four cells are printed before any rate; floors applied; GEE converged.

**Deviations.** None. Levels 2 and 3 not attempted (need gold standard and models).

**What Kyle should look at.** `docs/aim1c_level1.md` — the race and language tables and the exploratory GEE.

### Phase 3, stage 2 — text assembly, variants, pilot, encoding job (launched)

**What was done (Tier 1 choices, with reasons).**
- Text assembly (`scripts/run0919_notes_text.py`): per admission, under the primary linkage — discharge summary + inpatient radiology + the subject's outpatient radiology within −365/+30 days. Priority order: liver-inclusive radiology reports in full (classification = the imaging-denominator exam-name rule, joined from the per-note index), then other radiology reports' IMPRESSION section, then discharge-summary sections in this order — Discharge Diagnosis, Past Medical History, Pertinent Results, Brief Hospital Course, History of Present Illness, Chief Complaint, Impression, Abdomen, Social History, Major Surgical Procedure, Physical Exam — then remaining sections in document order with boilerplate skipped (name/dates/allergies/discharge instructions/medication lists/follow-up/disposition/mental-status blocks). Reason: the corpus-exploration section table shows the steatosis-bearing sections (Pertinent Results, PMH, Brief Hospital Course, HPI) have medians of 144–1,284 characters and p95s of 0.8–4.1k, so a 22,000-character budget (≈ 12 chunks × 512 tokens at ~3.6 characters/token for clinical text) fits them in full for nearly every admission; only 7.2% of assembled texts hit the budget.
- Variants: U unmasked; M every lexicon regex match (all tiers, any assertion status) → `[MASK]`; S every sentence (frozen rule's sentence splitter) containing any lexicon match deleted. Lexicon and splitter are imported from `scripts/note_phenotype.py`.
- Subsample: simple random sample of 13,000 DEV+TEST **subjects** (seed 20260922) → 29,980 admissions, plus all 2,865 GOLD_HOLDOUT admissions = 32,845. Sized from the pilot: 200 DEV admissions, variant S, Bio_ClinicalBERT on **CPU** (MPS unavailable) → 5,694 tokens/s, 0.539 s per admission (`results/embed_pilot.json`), so the 5-hour budget holds about 33,400 admissions. Subsample summary: DEV 23,816 · TEST 6,164 · GOLD 2,865; median assembled length 9,445 characters; 39% have a liver-inclusive report.
- Encoding (`scripts/run0919_embed.py`): 512-token chunks, stride 64, ≤ 12 chunks; attention-masked mean pooling per chunk; admission vector = concat(mean, max) over chunks = 1,536 dims, float16, shards of 1,000 admissions with an index Parquet under `data/processed/notes_embeddings_v1/S/` (untracked, resumable). Variant U only if budget remains.

**Deviation.** Chunked Bio_ClinicalBERT instead of Clinical-Longformer (methods plan) — laptop hardware, no MPS. Recorded as D-02 in the decisions file.

## Phase 6 — Reference-standard machinery (delegated to a subagent; full narrative in `phase6_notes.md`)

**Purpose.** Everything the chart review needs short of a human reading a chart: the estimator that turns 400 adjudications into the headline number with honest intervals; a simulation showing how precise that number can be; a data-confirmed packet specification and reading burden; the blank instrument; reviewer assignment; a packet generator proven in a dry run and then deleted; and a one-page brief for the reviewers.

**Results (aggregate; details and every number in `docs/aim1a_precision_forecast.md`, `docs/adjudication/*.md`, results JSONs).** Estimator unit tests hit the hand-checked targets exactly (under-capture 81.698%, PPV 87.08%, sensitivity 86.409%); the closed-form reference row for PPV_B = 0.85 reproduces exactly. The simulation's design finding: cell D (100 charts standing for ~345,000 admissions) carries 92–97% of the variance once D-prevalence ≥ 3 per 100, and at 1 per 100 bootstrap coverage drops to ~63–65% because a third of adjudications observe zero D positives (P6-05). Feasibility: discharge summary present in 89% of sampled charts, liver-inclusive imaging 61%, HbA1c 6%, HDL 7%. Reading burden: discharge median 9,515 characters (p95 19,627); a rough 74–87 reviewer-hours per reviewer for 250 charts at 200–250 wpm. Dry run: 420/420 packets generated, structured-field leak checks all zero except 20 ICD-10-shaped tokens that are drug-name fragments in the medication table (flagged for a grep at final generation); directory removed. `pytest -q`: 29 passed.

**Deviations.** The simulated mean matches the exact expectation of the ratio estimator, which sits 0–0.5 points below the plug-in closed form (Jensen); documented, not hidden. Tier 1 choices listed in `phase6_notes.md`.

**What Kyle should look at.** P6-05 in the decisions file; `docs/adjudication/reviewer_brief.md`; the [confirm]-tagged lines in `docs/admin/physionet_403_email_draft.md` (the repo's own record of the 403 problem is thinner than the run file's description).

## Phase 8.1 — TF-IDF development diagnostic (done; 8.2/8.3 await the embeddings)

**Purpose.** Show, cheaply, how much of the silver label a text model recovers by relearning the lexicon (variant U), what the mask token itself gives away (M), and what the *rest* of the documentation carries once every lexicon-bearing sentence is deleted (S). None of this is an accuracy estimate.

**Results** (`docs/aim1b_notes.md`, `results/aim1b_notes_tfidf.json`; subsample DEV 23,816 / TEST 6,164). TEST AUROC / AUPRC, unweighted: U 0.896 / 0.596; M 0.912 / 0.616; S 0.826 / 0.407. U's top positive terms are the lexicon (steatosis, fatty, fatty liver, hepatic steatosis, nash). M's top terms are the mask token and its bigrams — masking every match regardless of assertion status still leaves *the presence of a match* as a feature, which is why M scores as high as U; this is the circularity demonstration in its purest form. S is the interesting row: with every lexicon sentence removed, the remaining text still discriminates (cirrhosis, fibrosis, liver disease, "other forms of" — the company steatosis keeps), which is what a notes model could legitimately learn. Class weighting moves the calibration slope from 1.13 to 0.95 on S.

**Deviation.** None. Vocabulary was fit inside training folds; C fixed at 1 (Tier 1).

## Phase 11.1–11.3 — release readiness (done early, while the model jobs ran)

**Purpose.** The repository had a stale README describing a state before any data existed. Phase 11 makes the repository readable by someone who has never seen it, pins the environment, lists the pipeline in order, tests the new code, and audits the branch for anything that should not be committed.

**What was done.**
- **11.1** `README.md` rewritten: aims and their true status, how to obtain and verify the data (and that access cannot be shared), configuration through the append-only `scripts/masld_config.py`, a 14-stage pipeline table naming each script and the document it writes, and an explicit list of what is tracked versus never tracked. `requirements.txt` regenerated *from* `pip freeze` by a script rather than typed (a first hand-typed version had nine wrong pins and was discarded). `run_pipeline.sh` written as a manifest, deliberately not executable end-to-end: it marks the frozen stages that must not be re-run casually and leaves the final packet generation commented out pending clinician sign-off. No license added — that choice and its timing are **D-03** in the decisions file, with the data use agreement's code-contribution clause quoted.
- **11.2** Three new test modules: text variants (masking and sentence deletion behave identically for affirmed, negated and hedged mentions, so the mask cannot encode the label; masked and deleted text no longer fire the frozen rule; the section parser and priority ordering), metric mathematics (the analytic prior correction is exactly a −log(weight) logit shift, is the identity at weight 1, preserves ranking; weighted metrics respond to weights; calibration slope and intercept recover 1 and 0 on self-consistent predictions and detect systematic overprediction), and invariants over the results files (gate passed, partitions sum to the population, gold holdout covers every adjudication subject, folds disjoint, no phenotype-derived feature reached the models, equity floors respected, flow parts sum, no 8-digit identifier in tracked documents). `pytest -q`: **61 passed**.
- **11.3** `scripts/run0919_final_audit.py` implements checks (a)–(h) and writes `results/final_audit.json`. On its first run it reported two failures; both were inspected rather than suppressed. All 15 flagged 8-digit integers were file sizes in byte-valued fields plus one seed literal in a test, and the two flagged quoted lines were the study's own adjudication question quoted from the criteria document. The **exemption rules were made principled rather than the files edited**: seeds are now discovered by scanning tracked code for `default_rng(...)`/`seed = ...` literals instead of a hard-coded list; byte counts are exempt only when the enclosing JSON key names a size; a quoted line is exempt only when it appears verbatim in one of the study's own instrument documents. All eight checks then pass.

**Checks passed.** 61 tests; audit (a)–(h) all pass; frozen-artifact hashes identical to the start of the run; tags unchanged; no remote; `masld_config.py` +12 lines, −0.

**What Kyle should look at.** `README.md`; **D-03** (license and release timing).

## Phase 7 — Aim 1b, structured arm

**Purpose.** Ask how well routinely collected structured data predicts *documented* hepatic steatosis, and — the point of the exercise — separate how much of that prediction comes from the patient's clinical picture and how much from the documentation process itself (who got tested, imaged, prescribed and written about). The label is the note rule's output, which is known to contain error; every table says so.

**What was done.** `scripts/run0919_features.py` built 52 clinical and 42 availability/volume features, all time-bounded at discharge, reusing the project's own derivations (drug classes and the five cardiometabolic criteria from `cmrf.py`, etiology flags, `charlson_noliver` from Phase 4.2, first/last in-admission laboratory values and pre-admission outpatient HbA1c, triglycerides and HDL). The phenotype codes, the full Charlson index, and every note-rule output are excluded by construction and the exclusion list is published with its reasons. `scripts/run0919_aim1b_structured.py` then trained CatBoost (primary), XGBoost and LightGBM on three feature sets and three imbalance variants, tuned on DEV by subject-level cross-validation with early stopping on an inner split, and touched TEST once. Report: `docs/aim1b_structured.md` (702 lines, organized by the TRIPOD+AI development items), figures in `docs/figures/`.

**Results (TEST, 75,124 admissions; CatBoost unweighted unless stated).**

| feature set | contents | AUROC | AUPRC |
| --- | --- | --: | --: |
| FS-B | clinical values only | 0.787 | 0.282 |
| FS-AVAIL | availability and volume only | 0.812 | 0.245 |
| FS-A | everything | 0.857 | 0.380 |

- **The headline is the middle row.** Knowing only what was measured, imaged, ordered and written — with no clinical value at all — discriminates better than the clinical values do. The silver label is a property of documentation, and the documentation process predicts itself.
- **H1b-i is half borne out.** The single strongest FS-A attribution is whether the liver was imaged at all (mean |SHAP| 0.675, nearly twice the next feature). But only 28% of the top 25 are availability features, and the expectation named *laboratory* availability and diagnosis count specifically; neither is near the top. Age, body-mass index, the overweight criterion and first ALT are the strongest clinical contributors.
- **The calibration amendment (b) is confirmed and the 7 September expectation disconfirmed.** Unweighted models are almost exactly calibrated (intercept +0.03, slope 1.02). Class weighting leaves the slope near 1 but drives the intercept to **−2.38** — a large systematic overprediction of risk, exactly as the amendment anticipated. The analytic prior correction restores the intercept to +0.18 at no cost to discrimination (AUROC unchanged to four decimals, since it is a monotone transform). LightGBM weighted is worse still (slope 3.48).
- **Calibration differs by subgroup where discrimination does not.** 34 subgroup rows are flagged; among unweighted models the substantive ones are slope 0.48–0.77 for BLACK/CAPE VERDEAN and intercept +0.55 to +0.58 for HISPANIC OR LATINO, with AUROC broadly similar. This is the secondary H-calibration expectation borne out.
- **Recovery zone in silver-label form** (code-negative TEST admissions only): FS-A AUROC 0.857, FS-B 0.777, FS-AVAIL 0.817.
- **Imaging-observed secondary population** (DEV 109,220 / TEST 27,602): AUROC falls to 0.766 (FS-A) and 0.751 (FS-B). Restricting to admissions where the liver was actually imaged removes much of what the full-population model was using, which is consistent with the first bullet.

**Checks passed.** GOLD_HOLDOUT never entered any fit, tuning, early-stopping or threshold selection; TEST scored once per model; every feature classified before training; no phenotype-derived feature present (asserted in `tests/test_run0919_invariants.py`).

**Deviations.** The best configuration per learner was chosen once on FS-A (unweighted) and reused across feature sets and imbalance variants, rather than re-tuned for each of the 21 combinations — 4 configurations per learner rather than 20, to fit the run's time budget. Recorded as Tier 1 in the report.

**What Kyle should look at.** `docs/aim1b_structured.md` — the section "What the attributions say", and the calibration columns across the three imbalance variants.

## Phase 10.1–10.3 — manuscript methods draft, TRIPOD+AI checklist, results skeleton (delegated; notes in `phase10_drafts_notes.md`)

**Purpose.** Turn the run's outputs into the three documents a manuscript needs: a methods section that invents nothing, an item-by-item reporting-guideline checklist, and a results skeleton whose headline row is explicitly empty until the chart review happens.

**Results.** `docs/manuscript_methods_draft.md` (304 lines, 14 `[PENDING]`), `docs/tripod_ai_checklist.md` (104 lines, 4 `[PENDING]` plus 11 rows whose status is "pending"), `docs/manuscript_results_skeleton.md` (381 lines, 31 `[PENDING]`). The structured-arm results landed mid-draft and were folded in; the notes, fusion and locked-prediction sections name the exact results file each placeholder is waiting on.

**Five disagreements between existing documents and the recomputed results were found and flagged rather than silently resolved** (the results JSON was used in every case): the superseded "temporal window" claim in `docs/note_coverage.md`; a one-admission difference in a `table0.md` subtotal; rounded versus exact sampling weights; the superseded reviewer-time estimate in the criteria document; and two different cardiometabolic-unascertainability figures that turn out to be four- versus five-criterion operationalizations rather than a contradiction.

**The word "pre-registered" is not used as a claim anywhere in the new drafts.** Timing is described as what is true: the rule frozen and tagged before the cross-tabulation, and the hypotheses committed at `e2a4e1e` before any model was trained. Three lines in `docs/reference_standard.md` (31, 94, 126) still carry the old wording; those are a tracked project document making a claim about the paper, so they were **not** edited — the correction is **D-05**, and public registration versus the git audit trail is **D-04**.

**Deviation / correction by the lead.** An earlier `git add docs` swept two of these files into commit `877ead3` while they were still mid-draft; the finished versions are committed here.

## Phase 11.3 (revisited) — the audit's own leak detectors were wrong twice, and were fixed rather than silenced

Both times the audit reported a failure, the flagged lines were inspected and turned out to be benign, and both times the **rule** was tightened instead of the file being edited or the finding waved through:

1. Fifteen 8-digit integers were file sizes and one seed. Seeds are now discovered by scanning tracked code for `default_rng(...)` / `seed = ...` literals; byte counts are exempt only when the enclosing key names a size. A subject or admission identifier in a JSON field would still fire.
2. Blockquoted lines containing a lexicon term were flagged, including the manuscript's own headline sentence. The quoting heuristic was replaced with **direct fingerprints of MIMIC note text**: the de-identification placeholder that the corpus substitutes for every removed identifier, clinical report section headers inside quoted blocks, and over-8-word quoted windows that also carry one of those fingerprints.

`tests/test_run0919_audit_rules.py` adds nine negative controls so the detectors cannot silently rot: they must fire on a synthetic pasted radiology span, on the de-identification placeholder and on identifier-shaped integers, and must not fire on the study's own prose or on size-valued fields. Full suite: **70 passed**. All eight audit checks pass.

## Stretch item 2 — context-handling agreement with medspaCy ConText (done)

**Purpose.** The frozen note rule reimplements ConText rather than running the reference software, and the manuscript lists that as a limitation. This measures the limitation instead of asserting it.

**What was done.** `scripts/run0919_context_agreement.py` ran both systems over the **same** lexicon matches on 20,000 radiology reports drawn at random (seed 20260926) from the 45,355 reports carrying at least one asserted match. The lexicon, sentence splitter and screen terms are imported from the frozen rule; only its hit-iteration order is replicated, and the alignment is verified by comparing trigger names position by position — **0 of 20,000 reports failed that check**. Anatomically suppressed hits (2,182) are excluded rather than counted as disagreement, because ConText has no scoping analogue. Report: `docs/context_agreement.md`.

**Results.** 35,268 mentions compared; **overall agreement 90.76%**.

| assertion class | mentions | agreement |
| --- | --: | --: |
| affirmed | 32,867 | 91.55% |
| negated | 1,017 | 95.87% |
| uncertain (hedged) | 841 | 61.59% |
| historical | 361 | 72.30% |
| family | 0 | not estimable |

The informative asymmetry: 1,556 mentions the project affirms are negated by ConText, against 39 the other way — on this corpus the project's rule is the **more conservative negator**, asserting presence where the reference would not. Hedging is the weakest class, which is also the category the phenotype already reports separately (Tier C). Family attribution does not occur in radiology reports at all, so that class would need a discharge-summary sample to measure.

**Deviations.** medspaCy ConText is treated as an independent implementation, not a gold standard; the document says so. The frozen rule, its tags and the 2×2 are untouched.

**Incident.** This job initially wrote raw note text to a log via a third-party library's debug logging. See **B-04** in `BLOCKERS.md` — caught within about three minutes, nothing reached git, log deleted, logging silenced, regression test added.

**Stretch item 1 (embed variant U): skipped.** Variant U embeddings would need a second multi-hour encoding pass, and the run file itself notes U "mostly demonstrates circularity, which TF-IDF shows at no cost" — Phase 8.1 already showed exactly that (variant U's top coefficients are the lexicon itself). The variant U text is assembled and stored, so the pass can be run later without redoing anything. **Stretch item 3 (fine-tuning): skipped**, FINETUNE_BUDGET_HOURS = 0.

### Phase 8.2/8.3 dry run (validating the code path before the embedding budget expires)

Rather than discover a bug at the 21:39 deadline, the notes-arm script was given a `--smoke` mode and run on the shards available at 18:30 (9,000 admissions: DEV 5,541, TEST 1,439, GOLD 2,020). It completed end to end in 244 s: the logistic and LightGBM heads on the 1,536-dimensional vectors both fitted, LightGBM won on DEV out-of-fold AUPRC, and the notes-augmented CatBoost (FS-B plus the first 64 principal components, fitted inside training folds) produced out-of-fold and TEST predictions. **These numbers are not results** — they are a partial-data pipeline check, written to `data/processed/run_2026-09-19_scratch/` and superseded by the real run.

Two smoke model files were written under `models/run_2026-09-19/` before the mode was corrected to keep artifacts in scratch. They were **not deleted** — guardrail 12 permits deleting only the packet dry-run directory and scratch files, and unlike the B-04 log there is no safety reason to override it. Instead `scripts/run0919_fusion_lock.py` now excludes any `_SMOKE` file from the locked-prediction manifest and lists it under `excluded_from_manifest`, so the Phase 9.2 audit trail records exactly the models that produced the locked predictions and nothing else.

## Phase 8.2 / 8.3 — transformer embeddings and the notes-augmented model

**Purpose.** Ask whether a dense representation of the note text adds anything beyond the lexical model, and whether combining text with clinical structured features beats either. Everything here is a development diagnostic: the silver label is a lexical rule over the same text, so a notes model can score well by relearning the lexicon.

**What was done.** The encoder finished on budget at 21:40 UTC with **28 of 33 shards** — every gold-holdout shard (100% of 2,865 admissions) plus DEV 19,872 and TEST 5,108, giving 27,845 of 32,845 admissions embedded. Two heads were fitted on the 1,536-dimensional vectors (variant S) and the better on DEV out-of-fold AUPRC kept; then a notes-augmented CatBoost on FS-B plus the first 64 principal components, with the projection fitted inside training folds.

**Results.**

| model | TEST AUROC | TEST AUPRC |
| --- | --: | --: |
| embedding head, logistic regression | 0.754 | 0.217 |
| embedding head, LightGBM (kept) | 0.788 | 0.246 |
| TF-IDF variant S (Phase 8.1) | 0.826 | 0.407 |
| notes-augmented CatBoost, FS-B + 64 components | 0.829 | 0.328 |

**The transformer embeddings lost to TF-IDF**, on out-of-fold AUPRC (0.274 against 0.444) and on TEST. Two reasons are visible in the run and both are reported rather than explained away: the embeddings cover 85% of the subsample where TF-IDF covers all of it, and a frozen general clinical encoder with a light head is a weaker use of 1,536 dimensions than a vocabulary fitted to this corpus. Fine-tuning, which might close the gap, was budgeted at zero. The fusion stack therefore selected TF-IDF as its notes layer on DEV out-of-fold performance, not by hand.

## Phase 9 — fusion, locked predictions, gold harness

**Results** (`docs/aim1b_fusion.md`; paired subject-cluster bootstrap, 500 replicates).

| arm | AUROC | AUPRC | intercept | slope | recovery-zone AUROC |
| --- | --: | --: | --: | --: | --: |
| structured, FS-B clinical only | 0.793 | 0.291 | −0.14 | 1.01 | 0.763 |
| notes, TF-IDF variant S | 0.826 | 0.407 | −0.18 | 1.13 | 0.833 |
| notes-augmented, FS-B + components | 0.829 | 0.328 | −0.04 | 1.01 | 0.826 |
| **fusion, FS-B + notes** | **0.853** | **0.435** | −0.21 | 0.93 | 0.847 |
| fusion, FS-A + notes (sensitivity) | 0.860 | 0.464 | −0.22 | 0.96 | 0.858 |
| structured, FS-A (sensitivity) | 0.854 | 0.392 | −0.17 | 1.02 | 0.842 |

- **H1b-iii is half borne out.** Fusion is more discriminating than either base learner (+0.060 AUROC over the structured arm, 95% CI +0.031 to +0.089), but it is **not better calibrated** than the structured arm (slope 0.93 against 1.01). The hypothesis's own caveat also applies in the other direction: against the FS-A structured arm, fusion adds +0.006 AUROC — almost nothing, because the availability features FS-A already contains carry much of what the notes model contributes.
- The gain concentrates where the study cares: in code-negative admissions the fusion arm reaches 0.847 against the structured arm's 0.763. That is the silver-label shadow of H1b-ii; the real test needs the gold standard.
- **9.2 Locked predictions.** All 2,865 gold-holdout admissions were scored by 37 arm/variant columns before any adjudication exists. `data/processed/gold_holdout_predictions_v1.parquet` (untracked) with its SHA-256 and the hashes of all 16 model files are recorded in `docs/aim1b_locked_predictions.md`. The two smoke-test models are listed separately as excluded, so the manifest describes exactly the models that produced the locked predictions.
- **9.3 / 9.4** `scripts/aim1b_evaluate_gold.py` and `scripts/aim1b_gold_cv.py` are written and tested on synthetic labels, which are written to the scratch folder and carry SYNTHETIC in the filename and header. No synthetic result appears in `docs/`.

**Deviations.** Five DEV/TEST shards (24–28) were not encoded before the budget expired, so the notes arm trains on 85% of the intended subsample. The gold holdout is complete, so nothing downstream of the adjudication is affected.
