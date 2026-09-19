#!/usr/bin/env python3
"""run_2026-09-19 — report writers for Phases 7, 8, 9 (read results JSON only; no data). Usage: run0919_aim1b_reports.py [7|8|9|all]"""
import json, os, sys
R = "docs/run_2026-09-19/results"
SILVER = "**Silver label — known error; not adjudicated truth; final performance requires the gold standard.**"
DIAG = "**DEVELOPMENT DIAGNOSTIC — label and input share a source; not an accuracy estimate.**"
def f3(x): return "—" if x is None or (isinstance(x, float) and x != x) else f"{x:.3f}"
def ci(m, k): return f"{f3(m.get(k))} ({f3(m[k+'_ci'][0])}–{f3(m[k+'_ci'][1])})" if k + "_ci" in m else f3(m.get(k))
def mrow(name, m): return f"| {name} | {m['n']:,} | {m['pos']:,} | {ci(m,'auroc')} | {ci(m,'auprc')} | {ci(m,'brier')} | {f3(m.get('cal_intercept'))} | {f3(m.get('cal_slope'))} |"
MH = "| model | n | positives | AUROC (95% CI) | AUPRC (95% CI) | Brier (95% CI) | calibration intercept | calibration slope |\n| --- | --: | --: | --- | --- | --- | --: | --: |"

