# Aim 1c level 1 with the LLM note phenotype

> **Exploratory (analysis-plan amendment i, committed before any of these stratum results were computed).** Computable stage only: nothing here is validated against chart review. Numbers are written by `scripts/aim1c_llm_level1.py` into `docs/run_2026-10-27/results/aim1c_llm_level1.json`.

Scope: the dev/test notes subsample (29,980 admissions), a simple random sample of dev/test subjects. LLM phenotype: `docs/llm_review_protocol.md` (v4). Percentages with 95% subject-cluster bootstrap intervals (500 replicates).

**Reading the tables.** Only each stratum's admission count is shown, never the count behind a percentage. — means withheld (the count or its complement is 1–10, or the denominator is under 11). † means the interval is wider than 20 percentage points, so no claim is made. * marks a category that describes the encounter rather than the person.

## Recovery share (E1): % of note-positive admissions with no MASLD code

**overall**

| Stratum | Admissions | Rule | LLM | Either | LLM − rule (pp) |
| --- | --: | --: | --: | --: | --: |
| all | 29,980 | 79.7 (77.3–82.2) | 81.1 (78.9–83.4) | 83.1 (81.0–85.1) | 1.4 (0.5–2.2) |

**race**

| Stratum | Admissions | Rule | LLM | Either | LLM − rule (pp) |
| --- | --: | --: | --: | --: | --: |
| WHITE | 19,569 | 79.7 (76.4–82.8) | 81.5 (78.6–84.3) | 83.4 (80.7–86.1) | 1.8 (0.8–2.9) |
| BLACK/AFRICAN AMERICAN | 3,767 | 83.7 (74.7–90.8) | 83.2 (74.1–90.5) | 85.8 (78.1–91.8) | -0.5 (-3.1–2.2) |
| OTHER | 953 | 79.5 (65.9–89.6) † | 76.2 (64.2–87.6) † | 81.2 (68.5–91.0) † | -3.3 (-8.4–1.2) |
| UNKNOWN * | 779 | — | — | — | — |
| WHITE - OTHER EUROPEAN | 585 | — | — | — | — |
| HISPANIC/LATINO - PUERTO RICAN | 515 | 75.0 (56.9–88.9) † | 79.6 (62.9–91.4) † | 80.2 (64.2–91.8) † | 4.6 (1.2–9.9) |
| HISPANIC OR LATINO | 448 | — | — | — | — |
| ASIAN - CHINESE | 414 | 77.1 (63.8–92.3) † | 80.7 (67.8–93.8) † | 81.0 (68.1–93.9) † | 3.6 (0.9–7.1) |
| BLACK/CAPE VERDEAN | 390 | — | — | — | — |
| HISPANIC/LATINO - DOMINICAN | 370 | — | — | — | — |
| ASIAN | 366 | — | — | — | — |
| WHITE - RUSSIAN | 362 | — | — | — | — |
| BLACK/CARIBBEAN ISLAND | 189 | — | — | — | — |
| BLACK/AFRICAN | 134 | — | — | — | — |
| PATIENT DECLINED TO ANSWER * | 124 | — | — | — | — |
| PORTUGUESE | 110 | — | — | — | — |
| UNABLE TO OBTAIN * | 104 | — | — | — | — |
| ASIAN - SOUTH EAST ASIAN | 83 | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 0.0 (0.0–0.0) |
| WHITE - BRAZILIAN | 82 | — | — | — | — |
| WHITE - EASTERN EUROPEAN | 78 | — | — | — | — |
| HISPANIC/LATINO - SALVADORAN | 73 | — | — | — | — |
| ASIAN - ASIAN INDIAN | 67 | — | — | — | — |
| HISPANIC/LATINO - MEXICAN | 55 | — | — | — | — |
| AMERICAN INDIAN/ALASKA NATIVE | 54 | — | — | — | — |
| HISPANIC/LATINO - CUBAN | 51 | — | — | — | — |
| HISPANIC/LATINO - COLUMBIAN | 50 | — | — | — | — |
| HISPANIC/LATINO - GUATEMALAN | 43 | — | — | — | — |
| SOUTH AMERICAN | 42 | — | — | — | — |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 38 | — | — | — | — |
| HISPANIC/LATINO - HONDURAN | 32 | — | — | — | — |
| ASIAN - KOREAN | 23 | — | — | — | — |
| HISPANIC/LATINO - CENTRAL AMERICAN | 16 | — | — | — | — |
| MULTIPLE RACE/ETHNICITY | 14 | — | — | — | — |

