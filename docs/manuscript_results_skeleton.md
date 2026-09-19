# Results skeleton — table shells with computable-stage numbers

> **What this file is.** The manuscript's result tables, filled in wherever a tracked results file already contains the number, and marked `[PENDING ADJUDICATION]` wherever the number requires the chart adjudication. Every filled cell is traceable to a file named beneath its table. **No number here was written from memory, rounded beyond what the source states, or inferred.** Every Aim 1b model job has now completed, so Tables 4a–4e and 4g are filled; Table 4f (performance against the gold standard) and the whole of Table 5 remain `[PENDING ADJUDICATION]`.
>
> **Headline discipline.** The headline result of this study is the **inverse-probability-weighted, adjudicated under-capture estimate** (Table 5), which does not yet exist. The computable recovery share of 81.9% (Table 2) is a comparison of two computable phenotypes — an ICD code set against a frozen lexical rule — and is **never** to be presented as the headline, as a recovery estimate, or as a count of missed cases. The code−/note+ cell is a sampling stratum.

---

## Headline statement (to be completed after adjudication)

> Among admissions adjudicated as having documented hepatic steatosis, the population-weighted proportion carrying no MASLD diagnosis code was **[PENDING ADJUDICATION]%** (95% CI **[PENDING ADJUDICATION]** to **[PENDING ADJUDICATION]**), estimated from a stratified sample of 400 blinded chart reviews reweighted to the source population of 373,992 admissions.

---

## Table 1. Cohort derivation

Source: `docs/run_2026-09-19/results/cohort_flow.json`; cross-checked against `docs/aim1a_loose_ends.md` §4.5 and `docs/tables/table0.md`.

| Step | Admissions | Distinct subjects |
| --- | --: | --: |
| All admissions, MIMIC-IV v3.1 `hosp` | 546,028 | 223,452 |
| − admissions with zero diagnosis rows | −531 | — |
| **= Analysis population** | **545,497** | **223,291** |
| · MASLD code-positive | 9,143 | — |
| − note restriction (i): subject absent from MIMIC-IV-Note entirely (release lineage) | −100,029 | — |
| − note restriction (ii): subject has notes on other admissions, none linked to this one | −71,476 | — |
| **= Locked analysis population (≥ 1 linked discharge or radiology note)** | **373,992** | **161,119** |
| · MASLD code-positive | 5,740 | — |
| · MASLD code-negative | 368,252 | — |

Footnotes to carry into the manuscript:
- Grain is the admission (`hadm_id`). Distinct-subject counts for code-positive and code-negative overlap and are therefore not additive.
- The two note-restriction components sum to 171,505, equal to the subtraction-derived total (sum check passes); the locked population equals the cleaned-population row count exactly.
- **No admission-year window is imposed.** Coverage by derived admission year is flat at approximately 67–70%. Coverage by the per-patient `anchor_year_group` was 76.38% / 75.15% / 73.97% / 66.84% / 0.00% for 2008–2010 / 2011–2013 / 2014–2016 / 2017–2019 / 2020–2022; of removed admissions, 42,413 have anchor group 2020–2022 and 129,092 earlier groups. The lineage split is the one this table uses.
- Pre-specified sensitivity population (discharge summary required): 331,604 admissions / 145,817 subjects / 5,552 code-positive.
- The note restriction is differential: code-positive admissions fall 37.2% versus 31.4% overall.

### Table 1b. Analysis partitions for modelling

Source: `docs/run_2026-09-19/results/phase2_splits.json`.

| Partition | Admissions | Subjects | Note-positive (silver) | Silver prevalence | Code-positive |
| --- | --: | --: | --: | --: | --: |
| GOLD_HOLDOUT (never fitted on) | 2,865 | 411 | 1,161 | 40.52% | 479 |
| TEST (touched once per model) | 75,124 | 32,142 | 5,426 | 7.22% | 1,015 |
| DEV (5 subject-level folds) | 296,003 | 128,566 | 21,239 | 7.18% | 4,246 |

GOLD_HOLDOUT by sampling cell under the primary definition: code−/note− 1,612; code−/note+ 774; code+/note+ 387; code+/note− 92.

---

## Table 2. Code × note cross-tabulation under four definitions

Source: `docs/run_2026-09-19/results/integrity_gate.json` (field `reproduced`; all 14 integrity checks pass); percentages from `docs/aim1a_crosstab.md`. Population N = 373,992 admissions / 161,119 subjects. A = code+/note+, B = code−/note+, C = code+/note−, D = code−/note−.

| Definition | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− | Recovery share B/(A+B) | Corroboration share A/(A+C) |
| --- | --: | --: | --: | --: | --: | --: |
| (a) v1.1.0, inpatient-linked notes only | 4,805 (1.28%) | 13,612 (3.64%) | 935 (0.25%) | 354,640 (94.83%) | 73.91% | 83.71% |
| **(b) v1.1.0 + outpatient radiology −365/+30 — PRIMARY** | **5,027 (1.34%)** | **22,799 (6.10%)** | **713 (0.19%)** | **345,453 (92.37%)** | **81.93%** | **87.58%** |
| (c) v1.1.0 + outpatient radiology −90/+30 (window sensitivity) | 4,908 (1.31%) | 17,851 (4.77%) | 832 (0.22%) | 350,401 (93.69%) | 78.43% | 85.51% |
| (d) v1.0.0, inpatient-linked (rule-version sensitivity) | 4,850 (1.30%) | 22,443 (6.00%) | 890 (0.24%) | 345,809 (92.46%) | 82.23% | 84.49% |

Note-positive admissions under the primary definition: **27,826**.

**Mandatory caption text.** *This table compares two computable phenotypes. It is not an adjudicated estimate. The recovery share is the proportion of note-positive admissions carrying no MASLD code, not a proportion of patients whose disease was missed; the code−/note+ cell is a sampling stratum for the chart review in Table 5.*

### Table 2b. Sensitivity variants of the recovery share, primary definition (b)

Sources as marked.

| Variant | Note-positive | code−/note+ | Recovery share | Source |
| --- | --: | --: | --: | --- |
| Primary (steatosis level) | 27,826 | 22,799 | 81.93% | `integrity_gate.json` |
| Tier C (hedged) mentions counted positive | — | 23,353 | 82.23% | `loose_ends_43_44.json` |
| ICD-9 571.9 removed from the code set | — | 22,811 | 81.98% | `sens_5719.json` |
| Discharge-summary-only population (n = 331,604) | — | 21,134 | 81.06% | `loose_ends_43_44.json` |
| Imaging-observed population (n = 138,603) | — | 19,248 | 83.7% | `docs/imaging_denominator.md` |
| Steatosis excluding alcohol-related codes | 23,068 | 18,673 | 80.9% | `docs/sld_subclassification.md` |
| Steatosis + ≥ 1 cardiometabolic criterion (MASLD-consistent) | 26,517 | 21,593 | 81.4% | `docs/sld_subclassification.md` |
| Steatosis excluding all competing etiologies (NAFLD-era; **not** primary) | 18,749 | 15,646 | 83.4% | `docs/sld_subclassification.md` |

