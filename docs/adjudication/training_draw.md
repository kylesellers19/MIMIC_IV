# Reviewer-training draw (20 charts) — run_2026-09-19

Produced by `scripts/run0919_phase2_splits.py`; numbers from `docs/run_2026-09-19/results/phase2_splits.json`.

**Purpose.** Before formal review, both reviewers adjudicate the same 20 charts (criteria §9) to calibrate against each other and to revise the criteria once. These charts are drawn **outside** the 400-chart sample: no subject with any admission in the 400-chart sample is eligible, so nothing learned here can touch the sample.

- Primary definition (b): v1.1.0, inpatient + outpatient radiology −365/+30 days.
- Allocation in proportion to the main sample: code−/note+ 8 · code+/note+ 4 · code+/note− 3 · code−/note− 5 (total 20; 20 distinct subjects).
- Seed 20260919. Blinded IDs T001–T020 assigned after a seeded shuffle, so neither ID nor order encodes cell.
- Key stored beside the master key at `data/processed/aim1a_training_key.parquet` (untracked, credentialed).
- The allocation is revisable; nothing is estimated from this set.
