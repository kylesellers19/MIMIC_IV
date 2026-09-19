# Final report — run_2026-09-19

Branch `run/2026-09-19` off `main`. Assembled by `scripts/run0919_final_report.py` from this run's own records; every number is read from a results file, the git log, or the audit.

## Outcome

The environment reproduced every anchor number from earlier sessions (14/14 integrity checks) and the run then completed every phase it could without a human reader: the hypotheses were committed before any model existed; the 400-chart sample's subjects were removed from all model fitting; the Aim 1a loose ends, the equity audit at the computable stage, the whole reference-standard machinery short of a clinician, the structured and notes model arms, the manuscript drafts, the citation verification and the release audit were all produced. The substantive finding of the day is that the silver label is largely a property of documentation rather than of patients: a model given only availability and volume features, with no clinical value at all, reaches AUROC 0.812 against 0.787 for the clinical features alone, and 0.857 for both together. Class weighting was shown to wreck calibration (intercept -2.38) while the analytic prior correction repairs it (+0.18), which tests and partly overturns the expectation recorded on 7 September. No number anywhere in this run is validated against human adjudication, because the chart review has not happened; the headline Aim 1a estimate remains empty by design.

## Phases

| phase | status | commit | note |
| --- | --- | --- | --- |
| 0 —  | done | `1dfc52d` |  |
| 1 — pre-specification commit | done | `e2a4e1e` | 1.2 skipped — criteria Draft 1 verified-existing in docs/adjudication_criteria.md |
| 2 — training draw + splits | done | `d760d98` |  |
| 3 — notes text + embeddings (background) | done | `79a016c` | done — 28/33 shards encoded within the 5 h budget; 100% of GOLD_HOLDOUT |
| 4 — Aim 1a loose ends | done | `816215b` |  |
| 5 — Aim 1c level 1 | done | `816215b` |  |
| 6 — reference-standard machinery | done | `eeed2a9` | delegated to subagent |
| 7 — Aim 1b structured arm | done | `877ead3` | commit 877ead3 |
| 8 — Aim 1b notes arm | done | `` | done — 8.1 TF-IDF U/M/S; 8.2 embedding heads; 8.3 notes-augmented CatBoost |
| 9 — fusion + locked predictions + gold harness | done | `` | done — fusion stack, 2,865 gold predictions locked and hashed, gold harness + CV scaffold tested on synthetic labels |
| 10 — writing, citations, admin | done | `` | 10.1-10.3 commit 3991128; 10.4-10.6 commit db5a460 |
| 11 — release-readiness, audit, final report | done | `` | done — 11.1 release files, 11.2 tests (72), 11.3 audit (8/8), 11.4 final report |

Commits on this branch: **21**.

## The five things to read first

1. **`docs/aim1b_structured.md`**, section "What the attributions say" — availability and volume features alone out-discriminate the clinical features. This is the run's main empirical finding and it is a statement about the data, not a model success.
2. **`docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`** — every protocol question this run refused to answer, with what each option costs. D-01 (ICD-9 571.9) blocks the start of adjudication.
3. **`docs/charlson_validation.md`** §2–3 — the comorbidity gap between the recovery zone and the concordant cell was the phenotype code itself; it vanishes when the liver categories are removed.
4. **`docs/aim1c_level1.md`** — recovery and corroboration by stratum, with the strata that cannot support a claim named rather than merged.
5. **`docs/aim1a_precision_forecast.md`** — how precise the headline estimate can be, and why cell D dominates its width.

## Deviations from the run file

- **Phase 1.2 skipped** — adjudication criteria Draft 1 already existed in `docs/adjudication_criteria.md` with every `[CLINICIAN]` flag inline (Phase 0.4 verified it).
- **Clinical-Longformer replaced by chunked Bio_ClinicalBERT** — no Metal Performance Shaders on this macOS/torch pairing, so encoding ran on CPU. Logged as D-02.
- **Embedding subsample sized to the measured pilot** rather than to the 60,000 ceiling, and the budget enforced by a manager process that encoded the gold-holdout shards first.
- **Structured-arm tuning used 4 configurations per learner, not 20**, chosen once on FS-A and reused across feature sets and imbalance variants, to fit the time budget.
- **Stretch item 1 (variant U embeddings) skipped** — the run file notes it mostly demonstrates circularity, which Phase 8.1's TF-IDF already showed at no cost. **Stretch item 3 skipped** — FINETUNE_BUDGET_HOURS = 0.
- **LightGBM and XGBoost run through `scripts/run0919_env.sh`**, which points the dynamic loader at the OpenMP library bundled with torch; no system install was made.
- **The audit's own leak detectors were rewritten twice** after they produced false positives, so that the exemptions are principled rather than a list of excused files.
- **The run file's Appendix B (citation list) never arrived** — the message was truncated — so the citation registry was built from the repository's own citation strings instead.

