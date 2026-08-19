# Imaging Denominator — why 63% lack liver-inclusive imaging

> Aggregate only; read from CLEAN_POP; frozen phenotype unchanged. Population N = 373,992. Note-positive = Tier A (primary b).

## Step 1 — Three-way imaging split

**Inpatient-linked:** (a) no radiology **64,548 (17.3%)** · (b) radiology, none liver-inclusive **225,910 (60.4%)** · (c) ≥1 liver-inclusive **83,534 (22.3%)**
**With 365/30 outpatient window:** (a) no radiology **24,192 (6.5%)** · (b) radiology, none liver-inclusive **211,197 (56.5%)** · (c) ≥1 liver-inclusive **138,603 (37.1%)**

### (b) top exam types among imaged-but-not-liver-inclusive admissions (inpatient scope)

| exam_name | n |
| --- | --: |
| CHEST (PORTABLE AP) | 164,577 |
| CHEST (PA & LAT) | 106,843 |
| CT HEAD W/O CONTRAST | 52,149 |
| CHEST PORT. LINE PLACEMENT | 30,716 |
| -76 BY SAME PHYSICIAN | 22,643 |
| -77 BY DIFFERENT PHYSICIAN | 16,991 |
| -59 DISTINCT PROCEDURAL SERVICE | 12,199 |
| ___ | 11,906 |
| MR HEAD W & W/O CONTRAST | 10,264 |
| CT C-SPINE W/O CONTRAST | 10,119 |
| MR HEAD W/O CONTRAST | 9,147 |
| CTA CHEST W&W/O C&RECONS, NON-CORONARY | 9,126 |
| CHEST (PRE-OP PA & LAT) | 8,167 |
| CT CHEST W/O CONTRAST | 8,056 |
| CTA HEAD W&W/O C & RECONS | 7,901 |
| BILAT LOWER EXT VEINS | 7,120 |
| CTA NECK W&W/OC & RECONS | 6,052 |
| ABDOMEN (SUPINE & ERECT) | 5,976 |
| CHEST (SINGLE VIEW) | 5,948 |
| RENAL U.S. | 5,912 |
| FLUORO GUID PLCT/REPLCT/REMOVE CENTRAL LINE | 5,590 |
| PORTABLE ABDOMEN | 5,493 |
| MRA BRAIN W/O CONTRAST | 5,050 |
| US GUID FOR VAS. ACCESS | 4,818 |
| CAROTID SERIES COMPLETE | 4,364 |
| CTA CHEST  | 4,171 |
| CHEST PORT LINE/TUBE PLCT 1 EXAM | 3,672 |
| UNILAT LOWER EXT VEINS LEFT | 3,602 |
| MOD SEDATION, EACH ADDL 15 MINS | 3,558 |
| UNILAT LOWER EXT VEINS RIGHT | 3,464 |

## Step 2 — Presenting problem (principal diagnosis, seq_num=1)

Chapter mapping = ICD-10-CM / ICD-9-CM Tabular List chapter structure (WHO/CDC/CMS official chapters). Liver-inclusive imaging rate (365/30 window):

### by ICD chapter (ascending)

| chapter | n | liver-inclusive imaging % |
| --- | --: | --: |
| Eye | 247 | 11.3% |
| Ear | 331 | 15.1% |
| Mental | 15,573 | 15.3% |
| Musculoskeletal | 19,943 | 19.0% |
| Pregnancy | 5,809 | 19.2% |
| Skin | 7,389 | 20.6% |
| Congenital | 1,079 | 21.0% |
| Circulatory | 66,599 | 22.4% |
| Nervous | 12,762 | 26.1% |
| Respiratory | 21,947 | 27.8% |
| Injury/poisoning | 48,610 | 33.2% |
| Symptoms/ill-defined | 37,803 | 33.5% |
| Endocrine/metabolic | 15,131 | 33.8% |
| Factors/Z-codes | 8,330 | 43.1% |
| Genitourinary | 18,083 | 43.5% |
| Blood/immune | 4,672 | 45.6% |
| Neoplasms | 24,612 | 56.3% |
| Infectious | 18,231 | 60.2% |
| Digestive | 46,837 | 70.0% |

### by admission_type (ascending)

| admission_type | n | imaging % |
| --- | --: | --: |
| SURGICAL SAME DAY ADMISSION | 32,097 | 27.8% |
| DIRECT OBSERVATION | 14,734 | 28.5% |
| EU OBSERVATION | 62,606 | 29.3% |
| URGENT | 30,268 | 30.5% |
| ELECTIVE | 10,098 | 32.2% |
| AMBULATORY OBSERVATION | 5,255 | 34.7% |
| EW EMER. | 147,550 | 42.2% |
| DIRECT EMER. | 19,041 | 42.3% |
| OBSERVATION ADMIT | 52,343 | 43.0% |

### by admission_location (ascending)

