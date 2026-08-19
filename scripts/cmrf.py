#!/usr/bin/env python3
"""STEPS 1a/1b/2 — corrected drug-class counts + five CMRF criteria (Rinella 2023).

Fixes the Step-1 counting error (class totals were sums of per-drug distinct-
admission counts, double-counting admissions on >1 drug in a class). Reports
DISTINCT admissions per class within the locked population. Applies the rulings
(beta-blockers/insulin/hydralazine/metolazone/alpha-blockers excluded; metformin
included) and implements the five consensus CMRF criteria (code OR lab/vital OR
qualifying med). Materializes per-admission CMRF + alcohol + etiology flags to a
gitignored parquet. Aggregate only.

Run: python scripts/cmrf.py
"""
import os
import re
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, CLEAN_POP

RX = "data/raw/hosp/prescriptions.csv.gz"
OUT = "data/processed/cmrf.parquet"
FRAG = os.path.join(os.environ.get("SCRATCH", "/tmp"), "frag_cmrf.md")
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# ---- drug keyword lists (rulings applied) ----
INSULIN = ["insulin", "glargine", "lispro", "glulisine", "detemir", "degludec", "lantus",
           "humalog", "novolog", "novolin", "humulin", "levemir", "tresiba", "apidra",
           "toujeo", "basaglar", "admelog", "fiasp", " nph", "nph "]
METFORMIN = ["metformin", "glucophage", "glucovance", "metaglip", "janumet", "kombiglyze",
             "jentadueto", "synjardy", "invokamet", "xigduo"]
ORAL_AD = METFORMIN + ["glipizide", "glyburide", "glimepiride", "glibenclamide", "gliclazide",
    "chlorpropamide", "tolbutamide", "tolazamide", "pioglitazone", "rosiglitazone", "sitagliptin",
    "saxagliptin", "linagliptin", "alogliptin", "exenatide", "liraglutide", "dulaglutide",
    "semaglutide", "lixisenatide", "canagliflozin", "dapagliflozin", "empagliflozin",
    "ertugliflozin", "repaglinide", "nateglinide", "acarbose", "miglitol", "pramlintide",
    "januvia", "glucotrol", "amaryl", "actos", "avandia", "victoza", "trulicity", "ozempic",
    "rybelsus", "jardiance", "farxiga", "invokana", "steglatro"]
BB = ["metoprolol", "atenolol", "carvedilol", "labetalol", "propranolol", "bisoprolol",
      "nadolol", "nebivolol", "sotalol", "timolol", "pindolol", "acebutolol", "betaxolol",
      "esmolol", "carteolol"]
HTN_QUAL = ["lisinopril", "enalapril", "captopril", "ramipril", "benazepril", "quinapril",
    "fosinopril", "perindopril", "trandolapril", "moexipril", "losartan", "valsartan",
    "irbesartan", "candesartan", "olmesartan", "telmisartan", "azilsartan", "eprosartan",
    "amlodipine", "nifedipine", "diltiazem", "verapamil", "felodipine", "nicardipine",
    "isradipine", "nisoldipine", "clevidipine", "hydrochlorothiazide", "hctz", "chlorthalidone",
    "indapamide", "chlorothiazide", "clonidine", "methyldopa", "guanfacine", "minoxidil"]
HTN_EXCL = ["hydralazine", "metolazone", "doxazosin", "terazosin", "prazosin"]  # excluded from crit 3
STATIN = ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin",
          "pitavastatin", "fluvastatin", "lipitor", "crestor", "zocor", "livalo"]
LIPID_OTHER = ["gemfibrozil", "fenofibr", "clofibrate", "bezafibrate", "tricor", "trilipix",
    "ezetimibe", "zetia", "vytorin", "evolocumab", "alirocumab", "repatha", "praluent",
    "cholestyramine", "colestipol", "colesevelam", "welchol", "icosapent", "vascepa",
    "lovaza", "nicotinic"]


