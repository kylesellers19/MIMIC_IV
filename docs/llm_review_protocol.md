# Local-LLM review of liver sentences: protocol

**Status: DRAFT. Sections marked DECISION need sign-off before the full run or before any gold-standard evaluation.** This document holds the design, the prompts and the reporting plan. Study numbers live in the scripts' outputs, not here.

## 1. Role in the study

- **What it does:** a locally run language model reads liver-related sentences from MIMIC-IV-Note and says whether each states hepatic steatosis.
- **Uses:**
  - ranking charts for reviewers
  - an admission-level note label to compare with the frozen rule-based phenotype
  - possibly silver labels for a model arm
- **What it never does:** assign reference-standard labels. The 400-chart clinician adjudication remains the reference standard (`docs/reference_standard.md`).

## 2. Sentences reviewed (`scripts/liver_sentences.py`)

- **Scope:** discharge summaries and inpatient radiology linked by admission, plus outpatient radiology from −365 to +30 days around admission. DEV and TEST partitions only; the review script refuses GOLD_HOLDOUT admissions unless explicitly allowed (§6).
- **Line rejoining:** hard-wrapped lines are joined back into sentences before splitting. A break is kept at blank lines, before headings and before list items. Positions in the source note are unchanged.
- **Selection:** a sentence is kept when any of these holds, and the reason is recorded per sentence:
  - it names the liver (a token containing "hepat" or starting with "liver");
  - its nearest heading names the liver;
  - it contains NAFLD, NAFL, NASH, MASLD, MASH, MAFLD or MetALD;
  - it contains steato- or "fatty infiltration/change" and names no competing organ.

  `--anatomy-only` reproduces the original selection, for sensitivity analyses. Counts: `diagnostics/llm_review_audit/filter_misses.py`.
- **Per-admission cap:** 160 sentences, impression first.
- **Context recorded per sentence:** note type, nearest heading, previous and next sentence (up to 300 characters each).

## 3. Model and inference (`scripts/llm_sentence_review.py`)

- **Model:** Gemma 4 26B (mixture-of-experts, Apache 2.0, pretraining cutoff January 2025 per the model card), Q4_K_M quantization. Served by Ollama on the study laptop.
- **Version pinning:** the model digest, model details (including the bundled draft model), Ollama version and hardware are written to each run's `manifest.json`. A run refuses to resume if any of them change.
- **Local only:** models served from Ollama's cloud (`:cloud`, `-cloud`, remote hosts) are refused. Follows PhysioNet's 24 Sep 2025 guidance, which strongly recommends locally deployed LLMs.
- **Decoding:** temperature 0, seed 20260922, reasoning off, at most 12 output tokens, one request at a time.
- **Prompt layout:** every prompt puts the fixed instructions first and the per-sentence fields (note type, heading, context, sentence) last. Ollama's prompt cache then reuses the shared prefix. The first v3 pilot, with the note type first, ran at about a quarter of the speed.
- **Consistency:** every pilot includes a full rerun, and its agreement is reported (TRIPOD-LLM 6c). Reruns are not guaranteed to be identical: prompt caching and the bundled draft model can shift probabilities slightly. Stored answers, not reruns, are the record.
- **Output:** a plain-text two-word reply, parsed strictly. P(YES), P(NO) and P(UNCLEAR) are read from the first token's top-10 alternatives, and `done_reason` is stored.
  - JSON-schema output was tested and not used. On this Ollama version log probabilities come back for the first token only, and under a schema that token is "{".
- **Deduplication:** a unit is the sentence text plus the context fields shown to the model. Each unit is asked once.
- **Operator steps outside the script:**
  - turn off the Ollama app's automatic updates;
  - set `OLLAMA_NO_CLOUD=1` for the server;
  - keep `OLLAMA_NUM_PARALLEL=1`;
  - rerun the determinism check on at least 1,000 sentences after any Ollama or model change.

## 4. Prompts, verbatim, and how they were developed

