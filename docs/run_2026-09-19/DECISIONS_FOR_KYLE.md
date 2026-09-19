# Decisions for Kyle — run_2026-09-19

Tier 3 items: anything that changes a definition, a population, a primary analysis, or what the paper claims. Each entry gives the question, the options, what each option changes (numbers where computed), and what is blocked until it is decided. No recommendations.

## D-01 · Keep or drop ICD-9 571.9 from the code-positive set (Phase 4.1)

**Question.** The pre-specified code set includes 571.9 ("unspecified chronic liver disease without mention of alcohol"). The 2021 consensus table (Hagström et al., Hepatology 2021, PMID 33486773) does not list it. Keep it or drop it?

**Options and what each changes** (numbers: `docs/sensitivity_5719.md`, `docs/run_2026-09-19/results/sens_5719.json`).
- *Keep 571.9.* Matches every analysis already run (the 2×2, the sample, the weights). Departs from the consensus table; the manuscript must justify the inclusion.
- *Drop 571.9.* Aligns with the consensus. Code-positive falls from 5,740 to 5,700 (40 admissions, 38 subjects, are positive solely through 571.9). Under the primary definition the 2×2 becomes A 5,015 · B 22,811 · C 685 · D 345,481 (recovery share 81.98% vs 81.93%; corroboration 87.98% vs 87.58%). Between 1 and 10 already-sampled charts change cell (exact count in the untracked private folder), which changes the per-cell sample sizes and therefore the sampling weights (revised weights in the sensitivity doc). Every downstream table that uses code status (Aim 1c strata, the structured-arm exclusion list, the estimator weights) would be recomputed.

**Blocked until decided.** Adjudication cannot begin: weights are fixed at sampling time and a cell change after review starts would be a post-hoc reweighting.

## D-02 · Chunked Bio_ClinicalBERT instead of Clinical-Longformer (Phase 3)

**Question.** The methods plan names Clinical-Longformer for long documents. This run encodes everything with chunked Bio_ClinicalBERT (512-token chunks, stride 64, mean+max pooled) because long-attention models are slow or unsupported on this laptop (no MPS on this macOS/torch pairing; CPU only).

**Options.** (i) Keep chunked BERT as the transformer arm and describe it as such in the methods. (ii) Re-run the notes arm with Clinical-Longformer later on other hardware, keeping the same splits, subsample and variants, and report both. (iii) Drop the transformer arm and report TF-IDF only.

**What each changes.** (i) The limitations section states chunked BERT in place of a long-document model. (ii) Adds a hardware dependency and a second embedding run; nothing in this run blocks it — the splits, subsample and text variants are stored. (iii) Removes the embedding-based notes model and PCA features from Phases 8–9.

**Blocked until decided.** Nothing in this run; the manuscript's model description.


## Phase 6 decisions (P6-01 … P6-06) — merged from phase6_decisions.md

Format per the run file: question · options · what each changes · what is blocked. No recommendations. Numbers, where cited, live in the named results JSON; nothing here is hand-typed.

## P6-01 · "Insufficient information" in the headline estimate

**Question.** How does a chart adjudicated *Insufficient information* enter the under-capture, PPV and sensitivity estimates?

**Options** (both are always computed by `scripts/aim1a_estimator.py` and reported side by side under `estimates.insufficient_excluded` and `estimates.insufficient_counted_negative`).
- *Excluded.* The cell's positive proportion is x_c / (n_c − ins_c); the cell keeps its population weight. Treats non-adjudicable charts as missing at random within the cell.
- *Counted negative.* x_c / n_c. Treats "could not tell" as "no steatosis documented", which is arguably what the code axis is being compared against (information available to be coded).

**What each changes.** The two coincide when no chart is Insufficient. They diverge most in cell D (weight ≈ 3,455 per chart): excluding k Insufficient charts there raises p_D by a factor 100/(100 − k) and the headline by roughly the "shift per additional D positive" in `results/aim1a_precision_forecast.json` times the implied fractional positive. The kappa on the binary outcome is likewise reported with Insufficient excluded and with Insufficient counted negative.

**Blocked.** Which of the two is the primary number in the manuscript. Nothing computational is blocked.

## P6-02 · Final label for double-reviewed charts that disagree (criteria D8)

**Question.** The criteria leave open whether disagreements are resolved by a third adjudicator or by consensus discussion. The estimator needs one label per chart.

**Options** (all implemented; the choice is a file, not code).
- *Third adjudicator.* A resolution file (same columns) with one row per disagreeing ID; the estimator takes it as final. Pre-consensus rows still feed kappa.
- *Consensus discussion.* Same mechanism — the agreed label is written to the resolution file; the original rows are kept untouched so kappa is pre-consensus.
- *No resolution.* Disagreeing charts are excluded and counted (`resolution.unresolved_excluded`). This shrinks n_c in the affected cells and the weights no longer sum to the population.

