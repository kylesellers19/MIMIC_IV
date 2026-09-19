# Phase 10.1–10.3 working notes — manuscript drafts (run_2026-09-19)

## Purpose

Produce the three writing deliverables of Phase 10 from tracked results files only: the methods section, a TRIPOD+AI reporting-status audit, and a results skeleton whose table shells carry every computable-stage number and mark everything else as pending. The governing rule for this task was **invent nothing**: every number traceable to a JSON under `docs/run_2026-09-19/results/` or to a tracked document, every undetermined quantity written literally as `[PENDING]`, no bibliographic field written from memory.

## What was done

Created:

| file | what it is |
| --- | --- |
| `docs/manuscript_methods_draft.md` | Methods section, 13 numbered sections (data source and population → limitations). |
| `docs/tripod_ai_checklist.md` | TRIPOD+AI reporting-status audit, organized by section with locally-labelled rows. |
| `docs/manuscript_results_skeleton.md` | Table shells 1–5 with computable-stage numbers filled and pending cells marked. |

Appended (no rewriting; existing `## D-xx` style and numbering continued from the last free number, D-03):

- **D-04 · Public registration versus the repository's git audit trail.**
- **D-05 · The "pre-registered" wording that needs correcting.**

Sources read in full: `docs/analysis_population.md`, `note_coverage.md`, `tables/table0.md`, `aim1a_loose_ends.md`, `data_quality_report.md`, `sensitivity_5719.md`, `sql/masld_coded.sql`, `note_phenotype_spec.md`, `fatty_trigger_diagnostic.md` (headline sections), `aim1a_crosstab.md`, `sld_subclassification.md`, `imaging_denominator.md`, `reference_standard.md`, `aim1a_precision_forecast.md`, `adjudication_criteria.md`, `adjudication/packet_specification.md`, `adjudication/reviewer_assignment.md`, `adjudication/reviewer_brief.md`, `adjudication/data_dictionary.md`, `adjudication/training_draw.md`, `aim1c_level1.md`, `aim1b_splits.md`, `aim1b_notes.md`, `analysis_plan_prespecified.md`, `charlson_validation.md` (via RUN_LOG), `predefinition_descriptives.md` (CMRF section), `references/verified_references.md`, `references/unresolved.md`, `run_2026-09-19/RUN_LOG.md`, `BLOCKERS.md`, `DECISIONS_FOR_KYLE.md`, `STATE.json`, `phase10_notes.md`, `requirements.txt`, and the modelling scripts `run0919_aim1b_structured.py`, `run0919_notes_tfidf.py`, `run0919_notes_embed_arm.py`, `run0919_fusion_lock.py`, `run0919_features.py`.

Results JSONs read: `cohort_flow.json`, `integrity_gate.json`, `phase2_splits.json`, `embed_pilot.json`, `feature_classification.json`, `sens_5719.json`, `loose_ends_43_44.json`, `reviewer_assignment.json`, `reviewer_brief.json`, `aim1b_notes_tfidf.json`, `aim1b_structured.json`, `aim1c_level1.json` (via its rendered document), `aim1a_precision_forecast.json` (via its rendered document).

No file under `data/` or `models/` was opened. No patient-level row, note text, `subject_id`, `hadm_id` or `note_id` appears in any output. All cells below 11 are carried through as `<11` or as the source's stated range ("1–10" in the 571.9 sample-movement line), exactly as the source documents write them.

## Results

**Placeholder counts at completion:**

| file | `[PENDING` occurrences |
| --- | --: |
| `docs/manuscript_methods_draft.md` | 17 |
| `docs/tripod_ai_checklist.md` | 6 (plus 11 rows whose *status* is the word "pending") |
| `docs/manuscript_results_skeleton.md` | 65 |