**v1** (`scripts/llm_timing_test.py`): "You are reading a sentence from a hospital radiology report or clinical note. Does it state that this patient's liver is fatty or steatotic? Answer with exactly one word: YES, NO, or UNCLEAR. Sentence: {sentence}"

**v2:** v1 with "Answer NO if the sentence says nothing about fat in the liver. Answer UNCLEAR only if it suggests liver fat but is uncertain about it." inserted before the answer instruction.

- **Data used:** v1 and v2 were compared on a 500-sentence pilot drawn from DEV **and TEST**. That exposure of TEST to prompt development is disclosed here (TRIPOD-LLM 9b; MI-CLAIM-GEN Part 2). It concerns only silver-label metrics on TEST; GOLD_HOLDOUT was never used.

**v3** (primary): developed against invented sentences and DEV only. The full text is the constants `V3` and `RULES` in `scripts/llm_sentence_review.py`. Its hash is recorded in each run's manifest. It gives the note type and heading, then the same answer and timing definitions as the annotation guide (`docs/adjudication/llm_sentence_annotation_guide.md`), then the sentence.

**v4:** v3 plus one NO rule (`ALCOHOL_RULE` in the same file): alcohol-related liver disease, alcoholic hepatitis, and cirrhosis or liver fibrosis are NO unless the sentence also says the liver is fatty.

- **Why:** in the full v3 run, about a third of the admissions that only the model called positive rested on sentences with no word about fat. Those were mostly alcohol-related liver disease and cirrhosis (`diagnostics/llm_review_audit/disagreement_reasons.py`).
- **How it was applied:** because v4 only adds a NO criterion, only the units v3 answered YES or UNCLEAR were re-asked with v4. v3's NO answers were carried over. The merged result is in `data/processed/llm_review/full_v4_merged/` (`diagnostics/llm_review_audit/merge_reask.py`).
- **Data used:** this change was decided from count-level diagnostics over DEV and TEST sentences, which is disclosed under §4's data-use rule. It must be confirmed on the annotated sentences before any evaluation.

**Variants for the prompt-sensitivity analysis**, all in the same file:

| Variant | What differs |
| --- | --- |
| `v3_paraphrase_a` | Same rules, reworded |
| `v3_paraphrase_b` | Same rules, terse label format |
| `v3_fewshot` | Seven invented examples covering every answer |
| `v3_context` | Also shows the previous and next sentences |

Paraphrase B's first wording broke the reply format on the invented test set. Its corrected wording is the one in the file.

**Freeze:** the prompt used for any gold-standard evaluation is frozen, with its hash recorded, before gold labels are seen.

## 5. Admission-level label (DECISION: pre-specify before unblinding)

Proposed:
- **Primary:** an admission is positive when at least one kept sentence is YES with timing CURRENT or PAST. FAMILY never counts. UNCLEAR is not positive.
- **Sensitivity analyses, all reported:**
  - UNCLEAR counted positive
  - CURRENT only
  - anatomy-only selection
  - each prompt variant

## 6. Validation and evaluation

- **Sentence-level validation** (`scripts/llm_annotation.py`):
  - two credentialed annotators label blinded workbooks independently, following the annotation guide;
  - a third clinician adjudicates their disagreements;
  - report Cohen's kappa;
  - report sensitivity, PPV and specificity with Wilson 95% intervals, under both UNCLEAR mappings and weighted by how often each sentence occurs.
- **Development set:** the DEV pilot, used for prompt decisions.
- **Evaluation set:** drawn from TEST after the prompt is frozen, stratified by model answer:
  - all YES and UNCLEAR answers;
  - "hard negatives": NO answers containing a fat or echogenicity word, and sentences the selection drops;
  - a random sample of NO answers;
  - inverse-probability weights to restore the population. Balanced 50/50 designs are avoided because they inflate PPV at low prevalence.
