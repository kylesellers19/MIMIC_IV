#!/usr/bin/env python3
"""Small-cell suppression for counts published in this public repository (CELL_FLOOR = 11).

A count from 1 to 10 is published as "<11". Where a published total would give such a count back by
subtraction, a second cell is withheld as well ("withheld"), chosen as the smallest cell of at least 11
in the same row or column, and the step is repeated until every row and column with a hidden cell hides
at least two cells summing to 11 or more. Shares computed from a hidden cell are withheld too.

aim1c_public() applies this to the Aim 1c level 1 results (rows: strata; columns: the code x note cells A-D;
row totals are published as the stratum n, column totals as the overall 2x2) and to the 571.9-removed
recovery share wherever the published shares and counts would pin down a shift of 1 to 10 admissions.
"""
import copy
import math

FLOOR = 11
SMALL, WITHHELD = "<11", "withheld"


def is_small(v):
    return isinstance(v, int) and not isinstance(v, bool) and 0 < v < FLOOR


def suppress_table(rows, cols, key="stratum", row_totals=True, col_totals=True):
    """rows: dicts holding integer counts under cols. Returns {row key: {col: 'small' | 'withheld'}}."""
    mask = {r[key]: {c: "small" for c in cols if is_small(r[c])} for r in rows}

    def pick(cands):
        return min(cands, key=lambda x: x[0])[1] if cands else None

    changed = True
    while changed:
        changed = False
        if row_totals:
            for r in rows:
                m = mask[r[key]]
                if m and (len(m) == 1 or sum(r[c] for c in m) < FLOOR):
                    c = pick([(r[c], c) for c in cols if c not in m and r[c] >= FLOOR])
                    rest = [c for c in cols if c not in m and r[c] > 0]
                    for c in ([c] if c else rest):
                        m[c] = "withheld"
                        changed = True
        if col_totals:
            for c in cols:
                hid = [r for r in rows if c in mask[r[key]]]
                if hid and (len(hid) == 1 or sum(r[c] for r in hid) < FLOOR):
                    r = pick([(r[c], i) for i, r in enumerate(rows) if c not in mask[r[key]] and r[c] >= FLOOR])
                    if r is not None:
                        mask[rows[r][key]][c] = "withheld"
                        changed = True
    return mask


def shown(v, how):
    """The published form of a count: the integer, '<11' or 'withheld'."""
    return v if how is None else (SMALL if how == "small" else WITHHELD)


def cell(v):
    """Markdown cell for a published count."""
    return v if isinstance(v, str) else f"{v:,}"


def pins_small_shift(share, share_alt, n):
    """True when two shares over the same n (each rounded to 0.1 points) fix the count that moved
    between them to a value from 1 to 10."""
    if share is None or share_alt is None:
        return False
    implied, slack = (share_alt - share) / 100 * n, 0.1 / 100 * n
    lo, hi = math.ceil(implied - slack - 1e-9), math.floor(implied + slack + 1e-9)
    return lo >= 1 and hi < FLOOR


REC_FIELDS = ("recovery_share_pct", "rec_ci", "rec_ci_width", "rec_claim_supported", "smd_coding_rate_vs_rest",
              "recovery_share_no5719_pct", "rec_no5719_ci")
COR_FIELDS = ("corroboration_share_pct", "cor_ci", "cor_ci_width", "cor_claim_supported")
NO5719_FIELDS = ("recovery_share_no5719_pct", "rec_no5719_ci")


def aim1c_public(res):
    """A copy of the Aim 1c level 1 results that is safe to publish, plus {variable: mask}."""
    out, masks = copy.deepcopy(res), {}
    for var, rows in out["strata"].items():
        m = masks[var] = suppress_table(rows, ("A", "B", "C", "D"))
        for r in rows:
            how = m[r["stratum"]]
            withheld = []
            if {"A", "B"} & set(how):
                withheld += REC_FIELDS
            if {"A", "C"} & set(how):
                withheld += COR_FIELDS
            if not withheld and pins_small_shift(r.get("recovery_share_pct"), r.get("recovery_share_no5719_pct"), r["A"] + r["B"]):
                withheld += NO5719_FIELDS
            for f in withheld:
                if r.get(f) is not None:
                    r[f] = None
            if withheld:
                r["withheld"] = sorted(set(withheld))
            for c in ("A", "B", "C", "D"):
                r[c] = shown(r[c], how.get(c))
            if is_small(r["mech"]["n"]):
                r["mech"]["n"] = SMALL
    out["disclosure"] = ("Counts from 1 to 10 are published as '<11'; where a row or column total would give one back by "
                         "subtraction a second cell is 'withheld'; shares computed from a hidden cell are null and listed "
                         "under 'withheld'. Written by scripts/public_counts.py.")
    return out, masks