**Timing during drafting.** The structured arm (`scripts/run0919_aim1b_structured.py`) **completed while section 10 was being written** (runtime 3,953 s). All three documents were revised to carry its real numbers: methods §10.3 and §10.4, results Table 4b with sub-tables 4b-i to 4b-v, and TRIPOD rows M-15, R-4 and R-5. The embedding job (`scripts/run0919_embed.py`) was still running at completion.

**Missing when the model section was written** (and still missing at hand-off):

| expected | status |
| --- | --- |
| `results/aim1b_notes_arm.json` | absent — embedding job still running |
| `results/aim1b_fusion.json` | absent — depends on the embedding job |
| `results/locked_predictions.json` | absent — depends on the fusion step |
| `docs/aim1b_structured.md` | absent — the results JSON exists, the rendered narrative document does not |
| `docs/aim1b_fusion.md` | absent |
| `docs/aim1b_locked_predictions.md` | absent |

Present and used: `results/aim1b_structured.json`, `results/aim1b_notes_tfidf.json`, `results/feature_classification.json`, `results/phase2_splits.json`, `results/embed_pilot.json`, `docs/aim1b_splits.md`, `docs/aim1b_notes.md`.

## Checks

- **Wording constraint honoured.** The word "pre-registered" (and "pre-registration") appears in `docs/manuscript_methods_draft.md` and `docs/tripod_ai_checklist.md` **only** inside explicit statements that the phrase must not be used and inside the record of where it currently appears. No tracked file was edited to remove it; the correction is logged as D-05.
- **Every filled number was read, not recalled.** Where a document and a results JSON could have disagreed, the JSON was used (see Disagreements below).
- **Citations.** Full bibliographic detail is given only for the nine API-verified entries in `docs/references/verified_references.md`. The four entries in `docs/references/unresolved.md` are cited author–year with an explicit "unverified reference" marker and a pointer to that file, in both the methods draft and its reference note.
- **Small-cell rule.** No count of 1–10 is written as an exact number anywhere in the three new files; every such cell reads `<11`, and ranges the source documents already state as "1–10" (the 571.9 sample-movement line) and "<11" (the packet leak-check table) are carried through verbatim.
- **Integrity anchors.** Every 2×2 cell, the recovery share (81.9%) and the corroboration share (87.6%) were taken from `integrity_gate.json` field `reproduced`, not from `docs/aim1a_crosstab.md`, so they carry the run's own reproduction rather than the earlier session's.
- The `phase1_commit` hash quoted in the methods draft (`e2a4e1e5b2bade9f7f8cb07a7d546a23e57b1b9b`) was read from `STATE.json`, field `phase1_commit`, not from the RUN_LOG's abbreviated form.

## Deviations

1. **The structured arm finished mid-draft**, so section 10 was written twice: once fully pending, then revised with real numbers. The three documents are internally consistent as they now stand.
2. **TRIPOD+AI item numbers are not asserted.** The official item numbering and item text were not available to this task, so `docs/tripod_ai_checklist.md` uses its own section-plus-label scheme (`T-1`, `M-7`, `R-5` …) and states once, at the top, that the mapping onto the published checklist must be done before submission. This follows the instruction not to invent item numbers.
3. **`docs/reference_standard.md` was not edited**, per the instruction, even though three of its lines assert a registration that does not exist. The methods draft uses the corrected framing and therefore *contradicts* that file; D-05 records this explicitly so the contradiction is not discovered later by a reader.
4. **`docs/note_coverage.md` was not edited**, even though its "the window is temporal and hard-edged" section is superseded. The methods draft says so in §2 and the results skeleton's Table 1 footnotes repeat it, and a TRIPOD row (M-4) tells the manuscript which files to cite for the window question instead.
5. **Table 3 in the results skeleton is deliberately abbreviated** (largest strata only), as the task specified, with a pointer to `docs/aim1c_level1.md` and `docs/tables/aim1c_level1_*.md` for the complete 33-race and 26-language tables.
6. **Small-cell rule applied to strata that the source document prints in full.** `docs/aim1c_level1.md` prints every cell count including values of 1–10 (for example ASIAN code+/note− = 9). The abbreviated Table 3 in the results skeleton writes all such cells as `<11`, per the project's small-cell policy, with a footnote saying so. The exact values remain in `docs/aim1c_level1.md` and in `results/aim1c_level1.json`; nothing was lost.
7. **The orchestrating run committed the three new files mid-draft** (commit `877ead3`, the Phase 7 structured-arm commit, swept them in). `docs/manuscript_methods_draft.md` happened to be in its final state at that moment; `docs/tripod_ai_checklist.md` and `docs/manuscript_results_skeleton.md` were committed *before* their structured-arm revision and therefore show as modified in the working tree, and `docs/run_2026-09-19/phase10_drafts_notes.md` is untracked. **Nothing was committed by this task.** The working tree holds the final content of all four files.
8. **`docs/predefinition_descriptives.md` uses a four-criterion CMRF operationalization** ("Dyslipidemia unascertainable 60.5%") while `docs/sld_subclassification.md` uses the final five-criterion one (hypertriglyceridaemia unascertainable 60.1%, low HDL 61.8%). These are different operationalizations, not a contradiction. The methods limitation quotes the **five-criterion** figures, because those match the CMRF implementation the study actually uses.