### Table 2c. Subject grain (secondary), definition (b)

Source: `docs/aim1a_crosstab.md`. 161,119 subjects: code+/note+ 3,292; code−/note+ 11,709; code+/note− 383; code−/note− 145,735.

### Table 2d. Imaging denominator

Source: `docs/imaging_denominator.md`. Under the primary −365/+30 window: no radiology at all 24,192 (6.5%); imaged but no liver-inclusive study 211,197 (56.5%); at least one liver-inclusive study 138,603 (37.1%). Liver-inclusive imaging rate by principal-diagnosis chapter ranges from 11.3% (Eye) to 70.0% (Digestive). Within abdominal-plausible chapters the maximum one-versus-rest |SMD| in imaging rate grows rather than shrinks: race 0.277 → 0.381, insurance 0.058 → 0.177; coding status +0.736 → +0.663.

---

## Table 3. Recovery and corroboration shares by stratum (compact)

Source: `docs/run_2026-09-19/results/aim1c_level1.json`, rendered in `docs/aim1c_level1.md` and `docs/tables/aim1c_level1_{race,insurance,gender,language,age_band}.md`. Definition (b). 95% CIs are subject-cluster bootstraps, 500 replicates. Floors: no recovery share where B < 11; no corroboration share where A + C < 11. **Strata are never merged**; non-analyzable strata are declared. A CI wider than 20 percentage points is marked as not supporting a claim.

**Small-cell rule: any cell count of 1–10 is written `<11`.** **This is an abbreviated table showing the largest strata only. The complete tables — all 33 race levels, all 26 language levels, every cell count, every mechanism measure, and the 571.9 sensitivity column — are in `docs/aim1c_level1.md` and must be cited there.**

### 3a. Race (largest strata)

| Race (as recorded) | A | B | C | D | Recovery % (95% CI) | Claim supported? | Corroboration % (95% CI) | SMD coding rate vs rest |
| --- | --: | --: | --: | --: | --- | --- | --- | --: |
| WHITE | 3,167 | 14,785 | 447 | 222,559 | 82.4 (81.5–83.2) | yes | 87.6 (86.5–88.8) | −0.031 |
| BLACK/AFRICAN AMERICAN | 410 | 2,449 | 76 | 46,706 | 85.7 (84.1–87.1) | yes | 84.4 (80.6–87.8) | −0.112 |
| OTHER | 185 | 718 | 27 | 11,598 | 79.5 (75.5–82.7) | yes | 87.3 (81.9–92.2) | +0.064 |
| HISPANIC/LATINO – PUERTO RICAN | 235 | 622 | 20 | 5,943 | 72.6 (68.0–76.5) | yes | 92.2 (88.6–95.9) | +0.232 |
| WHITE – OTHER EUROPEAN | 139 | 524 | 22 | 6,441 | 79.0 (74.7–83.0) | yes | 86.3 (80.4–91.7) | +0.075 |
| HISPANIC OR LATINO | 92 | 518 | 16 | 5,543 | 84.9 (80.6–88.8) | yes | 85.2 (77.4–92.3) | −0.082 |
| UNKNOWN † | 88 | 493 | 11 | 9,134 | 84.9 (81.8–87.8) | yes | 88.9 (82.9–94.3) | −0.080 |
| ASIAN – CHINESE | 67 | 374 | 11 | 4,241 | 84.8 (80.3–88.6) | yes | 85.9 (77.2–92.7) | −0.078 |
| HISPANIC/LATINO – DOMINICAN | 79 | 289 | 13 | 3,229 | 78.5 (73.0–84.0) | yes | 85.9 (77.3–91.9) | +0.087 |
| ASIAN | 49 | 262 | <11 | 4,330 | 84.2 (78.8–89.2) | yes | 84.5 (73.5–93.7) — CI 20.2 pts, claim not supported | −0.062 |
| BLACK/CAPE VERDEAN | 57 | 235 | <11 | 3,691 | 80.5 (73.9–86.8) | yes | 93.4 (86.5–98.8) | +0.038 |
| WHITE – RUSSIAN | 81 | 214 | 11 | 4,354 | 72.5 (63.1–82.5) | yes | 88.0 (77.3–95.2) | +0.228 |

† UNKNOWN, UNABLE TO OBTAIN and PATIENT DECLINED TO ANSWER are encounter characteristics, not population groups. Analyzable race strata: **33 of 33**; claim-supported on recovery: **21**. Non-analyzable: **none**.

### 3b. Insurance

| Insurance | A | B | C | D | Recovery % (95% CI) | Corroboration % (95% CI) | SMD coding rate vs rest |
| --- | --: | --: | --: | --: | --- | --- | --: |
| Medicare | 1,882 | 8,684 | 327 | 169,614 | 82.2 (80.9–83.4) | 85.2 (83.6–87.0) | −0.011 |
| Private | 2,006 | 8,136 | 245 | 104,835 | 80.2 (79.1–81.3) | 89.1 (87.7–90.5) | +0.070 |
| Medicaid | 987 | 5,042 | 124 | 56,874 | 83.6 (82.4–84.9) | 88.8 (87.0–90.6) | −0.057 |
| Other | 122 | 724 | 13 | 9,111 | 85.6 (82.9–88.2) | 90.4 (84.7–95.1) | −0.102 |
| (missing) | 30 | 207 | <11 | 4,952 | 87.3 (82.3–91.5) | 88.2 (77.1–97.6) — CI 20.5 pts, claim not supported | −0.152 |
| No charge | 0 | <11 | 0 | 67 | **not analyzable** (B < 11) | **not analyzable** | — |

### 3c. Sex

| Sex | A | B | C | D | Recovery % (95% CI) | Corroboration % (95% CI) |
| --- | --: | --: | --: | --: | --- | --- |
| Female | 2,494 | 10,724 | 374 | 177,622 | 81.1 (80.1–82.0) | 87.0 (85.5–88.2) |
| Male | 2,533 | 12,075 | 339 | 167,831 | 82.7 (81.6–83.6) | 88.2 (86.9–89.5) |

### 3d. Age band

Ages ≥ 89 are recoded to 91 in MIMIC-IV, so the 89+ band is an aggregate.

