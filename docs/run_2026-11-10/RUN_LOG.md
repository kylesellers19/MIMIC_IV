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

## Phase 1 — exposure risk and push gate

- **`.gitignore`.** The uncommitted negation line for `diagnostics/**/*.csv` was removed; a comment now states the convention. Every CSV is ignored.
- **Heading tables moved.** The six CSVs in `diagnostics/section_rule_v2/` that have a `heading` field were moved to `data/processed/section_rule_v2_private/`. They were inspected by column shape only; no value was printed.
- **Aggregate diagnostics.** `scripts/run1110_diagnostics_json.py` wrote four counts-only files under `results/` (`diag_*.json`). Counts 1–10 read `<11`; a second cell is withheld wherever a published total or a neighbouring column would give the small count back by subtraction. The four CSVs were checked for note text by the gate's functions before they were opened.
- **Push gate.** `scripts/run1110_push_gate.py`, checks (a)–(g), with tests on synthetic fixtures in `tests/test_run1110_push_gate.py`. It reuses the September audit's patterns and `classify_token`.
  - Tier 1: text checks run on the added lines of every file that differs between the remote branch and the index.
  - Tier 1: real identifiers are read from the raw admissions and patients tables, so the check covers every MIMIC identifier, not only the analysis population.
  - Tier 1: check (e) also covers count-like JSON keys.
  - Tier 1: the comparison text for (d3) is the dev/test extractor output. GOLD_HOLDOUT sentences are sealed and are not read.
- **What the gate found on first use.** Two of the files listed for commit fail check (d3) and were held back (BLOCKERS B-01). An audit of the already-public base with the same rule is BLOCKERS F-01.
- **Tag.** Annotated tag `llm-gold-lock-v1` on the lock commit `41b155f`, pushed.

## Deviations

- **Phase 1.2 — six files moved, not eight.** The run file says eight heading-text CSVs and names six. Six files in the folder have a `heading` field holding note headings; those were moved. The other two CSVs there are the aggregates Phase 1.3 names (one is keyed by the study's own sub-heading list, the other has no heading field).
- **Phase 1.4 — three stated exemptions in gate check (d).** The run file lists none. A 30-character rule with no exemption fails on published disease names and on text the repository already shows. The exemptions are: text already at the remote base, lines marked as test fixtures, and matches lying inside a listed published disease name. This follows the September audit, which exempted the study's own instrument text. Anything else that is flagged is reworded.
- **Phase 1.6 — two listed files not committed.** `scripts/llm_timing_test.py` and `docs/adjudication/criteria_revision_proposal.md` fail the gate (B-01).
