# Autonomous run file — run_2026-11-10

Unattended overnight run for the MASLD / MIMIC-IV repository (`~/Program_Devel/masld_mimic`, branch `run/2026-09-19`, public remote `kylesellers19/MIMIC_IV`).

**Kyle is asleep. Do not ask him anything, do not wait for him, and do not stop until Phase 11 is finished.** Your only message to him is the final one.

Read this whole file before doing anything. Then read, for conventions: `docs/run_2026-10-27/RUN_LOG.md`, `docs/llm_review_protocol.md`, `docs/analysis_plan_prespecified.md`, and `docs/run_2026-09-19/{DECISIONS_FOR_KYLE,BLOCKERS,FINAL_REPORT}.md`.

---

## 1. Parameters

| Name | Value |
| --- | --- |
| RUN_ID | `run_2026-11-10` (journal under `docs/run_2026-11-10/`, new scripts prefixed `run1110_`) |
| TOTAL_BUDGET_HOURS | 10 |
| LLM_BUDGET_HOURS | 2 (Phase 4 only) |
| PUSH | true (only through the gate in Phase 1) |
| SIGNOFF_NAME | `Kyle Sellers (study lead; not a clinician)` |
| FIX_PREREG_WORDING | true |
| BOOTSTRAP_REPS / CELL_FLOOR | 500 / 11 (unchanged from the plan) |
| SEED_CARRYOVER / SEED_PILOT | 20261110 / 20261111 |
| Study model | `gemma4:26b`, digest starting `08ae7ec1`, Ollama 0.34.2 |

---

## 2. Guardrails (non-negotiable)

1. **No note-derived text anywhere but `data/`.** Never print, echo, log, or write to a tracked file: note text, sentence text, headings taken from notes, or any row-level record. Scripts may read text in memory; only counts leave them. Silence third-party loggers before touching notes (see BLOCKERS B-04 of the September run).
2. **No identifiers.** No `hadm_id`, `subject_id`, `note_id`, review ID or sentence key in any output, log line, commit or message.
3. **Small cells.** Counts 1–10 appear as `<11`. Withhold any figure that lets a small count be recovered by subtraction.
4. **GOLD_HOLDOUT stays sealed.** Never open the files under `data/processed/llm_review/gold_v4/` or the locked prediction files except to hash them. No answer distribution, no rerun, no `--include-gold`. Every analysis that uses language-model labels runs on the dev/test notes subsample only.
5. **Frozen artifacts stay frozen.** `scripts/note_phenotype.py`, the sample, the splits, the locked predictions, the lock files. `scripts/masld_config.py` is append-only. Hash them at the start and at the end.
6. **Ollama.** No `ollama pull`, no update, no cloud model, no second server. If the version or digest differs from Section 1, skip Phase 4 and log a blocker.
7. **Git.** Stay on `run/2026-09-19`. Stage by explicit path only: never `git add -A`, `git add .` or `git commit -a`. Never force-push, rebase, amend pushed commits or rewrite history. Every push goes through the gate (Phase 1). The repository is **public**.
8. **Append-only records.** Past `RUN_LOG.md` files and the amendments already in the analysis plan are never edited. Corrections are appended with a date.
9. **Deletions.** Only files this run created under `data/processed/run_2026-11-10_scratch/`. Moving the files named in Phase 1 is allowed.
10. **Installs and network.** No system installs. `pip` only into `.venv`, only if a phase cannot run without it, logged. Network use: PyPI, the citation APIs `verify_citations.py` already uses, and `git` to the remote. Nothing derived from MIMIC leaves this machine.
11. **Browser.** If browser tools exist in this session they are **read-only** and limited to `github.com/kylesellers19/MIMIC_IV`. Never open GitHub's web editor, change a setting, or type anything into a page.
12. **No hand-typed numbers.** Every number in a document is written by a script into a results JSON under `docs/run_2026-11-10/results/`, and the document names the script and file.

