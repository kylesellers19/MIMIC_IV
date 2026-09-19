# Pre-specified analysis plan — hypotheses, sensitivity registry, amendments

> **Draft assembled by Claude Code from decisions Kyle recorded in working sessions; not reviewed by Kyle at commit time; the purpose of this commit is the timestamp.**
>
> Committed on branch `run/2026-09-19` on 2026-09-19, before any model was trained and before any stratum-level rate was computed. The commit hash is recorded in `docs/run_2026-09-19/STATE.json` (`phase1_commit`). The hypotheses below were written in chat on 7 September 2026 and are recorded here verbatim. This is not a public registration; see the decisions file for the registration question.

## 1. Hypotheses (recorded verbatim, 7 September 2026)

**H1a.** Among admissions adjudicated as having documented hepatic steatosis, the majority — probably more than three-quarters — carry no MASLD code. The computable recovery share (81.9%) is not the headline; the inverse-probability-reweighted adjudicated estimate is. Secondary expectations: the note rule's PPV in the recovery zone is high but below one, with hedged and historical mentions the main sources of disagreement; rule sensitivity is imperfect, with misses in unusual phrasings and long discharge summaries; cell C adjudicates mostly as coding carried forward from prior encounters. Disconfirmation: recovery-zone PPV below about 0.6, which would mean the computable phenotype measures language rather than disease; the headline would then be restated from the adjudicated sample alone.

**H1b-i.** GBDT on structured data discriminates note-positive from note-negative admissions at a moderate level. With availability and volume features included, the top SHAP attributions are dominated by laboratory-availability indicators and diagnosis count rather than clinical values; excluding them costs discrimination and shifts attribution toward clinical values. The gap between the feature sets is reported as a result about the data.

**H1b-ii.** Against the gold standard, the notes-augmented arm outperforms the structured baseline specifically in the recovery zone. Silver-label metrics for the notes arm are inflated by circularity and are development diagnostics only.

**H1b-iii.** Stacked fusion is at least as discriminating as the better base learner and better calibrated than either; if the notes arm dominates, fusion may add little and that is reported as such.

**H-calibration (as recorded 7 September).** Under class weighting with post-hoc threshold tuning, calibration slope near 1 and intercept near 0 in development; calibration differs by subgroup even where AUROC does not, particularly where laboratory availability differs.

**H-silver-vs-gold.** Every gold-standard performance estimate is lower than its silver-label counterpart; the size of the drop is reported as a measure of silver-label error. Disconfirmation for 1b: a notes-augmented arm that does not exceed the structured baseline in the recovery zone against the gold standard.

**H1c.** The coding rate among note-positive admissions differs across race and insurance strata; direction not assumed. Note-based recovery is expected to redistribute ascertainment toward groups with thinner structured records, while the accuracy of that recovery (weighted PPV by stratum) and model calibration are less uniform than the recovery rate itself. Small strata yield intervals too wide to support a claim, and the study says so rather than collapsing categories. Disconfirmation: uniform recovery, accuracy and calibration across strata — reported as a useful negative result.

## 2. Registry of sensitivity analyses

| ID | Definition | Date pre-specified | Status |
| --- | --- | --- | --- |
| S1 | Outpatient radiology window −90/+30 days instead of −365/+30 (definition c) | 2026-08-17 (rule freeze) | done → `docs/aim1a_crosstab.md` |
| S2 | Rule version v1.0.0 instead of v1.1.0, inpatient-linked (definition d) | 2026-08-17 | done → `docs/aim1a_crosstab.md` |
| S3 | Imaging-observed population (≥1 liver-inclusive study, −365/+30) as denominator | 2026-08-19 | done → `docs/imaging_denominator.md` |
| S4 | Three etiology-based secondary recovery estimates (competing liver disease excluded under three code sets) | 2026-08-19 | done → `docs/predefinition_descriptives.md`, `docs/sld_subclassification.md` |
| S5 | Historical-mention split under two operationalizations (ConText temporality flag; PMH-section placement) | 2026-08-19 | done → `docs/predefinition_descriptives.md` |
| S6 | Subject grain (any-admission collapse) instead of admission grain | 2026-08-18 | done → `docs/aim1a_crosstab.md` |
| S7 | ICD-9 571.9 removed from the code-positive set (consensus-table alignment) | 2026-09-19 (this run, Phase 4.1) | this run → `docs/sensitivity_5719.md` |
| S8 | Discharge-summary-only population, definitions (a) and (b) | 2026-08-17 (population lock), never run as a 2×2 | this run → `docs/aim1a_loose_ends.md` |
| S9 | Tier C (hedged) mentions counted as note-positive | 2026-09-19 (this run, Phase 4.4) | this run → `docs/aim1a_loose_ends.md` |
| S10 | Availability differentials by race/insurance under both outpatient windows | 2026-09-19 (this run, Phase 4.6) | this run → `docs/aim1a_loose_ends.md` |
| S11 | Charlson index validated against comorbidipy; liver-excluded index for modeling | 2026-09-19 (this run, Phase 4.2) | this run → `docs/charlson_validation.md` |
| S12 | Aim 1c headline stratum table recomputed with 571.9 removed | 2026-09-19 (this run, Phase 5) | this run → `docs/aim1c_level1.md` |
| S13 | Aim 1b secondary modeling population: imaging-observed subset | 2026-09-19 (this run, Phase 7) | this run → `docs/aim1b_structured.md` |
| S14 | Aim 1b FS-A as a sensitivity Layer-0 input to fusion | 2026-09-19 (this run, Phase 9) | this run → `docs/aim1b_fusion.md` |