| Age band | A | B | C | D | Recovery % (95% CI) | Corroboration % (95% CI) |
| --- | --: | --: | --: | --: | --- | --- |
| 18–39 | 583 | 2,666 | 64 | 50,280 | 82.1 (80.3–83.8) | 90.1 (87.5–92.2) |
| 40–54 | 1,331 | 6,225 | 162 | 65,872 | 82.4 (81.1–83.7) | 89.1 (87.4–90.8) |
| 55–64 | 1,365 | 6,384 | 202 | 67,657 | 82.4 (81.0–83.8) | 87.1 (85.0–88.9) |
| 65–74 | 1,200 | 4,902 | 162 | 67,564 | 80.3 (78.6–81.8) | 88.1 (86.0–90.3) |
| 75–88 | 503 | 2,393 | 106 | 73,714 | 82.6 (80.3–84.6) | 82.6 (79.2–85.9) |
| 89+ | 45 | 229 | 17 | 20,366 | 83.6 (76.6–89.7) | 72.6 (56.1–88.1) — CI 32.0 pts, claim not supported |

### 3e. Language (largest strata)

Analyzable: **17 of 26**; claim-supported on recovery: **10**. Nine strata are declared non-analyzable and are not merged.

| Language | A | B | C | D | Recovery % (95% CI) | Claim supported? |
| --- | --: | --: | --: | --: | --- | --- |
| English | 4,428 | 20,342 | 629 | 310,810 | 82.1 (81.4–82.9) | yes |
| Spanish | 317 | 1,114 | 38 | 11,023 | 77.8 (74.4–80.8) | yes |
| Chinese | 55 | 381 | <11 | 4,559 | 87.4 (83.3–91.2) | yes |
| Russian | 76 | 227 | 14 | 6,098 | 74.9 (66.6–84.0) | yes |
| Kabuverdianu | 54 | 192 | <11 | 3,112 | 78.0 (70.5–85.8) | yes |
| Portuguese | 31 | 150 | <11 | 1,780 | 82.9 (76.1–89.2) | yes |

### 3f. Exploratory adjusted model

One GEE among the 27,826 note-positive admissions, outcome code-positive, binomial link, exchangeable working correlation, clustered on subject; covariates fixed before fitting; **diagnosis count and laboratory availability deliberately not adjusted for, because they are the proposed mechanism**. Labelled exploratory: these are associations in the computable data, not estimates of adjudicated under-coding by group. Selected adjusted odds ratios (full table in `docs/aim1c_level1.md`): HISPANIC/LATINO – PUERTO RICAN 1.603 (1.308–1.964); HISPANIC/LATINO – GUATEMALAN 2.039 (1.276–3.257); HISPANIC/LATINO – SALVADORAN 2.081 (1.192–3.633); Private vs Medicare 1.351 (1.206–1.515); surgical same-day admission vs emergency 2.906 (2.561–3.298); elective admission 1.768 (1.397–2.238); ICD-10-only era 1.403 (1.279–1.540); discharge-summary note source 16.748 (14.649–19.147).

**Level 2 of the equity audit — weighted positive predictive value by stratum against the gold standard — is `[PENDING ADJUDICATION]`. Level 3 — model calibration by stratum — now exists for the structured arm (Table 4b-v: 414 stratum rows, 225 estimable, 34 flagged) and is `[PENDING — the notes and fusion arms have no per-stratum metrics]`.**

---

## Table 4. Model performance

> **Caption text that must travel with every row of this table:** *Silver label — known error; not adjudicated truth. Rows for the notes arm additionally carry a circularity caveat: the label is a lexical rule applied to the same text the model reads, so these are development diagnostics, not accuracy estimates. Final performance requires the gold standard.*

Subsample for the notes arm: DEV 23,816 / TEST 6,164 / GOLD_HOLDOUT 2,865 (scored, never fitted).

### 4a. Notes arm — TF-IDF development diagnostic, TEST

Source: `docs/run_2026-09-19/results/aim1b_notes_tfidf.json`; rendered in `docs/aim1b_notes.md`. n = 6,164, 383 positive. Word 1–2-grams, min df 100, sublinear tf, L2 logistic regression (C = 1), vocabulary fit inside training folds only.

| Text variant | Imbalance variant | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | Calib. intercept | Calib. slope |
| --- | --- | --- | --- | --- | --: | --: |
| U unmasked | unweighted | 0.896 (0.862–0.937) | 0.596 (0.518–0.674) | 0.038 (0.031–0.045) | −0.144 | 1.444 |
| U unmasked | weighted | 0.909 (0.877–0.948) | 0.646 (0.572–0.720) | 0.063 (0.056–0.072) | −1.834 | 1.310 |
| U unmasked | weighted + prior correction | 0.909 (0.877–0.948) | 0.646 (0.572–0.720) | 0.038 (0.031–0.046) | 0.720 | 1.310 |
| M masked | unweighted | 0.912 (0.887–0.940) | 0.616 (0.538–0.691) | 0.037 (0.031–0.044) | −0.137 | 1.536 |
| M masked | weighted | 0.930 (0.908–0.953) | 0.671 (0.603–0.742) | 0.061 (0.054–0.069) | −1.821 | 1.423 |
| M masked | weighted + prior correction | 0.930 (0.908–0.953) | 0.671 (0.603–0.742) | 0.038 (0.030–0.045) | 0.732 | 1.423 |
| S sentence-deleted | unweighted | 0.826 (0.788–0.869) | 0.407 (0.326–0.488) | 0.047 (0.039–0.055) | −0.180 | 1.126 |
| S sentence-deleted | weighted | 0.829 (0.794–0.870) | 0.422 (0.346–0.503) | 0.096 (0.086–0.108) | −2.059 | 0.950 |
| S sentence-deleted | weighted + prior correction | 0.829 (0.794–0.870) | 0.422 (0.346–0.503) | 0.046 (0.038–0.055) | 0.494 | 0.950 |

Within code-negative TEST admissions only (n = 6,057, 286 positive), unweighted: U AUROC 0.907 / AUPRC 0.557; M 0.916 / 0.565; S 0.833 / 0.352.

Top positive coefficients, variant U: `steatosis` 11.739 (df 917), `fatty` 11.453 (df 1,709), `fatty liver` 9.427 (df 496), `hepatic steatosis` 9.087 (df 658), `nash` 5.901 (df 237) — **this row is the demonstration of circularity, not a finding.** Variant M: `mask` 22.772 (df 2,599) — masking every lexicon match still leaves the presence of a match as a feature. Variant S: `cirrhosis` 4.112, `liver disease` 4.018, `forms of` 3.728, `fibrosis` 3.625, `obesity` 1.717 — what the rest of the documentation carries, and the only row of this table that speaks to what a notes model could legitimately learn.

