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
