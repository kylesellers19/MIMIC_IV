#!/usr/bin/env python3
"""run_2026-09-19 Phase 8.2 + 8.3 — DEVELOPMENT DIAGNOSTIC (label and input share a source; not an accuracy estimate).
8.2 Heads on frozen Bio_ClinicalBERT admission vectors (variant S; U if present): L2 logistic regression and LightGBM; the
    better on DEV OOF (AUPRC) is kept. 8.3 Notes-augmented model: CatBoost on FS-B + first 64 principal components of the
    embeddings (PCA fit inside training folds); if no embeddings, FS-B + the TF-IDF (variant S) OOF logit instead.
Subsample DEV/TEST only; GOLD_HOLDOUT scored, never fitted. Missing shards (job stopped early) simply reduce the subsample."""
import argparse, json, os, sys, time, warnings
import numpy as np, pandas as pd, duckdb
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import statsmodels.api as sm
sys.path.insert(0, os.getcwd()); warnings.filterwarnings("ignore")
_ap = argparse.ArgumentParser(); _ap.add_argument("--smoke", action="store_true",
    help="validate the code path on whatever shards exist; write to the scratch folder, not to the run's outputs")
ARGS, _ = _ap.parse_known_args()
SEED = 20260919; REPS = 50 if ARGS.smoke else 500; THREADS = 4
TXT = "data/processed/run_2026-09-19_notes_text/subsample.parquet"; EMB = "data/processed/notes_embeddings_v1"; PREDDIR = "data/processed/run_2026-09-19_scratch/preds_smoke" if ARGS.smoke else "data/processed/run_2026-09-19_preds"
RESULTS = "data/processed/run_2026-09-19_scratch/aim1b_notes_arm_SMOKE.json" if ARGS.smoke else "docs/run_2026-09-19/results/aim1b_notes_arm.json"
os.makedirs(PREDDIR, exist_ok=True)
FEAT = "data/processed/run_2026-09-19_features.parquet"; CAT = ["gender", "admission_type", "admission_location", "icd_era", "marital_status"]
t0 = time.time(); log = lambda s: print(f"[{time.time()-t0:6.0f}s] {s}", flush=True)
def logit(p): p = np.clip(p, 1e-6, 1 - 1e-6); return np.log(p / (1 - p))
def sigmoid(z): return 1 / (1 + np.exp(-z))
def calib(y, p):
    z = logit(p)
    try: return float(sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=z).fit().params[0]), float(sm.GLM(y, sm.add_constant(z), family=sm.families.Binomial()).fit().params[1])
    except Exception: return np.nan, np.nan
def metrics(y, p, subj=None, reps=0):
    out = {"n": int(len(y)), "pos": int(y.sum()), "auroc": float(roc_auc_score(y, p)), "auprc": float(average_precision_score(y, p)), "brier": float(brier_score_loss(y, p))}
    out["cal_intercept"], out["cal_slope"] = calib(y, p)
    if reps and subj is not None:
        codes, inv = np.unique(subj, return_inverse=True); NS = len(codes); r2 = np.random.default_rng(SEED); b = {"auroc": [], "auprc": [], "brier": []}
        for _ in range(reps):
            w = r2.multinomial(NS, np.full(NS, 1 / NS))[inv].astype(float)
            if (w * y).sum() == 0: continue
            b["auroc"].append(roc_auc_score(y, p, sample_weight=w)); b["auprc"].append(average_precision_score(y, p, sample_weight=w)); b["brier"].append(brier_score_loss(y, p, sample_weight=w))
        for k, v in b.items(): out[f"{k}_ci"] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    return out
def load_emb(variant):
    d = f"{EMB}/{variant}"
    if not os.path.exists(f"{d}/index.parquet"): return None
    idx = pd.read_parquet(f"{d}/index.parquet"); parts = []
    for sh, g in idx.groupby("shard"):
        f = f"{d}/shard_{sh:04d}.npy"
        if os.path.exists(f): arr = np.load(f); parts.append(pd.DataFrame({"hadm_id": g.hadm_id.values, "_row": [arr[r].astype(np.float32) for r in g.row]}))
    if not parts: return None
    e = pd.concat(parts, ignore_index=True); return e
