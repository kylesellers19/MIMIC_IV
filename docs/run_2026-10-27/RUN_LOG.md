# Run log — run_2026-10-27 (local-LLM review, exploratory)

What was done and why. Numbers live in `results/`, written by the scripts named here.

1. **Amendment first.** Analysis-plan amendments (h)–(j) and registry entries S15–S17 were committed in `6338243`, before any stratum-level LLM result or any Aim 1b re-scoring existed. They say exactly what had already been seen.
2. **LLM phenotype.** `scripts/llm_phenotype.py` defines the admission-level label from the merged v4 answers (`docs/llm_review_protocol.md`). The scope is the dev/test notes subsample; GOLD_HOLDOUT is untouched.
3. **Preliminary results.** `scripts/llm_review_results.py` writes `results/llm_review_preliminary.json` and `docs/llm_review_preliminary.md`.
   - The LLM-versus-rule comparison is restricted to uncoded admissions, because the coded group's rule-by-LLM cells include counts below 11 that could be recovered by subtraction.
4. **Aim 1c.** `scripts/aim1c_llm_level1.py` writes `results/aim1c_llm_level1.json` and `docs/aim1c_llm_level1.md`: E1–E3 plus coverage, with a subject-cluster bootstrap.
   - Only stratum admission counts are published. Percentages are withheld when the count behind them or its complement is 1–10.
5. **Aim 1b.** `scripts/aim1b_llm_label.py` writes `results/aim1b_llm_label.json` and `docs/aim1b_llm_label.md`. The locked TEST predictions are scored against both labels; nothing is retrained and no locked file is touched.
6. **README.** `scripts/readme_preliminary.py` writes the README's "Preliminary results" block from the results files.
7. **GOLD_HOLDOUT lock.** `scripts/liver_sentences.py --partitions GOLD_HOLDOUT` extracted 41,773 sentence rows. Prompt v4 answered all 20,200 distinct units with `--include-gold` (0 errors), and `scripts/llm_gold_lock.py` wrote `results/llm_gold_lock.json` and `docs/llm_gold_lock.md` before any chart review. Only hashes and run counts are recorded; no answer distribution on GOLD_HOLDOUT was looked at.
8. **After the lock:** the admission rule (protocol §5) was signed off, and Ollama's automatic updates and cloud features were turned off (protocol §3). The main model's digest and the Ollama version were unchanged after the restart. The quantization check (protocol §6, `diagnostics/llm_review_audit/quant_check.py`) ran on DEV/TEST units only.

**Open decisions:**
- The annotation guide's open questions. (The admission rule, protocol §5, was signed off on 2026-10-27.)
- Who the two annotators are.
