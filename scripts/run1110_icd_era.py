#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 — coding by period (amendment n, S21). Exploratory.

Among note-positive admissions (definition b): B/(A+B), the share with no MASLD code, by anchor_year_group
and by the ICD version of the admission's diagnoses, each with the primary code set and with ICD-9 571.9
removed (S7). Subject-cluster bootstrap, 500 replicates, seed 20260919, 95% percentile intervals.
anchor_year_group is a three-year window assigned per patient, not the admission's calendar year.
Writes docs/run_2026-11-10/results/icd_era.json. Counts and shares only.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.getcwd())
from scripts.run1110_common import RES, FLOOR, Boot, load_frame, protect_partition, share


def guard(primary, sens):
    """The two counts differ by the admissions coded through 571.9 alone. Where that difference is 1-10 the
    sensitivity count is withheld (its share and interval stay), so the difference cannot be recovered."""
    a, b = primary.get("x"), sens.get("x")
    if isinstance(a, int) and isinstance(b, int) and 0 < abs(a - b) < FLOOR:
        sens["x"] = "withheld"
        sens["why_x_withheld"] = "differs from the primary count by fewer than 11"


def table(df, var, boot):
    nt = df.note_b.astype(bool).to_numpy()
    cp, cp2 = df.code_positive.astype(bool).to_numpy(), df.code_pos_no5719.astype(bool).to_numpy()
    levels = sorted(df[var].astype(str).unique())
    npos = {lv: int((nt & (df[var].astype(str) == lv).to_numpy()).sum()) for lv in levels}
    shown = protect_partition(npos)
    rows = []
    for lv in levels:
        g = (df[var].astype(str) == lv).to_numpy()
        den = nt & g
        n = npos[lv]
        r = {"stratum": lv, "note_positive_admissions": shown[lv]}
        approx = isinstance(shown[lv], str) and shown[lv].startswith("~")
        for key, code in (("primary_code_set", cp), ("with_571_9_removed", cp2)):
            b = den & ~code
            sh = share(int(b.sum()), n, boot.ratio_ci(b, den) if n >= FLOOR else None)
            if approx and sh.get("reported"):          # counts rounded with the denominator; the share and interval stay
                sh["n"], sh["x"] = shown[lv], f"~{int(round(sh['x'], -2)):,}"
            r[key] = sh
        guard(r["primary_code_set"], r["with_571_9_removed"])
        rows.append(r)
    return rows


def main():
    df = load_frame(with_5719=True)
    boot = Boot(df.subject_id)
    nt = df.note_b.astype(bool).to_numpy()
    out = {"script": "scripts/run1110_icd_era.py", "amendment": "n (S21)", "exploratory": True,
           "measure": "among note-positive admissions, the share with no MASLD code: B/(A+B)",
           "bootstrap": {"replicates": int(boot.W.shape[0]), "seed": 20260919, "cluster": "subject", "interval": "95% percentile"},
           "note_positive_admissions": int(nt.sum()),
           "overall": {"primary_code_set": share(int((nt & ~df.code_positive.astype(bool).to_numpy()).sum()), int(nt.sum()),
                                                 boot.ratio_ci(nt & ~df.code_positive.astype(bool).to_numpy(), nt)),
                       "with_571_9_removed": share(int((nt & ~df.code_pos_no5719.astype(bool).to_numpy()).sum()), int(nt.sum()),
                                                   boot.ratio_ci(nt & ~df.code_pos_no5719.astype(bool).to_numpy(), nt))},
           "by_anchor_year_group": table(df, "anchor_year_group", boot),
           "by_icd_version": table(df, "icd_era", boot),
           "limitation": "anchor_year_group is a three-year window assigned per patient"}
    guard(out["overall"]["primary_code_set"], out["overall"]["with_571_9_removed"])
    json.dump(out, open(f"{RES}/icd_era.json", "w"), indent=1)
    for k in ("by_anchor_year_group", "by_icd_version"):
        for r in out[k]:
            print(k, r["stratum"], r["note_positive_admissions"], r["primary_code_set"].get("pct"), r["primary_code_set"].get("ci95"),
                  r["with_571_9_removed"].get("pct"), r["with_571_9_removed"].get("ci95"))


if __name__ == "__main__":
    main()