sub = pd.read_parquet(TXT, columns=["hadm_id", "subject_id", "partition", "fold", "note_b", "code_positive"]); sub["y"] = sub.note_b.astype(int)
res = {"header": "DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.", "seed": SEED, "embed_heads": {}, "augmented": {}}
preds = {"oof": {}, "test": {}, "gold": {}}
emb_used = None
for variant in ["S", "U"]:
    e = load_emb(variant)
    if e is None: res["embed_heads"][variant] = "no embeddings available"; continue
    d = sub.merge(e, on="hadm_id"); X = np.stack(d._row.values); mu, sd = X[d.partition == "DEV"].mean(0), X[d.partition == "DEV"].std(0) + 1e-6; X = (X - mu) / sd
    DEV, TEST, GOLD = (d.partition == "DEV").to_numpy(), (d.partition == "TEST").to_numpy(), (d.partition == "GOLD_HOLDOUT").to_numpy()
    r = {"n_embedded": int(len(d)), "n_dev": int(DEV.sum()), "n_test": int(TEST.sum()), "n_gold": int(GOLD.sum()), "heads": {}}
    y = d.y.to_numpy(); folds = d.fold.to_numpy()
    for head in ["lr", "lgbm"]:
        def mk():
            if head == "lr": return LogisticRegression(C=0.05, max_iter=3000, random_state=SEED)
            from lightgbm import LGBMClassifier; return LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31, subsample=0.8, subsample_freq=1, colsample_bytree=0.5, n_jobs=THREADS, random_state=SEED, verbose=-1)
        p = np.full(len(d), np.nan)
        for k in range(5):
            tr = DEV & (folds != k); va = DEV & (folds == k); m = mk().fit(X[tr], y[tr]); p[va] = m.predict_proba(X[va])[:, 1]
        r["heads"][head] = {"oof": metrics(y[DEV], np.clip(p[DEV], 1e-6, 1 - 1e-6))}; log(f"{variant} {head} OOF AUROC {r['heads'][head]['oof']['auroc']:.4f} AUPRC {r['heads'][head]['oof']['auprc']:.4f}")
        m = mk().fit(X[DEV], y[DEV]); pt = np.clip(m.predict_proba(X[TEST])[:, 1], 1e-6, 1 - 1e-6); pg = np.clip(m.predict_proba(X[GOLD])[:, 1], 1e-6, 1 - 1e-6)
        r["heads"][head]["test"] = metrics(y[TEST], pt, d.subject_id.to_numpy()[TEST], REPS); neg = (d.code_positive.to_numpy()[TEST] == False); r["heads"][head]["test_code_negative_only"] = metrics(y[TEST][neg], pt[neg])
        preds["oof"][f"embed|{variant}|{head}"] = pd.Series(p[DEV], index=d.hadm_id[DEV]); preds["test"][f"embed|{variant}|{head}"] = pd.Series(pt, index=d.hadm_id[TEST]); preds["gold"][f"embed|{variant}|{head}"] = pd.Series(pg, index=d.hadm_id[GOLD])
    r["kept"] = max(r["heads"], key=lambda h: r["heads"][h]["oof"]["auprc"]); res["embed_heads"][variant] = r
    if variant == "S": emb_used = (d, X, DEV, TEST, GOLD)
# ---- 8.3 notes-augmented ----
con = duckdb.connect(); cls = json.load(open("docs/run_2026-09-19/results/feature_classification.json")); FSB = cls["clinical"]
feat = con.execute(f"SELECT hadm_id, {', '.join(FSB)} FROM read_parquet('{FEAT}')").fetchdf()
for c in CAT: feat[c] = feat[c].astype("category")
from catboost import CatBoostClassifier
def cb(spw): return CatBoostClassifier(iterations=200 if ARGS.smoke else 800, learning_rate=0.06, depth=6, l2_leaf_reg=3, thread_count=THREADS, verbose=0, random_seed=SEED, early_stopping_rounds=50, scale_pos_weight=spw, allow_writing_files=False)
if emb_used is not None:
    d, X, DEV, TEST, GOLD = emb_used; extra_name = "PC1-64 of Bio_ClinicalBERT (variant S)"
    def extra(tr_mask, ap_mask):  # PCA fit inside the training mask
        pca = PCA(n_components=64, random_state=SEED).fit(X[tr_mask]); return pca.transform(X[ap_mask])
else:
    tf = pd.read_parquet(f"{PREDDIR}/notes_tfidf_oof.parquet")[["hadm_id", "tfidf|S|unweighted"]]; tft = pd.read_parquet(f"{PREDDIR}/notes_tfidf_test.parquet")[["hadm_id", "tfidf|S|unweighted"]]; tfg = pd.read_parquet(f"{PREDDIR}/notes_tfidf_gold.parquet")[["hadm_id", "tfidf|S|unweighted"]]
    allp = pd.concat([tf, tft, tfg]).rename(columns={"tfidf|S|unweighted": "tfidf_logit"}); allp["tfidf_logit"] = logit(allp.tfidf_logit.to_numpy())
    d = sub.merge(allp, on="hadm_id"); DEV, TEST, GOLD = (d.partition == "DEV").to_numpy(), (d.partition == "TEST").to_numpy(), (d.partition == "GOLD_HOLDOUT").to_numpy(); extra_name = "TF-IDF (variant S) OOF logit"
    def extra(tr_mask, ap_mask): return d.tfidf_logit.to_numpy()[ap_mask].reshape(-1, 1)
