# Aim 1c level 1 — by insurance (run_2026-09-19)

Source: `docs/run_2026-09-19/results/aim1c_level1.json`.

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
| Other | 122 | 724 | 13 | 9,111 |
| (missing) | 30 | 207 | 4 | 4,952 |
| No charge | 0 | 6 | 0 | 67 |

Shares (analyzable strata only):

| insurance | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |
| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |
| Medicare | 82.2 | 80.9–83.4 | 2.5 | yes | 85.2 | 83.6–87.0 | 3.4 | yes | -0.011 | 82.2 (80.9–83.4) |
| Private | 80.2 | 79.1–81.3 | 2.2 | yes | 89.1 | 87.7–90.5 | 2.8 | yes | 0.07 | 80.3 (79.2–81.3) |
| Medicaid | 83.6 | 82.4–84.9 | 2.5 | yes | 88.8 | 87.0–90.6 | 3.6 | yes | -0.057 | 83.7 (82.4–84.9) |
| Other | 85.6 | 82.9–88.2 | 5.3 | yes | 90.4 | 84.7–95.1 | 10.4 | yes | -0.102 | 85.7 (82.9–88.3) |
| (missing) | 87.3 | 82.3–91.5 | 9.3 | yes | 88.2 | 77.1–97.6 | 20.5 | no — too wide | -0.152 | 87.3 (82.3–91.5) |
| No charge | not analyzable | | | | not analyzable | | | | | |

Mechanism measures (all admissions in the stratum):

| insurance | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |
| --- | --: | --: | --: | --: | --: | --: | --: |
| Medicare | 180,507 | 40.8 | 9.0 | 8.2 | 6.2 | 35.7 | 0.7 |
| Private | 115,222 | 38.1 | 6.8 | 7.6 | 5.2 | 38.4 | 4.2 |
| Medicaid | 63,027 | 42.1 | 7.2 | 6.8 | 4.6 | 39.4 | 3.8 |
| Other | 9,970 | 39.7 | 8.4 | 8.4 | 6.2 | 36.5 | 5.7 |
| (missing) | 5,193 | 32.1 | 9.1 | 9.5 | 7.7 | 28.6 | 20.4 |
| No charge | 73 | 35.6 | 6.8 | 8.2 | 8.2 | 35.6 | 9.6 |

