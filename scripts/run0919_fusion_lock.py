#!/usr/bin/env python3
"""run_2026-09-19 Phase 9.1 (stacked fusion) and 9.2 (locked GOLD_HOLDOUT predictions).
Layer 0: structured FS-B (best-calibrated imbalance variant on DEV OOF; FS-A as sensitivity) and the notes model (variant S:
the better of TF-IDF and the embedding head on DEV OOF). Layer 1: logistic regression on the two OOF logits, fit on the
subsample's DEV admissions. Code status is never an input. Arms evaluated on the same subsample TEST admissions with paired
subject-cluster bootstrap differences. Then every GOLD_HOLDOUT admission is scored by every arm/variant and the file is
hashed (SHA-256) with the model files — the audit trail that predictions predate the adjudication."""
import json, os, sys, time, hashlib, glob, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import statsmodels.api as sm
sys.path.insert(0, os.getcwd()); warnings.filterwarnings("ignore")
SEED = 20260919; REPS = 500; PREDDIR = "data/processed/run_2026-09-19_preds"; R = "docs/run_2026-09-19/results"
t0 = time.time(); log = lambda s: print(f"[{time.time()-t0:6.0f}s] {s}", flush=True)
def logit(p): p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); return np.log(p / (1 - p))
def calib(y, p):
    z = logit(p)
    try: return float(sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=z).fit().params[0]), float(sm.GLM(y, sm.add_constant(z), family=sm.families.Binomial()).fit().params[1])
    except Exception: return np.nan, np.nan
def metrics(y, p):
    out = {"n": int(len(y)), "pos": int(y.sum()), "auroc": float(roc_auc_score(y, p)), "auprc": float(average_precision_score(y, p)), "brier": float(brier_score_loss(y, p))}; out["cal_intercept"], out["cal_slope"] = calib(y, p); return out
sub = pd.read_parquet("data/processed/run_2026-09-19_notes_text/subsample.parquet", columns=["hadm_id", "subject_id", "partition", "fold", "note_b", "code_positive"]); sub["y"] = sub.note_b.astype(int)
st_oof = pd.read_parquet(f"{PREDDIR}/structured_oof.parquet"); st_te = pd.read_parquet(f"{PREDDIR}/structured_test.parquet"); st_go = pd.read_parquet(f"{PREDDIR}/structured_gold.parquet")
S = json.load(open(f"{R}/aim1b_structured.json")); N = json.load(open(f"{R}/aim1b_notes_tfidf.json"))
def best_cal(prefix):
    cands = {k: v for k, v in S["oof"].items() if k.startswith(prefix)}
    return min(cands, key=lambda k: abs(cands[k]["cal_intercept"]) + abs(cands[k]["cal_slope"] - 1))
L0 = {"structured_FS-B": best_cal("cat|FS-B|"), "structured_FS-A": best_cal("cat|FS-A|")}
tf_oof = pd.read_parquet(f"{PREDDIR}/notes_tfidf_oof.parquet"); tf_te = pd.read_parquet(f"{PREDDIR}/notes_tfidf_test.parquet"); tf_go = pd.read_parquet(f"{PREDDIR}/notes_tfidf_gold.parquet")
notes_col = "tfidf|S|unweighted"; notes_src = "tfidf"; note_tables = (tf_oof, tf_te, tf_go)
if os.path.exists(f"{PREDDIR}/notes_arm_oof.parquet"):
    NA = json.load(open(f"{R}/aim1b_notes_arm.json")); na_oof = pd.read_parquet(f"{PREDDIR}/notes_arm_oof.parquet"); na_te = pd.read_parquet(f"{PREDDIR}/notes_arm_test.parquet"); na_go = pd.read_parquet(f"{PREDDIR}/notes_arm_gold.parquet")
    eh = NA["embed_heads"].get("S")
    if isinstance(eh, dict):
        col = f"embed|S|{eh['kept']}"
        if eh["heads"][eh["kept"]]["oof"]["auprc"] > N["variants"]["S"]["oof"]["unweighted"]["auprc"]: notes_col, notes_src, note_tables = col, "embedding head", (na_oof, na_te, na_go)
else: NA = None; na_oof = na_te = na_go = None
res = {"header": "Silver label — known error; not adjudicated truth; final performance requires the gold standard. Rows including the notes model carry the circularity caveat (label and input share a source).",
       "layer0": {**L0, "notes": notes_col, "notes_source": notes_src}, "arms_test": {}, "paired_differences": {}, "fusion_coefficients": {}}
def frame(part, st, nt, extra=None):
    d = sub[sub.partition == part][["hadm_id", "subject_id", "y", "code_positive"]].merge(st, on="hadm_id", how="inner").merge(nt, on="hadm_id", how="inner")
    if extra is not None: d = d.merge(extra, on="hadm_id", how="left")
    return d.reset_index(drop=True)
D = frame("DEV", st_oof, note_tables[0], na_oof if na_oof is not None and notes_src == "tfidf" else None); T = frame("TEST", st_te, note_tables[1], na_te if na_te is not None and notes_src == "tfidf" else None)
arms = {}
for sens, skey in [("primary", "structured_FS-B"), ("sensitivity_FS-A", "structured_FS-A")]:
    sc = L0[skey]; Xd = np.column_stack([logit(D[sc]), logit(D[notes_col])]); Xt = np.column_stack([logit(T[sc]), logit(T[notes_col])])
    meta = LogisticRegression(C=1e6, max_iter=1000).fit(Xd, D.y); pf = meta.predict_proba(Xt)[:, 1]
    res["fusion_coefficients"][sens] = {"intercept": float(meta.intercept_[0]), "w_structured": float(meta.coef_[0][0]), "w_notes": float(meta.coef_[0][1])}
    arms[f"fusion ({sens})"] = pf; arms[f"structured ({sens}: {sc})"] = T[sc].to_numpy()
