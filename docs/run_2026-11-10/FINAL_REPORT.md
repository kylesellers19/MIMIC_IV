# Final report — run_2026-11-10

Branch `run/2026-09-19`. Assembled by `scripts/run1110_final_report.py` from this run's own records; every number is read from a results file, the state file, the gate's log or git.

## Incidents first

- **I-01 · INCIDENT — one push went out while the gate was failing** — `docs/run_2026-11-10/BLOCKERS.md`.
- In one sentence: one push went out while the gate was failing, because the push command depended on the wrong exit status. The gate's failure was a false positive and nothing sensitive was published. Pushes since go through `scripts/run1110_gated_push.sh`.

## Outcome

The run finished 12 of 12 phases in 2.1 hours. The frozen and locked files were unchanged from start to end (11 frozen, 24 locked; no drift). The exposure risk in the working tree was closed (every CSV ignored again, heading tables moved under `data/`), a push gate was built and every commit of the run passes it, and the record was corrected in the protocol, the October run log and the reference-standard document. Amendments (k)–(o) were committed and pushed before any of their analyses was computed. The exploratory results, none validated against chart review: among admissions with a computable FIB-4, 45.4% (44.3–46.6) of uncoded note-positive admissions are above 2.67, against 54.9% (52.3–57.7) of coded ones and 32.4% (32.0–32.8) where neither axis is positive; of patients first documented without a code who returned, 11.6% (10.8–12.4) were later coded and 8.4% (7.7–9.1) later carried a cirrhosis code; where the liver was imaged and a report was rule-positive, the discharge summary repeated it in 39.7% (38.7–40.7), and coding was 31.7% (30.4–33.1) when it did against 2.8% (2.5–3.2) when it did not. The carry-over check asked 3,000 carried-over NO units with v4: the answer was no longer NO for at most 0.67%, and the expected number of dev/test admissions changing label is at most 37 of 29,980. Two files the run was asked to commit fail the gate and stayed local, and the gate's rule also flags lines that were already public before the run. No GOLD_HOLDOUT file was opened; no adjudication exists; D-01 still blocks its start.

## Phases

| Phase | Status | Commit | Start (UTC) | End (UTC) | Note |
| --- | --- | --- | --- | --- | --- |
| 0 · preflight | done | `302c908` | 03:00 | 03:03 |  |
| 1 · exposure risk closed + push gate | done | `1791757` | 03:03 | 03:17 | two listed files held back by the gate (B-01); tag llm-gold-lock-v1 pushed |
| 2 · record corrected (documents) | done | `3aec3fb` | 03:17 | 03:20 |  |
| 3 · amendments (k)-(o), S18-S22 | done | `2b32fde` | 03:20 | 03:20 |  |
| 4 · carry-over check (background) | done | `a865907` | 03:21 | 05:03 | 3,000 units, 0 errors, inside the 2-hour budget |
| 5 · exploratory analyses (l)-(o) | done | `1e314d8` | 03:22 | 03:32 |  |
| 6 · materials for prospective reviewers | done | `bc15983` | 03:32 | 03:40 |  |
| 7 · manuscript drafts: language-model arm | done | `05ee628` | 03:35 | 03:42 | carry-over paragraph pending Phase 4; refilled when it finishes |
| 8 · citations | done | `113656d` | 03:42 | 03:49 |  |
| 9 · decisions file | done | `896986f` | 03:54 | 03:59 | N-02 cost figures pending Phase 4; regenerated when it finishes |
| 10 · README, push, check on GitHub | done | `f0db22b` | 04:00 | 05:04 |  |
| 11 · final audit, report, notification | done | `` | 05:04 | 05:04 | the commit that adds the final report follows this file |

Commits in this run: **12** (`ac58d57..f0db22b`). The amendments commit is `2b32fde`.

## The five things to read first

1. **`docs/run_2026-11-10/BLOCKERS.md`** — I-01 (the push on a failing gate), F-01 (lines already public that the new rule flags) and B-01 (two files held back).
2. **`docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`** — ten new items with options and draft amendment text. N-06 holds the crosswalk between the chart scale and the locked prompt; N-10 is a conflict between the one-pager and criteria §10. D-01 still blocks adjudication.
3. **`docs/preliminary_2026-11-10.md`** — the four exploratory analyses with their limitations. Section 1's sensitivity table shows how far FIB-4 moves when inpatient values are replaced.
4. **`scripts/run1110_push_gate.py`** (docstring) and the "Deviations" section of the run log — the gate's three exemptions, one of which was refined during the run after the gate failed on an article title.
5. **`docs/run_2026-11-10/results/carryover_check.json`** and protocol §4 — what re-asking the carried-over answers would change, which feeds decision N-02.

## Deviations from the run file

Full text in `docs/run_2026-11-10/RUN_LOG.md`, section "Deviations".

