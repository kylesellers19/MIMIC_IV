# Corpus Exploration — Hepatic Steatosis Documentation (unsupervised)

Aggregate frequency tables only. No note text, no windows, no identifiers were written. Reproducer: `scripts/corpus_explore.py`. Scope = full note corpus (discharge n=331,793; radiology n=2,321,355).

## Step 1 — Discharge section structure

Header candidates = line-initial `Label:` patterns. Top 40 of 176,597 distinct, by % of 331,793 discharge notes.

| header | notes | % notes | body len median | body p95 | body max |
| --- | ---: | ---: | ---: | ---: | ---: |
| NAME | 331,792 | 100.0 | 41 | 45 | 2,369 |
| DATE OF BIRTH | 331,787 | 100.0 | 30 | 30 | 114 |
| ADMISSION DATE | 331,782 | 100.0 | 44 | 44 | 318 |
| ALLERGIES | 331,666 | 100.0 | 49 | 95 | 3,839 |
| SERVICE | 331,581 | 99.9 | 13 | 19 | 2,906 |
| ATTENDING | 331,103 | 99.8 | 9 | 9 | 2,063 |
| DISCHARGE CONDITION | 330,920 | 99.7 | 2 | 88 | 4,034 |
| MAJOR SURGICAL OR INVASIVE PROCEDURE | 330,430 | 99.6 | 18 | 155 | 4,937 |
| DISCHARGE INSTRUCTIONS | 329,216 | 99.2 | 647 | 1,959 | 11,867 |
| DISCHARGE DISPOSITION | 327,479 | 98.7 | 9 | 22 | 446 |
| PAST MEDICAL HISTORY | 326,636 | 98.4 | 144 | 772 | 14,592 |
| HISTORY OF PRESENT ILLNESS | 326,392 | 98.4 | 917 | 2,403 | 12,160 |
| FOLLOWUP INSTRUCTIONS | 325,779 | 98.2 | 6 | 6 | 543 |
| DISCHARGE MEDICATIONS | 325,039 | 98.0 | 367 | 1,131 | 6,166 |
| SOCIAL HISTORY | 322,962 | 97.3 | 6 | 6 | 5,591 |
| FAMILY HISTORY | 321,643 | 96.9 | 57 | 242 | 4,629 |
| CHIEF COMPLAINT | 320,650 | 96.6 | 24 | 62 | 3,425 |
| PERTINENT RESULTS | 319,318 | 96.2 | 316 | 2,461 | 25,028 |
| DISCHARGE DIAGNOSIS | 318,352 | 95.9 | 32 | 197 | 2,647 |
| PHYSICAL EXAM | 317,535 | 95.7 | 2 | 295 | 5,206 |
| MEDICATIONS ON ADMISSION | 312,737 | 94.3 | 290 | 964 | 27,381 |
| BRIEF HOSPITAL COURSE | 291,905 | 88.0 | 1,284 | 4,129 | 24,981 |
| MENTAL STATUS | 257,784 | 77.7 | 22 | 55 | 2,948 |
| LEVEL OF CONSCIOUSNESS | 252,528 | 76.1 | 25 | 25 | 1,466 |
| ACTIVITY STATUS | 251,627 | 75.8 | 31 | 64 | 2,440 |
| HEENT | 211,662 | 63.8 | 49 | 142 | 1,936 |
| GENERAL | 165,668 | 49.9 | 41 | 111 | 4,718 |
| NEURO | 164,326 | 49.5 | 63 | 252 | 9,565 |
| FACILITY | 151,575 | 45.7 | 8 | 50 | 1,400 |
| CV | 147,278 | 44.4 | 44 | 109 | 2,950 |
| NECK | 145,381 | 43.8 | 31 | 80 | 3,599 |
| ABDOMEN | 135,902 | 41.0 | 72 | 160 | 3,400 |
| SKIN | 133,334 | 40.2 | 35 | 146 | 2,877 |
| EXT | 128,789 | 38.8 | 50 | 182 | 5,122 |
| LUNGS | 123,469 | 37.2 | 59 | 141 | 1,401 |
| IMPRESSION | 122,091 | 36.8 | 280 | 1,541 | 18,357 |
| ABD | 108,822 | 32.8 | 55 | 160 | 2,529 |
| GEN | 98,132 | 29.6 | 30 | 100 | 2,606 |
| VITALS | 96,486 | 29.1 | 43 | 160 | 4,125 |
| EXTREMITIES | 94,698 | 28.5 | 48 | 176 | 4,653 |

