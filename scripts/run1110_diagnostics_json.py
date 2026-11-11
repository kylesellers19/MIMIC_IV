#!/usr/bin/env python3
"""run_2026-11-10 Phase 1.3 — re-express the aggregate diagnostic tables as counts-only JSON.

The CSVs stay on disk, git-ignored (every CSV is ignored). This script writes, under
docs/run_2026-11-10/results/:
    diag_cap_sweep.json              from diagnostics/liver_sentence_cap/cap_sweep_summary.csv
    diag_unclear_audit.json          from diagnostics/llm_unclear_audit/unclear_audit_summary.csv
    diag_section_tableB.json         from diagnostics/section_rule_v2/tableB_continuing_headings.csv
    diag_section_study_headers.json  from diagnostics/section_rule_v2/step5_study_headers.csv

Small cells: a count of 1-10 is written as "<11". Where a total is published next to it, a second
cell of the same row or column is withheld as well ("withheld"), so the small count cannot be
recovered by subtraction; a percentage whose numerator or complement is masked is withheld too.
Heading labels are published only when they are entries of the study's own sub-heading list
(FINDINGS_SUBHEADINGS in scripts/liver_sentences.py); no heading text from notes is written.
"""
import json, os, sys
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.liver_sentences import FINDINGS_SUBHEADINGS

RES = "docs/run_2026-11-10/results"
MASK, HELD = "<11", "withheld"
CAPS = ["cap_40", "cap_80", "cap_160", "cap_320", "no_cap"]


def small(v):
    return isinstance(v, (int, float)) and not pd.isna(v) and 1 <= v <= 10


def num(v):
    if pd.isna(v):
        return None
    return int(v) if float(v).is_integer() else round(float(v), 2)


def suppress(table, total="All"):
    """table: {row: {col: count}} with an optional total row/column named `total`.
    Primary suppression of 1-10, then secondary suppression until no row or column that publishes its
    total has exactly one withheld cell."""
    t = {r: dict(c) for r, c in table.items()}
    hidden = {(r, c) for r in t for c in t[r] if small(t[r][c])}
    primary = set(hidden)
    rows = [r for r in t if r != total]
    cols = sorted({c for r in t for c in t[r] if c != total})
    changed = True
    while changed:
        changed = False
        for r in rows:                                   # along a row: the row total is t[r][total]
            if total in t[r]:
                h = [c for c in cols if (r, c) in hidden]
                if len(h) == 1 and (r, total) not in hidden:
                    rest = [c for c in cols if (r, c) not in hidden and c in t[r] and t[r][c] != 0]
                    if rest:
                        hidden.add((r, min(rest, key=lambda c: t[r][c])))
                    else:
                        hidden.add((r, total))
                    changed = True
        if total in t:                                   # down a column: the column total is t[total][c]
            for c in cols + [total]:
                h = [r for r in rows if (r, c) in hidden]
                if len(h) == 1 and (total, c) not in hidden and c in t[total]:
                    rest = [r for r in rows if (r, c) not in hidden and c in t[r] and t[r][c] != 0]
                    if rest:
                        hidden.add((min(rest, key=lambda r: t[r][c]), c))
                    else:
                        hidden.add((total, c))
                    changed = True
    out = {r: {c: (MASK if (r, c) in primary else HELD if (r, c) in hidden else num(v)) for c, v in cs.items()}
           for r, cs in t.items()}
    return out, len(primary), len(hidden) - len(primary)


def cap_sweep():
    df = pd.read_csv("diagnostics/liver_sentence_cap/cap_sweep_summary.csv")
    rows, masked, held = [], 0, 0
    key = lambda r: (r["item"], r["stratum"], r["metric"].rsplit(",", 1)[0])
    recs = df.to_dict("records")
    is_count = lambda r: r["metric"].rstrip().endswith(", n")
    hide = set()                                          # (item, stratum, stem, cap)
    for r in recs:
        if is_count(r):
            for c in CAPS:
                if small(r[c]) or small(r["denominator"] - r[c] if not pd.isna(r[c]) else None):
                    hide.add(key(r) + (c,))
    # kept and dropped sentence counts are complements of one total: withhold both together
    partner = {"sentences kept": "sentences dropped", "sentences dropped": "sentences kept"}
    for (item, stratum, stem, c) in list(hide):
        if stem in partner:
            hide.add((item, stratum, partner[stem], c))
    # strata that partition a published total (cells A-D, note types, sections): if exactly one member
    # is hidden while the total is shown, hide the smallest other non-zero member as well
    groups = [lambda s: s in "ABCD", lambda s: s.startswith("note type:"), lambda s: s.startswith("section:")]
    order = ["cap_160", "no_cap", "cap_80", "cap_40", "cap_320"]       # the study's cap is published first
    changed = True
    while changed:
        changed = False
        # the caps are nested, so the difference between two published counts in one row is itself a
        # count; withhold a value that sits 1-10 away from one already published in that row
        for r in recs:
            if not is_count(r):
                continue
            shown = []
            for c in order:
                if key(r) + (c,) in hide or pd.isna(r[c]):
                    continue
                if any(small(abs(r[c] - v)) for v in shown):
                    hide.add(key(r) + (c,)); changed = True
                else:
                    shown.append(r[c])
        for stem in {r["metric"] for r in recs if is_count(r)}:
            same = [r for r in recs if r["metric"] == stem]
            total = next((r for r in same if r["stratum"] == "overall"), None)
            for in_group in groups:
                members = [r for r in same if in_group(r["stratum"])]
                for c in CAPS:
                    hid = [r for r in members if key(r) + (c,) in hide]
                    if len(hid) != 1 or total is None or key(total) + (c,) in hide:
                        continue
                    rest = [r for r in members if key(r) + (c,) not in hide and not pd.isna(r[c]) and r[c] != 0]
                    target = min(rest, key=lambda r: r[c]) if rest else total
                    hide.add(key(target) + (c,))
                    changed = True
    # a percentage is hidden with its count: same item, stratum and stem
    for r in recs:
        o = {"item": r["item"], "metric": r["metric"], "stratum": r["stratum"], "denominator": num(r["denominator"])}
        for c in CAPS:
            if key(r) + (c,) in hide:
                if is_count(r) and small(r[c]):
                    o[c] = MASK; masked += 1
                else:
                    o[c] = HELD; held += 1
            else:
                o[c] = num(r[c])
        rows.append(o)
    return {"source": "diagnostics/liver_sentence_cap/cap_sweep_summary.csv (git-ignored)",
            "written_by": "scripts/run1110_diagnostics_json.py", "cells_masked": masked, "cells_withheld": held,
            "caps": CAPS, "rows": rows}


