# MASLD phenotyping on MIMIC-IV — code repository

A cross-sectional study of **MASLD** (metabolic dysfunction–associated steatotic liver disease) ascertainment in MIMIC-IV, asking how much documented hepatic steatosis the diagnosis codes miss, whether structured and note-based models can recover it, and whether recovery and its accuracy are even across patient groups.

**No data of any kind lives in this repository.** Every input is credentialed PhysioNet data held locally; every tracked file here is code or an aggregate document.

## Aims

| Aim | Question | Status |
| --- | --- | --- |
| 1a | Among admissions with documented hepatic steatosis, what population-weighted fraction carry no MASLD code? | Computable-stage 2×2 built. A second computable phenotype, a local language model, gives the same gap (`docs/llm_review_preliminary.md`). The headline estimate needs the 400-chart adjudication, which has not happened |
| 1b | Can models predict documented steatosis from structured data, from notes, and from both? | Silver-label development complete. The label-dependence check against the language-model label is done (`docs/aim1b_llm_label.md`). Gold-standard evaluation awaits the adjudication |
| 1c | Do recovery, its accuracy, and model calibration differ across race, insurance, sex, language and age? | Level 1 (computable stage) complete, and repeated with the language-model phenotype (`docs/aim1c_llm_level1.md`). Levels 2–3 need the gold standard |

## Preliminary results

<!-- preliminary-results:start -->

> **Computable stage only — not yet validated by chart review.** Exploratory. Every number in this block is written by `scripts/readme_preliminary.py` from the results files it cites; counts from 1 to 10 appear as <11. The 400-chart clinician review, which sets the headline estimates, has not happened.

**Aim 1a: steatosis documented in notes but never coded.**

- **Frozen keyword rule, full population:** 22,799 of 27,826 note-positive admissions (81.9%) carry no MASLD code. The population is 373,992 admissions of 161,119 patients (`docs/run_2026-09-19/results/integrity_gate.json`).
- **A second reader gives the same gap.** A language model run locally reviewed every liver sentence for a random sample of 13,000 dev/test patients. Among patients it finds steatosis for, 77.7% have no code; the rule gives 77.2%.
- **Scaled to all dev/test patients:** about 11,700 patients by the model and 11,300 by the rule have documented steatosis and no code, against about 3,700 with a code. That is 9,100 when both methods must agree and 13,700 when either is enough.
- **Why the code is missing:** among coded cases the model finds, 92.2% are written in the discharge summary, against 43.3% of uncoded ones. Of the uncoded cases, 38.9% appear only on outpatient imaging and 17.8% only in inpatient radiology reports.
- **Where the two readers disagree:** on uncoded admissions, the model confirms 82.1% of the rule's positives and finds steatosis in 1.6% of the rule's negatives. Those disagreements are where chart review is needed (`docs/llm_review_preliminary.md`).

**Aim 1b: label dependence.** The locked TEST predictions were scored against the model's label instead of the rule's. AUROC changes by at most 0.025, and every interval includes zero. The models are not simply learning the rule's quirks (`docs/aim1b_llm_label.md`).

**Aim 1c: equity at the computable stage.** Using the model instead of the rule raises the overall recovery share by 1.4 points (0.5–2.2). The two readers disagree more often for Medicare patients (36.3% [31.5–41.3] of admissions either calls positive) than for privately insured patients (26.1% [21.7–30.5]), and more for ages 75–88 (40.6% [31.5–50.7]) than for ages 40–54 (23.2% [18.9–28.0]). Note-based ascertainment is less consistent for older and Medicare patients, so the chart review should check those groups closely (`docs/aim1c_llm_level1.md`).

**Method notes.** The sentence filter was widened to admit NAFLD-type abbreviations, unnamed steatosis and sentences under liver headings. That cut the admissions whose steatosis statement never reached the model from 367 to 0. Prompt rewordings agree with the main prompt at Cohen's kappa 0.808–0.895 on a 500-sentence development pilot (`docs/llm_review_protocol.md`).

<!-- preliminary-results:end -->

## Obtaining and verifying the data

The study uses **MIMIC-IV v3.1** (`hosp` module) and **MIMIC-IV-Note v2.2** (`note` module) from PhysioNet. Both are credentialed: each person who touches them needs their own PhysioNet credentialing and their own signed data use agreement. Access cannot be shared.

Download into `data/raw/`, keeping files gzipped, in this layout:

```
data/raw/
├── hosp/    admissions.csv.gz  patients.csv.gz  diagnoses_icd.csv.gz  d_icd_diagnoses.csv.gz
│            labevents.csv.gz   d_labitems.csv.gz  omr.csv.gz  prescriptions.csv.gz
├── note/    discharge.csv.gz  discharge_detail.csv.gz  radiology.csv.gz  radiology_detail.csv.gz
└── SHA256SUMS*.txt            checksum manifests as published by PhysioNet
```

Verify before use — every `.csv.gz` must match its published digest:

```bash
scripts/run0919_env.sh scripts/run0919_data_inventory.py   # hashes each file, compares to the manifests
```

Terminal downloads returned HTTP 403 on this machine; see `docs/admin/physionet_403_email_draft.md`. Browser downloads worked.

## Configuration

All locked decisions live in one place: [scripts/masld_config.py](scripts/masld_config.py). It is **append-only** — new constants may be added, existing values never change. It defines the ICD code set, the analysis-population SQL, the approved laboratory itemids, the race-category policy, and the split/seed constants added by later runs.