### 4b. Structured arm — silver label, TEST

Source: `docs/run_2026-09-19/results/aim1b_structured.json`, rendered in `docs/aim1b_structured.md`. TEST n = 75,124, 5,426 silver-positive. 95% intervals are 500-replicate subject-cluster bootstraps. FS-A = 94 features (clinical + availability), FS-B = 52 clinical, FS-AVAIL = 42 availability/volume.

| Learner | Feature set | Imbalance variant | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | Calib. intercept | Calib. slope |
| --- | --- | --- | --- | --- | --- | --: | --: |
| CatBoost | FS-A | unweighted | 0.857 (0.849–0.866) | 0.380 (0.358–0.401) | 0.0543 (0.0519–0.0569) | 0.031 | 1.018 |
| CatBoost | FS-A | weighted | 0.857 (0.849–0.865) | 0.371 (0.350–0.391) | 0.1451 (0.1423–0.1482) | −2.378 | 1.055 |
| CatBoost | FS-A | weighted + prior correction | 0.857 (0.849–0.865) | 0.371 (0.350–0.391) | 0.0550 (0.0526–0.0578) | 0.175 | 1.055 |
| CatBoost | FS-B | unweighted | 0.787 (0.778–0.796) | 0.282 (0.263–0.299) | 0.0593 (0.0566–0.0624) | 0.027 | 0.980 |
| CatBoost | FS-B | weighted | 0.786 (0.777–0.796) | 0.277 (0.258–0.295) | 0.1739 (0.1714–0.1765) | −2.425 | 1.042 |
| CatBoost | FS-B | weighted + prior correction | 0.786 (0.777–0.796) | 0.277 (0.258–0.295) | 0.0597 (0.0571–0.0629) | 0.141 | 1.042 |
| CatBoost | FS-AVAIL | unweighted | 0.812 (0.803–0.820) | 0.245 (0.230–0.261) | 0.0598 (0.0574–0.0627) | 0.013 | 1.035 |
| CatBoost | FS-AVAIL | weighted | 0.811 (0.802–0.819) | 0.239 (0.224–0.255) | 0.1774 (0.1745–0.1805) | −2.496 | 1.017 |
| CatBoost | FS-AVAIL | weighted + prior correction | 0.811 (0.802–0.819) | 0.239 (0.224–0.255) | 0.0600 (0.0576–0.0629) | 0.063 | 1.017 |
| XGBoost | FS-A | unweighted | 0.858 (0.850–0.866) | 0.378 (0.358–0.398) | 0.0543 (0.0519–0.0570) | 0.044 | 0.979 |
| XGBoost | FS-A | weighted | 0.841 (0.832–0.850) | 0.360 (0.340–0.378) | 0.0886 (0.0862–0.0912) | −1.607 | 0.790 |
| XGBoost | FS-A | weighted + prior correction | 0.841 (0.832–0.850) | 0.360 (0.340–0.378) | 0.0580 (0.0550–0.0613) | 0.945 | 0.790 |
| XGBoost | FS-B | unweighted | 0.787 (0.778–0.797) | 0.287 (0.267–0.305) | 0.0592 (0.0564–0.0623) | 0.047 | 0.958 |
| XGBoost | FS-B | weighted | 0.762 (0.751–0.774) | 0.266 (0.248–0.283) | 0.1056 (0.1032–0.1081) | −1.714 | 0.736 |
| XGBoost | FS-B | weighted + prior correction | 0.762 (0.751–0.774) | 0.266 (0.248–0.283) | 0.0619 (0.0588–0.0654) | 0.853 | 0.736 |
| LightGBM | FS-A | unweighted | 0.857 (0.849–0.865) | 0.374 (0.352–0.396) | 0.0544 (0.0521–0.0571) | 0.040 | 0.978 |
| LightGBM | FS-A | weighted | 0.831 (0.823–0.841) | 0.267 (0.250–0.286) | 0.0634 (0.0610–0.0661) | −0.598 | 3.038 |
| LightGBM | FS-A | weighted + prior correction | 0.831 (0.823–0.841) | 0.267 (0.250–0.286) | 0.0699 (0.0665–0.0739) | 1.969 | 3.038 |
| LightGBM | FS-B | unweighted | 0.788 (0.778–0.797) | 0.286 (0.267–0.303) | 0.0592 (0.0564–0.0623) | 0.031 | 0.969 |
| LightGBM | FS-B | weighted | 0.738 (0.729–0.748) | 0.180 (0.167–0.192) | 0.0657 (0.0631–0.0689) | −0.419 | 3.478 |
| LightGBM | FS-B | weighted + prior correction | 0.738 (0.729–0.748) | 0.180 (0.167–0.192) | 0.0707 (0.0673–0.0748) | 2.148 | 3.478 |

DEV out-of-fold values for every row are in the results JSON (field `oof`) and agree with TEST to within about 0.01 AUROC throughout.

**Selected hyperparameters** (four random configurations per learner, best by mean DEV out-of-fold AUPRC on FS-A unweighted; the four configurations spanned 0.373–0.387, so the choice is not consequential): CatBoost lr 0.05, depth 8, L2 10 (0.387); XGBoost lr 0.05, depth 8, L2 5, min child weight 10 (0.383); LightGBM lr 0.08, depth 6, L2 10, min child weight 5 (0.384). Runtime 3,953 s.

#### 4b-i. Within code-negative TEST admissions only (n = 74,109, 4,555 positive)

| Learner · feature set | AUROC | AUPRC |
| --- | --: | --: |
| CatBoost · FS-A, unweighted | 0.857 | 0.323 |
| CatBoost · FS-B, unweighted | 0.777 | 0.228 |
| CatBoost · FS-AVAIL, unweighted | 0.817 | 0.213 |
| XGBoost · FS-A, unweighted | 0.857 | 0.318 |
| XGBoost · FS-B, unweighted | 0.777 | 0.230 |
| LightGBM · FS-A, unweighted | 0.857 | 0.315 |
| LightGBM · FS-B, unweighted | 0.778 | 0.230 |

#### 4b-ii. SHAP attribution (CatBoost unweighted; mean absolute SHAP on a 20,000-admission TEST subsample)

| Rank | FS-A feature | mean \|SHAP\| | class | | FS-B feature | mean \|SHAP\| |
| --: | --- | --: | --- | --- | --- | --: |
| 1 | liver_imaging_any_pre | 0.675 | availability | | age | 0.356 |
| 2 | age | 0.336 | clinical | | omr_BMI | 0.180 |
| 3 | omr_BMI | 0.225 | clinical | | cmrf_overweight | 0.159 |
| 4 | liver_imaging_out_pre365 | 0.206 | availability | | icd_era | 0.157 |
| 5 | cmrf_overweight | 0.197 | clinical | | first_val_ALT | 0.124 |

