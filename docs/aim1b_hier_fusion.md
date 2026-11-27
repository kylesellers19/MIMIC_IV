# Aim 1b — hierarchical Bayesian fusion (amendment (q))

Produced by `scripts/run1127_hier_fusion.py`; numbers from `docs/run_2026-11-27/results/hier_fusion.json`.

**Development diagnostic.** Silver label — known error; not adjudicated truth. The notes input shares a source with the label. Counts from 1 to 10 appear as <11.

Inputs: structured `cat|FS-B|unweighted`, notes `tfidf|S|unweighted`, on the notes subsample (DEV out-of-fold to fit, TEST to evaluate). Each of 8 data-availability strata has its own intercept and weights on the two standardised logits, partially pooled.

## Convergence

| attempt | form | target acceptance | warm-up | R-hat max | ESS min | divergences |
| --: | --- | --: | --: | --: | --: | --: |
| 1 | marginal | 0.9 | 1000 | 1.0049 | 800 | 1 |
| 2 | noncentered | 0.9 | 1000 | 1.0093 | 424 | 7 |
| 3 | marginal | 0.99 | 2000 | 1.0039 | 1295 | 0 |

Converged: **yes** (criteria: R-hat ≤ 1.01, ESS ≥ 400, no divergences).

## Weights by stratum (posterior mean, 95% interval; standardised logits)

| stratum | DEV admissions | intercept | structured weight | notes weight |
| --- | --: | --- | --- | --- |
| discharge summary no · liver imaging no · FIB-4 inputs no | 1,971 | -3.79 (-4.29, -3.35) | 0.89 (0.54, 1.37) | 1.30 (0.99, 1.66) |
| discharge summary no · liver imaging no · FIB-4 inputs yes | 96 | -3.52 (-4.35, -2.76) | 0.85 (0.41, 1.45) | 1.25 (0.79, 1.85) |
| discharge summary no · liver imaging yes · FIB-4 inputs no | 493 | -3.25 (-3.64, -2.83) | 0.81 (0.50, 1.15) | 1.03 (0.80, 1.26) |
| discharge summary no · liver imaging yes · FIB-4 inputs yes | 91 | -3.67 (-4.40, -3.08) | 0.78 (0.41, 1.19) | 1.08 (0.67, 1.45) |
| discharge summary yes · liver imaging no · FIB-4 inputs no | 8,858 | -3.43 (-3.60, -3.28) | 0.89 (0.72, 1.08) | 1.30 (1.06, 1.55) |
| discharge summary yes · liver imaging no · FIB-4 inputs yes | 4,408 | -3.80 (-4.05, -3.57) | 0.82 (0.65, 1.00) | 1.36 (1.10, 1.65) |
| discharge summary yes · liver imaging yes · FIB-4 inputs no | 3,098 | -3.18 (-3.39, -2.98) | 0.67 (0.52, 0.82) | 1.20 (1.06, 1.36) |
| discharge summary yes · liver imaging yes · FIB-4 inputs yes | 4,801 | -3.57 (-3.76, -3.39) | 0.63 (0.53, 0.73) | 0.97 (0.86, 1.07) |
| population (mu) | | -3.52 (-3.90, -3.18) | 0.79 (0.60, 1.03) | 1.18 (0.95, 1.43) |
| spread across strata (tau) | | 0.38 (0.15, 0.81) | 0.21 (0.06, 0.53) | 0.25 (0.09, 0.56) |

## TEST (scored once)

| arm | AUROC | AUPRC | Brier | log loss | intercept | slope | code-negative AUROC |
| --- | --: | --: | --: | --: | --: | --: | --: |
| hierarchical | 0.859 | 0.452 | 0.0447 | 0.1676 | -0.21 | 0.94 | 0.854 |
| stacked_refit | 0.853 | 0.435 | 0.0455 | 0.1704 | -0.21 | 0.93 | 0.847 |

Paired subject-cluster bootstrap, hierarchical minus stacked (500 replicates): auroc +0.0064 (+0.0022, +0.0105); auprc +0.0177 (+0.0007, +0.0339); brier -0.0008 (-0.0016, +0.0000).

## Calibration in the large by stratum (TEST)

Observed rate against mean predicted probability. A stratum's rates are withheld where a count is suppressed.

| stratum | admissions | positives | observed | hierarchical | stacked |
| --- | --: | --: | --: | --: | --: |
| discharge summary no · liver imaging no · FIB-4 inputs no | 482 | <11 | — | — | — |
| discharge summary no · liver imaging no · FIB-4 inputs yes | 28 | <11 | — | — | — |
| discharge summary no · liver imaging yes · FIB-4 inputs no | 143 | withheld | — | — | — |
| discharge summary no · liver imaging yes · FIB-4 inputs yes | 24 | <11 | — | — | — |
| discharge summary yes · liver imaging no · FIB-4 inputs no | 2,260 | 48 | 0.021 | 0.021 | 0.019 |
| discharge summary yes · liver imaging no · FIB-4 inputs yes | 1,147 | 35 | 0.030 | 0.031 | 0.035 |
| discharge summary yes · liver imaging yes · FIB-4 inputs no | 822 | 93 | 0.113 | 0.131 | 0.093 |
| discharge summary yes · liver imaging yes · FIB-4 inputs yes | 1,258 | 184 | 0.146 | 0.178 | 0.202 |

