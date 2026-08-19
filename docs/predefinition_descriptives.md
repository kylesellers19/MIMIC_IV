# Pre-adjudication Descriptives — MASLD / MIMIC-IV

> **Descriptive only. These characterize two computable phenotypes (ICD code vs
> frozen note rule v1.1.0) and the recovery-zone context. No adjudication has
> occurred; nothing here is a MASLD prevalence or a recovery estimate.** The note
> phenotype captures **steatosis**, not MASLD — MASLD additionally requires a
> cardiometabolic criterion and exclusion of competing etiologies, both of which
> are quantified below as gaps for the researcher to resolve.

Population: cleaned locked analysis population, N = 373,992 admissions. Cell
assignment uses the PRIMARY definition (b: v1.1.0 + outpatient 365/30); note-positive
= Tier A definite. Read from CLEAN_POP. Reproducers: `scripts/predef_etio_metab.py`,
`imaging_denom.py`, `note_triggers.py`, `comorbid_cluster.py`, `sample_rep.py`.

---
## Step 1 — Competing liver disease (code sets shown for verification)

Version-aware, dotless. Matched codes with `long_title` from d_icd_diagnoses:


<details><summary>Alcohol-related liver disease (K70; 571.0-571.3) — 17 codes </summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | K70 | Alcoholic liver disease |
| 10 | K700 | Alcoholic fatty liver |
| 10 | K701 | Alcoholic hepatitis |
| 10 | K7010 | Alcoholic hepatitis without ascites |
| 10 | K7011 | Alcoholic hepatitis with ascites |
| 10 | K702 | Alcoholic fibrosis and sclerosis of liver |
| 10 | K703 | Alcoholic cirrhosis of liver |
| 10 | K7030 | Alcoholic cirrhosis of liver without ascites |
| 10 | K7031 | Alcoholic cirrhosis of liver with ascites |
| 10 | K704 | Alcoholic hepatic failure |
| 10 | K7040 | Alcoholic hepatic failure without coma |
| 10 | K7041 | Alcoholic hepatic failure with coma |
| 10 | K709 | Alcoholic liver disease, unspecified |
| 9 | 5710 | Alcoholic fatty liver |
| 9 | 5711 | Acute alcoholic hepatitis |
| 9 | 5712 | Alcoholic cirrhosis of liver |
| 9 | 5713 | Alcoholic liver damage, unspecified |

</details>

<details><summary>Alcohol use disorder (F10; 303.x, 305.0x) — 86 codes </summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | F10 | Alcohol related disorders |
| 10 | F101 | Alcohol abuse |
| 10 | F1010 | Alcohol abuse, uncomplicated |
| 10 | F1011 | Alcohol abuse, in remission |
| 10 | F1012 | Alcohol abuse with intoxication |
| 10 | F10120 | Alcohol abuse with intoxication, uncomplicated |
| 10 | F10121 | Alcohol abuse with intoxication delirium |
| 10 | F10129 | Alcohol abuse with intoxication, unspecified |
| 10 | F1013 | Alcohol abuse, with withdrawal |
| 10 | F10130 | Alcohol abuse with withdrawal, uncomplicated |
| 10 | F10131 | Alcohol abuse with withdrawal delirium |
| 10 | F10132 | Alcohol abuse with withdrawal with perceptual disturbance |
| 10 | F10139 | Alcohol abuse with withdrawal, unspecified |
| 10 | F1014 | Alcohol abuse with alcohol-induced mood disorder |
| 10 | F1015 | Alcohol abuse with alcohol-induced psychotic disorder |
| 10 | F10150 | Alcohol abuse with alcohol-induced psychotic disorder with delusions |
| 10 | F10151 | Alcohol abuse with alcohol-induced psychotic disorder with hallucinations |
| 10 | F10159 | Alcohol abuse with alcohol-induced psychotic disorder, unspecified |
| 10 | F1018 | Alcohol abuse with other alcohol-induced disorders |
| 10 | F10180 | Alcohol abuse with alcohol-induced anxiety disorder |
| 10 | F10181 | Alcohol abuse with alcohol-induced sexual dysfunction |
| 10 | F10182 | Alcohol abuse with alcohol-induced sleep disorder |
| 10 | F10188 | Alcohol abuse with other alcohol-induced disorder |
| 10 | F1019 | Alcohol abuse with unspecified alcohol-induced disorder |
| 10 | F102 | Alcohol dependence |
| … | … | (+61 more) |

</details>