- **Against the 400-chart gold standard (decided 2026-10-27):** the LLM scores every GOLD_HOLDOUT admission with prompt v4 (all units, not a re-ask). Its sentence answers and admission labels are hashed and locked by `scripts/llm_gold_lock.py` (`docs/llm_gold_lock.md`) before adjudication begins, as was done for the other model arms (`docs/aim1b_locked_predictions.md`). No answer distribution on GOLD_HOLDOUT is looked at before the adjudication exists.
- **Blinding:** reviewers never see LLM answers, LLM-based ordering, codes or note-rule results (TRIPOD+AI 8c; STARD 13b). If the LLM is used to rank charts, that ranking is never shown to gold reviewers.
- **Fairness:** report sentence coverage and LLM error rates by race, insurance, sex, language and age, with intervals.
- **Downstream use:** if LLM labels feed prevalence estimates or train a model, correct them with design-based methods using the known sampling weights (design-based supervised learning; prediction-powered inference). Never evaluate a model against LLM labels.
- **Quantization (pending approval to download a second model build):** rerun a stratified 1–2k sentences on Gemma 4's smaller quantization-aware build and report how many answers flip. The 8-bit build does not fit in this laptop's memory.

## 7. Contamination and privacy

- **Contamination:** MIMIC-IV-Note v2.2 (January 2023) is credentialed data. No evidence was found that it is in Gemma's pretraining data, and the gold labels are newly created, so they cannot have leaked into the model. Listed as a limitation.
- **Inference:** all inference is local. Sentence text is never printed, logged or committed. Outputs live under `data/` (git-ignored). Ollama's server log at INFO level was checked and does not store prompts.
- **AI assistants:** the coding assistant used on this project ran only count-level diagnostics and never received sentence text.

## 8. Reporting map

| Item (source) | Where |
| --- | --- |
| Model name, version, cutoff (TRIPOD-LLM 6a) | §3; run manifest |
| Inference settings, output consistency (6c) | §3; determinism rerun in every pilot |
| Raw vs parsed output, thresholds (6d, 6e) | `reply`, `strict`, `done_reason`, probabilities in the shards; §5 |
| Annotation (7d, 8a–c) | Annotation guide; `scripts/llm_annotation.py` |
| Prompt development data (9a, 9b; MI-CLAIM-GEN Part 2) | §4 |
| Compute (12) | Run manifest `hardware`; throughput in run logs |
| Fairness (TRIPOD+AI 14, 23a; TRIPOD-LLM 19a) | §6 |
| Selection algorithm (RECORD 6.1, 7.1) | §2; `scripts/liver_sentences.py` |

## References

These were gathered by literature search; verify each against the source before citing in a manuscript.

- Gallifant J et al. TRIPOD-LLM. *Nat Med* 2025;31:60–69. doi:10.1038/s41591-024-03425-5
- Collins GS et al. TRIPOD+AI. *BMJ* 2024;385:e078378
- Miao BY et al. MI-CLAIM-GEN. *Nat Med* 2025;31:1394–1398. doi:10.1038/s41591-024-03470-0
- PhysioNet. Use of MIMIC data with large language models and online services. 24 Sep 2025. https://physionet.org/news/post/llm-responsible-use/
- Vong T et al. Incidental hepatic steatosis on ED imaging using LLMs. *Hepatol Commun* 2025;9:e0638
- Torgersen J et al. Hepatic steatosis by NLP. *Hepatol Commun* 2024;8:e0468
- John BV et al. MASLD by NLP (VALID). *Am J Gastroenterol* 2025;120:2583–91
- Van Vleck TT et al. NLP for NAFLD. *Int J Med Inform* 2019;129:334–41
- Wiest IC et al. Privacy-preserving LLMs on MIMIC-IV. *npj Digit Med* 2024;7:257
- Mukherjee P et al. Vicuna for labeling radiology reports. *Radiology* 2023;309:e231147
- Sclar M et al. Prompt formatting sensitivity. ICLR 2024 (arXiv:2310.11324)
- Egami N et al. Using imperfect surrogates for downstream inference. NeurIPS 2023 (arXiv:2306.04746)
- Harkema H et al. ConText. *J Biomed Inform* 2009;42:839–851