## 3. Amendments dated 2026-09-19

Each amendment carries the statement: **no result from this analysis had been seen when it was added.**

- **(a) 571.9 sensitivity (Phase 4.1).** Reason: the 2021 expert-panel consensus table (Hagström et al., Hepatology 2021) lists 571.8 and K76.0 for the disease overall and K75.8 for steatohepatitis; 571.9 is not in that table but is in this project's pre-specified set. The primary is unchanged; the code-positive set with 571.9 removed is computed side by side. No result from this analysis had been seen when it was added.
- **(b) Competing calibration expectation (Phases 7–9).** Class weighting inflates predicted risk for the same reason synthetic oversampling does, so the 7 September expectation (slope near 1, intercept near 0 under weighting) is tested, not assumed: unweighted, weighted, and weighted-with-analytic-prior-correction variants are all trained and reported side by side. No result from this analysis had been seen when it was added.
- **(c) Gold-holdout rule (Phase 2).** Every subject with any admission in the 400-chart sample or the 20-chart training set is removed from all model fitting, tuning, early stopping, threshold selection, recalibration, vocabulary building and dimensionality reduction, before any model exists. No result from this analysis had been seen when it was added.
- **(d) Liver-excluded Charlson index for modeling (Phase 4.2).** Reason: the Quan mild-liver category contains K76.0 and 571.x, the phenotype's own codes, so the full index leaks the code axis into a model whose label is the note axis. `charlson_noliver` removes both liver categories. No result from this analysis had been seen when it was added.
- **(e) Imaging-observed population as a secondary modeling population (Phase 7).** Reason: within admissions where the liver was imaged, the question becomes whether structured data predicts documented steatosis rather than who got imaged. No result from this analysis had been seen when it was added.
- **(f) Notes-arm diagnostic variants (Phase 8).** Unmasked (U), span-masked (M), and sentence-deleted (S) text variants, TF-IDF and transformer heads, and a notes-augmented CatBoost. None of these selects a training strategy; that decision is Kyle's and is written to the decisions file. No result from this analysis had been seen when it was added.
- **(g) Exploratory adjusted model (Phase 5).** Among note-positive admissions, outcome = code-positive; covariates fixed here before fitting: race (as recorded), insurance, sex, age band, admission type, ICD version of the admission, note source (discharge, inpatient radiology, outpatient radiology). Generalized estimating equations clustered on subject; exchangeable working correlation; adjusted odds ratios with 95% CIs. Diagnosis count and laboratory availability are **not** covariates (they are the proposed mechanism). If it does not converge with sparse categories, restrict to categories with at least 100 note-positive admissions and say so. Labelled exploratory everywhere. No result from this analysis had been seen when it was added.

## 4. Run parameters fixed at this commit

BOOTSTRAP_REPS = 500; CELL_FLOOR = 11; SEED_TRAINING_DRAW = 20260919; SEED_SPLIT = 20260920; SEED_REVIEWER_ASSIGN = 20260921; SEED_NOTES_SUBSAMPLE = 20260922. Age bands for Aim 1c: 18–39, 40–54, 55–64, 65–74, 75–88, 89 and over (MIMIC recodes ages ≥89 to 91). Subgroup metrics in Aim 1b are reported only where the subgroup has ≥50 positives and ≥50 negatives in TEST.