<details><summary>Viral hepatitis B/C (B18,B19; 070.x) — 39 codes </summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | B18 | Chronic viral hepatitis |
| 10 | B180 | Chronic viral hepatitis B with delta-agent |
| 10 | B181 | Chronic viral hepatitis B without delta-agent |
| 10 | B182 | Chronic viral hepatitis C |
| 10 | B188 | Other chronic viral hepatitis |
| 10 | B189 | Chronic viral hepatitis, unspecified |
| 10 | B19 | Unspecified viral hepatitis |
| 10 | B190 | Unspecified viral hepatitis with hepatic coma |
| 10 | B191 | Unspecified viral hepatitis B |
| 10 | B1910 | Unspecified viral hepatitis B without hepatic coma |
| 10 | B1911 | Unspecified viral hepatitis B with hepatic coma |
| 10 | B192 | Unspecified viral hepatitis C |
| 10 | B1920 | Unspecified viral hepatitis C without hepatic coma |
| 10 | B1921 | Unspecified viral hepatitis C with hepatic coma |
| 10 | B199 | Unspecified viral hepatitis without hepatic coma |
| 9 | 0700 | Viral hepatitis A with hepatic coma |
| 9 | 0701 | Viral hepatitis A without mention of hepatic coma |
| 9 | 07020 | Viral hepatitis B with hepatic coma, acute or unspecified, without mention of hepatitis delta |
| 9 | 07021 | Viral hepatitis B with hepatic coma, acute or unspecified, with hepatitis delta |
| 9 | 07022 | Chronic viral hepatitis B with hepatic coma without hepatitis delta |
| 9 | 07023 | Chronic viral hepatitis B with hepatic coma with hepatitis delta |
| 9 | 07030 | Viral hepatitis B without mention of hepatic coma, acute or unspecified, without mention of hepatitis delta |
| 9 | 07031 | Viral hepatitis B without mention of hepatic coma, acute or unspecified, with hepatitis delta |
| 9 | 07032 | Chronic viral hepatitis B without mention of hepatic coma without mention of hepatitis delta |
| 9 | 07033 | Chronic viral hepatitis B without mention of hepatic coma with hepatitis delta |
| … | … | (+14 more) |

</details>

<details><summary>Other etiology (AIH,PBC,PSC,hemochromatosis,Wilson,A1AT) — 13 codes </summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | E8301 | Wilson's disease |
| 10 | E8311 | Hemochromatosis |
| 10 | E8801 | Alpha-1-antitrypsin deficiency |
| 10 | K743 | Primary biliary cirrhosis |
| 10 | K754 | Autoimmune hepatitis |
| 10 | K830 | Cholangitis |
| 9 | 2734 | Alpha-1-antitrypsin deficiency |
| 9 | 27501 | Hereditary hemochromatosis |
| 9 | 27503 | Other hemochromatosis |
| 9 | 2751 | Disorders of copper metabolism |
| 9 | 57142 | Autoimmune hepatitis |
| 9 | 5716 | Biliary cirrhosis |
| 9 | 5761 | Cholangitis |

</details>

<details><summary>Cirrhosis & complications (K74,K76.6,K72; 571.5,572.x) — 31 codes </summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | K72 | Hepatic failure, not elsewhere classified |
| 10 | K720 | Acute and subacute hepatic failure |
| 10 | K7200 | Acute and subacute hepatic failure without coma |
| 10 | K7201 | Acute and subacute hepatic failure with coma |
| 10 | K721 | Chronic hepatic failure |
| 10 | K7210 | Chronic hepatic failure without coma |
| 10 | K7211 | Chronic hepatic failure with coma |
| 10 | K729 | Hepatic failure, unspecified |
| 10 | K7290 | Hepatic failure, unspecified without coma |
| 10 | K7291 | Hepatic failure, unspecified with coma |
| 10 | K74 | Fibrosis and cirrhosis of liver |
| 10 | K740 | Hepatic fibrosis |
| 10 | K7400 | Hepatic fibrosis, unspecified |
| 10 | K7401 | Hepatic fibrosis, early fibrosis |
| 10 | K7402 | Hepatic fibrosis, advanced fibrosis |
| 10 | K741 | Hepatic sclerosis |
| 10 | K742 | Hepatic fibrosis with hepatic sclerosis |
| 10 | K743 | Primary biliary cirrhosis |
| 10 | K744 | Secondary biliary cirrhosis |
| 10 | K745 | Biliary cirrhosis, unspecified |
| 10 | K746 | Other and unspecified cirrhosis of liver |
| 10 | K7460 | Unspecified cirrhosis of liver |
| 10 | K7469 | Other cirrhosis of liver |
| 10 | K766 | Portal hypertension |
| 9 | 5715 | Cirrhosis of liver without mention of alcohol |
| … | … | (+6 more) |

</details>