Downstream code reads the cleaned population through `CLEAN_POP`; code status comes from [sql/masld_coded.sql](sql/masld_coded.sql); note status from [scripts/note_phenotype.py](scripts/note_phenotype.py), frozen and git-tagged (`note-phenotype-v1.0.0`, `note-phenotype-v1.1.0`) before the 2×2 was built.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/run0919_env.sh -c "import duckdb, torch; print(duckdb.__version__)"
```

`scripts/run0919_env.sh` runs a script with the repository on `PYTHONPATH`, Hugging Face telemetry disabled, and `DYLD_LIBRARY_PATH` pointed at the OpenMP library bundled with torch — LightGBM and XGBoost need it and no system install is permitted.

## Pipeline

Stages in order, with the document each writes. See [run_pipeline.sh](run_pipeline.sh) for the runnable list.

| # | Stage | Script | Output |
| --: | --- | --- | --- |
| 1 | Data quality assessment (Kahn framework) | `dq_audit.py`, `conformance.py`, `plausibility_*.py`, `completeness_differential.py` | `docs/data_quality_report.md` |
| 2 | Cleaning (null, never drop) | `clean_population.py` | `docs/cleaning_execution.md` |
| 3 | Population lock | `lock_population.py` | `docs/analysis_population.md`, `docs/tables/table0.md` |
| 4 | Note phenotype (frozen, tagged) | `note_phenotype.py` | `docs/note_phenotype_spec.md` |
| 5 | Code × note 2×2 and sampling frame | `build_2x2.py`, `aim1a_report.py` | `docs/aim1a_crosstab.md` |
| 6 | Pre-adjudication descriptives | `predef_etio_metab.py`, `cmrf.py`, `imaging_denominator.py`, `comorbid_cluster.py` | `docs/predefinition_descriptives.md`, `docs/sld_subclassification.md`, `docs/imaging_denominator.md` |
| 7 | Pre-specified plan (committed before modeling) | — | `docs/analysis_plan_prespecified.md` |
| 8 | Splits with a gold holdout | `run0919_phase2_splits.py` | `docs/aim1b_splits.md` |
| 9 | Sensitivity and validation | `run0919_sens_5719.py`, `run0919_charlson_validation.py`, `run0919_loose_ends_43_44.py`, `run0919_cohort_flow.py`, `run0919_avail_windows.py` | `docs/sensitivity_5719.md`, `docs/charlson_validation.md`, `docs/aim1a_loose_ends.md` |
| 10 | Equity audit, level 1 | `run0919_aim1c_level1.py` | `docs/aim1c_level1.md` |
| 11 | Reference-standard machinery | `aim1a_estimator.py`, `run0919_precision_forecast.py`, `make_adjudication_template.py`, `assign_reviewers.py`, `make_reviewer_packets.py` | `docs/aim1a_precision_forecast.md`, `docs/adjudication/*` |
| 12 | Notes text and embeddings | `run0919_notes_index.py`, `run0919_notes_text.py`, `run0919_embed.py` | (credentialed derivatives only) |
| 13 | Models: structured, notes, fusion | `run0919_features.py`, `run0919_aim1b_structured.py`, `run0919_notes_tfidf.py`, `run0919_notes_embed_arm.py`, `run0919_fusion_lock.py` | `docs/aim1b_structured.md`, `docs/aim1b_notes.md`, `docs/aim1b_fusion.md`, `docs/aim1b_locked_predictions.md` |
| 14 | Gold-standard evaluation (after adjudication) | `aim1b_evaluate_gold.py`, `aim1b_gold_cv.py` | pending the chart review |
| 15 | Local-LLM sentence review (exploratory, amendments h–j) | `liver_sentences.py`, `llm_sentence_review.py`, `llm_annotation.py`, `llm_review_results.py`, `aim1c_llm_level1.py`, `aim1b_llm_label.py`, `readme_preliminary.py` | `docs/llm_review_protocol.md`, `docs/llm_review_preliminary.md`, `docs/aim1c_llm_level1.md`, `docs/aim1b_llm_label.md` |

Runs are journalled under `docs/run_<date>/`: `RUN_LOG.md` (what was done and why), `STATE.json`, `DECISIONS_FOR_KYLE.md` (open protocol questions), `BLOCKERS.md`, `FINAL_REPORT.md`.

## What is tracked, and what never is

**Tracked:** code, SQL, tests, and aggregate documents under `docs/`. Every number in a document is written by a script into a results file under `docs/**/results/`, and the document names the script and file that produced it. Counts below 11 appear as `<11`.

**Never tracked** (all git-ignored): anything under `data/` (raw MIMIC files, cleaned population, per-note index, assembled note text, embeddings, predictions, adjudication keys and reviewer forms), `models/` (fitted models are credentialed derivatives), `logs/`, and `*.csv` / `*.parquet` anywhere.

Confirm before any commit:

```bash
git status --short | grep -E "data/|models/|logs/"   # must print nothing
```

## Reference standard

The 400-chart adjudication has **not** been performed. The criteria are drafted but not signed off (`docs/adjudication_criteria.md` — every `[CLINICIAN]` flag is an open question), the blank instrument and reviewer assignment exist, and the packet generator has been dry-run and its output deleted. No performance number anywhere in this repository is validated against human adjudication; each is either a comparison of two computable phenotypes or a silver-label development diagnostic.
