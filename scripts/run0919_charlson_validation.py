#!/usr/bin/env python3
"""run_2026-09-19 Phase 4.2 — validate the project's hand-written Quan-2005 Charlson against comorbidipy,
and build charlson_noliver (both liver categories removed) for modeling.
Writes data/processed/run_2026-09-19_charlson.parquet (untracked: hadm_id, charlson_project, charlson_noliver,
17 category flags) and docs/run_2026-09-19/results/charlson_validation.json (aggregates)."""
import json, os, sys, re
import numpy as np, pandas as pd, duckdb
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP
# import the project's crosswalk WITHOUT running the module (it executes on import)
src = open("scripts/comorbid_cluster.py").read()
ns = {}
exec(src[src.index("CH = {"):src.index("def rex(")], ns)
CH = ns["CH"]
def rex(prefixes): return "^(" + "|".join(prefixes) + ")"
con = duckdb.connect(); con.execute("SET memory_limit='16GB'")
sel = [f"max(CASE WHEN (icd_version=10 AND regexp_matches(code,'{rex(p10)}')) OR (icd_version=9 AND regexp_matches(code,'{rex(p9)}')) THEN 1 ELSE 0 END) AS {cat}"
       for cat, (wt, p10, p9) in CH.items()]
cats = con.execute(f"""WITH d AS (SELECT hadm_id, trim(icd_code) AS code, icd_version FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
  SELECT hadm_id, {', '.join(sel)} FROM d WHERE hadm_id IN (SELECT hadm_id FROM read_parquet('{CLEAN_POP}')) GROUP BY hadm_id""").fetchdf().set_index("hadm_id")
cats.loc[cats.dm_comp == 1, "dm"] = 0; cats.loc[cats.severe_liver == 1, "mild_liver"] = 0; cats.loc[cats.mets == 1, "malig"] = 0
cats["charlson_project"] = sum(CH[c][0] * cats[c] for c in CH)
cats["charlson_noliver"] = sum(CH[c][0] * cats[c] for c in CH if c not in ("mild_liver", "severe_liver"))
# --- verify the leak: do the phenotype codes fall in mild_liver? ---
leak = {}
for ver, code in [(10, "K760"), (10, "K7581"), (9, "5718"), (9, "5719")]:
    p10, p9 = CH["mild_liver"][1], CH["mild_liver"][2]
    leak[f"{ver}:{code}"] = bool(re.match(rex(p10 if ver == 10 else p9), code))
