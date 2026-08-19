#!/usr/bin/env python3
"""STEPS 1-2 — competing liver disease (etiology) + cardiometabolic criterion.

Read-only, aggregate only. Scans diagnoses_icd once for code-based flags; prints
every code set with long_title for verification; combines with labs (CLEAN_POP)
and omr vitals for a missingness-tolerant cardiometabolic criterion. Writes a
markdown fragment to the scratchpad.

Run: python scripts/predef_etio_metab.py
"""
import os
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, CLEAN_POP

FRAG = os.path.join(os.environ.get("SCRATCH", "/tmp"), "frag_step1_2.md")
FRAME = "data/processed/aim1a_frame.parquet"
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# ---- code-set predicates (version-aware, dotless, on trim(icd_code) AS code) ----
SETS = {
    "Alcohol-related liver disease (K70; 571.0-571.3)":
        "((icd_version=10 AND code LIKE 'K70%') OR (icd_version=9 AND code IN ('5710','5711','5712','5713')))",
    "Alcohol use disorder (F10; 303.x, 305.0x)":
        "((icd_version=10 AND code LIKE 'F10%') OR (icd_version=9 AND (code LIKE '303%' OR code LIKE '3050%')))",
    "Viral hepatitis B/C (B18,B19; 070.x)":
        "((icd_version=10 AND (code LIKE 'B18%' OR code LIKE 'B19%')) OR (icd_version=9 AND code LIKE '070%'))",
    "Other etiology (AIH,PBC,PSC,hemochromatosis,Wilson,A1AT)":
        "((icd_version=10 AND code IN ('K754','K743','K830','E8311','E8301','E8801')) "
        "OR (icd_version=9 AND code IN ('57142','5716','5761','27501','27503','2751','2734')))",
    "Cirrhosis & complications (K74,K76.6,K72; 571.5,572.x)":
        "((icd_version=10 AND (code LIKE 'K74%' OR code='K766' OR code LIKE 'K72%')) "
        "OR (icd_version=9 AND (code='5715' OR code LIKE '572%')))",
    "Hepatocellular carcinoma (C22.0; 155.0)":
        "((icd_version=10 AND code='C220') OR (icd_version=9 AND code='1550'))",
}
CM = {
    "Overweight/obesity (E66,Z68; 278.0x)":
        "((icd_version=10 AND (code LIKE 'E66%' OR code LIKE 'Z68%')) OR (icd_version=9 AND code LIKE '2780%'))",
    "Type-2 diabetes (E11; 250.x)":
        "((icd_version=10 AND code LIKE 'E11%') OR (icd_version=9 AND code LIKE '250%'))",
    "Hypertension (I10-I15; 401-405)":
        "((icd_version=10 AND regexp_matches(code,'^I1[0-35]')) OR (icd_version=9 AND regexp_matches(code,'^40[1-5]')))",
    "Dyslipidemia (E78; 272.x)":
        "((icd_version=10 AND code LIKE 'E78%') OR (icd_version=9 AND code LIKE '272%'))",
}
ALL = {**SETS, **CM}
flagname = {k: f"f{i}" for i, k in enumerate(ALL)}

# ---- per-hadm code flags (one scan) ----
aggs = ",\n  ".join(
    f"max(CASE WHEN {pred} THEN 1 ELSE 0 END) AS {flagname[k]}" for k, pred in ALL.items())
codes = con.execute(f"""
  WITH d AS (SELECT hadm_id, trim(icd_code) AS code, icd_version
             FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
  SELECT hadm_id, {aggs} FROM d GROUP BY hadm_id
""").fetchdf()

# ---- verification: matched codes + long_title ----
L = []
def w(s=""): L.append(s)
w("## Step 1 — Competing liver disease (code sets shown for verification)\n")
w("Version-aware, dotless. Matched codes with `long_title` from d_icd_diagnoses:\n")
for k, pred in ALL.items():
    m = con.execute(f"""
      WITH dd AS (SELECT trim(icd_code) AS code, icd_version, long_title
                  FROM read_csv('{DATA}/d_icd_diagnoses.csv.gz', types={{'icd_code':'VARCHAR'}}))
      SELECT icd_version, code, long_title FROM dd WHERE {pred}
      ORDER BY icd_version DESC, code""").fetchdf()
    tag = "**[Step 2 cardiometabolic]**" if k in CM else ""
    w(f"\n<details><summary>{k} — {len(m)} codes {tag}</summary>\n")
    w("| v | code | long_title |")
    w("| --: | --- | --- |")
    show = m if len(m) <= 25 else m.head(25)
    for _, r in show.iterrows():
        w(f"| {r.icd_version} | {r.code} | {r.long_title} |")
    if len(m) > 25:
        w(f"| … | … | (+{len(m)-25} more) |")
    w("\n</details>")
