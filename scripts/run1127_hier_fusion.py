#!/usr/bin/env python3
"""Hierarchical Bayesian fusion of the structured and notes models (amendment (q)). DEVELOPMENT DIAGNOSTIC:
silver label; the notes input shares a source with the label.

Not run on MIMIC until amendment (q) is in the committed analysis plan: with the default (real) inputs the script
stops unless `git show HEAD:docs/analysis_plan_prespecified.md` contains the amendment's heading. It never reads a
GOLD_HOLDOUT prediction file (they are locked and sealed) and never touches the existing lock.

Inputs, as the locked stacked fusion (scripts/run0919_fusion_lock.py) used them:
  layer 0   the structured and notes predictions named in docs/run_2026-09-19/results/aim1b_fusion.json (layer0):
            DEV out-of-fold for fitting, TEST for evaluation, on the notes subsample
  strata    8 data-availability strata from run_2026-09-19_features.parquet, known at discharge:
            discharge summary present (n_notes_dc > 0) x liver imaging in the stay or the 365 days before
            (liver_imaging_any_pre) x AST, ALT and platelets all measured in the stay (FIB-4 inputs)
  never     code status, race, insurance, language, sex or age as inputs
Model: scripts/hier_bayes.py (each stratum its own intercept and weights on the two standardised logits, partially
pooled; Gamma(2) prior on the spreads; mu integrated out), fitted on DEV with the pre-specified convergence policy
(hier_bayes.ATTEMPTS / CRITERIA). If no attempt converges, nothing is evaluated on TEST.
Evaluation, once, on TEST against the stacked fusion refitted on the same DEV rows: AUROC, AUPRC, Brier, log loss,
calibration intercept and slope, all and code-negative only; paired subject-cluster bootstrap differences
(hierarchical minus stacked, 500 replicates); calibration in the large per stratum.

Outputs  docs/run_2026-11-27/results/hier_fusion.json and docs/aim1b_hier_fusion.md (aggregates; counts 1-10 as <11)
         (with --structured FS-A, sensitivity S23: the same names with _S23 before the extension)
         data/processed/run_2026-11-27_hier_fusion_test.parquet (TEST predictions), ..._draws.npz (posterior draws)
         data/processed/results_raw/hier_fusion_raw.json (unsuppressed per-stratum counts; git-ignored)
Run:  scripts/run0919_env.sh scripts/run1127_hier_fusion.py                      (primary)
      scripts/run0919_env.sh scripts/run1127_hier_fusion.py --structured FS-A    (S23)
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts import hier_bayes as HB  # noqa: E402
from scripts.public_counts import SMALL, is_small  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = "docs/analysis_plan_prespecified.md"
AMENDMENT_MARK = "**(q) Hierarchical Bayesian fusion"
SEED = 20261127
REPS = 500
STRATA = ["dc", "liver_imaging", "fib4_inputs"]
STRATUM_LABELS = [f"discharge summary {'yes' if g >> 2 & 1 else 'no'} · liver imaging {'yes' if g >> 1 & 1 else 'no'}"
                  f" · FIB-4 inputs {'yes' if g & 1 else 'no'}" for g in range(8)]
DEFAULTS = {"sub": "data/processed/run_2026-09-19_notes_text/subsample.parquet",
            "preddir": "data/processed/run_2026-09-19_preds",
            "features": "data/processed/run_2026-09-19_features.parquet",
            "layer0": "docs/run_2026-09-19/results/aim1b_fusion.json",
            "results": "docs/run_2026-11-27/results/hier_fusion.json",
            "doc": "docs/aim1b_hier_fusion.md",
            "processed": "data/processed"}


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def amendment_committed():
    try:
        txt = subprocess.run(["git", "show", f"HEAD:{PLAN}"], capture_output=True, text=True, check=True, cwd=ROOT).stdout
    except (OSError, subprocess.CalledProcessError):
        return False
    return AMENDMENT_MARK in txt


def real_inputs(a):
    proc = os.path.realpath(os.path.join(ROOT, "data", "processed"))
    return any(os.path.realpath(p).startswith(proc) for p in (a.sub, a.preddir, a.features))


# --- data
def load(a):
    import duckdb
    lay = json.load(open(a.layer0))["layer0"]
    s_col, n_col, n_src = lay["structured_FS-B" if a.structured == "FS-B" else "structured_FS-A"], lay["notes"], lay["notes_source"]
    notes_stem = "notes_tfidf" if n_src == "tfidf" else "notes_arm"
    con = duckdb.connect()
    q = lambda sql: con.execute(sql).fetchdf()
    sub = q(f"SELECT hadm_id, subject_id, partition, note_b, code_positive FROM read_parquet('{a.sub}') "
            "WHERE partition IN ('DEV', 'TEST')")          # GOLD_HOLDOUT rows are never read
    feat = q(f"""SELECT hadm_id, n_notes_dc > 0 AS dc, liver_imaging_any_pre > 0 AS liver_imaging,
                 (first_val_AST IS NOT NULL AND first_val_ALT IS NOT NULL AND first_val_Platelets IS NOT NULL) AS fib4_inputs
                 FROM read_parquet('{a.features}')""")
    frames = {}
    for part, suffix in (("DEV", "oof"), ("TEST", "test")):
        st = q(f"SELECT hadm_id, \"{s_col}\" AS p_structured FROM read_parquet('{a.preddir}/structured_{suffix}.parquet')")
        nt = q(f"SELECT hadm_id, \"{n_col}\" AS p_notes FROM read_parquet('{a.preddir}/{notes_stem}_{suffix}.parquet')")
        d = (sub[sub.partition == part].merge(st, on="hadm_id").merge(nt, on="hadm_id").merge(feat, on="hadm_id", how="left")
             .dropna(subset=["p_structured", "p_notes"]).reset_index(drop=True))
        for c in STRATA:
            d[c] = d[c].fillna(False).astype(bool)
        d["stratum"] = 4 * d.dc.astype(int) + 2 * d.liver_imaging.astype(int) + d.fib4_inputs.astype(int)
        d["y"] = d.note_b.astype(int)
        frames[part] = d
    return frames, {"structured": s_col, "notes": n_col, "notes_source": n_src}


# --- metrics (as run0919_fusion_lock.py)
def calib(y, p):
    import statsmodels.api as sm
    z = logit(p)
    try:
        a = sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=z).fit().params[0]
        b = sm.GLM(y, sm.add_constant(z), family=sm.families.Binomial()).fit().params[1]
        return float(a), float(b)
    except Exception:   # noqa: BLE001
        return float("nan"), float("nan")


def metrics(y, p):
    from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
    out = {"n": int(len(y)), "positives": int(y.sum()), "auroc": float(roc_auc_score(y, p)),
           "auprc": float(average_precision_score(y, p)), "brier": float(brier_score_loss(y, p)),
           "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)))}
    out["cal_intercept"], out["cal_slope"] = calib(y, p)
    return out


def paired_bootstrap(y, subj, pa, pb, reps=REPS, seed=SEED):
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
    codes, inv = np.unique(subj, return_inverse=True)
    rng = np.random.default_rng(seed)
    diffs = {"auroc": [], "auprc": [], "brier": []}
    for _ in range(reps):
        w = rng.multinomial(len(codes), np.full(len(codes), 1 / len(codes)))[inv].astype(float)
        if (w * y).sum() == 0:
            continue
        for k, f in (("auroc", roc_auc_score), ("auprc", average_precision_score), ("brier", brier_score_loss)):
            diffs[k].append(f(y, pa, sample_weight=w) - f(y, pb, sample_weight=w))
    return {k: {"mean": float(np.mean(v)), "ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]}
            for k, v in diffs.items()}


def public(v):
    return SMALL if is_small(v) else v


# --- run
def run(a):
    t0 = time.time()
    os.makedirs(a.processed, exist_ok=True)
    frames, inputs = load(a)
    dev, test = frames["DEV"], frames["TEST"]
    mean = {c: float(logit(dev[c]).mean()) for c in ("p_structured", "p_notes")}
    sd = {c: float(logit(dev[c]).std()) for c in ("p_structured", "p_notes")}
    Z = lambda d: np.column_stack([np.ones(len(d))] + [(logit(d[c]) - mean[c]) / sd[c] for c in ("p_structured", "p_notes")])
    Xd, yd, gd = Z(dev), dev.y.to_numpy(), dev.stratum.to_numpy()
    make = lambda form: HB.HierLogit(Xd, yd, gd, 8, parameterization=form)
    attempts = HB.ATTEMPTS if not a.quick else tuple(dict(x, warmup=x["warmup"] * 3 // 4) for x in HB.ATTEMPTS)
    model, fit, diag, log, ok = HB.fit_with_policy(make, seed=SEED, draws=a.draws, attempts=attempts)
    names = ["intercept", "w_structured", "w_notes"]
    post = HB.summarize(model, fit, names)
    print(f"[hier] DEV {len(dev):,} admissions; strata 8; attempts: "
          + "; ".join(f"{x['form']} target {x['target_accept']} R-hat {x['rhat_max']:.4f} ESS {x['ess_min']:.0f} divergences {x['divergences']}" for x in log)
          + f"; converged {'yes' if ok else 'NO'}", flush=True)
    res = {"header": "DEVELOPMENT DIAGNOSTIC — silver label; the notes input shares a source with the label. Amendment (q)" + (", sensitivity S23 (FS-A structured input)." if a.tag else "."),
           "seed": SEED, "inputs": inputs, "standardisation": {"mean": mean, "sd": sd},
           "priors": {"mu_sd": model.prior_sd.tolist(), "tau_prior": model.tau_prior, "tau_scale": model.tau_scale.tolist()},
           "form": model.form,
           "convergence": {"criteria": HB.CRITERIA, "attempts": log, "converged": ok, "chains": diag["chains"]},
           "posterior": {"mu": post["mu"], "tau": post["tau"],
                         "strata": [{"stratum": STRATUM_LABELS[g], "dev_admissions": public(int((dev.stratum == g).sum())),
                                     "dev_positives": public(int(dev.y[dev.stratum == g].sum())), **post["theta"][g]}
                                    for g in range(8)]}}
    raw = {"dev_strata": {STRATUM_LABELS[g]: {"admissions": int((dev.stratum == g).sum()),
                                              "positives": int(dev.y[dev.stratum == g].sum())} for g in range(8)}}
    if ok:
        from sklearn.linear_model import LogisticRegression
        L = lambda d: np.column_stack([logit(d.p_structured), logit(d.p_notes)])
        lr = LogisticRegression(C=1e6, max_iter=1000).fit(L(dev), dev.y)
        g_test = np.where(np.isin(test.stratum, np.unique(dev.stratum)), test.stratum, -1)
        p_h = HB.predict(model, fit, Z(test), g_test, seed=SEED)
        p_l = lr.predict_proba(L(test))[:, 1]
        y, subj, neg = test.y.to_numpy(), test.subject_id.to_numpy(), ~test.code_positive.astype(bool).to_numpy()
        res["test"] = {"hierarchical": {"all": metrics(y, p_h), "code_negative_only": metrics(y[neg], p_h[neg])},
                       "stacked_refit": {"all": metrics(y, p_l), "code_negative_only": metrics(y[neg], p_l[neg]),
                                         "coefficients": {"intercept": float(lr.intercept_[0]),
                                                          "w_structured": float(lr.coef_[0][0]), "w_notes": float(lr.coef_[0][1])}},
                       "paired_differences_hierarchical_minus_stacked": paired_bootstrap(y, subj, p_h, p_l)}
        per, raw["test_strata"] = [], {}
        for g in range(8):
            m = test.stratum.to_numpy() == g
            n_g, pos = int(m.sum()), int(y[m].sum())
            raw["test_strata"][STRATUM_LABELS[g]] = {"admissions": n_g, "positives": pos}
            hide = is_small(n_g) or is_small(pos) or is_small(n_g - pos)
            per.append({"stratum": STRATUM_LABELS[g], "admissions": public(n_g), "positives": public(pos),
                        "observed_rate": None if hide or not n_g else round(pos / n_g, 4),
                        "mean_predicted_hierarchical": None if hide or not n_g else round(float(p_h[m].mean()), 4),
                        "mean_predicted_stacked": None if hide or not n_g else round(float(p_l[m].mean()), 4)})
        res["test"]["calibration_in_the_large_by_stratum"] = per
        pd.DataFrame({"hadm_id": test.hadm_id, "stratum": test.stratum, "p_hierarchical": p_h, "p_stacked_refit": p_l}) \
          .to_parquet(os.path.join(a.processed, f"run_2026-11-27_hier_fusion{a.tag}_test.parquet"), index=False)
        th = res["test"]
        for k in ("hierarchical", "stacked_refit"):
            m_ = th[k]["all"]
            print(f"[hier] TEST {k:<13} AUROC {m_['auroc']:.3f}  AUPRC {m_['auprc']:.3f}  Brier {m_['brier']:.4f}  "
                  f"intercept {m_['cal_intercept']:+.2f}  slope {m_['cal_slope']:.2f}", flush=True)
        dd = th["paired_differences_hierarchical_minus_stacked"]
        print("[hier] hierarchical minus stacked: " + "  ".join(
            f"{k} {v['mean']:+.4f} ({v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f})" for k, v in dd.items()), flush=True)
    else:
        res["test"] = "not evaluated: the sampler did not meet the convergence criteria"
        print("[hier] not converged — TEST not touched", flush=True)
    np.savez_compressed(os.path.join(a.processed, f"run_2026-11-27_hier_fusion{a.tag}_draws.npz"),
                        draws=fit["draws"], mu=fit["mu"])
    res["runtime_s"] = round(time.time() - t0)
    os.makedirs(os.path.dirname(a.results), exist_ok=True)
    json.dump(res, open(a.results, "w"), indent=1)
    os.makedirs(os.path.join(a.processed, "results_raw"), exist_ok=True)
    json.dump(raw, open(os.path.join(a.processed, "results_raw", f"hier_fusion{a.tag}_raw.json"), "w"), indent=1)
    write_doc(a.doc, res, a.results, a.tag)
    return 0 if ok else 1


def write_doc(path, res, results_path, tag=""):
    L = ["# Aim 1b — hierarchical Bayesian fusion (amendment (q)" + ("; sensitivity S23, FS-A structured input" if tag else "") + ")\n",
         f"Produced by `scripts/run1127_hier_fusion.py`; numbers from `{results_path}`.\n",
         "**Development diagnostic.** Silver label — known error; not adjudicated truth. The notes input shares a source "
         "with the label. Counts from 1 to 10 appear as <11.\n",
         f"Inputs: structured `{res['inputs']['structured']}`, notes `{res['inputs']['notes']}`, on the notes subsample "
         "(DEV out-of-fold to fit, TEST to evaluate). Each of 8 data-availability strata has its own intercept and "
         "weights on the two standardised logits, partially pooled.\n",
         "## Convergence\n", "| attempt | form | target acceptance | warm-up | R-hat max | ESS min | divergences |",
         "| --: | --- | --: | --: | --: | --: | --: |"]
    for i, x in enumerate(res["convergence"]["attempts"], 1):
        L.append(f"| {i} | {x['form']} | {x['target_accept']} | {x['warmup']} | {x['rhat_max']:.4f} | {x['ess_min']:.0f} | {x['divergences']} |")
    L += ["", f"Converged: **{'yes' if res['convergence']['converged'] else 'no'}** "
          f"(criteria: R-hat ≤ {HB.CRITERIA['rhat_max']}, ESS ≥ {HB.CRITERIA['ess_min']:.0f}, no divergences).\n",
          "## Weights by stratum (posterior mean, 95% interval; standardised logits)\n",
          "| stratum | DEV admissions | intercept | structured weight | notes weight |", "| --- | --: | --- | --- | --- |"]
    f = lambda d: f"{d['mean']:.2f} ({d['q2.5']:.2f}, {d['q97.5']:.2f})"
    for s in res["posterior"]["strata"]:
        L.append(f"| {s['stratum']} | {s['dev_admissions'] if isinstance(s['dev_admissions'], str) else format(s['dev_admissions'], ',')} | "
                 f"{f(s['intercept'])} | {f(s['w_structured'])} | {f(s['w_notes'])} |")
    mu, tau = res["posterior"]["mu"], res["posterior"]["tau"]
    L.append(f"| population (mu) | | {f(mu['intercept'])} | {f(mu['w_structured'])} | {f(mu['w_notes'])} |")
    L.append(f"| spread across strata (tau) | | {f(tau['intercept'])} | {f(tau['w_structured'])} | {f(tau['w_notes'])} |\n")
    if isinstance(res["test"], dict):
        L += ["## TEST (scored once)\n", "| arm | AUROC | AUPRC | Brier | log loss | intercept | slope | code-negative AUROC |",
              "| --- | --: | --: | --: | --: | --: | --: | --: |"]
        for k in ("hierarchical", "stacked_refit"):
            m, c = res["test"][k]["all"], res["test"][k]["code_negative_only"]
            L.append(f"| {k} | {m['auroc']:.3f} | {m['auprc']:.3f} | {m['brier']:.4f} | {m['log_loss']:.4f} | "
                     f"{m['cal_intercept']:+.2f} | {m['cal_slope']:.2f} | {c['auroc']:.3f} |")
        L += ["", "Paired subject-cluster bootstrap, hierarchical minus stacked (500 replicates): " + "; ".join(
            f"{k} {v['mean']:+.4f} ({v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f})"
            for k, v in res["test"]["paired_differences_hierarchical_minus_stacked"].items()) + ".\n"]
    else:
        L.append(f"## TEST\n\n{res['test']}.\n")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w").write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k}", default=v)
    ap.add_argument("--structured", choices=["FS-B", "FS-A"], default="FS-B", help="FS-A is sensitivity S23")
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--quick", action="store_true", help="synthetic tests only: the policy with shorter warm-up")
    ap.add_argument("--force", action="store_true", help="score TEST again (it is meant to be scored once)")
    a = ap.parse_args(argv)
    a.tag = "" if a.structured == "FS-B" else "_S23"
    for k in ("results", "doc"):                     # S23 writes beside the primary, never over it
        if a.tag and getattr(a, k) == DEFAULTS[k]:
            stem, ext = os.path.splitext(DEFAULTS[k])
            setattr(a, k, stem + a.tag + ext)
    if real_inputs(a):
        if a.quick:
            sys.exit("REFUSING: --quick is for synthetic tests only")
        if not amendment_committed():
            sys.exit(f"REFUSING: amendment (q) is not in the committed {PLAN}. The analysis plan must record it "
                     "before this model touches the data (see docs/run_2026-11-27/AMENDMENT_q_DRAFT.md).")
    if os.path.exists(a.results) and not a.force:
        sys.exit(f"REFUSING: {a.results} exists; TEST is scored once. Pass --force only to redo a failed run.")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