<details><summary>Hepatocellular carcinoma (C22.0; 155.0) — 2 codes </summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | C220 | Liver cell carcinoma |
| 9 | 1550 | Malignant neoplasm of liver, primary |

</details>

<details><summary>Overweight/obesity (E66,Z68; 278.0x) — 48 codes **[Step 2 cardiometabolic]**</summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | E66 | Overweight and obesity |
| 10 | E660 | Obesity due to excess calories |
| 10 | E6601 | Morbid (severe) obesity due to excess calories |
| 10 | E6609 | Other obesity due to excess calories |
| 10 | E661 | Drug-induced obesity |
| 10 | E662 | Morbid (severe) obesity with alveolar hypoventilation |
| 10 | E663 | Overweight |
| 10 | E668 | Other obesity |
| 10 | E669 | Obesity, unspecified |
| 10 | Z68 | Body mass index [BMI] |
| 10 | Z681 | Body mass index [BMI] 19.9 or less, adult |
| 10 | Z682 | Body mass index [BMI] 20-29, adult |
| 10 | Z6820 | Body mass index [BMI] 20.0-20.9, adult |
| 10 | Z6821 | Body mass index [BMI] 21.0-21.9, adult |
| 10 | Z6822 | Body mass index [BMI] 22.0-22.9, adult |
| 10 | Z6823 | Body mass index [BMI] 23.0-23.9, adult |
| 10 | Z6824 | Body mass index [BMI] 24.0-24.9, adult |
| 10 | Z6825 | Body mass index [BMI] 25.0-25.9, adult |
| 10 | Z6826 | Body mass index [BMI] 26.0-26.9, adult |
| 10 | Z6827 | Body mass index [BMI] 27.0-27.9, adult |
| 10 | Z6828 | Body mass index [BMI] 28.0-28.9, adult |
| 10 | Z6829 | Body mass index [BMI] 29.0-29.9, adult |
| 10 | Z683 | Body mass index [BMI] 30-39, adult |
| 10 | Z6830 | Body mass index [BMI] 30.0-30.9, adult |
| 10 | Z6831 | Body mass index [BMI] 31.0-31.9, adult |
| … | … | (+23 more) |

</details>

<details><summary>Type-2 diabetes (E11; 250.x) — 156 codes **[Step 2 cardiometabolic]**</summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | E11 | Type 2 diabetes mellitus |
| 10 | E110 | Type 2 diabetes mellitus with hyperosmolarity |
| 10 | E1100 | Type 2 diabetes mellitus with hyperosmolarity without nonketotic hyperglycemic-hyperosmolar coma (NKHHC) |
| 10 | E1101 | Type 2 diabetes mellitus with hyperosmolarity with coma |
| 10 | E111 | Type 2 diabetes mellitus with ketoacidosis |
| 10 | E1110 | Type 2 diabetes mellitus with ketoacidosis without coma |
| 10 | E1111 | Type 2 diabetes mellitus with ketoacidosis with coma |
| 10 | E112 | Type 2 diabetes mellitus with kidney complications |
| 10 | E1121 | Type 2 diabetes mellitus with diabetic nephropathy |
| 10 | E1122 | Type 2 diabetes mellitus with diabetic chronic kidney disease |
| 10 | E1129 | Type 2 diabetes mellitus with other diabetic kidney complication |
| 10 | E113 | Type 2 diabetes mellitus with ophthalmic complications |
| 10 | E1131 | Type 2 diabetes mellitus with unspecified diabetic retinopathy |
| 10 | E11311 | Type 2 diabetes mellitus with unspecified diabetic retinopathy with macular edema |
| 10 | E11319 | Type 2 diabetes mellitus with unspecified diabetic retinopathy without macular edema |
| 10 | E1132 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy |
| 10 | E11321 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy with macular edema |
| 10 | E113211 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy with macular edema, right eye |
| 10 | E113212 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy with macular edema, left eye |
| 10 | E113213 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy with macular edema, bilateral |
| 10 | E113219 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy with macular edema, unspecified eye |
| 10 | E11329 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy without macular edema |
| 10 | E113291 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy without macular edema, right eye |
| 10 | E113292 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy without macular edema, left eye |
| 10 | E113293 | Type 2 diabetes mellitus with mild nonproliferative diabetic retinopathy without macular edema, bilateral |
| … | … | (+131 more) |

</details>

