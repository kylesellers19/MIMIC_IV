#!/usr/bin/env python3
"""Reviewer assignment for the 400-chart sample (seed SEED_REVIEWER_ASSIGN = 20260921).

The 100 double-review charts go to both reviewers; the other 300 are split 150/150 by a stratified split
within each cell (odd cells alternate which reviewer takes the extra chart, so the totals are exactly equal);
each reviewer's presentation order is an independent seeded shuffle of their 250 IDs.

Writes (untracked, beside the master key):
  data/processed/adjudication/reviewer_assignment.parquet   (review_id, reviewer [1/2], order)
  data/processed/adjudication/form_reviewer1.xlsx / form_reviewer2.xlsx   (250 sample rows each, in that
      reviewer's order; both carry the training sheet T001–T020)
and (tracked, aggregates only):
  docs/run_2026-09-19/results/reviewer_assignment.json, docs/adjudication/reviewer_assignment.md

Revisable: rerun with --n-reviewers when the number of reviewers changes (only 2 is implemented; the script
refuses other values so the design is re-derived deliberately rather than silently).
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.masld_config import SEED_REVIEWER_ASSIGN, TRAINING_KEY
from scripts.make_adjudication_template import build_form, load_ids, verify_commit_safe

MASTER_KEY = "data/processed/aim1a_sample.parquet"
OUT_DIR = "data/processed/adjudication"
OUT_JSON = "docs/run_2026-09-19/results/reviewer_assignment.json"
OUT_MD = "docs/adjudication/reviewer_assignment.md"
CELLS = ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]
LETTER = {"code+/note+": "A", "code-/note+": "B", "code+/note-": "C", "code-/note-": "D"}


def small(v):
    return "<11" if 0 < v < 11 else int(v)


def assign(key, seed=SEED_REVIEWER_ASSIGN):
    rng = np.random.default_rng(seed)
    rows = []
    for rid in key.loc[key.double_review, "review_id"]:
        rows.append((rid, 1))
        rows.append((rid, 2))
    extra_to = 1
    for c in CELLS:
        ids = key.loc[(~key.double_review) & (key.cell == c), "review_id"].to_numpy()
        ids = ids[rng.permutation(len(ids))]
        n1 = len(ids) // 2
        if len(ids) % 2 == 1:
            n1 += (extra_to == 1)
            extra_to = 3 - extra_to
        rows += [(r, 1) for r in ids[:n1]] + [(r, 2) for r in ids[n1:]]
    a = pd.DataFrame(rows, columns=["review_id", "reviewer"])
    parts = []
    for rv in (1, 2):
        sub = a[a.reviewer == rv].copy()
        sub = sub.iloc[rng.permutation(len(sub))].reset_index(drop=True)
        sub["order"] = np.arange(1, len(sub) + 1)
        parts.append(sub)
    a = pd.concat(parts, ignore_index=True)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-reviewers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=SEED_REVIEWER_ASSIGN)
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args()
    if a.n_reviewers != 2:
        raise SystemExit("Only 2 reviewers are implemented; revise assign() for a different design (Tier 3).")
    key = pd.read_parquet(MASTER_KEY)[["review_id", "cell", "double_review"]]
    asg = assign(key, a.seed)
    m = asg.merge(key, on="review_id")
    # checks
    assert (m.groupby("reviewer").size() == 250).all()
    assert m[m.double_review].groupby("review_id").size().eq(2).all() and m.double_review.sum() == 200
    assert m[~m.double_review].groupby("review_id").size().eq(1).all()
    assert (m[~m.double_review].groupby("reviewer").size() == 150).all()
    for c in CELLS:
        s = m[(~m.double_review) & (m.cell == c)].groupby("reviewer").size()
        assert abs(int(s.get(1, 0)) - int(s.get(2, 0))) <= 1
    assert m.groupby("reviewer")["order"].apply(lambda s: sorted(s) == list(range(1, 251))).all()
    # cell must not be predictable from presentation order (rank correlation ~ 0): report it
    order_check = {}
    for rv in (1, 2):
        sub = m[m.reviewer == rv]
        order_check[f"reviewer{rv}_spearman_order_vs_cell_index"] = round(float(pd.Series(sub.order.values).corr(pd.Series([CELLS.index(c) for c in sub.cell]), method="spearman")), 3)
    os.makedirs(a.out_dir, exist_ok=True)
    asg[["review_id", "reviewer", "order"]].to_parquet(f"{a.out_dir}/reviewer_assignment.parquet", index=False)
    _, training_ids = load_ids()
    forms = {}
    for rv in (1, 2):
        ids = asg[asg.reviewer == rv].sort_values("order")["review_id"].tolist()
        p = build_form(ids, training_ids, f"{a.out_dir}/form_reviewer{rv}.xlsx")
        verify_commit_safe(p)
        forms[rv] = {"path": p, "sample_rows": len(ids), "training_rows": len(training_ids)}
    per = {}
    for rv in (1, 2):
        sub = m[m.reviewer == rv]
        per[f"reviewer{rv}"] = {"total": int(len(sub)), "by_cell": {LETTER[c]: int((sub.cell == c).sum()) for c in CELLS},
                               "training_charts": len(training_ids)}
    res = {"script": "scripts/assign_reviewers.py", "seed": a.seed, "n_reviewers": 2,
           "double_review_total": int(key.double_review.sum()), "single_review_total": int((~key.double_review).sum()),
           "per_reviewer": per, "shared_charts_between_reviewers": int(key.double_review.sum()),
           "adjudications_total": int(len(m)), "order_independence": order_check,
           "outputs_untracked": [f"{a.out_dir}/reviewer_assignment.parquet", f"{a.out_dir}/form_reviewer1.xlsx", f"{a.out_dir}/form_reviewer2.xlsx"]}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(res, f, indent=1)
    write_md(res)
    print(f"reviewer1 {per['reviewer1']['total']} / reviewer2 {per['reviewer2']['total']}; shared {res['shared_charts_between_reviewers']}; "
          f"adjudications {res['adjudications_total']}; forms written to {a.out_dir}")


def write_md(r):
    L = ["# Reviewer assignment — 400-chart sample", "",
         f"Produced by `{r['script']}` (seed {r['seed']}); numbers from `docs/run_2026-09-19/results/reviewer_assignment.json`.", "",
         f"Design: {r['n_reviewers']} reviewers. {r['double_review_total']} charts are reviewed independently by both reviewers; the remaining "
         f"{r['single_review_total']} are split evenly by a stratified split within each sampling cell. Each reviewer's presentation order is an "
         "independent seeded shuffle, so neither the order nor the ID reveals the cell or whether a chart is double-reviewed. "
         f"Total adjudications: {r['adjudications_total']} (plus the 20-chart training round, done by both reviewers).", "",
         "| reviewer | charts | code+/note+ (A) | code−/note+ (B) | code+/note− (C) | code−/note− (D) | training charts |",
         "| --- | --: | --: | --: | --: | --: | --: |"]
    for rv in ("reviewer1", "reviewer2"):
        p = r["per_reviewer"][rv]
        L.append(f"| {rv} | {p['total']} | {p['by_cell']['A']} | {p['by_cell']['B']} | {p['by_cell']['C']} | {p['by_cell']['D']} | {p['training_charts']} |")
    L += ["",
          "Per-cell counts include each reviewer's share of the double-reviewed charts; which IDs those are is held only in the untracked master key "
          "and is not shown to reviewers or recorded here.", "",
          f"Spearman correlation between presentation order and cell index: reviewer 1 {r['order_independence']['reviewer1_spearman_order_vs_cell_index']}, "
          f"reviewer 2 {r['order_independence']['reviewer2_spearman_order_vs_cell_index']} (near zero, as expected from an independent shuffle).", "",
          "Outputs (untracked, credentialed, beside the master key): `data/processed/adjudication/reviewer_assignment.parquet` (review_id, reviewer, order) and the "
          "per-reviewer blank forms `form_reviewer1.xlsx` / `form_reviewer2.xlsx` (250 sample rows each in that reviewer's order, plus the training sheet).", "",
          "**Revisable.** If the number of reviewers changes, the assignment is re-derived by rerunning the script with a revised split rule under the same seed; "
          "nothing downstream depends on this assignment until adjudication begins."]
    with open(OUT_MD, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
