#!/usr/bin/env python3
"""run_2026-09-19 Phase 2 — reviewer-training draw (20 charts) and subject-level splits with a gold holdout.

Reads stored derivatives only. Writes:
  data/processed/aim1a_training_key.parquet   (untracked; beside the master key)
  data/processed/splits_v1.parquet            (untracked)
  docs/adjudication/training_draw.md, docs/aim1b_splits.md, docs/run_2026-09-19/results/phase2_splits.json  (aggregates)
"""
import json, os, sys
import numpy as np, pandas as pd, duckdb
sys.path.insert(0, os.getcwd())
from scripts.masld_config import CLEAN_POP

SEED_TRAINING_DRAW = 20260919
SEED_SPLIT = 20260920
FRAME = "data/processed/aim1a_frame.parquet"
SAMPLE = "data/processed/aim1a_sample.parquet"
TRAIN_KEY = "data/processed/aim1a_training_key.parquet"
SPLITS = "data/processed/splits_v1.parquet"
ALLOC = {"code-/note+": 8, "code+/note+": 4, "code+/note-": 3, "code-/note-": 5}

con = duckdb.connect()
df = con.execute(f"""SELECT f.hadm_id, f.subject_id, f.code_positive, f.note_b,
   CASE WHEN f.code_positive AND f.note_b THEN 'code+/note+' WHEN NOT f.code_positive AND f.note_b THEN 'code-/note+'
        WHEN f.code_positive AND NOT f.note_b THEN 'code+/note-' ELSE 'code-/note-' END AS cell
   FROM read_parquet('{FRAME}') f""").fetchdf()
sample = con.execute(f"SELECT hadm_id, subject_id, cell FROM read_parquet('{SAMPLE}')").fetchdf()
sample_subj = set(sample.subject_id.astype("int64"))

# ---- 2.1 training draw ----
rng = np.random.default_rng(SEED_TRAINING_DRAW)
pool = df[~df.subject_id.isin(sample_subj)]
parts = []
for cell, n in ALLOC.items():
    p = pool[pool.cell == cell]
    idx = rng.choice(p.index.values, size=n, replace=False)
    parts.append(df.loc[idx, ["hadm_id", "subject_id", "cell"]])
tr = pd.concat(parts, ignore_index=True)
tr = tr.iloc[rng.permutation(len(tr))].reset_index(drop=True)
tr["training_id"] = [f"T{i+1:03d}" for i in range(len(tr))]
tr = tr[["training_id", "hadm_id", "subject_id", "cell"]]
assert len(tr) == 20 and tr.hadm_id.is_unique
assert not set(tr.subject_id).intersection(sample_subj)
con.register("tr", tr); con.execute(f"COPY tr TO '{TRAIN_KEY}' (FORMAT parquet)")
n_train_subj = int(tr.subject_id.nunique())

# ---- 2.2 splits ----
gold_subj = sample_subj | set(tr.subject_id.astype("int64"))
subj = df.groupby("subject_id").agg(n_adm=("hadm_id", "size"), any_pos=("note_b", "max")).reset_index()
rest = subj[~subj.subject_id.isin(gold_subj)].copy()
rng2 = np.random.default_rng(SEED_SPLIT)
perm = rng2.permutation(len(rest))
rest = rest.iloc[perm].reset_index(drop=True)
n_test = int(round(0.20 * len(rest)))
rest["partition"] = "DEV"
rest.loc[:n_test - 1, "partition"] = "TEST"
dev = rest[rest.partition == "DEV"].copy()
dev["fold"] = (np.arange(len(dev)) % 5).astype(int)   # dev already randomly permuted
rest = rest.merge(dev[["subject_id", "fold"]], on="subject_id", how="left")
gold = subj[subj.subject_id.isin(gold_subj)][["subject_id"]].copy(); gold["partition"] = "GOLD_HOLDOUT"; gold["fold"] = np.nan
sp = pd.concat([rest[["subject_id", "partition", "fold"]], gold], ignore_index=True)
out = df[["hadm_id", "subject_id", "note_b", "code_positive", "cell"]].merge(sp, on="subject_id", how="left")
assert out.partition.notna().all() and len(out) == len(df)
out["fold"] = out["fold"].astype("Int64")
# overlap assertions (by subject)
P = {p: set(out[out.partition == p].subject_id) for p in ["GOLD_HOLDOUT", "TEST", "DEV"]}
assert not (P["GOLD_HOLDOUT"] & P["TEST"]) and not (P["GOLD_HOLDOUT"] & P["DEV"]) and not (P["TEST"] & P["DEV"])
F = {k: set(out[(out.partition == "DEV") & (out.fold == k)].subject_id) for k in range(5)}
for i in range(5):
    for j in range(i + 1, 5):
        assert not (F[i] & F[j])