<details><summary>Hypertension (I10-I15; 401-405) — 52 codes **[Step 2 cardiometabolic]**</summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | I10 | Essential (primary) hypertension |
| 10 | I11 | Hypertensive heart disease |
| 10 | I110 | Hypertensive heart disease with heart failure |
| 10 | I119 | Hypertensive heart disease without heart failure |
| 10 | I12 | Hypertensive chronic kidney disease |
| 10 | I120 | Hypertensive chronic kidney disease with stage 5 chronic kidney disease or end stage renal disease |
| 10 | I129 | Hypertensive chronic kidney disease with stage 1 through stage 4 chronic kidney disease, or unspecified chronic kidney disease |
| 10 | I13 | Hypertensive heart and chronic kidney disease |
| 10 | I130 | Hypertensive heart and chronic kidney disease with heart failure and stage 1 through stage 4 chronic kidney disease, or unspecified chronic kidney disease |
| 10 | I131 | Hypertensive heart and chronic kidney disease without heart failure |
| 10 | I1310 | Hypertensive heart and chronic kidney disease without heart failure, with stage 1 through stage 4 chronic kidney disease, or unspecified chronic kidney disease |
| 10 | I1311 | Hypertensive heart and chronic kidney disease without heart failure, with stage 5 chronic kidney disease, or end stage renal disease |
| 10 | I132 | Hypertensive heart and chronic kidney disease with heart failure and with stage 5 chronic kidney disease, or end stage renal disease |
| 10 | I15 | Secondary hypertension |
| 10 | I150 | Renovascular hypertension |
| 10 | I151 | Hypertension secondary to other renal disorders |
| 10 | I152 | Hypertension secondary to endocrine disorders |
| 10 | I158 | Other secondary hypertension |
| 10 | I159 | Secondary hypertension, unspecified |
| 9 | 4010 | Malignant essential hypertension |
| 9 | 4011 | Benign essential hypertension |
| 9 | 4019 | Unspecified essential hypertension |
| 9 | 40200 | Malignant hypertensive heart disease without heart failure |
| 9 | 40201 | Malignant hypertensive heart disease with heart failure |
| 9 | 40210 | Benign hypertensive heart disease without heart failure |
| … | … | (+27 more) |

</details>

<details><summary>Dyslipidemia (E78; 272.x) — 31 codes **[Step 2 cardiometabolic]**</summary>

| v | code | long_title |
| --: | --- | --- |
| 10 | E78 | Disorders of lipoprotein metabolism and other lipidemias |
| 10 | E780 | Pure hypercholesterolemia |
| 10 | E7800 | Pure hypercholesterolemia, unspecified |
| 10 | E7801 | Familial hypercholesterolemia |
| 10 | E781 | Pure hyperglyceridemia |
| 10 | E782 | Mixed hyperlipidemia |
| 10 | E783 | Hyperchylomicronemia |
| 10 | E784 | Other hyperlipidemia |
| 10 | E7841 | Elevated Lipoprotein(a) |
| 10 | E7849 | Other hyperlipidemia |
| 10 | E785 | Hyperlipidemia, unspecified |
| 10 | E786 | Lipoprotein deficiency |
| 10 | E787 | Disorders of bile acid and cholesterol metabolism |
| 10 | E7870 | Disorder of bile acid and cholesterol metabolism, unspecified |
| 10 | E7871 | Barth syndrome |
| 10 | E7872 | Smith-Lemli-Opitz syndrome |
| 10 | E7879 | Other disorders of bile acid and cholesterol metabolism |
| 10 | E788 | Other disorders of lipoprotein metabolism |
| 10 | E7881 | Lipoid dermatoarthritis |
| 10 | E7889 | Other lipoprotein metabolism disorders |
| 10 | E789 | Disorder of lipoprotein metabolism, unspecified |
| 9 | 2720 | Pure hypercholesterolemia |
| 9 | 2721 | Pure hyperglyceridemia |
| 9 | 2722 | Mixed hyperlipidemia |
| 9 | 2723 | Hyperchylomicronemia |
| … | … | (+6 more) |

</details>

### Etiology prevalence by 2×2 cell (primary b)

| cell | n | alcohol % | viral hep % | other etiology % | cirrhosis % |
| --- | --: | --: | --: | --: | --: |
| code+/note+ | 5,027 | 12.6 | 3.3 | 1.8 | 26.0 |
| code-/note+ | 22,799 | 18.1 | 8.2 | 3.0 | 12.8 |
| code+/note- | 713 | 9.7 | 4.5 | 2.5 | 12.2 |
| code-/note- | 345,453 | 7.0 | 4.4 | 1.1 | 3.3 |

## Step 2 — Cardiometabolic criterion (code OR lab OR vital; missingness-tolerant)

Note: 'glucose ≥100' uses any glucose (fasting status unknown); antidiabetic medication NOT incorporated (prescriptions not processed) — a stated limitation.

