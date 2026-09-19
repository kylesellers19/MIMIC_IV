# Aim 1c level 1 — by race (run_2026-09-19)

Source: `docs/run_2026-09-19/results/aim1c_level1.json`.

# Aim 1c, level 1 — equity of recovery at the computable stage (run_2026-09-19)

Produced by `scripts/run0919_aim1c_level1.py`; every number is read from `docs/run_2026-09-19/results/aim1c_level1.json`. Pre-specification: `docs/analysis_plan_prespecified.md` (H1c; amendment g). Definition (b), v1.1.0, −365/+30 outpatient window.

**What is measured.** Recovery share = B ÷ (A + B): among note-positive admissions, the share with no MASLD code. Corroboration share = A ÷ (A + C): among code-positive admissions, the share whose notes also document steatosis. Both are computable-stage quantities about *documentation and coding*, not adjudicated disease. 95% CIs are subject-cluster bootstraps (500 replicates; a subject's admissions are resampled together because one person can contribute several). Floors: no recovery share where B < 11; no corroboration share where A + C < 11; such strata are declared non-analyzable, not merged. A CI wider than 20 percentage points is marked as too wide to support a claim (an analyst threshold, stated here so it can be argued with). No p-values. The SMD column is the one-versus-rest standardized difference in the coding rate among note-positive admissions (A ÷ (A + B)), a descriptive contrast.

Levels 2 and 3 of the audit (weighted PPV by stratum against the gold standard; model calibration by stratum) require the adjudication and the models and are not attempted here.

UNKNOWN, UNABLE TO OBTAIN and PATIENT DECLINED TO ANSWER are reported but are **encounter characteristics, not population groups** (marked †). Ages ≥ 89 are recoded to 91 in MIMIC-IV, so the 89+ band is an aggregate.

## By race

Cell counts first:

| race | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |
| --- | --: | --: | --: | --: |
| WHITE | 3,167 | 14,785 | 447 | 222,559 |
| BLACK/AFRICAN AMERICAN | 410 | 2,449 | 76 | 46,706 |
| OTHER | 185 | 718 | 27 | 11,598 |
| UNKNOWN † | 88 | 493 | 11 | 9,134 |
| WHITE - OTHER EUROPEAN | 139 | 524 | 22 | 6,441 |
| HISPANIC/LATINO - PUERTO RICAN | 235 | 622 | 20 | 5,943 |
| HISPANIC OR LATINO | 92 | 518 | 16 | 5,543 |
| ASIAN - CHINESE | 67 | 374 | 11 | 4,241 |
| WHITE - RUSSIAN | 81 | 214 | 11 | 4,354 |
| ASIAN | 49 | 262 | 9 | 4,330 |
| BLACK/CAPE VERDEAN | 57 | 235 | 4 | 3,691 |
| HISPANIC/LATINO - DOMINICAN | 79 | 289 | 13 | 3,229 |
| BLACK/CARIBBEAN ISLAND | 16 | 101 | 2 | 2,283 |
| BLACK/AFRICAN | 25 | 92 | 3 | 1,895 |
| PATIENT DECLINED TO ANSWER † | 19 | 70 | 6 | 1,428 |
| UNABLE TO OBTAIN † | 9 | 55 | 2 | 1,326 |
| PORTUGUESE | 56 | 119 | 7 | 1,201 |
| ASIAN - SOUTH EAST ASIAN | 15 | 114 | 1 | 1,132 |
| HISPANIC/LATINO - GUATEMALAN | 55 | 138 | 4 | 982 |
| WHITE - EASTERN EUROPEAN | 12 | 54 | 2 | 977 |
| ASIAN - ASIAN INDIAN | 14 | 81 | 3 | 879 |
| WHITE - BRAZILIAN | 21 | 69 | 5 | 855 |
| AMERICAN INDIAN/ALASKA NATIVE | 10 | 43 | 2 | 709 |
| HISPANIC/LATINO - SALVADORAN | 34 | 58 | 0 | 637 |
| HISPANIC/LATINO - MEXICAN | 17 | 53 | 2 | 439 |
| HISPANIC/LATINO - COLUMBIAN | 15 | 46 | 3 | 442 |
| SOUTH AMERICAN | 9 | 46 | 0 | 388 |
| HISPANIC/LATINO - CUBAN | 6 | 22 | 0 | 400 |
| HISPANIC/LATINO - HONDURAN | 9 | 44 | 1 | 371 |
| MULTIPLE RACE/ETHNICITY | 4 | 24 | 0 | 390 |
| HISPANIC/LATINO - CENTRAL AMERICAN | 27 | 43 | 2 | 310 |
| ASIAN - KOREAN | 1 | 21 | 1 | 350 |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 4 | 23 | 0 | 290 |

Shares (analyzable strata only):

| race | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| WHITE | 82.4 | 81.5–83.2 | 1.7 | yes | 87.6 | 86.5–88.8 | 2.3 | yes | -0.031 | 82.4 (81.5–83.2) |
| BLACK/AFRICAN AMERICAN | 85.7 | 84.1–87.1 | 3.0 | yes | 84.4 | 80.6–87.8 | 7.2 | yes | -0.112 | 85.7 (84.1–87.1) |
| OTHER | 79.5 | 75.5–82.7 | 7.2 | yes | 87.3 | 81.9–92.2 | 10.3 | yes | 0.064 | 79.5 (75.5–82.7) |
| UNKNOWN † | 84.9 | 81.8–87.8 | 5.9 | yes | 88.9 | 82.9–94.3 | 11.4 | yes | -0.08 | 85.0 (82.1–87.9) |
| WHITE - OTHER EUROPEAN | 79.0 | 74.7–83.0 | 8.3 | yes | 86.3 | 80.4–91.7 | 11.3 | yes | 0.075 | 79.3 (74.8–83.2) |
| HISPANIC/LATINO - PUERTO RICAN | 72.6 | 68.0–76.5 | 8.5 | yes | 92.2 | 88.6–95.9 | 7.3 | yes | 0.232 | 72.6 (68.0–76.5) |
| HISPANIC OR LATINO | 84.9 | 80.6–88.8 | 8.2 | yes | 85.2 | 77.4–92.3 | 14.9 | yes | -0.082 | 85.1 (80.7–88.9) |
| ASIAN - CHINESE | 84.8 | 80.3–88.6 | 8.3 | yes | 85.9 | 77.2–92.7 | 15.4 | yes | -0.078 | 84.8 (80.3–88.6) |
| WHITE - RUSSIAN | 72.5 | 63.1–82.5 | 19.4 | yes | 88.0 | 77.3–95.2 | 17.9 | yes | 0.228 | 72.5 (63.1–82.5) |
| ASIAN | 84.2 | 78.8–89.2 | 10.4 | yes | 84.5 | 73.5–93.7 | 20.2 | no — too wide | -0.062 | 84.2 (78.8–89.2) |
| BLACK/CAPE VERDEAN | 80.5 | 73.9–86.8 | 12.9 | yes | 93.4 | 86.5–98.8 | 12.4 | yes | 0.038 | 80.5 (73.9–86.8) |
| HISPANIC/LATINO - DOMINICAN | 78.5 | 73.0–84.0 | 11.0 | yes | 85.9 | 77.3–91.9 | 14.6 | yes | 0.087 | 78.5 (73.0–84.0) |
| BLACK/CARIBBEAN ISLAND | 86.3 | 80.4–91.5 | 11.1 | yes | 88.9 | 69.2–100.0 | 30.8 | no — too wide | -0.121 | 86.3 (80.4–91.5) |
| BLACK/AFRICAN | 78.6 | 69.6–87.7 | 18.1 | yes | 89.3 | 75.9–100.0 | 24.1 | no — too wide | 0.083 | 78.6 (69.6–87.7) |
| PATIENT DECLINED TO ANSWER † | 78.7 | 68.9–86.2 | 17.4 | yes | 76.0 | 58.7–91.7 | 33.0 | no — too wide | 0.083 | 78.7 (68.9–86.2) |
| UNABLE TO OBTAIN † | 85.9 | 77.4–93.6 | 16.2 | yes | 81.8 | 58.3–100.0 | 41.7 | no — too wide | -0.109 | 85.9 (77.4–93.6) |
| PORTUGUESE | 68.0 | 51.3–85.6 | 34.3 | no — too wide | 88.9 | 75.0–96.0 | 21.0 | no — too wide | 0.328 | 68.0 (51.3–85.6) |
| ASIAN - SOUTH EAST ASIAN | 88.4 | 80.2–94.7 | 14.4 | yes | 93.8 | 77.8–100.0 | 22.2 | no — too wide | -0.183 | 88.4 (80.2–94.7) |
| HISPANIC/LATINO - GUATEMALAN | 71.5 | 59.5–82.4 | 23.0 | no — too wide | 93.2 | 83.7–98.5 | 14.8 | yes | 0.251 | 71.5 (59.5–82.4) |
| WHITE - EASTERN EUROPEAN | 81.8 | 72.3–90.9 | 18.6 | yes | 85.7 | 65.6–100.0 | 34.4 | no — too wide | 0.003 | 81.8 (72.3–90.9) |
| ASIAN - ASIAN INDIAN | 85.3 | 77.8–92.4 | 14.6 | yes | 82.4 | 55.6–100.0 | 44.4 | no — too wide | -0.09 | 85.3 (77.8–92.4) |
| WHITE - BRAZILIAN | 76.7 | 62.1–88.3 | 26.2 | no — too wide | 80.8 | 60.0–96.8 | 36.8 | no — too wide | 0.131 | 76.7 (62.1–88.3) |
| AMERICAN INDIAN/ALASKA NATIVE | 81.1 | 62.8–98.4 | 35.6 | no — too wide | 83.3 | 20.0–100.0 | 80.0 | no — too wide | 0.021 | 81.1 (62.8–98.4) |
| HISPANIC/LATINO - SALVADORAN | 63.0 | 49.2–80.3 | 31.1 | no — too wide | 100.0 | 100.0–100.0 | 0.0 | yes | 0.434 | 63.0 (49.2–80.3) |
| HISPANIC/LATINO - MEXICAN | 75.7 | 64.4–83.8 | 19.4 | yes | 89.5 | 79.1–100.0 | 20.9 | no — too wide | 0.153 | 75.7 (64.4–83.8) |
| HISPANIC/LATINO - COLUMBIAN | 75.4 | 62.4–87.2 | 24.8 | no — too wide | 83.3 | 59.4–100.0 | 40.6 | no — too wide | 0.16 | 75.4 (62.4–87.2) |
| SOUTH AMERICAN | 83.6 | 69.9–94.5 | 24.6 | no — too wide | — | — | — | n/a | -0.045 | 83.6 (69.9–94.5) |
| HISPANIC/LATINO - CUBAN | 78.6 | 64.2–92.9 | 28.6 | no — too wide | — | — | — | n/a | 0.085 | 78.6 (64.2–92.9) |
| HISPANIC/LATINO - HONDURAN | 83.0 | 66.1–97.5 | 31.4 | no — too wide | — | — | — | n/a | -0.029 | 83.0 (66.1–97.5) |
| MULTIPLE RACE/ETHNICITY | 85.7 | 68.8–100.0 | 31.2 | no — too wide | — | — | — | n/a | -0.103 | 85.7 (68.8–100.0) |
| HISPANIC/LATINO - CENTRAL AMERICAN | 61.4 | 49.6–80.8 | 31.3 | no — too wide | 93.1 | 76.7–100.0 | 23.3 | no — too wide | 0.469 | 61.4 (49.6–80.8) |
| ASIAN - KOREAN | 95.5 | 82.1–100.0 | 17.9 | yes | — | — | — | n/a | -0.437 | 95.5 (82.1–100.0) |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 85.2 | 66.1–100.0 | 33.9 | no — too wide | — | — | — | n/a | -0.088 | 85.2 (66.1–100.0) |

Mechanism measures (all admissions in the stratum):

| race | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |
| --- | --: | --: | --: | --: | --: | --: | --: |
| WHITE | 240,958 | 40.4 | 7.7 | 7.8 | 5.6 | 36.9 | 2.8 |
| BLACK/AFRICAN AMERICAN | 49,641 | 35.2 | 7.9 | 6.8 | 5.4 | 35.4 | 2.4 |
| OTHER | 12,528 | 39.3 | 8.8 | 7.6 | 5.9 | 34.7 | 3.4 |
| UNKNOWN | 9,726 | 56.1 | 18.9 | 16.4 | 10.5 | 30.6 | 1.9 |
| WHITE - OTHER EUROPEAN | 7,126 | 41.0 | 7.3 | 6.6 | 4.7 | 40.4 | 0.5 |
| HISPANIC/LATINO - PUERTO RICAN | 6,820 | 39.7 | 8.2 | 6.6 | 4.6 | 43.9 | 2.7 |
| HISPANIC OR LATINO | 6,169 | 33.7 | 6.4 | 6.7 | 5.3 | 40.1 | 6.8 |
| ASIAN - CHINESE | 4,693 | 42.0 | 6.4 | 6.4 | 4.5 | 46.7 | 2.1 |
| WHITE - RUSSIAN | 4,660 | 34.0 | 6.9 | 5.8 | 4.8 | 35.4 | 0.8 |
| ASIAN | 4,650 | 40.3 | 7.3 | 7.7 | 5.9 | 38.7 | 5.8 |
| BLACK/CAPE VERDEAN | 3,987 | 37.9 | 7.0 | 7.1 | 5.3 | 40.4 | 0.8 |
| HISPANIC/LATINO - DOMINICAN | 3,610 | 38.9 | 8.4 | 6.4 | 4.5 | 39.5 | 1.9 |
| BLACK/CARIBBEAN ISLAND | 2,402 | 42.9 | 9.5 | 8.7 | 7.0 | 37.8 | 1.6 |
| BLACK/AFRICAN | 2,015 | 39.4 | 9.4 | 8.0 | 6.2 | 32.6 | 3.5 |
| PATIENT DECLINED TO ANSWER | 1,523 | 36.6 | 8.5 | 8.3 | 5.8 | 32.5 | 2.8 |
| UNABLE TO OBTAIN | 1,392 | 54.1 | 18.1 | 15.4 | 11.2 | 30.1 | 5.2 |
| PORTUGUESE | 1,383 | 54.3 | 7.3 | 7.0 | 4.7 | 50.6 | 1.3 |
| ASIAN - SOUTH EAST ASIAN | 1,262 | 53.6 | 7.8 | 7.5 | 5.4 | 50.4 | 2.4 |
| HISPANIC/LATINO - GUATEMALAN | 1,179 | 41.2 | 8.8 | 5.7 | 3.9 | 46.4 | 5.2 |
| WHITE - EASTERN EUROPEAN | 1,045 | 36.7 | 7.6 | 6.0 | 4.8 | 39.8 | 1.9 |
| ASIAN - ASIAN INDIAN | 977 | 44.6 | 7.2 | 9.3 | 5.1 | 35.3 | 3.3 |
| WHITE - BRAZILIAN | 950 | 42.7 | 5.5 | 5.8 | 3.9 | 48.3 | 3.8 |
| AMERICAN INDIAN/ALASKA NATIVE | 764 | 47.4 | 7.3 | 7.7 | 5.1 | 41.0 | 2.7 |
| HISPANIC/LATINO - SALVADORAN | 729 | 38.7 | 7.1 | 7.3 | 5.9 | 47.5 | 4.1 |
| HISPANIC/LATINO - MEXICAN | 511 | 37.0 | 7.2 | 5.3 | 3.7 | 37.4 | 7.6 |
| HISPANIC/LATINO - COLUMBIAN | 506 | 35.2 | 8.3 | 5.9 | 4.3 | 38.1 | 3.2 |
| SOUTH AMERICAN | 443 | 32.7 | 7.0 | 5.4 | 4.5 | 35.2 | 2.7 |
| HISPANIC/LATINO - CUBAN | 428 | 36.9 | 7.5 | 7.2 | 5.1 | 39.0 | 2.1 |
| HISPANIC/LATINO - HONDURAN | 425 | 37.4 | 6.1 | 7.5 | 5.4 | 41.4 | 3.1 |
| MULTIPLE RACE/ETHNICITY | 418 | 36.4 | 5.7 | 7.2 | 5.7 | 32.1 | 10.0 |
| HISPANIC/LATINO - CENTRAL AMERICAN | 382 | 40.8 | 7.9 | 3.4 | 2.6 | 49.7 | 3.7 |
| ASIAN - KOREAN | 373 | 46.6 | 7.5 | 7.8 | 5.9 | 44.5 | 4.3 |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 317 | 47.9 | 12.0 | 12.0 | 9.8 | 31.5 | 5.0 |

