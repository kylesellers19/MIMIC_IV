# Aim 1b — structured arm (run_2026-09-19, Phase 7)

Produced by `scripts/run0919_aim1b_structured.py` (features: `scripts/run0919_features.py`); every number is read from `docs/run_2026-09-19/results/aim1b_structured.json` and `feature_classification.json` by `scripts/run0919_aim1b_reports.py`. Organized by the TRIPOD+AI development items (Collins et al. 2024).

**Silver label — known error; not adjudicated truth; final performance requires the gold standard.**

## Source of data, participants, outcome

MIMIC-IV v3.1 with MIMIC-IV-Note; the locked, cleaned analysis population; subject-level splits with a gold holdout (`docs/aim1b_splits.md`): DEV 296,003 admissions, TEST 75,124, GOLD_HOLDOUT 2,865 (never fitted on). Outcome = silver label: note-positive under the frozen rule v1.1.0, primary definition (b). Prevalence DEV 7.18%, TEST 7.22%.

## Predictors and the leakage audit

Everything is time-bounded at discharge; no post-discharge information. Never a feature: the four phenotype codes or anything derived from them; the full Charlson index (contains K76.0/571.x — `docs/charlson_validation.md`); any output of the note rule; note counts or lengths outside the availability set. Each candidate feature was classified before training as *clinical* or *availability/volume-derived*.

| class | n | features |
| --- | --: | --- |
| clinical | 52 | age, gender, admission_type, admission_location, icd_era, los_days, admit_year, marital_status, first_val_ALT, first_val_AST, first_val_Platelets, first_val_Triglycerides, first_val_HDL, first_val_HbA1c, first_val_Glucose, first_val_Albumin, first_val_Bilirubin_total, first_val_Alkaline_phosphatase, last_val_ALT, last_val_AST, last_val_Platelets, last_val_Triglycerides, last_val_HDL, last_val_HbA1c, last_val_Glucose, last_val_Albumin, last_val_Bilirubin_total, last_val_Alkaline_phosphatase, pre365_HbA1c, pre365_Triglycerides, pre365_HDL, omr_BMI, omr_SBP, omr_DBP, cmrf_overweight, cmrf_dysglycemia, cmrf_hypertension, cmrf_hypertg, cmrf_lowhdl, insulin, metformin, oral_ad, bb, htn_qual, htn_excl, lipid, charlson_noliver, etio_alcohol, etio_viral, etio_cirrhosis, etio_hcc, etio_other |
| availability / volume | 42 | miss_lab_ALT, miss_lab_AST, miss_lab_Platelets, miss_lab_Triglycerides, miss_lab_HDL, miss_lab_HbA1c, miss_lab_Glucose, miss_lab_Albumin, miss_lab_Bilirubin_total, miss_lab_Alkaline_phosphatase, miss_omr_BMI, miss_omr_SBP, miss_omr_DBP, miss_insurance, miss_marital_status, miss_language, n_ALT, n_AST, n_Platelets, n_Triglycerides, n_HDL, n_HbA1c, n_Glucose, n_Albumin, n_Bilirubin_total, n_Alkaline_phosphatase, n_lab_results_total, n_analytes_available, n_diagnoses, n_rx_orders, n_rx_distinct, n_notes_dc, chars_dc, n_notes_rad_inp, chars_rad_inp, liver_imaging_inp, n_notes_rad_out_pre365, liver_imaging_out_pre365, liver_imaging_any_pre, has_BMI, has_SBP, has_DBP |

Excluded (reason): code_positive — phenotype code (label axis); race — equity stratum (kept for subgroup reporting, not a feature); insurance — equity stratum; language — equity stratum; lab_GGT — 0.9% coverage — excluded; miss_lab_GGT — excluded with GGT; hospital_expire_flag — post-discharge/outcome information; discharge_location — discharge-time disposition (borderline; excluded as outcome-like); dischtime — timestamp; admittime — timestamp; flag_* — cleaning flags; lab_* (clean-pop single values) — superseded by first/last in-admission values; charlson (full) — contains K76.0/571.x — leaks the code axis; note rule outputs — label source; double-review / cell — sampling design.

Feature sets: **FS-A** everything; **FS-B** clinical only; **FS-AVAIL** availability/volume only (how much of the label the documentation process alone predicts). Limitation stated: tree models split on missing values natively, so FS-B still sees the missingness pattern even without explicit indicators; FS-AVAIL bounds that.

## Model development

