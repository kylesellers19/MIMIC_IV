# MASLD phenotyping on MIMIC-IV — code repository

**How many hospital patients have fatty liver disease written in their chart but never coded? Can the rest of the record find them? And are the gap and the fix fair across patient groups?**

This repository holds the code and aggregate results of a cross-sectional study of **MASLD** (metabolic dysfunction–associated steatotic liver disease, formerly NAFLD) in MIMIC-IV. MIMIC-IV is a credentialed research database of hospital admissions at Beth Israel Deaconess Medical Center in Boston.

**No data of any kind lives in this repository.** Every input is credentialed PhysioNet data held locally; every tracked file here is code or an aggregate document.

## Purpose

Health-record research, disease registries, quality measures and many decision tools find patients by their diagnosis codes. Hepatic steatosis, the finding that defines MASLD, is often written in a radiology report or a discharge summary with no matching code.

A patient like that is invisible to anything that counts codes:
- they drop out of research cohorts and prevalence estimates;
- they don't count in quality measures;
- reminders or follow-up triggered by a code, such as fibrosis risk assessment, may never happen.

This study measures how large that invisible group is. It then tests whether information already in the record can find these patients, and checks whether the gap and the fix fall evenly across patient groups.

## Gaps this research fills

1. **How big the coding gap is, measured against chart review.**
   - **What exists:** standard code lists for the disease (Hagström et al., *Hepatology* 2021), and keyword and language-model tools that find steatosis in notes.
   - **What's missing:** a well-established answer, for a general hospital population, to how many patients with documented steatosis carry no code. That answer has to be checked against clinicians reading the charts and weighted back to the whole population, not obtained by comparing one algorithm with another.
2. **Whether the record can recover missed cases, tested honestly.**
   - **The problem:** a model trained on labels taken from note keywords can score well just by relearning the keywords.
   - **What's needed:** structured data (labs, vital signs, medications, imaging), note text, or both have to be judged on charts the models never saw. Every prediction must be locked before the review starts.
3. **Whether ascertainment is fair.**
   - **The risk:** if coding misses steatosis more often in some groups, every code-based study and quality measure inherits that bias. Finding cases in notes could narrow the bias or create a new one, because notes depend on who gets imaged and how thoroughly they are documented.
   - **What's needed:** coding, recovery, the accuracy of recovery, and model calibration have to be compared across race, insurance, sex, language and age, with intervals, not assumed equal.
4. **Reproducibility.**
   - **The problem:** phenotyping results from private health-system data can't be rerun by others.
   - **What this study does:** it uses MIMIC-IV, which any credentialed researcher can obtain, together with:
     - an analysis plan committed before any model was trained;
     - a frozen, git-tagged note phenotype;
     - hashed and locked predictions;
     - a language model run locally at a pinned version.

## Aims

### Aim 1a: measure the coding gap

- **Question:** among admissions with documented hepatic steatosis, what population-weighted share carry no MASLD diagnosis code?
- **Approach:**
  - A frozen keyword phenotype reads every discharge summary and radiology report.
  - Codes are crossed with it in a code × note 2×2 table.
  - 400 charts, sampled from all four cells with the uncoded-but-documented cell largest, are reviewed by clinicians.
  - Inverse-probability weights carry their verdicts back to the whole population.
- **Hypothesis** (recorded 7 September 2026): most, probably more than three-quarters, carry no code.
- **Status:**
  - Computable-stage estimate done; a second phenotype, a local language model, gives the same gap.
  - The headline estimate awaits the chart review.

### Aim 1b: recover the missed cases

- **Question:** can models predict documented steatosis from structured data, from note text, and from both?
- **Approach:**
  - **Structured data:** gradient-boosted trees, with clinical-only and availability-only feature sets to show what drives prediction.
  - **Notes and both:** text models, and a stacked combination of the two.
  - **Process:** trained on a development partition, checked once on a test partition, then evaluated against the chart review on a held-out set no model was fitted on.
- **Hypothesis:** against the chart review, adding notes beats structured data alone among uncoded admissions.
- **Status:**
  - Development is complete against keyword labels.
  - Predictions on the held-out charts are hashed and locked.
  - Evaluation awaits the chart review.

### Aim 1c: check fairness

- **Question:** do coding, recovery, recovery accuracy and model calibration differ by race, insurance, sex, language and age?
- **Approach,** at three levels:
  1. coding and recovery rates by group at the computable stage;
  2. recovery accuracy by group, against the chart review;
  3. model calibration by group.
- **Hypothesis:** coding rates differ across race and insurance groups (direction not assumed), and accuracy and calibration are less even than the recovery rate itself.
- **Status:**
  - Level 1 is done with both phenotypes.
  - Levels 2 and 3 need the chart review.

The hypotheses, sensitivity analyses and every later amendment are in [docs/analysis_plan_prespecified.md](docs/analysis_plan_prespecified.md), each committed before the analysis it governs.

## Preliminary results

<!-- preliminary-results:start -->

> **Computable stage only — not yet validated by chart review.** Exploratory. Every number in this block is written by `scripts/readme_preliminary.py` from the results files it cites; counts from 1 to 10 appear as <11. The 400-chart clinician review, which sets the headline estimates, has not happened.

**Aim 1a: steatosis documented in notes but never coded.**