## Every `[PENDING]` left, and why

**In `docs/manuscript_methods_draft.md` (17):**

| where | placeholder | why |
| --- | --- | --- |
| §4, 571.9 | `[PENDING researcher decision D-01]` | Tier 3; must be settled before adjudication because weights are fixed at sampling time. |
| §5, freeze statement | `[PENDING researcher decision]` (re-tagging `note_phenotype.py` as v1.1.1 after the two-line CLEAN_POP repoint) | Tier 3 (tagging); no tag may be created by this run. |
| §9, adjudication criteria (×2) | `[PENDING clinician sign-off]` | D1–D8 are open; no chart may be adjudicated until they are signed off. |
| §9, adjudicated results | `[PENDING ADJUDICATION]` | The chart review has not occurred. |
| §10 status box, §10.3, §10.5, §10.6, §10.7 (×7) | `[PENDING — job still running at draft time]` | Embedding arm, fusion, locked predictions; and `docs/aim1b_structured.md` not yet rendered. |
| §10.5, notes-arm training strategy | `[PENDING researcher decision]` | Tier 3; the phase selects nothing. |
| §10.7, gold evaluation | `[PENDING ADJUDICATION]` | Requires the reference standard. |
| §10.8 item 1 | `[PENDING researcher decision D-02]` | Chunked BERT versus Clinical-Longformer. |
| §11, equity levels 2 and 3 | `[PENDING ADJUDICATION]`, `[PENDING — models still running]` | Weighted PPV by stratum needs gold labels; calibration by stratum needs the remaining models. |

**In `docs/tripod_ai_checklist.md` (6 `[PENDING` plus 11 rows with status "pending"):** title, abstract, funding, conflicts of interest, patient and public involvement, interpretation, implications, inter-rater agreement, and the reference-standard outcome definition — none of which can exist before the adjudication and the administrative information, which the repository does not hold at all. The inline `[PENDING]` markers are on the embedding-head selection outcome, the subgroup rendering, and the gold-standard performance rows.

**In `docs/manuscript_results_skeleton.md` (65):** the headline statement; Table 4b-v (subgroup rendering); Table 4c (embedding arm), 4d (fusion), 4e (locked predictions), 4f (gold-standard performance); and the whole of Table 5 — adjudication outcome by cell, the four weighted estimates with both interval types, the four kappa statistics plus disagreement count and measured minutes per chart, and six secondary adjudicated analyses. Plus `[PENDING researcher decision P6-01]` (Insufficient-information handling), `[PENDING clinician decision D1]` (positive collapse) and `[PENDING researcher decision P6-03]` / `[PENDING clinician decision D8 / P6-02]` (kappa weighting and disagreement resolution).

## Disagreements found between a document and a results JSON