w("")

# ---- assemble analytic frame ----
frame = con.execute(
    f"SELECT hadm_id, code_positive, note_b, gender, race, insurance FROM read_parquet('{FRAME}')"
).fetchdf()
labs = con.execute(f"""SELECT hadm_id, lab_HbA1c, lab_Glucose, lab_Triglycerides, lab_HDL,
    omr_BMI, omr_SBP, omr_DBP, has_BMI, has_SBP FROM read_parquet('{CLEAN_POP}')""").fetchdf()
df = frame.merge(codes, on="hadm_id", how="left").merge(labs, on="hadm_id", how="left")
for c in flagname.values():
    df[c] = df[c].fillna(0).astype(bool)
N = len(df)
f = flagname
df["cell"] = np.select(
    [df.code_positive & df.note_b, ~df.code_positive & df.note_b,
     df.code_positive & ~df.note_b, ~df.code_positive & ~df.note_b],
    ["code+/note+", "code-/note+", "code+/note-", "code-/note-"], default="")

# etiology composite flags
df["alcohol"] = df[f["Alcohol-related liver disease (K70; 571.0-571.3)"]] | df[f["Alcohol use disorder (F10; 303.x, 305.0x)"]]
df["viral"] = df[f["Viral hepatitis B/C (B18,B19; 070.x)"]]
df["other_etio"] = df[f["Other etiology (AIH,PBC,PSC,hemochromatosis,Wilson,A1AT)"]]
df["cirrhosis"] = df[f["Cirrhosis & complications (K74,K76.6,K72; 571.5,572.x)"]]
df["hcc"] = df[f["Hepatocellular carcinoma (C22.0; 155.0)"]]
df["any_competing"] = df.alcohol | df.viral | df.other_etio | df.cirrhosis | df.hcc

# ---- Step 1 report: per-cell etiology prevalence ----
w("### Etiology prevalence by 2×2 cell (primary b)\n")
w("| cell | n | alcohol % | viral hep % | other etiology % | cirrhosis % |")
w("| --- | --: | --: | --: | --: | --: |")
for cell in ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]:
    g = df[df.cell == cell]; n = len(g)
    w(f"| {cell} | {n:,} | {100*g.alcohol.mean():.1f} | {100*g.viral.mean():.1f} "
      f"| {100*g.other_etio.mean():.1f} | {100*g.cirrhosis.mean():.1f} |")
w("")

# ---- cardiometabolic criteria (code OR lab OR vital) ----
male = df.gender == "M"
df["cm_overwt_pos"] = df[f["Overweight/obesity (E66,Z68; 278.0x)"]] | (df.omr_BMI >= 25)
df["cm_overwt_asc"] = df[f["Overweight/obesity (E66,Z68; 278.0x)"]] | df.omr_BMI.notna()
df["cm_dysgly_pos"] = df[f["Type-2 diabetes (E11; 250.x)"]] | (df.lab_HbA1c >= 5.7) | (df.lab_Glucose >= 100)
df["cm_dysgly_asc"] = df[f["Type-2 diabetes (E11; 250.x)"]] | df.lab_HbA1c.notna() | df.lab_Glucose.notna()
df["cm_htn_pos"] = df[f["Hypertension (I10-I15; 401-405)"]] | (df.omr_SBP >= 130) | (df.omr_DBP >= 85)
df["cm_htn_asc"] = df[f["Hypertension (I10-I15; 401-405)"]] | df.omr_SBP.notna()
df["cm_dyslip_pos"] = (df[f["Dyslipidemia (E78; 272.x)"]] | (df.lab_Triglycerides >= 150)
                       | (male & (df.lab_HDL < 40)) | (~male & (df.lab_HDL < 50)))