CatBoost (primary), XGBoost and LightGBM comparators; native missing-value handling; no imputation; no synthetic oversampling. Imbalance variants: unweighted; weighted (scale_pos_weight = negatives ÷ positives in the training fold); weighted+corrected (the weighted model's logit shifted by −log of the weight — the analytic prior correction). Tuning: 4 configurations per learner on FS-A (unweighted) by 3-fold subject-level CV within DEV with early stopping on an inner 10% subject split; the best configuration per learner (by OOF AUPRC) was reused for every feature set and variant (Tier 1). Then 5-fold subject-level OOF predictions on DEV; final models fit on all DEV; TEST touched once.

| learner | best configuration | tuning OOF AUPRC per configuration |
| --- | --- | --- |
| cat | {'lr': 0.05, 'depth': 8, 'l2': 10} | 0.3838, 0.3736, 0.3869, 0.3811 |
| xgb | {'lr': 0.05, 'depth': 8, 'l2': 5, 'mcw': 10} | 0.3798, 0.3730, 0.3834, 0.3810 |
| lgb | {'lr': 0.08, 'depth': 6, 'l2': 10, 'mcw': 5} | 0.3833, 0.3757, 0.3807, 0.3838 |

## Performance on DEV (out-of-fold) — for calibration comparison across imbalance variants

| model | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| cat|FS-A|unweighted | 296,003 | 21,239 | 0.859 | 0.383 | 0.054 | 0.011 | 1.019 |
| cat|FS-A|weighted | 296,003 | 21,239 | 0.858 | 0.371 | 0.145 | -2.384 | 1.062 |
| cat|FS-A|weighted+corrected | 296,003 | 21,239 | 0.858 | 0.371 | 0.055 | 0.176 | 1.062 |
| cat|FS-B|unweighted | 296,003 | 21,239 | 0.796 | 0.305 | 0.058 | 0.017 | 1.039 |
| cat|FS-B|weighted | 296,003 | 21,239 | 0.796 | 0.292 | 0.172 | -2.424 | 1.090 |
| cat|FS-B|weighted+corrected | 296,003 | 21,239 | 0.796 | 0.292 | 0.059 | 0.139 | 1.090 |
| cat|FS-AVAIL|unweighted | 296,003 | 21,239 | 0.810 | 0.238 | 0.060 | 0.001 | 1.017 |
| cat|FS-AVAIL|weighted | 296,003 | 21,239 | 0.809 | 0.235 | 0.179 | -2.509 | 1.025 |
| cat|FS-AVAIL|weighted+corrected | 296,003 | 21,239 | 0.809 | 0.235 | 0.060 | 0.054 | 1.025 |
| xgb|FS-A|unweighted | 296,003 | 21,239 | 0.860 | 0.382 | 0.054 | 0.022 | 0.997 |
| xgb|FS-A|weighted | 296,003 | 21,239 | 0.844 | 0.358 | 0.083 | -1.499 | 0.771 |
| xgb|FS-A|weighted+corrected | 296,003 | 21,239 | 0.844 | 0.358 | 0.058 | 1.060 | 0.771 |
| xgb|FS-B|unweighted | 296,003 | 21,239 | 0.798 | 0.303 | 0.058 | 0.019 | 1.016 |
| xgb|FS-B|weighted | 296,003 | 21,239 | 0.768 | 0.276 | 0.098 | -1.622 | 0.746 |
| xgb|FS-B|weighted+corrected | 296,003 | 21,239 | 0.768 | 0.276 | 0.061 | 0.935 | 0.745 |
| lgb|FS-A|unweighted | 296,003 | 21,239 | 0.859 | 0.382 | 0.054 | 0.015 | 0.990 |
| lgb|FS-A|weighted | 296,003 | 21,239 | 0.811 | 0.215 | 0.063 | -0.428 | 3.014 |
| lgb|FS-A|weighted+corrected | 296,003 | 21,239 | 0.811 | 0.215 | 0.070 | 2.135 | 3.049 |
| lgb|FS-B|unweighted | 296,003 | 21,239 | 0.797 | 0.302 | 0.058 | 0.021 | 0.995 |
| lgb|FS-B|weighted | 296,003 | 21,239 | 0.744 | 0.178 | 0.065 | -0.428 | 3.529 |
| lgb|FS-B|weighted+corrected | 296,003 | 21,239 | 0.744 | 0.177 | 0.070 | 2.129 | 3.523 |

## Performance on TEST (touched once; subject-cluster bootstrap CIs, 500 replicates)

**Silver label — known error; not adjudicated truth; final performance requires the gold standard.**

| model | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| cat|FS-A|unweighted | 75,124 | 5,426 | 0.857 (0.849–0.866) | 0.380 (0.358–0.401) | 0.054 (0.052–0.057) | 0.031 | 1.018 |
| cat|FS-A|weighted | 75,124 | 5,426 | 0.857 (0.849–0.865) | 0.371 (0.350–0.391) | 0.145 (0.142–0.148) | -2.378 | 1.055 |
| cat|FS-A|weighted+corrected | 75,124 | 5,426 | 0.857 (0.849–0.865) | 0.371 (0.350–0.391) | 0.055 (0.053–0.058) | 0.175 | 1.055 |
| cat|FS-B|unweighted | 75,124 | 5,426 | 0.787 (0.778–0.796) | 0.282 (0.263–0.299) | 0.059 (0.057–0.062) | 0.027 | 0.980 |
| cat|FS-B|weighted | 75,124 | 5,426 | 0.786 (0.777–0.796) | 0.277 (0.258–0.295) | 0.174 (0.171–0.176) | -2.425 | 1.042 |
| cat|FS-B|weighted+corrected | 75,124 | 5,426 | 0.786 (0.777–0.796) | 0.277 (0.258–0.295) | 0.060 (0.057–0.063) | 0.141 | 1.042 |
| cat|FS-AVAIL|unweighted | 75,124 | 5,426 | 0.812 (0.803–0.820) | 0.245 (0.230–0.261) | 0.060 (0.057–0.063) | 0.013 | 1.035 |
| cat|FS-AVAIL|weighted | 75,124 | 5,426 | 0.811 (0.802–0.819) | 0.239 (0.224–0.255) | 0.177 (0.174–0.181) | -2.496 | 1.017 |
| cat|FS-AVAIL|weighted+corrected | 75,124 | 5,426 | 0.811 (0.802–0.819) | 0.239 (0.224–0.255) | 0.060 (0.058–0.063) | 0.063 | 1.017 |
| xgb|FS-A|unweighted | 75,124 | 5,426 | 0.858 (0.850–0.866) | 0.378 (0.358–0.398) | 0.054 (0.052–0.057) | 0.044 | 0.979 |
| xgb|FS-A|weighted | 75,124 | 5,426 | 0.841 (0.832–0.850) | 0.360 (0.340–0.378) | 0.089 (0.086–0.091) | -1.607 | 0.790 |
| xgb|FS-A|weighted+corrected | 75,124 | 5,426 | 0.841 (0.832–0.850) | 0.360 (0.340–0.378) | 0.058 (0.055–0.061) | 0.945 | 0.790 |
| xgb|FS-B|unweighted | 75,124 | 5,426 | 0.787 (0.778–0.797) | 0.287 (0.267–0.305) | 0.059 (0.056–0.062) | 0.047 | 0.958 |
| xgb|FS-B|weighted | 75,124 | 5,426 | 0.762 (0.751–0.774) | 0.266 (0.248–0.283) | 0.106 (0.103–0.108) | -1.714 | 0.736 |
| xgb|FS-B|weighted+corrected | 75,124 | 5,426 | 0.762 (0.751–0.774) | 0.266 (0.248–0.283) | 0.062 (0.059–0.065) | 0.853 | 0.736 |
| lgb|FS-A|unweighted | 75,124 | 5,426 | 0.857 (0.849–0.865) | 0.374 (0.352–0.396) | 0.054 (0.052–0.057) | 0.040 | 0.978 |
| lgb|FS-A|weighted | 75,124 | 5,426 | 0.831 (0.823–0.841) | 0.267 (0.250–0.286) | 0.063 (0.061–0.066) | -0.598 | 3.038 |
| lgb|FS-A|weighted+corrected | 75,124 | 5,426 | 0.831 (0.823–0.841) | 0.267 (0.250–0.286) | 0.070 (0.066–0.074) | 1.969 | 3.038 |
| lgb|FS-B|unweighted | 75,124 | 5,426 | 0.788 (0.778–0.797) | 0.286 (0.267–0.303) | 0.059 (0.056–0.062) | 0.031 | 0.969 |
| lgb|FS-B|weighted | 75,124 | 5,426 | 0.738 (0.729–0.748) | 0.180 (0.167–0.192) | 0.066 (0.063–0.069) | -0.419 | 3.478 |
| lgb|FS-B|weighted+corrected | 75,124 | 5,426 | 0.738 (0.729–0.748) | 0.180 (0.167–0.192) | 0.071 (0.067–0.075) | 2.148 | 3.478 |

### Within code-negative admissions only (the recovery-zone question in silver-label form)

| model | n | positives | AUROC | AUPRC | Brier |
| --- | --: | --: | --: | --: | --: |
| cat|FS-A|unweighted | 74,109 | 4,555 | 0.857 | 0.323 | 0.048 |
| cat|FS-A|weighted | 74,109 | 4,555 | 0.856 | 0.312 | 0.145 |
| cat|FS-A|weighted+corrected | 74,109 | 4,555 | 0.856 | 0.312 | 0.049 |
| cat|FS-B|unweighted | 74,109 | 4,555 | 0.777 | 0.228 | 0.053 |
| cat|FS-B|weighted | 74,109 | 4,555 | 0.777 | 0.224 | 0.174 |
| cat|FS-B|weighted+corrected | 74,109 | 4,555 | 0.777 | 0.224 | 0.053 |
| cat|FS-AVAIL|unweighted | 74,109 | 4,555 | 0.817 | 0.213 | 0.052 |
| cat|FS-AVAIL|weighted | 74,109 | 4,555 | 0.815 | 0.207 | 0.177 |
| cat|FS-AVAIL|weighted+corrected | 74,109 | 4,555 | 0.815 | 0.207 | 0.052 |
| xgb|FS-A|unweighted | 74,109 | 4,555 | 0.857 | 0.318 | 0.049 |
| xgb|FS-A|weighted | 74,109 | 4,555 | 0.838 | 0.298 | 0.086 |
| xgb|FS-A|weighted+corrected | 74,109 | 4,555 | 0.838 | 0.298 | 0.051 |
| xgb|FS-B|unweighted | 74,109 | 4,555 | 0.777 | 0.230 | 0.053 |
| xgb|FS-B|weighted | 74,109 | 4,555 | 0.750 | 0.209 | 0.103 |
| xgb|FS-B|weighted+corrected | 74,109 | 4,555 | 0.750 | 0.209 | 0.054 |
| lgb|FS-A|unweighted | 74,109 | 4,555 | 0.857 | 0.315 | 0.049 |
| lgb|FS-A|weighted | 74,109 | 4,555 | 0.835 | 0.234 | 0.056 |
| lgb|FS-A|weighted+corrected | 74,109 | 4,555 | 0.835 | 0.234 | 0.059 |
| lgb|FS-B|unweighted | 74,109 | 4,555 | 0.778 | 0.230 | 0.053 |
| lgb|FS-B|weighted | 74,109 | 4,555 | 0.734 | 0.152 | 0.058 |
| lgb|FS-B|weighted+corrected | 74,109 | 4,555 | 0.734 | 0.152 | 0.060 |

### Thresholds (chosen on DEV OOF by maximum F1; CatBoost rows)

| model | threshold | DEV OOF F1 | TEST sensitivity | TEST specificity | TEST PPV |
| --- | --: | --: | --: | --: | --: |
| cat|FS-A|unweighted | 0.208 | 0.408 | 0.479 | 0.936 | 0.368 |
| cat|FS-A|weighted | 0.743 | 0.402 | 0.489 | 0.931 | 0.355 |
| cat|FS-A|weighted+corrected | 0.183 | 0.402 | 0.492 | 0.930 | 0.353 |
| cat|FS-B|unweighted | 0.156 | 0.340 | 0.408 | 0.918 | 0.279 |
| cat|FS-B|weighted | 0.695 | 0.337 | 0.389 | 0.922 | 0.280 |
| cat|FS-B|weighted+corrected | 0.149 | 0.337 | 0.389 | 0.922 | 0.280 |
| cat|FS-AVAIL|unweighted | 0.162 | 0.324 | 0.512 | 0.875 | 0.242 |
| cat|FS-AVAIL|weighted | 0.711 | 0.323 | 0.508 | 0.876 | 0.242 |
| cat|FS-AVAIL|weighted+corrected | 0.159 | 0.323 | 0.510 | 0.875 | 0.242 |

## Secondary population — imaging-observed admissions (≥1 liver-inclusive study, −365/+30)

Sizes: DEV 109,220 (positives 17,559), TEST 27,602 (positives 4,493). Within admissions where the liver was actually imaged, can structured data predict documented steatosis?

| model | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |
| --- | --: | --: | --- | --- | --- | --: | --: |
| cat|FS-A|unweighted | 27,602 | 4,493 | 0.766 (0.754–0.778) | 0.426 (0.403–0.453) | 0.116 (0.111–0.120) | 0.030 | 1.039 |
| cat|FS-A|weighted | 27,602 | 4,493 | 0.765 (0.753–0.777) | 0.421 (0.397–0.447) | 0.184 (0.181–0.188) | -1.505 | 1.068 |
| cat|FS-A|weighted+corrected | 27,602 | 4,493 | 0.765 (0.753–0.777) | 0.421 (0.397–0.447) | 0.117 (0.112–0.122) | 0.138 | 1.068 |
| cat|FS-B|unweighted | 27,602 | 4,493 | 0.750 (0.738–0.763) | 0.402 (0.378–0.427) | 0.118 (0.113–0.123) | 0.028 | 0.997 |
| cat|FS-B|weighted | 27,602 | 4,493 | 0.750 (0.737–0.762) | 0.397 (0.372–0.420) | 0.193 (0.190–0.197) | -1.536 | 1.063 |
| cat|FS-B|weighted+corrected | 27,602 | 4,493 | 0.750 (0.737–0.762) | 0.397 (0.372–0.420) | 0.119 (0.114–0.125) | 0.121 | 1.063 |

## Subgroups (TEST; CatBoost; metric only where ≥50 positives and ≥50 negatives)

A subgroup is flagged when its calibration intercept differs from the overall by more than 0.5 or its slope by more than 0.25 (analyst threshold).

### cat|FS-A|unweighted

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.863 | 0.370 | 0.052 | 0.282 | 1.046 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.816 | 0.263 | 0.064 | -0.208 | 0.727 | **yes** |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.870 | 0.349 | 0.045 | -0.345 | 1.102 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.780 | 0.174 | 0.065 | -0.441 | 0.639 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.843 | 0.498 | 0.081 | 0.552 | 0.974 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.838 | 0.488 | 0.065 | -0.018 | 1.062 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.784 | 0.460 | 0.147 | 0.487 | 0.770 | no |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.837 | 0.489 | 0.077 | 0.138 | 0.969 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.879 | 0.466 | 0.048 | 0.077 | 1.173 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.852 | 0.382 | 0.047 | 0.006 | 1.020 | no |
| race=WHITE | 48,555 | 3,444 | 0.857 | 0.375 | 0.054 | 0.075 | 1.016 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.862 | 0.395 | 0.070 | 0.153 | 1.077 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.877 | 0.553 | 0.039 | 0.111 | 1.316 | **yes** |
| insurance=Medicaid | 12,839 | 1,212 | 0.867 | 0.446 | 0.066 | 0.062 | 1.103 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.842 | 0.298 | 0.046 | -0.032 | 0.945 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.879 | 0.444 | 0.059 | 0.075 | 1.151 | no |
| insurance=Private | 22,784 | 1,950 | 0.857 | 0.415 | 0.062 | 0.086 | 1.034 | no |
| gender=F | 38,109 | 2,528 | 0.861 | 0.369 | 0.050 | 0.054 | 1.040 | no |
| gender=M | 37,015 | 2,898 | 0.852 | 0.390 | 0.058 | 0.010 | 1.001 | no |
| age_band=18-39 | 10,566 | 684 | 0.903 | 0.467 | 0.045 | 0.145 | 1.122 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.844 | 0.440 | 0.073 | 0.112 | 1.012 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.830 | 0.349 | 0.070 | -0.076 | 1.005 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.828 | 0.357 | 0.058 | -0.023 | 0.992 | no |
| age_band=75-88 | 15,587 | 626 | 0.842 | 0.269 | 0.034 | 0.106 | 1.003 | no |
| age_band=89+ | 4,081 | 59 | 0.867 | 0.095 | 0.014 | -0.220 | 1.023 | no |

### cat|FS-A|weighted

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.868 | 0.387 | 0.114 | -2.107 | 1.094 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.822 | 0.263 | 0.163 | -2.489 | 0.806 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.869 | 0.336 | 0.156 | -2.726 | 1.152 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.777 | 0.154 | 0.198 | -2.810 | 0.652 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.845 | 0.488 | 0.149 | -1.836 | 1.012 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.832 | 0.510 | 0.191 | -2.418 | 1.065 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.795 | 0.459 | 0.241 | -1.914 | 0.883 | no |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.838 | 0.497 | 0.190 | -2.275 | 1.013 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.871 | 0.448 | 0.132 | -2.344 | 1.160 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.858 | 0.358 | 0.127 | -2.406 | 1.025 | no |
| race=WHITE | 48,555 | 3,444 | 0.857 | 0.366 | 0.140 | -2.344 | 1.053 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.857 | 0.372 | 0.169 | -2.272 | 1.097 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.876 | 0.574 | 0.104 | -2.231 | 1.377 | **yes** |
| insurance=Medicaid | 12,839 | 1,212 | 0.864 | 0.428 | 0.171 | -2.333 | 1.142 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.842 | 0.295 | 0.127 | -2.438 | 0.981 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.883 | 0.441 | 0.153 | -2.331 | 1.245 | no |
| insurance=Private | 22,784 | 1,950 | 0.856 | 0.403 | 0.161 | -2.337 | 1.067 | no |
| gender=F | 38,109 | 2,528 | 0.861 | 0.359 | 0.135 | -2.370 | 1.070 | no |
| gender=M | 37,015 | 2,898 | 0.851 | 0.382 | 0.156 | -2.385 | 1.043 | no |
| age_band=18-39 | 10,566 | 684 | 0.903 | 0.451 | 0.106 | -2.203 | 1.189 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.844 | 0.425 | 0.184 | -2.305 | 1.063 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.827 | 0.348 | 0.201 | -2.498 | 1.042 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.827 | 0.351 | 0.169 | -2.472 | 1.029 | no |
| age_band=75-88 | 15,587 | 626 | 0.843 | 0.275 | 0.086 | -2.264 | 1.071 | no |
| age_band=89+ | 4,081 | 59 | 0.866 | 0.103 | 0.036 | -2.412 | 1.110 | no |

### cat|FS-A|weighted+corrected

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.868 | 0.387 | 0.052 | 0.447 | 1.094 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.822 | 0.263 | 0.061 | 0.064 | 0.806 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.869 | 0.336 | 0.045 | -0.173 | 1.152 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.777 | 0.154 | 0.064 | -0.257 | 0.652 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.845 | 0.488 | 0.085 | 0.717 | 1.012 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.832 | 0.510 | 0.067 | 0.135 | 1.065 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.795 | 0.459 | 0.146 | 0.639 | 0.883 | no |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.838 | 0.497 | 0.078 | 0.278 | 1.013 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.871 | 0.448 | 0.050 | 0.209 | 1.160 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.858 | 0.358 | 0.048 | 0.147 | 1.025 | no |
| race=WHITE | 48,555 | 3,444 | 0.857 | 0.366 | 0.054 | 0.209 | 1.053 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.857 | 0.372 | 0.071 | 0.282 | 1.097 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.876 | 0.574 | 0.040 | 0.322 | 1.377 | **yes** |
| insurance=Medicaid | 12,839 | 1,212 | 0.864 | 0.428 | 0.068 | 0.220 | 1.142 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.842 | 0.295 | 0.046 | 0.116 | 0.981 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.883 | 0.441 | 0.060 | 0.222 | 1.245 | no |
| insurance=Private | 22,784 | 1,950 | 0.856 | 0.403 | 0.063 | 0.216 | 1.067 | no |
| gender=F | 38,109 | 2,528 | 0.861 | 0.359 | 0.051 | 0.183 | 1.070 | no |
| gender=M | 37,015 | 2,898 | 0.851 | 0.382 | 0.059 | 0.168 | 1.043 | no |
| age_band=18-39 | 10,566 | 684 | 0.903 | 0.451 | 0.047 | 0.350 | 1.189 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.844 | 0.425 | 0.075 | 0.249 | 1.063 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.827 | 0.348 | 0.070 | 0.055 | 1.042 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.827 | 0.351 | 0.059 | 0.081 | 1.029 | no |
| age_band=75-88 | 15,587 | 626 | 0.843 | 0.275 | 0.034 | 0.289 | 1.071 | no |
| age_band=89+ | 4,081 | 59 | 0.866 | 0.103 | 0.014 | 0.141 | 1.110 | no |

### cat|FS-B|unweighted

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.810 | 0.246 | 0.057 | 0.199 | 0.982 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.765 | 0.212 | 0.065 | -0.038 | 0.764 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.792 | 0.261 | 0.049 | -0.347 | 1.097 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.661 | 0.129 | 0.067 | -0.401 | 0.477 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.751 | 0.325 | 0.095 | 0.580 | 0.859 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.773 | 0.268 | 0.079 | 0.115 | 0.935 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.677 | 0.392 | 0.165 | 0.574 | 0.532 | **yes** |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.780 | 0.376 | 0.087 | 0.230 | 0.999 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.806 | 0.368 | 0.053 | 0.011 | 1.142 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.797 | 0.313 | 0.050 | -0.083 | 0.993 | no |
| race=WHITE | 48,555 | 3,444 | 0.788 | 0.278 | 0.058 | 0.062 | 0.975 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.775 | 0.279 | 0.078 | 0.190 | 0.935 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.778 | 0.361 | 0.046 | 0.146 | 1.126 | no |
| insurance=Medicaid | 12,839 | 1,212 | 0.792 | 0.327 | 0.074 | 0.063 | 1.040 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.769 | 0.224 | 0.048 | -0.034 | 0.900 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.818 | 0.395 | 0.063 | -0.002 | 1.162 | no |
| insurance=Private | 22,784 | 1,950 | 0.785 | 0.304 | 0.069 | 0.084 | 1.011 | no |
| gender=F | 38,109 | 2,528 | 0.791 | 0.276 | 0.055 | 0.049 | 1.010 | no |
| gender=M | 37,015 | 2,898 | 0.781 | 0.288 | 0.064 | 0.007 | 0.957 | no |
| age_band=18-39 | 10,566 | 684 | 0.850 | 0.334 | 0.051 | 0.107 | 1.106 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.766 | 0.334 | 0.082 | 0.106 | 1.004 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.738 | 0.258 | 0.076 | -0.073 | 0.930 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.744 | 0.262 | 0.063 | -0.035 | 0.947 | no |
| age_band=75-88 | 15,587 | 626 | 0.757 | 0.213 | 0.035 | 0.125 | 0.966 | no |
| age_band=89+ | 4,081 | 59 | 0.740 | 0.065 | 0.014 | -0.127 | 0.847 | no |

### cat|FS-B|weighted

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.822 | 0.296 | 0.137 | -2.238 | 1.150 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.764 | 0.210 | 0.173 | -2.401 | 0.860 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.788 | 0.270 | 0.196 | -2.790 | 1.196 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.668 | 0.133 | 0.234 | -2.808 | 0.546 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.740 | 0.315 | 0.184 | -1.872 | 0.893 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.758 | 0.245 | 0.218 | -2.333 | 0.927 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.675 | 0.338 | 0.277 | -1.821 | 0.539 | **yes** |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.769 | 0.369 | 0.216 | -2.197 | 1.058 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.804 | 0.372 | 0.162 | -2.435 | 1.222 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.799 | 0.285 | 0.157 | -2.507 | 1.035 | no |
| race=WHITE | 48,555 | 3,444 | 0.789 | 0.271 | 0.167 | -2.398 | 1.032 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.777 | 0.272 | 0.200 | -2.269 | 0.999 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.774 | 0.397 | 0.125 | -2.280 | 1.150 | no |
| insurance=Medicaid | 12,839 | 1,212 | 0.791 | 0.325 | 0.209 | -2.374 | 1.125 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.767 | 0.220 | 0.149 | -2.490 | 0.945 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.818 | 0.385 | 0.191 | -2.434 | 1.271 | no |
| insurance=Private | 22,784 | 1,950 | 0.784 | 0.296 | 0.195 | -2.376 | 1.074 | no |
| gender=F | 38,109 | 2,528 | 0.791 | 0.272 | 0.160 | -2.407 | 1.066 | no |
| gender=M | 37,015 | 2,898 | 0.780 | 0.282 | 0.189 | -2.441 | 1.023 | no |
| age_band=18-39 | 10,566 | 684 | 0.850 | 0.329 | 0.133 | -2.319 | 1.184 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.764 | 0.324 | 0.228 | -2.349 | 1.081 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.739 | 0.262 | 0.240 | -2.521 | 1.012 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.745 | 0.258 | 0.202 | -2.513 | 1.031 | no |
| age_band=75-88 | 15,587 | 626 | 0.756 | 0.199 | 0.094 | -2.317 | 1.012 | no |
| age_band=89+ | 4,081 | 59 | 0.725 | 0.058 | 0.036 | -2.471 | 0.845 | no |

### cat|FS-B|weighted+corrected

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.822 | 0.296 | 0.056 | 0.327 | 1.150 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.764 | 0.210 | 0.064 | 0.164 | 0.860 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.788 | 0.270 | 0.049 | -0.225 | 1.196 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.668 | 0.133 | 0.064 | -0.242 | 0.546 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.740 | 0.315 | 0.097 | 0.693 | 0.893 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.758 | 0.245 | 0.080 | 0.233 | 0.927 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.675 | 0.338 | 0.169 | 0.745 | 0.539 | **yes** |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.769 | 0.369 | 0.089 | 0.369 | 1.058 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.804 | 0.372 | 0.053 | 0.131 | 1.222 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.799 | 0.285 | 0.051 | 0.058 | 1.035 | no |
| race=WHITE | 48,555 | 3,444 | 0.789 | 0.271 | 0.059 | 0.167 | 1.032 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.777 | 0.272 | 0.079 | 0.296 | 0.999 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.774 | 0.397 | 0.047 | 0.286 | 1.150 | no |
| insurance=Medicaid | 12,839 | 1,212 | 0.791 | 0.325 | 0.075 | 0.192 | 1.125 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.767 | 0.220 | 0.049 | 0.076 | 0.945 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.818 | 0.385 | 0.064 | 0.131 | 1.271 | no |
| insurance=Private | 22,784 | 1,950 | 0.784 | 0.296 | 0.070 | 0.190 | 1.074 | no |
| gender=F | 38,109 | 2,528 | 0.791 | 0.272 | 0.055 | 0.159 | 1.066 | no |
| gender=M | 37,015 | 2,898 | 0.780 | 0.282 | 0.064 | 0.125 | 1.023 | no |
| age_band=18-39 | 10,566 | 684 | 0.850 | 0.329 | 0.052 | 0.246 | 1.184 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.764 | 0.324 | 0.083 | 0.216 | 1.081 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.739 | 0.262 | 0.076 | 0.045 | 1.012 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.745 | 0.258 | 0.063 | 0.052 | 1.031 | no |
| age_band=75-88 | 15,587 | 626 | 0.756 | 0.199 | 0.036 | 0.249 | 1.012 | no |
| age_band=89+ | 4,081 | 59 | 0.725 | 0.058 | 0.014 | 0.094 | 0.845 | no |

### cat|FS-AVAIL|unweighted

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.820 | 0.266 | 0.056 | 0.006 | 1.010 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.795 | 0.219 | 0.062 | -0.223 | 0.996 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.829 | 0.232 | 0.049 | -0.187 | 1.154 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.764 | 0.142 | 0.062 | -0.268 | 0.766 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.802 | 0.325 | 0.093 | 0.628 | 0.931 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.774 | 0.240 | 0.078 | 0.030 | 0.879 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.799 | 0.461 | 0.153 | 0.831 | 1.138 | **yes** |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.754 | 0.274 | 0.092 | 0.322 | 0.792 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.819 | 0.270 | 0.056 | 0.078 | 1.050 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.827 | 0.257 | 0.051 | 0.126 | 1.092 | no |
| race=WHITE | 48,555 | 3,444 | 0.811 | 0.240 | 0.059 | 0.002 | 1.030 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.800 | 0.338 | 0.075 | 0.152 | 1.046 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.824 | 0.221 | 0.049 | -0.215 | 1.252 | no |
| insurance=Medicaid | 12,839 | 1,212 | 0.816 | 0.293 | 0.075 | 0.239 | 1.045 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.802 | 0.199 | 0.049 | -0.261 | 1.032 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.863 | 0.367 | 0.064 | 0.234 | 1.269 | no |
| insurance=Private | 22,784 | 1,950 | 0.813 | 0.272 | 0.069 | 0.223 | 0.986 | no |
| gender=F | 38,109 | 2,528 | 0.819 | 0.239 | 0.055 | -0.058 | 1.094 | no |
| gender=M | 37,015 | 2,898 | 0.805 | 0.252 | 0.064 | 0.080 | 0.984 | no |
| age_band=18-39 | 10,566 | 684 | 0.864 | 0.314 | 0.051 | 0.115 | 1.222 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.803 | 0.298 | 0.083 | 0.377 | 0.946 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.785 | 0.241 | 0.076 | 0.126 | 0.916 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.789 | 0.239 | 0.063 | -0.010 | 0.971 | no |
| age_band=75-88 | 15,587 | 626 | 0.812 | 0.165 | 0.037 | -0.529 | 1.123 | **yes** |
| age_band=89+ | 4,081 | 59 | 0.871 | 0.108 | 0.016 | -1.386 | 1.525 | **yes** |

### cat|FS-AVAIL|weighted

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.813 | 0.273 | 0.166 | -2.471 | 0.967 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.794 | 0.221 | 0.215 | -2.731 | 0.983 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.826 | 0.218 | 0.173 | -2.706 | 1.124 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.755 | 0.137 | 0.213 | -2.776 | 0.741 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.800 | 0.304 | 0.169 | -1.872 | 0.896 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.775 | 0.230 | 0.221 | -2.484 | 0.866 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.800 | 0.457 | 0.226 | -1.689 | 1.132 | **yes** |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.753 | 0.261 | 0.214 | -2.194 | 0.780 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.816 | 0.256 | 0.160 | -2.428 | 1.020 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.827 | 0.266 | 0.136 | -2.354 | 1.082 | no |
| race=WHITE | 48,555 | 3,444 | 0.810 | 0.235 | 0.176 | -2.506 | 1.014 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.806 | 0.326 | 0.202 | -2.369 | 1.066 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.823 | 0.216 | 0.184 | -2.752 | 1.241 | no |
| insurance=Medicaid | 12,839 | 1,212 | 0.814 | 0.285 | 0.185 | -2.273 | 1.028 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.800 | 0.196 | 0.181 | -2.775 | 1.016 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.860 | 0.352 | 0.158 | -2.267 | 1.245 | no |
| insurance=Private | 22,784 | 1,950 | 0.812 | 0.263 | 0.173 | -2.278 | 0.966 | no |
| gender=F | 38,109 | 2,528 | 0.819 | 0.233 | 0.176 | -2.573 | 1.081 | no |
| gender=M | 37,015 | 2,898 | 0.803 | 0.245 | 0.179 | -2.422 | 0.961 | no |
| age_band=18-39 | 10,566 | 684 | 0.862 | 0.301 | 0.139 | -2.372 | 1.182 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.803 | 0.289 | 0.182 | -2.131 | 0.931 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.783 | 0.238 | 0.201 | -2.383 | 0.902 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.789 | 0.232 | 0.191 | -2.527 | 0.958 | no |
| age_band=75-88 | 15,587 | 626 | 0.810 | 0.166 | 0.171 | -3.044 | 1.103 | **yes** |
| age_band=89+ | 4,081 | 59 | 0.865 | 0.107 | 0.143 | -3.897 | 1.461 | **yes** |

### cat|FS-AVAIL|weighted+corrected

| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| race=AMERICAN INDIAN/ALASKA NATIVE | | | not estimable | | | | | |
| race=ASIAN | 863 | 58 | 0.813 | 0.273 | 0.056 | 0.088 | 0.967 | no |
| race=ASIAN - ASIAN INDIAN | | | not estimable | | | | | |
| race=ASIAN - CHINESE | 988 | 72 | 0.794 | 0.221 | 0.062 | -0.172 | 0.983 | no |
| race=ASIAN - KOREAN | | | not estimable | | | | | |
| race=ASIAN - SOUTH EAST ASIAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN | | | not estimable | | | | | |
| race=BLACK/AFRICAN AMERICAN | 9,834 | 568 | 0.826 | 0.218 | 0.049 | -0.147 | 1.124 | no |
| race=BLACK/CAPE VERDEAN | 803 | 54 | 0.755 | 0.137 | 0.062 | -0.218 | 0.741 | **yes** |
| race=BLACK/CARIBBEAN ISLAND | | | not estimable | | | | | |
| race=HISPANIC OR LATINO | 1,122 | 131 | 0.800 | 0.304 | 0.094 | 0.686 | 0.896 | **yes** |
| race=HISPANIC/LATINO - CENTRAL AMERICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - COLUMBIAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - CUBAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - DOMINICAN | 790 | 75 | 0.775 | 0.230 | 0.078 | 0.074 | 0.866 | no |
| race=HISPANIC/LATINO - GUATEMALAN | 264 | 57 | 0.800 | 0.457 | 0.154 | 0.869 | 1.132 | **yes** |
| race=HISPANIC/LATINO - HONDURAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - MEXICAN | | | not estimable | | | | | |
| race=HISPANIC/LATINO - PUERTO RICAN | 1,468 | 167 | 0.753 | 0.261 | 0.093 | 0.365 | 0.780 | no |
| race=HISPANIC/LATINO - SALVADORAN | | | not estimable | | | | | |
| race=MULTIPLE RACE/ETHNICITY | | | not estimable | | | | | |
| race=NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | | | not estimable | | | | | |
| race=OTHER | 2,491 | 169 | 0.816 | 0.256 | 0.057 | 0.131 | 1.020 | no |
| race=PATIENT DECLINED TO ANSWER | | | not estimable | | | | | |
| race=PORTUGUESE | | | not estimable | | | | | |
| race=SOUTH AMERICAN | | | not estimable | | | | | |
| race=UNABLE TO OBTAIN | | | not estimable | | | | | |
| race=UNKNOWN | 1,885 | 117 | 0.827 | 0.266 | 0.051 | 0.205 | 1.082 | no |
| race=WHITE | 48,555 | 3,444 | 0.810 | 0.235 | 0.059 | 0.053 | 1.014 | no |
| race=WHITE - BRAZILIAN | | | not estimable | | | | | |
| race=WHITE - EASTERN EUROPEAN | | | not estimable | | | | | |
| race=WHITE - OTHER EUROPEAN | 1,532 | 146 | 0.806 | 0.326 | 0.075 | 0.189 | 1.066 | no |
| race=WHITE - RUSSIAN | 966 | 56 | 0.823 | 0.216 | 0.049 | -0.194 | 1.241 | no |
| insurance=Medicaid | 12,839 | 1,212 | 0.814 | 0.285 | 0.075 | 0.285 | 1.028 | no |
| insurance=Medicare | 36,382 | 2,046 | 0.800 | 0.196 | 0.049 | -0.216 | 1.016 | no |
| insurance=No charge | | | not estimable | | | | | |
| insurance=Other | 2,027 | 168 | 0.860 | 0.352 | 0.064 | 0.291 | 1.245 | no |
| insurance=Private | 22,784 | 1,950 | 0.812 | 0.263 | 0.070 | 0.281 | 0.966 | no |
| gender=F | 38,109 | 2,528 | 0.819 | 0.233 | 0.055 | -0.014 | 1.081 | no |
| gender=M | 37,015 | 2,898 | 0.803 | 0.245 | 0.065 | 0.136 | 0.961 | no |
| age_band=18-39 | 10,566 | 684 | 0.862 | 0.301 | 0.052 | 0.186 | 1.182 | no |
| age_band=40-54 | 14,702 | 1,528 | 0.803 | 0.289 | 0.083 | 0.428 | 0.931 | no |
| age_band=55-64 | 15,348 | 1,408 | 0.783 | 0.238 | 0.076 | 0.176 | 0.902 | no |
| age_band=65-74 | 14,840 | 1,121 | 0.789 | 0.232 | 0.063 | 0.031 | 0.958 | no |
| age_band=75-88 | 15,587 | 626 | 0.810 | 0.166 | 0.037 | -0.485 | 1.103 | **yes** |
| age_band=89+ | 4,081 | 59 | 0.865 | 0.107 | 0.016 | -1.338 | 1.461 | **yes** |

## Interpretation — SHAP (CatBoost, unweighted, 20,000-admission TEST sample; top 25 per feature set)

### FS-A — share of top-25 that are availability/volume features: 28%

| rank | feature | class | mean |SHAP| |
| --: | --- | --- | --: |
| 1 | liver_imaging_any_pre | availability | 0.6752 |
| 2 | age | clinical | 0.3360 |
| 3 | omr_BMI | clinical | 0.2254 |
| 4 | liver_imaging_out_pre365 | availability | 0.2062 |
| 5 | cmrf_overweight | clinical | 0.1967 |
| 6 | icd_era | clinical | 0.1574 |
| 7 | first_val_ALT | clinical | 0.1242 |
| 8 | etio_alcohol | clinical | 0.1120 |
| 9 | chars_dc | availability | 0.0937 |
| 10 | pre365_Triglycerides | clinical | 0.0864 |
| 11 | liver_imaging_inp | availability | 0.0851 |
| 12 | chars_rad_inp | availability | 0.0638 |
| 13 | pre365_HbA1c | clinical | 0.0635 |
| 14 | omr_DBP | clinical | 0.0627 |
| 15 | n_diagnoses | availability | 0.0617 |
| 16 | etio_cirrhosis | clinical | 0.0608 |
| 17 | last_val_Glucose | clinical | 0.0593 |
| 18 | insulin | clinical | 0.0585 |
| 19 | last_val_ALT | clinical | 0.0584 |
| 20 | charlson_noliver | clinical | 0.0545 |
| 21 | n_notes_rad_out_pre365 | availability | 0.0512 |
| 22 | marital_status | clinical | 0.0474 |
| 23 | omr_SBP | clinical | 0.0450 |
| 24 | cmrf_dysglycemia | clinical | 0.0407 |
| 25 | cmrf_hypertension | clinical | 0.0401 |

### FS-B — share of top-25 that are availability/volume features: 0%

| rank | feature | class | mean |SHAP| |
| --: | --- | --- | --: |
| 1 | age | clinical | 0.3557 |
| 2 | omr_BMI | clinical | 0.1805 |
| 3 | cmrf_overweight | clinical | 0.1588 |
| 4 | icd_era | clinical | 0.1570 |
| 5 | first_val_ALT | clinical | 0.1244 |
| 6 | omr_SBP | clinical | 0.1201 |
| 7 | pre365_Triglycerides | clinical | 0.1161 |
| 8 | etio_alcohol | clinical | 0.1062 |
| 9 | first_val_Bilirubin_total | clinical | 0.0996 |
| 10 | omr_DBP | clinical | 0.0780 |
| 11 | etio_cirrhosis | clinical | 0.0774 |
| 12 | pre365_HbA1c | clinical | 0.0701 |
| 13 | last_val_Glucose | clinical | 0.0664 |
| 14 | first_val_AST | clinical | 0.0635 |
| 15 | marital_status | clinical | 0.0623 |
| 16 | last_val_ALT | clinical | 0.0560 |
| 17 | htn_excl | clinical | 0.0533 |
| 18 | insulin | clinical | 0.0529 |
| 19 | admission_type | clinical | 0.0464 |
| 20 | pre365_HDL | clinical | 0.0395 |
| 21 | last_val_Alkaline_phosphatase | clinical | 0.0355 |
| 22 | charlson_noliver | clinical | 0.0352 |
| 23 | cmrf_dysglycemia | clinical | 0.0335 |
| 24 | gender | clinical | 0.0331 |
| 25 | bb | clinical | 0.0325 |

### FS-AVAIL — share of top-25 that are availability/volume features: 100%

| rank | feature | class | mean |SHAP| |
| --: | --- | --- | --: |
| 1 | liver_imaging_any_pre | availability | 0.4642 |
| 2 | liver_imaging_out_pre365 | availability | 0.2579 |
| 3 | liver_imaging_inp | availability | 0.2232 |
| 4 | chars_dc | availability | 0.1346 |
| 5 | n_diagnoses | availability | 0.1285 |
| 6 | n_Platelets | availability | 0.1216 |
| 7 | n_notes_rad_out_pre365 | availability | 0.1056 |
| 8 | n_analytes_available | availability | 0.1051 |
| 9 | chars_rad_inp | availability | 0.0638 |
| 10 | has_BMI | availability | 0.0632 |
| 11 | n_Bilirubin_total | availability | 0.0607 |
| 12 | n_ALT | availability | 0.0577 |
| 13 | n_AST | availability | 0.0576 |
| 14 | miss_omr_DBP | availability | 0.0433 |
| 15 | has_DBP | availability | 0.0393 |
| 16 | n_Alkaline_phosphatase | availability | 0.0354 |
| 17 | n_rx_distinct | availability | 0.0317 |
| 18 | miss_omr_BMI | availability | 0.0301 |
| 19 | n_Glucose | availability | 0.0282 |
| 20 | n_rx_orders | availability | 0.0276 |
| 21 | miss_lab_Albumin | availability | 0.0262 |
| 22 | n_notes_rad_inp | availability | 0.0242 |
| 23 | n_Albumin | availability | 0.0234 |
| 24 | has_SBP | availability | 0.0215 |
| 25 | n_lab_results_total | availability | 0.0158 |

### What the attributions say

The single strongest attribution in FS-A is **liver_imaging_any_pre** (availability, mean |SHAP| 0.675) — whether the liver was imaged at all. Below it the ranking is mixed: 2 of the top 5 and 28% of the top 25 are availability or volume features, with age, body-mass index and the overweight criterion among the strongest clinical contributors. So the pre-specified expectation (H1b-i) is only half borne out: the top attribution is an availability feature, but it is **imaging availability, not laboratory availability or diagnosis count**, and clinical values are not displaced from the upper ranks.

The feature-set comparison is the sharper result:

| feature set | what it contains | TEST AUROC | TEST AUPRC |
| --- | --- | --: | --: |
| FS-B | clinical values only | 0.787 | 0.282 |
| FS-AVAIL | availability and volume only, no clinical value | 0.812 | 0.245 |
| FS-A | everything | 0.857 | 0.380 |

**Knowing only what was measured, imaged, ordered and written — with no clinical value at all — discriminates better than the clinical values do** (0.812 versus 0.787 AUROC). That is a finding about the data, not a successful clinical model: the silver label is a property of documentation, and the documentation process predicts itself. It also bounds the caveat that tree models see missingness natively — FS-B cannot be read as a clean 'clinical signal' estimate, because its own missingness pattern carries part of what FS-AVAIL measures directly.

## Calibration plots

Reliability diagrams (10 quantile bins, TEST) for every CatBoost row: `docs/figures/aim1b_cal_cat_*.png`.

Runtime 1.1 h.
