#!/usr/bin/env python3
"""run_2026-09-19 — cross-check numbers in the manuscript drafts against the results files.

Collects every value found anywhere in docs/run_2026-09-19/results/*.json (recursively, as both raw
and comma-grouped/rounded string forms), then scans the drafts for numeric tokens and reports which
ones are NOT attributable to a results file. This cannot prove a number is used correctly; it catches
numbers that exist nowhere in the run's outputs — the fingerprint of a value written from memory.
Writes docs/run_2026-09-19/results/doc_number_check.json."""
import json, glob, os, re, sys

DOCS = ["docs/manuscript_methods_draft.md", "docs/manuscript_results_skeleton.md",
        "docs/tripod_ai_checklist.md", "docs/aim1b_structured.md", "docs/aim1c_level1.md",
        "docs/sensitivity_5719.md", "docs/charlson_validation.md", "docs/aim1a_loose_ends.md",
        "docs/aim1b_splits.md", "docs/aim1b_notes.md"]
NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w])")


def forms(v):
    """Every string a number might legitimately be written as in prose."""
    out = set()
    if isinstance(v, bool) or v is None:
        return out
    if isinstance(v, int):
        out |= {str(v), f"{v:,}", str(abs(v)), f"{abs(v):,}"}
    elif isinstance(v, float):
        out.add(repr(v))
        for d in range(0, 6):
            out.add(f"{v:.{d}f}"); out.add(f"{abs(v):.{d}f}")
            out.add(f"{v*100:.{d}f}"); out.add(f"{abs(v)*100:.{d}f}")
        if abs(v - round(v)) < 1e-9:
            out |= {str(int(round(v))), f"{int(round(v)):,}"}
    return {s.lstrip("-") for s in out}


def harvest(o, acc):
    if isinstance(o, dict):
        for v in o.values():
            harvest(v, acc)
    elif isinstance(o, list):
        for v in o:
            harvest(v, acc)
    else:
        acc |= forms(o)


def main():
    known = set()
    files = sorted(glob.glob("docs/run_2026-09-19/results/*.json"))
    for f in files:
        try:
            harvest(json.load(open(f)), known)
        except (json.JSONDecodeError, OSError):
            continue
    # Numbers are also legitimately sourced from the project's pre-existing aggregate documents
    # (the drafts were told to trace to a results file OR to an existing tracked document).
    SOURCE_DOCS = [d for d in glob.glob("docs/*.md") + glob.glob("docs/tables/**/*.md", recursive=True)
                   if d not in DOCS]
    for d in SOURCE_DOCS:
        try:
            for m in NUM.finditer(open(d, encoding="utf-8", errors="replace").read()):
                known.add(m.group(1)); known.add(m.group(1).replace(",", ""))
        except OSError:
            continue
    report_sources = len(SOURCE_DOCS)

    # structural numbers that are not study results
    for n in range(0, 101):
        known |= {str(n), f"{n}.0"}
    known |= {"2023", "2024", "2025", "2026", "2021", "2005", "1987", "2016", "2009", "2001", "2019", "2022",
              "365", "512", "1536", "1000", "2000", "500", "400", "300", "250", "200", "150", "100", "1.1.0", "1.0.0"}
    report = {"results_files_scanned": len(files), "source_docs_scanned": report_sources,
              "distinct_known_numeric_forms": len(known), "docs": {}}
    for doc in DOCS:
        if not os.path.exists(doc):
            continue
        unattributed, total = {}, 0
        for i, line in enumerate(open(doc, encoding="utf-8", errors="replace").read().splitlines(), 1):
            if re.search(r"\b(PMID|doi|DOI|http|version|v\d|Python|==)\b", line):
                continue
            line = re.sub(r"20\d{2}-\d{2}-\d{2}", " ", line)        # ISO dates
            line = re.sub(r"\bK7\d|\b57\d\.\d\b", " ", line)       # ICD codes are identifiers, not results
            for m in NUM.finditer(line):
                tok = m.group(1); total += 1
                if tok in known or tok.replace(",", "") in known:
                    continue
                unattributed.setdefault(tok, []).append(i)
        report["docs"][doc] = {"numeric_tokens": total, "unattributed_distinct": len(unattributed),
                               "unattributed": {k: v[:4] for k, v in sorted(unattributed.items(), key=lambda x: -len(x[1]))[:40]}}
    json.dump(report, open("docs/run_2026-09-19/results/doc_number_check.json", "w"), indent=1)
    for doc, r in report["docs"].items():
        print(f"{doc:46s} {r['numeric_tokens']:6d} tokens  {r['unattributed_distinct']:4d} unattributed")
    return report


if __name__ == "__main__":
    main()