1. **The "window" claim.** `docs/note_coverage.md` states that note coverage is "temporal and hard-edged" and that the analysable window is `anchor_year_group` 2008–2019. `docs/analysis_population.md`, `docs/tables/table0.md` and `results/cohort_flow.json` all establish that there is **no admission-year window** (coverage flat at ~67–70% by derived admission year) and decompose the exclusion by subject lineage instead. **Resolution: the JSON and the two later documents are used; `note_coverage.md` is cited only for note-table scale, outpatient-linkage counts and the differential-loss analysis, and the methods draft says explicitly that its window claim is superseded.** Already flagged in `docs/aim1a_loose_ends.md` §4.5; not resolved by editing, per the no-edit instruction.
2. **A one-admission subtotal discrepancy.** `docs/tables/table0.md` and `docs/analysis_population.md` both say the release-lineage exclusion "includes all 42,412 anchor-2020–2022 admissions". `results/cohort_flow.json` gives 42,414 admissions in that anchor group, of which 42,413 were removed. The main flow counts agree exactly; only this subtotal differs. **Resolution: the JSON's 42,414 / 42,413 are used in the methods draft, and the discrepancy is named there.**
3. **Sampling weights, rounded versus exact.** `docs/aim1a_crosstab.md` Step 4 prints weights as 152.0 / 62.8 / 10.2 / 3,454.5; `results/integrity_gate.json` and `docs/aim1a_precision_forecast.md` carry 151.9933 / 62.8375 / 10.1857 / 3454.53. This is rounding in a display table, not a disagreement, but the **exact values are used everywhere in the new documents** because the estimator uses them.
4. **Reviewer time estimate, superseded.** `docs/adjudication_criteria.md` offers ~10–18 minutes per chart and 85–150 reviewer-hours total; `results/reviewer_brief.json` and `docs/adjudication/reviewer_brief.md` give 18–21 minutes (full read) or 14–16 (focused read), 74–87 or 58–67 hours per reviewer. The criteria document itself states that its figure predates confirmation of packet contents against the data. **Resolution: the JSON-derived figures are used and the earlier estimate is described as superseded.**
5. **Cardiometabolic unascertainability, four- versus five-criterion.** `docs/predefinition_descriptives.md` reports "Dyslipidemia unascertainable 60.5%" under a four-criterion scheme; `docs/sld_subclassification.md` reports hypertriglyceridaemia 60.1% and low HDL 61.8% under the final five-criterion scheme with medications. Not a contradiction (different operationalizations), but the two could easily be confused in a manuscript. **Resolution: the five-criterion figures are used, and the methods draft names the operationalization alongside them.**

No disagreement was found between any number in `integrity_gate.json`, `cohort_flow.json`, `phase2_splits.json`, `sens_5719.json`, `loose_ends_43_44.json`, `aim1b_notes_tfidf.json` or `aim1b_structured.json` and the documents that render them.

## What Kyle should look at

1. **D-05.** Three lines in `docs/reference_standard.md` (31, 94, 126) assert a pre-registration that does not exist, and the same sentence is in an older methods draft in your claude.ai project. `docs/manuscript_methods_draft.md` was written with the corrected framing and therefore contradicts `reference_standard.md` as it currently stands. This is the one item in this phase that is about the accuracy of a claim rather than about a number.
2. **D-04.** Whether to register publicly at all, and if so, that a registration created now must disclose which results already existed. This governs what the paper may say about timing.
3. **§10.8 of the methods draft** — the full deviation list, twelve items. Check that nothing is missing and that you are content for each to appear in the paper.
4. **Table 4b-ii and 4b-iv of the results skeleton.** The pre-committed expectation H1b-i is only *partly* supported: one availability feature dominates the FS-A attribution (`liver_imaging_any_pre`, mean |SHAP| 0.675, roughly double the next) and FS-AVAIL alone out-discriminates the whole clinical set on AUROC, but availability features are only 28% of the FS-A top 25 and `n_diagnoses` sits fifteenth. Separately, the FS-A advantage collapses from 0.070 to 0.016 AUROC in the imaging-observed population. Both readings are written as "partly supported" and "consistent with", not as confirmation; check you agree with that framing before it hardens into prose.
5. **The four unverified references.** The VA/VACS steatosis NLP algorithm underpins the anatomical-scoping design and is currently cited with no author at all. Bio_ClinicalBERT, Clinical-Longformer and MIMIC-IV-Note likewise need full citation strings added to the repository so `scripts/verify_citations.py` can confirm them.
6. **Re-run the model section once the embedding, fusion and locked-prediction jobs finish.** Sections 10.5–10.7 of the methods, Tables 4c–4e of the results skeleton, and TRIPOD rows M-15/M-16/R-5 all have named placeholders waiting for exactly those files.
7. **`docs/tripod_ai_checklist.md`, the note at the top.** The item numbering is the drafter's own and must be mapped onto the published TRIPOD+AI checklist before submission, with any published item this file omits added.

