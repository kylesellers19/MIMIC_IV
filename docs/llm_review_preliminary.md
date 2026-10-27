# Local-LLM review of liver sentences: preliminary results

> **PRELIMINARY and exploratory (analysis-plan amendment h).** Nothing here is validated against human review. Every number is written by `scripts/llm_review_results.py` into `docs/run_2026-10-27/results/llm_review_preliminary.json`. Counts from 1 to 10 appear as <11.

Scope: the dev/test notes subsample, 29,980 admissions of 13,000 subjects (a simple random sample of dev/test subjects). Scaled figures multiply by 12.36, the ratio of all dev/test subjects to sampled subjects, and are rounded to the nearest 100. Method: `docs/llm_review_protocol.md`.

## Documented in notes, never coded

| Note phenotype | Admissions (sample) | Subjects (sample) | Subjects, scaled | Share of note-positive subjects uncoded |
| --- | --: | --: | --: | --: |
| Rule and LLM agree | 1,376 | 737 | ~9,100 | 73.6% |
| Frozen keyword rule | 1,676 | 912 | ~11,300 | 77.2% |
| Local LLM (v4) | 1,827 | 943 | ~11,700 | 77.7% |
| Either | 2,127 | 1,112 | ~13,700 | 80.2% |

For comparison, subjects with a MASLD code, scaled: ~3,700.

## The LLM against the frozen rule, uncoded admissions

Restricted to admissions without a MASLD code, where recovery happens; the coded group is reported only as totals, because its rule-by-LLM cells include counts below 11.

| | Rule positive | Rule negative |
| --- | --: | --: |
| **LLM positive** | 1,376 | 451 |
| **LLM negative** | 300 | 27,383 |

The LLM confirms 82.1% of the rule's uncoded positives and finds steatosis in 1.6% of the admissions the rule calls negative. Coded admissions: 470, of which the LLM calls 425 positive and the rule 426.


Why the LLM alone calls an uncoded admission positive:

- fat or imaging wording outside the rule's term list: 187
- rule term present, rejected by the rule: 151
- no fat-related word (unexplained): 62
- imaging sign only (outside the rule's primary definition): 51

Why the rule alone calls an uncoded admission positive:

- model answered NO: 183
- model answered UNCLEAR: 106
- no rule term in any kept sentence: 11

## Where uncoded cases are documented

| LLM-positive admissions | n | Discharge summary | Inpatient radiology only | Outpatient radiology only | Past mentions only |
| --- | --: | --: | --: | --: | --: |
| uncoded | 1,827 | 43.3% | 17.8% | 38.9% | 11.0% |
| coded | 425 | 92.2% | 2.6% | 5.2% | 23.1% |

## Method checks

- Sentence selection: admissions whose steatosis statement never reached the model fell from 367 (anatomy-only) to 0; rule-positive admissions with no steatosis or echogenicity word in any kept sentence fell from 145 to 22.
- Dev pilot of 500 sentences: identical answers on rerun 499/500; Cohen's kappa against v3 for the paraphrases 0.808 and 0.811, few-shot 0.819, neighbouring-sentence context 0.895.
- Full run (v3): 89,928 distinct units, 0 errors, 71 unparsed, 22.0 model-hours; v4 re-ask of YES/UNCLEAR units: 5,785 units, 0 errors.
- YES rate by selection reason (sentence rows, %): anatomy 3.6, liver disease term 93.2, liver heading 0.4, steatosis term, no other organ 32.9.

## Caveats

- The prompt was revised twice on information that included TEST (amendment h); TEST is not independent of prompt development.
- Both phenotypes are automated readings of the same notes; neither is the reference standard. The 400-chart review decides.
- Scaled figures assume the subsample's subjects represent all dev/test subjects (simple random sampling makes this reasonable; GOLD_HOLDOUT subjects are excluded).
