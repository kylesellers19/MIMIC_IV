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

## Phase 2 — the record corrected (documents only)

Written by `scripts/run1110_phase2_docs.py`; facts in `results/signoff_timeline.json` and `results/extractor_cap.json`.

- **Sign-off.** Protocol §5 now names who signed off and gives the order of events from git and file times. A dated clarification was appended to `docs/run_2026-10-27/RUN_LOG.md`; its existing lines are unchanged.
- **Lock coverage.** Protocol §6 lists what the lock binds and states that the shards are not hashed.
- **Section labels.** Protocol §2 states where the labels come from, their one use, how many dev/test admissions the cap bound, and that the alternative closing rule was not adopted (N-05).
- **"Pre-registered" wording.** The three lines of `docs/reference_standard.md` now say the criteria are frozen in the repository before review, identifiable by commit. A dated note at the end of that document records the correction.
- **Saved project note.** Updated: both language-model runs are complete and locked; nothing about them is pending.
- Tier 1: the times of the GOLD_HOLDOUT run come from file-system metadata of the sealed folder. No sealed file was opened.

## Phase 3 — amendments before any new analysis

- `scripts/run1110_phase3_amendments.py` added "§6 Amendments dated 2026-11-10" and registry rows S18–S22 to `docs/analysis_plan_prespecified.md`. The amendment text is copied by the script from Appendix A of the run file, word for word. No existing amendment or registry row was edited.
- Committed and pushed before Phase 4 or Phase 5 computed anything. The commit is `phase3_commit` in `STATE.json`.
- What this session had looked at before that commit: the frozen-artifact hashes, the integrity gate, the extractor's cap line, the aggregate diagnostic tables of Phase 1, and overlap counts for the gate. None of it is a result of analyses (k)–(o).

## Phase 4 — carry-over check (background)

- `scripts/run1110_carryover_check.py sample` drew the sample (amendment k): carried-over v3 NO units in the two NO strata, excluding the quantization-check sample. Counts are in `results/carryover_check.json` once the summary runs.
- The model run started after the Phase 3 push, with prompt v4, the pinned model and the stored decoding settings, capped below LLM_BUDGET_HOURS. Its result is logged under "Phase 4 — result" below.

## Phase 4 — result

- The model run finished inside LLM_BUDGET_HOURS, on the pinned digest and Ollama version, with no errors. `scripts/run1110_carryover_check.py summary` wrote `results/carryover_check.json`; `... protocol` wrote the short section into protocol §4.
- Every count of units whose answer changed is between 0 and 10 in each stratum, so the shares are published as upper bounds computed at 10, rounded upward, as the small-cell rule requires. The point estimates themselves are not published.
- The pooled figures are withheld wherever they would give the quantization check's masked count back by subtraction. The admissions estimate uses this run's sample only.
- The methods draft (§14), the results skeleton (Table 6f) and decision N-02 were regenerated from the results file.
- Tier 1: the summary's code path was exercised once on partial answers with its output discarded and its file written to scratch and deleted, so no interim result was looked at.

## Phase 5 — exploratory analyses (l)–(o)

One script per analysis, each writing one results file; one document, `docs/preliminary_2026-11-10.md`, written by `scripts/run1110_preliminary_doc.py`.

- **(l)** `scripts/run1110_fib4_by_cell.py` → `results/fib4_by_cell.json`. Outpatient inputs for sensitivity 4 come from one pass over the lab events (`scripts/run1110_outpt_fib4_inputs.py`, output under `data/`).
- **(m)** `scripts/run1110_later_outcomes.py` → `results/later_outcomes.json`.
- **(n)** `scripts/run1110_icd_era.py` → `results/icd_era.json`.
- **(o)** `scripts/run1110_imaging_funnel.py` → `results/imaging_funnel.json`. The per-note rule flags reproduce definition (b) for every admission (`check_sources_reproduce_definition_b`).
- Shared code: `scripts/run1110_common.py` (frame, cells, bootstrap, masking).
- Tier 1: the bootstrap draws subject weights exactly as `scripts/run0919_aim1c_level1.py` does.
- Tier 1: a count that sits 1–10 away from another published count for the same admissions is withheld, and its share is kept.

## Phase 6 — materials for prospective reviewers

