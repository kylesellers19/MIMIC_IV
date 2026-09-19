# Aim 1b — notes arm (run_2026-09-19, Phase 8)

**DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.**

Produced by `scripts/run0919_notes_tfidf.py` and `scripts/run0919_notes_embed_arm.py`; numbers read from `docs/run_2026-09-19/results/aim1b_notes_tfidf.json` and `aim1b_notes_arm.json`.

**Read this first.** The silver label is produced by a lexical rule applied to the same text a notes model reads, so a notes model can score near-perfectly by relearning the lexicon. Nothing in this phase is an accuracy estimate. Text variants: **U** unmasked; **M** every lexicon match (all tiers, any assertion status) masked; **S** every sentence containing any lexicon match deleted — asking whether the rest of the documentation carries signal. Masking ignores assertion status on purpose: if only affirmed mentions were masked, the mask itself would encode the label. How the notes arm is ultimately trained (trigger masking, or cross-validation within the 400 adjudicated charts, or both) is Kyle's open decision (D-07); this phase selects nothing.

Subsample: DEV 23,816 · TEST 6,164 · GOLD_HOLDOUT 2,865 (scored, never fitted).

## 8.1 TF-IDF + L2 logistic regression (word 1–2-grams, min_df = 100, sublinear tf; vocabulary fit inside training folds)

**DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.**

| variant · imbalance | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| U · unweighted (TEST) | 6,164 | 383 | 0.896 (0.862–0.937) | 0.596 (0.518–0.674) | 0.038 (0.031–0.045) | -0.144 | 1.444 |
| U · weighted (TEST) | 6,164 | 383 | 0.909 (0.877–0.948) | 0.646 (0.572–0.720) | 0.063 (0.056–0.072) | -1.834 | 1.310 |
| U · weighted+corrected (TEST) | 6,164 | 383 | 0.909 (0.877–0.948) | 0.646 (0.572–0.720) | 0.038 (0.031–0.046) | 0.720 | 1.310 |
| M · unweighted (TEST) | 6,164 | 383 | 0.912 (0.887–0.940) | 0.616 (0.538–0.691) | 0.037 (0.031–0.044) | -0.137 | 1.536 |
| M · weighted (TEST) | 6,164 | 383 | 0.930 (0.908–0.953) | 0.671 (0.603–0.742) | 0.061 (0.054–0.069) | -1.821 | 1.423 |
| M · weighted+corrected (TEST) | 6,164 | 383 | 0.930 (0.908–0.953) | 0.671 (0.603–0.742) | 0.038 (0.030–0.045) | 0.732 | 1.423 |
| S · unweighted (TEST) | 6,164 | 383 | 0.826 (0.788–0.869) | 0.407 (0.326–0.488) | 0.047 (0.039–0.055) | -0.180 | 1.126 |
| S · weighted (TEST) | 6,164 | 383 | 0.829 (0.794–0.870) | 0.422 (0.346–0.503) | 0.096 (0.086–0.108) | -2.059 | 0.950 |
| S · weighted+corrected (TEST) | 6,164 | 383 | 0.829 (0.794–0.870) | 0.422 (0.346–0.503) | 0.046 (0.038–0.055) | 0.494 | 0.950 |

DEV OOF:

| variant · imbalance | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| U · unweighted (OOF) | 23,816 | 1,719 | 0.926 | 0.636 | 0.043 | 0.066 | 1.661 |
| U · weighted (OOF) | 23,816 | 1,719 | 0.941 | 0.692 | 0.060 | -1.631 | 1.527 |
| U · weighted+corrected (OOF) | 23,816 | 1,719 | 0.941 | 0.691 | 0.045 | 0.924 | 1.525 |
| M · unweighted (OOF) | 23,816 | 1,719 | 0.927 | 0.642 | 0.043 | 0.066 | 1.678 |
| M · weighted (OOF) | 23,816 | 1,719 | 0.943 | 0.701 | 0.059 | -1.622 | 1.563 |
| M · weighted+corrected (OOF) | 23,816 | 1,719 | 0.943 | 0.700 | 0.045 | 0.932 | 1.560 |
| S · unweighted (OOF) | 23,816 | 1,719 | 0.859 | 0.444 | 0.052 | 0.041 | 1.256 |
| S · weighted (OOF) | 23,816 | 1,719 | 0.864 | 0.456 | 0.090 | -1.821 | 1.056 |
| S · weighted+corrected (OOF) | 23,816 | 1,719 | 0.863 | 0.456 | 0.054 | 0.734 | 1.055 |

Within code-negative TEST admissions:

| variant · imbalance | n | positives | AUROC | AUPRC |
| --- | --: | --: | --: | --: |
| U · unweighted | 6,057 | 286 | 0.907 | 0.557 |
| U · weighted | 6,057 | 286 | 0.919 | 0.613 |
| U · weighted+corrected | 6,057 | 286 | 0.919 | 0.613 |
| M · unweighted | 6,057 | 286 | 0.916 | 0.565 |
| M · weighted | 6,057 | 286 | 0.933 | 0.625 |
| M · weighted+corrected | 6,057 | 286 | 0.933 | 0.625 |
| S · unweighted | 6,057 | 286 | 0.833 | 0.352 |
| S · weighted | 6,057 | 286 | 0.836 | 0.371 |
| S · weighted+corrected | 6,057 | 286 | 0.836 | 0.371 |