| criterion | positive % | UNASCERTAINABLE % |
| --- | --: | --: |
| Overweight/obesity | 55.0 | 21.9 |
| Dysglycemia | 60.9 | 14.8 |
| Hypertension | 64.5 | 13.4 |
| Dyslipidemia | 37.1 | 60.5 |

- Meet ≥1 criterion: **334,611 (89.5%)**
- Meet none (ascertainable, no criterion): 29,061 (7.8%)
- Unascertainable for ALL four: 10,320 (2.8%)

### Cardiometabolic ascertainment: meets≥1 / none / unascertainable-all, by cell

| cell | n | meets≥1 % | none % | unasc-all % |
| --- | --: | --: | --: | --: |
| code-/note- | 345,453 | 89.0 | 8.1 | 2.9 |
| code-/note+ | 22,799 | 94.8 | 4.4 | 0.8 |
| code+/note+ | 5,027 | 98.1 | 1.8 | 0.1 |
| code+/note- | 713 | 97.3 | 2.4 | 0.3 |

### Cardiometabolic ascertainment: meets≥1 / none / unascertainable-all, by race

| race | n | meets≥1 % | none % | unasc-all % |
| --- | --: | --: | --: | --: |
| WHITE | 240,958 | 89.2 | 8.0 | 2.8 |
| BLACK/AFRICAN AMERICAN | 49,641 | 92.2 | 5.4 | 2.5 |
| OTHER | 12,528 | 86.7 | 9.8 | 3.5 |
| UNKNOWN | 9,726 | 90.5 | 7.5 | 2.0 |
| WHITE - OTHER EUROPEAN | 7,126 | 92.3 | 7.2 | 0.5 |
| HISPANIC/LATINO - PUERTO RICAN | 6,820 | 91.4 | 5.8 | 2.7 |
| HISPANIC OR LATINO | 6,169 | 84.5 | 8.6 | 6.8 |
| ASIAN - CHINESE | 4,693 | 85.9 | 12.0 | 2.0 |
| WHITE - RUSSIAN | 4,660 | 96.3 | 3.0 | 0.7 |
| ASIAN | 4,650 | 78.1 | 16.1 | 5.8 |
| BLACK/CAPE VERDEAN | 3,987 | 91.0 | 8.2 | 0.8 |
| HISPANIC/LATINO - DOMINICAN | 3,610 | 92.6 | 5.5 | 1.9 |
| BLACK/CARIBBEAN ISLAND | 2,402 | 94.4 | 4.1 | 1.5 |
| BLACK/AFRICAN | 2,015 | 87.4 | 9.1 | 3.4 |
| PATIENT DECLINED TO ANSWER | 1,523 | 87.5 | 9.4 | 3.2 |
| UNABLE TO OBTAIN | 1,392 | 86.1 | 8.4 | 5.5 |
| PORTUGUESE | 1,383 | 93.3 | 5.4 | 1.4 |
| ASIAN - SOUTH EAST ASIAN | 1,262 | 86.9 | 10.8 | 2.3 |
| HISPANIC/LATINO - GUATEMALAN | 1,179 | 88.9 | 6.1 | 5.0 |
| WHITE - EASTERN EUROPEAN | 1,045 | 89.0 | 9.2 | 1.8 |
| ASIAN - ASIAN INDIAN | 977 | 85.2 | 11.5 | 3.4 |
| WHITE - BRAZILIAN | 950 | 79.2 | 17.3 | 3.6 |
| AMERICAN INDIAN/ALASKA NATIVE | 764 | 89.4 | 7.9 | 2.7 |
| HISPANIC/LATINO - SALVADORAN | 729 | 87.0 | 9.1 | 4.0 |
| HISPANIC/LATINO - MEXICAN | 511 | 79.1 | 13.3 | 7.6 |
| HISPANIC/LATINO - COLUMBIAN | 506 | 87.2 | 10.1 | 2.8 |
| SOUTH AMERICAN | 443 | 92.3 | 4.7 | 2.9 |
| HISPANIC/LATINO - CUBAN | 428 | 91.8 | 6.1 | 2.1 |
| HISPANIC/LATINO - HONDURAN | 425 | 93.4 | 3.5 | 3.1 |
| MULTIPLE RACE/ETHNICITY | 418 | 80.1 | 9.6 | 10.3 |
| HISPANIC/LATINO - CENTRAL AMERICAN | 382 | 92.7 | 3.7 | 3.7 |
| ASIAN - KOREAN | 373 | 74.5 | 20.9 | 4.6 |
| NATIVE HAWAIIAN OR OTHER PACIFIC ISL | 317 | 83.0 | 12.0 | 5.0 |

### Cardiometabolic ascertainment: meets≥1 / none / unascertainable-all, by insurance

