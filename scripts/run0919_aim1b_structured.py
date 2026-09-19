#!/usr/bin/env python3
"""run_2026-09-19 Phase 7 — Aim 1b structured arm. Silver label (note_b). GOLD_HOLDOUT never fitted on.
Learners: CatBoost (primary), XGBoost, LightGBM. Feature sets FS-A (all), FS-B (clinical), FS-AVAIL (availability/volume).
Imbalance variants: unweighted; weighted (scale_pos_weight = neg/pos in the training fold); weighted+corrected (weighted
model's logit shifted by -log(w) — no extra fit). Tuning: random configs, subject-level CV on DEV with early stopping on an
inner 10% subject split; TEST touched once. Writes results JSON, OOF/TEST/GOLD predictions (untracked), models (untracked)."""
import json, os, sys, time, warnings
import numpy as np, pandas as pd, duckdb
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import statsmodels.api as sm
sys.path.insert(0, os.getcwd())
from scripts.masld_config import SPLITS_V1, LOCKED_POP
warnings.filterwarnings("ignore")
SEED = 20260919; THREADS = 4; N_CFG = 4; REPS = 500; TUNE_FOLDS = 3
FEAT = "data/processed/run_2026-09-19_features.parquet"; IDX = "data/processed/run_2026-09-19_notes_index"
MODELDIR = "models/run_2026-09-19"; PREDDIR = "data/processed/run_2026-09-19_preds"; RES = "docs/run_2026-09-19/results/aim1b_structured.json"
os.makedirs(MODELDIR, exist_ok=True); os.makedirs(PREDDIR, exist_ok=True)
t0 = time.time(); log = lambda s: print(f"[{time.time()-t0:7.0f}s] {s}", flush=True)
cls = json.load(open("docs/run_2026-09-19/results/feature_classification.json"))
FS = {"FS-A": cls["clinical"] + cls["availability"], "FS-B": cls["clinical"], "FS-AVAIL": cls["availability"]}
CAT = ["gender", "admission_type", "admission_location", "icd_era", "marital_status"]
con = duckdb.connect()
df = con.execute(f"""SELECT x.*, s.partition, s.fold, f.note_b, f.code_positive, f.age AS age_int, l.admittime
                     FROM read_parquet('{FEAT}') x JOIN read_parquet('{SPLITS_V1}') s USING (hadm_id)
                     JOIN read_parquet('data/processed/aim1a_frame.parquet') f USING (hadm_id) JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""").fetchdf()
df["y"] = df.note_b.astype(int)
df["age_band"] = pd.cut(df.age_int, [-1, 17, 39, 54, 64, 74, 88, 200], labels=["<18", "18-39", "40-54", "55-64", "65-74", "75-88", "89+"]).astype(str)
for c in CAT: df[c] = df[c].astype("category")
# imaging-observed population (≥1 liver-inclusive study, inpatient or outpatient −365/+30) — the Phase-7 secondary population
op = con.execute(f"SELECT subject_id, charttime FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NULL AND liver_incl").fetchdf()
mm = df[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
d = (pd.to_datetime(mm.charttime) - pd.to_datetime(mm.admittime)).dt.total_seconds() / 86400.0
df["imaging_observed"] = (df.liver_imaging_inp > 0) | df.hadm_id.isin(set(mm[(d >= -365) & (d <= 30)].hadm_id))
DEV = df[df.partition == "DEV"].reset_index(drop=True); TEST = df[df.partition == "TEST"].reset_index(drop=True); GOLD = df[df.partition == "GOLD_HOLDOUT"].reset_index(drop=True)
log(f"DEV {len(DEV):,} TEST {len(TEST):,} GOLD {len(GOLD):,}; imaging-observed DEV {int(DEV.imaging_observed.sum()):,} TEST {int(TEST.imaging_observed.sum()):,}")
rng = np.random.default_rng(SEED)

def inner_split(tr):
    subj = tr.subject_id.unique(); es = set(rng.choice(subj, max(1, int(0.1 * len(subj))), replace=False))
    m = tr.subject_id.isin(es); return tr[~m], tr[m]

def make(learner, cfg, spw):
    if learner == "cat":
        from catboost import CatBoostClassifier
        return CatBoostClassifier(iterations=1000, learning_rate=cfg["lr"], depth=cfg["depth"], l2_leaf_reg=cfg["l2"], thread_count=THREADS, verbose=0,
                                  random_seed=SEED, eval_metric="Logloss", early_stopping_rounds=50, scale_pos_weight=spw, allow_writing_files=False)
    if learner == "xgb":
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=1000, learning_rate=cfg["lr"], max_depth=cfg["depth"], min_child_weight=cfg["mcw"], subsample=0.8, colsample_bytree=0.8,
                             reg_lambda=cfg["l2"], tree_method="hist", enable_categorical=True, n_jobs=THREADS, random_state=SEED, eval_metric="logloss", early_stopping_rounds=50,
                             scale_pos_weight=spw if spw else 1.0)
    from lightgbm import LGBMClassifier
    return LGBMClassifier(n_estimators=1000, learning_rate=cfg["lr"], num_leaves=2 ** cfg["depth"] - 1, min_child_samples=cfg["mcw"] * 5, subsample=0.8, subsample_freq=1,
                          colsample_bytree=0.8, reg_lambda=cfg["l2"], n_jobs=THREADS, random_state=SEED, verbose=-1, scale_pos_weight=spw if spw else 1.0)

