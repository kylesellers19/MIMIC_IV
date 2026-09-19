# Aim 1b — fusion arm (run_2026-09-19, Phase 9.1)

Silver label — known error; not adjudicated truth; final performance requires the gold standard. Rows including the notes model carry the circularity caveat (label and input share a source).

Produced by `scripts/run0919_fusion_lock.py`; numbers from `docs/run_2026-09-19/results/aim1b_fusion.json`. Locked GOLD_HOLDOUT predictions: `docs/aim1b_locked_predictions.md`.

Layer 0: structured FS-B best-calibrated variant on DEV OOF = `cat|FS-B|unweighted` (FS-A sensitivity = `cat|FS-A|unweighted`); notes model = `tfidf|S|unweighted` (tfidf). Layer 1: logistic regression on the two logits, fit on the subsample's DEV OOF predictions. Code status is never an input.

Fusion coefficients: primary: intercept 1.235, w_structured 0.519, w_notes 0.993; sensitivity_FS-A: intercept 0.760, w_structured 0.533, w_notes 0.793.

## Arms on the subsample TEST admissions

**Not every arm is scored on the same admissions.** Arms that need an embedding are evaluated only on the TEST admissions that were encoded before the embedding budget expired; the `n` column makes this explicit and the rows are not strictly comparable with the full-TEST rows.

| arm | n | positives | AUROC | AUPRC | Brier | intercept | slope | code-negative AUROC | code-negative AUPRC |
| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| fusion (primary) | 6,164 | 383 | 0.853 | 0.435 | 0.046 | -0.207 | 0.934 | 0.847 | 0.353 |
| structured (primary: cat|FS-B|unweighted) | 6,164 | 383 | 0.793 | 0.291 | 0.051 | -0.139 | 1.013 | 0.763 | 0.188 |
| fusion (sensitivity_FS-A) | 6,164 | 383 | 0.860 | 0.464 | 0.044 | -0.217 | 0.961 | 0.858 | 0.384 |
| structured (sensitivity_FS-A: cat|FS-A|unweighted) | 6,164 | 383 | 0.854 | 0.392 | 0.047 | -0.167 | 1.021 | 0.842 | 0.276 |
| notes (tfidf|S|unweighted) | 6,164 | 383 | 0.826 | 0.407 | 0.047 | -0.180 | 1.126 | 0.833 | 0.352 |
| notes-augmented (aug|FS-B+notes|unweighted) | 5,108 | 322 | 0.829 | 0.328 | 0.050 | -0.036 | 1.010 | 0.826 | 0.245 |
| notes-augmented (aug|FS-B+notes|weighted) | 5,108 | 322 | 0.813 | 0.255 | 0.143 | -2.373 | 0.989 | 0.814 | 0.186 |
| notes-augmented (aug|FS-B+notes|weighted+corrected) | 5,108 | 322 | 0.813 | 0.255 | 0.053 | 0.178 | 0.989 | 0.814 | 0.186 |

## Paired differences versus the primary structured arm (subject-cluster bootstrap, 500 replicates)

| comparison | ΔAUROC (95% CI) | ΔAUPRC (95% CI) | ΔBrier (95% CI) |
| --- | --- | --- | --- |
| fusion (primary) minus structured (primary: cat|FS-B|unweighted) | +0.060 (+0.031, +0.089) | +0.147 (+0.074, +0.223) | -0.006 (-0.009, -0.002) |
| fusion (sensitivity_FS-A) minus structured (primary: cat|FS-B|unweighted) | +0.067 (+0.034, +0.100) | +0.176 (+0.100, +0.254) | -0.007 (-0.010, -0.004) |
| structured (sensitivity_FS-A: cat|FS-A|unweighted) minus structured (primary: cat|FS-B|unweighted) | +0.061 (+0.037, +0.086) | +0.100 (+0.068, +0.136) | -0.004 (-0.006, -0.003) |
| notes (tfidf|S|unweighted) minus structured (primary: cat|FS-B|unweighted) | +0.033 (-0.018, +0.080) | +0.121 (+0.019, +0.221) | -0.005 (-0.008, -0.001) |
| notes-augmented (aug|FS-B+notes|unweighted) minus structured (primary: cat|FS-B|unweighted) | +0.036 (+0.003, +0.068) | +0.042 (-0.021, +0.103) | -0.001 (-0.004, +0.002) |
| notes-augmented (aug|FS-B+notes|weighted) minus structured (primary: cat|FS-B|unweighted) | +0.021 (-0.016, +0.055) | -0.029 (-0.091, +0.034) | +0.091 (+0.079, +0.104) |
| notes-augmented (aug|FS-B+notes|weighted+corrected) minus structured (primary: cat|FS-B|unweighted) | +0.021 (-0.016, +0.055) | -0.029 (-0.091, +0.034) | +0.001 (-0.002, +0.005) |

Every row that includes the notes model inherits the circularity caveat: its silver-label advantage is partly the label's own lexicon. H1b-iii (fusion at least as discriminating as the better base learner and better calibrated) is a silver-label observation here; the gold harness (`scripts/aim1b_evaluate_gold.py`) is what tests it.