df["cm_dyslip_asc"] = df[f["Dyslipidemia (E78; 272.x)"]] | df.lab_Triglycerides.notna() | df.lab_HDL.notna()
CRIT = ["overwt", "dysgly", "htn", "dyslip"]
df["cm_meets1"] = np.logical_or.reduce([df[f"cm_{c}_pos"] for c in CRIT])
df["cm_asc_any"] = np.logical_or.reduce([df[f"cm_{c}_asc"] for c in CRIT])
df["cm_unasc_all"] = ~df.cm_asc_any
df["cm_none"] = ~df.cm_meets1 & ~df.cm_unasc_all
df["metabolic_risk"] = df.cm_meets1

w("## Step 2 — Cardiometabolic criterion (code OR lab OR vital; missingness-tolerant)\n")
w("Note: 'glucose ≥100' uses any glucose (fasting status unknown); antidiabetic "
  "medication NOT incorporated (prescriptions not processed) — a stated limitation.\n")
w("| criterion | positive % | UNASCERTAINABLE % |")
w("| --- | --: | --: |")
for c, lab in [("overwt", "Overweight/obesity"), ("dysgly", "Dysglycemia"),
               ("htn", "Hypertension"), ("dyslip", "Dyslipidemia")]:
    w(f"| {lab} | {100*df[f'cm_{c}_pos'].mean():.1f} | {100*(~df[f'cm_{c}_asc']).mean():.1f} |")
w(f"\n- Meet ≥1 criterion: **{int(df.cm_meets1.sum()):,} ({100*df.cm_meets1.mean():.1f}%)**")
w(f"- Meet none (ascertainable, no criterion): {int(df.cm_none.sum()):,} ({100*df.cm_none.mean():.1f}%)")
w(f"- Unascertainable for ALL four: {int(df.cm_unasc_all.sum()):,} ({100*df.cm_unasc_all.mean():.1f}%)\n")

def by(group, col, title):
    w(f"### {title}: meets≥1 / none / unascertainable-all, by {group}\n")
    w(f"| {group} | n | meets≥1 % | none % | unasc-all % |")
    w("| --- | --: | --: | --: | --: |")
    order = df.groupby(group).size().sort_values(ascending=False).index
    for v in order:
        g = df[df[group] == v]; n = len(g)
        if n < 200:
            continue
        w(f"| {str(v)[:36]} | {n:,} | {100*g.cm_meets1.mean():.1f} | {100*g.cm_none.mean():.1f} "
          f"| {100*g.cm_unasc_all.mean():.1f} |")
    w("")
by("cell", "cm", "Cardiometabolic ascertainment")
by("race", "cm", "Cardiometabolic ascertainment")
by("insurance", "cm", "Cardiometabolic ascertainment")

# ---- Step 1 cross-tab within note-positive + recovery-zone definitions ----
w("### Within note-positive (primary b): metabolic-risk / alcohol cross-tab\n")
npos = df[df.note_b]
mo = npos.metabolic_risk & ~npos.alcohol
ao = ~npos.metabolic_risk & npos.alcohol
bo = npos.metabolic_risk & npos.alcohol
ne = ~npos.metabolic_risk & ~npos.alcohol
w(f"Among {len(npos):,} note-positive admissions: metabolic-only "
  f"{int(mo.sum()):,} ({100*mo.mean():.1f}%); alcohol-only {int(ao.sum()):,} ({100*ao.mean():.1f}%); "
  f"both {int(bo.sum()):,} ({100*bo.mean():.1f}%); neither {int(ne.sum()):,} ({100*ne.mean():.1f}%).\n")

rz = df[df.cell == "code-/note+"]
w("### Recovery-zone (code−/note+) count under three definitions (sensitivity — do not pick)\n")
w(f"- Steatosis alone: **{len(rz):,}**")
w(f"- Excluding alcohol codes (ALD/AUD): {int((~rz.alcohol).sum()):,} "
  f"(−{int(rz.alcohol.sum()):,})")
w(f"- Excluding ALL competing etiologies: {int((~rz.any_competing).sum()):,} "
  f"(−{int(rz.any_competing.sum()):,})\n")

os.makedirs(os.path.dirname(FRAG), exist_ok=True)
with open(FRAG, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {FRAG}")
print(f"recovery zone: alone={len(rz):,}  excl-alcohol={int((~rz.alcohol).sum()):,}  "
      f"excl-all-competing={int((~rz.any_competing).sum()):,}")
print(f"cardiometabolic meets>=1: {100*df.cm_meets1.mean():.1f}%  unasc-all: {100*df.cm_unasc_all.mean():.1f}%")
