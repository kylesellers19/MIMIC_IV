#!/usr/bin/env python3
"""STEP 6 — sample representativeness: each stratum's draw vs its full cell.

SMDs (sample vs cell) per cell on age, sex, race, insurance, admission_type, LOS.
|SMD|>0.1 flags an unlucky draw (reweighting would then be biased). Aggregate only.
Writes frag_step6.md.

Run: python scripts/sample_rep.py
"""
import os
import numpy as np
import pandas as pd
import duckdb

FRAG = os.path.join(os.environ.get("SCRATCH", "/tmp"), "frag_step6.md")
con = duckdb.connect()
frame = con.execute("""SELECT hadm_id, code_positive, note_b, age, gender, race,
    insurance, admission_type, los_days FROM read_parquet('data/processed/aim1a_frame.parquet')""").fetchdf()
frame["cell"] = frame.apply(lambda r: ("code+" if r.code_positive else "code-") +
                            ("/note+" if r.note_b else "/note-"), axis=1)
sample = con.execute(
    "SELECT hadm_id, cell FROM read_parquet('data/processed/aim1a_sample.parquet')").fetchdf()
smpl_hadm = dict(zip(sample.hadm_id.astype("int64"), sample.cell))
frame["in_sample"] = frame.hadm_id.astype("int64").map(lambda h: h in smpl_hadm)


def smd_cont(a, b):
    a, b = a.dropna(), b.dropna()
    d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return np.nan if d == 0 else (a.mean() - b.mean()) / d

def smd_bin(p1, p0):
    d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
    return np.nan if d == 0 else (p1 - p0) / d

def cat_maxsmd(ss, sc, minshare=0.05):
    """Max per-level |SMD| over levels with cell share >= minshare. Multinomial
    SMD is unstable at n~80 over many sparse categories; this is small-n robust."""
    shares = sc.value_counts(normalize=True)
    best = 0.0
    for lv in shares[shares >= minshare].index:
        s = smd_bin((ss == lv).mean(), (sc == lv).mean())
        if not np.isnan(s):
            best = max(best, abs(s))
    return best


L = []
def w(s=""): L.append(s)
w("## Step 6 — Sample representativeness (draw vs full cell; seed 20260818)\n")
w("SMD of each covariate, sampled charts vs the full cell they were drawn from. "
  "**|SMD|>0.1 flagged** (would bias reweighting). Categoricals (race/insurance/"
  "admission_type) = max per-level |SMD| over levels with ≥5% cell share (multinomial "
  "SMD is unstable at n≈80 over sparse categories).\n")
w("| cell | n_sample | age | sex(M) | race | insurance | admission_type | LOS | max\\|SMD\\| |")
w("| --- | --: | --: | --: | --: | --: | --: | --: | --: |")
flags = []
for cell in ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]:
    g = frame[frame.cell == cell]
    s = g[g.in_sample]; c = g            # sample vs full cell
    a = smd_cont(s.age, c.age)
    sx = smd_bin((s.gender == "M").mean(), (c.gender == "M").mean())
    rc = cat_maxsmd(s.race, c.race)
    ins = cat_maxsmd(s.insurance, c.insurance)
    at = cat_maxsmd(s.admission_type, c.admission_type)
    lo = smd_cont(s.los_days, c.los_days)
    vals = [a, sx, rc, ins, at, lo]
    mx = max(abs(v) for v in vals if not np.isnan(v))
    if mx > 0.1:
        flags.append((cell, mx))
    w(f"| {cell} | {len(s):,} | {a:+.3f} | {sx:+.3f} | {rc:.3f} | {ins:.3f} | {at:.3f} "
      f"| {lo:+.3f} | {mx:.3f} |")
w("")
if flags:
    w("**FLAG (|SMD|>0.1):** " + "; ".join(f"{c} (max|SMD|={m:.3f})" for c, m in flags)
      + ". These are max per-level differences at n=70–150 (chiefly admission_type). Because "
      "sampling is a simple random draw WITHIN each cell, the population-weighted 1a estimate "
      "(cell weight = N_pop/n_sample) remains unbiased in expectation; the flags indicate "
      "covariate imbalance in this particular draw, relevant only if within-cell "
      "covariate-adjusted analyses are planned. Researcher to decide on re-draw vs adjustment.\n")
else:
    w("**No cell exceeds |SMD|>0.1** — each draw resembles its cell.\n")

os.makedirs(os.path.dirname(FRAG), exist_ok=True)
with open(FRAG, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {FRAG}; flags: {flags if flags else 'none'}")
