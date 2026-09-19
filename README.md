# MASLD phenotyping on MIMIC-IV — code repository

A cross-sectional study of **MASLD** (metabolic dysfunction–associated steatotic liver disease) ascertainment in MIMIC-IV, asking how much documented hepatic steatosis the diagnosis codes miss, whether structured and note-based models can recover it, and whether recovery and its accuracy are even across patient groups.

**No data of any kind lives in this repository.** Every input is credentialed PhysioNet data held locally; every tracked file here is code or an aggregate document.

## Aims

| Aim | Question | Status |
| --- | --- | --- |
| 1a | Among admissions with documented hepatic steatosis, what population-weighted fraction carry no MASLD code? | Computable-stage 2×2 built; the headline estimate needs the 400-chart adjudication, which has not happened |
| 1b | Can models predict documented steatosis from structured data, from notes, and from both? | Silver-label development complete; gold-standard evaluation awaits the adjudication |
| 1c | Do recovery, its accuracy, and model calibration differ across race, insurance, sex, language and age? | Level 1 (computable stage) complete; levels 2–3 need the gold standard |

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