def fit(learner, cfg, tr, feats, weighted):
    a, b = inner_split(tr); spw = float((a.y == 0).sum() / max(1, (a.y == 1).sum())) if weighted else None
    m = make(learner, cfg, spw)
    if learner == "cat":
        m.fit(a[feats], a.y, cat_features=[f for f in feats if f in CAT], eval_set=(b[feats], b.y))
    elif learner == "xgb":
        m.fit(a[feats], a.y, eval_set=[(b[feats], b.y)], verbose=False)
    else:
        import lightgbm as lgb
        m.fit(a[feats], a.y, eval_set=[(b[feats], b.y)], callbacks=[lgb.early_stopping(50, verbose=False)])
    return m, spw

def predict(m, X): return np.clip(m.predict_proba(X)[:, 1], 1e-6, 1 - 1e-6)
def logit(p): return np.log(p / (1 - p))
def sigmoid(z): return 1 / (1 + np.exp(-z))
def corrected(p, spw): return sigmoid(logit(p) - np.log(spw))

def calib(y, p):
    z = logit(p)
    try:
        ic = float(sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=z).fit().params[0])
        sl = float(sm.GLM(y, sm.add_constant(z), family=sm.families.Binomial()).fit().params[1])
    except Exception: ic, sl = np.nan, np.nan
    return ic, sl

def metrics(y, p, subj=None, reps=0):
    out = {"n": int(len(y)), "pos": int(y.sum()), "auroc": float(roc_auc_score(y, p)), "auprc": float(average_precision_score(y, p)), "brier": float(brier_score_loss(y, p))}
    out["cal_intercept"], out["cal_slope"] = calib(y, p)
    if reps and subj is not None:
        codes, inv = np.unique(subj, return_inverse=True); NS = len(codes); r2 = np.random.default_rng(SEED)
        boots = {"auroc": [], "auprc": [], "brier": []}
        for _ in range(reps):
            w = r2.multinomial(NS, np.full(NS, 1 / NS))[inv].astype(float)
            if (w * y).sum() == 0 or (w * (1 - y)).sum() == 0: continue
            boots["auroc"].append(roc_auc_score(y, p, sample_weight=w)); boots["auprc"].append(average_precision_score(y, p, sample_weight=w)); boots["brier"].append(brier_score_loss(y, p, sample_weight=w))
        for k, v in boots.items(): out[f"{k}_ci"] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    return out

GRID = {"cat": [{"lr": 0.05, "depth": 6, "l2": 3}, {"lr": 0.1, "depth": 4, "l2": 1}, {"lr": 0.05, "depth": 8, "l2": 10}, {"lr": 0.08, "depth": 6, "l2": 10}],
        "xgb": [{"lr": 0.05, "depth": 6, "l2": 1, "mcw": 5}, {"lr": 0.1, "depth": 4, "l2": 1, "mcw": 1}, {"lr": 0.05, "depth": 8, "l2": 5, "mcw": 10}, {"lr": 0.08, "depth": 6, "l2": 10, "mcw": 5}],
        "lgb": [{"lr": 0.05, "depth": 6, "l2": 1, "mcw": 5}, {"lr": 0.1, "depth": 4, "l2": 1, "mcw": 1}, {"lr": 0.05, "depth": 8, "l2": 5, "mcw": 10}, {"lr": 0.08, "depth": 6, "l2": 10, "mcw": 5}]}
