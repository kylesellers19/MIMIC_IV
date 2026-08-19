#!/usr/bin/env python3
"""STEP 1 — drug-class resolution from prescriptions (PRINT for approval; then STOP).

Resolves antidiabetic / antihypertensive / lipid-lowering classes by drug-name
matching (GSN/NDC present in the file for audit; matching is name-based). Prints
every matched drug string per class with order + admission counts; reports the
beta-blocker / insulin / metformin traps separately with "meets-criterion-by-this-
alone" counts. Read-only, aggregate only. Scope = locked population (CLEAN_POP).

Run: python scripts/drug_classes.py
"""
import os
import re
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA, CLEAN_POP, MASLD_PREDICATE

RX = "data/raw/hosp/prescriptions.csv.gz"
FULL = os.path.join(os.environ.get("SCRATCH", "/tmp"), "drug_matches_full.txt")
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# ---- keyword lists (lowercase; substring match) ----
INSULIN = ["insulin", "glargine", "lispro", "glulisine", "detemir", "degludec",
           "lantus", "humalog", "novolog", "novolin", "humulin", "levemir", "tresiba",
           "apidra", "toujeo", "basaglar", "admelog", "fiasp", " nph", "nph "]  # 'aspart' via regex
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
NONBB_HTN = ["lisinopril", "enalapril", "captopril", "ramipril", "benazepril", "quinapril",
    "fosinopril", "perindopril", "trandolapril", "moexipril", "losartan", "valsartan",
    "irbesartan", "candesartan", "olmesartan", "telmisartan", "azilsartan", "eprosartan",
    "amlodipine", "nifedipine", "diltiazem", "verapamil", "felodipine", "nicardipine",
    "isradipine", "nisoldipine", "clevidipine", "hydrochlorothiazide", "hctz", "chlorthalidone",
    "indapamide", "metolazone", "chlorothiazide", "clonidine", "hydralazine", "methyldopa",
    "minoxidil", "guanfacine", "doxazosin", "terazosin", "prazosin"]
STATIN = ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin",
          "pitavastatin", "fluvastatin", "lipitor", "crestor", "zocor", "livalo"]
LIPID_OTHER = ["gemfibrozil", "fenofibr", "clofibrate", "bezafibrate", "tricor",
    "trilipix", "ezetimibe", "zetia", "vytorin", "evolocumab", "alirocumab", "repatha",
    "praluent", "cholestyramine", "colestipol", "colesevelam", "welchol", "icosapent",
    "vascepa", "lovaza", "nicotinic"]  # 'lopid' dropped (matched clopidogrel); 'niacin' via regex
AMBIG_NOTE = {"minoxidil": "topical hair-loss use", "timolol": "ophthalmic (glaucoma)",
              "niacin": "vitamin at low dose", "nph": "insulin NPH"}


def match(d):
    if "metamucil" in d:               # fiber supplement (with aspartame) — not a drug of interest
        return dict(insulin=False, metformin=False, oral_ad=False, antidiab=False,
                    bb=False, nonbb_htn=False, antihtn=False, lipid=False)
    def has(lst): return any(k in d for k in lst)
    ins = has(INSULIN) or bool(re.search(r"aspart(?!ame)", d))   # insulin aspart, not aspartame
    met = has(METFORMIN); oral = has(ORAL_AD)
    bb = has(BB); nonbb = has(NONBB_HTN)
    lip = has(STATIN) or has(LIPID_OTHER) or bool(re.search(r"niacin(?!amide)", d))  # niacin, not niacinamide
    antidiab = ins or oral
    antihtn = bb or nonbb
    return dict(insulin=ins, metformin=met, oral_ad=oral, antidiab=antidiab,
                bb=bb, nonbb_htn=nonbb, antihtn=antihtn, lipid=lip)


# distinct drug strings + counts (locked population)
con.execute(f"CREATE TEMP VIEW lh AS SELECT hadm_id FROM read_parquet('{CLEAN_POP}')")
ds = con.execute(f"""
  SELECT lower(drug) AS drug, count(*) AS orders, count(DISTINCT hadm_id) AS adm
  FROM read_csv_auto('{RX}') SEMI JOIN lh USING (hadm_id)
  WHERE drug IS NOT NULL
    AND (route IS NULL OR (upper(route) NOT LIKE '%EYE%' AND upper(route) NOT IN ('OU','OS','OD')))
  GROUP BY 1
""").fetchdf()
flags = ds.drug.map(match).apply(pd.Series)
ds = pd.concat([ds, flags], axis=1)

def cls_rows(col):
    return ds[ds[col]].sort_values("adm", ascending=False)

# full lists to file
with open(FULL, "w") as fh:
    for col in ["antidiab", "antihtn", "lipid", "insulin", "bb", "metformin"]:
        fh.write(f"\n===== {col} ({int(ds[col].sum())} distinct strings) =====\n")
        for _, r in cls_rows(col).iterrows():
            fh.write(f"  {r.adm:>7,} adm  {r.orders:>8,} ord  {r.drug}\n")

print("=" * 74)
print("STEP 1 — DRUG-CLASS MATCH LISTS (for approval). Scope = locked population.")
print("Matching: drug-name substring (GSN/NDC present in file for audit).")
print("=" * 74)
for col, lab in [("antidiab", "ANTIDIABETIC (all)"), ("antihtn", "ANTIHYPERTENSIVE (all, incl BB)"),
                 ("lipid", "LIPID-LOWERING")]:
    g = cls_rows(col)
    print(f"\n## {lab}: {len(g)} distinct strings, "
          f"{int(g.orders.sum()):,} orders, {int(g.adm.sum()):,} admissions")
    for _, r in g.head(30).iterrows():
        print(f"   {r.adm:>7,} adm  {r.orders:>8,} ord  {r.drug}")
    if len(g) > 30:
        print(f"   ... (+{len(g)-30} more; full list in {FULL})")

