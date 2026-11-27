# Aim 1b — hierarchical Bayesian fusion (amendment (q); sensitivity S23, FS-A structured input)

Produced by `scripts/run1127_hier_fusion.py`; numbers from `docs/run_2026-11-27/results/hier_fusion_S23.json`.

**Development diagnostic.** Silver label — known error; not adjudicated truth. The notes input shares a source with the label. Counts from 1 to 10 appear as <11.

Inputs: structured `cat|FS-A|unweighted`, notes `tfidf|S|unweighted`, on the notes subsample (DEV out-of-fold to fit, TEST to evaluate). Each of 8 data-availability strata has its own intercept and weights on the two standardised logits, partially pooled.

## Convergence

| attempt | form | target acceptance | warm-up | R-hat max | ESS min | divergences |
| --: | --- | --: | --: | --: | --: | --: |
| 1 | marginal | 0.9 | 1000 | 1.0048 | 655 | 0 |

Converged: **yes** (criteria: R-hat ≤ 1.01, ESS ≥ 400, no divergences).

## Weights by stratum (posterior mean, 95% interval; standardised logits)

| stratum | DEV admissions | intercept | structured weight | notes weight |
| --- | --: | --- | --- | --- |
| discharge summary no · liver imaging no · FIB-4 inputs no | 1,971 | -3.36 (-3.95, -2.77) | 1.31 (0.82, 2.00) | 1.28 (0.92, 1.67) |
| discharge summary no · liver imaging no · FIB-4 inputs yes | 96 | -3.45 (-4.52, -2.33) | 1.27 (0.70, 2.14) | 1.24 (0.72, 1.92) |
| discharge summary no · liver imaging yes · FIB-4 inputs no | 493 | -4.31 (-4.97, -3.75) | 1.29 (0.93, 1.74) | 0.89 (0.64, 1.14) |
| discharge summary no · liver imaging yes · FIB-4 inputs yes | 91 | -4.17 (-5.11, -3.40) | 1.16 (0.66, 1.71) | 0.99 (0.52, 1.44) |
| discharge summary yes · liver imaging no · FIB-4 inputs no | 8,858 | -3.10 (-3.25, -2.95) | 1.29 (1.05, 1.54) | 1.28 (1.03, 1.54) |
| discharge summary yes · liver imaging no · FIB-4 inputs yes | 4,408 | -3.38 (-3.58, -3.19) | 1.17 (0.95, 1.40) | 1.38 (1.10, 1.68) |
| discharge summary yes · liver imaging yes · FIB-4 inputs no | 3,098 | -4.03 (-4.31, -3.77) | 1.05 (0.84, 1.25) | 1.09 (0.94, 1.24) |
| discharge summary yes · liver imaging yes · FIB-4 inputs yes | 4,801 | -4.15 (-4.38, -3.92) | 1.02 (0.86, 1.17) | 0.92 (0.81, 1.02) |
| population (mu) | | -3.74 (-4.26, -3.21) | 1.19 (0.94, 1.53) | 1.13 (0.86, 1.41) |
| spread across strata (tau) | | 0.63 (0.31, 1.21) | 0.27 (0.07, 0.67) | 0.30 (0.12, 0.65) |

## TEST (scored once)

| arm | AUROC | AUPRC | Brier | log loss | intercept | slope | code-negative AUROC |
| --- | --: | --: | --: | --: | --: | --: | --: |
| hierarchical | 0.866 | 0.481 | 0.0433 | 0.1631 | -0.22 | 0.97 | 0.858 |
| stacked_refit | 0.860 | 0.464 | 0.0444 | 0.1675 | -0.22 | 0.96 | 0.858 |

Paired subject-cluster bootstrap, hierarchical minus stacked (500 replicates): auroc +0.0058 (-0.0012, +0.0135); auprc +0.0166 (-0.0003, +0.0334); brier -0.0010 (-0.0020, -0.0002).

## Calibration in the large by stratum (TEST)

Observed rate against mean predicted probability. A stratum's rates are withheld where a count is suppressed.

| stratum | admissions | positives | observed | hierarchical | stacked |
| --- | --: | --: | --: | --: | --: |
| discharge summary no · liver imaging no · FIB-4 inputs no | 482 | <11 | — | — | — |
| discharge summary no · liver imaging no · FIB-4 inputs yes | 28 | <11 | — | — | — |
| discharge summary no · liver imaging yes · FIB-4 inputs no | 143 | withheld | — | — | — |
| discharge summary no · liver imaging yes · FIB-4 inputs yes | 24 | <11 | — | — | — |
| discharge summary yes · liver imaging no · FIB-4 inputs no | 2,260 | 48 | 0.021 | 0.021 | 0.014 |
| discharge summary yes · liver imaging no · FIB-4 inputs yes | 1,147 | 35 | 0.030 | 0.031 | 0.023 |
| discharge summary yes · liver imaging yes · FIB-4 inputs no | 822 | 93 | 0.113 | 0.135 | 0.127 |
| discharge summary yes · liver imaging yes · FIB-4 inputs yes | 1,258 | 184 | 0.146 | 0.175 | 0.201 |

