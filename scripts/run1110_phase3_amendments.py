#!/usr/bin/env python3
"""run_2026-11-10 Phase 3 — add "§6 Amendments dated 2026-11-10" and registry rows S18-S22 to
docs/analysis_plan_prespecified.md, before Phase 4 or 5 computes anything.

The amendment text is copied word for word from Appendix A of docs/run_2026-11-10/RUN_FILE.md by this
script (nothing is retyped). Existing amendments and registry rows are not edited. Idempotent.
"""
import re

PLAN = "docs/analysis_plan_prespecified.md"
RUN_FILE = "docs/run_2026-11-10/RUN_FILE.md"
HEAD = ("*Assembled by Claude Code from the run file Kyle launched; not reviewed by Kyle at commit time; "
        "the purpose of this commit is the timestamp. Exploratory throughout.*")
ROWS = [
    ("S18", "Carry-over check for v3 answers (amendment k)", "`docs/run_2026-11-10/results/carryover_check.json`; `docs/llm_review_protocol.md` §4"),
    ("S19", "Fibrosis index by cell (amendment l)", "`docs/preliminary_2026-11-10.md`"),
    ("S20", "Later outcomes after an uncoded mention (amendment m)", "`docs/preliminary_2026-11-10.md`"),
    ("S21", "Coding by period (amendment n)", "`docs/preliminary_2026-11-10.md`"),
    ("S22", "Documentation funnel where the liver was imaged (amendment o)", "`docs/preliminary_2026-11-10.md`"),
]


def appendix_a():
    text = open(RUN_FILE).read()
    m = re.search(r"## Appendix A[^\n]*\n(.*?)\n---\n\n## Appendix B", text, re.S)
    assert m, "Appendix A not found"
    return m.group(1).strip("\n")


def main():
    s = open(PLAN).read()
    if "## 6. Amendments dated 2026-11-10" in s:
        print("already present"); return
    last = "| S17 | Aim 1b TEST predictions re-scored against the LLM phenotype (amendment j) | 2026-10-27 | exploratory → `docs/aim1b_llm_label.md` |\n"
    assert last in s
    rows = "".join(f"| {i} | {d} | 2026-11-10 | exploratory; not run when this row was committed → {where} |\n" for i, d, where in ROWS)
    s = s.replace(last, last + rows, 1)
    s = s.rstrip("\n") + "\n\n## 6. Amendments dated 2026-11-10\n\n> " + HEAD + "\n\n" + (
        "These analyses were not in the 7 September plan. The text below is copied word for word from Appendix A of "
        "`docs/run_2026-11-10/RUN_FILE.md`. Each amendment states what had already been seen when it was written (\"Already seen\"). "
        "This section was committed before any of these analyses was computed; the commit is recorded in "
        "`docs/run_2026-11-10/STATE.json` as `phase3_commit`.\n\n") + appendix_a() + "\n"
    open(PLAN, "w").write(s)
    print("added §6 and rows", ", ".join(r[0] for r in ROWS))


if __name__ == "__main__":
    main()
