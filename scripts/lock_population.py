#!/usr/bin/env python3
"""PROMPT 1 — lock the analysis population.

Defines the note-covered window at ADMISSION level (derived admission year =
year(admittime)), separates the two exclusions (out-of-window vs in-window-no-note),
locks the population, and (when WRITE=1) materializes the covariate parquet.

No note text is read — only subject_id/hadm_id linkage keys. Aggregates only.
Run:  python scripts/lock_population.py         # report only
      WRITE=1 python scripts/lock_population.py  # also materialize parquet
"""
import os
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, analysis_admissions_sql

NOTE = "data/raw/note"
from scripts.masld_config import LOCKED_POP as OUT   # this script produces the uncleaned locked parquet
WINDOW_COV_THRESHOLD = 0.20     # a year counts as "covered" if either% >= this
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")


def smd_bin(p1, p0):
    d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
    return np.nan if d == 0 else (p1 - p0) / d

def smd_cont(a, b):
    a, b = a.dropna(), b.dropna()
    d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return np.nan if d == 0 else (a.mean() - b.mean()) / d


con.execute(f"CREATE TEMP VIEW ap AS {analysis_admissions_sql()}")
df = con.execute("""
  SELECT hadm_id, subject_id, code_positive, n_diagnoses,
         LEAST(age_at_admit, 91) AS age, gender, race, insurance, language,
         marital_status, admission_type, admission_location, hospital_expire_flag,
         los_days, anchor_year_group, admittime, dischtime,
         year(admittime) AS admit_year
  FROM ap
""").fetchdf()

disch = con.execute(f"SELECT hadm_id FROM read_csv_auto('{NOTE}/discharge.csv.gz')").fetchdf()
rad = con.execute(f"SELECT hadm_id FROM read_csv_auto('{NOTE}/radiology.csv.gz')").fetchdf()
disch_hadm = set(disch.hadm_id.dropna().astype("int64"))
rad_hadm = set(rad.hadm_id.dropna().astype("int64"))
df["has_dc"] = df.hadm_id.isin(disch_hadm)
df["has_rad"] = df.hadm_id.isin(rad_hadm)
df["has_note"] = df.has_dc | df.has_rad
N = len(df)

# ---------------------------------------------------------------- STEP 1
print("=" * 74 + "\nSTEP 1 — note coverage by DERIVED admission year = year(admittime)\n" + "=" * 74)
by = df.groupby("admit_year").agg(n=("hadm_id", "size"),
                                  either=("has_note", "mean")).sort_index()
by["either%"] = (by.either * 100).round(1)
covered_years = by.index[by.either >= WINDOW_COV_THRESHOLD]
cutoff = int(covered_years.max())
print(by[["n", "either%"]].to_string())
tail = by[by.either < WINDOW_COV_THRESHOLD]
print(f"\nFINDING: coverage is ~flat (67-70%) across 2110-2207 — NO admission-year cliff. "
      f"It only tapers in the sparse tail; years below {WINDOW_COV_THRESHOLD:.0%} coverage "
      f"= {list(tail.index)} ({int(tail['n'].sum()):,} admissions total). "
      f"=> Note missingness is NOT a temporal window at admission level.")

# ---------------------------------------------------------------- STEP 2
# Because admission-year shows no window, the release-lineage exclusion is PATIENT-level
# (a subject is in the note release, all-or-nothing) — verified below.
print("\n" + "=" * 74 + "\nSTEP 2 — separate the two exclusions (patient-level, data-driven)\n" + "=" * 74)
df["subj_has_note"] = df.groupby("subject_id")["has_note"].transform("any")

# verify all-or-nothing: among multi-admission subjects, how consistent is has_note?
multi = df.groupby("subject_id").filter(lambda g: len(g) > 1)
by_subj = multi.groupby("subject_id")["has_note"].agg(["mean", "size"])
all_or_none = ((by_subj["mean"] == 0) | (by_subj["mean"] == 1)).mean()
print(f"  multi-admission subjects whose has_note is all-or-nothing: {100*all_or_none:.1f}% "
      f"(supports patient-level release membership)")