## Step 2 — Seed-term frequency

Case-insensitive, word-boundary. 'section' = modal enclosing discharge section.

| term | DC notes | DC % | DC adm | top DC section | RAD notes | RAD % | RAD adm |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| steatosis | 5,883 | 1.77 | 5,883 | IMPRESSION | 21,914 | 0.94 | 6,732 |
| steatotic | 82 | 0.02 | 82 | BRIEF HOSPITAL COURSE | 236 | 0.01 | 83 |
| fatty liver | 5,175 | 1.56 | 5,175 | PAST MEDICAL HISTORY | 5,885 | 0.25 | 2,015 |
| fatty infiltration | 1,975 | 0.60 | 1,975 | IMPRESSION | 12,401 | 0.53 | 4,323 |
| hepatic steatosis | 3,220 | 0.97 | 3,220 | IMPRESSION | 13,014 | 0.56 | 4,133 |
| NAFLD | 637 | 0.19 | 637 | PAST MEDICAL HISTORY | 159 | 0.01 | 35 |
| NASH | 3,116 | 0.94 | 3,116 | HISTORY OF PRESENT ILLNESS | 3,637 | 0.16 | 898 |
| MASLD | 0 | 0.00 | 0 | - | 0 | 0.00 | 0 |
| MASH | 11 | 0.00 | 11 | HISTORY OF PRESENT ILLNESS | 5 | 0.00 | 2 |
| hepatic echogenicity | 49 | 0.01 | 49 | IMPRESSION | 252 | 0.01 | 90 |
| fatty change | 111 | 0.03 | 111 | IMPRESSION | 620 | 0.03 | 199 |

## Step 3 — Discovered terms (I did not seed these)

### 3a. Content unigrams in ±4-word windows around seed hits (stopwords removed), top 100