### Top coefficients, variant U (alphabetic tokens, document frequency ≥ 100; vocabulary 44,420)

| positive term | coef | df | | negative term | coef | df |
| --- | --: | --: | --- | --- | --: | --: |
| steatosis | 11.739 | 917 | | etoh cirrhosis | -1.066 | 306 |
| fatty | 11.453 | 1,709 | | parenchyma appears | -0.96 | 779 |
| fatty liver | 9.427 | 496 | | homogenous attenuation | -0.909 | 1,751 |
| hepatic steatosis | 9.087 | 658 | | hcv cirrhosis | -0.901 | 276 |
| nash | 5.901 | 237 | | throughout there | -0.812 | 1,861 |
| liver | 5.046 | 9,647 | | no | -0.756 | 23,533 |
| fatty infiltration | 4.735 | 562 | | alcoholic cirrhosis | -0.744 | 286 |
| cirrhosis | 4.255 | 1,970 | | the | -0.729 | 23,084 |
| hepatic | 4.241 | 5,662 | | dementia | -0.718 | 1,306 |
| infiltration | 3.837 | 961 | | appears within | -0.717 | 1,229 |
| liver disease | 3.782 | 1,318 | | liver enhances | -0.702 | 697 |
| with fatty | 3.493 | 340 | | assess for | -0.702 | 2,561 |
| nash cirrhosis | 3.32 | 138 | | the hepatic | -0.7 | 2,174 |
| echogenic | 3.054 | 1,173 | | chf | -0.682 | 3,217 |
| fibrosis | 3.026 | 1,264 | | groin | -0.68 | 1,488 |
| echogenic liver | 2.871 | 410 | | calcifications | -0.664 | 4,061 |
| steatosis there | 2.446 | 171 | | ckd | -0.657 | 2,127 |
| steatohepatitis | 2.419 | 244 | | limits the | -0.652 | 2,370 |
| is diffusely | 2.341 | 639 | | of | -0.649 | 23,225 |
| liver consistent | 2.312 | 515 | | demonstrates homogenous | -0.641 | 1,768 |
| infiltration of | 2.265 | 255 | | measures cm | -0.634 | 2,141 |
| with steatosis | 2.264 | 239 | | transplant | -0.627 | 1,690 |
| forms of | 2.134 | 360 | | the rectum | -0.618 | 1,839 |
| diffusely | 2.123 | 2,163 | | calcified | -0.616 | 2,496 |
| hepatic fibrosis | 1.998 | 309 | | temporal | -0.592 | 1,086 |

### Top coefficients, variant M (alphabetic tokens, document frequency ≥ 100; vocabulary 44,413)

| positive term | coef | df | | negative term | coef | df |
| --- | --: | --: | --- | --- | --: | --: |
| mask | 22.772 | 2,599 | | homogenous attenuation | -0.961 | 1,751 |
| with mask | 6.119 | 671 | | etoh cirrhosis | -0.944 | 306 |
| cirrhosis | 4.217 | 1,970 | | parenchyma appears | -0.927 | 779 |
| mask there | 3.134 | 298 | | hcv cirrhosis | -0.833 | 276 |
| mask of | 3.028 | 288 | | throughout there | -0.828 | 1,861 |
| fibrosis | 3.02 | 1,264 | | dementia | -0.727 | 1,306 |
| mask cirrhosis | 2.967 | 147 | | no | -0.726 | 23,533 |
| liver disease | 2.884 | 1,249 | | liver enhances | -0.72 | 697 |
| mask impression | 2.873 | 115 | | the | -0.719 | 23,084 |
| liver | 2.765 | 9,530 | | groin | -0.699 | 1,488 |
| of mask | 2.754 | 432 | | chf | -0.694 | 3,217 |
| diffuse mask | 2.535 | 148 | | demonstrates homogenous | -0.683 | 1,768 |
| is diffusely | 2.463 | 639 | | appears within | -0.673 | 1,229 |
| mask no | 2.32 | 202 | | assess for | -0.667 | 2,561 |
| mask consistent | 2.308 | 304 | | ckd | -0.659 | 2,127 |
| diffusely | 2.233 | 2,163 | | calcifications | -0.658 | 4,061 |
| mask with | 2.188 | 160 | | transplant | -0.652 | 1,690 |
| forms of | 2.147 | 360 | | alcoholic cirrhosis | -0.65 | 286 |
| mild mask | 2.128 | 138 | | limits the | -0.637 | 2,370 |
| hepatic fibrosis | 1.979 | 309 | | measures cm | -0.637 | 2,141 |
| forms | 1.978 | 462 | | homogenous | -0.633 | 1,918 |
| liver is | 1.881 | 3,630 | | of | -0.632 | 23,225 |
| cirrhosis cannot | 1.859 | 291 | | the rectum | -0.624 | 1,839 |
| other forms | 1.858 | 302 | | baseline | -0.619 | 7,690 |
| disease including | 1.854 | 440 | | calcified | -0.612 | 2,496 |

