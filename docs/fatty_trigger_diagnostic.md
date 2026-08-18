# Bare `fatty` Trigger Diagnostic (pre-adjudication)

Frozen rule v1.0.0. Read-only; no gold standard, no code changes. Scope = inpatient-linked notes on the locked population. Aggregate only.

## Headline counts

- Notes with ≥1 affirmed bare-`fatty` Tier A hit: **12,402** (this is the 12,402 figure — a note count, not admissions).
- Affirmed bare-`fatty` hits (hit level): **15,126**.
- Admissions positive by any Tier A trigger: **27,293**.
- Admissions with a bare-`fatty` Tier A positive: **10,983**.

## Step 2 — How much is bare `fatty` actually adding?

- Admissions positive by bare `fatty` **ONLY** (no other Tier A trigger in any linked note): **8,142**  (code+ 87 / code− 8,055).
- Admissions where bare `fatty` is **redundant** with another Tier A trigger: **2,841**  (code+ 506 / code− 2,335).

## Step 1 — What phrases is bare `fatty` firing on?

### Source: discharge

### `fatty` + following token (top 50)

| # | fragment | count |
| ---: | --- | ---: |
| 1 | fatty acids | 4,174 |
| 2 | fatty </s> | 1,490 |
| 3 | fatty or | 649 |
| 4 | fatty foods | 555 |
| 5 | fatty deposition | 380 |
| 6 | fatty acid | 200 |
| 7 | fatty atrophy | 155 |
| 8 | fatty meal | 150 |
| 9 | fatty meals | 109 |
| 10 | fatty food | 95 |
| 11 | fatty stranding | 93 |
| 12 | fatty hilum | 74 |
| 13 | fatty tissue | 72 |
| 14 | fatty replacement | 64 |
| 15 | fatty deposits | 61 |
| 16 | fatty infiltrate | 54 |
| 17 | fatty changes | 52 |
| 18 | fatty mass | 45 |
| 19 | fatty and | 35 |
| 20 | fatty lesion | 34 |
| 21 | fatty tumor | 33 |
| 22 | fatty hila | 30 |
| 23 | fatty replaced | 20 |
| 24 | fatty infiltrated | 17 |
| 25 | fatty stools | 16 |
| 26 | fatty acids/vitamin | 14 |
| 27 | fatty deposit | 12 |
| 28 | fatty attenuation | 11 |
| 29 | fatty fried | 11 |
| 30 | fatty necrosis | 11 |
| 31 | fatty density | 11 |
| 32 | fatty infiltrates | 10 |
| 33 | fatty tumors | 9 |
| 34 | fatty stool | 9 |
| 35 | fatty hepatic | 8 |
| 36 | fatty diarrhea | 8 |
| 37 | fatty but | 8 |
| 38 | fatty tissues | 8 |
| 39 | fatty diet | 8 |
| 40 | fatty component | 7 |
| 41 | fatty subcutaneous | 7 |
| 42 | fatty lesions | 6 |
| 43 | fatty unsweetened | 6 |
| 44 | fatty in | 6 |
| 45 | fatty appearing | 6 |
| 46 | fatty liver | 6 |
| 47 | fatty inflammatory | 6 |
| 48 | fatty mural | 6 |
| 49 | fatty liverdisease | 6 |
| 50 | fatty greasy | 5 |

### preceding token + `fatty` (top 50)

| # | fragment | count |
| ---: | --- | ---: |
| 1 | 3 fatty | 4,273 |
| 2 | avoid fatty | 744 |
| 3 | <s> fatty | 720 |
| 4 | with fatty | 625 |
| 5 | a fatty | 184 |
| 6 | and fatty | 171 |
| 7 | of fatty | 141 |
| 8 | diffuse fatty | 127 |
| 9 | focal fatty | 108 |
| 10 | to fatty | 91 |
| 11 | eating fatty | 91 |
| 12 | mild fatty | 66 |
| 13 | chain fatty | 64 |
| 14 | showed fatty | 61 |
| 15 | is fatty | 57 |
| 16 | or fatty | 54 |
| 17 | adjacent fatty | 46 |
| 18 | after fatty | 36 |
| 19 | omega fatty | 36 |
| 20 | severe fatty | 33 |
| 21 | the fatty | 31 |
| 22 | large fatty | 31 |
| 23 | some fatty | 27 |
| 24 | by fatty | 26 |
| 25 | spicy fatty | 25 |
| 26 | avoids fatty | 25 |
| 27 | diffusely fatty | 22 |
| 28 | suggesting fatty | 20 |
| 29 | extensive fatty | 19 |
| 30 | for fatty | 19 |
| 31 | avoiding fatty | 18 |
| 32 | demonstrated fatty | 18 |
| 33 | subcutaneous fatty | 18 |
| 34 | predominantly fatty | 16 |
| 35 | from fatty | 16 |
| 36 | heterogeneous fatty | 16 |
| 37 | surrounding fatty | 15 |
| 38 | 2 fatty | 15 |
| 39 | likely fatty | 14 |
| 40 | as fatty | 14 |
| 41 | benign fatty | 14 |
| 42 | essential fatty | 14 |
| 43 | especially fatty | 13 |
| 44 | eats fatty | 13 |
| 45 | in fatty | 12 |
| 46 | suggests fatty | 12 |
| 47 | have fatty | 12 |
| 48 | chocolate fatty | 11 |
| 49 | all fatty | 11 |
| 50 | showing fatty | 10 |