arms[f"notes ({notes_col})"] = T[notes_col].to_numpy()
if na_te is not None:
    for c in [c for c in na_te.columns if c.startswith("aug|")]:
        if c in T.columns: arms[f"notes-augmented ({c})"] = T[c].to_numpy()
        else: arms[f"notes-augmented ({c})"] = T[["hadm_id"]].merge(na_te[["hadm_id", c]], on="hadm_id", how="left")[c].to_numpy()
y = T.y.to_numpy(); subj = T.subject_id.to_numpy(); neg = (T.code_positive == False).to_numpy()
for k, p in arms.items():
    ok = ~np.isnan(p); res["arms_test"][k] = {"all": metrics(y[ok], p[ok]), "code_negative_only": metrics(y[ok & neg], p[ok & neg])}
# paired bootstrap differences vs the primary structured arm
codes, inv = np.unique(subj, return_inverse=True); NS = len(codes); rng = np.random.default_rng(SEED); base = f"structured (primary: {L0['structured_FS-B']})"
diffs = {k: {"auroc": [], "auprc": [], "brier": []} for k in arms if k != base}
for _ in range(REPS):
    w = rng.multinomial(NS, np.full(NS, 1 / NS))[inv].astype(float)
    b = {m: f(y, arms[base], sample_weight=w) for m, f in [("auroc", roc_auc_score), ("auprc", average_precision_score), ("brier", brier_score_loss)]}
    for k in diffs:
        p = arms[k]; ok = ~np.isnan(p)
        for m, f in [("auroc", roc_auc_score), ("auprc", average_precision_score), ("brier", brier_score_loss)]:
            diffs[k][m].append(f(y[ok], p[ok], sample_weight=w[ok]) - b[m])
for k, v in diffs.items(): res["paired_differences"][f"{k} minus {base}"] = {m: {"mean": float(np.mean(x)), "ci": [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]} for m, x in v.items()}
log("fusion evaluated")
# ---- 9.2 lock GOLD predictions ----
G = sub[sub.partition == "GOLD_HOLDOUT"][["hadm_id"]].merge(st_go, on="hadm_id", how="left").merge(tf_go, on="hadm_id", how="left")
if na_go is not None: G = G.merge(na_go, on="hadm_id", how="left")
for sens, skey in [("primary", "structured_FS-B"), ("sensitivity_FS-A", "structured_FS-A")]:
    sc = L0[skey]; c = res["fusion_coefficients"][sens]; G[f"fusion|{sens}"] = 1 / (1 + np.exp(-(c["intercept"] + c["w_structured"] * logit(G[sc]) + c["w_notes"] * logit(G[notes_col]))))
out = "data/processed/gold_holdout_predictions_v1.parquet"; G.to_parquet(out, index=False)
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
lock = {"file": out, "sha256": sha(out), "rows": int(len(G)), "columns": [c for c in G.columns if c != "hadm_id"], "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": {os.path.basename(f): {"sha256": sha(f), "bytes": os.path.getsize(f)}
                   for f in sorted(glob.glob("models/run_2026-09-19/*")) if "_SMOKE" not in f},
        "excluded_from_manifest": [os.path.basename(f) for f in sorted(glob.glob("models/run_2026-09-19/*")) if "_SMOKE" in f],
        "prediction_files": {os.path.basename(f): sha(f) for f in sorted(glob.glob(f"{PREDDIR}/*_gold.parquet"))}}
json.dump(lock, open(f"{R}/locked_predictions.json", "w"), indent=1); json.dump(res, open(f"{R}/aim1b_fusion.json", "w"), indent=1)
L = ["# Aim 1b — locked GOLD_HOLDOUT predictions (run_2026-09-19, Phase 9.2)\n", f"Produced by `scripts/run0919_fusion_lock.py`; hashes in `docs/run_2026-09-19/results/locked_predictions.json`.\n",
     "Every GOLD_HOLDOUT admission (all admissions of every subject in the 400-chart sample or the 20-chart training set) was scored by every arm and variant **before any adjudication exists**. The file below is untracked (credentialed derivative); its SHA-256 and the model-file hashes are recorded here so that, when the gold labels arrive, it can be shown that no model was tuned against them.\n",
     f"- File: `{out}` · rows {lock['rows']:,} · written {lock['written_utc']}", f"- SHA-256: `{lock['sha256']}`", f"- Columns ({len(lock['columns'])}): " + ", ".join(f"`{c}`" for c in lock["columns"]), "", "| model file | bytes | SHA-256 |", "| --- | --: | --- |"]
for k, v in lock["models"].items(): L.append(f"| {k} | {v['bytes']:,} | `{v['sha256']}` |")
L += ["", "Per-arm gold prediction files:", ""] + [f"- `{k}`: `{v}`" for k, v in lock["prediction_files"].items()]
open("docs/aim1b_locked_predictions.md", "w").write("\n".join(L) + "\n"); log("DONE")