| # | unigram | count | | # | unigram | count |
| ---: | --- | ---: | --- | ---: | --- | ---: |
| 1 | liver | 35,372 | | 2 | hepatic | 18,680 |
| 3 | steatosis | 16,367 | | 4 | consistent | 15,603 |
| 5 | infiltration | 14,574 | | 6 | there | 13,716 |
| 7 | echogenic | 9,986 | | 8 | other | 7,750 |
| 9 | forms | 7,548 | | 10 | focal | 6,869 |
| 11 | cirrhosis | 6,215 | | 12 | evidence | 5,992 |
| 13 | mild | 5,675 | | 14 | diffuse | 4,924 |
| 15 | compatible | 3,992 | | 16 | history | 2,812 |
| 17 | likely | 2,502 | | 18 | suggest | 2,411 |
| 19 | imaging | 2,252 | | 20 | disease | 2,177 |
| 21 | old | 2,134 | | 22 | diffusely | 2,107 |
| 23 | attenuation | 2,025 | | 24 | impression | 2,023 |
| 25 | abdomen | 1,944 | | 26 | year | 1,937 |
| 27 | phase | 1,870 | | 28 | lesions | 1,687 |
| 29 | suggestive | 1,655 | | 30 | gallbladder | 1,452 |
| 31 | fat | 1,435 | | 32 | severe | 1,419 |
| 33 | seen | 1,415 | | 34 | woman | 1,411 |
| 35 | more | 1,396 | | 36 | biliary | 1,393 |
| 37 | throughout | 1,381 | | 38 | normal | 1,368 |
| 39 | echogenicity | 1,311 | | 40 | images | 1,299 |
| 41 | lesion | 1,281 | | 42 | man | 1,270 |
| 43 | moderate | 1,259 | | 44 | pancreas | 1,254 |
| 45 | ascites | 1,236 | | 46 | small | 1,223 |
| 47 | findings | 1,215 | | 48 | ultrasound | 1,190 |
| 49 | spleen | 1,114 | | 50 | contour | 1,114 |
| 51 | exclude | 1,085 | | 52 | radiological | 1,068 |
| 53 | suspicious | 1,067 | | 54 | does | 1,063 |
| 55 | noted | 1,061 | | 56 | significant | 1,060 |
| 57 | most | 1,048 | | 58 | ct | 1,023 |
| 59 | demonstrates | 1,017 | | 60 | suggesting | 1,013 |
| 61 | left | 977 | | 62 | iron | 977 |
| 63 | hypodense | 967 | | 64 | however | 951 |
| 65 | fraction | 924 | | 66 | hepatobiliary | 923 |
| 67 | right | 919 | | 68 | may | 918 |
| 69 | areas | 910 | | 70 | advanced | 896 |
| 71 | indication | 888 | | 72 | technique | 884 |
| 73 | unchanged | 876 | | 74 | portal | 870 |
| 75 | chronic | 854 | | 76 | change | 843 |
| 77 | multiple | 836 | | 78 | cholelithiasis | 828 |
| 79 | parenchyma | 827 | | 80 | deposition | 813 |
| 81 | again | 812 | | 82 | acute | 810 |
| 83 | due | 797 | | 84 | presence | 792 |
| 85 | patient | 777 | | 86 | but | 773 |
| 87 | prior | 738 | | 88 | abdominal | 737 |
| 89 | study | 720 | | 90 | unremarkable | 686 |
| 91 | hypertension | 673 | | 92 | concerning | 665 |
| 93 | splenomegaly | 662 | | 94 | low | 641 |
| 95 | hypoattenuating | 634 | | 96 | upper | 632 |
| 97 | increased | 632 | | 98 | fatty | 628 |
| 99 | fibrosis | 627 | | 100 | within | 627 |

### 3b. Bigrams in seed windows, top 100