**insurance**

| Stratum | Admissions | Rule | LLM | Either | LLM − rule (pp) |
| --- | --: | --: | --: | --: | --: |
| Medicare | 14,512 | 80.8 (76.4–84.9) | 82.3 (78.6–86.0) | 84.7 (81.3–87.9) | 1.5 (-0.0–3.1) |
| Private | 9,443 | 76.4 (72.0–80.4) | 77.3 (72.8–81.3) | 79.6 (75.5–83.3) | 0.9 (-0.7–2.2) |
| Medicaid | 4,834 | 82.6 (77.8–86.9) | 84.6 (80.2–88.3) | 85.4 (81.3–89.0) | 2.0 (0.5–3.7) |
| Other | 766 | 83.3 (66.4–96.4) † | 84.1 (67.5–96.5) † | 85.5 (70.6–96.8) † | 0.7 (-1.2–3.4) |
| (missing) | 421 | — | — | — | — |

**sex**

| Stratum | Admissions | Rule | LLM | Either | LLM − rule (pp) |
| --- | --: | --: | --: | --: | --: |
| F | 15,394 | 81.4 (78.4–84.3) | 82.6 (79.5–85.4) | 84.6 (81.8–87.1) | 1.2 (0.1–2.3) |
| M | 14,586 | 78.0 (74.2–82.1) | 79.7 (75.9–83.3) | 81.6 (78.3–85.0) | 1.6 (0.3–2.9) |

**language**

| Stratum | Admissions | Rule | LLM | Either | LLM − rule (pp) |
| --- | --: | --: | --: | --: | --: |
| English | 26,885 | 79.2 (76.4–82.0) | 80.6 (78.0–83.1) | 82.7 (80.2–85.0) | 1.4 (0.5–2.4) |
| Spanish | 1,005 | 81.5 (73.4–88.4) | 81.8 (74.2–88.1) | 83.2 (76.5–89.5) | 0.4 (-2.5–3.0) |
| Russian | 507 | — | — | — | — |
| Chinese | 449 | — | — | — | — |
| Kabuverdianu | 268 | — | — | — | — |
| Haitian | 182 | — | — | — | — |
| Portuguese | 142 | — | — | — | — |
| American Sign Language | 104 | — | — | — | — |
| Italian | 64 | — | — | — | — |
| Other | 62 | — | — | — | — |
| Vietnamese | 62 | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 0.0 (0.0–0.0) |
| Modern Greek (1453-) | 43 | — | — | — | — |
| (missing) | 37 | — | — | — | — |
| Arabic | 37 | — | — | — | — |
| Persian | 35 | — | — | — | — |
| Polish | 26 | — | — | — | — |
| French | 21 | — | — | — | — |
| Bengali | 11 | — | — | — | — |
| Korean | 11 | — | — | — | — |

**age_band**

