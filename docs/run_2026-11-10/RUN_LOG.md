# Run log — run_2026-11-10 (unattended overnight run)

What was done and why, one phase at a time. Numbers live in `results/`, written by the scripts named here. The instructions are `RUN_FILE.md` in this folder. Decision tiers: Tier 1 is logged here in one line; Tier 2 is logged under "Deviations"; Tier 3 goes to `DECISIONS_FOR_KYLE.md` and is never decided.

## Phase 0 — preflight

- **Position.** On `run/2026-09-19`, local equal to `origin/run/2026-09-19` after `git fetch`. Uncommitted and untracked path names are listed in `results/preflight.json` (`scripts/run1110_preflight.py`).
- **Frozen artifacts.** `scripts/run1110_frozen_hashes.py --when start` wrote `results/frozen_hashes_start.json`. Every file named in `docs/llm_gold_lock.md` and `docs/aim1b_locked_predictions.md` equals its recorded hash. The sealed GOLD_HOLDOUT files were hashed as bytes and not opened as data.
- **Integrity gate and tests.** `scripts/run0919_integrity_gate.py` and `pytest -q`: results in `results/preflight.json`.
  - Tier 1: the gate rewrote September's `integrity_gate.json` with two keys in a different order and no value changed. The file was restored from git, so the past run's record is untouched.
- **Local model.** Ollama version, the digest of `gemma4:26b`, the server log's cloud-disabled line, the listener address on port 11434 and `fdesetup status` are recorded in `results/preflight.json`. All match Section 1 of the run file.
- **Permissions exercised.** A commit (this one), `git push --dry-run`, one model call on an invented sentence, one request each to the Crossref and NCBI citation APIs, a macOS notification, and a browser-tool status call. All answered.
- **Tier 1 choices.**
  - The frozen set for this run is September's five files plus the training key, the splits, both lock JSON files and both lock documents; the locked set is every file the two locks name.
  - Pushing starts in Phase 1, once the gate exists. The Phase 0 commit stays local until then.
  - A `STATE.json` helper (`scripts/run1110_state.py`) records each phase's status, commit and times.

## Deviations

(none yet)