| # | bigram | count |
| ---: | --- | ---: |
| 1 | hepatic steatosis | 31,914 |
| 2 | consistent with | 15,533 |
| 3 | fatty infiltration | 14,395 |
| 4 | there is | 11,489 |
| 5 | fatty liver | 11,156 |
| 6 | echogenic liver | 7,509 |
| 7 | liver consistent | 7,468 |
| 8 | other forms | 7,027 |
| 9 | with steatosis | 6,705 |
| 10 | forms of | 6,678 |
| 11 | is no | 6,199 |
| 12 | with fatty | 6,075 |
| 13 | with hepatic | 5,739 |
| 14 | steatosis there | 5,614 |
| 15 | steatosis other | 5,194 |
| 16 | of the | 5,156 |
| 17 | the liver | 5,127 |
| 18 | of liver | 4,994 |
| 19 | nash cirrhosis | 4,045 |
| 20 | evidence of | 4,045 |
| 21 | compatible with | 3,938 |
| 22 | infiltration of | 3,902 |
| 23 | steatosis no | 3,579 |
| 24 | no evidence | 3,481 |
| 25 | of hepatic | 3,399 |
| 26 | no focal | 3,063 |
| 27 | steatosis the | 2,853 |
| 28 | mild hepatic | 2,454 |
| 29 | of fatty | 2,397 |
| 30 | with nash | 2,379 |
| 31 | diffuse hepatic | 2,191 |
| 32 | 2 hepatic | 2,053 |
| 33 | diffuse fatty | 2,050 |
| 34 | 3 hepatic | 1,888 |
| 35 | steatosis with | 1,881 |
| 36 | year old | 1,870 |
| 37 | to suggest | 1,851 |
| 38 | no hepatic | 1,796 |
| 39 | focal fatty | 1,674 |
| 40 | echogenic consistent | 1,634 |
| 41 | suggestive of | 1,614 |
| 42 | there are | 1,600 |
| 43 | suggest hepatic | 1,472 |
| 44 | liver disease | 1,449 |
| 45 | woman with | 1,395 |
| 46 | infiltration other | 1,335 |
| 47 | is diffuse | 1,324 |
| 48 | infiltration the | 1,320 |
| 49 | steatosis 3 | 1,318 |
| 50 | imaging to | 1,303 |
| 51 | focal liver | 1,295 |
| 52 | infiltration there | 1,279 |
| 53 | man with | 1,260 |
| 54 | history of | 1,254 |
| 55 | impression 1 | 1,251 |
| 56 | diffusely echogenic | 1,190 |
| 57 | infiltration no | 1,134 |
| 58 | steatosis or | 1,108 |
| 59 | old woman | 1,094 |
| 60 | is a | 1,082 |
| 61 | is mild | 1,067 |
| 62 | 2 fatty | 1,058 |
| 63 | radiological evidence | 1,036 |
| 64 | does not | 1,030 |
| 65 | 4 hepatic | 1,020 |
| 66 | not exclude | 1,011 |
| 67 | liver does | 1,009 |
| 68 | steatosis 4 | 985 |
| 69 | old man | 962 |
| 70 | s radiological | 957 |
| 71 | mild fatty | 934 |
| 72 | phase imaging | 916 |
| 73 | steatosis and | 913 |
| 74 | with mild | 906 |
| 75 | fat fraction | 884 |
| 76 | no suspicious | 870 |
| 77 | focal hepatic | 863 |
| 78 | the gallbladder | 853 |
| 79 | 3 fatty | 852 |
| 80 | of steatosis | 843 |
| 81 | steatosis a | 826 |
| 82 | liver is | 825 |
| 83 | of nash | 819 |
| 84 | contour of | 800 |
| 85 | presence of | 788 |
| 86 | the contour | 785 |
| 87 | due to | 770 |
| 88 | liver compatible | 763 |
| 89 | iron deposition | 755 |
| 90 | in the | 747 |
| 91 | the pancreas | 744 |
| 92 | or iron | 738 |
| 93 | are no | 734 |
| 94 | fatty change | 731 |
| 95 | steatosis is | 722 |
| 96 | the presence | 703 |
| 97 | severe hepatic | 700 |
| 98 | more advanced | 698 |
| 99 | cirrhosis and | 695 |
| 100 | attenuation consistent | 695 |

### 3c. Corpus bigrams/trigrams containing 'liver' or 'hepatic', top 150