| Stratum | Admissions | Rule | LLM | Either | LLM − rule (pp) |
| --- | --: | --: | --: | --: | --: |
| 75-88 | 6,291 | 83.5 (77.0–90.1) | 86.0 (80.0–91.9) | 88.0 (82.5–93.1) | 2.5 (-0.1–5.8) |
| 55-64 | 6,062 | 78.5 (73.1–82.9) | 81.0 (76.2–85.1) | 82.6 (77.9–86.4) | 2.5 (0.8–4.2) |
| 65-74 | 5,906 | 76.5 (71.3–81.6) | 77.1 (72.3–82.2) | 79.8 (75.1–84.5) | 0.6 (-1.3–2.6) |
| 40-54 | 5,853 | 82.2 (77.6–86.3) | 82.5 (78.2–86.7) | 83.9 (79.9–87.8) | 0.3 (-0.9–1.5) |
| 18-39 | 4,129 | 82.0 (73.9–88.3) | 82.6 (75.2–88.4) | 85.1 (78.0–90.4) | 0.6 (-1.9–3.1) |
| 89+ | 1,739 | — | — | — | — |

## Rule–LLM discordance (E2): % of admissions positive by either method

**overall**

| Stratum | Admissions | Exactly one | LLM only | Rule only |
| --- | --: | --: | --: | --: |
| all | 29,980 | 29.9 (26.8–32.8) | 17.9 (15.4–20.4) | 12.0 (10.3–13.8) |

**race**

| Stratum | Admissions | Exactly one | LLM only | Rule only |
| --- | --: | --: | --: | --: |
| WHITE | 19,569 | 30.9 (26.7–34.8) | 19.3 (15.8–22.7) | 11.6 (9.4–14.0) |
| BLACK/AFRICAN AMERICAN | 3,767 | 33.5 (23.7–43.3) | 15.6 (8.0–23.7) | 17.9 (10.9–25.4) |
| OTHER | 953 | 30.0 (13.5–46.0) † | — | 21.2 (6.3–38.2) † |
| UNKNOWN * | 779 | 23.4 (13.2–33.3) † | — | — |
| WHITE - OTHER EUROPEAN | 585 | — | — | — |
| HISPANIC/LATINO - PUERTO RICAN | 515 | 23.8 (12.2–38.8) † | 20.8 (9.2–34.9) † | — |
| HISPANIC OR LATINO | 448 | 29.3 (12.1–45.2) † | 22.4 (6.7–37.4) † | — |
| ASIAN - CHINESE | 414 | 19.0 (7.8–34.2) † | — | — |
| BLACK/CAPE VERDEAN | 390 | — | — | — |
| HISPANIC/LATINO - DOMINICAN | 370 | — | — | — |
| ASIAN | 366 | 39.3 (18.9–57.1) † | — | — |
| WHITE - RUSSIAN | 362 | — | — | — |
| BLACK/CARIBBEAN ISLAND | 189 | — | — | — |
| BLACK/AFRICAN | 134 | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| PATIENT DECLINED TO ANSWER * | 124 | — | — | — |
| PORTUGUESE | 110 | — | — | — |
| UNABLE TO OBTAIN * | 104 | — | — | — |
| ASIAN - SOUTH EAST ASIAN | 83 | 53.8 (0.0–93.3) † | — | — |
| WHITE - BRAZILIAN | 82 | — | — | — |
| WHITE - EASTERN EUROPEAN | 78 | — | — | — |
| HISPANIC/LATINO - SALVADORAN | 73 | — | — | — |
| ASIAN - ASIAN INDIAN | 67 | — | — | — |
| HISPANIC/LATINO - MEXICAN | 55 | — | — | 0.0 (0.0–0.0) |
| AMERICAN INDIAN/ALASKA NATIVE | 54 | — | — | — |
| HISPANIC/LATINO - CUBAN | 51 | — | — | — |
| HISPANIC/LATINO - COLUMBIAN | 50 | — | — | — |
| HISPANIC/LATINO - GUATEMALAN | 43 | — | — | 0.0 (0.0–0.0) |
| SOUTH AMERICAN | 42 | — | — | — |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 38 | — | — | — |
| HISPANIC/LATINO - HONDURAN | 32 | — | — | — |
| ASIAN - KOREAN | 23 | — | — | — |
| HISPANIC/LATINO - CENTRAL AMERICAN | 16 | — | — | — |
| MULTIPLE RACE/ETHNICITY | 14 | — | — | — |

