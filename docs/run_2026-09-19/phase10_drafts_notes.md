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
