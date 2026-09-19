# Data inventory — credentialed and derived data on this machine (run_2026-09-19, Phase 10.6)

Generated 2026-09-19T16:58:50+00:00 by `scripts/run0919_data_inventory.py` (JSON: `docs/run_2026-09-19/results/data_inventory.json`). Names, sizes, git status and checksum status only; no file contents were read except to stream bytes through SHA-256. Paths are relative to the repository root. `tracked` = present in `git ls-files`; everything else is untracked and, for the data locations below, git-ignored by `.gitignore`.

## Summary

| Location | Classification | Files | Size | Tracked files |
|---|---|---:|---:|---:|
| `data/raw` | credentialed | 18 | 4.9 GB | 0 |
| `data/processed` | credentialed derivative | 58 | 654.3 MB | 0 |
| `models` | credentialed derivative | 0 | 0 B | 0 |
| `logs/run_2026-09-19` | credentialed derivative (policy) | 17 | 9.4 KB | 0 |
| `test files` | not credentialed | 46 | 31.1 MB | 0 |
| `docs/tables` | aggregate derivative | 32 | 100.1 KB | 16 |
| `/Users/betsylujan/.cache/huggingface/hub` (model checkpoints) | not credentialed (public model checkpoints) | 1 model dirs | 831.4 MB (hub dir total 831.4 MB) | 0 |
| `.venv` | not credentialed (Python environment) | — | 1.7 GB | 0 |
| tracked docs / code | not credentialed (tracked docs, scripts, sql, tests; aggregates only by guardrail) | 111 | — | all |

## What is credentialed PhysioNet data (or a derivative of it)

- **Raw**: every `.csv.gz` under `data/raw/` (MIMIC-IV v3.1 hosp tables; MIMIC-IV-Note v2.2 discharge and radiology notes). Read-only; never decompressed to disk.
- **Processed derivatives** under `data/processed/`: DuckDB databases and parquet extracts, the note index and extracted note text, chunked Bio_ClinicalBERT embeddings, model predictions, adjudication master keys and sampling frames, private small-cell counts, and scratch outputs. All are patient-level or re-identifiable derivatives and are covered by the PhysioNet DUA.
- **Fitted models** under `models/` (empty at inventory time if listed as 0 files) and any model weights written elsewhere in `data/processed/` are credentialed derivatives.
- **Run logs** under `logs/run_2026-09-19/`: aggregate by guardrail, but treated as credentialed derivatives by the project's `.gitignore` policy.
- **Aggregate tables** `docs/tables/*.csv` and `*.md`: aggregate results with small cells suppressed; the `.csv` copies are git-ignored by the `*.csv` pattern, the `.md` copies are tracked. Not patient-level.

## What is not credentialed data

- `test files/` — open-access MIMIC-IV demo releases (per `.gitignore`), git-ignored.
- Tracked documentation, scripts, SQL and tests (aggregates only by guardrail).
- `.venv/` (Python packages) and the Hugging Face cache (public model checkpoints; `HF_HUB_DISABLE_TELEMETRY=1`).

## `data/raw/` checksum verification

Manifests found in `data/raw/`: `SHA256SUMS.hosp.txt`, `SHA256SUMS.meds.txt`, `SHA256SUMS.note.txt`, `SHA256SUMS_mimiciv31_original.txt`, `SHA256SUMS_note_original.txt`. Each `.csv.gz` was hashed with SHA-256 and compared, by file name, against every manifest that lists it. Hashed: True.

**Summary:** match 12 · match in some manifests only 0 · mismatch 0 · not listed 0 · unreadable 0.

Listed in a manifest but not present on disk (names only): `CHANGELOG.txt`, `LICENSE.txt`, `caregiver.csv.gz`, `chartevents.csv.gz`, `d_hcpcs.csv.gz`, `d_icd_procedures.csv.gz`, `d_items.csv.gz`, `datetimeevents.csv.gz`, `drgcodes.csv.gz`, `emar.csv.gz`, `emar_detail.csv.gz`, `hcpcsevents.csv.gz`, `icustays.csv.gz`, `ingredientevents.csv.gz`, `inputevents.csv.gz`, `microbiologyevents.csv.gz`, `outputevents.csv.gz`, `pharmacy.csv.gz`, `poe.csv.gz`, `poe_detail.csv.gz`, `procedureevents.csv.gz`, `procedures_icd.csv.gz`, `provider.csv.gz`, `services.csv.gz`, `transfers.csv.gz`.