---

## 3. Operating protocol

- **Decisions.**
  - *Tier 1* (implementation detail): decide, log one line in `RUN_LOG.md`.
  - *Tier 2* (an analysis detail this file leaves open): take the choice closest to what the repository already does, and log it under "Deviations".
  - *Tier 3* (a definition, a population, a primary analysis, or what the paper claims): **never decide.** Write it to `DECISIONS_FOR_KYLE.md` as question, options, what each changes, what is blocked. No recommendation. Where it is cheap, compute every option.
- **Failures.** At most three attempts or 20 minutes per failure. Then write `BLOCKERS.md` (what failed, what was tried, what was skipped) and move to the next phase that does not depend on it.
- **Subagents.** If a subagent is cut short by a rate limit or an exhausted budget, do not wait it out and do not quietly finish its work some other way. Record what it completed in `STATE.json` and `BLOCKERS.md`, skip the rest of that phase, and move on.
- **Incidents.** If note text or an identifier reaches a tracked file, a staged file, a log outside `data/`, or your own context: contain it (unstage; delete only a file this run created), write an `INCIDENT` entry in `BLOCKERS.md`, set PUSH to false for the rest of the run, and continue with work that does not touch notes.
- **Hard halt.** If a frozen-artifact hash does not match in Phase 0 or Phase 11: stop all analysis, write the incident, go straight to the final report.
- **State.** Update `docs/run_2026-11-10/STATE.json` after every phase (status, commit, start and end time), so a relaunch can resume.
- **Budget.** Phases are in priority order. If time runs short, drop from the bottom of Phase 5, then Phase 6, then Phase 8. Phases 9–11 always run.
- **Commits.** One commit per phase, message prefix `run-1110:`. Push after each commit when PUSH is true and the gate passes.

---

## 4. Phases

### Phase 0 — Preflight (Kyle may still be at the desk for this one)

1. Start `caffeinate -i` in the background for the life of the run.
2. `git fetch`; confirm the branch and that local equals `origin/run/2026-09-19`. Record every uncommitted and untracked path (names only).
3. Create `docs/run_2026-11-10/` with `RUN_LOG.md`, `STATE.json`, `DECISIONS_FOR_KYLE.md`, `BLOCKERS.md`, `results/`. Commit this run file there as `RUN_FILE.md` if it is not already tracked.
4. Hash the frozen artifacts → `results/frozen_hashes_start.json`. Re-hash the four files named in `docs/llm_gold_lock.md` and every file named in `docs/aim1b_locked_predictions.md`; each must equal its recorded hash.
5. Run `scripts/run0919_integrity_gate.py` (expect 14/14) and `pytest -q`.
6. Local-model checks, recorded as facts in the run log: Ollama version; digest of `gemma4:26b`; the server log's cloud-disabled line; the listener on port 11434 is `127.0.0.1` only; `fdesetup status`.
7. Exercise every permission this run needs: a commit, `git push --dry-run`, one model call on an invented sentence, one request to a citation API, a macOS notification, and whether browser tools respond.
8. Print one line: `PREFLIGHT PASSED — safe to leave` or `PREFLIGHT ISSUES:` with the list. Continue either way.

### Phase 1 — Close the exposure risk and build the push gate

