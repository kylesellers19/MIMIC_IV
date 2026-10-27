# LLM phenotype: locked GOLD_HOLDOUT answers

Written by `scripts/llm_gold_lock.py` into `docs/run_2026-10-27/results/llm_gold_lock.json` at 2026-10-27T22:11:04Z (code at `27618b1d0ffb`), before chart review.

Every GOLD_HOLDOUT admission was labelled by the local LLM, prompt v4 (`docs/llm_review_protocol.md`). The files below are untracked credentialed derivatives; their SHA-256 hashes are recorded here, so that when the adjudication exists it can be shown the LLM's answers were fixed first and nothing was tuned against them. **No answer distribution on GOLD_HOLDOUT is reported or was looked at.**

| file | rows | SHA-256 |
| --- | --: | --- |
| `data/processed/llm_review/gold_v4/gold_admission_labels_v4.parquet` | 2,865 | `00e7454053184c8805bc298fca3dbf655d6ef5edbdaeed3a58c1186464cc72a1` |
| `data/processed/llm_review/gold_v4/run/sentence_answers.parquet` | 41,773 | `4e224981bcdaae046104bf741b331bb1cd1072260e93d2bb3dbbc24e9cd21e2d` |
| `data/processed/llm_review/gold_v4/liver_sentences_gold.parquet` | 41,773 | `53b068fc359d1030b0c534faa221c7eb646e4594c42316d3889b2358f8f74cce` |
| `data/processed/llm_review/gold_v4/run/manifest.json` | — | `834b5df6e288787bd317a47f367902ab7a4c6c27d98b557e99ab3451b749211c` |

Model: gemma4:26b (25.2B, Q4_K_M), digest `08ae7ec1744bd7f451c4a530afb39d2673ad9d07a8369b8a33a3613b41212a68`, Ollama 0.34.2. Prompt v4, SHA-256 `fe3fada7db8c13d2531507cb37ef11c1616c08977d2ffb16e5802900faaec032`.

Run counts: gold admissions 2,865, sentence rows 41,773, distinct units 20,200, errors 0, unparsed 37, not two word 39.

Dev/test labels (docs/llm_review_preliminary.md) merge v4 answers for units v3 called YES or UNCLEAR with v3's other answers; GOLD_HOLDOUT is answered by v4 throughout.