def report7():
    S = json.load(open(f"{R}/aim1b_structured.json")); C = json.load(open(f"{R}/feature_classification.json")); sp = json.load(open(f"{R}/phase2_splits.json"))
    L = ["# Aim 1b — structured arm (run_2026-09-19, Phase 7)\n", f"Produced by `scripts/run0919_aim1b_structured.py` (features: `scripts/run0919_features.py`); every number is read from `{R}/aim1b_structured.json` and `feature_classification.json` by `scripts/run0919_aim1b_reports.py`. Organized by the TRIPOD+AI development items (Collins et al. 2024).\n", SILVER + "\n",
         "## Source of data, participants, outcome\n",
         f"MIMIC-IV v3.1 with MIMIC-IV-Note; the locked, cleaned analysis population; subject-level splits with a gold holdout (`docs/aim1b_splits.md`): DEV {sp['partitions']['DEV']['admissions']:,} admissions, TEST {sp['partitions']['TEST']['admissions']:,}, GOLD_HOLDOUT {sp['partitions']['GOLD_HOLDOUT']['admissions']:,} (never fitted on). Outcome = silver label: note-positive under the frozen rule v1.1.0, primary definition (b). Prevalence DEV {sp['partitions']['DEV']['silver_prevalence_pct']}%, TEST {sp['partitions']['TEST']['silver_prevalence_pct']}%.\n",
         "## Predictors and the leakage audit\n",
         "Everything is time-bounded at discharge; no post-discharge information. Never a feature: the four phenotype codes or anything derived from them; the full Charlson index (contains K76.0/571.x — `docs/charlson_validation.md`); any output of the note rule; note counts or lengths outside the availability set. Each candidate feature was classified before training as *clinical* or *availability/volume-derived*.\n",
         f"| class | n | features |", "| --- | --: | --- |", f"| clinical | {len(C['clinical'])} | {', '.join(C['clinical'])} |", f"| availability / volume | {len(C['availability'])} | {', '.join(C['availability'])} |", "",
         "Excluded (reason): " + "; ".join(f"{k} — {v}" for k, v in C["excluded"].items()) + ".\n",
         "Feature sets: **FS-A** everything; **FS-B** clinical only; **FS-AVAIL** availability/volume only (how much of the label the documentation process alone predicts). Limitation stated: tree models split on missing values natively, so FS-B still sees the missingness pattern even without explicit indicators; FS-AVAIL bounds that.\n",
         "## Model development\n",
         f"CatBoost (primary), XGBoost and LightGBM comparators; native missing-value handling; no imputation; no synthetic oversampling. Imbalance variants: unweighted; weighted (scale_pos_weight = negatives ÷ positives in the training fold); weighted+corrected (the weighted model's logit shifted by −log of the weight — the analytic prior correction). Tuning: {S['n_configs_per_learner']} configurations per learner on FS-A (unweighted) by 3-fold subject-level CV within DEV with early stopping on an inner 10% subject split; the best configuration per learner (by OOF AUPRC) was reused for every feature set and variant (Tier 1). Then 5-fold subject-level OOF predictions on DEV; final models fit on all DEV; TEST touched once.\n",
         "| learner | best configuration | tuning OOF AUPRC per configuration |", "| --- | --- | --- |"]
    for l, t in S["tuning"].items(): L.append(f"| {l} | {t['best']} | " + ", ".join(f"{c['mean_auprc_oof']:.4f}" for c in t["configs"]) + " |")
    L += ["", "## Performance on DEV (out-of-fold) — for calibration comparison across imbalance variants\n", MH]
    for k, m in S["oof"].items(): L.append(mrow(k, m))
    L += ["", "## Performance on TEST (touched once; subject-cluster bootstrap CIs, 500 replicates)\n", SILVER + "\n", MH]
    for k, m in S["test"].items(): L.append(mrow(k, m))
    L += ["", "### Within code-negative admissions only (the recovery-zone question in silver-label form)\n", "| model | n | positives | AUROC | AUPRC | Brier |", "| --- | --: | --: | --: | --: | --: |"]
    for k, m in S["test_code_negative_only"].items(): L.append(f"| {k} | {m['n']:,} | {m['pos']:,} | {f3(m['auroc'])} | {f3(m['auprc'])} | {f3(m['brier'])} |")
    L += ["", "### Thresholds (chosen on DEV OOF by maximum F1; CatBoost rows)\n", "| model | threshold | DEV OOF F1 | TEST sensitivity | TEST specificity | TEST PPV |", "| --- | --: | --: | --: | --: | --: |"]
    for k, t in S["thresholds"].items(): L.append(f"| {k} | {f3(t['threshold_maxF1_dev_oof'])} | {f3(t['dev_oof_F1'])} | {f3(t.get('test_sensitivity'))} | {f3(t.get('test_specificity'))} | {f3(t.get('test_ppv'))} |")
    L += ["", "## Secondary population — imaging-observed admissions (≥1 liver-inclusive study, −365/+30)\n", f"Sizes: DEV {S['secondary_imaging_observed']['sizes']['DEV']:,} (positives {S['secondary_imaging_observed']['sizes']['DEV_pos']:,}), TEST {S['secondary_imaging_observed']['sizes']['TEST']:,} (positives {S['secondary_imaging_observed']['sizes']['TEST_pos']:,}). Within admissions where the liver was actually imaged, can structured data predict documented steatosis?\n", MH]
    for k, m in S["secondary_imaging_observed"].items():
        if k != "sizes": L.append(mrow(k, m))
    L += ["", "## Subgroups (TEST; CatBoost; metric only where ≥50 positives and ≥50 negatives)\n", "A subgroup is flagged when its calibration intercept differs from the overall by more than 0.5 or its slope by more than 0.25 (analyst threshold).\n"]
    for k, sg in S["subgroups"].items():
        L += [f"### {k}\n", "| stratum | n | positives | AUROC | AUPRC | Brier | intercept | slope | flagged |", "| --- | --: | --: | --: | --: | --: | --: | --: | --- |"]
        for var, levels in sg.items():
            for lev, m in levels.items():
                if isinstance(m, str): L.append(f"| {var}={lev} | | | not estimable | | | | | |")
                else: L.append(f"| {var}={lev} | {m['n']:,} | {m['pos']:,} | {f3(m['auroc'])} | {f3(m['auprc'])} | {f3(m['brier'])} | {f3(m['cal_intercept'])} | {f3(m['cal_slope'])} | {'**yes**' if m['material_calibration_difference'] else 'no'} |")
        L.append("")
    L += ["## Interpretation — SHAP (CatBoost, unweighted, 20,000-admission TEST sample; top 25 per feature set)\n"]
    for fs in ["FS-A", "FS-B", "FS-AVAIL"]:
        if fs not in S["shap"]: continue
        share = S["shap"].get(fs + "_availability_share_top25"); L += [f"### {fs} — share of top-25 that are availability/volume features: {share:.0%}\n" if share is not None else f"### {fs}\n", "| rank | feature | class | mean |SHAP| |", "| --: | --- | --- | --: |"]
        for i, r in enumerate(S["shap"][fs], 1): L.append(f"| {i} | {r['feature']} | {r['class']} | {r['mean_abs_shap']:.4f} |")
        L.append("")
    if "FS-A" in S["shap"]:
        top = S["shap"]["FS-A"][:5]; av = sum(r["class"] == "availability" for r in top)
        L.append(f"Plain statement: {av} of the top 5 FS-A attributions are availability or volume indicators. " + ("The model is learning the documentation process — who gets tested, imaged and documented — which is a finding about the data, not a successful clinical model." if av >= 3 else "Clinical values dominate the top attributions in FS-A.") + " The FS-A minus FS-B gap and the FS-AVAIL row quantify how much of the silver label the documentation process alone predicts.\n")
    L += ["## Calibration plots\n", "Reliability diagrams (10 quantile bins, TEST) for every CatBoost row: `docs/figures/aim1b_cal_cat_*.png`.\n", f"Runtime {S.get('runtime_s', 0)/3600:.1f} h."]
    open("docs/aim1b_structured.md", "w").write("\n".join(L) + "\n"); print("wrote docs/aim1b_structured.md")

