#!/usr/bin/env python3
"""Aim 1b label dependence (analysis-plan amendment j, S17). Exploratory.

Re-scores the TEST-partition predictions already locked in data/processed/run_2026-09-19_preds/
against two computable labels on the TEST admissions of the notes subsample: the frozen rule
(note_b, the label every model was trained on) and the LLM phenotype (llm_phenotype.load()).
Arms: CatBoost FS-A / FS-B / FS-AVAIL unweighted, TF-IDF S unweighted, embedding head S (logistic
regression), notes-augmented CatBoost unweighted. AUROC and AUPRC under each label and the paired
difference (LLM label minus rule label), on all TEST admissions and on code-negative ones; subject-
cluster bootstrap, 500 replicates, seed 20260919, 95% percentile intervals. No model is retrained and
no locked file is modified. Writes docs/run_2026-10-27/results/aim1b_llm_label.json and docs/aim1b_llm_label.md.
USAGE: scripts/run0919_env.sh scripts/aim1b_llm_label.py
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, ".")
from scripts import llm_phenotype as LP

REPS, SEED = 500, 20260919
PRED = "data/processed/run_2026-09-19_preds"
ARMS = [("CatBoost FS-A (clinical + availability)", "structured_test", "cat|FS-A|unweighted"),
        ("CatBoost FS-B (clinical)", "structured_test", "cat|FS-B|unweighted"),
        ("CatBoost FS-AVAIL (availability only)", "structured_test", "cat|FS-AVAIL|unweighted"),
        ("TF-IDF, lexicon sentences deleted (S)", "notes_tfidf_test", "tfidf|S|unweighted"),
        ("Embedding head (S), logistic regression", "notes_arm_test", "embed|S|lr"),
        ("Notes-augmented CatBoost (FS-B + notes)", "notes_arm_test", "aug|FS-B+notes|unweighted")]
METRICS = {"AUROC": roc_auc_score, "AUPRC": average_precision_score}


def main():
    a = LP.load()
    t = a[a.partition == "TEST"].reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    out = {"status": "exploratory (amendment j)", "scope": "TEST admissions of the dev/test notes subsample",
           "test_admissions": LP.suppress(len(t)), "bootstrap": {"reps": REPS, "seed": SEED},
           "labels": {"rule_positive": LP.suppress(t.rule.sum()), "llm_positive": LP.suppress(t.llm.sum()),
                      "kappa_rule_llm": kappa(t.rule, t.llm)}, "arms": {}}
    cache = {}
    for name, f, col in ARMS:
        if f not in cache:
            cache[f] = pd.read_parquet(f"{PRED}/{f}.parquet")
        d = t.merge(cache[f][["hadm_id", col]], on="hadm_id", how="inner").dropna(subset=[col]).reset_index(drop=True)
        codes, idx = np.unique(d.subject_id.to_numpy(), return_inverse=True)
        W = rng.multinomial(len(codes), np.full(len(codes), 1 / len(codes)), size=REPS)[:, idx].astype(float)
        res = {}
        for subset, m in (("all", np.ones(len(d), bool)), ("code_negative", ~d.code.to_numpy())):
            p = d[col].to_numpy()[m]
            yr, yl, w = d.rule.to_numpy()[m].astype(int), d.llm.to_numpy()[m].astype(int), W[:, m]
            r = {"n": LP.suppress(m.sum()), "rule_pos": LP.suppress(yr.sum()), "llm_pos": LP.suppress(yl.sum())}
            for mn, fn in METRICS.items():
                er, el = fn(yr, p), fn(yl, p)
                br = np.array([fn(yr, p, sample_weight=w[i]) for i in range(REPS)])
                bl = np.array([fn(yl, p, sample_weight=w[i]) for i in range(REPS)])
                ci = lambda x: [round(float(v), 3) for v in np.percentile(x, [2.5, 97.5])]
                r[mn] = {"rule": round(float(er), 3), "rule_ci": ci(br), "llm": round(float(el), 3), "llm_ci": ci(bl),
                         "llm_minus_rule": round(float(el - er), 3), "diff_ci": ci(bl - br)}
            res[subset] = r
        out["arms"][name] = res
        print(f"  {name}: AUROC rule {res['all']['AUROC']['rule']} llm {res['all']['AUROC']['llm']}", flush=True)
    path = f"{LP.results_dir()}/aim1b_llm_label.json"
    json.dump(out, open(path, "w"), indent=1)
    write_doc(out, path)
    print(f"wrote {path} and docs/aim1b_llm_label.md")


def kappa(x, y):
    x, y = np.asarray(x, bool), np.asarray(y, bool)
    po = float((x == y).mean())
    pe = float(x.mean() * y.mean() + (~x).mean() * (~y).mean())
    return round((po - pe) / (1 - pe), 3)


def write_doc(r, src):
    L = ["# Aim 1b: how much do silver-label metrics depend on the label?\n",
         "> **Exploratory (analysis-plan amendment j, committed before this analysis was run).** Both labels are "
         "computable phenotypes, not the reference standard. Numbers are written by `scripts/aim1b_llm_label.py` into "
         f"`{src}`.\n",
         f"Every model was trained on the frozen rule's label. Here its locked TEST predictions are scored against the rule "
         f"label and against the LLM phenotype, on {r['test_admissions']:,} TEST admissions of the notes subsample "
         f"(rule-positive {r['labels']['rule_positive']:,}, LLM-positive {r['labels']['llm_positive']:,}, Cohen's kappa "
         f"between the labels {r['labels']['kappa_rule_llm']}). Intervals: 95% subject-cluster bootstrap, "
         f"{r['bootstrap']['reps']} replicates. Caveats: the LLM prompt was revised twice on information that included "
         "TEST (amendment h); the notes arms and the LLM read the same notes.\n"]
    for subset, title in (("all", "All TEST admissions"), ("code_negative", "Code-negative TEST admissions")):
        L += [f"## {title}\n", "| Arm | n | AUROC, rule label | AUROC, LLM label | Difference | AUPRC, rule label | AUPRC, LLM label | Difference |",
              "| --- | --: | --: | --: | --: | --: | --: | --: |"]
        for name, res in r["arms"].items():
            x = res[subset]
            f = lambda m, k: f"{x[m][k]} ({x[m][k + '_ci'][0]}–{x[m][k + '_ci'][1]})"
            d = lambda m: f"{x[m]['llm_minus_rule']:+} ({x[m]['diff_ci'][0]}–{x[m]['diff_ci'][1]})"
            n = x["n"]
            L.append(f"| {name} | {n:,} | {f('AUROC', 'rule')} | {f('AUROC', 'llm')} | {d('AUROC')} | "
                     f"{f('AUPRC', 'rule')} | {f('AUPRC', 'llm')} | {d('AUPRC')} |")
        L.append("")
    open("docs/aim1b_llm_label.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
