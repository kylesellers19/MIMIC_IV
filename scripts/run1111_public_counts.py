#!/usr/bin/env python3
"""run_2026-11-11 — suppress small counts already published by the September run, without recomputing.

Reads the raw results kept (git-ignored) in data/processed/results_raw/ and rewrites the published copies:
  * Aim 1c level 1: docs/run_2026-09-19/results/aim1c_level1.json, docs/aim1c_level1.md and
    docs/tables/aim1c_level1_*.md through scripts/public_counts.py, and the same cells of the race and
    insurance tables in docs/aim1a_crosstab.md (step 3 repeats those strata's counts);
  * the 571.9 sensitivity: for a definition where fewer than 11 solely-571.9 admissions move out of a cell,
    that count reads <11, the other move is withheld, and so is the 571.9-removed 2x2 (each of its cells
    differs from the current 2x2 by one of those moves) — docs/run_2026-09-19/results/sens_5719.json and
    docs/sensitivity_5719.md;
  * the ConText confusion matrix: counts 1-10 read <11 and, because each row's total is published, the
    smallest off-diagonal cell of at least 11 in that row is withheld — docs/run_2026-09-19/results/
    context_agreement.json, then docs/context_agreement.md through scripts/run0919_context_agreement_doc.py.
Idempotent: it always starts from the raw files. Prints file names and cell counts only.
USAGE: scripts/run0919_env.sh scripts/run1111_public_counts.py
"""
import json
import os
import runpy
import sys

sys.path.insert(0, os.getcwd())
from scripts import aim1c_level1_docs
from scripts.public_counts import FLOOR, SMALL, WITHHELD, aim1c_public, cell, is_small

RAW = "data/processed/results_raw"
RES = "docs/run_2026-09-19/results"
CELLS = ("A", "B", "C", "D")


def load(name):
    with open(f"{RAW}/{name}.json") as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def table_rows(lines, heading):
    """Indexes of the data rows of the first table after a heading line."""
    i, out = lines.index(heading), []
    for j in range(i + 1, len(lines)):
        if lines[j].startswith("#"):
            break
        if lines[j].startswith("|") and not set(lines[j]) <= set("|-: "):
            out.append(j)
    return out[1:]                                  # drop the header row


def set_cells(line, values):
    """Replace cells 1.. of a markdown row (cell 0 is the label) with values, keeping the rest."""
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    for k, v in values.items():
        c[k] = v
    return "| " + " | ".join(c) + " |"


def aim1c():
    pub, masks = aim1c_public(load("aim1c_level1"))
    dump(pub, f"{RES}/aim1c_level1.json")
    aim1c_level1_docs.write(pub)
    hidden = {v: sum(len(m) for m in mk.values()) for v, mk in masks.items()}
    print(f"aim1c_level1: cells hidden per variable {hidden}")

    lines = open("docs/aim1a_crosstab.md").read().splitlines()
    order = {1: "A", 2: "B", 3: "C", 4: "D"}          # code+/note+, code−/note+, code+/note−, code−/note−
    pubrows = {var: {r["stratum"]: r for r in pub["strata"][var]} for var in ("race", "insurance")}
    n = 0
    for var, heading in (("race", "### By race"), ("insurance", "### By insurance")):
        for j in table_rows(lines, heading):
            label = lines[j].strip().strip("|").split("|")[0].strip()
            r = pubrows[var].get(label) or next(r for s, r in pubrows[var].items() if s.startswith(label))
            new = {k: cell(r[c]) for k, c in order.items() if isinstance(r[c], str)}
            if new:
                lines[j] = set_cells(lines[j], new)
                n += len(new)
    open("docs/aim1a_crosstab.md", "w").write("\n".join(lines) + "\n")
    print(f"aim1a_crosstab.md: {n} cells hidden in the step 3 race and insurance tables")


def sens():
    s = load("sens_5719")
    held = []
    for d, rec in s["by_definition"].items():
        moves = rec["solely_5719_cells"]
        if any(is_small(v) for v in moves.values()):
            for k, v in moves.items():
                moves[k] = SMALL if is_small(v) else WITHHELD
            rec["no5719"] = {k: WITHHELD for k in rec["no5719"]}
            held.append(d)
    s["disclosure"] = ("For a definition where fewer than 11 solely-571.9 admissions move out of a cell, that move reads "
                       "<11 and the other move and the 571.9-removed 2x2 are withheld, since either would give it back by "
                       "subtraction (scripts/run1111_public_counts.py).")
    dump(s, f"{RES}/sens_5719.json")

    lines = open("docs/sensitivity_5719.md").read().splitlines()
    tag = {"a": "(a)", "b": "(b)", "c": "(c)", "d": "(d)"}
    first = next(i for i, l in enumerate(lines) if l.startswith("| definition | variant |"))
    for j in range(first + 2, len(lines)):
        if not lines[j].startswith("|"):
            break
        c = [x.strip() for x in lines[j].strip("|").split("|")]
        if c[1] == "571.9 removed" and any(c[0].startswith(tag[d]) for d in held):
            lines[j] = set_cells(lines[j], {k: WITHHELD for k in range(2, 8)})
    second = next(i for i, l in enumerate(lines) if l.startswith("| definition | in A (would move to B)"))
    for j in range(second + 2, len(lines)):
        if not lines[j].startswith("|"):
            break
        c = [x.strip() for x in lines[j].strip("|").split("|")]
        d = next((d for d in held if c[0].startswith(tag[d])), None)
        if d:
            m = s["by_definition"][d]["solely_5719_cells"]
            lines[j] = set_cells(lines[j], {1: m["A (->B)"], 2: m["C (->D)"]})
    open("docs/sensitivity_5719.md", "w").write("\n".join(lines) + "\n")
    print(f"sens_5719: definitions with the 571.9-removed 2x2 withheld: {held}")


def context():
    c = load("context_agreement")
    m = c["confusion_project_rows_medspacy_columns"]
    classes = ["affirmed", "negated", "uncertain", "historical", "family"]
    hide = {}
    for row in classes:
        small = [col for col in classes if is_small(m.get(f"{row}->{col}", 0))]
        if not small:
            continue
        for col in small:
            hide[f"{row}->{col}"] = SMALL
        if len(small) == 1 or sum(m[f"{row}->{col}"] for col in small) < FLOOR:   # the row total is published
            cands = [(m.get(f"{row}->{col}", 0), col) for col in classes
                     if col != row and col not in small and m.get(f"{row}->{col}", 0) >= FLOOR]
            hide[f"{row}->{min(cands)[1]}"] = WITHHELD
    for k, v in hide.items():
        m[k] = v
    c["disclosure"] = ("Counts 1-10 read <11; because each row's total is published, the smallest off-diagonal cell of "
                       "at least 11 in that row is withheld (scripts/run1111_public_counts.py).")
    dump(c, f"{RES}/context_agreement.json")

    runpy.run_path("scripts/run0919_context_agreement_doc.py")     # the doc is written from the results file
    print(f"context_agreement: {sum(v == SMALL for v in hide.values())} cells <11, {sum(v == WITHHELD for v in hide.values())} withheld")


if __name__ == "__main__":
    aim1c()
    sens()
    context()
