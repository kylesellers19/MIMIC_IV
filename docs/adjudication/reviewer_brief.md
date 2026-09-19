# Reviewer brief — hepatic steatosis chart adjudication

Numbers in this brief are read from `docs/run_2026-09-19/results/packet_feasibility.json`, `docs/run_2026-09-19/results/reviewer_assignment.json` and `docs/run_2026-09-19/results/reviewer_brief.json` by `scripts/run0919_phase6_docs.py`.

## What you are being asked to do

We are validating a computable phenotype for hepatic steatosis (fatty liver). For each chart packet you receive — a discharge summary, the linked radiology reports, in-admission laboratory values, outpatient BMI/blood pressure/weight/height, medication orders, and age and sex — answer one primary question:

> *Is there evidence of hepatic steatosis during or before this admission?*

on a five-option scale, then three short secondary questions when the answer is Definite or Probable. Full criteria: `docs/adjudication_criteria.md`; form fields: `docs/adjudication/data_dictionary.md`.

## The scale

| response | meaning (criteria §3) |
| --- | --- |
| Definite | liver biopsy reporting steatosis, or CT/MRI reporting hepatic steatosis, fatty liver, fatty infiltration or decreased hepatic attenuation |
| Probable | ultrasound reporting increased hepatic echogenicity consistent with steatosis, or a clinician's statement ('fatty liver', 'known NAFLD') without supporting imaging in the packet |
| Possible | hedged radiology only ('cannot exclude steatosis', 'may represent hepatic steatosis') — rationale required |
| Absent | no steatosis statement; elevated transaminases or metabolic risk alone do not count |
| Insufficient information | the packet does not allow a judgement either way (e.g. no discharge summary and no liver imaging) |

Record separately whether the evidence is from during this admission, before it, or both. An explicit newer negative study may override an older positive finding only if you judge it more reliable — say so in the rationale. You are not asked whether a code should have been assigned; you will not see any coding data.

## Secondary questions (Definite/Probable only)

- 6a Cardiometabolic risk: any of BMI ≥ 25; diabetes or prediabetes; BP ≥ 130/85 or antihypertensive treatment; triglycerides ≥ 150; HDL ≤ 40 (M) / ≤ 50 (F); lipid-lowering therapy.
- 6b Alcohol: from the documented history, below / within / above the MetALD band, or not documented. Charts rarely quantify intake; 'not documented' is expected to be common.
- 6c Another identifiable cause of steatosis (amiodarone, methotrexate, tamoxifen, valproate, HIV therapy, TPN, rapid weight loss, Wilson disease, lipodystrophy): Yes (specify) / No / Unclear.

## How much reading

Each reviewer has 250 charts in the formal round (shared with the other reviewer for a subset you will not be told about) plus the 20-chart calibration round. A typical packet carries about 9,515 characters of discharge summary (95th percentile 19,627) and 5 radiology reports (95th percentile 18), of which a median of 1 involve the liver or abdomen; labs, vitals and medication orders are short tables.

Rough hours, assuming 6 characters per word, a reading speed of 200–250 words per minute, and a fixed 5 minutes per chart for the tables and the form:

| reading strategy | minutes per chart | hours for your 250 charts | hours for the 20 training charts |
| --- | --: | --: | --: |
| full read: discharge summary + every radiology report | 18–21 | 74–87 | 6–7 |
| focused read: discharge summary + liver-inclusive radiology only | 14–16 | 58–67 | — |

These are rough figures: the long tail (largest packet 93,672 characters) and the time a chart with ambiguous imaging takes are not captured by an average. The calibration round exists partly to replace them with your measured time per chart (record `minutes_spent` on every row).

## The 20-chart calibration round

Before the formal review both reviewers independently adjudicate the same 20 charts (T001–T020), which are not part of the 400-chart sample. Disagreements are discussed and the criteria are revised once. After that the criteria are frozen for the formal review; nothing in the calibration round is used in any estimate.

## Access — please read

The packets are derived from MIMIC-IV and MIMIC-IV-Note (PhysioNet). **Each reviewer must hold their own PhysioNet credentialing and have signed the Data Use Agreement for MIMIC-IV-Note before seeing any packet.** The DUA does not allow access to be shared: no packet, screenshot, excerpt or note text may be sent to anyone who is not credentialed, and nothing from a packet may be pasted into the form, an e-mail, or any external tool. Keep the packets on the machine on which you received them and delete them when the review is complete.