Availability share of the top 25 features: **FS-A 0.28**, FS-B 0.00 (by construction). `n_diagnoses` ranks fifteenth under FS-A (0.062). **Reading for the manuscript:** the single dominant attribution under FS-A is an availability feature and FS-AVAIL alone out-discriminates the full clinical set on AUROC (0.812 vs 0.787), but availability features do **not** dominate the attribution *ranking*, so the pre-committed expectation (H1b-i) is only partly supported and must be reported as partly supported.

#### 4b-iii. Operating points at the DEV out-of-fold maximum-F1 threshold (descriptive; no threshold is proposed for use)

| Model | Threshold | DEV OOF F1 | TEST sensitivity | TEST specificity | TEST PPV |
| --- | --: | --: | --: | --: | --: |
| CatBoost · FS-A · unweighted | 0.208 | 0.408 | 0.479 | 0.936 | 0.368 |
| CatBoost · FS-A · weighted | 0.743 | 0.402 | 0.489 | 0.931 | 0.355 |
| CatBoost · FS-A · weighted + corrected | 0.183 | 0.402 | 0.492 | 0.930 | 0.353 |
| CatBoost · FS-B · unweighted | 0.156 | 0.340 | 0.408 | 0.918 | 0.279 |
| CatBoost · FS-B · weighted | 0.695 | 0.337 | 0.389 | 0.922 | 0.280 |
| CatBoost · FS-B · weighted + corrected | 0.149 | 0.337 | 0.389 | 0.922 | 0.280 |

#### 4b-iv. Secondary population: imaging-observed admissions (pre-specified amendment (e))

DEV 109,220 (17,559 positive); TEST 27,602 (4,493 positive). CatBoost only.

| Feature set | Imbalance variant | AUROC (95% CI) | AUPRC (95% CI) | Calib. intercept | Calib. slope |
| --- | --- | --- | --- | --: | --: |
| FS-A | unweighted | 0.766 (0.754–0.778) | 0.426 (0.403–0.453) | 0.030 | 1.039 |
| FS-A | weighted | 0.765 (0.753–0.777) | 0.421 (0.397–0.447) | −1.505 | 1.068 |
| FS-A | weighted + prior correction | 0.765 (0.753–0.777) | 0.421 (0.397–0.447) | 0.138 | 1.068 |
| FS-B | unweighted | 0.750 (0.738–0.763) | 0.402 (0.378–0.427) | 0.028 | 0.997 |
| FS-B | weighted | 0.750 (0.737–0.762) | 0.397 (0.372–0.420) | −1.536 | 1.063 |
| FS-B | weighted + prior correction | 0.750 (0.737–0.762) | 0.397 (0.372–0.420) | 0.121 | 1.063 |

The FS-A advantage over FS-B collapses from 0.070 AUROC in the full population to 0.016 here, which is the comparison the manuscript should foreground when discussing what the availability features are actually carrying.

#### 4b-v. Subgroup performance

Computed per race, insurance, language, sex and age-band stratum for all nine CatBoost rows, with a metric reported only where a stratum has at least 50 positives and at least 50 negatives, strata below that floor recorded as "not estimable" rather than merged, and a per-stratum `material_calibration_difference` flag (analyst threshold: calibration intercept differing from the overall model by more than 0.5, or slope by more than 0.25). **414 stratum rows; 225 estimable; 34 flagged.** Among the unweighted models the substantive flags are a slope of 0.48–0.77 for BLACK/CAPE VERDEAN and an intercept of +0.55 to +0.58 for HISPANIC OR LATINO, with AUROC broadly similar across strata. Full tables: `docs/run_2026-09-19/results/aim1b_structured.json`, field `subgroups`, rendered in `docs/aim1b_structured.md` §"Subgroups".

### 4c. Embedding-based notes arm

Source: `docs/run_2026-09-19/results/aim1b_notes_arm.json`. Frozen Bio_ClinicalBERT, 512-token chunks, stride 64, ≤ 12 chunks, mean+max pooled to 1,536 dimensions; heads = L2 logistic regression and LightGBM, the better on DEV out-of-fold AUPRC kept; notes-augmented model = CatBoost on FS-B plus the first 64 principal components (PCA fit inside training folds). Pilot throughput that sized the subsample: 0.539 s per admission on CPU, 5,694 tokens/s, 33,414-admission budget ceiling (`embed_pilot.json`). Runtime of the arm itself 301 s.

**Encoder coverage — read this before the table.** Encoding stopped at its compute budget with **28 of 33 shards**: **27,845 of 32,845 subsampled admissions (84.8%)**, namely DEV 19,872, TEST 5,108 and **all 2,865 GOLD_HOLDOUT admissions (100%)**. DEV/TEST shards 24–28 were never encoded, and the gold shards (29–32) were deliberately encoded first. Only variant S was encoded; variant U has no embeddings. Every row below therefore rests on 85% of the intended subsample, and its n differs from Table 4a's.

| Head on the 1,536-dim vectors (variant S) | DEV OOF AUROC | DEV OOF AUPRC | TEST AUROC (95% CI) | TEST AUPRC (95% CI) | Brier (95% CI) | Calib. intercept | Calib. slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| L2 logistic regression | 0.785 | 0.251 | 0.754 (0.704–0.799) | 0.216 (0.165–0.292) | 0.058 (0.050–0.068) | −0.254 | 0.511 |
| LightGBM (**kept**) | 0.804 | 0.274 | 0.788 (0.742–0.832) | 0.246 (0.187–0.326) | 0.055 (0.046–0.065) | 0.804 | 0.589 |

DEV 19,872 with 1,438 silver-positive; TEST 5,108 with 322. Within code-negative TEST admissions only (n = 5,016, 239 positive): logistic regression AUROC 0.760 / AUPRC 0.171; LightGBM 0.794 / 0.179.

**The transformer embeddings lost to TF-IDF on the selection criterion itself.** The kept LightGBM head reached DEV out-of-fold AUPRC **0.274** against TF-IDF variant S's **0.444** (Table 4a's source JSON, field `oof`), and TEST 0.788 / 0.246 against 0.826 / 0.407. Two reasons are stated in the run record and neither is offered as a defence: the embeddings cover 85% of the subsample where the TF-IDF model covers all of it, and a frozen general-purpose clinical encoder with a light head is a weaker use of 1,536 dimensions than a vocabulary fitted to this corpus. Fine-tuning was budgeted at zero hours and not attempted. **Consequence for the fusion stack:** Layer 0's notes model was chosen as TF-IDF by the pre-stated DEV out-of-fold rule, not by hand (Table 4d).

