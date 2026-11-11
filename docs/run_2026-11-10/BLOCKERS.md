# Blockers — run_2026-11-10

Each entry: what failed · what was tried (at most three attempts or 20 minutes) · what was skipped as a result. Incidents are headed `INCIDENT`. Findings about material that predates this run are headed `FINDING`.

## I-01 · INCIDENT — one push went out while the gate was failing

- **What happened.** The Phase 8 commit (`113656d`) was pushed although the gate had printed "GATE FAILED". The command was `gate | tail -1 && git push`: the shell took the exit status of `tail`, which is always zero, so the push did not depend on the gate at all. Every earlier push of this run used the same pattern. In each of those the gate had passed, so only this push went out on a failure, but none of them was actually conditional on the gate.
- **What the gate had flagged.** Check (e), small counts, on two lines of `results/base_exposure_audit.json`. Both are counts of flagged lines in a file, written under a key that is the file's path; the path contains the word "sentences", which the check reads as a count of sentences. Neither is a count of patients, admissions or notes. No note text, no identifier and no small patient count was published.
- **How it was checked.** The gate was rerun on the pushed commit and on the whole range of the run from its start. After the false positive was fixed (a file path used as a JSON key is not a patient count; a test covers it), both runs exit 0.
- **What was changed.** Pushing now goes only through `scripts/run1110_gated_push.sh`, which runs the gate with nothing piped after it and pushes only when the gate itself exits 0. No push since has used anything else.
- **What was not done.** Nothing was removed from the remote and no history was rewritten (guardrail 7). PUSH was left on: the run file switches it off when note text or an identifier escapes, which did not happen. If Kyle reads this differently, the commits after `113656d` are the ones to look at.
- **Why it matters beyond this push.** The rule "push only immediately after the gate exits 0" was being followed by reading the gate's last line, not by its exit status. That is a weaker control than the run file asked for.

## B-01 · Two files named in Phase 1.6 fail the push gate and were not committed

- **What failed.** The gate's note-text check (d3: any window of 30 or more characters matching a liver-extractor sentence or its neighbours) fails `scripts/llm_timing_test.py` and `docs/adjudication/criteria_revision_proposal.md`. Both were staged, the gate failed, and both were unstaged again. Neither is in any commit.
- **What the matches are.** Counts are in `results/held_back_files.json` (`scripts/run1110_exposure_audit.py --held`): lines flagged per file, the longest overlap in characters, how many extractor strings contain each overlap, and how many quoted strings equal a whole extractor string.
  - `criteria_revision_proposal.md`: short overlaps inside the study's own criteria prose. No quoted string equals a whole extractor string.
  - `llm_timing_test.py`: the overlaps are in its list of probe sentences. Some quoted probe sentences equal a whole extractor string. Whether those are invented sentences that coincide with stock report phrasing, or sentences taken from reports, cannot be told from counts, and the file was not read to find out.
- **What was tried.** Nothing beyond the statistics. The gate's exemptions are narrow on purpose (already-public text, marked test fixtures, published disease names), and none applies. Rewording Kyle's criteria text or a recorded probe set was not attempted: it would change documents this run was asked only to commit.
- **What was skipped.** The two files stay untracked on this machine. Phase 10 does not link the criteria proposal from the README. The question of what to do with them is item N-09 in `DECISIONS_FOR_KYLE.md`.

## F-01 · FINDING — the already-public repository contains lines the new gate rule would flag

- **What was found.** `scripts/run1110_exposure_audit.py` applied the gate's checks (c) and (d) to every text file at the remote base, with no exemption for already-public text. Result: `results/base_exposure_audit.json`. No identifier was found. The note-text checks flag lines in tracked documents, scripts and tests; the per-file counts, the longest overlap per file and how many extractor strings contain each overlap are in that file.
- **What it means and does not mean.** September's audit allowed short context windows around a lexicon match and passed these files. The 10 November run file sets a stricter rule (30 characters) for a repository that is now public. A flagged line is an overlap of 30 or more characters with a dev/test extractor string. It may be an invented example in report phrasing, a code title, or text taken from a note. The file with the most flagged lines is named first in the results file; most of its overlaps occur in exactly one extractor string.
- **What was done.** Nothing was changed. The flagged lines were not read. History was not rewritten and nothing was removed from the remote (guardrail 7). Pushing continued, because every push adds only lines that pass the gate.
- **What is waiting.** Whether those lines need to be reviewed and replaced is item N-09 in `DECISIONS_FOR_KYLE.md`.
