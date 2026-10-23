#!/usr/bin/env python3
"""run_2026-09-19 Phase 8.1 — DEVELOPMENT DIAGNOSTIC: TF-IDF (word 1–2-grams, min_df=100, sublinear tf) + L2 logistic
regression on text variants U/M/S of the Phase 3 subsample. Vocabulary fit inside training folds only. GOLD_HOLDOUT scored, never fitted.
Label and input share a source (the silver label is a lexical rule over the same text): NOT an accuracy estimate.
Writes results JSON, OOF/TEST/GOLD predictions (untracked), and top coefficients (alphabetic tokens, df>=100).
Refuses to run once the GOLD_HOLDOUT predictions are locked (scripts/run0919_lock_guard.py) unless --force."""
import argparse, json, os, sys, time, re, warnings
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import statsmodels.api as sm
sys.path.insert(0, os.getcwd()); warnings.filterwarnings("ignore")
from scripts.run0919_lock_guard import refuse_if_locked
_ap = argparse.ArgumentParser(); _ap.add_argument("--force", action="store_true", help="overwrite GOLD predictions recorded in the lock"); ARGS = _ap.parse_args()
refuse_if_locked(["notes_tfidf_gold.parquet"], ARGS.force)
SEED = 20260919; REPS = 500; C = 1.0
TXT = "data/processed/run_2026-09-19_notes_text/subsample.parquet"; PREDDIR = "data/processed/run_2026-09-19_preds"; os.makedirs(PREDDIR, exist_ok=True)
t0 = time.time(); log = lambda s: print(f"[{time.time()-t0:6.0f}s] {s}", flush=True)
df = pd.read_parquet(TXT); df["y"] = df.note_b.astype(int)
DEV = df[df.partition == "DEV"].reset_index(drop=True); TEST = df[df.partition == "TEST"].reset_index(drop=True); GOLD = df[df.partition == "GOLD_HOLDOUT"].reset_index(drop=True)
def logit(p): return np.log(p / (1 - p))
def sigmoid(z): return 1 / (1 + np.exp(-z))
def calib(y, p):
    z = logit(np.clip(p, 1e-6, 1 - 1e-6))
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
def vec(): return TfidfVectorizer(ngram_range=(1, 2), min_df=100, sublinear_tf=True, max_features=300000, dtype=np.float32)
def fit_lr(X, y, weighted):
    return LogisticRegression(C=C, penalty="l2", solver="liblinear", max_iter=2000, class_weight="balanced" if weighted else None, random_state=SEED).fit(X, y)
res = {"header": "DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.", "seed": SEED, "C": C, "sizes": {"DEV": len(DEV), "TEST": len(TEST), "GOLD": len(GOLD)}, "variants": {}}
oof_all, te_all, go_all = {"hadm_id": DEV.hadm_id.values}, {"hadm_id": TEST.hadm_id.values}, {"hadm_id": GOLD.hadm_id.values}
for var in ["U", "M", "S"]:
    col = f"text_{var}"; r = {"oof": {}, "test": {}, "test_code_negative_only": {}, "top_terms": {}}
    for weighted in [False, True]:
        p = np.full(len(DEV), np.nan); pc = np.full(len(DEV), np.nan)
        for k in range(5):
            tr = DEV.fold != k; v = vec(); Xtr = v.fit_transform(DEV.loc[tr, col].fillna("")); Xva = v.transform(DEV.loc[~tr, col].fillna(""))
            m = fit_lr(Xtr, DEV.y[tr], weighted); pk = np.clip(m.predict_proba(Xva)[:, 1], 1e-6, 1 - 1e-6); p[~tr] = pk
            if weighted: w = float((DEV.y[tr] == 0).sum() / (DEV.y[tr] == 1).sum()); pc[~tr] = sigmoid(logit(pk) - np.log(w))
        nm = "weighted" if weighted else "unweighted"; r["oof"][nm] = metrics(DEV.y.to_numpy(), p); oof_all[f"tfidf|{var}|{nm}"] = p
        if weighted: r["oof"]["weighted+corrected"] = metrics(DEV.y.to_numpy(), pc); oof_all[f"tfidf|{var}|weighted+corrected"] = pc
        log(f"{var} {nm} OOF AUROC {r['oof'][nm]['auroc']:.4f} AUPRC {r['oof'][nm]['auprc']:.4f}")
    v = vec(); Xd = v.fit_transform(DEV[col].fillna("")); Xt = v.transform(TEST[col].fillna("")); Xg = v.transform(GOLD[col].fillna(""))
    dfreq = np.asarray((Xd > 0).sum(0)).ravel(); vocab = np.array(v.get_feature_names_out())
    for weighted in [False, True]:
        m = fit_lr(Xd, DEV.y, weighted); pt = np.clip(m.predict_proba(Xt)[:, 1], 1e-6, 1 - 1e-6); pg = np.clip(m.predict_proba(Xg)[:, 1], 1e-6, 1 - 1e-6)
        nm = "weighted" if weighted else "unweighted"; neg = (TEST.code_positive == False).to_numpy()
        r["test"][nm] = metrics(TEST.y.to_numpy(), pt, TEST.subject_id.to_numpy(), REPS); r["test_code_negative_only"][nm] = metrics(TEST.y.to_numpy()[neg], pt[neg])
        te_all[f"tfidf|{var}|{nm}"] = pt; go_all[f"tfidf|{var}|{nm}"] = pg
        if weighted:
            w = float((DEV.y == 0).sum() / (DEV.y == 1).sum()); ptc, pgc = sigmoid(logit(pt) - np.log(w)), sigmoid(logit(pg) - np.log(w))
            r["test"]["weighted+corrected"] = metrics(TEST.y.to_numpy(), ptc, TEST.subject_id.to_numpy(), REPS); r["test_code_negative_only"]["weighted+corrected"] = metrics(TEST.y.to_numpy()[neg], ptc[neg])
            te_all[f"tfidf|{var}|weighted+corrected"] = ptc; go_all[f"tfidf|{var}|weighted+corrected"] = pgc
        if not weighted:
            coef = m.coef_.ravel(); ok = np.array([bool(re.fullmatch(r"[a-z]+( [a-z]+)?", t)) for t in vocab]) & (dfreq >= 100)
            order = np.argsort(coef); pos = [i for i in order[::-1] if ok[i]][:25]; negs = [i for i in order if ok[i]][:25]
            r["top_terms"] = {"positive": [{"term": vocab[i], "coef": round(float(coef[i]), 3), "df": int(dfreq[i])} for i in pos],
                              "negative": [{"term": vocab[i], "coef": round(float(coef[i]), 3), "df": int(dfreq[i])} for i in negs], "vocab_size": int(len(vocab))}
        log(f"{var} {nm} TEST AUROC {r['test'][nm]['auroc']:.4f} AUPRC {r['test'][nm]['auprc']:.4f} slope {r['test'][nm]['cal_slope']:.3f}")
    res["variants"][var] = r
pd.DataFrame(oof_all).to_parquet(f"{PREDDIR}/notes_tfidf_oof.parquet", index=False); pd.DataFrame(te_all).to_parquet(f"{PREDDIR}/notes_tfidf_test.parquet", index=False); pd.DataFrame(go_all).to_parquet(f"{PREDDIR}/notes_tfidf_gold.parquet", index=False)
res["runtime_s"] = round(time.time() - t0); json.dump(res, open("docs/run_2026-09-19/results/aim1b_notes_tfidf.json", "w"), indent=1); log("DONE")
