# Reviewer packet — specification and feasibility (400-chart sample)

Produced by `scripts/run0919_phase6_docs.py` from `docs/run_2026-09-19/results/packet_feasibility.json` (`scripts/run0919_packet_feasibility.py`) and `docs/run_2026-09-19/results/packet_dryrun.json` (`scripts/make_reviewer_packets.py --dryrun`). Generator: `scripts/make_reviewer_packets.py`. Criteria §1 (docs/adjudication_criteria.md) defines what the packet may contain; this document confirms each element against the data.

## 1. What each packet contains

One plain-text file per chart, named by the blinded ID (`R0001.txt` … `R0400.txt`; `T001.txt` … `T020.txt` for the training round). Sections, in order:

| # | element | source | rule |
| --- | --- | --- | --- |
| header | age at admission (capped at '89 or older'), sex, length of stay | patients / admissions via the locked population | no dates; no race, insurance, language, marital status |
| 1 | discharge summary, full text, verbatim | MIMIC-IV-Note `discharge` | all documents linked to the admission (note_seq order); charttime as a day offset |
| 2 | radiology reports, full text, verbatim, with exam name | MIMIC-IV-Note `radiology` + `radiology_detail` (exam_name) | linked to the admission, plus outpatient reports (no hadm_id) for the same patient within −365/+30 days of admission; day offsets |
| 3 | laboratory values, ten analytes | `labevents` itemids ALT 50861, AST 50878, Platelets 51265, Triglycerides 51000, HDL 50904, HbA1c 50852, Glucose 50931, Albumin 50862, Bilirubin_total 50885, Alkaline_phosphatase 50863 | labevents row with hadm_id = the admission, OR hadm_id NULL for the same subject with charttime in [admittime, dischtime]; value, unit, flag, reference range, day offset |
| 4 | vitals and anthropometrics | `omr` (BMI, blood pressure incl. positional variants, weight, height) | within −365/+30 days of admission; day offsets |
| 5 | medication orders | `prescriptions` | linked to the admission: drug, route, dose, start/stop day offsets |

Stripped by construction: note_id, subject_id, hadm_id, calendar dates, ICD codes and coded problem lists, race, insurance, language, marital status, cell membership, the note rule's output and any highlighting. Clinician-written narrative is never edited, including a narrative 'Discharge Diagnosis:' section. All times are day offsets from admission (day +0.0); the sections are delimited so that automated checks can tell narrative from structured text.

## 2. Availability of each element (400 sampled admissions)

| element | overall | A (n=80) | B (n=150) | C (n=70) | D (n=100) |
| --- | --: | --: | --: | --: | --: |
| discharge summary present | 89.2% | 98.8% | 89.3% | 84.3% | 85.0% |
| ≥1 inpatient radiology report | 85.8% | 81.2% | 90.7% | 77.1% | 88.0% |
| ≥1 outpatient radiology report in window | 72.2% | 77.5% | 74.7% | 77.1% | 61.0% |
| ≥1 radiology report of either kind | 95.8% | 97.5% | 100.0% | 90.0% | 92.0% |
| ≥1 liver-inclusive imaging report (exam-name rule) | 60.5% | 72.5% | 83.3% | 45.7% | 27.0% |
| ≥1 of the ten labs in admission | 86.2% | 86.2% | 89.3% | 88.6% | 80.0% |
| BMI in omr window | 71.5% | 85.0% | 70.0% | 78.6% | 58.0% |
| blood pressure in omr window | 66.8% | 77.5% | 66.0% | 71.4% | 56.0% |
| weight in omr window | 75.0% | 85.0% | 74.0% | 81.4% | 64.0% |
| height in omr window | 62.3% | 71.2% | 64.7% | 70.0% | 46.0% |
| ≥1 prescription | 92.5% | 98.8% | 91.3% | 90.0% | 91.0% |

Each of the ten labs present at least once (in-admission definition; the hadm_id-linked rate is in the JSON and differs by < 1 point):

| analyte | overall | A | B | C | D |
| --- | --: | --: | --: | --: | --: |
| ALT | 52.5% | 63.7% | 59.3% | 47.1% | 37.0% |
| AST | 52.8% | 63.7% | 60.0% | 47.1% | 37.0% |
| Platelets | 83.5% | 83.8% | 86.7% | 87.1% | 76.0% |
| Triglycerides | 11.8% | 18.8% | 12.0% | 7.1% | 9.0% |
| HDL | 6.8% | 7.5% | 5.3% | 7.1% | 8.0% |
| HbA1c | 6.0% | 6.2% | 6.0% | 5.7% | 6.0% |
| Glucose | 83.2% | 85.0% | 86.7% | 87.1% | 74.0% |
| Albumin | 43.2% | 47.5% | 50.7% | 38.6% | 32.0% |
| Bilirubin total | 51.7% | 63.7% | 58.7% | 47.1% | 35.0% |
| Alkaline phosphatase | 52.5% | 63.7% | 59.3% | 47.1% | 37.0% |

Cells are reported at the cell level (n = 80/150/70/100, all ≥ 11). Cell A = code+/note+, B = code−/note+, C = code+/note−, D = code−/note−.

## 3. What the criteria call for that MIMIC cannot supply

- quantified alcohol intake (g/week) — only narrative mentions in notes; no structured field
- liver biopsy / pathology reports as a structured source — MIMIC-IV-Note has discharge and radiology notes only; biopsy results appear only if narrated in the discharge summary
- waist circumference — not in omr (omr carries BMI, weight, height, blood pressure, eGFR)
- structured diabetes / hypertension / dyslipidaemia diagnoses — ICD codes are stripped by design; reviewers infer from HbA1c, glucose, lipids, BP, medication orders and narrative
- outpatient laboratory values in the -365/+30 window — labevents rows without hadm_id exist but are not part of the packet (criteria §1 lists in-admission labs); computable later if the criteria ask
- elastography / FIB-4 / imaging-derived fat fraction as structured values — only if narrated in a radiology report