| insurance | n | meets≥1 % | none % | unasc-all % |
| --- | --: | --: | --: | --: |
| Medicare | 180,507 | 95.4 | 3.8 | 0.8 |
| Private | 115,222 | 84.3 | 11.5 | 4.2 |
| Medicaid | 63,027 | 85.1 | 11.0 | 3.9 |
| Other | 9,970 | 82.7 | 11.5 | 5.8 |

### Within note-positive (primary b): metabolic-risk / alcohol cross-tab

Among 27,826 note-positive admissions: metabolic-only 22,238 (79.9%); alcohol-only 441 (1.6%); both 4,317 (15.5%); neither 830 (3.0%).

### Recovery-zone (code−/note+) count under three definitions (sensitivity — do not pick)

- Steatosis alone: **22,799**
- Excluding alcohol codes (ALD/AUD): 18,673 (−4,126)
- Excluding ALL competing etiologies: 15,646 (−7,153)


## Step 3 — Imaging denominator (liver-inclusive studies)

Classification by structured `exam_name` (radiology_detail): liver-inclusive = cross-sectional/US modality AND abdominal/liver region; plain abdominal films and non-liver organ studies excluded.

<details><summary>Exam names flagged liver-inclusive (top 25, verification)</summary>

| exam_name | n |
| --- | --: |
| CT ABD & PELVIS WITH CONTRAST | 73,838 |
| LIVER OR GALLBLADDER US (SINGLE ORGAN) | 40,207 |
| CT ABDOMEN W/CONTRAST | 24,756 |
| CT ABD & PELVIS W/O CONTRAST | 19,735 |
| ABDOMEN US (COMPLETE STUDY) | 10,895 |
| CTA ABD & PELVIS | 9,612 |
| ABDOMEN U.S. (COMPLETE STUDY) | 9,509 |
| CT ABD W&W/O C | 8,981 |
| CT ABDOMEN W/O CONTRAST | 8,813 |
| MRCP (MR ABD W&W/OC) | 8,223 |
| CT ABD & PELVIS W & W/O CONTRAST, ADDL SECTIONS | 8,120 |
| MRI ABDOMEN W/O & W/CONTRAST | 7,942 |
| US ABD LIMIT, SINGLE ORGAN | 6,166 |
| CTA ABD W&W/O C & RECONS | 5,014 |
| LIVER OR GALLBLADDER US (SINGLE ORGAN) PORT | 4,246 |
| MRI LIVER W&W/O CONTRAST | 3,566 |
| GUIDANCE FOR THORA/ABD/PARA CENTESIS US | 2,307 |
| MRI ABDOMEN W/O CONTRAST | 2,011 |
| MRI (ABDOMEN & PELVIS) W&W/O CONTRAST | 760 |
| CT ABDOMEN W/CONTRAST W/ONC TABLE | 689 |
| CT RFA LIVER 1 OR MORE | 658 |
| CT ABD BX, LYMPHNODE BX | 503 |
| MR UROGRAM(MR ABD&PEL W&W/OC) | 392 |
| SKULL AP&LAT/C-SP/CXR/ABD SLG VIEWS MR SCREENING | 363 |
| ABDOMEN US (COMPLETE STUDY) PORT | 327 |

</details>

- Admissions with ≥1 liver-inclusive study (inpatient): **83,534 (22.3%)**
- + within 365/30 outpatient window: **138,603 (37.1%)** (imaging-observed population)

**Is being imaged differential?** liver-inclusive imaging: code+ 71.0% vs code− 36.5%, SMD=+0.736. By race/insurance (imaging %):

- **race** range 30.1%–50.6% (max PORTUGUESE 50.6%, min UNABLE TO OBTAIN 30.1%)
- **insurance** range 35.7%–39.4% (max Medicaid 39.4%, min Medicare 35.7%)

### 2×2 restricted to imaging-observed population (primary b), n (% of imaged)

| cell | n | % of imaged |
| --- | --: | --: |
| code+/note+ | 3,739 | 2.70% |
| code−/note+ | 19,248 | 13.89% |
| code+/note− | 335 | 0.24% |
| code−/note− | 115,281 | 83.17% |

Imaging-observed population N = 138,603 of 373,992 admissions (37.1%). This is a pre-specified SECONDARY analysis population (note-negative outside it may mean non-observation, not absence).


## Step 4 — Note & trigger descriptives

### Notes per admission by type (linked notes)

| type | % admissions with ≥1 | median | p95 |
| --- | --: | --: | --: |
| DS | 88.7% | 1 | 1 |
| RR | 82.7% | 2 | 10 |
| AR | 2.3% | 0 | 0 |

### Section of triggering hit (discharge, among note-positive) — top 12