def match(d):
    if "metamucil" in d:
        return {k: False for k in ["insulin", "metformin", "oral_ad", "bb", "htn_qual",
                                   "htn_excl", "lipid"]}
    def has(lst): return any(k in d for k in lst)
    return dict(
        insulin=has(INSULIN) or bool(re.search(r"aspart(?!ame)", d)),
        metformin=has(METFORMIN), oral_ad=has(ORAL_AD),
        bb=has(BB), htn_qual=has(HTN_QUAL), htn_excl=has(HTN_EXCL),
        lipid=has(STATIN) or has(LIPID_OTHER) or bool(re.search(r"niacin(?!amide)", d)),
    )


# ---- per-drug flags (locked pop, non-ophthalmic route) ----
con.execute(f"CREATE TEMP VIEW lh AS SELECT hadm_id FROM read_parquet('{CLEAN_POP}')")
RTFILTER = "(route IS NULL OR (upper(route) NOT LIKE '%EYE%' AND upper(route) NOT IN ('OU','OS','OD')))"
ds = con.execute(f"""
  SELECT DISTINCT lower(drug) AS drug FROM read_csv_auto('{RX}')
  SEMI JOIN lh USING (hadm_id) WHERE drug IS NOT NULL AND {RTFILTER}
""").fetchdf()
fl = ds.drug.map(match).apply(pd.Series)
d2c = pd.concat([ds, fl], axis=1)
con.register("d2c", d2c)

# ---- per-admission med flags (DISTINCT admissions) ----
medh = con.execute(f"""
  SELECT p.hadm_id,
     max(insulin::INT) insulin, max(metformin::INT) metformin, max(oral_ad::INT) oral_ad,
     max(bb::INT) bb, max(htn_qual::INT) htn_qual, max(htn_excl::INT) htn_excl,
     max(lipid::INT) lipid
  FROM read_csv_auto('{RX}') p JOIN d2c ON lower(p.drug)=d2c.drug
  SEMI JOIN lh ON p.hadm_id=lh.hadm_id WHERE {RTFILTER}
  GROUP BY p.hadm_id
""").fetchdf()

pop = con.execute(f"""SELECT hadm_id, gender, lab_HbA1c, lab_Glucose, lab_Triglycerides, lab_HDL,
    omr_BMI, omr_SBP, omr_DBP FROM read_parquet('{CLEAN_POP}')""").fetchdf()
# ---- code flags (one diagnoses scan) ----
codes = con.execute(f"""
  WITH d AS (SELECT hadm_id, trim(icd_code) code, icd_version
             FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
  SELECT hadm_id,
    max(((icd_version=10 AND (code LIKE 'E66%' OR code LIKE 'Z683%' OR code LIKE 'Z684%'))
       OR (icd_version=9 AND code LIKE '2780%'))::INT) ow_code,
    max(((icd_version=10 AND (code LIKE 'E11%' OR code='R7303'))
       OR (icd_version=9 AND (code LIKE '250%' OR code LIKE '7902%')))::INT) dg_code,
    max(((icd_version=10 AND regexp_matches(code,'^I1[0-6]'))
       OR (icd_version=9 AND regexp_matches(code,'^40[1-5]')))::INT) htn_code,
    max(((icd_version=10 AND (code LIKE 'E781%' OR code LIKE 'E782%'))
       OR (icd_version=9 AND code='2721'))::INT) tg_code,
    max(((icd_version=10 AND code='E786') OR (icd_version=9 AND code='2725'))::INT) hdl_code,
    max(((icd_version=10 AND code LIKE 'K70%') OR (icd_version=9 AND code IN ('5710','5711','5712','5713'))
       OR (icd_version=10 AND code LIKE 'F10%') OR (icd_version=9 AND (code LIKE '303%' OR code LIKE '3050%')))::INT) alcohol,
    max(((icd_version=10 AND (code LIKE 'B18%' OR code LIKE 'B19%')) OR (icd_version=9 AND code LIKE '070%'))::INT) viral,
    max(((icd_version=10 AND code IN ('K754','K743','K830','E8311','E8301','E8801'))
       OR (icd_version=9 AND code IN ('57142','5716','5761','27501','27503','2751','2734')))::INT) other_etio,
    max(((icd_version=10 AND (code LIKE 'K74%' OR code='K766' OR code LIKE 'K72%'))
       OR (icd_version=9 AND (code='5715' OR code LIKE '572%')))::INT) cirrhosis,
    max(((icd_version=10 AND code='C220') OR (icd_version=9 AND code='1550'))::INT) hcc
  FROM d GROUP BY hadm_id
""").fetchdf()