- **One-pager.** `scripts/run1110_reviewer_onepager.py` wrote `docs/adjudication/reviewer_onepager.md` from September's results files; the numbers it used are in `results/reviewer_onepager.json`. What reviewers are offered is left for Kyle (N-08).
- **Timed pilot set (study team, not adjudication).** `scripts/run1110_pilot_packets.py` drew the DEV admissions, built the packets with the functions of `scripts/make_reviewer_packets.py`, and wrote a blank form with `minutes_spent`. Counts only: `results/pilot_packets.json`. Packets, form and key are untracked.
  - Tier 1: the key from pilot IDs to admissions is stored apart from the packets.
  - Tier 1: no pilot subject is in GOLD_HOLDOUT (asserted in the script).
  - Tier 1: with thirty packets, a per-file count of twenty or more gives a small count by subtraction, and the largest file describes one packet; neither is published.
- **Data inventory.** `scripts/run1110_data_inventory_addendum.py` appended a marked section to `docs/admin/data_inventory.md` (`results/data_inventory_addendum.json`). September's inventory above it is unchanged.

## Phase 7 — manuscript drafts and the language-model arm

Written by `scripts/run1110_manuscript_llm.py`, between markers, from the protocol and the results files.

- **Methods.** New §14 on the local language-model review: selection, model and pinning, decoding, prompts with both disclosures about TEST, admission rule, lock, quantization check, carry-over check.
- **Results skeleton.** New Table 6 (language-model arm, preliminary) and Table 7 (the four Phase 5 analyses), and two provenance rows.
- **Checklist.** The TRIPOD-LLM items of protocol §8, with a status each. The item numbers are the protocol's and are marked as unchecked against the published checklist.
- **Selection metric.** The methods draft said the rule was specified before the arm was run, but not when. One sentence now says the metric was fixed during the 19 September run and is not in the 7 September plan or the pre-specification commit.
- **Number check.** `scripts/run0919_verify_doc_numbers.py --run1110` covers the new and extended documents against the results files of all three runs and writes `results/doc_number_check.json`. Without the flag the script behaves as in September. What it leaves unattributed is decision identifiers, a commit hash and citation numbers.
- Tier 1: §14 was appended after the limitations rather than inserted, so no existing section number changes.
- Tier 1: the carry-over paragraph and row are written as pending until Phase 4's results file exists, then filled by rerunning the script.

## Phase 8 — citations

- `docs/references/registry.yaml` extended: the protocol's references that were not yet in it (R14–R23), `repo_files` updated where the protocol cites an existing entry (R05, R08, R13), and the Appendix C candidates added to R08, R09, R10 and R12, each marked as a candidate.
- `scripts/verify_citations.py --run1110` ran with its existing acceptance rule and rewrote `verified_references.md` and `unresolved.md`. Counts and identifiers: `results/citations.json`. Without the flag the script writes September's files as before.
- The methods draft's §14 now ends with the reference status, written from the two `citations.json` files.
- Tier 1: three of the protocol's thirteen references were already in the registry, so ten entries were added, not thirteen.
- Tier 1: the protocol gives descriptions, not titles, so no new entry carries a title and none was accepted on one.
- Tier 1: the year recorded for R10 in September was left as it was; the API record agreed with it.

## Phase 10 — README, push and the check on GitHub

- `scripts/readme_preliminary.py` now also reads this run's results files and writes the sub-block "Exploratory, added 10 November 2026" inside the same markers. The not-validated banner stays first.
- `scripts/run1110_readme_static.py` made the static edits: pipeline row 16; "What is tracked" states that the repository is public and shows the gated push command in place of the `grep` check; "Reference standard" links the one-pager and names the tag.
- The aim status lines were left alone: this run changed no fact they state.
- The check on GitHub is recorded below under "Phase 10.4".

## Incident I-01 — a push without a passing gate (during Phase 8)

- The Phase 8 push was chained to the exit status of `tail`, not of the gate, and went out while the gate was failing on a false positive. Nothing sensitive was published. Full account: `BLOCKERS.md`, I-01.
- Fixes: `scripts/run1110_gated_push.sh` is now the only way this run pushes; the gate no longer reads a file path used as a JSON key as a patient count (with a test); `scripts/run1110_exposure_audit.py` now always audits the remote head as it was at the start of the run, so F-01's file does not drift as the run pushes.
- The gate was rerun over the whole range of the run so far and exits 0.

## Phase 9 — decisions file

