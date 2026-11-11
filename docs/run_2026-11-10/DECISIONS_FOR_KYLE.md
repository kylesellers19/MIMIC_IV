# Decisions for Kyle — run_2026-11-10

Tier 3 items: anything that changes a definition, a population, a primary analysis, or what the paper claims. Each entry gives the question, the options, what each option changes, what is blocked until it is decided, and draft amendment text for every option, so the chosen one can be committed as written. **No recommendation is made anywhere in this file.**

Written by `scripts/run1110_decisions.py`. Numbers come from results files; the ones computed for this file are in `docs/run_2026-11-10/results/decisions_inputs.json`.

## At a glance

| Item | Decision | Blocks |
| --- | --- | --- |
| N-01 | Admission-level probability for the language-model arm | Any probability-based metric for that arm; must be fixed before an adjudication result is seen |
| N-02 | Prompt-version difference between dev/test and GOLD_HOLDOUT | What the manuscript says about the merged dev/test labels |
| N-03 | Sample admissions with no kept sentence | How the language-model arm's errors are tabulated against chart review |
| N-04 | Note axis for Aim 1a | Which computable phenotype the headline comparison uses |
| N-05 | The alternative section-closing rule | Nothing computational |
| N-06 | Reviewer criteria against the locked prompt | The chart criteria, and so the start of adjudication |
| N-07 | Registration (updates D-04) | The manuscript's timing claims |
| N-08 | What prospective reviewers are offered | Sending the one-pager |
| N-09 | Material the push gate flags: two held-back files, and lines already public | Two files stay local; possible clean-up of public documents |
| N-10 | The one-pager states the study question; criteria §10 says reviewers are not told it | Sending the one-pager to a prospective reviewer |
| D-01 (September) | Keep or drop ICD-9 571.9 | **The start of adjudication** |

## N-01 · Admission-level probability for the language-model arm

**Question.** The locked answers hold three probabilities per sentence. The admission rule is a classification (at least one YES, current or past). Which admission-level probability, if any, represents this arm when it is scored against chart review? It must be fixed before any adjudication result is seen.

**What was computed (dev/test only; distribution only; no gold).** `docs/run_2026-11-10/results/decisions_inputs.json`, field `n01`. Of 29,980 dev/test admissions, 2,712 have at least one sentence with timing CURRENT or PAST; the other 27,268 score zero under both formulas. The median number of such sentences, where there is one, is 2. A sentence answered NO has timing NA, so only YES and UNCLEAR sentences enter either formula.