**insurance**

| Stratum | Admissions | Exactly one | LLM only | Rule only |
| --- | --: | --: | --: | --: |
| Medicare | 14,512 | 36.3 (31.5–41.3) | 20.6 (16.2–25.1) | 15.7 (12.3–19.5) |
| Private | 9,443 | 26.1 (21.7–30.5) | 15.2 (11.5–18.6) | 10.9 (8.2–14.3) |
| Medicaid | 4,834 | 25.8 (20.3–31.6) | 18.2 (12.5–23.7) | 7.7 (4.9–10.5) |
| Other | 766 | 22.4 (12.7–34.6) † | — | — |
| (missing) | 421 | — | — | — |

**sex**

| Stratum | Admissions | Exactly one | LLM only | Rule only |
| --- | --: | --: | --: | --: |
| F | 15,394 | 30.9 (26.4–35.5) | 17.8 (14.1–21.7) | 13.0 (10.6–15.6) |
| M | 14,586 | 29.0 (24.7–32.8) | 17.9 (14.8–21.3) | 11.0 (8.4–13.8) |

**language**

| Stratum | Admissions | Exactly one | LLM only | Rule only |
| --- | --: | --: | --: | --: |
| English | 26,885 | 29.8 (26.7–32.9) | 18.0 (15.2–20.8) | 11.9 (10.0–13.9) |
| Spanish | 1,005 | 21.0 (11.9–31.2) | 13.3 (6.4–21.1) | 7.7 (1.7–16.8) |
| Russian | 507 | — | — | — |
| Chinese | 449 | 22.4 (9.3–38.1) † | 20.7 (7.7–35.7) † | — |
| Kabuverdianu | 268 | — | — | — |
| Haitian | 182 | — | — | — |
| Portuguese | 142 | — | — | — |
| American Sign Language | 104 | — | — | — |
| Italian | 64 | — | — | — |
| Other | 62 | — | — | — |
| Vietnamese | 62 | 57.7 (0.0–100.0) † | — | — |
| Modern Greek (1453-) | 43 | — | — | — |
| (missing) | 37 | — | — | — |
| Arabic | 37 | — | — | — |
| Persian | 35 | — | — | — |
| Polish | 26 | — | — | — |
| French | 21 | — | — | — |
| Bengali | 11 | — | — | — |
| Korean | 11 | — | — | — |

**age_band**

| Stratum | Admissions | Exactly one | LLM only | Rule only |
| --- | --: | --: | --: | --: |
| 75-88 | 6,291 | 40.6 (31.5–50.7) | 26.9 (18.0–37.0) | 13.7 (8.0–19.8) |
| 55-64 | 6,062 | 29.5 (23.8–35.6) | 20.3 (15.3–26.0) | 9.2 (6.6–12.8) |
| 65-74 | 5,906 | 29.7 (24.3–35.0) | 14.8 (10.7–19.5) | 15.0 (11.0–19.1) |
| 40-54 | 5,853 | 23.2 (18.9–28.0) | 12.9 (9.5–16.4) | 10.4 (7.5–14.0) |
| 18-39 | 4,129 | 31.8 (23.2–39.5) | 17.3 (10.3–24.8) | 14.5 (8.5–22.4) |
| 89+ | 1,739 | 64.8 (40.1–85.3) † | 42.6 (17.5–67.8) † | 22.2 (7.0–45.8) † |

## Where uncoded LLM-positive cases are documented (E3): %

**overall**

| Stratum | Admissions | Discharge summary | Inpatient radiology only | Outpatient radiology only |
| --- | --: | --: | --: | --: |
| all | 29,980 | 43.3 (39.5–47.5) | 17.8 (16.0–19.8) | 38.9 (34.6–42.7) |

**race**

