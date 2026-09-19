#!/usr/bin/env python3
"""Aim 1b gold-standard evaluation harness (run_2026-09-19 Phase 9.3).

Given a completed adjudication file (schema of docs/adjudication/data_dictionary.md: review_id, primary_response, ...)
and a locked prediction file (hadm_id + one column per arm/variant), computes inverse-probability-weighted AUROC, AUPRC,
Brier, calibration intercept and slope with stratified (within-cell) bootstrap CIs; the same restricted to the recovery zone
(cell code-/note+); silver-minus-gold deltas (silver = note_b on the same charts); subgroup results where supported.
Positive = Definite or Probable (draft collapse). "Insufficient information" is handled both ways (excluded / negative).

Usage:
  scripts/run0919_env.sh scripts/aim1b_evaluate_gold.py --adjudication <file.csv|.xlsx> --predictions <preds.parquet> --out <results.json>
  scripts/run0919_env.sh scripts/aim1b_evaluate_gold.py --synthetic   # plumbing test with SYNTHETIC labels (scratch only)
No patient-level row is ever printed."""
import argparse, json, os, sys, warnings
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import statsmodels.api as sm
sys.path.insert(0, os.getcwd()); warnings.filterwarnings("ignore")
KEY = "data/processed/aim1a_sample.parquet"; FRAME = "data/processed/aim1a_frame.parquet"; SEED = 20260919
POSITIVE = {"Definite", "Probable"}; NEG = {"Possible", "Absent"}; INSUFF = "Insufficient information"
SUBGROUP_MIN = 20   # positives and negatives required within a subgroup of a 400-chart sample (stated in the doc)

def load_adj(path):
    a = pd.read_excel(path) if path.endswith(".xlsx") else pd.read_csv(path)
    a = a[["review_id", "primary_response"]].dropna(subset=["primary_response"]); return a

def wmetrics(y, p, w):
    z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    out = {"n": int(len(y)), "pos": int(y.sum()), "auroc": float(roc_auc_score(y, p, sample_weight=w)) if 0 < y.sum() < len(y) else np.nan,
           "auprc": float(average_precision_score(y, p, sample_weight=w)) if y.sum() > 0 else np.nan, "brier": float(brier_score_loss(y, p, sample_weight=w))}
    try:
        out["cal_intercept"] = float(sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=z, freq_weights=w).fit().params[0])
        out["cal_slope"] = float(sm.GLM(y, sm.add_constant(z), family=sm.families.Binomial(), freq_weights=w).fit().params[1])
    except Exception: out["cal_intercept"], out["cal_slope"] = np.nan, np.nan
    return out

def strat_boot(d, col, reps, rng):
    b = {k: [] for k in ["auroc", "auprc", "brier", "cal_intercept", "cal_slope"]}
    for _ in range(reps):
        idx = np.concatenate([rng.choice(g.index.to_numpy(), len(g), replace=True) for _, g in d.groupby("cell")])
        s = d.loc[idx]; m = wmetrics(s.y.to_numpy(), s[col].to_numpy(), s.weight.to_numpy())
        for k in b: b[k].append(m[k])
    return {f"{k}_ci": [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in b.items()}

def evaluate(adj, preds, reps=500, subgroups=None):
    key = pd.read_parquet(KEY); fr = pd.read_parquet(FRAME, columns=["hadm_id", "note_b", "race", "insurance", "gender", "age"])
    d = key.merge(adj, on="review_id").merge(preds, on="hadm_id").merge(fr, on="hadm_id")
    arms = [c for c in preds.columns if c != "hadm_id"]; rng = np.random.default_rng(SEED); res = {"arms": {}, "n_adjudicated": int(len(d)), "n_insufficient": int((d.primary_response == INSUFF).sum())}
    for handling in ["insufficient_excluded", "insufficient_negative"]:
        dd = d[d.primary_response != INSUFF].copy() if handling == "insufficient_excluded" else d.copy()
        dd["y"] = dd.primary_response.isin(POSITIVE).astype(int); dd = dd.reset_index(drop=True)
        for arm in arms:
            r = {"all": wmetrics(dd.y.to_numpy(), dd[arm].to_numpy(), dd.weight.to_numpy())}; r["all"].update(strat_boot(dd, arm, reps, rng))
            rz = dd[dd.cell == "code-/note+"].reset_index(drop=True)
            r["recovery_zone"] = wmetrics(rz.y.to_numpy(), rz[arm].to_numpy(), rz.weight.to_numpy()); r["recovery_zone"].update(strat_boot(rz, arm, reps, rng))
            sil = wmetrics(dd.note_b.astype(int).to_numpy(), dd[arm].to_numpy(), dd.weight.to_numpy())
            r["silver_on_same_charts"] = sil; r["silver_minus_gold"] = {k: (sil[k] - r["all"][k]) for k in ["auroc", "auprc", "brier"]}
            sg = {}
            for var in (subgroups or ["insurance", "gender"]):
                sg[var] = {}
                for lev, g in dd.groupby(var):
                    if g.y.sum() >= SUBGROUP_MIN and (1 - g.y).sum() >= SUBGROUP_MIN: sg[var][str(lev)] = wmetrics(g.y.to_numpy(), g[arm].to_numpy(), g.weight.to_numpy())
                    else: sg[var][str(lev)] = "not estimable"
            r["subgroups"] = sg; res["arms"].setdefault(arm, {})[handling] = r
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--adjudication"); ap.add_argument("--predictions"); ap.add_argument("--out"); ap.add_argument("--synthetic", action="store_true"); ap.add_argument("--reps", type=int, default=500)
    a = ap.parse_args()
    if a.synthetic:
        os.makedirs("data/processed/run_2026-09-19_scratch", exist_ok=True)
        key = pd.read_parquet(KEY); fr = pd.read_parquet(FRAME, columns=["hadm_id", "note_b"]); rng = np.random.default_rng(SEED)
        d = key.merge(fr, on="hadm_id"); flip = rng.random(len(d)) < 0.15; y = d.note_b.astype(bool) ^ flip
        resp = np.where(y, rng.choice(["Definite", "Probable"], len(d)), rng.choice(["Absent", "Possible"], len(d))); resp[rng.random(len(d)) < 0.03] = INSUFF
        adj = pd.DataFrame({"review_id": d.review_id, "primary_response": resp}); adj.to_csv("data/processed/run_2026-09-19_scratch/SYNTHETIC_adjudication.csv", index=False)
        predfile = a.predictions or "data/processed/run_2026-09-19_preds/structured_gold.parquet"
        preds = pd.read_parquet(predfile); preds = preds[["hadm_id"] + [c for c in preds.columns if c != "hadm_id"][:3]]
        res = evaluate(adj, preds, reps=a.reps); res["HEADER"] = "SYNTHETIC LABELS — plumbing test only; not a finding"
        out = "data/processed/run_2026-09-19_scratch/SYNTHETIC_gold_eval.json"; json.dump(res, open(out, "w"), indent=1)
        print(json.dumps({"SYNTHETIC": True, "n": res["n_adjudicated"], "arms": list(res["arms"]), "example_auroc_all": {k: round(v["insufficient_excluded"]["all"]["auroc"], 3) for k, v in res["arms"].items()}}))
    else:
        res = evaluate(load_adj(a.adjudication), pd.read_parquet(a.predictions), reps=a.reps); json.dump(res, open(a.out, "w"), indent=1); print(f"wrote {a.out}")
