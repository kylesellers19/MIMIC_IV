# Decisions for Kyle — run_2026-09-19

Tier 3 items: anything that changes a definition, a population, a primary analysis, or what the paper claims. Each entry gives the question, the options, what each option changes (numbers where computed), and what is blocked until it is decided. No recommendations.

## D-01 · Keep or drop ICD-9 571.9 from the code-positive set (Phase 4.1)

**Question.** The pre-specified code set includes 571.9 ("unspecified chronic liver disease without mention of alcohol"). The 2021 consensus table (Hagström et al., Hepatology 2021, PMID 33486773) does not list it. Keep it or drop it?

**Options and what each changes** (numbers: `docs/sensitivity_5719.md`, `docs/run_2026-09-19/results/sens_5719.json`).
- *Keep 571.9.* Matches every analysis already run (the 2×2, the sample, the weights). Departs from the consensus table; the manuscript must justify the inclusion.
- *Drop 571.9.* Aligns with the consensus. Code-positive falls from 5,740 to 5,700 (40 admissions, 38 subjects, are positive solely through 571.9). Under the primary definition the 2×2 becomes A 5,015 · B 22,811 · C 685 · D 345,481 (recovery share 81.98% vs 81.93%; corroboration 87.98% vs 87.58%). Between 1 and 10 already-sampled charts change cell (exact count in the untracked private folder), which changes the per-cell sample sizes and therefore the sampling weights (revised weights in the sensitivity doc). Every downstream table that uses code status (Aim 1c strata, the structured-arm exclusion list, the estimator weights) would be recomputed.

**Blocked until decided.** Adjudication cannot begin: weights are fixed at sampling time and a cell change after review starts would be a post-hoc reweighting.

## D-02 · Chunked Bio_ClinicalBERT instead of Clinical-Longformer (Phase 3)

**Question.** The methods plan names Clinical-Longformer for long documents. This run encodes everything with chunked Bio_ClinicalBERT (512-token chunks, stride 64, mean+max pooled) because long-attention models are slow or unsupported on this laptop (no MPS on this macOS/torch pairing; CPU only).

**Options.** (i) Keep chunked BERT as the transformer arm and describe it as such in the methods. (ii) Re-run the notes arm with Clinical-Longformer later on other hardware, keeping the same splits, subsample and variants, and report both. (iii) Drop the transformer arm and report TF-IDF only.

**What each changes.** (i) The limitations section states chunked BERT in place of a long-document model. (ii) Adds a hardware dependency and a second embedding run; nothing in this run blocks it — the splits, subsample and text variants are stored. (iii) Removes the embedding-based notes model and PCA features from Phases 8–9.

**Blocked until decided.** Nothing in this run; the manuscript's model description.
