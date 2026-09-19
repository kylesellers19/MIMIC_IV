# Phase 6 — Tier 3 questions for Kyle (reference-standard machinery)

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