---

# Phase 10.4 — filling the drafts once the notes, fusion and locked-prediction results existed

## Purpose

The three Phase 10 deliverables were written while the embedding job, the fusion stack and the locked-prediction step were still running, so every claim about them was left as `[PENDING — job still running at draft time]`. Those files now exist. This pass resolved every placeholder those files can resolve and left untouched every placeholder that genuinely needs the chart adjudication. The governing rule was unchanged: **invent nothing**; no number written from memory; no bibliographic field written from memory; the word "pre-registered" not introduced; cells below 11 written `<11`.

## Files edited

| file | edit |
| --- | --- |
| `docs/manuscript_methods_draft.md` | §10 status box rewritten; §10.5 embedding arm, §10.6 fusion and §10.7 locked predictions filled; deviations 13–17 added; §11 equity level 3 updated; limitation 7 (ConText) rewritten around the measured agreement; limitations 11 and 12 added and 11–13 renumbered to 13–15. |
| `docs/manuscript_results_skeleton.md` | Intro rewritten; Table 4b source line and Table 4b-v filled; Tables 4c, 4c-i, 4d, 4d-i, 4e filled; **Table 4g (hypothesis outcomes) added**; the Table 3 levels-2-and-3 line updated; provenance index rewritten for 4b–4g. |
| `docs/tripod_ai_checklist.md` | Status-vocabulary note, A-1, M-11, M-15, M-16, R-4, R-5, R-7, D-2 and blocker item 3 updated. |
| `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md` | **D-06** appended (what the manuscript may claim from the transformer-versus-TF-IDF comparison). Continued from the last free number, D-05. |

No other file was touched. Nothing was committed or tagged. No file under `data/` or `models/` was opened.

## Sources read for this pass

Results JSONs: `aim1b_notes_arm.json`, `aim1b_fusion.json`, `locked_predictions.json`, `context_agreement.json`, `notes_subsample.json`, `aim1b_notes_tfidf.json` (field `oof`, for the TF-IDF-versus-embedding comparison), `aim1b_structured.json` (field `subgroups`, for the level-3 equity counts), `doc_number_check.json`. Documents: `docs/aim1b_structured.md`, `docs/aim1b_notes.md`, `docs/aim1b_fusion.md`, `docs/aim1b_locked_predictions.md`, `docs/context_agreement.md`, `docs/run_2026-09-19/RUN_LOG.md` (Phases 3 stage 2, 6, 7, 8.1, 8.2/8.3, 9, stretch item 2), `STATE.json`, `docs/analysis_plan_prespecified.md` §1 and the amendment list, `DECISIONS_FOR_KYLE.md`, `scripts/run0919_verify_doc_numbers.py`, `scripts/run0919_embed.py`.

## Placeholder counts