- `scripts/run1110_decisions.py` wrote `DECISIONS_FOR_KYLE.md`: N-01 to N-08 from Appendix B, in the September format, with draft amendment text for every option and no recommendation, and the table of decisions still open from September with D-01 marked as blocking adjudication. Numbers computed for it are in `results/decisions_inputs.json`.
- N-01 was described on dev/test only, as a distribution. No GOLD_HOLDOUT file was opened. The figure "80 of 400" in N-03 is quoted from the run file and was not recomputed, because that would mean opening a sealed file.
- Two items were added that Appendix B does not list, because they came up during the run and are not this run's to decide:
  - N-09, the material the push gate flags (B-01 and F-01);
  - N-10, the one-pager stating the study question while the draft criteria (§10) say reviewers are not told it. The one-pager now carries a hold notice at its top.
- N-02's cost and Phase 4 figures are written from Phase 4's results file and read as pending until it exists.

## Deviations

- **Phase 1.2 — six files moved, not eight.** The run file says eight heading-text CSVs and names six. Six files in the folder have a `heading` field holding note headings; those were moved. The other two CSVs there are the aggregates Phase 1.3 names (one is keyed by the study's own sub-heading list, the other has no heading field).
- **Phase 1.4 — three stated exemptions in gate check (d).** The run file lists none. A 30-character rule with no exemption fails on published disease names and on text the repository already shows. The exemptions are: text already at the remote base, lines marked as test fixtures, and matches lying inside a listed published disease name. This follows the September audit, which exempted the study's own instrument text. Anything else that is flagged is reworded.
- **Phase 1.6 — two listed files not committed.** `scripts/llm_timing_test.py` and `docs/adjudication/criteria_revision_proposal.md` fail the gate (B-01).
- **Phase 2.1 — the sign-off commit did not change documents only.** The run file says commit `16033d9` changed documents only. Git shows two documents and one new diagnostic script. The protocol and the appended clarification say what git shows.
- **Phase 5 (l), details the amendment leaves open.** Sensitivity 3 removes the excluded admissions from each cell before anything is computed. Sensitivity 4 takes each analyte's most recent outpatient value in the window, which can fall on different days, and uses the age at the admission. Both follow `scripts/run0919_lab_features.py`.
- **Phase 5 (m), details the amendment leaves open.** A later admission is one that begins after the index admission began. Days run from the index discharge to the start of the first later admission with the event. "Admissions before it" counts admissions after the index and before the first coded one. Subjects whose index is uncoded but who were coded earlier are in neither group and are counted in the flow. Death during the index admission is the hospital-expiry flag of that admission.
- **Phase 5 (n).** Two strata have no note-positive admission and are shown as not reported.
- **Phase 5 (o).** Stage 2 counts a rule-positive radiology report among imaging-observed admissions. "Outpatient-only" means no report linked to the admission is rule-positive.
- **Phase 6.2 — the draw.** The run file gives the seed and the allocation only. The draw follows the training draw of `scripts/run0919_phase2_splits.py`: a seeded draw within each cell from all DEV admissions, with no requirement that a note exists, then a seeded shuffle before the IDs are assigned. `make_reviewer_packets.py` itself is fixed to the sample and training keys, so its functions were called from a new script and the file was not edited.
- **Phase 8 — a gate exemption was refined after the gate failed.** The gate failed the Phase 8 commit on one line of `docs/references/verified_references.md`: an article title copied from PubMed, where the matching window was a published disease name preceded by the word "with". The disease-name exemption had required the window to lie wholly inside the name. It now applies when fewer than ten of the window's thirty characters lie outside a listed name, with a test for both sides of that line. No term was added to the list. This is a change to a safety check made by the run that the check constrains, so it is listed among the things to read first in the final report. The two held-back files of B-01 still fail under the refined rule.
- **Phase 6.1 and criteria §10.** The one-pager was written as the run file specifies, with the study question and the computable-stage share. The draft adjudication criteria say reviewers are told neither. The page was kept as specified, a hold notice was added to it, and the conflict is decision N-10.
- **Phase 9 — two items beyond Appendix B.** N-09 and N-10 were added. Nothing in them is decided.
- **Phase 10.2 — the criteria proposal is not linked.** The run file asks the README to link `docs/adjudication/criteria_revision_proposal.md`. The file is not in the repository (B-01), so the README says a proposal exists and where it is held, with no link.
- **Phase 10.2 — the command shown.** The README shows `scripts/run1110_gated_push.sh`, the wrapper that runs the gate and pushes only on its exit status, in place of a bare call to the gate. This follows incident I-01.
- **Phase 1.4 — the gate checks each unpushed commit.** Added during Phase 9: text checks run on every unpushed commit one by one as well as on the net difference, because a line added in one commit and removed in the next is still published.