| # | n-gram | count |
| ---: | --- | ---: |
| 1 | the liver | 384,999 |
| 2 | liver is | 103,983 |
| 3 | the liver is | 97,497 |
| 4 | liver demonstrates | 65,333 |
| 5 | the hepatic | 64,169 |
| 6 | the liver demonstrates | 62,969 |
| 7 | focal liver | 59,135 |
| 8 | right hepatic | 53,455 |
| 9 | liver disease | 49,352 |
| 10 | liver the | 47,971 |
| 11 | hepatic artery | 47,714 |
| 12 | liver lesions | 42,351 |
| 13 | left hepatic | 39,830 |
| 14 | hepatic lobe | 35,747 |
| 15 | of liver | 34,425 |
| 16 | findings liver | 33,761 |
| 17 | hepatic veins | 32,084 |
| 18 | liver transplant | 30,317 |
| 19 | liver mass | 30,300 |
| 20 | findings liver the | 29,728 |
| 21 | extra hepatic | 29,578 |
| 22 | hepatic parenchyma | 28,976 |
| 23 | liver or | 27,837 |
| 24 | liver lesion | 27,773 |
| 25 | liver and | 27,690 |
| 26 | hepatic biliary | 26,114 |
| 27 | focal liver mass | 24,926 |
| 28 | the hepatic parenchyma | 24,719 |
| 29 | extra hepatic biliary | 23,189 |
| 30 | examination liver | 23,045 |
| 31 | hepatic steatosis | 22,852 |
| 32 | examination liver or | 22,831 |
| 33 | liver biopsy | 22,673 |
| 34 | hepatic lesions | 22,133 |
| 35 | right hepatic lobe | 21,963 |
| 36 | focal liver lesions | 21,651 |
| 37 | and hepatic | 20,054 |
| 38 | common hepatic | 19,469 |
| 39 | liver with | 19,031 |
| 40 | hepatic encephalopathy | 18,733 |
| 41 | liver gallbladder | 17,212 |
| 42 | of liver disease | 16,006 |
| 43 | focal hepatic | 15,992 |
| 44 | hepatic duct | 15,979 |
| 45 | your liver | 15,922 |
| 46 | cirrhotic liver | 15,163 |
| 47 | fatty liver | 14,847 |
| 48 | echogenic liver | 14,602 |
| 49 | liver consistent | 14,350 |
| 50 | the liver and | 13,904 |
| 51 | liver spleen | 13,901 |
| 52 | liver enhances | 13,070 |
| 53 | left hepatic lobe | 12,971 |
| 54 | and liver | 12,848 |
| 55 | the liver enhances | 12,226 |
| 56 | hepatic lesion | 12,087 |
| 57 | hepatic vasculature | 12,082 |
| 58 | right hepatic artery | 11,930 |
| 59 | hepatic vein | 11,921 |
| 60 | of hepatic | 11,766 |
| 61 | focal liver lesion | 11,723 |
| 62 | hepatic arterial | 11,517 |
| 63 | and hepatic veins | 11,493 |
| 64 | the liver spleen | 11,471 |
| 65 | the liver gallbladder | 11,318 |
| 66 | liver function | 11,200 |
| 67 | patent hepatic | 10,751 |
| 68 | the hepatic veins | 10,487 |
| 69 | main hepatic | 10,375 |
| 70 | hepatic fibrosis | 10,371 |
| 71 | left hepatic artery | 10,088 |
| 72 | hepatic segment | 9,704 |
| 73 | liver parenchyma | 9,691 |
| 74 | echogenic liver consistent | 9,568 |
| 75 | liver there | 9,447 |
| 76 | with liver | 9,213 |
| 77 | common hepatic duct | 8,958 |
| 78 | focal hepatic lesions | 8,761 |
| 79 | hepatic cysts | 8,566 |
| 80 | liver which | 8,124 |
| 81 | p liver | 7,991 |
| 82 | for liver | 7,979 |
| 83 | to liver | 7,832 |
| 84 | patent hepatic vasculature | 7,801 |
| 85 | main hepatic artery | 7,787 |
| 86 | with hepatic | 7,703 |
| 87 | liver failure | 7,523 |
| 88 | the liver the | 7,448 |
| 89 | hepatic cyst | 7,447 |
| 90 | hepatic and | 7,351 |
| 91 | cirrhotic liver with | 7,176 |
| 92 | common hepatic artery | 7,146 |
| 93 | post liver | 7,052 |
| 94 | liver are | 6,983 |
| 95 | liver appears | 6,925 |
| 96 | targeted liver | 6,754 |
| 97 | liver ultrasound | 6,707 |
| 98 | hepatic arteries | 6,674 |
| 99 | the liver which | 6,672 |
| 100 | the liver there | 6,583 |
| 101 | the liver with | 6,555 |
| 102 | targeted liver biopsy | 6,526 |
| 103 | effusion liver | 6,455 |
| 104 | hepatic dome | 6,369 |
| 105 | in hepatic | 6,335 |
| 106 | the liver appears | 6,181 |
| 107 | advanced liver | 6,104 |
| 108 | a liver | 6,068 |
| 109 | hepatic flexure | 6,048 |
| 110 | advanced liver disease | 6,015 |
| 111 | p liver transplant | 5,994 |
| 112 | the liver parenchyma | 5,947 |
| 113 | liver enzymes | 5,926 |
| 114 | the liver are | 5,732 |
| 115 | significant hepatic | 5,663 |
| 116 | post liver transplant | 5,600 |
| 117 | liver shows | 5,465 |
| 118 | right hepatic vein | 5,283 |
| 119 | hepatic mass | 5,160 |
| 120 | in hepatic segment | 5,074 |
| 121 | significant hepatic fibrosis | 5,053 |
| 122 | multiple hepatic | 5,016 |
| 123 | chronic liver | 5,005 |
| 124 | the liver shows | 4,935 |
| 125 | liver without | 4,909 |
| 126 | comparison liver | 4,839 |
| 127 | focal hepatic lesion | 4,763 |
| 128 | liver has | 4,731 |
| 129 | liver no | 4,600 |
| 130 | the hepatic flexure | 4,508 |
| 131 | hepatic bile | 4,499 |
| 132 | hepatic hypodensities | 4,479 |
| 133 | in liver | 4,439 |
| 134 | chronic liver disease | 4,433 |
| 135 | liver 2 | 4,378 |
| 136 | liver measuring | 4,374 |
| 137 | elevated liver | 4,368 |
| 138 | the liver has | 4,293 |
| 139 | hepatic metastases | 4,255 |
| 140 | liver was | 4,220 |
| 141 | liver on | 4,173 |
| 142 | the hepatic dome | 4,170 |
| 143 | liver cirrhosis | 4,144 |
| 144 | the liver measuring | 4,141 |
| 145 | liver cancer | 4,045 |
| 146 | concerning liver | 4,035 |
| 147 | underlying liver | 4,030 |
| 148 | hepatic architecture | 4,024 |
| 149 | extra hepatic bile | 4,003 |
| 150 | hepatic arteriogram | 3,906 |