**What each changes.** Only the label of the disagreeing charts; the estimator's arithmetic and the kappa are unchanged. The third-adjudicator route needs a third credentialed clinician.

**Blocked.** Nothing until the first disagreement exists.

## P6-03 · Weighting scheme for the ordinal (4-level) kappa

**Question.** Criteria §8 says "weighted kappa on the four-level scale" without naming the weights.

**Options** (both computed: `agreement.weighted_kappa_linear_4level`, `agreement.weighted_kappa_quadratic_4level`; the unweighted 4-level kappa is also reported).
- *Linear weights.* A Definite-vs-Absent disagreement counts three times a Definite-vs-Probable one.
- *Quadratic weights.* Nine times; equivalent to an intraclass correlation; typically higher.

**What each changes.** Only the reported agreement statistic. "Insufficient information" is not an ordinal level and is dropped from the 4-level kappa in both (analyst flag 1 in the criteria doc); the binary kappa handles it per P6-01.

**Blocked.** Nothing.

## P6-04 · Alcohol question 6b option labels in the form (criteria D6)

**Question.** The template's `q6b_alcohol` dropdown follows Draft 1 (four MetALD g/week bands). The criteria flag that a qualitative scale (none / social / heavy / not documented) may be more usable.

**Options.**
- *Keep the g/week bands* (as generated). Aligns with the MetALD definition; expected to collapse to "(iv) Not documented / insufficient" for most charts (the feasibility JSON lists quantified intake as not suppliable by MIMIC).
- *Switch to the qualitative scale.* One-line change to `OPTIONS["q6b_alcohol"]` in `scripts/make_adjudication_template.py`, then regenerate the template and both reviewer forms (`scripts/assign_reviewers.py`, same seed — the assignment does not change).

**What each changes.** The SLD subclassification secondary analysis (MetALD band) can only be computed from the band version; the qualitative version supports a none/any/heavy contrast only.

**Blocked.** The forms must be regenerated before the training round if the scale changes; the template is otherwise ready.

## P6-05 · Precision at low prevalence in cell D (design finding, not a choice already made)

**Question.** The precision forecast (`results/aim1a_precision_forecast.json`, `docs/aim1a_precision_forecast.md`) shows that if the true rate of steatosis among code−/note− admissions is about 1 per 100, roughly a third of adjudications will observe *no* positive among the 100 D charts, and the 95% interval then undercovers badly (coverage ≈ 63% in that row); at 2 per 100 coverage is ≈ 85%, at ≥ 3 per 100 ≈ 92%. Each D chart stands for ≈ 3,455 admissions.

**Options.**
- *Accept as is* and pre-specify that, if x_D ≤ 1, the headline interval is accompanied by a one-sided upper bound on p_D (rule of three) and the limitation is stated.
- *Enlarge cell D* (e.g. beyond 100 charts) before review starts. Changes the allocation, the weights, and the master key (a new draw for the added charts only); the packet, template and assignment machinery regenerates from the key.
- *Reallocate* from B or C to D within 400. Same consequences; B is the recovery zone and the design says it stays largest.

**What each changes.** The first changes only the write-up; the other two change the sampling design and every downstream weight and would need to happen before any chart is adjudicated (a post-hoc change is a reweighting).

**Blocked.** Nothing computational; the manuscript's precision claim.

## P6-06 · Which positive levels collapse to "positive" (criteria D1) — supported, not decided

The estimator's `--positive-levels` defaults to `Definite,Probable` (the draft). Running it with `Definite,Probable,Possible` is a sensitivity analysis available at no cost once the criteria are signed off; the clinician's D1 decision remains the primary.

## D-03 · License and the timing of a public code release (Phase 11.1)

**Question.** The repository has no license file. One was not added by this run, because the choice and the timing are yours.

**Background from the data use agreement.** The PhysioNet credentialed-data DUA commits the user to contributing code behind openly disseminated results to a repository open to the research community. That obliges a code release at publication; it does not choose a license, and it never permits releasing data or any derivative of it.

**Options.**
- *Permissive (MIT, BSD-3, Apache-2.0).* Maximum reuse; Apache-2.0 additionally grants patent rights and requires a change notice. Common for research code.
- *Copyleft (GPL-3.0).* Derivative works must also be open. Rarely used for analysis pipelines; can deter reuse by groups with proprietary stacks.
- *No license, public repository.* Default copyright applies and nobody may legally reuse the code. It satisfies "open to the research community" only in the weakest sense.
- *Timing: release at submission, at acceptance, or at publication.* Earlier release lets reviewers run the code; later release avoids a public artifact that changes after review.

**What is blocked.** Nothing in this run. The decision is needed before the repository is made public, and the DUA clause should be quoted in the manuscript's data-availability statement either way.