- Phase 1.2 — six files moved, not eight.
- Phase 1.4 — three stated exemptions in gate check (d).
- Phase 1.6 — two listed files not committed.
- Phase 2.1 — the sign-off commit did not change documents only.
- Phase 5 (l), details the amendment leaves open.
- Phase 5 (m), details the amendment leaves open.
- Phase 5 (n).
- Phase 5 (o).
- Phase 6.2 — the draw.
- Phase 8 — a gate exemption was refined after the gate failed.
- Phase 6.1 and criteria §10.
- Phase 9 — two items beyond Appendix B.
- Phase 10.2 — the criteria proposal is not linked.
- Phase 10.2 — the command shown.
- Phase 1.4 — the gate checks each unpushed commit.

## Blockers, incidents and findings

Full text in `docs/run_2026-11-10/BLOCKERS.md`.

- I-01 · INCIDENT — one push went out while the gate was failing
- B-01 · Two files named in Phase 1.6 fail the push gate and were not committed
- F-01 · FINDING — the already-public repository contains lines the new gate rule would flag

## Decisions waiting for Kyle

New, in `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`:

- N-01 · Admission-level probability for the language-model arm
- N-02 · Prompt-version difference between dev/test and GOLD_HOLDOUT
- N-03 · Sample admissions with no kept sentence
- N-04 · Note axis for Aim 1a
- N-05 · The alternative section-closing rule
- N-06 · Reviewer criteria against the locked prompt
- N-07 · Registration (updates D-04)
- N-08 · What prospective reviewers are offered
- N-09 · Material the push gate flags
- N-10 · The one-pager states the study question; the criteria say reviewers are not told it

Carried over from September (`docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`); **D-01 blocks the start of adjudication**:

- D-01 · Keep or drop ICD-9 571.9 from the code-positive set (Phase 4.1)
- D-02 · Chunked Bio_ClinicalBERT instead of Clinical-Longformer (Phase 3)
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

## What is public now, and what stayed local

- **Public:** commits `ac58d57..f0db22b` on `run/2026-09-19` (12 commits), and the tag(s) `llm-gold-lock-v1`.
- **Local head when this report was written:** `f0db22b`; remote head: `f0db22b` (equal). The commit that adds this report comes after both and is pushed through the gate like the others.
- **Check on GitHub (Phase 10.4):** remote head equal to local head: True; README on the remote shows the new sub-block: True, with the not-validated banner before it: True; tabular files added during the run: 0; binary files changed: 0 (`docs/run_2026-11-10/results/github_check.json`). The rendered page was also opened read-only in the browser; see the run log.
- **Tags that exist only on this machine:** `note-phenotype-v1.0.0`, `note-phenotype-v1.1.0`. This run was told to push one tag and pushed one (decision N-07).
- **Untracked, on this machine only:** `docs/adjudication/criteria_revision_proposal.md`, `scripts/llm_timing_test.py` — they fail the gate's note-text rule (B-01, N-09).
- **Never tracked, by design:** everything under `data/` and `logs/`, listed with sizes below.

## Gate results

Recorded run over the whole run (`docs/run_2026-11-10/results/push_gate.json`): base `ac58d57`, head `f0db22b`, 74 files, 12 commits checked one by one.

| Check | Result | Findings |
| --- | --- | --: |
| a_forbidden_paths | PASS | 0 |
| b_tabular_or_binary | PASS | 0 |
| c_identifiers | PASS | 0 |
| d_note_text | PASS | 0 |
| e_small_counts | PASS | 0 |
| f_config_append_only | PASS | 0 |
| g_frozen_hashes | PASS | 0 |

Gate runs during the run (`logs/run_2026-11-10/push_gate.log`, untracked): 24 in all, 19 passed and 5 failed. Each failure was followed by a fix or by holding files back, except the one described in I-01, which was followed by a push.

Frozen-artifact hashes at the end against the start (`docs/run_2026-11-10/results/frozen_hashes_end.json`): 0 changed, 0 lock mismatches, 0 missing.

Test suite at the end: 112 passed, 0 failed.

## Disk used by this run (all untracked)

| Location | Files | Size |
| --- | --: | --: |
| `data/processed/pilot_packets_2026-11-10` | 32 | 852.6 KB |
| `data/processed/run_2026-11-10_private` | 1 | 3.2 KB |
| `data/processed/section_rule_v2_private` | 6 | 1.0 MB |
| `data/processed/llm_review/carryover_check` | 10 | 997.3 KB |
| `data/processed/run_2026-11-10_outpt_fib4.parquet` | 1 | 2.7 MB |
| `data/processed/run_2026-11-10_scratch` | 53 | 17.5 MB |
| `logs/run_2026-11-10` | 3 | 6.9 KB |

Total: 23.0 MB.

## Hours used

2.1 hours from start to this report, of a budget of 10. The language-model run took 1.66 hours of its 2-hour budget.