- **Frozen keyword rule, full population:** 22,799 of 27,826 note-positive admissions (81.9%) carry no MASLD code. The population is 373,992 admissions of 161,119 patients (`docs/run_2026-09-19/results/integrity_gate.json`).
- **A second reader gives the same gap.** A language model run locally reviewed every liver sentence for a random sample of 13,000 dev/test patients. Among patients it finds steatosis for, 77.7% have no code; the rule gives 77.2%.
- **Scaled to all dev/test patients:** about 11,700 patients by the model and 11,300 by the rule have documented steatosis and no code, against about 3,700 with a code. That is 9,100 when both methods must agree and 13,700 when either is enough.
- **Why the code is missing:** among coded cases the model finds, 92.2% are written in the discharge summary, against 43.3% of uncoded ones. Of the uncoded cases, 38.9% appear only on outpatient imaging and 17.8% only in inpatient radiology reports.
- **Where the two readers disagree:** on uncoded admissions, the model confirms 82.1% of the rule's positives and finds steatosis in 1.6% of the rule's negatives. Those disagreements are where chart review is needed (`docs/llm_review_preliminary.md`).

**Aim 1b: recovering missed cases.** These are scored against the keyword label, not chart review.

- **Structured data predicts documented steatosis,** with gradient-boosted trees on the TEST partition (75,124 admissions): AUROC 0.857 (0.849–0.866) with every feature.
- **Much of that is documentation, not physiology.** Clinical values alone (labs, blood pressure, BMI, medications, comorbidity) give 0.787 (0.778–0.796). Knowing only what was measured, imaged, ordered and written, with no clinical value at all, gives 0.812 (0.803–0.820). The keyword label partly reflects how thoroughly a patient was worked up, which is why the models must be judged against chart review (`docs/aim1b_structured.md`).
- **Label dependence:** the locked TEST predictions were scored against the language model's label instead of the rule's. AUROC changes by at most 0.025, and every interval includes zero. The models are not simply learning the rule's quirks (`docs/aim1b_llm_label.md`).

**Aim 1c: fairness at the computable stage.**

- **The gap is large in every group.** Among note-positive admissions, the share with no code is 85.7% [84.1–87.1] for Black/African American patients against 82.4% [81.5–83.2] for White patients. It is 83.6% [82.4–84.9] for Medicaid against 80.2% [79.1–81.3] for private insurance, and 81.1% [80.1–82.0] for women against 82.7% [81.6–83.6] for men. Across age bands it ranges from 80.3% to 83.6%. The differences are a few points, and the intervals separate for race and insurance (`docs/aim1c_level1.md`).
- **The two readers disagree unevenly.** Of the admissions either the rule or the language model calls positive, they disagree on 36.3% [31.5–41.3] for Medicare patients against 26.1% [21.7–30.5] for privately insured patients, and on 40.6% [31.5–50.7] for ages 75–88 against 23.2% [18.9–28.0] for ages 40–54. Note-based ascertainment is less consistent for older and Medicare patients, so the chart review should check those groups closely. Swapping the rule for the language model raises the overall recovery share by only 1.4 points (0.5–2.2) (`docs/aim1c_llm_level1.md`).

**Ready for the chart review.**

- **Every model's held-out predictions are hashed and locked** before any chart is reviewed (`docs/aim1b_locked_predictions.md`).
- **So are the language model's answers:** it labelled all 2,865 held-out admissions (20,200 distinct sentences, 0 errors), and its answers were hashed. Nothing about those answers has been looked at (`docs/llm_gold_lock.md`). The rule turning sentence answers into admission labels was in the analysis plan before the run (amendment h).
- **The language model's answers barely depend on how it is compressed.** A smaller build of the same model was run on a stratified sample of 1,300 dev/test sentences. Weighted back to all 89,857, it changed an estimated 0.47% of answers (conservative 95% bounds 0.32–1.86%). Whether a sentence counts toward the label changed for 0.29% (0.17–1.65%), about evenly in each direction (`docs/llm_review_protocol.md` §6).

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
| 15 | Local-LLM sentence review (exploratory, amendments h–j) | `liver_sentences.py`, `llm_sentence_review.py`, `llm_phenotype.py`, `llm_annotation.py`, `llm_review_results.py`, `aim1c_llm_level1.py`, `aim1b_llm_label.py`, `llm_gold_lock.py`, `readme_preliminary.py` | `docs/llm_review_protocol.md`, `docs/llm_review_preliminary.md`, `docs/aim1c_llm_level1.md`, `docs/aim1b_llm_label.md`, `docs/llm_gold_lock.md` |

Runs are journalled under `docs/run_<date>/`: `RUN_LOG.md` (what was done and why), `STATE.json`, `DECISIONS_FOR_KYLE.md` (open protocol questions), `BLOCKERS.md`, `FINAL_REPORT.md`.

## What is tracked, and what never is

**Tracked:** code, SQL, tests, and aggregate documents under `docs/`. Every number in a document is written by a script into a results file under `docs/**/results/`, and the document names the script and file that produced it. Counts below 11 appear as `<11`.

**Never tracked** (all git-ignored): anything under `data/` (raw MIMIC files, cleaned population, per-note index, assembled note text, embeddings, predictions, adjudication keys and reviewer forms), `models/` (fitted models are credentialed derivatives), `logs/`, and `*.csv` / `*.parquet` anywhere.

Confirm before any commit:

```bash
git status --short | grep -E "data/|models/|logs/"   # must print nothing
```

## Reference standard

The 400-chart adjudication has **not** been performed, and clinician reviewers join later.

- **Ready:** the blank instrument and reviewer assignment exist, and the packet generator has been dry-run and its output deleted. Every model arm's predictions on the held-out charts (`docs/aim1b_locked_predictions.md`) and the local language model's answers (`docs/llm_gold_lock.md`) are hashed and locked, so it can be shown that nothing was tuned against the review.
- **Still needed:** clinician sign-off on the criteria (`docs/adjudication_criteria.md`; every `[CLINICIAN]` flag is an open question) and the reviewers themselves.

No performance number anywhere in this repository is validated against human adjudication. Each is either a comparison of two computable phenotypes or a silver-label development diagnostic.
