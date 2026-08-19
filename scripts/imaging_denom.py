#!/usr/bin/env python3
"""STEP 3 — imaging denominator: liver-inclusive studies as an observation window.

Classifies radiology by structured exam_name (radiology_detail): liver-inclusive =
cross-sectional/US modality AND abdominal/liver region, excluding plain abdominal
films and non-liver organ studies. Reports the imaging-observed population, the
2x2 restricted to it, and whether being imaged differs by coding/race/insurance.
Aggregate only (exam names are generic metadata). Writes frag_step3.md.

Run: python scripts/imaging_denom.py
"""
import os
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import CLEAN_POP, LOCKED_POP

FRAG = os.path.join(os.environ.get("SCRATCH", "/tmp"), "frag_step3.md")
NOTE = "data/raw/note"
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

MOD = r"(\bCT\b|\bCTA\b|\bMR\b|\bMRI\b|\bUS\b|U\.S|ULTRASOUND|SONO)"
REGION = r"(ABD|LIVER|HEPAT|\bRUQ\b|BILIARY|GALLBLADDER)"

# note_id -> liver-inclusive (any exam_name qualifies)
exam = con.execute(f"""
  WITH e AS (SELECT note_id, upper(field_value) AS exam
             FROM read_csv_auto('{NOTE}/radiology_detail.csv.gz') WHERE field_name='exam_name')
  SELECT note_id,
         max(CASE WHEN regexp_matches(exam,'{MOD}') AND regexp_matches(exam,'{REGION}')
                  THEN 1 ELSE 0 END) AS liver_incl
  FROM e GROUP BY note_id
""").fetchdf()
li_notes = set(exam[exam.liver_incl == 1].note_id)

# verification: which exam_names were flagged liver-inclusive (top 25)
ver = con.execute(f"""
  WITH e AS (SELECT upper(field_value) AS exam
             FROM read_csv_auto('{NOTE}/radiology_detail.csv.gz') WHERE field_name='exam_name')
  SELECT exam, count(*) n FROM e
  WHERE regexp_matches(exam,'{MOD}') AND regexp_matches(exam,'{REGION}')
  GROUP BY exam ORDER BY n DESC LIMIT 25
""").fetchdf()

# radiology note -> subject/hadm/charttime (no text)
rad = con.execute(f"""
  SELECT note_id, subject_id, hadm_id, charttime
  FROM read_csv_auto('{NOTE}/radiology.csv.gz')
""").fetchdf()
rad["liver"] = rad.note_id.isin(li_notes)
li = rad[rad.liver]

# population
pop = con.execute(f"""
  SELECT c.hadm_id, c.subject_id, c.code_positive, c.race, c.insurance,
         c.age, c.gender, c.admission_type, c.los_days, l.admittime
  FROM read_parquet('{CLEAN_POP}') c
  JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)
""").fetchdf()
frame = con.execute("SELECT hadm_id, note_b FROM read_parquet('data/processed/aim1a_frame.parquet')").fetchdf()
pop = pop.merge(frame, on="hadm_id", how="left")
pop["admittime"] = pd.to_datetime(pop["admittime"])

locked_hadm = set(pop.hadm_id.astype("int64"))
locked_subj = set(pop.subject_id.astype("int64"))
# inpatient liver-inclusive (hadm-linked)
inp = set(li[li.hadm_id.notna()].hadm_id.astype("int64")) & locked_hadm
pop["img_inp"] = pop.hadm_id.isin(inp)
# outpatient liver-inclusive within 365/30
op = li[li.hadm_id.isna() & li.subject_id.isin(locked_subj)][["subject_id", "charttime"]].copy()
op["charttime"] = pd.to_datetime(op["charttime"])
m = pop[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
dt = (m.charttime - m.admittime).dt.total_seconds() / 86400.0
img_out = set(m[(dt >= -365) & (dt <= 30)].hadm_id.astype("int64"))
pop["img_out"] = pop.hadm_id.isin(img_out)
pop["img_any"] = pop.img_inp | pop.img_out
N = len(pop)

L = []
def w(s=""): L.append(s)
w("## Step 3 — Imaging denominator (liver-inclusive studies)\n")
w("Classification by structured `exam_name` (radiology_detail): liver-inclusive = "
  "cross-sectional/US modality AND abdominal/liver region; plain abdominal films and "
  "non-liver organ studies excluded.\n")
w("<details><summary>Exam names flagged liver-inclusive (top 25, verification)</summary>\n")
w("| exam_name | n |"); w("| --- | --: |")
for _, r in ver.iterrows():
    w(f"| {r.exam} | {r.n:,} |")
w("\n</details>\n")
w(f"- Admissions with ≥1 liver-inclusive study (inpatient): "
  f"**{int(pop.img_inp.sum()):,} ({100*pop.img_inp.mean():.1f}%)**")
w(f"- + within 365/30 outpatient window: **{int(pop.img_any.sum()):,} "
  f"({100*pop.img_any.mean():.1f}%)** (imaging-observed population)\n")

def smd_bin(p1, p0):
    d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
    return np.nan if d == 0 else (p1 - p0) / d
p1 = pop[pop.code_positive].img_any.mean(); p0 = pop[~pop.code_positive].img_any.mean()
w(f"**Is being imaged differential?** liver-inclusive imaging: code+ {100*p1:.1f}% vs "
  f"code− {100*p0:.1f}%, SMD={smd_bin(p1,p0):+.3f}. By race/insurance (imaging %):\n")
for grp in ["race", "insurance"]:
    r = (pop.groupby(grp).img_any.agg(["mean", "size"]))
    r = r[r["size"] >= 500].sort_values("mean", ascending=False)
    w(f"- **{grp}** range {100*r['mean'].min():.1f}%–{100*r['mean'].max():.1f}% "
      f"(max {r.index[0]} {100*r['mean'].iloc[0]:.1f}%, min {r.index[-1]} {100*r['mean'].iloc[-1]:.1f}%)")
w("")

# 2x2 restricted to imaging-observed population
w("### 2×2 restricted to imaging-observed population (primary b), n (% of imaged)\n")
sub = pop[pop.img_any]; ni = len(sub)
cp = sub.code_positive.astype(bool); nt = sub.note_b.astype(bool)
w("| cell | n | % of imaged |"); w("| --- | --: | --: |")
for lab, mask in [("code+/note+", cp & nt), ("code−/note+", ~cp & nt),
                  ("code+/note−", cp & ~nt), ("code−/note−", ~cp & ~nt)]:
    w(f"| {lab} | {int(mask.sum()):,} | {100*mask.mean():.2f}% |")
w(f"\nImaging-observed population N = {ni:,} of {N:,} admissions "
  f"({100*ni/N:.1f}%). This is a pre-specified SECONDARY analysis population "
  f"(note-negative outside it may mean non-observation, not absence).\n")

os.makedirs(os.path.dirname(FRAG), exist_ok=True)
with open(FRAG, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {FRAG}")
print(f"imaging-observed: inp {100*pop.img_inp.mean():.1f}%  any {100*pop.img_any.mean():.1f}%  "
      f"code+ {100*p1:.1f}% vs code- {100*p0:.1f}% SMD {smd_bin(p1,p0):+.3f}")