| | Maximum P(YES) | Noisy-OR |
| --- | --: | --: |
| Percentiles 10 / 25 / 50 / 75 / 90, admissions with an eligible sentence | 0.000 / 1.000 / 1.000 / 1.000 / 1.000 | 0.000 / 1.000 / 1.000 / 1.000 / 1.000 |
| Same, primary-positive admissions | 1.000 / 1.000 / 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 / 1.000 / 1.000 |
| Same, primary-negative admissions with an eligible sentence | 0.000 / 0.000 / 0.000 / 0.000 / 0.003 | 0.000 / 0.000 / 0.000 / 0.000 / 0.003 |
| Admissions at or above 0.5 | 2,252 | 2,252 |
| Admissions above 0.99 | 2,208 | withheld (within 10 of the maximum's count) |
| At or above 0.5 but negative by the rule | 0 | 0 |
| Below 0.5 but positive by the rule | 0 | 0 |
| Distinct score values (3 decimals) | 73 | 71 |

Rank correlation between the two scores: 0.996. Admissions where noisy-OR exceeds the maximum by more than 0.10: 0. Primary-positive admissions under the classification rule: 2,252. On dev/test, cutting either score at 0.5 gives exactly the classification rule's labels.

**Options and what each changes.**
- *Maximum P(YES) over sentences with CURRENT or PAST timing.* One sentence decides the score, as one sentence decides the label. Many admissions share a score near 1, so ranking among them is coarse and calibration rests on few distinct values.
- *Noisy-OR over those sentences.* The score rises with the number of supporting sentences. It treats sentences as independent, which repeated statements of one finding are not, so long charts score higher for the same evidence.
- *Report the arm as a classifier only.* No probability is defined. Sensitivity, specificity and predictive values are reported; AUROC, AUPRC, calibration and any comparison that needs a score are not, and the arm cannot enter a stacked model as a probability.

**Blocked until decided.** Every probability-based metric for the language-model arm against chart review. Nothing in this run.

**Draft amendment text.**
- *Maximum:* "The language-model arm's admission-level probability is the maximum P(YES) over kept sentences whose timing is CURRENT or PAST, and zero when there is none. Fixed on [date], before any adjudication result was seen. Its distribution on dev/test had been seen."
- *Noisy-OR:* "The language-model arm's admission-level probability is one minus the product of (1 − P(YES)) over the distinct kept sentences whose timing is CURRENT or PAST, and zero when there is none. Fixed on [date], before any adjudication result was seen. Its distribution on dev/test had been seen."
- *Classifier only:* "The language-model arm is evaluated as a classifier under the admission rule of amendment (h). No admission-level probability is defined for it, and no metric that needs one is reported. Fixed on [date], before any adjudication result was seen."

## N-02 · Prompt-version difference between dev/test and GOLD_HOLDOUT

**Question.** On dev/test, units v3 answered NO were carried into the merged labels without being asked with v4. On GOLD_HOLDOUT, v4 answered every unit. What is done about the difference?

**What Phase 4 found.** [PENDING] Phase 4 had not finished when this file was written; rerun `scripts/run1110_decisions.py` once `carryover_check.json` exists.

**Options and what each changes.**
- *Re-ask all carried-over NO units with v4.* [PENDING] The unit count and hours are written from Phase 4's results file. Dev/test labels would then come from one prompt throughout, like GOLD_HOLDOUT. Every dev/test table that uses the language-model phenotype would be recomputed and dated, and the earlier figures kept beside them.
- *Keep the merged labels and report Phase 4.* Nothing is recomputed. The manuscript states the design, the estimated share of units and admissions affected, and its bounds.
- *Keep language-model output out of stacked-model training.* Can be combined with either option above. The arm is then compared with the other arms but is never an input to a model evaluated on GOLD_HOLDOUT, so no model is trained on labels produced under one design and tested on labels produced under another.

**Blocked until decided.** The wording of the methods on the merged labels. Whether the language-model phenotype may be a model input.

**Draft amendment text.**
- *Re-ask:* "All dev/test units whose stored answer was v3's NO were asked with prompt v4 on the pinned model on [dates]. The merged labels were replaced; tables computed from the earlier labels are retained and marked superseded. The carry-over check of 10 November 2026 had been seen."
- *Keep and report:* "Dev/test labels remain the merged v4 labels. The carry-over check (amendment k) is reported with its bounds as the estimate of what re-asking would change."
- *Not a model input:* "No label or probability from the language-model arm is used to fit, tune or select any model that is evaluated on GOLD_HOLDOUT."

## N-03 · Sample admissions with no kept sentence

**Question.** The run file states that 80 of the 400 sampled admissions have no kept sentence, all in the two note-negative strata. The language-model arm labels them negative by construction. If chart review finds steatosis in one of them, whose error is it? *(The figure is quoted from the run file. It was not recomputed here: that would mean opening a sealed file.)*

**Options and what each changes.**
- *Report them as extractor misses, separately.* The arm's sensitivity is given twice: over all sampled admissions, and over those with a kept sentence. A positive chart with no kept sentence is counted against the extractor.
- *Pool them into the language-model arm's error.* One sensitivity figure for the pipeline as a whole. A miss by the extractor and a miss by the model are not distinguished.

**What each changes.** The headline comparison between arms is unchanged in the pooled figure. The separate table needs the count of positive charts among those admissions, which may be below 11 and would then be masked.

**Blocked until decided.** The layout of the language-model arm's error table. Must be fixed before adjudication results are seen.

**Draft amendment text.**
- *Separate:* "For the language-model arm, admissions with no kept sentence are reported as a separate row. Sensitivity is reported for the whole pipeline and for admissions with at least one kept sentence. Counts from 1 to 10 are masked."
- *Pooled:* "For the language-model arm, an admission with no kept sentence is a negative prediction, and any error on it is counted as the arm's error."

## N-04 · Note axis for Aim 1a

**Question.** Aim 1a compares a code axis with a note axis. The note axis has been the frozen keyword rule. A second computable note phenotype now exists. Which is the note axis?

**Options and what each changes.**
- *The frozen rule.* Nothing changes. The sample, its strata and its weights were drawn on this axis. The language-model phenotype stays an exploratory second phenotype (S15).
- *The language model.* The computable cross-tabulation would be rebuilt on a phenotype that exists only for the dev/test notes subsample and GOLD_HOLDOUT, not for the whole population. The sample was not stratified on it, so the weights do not match its cells.
- *Both.* The frozen rule remains the axis the sample was drawn on and the primary comparison. The language model is reported beside it wherever it exists, and the adjudicated estimates are computed for both, with the sample's weights applied to each.

**Blocked until decided.** The framing of the Aim 1a result. Nothing computational.

**Draft amendment text.**
- *Frozen rule:* "The note axis of Aim 1a is the frozen keyword rule, version 1.1.0, as sampled. The language-model phenotype is reported as an exploratory comparison (S15) and does not define a cell."
- *Language model:* "The note axis of Aim 1a is the language-model phenotype of amendment (h). The sample was stratified on the frozen rule; estimates on the new axis use the original sampling weights and are reported with that limitation."
- *Both:* "Aim 1a is reported on two note axes. The frozen keyword rule, on which the sample was stratified, is primary. The language-model phenotype is secondary and uses the same sample and weights."

## N-05 · The alternative section-closing rule

**Question.** A different rule for closing a findings block was examined on 23–26 September and not adopted. Is it dropped, or run as a dev/test-only sensitivity analysis?

**What is known.** Section labels only set priority under the 160-sentence cap, and the cap bound <11 of 29,980 dev/test admissions (`docs/run_2026-11-10/results/extractor_cap.json`). For every other admission a different closing rule changes a label that nothing uses. Aggregate counts from the September examination are in `docs/run_2026-11-10/results/diag_section_study_headers.json` and `diag_section_tableB.json`.

**Options and what each changes.**
- *Drop it.* The protocol already says it was examined and not adopted. Nothing is run.
- *Run it as a dev/test-only sensitivity analysis.* The extractor is rerun with the alternative rule, the changed sentences are asked with v4, and the admission labels are compared. GOLD_HOLDOUT is not touched, so the result cannot be scored against chart review.

**Blocked until decided.** Nothing.

**Draft amendment text.**
- *Drop:* "The alternative section-closing rule examined on 23–26 September 2026 is not part of any analysis."
- *Sensitivity:* "Sensitivity analysis S23: the extractor's section-closing rule is replaced by the alternative examined on 23–26 September 2026, on dev/test only. Reported: sentences whose section label changes, admissions whose kept sentences change, admissions whose label changes. Already seen: the aggregate counts of the September examination."

## N-06 · Reviewer criteria against the locked prompt

**Question.** Chart reviewers will answer on the scale Definite, Probable, Possible, Absent, Insufficient information (`docs/adjudication_criteria.md`, Draft 1). The locked prompt answers YES, UNCLEAR or NO for a sentence, with a timing word. The two were written separately. Where they differ, the language-model arm is scored against a standard that defines the finding differently. Are the chart criteria written from the clinical definition, with the differences reported, or aligned to the prompt?

**Who has reviewed what.** The admission rule was signed off by Kyle Sellers (study lead; not a clinician). No clinician has reviewed the admission rule or the prompt's rules. The chart criteria are a draft with open clinician decisions (D1–D8 in that document).

**Crosswalk.** Chart levels are from Draft 1, where Definite and Probable are positive. Prompt answers are from `RULES` and `ALCOHOL_RULE` in `scripts/llm_sentence_review.py`; an admission is positive when one sentence is YES with timing CURRENT or PAST.

| Evidence | Chart criteria, Draft 1 | Locked prompt, v4 | Same result? |
| --- | --- | --- | --- |
| CT or MRI reporting steatosis, fatty liver, fatty infiltration or decreased attenuation | Definite | YES. Also names attenuation below the spleen or below 40 HU, and signal loss on out-of-phase MRI | Yes. The prompt names signs the criteria do not list |
| Liver biopsy reporting steatosis | Definite | YES when a kept sentence says so. Pathology reports are not among the notes read | Yes, where a sentence exists |
| Ultrasound: increased echogenicity "consistent with steatosis" | Probable (open decision D2) | YES | Yes |
| **Ultrasound echogenicity reported, interpretation absent** | Not listed. Row (c) requires the interpretation | YES: "a diffusely echogenic or hyperechoic liver" | **Differs.** The prompt counts it; the criteria are silent |
| Clinician statement ("fatty liver", "known NAFLD") without imaging | Probable | YES (the abbreviations are listed) | Yes |
| **Hedged wording: "likely", "probable", "suggestive of"** | Not listed as hedged. The criteria's examples of hedging are "cannot exclude" and "may represent" | UNCLEAR, which is not positive | **May differ.** A reviewer could reasonably read "likely steatosis" as Probable, which is positive |
| Hedged wording: "cannot exclude", "may represent", "possible" | Possible (open decision D3) | UNCLEAR | Yes under the draft. Differs if D3 moves hedged imaging to Probable |
| "Consistent with", "compatible with" | Row (c) uses "consistent with" for Probable | YES | Yes |
| Coarse or heterogeneous echotexture only | Not listed | UNCLEAR | Prompt only |
| Focal fatty sparing | Not listed | YES ("the rest of the liver is fatty") | Prompt only |
| Focal fat, or a single fatty lesion | Not listed | NO | Prompt only |
| A request to evaluate for or rule out fatty liver | Not listed | NO | Prompt only |
| Alcohol-related liver disease, alcoholic hepatitis, and cirrhosis or liver fibrosis; fat not stated | Not addressed. Alcohol is a secondary question (6b) | NO. Alcoholic fatty liver and alcoholic steatohepatitis are YES | Prompt only. The criteria do not say how cirrhosis without a statement of fat is read |
| Raised liver enzymes or metabolic risk alone | Absent | NO | Yes |
| **Ongoing diagnosis listed in the history** ("history of NAFLD") | Positive in the draft; recorded as before, during or both (open decision D4) | PAST or CURRENT, at the model's reading. Both count | Same label. The timing field can differ, which matters only for the CURRENT-only sensitivity definition |
| Family history | Not addressed | FAMILY, never positive | Prompt only |
| **A newer study stating no steatosis** | Can override an older positive, at the reviewer's judgement (open decision D5) | No override. One YES sentence anywhere makes the admission positive | **Differs in structure** |
| **Not enough information** | Insufficient information | No equivalent. An admission with no kept sentence is negative | **Differs in structure** (see N-03 and P6-01) |
| Unit read | The whole packet: summary, radiology reports, laboratory values, medication orders | One sentence, with its note type and heading; liver-related sentences only | Differs in structure |

**Options and what each changes.**
- *Write the chart criteria from the clinical definition and report the differences.* Clinicians settle D1–D8 without reference to the prompt. The crosswalk above is frozen with the criteria and published as the list of known construct differences. The language-model arm is then scored against a standard defined independently of it, and part of its disagreement is attributable to rows marked "differs".
- *Align the chart criteria to the prompt's construct.* The rows marked "differs" and "prompt only" are written into the criteria in the prompt's direction (for example, echogenicity reported without interpretation counts as Probable). Agreement between the arm and chart review rises by construction. The reference standard is then partly defined by one of the arms it evaluates, and the frozen keyword rule and the other models are scored against a standard shaped to a competitor. The prompt is locked, so alignment can only run in that direction.

**Blocked until decided.** The chart criteria, and through them the start of adjudication. Clinician review of the admission rule is outstanding under either option.

**Draft amendment text.**
- *Independent criteria:* "The adjudication criteria were finalised by clinicians from the clinical definition of hepatic steatosis, without reference to the language-model prompt. The crosswalk between the chart scale and the prompt's answers, frozen with the criteria, lists every known difference in construct; disagreement on those rows is reported separately."
- *Aligned criteria:* "The adjudication criteria were aligned to the construct of the locked language-model prompt on the following rows: [list]. The prompt was locked first. Agreement between the language-model arm and chart review on those rows is therefore partly by construction, and comparisons between that arm and the other arms are reported with and without them."

## N-07 · Registration (updates D-04)

**Question.** D-04 asked whether to register publicly or rely on the git history. What has changed since September?

**What has changed.**
- The language-model arm's GOLD_HOLDOUT answers are locked, with SHA-256 hashes in `docs/llm_gold_lock.md`, and the lock commit carries the annotated tag `llm-gold-lock-v1`, which is on the remote. A registration made now could cite the tag and the hashes (2,865 admissions, 20,200 units).
- The repository is public, so a reader can already check the history.
- The two rule tags, `note-phenotype-v1.0.0` and `note-phenotype-v1.1.0`, exist only on this machine. `git ls-remote --tags` shows one tag on the remote. D-04 cites those tags as part of the audit trail. This run did not push them, because it was told to push one tag.
- The dev/test results of the language-model arm, the carry-over check and the four exploratory analyses of this run have been computed. A registration made now would post-date them and would have to say so.

**Options and what each changes.** As in D-04 (register now; rely on the git history; register only what has not yet been run), with two additions.
- *Any registration made now* can include the lock hashes and the tag, which gives the gold-standard comparison a third-party timestamp before adjudication starts.
- *Under any option,* the two rule tags can be pushed so that the trail D-04 describes is visible on the remote, or left local and the manuscript's claim narrowed to what the remote shows.

**Blocked until decided.** The manuscript's timing claims.

**Draft amendment text.**
- *Register now:* "The analysis plan, the locked-prediction hashes of both model locks and the tag `llm-gold-lock-v1` were registered at [registry, identifier] on [date]. The registration post-dates the computable-stage results, the dev/test language-model results and the exploratory analyses of 10 November 2026, and says so."
- *Git history only:* "This study is not registered. Its timing claims rest on the public git history: rule tags, the pre-specification commit, the amendment commits and the lock tag."
- *Register the unrun part:* "The adjudication criteria, the estimator and the gold-standard comparison, with both lock hashes, were registered at [registry, identifier] on [date], before any chart was adjudicated. Everything computed before that date is described as preceding registration."

## N-08 · What prospective reviewers are offered

**Question.** What does the study offer a clinician who reviews charts? `docs/adjudication/reviewer_onepager.md` leaves this section empty.

**Options.** Left blank for Kyle, as the run file instructs.

**Blocked until decided.** Sending the one-pager to anyone.

**Draft text.** None drafted.

## N-09 · Material the push gate flags

**Question.** The gate's note-text rule is a 30-character overlap with a dev/test extractor sentence. It flags two files this run was asked to commit, and it flags lines in documents that were already public when the run began. What is done with each?

**What is known (counts only; no flagged line was read).**
- `scripts/llm_timing_test.py`: 24 lines flagged, longest overlap 49 characters; 2 quoted probe sentences equal a whole extractor string (`docs/run_2026-11-10/results/held_back_files.json`).
- `docs/adjudication/criteria_revision_proposal.md`: 4 lines flagged, longest overlap 38 characters, none equal to a whole extractor string. The overlaps are inside the study's own criteria prose.
- Already public at the start of this run: 148 lines across 28 files (`docs/run_2026-11-10/results/base_exposure_audit.json`). The file with the most is `docs/predefinition_descriptives.md`: 50 lines, of which 36 overlap exactly one extractor string. No real identifier was found in any tracked file.
- September's audit allowed short context windows around a keyword match and passed these documents. The rule in force now is stricter, and the repository has since become public.

**Options and what each changes.**
- *Review and replace.* Someone entitled to read the notes checks each flagged line against its matching sentence. Lines that are note text are replaced in a new commit. Git history keeps the old text unless history is rewritten, which this run's rules forbid and which would break the timestamps the audit trail relies on.
- *Accept short overlaps as stock phrasing.* The gate's rule is relaxed for study-authored files by a stated criterion, for example an overlap that occurs in at least 11 extractor strings. The two held-back files may then pass or not, depending on the criterion; the counts needed to judge that are in the two results files.
- *Keep the two files local and leave the public lines as they are.* Nothing changes. The README does not link the criteria proposal.
- *Reword the two files.* The four criteria lines and the probe sentences are reworded until the gate passes, then committed. The probe set would no longer be the one the v1 prompt was timed on.

**Blocked until decided.** The two files stay untracked. Whether any public document needs replacing.

**Draft amendment text.** Not an analysis-plan matter. If the gate's rule is changed, the change belongs in the docstring of `scripts/run1110_push_gate.py` and in a dated line of the run log.

## N-10 · The one-pager states the study question; the criteria say reviewers are not told it

**Question.** The run file asked for a one-pager that gives the question and what the computable stage shows. `docs/adjudication_criteria.md` §10 says reviewers are told only that a computable phenotype for hepatic steatosis is being validated, and nothing more of the hypothesis. The one-pager as written tells a prospective reviewer that the study is about fatty liver being documented but not coded, and gives the uncoded share. Which document gives way?

**What is known.** The page carries a notice at its top pointing here. The repository is public and its README states the purpose, so a reviewer who looks will find it either way.

**Options and what each changes.**
- *Keep the one-pager; revise §10.* Reviewers know the question. Blinding then covers code status, rule output, model output and cell membership, but not the hypothesis. The manuscript must say so.
- *Cut the question and the computable-stage section from the page given to reviewers.* The page says what §10 allows. The fuller page can still be used for people who will not review, such as a department lead being asked for time.
- *Keep both as they are and use the page only for non-reviewers.* A second, shorter page would be needed for reviewers.

**Blocked until decided.** Sending the one-pager to a prospective reviewer.

**Draft amendment text (criteria §10).**
- *Revise §10:* "Reviewers are told the study question. They are blinded to code status, to the output of the keyword rule and of every model, and to the stratum a chart was sampled from."
- *Keep §10:* no change to the criteria; `docs/adjudication/reviewer_onepager.md` is regenerated without its first two sections for reviewers.

## Decisions still open from September

From `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`. Full text, options and stakes are there.

| Item | Question | Where it stands |
| --- | --- | --- |
| D-01 | Keep or drop ICD-9 571.9 from the code-positive set | **Open. Blocks the start of adjudication:** the sampling weights are fixed at sampling time. |
| D-02 | Chunked Bio_ClinicalBERT instead of Clinical-Longformer | Open. |
| P6-01 | "Insufficient information" in the headline estimate | Open. |
| P6-02 | Final label for double-reviewed charts that disagree | Open. |
| P6-03 | Weighting scheme for the ordinal (4-level) kappa | Open. |
| P6-04 | Alcohol question 6b option labels in the form | Open. |
| P6-05 | Precision at low prevalence in cell D | Open. |
| P6-06 | Which positive levels collapse to "positive" | Open. |
| D-03 | License and the timing of a public code release | Open. The repository is public and has no license file. |
| D-04 | Public registration versus the repository's git audit trail | Open. Updated by N-07 above. |
| D-05 | The "pre-registered" wording that needs correcting | Partly closed on 2026-11-10: the three lines in `docs/reference_standard.md` now follow option 1. The sentence in the older draft outside this repository, and any slide or abstract reusing it, are untouched. |
| D-06 | What the manuscript may claim from the transformer-versus-TF-IDF comparison | Open. |
| D-07 | How the notes arm is ultimately trained | Open. |

**D-01 is the one that blocks the start of adjudication.** N-06 and the clinician sign-off on the criteria block it as well.
