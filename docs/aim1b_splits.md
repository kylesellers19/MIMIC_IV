# Aim 1b — subject-level splits with a gold holdout (splits_v1)

Produced by `scripts/run0919_phase2_splits.py`; numbers from `docs/run_2026-09-19/results/phase2_splits.json`. Seed 20260920. File `data/processed/splits_v1.parquet` (untracked).

**Rule.** GOLD_SUBJECTS = every subject with an admission in the 400-chart sample or the 20-chart training set. All their admissions form GOLD_HOLDOUT, which is never used for fitting, tuning, early stopping, threshold selection, recalibration, vocabulary building or dimensionality reduction. Of the remaining subjects, 20% form TEST (touched once per model) and 80% DEV, split into 5 subject-level folds. Partitioning is by subject, never by admission.

Silver label = note-positive under the primary definition (b). **Silver label — known error; not adjudicated truth; final performance requires the gold standard.**

| partition | admissions | subjects | note-positive | silver prevalence % | code-positive |
| --- | --: | --: | --: | --: | --: |
| GOLD_HOLDOUT | 2,865 | 411 | 1,161 | 40.52 | 479 |
| TEST | 75,124 | 32,142 | 5,426 | 7.22 | 1,015 |
| DEV | 296,003 | 128,566 | 21,239 | 7.18 | 4,246 |

| DEV fold | admissions | subjects | note-positive | silver prevalence % |
| --- | --: | --: | --: | --: |
| 0 | 58,048 | 25,714 | 3,971 | 6.84 |
| 1 | 59,331 | 25,713 | 4,288 | 7.23 |
| 2 | 59,358 | 25,713 | 4,381 | 7.38 |
| 3 | 59,804 | 25,713 | 4,201 | 7.02 |
| 4 | 59,462 | 25,713 | 4,398 | 7.4 |

GOLD_HOLDOUT admissions by cell (definition b): code-/note- 1,612, code-/note+ 774, code+/note+ 387, code+/note- 92.

Checks: zero subject overlap between partitions and between folds (asserted in the script); every sampled and training subject is in GOLD_HOLDOUT.