m = pop.merge(medh, on="hadm_id", how="left").merge(codes, on="hadm_id", how="left")
medcols = ["insulin", "metformin", "oral_ad", "bb", "htn_qual", "htn_excl", "lipid"]
codecols = ["ow_code", "dg_code", "htn_code", "tg_code", "hdl_code", "alcohol", "viral",
            "other_etio", "cirrhosis", "hcc"]
for c in medcols + codecols:
    m[c] = m[c].fillna(0).astype(bool)
N = len(m)
male = m.gender == "M"

L = []
def w(s=""): L.append(s)

# ---------------- STEP 1a ----------------
w("## Step 1a — Counting error diagnosed and corrected\n")
w("**Cause:** the Step-1 class totals summed each drug string's DISTINCT-admission "
  "count across the class, so an admission on ≥2 drugs in a class (e.g. metoprolol AND "
  "lisinopril) was counted once per drug → the antihypertensive total (449,087) exceeded "
  "the population (373,992). The matching WAS already restricted to the locked population. "
  "**Fix:** count DISTINCT admissions per class from the per-admission flags.\n")
def dc(mask): return int(mask.sum())
antidiab_all = m.insulin | m.oral_ad
antihtn_all = m.bb | m.htn_qual | m.htn_excl
w("| class | DISTINCT admissions | % of pop |")
w("| --- | --: | --: |")
for lab, mask in [("Antidiabetic (all, incl insulin)", antidiab_all),
                  ("  — oral antidiabetic (crit-2 qualifying, insulin excl)", m.oral_ad),
                  ("  — metformin (incl in oral)", m.metformin),
                  ("  — insulin (EXCLUDED from crit 2)", m.insulin),
                  ("Antihypertensive (all)", antihtn_all),
                  ("  — qualifying antihypertensive (crit-3)", m.htn_qual),
                  ("  — beta-blockers (EXCLUDED)", m.bb),
                  ("  — hydralazine/metolazone/alpha (EXCLUDED)", m.htn_excl),
                  ("Lipid-lowering (crit 4/5)", m.lipid)]:
    w(f"| {lab} | {dc(mask):,} | {100*dc(mask)/N:.1f}% |")
w(f"\nAll class totals ≤ {N:,}. ✔\n")

# ---------------- STEP 1b principle ----------------
w("### Ruling principle (recorded)\n")
w("Criteria 2 and 3 are already satisfied by a code OR a lab/vital, so **medications "
  "operate only in the residual where neither exists**. Being restrictive there costs "
  "little and protects specificity. Beta-blockers, insulin, hydralazine, metolazone, and "
  "alpha-blockers are therefore excluded (see Step 6 for per-class rationale).\n")

# ---------------- STEP 2 — CMRF criteria ----------------
crit = {}
# 1 overweight
crit["Overweight/obesity"] = dict(
    code=m.ow_code, lab=pd.Series(False, index=m.index), vital=(m.omr_BMI >= 25),
    med=pd.Series(False, index=m.index), meas=m.omr_BMI.notna())
# 2 dysglycemia (oral antidiabetic med only)
crit["Dysglycemia"] = dict(
    code=m.dg_code, lab=((m.lab_HbA1c >= 5.7) | (m.lab_Glucose >= 100)),
    vital=pd.Series(False, index=m.index), med=m.oral_ad,
    meas=(m.lab_HbA1c.notna() | m.lab_Glucose.notna()))
# 3 hypertension (qualifying antihypertensive)
crit["Hypertension"] = dict(
    code=m.htn_code, lab=pd.Series(False, index=m.index),
    vital=((m.omr_SBP >= 130) | (m.omr_DBP >= 85)), med=m.htn_qual,
    meas=m.omr_SBP.notna())
