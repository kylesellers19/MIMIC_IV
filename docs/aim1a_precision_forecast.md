# Aim 1a precision forecast — simulation of the under-capture estimator

Produced by `scripts/run0919_precision_forecast.py`; every number below is read from `docs/run_2026-09-19/results/aim1a_precision_forecast.json`. No patient data are used: the calculation needs only the population cell sizes and the allocation from `docs/aim1a_crosstab.md`.

## What is estimated

The headline Aim 1a quantity is the population-weighted share of adjudicated steatosis-positive admissions that are code-negative: (w_B x_B + w_D x_D) / (w_A x_A + w_B x_B + w_C x_C + w_D x_D), with x_c the adjudicated positives in cell c and w_c = N_pop(c)/n_sample(c). Cells: A = code+/note+, B = code−/note+, C = code+/note−, D = code−/note−. Sample sizes 80/150/70/100; weights 62.8375 / 151.9933 / 10.1857 / 3454.53. Implementation: `scripts/aim1a_estimator.py` (unit tests `tests/test_aim1a_estimator.py`).

Hand-checked unit-test target (x = 76/128/35/1 positives in A/B/C/D): under-capture 81.698%, note-rule PPV 87.08%, sensitivity 86.409%.

## Simulation design

For PPV in cell B ∈ {0.95, 0.85, 0.75} and positives per 100 charts in cell D ∈ {0, 1, 2, 3, 5}, holding cell A at 0.95 and cell C at 0.50, 2,000 adjudications were simulated per scenario (independent binomial draws per cell, seed 20260925). For each simulated adjudication the estimate, a stratified bootstrap 95% CI (500 reps, resampling within cells) and a linearized 95% CI were computed. Coverage is the share of simulated intervals containing the closed-form truth.

Reference row (PPV_B = 0.85), closed form for D = 0, 1, 2, 3, 5: 79.06, 81.65, 83.67, 85.28, 87.72 — matches the pre-specified reference row 79.06, 81.65, 83.67, 85.28, 87.72: **yes**.

## Results

| PPV_B | D per 100 | closed form % | exact E[estimate] % | sim mean % (MC SE) | boot CI mean width | boot coverage % | lin CI mean width | lin coverage % | var. share from D % | width without D | shift per extra D positive |
| --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| 0.95 | 0 | 80.84 | 80.84 | 80.85 (0.01) | 1.88 | 93.0 | 1.88 | 94.2 | 0.0 | 1.88 | 2.19 |
| 0.95 | 1 | 83.03 | 82.83 | 82.83 (0.04) | 5.24 | 63.2 | 5.80 | 62.1 | 60.4 | 1.66 | 1.74 |
| 0.95 | 2 | 84.77 | 84.47 | 84.40 (0.05) | 6.90 | 84.9 | 7.38 | 83.4 | 83.0 | 1.49 | 1.42 |
| 0.95 | 3 | 86.19 | 85.84 | 85.83 (0.05) | 7.71 | 91.5 | 7.97 | 92.0 | 92.5 | 1.35 | 1.18 |
| 0.95 | 5 | 88.35 | 88.01 | 88.03 (0.05) | 7.75 | 91.7 | 7.68 | 93.0 | 97.1 | 1.12 | 0.85 |
| 0.85 | 0 | 79.06 | 79.05 | 79.05 (0.02) | 2.74 | 93.8 | 2.75 | 94.7 | 0.0 | 2.75 | 2.59 |
| 0.85 | 1 | 81.65 | 81.38 | 81.46 (0.05) | 6.49 | 65.1 | 7.07 | 63.8 | 60.9 | 2.30 | 2.02 |
| 0.85 | 2 | 83.67 | 83.29 | 83.26 (0.06) | 8.17 | 85.9 | 8.65 | 84.2 | 83.0 | 2.00 | 1.62 |
| 0.85 | 3 | 85.28 | 84.86 | 84.85 (0.06) | 8.89 | 91.8 | 9.09 | 91.3 | 91.8 | 1.73 | 1.33 |
| 0.85 | 5 | 87.72 | 87.31 | 87.30 (0.05) | 8.79 | 92.4 | 8.63 | 92.8 | 96.9 | 1.38 | 0.94 |
| 0.75 | 0 | 76.91 | 76.89 | 76.86 (0.02) | 3.74 | 94.6 | 3.74 | 95.2 | 0.0 | 3.74 | 3.10 |
| 0.75 | 1 | 80.02 | 79.67 | 79.60 (0.06) | 7.73 | 63.9 | 8.36 | 62.9 | 58.7 | 3.07 | 2.37 |
| 0.75 | 2 | 82.39 | 81.91 | 82.03 (0.06) | 9.82 | 87.4 | 10.25 | 85.8 | 83.8 | 2.50 | 1.87 |
| 0.75 | 3 | 84.25 | 83.73 | 83.72 (0.07) | 10.41 | 92.8 | 10.57 | 92.3 | 92.1 | 2.15 | 1.51 |
| 0.75 | 5 | 87.01 | 86.52 | 86.48 (0.06) | 10.04 | 91.5 | 9.75 | 92.5 | 96.6 | 1.63 | 1.04 |

