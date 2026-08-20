# Reference Standard §2 — Chart-Review Adjudication Criteria

**DRAFT 1 — requires clinician review and sign-off before use.**

> Status: this is the gate identified in [reference_standard.md](reference_standard.md)
> §2. The criteria are **not frozen**. Per §9, the only permitted revision point is
> after the 20-chart training set; once formal review of the 400-chart sample begins
> they are frozen. No chart from the 400-chart sample may be adjudicated until this
> document is signed off. `[CLINICIAN]` markers below are open decisions for the
> reviewing clinician — they are **not** resolved here.

## 1. What the reviewer sees

A **code-stripped** chart packet per admission:
- discharge summary, full text
- all linked radiology reports (inpatient, and outpatient within 365 days prior /
  30 days after)
- laboratory values (LFTs, lipids, HbA1c, glucose, platelets)
- vitals and anthropometrics
- medication orders
- demographics (age, sex) only

**Excluded from the packet:**
- all ICD codes, coded problem lists, billing data
- the note-phenotype rule's output or any highlighting of trigger terms
- race, insurance, language (not needed for adjudication; their absence protects the
  equity analysis from reviewer bias)
- blinded review ID only; no cell membership, no ordering by cell

## 2. Primary question

*"Is there evidence of hepatic steatosis during or before this admission?"*
Response: **Definite / Probable / Possible / Absent / Insufficient information**.

`[CLINICIAN]` Confirm the scale and which levels collapse to "positive" for the
primary analysis. Draft assumption: **Definite + Probable = positive**.

## 3. Evidence hierarchy

| # | Evidence | Level |
|---|---|---|
| a | Liver biopsy reporting steatosis | Definite |
| b | CT/MRI reporting hepatic steatosis, fatty liver, fatty infiltration, or decreased hepatic attenuation | Definite |
| c | Ultrasound reporting increased hepatic echogenicity consistent with steatosis | Probable |
| d | Clinician note statement ("fatty liver", "known NAFLD") without supporting imaging in the packet | Probable |
| e | Hedged radiology ("cannot exclude steatosis", "may represent hepatic steatosis") | Possible |
| f | Elevated transaminases or metabolic risk alone, no steatosis statement | Absent (for this question) |

`[CLINICIAN]` (3c) US is operator-dependent and echogenicity nonspecific — is
Probable right, or does an explicit radiologist statement of steatosis raise it to
Definite? (3e) Radiologists hedge routinely — should hedged imaging count as Probable?

## 4. Temporality

Record separately: steatosis documented **during** this admission / **before** this
admission (history, prior imaging in the packet) / **both**.

`[CLINICIAN]` Both count as positive in the draft (the question is whether the
information was available to be coded). Confirm.

## 5. Negation