| admission_location | n | imaging % |
| --- | --: | --: |
| INTERNAL TRANSFER TO OR FROM PSYCH | 4,164 | 8.8% |
| PACU | 4,905 | 31.1% |
| PHYSICIAN REFERRAL | 92,117 | 33.7% |
| TRANSFER FROM HOSPITAL | 34,843 | 34.6% |
| INFORMATION NOT AVAILABLE | 316 | 37.3% |
| EMERGENCY ROOM | 204,583 | 38.4% |
| PROCEDURE SITE | 5,923 | 39.7% |
| TRANSFER FROM SKILLED NURSING FACILITY | 3,746 | 40.5% |
| WALK-IN/SELF REFERRAL | 13,670 | 46.5% |
| CLINIC REFERRAL | 9,551 | 49.2% |

## Step 3 — Access vs indication (imaging rate by race/insurance, then within-chapter)

Within-indication subset = principal dx in ['Circulatory', 'Digestive', 'Endocrine/metabolic', 'Infectious', 'Neoplasms'] (n=171,410).

### insurance: imaging rate + one-vs-rest SMD (unadjusted vs within-plausible-chapters)

| insurance | n | unadj img% | unadj SMD | within-chap img% | within SMD |
| --- | --: | --: | --: | --: | --: |
| Medicare | 180,507 | 35.7% | -0.056 | 41.3% | -0.171 |
| Private | 115,222 | 38.4% | +0.040 | 48.4% | +0.090 |
| Medicaid | 63,027 | 39.4% | +0.058 | 52.9% | +0.177 |
| Other | 9,970 | 36.5% | -0.011 | 50.9% | +0.114 |

*max one-vs-rest |SMD|: unadjusted 0.058 → within-chapter 0.177.*

### race: imaging rate + one-vs-rest SMD (unadjusted vs within-plausible-chapters)

| race | n | unadj img% | unadj SMD | within-chap img% | within SMD |
| --- | --: | --: | --: | --: | --: |
| WHITE | 240,958 | 36.9% | -0.008 | 44.9% | -0.025 |
| BLACK/AFRICAN AMERICAN | 49,641 | 35.4% | -0.040 | 45.3% | -0.000 |
| OTHER | 12,528 | 34.7% | -0.051 | 43.9% | -0.029 |
| UNKNOWN | 9,726 | 30.6% | -0.140 | 31.0% | -0.307 |
| WHITE - OTHER EUROPEAN | 7,126 | 40.4% | +0.070 | 48.3% | +0.061 |
| HISPANIC/LATINO - PUERTO RICAN | 6,820 | 43.9% | +0.143 | 55.3% | +0.204 |
| HISPANIC OR LATINO | 6,169 | 40.1% | +0.063 | 53.6% | +0.169 |
| ASIAN - CHINESE | 4,693 | 46.7% | +0.199 | 56.6% | +0.231 |
| WHITE - RUSSIAN | 4,660 | 35.4% | -0.035 | 40.3% | -0.102 |
| ASIAN | 4,650 | 38.7% | +0.035 | 50.6% | +0.107 |
| BLACK/CAPE VERDEAN | 3,987 | 40.4% | +0.068 | 52.1% | +0.138 |
| HISPANIC/LATINO - DOMINICAN | 3,610 | 39.5% | +0.051 | 50.3% | +0.102 |
| BLACK/CARIBBEAN ISLAND | 2,402 | 37.8% | +0.015 | 44.5% | -0.016 |
| BLACK/AFRICAN | 2,015 | 32.6% | -0.094 | 44.1% | -0.024 |
| PATIENT DECLINED TO ANSWER | 1,523 | 32.5% | -0.096 | 35.3% | -0.207 |
| UNABLE TO OBTAIN | 1,392 | 30.1% | -0.148 | 31.0% | -0.300 |
| PORTUGUESE | 1,383 | 50.6% | +0.277 | 63.9% | +0.381 |
| ASIAN - SOUTH EAST ASIAN | 1,262 | 50.4% | +0.272 | 57.2% | +0.241 |
| HISPANIC/LATINO - GUATEMALAN | 1,179 | 46.4% | +0.191 | 59.1% | +0.279 |
| WHITE - EASTERN EUROPEAN | 1,045 | 39.8% | +0.057 | 47.7% | +0.049 |
| ASIAN - ASIAN INDIAN | 977 | 35.3% | -0.036 | 44.1% | -0.024 |
| WHITE - BRAZILIAN | 950 | 48.3% | +0.230 | 58.8% | +0.272 |
| AMERICAN INDIAN/ALASKA NATIVE | 764 | 41.0% | +0.080 | 53.5% | +0.164 |
| HISPANIC/LATINO - SALVADORAN | 729 | 47.5% | +0.212 | 59.0% | +0.277 |
| HISPANIC/LATINO - MEXICAN | 511 | 37.4% | +0.007 | — | — |
| HISPANIC/LATINO - COLUMBIAN | 506 | 38.1% | +0.022 | 57.7% | +0.251 |

