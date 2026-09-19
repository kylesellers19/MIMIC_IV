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