#### 4c-i. Notes-augmented model — CatBoost on FS-B + 64 embedding components

DEV 19,872 (1,438 positive), TEST 5,108 (322 positive).

| Imbalance variant | DEV OOF AUROC | DEV OOF AUPRC | TEST AUROC (95% CI) | TEST AUPRC (95% CI) | Brier (95% CI) | Calib. intercept | Calib. slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| unweighted | 0.840 | 0.305 | 0.829 (0.795–0.863) | 0.328 (0.246–0.436) | 0.050 (0.042–0.059) | −0.036 | 1.010 |
| weighted | 0.835 | 0.298 | 0.813 (0.776–0.848) | 0.255 (0.182–0.366) | 0.143 (0.132–0.154) | −2.373 | 0.989 |
| weighted + prior correction | 0.835 | 0.298 | 0.813 (0.776–0.848) | 0.255 (0.182–0.366) | 0.053 (0.044–0.062) | 0.178 | 0.989 |

Within code-negative TEST admissions only (n = 5,016, 239 positive), unweighted: AUROC 0.826 / AUPRC 0.245. The weighting-and-correction pattern reproduces the structured arm's exactly: weighting drives the intercept to −2.373 at an unchanged AUROC, and the analytic prior correction returns it to +0.178.

### 4d. Stacked fusion

Source: `docs/run_2026-09-19/results/aim1b_fusion.json`, rendered in `docs/aim1b_fusion.md`. Layer 0 = structured FS-B (best-calibrated DEV out-of-fold variant, selected as `cat\|FS-B\|unweighted`; FS-A sensitivity input `cat\|FS-A\|unweighted`) + notes model variant S (selected as `tfidf\|S\|unweighted`, the better of TF-IDF and the embedding head on DEV out-of-fold AUPRC). Layer 1 = logistic regression on the two out-of-fold logits, fitted on subsample DEV only. **Code status is never an input to any layer.** Fitted Layer-1 coefficients: primary intercept 1.235, structured logit 0.519, notes logit 0.993; FS-A sensitivity intercept 0.760, structured 0.533, notes 0.793.

All arms are scored on the same subsample TEST admissions, n = 6,164 with 383 silver-positive, **except** the notes-augmented rows, which are scored on the 5,108 of those admissions that have embeddings (322 positive) and are therefore not strictly comparable with the rest of the column.

| Arm | n | positives | AUROC | AUPRC | Brier | Calib. intercept | Calib. slope | Code-negative AUROC | Code-negative AUPRC |
| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| **fusion (primary): FS-B + notes** | 6,164 | 383 | **0.853** | **0.435** | 0.046 | −0.207 | 0.934 | **0.847** | 0.353 |
| structured (primary): `cat\|FS-B\|unweighted` | 6,164 | 383 | 0.793 | 0.291 | 0.051 | −0.139 | 1.013 | 0.763 | 0.188 |
| fusion (sensitivity): FS-A + notes | 6,164 | 383 | 0.860 | 0.464 | 0.044 | −0.217 | 0.961 | 0.858 | 0.384 |
| structured (sensitivity): `cat\|FS-A\|unweighted` | 6,164 | 383 | 0.854 | 0.392 | 0.047 | −0.167 | 1.021 | 0.842 | 0.276 |
| notes: `tfidf\|S\|unweighted` | 6,164 | 383 | 0.826 | 0.407 | 0.047 | −0.180 | 1.126 | 0.833 | 0.352 |
| notes-augmented: `aug\|FS-B+notes\|unweighted` | 5,108 | 322 | 0.829 | 0.328 | 0.050 | −0.036 | 1.010 | 0.826 | 0.245 |
| notes-augmented: `aug\|FS-B+notes\|weighted` | 5,108 | 322 | 0.813 | 0.255 | 0.143 | −2.373 | 0.989 | 0.814 | 0.186 |
| notes-augmented: `aug\|FS-B+notes\|weighted+corrected` | 5,108 | 322 | 0.813 | 0.255 | 0.053 | 0.178 | 0.989 | 0.814 | 0.186 |

#### 4d-i. Paired differences against the primary structured arm (subject-cluster bootstrap, 500 replicates)

| Comparison | ΔAUROC (95% CI) | ΔAUPRC (95% CI) | ΔBrier (95% CI) |
| --- | --- | --- | --- |
| fusion (primary) − structured (primary) | **+0.060 (+0.031, +0.089)** | +0.147 (+0.074, +0.223) | −0.006 (−0.009, −0.002) |
| fusion (sensitivity FS-A) − structured (primary) | +0.067 (+0.034, +0.100) | +0.176 (+0.100, +0.254) | −0.007 (−0.010, −0.004) |
| structured (sensitivity FS-A) − structured (primary) | +0.061 (+0.037, +0.086) | +0.100 (+0.068, +0.136) | −0.004 (−0.006, −0.003) |
| notes − structured (primary) | +0.033 (−0.018, +0.080) | +0.121 (+0.019, +0.221) | −0.005 (−0.008, −0.001) |
| notes-augmented (unweighted) − structured (primary) | +0.036 (+0.003, +0.068) | +0.042 (−0.021, +0.103) | −0.001 (−0.004, +0.002) |
| notes-augmented (weighted) − structured (primary) | +0.021 (−0.016, +0.055) | −0.029 (−0.091, +0.034) | +0.091 (+0.079, +0.104) |
| notes-augmented (weighted + corrected) − structured (primary) | +0.021 (−0.016, +0.055) | −0.029 (−0.091, +0.034) | +0.001 (−0.002, +0.005) |

**Every row involving the notes model inherits the circularity caveat**: its silver-label advantage is partly the label's own lexicon. The paired differences are silver-label observations; the gold harness (`scripts/aim1b_evaluate_gold.py`) is what tests H1b-iii properly.

### 4e. Locked gold-holdout predictions (audit trail)

Source: `docs/run_2026-09-19/results/locked_predictions.json`, rendered in `docs/aim1b_locked_predictions.md`. **This is not a performance table.** It is the audit trail establishing that every prediction on the gold holdout predates the reference standard.

| Item | Value |
| --- | --- |
| Prediction file (untracked credentialed derivative) | `data/processed/gold_holdout_predictions_v1.parquet` |
| Rows (GOLD_HOLDOUT admissions scored) | 2,865 |
| Arm/variant columns | 37 |
| Written (UTC) | 2026-09-19T21:49:43Z |
| SHA-256 of the prediction file | `0b3d9a4d256568534772adef66435986b3fda96238cf146b9593f721601e7aca` |
| Fitted model files hashed (SHA-256 + byte size each) | 16 |
| Per-arm gold prediction files hashed | 3 (`structured_gold.parquet`, `notes_tfidf_gold.parquet`, `notes_arm_gold.parquet`) |
| Model files excluded from the manifest, by name | 2 (`aug_FS-B_notes_unweighted_SMOKE.cbm`, `aug_FS-B_notes_weighted_SMOKE.cbm`) |