| section | hits |
| --- | --: |
| PAST MEDICAL HISTORY | 4,998 (18.2%) |
| IMPRESSION | 3,900 (14.2%) |
| BRIEF HOSPITAL COURSE | 3,846 (14.0%) |
| HISTORY OF PRESENT ILLNESS | 2,590 (9.4%) |
| PERTINENT RESULTS | 1,634 (6.0%) |
| IMAGING | 1,033 (3.8%) |
| DISCHARGE DIAGNOSIS | 627 (2.3%) |
| PMH | 362 (1.3%) |
| TRANSITIONAL ISSUES | 344 (1.3%) |
| ACUTE ISSUES | 326 (1.2%) |
| DISCHARGE LABS | 306 (1.1%) |
| ACTIVE ISSUES | 267 (1.0%) |

### Tier A triggers per note-positive admission

- 1 trigger: 12,717 (45.7%); 2: 3,943; 3+: 1,757.

### Top Tier A trigger co-occurrences (admissions with both)

| trigger A | trigger B | n |
| --- | --- | --: |
| steatohepatitis | steatosis | 1,859 |
| hepatic steatosis | steatosis | 1,566 |
| fatty liver | steatosis | 774 |
| hepatic steatosis | steatohepatitis | 653 |
| fatty liver | hepatic steatosis | 650 |
| fatty infiltration | fatty liver | 644 |
| fatty liver | steatohepatitis | 533 |
| fatty liver | nonalcoholic fatty liver | 377 |
| nonalcoholic fatty liver | steatosis | 327 |
| NASH | nonalcoholic steatohepatitis | 293 |
| NASH | fatty liver | 266 |
| nonalcoholic fatty liver | steatohepatitis | 265 |

### Which triggers drive the recovery zone (code−/note+) vs code+/note+

Recovery-zone n=22,799, code+/note+ n=5,027. Trigger presence %:

| trigger | recovery-zone % | code+/note+ % |
| --- | --: | --: |
| steatosis | 17.3% | 17.5% |
| hepatic steatosis | 17.1% | 19.6% |
| fatty liver | 16.5% | 38.8% |
| fatty infiltration | 10.1% | 5.9% |
| steatohepatitis | 7.5% | 11.8% |
| NASH | 6.5% | 32.5% |
| fatty deposition | 1.9% | 1.4% |
| fatty sparing | 1.8% | 1.9% |
| NAFLD | 1.4% | 5.8% |
| nonalcoholic fatty liver | 1.3% | 6.1% |
| fatty change | 0.9% | 0.5% |
| nonalcoholic steatohepatitis | 0.7% | 6.1% |
| steatotic | 0.5% | 0.5% |
| fatty infiltrate | 0.4% | 0.3% |

**Fragility check:** 41.9% of recovery-zone admissions rest on a SINGLE trigger; the most common single drivers: fatty liver (2,371), hepatic steatosis (2,198), steatosis (1,460), fatty infiltration (1,403), NASH (1,091).

### Tier C (hedged) distribution across 2×2 cells

| cell | n | with Tier C hit | % |
| --- | --: | --: | --: |
| code+/note+ | 5,027 | 173 | 3.44% |
| code-/note+ | 22,799 | 511 | 2.24% |
| code+/note- | 713 | 18 | 2.52% |
| code-/note- | 345,453 | 328 | 0.09% |


## Step 5 — Clustering & comorbidity burden

### Subjects by number of admissions contributed

| admissions | subjects | % |
| --- | --: | --: |
| 1 | 93,852 | 58.3% |
| 2 | 29,525 | 18.3% |
| 3-5 | 25,485 | 15.8% |
| 6+ | 12,257 | 7.6% |

### Coding inconsistency among code−/note+ subjects

- code−/note+ admissions: 22,799 across **13,199 subjects**.
- Subjects with ≥1 OTHER admission in a different cell: **8,295 (62.8%)**.
- Subjects whose **coding status changes** across stays (code+ on some admission, code− on another): **1,490 (11.3%)** — directly informative about coding inconsistency.

### Charlson Comorbidity Index by 2×2 cell (Quan 2005 crosswalk, Charlson weights)

| cell | n | mean | median [IQR] | SMD vs code+/note+ |
| --- | --: | --: | --- | --: |
| code+/note+ | 5,027 | 3.29 | 3 [1, 5] |  |
| code-/note+ | 22,799 | 2.45 | 2 [1, 4] | -0.356 |
| code+/note- | 713 | 3.19 | 3 [1, 4] | -0.043 |
| code-/note- | 345,453 | 2.08 | 1 [0, 3] | -0.526 |


## Step 6 — Sample representativeness (draw vs full cell; seed 20260818)

