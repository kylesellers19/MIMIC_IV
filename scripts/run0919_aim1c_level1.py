#!/usr/bin/env python3
"""run_2026-09-19 Phase 5 — Aim 1c level 1: equity of recovery at the computable stage.
Cell counts first; recovery share (B/(A+B)) and corroboration share (A/(A+C)) by stratum with subject-cluster
bootstrap CIs; floors (B>=11; A+C>=11); one exploratory GEE among note-positive admissions (covariates fixed in
docs/analysis_plan_prespecified.md amendment g). Writes docs/run_2026-09-19/results/aim1c_level1.json,
docs/aim1c_level1.md, docs/tables/aim1c_*.md (+ .csv on disk, git-ignored)."""
import json, os, sys, time, warnings
import duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.getcwd())
from scripts.masld_config import CLEAN_POP, LOCKED_POP, DATA, RACE_NONINFORMATIVE
warnings.filterwarnings("ignore")
REPS = 500; FLOOR = 11; SEED = 20260919; WIDE = 20.0   # CI width in percentage points beyond which no claim is supported (Tier 1 threshold)
IDX = "data/processed/run_2026-09-19_notes_index"
ENCOUNTER_CHAR = {"UNKNOWN", "UNABLE TO OBTAIN", "PATIENT DECLINED TO ANSWER"}
t0 = time.time()
con = duckdb.connect(); con.execute("SET memory_limit='16GB'")
df = con.execute(f"""SELECT f.hadm_id, f.subject_id, f.code_positive, f.note_b, f.age, f.gender, f.race, f.insurance, f.language,
      f.admission_type, f.miss_lab_ALT, f.miss_lab_HbA1c, f.miss_lab_Triglycerides, f.miss_lab_HDL, c.icd_era, l.admittime,
      m.cmrf_unasc_all, m.cmrf_ge1
      FROM read_parquet('data/processed/aim1a_frame.parquet') f JOIN read_parquet('{CLEAN_POP}') c USING (hadm_id)
      JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id) LEFT JOIN read_parquet('data/processed/cmrf.parquet') m USING (hadm_id)""").fetchdf()
df["language"] = df.language.fillna("(missing)"); df["insurance"] = df.insurance.fillna("(missing)")
df["age_band"] = pd.cut(df.age, [-1, 17, 39, 54, 64, 74, 88, 200], labels=["<18", "18-39", "40-54", "55-64", "65-74", "75-88", "89+"]).astype(str)
# 571.9-only flag
dx = con.execute(f"""SELECT hadm_id, max(CASE WHEN icd_version=9 AND trim(icd_code)='5719' THEN 1 ELSE 0 END) AS h5719,
   max(CASE WHEN (icd_version=10 AND trim(icd_code) IN ('K760','K7581')) OR (icd_version=9 AND trim(icd_code)='5718') THEN 1 ELSE 0 END) AS hoth
   FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}) GROUP BY hadm_id""").fetchdf()