def report8():
    N = json.load(open(f"{R}/aim1b_notes_tfidf.json")); A = json.load(open(f"{R}/aim1b_notes_arm.json")) if os.path.exists(f"{R}/aim1b_notes_arm.json") else None
    L = ["# Aim 1b — notes arm (run_2026-09-19, Phase 8)\n", DIAG + "\n",
         f"Produced by `scripts/run0919_notes_tfidf.py` and `scripts/run0919_notes_embed_arm.py`; numbers read from `{R}/aim1b_notes_tfidf.json` and `aim1b_notes_arm.json`.\n",
         "**Read this first.** The silver label is produced by a lexical rule applied to the same text a notes model reads, so a notes model can score near-perfectly by relearning the lexicon. Nothing in this phase is an accuracy estimate. Text variants: **U** unmasked; **M** every lexicon match (all tiers, any assertion status) masked; **S** every sentence containing any lexicon match deleted — asking whether the rest of the documentation carries signal. Masking ignores assertion status on purpose: if only affirmed mentions were masked, the mask itself would encode the label. How the notes arm is ultimately trained (trigger masking, or cross-validation within the 400 adjudicated charts, or both) is Kyle's open decision (D-03); this phase selects nothing.\n",
         f"Subsample: DEV {N['sizes']['DEV']:,} · TEST {N['sizes']['TEST']:,} · GOLD_HOLDOUT {N['sizes']['GOLD']:,} (scored, never fitted).\n",
         "## 8.1 TF-IDF + L2 logistic regression (word 1–2-grams, min_df = 100, sublinear tf; vocabulary fit inside training folds)\n", DIAG + "\n", MH.replace("| model |", "| variant · imbalance |")]
    for v, r in N["variants"].items():
        for nm, m in r["test"].items(): L.append(mrow(f"{v} · {nm} (TEST)", m))
    L += ["", "DEV OOF:", "", MH.replace("| model |", "| variant · imbalance |")]
    for v, r in N["variants"].items():
        for nm, m in r["oof"].items(): L.append(mrow(f"{v} · {nm} (OOF)", m))
    L += ["", "Within code-negative TEST admissions:", "", "| variant · imbalance | n | positives | AUROC | AUPRC |", "| --- | --: | --: | --: | --: |"]
    for v, r in N["variants"].items():
        for nm, m in r["test_code_negative_only"].items(): L.append(f"| {v} · {nm} | {m['n']:,} | {m['pos']:,} | {f3(m['auroc'])} | {f3(m['auprc'])} |")
    for v, r in N["variants"].items():
        tt = r["top_terms"]; L += ["", f"### Top coefficients, variant {v} (alphabetic tokens, document frequency ≥ 100; vocabulary {tt['vocab_size']:,})\n", "| positive term | coef | df | | negative term | coef | df |", "| --- | --: | --: | --- | --- | --: | --: |"]
        for a, b in zip(tt["positive"], tt["negative"]): L.append(f"| {a['term']} | {a['coef']} | {a['df']:,} | | {b['term']} | {b['coef']} | {b['df']:,} |")
    L += ["", "Variant U's top terms are expected to be the lexicon itself — that table is the demonstration of circularity. What survives in S is the interesting result.\n"]
    if A:
        L += ["## 8.2 Transformer embeddings (chunked Bio_ClinicalBERT, 1,536-d admission vectors)\n", DIAG + "\n"]
        for v, r in A["embed_heads"].items():
            if isinstance(r, str): L.append(f"- Variant {v}: {r}."); continue
            L += [f"Variant {v}: {r['n_embedded']:,} admissions embedded (DEV {r['n_dev']:,}, TEST {r['n_test']:,}, GOLD {r['n_gold']:,}); head kept by DEV OOF AUPRC: **{r['kept']}**.\n", MH.replace("| model |", "| head · split |")]
            for h, hh in r["heads"].items():
                L.append(mrow(f"{h} · OOF", hh["oof"])); L.append(mrow(f"{h} · TEST", hh["test"]))
            L.append("")
        aug = A["augmented"]; L += [f"## 8.3 Notes-augmented model — CatBoost on FS-B + {aug['extra_features']}\n", DIAG + " " + SILVER + "\n", f"DEV {aug['n_dev']:,} · TEST {aug['n_test']:,}.\n", MH.replace("| model |", "| imbalance · split |")]
        for nm, v in aug["variants"].items():
            L.append(mrow(f"{nm} · OOF", v["oof"])); L.append(mrow(f"{nm} · TEST", v["test"]))
    else: L += ["## 8.2 / 8.3\n", "Embedding-based heads and the notes-augmented model: not available (see RUN_LOG / BLOCKERS)."]
    open("docs/aim1b_notes.md", "w").write("\n".join(L) + "\n"); print("wrote docs/aim1b_notes.md")