SMD of each covariate, sampled charts vs the full cell they were drawn from. **|SMD|>0.1 flagged** (would bias reweighting). Categoricals (race/insurance/admission_type) = max per-level |SMD| over levels with ≥5% cell share (multinomial SMD is unstable at n≈80 over sparse categories).

| cell | n_sample | age | sex(M) | race | insurance | admission_type | LOS | max\|SMD\| |
| --- | --: | --: | --: | --: | --: | --: | --: | --: |
| code+/note+ | 80 | -0.050 | -0.108 | 0.068 | 0.103 | 0.122 | +0.068 | 0.122 |
| code-/note+ | 150 | -0.102 | -0.033 | 0.047 | 0.107 | 0.219 | +0.000 | 0.219 |
| code+/note- | 70 | -0.057 | +0.164 | 0.026 | 0.178 | 0.200 | -0.107 | 0.200 |
| code-/note- | 100 | -0.030 | -0.112 | 0.091 | 0.052 | 0.240 | -0.007 | 0.240 |

**FLAG (|SMD|>0.1):** code+/note+ (max|SMD|=0.122); code-/note+ (max|SMD|=0.219); code+/note- (max|SMD|=0.200); code-/note- (max|SMD|=0.240). These are max per-level differences at n=70–150 (chiefly admission_type). Because sampling is a simple random draw WITHIN each cell, the population-weighted 1a estimate (cell weight = N_pop/n_sample) remains unbiased in expectation; the flags indicate covariate imbalance in this particular draw, relevant only if within-cell covariate-adjusted analyses are planned. Researcher to decide on re-draw vs adjustment.


---

## Step 7 — Decisions required before adjudication (options + stakes; no recommendation)

**1. Competing-etiology exclusions defining the PRIMARY phenotype.**
The recovery-zone (code−/note+) count swings with the definition: steatosis alone
**22,799** → excluding alcohol codes (ALD/AUD) **18,673** → excluding ALL competing
etiologies (alcohol, viral, autoimmune/metabolic, cirrhosis, HCC) **15,646** (−31%).
*Options:* (a) steatosis alone — captures MASLD + MetALD + ALD + viral, not
MASLD-specific; (b) exclude alcohol codes — MASLD-leaning but ICD alcohol codes
undercount true intake (social-history alcohol is often uncoded), so residual ALD
remains; (c) exclude all competing etiologies — strictest, but drops true MASLD
that carries an incidental viral/cirrhosis code. *Stakes:* directly sets what the
recovery zone means and its magnitude; the alcohol axis is the largest single
contaminant (18.1% of the recovery zone carries an alcohol code).

**2. Cardiometabolic criterion operationalization and the unascertainable.**
As operationalized (code OR lab OR vital, ≥1 of four), **89.5% meet ≥1**, 7.8% meet
none, **2.8% are unascertainable for all four** — but unascertainability is
differential by race (0.5%–6.8%; highest in HISPANIC OR LATINO). *Options:* (a)
keep the missingness-tolerant ≥1 rule; (b) treat unascertainable admissions as
not-MASLD (conservative) vs (c) exclude them vs (d) impute; (e) whether to
incorporate antidiabetic medications (prescriptions not yet processed). *Stakes:*
differential ascertainability means the metabolic criterion is not equally
applicable across groups — a direct constraint on Aim 1c; and the unascertainable
cannot be MASLD-classified either way.

**3. Imaging-restricted population: primary or secondary.**
Liver-inclusive imaging is present for 37.1% of admissions and is **highly
differential by coding status (code+ 71.0% vs code− 36.5%, SMD +0.736)**. Outside
the imaged population, note-negative plausibly means non-observation, not absence.
*Options:* (a) primary analysis on the full population (note-negative conflates
absence and non-observation); (b) primary analysis restricted to the imaging-observed
population (138,603) with the full population as sensitivity — removes
non-observation bias but selects a sicker, more-imaged subset and shrinks the
denominator. *Stakes:* changes the recovery-zone denominator and how much of the
"codes miss" signal is real vs an imaging artifact.

**4. MetALD-consistent admissions reported separately.**
Among note-positive admissions, **15.5% have both metabolic risk and an alcohol
code** (MetALD-consistent), 1.6% alcohol-only, 79.9% metabolic-only. MetALD has no
ICD code, so it exists entirely in the note/steatosis space. *Options:* (a) report
MetALD-consistent admissions as their own category throughout; (b) fold them into
MASLD or into ALD. *Stakes:* under current nomenclature these are a distinct entity;
folding them either way biases the MASLD recovery estimate and misaligns with the
MASLD/MetALD/ALD framework the study invokes.