1. **`.gitignore`.** Remove the uncommitted line `!diagnostics/**/*.csv`. Every CSV stays ignored, as the repository's convention already says.
2. **Move the eight heading-text CSVs** in `diagnostics/section_rule_v2/` (`tableA_closing_headings`, `step2_wellformedness`, `step5_optionA_moves`, `step4_dirty_openers`, `step3_safety_check`, `step4_indings`, and any other whose `heading` field holds text from notes) to `data/processed/section_rule_v2_private/`. Their heading values are text from single notes.
3. **Aggregate diagnostics** (`cap_sweep_summary.csv`, `unclear_audit_summary.csv`, `tableB_continuing_headings.csv`, `step5_study_headers.csv`): re-express as JSON under `results/`, counts only, small cells masked. The CSVs stay on disk, ignored.
4. **`scripts/run1110_push_gate.py`**, reusing the functions in `scripts/run0919_final_audit.py`. It inspects every file that differs from `origin/run/2026-09-19` plus everything staged, and exits non-zero if any check fails:
   - (a) anything under `data/`, `models/`, `logs/`;
   - (b) any new `.csv`, `.parquet`, `.duckdb`, `.xlsx`, `.pkl` or other tabular or binary file;
   - (c) any 8-digit number equal to a real `hadm_id` or `subject_id` (seeds, byte counts and citation identifiers exempt, as in the September audit);
   - (d) note text: de-identification marks, report headers, any window of 30 or more characters matching a liver-extractor sentence or its neighbours, and any heading value of four or more words from the private heading CSVs;
   - (e) counts 1–10 in count columns;
   - (f) `masld_config.py` deletions or changed lines;
   - (g) a frozen-artifact hash that differs from the start.

   It prints counts and `file:line` only. Add tests with synthetic fixtures to `tests/`.
5. **Rule for the rest of the run:** `git push` only immediately after the gate exits 0 on the full unpushed range. If it fails, leave the commits local, write a blocker, keep working.
6. **Commit** (explicit paths, after the gate): `.gitignore`, the gate and its tests, `docs/adjudication/criteria_revision_proposal.md`, `scripts/llm_timing_test.py`, `liver_sentences_cap.py`, `liver_sentences_baseline.py`, `whitelist_change.diff`.
7. **Tag** the lock commit: annotated tag `llm-gold-lock-v1` on `41b155f`. Push the tag.

### Phase 2 — Correct the record (documents only)