| file | before | after | of which `[PENDING ADJUDICATION]` after |
| --- | --: | --: | --: |
| `docs/manuscript_methods_draft.md` | 17 | 14 | 6 |
| `docs/tripod_ai_checklist.md` | 6 | 3 | 2 |
| `docs/manuscript_results_skeleton.md` | 65 | 66 | 60 |

The results skeleton's count **rose by one** rather than falling, and that is the correct behaviour: seven `[PENDING — job still running at draft time]` markers were removed across Tables 4b-v, 4c, 4d and 4e, and the new Table 4g (hypothesis outcomes) introduced eight new markers, every one of them an honest `[PENDING ADJUDICATION]` on a hypothesis that cannot be evaluated without the chart review (H1a, H1b-ii, H-silver-vs-gold, and the accuracy half of H1c).

## Every `[PENDING]` that remains, and why

**`docs/manuscript_methods_draft.md` (14).** One is the word `[PENDING]` inside the draft-status note explaining the convention. Four are researcher or clinician decisions that this run may not make: D-01 (571.9), whether to re-tag `note_phenotype.py` as v1.1.1, how the notes arm is ultimately trained, D-02 (chunked BERT). Two are `[PENDING clinician sign-off]` on the adjudication criteria. Six are `[PENDING ADJUDICATION]`: the headline under-capture quantity (§7 and §9), the gold-standard evaluation of the models (§10.7), equity level 2 (§11), and limitation 14. One is new and narrower: `[PENDING — the notes and fusion arms have no per-stratum metrics]` in §11, which is a real gap in what was computed, not a gap in what was available to write.

**`docs/tripod_ai_checklist.md` (3).** R-5's gold-standard performance row and R-7's weighted-PPV-by-stratum row are `[PENDING ADJUDICATION]`; R-7 additionally carries the per-stratum gap for the notes and fusion arms. Eleven rows still carry the *status word* "pending" — title, abstract, funding, conflicts of interest, ethics determination, patient and public involvement, interpretation, implications, inter-rater agreement — and none of those can be resolved by a results file; they need the adjudication or administrative facts the repository does not hold.

**`docs/manuscript_results_skeleton.md` (66).** Sixty are `[PENDING ADJUDICATION]`: the headline statement, Table 4f, the whole of Table 5 (5b adjudication outcome by cell, 5c the four weighted estimates under two interval types, 5d the four kappa statistics plus disagreement count and measured minutes, 5e the six secondary adjudicated analyses), and the four hypothesis rows in Table 4g that depend on gold labels. Four are named researcher or clinician decisions (P6-01, P6-03, D1, D8/P6-02). Two are the per-stratum gap for the notes and fusion arms.

## What was written that the earlier draft got wrong, or could not know

1. **The fusion stack's notes layer is TF-IDF, and the transformer lost.** The earlier draft described the Layer-0 notes model as "the better of TF-IDF and the embedding head by DEV out-of-fold AUPRC" and left the outcome pending. The outcome is that TF-IDF won, 0.444 against 0.274. The drafts now say so, name both reasons the run log gives (85% coverage; a frozen general-purpose encoder with a light head against a vocabulary fitted to this corpus), and state that fine-tuning was budgeted at zero — without using any of those to soften the result.
2. **The encoder did not finish.** 28 of 33 shards; 27,845 of 32,845 admissions; **100% of the gold holdout**; DEV/TEST shards 24–28 never written. The gold shards (29–32) were encoded out of sequence and first, so the shortfall fell entirely on DEV and TEST and the missing 15% is not a random subset. This is now a deviation (§10.8 items 13 and 14) and a limitation (§13 item 12).
3. **H1b-iii is partly supported and the two halves point opposite ways.** Fusion is more discriminating than either base learner (+0.060 AUROC, 95% CI +0.031 to +0.089) but is **not better calibrated** than the structured FS-B arm (slope 0.934 against 1.013), and against the FS-A structured arm it adds only +0.006 AUROC. Both halves are now stated wherever the hypothesis is mentioned.
4. **The 7 September calibration expectation is not supported; amendment (b)'s competing expectation is.** The earlier draft already carried this for the structured arm; the notes-augmented model reproduces it exactly (weighted intercept −2.373, corrected +0.178, AUROC unchanged), so it is now a pattern across arms rather than a single learner's quirk.
5. **The ConText limitation is now measured rather than asserted** — 90.76% over 35,268 mentions; negation 95.87%; hedging 61.59% — with the asymmetry named (1,556 project-affirmed mentions negated by ConText against 39 the other way) and with medspaCy stated to be an independent implementation, not a gold standard.
6. **Equity level 3 is partly available.** It was `[PENDING — models still running]`. The structured arm's per-stratum calibration exists: 414 stratum rows, 225 estimable, 34 flagged. The notes and fusion arms were never stratified, so the placeholder narrowed rather than disappeared.