### Top coefficients, variant S (alphabetic tokens, document frequency ≥ 100; vocabulary 44,380)

| positive term | coef | df | | negative term | coef | df |
| --- | --: | --: | --- | --- | --: | --: |
| cirrhosis | 4.112 | 1,889 | | parenchyma appears | -1.493 | 779 |
| liver disease | 4.018 | 1,229 | | homogenous attenuation | -1.189 | 1,750 |
| forms of | 3.728 | 350 | | etoh cirrhosis | -1.168 | 302 |
| fibrosis | 3.625 | 1,173 | | appears within | -1.067 | 1,229 |
| forms | 3.458 | 452 | | hcv cirrhosis | -1.057 | 276 |
| other forms | 3.342 | 293 | | the hepatic | -1.039 | 2,166 |
| is diffusely | 2.904 | 589 | | hepatic parenchyma | -0.977 | 1,144 |
| of liver | 2.818 | 1,186 | | limits the | -0.95 | 2,370 |
| excluded on | 2.445 | 428 | | demonstrates homogenous | -0.932 | 1,761 |
| cirrhosis cannot | 2.385 | 207 | | liver enhances | -0.889 | 697 |
| diffusely | 2.346 | 2,096 | | alcoholic cirrhosis | -0.874 | 283 |
| diffusely echogenic | 2.272 | 288 | | homogenous | -0.873 | 1,910 |
| echogenic | 2.233 | 1,057 | | throughout there | -0.845 | 1,870 |
| liver | 2.174 | 9,471 | | dementia | -0.817 | 1,306 |
| fibrosis cirrhosis | 2.09 | 174 | | transplant | -0.808 | 1,690 |
| more advanced | 2.018 | 148 | | groin | -0.795 | 1,488 |
| hepatic fibrosis | 1.981 | 176 | | calcifications | -0.793 | 4,061 |
| fatty | 1.965 | 815 | | chf | -0.788 | 3,217 |
| impression other | 1.953 | 159 | | assess for | -0.786 | 2,559 |
| crohn | 1.882 | 437 | | baseline | -0.745 | 7,669 |
| excluded | 1.796 | 4,087 | | the rectum | -0.727 | 1,839 |
| advanced liver | 1.795 | 141 | | demonstrates | -0.725 | 5,484 |
| be excluded | 1.741 | 2,363 | | ckd | -0.719 | 2,124 |
| adenoma | 1.735 | 888 | | and there | -0.719 | 3,766 |
| obesity | 1.717 | 1,880 | | measures cm | -0.717 | 2,141 |

Variant U's top terms are expected to be the lexicon itself — that table is the demonstration of circularity. What survives in S is the interesting result.

## 8.2 Transformer embeddings (chunked Bio_ClinicalBERT, 1,536-d admission vectors)

**DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.**

Variant S: 27,845 admissions embedded (DEV 19,872, TEST 5,108, GOLD 2,865); head kept by DEV OOF AUPRC: **lgbm**.

| head · split | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| lr · OOF | 19,872 | 1,438 | 0.785 | 0.251 | 0.064 | -0.018 | 0.553 |
| lr · TEST | 5,108 | 322 | 0.754 (0.704–0.799) | 0.216 (0.165–0.292) | 0.058 (0.050–0.068) | -0.254 | 0.511 |
| lgbm · OOF | 19,872 | 1,438 | 0.804 | 0.274 | 0.063 | 1.324 | 0.577 |
| lgbm · TEST | 5,108 | 322 | 0.788 (0.742–0.832) | 0.246 (0.187–0.326) | 0.055 (0.046–0.065) | 0.804 | 0.589 |

- Variant U: no embeddings available.
## 8.3 Notes-augmented model — CatBoost on FS-B + PC1-64 of Bio_ClinicalBERT (variant S)

**DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.** **Silver label — known error; not adjudicated truth; final performance requires the gold standard.**

DEV 19,872 · TEST 5,108.

| imbalance · split | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| unweighted · OOF | 19,872 | 1,438 | 0.840 | 0.305 | 0.058 | 0.126 | 1.056 |
| unweighted · TEST | 5,108 | 322 | 0.829 (0.795–0.863) | 0.328 (0.246–0.436) | 0.050 (0.042–0.059) | -0.036 | 1.010 |
| weighted · OOF | 19,872 | 1,438 | 0.835 | 0.298 | 0.132 | -2.121 | 1.105 |
| weighted · TEST | 5,108 | 322 | 0.813 (0.776–0.848) | 0.255 (0.182–0.366) | 0.143 (0.132–0.154) | -2.373 | 0.989 |
| weighted+corrected · OOF | 19,872 | 1,438 | 0.835 | 0.298 | 0.059 | 0.440 | 1.106 |
| weighted+corrected · TEST | 5,108 | 322 | 0.813 (0.776–0.848) | 0.255 (0.182–0.366) | 0.053 (0.044–0.062) | 0.178 | 0.989 |
