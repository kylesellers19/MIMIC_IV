#!/usr/bin/env python3
"""Imaging denominator deep-dive: WHY admissions lack liver-inclusive imaging.

Read-only, aggregate only (exam names are generic metadata; no note text). Reads
CLEAN_POP. Three-way radiology split, principal-diagnosis ICD-chapter mapping,
access-vs-indication test, LOS bands, and side-by-side 2x2s. Writes Steps 1-5 of
docs/imaging_denominator.md; Steps 6-7 prose appended separately.

Run: python scripts/imaging_denominator.py
"""
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, CLEAN_POP, LOCKED_POP

NOTE = "data/raw/note"
DOC = "docs/imaging_denominator.md"
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
MOD = r"(\bCT\b|\bCTA\b|\bMR\b|\bMRI\b|\bUS\b|U\.S|ULTRASOUND|SONO)"
REGION = r"(ABD|LIVER|HEPAT|\bRUQ\b|BILIARY|GALLBLADDER)"

# note_id -> liver_incl (and keep exam rows for (b) tally)
det = con.execute(f"""
  SELECT note_id, upper(field_value) AS exam,
         (regexp_matches(upper(field_value),'{MOD}') AND regexp_matches(upper(field_value),'{REGION}')) AS liver
  FROM read_csv_auto('{NOTE}/radiology_detail.csv.gz') WHERE field_name='exam_name'
""").fetchdf()
note_liver = det.groupby("note_id").liver.max()
rad = con.execute(f"SELECT note_id, subject_id, hadm_id, charttime FROM read_csv_auto('{NOTE}/radiology.csv.gz')").fetchdf()
rad["liver"] = rad.note_id.map(note_liver).fillna(False).astype(bool)

# population
pop = con.execute(f"""
  SELECT c.hadm_id, c.subject_id, c.code_positive, c.race, c.insurance, c.age, c.gender,
         c.admission_type, c.admission_location, c.los_days, l.admittime
  FROM read_parquet('{CLEAN_POP}') c JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)
""").fetchdf()
frame = con.execute("SELECT hadm_id, note_b FROM read_parquet('data/processed/aim1a_frame.parquet')").fetchdf()
pop = pop.merge(frame, on="hadm_id", how="left")
pop["admittime"] = pd.to_datetime(pop["admittime"])
lh = set(pop.hadm_id.astype("int64")); ls = set(pop.subject_id.astype("int64"))