### 3d. Hedging / uncertainty phrases (note frequency, corpus)

| phrase | notes |
| --- | ---: |
| cannot exclude | 1,900 |
| cannot be excluded | 22,600 |
| may represent | 33,464 |
| no evidence of | 213,232 |
| query | 1,915 |
| concerning for | 70,838 |
| suggestive of | 35,791 |
| consistent with | 123,949 |
| likely represents | 24,715 |

## Step 4 — Negation / context cues in preceding 5 tokens of seed hits

Total seed hits scanned (first hit per note): 78,382.

| cue | hits with cue | % of hits |
| --- | ---: | ---: |
| no | 5,983 | 7.6 |
| without | 1,007 | 1.3 |
| denies | 10 | 0.0 |
| versus | 71 | 0.1 |
| vs | 134 | 0.2 |
| negative for | 5 | 0.0 |
| family history of | 1 | 0.0 |
| history of | 1,258 | 1.6 |
| ruled out | 2 | 0.0 |
| rule out | 44 | 0.1 |

## Step 5 — Coverage sanity check (NOT a recovery estimate)

- Code-positive locked admissions with ≥1 seed hit in any linked note: **4,723 / 5,740 (82.3%)** — face-validity check on the seed set.
- Code-NEGATIVE locked admissions with ≥1 seed hit (raw count): **15,650** of 368,252.
- Outpatient (null-hadm) radiology added seed hits for 14,685 distinct subjects (not counted above; subject-linked, for later).

> This is UNADJUDICATED and UNNEGATED and is NOT the 2×2 or the Aim-1a recovery estimate. It is only a face-validity check on the seed set. The code-negative count includes negated and historical mentions and is not a count of missed cases.