assert sample_subj <= P["GOLD_HOLDOUT"] and set(tr.subject_id) <= P["GOLD_HOLDOUT"]
con.register("o", out[["hadm_id", "subject_id", "partition", "fold"]]); con.execute(f"COPY o TO '{SPLITS}' (FORMAT parquet)")

def summ(g):
    return {"admissions": int(len(g)), "subjects": int(g.subject_id.nunique()),
            "note_positive": int(g.note_b.sum()), "silver_prevalence_pct": round(100 * g.note_b.mean(), 2),
            "code_positive": int(g.code_positive.sum())}
res = {"seed_training_draw": SEED_TRAINING_DRAW, "seed_split": SEED_SPLIT,
       "training_alloc": ALLOC, "training_n": 20, "training_subjects": n_train_subj,
       "gold_subjects": len(gold_subj), "sample_subjects": len(sample_subj),
       "partitions": {p: summ(out[out.partition == p]) for p in ["GOLD_HOLDOUT", "TEST", "DEV"]},
       "dev_folds": {str(k): summ(out[(out.partition == "DEV") & (out.fold == k)]) for k in range(5)},
       "gold_holdout_cells": {c: int(n) for c, n in out[out.partition == "GOLD_HOLDOUT"].cell.value_counts().items()},
       "overlap_checks": "all zero (asserted)"}
os.makedirs("docs/run_2026-09-19/results", exist_ok=True)
json.dump(res, open("docs/run_2026-09-19/results/phase2_splits.json", "w"), indent=1)

with open("docs/adjudication/training_draw.md", "w") as f:
    f.write(f"""# Reviewer-training draw (20 charts) — run_2026-09-19

Produced by `scripts/run0919_phase2_splits.py`; numbers from `docs/run_2026-09-19/results/phase2_splits.json`.

**Purpose.** Before formal review, both reviewers adjudicate the same 20 charts (criteria §9) to calibrate against each other and to revise the criteria once. These charts are drawn **outside** the 400-chart sample: no subject with any admission in the 400-chart sample is eligible, so nothing learned here can touch the sample.

- Primary definition (b): v1.1.0, inpatient + outpatient radiology −365/+30 days.
- Allocation in proportion to the main sample: code−/note+ 8 · code+/note+ 4 · code+/note− 3 · code−/note− 5 (total 20; {n_train_subj} distinct subjects).
- Seed {SEED_TRAINING_DRAW}. Blinded IDs T001–T020 assigned after a seeded shuffle, so neither ID nor order encodes cell.
- Key stored beside the master key at `data/processed/aim1a_training_key.parquet` (untracked, credentialed).
- The allocation is revisable; nothing is estimated from this set.
""")
with open("docs/aim1b_splits.md", "w") as f:
    L = ["# Aim 1b — subject-level splits with a gold holdout (splits_v1)\n",
         "Produced by `scripts/run0919_phase2_splits.py`; numbers from `docs/run_2026-09-19/results/phase2_splits.json`. "
         f"Seed {SEED_SPLIT}. File `data/processed/splits_v1.parquet` (untracked).\n",
         "**Rule.** GOLD_SUBJECTS = every subject with an admission in the 400-chart sample or the 20-chart training set. "
         "All their admissions form GOLD_HOLDOUT, which is never used for fitting, tuning, early stopping, threshold selection, "
         "recalibration, vocabulary building or dimensionality reduction. Of the remaining subjects, 20% form TEST (touched once per model) "
         "and 80% DEV, split into 5 subject-level folds. Partitioning is by subject, never by admission.\n",
         "Silver label = note-positive under the primary definition (b). **Silver label — known error; not adjudicated truth; final performance requires the gold standard.**\n",
         "| partition | admissions | subjects | note-positive | silver prevalence % | code-positive |", "| --- | --: | --: | --: | --: | --: |"]
    for p, s in res["partitions"].items():
        L.append(f"| {p} | {s['admissions']:,} | {s['subjects']:,} | {s['note_positive']:,} | {s['silver_prevalence_pct']} | {s['code_positive']:,} |")
    L += ["", "| DEV fold | admissions | subjects | note-positive | silver prevalence % |", "| --- | --: | --: | --: | --: |"]
    for k, s in res["dev_folds"].items():
        L.append(f"| {k} | {s['admissions']:,} | {s['subjects']:,} | {s['note_positive']:,} | {s['silver_prevalence_pct']} |")
    L += ["", "GOLD_HOLDOUT admissions by cell (definition b): " + ", ".join(f"{c} {n:,}" for c, n in res["gold_holdout_cells"].items()) + ".",
          "", "Checks: zero subject overlap between partitions and between folds (asserted in the script); every sampled and training subject is in GOLD_HOLDOUT."]
    f.write("\n".join(L) + "\n")
print(json.dumps({k: res[k] for k in ["gold_subjects", "partitions"]}, indent=1))