# inpatient linkage
rad_inp = rad[rad.hadm_id.notna()]
any_inp = set(rad_inp.hadm_id.astype("int64")) & lh
liv_inp = set(rad_inp[rad_inp.liver].hadm_id.astype("int64")) & lh
pop["any_inp"] = pop.hadm_id.isin(any_inp)
pop["liv_inp"] = pop.hadm_id.isin(liv_inp)
# outpatient window 365/30
op = rad[rad.hadm_id.isna() & rad.subject_id.isin(ls)][["subject_id", "charttime", "liver"]].copy()
op["charttime"] = pd.to_datetime(op["charttime"])
m = pop[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
dt = (m.charttime - m.admittime).dt.total_seconds() / 86400.0
inwin = (dt >= -365) & (dt <= 30)
any_out = set(m[inwin].hadm_id.astype("int64"))
liv_out = set(m[inwin & m.liver].hadm_id.astype("int64"))
pop["any_win"] = pop.any_inp | pop.hadm_id.isin(any_out)
pop["liv_win"] = pop.liv_inp | pop.hadm_id.isin(liv_out)
N = len(pop)

# principal diagnosis chapter
seq1 = con.execute(f"""
  SELECT hadm_id, icd_version, trim(icd_code) AS code
  FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}) WHERE seq_num=1
""").fetchdf()

def ch10(c):
    a = c[0]
    if a in "AB": return "Infectious"
    if a == "C" or (a == "D" and c[1:3].isdigit() and int(c[1:3]) <= 49): return "Neoplasms"
    if a == "D": return "Blood/immune"
    if a == "E": return "Endocrine/metabolic"
    if a == "F": return "Mental"
    if a == "G": return "Nervous"
    if a == "H": return "Eye" if (c[1:3].isdigit() and int(c[1:3]) <= 59) else "Ear"
    if a == "I": return "Circulatory"
    if a == "J": return "Respiratory"
    if a == "K": return "Digestive"
    if a == "L": return "Skin"
    if a == "M": return "Musculoskeletal"
    if a == "N": return "Genitourinary"
    if a == "O": return "Pregnancy"
    if a == "P": return "Perinatal"
    if a == "Q": return "Congenital"
    if a == "R": return "Symptoms/ill-defined"
    if a in "ST": return "Injury/poisoning"
    if a in "VWXY": return "External causes"
    if a == "Z": return "Factors/Z-codes"
    return "Other"

def ch9(c):
    if c[:1] == "V": return "Factors/Z-codes"
    if c[:1] == "E": return "External causes"
    try: n = int(c[:3])
    except ValueError: return "Other"
    for lo, hi, lab in [(1,139,"Infectious"),(140,239,"Neoplasms"),(240,279,"Endocrine/metabolic"),
        (280,289,"Blood/immune"),(290,319,"Mental"),(320,389,"Nervous"),(390,459,"Circulatory"),
        (460,519,"Respiratory"),(520,579,"Digestive"),(580,629,"Genitourinary"),(630,679,"Pregnancy"),
        (680,709,"Skin"),(710,739,"Musculoskeletal"),(740,759,"Congenital"),(760,779,"Perinatal"),
        (780,799,"Symptoms/ill-defined"),(800,999,"Injury/poisoning")]:
        if lo <= n <= hi: return lab
    return "Other"

seq1["chapter"] = [ch10(c) if v == 10 else ch9(c) for c, v in zip(seq1.code, seq1.icd_version)]
# one principal chapter per hadm (prefer ICD-10)
seq1 = seq1.sort_values("icd_version", ascending=False).drop_duplicates("hadm_id")
pop = pop.merge(seq1[["hadm_id", "chapter"]], on="hadm_id", how="left")

L = []
def w(s=""): L.append(s)

# ---------------- STEP 1 ----------------
w("## Step 1 — Three-way imaging split\n")
def split(a_col, l_col, label):
    c = pop[l_col].sum()
    b = (pop[a_col] & ~pop[l_col]).sum()
    a = (~pop[a_col]).sum()
    w(f"**{label}:** (a) no radiology **{a:,} ({100*a/N:.1f}%)** · "
      f"(b) radiology, none liver-inclusive **{b:,} ({100*b/N:.1f}%)** · "
      f"(c) ≥1 liver-inclusive **{c:,} ({100*c/N:.1f}%)**")
split("any_inp", "liv_inp", "Inpatient-linked")
split("any_win", "liv_win", "With 365/30 outpatient window")
w("")
# (b) exam types — inpatient scope
b_hadm = set(pop[pop.any_inp & ~pop.liv_inp].hadm_id.astype("int64"))
bexam = det.merge(rad_inp[["note_id", "hadm_id"]], on="note_id")
bexam = bexam[bexam.hadm_id.astype("int64").isin(b_hadm) & ~bexam.liver]
top = bexam.exam.value_counts().head(30)
w("### (b) top exam types among imaged-but-not-liver-inclusive admissions (inpatient scope)\n")
w("| exam_name | n |"); w("| --- | --: |")
for e, n in top.items():
    w(f"| {e} | {n:,} |")
w("")

# ---------------- STEP 2 ----------------
w("## Step 2 — Presenting problem (principal diagnosis, seq_num=1)\n")
w("Chapter mapping = ICD-10-CM / ICD-9-CM Tabular List chapter structure "
  "(WHO/CDC/CMS official chapters). Liver-inclusive imaging rate (365/30 window):\n")
w("### by ICD chapter (ascending)\n")
w("| chapter | n | liver-inclusive imaging % |"); w("| --- | --: | --: |")
g = pop.groupby("chapter").agg(n=("hadm_id", "size"), img=("liv_win", "mean"))
for ch, r in g.sort_values("img").iterrows():
    if r.n >= 200:
        w(f"| {ch} | {int(r.n):,} | {100*r.img:.1f}% |")
w("")
for col, title in [("admission_type", "admission_type"), ("admission_location", "admission_location")]:
    w(f"### by {title} (ascending)\n")
    w(f"| {title} | n | imaging % |"); w("| --- | --: | --: |")
    gg = pop.groupby(col).agg(n=("hadm_id", "size"), img=("liv_win", "mean"))
    for v, r in gg.sort_values("img").iterrows():
        if r.n >= 200:
            w(f"| {str(v)[:40]} | {int(r.n):,} | {100*r.img:.1f}% |")
    w("")

# ---------------- STEP 3 ----------------
def smd_bin(p1, p0):
    d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
    return np.nan if d == 0 else (p1 - p0) / d
PLAUS = {"Digestive", "Infectious", "Neoplasms", "Endocrine/metabolic", "Circulatory"}
sub = pop[pop.chapter.isin(PLAUS)]
w("## Step 3 — Access vs indication (imaging rate by race/insurance, then within-chapter)\n")
w(f"Within-indication subset = principal dx in {sorted(PLAUS)} (n={len(sub):,}).\n")

def group_report(col):
    w(f"### {col}: imaging rate + one-vs-rest SMD (unadjusted vs within-plausible-chapters)\n")
    w(f"| {col} | n | unadj img% | unadj SMD | within-chap img% | within SMD |")
    w("| --- | --: | --: | --: | --: | --: |")
    order = pop.groupby(col).size().sort_values(ascending=False).index
    mx_u = mx_w = 0.0
    for v in order:
        gp = pop[pop[col] == v]
        if len(gp) < 500: continue
        pu = gp.liv_win.mean(); pu_rest = pop[pop[col] != v].liv_win.mean()
        su = smd_bin(pu, pu_rest)
        sg = sub[sub[col] == v]; sgr = sub[sub[col] != v]
        if len(sg) >= 200:
            pw = sg.liv_win.mean(); pw_rest = sgr.liv_win.mean(); sw = smd_bin(pw, pw_rest)
        else:
            pw, sw = np.nan, np.nan
        mx_u = max(mx_u, abs(su)); mx_w = max(mx_w, abs(sw) if not np.isnan(sw) else 0)
        w(f"| {str(v)[:30]} | {len(gp):,} | {100*pu:.1f}% | {su:+.3f} "
          f"| {(str(round(100*pw,1))+'%') if not np.isnan(pw) else '—'} "
          f"| {(f'{sw:+.3f}') if not np.isnan(sw) else '—'} |")
    w(f"\n*max one-vs-rest |SMD|: unadjusted {mx_u:.3f} → within-chapter {mx_w:.3f}.*\n")
    return mx_u, mx_w
ins_u, ins_w = group_report("insurance")
race_u, race_w = group_report("race")
# code status SMD
cs_u = smd_bin(pop[pop.code_positive].liv_win.mean(), pop[~pop.code_positive].liv_win.mean())
cs_w = smd_bin(sub[sub.code_positive].liv_win.mean(), sub[~sub.code_positive].liv_win.mean())
w(f"**Coding status (code+ vs code−) imaging SMD:** unadjusted {cs_u:+.3f} → "
  f"within-plausible-chapters {cs_w:+.3f}.\n")

# ---------------- STEP 4 ----------------
w("## Step 4 — Length of stay and opportunity\n")
pop["losband"] = pd.cut(pop.los_days, [-1e9, 1, 2, 5, 1e9], labels=["<1 day", "1-2", "3-5", "6+"])
w("| LOS band | n | imaging % |"); w("| --- | --: | --: |")
for band in ["<1 day", "1-2", "3-5", "6+"]:
    gp = pop[pop.losband == band]
    w(f"| {band} | {len(gp):,} | {100*gp.liv_win.mean():.1f}% |")
short = pop.los_days < 1; noimg = ~pop.liv_win
w(f"\n- Short-stay (<1 day): {int(short.sum()):,} ({100*short.mean():.1f}%). "
  f"Of these, {int((short & noimg).sum()):,} ({100*(short & noimg).mean() / short.mean():.1f}% "
  f"of short-stay) are NOT liver-imaged.")
w(f"- Of all non-imaged admissions ({int(noimg.sum()):,}), {int((short & noimg).sum()):,} "
  f"({100*(short & noimg).sum()/noimg.sum():.1f}%) are short-stay.\n")

# ---------------- STEP 5 ----------------
w("## Step 5 — The 2×2 side by side\n")
def two_by_two(mask, label):
    d = pop[mask]; cp = d.code_positive.astype(bool); nt = d.note_b.astype(bool)
    pp = int((cp & nt).sum()); npp = int((~cp & nt).sum())
    pn = int((cp & ~nt).sum()); nn = int((~cp & ~nt).sum())
    notepos = pp + npp
    rec = 100 * npp / notepos if notepos else float("nan")
    w(f"| {label} | {len(d):,} | {pp:,} | {npp:,} | {pn:,} | {nn:,} | {rec:.1f}% |")
    return rec
w("Recovery % = code−/note+ ÷ all note+.\n")
w("| population | N | code+/note+ | code−/note+ | code+/note− | code−/note− | recovery % |")
w("| --- | --: | --: | --: | --: | --: | --: |")
r_full = two_by_two(pop.hadm_id.notna(), "Full population")
r_img = two_by_two(pop.liv_win, "Imaging-restricted (liver-inclusive)")
r_b = two_by_two(pop.any_win & ~pop.liv_win, "(b) imaged, not liver-inclusive")
w(f"\n**Recovery % moves: full {r_full:.1f}% → imaging-restricted {r_img:.1f}% "
  f"(Δ {r_img-r_full:+.1f} pts).**\n")

with open(DOC, "w") as fh:
    fh.write("# Imaging Denominator — why 63% lack liver-inclusive imaging\n\n"
             "> Aggregate only; read from CLEAN_POP; frozen phenotype unchanged. Population "
             f"N = {N:,}. Note-positive = Tier A (primary b).\n\n" + "\n".join(L) + "\n")
print("wrote", DOC)
print(f"insurance SMD {ins_u:.3f}->{ins_w:.3f} | race SMD {race_u:.3f}->{race_w:.3f} | "
      f"code SMD {cs_u:+.3f}->{cs_w:+.3f}")
print(f"recovery full {r_full:.1f}% img {r_img:.1f}% b {r_b:.1f}%")