### trigrams centered on `fatty` (top 30)

| # | fragment | count |
| ---: | --- | ---: |
| 1 | 3 fatty acids | 4,013 |
| 2 | avoid fatty or | 601 |
| 3 | with fatty </s> | 330 |
| 4 | <s> fatty </s> | 162 |
| 5 | with fatty deposition | 156 |
| 6 | 3 fatty </s> | 121 |
| 7 | 3 fatty acid | 111 |
| 8 | avoid fatty foods | 104 |
| 9 | a fatty meal | 81 |
| 10 | focal fatty </s> | 72 |
| 11 | <s> fatty foods | 68 |
| 12 | of fatty </s> | 65 |
| 13 | <s> fatty acids | 63 |
| 14 | eating fatty foods | 53 |
| 15 | <s> fatty deposition | 53 |
| 16 | and fatty foods | 50 |
| 17 | diffuse fatty </s> | 49 |
| 18 | and fatty </s> | 48 |
| 19 | <s> fatty atrophy | 44 |
| 20 | to fatty </s> | 43 |
| 21 | showed fatty </s> | 38 |
| 22 | with fatty foods | 38 |
| 23 | chain fatty acid | 35 |
| 24 | adjacent fatty stranding | 33 |
| 25 | a fatty </s> | 31 |
| 26 | omega fatty acids | 31 |
| 27 | or fatty foods | 30 |
| 28 | chain fatty acids | 27 |
| 29 | mild fatty </s> | 27 |
| 30 | diffuse fatty atrophy | 25 |

### Source: radiology

### `fatty` + following token (top 50)

| # | fragment | count |
| ---: | --- | ---: |
| 1 | fatty </s> | 1,740 |
| 2 | fatty deposition | 1,068 |
| 3 | fatty atrophy | 778 |
| 4 | fatty replacement | 309 |
| 5 | fatty hilum | 269 |
| 6 | fatty stranding | 244 |
| 7 | fatty replaced | 121 |
| 8 | fatty lesion | 108 |
| 9 | fatty infiltrated | 106 |
| 10 | fatty hila | 97 |
| 11 | fatty changes | 50 |
| 12 | fatty in | 45 |
| 13 | fatty proliferation | 42 |
| 14 | fatty attenuation | 41 |
| 15 | fatty density | 38 |
| 16 | fatty tissue | 36 |
| 17 | fatty mass | 32 |
| 18 | fatty but | 32 |
| 19 | fatty without | 32 |
| 20 | fatty and | 32 |
| 21 | fatty hilus | 28 |
| 22 | fatty with | 26 |
| 23 | fatty infiltrate | 22 |
| 24 | fatty deposit | 21 |
| 25 | fatty tissues | 20 |
| 26 | fatty inflammatory | 19 |
| 27 | fatty hypertrophy | 18 |
| 28 | fatty appearance | 14 |
| 29 | fatty component | 14 |
| 30 | fatty rests | 14 |
| 31 | fatty deposits | 13 |
| 32 | fatty atrophied | 13 |
| 33 | fatty meal | 12 |
| 34 | fatty mural | 12 |
| 35 | fatty filum | 12 |
| 36 | fatty rest | 11 |
| 37 | fatty muscular | 11 |
| 38 | fatty muscle | 11 |
| 39 | fatty inguinal | 10 |
| 40 | fatty nodule | 10 |
| 41 | fatty signal | 10 |
| 42 | fatty infiltrates | 10 |
| 43 | fatty degeneration | 10 |
| 44 | fatty hepatic | 8 |
| 45 | fatty center | 8 |
| 46 | fatty streaking | 8 |
| 47 | fatty structure | 7 |
| 48 | fatty hemangiomas | 7 |
| 49 | fatty metaplasia | 7 |
| 50 | fatty lesions | 7 |