print("\n" + "=" * 74 + "\nFLAGGED TRAPS (full lists)\n" + "=" * 74)
for col, lab in [("insulin", "INSULIN"), ("bb", "BETA-BLOCKERS"), ("metformin", "METFORMIN")]:
    g = cls_rows(col)
    print(f"\n## {lab}: {len(g)} distinct strings, {int(g.adm.sum()):,} admissions")
    for _, r in g.iterrows():
        note = ""
        for k, v in AMBIG_NOTE.items():
            if k in r.drug:
                note = f"  [{v}]"
        print(f"   {r.adm:>7,} adm  {r.orders:>8,} ord  {r.drug}{note}")

# combos and multi-class
ds["ntop"] = ds.antidiab.astype(int) + ds.antihtn.astype(int) + ds.lipid.astype(int)
combo = ds[(ds.ntop >= 1) & ds.drug.str.contains(r"[-/]", regex=True)]
multi = ds[ds.ntop >= 2]
print(f"\n## COMBINATION products (hyphen/slash, matched): {len(combo)} strings")
for _, r in combo.sort_values("adm", ascending=False).head(20).iterrows():
    print(f"   {r.adm:>7,} adm  {r.drug}")
print(f"\n## MULTI-CLASS (matches >1 of the 3 top classes): {len(multi)} strings")
for _, r in multi.iterrows():
    print(f"   {r.drug}  (antidiab={r.antidiab}, antihtn={r.antihtn}, lipid={r.lipid})")

# ---- per-admission med flags + "alone" counts ----
d2c = ds[["drug", "insulin", "metformin", "oral_ad", "bb", "nonbb_htn", "lipid"]].copy()
d2c["oral_ad_nonmet"] = d2c.oral_ad & ~d2c.metformin
con.register("d2c", d2c)
medh = con.execute(f"""
  SELECT p.hadm_id,
     max(insulin::INT) insulin, max(metformin::INT) metformin,
     max(oral_ad::INT) oral_ad, max(oral_ad_nonmet::INT) oral_ad_nonmet,
     max(bb::INT) bb, max(nonbb_htn::INT) nonbb_htn, max(lipid::INT) lipid
  FROM read_csv_auto('{RX}') p JOIN d2c ON lower(p.drug)=d2c.drug
  SEMI JOIN lh ON p.hadm_id=lh.hadm_id
  WHERE (p.route IS NULL OR (upper(p.route) NOT LIKE '%EYE%' AND upper(p.route) NOT IN ('OU','OS','OD')))
  GROUP BY p.hadm_id
""").fetchdf()

pop = con.execute(f"SELECT hadm_id, gender, lab_HbA1c, lab_Glucose, omr_SBP, omr_DBP FROM read_parquet('{CLEAN_POP}')").fetchdf()
codes = con.execute(f"""
  WITH d AS (SELECT hadm_id, trim(icd_code) code, icd_version
             FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
  SELECT hadm_id,
    max(CASE WHEN (icd_version=10 AND (code LIKE 'E11%' OR code='R7303'))
             OR (icd_version=9 AND (code LIKE '250%' OR code LIKE '7902%')) THEN 1 ELSE 0 END) dysgly_code,
    max(CASE WHEN (icd_version=10 AND regexp_matches(code,'^I1[0-6]'))
             OR (icd_version=9 AND regexp_matches(code,'^40[1-5]')) THEN 1 ELSE 0 END) htn_code
  FROM d GROUP BY hadm_id
""").fetchdf()
m = pop.merge(medh, on="hadm_id", how="left").merge(codes, on="hadm_id", how="left").fillna(0)
for c in ["insulin", "metformin", "oral_ad", "oral_ad_nonmet", "bb", "nonbb_htn", "lipid",
          "dysgly_code", "htn_code"]:
    m[c] = m[c].astype(bool)
crit2_nonmed = m.dysgly_code | (m.lab_HbA1c >= 5.7) | (m.lab_Glucose >= 100)
crit3_nonmed = m.htn_code | (m.omr_SBP >= 130) | (m.omr_DBP >= 85)
insulin_alone = m.insulin & ~m.oral_ad & ~crit2_nonmed
metformin_alone = m.metformin & ~m.oral_ad_nonmet & ~m.insulin & ~crit2_nonmed
bb_alone = m.bb & ~m.nonbb_htn & ~crit3_nonmed
print("\n" + "=" * 74 + "\n\"MEETS CRITERION BY THIS ALONE\" (the numbers you asked for)\n" + "=" * 74)
print(f"  Criterion 3 (HTN) by BETA-BLOCKER alone (no other antihtn med, no HTN code, no BP≥130/85): "
      f"{int(bb_alone.sum()):,} admissions")
print(f"  Criterion 2 (dysglycemia) by INSULIN alone (no oral antidiabetic, no dysgly code/lab): "
      f"{int(insulin_alone.sum()):,} admissions")
print(f"  Criterion 2 by METFORMIN alone (no other antidiabetic, no dysgly code/lab): "
      f"{int(metformin_alone.sum()):,} admissions")
print("\nSTOP — approve the drug lists (and rule on beta-blockers / insulin / metformin) "
      "before I proceed to Step 2.")