The 37 columns are the three gradient-boosted learners × feature sets × imbalance variants as fitted (21), the three TF-IDF text variants × three imbalance variants (9), the two embedding heads (2), the three notes-augmented variants (3), and the two fusion arms (2). **No adjudicated label existed when the file was written.**

The two excluded files were written by a partial-data smoke test of the notes-arm code path before its output location was corrected. They were not deleted — the run's deletion guardrail permits deletion only in two named locations — so the locking script excludes any `_SMOKE` file from the manifest and records it under `excluded_from_manifest`, and the manifest describes exactly the models that produced the locked predictions and nothing else. The smoke numbers are not results and appear in no tracked document. The full 16-row hash table is in `docs/aim1b_locked_predictions.md` and is not reproduced here.

### 4f. Model performance against the gold standard

**Entirely `[PENDING ADJUDICATION]`.** This is the only part of Table 4 that is an accuracy estimate. It will report, for each arm, discrimination and calibration against adjudicated labels on the gold holdout, with the drop from the silver-label counterpart reported explicitly as a measure of silver-label error, and with the recovery-zone contrast (notes-augmented versus structured baseline within code−/note+ charts) as the pre-committed test of H1b-ii.

---

## Table 4g. Hypothesis outcomes as the evidence now stands

> **Vocabulary.** "Partly supported", "not supported" and "consistent with" are used throughout. Nothing here is described as confirmed, and nothing that depends on adjudicated labels is described at all. The hypotheses were committed at `e2a4e1e5b2bade9f7f8cb07a7d546a23e57b1b9b` before any model was trained; that is a repository audit trail and **not** a public registration.

| Hypothesis | Outcome | What the evidence is |
| --- | --- | --- |
| **H1a** (adjudicated under-capture; the headline) | `[PENDING ADJUDICATION]` | Requires the 400 chart reviews. No computable-stage share substitutes for it. |
| **H1b-i** (structured discrimination; availability features dominate the attributions) | **partly supported** | The feature-set gap is large and in the predicted direction (TEST AUROC 0.857 FS-A vs 0.787 FS-B; AUPRC 0.380 vs 0.282), and FS-AVAIL alone reaches 0.812 AUROC — availability and volume information by itself out-discriminates the whole clinical feature set. But the attribution *ranking* is not dominated by availability: one availability feature leads (`liver_imaging_any_pre`, mean \|SHAP\| 0.675, roughly double the next), while availability features are 28% of the FS-A top 25, and the two the hypothesis named specifically — laboratory availability and diagnosis count — are not near the top (`n_diagnoses` fifteenth at 0.062). The dominant feature is *imaging* availability. See Tables 4b, 4b-ii. |
| **H1b-ii** (notes-augmented arm beats the structured baseline in the recovery zone, **against the gold standard**) | `[PENDING ADJUDICATION]` | The gold-standard test does not exist. A **silver-label shadow** of it may be reported, explicitly labelled as not the test: within code-negative TEST admissions the fusion arm reaches AUROC **0.847** against the structured FS-B arm's **0.763**, and the notes-augmented arm reaches 0.826 (Table 4d). This is a development diagnostic on a label the notes arm partly relearned; it is not evidence about H1b-ii and must never be presented as such. |
| **H1b-iii** (fusion at least as discriminating as the better base learner **and** better calibrated than either) | **partly supported — and both halves must be stated** | *Discrimination:* fusion is more discriminating than either base learner, +0.060 AUROC over the structured FS-B arm (95% CI +0.031 to +0.089), and +0.147 AUPRC (+0.074 to +0.223). *Calibration:* fusion is **not** better calibrated than that arm — slope **0.934** against **1.013**, intercept −0.207 against −0.139. The second half of the hypothesis is therefore not supported. The hypothesis's own caveat also applies: against the **FS-A** structured arm, fusion adds **+0.006 AUROC** (0.860 vs 0.854), which is almost nothing. See Tables 4d, 4d-i. |
| **H-calibration**, as recorded 7 September (weighting plus threshold tuning gives slope near 1 and intercept near 0) | **not supported** | Class weighting leaves the slope near 1 but drives the calibration intercept far from 0: CatBoost weighted intercepts −2.378 (FS-A), −2.425 (FS-B), −2.496 (FS-AVAIL), and −2.373 for the notes-augmented model. LightGBM weighting additionally distorts the slope (3.038 FS-A, 3.478 FS-B) and loses AUPRC. |
| **H-calibration**, amendment (b)'s competing expectation (weighting inflates predicted risk; the analytic prior correction repairs it without touching discrimination) | **supported** | The −log(w) logit shift returns the CatBoost intercepts to 0.175 / 0.141 / 0.063 and the notes-augmented intercept to 0.178, with AUROC and AUPRC unchanged to three decimals, as a monotone transform must. Unweighted models were already well calibrated (CatBoost FS-A intercept 0.031, slope 1.018). |
| **H-calibration**, secondary (calibration differs by subgroup even where AUROC does not) | **consistent with** | 34 of 414 subgroup rows are flagged for a material calibration difference (225 estimable); among unweighted models, slope 0.48–0.77 for BLACK/CAPE VERDEAN and intercept +0.55 to +0.58 for HISPANIC OR LATINO, with AUROC broadly similar. Table 4b-v. |
| **H-silver-vs-gold** (every gold-standard estimate is lower than its silver-label counterpart; the drop measures silver-label error) | **entirely `[PENDING ADJUDICATION]`** | Nothing in this study bears on it. Both sides of every comparison it names require the adjudication; the silver-label side alone says nothing about the size of the drop. |
| **H1c** (coding rate among note-positive admissions differs across strata) | **consistent with, at the computable stage only** | Recovery shares range from roughly 61% to 96% across analyzable strata, with 33 of 33 race levels analyzable and 21 claim-supported, and the direction is not a uniform disadvantage gradient (Table 3). The accuracy half of the hypothesis — weighted PPV by stratum — is `[PENDING ADJUDICATION]`; the calibration half now exists for the structured arm only (Table 4b-v) and `[PENDING — the notes and fusion arms have no per-stratum metrics]`. |

**The computable recovery share remains a comparison of two computable phenotypes and is never the headline.** Nothing in this table changes that.

---

## Table 5. Adjudicated under-capture estimate (the headline)