def unclear_audit():
    df = pd.read_csv("diagnostics/llm_unclear_audit/unclear_audit_summary.csv")
    tables, masked, held = {}, 0, 0
    for name, g in df.groupby("table", sort=False):
        t = {}
        for r in g.to_dict("records"):
            t.setdefault(str(r["row"]), {})[str(r["column"])] = r["value"]
        counts = {r: {c: v for c, v in cs.items() if not c.endswith("%")} for r, cs in t.items()}
        out, m, h = suppress(counts)
        masked += m; held += h
        for r, cs in t.items():
            for c, v in cs.items():
                if c.endswith("%"):
                    base = c[:-1].strip()
                    shown = isinstance(out[r].get(base), (int, float)) and isinstance(out[r].get("All"), (int, float))
                    comp_small = shown and small(out[r]["All"] - out[r][base])
                    out[r][c] = num(v) if shown and not comp_small else HELD
        tables[name] = out
    return {"source": "diagnostics/llm_unclear_audit/unclear_audit_summary.csv (git-ignored)",
            "written_by": "scripts/run1110_diagnostics_json.py", "cells_masked": masked, "cells_withheld": held,
            "tables": tables}


def table_b():
    df = pd.read_csv("diagnostics/section_rule_v2/tableB_continuing_headings.csv")
    rows, masked, not_listed = [], 0, 0
    for r in df.to_dict("records"):
        label = str(r["whitelist_heading"])
        if label not in FINDINGS_SUBHEADINGS:
            label, not_listed = "(not an entry of FINDINGS_SUBHEADINGS; label withheld)", not_listed + 1
        o = {"subheading": label, "note_type": r["note_type"]}
        for c in ("times_continued_block", "kept_sentences_beneath"):
            if small(r[c]):
                o[c] = MASK; masked += 1
            else:
                o[c] = num(r[c])
        rows.append(o)
    return {"source": "diagnostics/section_rule_v2/tableB_continuing_headings.csv (git-ignored)",
            "written_by": "scripts/run1110_diagnostics_json.py", "cells_masked": masked,
            "labels_withheld": not_listed, "rows": rows}


def study_headers():
    df = pd.read_csv("diagnostics/section_rule_v2/step5_study_headers.csv")
    count_cols = ["closes", "kept_sentences_now_other", "closes_followed_by_findings", "distinct_study_headings"]
    rows, masked = [], 0
    for r in df.to_dict("records"):
        o = {"note_type": r["note_type"]}
        hide_pct = False
        for c in count_cols:
            if small(r[c]):
                o[c] = MASK; masked += 1; hide_pct = hide_pct or c == "closes_followed_by_findings"
            else:
                o[c] = num(r[c])
        o["pct_followed"] = HELD if hide_pct else num(r["pct_followed"])
        o["median_selected_sentences_between"] = num(r["median_selected_sentences_between"])
        rows.append(o)
    return {"source": "diagnostics/section_rule_v2/step5_study_headers.csv (git-ignored)",
            "written_by": "scripts/run1110_diagnostics_json.py", "cells_masked": masked, "rows": rows}


def main():
    for name, fn in (("diag_cap_sweep", cap_sweep), ("diag_unclear_audit", unclear_audit),
                     ("diag_section_tableB", table_b), ("diag_section_study_headers", study_headers)):
        out = fn()
        json.dump(out, open(f"{RES}/{name}.json", "w"), indent=1)
        print(name, {k: v for k, v in out.items() if k.startswith(("cells", "labels"))})


if __name__ == "__main__":
    main()
