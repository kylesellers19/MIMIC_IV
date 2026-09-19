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
