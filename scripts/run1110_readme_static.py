#!/usr/bin/env python3
"""run_2026-11-10 Phase 10.2 — the static edits to README.md (no study number is written here).

  pipeline table        row 16 for this run
  "What is tracked"     the repository is public; every push passes scripts/run1110_push_gate.py; that command
                        replaces the grep check
  "Reference standard"  links the reviewer one-pager, names the tag llm-gold-lock-v1, and says where the
                        criteria revision proposal is
Idempotent. The aim status lines are left as they are: this run changed no fact they state.
"""
import os

README = "README.md"
ROW16 = ("| 16 | Exploratory analyses, record corrections and the push gate (run of 10 November 2026; amendments k–o) | "
         "`run1110_push_gate.py`, `run1110_gated_push.sh`, `run1110_carryover_check.py`, `run1110_fib4_by_cell.py`, `run1110_later_outcomes.py`, "
         "`run1110_icd_era.py`, `run1110_imaging_funnel.py`, `run1110_preliminary_doc.py`, `run1110_reviewer_onepager.py`, `run1110_pilot_packets.py`, "
         "`run1110_manuscript_llm.py`, `run1110_decisions.py`, `run1110_final_report.py` | "
         "`docs/preliminary_2026-11-10.md`, `docs/adjudication/reviewer_onepager.md`, `docs/run_2026-11-10/` (run log, decisions, blockers, final report) |\n")
OLD_CHECK = '''Confirm before any commit:

```bash
git status --short | grep -E "data/|models/|logs/"   # must print nothing
```
'''
NEW_CHECK = '''**This repository is public.** Every push passes `scripts/run1110_push_gate.py`. It checks each unpushed commit, one by one, for: paths under `data/`, `models/` or `logs/`; tabular or binary files; real patient or admission identifiers; note text; counts from 1 to 10; changed lines in `scripts/masld_config.py`; and any change to a frozen or locked file.

Push only this way:

```bash
zsh scripts/run1110_gated_push.sh   # runs scripts/run1110_push_gate.py and pushes only if the gate exits 0
```
'''
OLD_REF = "- **Still needed:** clinician sign-off on the criteria (`docs/adjudication_criteria.md`; every `[CLINICIAN]` flag is an open question) and the reviewers themselves.\n"


def main():
    s = open(README).read()
    if "| 16 |" not in s:
        i = s.index("| 15 | Local-LLM sentence review")
        j = s.index("\n", i) + 1
        s = s[:j] + ROW16 + s[j:]
    if OLD_CHECK in s:
        s = s.replace(OLD_CHECK, NEW_CHECK, 1)
    if "llm-gold-lock-v1" not in s.split("## Reference standard")[1]:
        assert OLD_REF in s
        proposal = "docs/adjudication/criteria_revision_proposal.md"
        tracked = os.popen(f"git ls-files {proposal}").read().strip() != ""
        prop_line = (f"- **Proposed revision of the criteria:** [{proposal}]({proposal}).\n" if tracked else
                     "- **Proposed revision of the criteria:** a proposal exists but is not in this repository yet. The push gate holds it back "
                     "(`docs/run_2026-11-10/BLOCKERS.md`, B-01; decision N-09).\n")
        s = s.replace(OLD_REF, OLD_REF
                      + "- **Lock tag:** the commit that locked the language model's answers carries the annotated tag `llm-gold-lock-v1`.\n"
                      + "- **For prospective reviewers:** [docs/adjudication/reviewer_onepager.md](docs/adjudication/reviewer_onepager.md), one page on the task, the hours and the access needed. "
                        "It is held until two open decisions are made (N-08 and N-10 in `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`).\n"
                      + prop_line, 1)
    open(README, "w").write(s)
    print("README static edits applied")


if __name__ == "__main__":
    main()