# --- comorbidipy ---
res = {"leak_check_mild_liver_matches_phenotype_codes": leak, "population_admissions": int(len(cats))}
try:
    import polars as pl
    from comorbidipy import comorbidity
    from comorbidipy.calculators.comorbidity import WeightingVariant, ICDVersion, MappingVariant
    res["comorbidipy_weighting_options"] = [w.value for w in WeightingVariant]
    wname = "charlson" if any(w.value == "charlson" for w in WeightingVariant) else "quan"
    W = [w for w in WeightingVariant if w.value == wname][0]
    dxr = con.execute(f"""SELECT hadm_id, trim(icd_code) AS code, icd_version FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}})
                          WHERE hadm_id IN (SELECT hadm_id FROM read_parquet('{CLEAN_POP}'))""").fetchdf()
    parts = []
    for ver, icd in [(9, ICDVersion.ICD9), (10, ICDVersion.ICD10)]:
        sub = dxr[dxr.icd_version == ver][["hadm_id", "code"]]
        out = comorbidity(pl.from_pandas(sub), id_col="hadm_id", code_col="code", score="charlson", icd=icd, variant=MappingVariant.QUAN, weighting=W, assign0=True).to_pandas()
        parts.append(out)
    cp = pd.concat(parts, ignore_index=True).groupby("hadm_id").max()  # an admission has one version; max is a no-op safeguard
    res["comorbidipy_columns"] = list(cp.columns)
    score_col = "comorbidity_score"
    j = cats[["charlson_project", "charlson_noliver"]].join(cp, how="inner")
    res["compared_admissions"] = int(len(j))
    diff = (j.charlson_project - j[score_col])
    res["weighting_used"] = wname
    res["pct_identical"] = round(100 * float((diff == 0).mean()), 3)
    res["difference_distribution"] = {str(int(k)): int(v) for k, v in diff.value_counts().sort_index().items()}
    res["mean_project"] = round(float(j.charlson_project.mean()), 4); res["mean_comorbidipy"] = round(float(j[score_col].mean()), 4)
    # per-category agreement — map names heuristically by shared substrings
    catmap = {"mi": ["mi", "myocardial"], "chf": ["chf", "heart_failure", "congestive"], "pvd": ["pvd", "peripheral"], "cevd": ["cevd", "cerebrovascular"],
              "dementia": ["dementia"], "copd": ["copd", "pulmonary", "chronic_pulmonary"], "rheum": ["rheum", "connective"], "pud": ["pud", "peptic"],
              "mild_liver": ["mld", "mild_liver", "liver_mild"], "dm": ["diab", "dm"], "dm_comp": ["diabwc", "dm_comp", "diabetes_complicat"], "hemi": ["hp", "hemi", "paraplegia"],
              "renal": ["rend", "renal"], "malig": ["canc", "malig"], "severe_liver": ["msld", "severe_liver", "liver_severe"], "mets": ["metacanc", "mets", "metast"], "hiv": ["aids", "hiv"]}
    percat = {}
    cols = [c for c in cp.columns if c != score_col]
    for cat, keys in catmap.items():
        match = [c for c in cols if any(c.lower() == k or c.lower().startswith(k) for k in keys)]
        # prefer exact-ish: avoid 'dm' matching 'dm_comp' etc.
        if cat == "dm": match = [c for c in match if "comp" not in c.lower() and "wc" not in c.lower()]
        if cat == "mild_liver": match = [c for c in match if "s" != c.lower()[:1] or c.lower().startswith("mild")]
        if cat == "malig": match = [c for c in match if "meta" not in c.lower()]
        if match:
            c = match[0]; a = cats[cat].reindex(j.index).astype(int); b = j[c].astype(int)
            percat[cat] = {"comorbidipy_col": c, "pct_agree": round(100 * float((a == b).mean()), 3), "n_project": int(a.sum()), "n_comorbidipy": int(b.sum())}
        else:
            percat[cat] = {"comorbidipy_col": None}
    res["per_category"] = percat
    # SMD recovery-zone vs concordant
    fr = con.execute("SELECT hadm_id, code_positive, note_b FROM read_parquet('data/processed/aim1a_frame.parquet')").fetchdf().set_index("hadm_id")
    jj = j.join(fr, how="inner")
    def smd(a, b):
        d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2); return float((a.mean() - b.mean()) / d)
    rz = jj[(~jj.code_positive) & jj.note_b]; cc = jj[jj.code_positive & jj.note_b]
    res["smd_recovery_vs_concordant"] = {"project": round(smd(rz.charlson_project, cc.charlson_project), 4),
                                         "comorbidipy": round(smd(rz[score_col], cc[score_col]), 4),
                                         "project_noliver": round(smd(rz.charlson_noliver, cc.charlson_noliver), 4)}
except Exception as e:
    res["comorbidipy_error"] = type(e).__name__
    res["comorbidipy_error_msg"] = str(e)[:300]
# structural self-check on synthetic codes (both versions) — always run
sc = {}
for cat, (wt, p10, p9) in CH.items():
    sc[cat] = {"weight": wt, "fires_icd10_on_first_prefix": bool(re.match(rex(p10), p10[0] + "0")), "fires_icd9_on_first_prefix": bool(re.match(rex(p9), p9[0] + "0"))}
res["structural_self_check"] = sc
res["weights_match_charlson1987"] = {c: CH[c][0] for c in CH} == {"mi":1,"chf":1,"pvd":1,"cevd":1,"dementia":1,"copd":1,"rheum":1,"pud":1,"mild_liver":1,"dm":1,"dm_comp":2,"hemi":2,"renal":2,"malig":2,"severe_liver":3,"mets":6,"hiv":6}
res["noliver_summary"] = {"mean_project": round(float(cats.charlson_project.mean()), 4), "mean_noliver": round(float(cats.charlson_noliver.mean()), 4),
                          "pct_admissions_changed": round(100 * float((cats.charlson_project != cats.charlson_noliver).mean()), 3)}
cats.reset_index()[["hadm_id", "charlson_project", "charlson_noliver"] + list(CH)].to_parquet("data/processed/run_2026-09-19_charlson.parquet", index=False)
json.dump(res, open("docs/run_2026-09-19/results/charlson_validation.json", "w"), indent=1)
print(json.dumps({k: res.get(k) for k in ["leak_check_mild_liver_matches_phenotype_codes", "pct_identical", "difference_distribution", "smd_recovery_vs_concordant", "comorbidipy_error", "comorbidipy_error_msg", "weighting_used", "comorbidipy_weighting_options", "noliver_summary"]}, indent=1))
