# Aim 1c, level 1 — equity of recovery at the computable stage (run_2026-09-19)

Produced by `scripts/run0919_aim1c_level1.py`; every number is read from `docs/run_2026-09-19/results/aim1c_level1.json`. Pre-specification: `docs/analysis_plan_prespecified.md` (H1c; amendment g). Definition (b), v1.1.0, −365/+30 outpatient window.

**What is measured.** Recovery share = B ÷ (A + B): among note-positive admissions, the share with no MASLD code. Corroboration share = A ÷ (A + C): among code-positive admissions, the share whose notes also document steatosis. Both are computable-stage quantities about *documentation and coding*, not adjudicated disease. 95% CIs are subject-cluster bootstraps (500 replicates; a subject's admissions are resampled together because one person can contribute several). Floors: no recovery share where B < 11; no corroboration share where A + C < 11; such strata are declared non-analyzable, not merged. A CI wider than 20 percentage points is marked as too wide to support a claim (an analyst threshold, stated here so it can be argued with). No p-values. The SMD column is the one-versus-rest standardized difference in the coding rate among note-positive admissions (A ÷ (A + B)), a descriptive contrast.

**Small counts.** Counts from 1 to 10 appear as <11. Where a stratum's n or a column's overall total would give such a count back by subtraction, a second cell is shown as *withheld*, and shares computed from a hidden cell are *withheld* too (`scripts/public_counts.py`).

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
| ASIAN | withheld | 262 | <11 | 4,330 |
| BLACK/CAPE VERDEAN | withheld | 235 | <11 | 3,691 |
| HISPANIC/LATINO - DOMINICAN | 79 | 289 | 13 | 3,229 |
| BLACK/CARIBBEAN ISLAND | withheld | 101 | <11 | 2,283 |
| BLACK/AFRICAN | withheld | 92 | <11 | 1,895 |
| PATIENT DECLINED TO ANSWER † | withheld | 70 | <11 | 1,428 |
| UNABLE TO OBTAIN † | <11 | 55 | <11 | 1,326 |
| PORTUGUESE | withheld | 119 | <11 | 1,201 |
| ASIAN - SOUTH EAST ASIAN | withheld | 114 | <11 | 1,132 |
| HISPANIC/LATINO - GUATEMALAN | withheld | 138 | <11 | 982 |
| WHITE - EASTERN EUROPEAN | withheld | 54 | <11 | 977 |
| ASIAN - ASIAN INDIAN | withheld | 81 | <11 | 879 |
| WHITE - BRAZILIAN | withheld | 69 | <11 | 855 |
| AMERICAN INDIAN/ALASKA NATIVE | <11 | 43 | <11 | 709 |
| HISPANIC/LATINO - SALVADORAN | 34 | 58 | 0 | 637 |
| HISPANIC/LATINO - MEXICAN | withheld | 53 | <11 | 439 |
| HISPANIC/LATINO - COLUMBIAN | withheld | 46 | <11 | 442 |
| SOUTH AMERICAN | <11 | withheld | 0 | 388 |
| HISPANIC/LATINO - CUBAN | <11 | withheld | 0 | 400 |
| HISPANIC/LATINO - HONDURAN | <11 | withheld | <11 | 371 |
| MULTIPLE RACE/ETHNICITY | <11 | withheld | 0 | 390 |
| HISPANIC/LATINO - CENTRAL AMERICAN | withheld | 43 | <11 | 310 |
| ASIAN - KOREAN | <11 | withheld | <11 | 350 |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | <11 | withheld | 0 | 290 |

Shares (analyzable strata only):

| race | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| WHITE | 82.4 | 81.5–83.2 | 1.7 | yes | 87.6 | 86.5–88.8 | 2.3 | yes | -0.031 | 82.4 (81.5–83.2) |
| BLACK/AFRICAN AMERICAN | 85.7 | 84.1–87.1 | 3.0 | yes | 84.4 | 80.6–87.8 | 7.2 | yes | -0.112 | 85.7 (84.1–87.1) |
| OTHER | 79.5 | 75.5–82.7 | 7.2 | yes | 87.3 | 81.9–92.2 | 10.3 | yes | 0.064 | 79.5 (75.5–82.7) |
| UNKNOWN † | 84.9 | 81.8–87.8 | 5.9 | yes | 88.9 | 82.9–94.3 | 11.4 | yes | -0.08 | 85.0 (82.1–87.9) |
| WHITE - OTHER EUROPEAN | 79.0 | 74.7–83.0 | 8.3 | yes | 86.3 | 80.4–91.7 | 11.3 | yes | 0.075 | withheld |
| HISPANIC/LATINO - PUERTO RICAN | 72.6 | 68.0–76.5 | 8.5 | yes | 92.2 | 88.6–95.9 | 7.3 | yes | 0.232 | 72.6 (68.0–76.5) |
| HISPANIC OR LATINO | 84.9 | 80.6–88.8 | 8.2 | yes | 85.2 | 77.4–92.3 | 14.9 | yes | -0.082 | withheld |
| ASIAN - CHINESE | 84.8 | 80.3–88.6 | 8.3 | yes | 85.9 | 77.2–92.7 | 15.4 | yes | -0.078 | 84.8 (80.3–88.6) |
| WHITE - RUSSIAN | 72.5 | 63.1–82.5 | 19.4 | yes | 88.0 | 77.3–95.2 | 17.9 | yes | 0.228 | 72.5 (63.1–82.5) |
| ASIAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| BLACK/CAPE VERDEAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - DOMINICAN | 78.5 | 73.0–84.0 | 11.0 | yes | 85.9 | 77.3–91.9 | 14.6 | yes | 0.087 | 78.5 (73.0–84.0) |
| BLACK/CARIBBEAN ISLAND | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| BLACK/AFRICAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| PATIENT DECLINED TO ANSWER † | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| UNABLE TO OBTAIN † | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| PORTUGUESE | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| ASIAN - SOUTH EAST ASIAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - GUATEMALAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| WHITE - EASTERN EUROPEAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| ASIAN - ASIAN INDIAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| WHITE - BRAZILIAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| AMERICAN INDIAN/ALASKA NATIVE | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - SALVADORAN | 63.0 | 49.2–80.3 | 31.1 | no — too wide | 100.0 | 100.0–100.0 | 0.0 | yes | 0.434 | 63.0 (49.2–80.3) |
| HISPANIC/LATINO - MEXICAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - COLUMBIAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| SOUTH AMERICAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - CUBAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - HONDURAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| MULTIPLE RACE/ETHNICITY | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| HISPANIC/LATINO - CENTRAL AMERICAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| ASIAN - KOREAN | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |

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

## By insurance

Cell counts first:

| insurance | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |
| --- | --: | --: | --: | --: |
| Medicare | 1,882 | 8,684 | 327 | 169,614 |
| Private | 2,006 | 8,136 | 245 | 104,835 |
| Medicaid | 987 | 5,042 | 124 | 56,874 |
| Other | withheld | 724 | withheld | 9,111 |
| (missing) | withheld | withheld | <11 | withheld |
| No charge | 0 | <11 | 0 | withheld |

Shares (analyzable strata only):

| insurance | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| Medicare | 82.2 | 80.9–83.4 | 2.5 | yes | 85.2 | 83.6–87.0 | 3.4 | yes | -0.011 | 82.2 (80.9–83.4) |
| Private | 80.2 | 79.1–81.3 | 2.2 | yes | 89.1 | 87.7–90.5 | 2.8 | yes | 0.07 | 80.3 (79.2–81.3) |
| Medicaid | 83.6 | 82.4–84.9 | 2.5 | yes | 88.8 | 87.0–90.6 | 3.6 | yes | -0.057 | 83.7 (82.4–84.9) |
| Other | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| (missing) | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| No charge | withheld | withheld | withheld | withheld | not analyzable |  |  |  | withheld | withheld |

Mechanism measures (all admissions in the stratum):

| insurance | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |
| --- | --: | --: | --: | --: | --: | --: | --: |
| Medicare | 180,507 | 40.8 | 9.0 | 8.2 | 6.2 | 35.7 | 0.7 |
| Private | 115,222 | 38.1 | 6.8 | 7.6 | 5.2 | 38.4 | 4.2 |
| Medicaid | 63,027 | 42.1 | 7.2 | 6.8 | 4.6 | 39.4 | 3.8 |
| Other | 9,970 | 39.7 | 8.4 | 8.4 | 6.2 | 36.5 | 5.7 |
| (missing) | 5,193 | 32.1 | 9.1 | 9.5 | 7.7 | 28.6 | 20.4 |
| No charge | 73 | 35.6 | 6.8 | 8.2 | 8.2 | 35.6 | 9.6 |

## By gender

Cell counts first:

| gender | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |
| --- | --: | --: | --: | --: |
| F | 2,494 | 10,724 | 374 | 177,622 |
| M | 2,533 | 12,075 | 339 | 167,831 |

Shares (analyzable strata only):

| gender | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| F | 81.1 | 80.1–82.0 | 1.9 | yes | 87.0 | 85.5–88.2 | 2.8 | yes | 0.04 | 81.2 (80.2–82.1) |
| M | 82.7 | 81.6–83.6 | 2.0 | yes | 88.2 | 86.9–89.5 | 2.7 | yes | -0.04 | 82.7 (81.7–83.6) |

Mechanism measures (all admissions in the stratum):

| gender | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |
| --- | --: | --: | --: | --: | --: | --: | --: |
| F | 191,214 | 37.5 | 6.9 | 7.1 | 5.1 | 37.1 | 2.3 |
| M | 182,778 | 42.7 | 9.2 | 8.6 | 6.2 | 37.0 | 3.2 |

## By language

Cell counts first:

| language | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |
| --- | --: | --: | --: | --: |
| English | 4,428 | 20,342 | 629 | 310,810 |
| Spanish | 317 | 1,114 | 38 | 11,023 |
| Russian | 76 | 227 | 14 | 6,098 |
| Chinese | withheld | 381 | <11 | 4,559 |
| Kabuverdianu | withheld | 192 | <11 | 3,112 |
| Portuguese | withheld | 150 | <11 | 1,780 |
| Haitian | <11 | withheld | <11 | 1,637 |
| Other | withheld | 53 | <11 | 850 |
| Italian | 11 | 38 | 0 | 743 |
| Vietnamese | <11 | withheld | 0 | 715 |
| Modern Greek (1453-) | <11 | withheld | 0 | 695 |
| (missing) | <11 | withheld | <11 | 590 |
| Arabic | 0 | withheld | <11 | 442 |
| American Sign Language | <11 | withheld | <11 | 376 |
| Persian | <11 | withheld | <11 | 316 |
| Polish | <11 | withheld | <11 | 309 |
| Korean | <11 | withheld | <11 | 231 |
| Khmer | <11 | <11 | 0 | withheld |
| Thai | <11 | <11 | 0 | 178 |
| Amharic | <11 | <11 | 0 | 152 |
| French | 0 | <11 | 0 | withheld |
| Somali | 0 | <11 | 0 | withheld |
| Hindi | <11 | <11 | 0 | withheld |
| Japanese | 0 | 0 | 0 | 93 |
| Bengali | <11 | <11 | <11 | withheld |
| Armenian | <11 | 0 | 0 | withheld |

Shares (analyzable strata only):

| language | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| English | 82.1 | 81.4–82.9 | 1.5 | yes | 87.6 | 86.5–88.6 | 2.1 | yes | -0.044 | 82.2 (81.4–82.9) |
| Spanish | 77.8 | 74.4–80.8 | 6.5 | yes | 89.3 | 85.6–92.5 | 6.8 | yes | 0.108 | 77.9 (74.4–80.9) |
| Russian | 74.9 | 66.6–84.0 | 17.4 | yes | 84.4 | 70.9–94.4 | 23.6 | no — too wide | 0.173 | 74.9 (66.6–84.0) |
| Chinese | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Kabuverdianu | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Portuguese | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Haitian | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Other | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Italian | 77.6 | 64.3–88.9 | 24.6 | no — too wide | 100.0 | 100.0–100.0 | 0.0 | yes | 0.109 | 77.6 (64.3–88.9) |
| Vietnamese | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Modern Greek (1453-) | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| (missing) | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Arabic | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| American Sign Language | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Persian | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Polish | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Korean | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Khmer | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Thai | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Amharic | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| French | withheld | withheld | withheld | withheld | not analyzable |  |  |  | withheld | withheld |
| Somali | withheld | withheld | withheld | withheld | not analyzable |  |  |  | withheld | withheld |
| Hindi | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Japanese | not analyzable | | | | not analyzable | | | | | |
| Bengali | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |
| Armenian | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld | withheld |

Mechanism measures (all admissions in the stratum):

| language | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |
| --- | --: | --: | --: | --: | --: | --: | --: |
| English | 336,209 | 39.9 | 7.9 | 7.8 | 5.6 | 36.6 | 2.9 |
| Spanish | 12,492 | 39.9 | 9.7 | 7.8 | 5.8 | 41.8 | 2.7 |
| Russian | 6,415 | 32.7 | 6.9 | 6.6 | 5.7 | 34.8 | 0.6 |
| Chinese | 5,005 | 43.5 | 6.6 | 6.7 | 5.1 | 48.3 | 1.8 |
| Kabuverdianu | 3,363 | 37.1 | 8.6 | 8.1 | 6.5 | 38.2 | 0.4 |
| Portuguese | 1,966 | 49.1 | 9.6 | 9.4 | 6.6 | 43.5 | 2.2 |
| Haitian | 1,694 | 45.3 | 12.8 | 10.7 | 8.7 | 37.0 | 0.7 |
| Other | 916 | 47.7 | 11.2 | 10.3 | 8.7 | 37.9 | 2.1 |
| Italian | 792 | 44.1 | 8.0 | 6.4 | 4.4 | 38.4 | 0.1 |
| Vietnamese | 789 | 59.1 | 10.5 | 8.4 | 6.3 | 52.0 | 0.3 |
| Modern Greek (1453-) | 717 | 40.9 | 8.9 | 8.4 | 6.6 | 38.6 | 0.4 |
| (missing) | 624 | 54.8 | 14.3 | 15.7 | 10.4 | 29.2 | 2.6 |
| Arabic | 473 | 48.8 | 9.7 | 8.7 | 5.3 | 44.6 | 1.7 |
| American Sign Language | 398 | 40.5 | 6.0 | 5.8 | 2.8 | 44.2 | 1.0 |
| Persian | 335 | 38.2 | 8.4 | 7.2 | 5.7 | 40.0 | 0.0 |
| Polish | 333 | 46.5 | 7.5 | 7.5 | 6.3 | 39.3 | 0.9 |
| Korean | 248 | 46.8 | 8.5 | 7.7 | 6.0 | 44.4 | 3.6 |
| Khmer | 203 | 65.0 | 12.3 | 12.8 | 10.3 | 53.2 | 1.0 |
| Thai | 189 | 39.7 | 7.4 | 6.3 | 5.3 | 40.7 | 2.1 |
| Amharic | 163 | 33.7 | 12.9 | 9.2 | 8.0 | 43.6 | 1.2 |
| French | 156 | 44.2 | 9.0 | 9.0 | 7.1 | 28.2 | 3.8 |
| Somali | 134 | 32.1 | 7.5 | 5.2 | 5.2 | 50.0 | 0.0 |
| Hindi | 124 | 52.4 | 12.1 | 14.5 | 10.5 | 28.2 | 1.6 |
| Japanese | 93 | 28.0 | 1.1 | 3.2 | 3.2 | 32.3 | 7.5 |
| Bengali | 86 | 45.3 | 12.8 | 10.5 | 5.8 | 40.7 | 0.0 |
| Armenian | 75 | 40.0 | 14.7 | 5.3 | 6.7 | 28.0 | 1.3 |

## By age_band

Cell counts first:

| age_band | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |
| --- | --: | --: | --: | --: |
| 75-88 | 503 | 2,393 | 106 | 73,714 |
| 55-64 | 1,365 | 6,384 | 202 | 67,657 |
| 65-74 | 1,200 | 4,902 | 162 | 67,564 |
| 40-54 | 1,331 | 6,225 | 162 | 65,872 |
| 18-39 | 583 | 2,666 | 64 | 50,280 |
| 89+ | 45 | 229 | 17 | 20,366 |

Shares (analyzable strata only):

| age_band | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| 75-88 | 82.6 | 80.3–84.6 | 4.3 | yes | 82.6 | 79.2–85.9 | 6.7 | yes | -0.02 | 82.7 (80.3–84.7) |
| 55-64 | 82.4 | 81.0–83.8 | 2.7 | yes | 87.1 | 85.0–88.9 | 3.9 | yes | -0.016 | 82.4 (81.0–83.8) |
| 65-74 | 80.3 | 78.6–81.8 | 3.2 | yes | 88.1 | 86.0–90.3 | 4.3 | yes | 0.053 | 80.4 (78.6–81.8) |
| 40-54 | 82.4 | 81.1–83.7 | 2.6 | yes | 89.1 | 87.4–90.8 | 3.4 | yes | -0.016 | 82.4 (81.1–83.7) |
| 18-39 | 82.1 | 80.3–83.8 | 3.5 | yes | 90.1 | 87.5–92.2 | 4.7 | yes | -0.004 | 82.2 (80.4–83.8) |
| 89+ | 83.6 | 76.6–89.7 | 13.2 | yes | 72.6 | 56.1–88.1 | 32.0 | no — too wide | -0.044 | 83.6 (76.6–89.7) |

Mechanism measures (all admissions in the stratum):

| age_band | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |
| --- | --: | --: | --: | --: | --: | --: | --: |
| 75-88 | 76,716 | 39.0 | 9.7 | 8.7 | 7.0 | 33.7 | 0.5 |
| 55-64 | 75,608 | 43.1 | 8.6 | 8.2 | 5.7 | 41.0 | 1.6 |
| 65-74 | 73,828 | 42.3 | 9.8 | 8.5 | 6.3 | 38.4 | 0.7 |
| 40-54 | 73,590 | 40.2 | 6.9 | 7.5 | 4.9 | 39.5 | 3.9 |
| 18-39 | 53,593 | 36.2 | 4.2 | 5.6 | 3.4 | 34.2 | 9.7 |
| 89+ | 20,657 | 33.7 | 7.2 | 7.2 | 6.5 | 28.6 | 0.6 |

## EXPLORATORY adjusted model (GEE) — among note-positive admissions, outcome = code-positive

**Exploratory.** Covariates fixed before fitting (amendment g): race, insurance, sex, age band, admission type, ICD version of the admission, note source (discharge / inpatient radiology / outpatient radiology). GEE with a binomial link, exchangeable working correlation, clustered on subject. Diagnosis count and laboratory availability are deliberately not adjusted for: they are the proposed mechanism. Fit: all categories; n = 27826. Reference levels: {'race': 'WHITE', 'insurance': 'Medicare', 'gender': 'M', 'age_band': '55-64', 'admission_type': 'EW EMER.', 'icd_era': 'ICD-9 only'}.

| term | adjusted OR | 95% CI |
| --- | --: | --- |
| race[T.BLACK/AFRICAN AMERICAN] | 0.901 | 0.782–1.037 |
| race[T.OTHER] | 1.161 | 0.947–1.423 |
| race[T.HISPANIC/LATINO - PUERTO RICAN] | 1.603 | 1.308–1.964 |
| race[T.WHITE - OTHER EUROPEAN] | 1.238 | 0.979–1.567 |
| race[T.HISPANIC OR LATINO] | 1.111 | 0.807–1.531 |
| race[T.UNKNOWN] | 0.821 | 0.639–1.055 |
| race[T.ASIAN - CHINESE] | 1.048 | 0.751–1.461 |
| race[T.HISPANIC/LATINO - DOMINICAN] | 1.272 | 0.88–1.84 |
| race[T.ASIAN] | 0.969 | 0.679–1.381 |
| race[T.WHITE - RUSSIAN] | 1.36 | 0.889–2.08 |
| race[T.BLACK/CAPE VERDEAN] | 1.245 | 0.892–1.737 |
| race[T.HISPANIC/LATINO - GUATEMALAN] | 2.039 | 1.276–3.257 |
| race[T.PORTUGUESE] | 1.029 | 0.62–1.709 |
| race[T.ASIAN - SOUTH EAST ASIAN] | 1.02 | 0.532–1.955 |
| race[T.BLACK/AFRICAN] | 1.491 | 0.889–2.501 |
| race[T.BLACK/CARIBBEAN ISLAND] | 0.58 | 0.318–1.057 |
| race[T.ASIAN - ASIAN INDIAN] | 0.844 | 0.47–1.518 |
| race[T.HISPANIC/LATINO - SALVADORAN] | 2.081 | 1.192–3.633 |
| race[T.WHITE - BRAZILIAN] | 1.878 | 0.962–3.667 |
| race[T.PATIENT DECLINED TO ANSWER] | 1.359 | 0.779–2.373 |
| race[T.HISPANIC/LATINO - CENTRAL AMERICAN] | 1.32 | 0.543–3.212 |
| race[T.HISPANIC/LATINO - MEXICAN] | 1.357 | 0.68–2.707 |
| race[T.WHITE - EASTERN EUROPEAN] | 1.095 | 0.51–2.351 |
| race[T.UNABLE TO OBTAIN] | 1.033 | 0.5–2.136 |
| race[T.HISPANIC/LATINO - COLUMBIAN] | 1.424 | 0.625–3.245 |
| race[T.SOUTH AMERICAN] | 0.559 | 0.216–1.446 |
| race[T.HISPANIC/LATINO - HONDURAN] | 1.201 | 0.426–3.388 |
| race[T.AMERICAN INDIAN/ALASKA NATIVE] | 0.523 | 0.105–2.619 |
| race[T.MULTIPLE RACE/ETHNICITY] | 0.653 | 0.104–4.099 |
| race[T.HISPANIC/LATINO - CUBAN] | 0.919 | 0.39–2.165 |
| race[T.NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER] | 0.767 | 0.229–2.567 |
| race[T.ASIAN - KOREAN] | 0.548 | 0.076–3.929 |
| insurance[T.Private] | 1.351 | 1.206–1.515 |
| insurance[T.Medicaid] | 1.082 | 0.945–1.238 |
| insurance[T.Other] | 0.972 | 0.754–1.252 |
| insurance[T.(missing)] | 1.005 | 0.648–1.56 |
| insurance[T.No charge] | 0.0 | 0.0–0.0 |
| gender[T.F] | 1.04 | 0.959–1.128 |
| age_band[T.40-54] | 1.002 | 0.9–1.116 |
| age_band[T.65-74] | 1.208 | 1.06–1.378 |
| age_band[T.18-39] | 1.059 | 0.927–1.209 |
| age_band[T.75-88] | 1.104 | 0.933–1.307 |
| age_band[T.89+] | 1.22 | 0.797–1.868 |
| admission_type[T.OBSERVATION ADMIT] | 0.993 | 0.892–1.106 |
| admission_type[T.EU OBSERVATION] | 1.066 | 0.934–1.216 |
| admission_type[T.SURGICAL SAME DAY ADMISSION] | 2.906 | 2.561–3.298 |
| admission_type[T.URGENT] | 0.934 | 0.807–1.083 |
| admission_type[T.DIRECT EMER.] | 1.071 | 0.904–1.27 |
| admission_type[T.DIRECT OBSERVATION] | 1.223 | 1.003–1.491 |
| admission_type[T.ELECTIVE] | 1.768 | 1.397–2.238 |
| admission_type[T.AMBULATORY OBSERVATION] | 1.512 | 1.124–2.034 |
| icd_era[T.ICD-10 only] | 1.403 | 1.279–1.54 |
| src_dc | 16.748 | 14.649–19.147 |
| src_rad_inp | 0.778 | 0.718–0.844 |
| src_rad_out | 1.306 | 1.18–1.446 |

*Exploratory adjusted odds ratios describe association in the computable data; they are not estimates of adjudicated under-coding by group.*
