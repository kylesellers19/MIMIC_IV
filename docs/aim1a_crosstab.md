# Aim 1a — Code × Note Cross-tabulation and Chart-Review Sampling Frame

> **This 2×2 compares two COMPUTABLE PHENOTYPES (ICD code vs frozen note rule v1.1.0). It is NOT an adjudicated estimate.** The headline Aim 1a figure — the population-weighted fraction of gold-standard-positive admissions that codes miss — REQUIRES the chart review sampled below, which HAS NOT YET OCCURRED. No number here is a recovery estimate; the code−/note+ cell is a sampling stratum, not a count of missed cases.

Population: cleaned locked analysis population, N = 373,992 admissions (161,119 subjects). Note-positive = Tier A definite. Reproducers: `scripts/build_2x2.py`, `scripts/aim1a_report.py`.

## Step 1 — The 2×2 (four versions)

### Admission grain (primary), n (% of population)

| version | code+/note+ | code−/note+ | code+/note− | code−/note− |
| --- | --: | --: | --: | --: |
| (a) v1.1.0 inpatient-linked | 4,805 (1.28%) | 13,612 (3.64%) | 935 (0.25%) | 354,640 (94.83%) |
| (b) v1.1.0 + outpatient 365/30  — **PRIMARY** | 5,027 (1.34%) | 22,799 (6.10%) | 713 (0.19%) | 345,453 (92.37%) |
| (c) v1.1.0 + outpatient 90/30  (sensitivity) | 4,908 (1.31%) | 17,851 (4.77%) | 832 (0.22%) | 350,401 (93.69%) |
| (d) v1.0.0 inpatient-linked  (rule-version sensitivity) | 4,850 (1.30%) | 22,443 (6.00%) | 890 (0.24%) | 345,809 (92.46%) |

### Subject grain (secondary)

Collapse rule: a subject is **code+** if ANY of their admissions is code+, and **note+** if ANY admission is note+ (under that version).

| version | subjects | code+/note+ | code−/note+ | code+/note− | code−/note− |
| --- | --: | --: | --: | --: | --: |
| (a) v1.1.0 inpatient-linked | 161,119 | 3,162 | 8,577 | 513 | 148,867 |
| (b) v1.1.0 + outpatient 365/30  — **PRIMARY** | 161,119 | 3,292 | 11,709 | 383 | 145,735 |
| (c) v1.1.0 + outpatient 90/30  (sensitivity) | 161,119 | 3,237 | 10,477 | 438 | 146,967 |
| (d) v1.0.0 inpatient-linked  (rule-version sensitivity) | 161,119 | 3,230 | 14,943 | 445 | 142,501 |

**Rule-version dependence (isolated — both inpatient-linked, code−/note+ cell):** v1.1.0 (a) = 13,612 vs v1.0.0 (d) = 22,443. The pre-revision lexicon would have made this cell **+8,831 larger (+64.9%)**, driven by bare-`fatty` false positives (predominantly code-negative). The primary headline uses (b) = 22,799; (d) is a sensitivity reference so the manuscript can state how much the count depends on the lexicon revision — NOT a competing estimate.

## Step 2 — Recovery zone & code+/note− (descriptive; SMDs, not p-values)

### code−/note+ (recovery zone, n=22,799) vs code+/note+ (n=5,027)

| variable | code−/note+ | code+/note+ | SMD |
| --- | --- | --- | --: |
| Age at admission, median [IQR] | 58.0 [48.0, 67.0] | 59.0 [49.0, 68.0] | -0.009 |
| Length of stay (days) | 3.7 [1.8, 6.9] | 3.6 [2.0, 6.7] | +0.047 |
| Distinct diagnoses | 12.0 [8.0, 18.0] | 15.0 [10.0, 20.0] | -0.334 |
| Male, % | 53.0% | 50.4% | +0.052 |
| Race (multinomial) | — | — | +0.214 |
| Insurance (multinomial) | — | — | +0.108 |
| Language (multinomial) | — | — | +0.134 |
| Admission type (multinomial) | — | — | +0.268 |

Lab availability (available = has ≥1 result; SMD of availability):

| analyte | code−/note+ avail% | code+/note+ avail% | SMD |
| --- | --: | --: | --: |
| ALT | 62.0% | 64.8% | -0.058 |
| AST | 62.0% | 64.8% | -0.058 |
| Platelets | 89.5% | 88.3% | +0.039 |
| Triglycerides | 10.5% | 9.7% | +0.026 |
| HDL | 4.7% | 5.2% | -0.023 |
| HbA1c | 7.3% | 9.4% | -0.079 |
| Glucose | 89.1% | 88.1% | +0.032 |
| Albumin | 44.5% | 47.5% | -0.062 |
| Bilirubin_total | 61.4% | 64.3% | -0.061 |
| Alkaline_phosphatase | 61.4% | 64.3% | -0.061 |