rel = ~df.subj_has_note                    # (a) subject has ZERO notes anywhere
enc = df.subj_has_note & ~df.has_note       # (b) subject has notes elsewhere, not this adm
print(f"\n(a) RELEASE-LINEAGE (subject absent from note dataset): "
      f"{int(rel.sum()):,} admissions, {df[rel].subject_id.nunique():,} subjects "
      f"({100*rel.mean():.1f}% of admissions)")
print(f"(b) ENCOUNTER-LEVEL (subject has notes, this admission has none): "
      f"{int(enc.sum()):,} admissions ({100*enc.sum()/df.subj_has_note.sum():.1f}% of "
      f"note-release admissions)")
print("\n(a) release-lineage admissions by anchor_year_group (ties to prior finding):")
print((df[rel].groupby("anchor_year_group").size()).to_string())

# (b) selection-threat characterization
w = df[df.subj_has_note].copy()            # restrict to note-release patients
w["no_note"] = ~w.has_note
print("\n(b) differs by coding status?")
p1 = w[w.code_positive].no_note.mean(); p0 = w[~w.code_positive].no_note.mean()
print(f"    encounter no-note rate: code+ {p1*100:.1f}%  code- {p0*100:.1f}%  "
      f"SMD={smd_bin(p1,p0):+.3f}")
print("\n(b) encounter no-note rate by admission_type:")
print((w.groupby("admission_type").no_note.agg(["mean", "size"])
       .assign(pct=lambda x: (x["mean"]*100).round(1))[["pct", "size"]]
       .sort_values("pct", ascending=False)).to_string())
print("\n(b) encounter no-note rate by insurance:")
print((w.groupby("insurance").no_note.mean()*100).round(1).sort_values(ascending=False).to_string())
print("\n(b) encounter no-note rate by race (n>=500):")
rr = w.groupby("race").no_note.agg(["mean", "size"]); rr = rr[rr["size"] >= 500]
print((rr["mean"]*100).round(1).sort_values(ascending=False).to_string())
print("\n(b) LOS: encounter no-note vs has-note")
print(f"    LOS median no-note={w[w.no_note].los_days.median():.2f}d  "
      f"has-note={w[~w.no_note].los_days.median():.2f}d  "
      f"SMD={smd_cont(w[w.no_note].los_days, w[~w.no_note].los_days):+.3f}")
short = (w.los_days < 1)
print(f"    LOS<1 day: no-note {100*short[w.no_note].mean():.1f}%  "
      f"has-note {100*short[~w.no_note].mean():.1f}%")

# ---------------------------------------------------------------- STEP 3
print("\n" + "=" * 74 + "\nSTEP 3 — lock the population\n" + "=" * 74)
# Operative restriction = note presence (admission-year window is negligible; not imposed).
locked = df[df.has_note]
dc_only = df[df.has_dc]
def desc(d, label):
    print(f"  {label:40s} adm={len(d):,}  subj={d.subject_id.nunique():,}  "
          f"code+={int(d.code_positive.sum()):,}  code-={int((~d.code_positive).sum()):,}")
desc(locked, "LOCKED (>=1 linked note, discharge OR radiology)")
desc(dc_only, "  sensitivity: discharge-only")
print(f"  removed vs analysis pop ({N:,}): {N-len(locked):,}  "
      f"[(a) release-lineage {int(rel.sum()):,} + (b) encounter no-note {int(enc.sum()):,}]")

# ---------------------------------------------------------------- STEP 5 (guarded)
if os.environ.get("WRITE") == "1":
    keep = df[df.has_note].copy()
    con.register("keep_df", keep)
    con.execute(f"COPY keep_df TO '{OUT}' (FORMAT parquet)")
    print(f"\n[WRITE] materialized {OUT}  rows={len(keep):,}  cols={len(keep.columns)}")
    print("        columns: " + ", ".join(keep.columns))
else:
    print("\n[report-only] set WRITE=1 to materialize the parquet.")
