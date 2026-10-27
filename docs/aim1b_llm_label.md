# Aim 1b: how much do silver-label metrics depend on the label?

> **Exploratory (analysis-plan amendment j, committed before this analysis was run).** Both labels are computable phenotypes, not the reference standard. Numbers are written by `scripts/aim1b_llm_label.py` into `docs/run_2026-10-27/results/aim1b_llm_label.json`.

Every model was trained on the frozen rule's label. Here its locked TEST predictions are scored against the rule label and against the LLM phenotype, on 6,164 TEST admissions of the notes subsample (rule-positive 383, LLM-positive 406, Cohen's kappa between the labels 0.82). Intervals: 95% subject-cluster bootstrap, 500 replicates. Caveats: the LLM prompt was revised twice on information that included TEST (amendment h); the notes arms and the LLM read the same notes.

## All TEST admissions

| Arm | n | AUROC, rule label | AUROC, LLM label | Difference | AUPRC, rule label | AUPRC, LLM label | Difference |
| --- | --: | --: | --: | --: | --: | --: | --: |
| CatBoost FS-A (clinical + availability) | 6,164 | 0.854 (0.826–0.882) | 0.846 (0.818–0.872) | -0.008 (-0.022–0.007) | 0.392 (0.305–0.48) | 0.378 (0.291–0.472) | -0.013 (-0.051–0.021) |
| CatBoost FS-B (clinical) | 6,164 | 0.793 (0.758–0.828) | 0.768 (0.732–0.806) | -0.025 (-0.052–0.002) | 0.291 (0.206–0.382) | 0.285 (0.207–0.374) | -0.006 (-0.027–0.019) |
| CatBoost FS-AVAIL (availability only) | 6,164 | 0.778 (0.734–0.82) | 0.782 (0.739–0.821) | +0.004 (-0.011–0.017) | 0.196 (0.151–0.259) | 0.205 (0.157–0.268) | +0.009 (-0.017–0.032) |
| TF-IDF, lexicon sentences deleted (S) | 6,164 | 0.826 (0.782–0.863) | 0.822 (0.782–0.856) | -0.004 (-0.018–0.009) | 0.407 (0.329–0.487) | 0.37 (0.3–0.453) | -0.037 (-0.075–0.001) |
| Embedding head (S), logistic regression | 5,108 | 0.754 (0.699–0.803) | 0.75 (0.702–0.794) | -0.003 (-0.02–0.013) | 0.216 (0.164–0.284) | 0.209 (0.159–0.276) | -0.007 (-0.048–0.034) |
| Notes-augmented CatBoost (FS-B + notes) | 5,108 | 0.829 (0.798–0.861) | 0.821 (0.791–0.854) | -0.008 (-0.027–0.008) | 0.328 (0.245–0.416) | 0.318 (0.238–0.402) | -0.011 (-0.053–0.023) |

## Code-negative TEST admissions

| Arm | n | AUROC, rule label | AUROC, LLM label | Difference | AUPRC, rule label | AUPRC, LLM label | Difference |
| --- | --: | --: | --: | --: | --: | --: | --: |
| CatBoost FS-A (clinical + availability) | 6,057 | 0.842 (0.813–0.869) | 0.834 (0.808–0.858) | -0.007 (-0.026–0.012) | 0.276 (0.219–0.339) | 0.27 (0.215–0.331) | -0.006 (-0.049–0.035) |
| CatBoost FS-B (clinical) | 6,057 | 0.763 (0.729–0.796) | 0.733 (0.695–0.771) | -0.03 (-0.063–0.004) | 0.188 (0.14–0.247) | 0.188 (0.143–0.251) | +0.001 (-0.023–0.027) |
| CatBoost FS-AVAIL (availability only) | 6,057 | 0.782 (0.744–0.818) | 0.786 (0.749–0.82) | +0.004 (-0.015–0.021) | 0.147 (0.116–0.193) | 0.156 (0.122–0.197) | +0.009 (-0.018–0.033) |
| TF-IDF, lexicon sentences deleted (S) | 6,057 | 0.833 (0.795–0.867) | 0.827 (0.793–0.858) | -0.006 (-0.023–0.01) | 0.352 (0.281–0.427) | 0.305 (0.245–0.38) | -0.047 (-0.092–0.0) |
| Embedding head (S), logistic regression | 5,016 | 0.76 (0.719–0.802) | 0.754 (0.717–0.79) | -0.006 (-0.026–0.014) | 0.171 (0.125–0.23) | 0.164 (0.123–0.216) | -0.007 (-0.054–0.039) |
| Notes-augmented CatBoost (FS-B + notes) | 5,016 | 0.826 (0.792–0.858) | 0.816 (0.783–0.849) | -0.01 (-0.035–0.01) | 0.245 (0.19–0.317) | 0.234 (0.182–0.304) | -0.011 (-0.06–0.028) |