The reviewer form therefore expects 'Not documented / insufficient' to dominate question 6b (alcohol), and 6a (cardiometabolic risk) to be answered from labs, BMI/BP, medication orders and narrative rather than from any coded diagnosis.

## 4. Reading burden (from the per-note index; no text read)

| cell | n | discharge chars median | p95 | radiology reports median | p95 | liver-inclusive reports median | narrative chars per packet median | p95 |
| --- | --: | --: | --: | --: | --: | --: | --: | --: |
| A code+/note+ | 80 | 10,701 | 22,428 | 5 | 18 | 1 | 16,924 | 39,191 |
| B code−/note+ | 150 | 10,414 | 20,887 | 6 | 20 | 1 | 18,568 | 53,501 |
| C code+/note− | 70 | 8,140 | 17,783 | 4 | 17 | 0 | 14,409 | 40,543 |
| D code−/note− | 100 | 8,674 | 18,704 | 4 | 14 | 0 | 13,602 | 32,762 |
| all | 400 | 9,515 | 19,627 | 5 | 18 | 1 | 16,228 | 42,208 |

Across the 400 packets: 4,003,760 discharge-summary characters and 3,633,569 radiology characters (2,646 reports, of which 508 are liver-inclusive by the exam-name rule); median 10 lab rows, 8 omr rows and 28 medication orders per chart. Longest packet: 93,672 narrative characters. Training round (20 charts): 363,641 narrative characters in total.

## 5. Dry run of the generator

`scripts/make_reviewer_packets.py --dryrun` generated all 420 packets (400 sample + 20 training) into `data/processed/_packet_dryrun/`, ran the leak checks below, and removed the directory (removed: True). Files generated: 420; exceptions by class: none; median file size 21,127 bytes (p95 60,464, max 114,390); load 81.2 s, generate 4.1 s. Discharge text verbatim check: 420 of 420 charts reproduce the character count of the per-note index exactly (375 charts have a discharge summary; for the rest both counts are zero — see availability above).

Rows pulled: 375 discharge documents, 2777 radiology reports (1370 inpatient, 1407 outpatient in window), 9303 lab rows, 8352 omr rows, 18920 medication orders.

| check | where | hits | files with ≥1 hit |
| --- | --- | --: | --: |
| (i) ICD-10-shaped token | structured | 20 | <11 |
| (i) ICD-10-shaped token | structured, value/dose columns removed | 20 | <11 |
| (i) ICD-9-shaped number ddd.dd | structured | 6725 | 329 |
| (i) ICD-9-shaped number ddd.dd | structured, value/dose columns removed | 5172 | 268 |
| (i) ICD-9-shaped number ddd.dd | structured, value/dose columns and signed day offsets removed | 0 | 0 |
| (ii) phenotype-code long title | structured | 0 | 0 |
| (ii) phenotype-code long title | narrative | <11 | <11 |
| (iii) demographic label | structured | 0 | 0 |
| (iv) 8-digit integer | structured | 0 | 0 |
| (iv) 8-digit integer | narrative | 0 | 0 |
| (v) cell label | structured | 0 | 0 |
| (v) cell label incl. the word 'recovery' | narrative | 65 | 53 |
| (v) of which the plain word 'recovery' | narrative | 65 | 53 |
| (vi) markup token | structured | 0 | 0 |
| (vi) markup token | narrative | 238 | 80 |
| (vii) chart's own hadm_id / subject_id / note_id | structured | 0 | 0 |
| (vii) chart's own hadm_id / subject_id / note_id | narrative | 0 | 0 |

Tokens matched by the ICD-shaped patterns in structured text with the value/dose columns and signed day offsets removed (frequency table; these are the only candidates for a real leak):

| token | hits |
| --- | --: |
| `icd10-shaped: B32 (section 5)` | 13 |
| `icd10-shaped: B22 (section 5)` | <11 |

Hit counts of 1–10 are written as <11 (the project's small-count rule). Section numbers in the token table refer to the packet sections in §1: section 5 is the medication table, section 3 the lab table, section 4 the vitals table; the tokens listed are what Kyle should grep for in the final packets before release.

Reading the checks. Structured text is everything outside the delimited note-text blocks (header, section titles, the lab / vitals / medication tables). ICD-shaped hits in structured text come from numeric lab values (ddd.dd), signed day offsets such as −123.4 in the outpatient window, and drug names such as 'Vitamin B12', which is why the counts with the value and dose columns and signed day offsets removed — and the token table — are the ones that matter; long-title, demographic-label, cell-label, markup and own-identifier hits in structured text are the true leak tests and must be zero. Narrative hits are inside clinician-written note text, which is kept verbatim by design: the word 'recovery' (recovery room, post-anaesthesia recovery) and any '**' or '[[' a clinician typed are documentation, not highlighting; an 8-digit number in narrative would be a number a clinician wrote in an already de-identified note, not a structured identifier. Check definitions are recorded in the results JSON (`check_definitions`).

## 6. Final generation (after the criteria are frozen)

```
scripts/run0919_env.sh scripts/make_reviewer_packets.py --out data/processed/adjudication/packets
```

The output directory is untracked (everything under `data/` is git-ignored). The same leak checks run and their counts are printed; the packets stay in place. Each reviewer receives only the packets for the IDs on their own form (`docs/adjudication/reviewer_assignment.md`), and only after their own PhysioNet credentialing and MIMIC-IV-Note DUA are in place.