### preceding token + `fatty` (top 50)

| # | fragment | count |
| ---: | --- | ---: |
| 1 | with fatty | 1,158 |
| 2 | <s> fatty | 695 |
| 3 | is fatty | 451 |
| 4 | focal fatty | 390 |
| 5 | diffuse fatty | 342 |
| 6 | mild fatty | 260 |
| 7 | a fatty | 200 |
| 8 | of fatty | 154 |
| 9 | diffusely fatty | 133 |
| 10 | and fatty | 126 |
| 11 | to fatty | 101 |
| 12 | adjacent fatty | 89 |
| 13 | severe fatty | 83 |
| 14 | suggesting fatty | 58 |
| 15 | moderate fatty | 51 |
| 16 | predominantly fatty | 45 |
| 17 | preserved fatty | 42 |
| 18 | extensive fatty | 42 |
| 19 | heterogeneous fatty | 38 |
| 20 | cm fatty | 38 |
| 21 | the fatty | 38 |
| 22 | subcutaneous fatty | 33 |
| 23 | surrounding fatty | 32 |
| 24 | demonstrates fatty | 32 |
| 25 | or fatty | 30 |
| 26 | demonstrate fatty | 29 |
| 27 | asymmetric fatty | 27 |
| 28 | marked fatty | 27 |
| 29 | submucosal fatty | 25 |
| 30 | significant fatty | 24 |
| 31 | central fatty | 24 |
| 32 | mildly fatty | 24 |
| 33 | appears fatty | 23 |
| 34 | small fatty | 20 |
| 35 | some fatty | 20 |
| 36 | associated fatty | 19 |
| 37 | indicate fatty | 19 |
| 38 | borderline fatty | 18 |
| 39 | representing fatty | 18 |
| 40 | likely fatty | 18 |
| 41 | partially fatty | 17 |
| 42 | suggest fatty | 17 |
| 43 | represents fatty | 16 |
| 44 | slightly fatty | 16 |
| 45 | mm fatty | 16 |
| 46 | intramural fatty | 16 |
| 47 | suggests fatty | 16 |
| 48 | from fatty | 15 |
| 49 | partial fatty | 14 |
| 50 | prominent fatty | 14 |

### trigrams centered on `fatty` (top 30)

| # | fragment | count |
| ---: | --- | ---: |
| 1 | with fatty </s> | 624 |
| 2 | with fatty deposition | 401 |
| 3 | focal fatty deposition | 166 |
| 4 | focal fatty </s> | 162 |
| 5 | <s> fatty atrophy | 129 |
| 6 | <s> fatty deposition | 127 |
| 7 | is fatty </s> | 124 |
| 8 | diffuse fatty atrophy | 121 |
| 9 | is fatty atrophy | 116 |
| 10 | mild fatty atrophy | 108 |
| 11 | diffuse fatty </s> | 100 |
| 12 | a fatty hilum | 94 |
| 13 | adjacent fatty stranding | 73 |
| 14 | mild fatty </s> | 69 |
| 15 | <s> fatty </s> | 64 |
| 16 | severe fatty atrophy | 61 |
| 17 | diffusely fatty </s> | 60 |
| 18 | diffuse fatty deposition | 59 |
| 19 | <s> fatty replacement | 52 |
| 20 | of fatty </s> | 52 |
| 21 | <s> fatty hilum | 51 |
| 22 | to fatty deposition | 43 |
| 23 | to fatty </s> | 40 |
| 24 | is fatty replacement | 38 |
| 25 | with fatty replacement | 37 |
| 26 | suggesting fatty </s> | 36 |
| 27 | diffusely fatty infiltrated | 35 |
| 28 | is fatty infiltrated | 33 |
| 29 | <s> fatty stranding | 31 |
| 30 | mild fatty deposition | 29 |

## Step 3 — Characterize the unique contributors (bare-`fatty`-ONLY admissions)

Bare-`fatty` hits in ONLY admissions: 10,977.

### Producing `fatty`+next bigrams, ranked