### code+/note− (n=713) — coded, no detectable note evidence (describe, do not adjudicate)

- **Note-source availability:** 86.1% have a linked discharge note, 78.5% a radiology note (100.0% either) — so a share have documents that simply lack detectable steatosis language; the remainder have no linked note at all.
- **LOS:** median 3.2 [1.5, 6.1] days.
- **MASLD code seq_num:** principal (seq=1) 0.0%; median seq 8 [4, 13]. seq_num distribution (min MASLD seq):

| min MASLD seq_num | n |
| --: | --: |
| 2 | 66 |
| 3 | 67 |
| 4 | 72 |
| 5 | 44 |
| 6 | 50 |
| 7 | 52 |
| 8 | 40 |
| 9 | 38 |
| 10 | 34 |
| 11 | 24 |
| 12 | 36 |
| 13 | 28 |
| 14 | 19 |
| 15 | 25 |
| 16 | 18 |
| >15 | 118 |

## Step 3 — Equity stratification (CELL SIZES FIRST; floor = 11 for code−/note+)

Using the primary (b) definition. **No recovery rates are computed.** Strata are NOT collapsed — failures are listed for the researcher to decide on.

### By race

| stratum | code+/note+ | code−/note+ | code+/note− | code−/note− | code−/note+ ≥11? |
| --- | --: | --: | --: | --: | :--: |
| AMERICAN INDIAN/ALASKA NATIVE | 10 | 43 | 2 | 709 | yes |
| ASIAN | 49 | 262 | 9 | 4,330 | yes |
| ASIAN - ASIAN INDIAN | 14 | 81 | 3 | 879 | yes |
| ASIAN - CHINESE | 67 | 374 | 11 | 4,241 | yes |
| ASIAN - KOREAN | 1 | 21 | 1 | 350 | yes |
| ASIAN - SOUTH EAST ASIAN | 15 | 114 | 1 | 1,132 | yes |
| BLACK/AFRICAN | 25 | 92 | 3 | 1,895 | yes |
| BLACK/AFRICAN AMERICAN | 410 | 2,449 | 76 | 46,706 | yes |
| BLACK/CAPE VERDEAN | 57 | 235 | 4 | 3,691 | yes |
| BLACK/CARIBBEAN ISLAND | 16 | 101 | 2 | 2,283 | yes |
| HISPANIC OR LATINO | 92 | 518 | 16 | 5,543 | yes |
| HISPANIC/LATINO - CENTRAL AMERICAN | 27 | 43 | 2 | 310 | yes |
| HISPANIC/LATINO - COLUMBIAN | 15 | 46 | 3 | 442 | yes |
| HISPANIC/LATINO - CUBAN | 6 | 22 | 0 | 400 | yes |
| HISPANIC/LATINO - DOMINICAN | 79 | 289 | 13 | 3,229 | yes |
| HISPANIC/LATINO - GUATEMALAN | 55 | 138 | 4 | 982 | yes |
| HISPANIC/LATINO - HONDURAN | 9 | 44 | 1 | 371 | yes |
| HISPANIC/LATINO - MEXICAN | 17 | 53 | 2 | 439 | yes |
| HISPANIC/LATINO - PUERTO RICAN | 235 | 622 | 20 | 5,943 | yes |
| HISPANIC/LATINO - SALVADORAN | 34 | 58 | 0 | 637 | yes |
| MULTIPLE RACE/ETHNICITY | 4 | 24 | 0 | 390 | yes |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDE | 4 | 23 | 0 | 290 | yes |
| OTHER | 185 | 718 | 27 | 11,598 | yes |
| PATIENT DECLINED TO ANSWER | 19 | 70 | 6 | 1,428 | yes |
| PORTUGUESE | 56 | 119 | 7 | 1,201 | yes |
| SOUTH AMERICAN | 9 | 46 | 0 | 388 | yes |
| UNABLE TO OBTAIN | 9 | 55 | 2 | 1,326 | yes |
| UNKNOWN | 88 | 493 | 11 | 9,134 | yes |
| WHITE | 3,167 | 14,785 | 447 | 222,559 | yes |
| WHITE - BRAZILIAN | 21 | 69 | 5 | 855 | yes |
| WHITE - EASTERN EUROPEAN | 12 | 54 | 2 | 977 | yes |
| WHITE - OTHER EUROPEAN | 139 | 524 | 22 | 6,441 | yes |
| WHITE - RUSSIAN | 81 | 214 | 11 | 4,354 | yes |