An explicit statement of absence ("no evidence of hepatic steatosis", "normal
hepatic echotexture") on the **most recent liver-inclusive imaging** overrides an
older positive finding **only if** the reviewer judges the newer study more reliable.
Record the reasoning in a free-text field.

`[CLINICIAN]` Steatosis is reversible with weight loss — is override appropriate, or
should any prior positive stand?

## 6. Secondary questions (asked only if steatosis is Definite/Probable)

- **6a. Cardiometabolic risk:** ≥1 of BMI ≥25; T2D or prediabetes; BP ≥130/85 or
  antihypertensive treatment; triglycerides ≥150; HDL ≤40 (M) / ≤50 (F); or
  lipid-lowering therapy? **Yes / No / Insufficient.**
- **6b. Alcohol:** from documented history, does intake appear (i) below the MetALD
  threshold, (ii) within the MetALD band (140–350 g/wk F, 210–420 g/wk M),
  (iii) above it, or (iv) not documented / insufficient?
  `[CLINICIAN]` Charts rarely quantify intake — expect (iv) to dominate. Is a
  qualitative scale (none / social / heavy / not documented) more usable?
- **6c. Other identifiable cause** of steatosis (amiodarone, methotrexate, tamoxifen,
  valproate, HIV therapy, TPN, rapid weight loss, Wilson disease, lipodystrophy)?
  **Yes (specify) / No / Unclear.**

## 7. Reviewer output

Per chart: blinded ID, primary response, temporality, secondary responses, free-text
rationale (required for Possible and for any negation override), time spent.

`[CLINICIAN]` Estimate time per chart so the 400-chart burden can be scoped honestly.
(An analyst estimate is offered in the review section below, to be validated by §9.)

## 8. Double review and disagreement

100 charts (25%) reviewed independently by both reviewers, drawn across all four
cells, not identifiable as the overlap subset. **Cohen's kappa** on the collapsed
binary outcome; **weighted kappa** on the four-level scale. Disagreements resolved by
`[CLINICIAN — third adjudicator, or consensus discussion?]`. If consensus discussion,
pre-consensus responses are retained and kappa is computed on those.

## 9. Training set

Before formal review, both reviewers independently adjudicate the same **20 charts NOT
drawn from the 400-chart sample**. Discrepancies are discussed and the criteria
revised. **This is the only point at which the criteria may change**; after formal
review begins they are frozen.

## 10. What reviewers are not asked

Reviewers do not judge whether a code should have been assigned, do not see coding
data, and are told only "we are validating a computable phenotype for hepatic
steatosis" — nothing more of the study hypothesis.

---

## Open decisions for clinician sign-off (collated)

| # | Section | Decision |
|---|---|---|
| D1 | §2 | Confirm the response scale (4 ordinal levels + Insufficient?) and the positive collapse (draft: Definite+Probable). |
| D2 | §3c | Ultrasound echogenicity: keep Probable, or raise an explicit radiologist steatosis statement to Definite? |
| D3 | §3e | Hedged imaging: Possible (draft) or Probable? |
| D4 | §4 | Confirm during-AND-before both count as positive. |
| D5 | §5 | Negation override by newer imaging, or does any prior positive stand (reversibility)? |
| D6 | §6b | Alcohol: g/wk bands or a qualitative none/social/heavy/not-documented scale? |
| D7 | §7 | Per-chart time (validated by the §9 training set). |
| D8 | §8 | Disagreement resolution: third adjudicator vs consensus discussion. |

---

## Analyst cross-consistency check & flags (NOT clinical decisions)

Provided by the analytic pipeline to surface alignment and inconsistencies for the
clinician's review. No clinical judgement is made here.

**Consistent with the built infrastructure ✔**
- **Outpatient imaging window (365 prior / 30 after)** in the packet matches the frozen
  note-phenotype's primary window and the built 2×2, so a reviewer sees the same
  imaging evidence the rule could act on.
- **Blinding**: no codes, no rule output, no highlighting → protects Aim 1a from
  circularity (the reference standard is independent of both compared phenotypes).
  Race/insurance/language withheld from the packet while retained at the analysis
  level → protects the Aim 1c equity analysis from reviewer bias, as intended.
- **Double review** (100 charts / 25%, `double_review` marked in the master key only,
  `review_id` does not encode cell) matches the drawn 400-chart sample
  (`data/processed/aim1a_sample.parquet`, seed 20260818).
- **6a CMRF thresholds** match the computable operationalization used in
  `docs/sld_subclassification.md` (BMI≥25; T2D/prediabetes; BP≥130/85 or
  antihypertensive; TG≥150; HDL≤40/≤50; lipid-lowering), enabling a later
  adjudicated-vs-computed CMRF comparison.
- **6b alcohol** aligns with the documented limitation that MIMIC lacks quantified
  intake; the analyst pipeline likewise proxies alcohol by ICD code only.

**Inconsistencies / gaps to resolve (flagged, not fixed)**
1. **4- vs 5-level scale.** §2 lists five responses but §8 computes weighted kappa on
   "the four-level scale." *Insufficient* is a non-response, not an ordinal level.
   Clarify (D1): weighted kappa over the 4 ordinal levels (Definite→Absent) with
   *Insufficient* handled separately (excluded or treated as missing).
2. **Double-review allocation.** §8 says "drawn across all four cells." The built
   overlap subset was a simple random draw of 100 from the 400, i.e. **proportional**
   to the cell allocation (~37 code−/note+, ~20 code+/note+, ~17 code+/note−,
   ~25 code−/note−), not 25 per cell. If per-cell kappa is wanted, a stratified
   (equal-per-cell) overlap would be needed instead — decide before finalizing.
3. **6c has no computable analog.** "Other identifiable cause" (drug-induced steatosis,
   Wilson, lipodystrophy…) corresponds to Rinella's *specific-aetiology SLD*, which
   the computable phenotype does not model. 6c results are adjudication-only and cannot
   be validated against a computed measure (unlike 6a and 6b).
4. **Negation divergence is expected.** §5's "newer normal study overrides older
   positive" is a chart-level reliability judgement; the frozen rule negates at the
   sentence level (ConText). The reference standard takes precedence, so legitimate
   reviewer-vs-rule disagreements here are part of what Aim 1a measures, not error.

**Data-informed time estimate (analyst input for D7; to be validated by §9)**
Chart size in this corpus: discharge summaries median **~9,847 chars** (~1,600 words;
p95 ~18,619, max ~60,381), radiology reports median ~781 chars (often several per
admission). A steatosis-focused packet read — discharge summary + scan of linked
radiology + labs/meds/vitals for 6a and alcohol history for 6b — plausibly runs
**~10–18 minutes per chart** with a long right tail on the largest discharge
summaries. Across 400 primary + 100 duplicated double-review = 500 adjudications, that
is roughly **85–150 reviewer-hours total**. This is an estimate only; the 20-chart
training set (§9) should produce the empirical per-chart time before anyone commits.