| # | fragment | count |
| ---: | --- | ---: |
| 1 | fatty acids | 3,915 |
| 2 | fatty </s> | 1,283 |
| 3 | fatty atrophy | 826 |
| 4 | fatty deposition | 669 |
| 5 | fatty or | 611 |
| 6 | fatty foods | 441 |
| 7 | fatty hilum | 316 |
| 8 | fatty replacement | 294 |
| 9 | fatty stranding | 283 |
| 10 | fatty acid | 184 |
| 11 | fatty lesion | 120 |
| 12 | fatty replaced | 119 |
| 13 | fatty meal | 115 |
| 14 | fatty hila | 108 |
| 15 | fatty tissue | 100 |
| 16 | fatty meals | 82 |
| 17 | fatty mass | 75 |
| 18 | fatty food | 71 |
| 19 | fatty deposits | 67 |
| 20 | fatty changes | 57 |
| 21 | fatty infiltrated | 49 |
| 22 | fatty and | 47 |
| 23 | fatty density | 46 |
| 24 | fatty proliferation | 39 |
| 25 | fatty attenuation | 37 |
| 26 | fatty tumor | 35 |
| 27 | fatty infiltrate | 31 |
| 28 | fatty hilus | 31 |
| 29 | fatty tissues | 28 |
| 30 | fatty deposit | 27 |
| 31 | fatty in | 26 |
| 32 | fatty inflammatory | 25 |
| 33 | fatty rests | 17 |
| 34 | fatty component | 16 |
| 35 | fatty rest | 15 |
| 36 | fatty atrophied | 15 |
| 37 | fatty necrosis | 15 |
| 38 | fatty without | 15 |
| 39 | fatty acids/vitamin | 14 |
| 40 | fatty filum | 14 |

- Source of ONLY admissions: discharge-only 5,025 · radiology-only 2,459 · both 658.
- Code split of ONLY admissions: code+ 87 · code− 8,055.

### Phrase classes (assigned by token following `fatty`; you verify/reassign)

| class | description | hits |
| --- | --- | ---: |
| a | plausible steatosis phrasing | 1,937 |
| b | clearly not steatosis | 5,026 |
| c | ambiguous / organ-uncertain | 4,014 |

**Class a (plausible steatosis phrasing) — phrases assigned:** fatty atrophy (826), fatty deposition (669), fatty replacement (294), fatty deposits (67), fatty infiltrate (31), fatty deposit (27), fatty infiltrates (11), fatty degeneration (11), fatty metamorphosis (1)

**Class b (clearly not steatosis) — phrases assigned:** fatty acids (3915), fatty foods (441), fatty acid (184), fatty meal (115), fatty tissue (100), fatty meals (82), fatty food (71), fatty tumor (35), fatty tissues (28), fatty necrosis (15), fatty tumors (10), fatty stools (10), fatty stool (9), fatty plaque (5), fatty diarrhea (4), fatty casts (1), fatty hernia (1)

**Class c (ambiguous / organ-uncertain) — phrases assigned:** fatty </s> (1283), fatty or (611), fatty hilum (316), fatty stranding (283), fatty lesion (120), fatty replaced (119), fatty hila (108), fatty mass (75), fatty changes (57), fatty infiltrated (49), fatty and (47), fatty density (46), fatty proliferation (39), fatty attenuation (37), fatty hilus (31), fatty in (26), fatty inflammatory (25), fatty rests (17), fatty component (16), fatty rest (15), fatty atrophied (15), fatty without (15), fatty acids/vitamin (14), fatty filum (14), fatty muscle (14), fatty but (13), fatty muscular (13), fatty mural (13), fatty hypertrophy (13), fatty with (10)

## Step 4 — Stress the anatomical scoping

- Non-suppressed bare-`fatty` hits with a competing-organ token **somewhere in the same sentence** (not nearest): **20 / 15,126 (0.1%)**.
- Hits that passed with **NO liver/hepatic token in the sentence** (passed only because no competing organ present): **12,428 (82.2%)**.

### Distance from `fatty` to nearest liver/hepatic token

| distance (tokens) | hits |
| ---: | ---: |
| 0 | 0 |
| 1 | 35 |
| 2 | 306 |
| 3 | 745 |
| 4 | 532 |
| 5 | 234 |
| 6 | 453 |
| 7 | 183 |
| 8 | 134 |
| 9 | 51 |
| 10 | 16 |
| none in sentence | 12,428 |

## Step 5 — What dropping bare `fatty` would cost

Dropping the bare-`fatty` trigger would remove the **8,142 admissions** that are note-positive by bare `fatty` ONLY (code+ 87 / code− 8,055); the other 2,841 bare-`fatty` admissions remain positive via other Tier A triggers. No recommendation is made and no code is changed.
