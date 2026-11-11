# run_2026-11-11 — small counts in already-published documents

**Why.** The README states that counts from 1 to 10 appear as <11, but documents written in August and September published some exactly. The push gate added on 10 November checks only newly added lines, and only columns whose headers it recognised, so they were never flagged.

**Audit.** Every tracked `.md` and `.json` was scanned for table cells, JSON values and prose counts from 1 to 10. Ranks, fold numbers, ICD versions, design allocations, medians and settings were set aside as not counts. Counts of admissions, patients, notes, lab or omr values, or mentions were found in these files:
- Aim 1c level 1: `docs/aim1c_level1.md`, `docs/tables/aim1c_level1_*.md`, `results/aim1c_level1.json`, and the same strata's cells in step 3 of `docs/aim1a_crosstab.md`;
- the 571.9 sensitivity: `docs/sensitivity_5719.md`, `results/sens_5719.json`;
- ConText agreement: `docs/context_agreement.md`, `results/context_agreement.json`;
- cleaning and data quality: `docs/cleaning_execution.md`, `docs/cleaning_spec.md`, `docs/tables/tableS1.md` (and its `clean/` copy), `docs/data_quality_report.md`;
- corpus diagnostics: `docs/corpus_exploration.md`, `docs/fatty_trigger_diagnostic.md`.

**Fix.**
- Each such count now reads <11.
- Where a published total would give a hidden count back by subtraction, a second cell reads *withheld*. Those totals are a stratum's n, the overall 2×2, a class's mention count, or the total of impossible omr values in Table S1.
- **Shares:** any share computed from a hidden cell is withheld too.
- **571.9 sensitivity:** definitions (a), (c) and (d) move fewer than 11 admissions out of cell A, and the difference between their two published 2×2 tables gave that number. Their 571.9-removed tables are therefore withheld. The primary definition (b) is unchanged.
- **Code:** `scripts/public_counts.py` holds the suppression. `scripts/run0919_aim1c_level1.py` and `scripts/run0919_context_agreement_doc.py` now write through it, and the raw results stay in `data/processed/results_raw/` (git-ignored). `scripts/run1111_public_counts.py` re-applied it without recomputing anything.
- **Tests:** `tests/test_public_small_counts.py` fails if any tracked file publishes such a count again. The push gate's count check now also recognises the cell, cleaning and corpus column headers.

**Not changed.**
- Git history still holds the earlier versions of these files, which have been on GitHub since 22 September 2026.
- Removing them would mean rewriting the branch and force-pushing. That would change every commit hash, including the ones the lock records and the `llm-gold-lock-v1` tag point to. That decision is Kyle's.
- No frozen or locked artifact was touched.
