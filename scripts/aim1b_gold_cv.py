#!/usr/bin/env python3
"""Aim 1b gold cross-validation scaffold (run_2026-09-19 Phase 9.4) — the second notes-arm training option, kept runnable.
Repeated, stratified (by adjudicated label), SUBJECT-level cross-validation within the 400 adjudicated charts using frozen
Bio_ClinicalBERT embeddings (variant S) and a light L2 logistic head, carrying the cell sampling weights as sample weights.
Reports weighted AUROC/AUPRC across repeats. --synthetic runs plumbing on SYNTHETIC labels (scratch only).
Usage: scripts/run0919_env.sh scripts/aim1b_gold_cv.py --adjudication <file> [--variant S] [--repeats 5] [--folds 5]"""
import argparse, json, os, sys, glob, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score
sys.path.insert(0, os.getcwd()); warnings.filterwarnings("ignore")
KEY = "data/processed/aim1a_sample.parquet"; EMB = "data/processed/notes_embeddings_v1"; SEED = 20260919
POSITIVE = {"Definite", "Probable"}; INSUFF = "Insufficient information"

def load_embeddings(variant, hadm_ids):
    idx = pd.read_parquet(f"{EMB}/{variant}/index.parquet"); idx = idx[idx.hadm_id.isin(set(hadm_ids))]
    E = np.zeros((len(idx), 1536), dtype=np.float32); rows = {}
    for sh, g in idx.groupby("shard"):
        f = f"{EMB}/{variant}/shard_{sh:04d}.npy"
        if not os.path.exists(f): continue
        arr = np.load(f)
        for i, (h, r) in enumerate(zip(g.hadm_id, g.row)): rows[h] = arr[r].astype(np.float32)
    return rows

def run(adj, variant="S", repeats=5, folds=5, C=0.1):
    key = pd.read_parquet(KEY); d = key.merge(adj, on="review_id"); d = d[d.primary_response != INSUFF].copy()
    d["y"] = d.primary_response.isin(POSITIVE).astype(int)
    rows = load_embeddings(variant, d.hadm_id); d = d[d.hadm_id.isin(rows)].reset_index(drop=True)
    X = np.stack([rows[h] for h in d.hadm_id]); X = (X - X.mean(0)) / (X.std(0) + 1e-6); y = d.y.to_numpy(); w = d.weight.to_numpy(); g = d.subject_id.to_numpy()
    res = {"n": int(len(d)), "pos": int(y.sum()), "variant": variant, "repeats": repeats, "folds": folds, "C": C, "auroc_weighted": [], "auprc_weighted": []}
    for r in range(repeats):
        p = np.zeros(len(d)); skf = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=SEED + r)
        for tr, te in skf.split(X, y, groups=g):
            m = LogisticRegression(C=C, max_iter=2000).fit(X[tr], y[tr], sample_weight=w[tr]); p[te] = m.predict_proba(X[te])[:, 1]
        res["auroc_weighted"].append(float(roc_auc_score(y, p, sample_weight=w))); res["auprc_weighted"].append(float(average_precision_score(y, p, sample_weight=w)))
    res["auroc_mean_sd"] = [float(np.mean(res["auroc_weighted"])), float(np.std(res["auroc_weighted"]))]; res["auprc_mean_sd"] = [float(np.mean(res["auprc_weighted"])), float(np.std(res["auprc_weighted"]))]
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--adjudication"); ap.add_argument("--variant", default="S"); ap.add_argument("--repeats", type=int, default=5); ap.add_argument("--folds", type=int, default=5); ap.add_argument("--synthetic", action="store_true"); ap.add_argument("--out")
    a = ap.parse_args()
    if a.synthetic:
        adj = pd.read_csv("data/processed/run_2026-09-19_scratch/SYNTHETIC_adjudication.csv")
        res = run(adj, a.variant, a.repeats, a.folds); res["HEADER"] = "SYNTHETIC LABELS — plumbing test only; not a finding"
        json.dump(res, open("data/processed/run_2026-09-19_scratch/SYNTHETIC_gold_cv.json", "w"), indent=1); print(json.dumps({"SYNTHETIC": True, "n": res["n"], "auroc_mean_sd": res["auroc_mean_sd"]}))
    else:
        adj = pd.read_excel(a.adjudication) if a.adjudication.endswith(".xlsx") else pd.read_csv(a.adjudication)
        res = run(adj[["review_id", "primary_response"]].dropna(), a.variant, a.repeats, a.folds); json.dump(res, open(a.out, "w"), indent=1); print(f"wrote {a.out}")