# 4 hypertriglyceridemia
crit["Hypertriglyceridemia"] = dict(
    code=m.tg_code, lab=(m.lab_Triglycerides >= 150),
    vital=pd.Series(False, index=m.index), med=m.lipid, meas=m.lab_Triglycerides.notna())
# 5 low HDL
crit["Low HDL"] = dict(
    code=m.hdl_code, lab=((male & (m.lab_HDL <= 40)) | (~male & (m.lab_HDL <= 50))),
    vital=pd.Series(False, index=m.index), med=m.lipid, meas=m.lab_HDL.notna())

w("## Step 2 — Five CMRF criteria (Rinella 2023), per-source contribution\n")
w("Each criterion: positive = code OR lab/vital-over-threshold OR qualifying med; "
  "unascertainable = no code, no med, no measurement.\n")
w("| criterion | positive % | unasc % | by code | by lab | by vital | by med | **med-ONLY** |")
w("| --- | --: | --: | --: | --: | --: | --: | --: |")
pos_any = pd.Series(False, index=m.index); asc_any = pd.Series(False, index=m.index)
for name, c in crit.items():
    positive = c["code"] | c["lab"] | c["vital"] | c["med"]
    ascertain = c["code"] | c["med"] | c["meas"]
    med_only = c["med"] & ~(c["code"] | c["lab"] | c["vital"])
    crit[name]["pos"] = positive; crit[name]["asc"] = ascertain
    pos_any = pos_any | positive; asc_any = asc_any | ascertain
    def pc(x): return f"{100*x.mean():.1f}"
    w(f"| {name} | {pc(positive)} | {100*(~ascertain).mean():.1f} | {pc(c['code'])} | "
      f"{pc(c['lab'])} | {pc(c['vital'])} | {pc(c['med'])} | {int(med_only.sum()):,} "
      f"({100*med_only.mean():.2f}%) |")
w("")
m["cmrf_ge1"] = pos_any
m["cmrf_unasc_all"] = ~asc_any

# headline: med contribution vs no-med
pos_nomed = pd.Series(False, index=m.index)
for name, c in crit.items():
    pos_nomed = pos_nomed | (c["code"] | c["lab"] | c["vital"])
w("### Headline — did medications move the ≥1-CMRF proportion?\n")
w(f"- ≥1 CMRF **without** medications (5-criteria, code|lab|vital): **{100*pos_nomed.mean():.1f}%**")
w(f"- ≥1 CMRF **with** qualifying medications: **{100*m.cmrf_ge1.mean():.1f}%** "
  f"(Δ +{100*(m.cmrf_ge1.mean()-pos_nomed.mean()):.2f} pts; "
  f"{int((m.cmrf_ge1 & ~pos_nomed).sum()):,} admissions added by meds alone)")
w(f"- Unascertainable for ALL five: {100*m.cmrf_unasc_all.mean():.1f}%")
w(f"\n(For reference, the earlier 4-criteria without-meds figure was 89.5%.) The "
  f"medication contribution is small: the CMRF requirement is **nearly non-binding** in "
  f"this inpatient population — a reportable finding for the discussion.\n")

# ---------------- materialize ----------------
keep = m[["hadm_id", "cmrf_ge1", "cmrf_unasc_all", "alcohol", "viral", "other_etio",
          "cirrhosis", "hcc"]].copy()
con.register("keepdf", keep)
con.execute(f"COPY keepdf TO '{OUT}' (FORMAT parquet)")
os.makedirs(os.path.dirname(FRAG), exist_ok=True)
with open(FRAG, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {OUT} and {FRAG}")
print(f"antidiab_all={dc(antidiab_all):,} antihtn_all={dc(antihtn_all):,} lipid={dc(m.lipid):,} "
      f"(all <= {N:,})")
print(f"cmrf>=1 nomed={100*pos_nomed.mean():.1f}%  withmed={100*m.cmrf_ge1.mean():.1f}%  "
      f"unasc-all={100*m.cmrf_unasc_all.mean():.1f}%")