def report9():
    F = json.load(open(f"{R}/aim1b_fusion.json"))
    L = ["# Aim 1b — fusion arm (run_2026-09-19, Phase 9.1)\n", F["header"] + "\n", f"Produced by `scripts/run0919_fusion_lock.py`; numbers from `{R}/aim1b_fusion.json`. Locked GOLD_HOLDOUT predictions: `docs/aim1b_locked_predictions.md`.\n",
         f"Layer 0: structured FS-B best-calibrated variant on DEV OOF = `{F['layer0']['structured_FS-B']}` (FS-A sensitivity = `{F['layer0']['structured_FS-A']}`); notes model = `{F['layer0']['notes']}` ({F['layer0']['notes_source']}). Layer 1: logistic regression on the two logits, fit on the subsample's DEV OOF predictions. Code status is never an input.\n",
         "Fusion coefficients: " + "; ".join(f"{k}: intercept {v['intercept']:.3f}, w_structured {v['w_structured']:.3f}, w_notes {v['w_notes']:.3f}" for k, v in F["fusion_coefficients"].items()) + ".\n",
         "## Arms on the same subsample TEST admissions\n", "| arm | n | positives | AUROC | AUPRC | Brier | intercept | slope | code-negative AUROC | code-negative AUPRC |", "| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |"]
    for k, v in F["arms_test"].items():
        a, c = v["all"], v["code_negative_only"]; L.append(f"| {k} | {a['n']:,} | {a['pos']:,} | {f3(a['auroc'])} | {f3(a['auprc'])} | {f3(a['brier'])} | {f3(a['cal_intercept'])} | {f3(a['cal_slope'])} | {f3(c['auroc'])} | {f3(c['auprc'])} |")
    L += ["", "## Paired differences versus the primary structured arm (subject-cluster bootstrap, 500 replicates)\n", "| comparison | ΔAUROC (95% CI) | ΔAUPRC (95% CI) | ΔBrier (95% CI) |", "| --- | --- | --- | --- |"]
    for k, v in F["paired_differences"].items(): L.append(f"| {k} | " + " | ".join(f"{v[m]['mean']:+.3f} ({v[m]['ci'][0]:+.3f}, {v[m]['ci'][1]:+.3f})" for m in ["auroc", "auprc", "brier"]) + " |")
    L += ["", "Every row that includes the notes model inherits the circularity caveat: its silver-label advantage is partly the label's own lexicon. H1b-iii (fusion at least as discriminating as the better base learner and better calibrated) is a silver-label observation here; the gold harness (`scripts/aim1b_evaluate_gold.py`) is what tests it."]
    open("docs/aim1b_fusion.md", "w").write("\n".join(L) + "\n"); print("wrote docs/aim1b_fusion.md")

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for w, f in [("7", report7), ("8", report8), ("9", report9)]:
        if which in (w, "all"):
            try: f()
            except FileNotFoundError as e: print(f"report {w}: missing input {e.filename}")