| Stratum | Admissions | Discharge summary | Inpatient radiology only | Outpatient radiology only |
| --- | --: | --: | --: | --: |
| WHITE | 19,569 | 43.2 (38.2–48.7) | 17.6 (15.4–19.9) | 39.2 (33.9–44.0) |
| BLACK/AFRICAN AMERICAN | 3,767 | 39.6 (31.3–49.7) | 14.1 (8.5–21.3) | 46.3 (34.5–56.9) † |
| OTHER | 953 | — | — | — |
| UNKNOWN * | 779 | — | — | — |
| WHITE - OTHER EUROPEAN | 585 | — | — | — |
| HISPANIC/LATINO - PUERTO RICAN | 515 | 55.1 (29.8–72.7) † | 14.1 (7.6–26.7) | 30.8 (15.1–50.9) † |
| HISPANIC OR LATINO | 448 | — | — | — |
| ASIAN - CHINESE | 414 | — | — | — |
| BLACK/CAPE VERDEAN | 390 | — | — | — |
| HISPANIC/LATINO - DOMINICAN | 370 | — | — | — |
| ASIAN | 366 | — | — | — |
| WHITE - RUSSIAN | 362 | — | — | — |
| BLACK/CARIBBEAN ISLAND | 189 | — | — | — |
| BLACK/AFRICAN | 134 | — | — | — |
| PATIENT DECLINED TO ANSWER * | 124 | — | — | — |
| PORTUGUESE | 110 | — | — | — |
| UNABLE TO OBTAIN * | 104 | — | — | — |
| ASIAN - SOUTH EAST ASIAN | 83 | — | — | — |
| WHITE - BRAZILIAN | 82 | — | — | — |
| WHITE - EASTERN EUROPEAN | 78 | — | — | — |
| HISPANIC/LATINO - SALVADORAN | 73 | — | — | — |
| ASIAN - ASIAN INDIAN | 67 | — | — | — |
| HISPANIC/LATINO - MEXICAN | 55 | — | — | — |
| AMERICAN INDIAN/ALASKA NATIVE | 54 | — | — | — |
| HISPANIC/LATINO - CUBAN | 51 | — | — | — |
| HISPANIC/LATINO - COLUMBIAN | 50 | — | — | — |
| HISPANIC/LATINO - GUATEMALAN | 43 | — | — | — |
| SOUTH AMERICAN | 42 | — | — | — |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 38 | — | — | — |
| HISPANIC/LATINO - HONDURAN | 32 | — | — | — |
| ASIAN - KOREAN | 23 | — | — | — |
| HISPANIC/LATINO - CENTRAL AMERICAN | 16 | — | — | — |
| MULTIPLE RACE/ETHNICITY | 14 | — | — | — |

**insurance**

| Stratum | Admissions | Discharge summary | Inpatient radiology only | Outpatient radiology only |
| --- | --: | --: | --: | --: |
| Medicare | 14,512 | 41.4 (36.3–46.7) | 15.8 (12.8–19.0) | 42.8 (37.1–48.3) |
| Private | 9,443 | 43.1 (37.1–50.2) | 18.2 (14.9–22.0) | 38.7 (31.8–44.3) |
| Medicaid | 4,834 | 46.8 (40.0–54.6) | 18.2 (14.4–22.5) | 35.0 (27.1–41.6) |
| Other | 766 | 48.3 (34.3–62.4) † | 22.4 (11.3–35.2) † | 29.3 (15.8–42.3) † |
| (missing) | 421 | — | — | — |

**sex**

| Stratum | Admissions | Discharge summary | Inpatient radiology only | Outpatient radiology only |
| --- | --: | --: | --: | --: |
| F | 15,394 | 43.2 (37.1–49.6) | 14.8 (12.5–17.4) | 42.0 (35.3–48.1) |
| M | 14,586 | 43.4 (39.0–47.9) | 20.9 (18.1–23.7) | 35.7 (30.8–40.4) |

**language**

