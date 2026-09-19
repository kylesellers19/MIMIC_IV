#!/bin/zsh
# MASLD / MIMIC-IV — pipeline stages in order.
#
# THIS SCRIPT IS A MANIFEST, NOT A ONE-CLICK RUN. It is intentionally not executed as a whole:
# several stages take hours, some were frozen and tagged at a point in time and must not be re-run
# casually (the note phenotype, the population lock, the 400-chart draw), and the final packet
# generation must wait for clinician sign-off. Run stages individually, in this order, reading the
# document each one writes before moving on.
#
# Prerequisites: .venv created, `pip install -r requirements.txt`, credentialed MIMIC-IV v3.1 (hosp)
# and MIMIC-IV-Note v2.2 (note) verified under data/raw/ (see README).
#
# Every command below goes through scripts/run0919_env.sh, which sets PYTHONPATH, disables Hugging
# Face telemetry, and points DYLD_LIBRARY_PATH at the OpenMP library bundled with torch.
set -euo pipefail
cd "$(dirname "$0")"
RUN=scripts/run0919_env.sh

# ---- 1. Data quality (Kahn framework) -> docs/data_quality_report.md -----------------------------
$RUN scripts/dq_audit.py
$RUN scripts/conformance.py
$RUN scripts/plausibility_atemporal.py
$RUN scripts/plausibility_temporal.py
$RUN scripts/completeness_differential.py
$RUN scripts/dq_race.py

# ---- 2. Cleaning: null-not-drop -> docs/cleaning_execution.md ------------------------------------
$RUN scripts/clean_population.py

# ---- 3. Population lock -> docs/analysis_population.md, docs/tables/table0.md ---------------------
# FROZEN. Re-running changes the analysis population and invalidates everything downstream.
$RUN scripts/lock_population.py

# ---- 4. Note phenotype -> docs/note_phenotype_spec.md --------------------------------------------
# FROZEN and git-tagged (note-phenotype-v1.1.0) before the 2x2 was built. Behaviour report only.
$RUN scripts/note_phenotype.py
$RUN -m pytest -q tests/

# ---- 5. Code x note 2x2 and the 400-chart sampling frame -> docs/aim1a_crosstab.md ----------------
# FROZEN: aim1a_sample.parquet is the master key for the chart review. Do not redraw.
$RUN scripts/build_2x2.py
$RUN scripts/aim1a_report.py

# ---- 6. Pre-adjudication descriptives ------------------------------------------------------------
$RUN scripts/drug_classes.py
$RUN scripts/cmrf.py
$RUN scripts/predef_etio_metab.py
$RUN scripts/note_historical.py
$RUN scripts/imaging_denominator.py
$RUN scripts/comorbid_cluster.py
$RUN scripts/sld_report.py
$RUN scripts/make_tables.py

# ---- 7. Splits with a gold holdout -> docs/aim1b_splits.md ----------------------------------------
# Must run AFTER the pre-specified plan is committed and BEFORE any model exists.
$RUN scripts/run0919_phase2_splits.py

# ---- 8. Sensitivity analyses and validation ------------------------------------------------------
$RUN scripts/run0919_sens_5719.py
$RUN scripts/run0919_charlson_validation.py
$RUN scripts/run0919_notes_index.py          # ~2 min; per-note flags and lengths, no text
$RUN scripts/run0919_loose_ends_43_44.py
$RUN scripts/run0919_cohort_flow.py
$RUN scripts/run0919_outpt_labs.py
$RUN scripts/run0919_avail_windows.py

# ---- 9. Equity audit, level 1 -> docs/aim1c_level1.md ---------------------------------------------
$RUN scripts/run0919_aim1c_level1.py

# ---- 10. Reference-standard machinery -------------------------------------------------------------
$RUN scripts/run0919_precision_forecast.py
$RUN scripts/run0919_packet_feasibility.py
$RUN scripts/make_adjudication_template.py
$RUN scripts/assign_reviewers.py
$RUN scripts/make_reviewer_packets.py --dryrun      # generates, leak-checks, then deletes
$RUN scripts/run0919_phase6_docs.py
# FINAL packet generation — only after the criteria are signed off and reviewers are credentialed:
#   $RUN scripts/make_reviewer_packets.py --out data/processed/adjudication/packets

# ---- 11. Notes text and embeddings (hours) --------------------------------------------------------
$RUN scripts/run0919_notes_text.py --pilot
$RUN scripts/run0919_embed.py --pilot --budget_hours 5      # measures throughput, sizes the subsample
$RUN scripts/run0919_notes_text.py --subsample 13000
$RUN scripts/run0919_embed.py --variant S                   # resumable; shards under data/processed/notes_embeddings_v1/

# ---- 12. Models (hours) ---------------------------------------------------------------------------
$RUN scripts/run0919_lab_features.py
$RUN scripts/run0919_features.py
$RUN scripts/run0919_aim1b_structured.py
$RUN scripts/run0919_notes_tfidf.py
$RUN scripts/run0919_notes_embed_arm.py
$RUN scripts/run0919_fusion_lock.py                         # also locks and hashes gold-holdout predictions
$RUN scripts/run0919_aim1b_reports.py all

# ---- 13. Citations and admin ----------------------------------------------------------------------
$RUN scripts/verify_citations.py
$RUN scripts/run0919_data_inventory.py

# ---- 14. AFTER the chart review exists ------------------------------------------------------------
# $RUN scripts/aim1a_estimator.py --adjudication <completed form> --out docs/run_.../results/aim1a_gold.json
# $RUN scripts/aim1b_evaluate_gold.py --adjudication <completed form> \
#      --predictions data/processed/gold_holdout_predictions_v1.parquet --out <results.json>
# $RUN scripts/aim1b_gold_cv.py --adjudication <completed form> --out <results.json>