df = df.merge(dx, on="hadm_id", how="left").fillna({"h5719": 0, "hoth": 0})
df["code_pos_no5719"] = df.code_positive & ~((df.h5719 == 1) & (df.hoth == 0))
# note sources + liver-inclusive imaging in window, from the per-note index
dcs = con.execute(f"SELECT hadm_id, max(a_pos::INT) AS src_dc FROM read_parquet('{IDX}/discharge.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
ri = con.execute(f"SELECT hadm_id, max(a_pos::INT) AS src_rad_inp, max(liver_incl::INT) AS liv_inp FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
df = df.merge(dcs, on="hadm_id", how="left").merge(ri, on="hadm_id", how="left").fillna({"src_dc": 0, "src_rad_inp": 0, "liv_inp": 0})
op = con.execute(f"SELECT subject_id, charttime, a_pos, liver_incl FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NULL AND (a_pos OR liver_incl)").fetchdf()
m = df[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
d = (pd.to_datetime(m.charttime) - pd.to_datetime(m.admittime)).dt.total_seconds() / 86400.0; w = (d >= -365) & (d <= 30)
df["src_rad_out"] = df.hadm_id.isin(set(m[w & m.a_pos].hadm_id)).astype(int)
df["liv_win"] = (df.liv_inp.astype(bool) | df.hadm_id.isin(set(m[w & m.liver_incl].hadm_id))).astype(int)
cp = df.code_positive.astype(bool); nt = df.note_b.astype(bool)
df["cA"] = (cp & nt).astype(int); df["cB"] = (~cp & nt).astype(int); df["cC"] = (cp & ~nt).astype(int); df["cD"] = (~cp & ~nt).astype(int)
cp2 = df.code_pos_no5719.astype(bool)
df["cA2"] = (cp2 & nt).astype(int); df["cB2"] = (~cp2 & nt).astype(int); df["cC2"] = (cp2 & ~nt).astype(int)
subj_codes, subj_idx = np.unique(df.subject_id.to_numpy(), return_inverse=True); NS = len(subj_codes)
rng = np.random.default_rng(SEED)
W = rng.multinomial(NS, np.full(NS, 1.0 / NS), size=REPS).astype(np.float64)   # subject-cluster bootstrap weights (REPS x NS)

def stratum_table(var):
    lv, li = np.unique(df[var].astype(str).to_numpy(), return_inverse=True)
    out = []
    mats = {}
    for c in ["cA", "cB", "cC", "cD", "cA2", "cB2", "cC2"]:
        M = np.zeros((NS, len(lv))); np.add.at(M, (subj_idx, li), df[c].to_numpy()); mats[c] = M
    A, B, C, D = (mats[c].sum(0) for c in ["cA", "cB", "cC", "cD"])
    bA, bB, bC = (W @ mats[c] for c in ["cA", "cB", "cC"])
    bA2, bB2, bC2 = (W @ mats[c] for c in ["cA2", "cB2", "cC2"])
    with np.errstate(divide="ignore", invalid="ignore"):
        rec = 100 * bB / (bA + bB); cor = 100 * bA / (bA + bC); rec2 = 100 * bB2 / (bA2 + bB2)
    for j, name in enumerate(lv):
        r = {"stratum": name, "A": int(A[j]), "B": int(B[j]), "C": int(C[j]), "D": int(D[j]),
             "encounter_characteristic": name in ENCOUNTER_CHAR}
        if B[j] >= FLOOR:
            lo, hi = np.nanpercentile(rec[:, j], [2.5, 97.5]); r.update({"recovery_share_pct": round(100 * B[j] / (A[j] + B[j]), 1), "rec_ci": [round(lo, 1), round(hi, 1)], "rec_ci_width": round(hi - lo, 1), "rec_claim_supported": bool(hi - lo <= WIDE)})
        else:
            r.update({"recovery_share_pct": None, "rec_note": f"not analyzable (B < {FLOOR})"})
        if A[j] + C[j] >= FLOOR:
            lo, hi = np.nanpercentile(cor[:, j], [2.5, 97.5]); r.update({"corroboration_share_pct": round(100 * A[j] / (A[j] + C[j]), 1), "cor_ci": [round(lo, 1), round(hi, 1)], "cor_ci_width": round(hi - lo, 1), "cor_claim_supported": bool(hi - lo <= WIDE)})
        else:
            r.update({"corroboration_share_pct": None, "cor_note": f"not analyzable (A+C < {FLOOR})"})
        A2, B2 = mats["cA2"].sum(0)[j], mats["cB2"].sum(0)[j]
        if B2 >= FLOOR:
            lo, hi = np.nanpercentile(rec2[:, j], [2.5, 97.5]); r.update({"recovery_share_no5719_pct": round(100 * B2 / (A2 + B2), 1), "rec_no5719_ci": [round(lo, 1), round(hi, 1)]})
        # one-vs-rest SMD of the coding rate among note-positive (A/(A+B)) — descriptive contrast
        n_in = A[j] + B[j]; n_out = (A.sum() + B.sum()) - n_in
        if n_in >= FLOOR and n_out >= FLOOR:
            p1 = A[j] / n_in; p0 = (A.sum() - A[j]) / n_out; den = np.sqrt((p1 * (1 - p1) + p0 * (1 - p0)) / 2)
            r["smd_coding_rate_vs_rest"] = round(float((p1 - p0) / den), 3) if den > 0 else None
        # mechanism measures
        sel = (li == j)
        g = df[sel]
        r["mech"] = {"n": int(sel.sum()), "ALT_avail_pct": round(100 * float((~g.miss_lab_ALT).mean()), 1), "HbA1c_avail_pct": round(100 * float((~g.miss_lab_HbA1c).mean()), 1),
                     "TG_avail_pct": round(100 * float((~g.miss_lab_Triglycerides).mean()), 1), "HDL_avail_pct": round(100 * float((~g.miss_lab_HDL).mean()), 1),
                     "liver_imaging_in_window_pct": round(100 * float(g.liv_win.mean()), 1),
                     "cmrf_unascertainable_all_pct": round(100 * float(g.cmrf_unasc_all.fillna(False).astype(bool).mean()), 1)}
        out.append(r)
    return out

res = {"reps": REPS, "floor": FLOOR, "seed": SEED, "wide_ci_threshold_pp": WIDE, "population": int(len(df)), "subjects": NS, "strata": {}}
for var in ["race", "insurance", "gender", "language", "age_band"]:
    res["strata"][var] = stratum_table(var); print(f"{var} done {time.time()-t0:,.0f}s", flush=True)

# ---- exploratory GEE among note-positive admissions ----
import statsmodels.api as sm, statsmodels.formula.api as smf
pos = df[nt].copy().sort_values("subject_id")
pos["y"] = pos.code_positive.astype(int)
for c in ["race", "insurance", "gender", "age_band", "admission_type", "icd_era"]:
    pos[c] = pos[c].astype(str)
def ref_sorted(col):  # reference = largest category
    order = pos[col].value_counts().index.tolist(); return pd.Categorical(pos[col], categories=order)
gee_res = {"label": "EXPLORATORY", "outcome": "code-positive among note-positive admissions", "n": int(len(pos))}
def fit(data, note):
    for c in ["race", "insurance", "gender", "age_band", "admission_type", "icd_era"]:
        data[c] = pd.Categorical(data[c], categories=data[c].value_counts().index.tolist())
    mod = smf.gee("y ~ race + insurance + gender + age_band + admission_type + icd_era + src_dc + src_rad_inp + src_rad_out",
                  groups="subject_id", data=data, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable())
    r = mod.fit(maxiter=100)
    if not getattr(r, "converged", True): raise RuntimeError("GEE did not converge")
    ci = r.conf_int(); rows = []
    for k in r.params.index:
        if k == "Intercept": continue
        rows.append({"term": k, "aOR": round(float(np.exp(r.params[k])), 3), "ci_lo": round(float(np.exp(ci.loc[k, 0])), 3), "ci_hi": round(float(np.exp(ci.loc[k, 1])), 3)})
    return {"note": note, "n": int(len(data)), "terms": rows, "reference_levels": {c: str(data[c].cat.categories[0]) for c in ["race", "insurance", "gender", "age_band", "admission_type", "icd_era"]}}
try:
    gee_res.update(fit(pos.copy(), "all categories"))
except Exception as e:
    gee_res["full_model_error"] = type(e).__name__
    keep = pos.copy()
    for c in ["race", "insurance", "language", "age_band", "admission_type"]:
        vc = keep[c].value_counts(); keep = keep[keep[c].isin(vc[vc >= 100].index)]
    try:
        gee_res.update(fit(keep, "restricted to categories with >=100 note-positive admissions"))
    except Exception as e2:
        gee_res["restricted_model_error"] = type(e2).__name__
res["gee_exploratory"] = gee_res
json.dump(res, open("docs/run_2026-09-19/results/aim1c_level1.json", "w"), indent=1)
print(f"GEE: {gee_res.get('note', gee_res)} — total {time.time()-t0:,.0f}s", flush=True)

# ---- docs ----
os.makedirs("docs/tables", exist_ok=True)
def fmt(v): return "—" if v is None else (f"{v}" if not isinstance(v, list) else f"{v[0]}–{v[1]}")
L = ["# Aim 1c, level 1 — equity of recovery at the computable stage (run_2026-09-19)\n",
     "Produced by `scripts/run0919_aim1c_level1.py`; every number is read from `docs/run_2026-09-19/results/aim1c_level1.json`. Pre-specification: `docs/analysis_plan_prespecified.md` (H1c; amendment g). Definition (b), v1.1.0, −365/+30 outpatient window.\n",
     "**What is measured.** Recovery share = B ÷ (A + B): among note-positive admissions, the share with no MASLD code. Corroboration share = A ÷ (A + C): among code-positive admissions, the share whose notes also document steatosis. Both are computable-stage quantities about *documentation and coding*, not adjudicated disease. 95% CIs are subject-cluster bootstraps "
     f"({REPS} replicates; a subject's admissions are resampled together because one person can contribute several). Floors: no recovery share where B < {FLOOR}; no corroboration share where A + C < {FLOOR}; such strata are declared non-analyzable, not merged. A CI wider than {WIDE:.0f} percentage points is marked as too wide to support a claim (an analyst threshold, stated here so it can be argued with). No p-values. The SMD column is the one-versus-rest standardized difference in the coding rate among note-positive admissions (A ÷ (A + B)), a descriptive contrast.\n",
     "Levels 2 and 3 of the audit (weighted PPV by stratum against the gold standard; model calibration by stratum) require the adjudication and the models and are not attempted here.\n",
     "UNKNOWN, UNABLE TO OBTAIN and PATIENT DECLINED TO ANSWER are reported but are **encounter characteristics, not population groups** (marked †). Ages ≥ 89 are recoded to 91 in MIMIC-IV, so the 89+ band is an aggregate.\n"]
for var, rows in res["strata"].items():
    L += [f"## By {var}\n", "Cell counts first:\n", f"| {var} | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |", "| --- | --: | --: | --: | --: |"]
    for r in sorted(rows, key=lambda x: -(x["A"] + x["B"] + x["C"] + x["D"])):
        L.append(f"| {r['stratum']}{' †' if r['encounter_characteristic'] else ''} | {r['A']:,} | {r['B']:,} | {r['C']:,} | {r['D']:,} |")
    L += ["", "Shares (analyzable strata only):\n", f"| {var} | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |", "| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |"]
    for r in sorted(rows, key=lambda x: -(x["A"] + x["B"] + x["C"] + x["D"])):
        if r.get("recovery_share_pct") is None and r.get("corroboration_share_pct") is None:
            L.append(f"| {r['stratum']}{' †' if r['encounter_characteristic'] else ''} | not analyzable | | | | not analyzable | | | | | |"); continue
        L.append(f"| {r['stratum']}{' †' if r['encounter_characteristic'] else ''} | {fmt(r.get('recovery_share_pct'))} | {fmt(r.get('rec_ci'))} | {fmt(r.get('rec_ci_width'))} | {('yes' if r.get('rec_claim_supported') else 'no — too wide') if r.get('recovery_share_pct') is not None else 'n/a'} "
                 f"| {fmt(r.get('corroboration_share_pct'))} | {fmt(r.get('cor_ci'))} | {fmt(r.get('cor_ci_width'))} | {('yes' if r.get('cor_claim_supported') else 'no — too wide') if r.get('corroboration_share_pct') is not None else 'n/a'} | {fmt(r.get('smd_coding_rate_vs_rest'))} | {fmt(r.get('recovery_share_no5719_pct'))} ({fmt(r.get('rec_no5719_ci'))}) |")
    L += ["", "Mechanism measures (all admissions in the stratum):\n", f"| {var} | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |", "| --- | --: | --: | --: | --: | --: | --: | --: |"]
    for r in sorted(rows, key=lambda x: -x["mech"]["n"]):
        mm = r["mech"]; L.append(f"| {r['stratum']} | {mm['n']:,} | {mm['ALT_avail_pct']} | {mm['HbA1c_avail_pct']} | {mm['TG_avail_pct']} | {mm['HDL_avail_pct']} | {mm['liver_imaging_in_window_pct']} | {mm['cmrf_unascertainable_all_pct']} |")
    L.append("")
    tbl = pd.DataFrame([{k: (v if not isinstance(v, (list, dict)) else json.dumps(v)) for k, v in r.items()} for r in rows])
    tbl.to_csv(f"docs/tables/aim1c_level1_{var}.csv", index=False)
    with open(f"docs/tables/aim1c_level1_{var}.md", "w") as fh:
        fh.write(f"# Aim 1c level 1 — by {var} (run_2026-09-19)\n\nSource: `docs/run_2026-09-19/results/aim1c_level1.json`.\n\n" + "\n".join(L[-(len(rows) * 3 + 20):]) + "\n")
g = res["gee_exploratory"]
L += ["## EXPLORATORY adjusted model (GEE) — among note-positive admissions, outcome = code-positive\n",
      f"**Exploratory.** Covariates fixed before fitting (amendment g): race, insurance, sex, age band, admission type, ICD version of the admission, note source (discharge / inpatient radiology / outpatient radiology). GEE with a binomial link, exchangeable working correlation, clustered on subject. Diagnosis count and laboratory availability are deliberately not adjusted for: they are the proposed mechanism. Fit: {g.get('note', g.get('full_model_error', 'failed'))}; n = {g.get('n')}. Reference levels: {g.get('reference_levels')}.\n"]
if "terms" in g:
    L += ["| term | adjusted OR | 95% CI |", "| --- | --: | --- |"]
    for t in g["terms"]: L.append(f"| {t['term']} | {t['aOR']} | {t['ci_lo']}–{t['ci_hi']} |")
else:
    L.append(f"Model did not fit: {g}")
L += ["", "*Exploratory adjusted odds ratios describe association in the computable data; they are not estimates of adjudicated under-coding by group.*"]
open("docs/aim1c_level1.md", "w").write("\n".join(L) + "\n")
print("wrote docs/aim1c_level1.md", flush=True)