| Stratum | Admissions | Discharge summary | Inpatient radiology only | Outpatient radiology only |
| --- | --: | --: | --: | --: |
| English | 26,885 | 44.0 (40.0–48.4) | 17.6 (15.6–19.7) | 38.4 (33.7–42.6) |
| Spanish | 1,005 | 52.8 (35.8–68.1) † | 15.7 (9.5–25.0) | 31.5 (18.8–46.7) † |
| Russian | 507 | — | — | — |
| Chinese | 449 | — | — | — |
| Kabuverdianu | 268 | — | — | — |
| Haitian | 182 | — | — | — |
| Portuguese | 142 | — | — | — |
| American Sign Language | 104 | — | — | — |
| Italian | 64 | — | — | — |
| Other | 62 | — | — | — |
| Vietnamese | 62 | — | — | — |
| Modern Greek (1453-) | 43 | — | — | — |
| (missing) | 37 | — | — | — |
| Arabic | 37 | — | — | — |
| Persian | 35 | — | — | — |
| Polish | 26 | — | — | — |
| French | 21 | — | — | — |
| Bengali | 11 | — | — | — |
| Korean | 11 | — | — | — |

**age_band**

| Stratum | Admissions | Discharge summary | Inpatient radiology only | Outpatient radiology only |
| --- | --: | --: | --: | --: |
| 75-88 | 6,291 | 40.5 (31.3–50.8) | 18.4 (12.6–25.0) | 41.1 (30.7–52.2) † |
| 55-64 | 6,062 | 44.8 (37.5–53.2) | 17.7 (14.7–22.1) | 37.5 (29.9–44.7) |
| 65-74 | 5,906 | 43.8 (36.8–50.7) | 13.3 (9.7–16.7) | 43.0 (35.5–50.5) |
| 40-54 | 5,853 | 43.1 (37.0–49.9) | 17.4 (14.0–21.6) | 39.5 (32.5–46.5) |
| 18-39 | 4,129 | 44.4 (36.7–53.0) | 26.1 (20.0–33.0) | 29.4 (20.5–38.1) |
| 89+ | 1,739 | — | — | — |

## Coverage (described before amendment i): % of admissions with ≥1 kept liver sentence

**overall**

| Stratum | Admissions | Coverage |
| --- | --: | --: |
| all | 29,980 | 51.7 (50.7–52.6) |

**race**

| Stratum | Admissions | Coverage |
| --- | --: | --: |
| WHITE | 19,569 | 51.3 (50.1–52.4) |
| BLACK/AFRICAN AMERICAN | 3,767 | 49.2 (46.0–52.3) |
| OTHER | 953 | 50.1 (46.2–53.9) |
| UNKNOWN * | 779 | 49.7 (46.2–53.7) |
| WHITE - OTHER EUROPEAN | 585 | 53.2 (47.3–59.2) |
| HISPANIC/LATINO - PUERTO RICAN | 515 | 62.9 (53.6–71.4) |
| HISPANIC OR LATINO | 448 | 50.4 (43.1–58.7) |
| ASIAN - CHINESE | 414 | 67.6 (60.0–74.8) |
| BLACK/CAPE VERDEAN | 390 | 62.3 (53.9–70.5) |
| HISPANIC/LATINO - DOMINICAN | 370 | 54.3 (42.9–64.4) † |
| ASIAN | 366 | 60.4 (53.3–67.2) |
| WHITE - RUSSIAN | 362 | 49.4 (42.0–56.8) |
| BLACK/CARIBBEAN ISLAND | 189 | 50.8 (41.4–60.1) |
| BLACK/AFRICAN | 134 | 55.2 (43.8–67.1) † |
| PATIENT DECLINED TO ANSWER * | 124 | 43.5 (33.6–53.3) |
| PORTUGUESE | 110 | 48.2 (31.6–62.4) † |
| UNABLE TO OBTAIN * | 104 | 49.0 (37.6–60.6) † |
| ASIAN - SOUTH EAST ASIAN | 83 | 62.7 (43.9–77.0) † |
| WHITE - BRAZILIAN | 82 | 54.9 (40.2–69.2) † |
| WHITE - EASTERN EUROPEAN | 78 | 56.4 (40.0–70.5) † |
| HISPANIC/LATINO - SALVADORAN | 73 | 46.6 (31.8–66.9) † |
| ASIAN - ASIAN INDIAN | 67 | 59.7 (39.0–72.1) † |
| HISPANIC/LATINO - MEXICAN | 55 | 50.9 (36.3–68.2) † |
| AMERICAN INDIAN/ALASKA NATIVE | 54 | 48.1 (24.4–75.5) † |
| HISPANIC/LATINO - CUBAN | 51 | 70.6 (49.2–89.2) † |
| HISPANIC/LATINO - COLUMBIAN | 50 | 42.0 (25.0–59.3) † |
| HISPANIC/LATINO - GUATEMALAN | 43 | 51.2 (35.9–67.0) † |
| SOUTH AMERICAN | 42 | — |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER | 38 | 52.6 (28.1–70.5) † |
| HISPANIC/LATINO - HONDURAN | 32 | 65.6 (33.3–80.7) † |
| ASIAN - KOREAN | 23 | 47.8 (25.0–69.4) † |
| HISPANIC/LATINO - CENTRAL AMERICAN | 16 | — |
| MULTIPLE RACE/ETHNICITY | 14 | — |