*max one-vs-rest |SMD|: unadjusted 0.277 → within-chapter 0.381.*

**Coding status (code+ vs code−) imaging SMD:** unadjusted +0.736 → within-plausible-chapters +0.663.

## Step 4 — Length of stay and opportunity

| LOS band | n | imaging % |
| --- | --: | --: |
| <1 day | 64,410 | 27.1% |
| 1-2 | 68,117 | 32.6% |
| 3-5 | 127,833 | 36.2% |
| 6+ | 113,543 | 46.3% |

- Short-stay (<1 day): 64,320 (17.2%). Of these, 46,882 (72.9% of short-stay) are NOT liver-imaged.
- Of all non-imaged admissions (235,389), 46,882 (19.9%) are short-stay.

## Step 5 — The 2×2 side by side

Recovery % = code−/note+ ÷ all note+.

| population | N | code+/note+ | code−/note+ | code+/note− | code−/note− | recovery % |
| --- | --: | --: | --: | --: | --: | --: |
| Full population | 373,992 | 5,027 | 22,799 | 713 | 345,453 | 81.9% |
| Imaging-restricted (liver-inclusive) | 138,603 | 3,739 | 19,248 | 335 | 115,281 | 83.7% |
| (b) imaged, not liver-inclusive | 211,197 | 1,124 | 3,321 | 324 | 206,428 | 74.7% |

**Recovery % moves: full 81.9% → imaging-restricted 83.7% (Δ +1.8 pts).**


## Step 6 — Would the `services` table materially improve Step 2?

`services` (hospital service line: MED, SURG, PSYCH, OMED, CMED, NMED, OBS, ORTHO,
TSURG, VSURG, …) is a MIMIC-IV hosp table not currently downloaded. Assessment
relative to the ICD-chapter mapping used here:

- **Redundant for the core question.** The principal-diagnosis chapter already
  produces a strong, clinically-coherent indication gradient (Eye 11.3% → Digestive
  70.0%) and cleanly isolates the low-imaging service-adjacent chapters (Mental
  15.3%, Musculoskeletal 19.0%, Pregnancy 19.2%, Eye 11.3%). Service line is
  correlated with chapter and would reproduce most of this separation.
- **Modest incremental value in two places:** (i) it would disambiguate the
  chapters that are indication-ambiguous — `Symptoms/ill-defined` (33.5%),
  `Factors/Z-codes` (43.1%), `Injury/poisoning` (33.2%) — where the care service
  (SURG vs MED vs PSYCH) clarifies context; (ii) it supplies an independent
  adjustment axis for Step 3, allowing a service-line-adjusted re-test of the
  residual race/insurance differential.
- **Not material to the conclusion.** The residual differential persisted (grew)
  within diagnostic chapters, so it is unlikely to vanish under service adjustment;
  the indication-vs-access question is already answerable without it.

**Verdict: a modest, complementary improvement — worth fetching (small file) only if
a service-line-adjusted sensitivity analysis is wanted; not required for Step 2 or
for the primary conclusion.**

## Step 7 — Is non-imaging indication-driven or access-driven?

**Predominantly indication-driven, with a residual access/context component that
does not disappear when indication is held constant.**

*Indication dominates.* Only **6.5%** of admissions had no radiology at all; **56.5%**
were imaged but of other body regions matching their presenting problem (renal US,
portable abdomen, brain MRA, carotid, vascular access, leg veins). Liver-inclusive
imaging tracks the principal-diagnosis chapter as clinically expected — bottom for
eye/mental/musculoskeletal/obstetric (11–19%), top for digestive/infectious/
neoplasm (56–70%). Length of stay contributes partially (imaging 27.1% → 46.3%
across LOS bands) but explains only ~20% of non-imaging (80% of non-imaged
admissions are not short-stay).

*A residual access/context signal remains.* Race and insurance differentials did
**not** shrink once indication was held constant — they persisted or grew within
abdominal-plausible chapters (race max one-vs-rest |SMD| 0.28 → 0.38; insurance
0.06 → 0.18). The direction is mixed rather than a simple disadvantage gradient:
several immigrant/language-associated groups image higher, while UNKNOWN /
UNABLE-TO-OBTAIN / PATIENT-DECLINED race and Medicare image lower. This residual
belongs in the paper alongside the lab-availability finding, though its
interpretation is less clean than the lab result. The coding-status imaging
differential stays large within-chapter (SMD +0.66), consistent with the
imaging → incidental-finding → code pathway.

*Implication for the primary-population choice.* The recovery percentage
(code−/note+ ÷ all note+) moves only **+1.8 points** between the full population
(81.9%) and the imaging-restricted population (83.7%). Because this recovery metric
conditions on note-positivity — which already requires documentation — it is
largely insensitive to the imaging denominator. Whether the imaging-restricted
population is made primary therefore has little effect on the headline recovery
estimate, and the value of redrawing the 400-chart sample for imaging-restriction
turns on that ~2-point movement.
