# Reviewer assignment — 400-chart sample

Produced by `scripts/assign_reviewers.py` (seed 20260921); numbers from `docs/run_2026-09-19/results/reviewer_assignment.json`.

Design: 2 reviewers. 100 charts are reviewed independently by both reviewers; the remaining 300 are split evenly by a stratified split within each sampling cell. Each reviewer's presentation order is an independent seeded shuffle, so neither the order nor the ID reveals the cell or whether a chart is double-reviewed. Total adjudications: 500 (plus the 20-chart training round, done by both reviewers).

| reviewer | charts | code+/note+ (A) | code−/note+ (B) | code+/note− (C) | code−/note− (D) | training charts |
| --- | --: | --: | --: | --: | --: | --: |
| reviewer1 | 250 | 48 | 96 | 40 | 66 | 20 |
| reviewer2 | 250 | 47 | 97 | 40 | 66 | 20 |

Per-cell counts include each reviewer's share of the double-reviewed charts; which IDs those are is held only in the untracked master key and is not shown to reviewers or recorded here.

Spearman correlation between presentation order and cell index: reviewer 1 -0.01, reviewer 2 0.038 (near zero, as expected from an independent shuffle).

Outputs (untracked, credentialed, beside the master key): `data/processed/adjudication/reviewer_assignment.parquet` (review_id, reviewer, order) and the per-reviewer blank forms `form_reviewer1.xlsx` / `form_reviewer2.xlsx` (250 sample rows each in that reviewer's order, plus the training sheet).

**Revisable.** If the number of reviewers changes, the assignment is re-derived by rerunning the script with a revised split rule under the same seed; nothing downstream depends on this assignment until adjudication begins.