## Discrepancies found in this pass

1. **Affirmed-mention count in the ConText comparison.** `docs/run_2026-09-19/RUN_LOG.md` (stretch item 2) tabulates affirmed mentions as **32,867**. `results/context_agreement.json` gives `by_assertion_class.affirmed.project_n` = **33,049**, which is the value that makes the arithmetic close: 33,049 + 1,017 + 841 + 361 = 35,268 = `aligned_hits`, and 30,256 ÷ 33,049 = 91.55%, the agreement figure both documents print. `docs/context_agreement.md` also prints 33,049. **Resolution: the JSON's 33,049 is used; the RUN_LOG line appears to be a transcription slip and was not edited (it is outside this task's file list).**
2. **Two different things are called D-03.** `docs/aim1b_notes.md` and methods §10.5 call the notes-arm training strategy "D-03", while `DECISIONS_FOR_KYLE.md` D-03 is the license and code-release decision. The methods draft already hedges this as "D-03 in the notes documentation"; the collision was not introduced by this pass and was not resolved by it, because renumbering would mean editing files outside this task's list. **Flagged for Kyle.**
3. **`docs/aim1b_fusion.json` carries no per-arm confidence intervals**, only point estimates plus paired bootstrap differences. The results skeleton's Table 4d therefore reports point estimates without intervals and puts every interval in Table 4d-i, where the source actually has them. This is stated in the table rather than silently omitted.
4. **The notes-augmented arm is scored on 5,108 TEST admissions, not 6,164**, because it needs embeddings. `docs/aim1b_fusion.md` puts those rows in the same table as the 6,164-admission arms; the results skeleton keeps them in the same table but says in the text immediately above it that they are not strictly comparable.
5. **No software citation for medspaCy exists in this repository.** The methods draft names it and adds an explicit note that the citation must be added before submission, rather than writing a bibliographic field from memory. This is a fifth unverified reference in substance, though it is not listed in `docs/references/unresolved.md` (which was not edited).

## Checks

- `.venv/bin/python scripts/run0919_verify_doc_numbers.py` was run after the edits. Unattributed numeric tokens in the three drafts: **2, 2 and 2** — identical to the pre-edit baseline, and in every case a fragment of a decision identifier (`D-01`, `D-02`, `D-03`, `P6-02`, `P6-03`) that the tokenizer splits on the hyphen. **No unattributed number remains.** Token counts rose from 735 → 986 (methods), 1,101 → 1,455 (results skeleton) and 108 → 148 (checklist), which is the new content.
- The word "pre-registered" was not introduced. It appears in these files only inside statements that it must not be used.
- No count of 1–10 was written as an exact number. Every count added in this pass is a model-evaluation n (5,016 / 5,108 / 6,057 / 6,164 / 19,872 / 27,845 / 32,845 / 2,865) or a non-patient count (shards, model files, prediction columns, stratum rows).
- No `subject_id`, `hadm_id`, `note_id`, patient-level row or note text appears in any edited file. No file under `data/` or `models/` was opened; the locked-prediction file is referred to by path and SHA-256 only.
- No number was carried over from the RUN_LOG where the results JSON disagreed with it; see Discrepancy 1.