1. **Sign-off.** In `docs/llm_review_protocol.md` §5, name who signed off (SIGNOFF_NAME) and give the timeline from git: rule text committed in `6338243` before the GOLD_HOLDOUT run started; lock committed in `41b155f`; the sign-off commit `16033d9` changed documents only. Append a dated clarification to `docs/run_2026-10-27/RUN_LOG.md`; do not edit its existing lines.
2. **Lock coverage.** Add to protocol §6 what the lock binds: the answers file (which contains the three probabilities), the admission labels, the extractor output, the manifest (prompt text, decoding settings), the model digest and the commit. State that the shards are not hashed.
3. **Section labels, as run.** Add to protocol §2: section labels come from the organ-subheading list `FINDINGS_SUBHEADINGS`; they only set priority under the 160-sentence cap; how many dev/test admissions the cap bound (count from the extractor's own report). State that an alternative closing rule was examined on 23–26 September and not adopted. Whether to run it as a sensitivity analysis is decision N-05.
4. **"Pre-registered" wording** (only if FIX_PREREG_WORDING): in `docs/reference_standard.md` lines 31, 94 and 126, replace the registration claim with what is true, following option 1 of D-05: criteria are frozen in the repository before review starts, identifiable by commit. No registry is claimed.
5. **Your own saved project note.** Update it: the dev/test and GOLD_HOLDOUT language-model runs are complete and locked; nothing about them is pending.

### Phase 3 — Amendments before any new analysis

Add "§6 Amendments dated 2026-11-10" and registry rows S18–S22 to `docs/analysis_plan_prespecified.md`, using the definitions in Appendix A word for word. Head the section: *"Assembled by Claude Code from the run file Kyle launched; not reviewed by Kyle at commit time; the purpose of this commit is the timestamp. Exploratory throughout."* Each amendment states what had already been seen (Appendix A lists it).

**Commit and push this before Phase 4 or 5 computes anything.** Record the hash in `STATE.json` as `phase3_commit`.

### Phase 4 — Carry-over check for the v3 answers (amendment k; background; LLM_BUDGET_HOURS)

Run in the background while Phase 5 proceeds. Follow `diagnostics/llm_review_audit/quant_check.py` for sampling, running and weighting. Outputs under `data/processed/llm_review/carryover_check/`; results in `results/carryover_check.json`; a short section appended to protocol §4.

### Phase 5 — Exploratory analyses (amendments l–o)

One script per analysis (`run1110_fib4_by_cell.py`, `run1110_later_outcomes.py`, `run1110_icd_era.py`, `run1110_imaging_funnel.py`), each writing a results JSON. One document, `docs/preliminary_2026-11-10.md`, written by `scripts/run1110_preliminary_doc.py`, with the banner used in `docs/llm_review_preliminary.md` (preliminary, exploratory, not validated against chart review) and a limitations paragraph per analysis.

### Phase 6 — Materials for prospective reviewers

1. **`docs/adjudication/reviewer_onepager.md`**, written by a script from results files. One page, plain language, no jargon left undefined: the question; what the computable stage shows; what a reviewer is asked to do and the hours (from `reviewer_brief.json`); the access requirement (own PhysioNet credentialing and signed data use agreement); blinding; what is already locked. Do not state what reviewers are offered; that is decision N-08.
2. **Timed pilot set for Kyle.** Draw 30 DEV admissions (seed SEED_PILOT), 11 / 6 / 5 / 8 across cells B / A / C / D under definition (b). Generate packets with `scripts/make_reviewer_packets.py` and a blank form with a `minutes_spent` column into `data/processed/pilot_packets_2026-11-10/`, blinded IDs P001–P030. Untracked. Record counts only, and add the folder to `docs/admin/data_inventory.md`. Label it everywhere as a study-team pilot, not adjudication.

### Phase 7 — Manuscript drafts catch up with the language-model arm

`docs/manuscript_methods_draft.md`, `docs/manuscript_results_skeleton.md` and `docs/tripod_ai_checklist.md` do not mention the language-model arm at all.

1. Methods: add a section on the local language-model review, drawn from the protocol (selection, model and pinning, decoding, prompts and how they were developed including the two disclosures about TEST, admission rule, lock, quantization check, carry-over check).
2. Results skeleton: add the language-model preliminary tables and the Phase 5 tables, each filled by script.
3. Checklist: add the TRIPOD-LLM items from protocol §8.
4. Confirm the methods draft says the model-selection metric (development out-of-fold AUPRC) was fixed during the 19 September run and not in the 7 September plan. If it does not, add that sentence.
5. Run `scripts/run0919_verify_doc_numbers.py` (extend it to the new documents) so no number is hand-typed.

### Phase 8 — Citations

Add to `docs/references/registry.yaml` the protocol's thirteen references and fuller strings for R08, R09, R10 and R12 (Appendix C gives candidate identifiers; they are candidates, not facts). Run `scripts/verify_citations.py`. Accept only by its existing rule. Rewrite `verified_references.md` and `unresolved.md`.

### Phase 9 — Decisions file

Write `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md` with the items in Appendix B, in the September format, no recommendations. For each item give the draft amendment text for every option, so the chosen one can be committed as written. End with a table of the decisions still open from September (D-01 to D-07, P6-01 to P6-06) and mark D-01 as the one that blocks the start of adjudication.

### Phase 10 — README, push, and the check on GitHub

1. Extend `scripts/readme_preliminary.py` to read `docs/run_2026-11-10/results/*.json` and add a sub-block **"Exploratory, added 10 November 2026"**: fibrosis index by cell, later outcomes, coding by period, the imaging funnel, the carry-over check. Same rules: script-written, small cells masked, the not-validated banner stays first.
2. Static edits to `README.md`:
   - pipeline table: add row 16 for this run (scripts and documents);
   - "What is tracked": state that the repository is public and that every push passes `scripts/run1110_push_gate.py`; show that command in place of the `grep` check;
   - "Reference standard": link `docs/adjudication/criteria_revision_proposal.md` and `docs/adjudication/reviewer_onepager.md`; name the tag `llm-gold-lock-v1`;
   - aim status lines: only where this run changed a fact.
3. Commit, run the gate, push.
4. **Check on GitHub.** If browser tools are available: open the repository page, confirm the rendered README shows the new sub-block and that the latest commit on the page equals local `HEAD`, and open the commit list to confirm no tabular or binary file was added. Read-only. If browser tools are not available, do the same check with `git ls-remote` and the raw README over HTTPS, and say so in the report.

   Do **not** edit the README in GitHub's web editor. That would skip the gate and the script-written-numbers rule, and leave the remote ahead of this machine.

### Phase 11 — Final audit, report, notification

1. Re-hash the frozen artifacts → `results/frozen_hashes_end.json`; compare with the start.
2. Run the gate once more over the whole run's range; run `pytest -q`.
3. `scripts/run1110_final_report.py` writes `docs/run_2026-11-10/FINAL_REPORT.md`: outcome in one paragraph; phases table with commits; the five things to read first; deviations; blockers and incidents; decisions waiting (new, then carried over); what is public now (commit range, tag) and what stayed local and why; gate results; disk used; hours used.
4. Commit, gate, push.
5. Send a macOS notification (`run_2026-11-10 finished`), stop `caffeinate`, and give Kyle one final message: five lines at most, pointing to `FINAL_REPORT.md`, with any incident stated first.

---

## Appendix A — Amendment text (use word for word in Phase 3)

Common to (l)–(o): exploratory; admission grain unless stated; primary definition (b) and the cells A (code+/note+), B (code−/note+), C (code+/note−), D (code−/note−) as in `docs/aim1a_crosstab.md`; subject-cluster bootstrap, 500 replicates, seed 20260919, 95% percentile intervals; a stratum is reported when its denominator is at least 11. None of these changes a primary analysis.

**(k) Carry-over check for v3 answers (S18).**
- *Question:* would the dev/test units that v3 answered NO, and that were carried into the merged v4 labels without being re-asked, still be answered NO by v4?
- *Sample:* distinct dev/test units whose stored answer is a carried-over v3 NO, in the two strata of the quantization check ("NO, fat word", "NO, other"); 1,500 per stratum, seed 20261110, excluding units already in the quantization-check sample.
- *Run:* prompt v4, the study model at its pinned digest, the stored decoding settings.
- *Report:* per stratum and population-weighted (Wilson bounds as in `quant_check.py`), the share whose v4 answer is not NO, and the share whose primary-label status changes. Report the quantization check's carried-over NO units separately and pooled. Estimate how many dev/test admissions would change label.
- *What it does not change:* no stored answer, label or result.
- *Already seen:* the quantization check's statement that over 99% of carried-over NO units kept their answer.

**(l) Fibrosis index by cell (S19).**
- *Measure:* FIB-4 = age × AST / (platelets × √ALT), approved itemids, age handled as in Table 3.
- *Primary:* first result per admission; by cell: computable n (%), median [IQR], share below 1.3, 1.3–2.67, above 2.67.
- *Sensitivity:* (1) lower cutoff 2.0 at age 65 and over; (2) last result per admission; (3) excluding admissions with AST or ALT above 200 U/L and admissions flagged alcohol, viral, other etiology or cirrhosis in `cmrf.parquet`; (4) most recent outpatient AST, ALT and platelets in the 365 days before admission, where all three exist.
- *Replicate:* dev/test notes subsample with the language-model phenotype (uncoded positive against coded positive).
- *Already seen:* Table 3 (FIB-4 by code status only).
- *Stated limitation:* FIB-4 is validated in outpatients; acute illness raises AST and lowers platelets; computability differs by cell.

**(m) Later outcomes after an uncoded mention (S20).**
- *Grain:* subject. *Index:* the subject's earliest note-positive admission.
- *Groups:* U, index code-negative with no earlier code-positive admission; C, index code-positive. Exclude subjects with a cirrhosis or HCC flag (`cmrf.parquet`, as already defined) at or before index, and subjects who died during the index admission.
- *Report per group:* subjects; subjects with at least one later admission; among those, the share with a later cirrhosis flag and a later HCC flag, with median [IQR] days from index discharge. For U only: the share later coded, days to the first coded admission, and admissions before it.
- *Intervals:* Wilson. No survival model.
- *Already seen:* the coding-inconsistency counts in `docs/predefinition_descriptives.md` Step 5.
- *Stated limitation:* only returns to this hospital are observed, so every figure is a floor.

**(n) Coding by period (S21).**
- *Measure:* among note-positive admissions, B/(A+B) by `anchor_year_group` and by the ICD version of the admission's diagnoses, each with the primary code set and with 571.9 removed (S7).
- *Already seen:* the ICD-version coefficient in the exploratory adjusted model of `docs/aim1c_level1.md`.
- *Stated limitation:* `anchor_year_group` is a three-year window assigned per patient.

**(o) Documentation funnel where the liver was imaged (S22).**
- *Population:* imaging-observed admissions (S3).
- *Stages:* (1) imaging-observed; (2) rule-positive in at least one radiology report, inpatient-linked or in the outpatient window; (3) of those, the discharge summary is also rule-positive; (4) the coded share among stage-3 yes and among stage-3 no. Also split stage 2 by inpatient against outpatient-only source.
- *Already seen:* the language-model documentation-pathway table in `docs/llm_review_preliminary.md`, and the note-source covariate in the exploratory adjusted model.

---

## Appendix B — Items for `DECISIONS_FOR_KYLE.md` (options only)

- **N-01 Admission-level probability for the language-model arm.** Maximum P(YES) over sentences with CURRENT or PAST timing; noisy-OR over those sentences; report the arm as a classifier only. Describe each on dev/test (distribution only; no gold). Must be fixed before any adjudication result is seen.
- **N-02 Prompt-version difference between dev/test and GOLD_HOLDOUT**, in light of Phase 4. Re-ask all carried-over NO units with v4 (about 84,000 units; give the hours at measured speed); keep the merged labels and report Phase 4; keep language-model output out of stacked-model training.
- **N-03 Sample admissions with no kept sentence** (80 of 400, all in the two note-negative strata). Report their errors as extractor misses, separately; or pool them into the language-model arm's error.
- **N-04 Note axis for Aim 1a.** The frozen rule; the language model; both.
- **N-05 The alternative section-closing rule.** Drop it; or run it as a dev/test-only sensitivity analysis.
- **N-06 Reviewer criteria against the locked prompt.** Build the crosswalk between the chart scale (Definite, Probable, Possible, Absent, Insufficient) and the sentence answers (YES, UNCLEAR, NO, with timing), and list every place they differ (for example ultrasound echogenicity, "likely" and "probable", ongoing diagnoses). Options: write the chart criteria from the clinical definition and report the differences; or align the chart criteria to the prompt's construct. Note that SIGNOFF_NAME is not a clinician, so clinician review of the admission rule is outstanding.
- **N-07 Registration** (updates D-04): a registration now could include the lock hashes and the tag.
- **N-08 What prospective reviewers are offered.** Left blank for Kyle.

---

## Appendix C — Candidate identifiers for Phase 8 (unverified; accept only if the API confirms first author, year and title)

- R08: Torgersen J, 2024, *Hepatology Communications* — DOI 10.1097/HC9.0000000000000468, PMID 38896066.
- R09: Alsentzer E, 2019, Clinical NLP Workshop — DOI 10.18653/v1/W19-1909.
- R10: Li Y, Clinical-Longformer — try DOI 10.1093/jamia/ocac225.
- R12: Johnson A, MIMIC-IV-Note v2.2, PhysioNet — try DOI 10.13026/1n74-ne17.

If the API does not confirm one, it stays in `unresolved.md` with what was tried.
