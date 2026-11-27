# Draft amendment (q): hierarchical Bayesian fusion

> **Superseded.** Kyle approved this draft as written on 2026-11-27; it is now section 8 of `docs/analysis_plan_prespecified.md`, which governs. On decision 1 below, option (i) was taken: GOLD_HOLDOUT is not scored. No hypothesis was recorded (decision 2). This file is kept as the record of the draft.
>
> **What had been seen when this was written:** the stacked fusion's published DEV and TEST results (`docs/aim1b_fusion.md`). The hierarchical model had been run only on simulated data. No result for any stratum defined below had been computed on MIMIC.

Proposed text, to append to the plan as "## 8. Amendment dated <date committed>":

---

- **(q) Hierarchical Bayesian fusion (S23 for its FS-A sensitivity).**
  - **Why.** The working paper describes the fusion as a hierarchical Bayesian combination of the gradient-boosted (structured) and text (notes) models. The repository's fusion (Phase 9.1, `scripts/run0919_fusion_lock.py`) is a single stacked logistic regression. This amendment adds the hierarchical model beside it. The stacked fusion, its results and its locked GOLD_HOLDOUT predictions are unchanged.
  - **Inputs.** The same layer-0 predictions as the stacked fusion, read from `docs/run_2026-09-19/results/aim1b_fusion.json`: structured `cat|FS-B|unweighted` and notes `tfidf|S|unweighted`. The model is fit on their DEV out-of-fold predictions in the notes subsample and evaluated on TEST. Each logit is standardised with the DEV mean and standard deviation.
  - **Strata.** Eight strata from three binary data-availability flags, all known at discharge (`data/processed/run_2026-09-19_features.parquet`):
    1. a discharge summary is linked (`n_notes_dc > 0`);
    2. the liver was imaged in the stay or in the 365 days before it (`liver_imaging_any_pre`);
    3. AST, ALT and platelets were all measured in the stay (the FIB-4 inputs).

    The strata follow H1b-i's finding that what was measured carries much of the signal, so the model is allowed to weigh the notes and structured predictions differently where the record differs.
  - **Never inputs.** Code status, race, insurance, language, sex and age. They are equity strata (Aim 1c) and must not shape the weights.
  - **Model.** For admission i in stratum g: y_i ~ Bernoulli(sigmoid(α_g + β_s,g z_s,i + β_n,g z_n,i)). Each stratum's (α, β_s, β_n) ~ Normal(μ, τ), component by component. μ ~ Normal(0, 5) for the intercept and Normal(0, 2.5) for each weight. τ ~ Gamma(2, rate 2), that is mode 0.5 and mean 1, a prior that keeps τ off zero with only eight strata (Chung et al. 2013). Two parameterizations of this one model are used: the *marginal* form, in which μ is integrated out analytically and drawn afterwards from its exact conditional, and the *non-centred* form. They target the same posterior and differ only in how well the sampler moves through it. The convergence policy below chooses between them; the choice does not change what is estimated.
  - **Fitting.** `scripts/hier_bayes.py`, Hamiltonian Monte Carlo written for this study in NumPy; no probabilistic-programming library was installed. Validation is in `tests/test_hier_bayes.py`:
    - analytic gradients against finite differences;
    - recovery of known parameters;
    - the maximum-likelihood answer when there is one stratum;
    - partial pooling of a small stratum;
    - the R̂ and effective-sample-size estimators on chains with known behaviour.

    Settings: 4 chains of 1,000 draws, seed 20261127.
  - **Convergence (fixed here).** Every sampled parameter and μ must have split R̂ ≤ 1.01 and effective sample size ≥ 400, with no divergent transition. Up to four attempts are made, in this order, stopping at the first that meets every criterion (`hier_bayes.ATTEMPTS`):
    1. marginal form, target acceptance 0.9, 1,000 warm-up iterations;
    2. non-centred form, 0.9, 1,000;
    3. marginal form, 0.99, 2,000;
    4. non-centred form, 0.99, 2,000.

    If none meets them, the fit is reported as not converged and TEST is not touched. On simulated data like the study's, one of the four always met them: the marginal form where every stratum is large, the non-centred form where some weights do not vary between strata.
  - **Evaluation, once, on TEST.**
    - **Comparator:** the stacked fusion, refit on the same DEV rows.
    - **Measures:** AUROC, AUPRC, Brier score, log loss, and calibration intercept and slope, for all admissions and for code-negative admissions only.
    - **Differences:** hierarchical minus stacked, with paired subject-cluster bootstrap intervals (500 replicates).
    - **Per stratum:** calibration in the large.
    - **Strata seen in TEST but not in DEV** draw a new stratum from the population distribution.
  - **Sensitivity S23.** FS-A (`cat|FS-A|unweighted`) as the structured input, as S14 did for the stacked fusion.
  - **Labels.** Silver labels: definition (b), the frozen keyword rule. The notes input shares a source with the label, so every result is a development diagnostic, not an accuracy estimate.
  - **What it does not change:** no stored label, prediction, lock or result.

---

## Decisions this draft leaves to Kyle

1. **GOLD_HOLDOUT.** Scoring the held-out charts with this model means reading the per-arm GOLD prediction files, which are locked and sealed except for hashing.
   - (i) Do not score GOLD_HOLDOUT; the model stays a TEST-only development diagnostic.
   - (ii) Before any adjudication exists, compute its GOLD predictions from the locked per-arm files, then hash and lock them under a new record, leaving the existing lock untouched.
2. **Hypothesis.** None is recorded here. If one is wanted (for example, about calibration in the small strata), it must be written before the run.
3. **The fine-tuned transformer (Prompt 2).** If it is added later as a third input, that needs its own amendment.
4. **A cross-check of the sampler with Stan or PyMC.** It would need installing one of them, a new download.