res = {"seed": SEED, "n_configs_per_learner": N_CFG, "tuning": {}, "oof": {}, "test": {}, "test_code_negative_only": {}, "subgroups": {}, "shap": {}, "thresholds": {}, "secondary_imaging_observed": {}, "sizes": {"DEV": len(DEV), "TEST": len(TEST), "GOLD": len(GOLD)}}
# ---- tuning on FS-A, unweighted, 3-fold subject CV (folds 0-2 of the 5) ----
best = {}
for learner in ["cat", "xgb", "lgb"]:
    scores = []
    for ci, cfg in enumerate(GRID[learner][:N_CFG]):
        ap = []
        for k in range(TUNE_FOLDS):
            tr, va = DEV[DEV.fold != k], DEV[DEV.fold == k]
            m, _ = fit(learner, cfg, tr, FS["FS-A"], False); ap.append(average_precision_score(va.y, predict(m, va[FS["FS-A"]])))
        scores.append({"cfg": cfg, "mean_auprc_oof": float(np.mean(ap))}); log(f"tune {learner} cfg{ci} AUPRC {np.mean(ap):.4f}")
    best[learner] = max(scores, key=lambda s: s["mean_auprc_oof"])["cfg"]; res["tuning"][learner] = {"configs": scores, "best": best[learner]}
# ---- OOF (5 folds) for every learner x FS x {unweighted, weighted}; corrected derived ----
oof_rows = []
PLAN = [(l, fs) for l in ["cat", "xgb", "lgb"] for fs in (["FS-A", "FS-B", "FS-AVAIL"] if l == "cat" else ["FS-A", "FS-B"])]
for learner, fs in PLAN:
    for weighted in [False, True]:
        p = np.full(len(DEV), np.nan); pc = np.full(len(DEV), np.nan)
        for k in range(5):
            tr_idx = DEV.fold != k; m, spw = fit(learner, best[learner], DEV[tr_idx], FS[fs], weighted)
            pk = predict(m, DEV.loc[~tr_idx, FS[fs]]); p[~tr_idx] = pk
            if weighted: pc[~tr_idx] = corrected(pk, spw)
        name = f"{learner}|{fs}|{'weighted' if weighted else 'unweighted'}"
        res["oof"][name] = metrics(DEV.y.to_numpy(), p); oof_rows.append((name, p)); log(f"OOF {name} AUROC {res['oof'][name]['auroc']:.4f} slope {res['oof'][name]['cal_slope']:.3f}")
        if weighted:
            n2 = f"{learner}|{fs}|weighted+corrected"; res["oof"][n2] = metrics(DEV.y.to_numpy(), pc); oof_rows.append((n2, pc))
oof = pd.DataFrame({n: p for n, p in oof_rows}); oof.insert(0, "hadm_id", DEV.hadm_id.values); oof.to_parquet(f"{PREDDIR}/structured_oof.parquet", index=False)
# thresholds on DEV OOF (max F1) for CatBoost rows
for n, p in oof_rows:
    if not n.startswith("cat"): continue
    y = DEV.y.to_numpy(); ths = np.quantile(p, np.linspace(0.5, 0.995, 100)); f1s = []
    for t in ths:
        pr = p >= t; tp = (pr & (y == 1)).sum(); f1s.append(2 * tp / max(1, pr.sum() + (y == 1).sum()))
    res["thresholds"][n] = {"threshold_maxF1_dev_oof": float(ths[int(np.argmax(f1s))]), "dev_oof_F1": float(max(f1s))}