**Entirely `[PENDING ADJUDICATION]`.** Nothing in this table can be filled before the 400 charts are reviewed, and no computable-stage number may be substituted for any cell of it.

Estimator (`scripts/aim1a_estimator.py`): under-capture = (w_B x_B + w_D x_D) ÷ (w_A x_A + w_B x_B + w_C x_C + w_D x_D), with x_c the adjudicated positives in cell c and w_c = N_pop(c) ÷ n_sample(c).

### 5a. Sampling frame, allocation and weights (fixed at sampling time; these are known)

Source: `docs/run_2026-09-19/results/integrity_gate.json`.

| Cell | Population N | Charts sampled | Weight = N_pop ÷ n_sample |
| --- | --: | --: | --: |
| A code+/note+ | 5,027 | 80 | 62.8375 |
| B code−/note+ (recovery zone) | 22,799 | 150 | 151.9933 |
| C code+/note− | 713 | 70 | 10.1857 |
| D code−/note− | 345,453 | 100 | 3454.53 |
| **Total** | **373,992** | **400** | — |

Double review: 100 charts (25%), flagged only in the untracked master key. Reviewer 1: 250 charts (A 48 / B 96 / C 40 / D 66); reviewer 2: 250 charts (A 47 / B 97 / C 40 / D 66); 500 adjudications in total, plus a 20-chart calibration round adjudicated by both.

### 5b. Adjudication outcome by cell

| Cell | Charts | Definite | Probable | Possible | Absent | Insufficient | Adjudicated positive (Definite+Probable) |
| --- | --: | --: | --: | --: | --: | --: | --: |
| A code+/note+ | 80 | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |
| B code−/note+ | 150 | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |
| C code+/note− | 70 | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |
| D code−/note− | 100 | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |

Cells below 11 will be written `<11`.

### 5c. Headline and companion estimates

| Quantity | Estimate (%) | 95% CI (stratified bootstrap, 500 reps) | 95% CI (linearized, logit scale) |
| --- | --- | --- | --- |
| **Under-capture: population-weighted share of adjudicated-positive admissions that are code-negative** | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |
| Note-rule positive predictive value (cells A and B) | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |
| Note-rule sensitivity | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |
| ICD positive predictive value | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` | `[PENDING ADJUDICATION]` |

Reported twice, under both pre-specified handlings of *Insufficient information* (excluded, and counted negative); which is primary is `[PENDING researcher decision P6-01]`. A secondary version collapsing *Possible* into positive is available at no cost and is `[PENDING clinician decision D1]`.

**If x_D ≤ 1**, the interval must be accompanied by an explicit one-sided upper bound on the cell-D prevalence (rule of three: p_D < 3% with 95% confidence when x_D = 0, i.e. up to approximately 10,000 unobserved positives in that cell) rather than presented as a calibrated 95% interval. The design-stage simulation (`docs/aim1a_precision_forecast.md`) shows bootstrap coverage of 63–65% at 1 positive per 100 in cell D, approximately 85% at 2 and approximately 92% at 3 or more; one additional cell-D positive moves the estimate by 2–3 percentage points.

### 5d. Inter-rater agreement

| Statistic | Value | Source |
| --- | --- | --- |
| Cohen's kappa, binary collapsed outcome (100 double-reviewed charts) | `[PENDING ADJUDICATION]` | `scripts/aim1a_estimator.py` |
| Weighted kappa, 4 ordinal levels, linear weights | `[PENDING ADJUDICATION]` | idem |
| Weighted kappa, 4 ordinal levels, quadratic weights | `[PENDING ADJUDICATION]` | idem |
| Unweighted kappa, 4 ordinal levels | `[PENDING ADJUDICATION]` | idem |
| Disagreements requiring resolution | `[PENDING ADJUDICATION]` | idem |
| Median minutes per chart (measured) | `[PENDING ADJUDICATION]` | reviewer forms, `minutes_spent` |

Which weighting is reported as primary is `[PENDING researcher decision P6-03]`; how disagreements are resolved is `[PENDING clinician decision D8 / P6-02]`. *Insufficient information* is not an ordinal level and is dropped from the four-level kappa.

### 5e. Secondary adjudicated analyses

| Analysis | Status |
| --- | --- |
| Adjudicated cardiometabolic risk (question 6a) versus the computable five-criterion operationalization | `[PENDING ADJUDICATION]` |
| Adjudicated alcohol band (question 6b) versus the ICD-code proxy; expected to be dominated by "not documented" | `[PENDING ADJUDICATION]` |
| Other identifiable cause of steatosis (question 6c) — adjudication-only; no computable analog exists | `[PENDING ADJUDICATION]` |
| Temporality (during / before / both) among adjudicated positives | `[PENDING ADJUDICATION]` |
| Negation overrides invoked by reviewers | `[PENDING ADJUDICATION]` |
| Equity audit level 2: weighted PPV by stratum | `[PENDING ADJUDICATION]` |

---

## Provenance index

| Table | Primary source file |
| --- | --- |
| 1, 1b | `docs/run_2026-09-19/results/cohort_flow.json`, `phase2_splits.json` |
| 2, 2a–2c | `docs/run_2026-09-19/results/integrity_gate.json`, `loose_ends_43_44.json`, `sens_5719.json`, `docs/sld_subclassification.md`, `docs/aim1a_crosstab.md` |
| 2d | `docs/imaging_denominator.md` |
| 3 | `docs/run_2026-09-19/results/aim1c_level1.json` → `docs/aim1c_level1.md`, `docs/tables/aim1c_level1_*.md` |
| 4a | `docs/run_2026-09-19/results/aim1b_notes_tfidf.json` → `docs/aim1b_notes.md` |
| 4b | `docs/run_2026-09-19/results/aim1b_structured.json` → `docs/aim1b_structured.md` |
| 4c, 4c-i | `docs/run_2026-09-19/results/aim1b_notes_arm.json`, `notes_subsample.json`, `embed_pilot.json` |
| 4d, 4d-i | `docs/run_2026-09-19/results/aim1b_fusion.json` → `docs/aim1b_fusion.md` |
| 4e | `docs/run_2026-09-19/results/locked_predictions.json` → `docs/aim1b_locked_predictions.md` |
| 4f | **does not exist**: requires the chart adjudication |
| 4g | `aim1b_structured.json`, `aim1b_notes_arm.json`, `aim1b_fusion.json`, `aim1c_level1.json`, `docs/analysis_plan_prespecified.md` §1 |
| 5a | `docs/run_2026-09-19/results/integrity_gate.json`, `reviewer_assignment.json` |
| 5b–5e | **do not exist**: require the chart adjudication |