d = d.reset_index(drop=True); F = d[["hadm_id"]].merge(feat, on="hadm_id", how="left"); y = d.y.to_numpy(); folds = d.fold.to_numpy(); subj = d.subject_id.to_numpy()
def build(mask_tr, mask_ap):
    Z = extra(mask_tr, mask_ap); Xf = F.loc[mask_ap, FSB].reset_index(drop=True); Zf = pd.DataFrame(Z, columns=[f"nz_{i}" for i in range(Z.shape[1])]); return pd.concat([Xf, Zf], axis=1)
res["augmented"] = {"extra_features": extra_name, "n_dev": int(DEV.sum()), "n_test": int(TEST.sum()), "variants": {}}
rng = np.random.default_rng(SEED)
def fitcb(mask_tr, weighted):
    tr_idx = np.where(mask_tr)[0]; s = np.unique(subj[tr_idx]); es = set(rng.choice(s, max(1, len(s) // 10), replace=False)); inner = np.isin(subj, list(es)) & mask_tr; core = mask_tr & ~inner
    spw = float((y[core] == 0).sum() / max(1, (y[core] == 1).sum())) if weighted else None
    Xc, Xi = build(core, core), build(core, inner); m = cb(spw); m.fit(Xc, y[core], cat_features=[c for c in FSB if c in CAT], eval_set=(Xi, y[inner])); return m, spw, core
for weighted in [False, True]:
    p = np.full(len(d), np.nan); pc = np.full(len(d), np.nan)
    for k in range(5):
        tr = DEV & (folds != k); va = DEV & (folds == k); m, spw, core = fitcb(tr, weighted); pk = np.clip(m.predict_proba(build(core, va))[:, 1], 1e-6, 1 - 1e-6); p[va] = pk
        if weighted: pc[va] = sigmoid(logit(pk) - np.log(spw))
    nm = "weighted" if weighted else "unweighted"; v = {"oof": metrics(y[DEV], p[DEV])}
    m, spw, core = fitcb(DEV, weighted); pt = np.clip(m.predict_proba(build(core, TEST))[:, 1], 1e-6, 1 - 1e-6); pg = np.clip(m.predict_proba(build(core, GOLD))[:, 1], 1e-6, 1 - 1e-6)
    v["test"] = metrics(y[TEST], pt, subj[TEST], REPS); neg = d.code_positive.to_numpy()[TEST] == False; v["test_code_negative_only"] = metrics(y[TEST][neg], pt[neg]); res["augmented"]["variants"][nm] = v
    preds["oof"][f"aug|FS-B+notes|{nm}"] = pd.Series(p[DEV], index=d.hadm_id[DEV]); preds["test"][f"aug|FS-B+notes|{nm}"] = pd.Series(pt, index=d.hadm_id[TEST]); preds["gold"][f"aug|FS-B+notes|{nm}"] = pd.Series(pg, index=d.hadm_id[GOLD])
    if weighted:
        v2 = {"oof": metrics(y[DEV], pc[DEV]), "test": metrics(y[TEST], sigmoid(logit(pt) - np.log(spw)), subj[TEST], REPS)}; res["augmented"]["variants"]["weighted+corrected"] = v2
        preds["oof"]["aug|FS-B+notes|weighted+corrected"] = pd.Series(pc[DEV], index=d.hadm_id[DEV]); preds["test"]["aug|FS-B+notes|weighted+corrected"] = pd.Series(sigmoid(logit(pt) - np.log(spw)), index=d.hadm_id[TEST]); preds["gold"]["aug|FS-B+notes|weighted+corrected"] = pd.Series(sigmoid(logit(pg) - np.log(spw)), index=d.hadm_id[GOLD])
    _mdir = PREDDIR if ARGS.smoke else "models/run_2026-09-19"   # smoke artifacts stay in scratch
    m.save_model(f"{_mdir}/aug_FS-B_notes_{nm}{'_SMOKE' if ARGS.smoke else ''}.cbm"); log(f"augmented {nm} OOF AUROC {v['oof']['auroc']:.4f} TEST AUROC {v['test']['auroc']:.4f}")
for part in ["oof", "test", "gold"]:
    pd.DataFrame(preds[part]).rename_axis("hadm_id").reset_index().to_parquet(f"{PREDDIR}/notes_arm_{part}.parquet", index=False)
res["runtime_s"] = round(time.time() - t0); json.dump(res, open(RESULTS, "w"), indent=1); log("DONE")