| File | Size | Status | Manifests listing it |
|---|---:|---|---|
| `data/raw/hosp/admissions.csv.gz` | 19.0 MB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/d_icd_diagnoses.csv.gz` | 855.8 KB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/d_labitems.csv.gz` | 12.9 KB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/diagnoses_icd.csv.gz` | 32.0 MB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/labevents.csv.gz` | 2.4 GB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/omr.csv.gz` | 42.0 MB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/patients.csv.gz` | 2.7 MB | match | SHA256SUMS.hosp.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/hosp/prescriptions.csv.gz` | 578.2 MB | match | SHA256SUMS.meds.txt, SHA256SUMS_mimiciv31_original.txt |
| `data/raw/note/discharge.csv.gz` | 1.1 GB | match | SHA256SUMS.note.txt, SHA256SUMS_note_original.txt |
| `data/raw/note/discharge_detail.csv.gz` | 770.9 KB | match | SHA256SUMS.note.txt, SHA256SUMS_note_original.txt |
| `data/raw/note/radiology.csv.gz` | 745.6 MB | match | SHA256SUMS.note.txt, SHA256SUMS_note_original.txt |
| `data/raw/note/radiology_detail.csv.gz` | 37.2 MB | match | SHA256SUMS.note.txt, SHA256SUMS_note_original.txt |

## `data/raw` — credentialed

PhysioNet MIMIC-IV v3.1 hosp, MIMIC-IV-Note v2.2 raw .csv.gz files (read-only); SHA256SUMS manifests are checksum text only

| File | Size | Tracked |
|---|---:|---|
| `data/raw/.gitkeep` | 0 B | no |
| `data/raw/SHA256SUMS.hosp.txt` | 621 B | no |
| `data/raw/SHA256SUMS.meds.txt` | 179 B | no |
| `data/raw/SHA256SUMS.note.txt` | 444 B | no |
| `data/raw/SHA256SUMS_mimiciv31_original.txt` | 2.8 KB | no |
| `data/raw/SHA256SUMS_note_original.txt` | 439 B | no |
| `data/raw/hosp/admissions.csv.gz` | 19.0 MB | no |
| `data/raw/hosp/d_icd_diagnoses.csv.gz` | 855.8 KB | no |
| `data/raw/hosp/d_labitems.csv.gz` | 12.9 KB | no |
| `data/raw/hosp/diagnoses_icd.csv.gz` | 32.0 MB | no |
| `data/raw/hosp/labevents.csv.gz` | 2.4 GB | no |
| `data/raw/hosp/omr.csv.gz` | 42.0 MB | no |
| `data/raw/hosp/patients.csv.gz` | 2.7 MB | no |
| `data/raw/hosp/prescriptions.csv.gz` | 578.2 MB | no |
| `data/raw/note/discharge.csv.gz` | 1.1 GB | no |
| `data/raw/note/discharge_detail.csv.gz` | 770.9 KB | no |
| `data/raw/note/radiology.csv.gz` | 745.6 MB | no |
| `data/raw/note/radiology_detail.csv.gz` | 37.2 MB | no |

## `data/processed` — credentialed derivative

DuckDB/parquet extracts, note index and note text, embeddings, predictions, adjudication keys, private small-cell counts, scratch

| Sub-path | Files | Size |
|---|---:|---:|
| `data/processed/.gitkeep` | 1 | 0 B |
| `data/processed/adjudication` | 3 | 39.1 KB |
| `data/processed/aim1a_frame.parquet` | 1 | 6.6 MB |
| `data/processed/aim1a_sample.parquet` | 1 | 7.2 KB |
| `data/processed/aim1a_training_key.parquet` | 1 | 1.0 KB |
| `data/processed/analysis_population.parquet` | 1 | 11.5 MB |
| `data/processed/analysis_population_clean.parquet` | 1 | 10.5 MB |
| `data/processed/cmrf.parquet` | 1 | 2.0 MB |
| `data/processed/note_historical.parquet` | 1 | 1.9 MB |
| `data/processed/notes_embeddings_v1` | 2 | 3.2 MB |
| `data/processed/run_2026-09-19_charlson.parquet` | 1 | 3.2 MB |
| `data/processed/run_2026-09-19_features.parquet` | 1 | 19.8 MB |
| `data/processed/run_2026-09-19_lab_features.parquet` | 1 | 7.4 MB |
| `data/processed/run_2026-09-19_notes_index` | 2 | 45.3 MB |
| `data/processed/run_2026-09-19_notes_text` | 4 | 520.6 MB |
| `data/processed/run_2026-09-19_outpt_labs.parquet` | 1 | 18.2 MB |
| `data/processed/run_2026-09-19_private` | 1 | 163 B |
| `data/processed/run_2026-09-19_scratch` | 33 | 512.0 KB |
| `data/processed/splits_v1.parquet` | 1 | 3.6 MB |

| File | Size | Tracked |
|---|---:|---|
| `data/processed/.gitkeep` | 0 B | no |
| `data/processed/aim1a_frame.parquet` | 6.6 MB | no |
| `data/processed/aim1a_sample.parquet` | 7.2 KB | no |
| `data/processed/aim1a_training_key.parquet` | 1.0 KB | no |
| `data/processed/analysis_population.parquet` | 11.5 MB | no |
| `data/processed/analysis_population_clean.parquet` | 10.5 MB | no |
| `data/processed/cmrf.parquet` | 2.0 MB | no |
| `data/processed/note_historical.parquet` | 1.9 MB | no |
| `data/processed/run_2026-09-19_charlson.parquet` | 3.2 MB | no |
| `data/processed/run_2026-09-19_features.parquet` | 19.8 MB | no |
| `data/processed/run_2026-09-19_lab_features.parquet` | 7.4 MB | no |
| `data/processed/run_2026-09-19_outpt_labs.parquet` | 18.2 MB | no |
| `data/processed/splits_v1.parquet` | 3.6 MB | no |
| `data/processed/adjudication/form_reviewer1.xlsx` | 16.8 KB | no |
| `data/processed/adjudication/form_reviewer2.xlsx` | 16.8 KB | no |
| `data/processed/adjudication/reviewer_assignment.parquet` | 5.6 KB | no |
| `data/processed/notes_embeddings_v1/S/index.parquet` | 240.3 KB | no |
| `data/processed/notes_embeddings_v1/S/shard_0000.npy` | 2.9 MB | no |
| `data/processed/run_2026-09-19_notes_index/discharge.parquet` | 7.3 MB | no |
| `data/processed/run_2026-09-19_notes_index/radiology.parquet` | 37.9 MB | no |
| `data/processed/run_2026-09-19_notes_text/pilot.parquet` | 3.1 MB | no |
| `data/processed/run_2026-09-19_notes_text/pilot.parquet.summary.json` | 235 B | no |
| `data/processed/run_2026-09-19_notes_text/subsample.parquet` | 517.5 MB | no |
| `data/processed/run_2026-09-19_notes_text/subsample.parquet.summary.json` | 281 B | no |
| `data/processed/run_2026-09-19_private/sens_5719_exact.json` | 163 B | no |
| `data/processed/run_2026-09-19_scratch/inventory.log` | 0 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R01_hagstrom_2021_pubmed_pmid.xml` | 31.4 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R02_rinella_2023_pubmed_pmid.xml` | 28.8 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R03_kahn_2016_pubmed_doi_efetch.xml` | 31.7 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R03_kahn_2016_pubmed_doi_esearch.json` | 296 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R04_chapman_2001_crossref_title.json` | 14.6 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R04_chapman_2001_pubmed_title_efetch.xml` | 5.6 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R04_chapman_2001_pubmed_title_esearch.json` | 456 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R04_chapman_2001_pubmed_title_words_esearch.json` | 358 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R05_harkema_2009_crossref_title.json` | 37.3 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R05_harkema_2009_pubmed_title_efetch.xml` | 16.9 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R05_harkema_2009_pubmed_title_esearch.json` | 486 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R05_harkema_2009_pubmed_title_words_esearch.json` | 382 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R06_quan_2005_pubmed_author_efetch.xml` | 7.4 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R06_quan_2005_pubmed_author_esearch.json` | 481 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R07_charlson_1987_pubmed_author_efetch.xml` | 5.5 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R07_charlson_1987_pubmed_author_esearch.json` | 417 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R08_vacs_steatosis_nlp_2024_pubmed_journal_kw_efetch.xml` | 29.8 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R08_vacs_steatosis_nlp_2024_pubmed_journal_kw_esearch.json` | 493 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R09_alsentzer_2019_bio_clinicalbert_crossref_author.json` | 22.5 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R09_alsentzer_2019_bio_clinicalbert_crossref_keywords.json` | 20.3 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R09_alsentzer_2019_bio_clinicalbert_pubmed_author_esearch.json` | 443 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R10_li_2022_clinical_longformer_crossref_author.json` | 34.8 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R10_li_2022_clinical_longformer_crossref_keywords.json` | 49.5 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R10_li_2022_clinical_longformer_pubmed_author_esearch.json` | 411 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R11_johnson_2023_mimic_iv_crossref_author.json` | 45.9 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R11_johnson_2023_mimic_iv_pubmed_author_efetch.xml` | 16.1 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R11_johnson_2023_mimic_iv_pubmed_author_esearch.json` | 419 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R12_johnson_mimic_iv_note_crossref_author.json` | 9.7 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R12_johnson_mimic_iv_note_crossref_keywords.json` | 39.1 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R12_johnson_mimic_iv_note_pubmed_author_esearch.json` | 397 B | no |
| `data/processed/run_2026-09-19_scratch/citations/R13_collins_2024_tripod_ai_pubmed_author_efetch.xml` | 59.9 KB | no |
| `data/processed/run_2026-09-19_scratch/citations/R13_collins_2024_tripod_ai_pubmed_author_esearch.json` | 412 B | no |

## `models` — credentialed derivative

fitted model weights (git-ignored)

| File | Size | Tracked |
|---|---:|---|

## `logs/run_2026-09-19` — credentialed derivative (policy)

run logs; aggregate output only by guardrail, but git-ignored as credentialed derivatives under the project's logs/ rule

| File | Size | Tracked |
|---|---:|---|
| `logs/run_2026-09-19/aim1b_structured.log` | 202 B | no |
| `logs/run_2026-09-19/aim1c_level1.log` | 143 B | no |
| `logs/run_2026-09-19/embed_main.log` | 1.5 KB | no |
| `logs/run_2026-09-19/embed_main.sh` | 333 B | no |
| `logs/run_2026-09-19/embed_pilot.log` | 1.6 KB | no |
| `logs/run_2026-09-19/embed_pilot.sh` | 195 B | no |
| `logs/run_2026-09-19/lab_features.log` | 60 B | no |
| `logs/run_2026-09-19/notes_index.log` | 1.6 KB | no |
| `logs/run_2026-09-19/notes_tfidf.log` | 234 B | no |
| `logs/run_2026-09-19/outpt_labs.log` | 39 B | no |
| `logs/run_2026-09-19/packet_dryrun.log` | 874 B | no |
| `logs/run_2026-09-19/packet_feasibility.log` | 185 B | no |
| `logs/run_2026-09-19/pip_install.log` | 787 B | no |
| `logs/run_2026-09-19/pip_install.sh` | 454 B | no |
| `logs/run_2026-09-19/precision_forecast.log` | 1.3 KB | no |
| `logs/run_2026-09-19/pytest.log` | 23 B | no |
| `logs/run_2026-09-19/trivial.log` | 0 B | no |

## `test files` — not credentialed

open-access MIMIC-IV demo data (per .gitignore comment); git-ignored

| Sub-path | Files | Size |
|---|---:|---:|
| `test files/.DS_Store` | 1 | 6.0 KB |
| `test files/mimic-iv-clinical-database-demo-2.2` | 35 | 15.5 MB |
| `test files/mimic-iv-clinical-database-demo-2.2.zip` | 1 | 15.4 MB |
| `test files/mimic-iv-ed-demo-2.2` | 8 | 111.8 KB |
| `test files/mimic-iv-ed-demo-2.2.zip` | 1 | 95.5 KB |

| File | Size | Tracked |
|---|---:|---|
| `test files/.DS_Store` | 6.0 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2.zip` | 15.4 MB | no |
| `test files/mimic-iv-ed-demo-2.2.zip` | 95.5 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/LICENSE.txt` | 25.2 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/README.txt` | 978 B | no |
| `test files/mimic-iv-clinical-database-demo-2.2/SHA256SUMS.txt` | 2.9 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/demo_subject_id.csv` | 911 B | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/admissions.csv.gz` | 10.8 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/d_hcpcs.csv.gz` | 498.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/d_icd_diagnoses.csv.gz` | 1.7 MB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/d_icd_procedures.csv.gz` | 1.0 MB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/d_labitems.csv.gz` | 13.2 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/diagnoses_icd.csv.gz` | 23.6 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/drgcodes.csv.gz` | 7.3 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/emar.csv.gz` | 717.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/emar_detail.csv.gz` | 676.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/hcpcsevents.csv.gz` | 963 B | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/labevents.csv.gz` | 1.9 MB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/microbiologyevents.csv.gz` | 79.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/omr.csv.gz` | 16.9 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/patients.csv.gz` | 1.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/pharmacy.csv.gz` | 492.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/poe.csv.gz` | 596.9 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/poe_detail.csv.gz` | 26.0 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/prescriptions.csv.gz` | 592.2 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/procedures_icd.csv.gz` | 6.4 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/provider.csv.gz` | 147.7 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/services.csv.gz` | 5.0 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/hosp/transfers.csv.gz` | 22.9 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/caregiver.csv.gz` | 42.4 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/chartevents.csv.gz` | 5.3 MB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/d_items.csv.gz` | 55.7 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/datetimeevents.csv.gz` | 116.6 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/icustays.csv.gz` | 5.5 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/ingredientevents.csv.gz` | 587.1 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/inputevents.csv.gz` | 769.8 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/outputevents.csv.gz` | 94.2 KB | no |
| `test files/mimic-iv-clinical-database-demo-2.2/icu/procedureevents.csv.gz` | 43.8 KB | no |
| `test files/mimic-iv-ed-demo-2.2/LICENSE.txt` | 25.2 KB | no |
| `test files/mimic-iv-ed-demo-2.2/SHA256SUMS.txt` | 577 B | no |
| `test files/mimic-iv-ed-demo-2.2/ed/diagnosis.csv.gz` | 8.8 KB | no |
| `test files/mimic-iv-ed-demo-2.2/ed/edstays.csv.gz` | 6.1 KB | no |
| `test files/mimic-iv-ed-demo-2.2/ed/medrecon.csv.gz` | 38.7 KB | no |
| `test files/mimic-iv-ed-demo-2.2/ed/pyxis.csv.gz` | 12.1 KB | no |
| `test files/mimic-iv-ed-demo-2.2/ed/triage.csv.gz` | 5.4 KB | no |
| `test files/mimic-iv-ed-demo-2.2/ed/vitalsign.csv.gz` | 14.9 KB | no |

## `docs/tables` — aggregate derivative

aggregate result tables; .md tracked, .csv git-ignored by the *.csv pattern; small cells suppressed by project rule

| File | Size | Tracked |
|---|---:|---|
| `docs/tables/aim1c_level1_age_band.csv` | 2.0 KB | no |
| `docs/tables/aim1c_level1_age_band.md` | 2.3 KB | yes |
| `docs/tables/aim1c_level1_gender.csv` | 848 B | no |
| `docs/tables/aim1c_level1_gender.md` | 1.5 KB | yes |
| `docs/tables/aim1c_level1_insurance.csv` | 2.0 KB | no |
| `docs/tables/aim1c_level1_insurance.md` | 2.5 KB | yes |
| `docs/tables/aim1c_level1_language.csv` | 7.8 KB | no |
| `docs/tables/aim1c_level1_language.md` | 6.0 KB | yes |
| `docs/tables/aim1c_level1_race.csv` | 10.6 KB | no |
| `docs/tables/aim1c_level1_race.md` | 10.5 KB | yes |
| `docs/tables/table0.csv` | 638 B | no |
| `docs/tables/table0.md` | 2.1 KB | yes |
| `docs/tables/table1.csv` | 5.8 KB | no |
| `docs/tables/table1.md` | 7.4 KB | yes |
| `docs/tables/table2.csv` | 2.7 KB | no |
| `docs/tables/table2.md` | 3.8 KB | yes |
| `docs/tables/table3.csv` | 480 B | no |
| `docs/tables/table3.md` | 1.0 KB | yes |
| `docs/tables/table4.csv` | 345 B | no |
| `docs/tables/table4.md` | 635 B | yes |
| `docs/tables/tableS1.csv` | 1.5 KB | no |
| `docs/tables/tableS1.md` | 2.1 KB | yes |
| `docs/tables/clean/table1.csv` | 5.8 KB | no |
| `docs/tables/clean/table1.md` | 7.4 KB | yes |
| `docs/tables/clean/table2.csv` | 2.7 KB | no |
| `docs/tables/clean/table2.md` | 3.8 KB | yes |
| `docs/tables/clean/table3.csv` | 480 B | no |
| `docs/tables/clean/table3.md` | 1.0 KB | yes |
| `docs/tables/clean/table4.csv` | 345 B | no |
| `docs/tables/clean/table4.md` | 635 B | yes |
| `docs/tables/clean/tableS1.csv` | 1.5 KB | no |
| `docs/tables/clean/tableS1.md` | 2.1 KB | yes |

## Hugging Face cache (model checkpoints only)

| Model directory | Size |
|---|---:|
| `/Users/betsylujan/.cache/huggingface/hub/models--emilyalsentzer--Bio_ClinicalBERT` | 831.4 MB |

## `.venv`

Python environment, 1.7 GB. Not data.