# ---- final fits on all DEV -> TEST (once) and GOLD (scored, never fitted on) ----
test_rows, gold_rows = [], []
for learner, fs in PLAN:
    for weighted in [False, True]:
        m, spw = fit(learner, best[learner], DEV, FS[fs], weighted); name = f"{learner}|{fs}|{'weighted' if weighted else 'unweighted'}"
        pt = predict(m, TEST[FS[fs]]); pg = predict(m, GOLD[FS[fs]])
        variants = [(name, pt, pg)] + ([(f"{learner}|{fs}|weighted+corrected", corrected(pt, spw), corrected(pg, spw))] if weighted else [])
        for n, a, b in variants:
            res["test"][n] = metrics(TEST.y.to_numpy(), a, TEST.subject_id.to_numpy(), REPS); test_rows.append((n, a)); gold_rows.append((n, b))
            neg = (TEST.code_positive == False).to_numpy(); res["test_code_negative_only"][n] = metrics(TEST.y.to_numpy()[neg], a[neg])
            if n in res["thresholds"]:
                t = res["thresholds"][n]["threshold_maxF1_dev_oof"]; pr = a >= t; y = TEST.y.to_numpy()
                res["thresholds"][n].update({"test_sensitivity": float((pr & (y == 1)).sum() / max(1, (y == 1).sum())), "test_specificity": float((~pr & (y == 0)).sum() / max(1, (y == 0).sum())), "test_ppv": float((pr & (y == 1)).sum() / max(1, pr.sum()))})
            log(f"TEST {n} AUROC {res['test'][n]['auroc']:.4f} AUPRC {res['test'][n]['auprc']:.4f} int {res['test'][n]['cal_intercept']:.3f} slope {res['test'][n]['cal_slope']:.3f}")
            if learner == "cat":
                sg = {}
                for var in ["race", "insurance", "gender", "age_band"]:
                    sg[var] = {}
                    for lev, g in TEST.groupby(var):
                        idx = g.index.to_numpy(); yy = TEST.y.to_numpy()[idx]
                        if (yy == 1).sum() >= 50 and (yy == 0).sum() >= 50:
                            mm_ = metrics(yy, a[idx]); mm_["material_calibration_difference"] = bool(abs(mm_["cal_intercept"] - res["test"][n]["cal_intercept"]) > 0.5 or abs(mm_["cal_slope"] - res["test"][n]["cal_slope"]) > 0.25)
                            sg[var][str(lev)] = mm_
                        else: sg[var][str(lev)] = "not estimable"
                res["subgroups"][n] = sg
        fn = f"{MODELDIR}/{learner}_{fs}_{'weighted' if weighted else 'unweighted'}"
        if learner == "cat": m.save_model(fn + ".cbm")
        elif learner == "xgb": m.save_model(fn + ".json")
        else: m.booster_.save_model(fn + ".txt")
        if learner == "cat" and not weighted:
            from catboost import Pool
            samp = TEST.sample(min(20000, len(TEST)), random_state=SEED)
            sv = m.get_feature_importance(Pool(samp[FS[fs]], cat_features=[f for f in FS[fs] if f in CAT]), type="ShapValues")[:, :-1]
            imp = pd.Series(np.abs(sv).mean(0), index=FS[fs]).sort_values(ascending=False)
            res["shap"][fs] = [{"feature": f, "mean_abs_shap": float(v), "class": "availability" if f in cls["availability"] else "clinical"} for f, v in imp.head(25).items()]
            res["shap"][fs + "_availability_share_top25"] = float(np.mean([f in cls["availability"] for f in imp.head(25).index]))
te = pd.DataFrame({n: p for n, p in test_rows}); te.insert(0, "hadm_id", TEST.hadm_id.values); te.to_parquet(f"{PREDDIR}/structured_test.parquet", index=False)
go = pd.DataFrame({n: p for n, p in gold_rows}); go.insert(0, "hadm_id", GOLD.hadm_id.values); go.to_parquet(f"{PREDDIR}/structured_gold.parquet", index=False)
# ---- secondary population: imaging-observed, CatBoost FS-A / FS-B ----
D2, T2 = DEV[DEV.imaging_observed].reset_index(drop=True), TEST[TEST.imaging_observed].reset_index(drop=True)
res["secondary_imaging_observed"]["sizes"] = {"DEV": len(D2), "DEV_pos": int(D2.y.sum()), "TEST": len(T2), "TEST_pos": int(T2.y.sum())}
for fs in ["FS-A", "FS-B"]:
    for weighted in [False, True]:
        m, spw = fit("cat", best["cat"], D2, FS[fs], weighted); pt = predict(m, T2[FS[fs]]); name = f"cat|{fs}|{'weighted' if weighted else 'unweighted'}"
        res["secondary_imaging_observed"][name] = metrics(T2.y.to_numpy(), pt, T2.subject_id.to_numpy(), REPS)
        if weighted: res["secondary_imaging_observed"][f"cat|{fs}|weighted+corrected"] = metrics(T2.y.to_numpy(), corrected(pt, spw), T2.subject_id.to_numpy(), REPS)
        log(f"secondary {name} AUROC {res['secondary_imaging_observed'][name]['auroc']:.4f}")
# ---- calibration plots (CatBoost, TEST) ----
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
for n, p in test_rows:
    if not n.startswith("cat"): continue
    y = TEST.y.to_numpy(); q = pd.qcut(p, 10, labels=False, duplicates="drop"); g = pd.DataFrame({"y": y, "p": p, "q": q}).groupby("q").agg(obs=("y", "mean"), pred=("p", "mean"))
    plt.figure(figsize=(4, 4)); plt.plot([0, 1], [0, 1], "k--", lw=0.8); plt.plot(g.pred, g.obs, "o-"); plt.xlabel("mean predicted"); plt.ylabel("observed"); plt.title(n + "\nSilver label — not adjudicated truth", fontsize=8); plt.tight_layout()
    plt.savefig(f"docs/figures/aim1b_cal_{n.replace('|', '_').replace('+', '-')}.png", dpi=110); plt.close()
res["runtime_s"] = round(time.time() - t0); json.dump(res, open(RES, "w"), indent=1); log("DONE")