**Analysable (race, code−/note+ ≥ 11):** WHITE (14785), BLACK/AFRICAN AMERICAN (2449), OTHER (718), HISPANIC/LATINO - PUERTO RICAN (622), WHITE - OTHER EUROPEAN (524), HISPANIC OR LATINO (518), UNKNOWN (493), ASIAN - CHINESE (374), HISPANIC/LATINO - DOMINICAN (289), ASIAN (262), BLACK/CAPE VERDEAN (235), WHITE - RUSSIAN (214), HISPANIC/LATINO - GUATEMALAN (138), PORTUGUESE (119), ASIAN - SOUTH EAST ASIAN (114), BLACK/CARIBBEAN ISLAND (101), BLACK/AFRICAN (92), ASIAN - ASIAN INDIAN (81), PATIENT DECLINED TO ANSWER (70), WHITE - BRAZILIAN (69), HISPANIC/LATINO - SALVADORAN (58), UNABLE TO OBTAIN (55), WHITE - EASTERN EUROPEAN (54), HISPANIC/LATINO - MEXICAN (53), HISPANIC/LATINO - COLUMBIAN (46), SOUTH AMERICAN (46), HISPANIC/LATINO - HONDURAN (44), AMERICAN INDIAN/ALASKA NATIVE (43), HISPANIC/LATINO - CENTRAL AMERICAN (43), MULTIPLE RACE/ETHNICITY (24), NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER (23), HISPANIC/LATINO - CUBAN (22), ASIAN - KOREAN (21).

**NOT analysable (below floor):** none.

### By insurance

| stratum | code+/note+ | code−/note+ | code+/note− | code−/note− | code−/note+ ≥11? |
| --- | --: | --: | --: | --: | :--: |
| Medicaid | 987 | 5,042 | 124 | 56,874 | yes |
| Medicare | 1,882 | 8,684 | 327 | 169,614 | yes |
| No charge | 0 | 6 | 0 | 67 | NO |
| Other | 122 | 724 | 13 | 9,111 | yes |
| Private | 2,006 | 8,136 | 245 | 104,835 | yes |

**Analysable (insurance, code−/note+ ≥ 11):** Medicare (8684), Private (8136), Medicaid (5042), Other (724).

**NOT analysable (below floor):** No charge (6).

## Step 4 — Chart-review sampling frame

Allocation (per docs/reference_standard.md, ~400 charts), cell assignment by PRIMARY (b). Random seed **20260818** (also in `scripts/aim1a_report.py`).

| cell | population N | allocation | enough to sample? |
| --- | --: | --: | :--: |
| code-/note+ | 22,799 | 150 | yes |
| code+/note+ | 5,027 | 80 | yes |
| code+/note- | 713 | 70 | yes |
| code-/note- | 345,453 | 100 | yes |

**Drawn: 400 charts** written to `data/processed/aim1a_sample.parquet` (credentialed, gitignored). Blinded IDs R0001–R0400 assigned AFTER a seeded shuffle, so neither the ID nor the row order encodes cell membership; the reviewer-facing view excludes `cell` and `double_review`.

**Double review (Cohen's κ):** 100 charts (25%) flagged `double_review` in the master key only.

### Sampling weights (population reweighting)

Disproportionate sampling → each cell reweighted to its population frequency. For a sampled chart in cell *c*: **weight = N_pop(c) / n_sample(c)**. The headline 1a estimate (of adjudicated gold-positive admissions, the population-weighted fraction that are code-negative) is computed as Σ wᵢ·[code−] / Σ wᵢ over gold-positive sampled charts.

| cell | N_pop | n_sample | weight = N_pop / n_sample |
| --- | --: | --: | --: |
| code-/note+ | 22,799 | 150 | 152.0 |
| code+/note+ | 5,027 | 80 | 62.8 |
| code+/note- | 713 | 70 | 10.2 |
| code-/note- | 345,453 | 100 | 3,454.5 |

---

## Pre-specified secondary analyses (SLD nomenclature)

The primary 2×2 stays at the **steatosis** level (the code axis requires no
cardiometabolic criterion, so gating note-positivity on CMRF would compare
non-comparable constructs). Pre-specified secondary analyses — full detail,
five-CMRF operationalization (Rinella et al. 2023), SLD subclassification
(MASLD / MetALD / ALD / Cryptogenic / Unclassifiable), and the alcohol-proxy
caveat — are in [docs/sld_subclassification.md](sld_subclassification.md).
Recovery estimate (code−/note+ ÷ all note+) is robust across definitions:

| definition | recovery % |
| --- | --: |
| PRIMARY: steatosis | 81.9% |
| (i) steatosis excluding alcohol-related codes | 80.9% |
| (ii) steatosis + ≥1 CMRF (MASLD-consistent) | 81.4% |
| (iii) steatosis excl. all competing etiologies (NAFLD-era; NOT primary under current nomenclature) | 83.4% |

MetALD-consistent admissions (steatosis + ≥1 CMRF + alcohol code) = 4,308 of
note-positive (15.5%); MetALD has no ICD code, so it is invisible to the code axis
by construction. See the linked doc for the alcohol-proxy limitation.

---

*This document reports a computable-phenotype comparison and a sampling design only. The Aim 1a recovery estimate is not final and requires the chart adjudication that this frame is built to enable.*