Widths and shifts are in percentage points. 'Exact E[estimate]' is the expectation of the ratio estimator over the binomial draws (cells D, B and A enumerated, C at its mean). 'Width without D' is the linearized interval width if cell D contributed no sampling variance.

## Reading the table

- **Closed form vs simulated mean.** The simulated mean matches the exact expectation of the estimator within Monte Carlo error in every scenario (largest discrepancy 1.94 MC standard errors). It sits slightly *below* the plug-in closed form whenever D > 0 (largest gap 0.52 percentage points): the estimator is a ratio that is concave in x_D, so averaging over the binomial draw of x_D (Jensen's inequality) pulls the mean down. This is a property of the ratio estimator with 100 charts in cell D, not a coding error; it is smaller than a tenth of the interval width.
- **Where the interval comes from.** Each of the 100 charts in cell D stands for about 3,455 admissions. One additional adjudicated positive in D moves the estimate by the amount in the last column (2–3 percentage points), whereas one additional positive in B moves it by about 0.1 points. The 'var. share from D' column says what fraction of the linearized variance is due to cell D alone, and 'width without D' shows how narrow the interval would be if D were known exactly. In plain words: once even one or two positives turn up among the 100 code−/note− charts, most of the uncertainty in the headline number is the uncertainty about how many such positives there really are in the ~345,000 admissions that cell represents, and no amount of extra precision in the other three cells can remove it.
- **Coverage fails when cell D is nearly empty.** At 1 positive per 100 in D, 36–38% of simulated adjudications observe *no* positive in D; both intervals then have nothing to resample or linearize in that cell, collapse to the width of cells A–C, and miss the truth. Coverage in the D = 1 row is only 63–65% (bootstrap) and recovers to ~85% at D = 2 and ~92% at D ≥ 3. At D = 0 coverage is nominal only because the truth also has no D contribution. Practical reading: if the real adjudication finds 0 or 1 positives among the 100 code−/note− charts, the headline interval must be accompanied by an explicit upper bound on p_D (e.g. rule of three: p_D < 3% with 95% confidence when x_D = 0, i.e. up to ~10,000 unobserved positives in that cell) rather than presented as a well-calibrated 95% interval. This is a consequence of the 100-chart allocation to D and is a design-stage fact, not something the estimator can repair.
- **Sensitivity is much less precise than under-capture.** Its bootstrap interval is 20–40 percentage points wide once D > 0 (results JSON, `sensitivity`), because every D positive enters its denominator at weight ~3,455; the note-rule PPV interval is 6–11 points wide and unaffected by D.
- **Bootstrap vs linearized.** The two intervals agree in width to within a few percent when x_D ≥ 2; with x_D ∈ {0, 1} the percentile bootstrap is asymmetric and the symmetric normal interval can exceed 100% (the estimator JSON also carries a logit-scale linearized interval, which respects the bounds).
- **PPV and sensitivity.** The note-rule PPV (cells A and B only) is not exposed to cell D and its interval is narrow; sensitivity is exposed to D in the denominator and behaves like the under-capture estimate. Their per-scenario widths and coverage are in the results JSON.

## Tier 3 items arising

Handling of 'Insufficient information' (excluded vs counted negative), the final-label rule for double-reviewed disagreements, and the choice of weighting for the ordinal kappa are logged in `docs/run_2026-09-19/phase6_decisions.md`; the estimator computes every option and leaves the primary as specified.