## Blockers and incidents

Full text in `docs/run_2026-09-19/BLOCKERS.md`.

- B-01 · Run file truncated in transmission (Appendix A tail and all of Appendix B missing)
- B-02 · LightGBM / XGBoost could not load libomp
- B-03 · MPS unavailable
- B-04 · INCIDENT — raw note text was written to a log file by a third-party library, and a log was deleted to remove it

## Decisions waiting for Kyle

Full text, with options and stakes, in `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`.

- D-01 · Keep or drop ICD-9 571.9 from the code-positive set (Phase 4.1)
- D-02 · Chunked Bio_ClinicalBERT instead of Clinical-Longformer (Phase 3)
- Phase 6 decisions (P6-01 … P6-06) — merged from phase6_decisions.md
- P6-01 · "Insufficient information" in the headline estimate
- P6-02 · Final label for double-reviewed charts that disagree (criteria D8)
- P6-03 · Weighting scheme for the ordinal (4-level) kappa
- P6-04 · Alcohol question 6b option labels in the form (criteria D6)
- P6-05 · Precision at low prevalence in cell D (design finding, not a choice already made)
- P6-06 · Which positive levels collapse to "positive" (criteria D1) — supported, not decided
- D-03 · License and the timing of a public code release (Phase 11.1)
- D-04 · Public registration versus the repository's git audit trail (Phase 10.1)
- D-05 · The "pre-registered" wording that needs correcting (Phase 10.1)
- D-06 · What the manuscript may claim from the transformer-versus-TF-IDF comparison (Phase 10.4)
- D-07 · How the notes arm is ultimately trained (Phase 8)
- P6-01 · "Insufficient information" in the headline estimate  *(`phase6_decisions.md`)*
- P6-02 · Final label for double-reviewed charts that disagree (criteria D8)  *(`phase6_decisions.md`)*
- P6-03 · Weighting scheme for the ordinal (4-level) kappa  *(`phase6_decisions.md`)*
- P6-04 · Alcohol question 6b option labels in the form (criteria D6)  *(`phase6_decisions.md`)*
- P6-05 · Precision at low prevalence in cell D (design finding, not a choice already made)  *(`phase6_decisions.md`)*
- P6-06 · Which positive levels collapse to "positive" (criteria D1) — supported, not decided  *(`phase6_decisions.md`)*

## Release audit

`scripts/run0919_final_audit.py`, results in `docs/run_2026-09-19/results/final_audit.json`.

| check | result | detail |
| --- | --- | --- |
| (a) nothing under data/, models/, logs/ is tracked | PASS | 0 tracked files |
| (b) 8-digit integers on changed files | PASS | 110 hits, all exempt (seeds, byte counts, citation identifiers) |
| (c) counts 1–10 in count columns | PASS | 0 found |
| (d) note text in tracked documents | PASS | 0 de-identification placeholders, 0 report headers, 0 long windows |
| (e) frozen-artifact hashes unchanged | PASS | 5 artifacts, 0 changed |
| (f) tags identical to the start | PASS | note-phenotype-v1.0.0, note-phenotype-v1.1.0 |
| (g) no remote | PASS | 0 configured |
| (h) masld_config.py additions only | PASS | +12 lines, −0 |

Test suite: `a9e26da` — run `.venv/bin/python -m pytest -q`.

## Disk used by new derivatives (all untracked)

| path | size |
| --- | --: |
| `data/processed/run_2026-09-19_notes_text` | 528 MB |
| `data/processed/notes_embeddings_v1` | 82 MB |
| `data/processed/run_2026-09-19_preds` | 60 MB |
| `models/run_2026-09-19` | 50 MB |
| `data/processed/run_2026-09-19_notes_index` | 45 MB |
| `data/processed/run_2026-09-19_features.parquet` | 20 MB |
| `data/processed/run_2026-09-19_outpt_labs.parquet` | 18 MB |
| `data/processed/run_2026-09-19_lab_features.parquet` | 7 MB |
| `data/processed/run_2026-09-19_charlson.parquet` | 3 MB |
| `data/processed/run_2026-09-19_scratch` | 1 MB |
| `data/processed/gold_holdout_predictions_v1.parquet` | 1 MB |
| **total** | **0.80 GB** |

## Keeping or discarding this run

To keep the work:

```bash
git checkout main
git merge --no-ff run/2026-09-19
```

To discard the tracked work:

```bash
git checkout main
git branch -D run/2026-09-19
```

Untracked derivatives under `data/processed/` and `models/` stay on disk either way; `docs/admin/data_inventory.md` lists them.