**insurance**

| Stratum | Admissions | Coverage |
| --- | --: | --: |
| Medicare | 14,512 | 50.9 (49.5–52.3) |
| Private | 9,443 | 51.3 (49.8–53.0) |
| Medicaid | 4,834 | 56.2 (54.0–58.6) |
| Other | 766 | 49.9 (45.3–54.1) |
| (missing) | 421 | 37.3 (32.6–42.5) |

**sex**

| Stratum | Admissions | Coverage |
| --- | --: | --: |
| F | 15,394 | 51.8 (50.5–53.1) |
| M | 14,586 | 51.5 (50.1–52.8) |

**language**

| Stratum | Admissions | Coverage |
| --- | --: | --: |
| English | 26,885 | 51.2 (50.2–52.1) |
| Spanish | 1,005 | 56.2 (49.4–62.5) |
| Russian | 507 | 46.9 (39.8–54.6) |
| Chinese | 449 | 68.4 (60.9–75.1) |
| Kabuverdianu | 268 | 54.9 (45.3–63.5) |
| Haitian | 182 | 54.4 (44.2–65.5) † |
| Portuguese | 142 | 57.0 (44.0–68.6) † |
| American Sign Language | 104 | 73.1 (50.6–78.0) † |
| Italian | 64 | 35.9 (17.6–54.2) † |
| Other | 62 | 58.1 (38.6–73.8) † |
| Vietnamese | 62 | 75.8 (55.4–87.7) † |
| Modern Greek (1453-) | 43 | 39.5 (17.7–68.8) † |
| (missing) | 37 | 35.1 (19.0–52.8) † |
| Arabic | 37 | 48.6 (34.7–69.0) † |
| Persian | 35 | 31.4 (15.3–50.0) † |
| Polish | 26 | 46.2 (0.0–73.9) † |
| French | 21 | — |
| Bengali | 11 | 100.0 (100.0–100.0) |
| Korean | 11 | — |

**age_band**

| Stratum | Admissions | Coverage |
| --- | --: | --: |
| 75-88 | 6,291 | 47.5 (45.7–49.4) |
| 55-64 | 6,062 | 56.3 (54.1–58.6) |
| 65-74 | 5,906 | 54.4 (52.6–56.4) |
| 40-54 | 5,853 | 54.4 (52.4–56.6) |
| 18-39 | 4,129 | 45.7 (43.6–47.7) |
| 89+ | 1,739 | 46.4 (42.7–49.7) |

