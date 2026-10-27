#!/usr/bin/env python3
"""Preliminary results of the local-LLM sentence review (amendment h), for the public repository.

Reads the run outputs under data/processed/llm_review/ (credentialed, untracked) and writes
docs/run_2026-10-27/results/llm_review_preliminary.json and docs/llm_review_preliminary.md.
Every count from 1 to 10 is published as "<11", and a percentage is withheld when its numerator,
denominator or complement is below 11. No text is read beyond what the classification of
disagreements needs in memory; none is written.

Nothing here is validated against human review.
USAGE: scripts/run0919_env.sh scripts/llm_review_results.py
"""
import glob
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts import llm_phenotype as LP
from scripts.llm_sentence_review import load_input
from scripts.note_phenotype import TRIGGERS

D = "data/processed/llm_review"
S = LP.suppress


def units(run):
    return pd.concat([pd.read_parquet(f) for f in glob.glob(f"{D}/{run}/shards/*.parquet")]).drop_duplicates("key", keep="last")


def F(v):
    return f"{v:,}" if isinstance(v, (int, np.integer)) else str(v)


def counts(series):
    return {str(k): S(v) for k, v in series.value_counts().items()}


def kappa(x, y):
    x, y = np.asarray(x), np.asarray(y)
    po = float((x == y).mean())
    pe = sum(float((x == l).mean()) * float((y == l).mean()) for l in set(x) | set(y))
    return round((po - pe) / (1 - pe), 3)


def run_facts():
    out = {}
    for run in ("full_v3_devtest", "full_v4_reask"):
        m = json.load(open(f"{D}/{run}/manifest.json"))
        u = units(run)
        out[run] = {"variant": m["variant"], "model": m["model"], "model_digest": m["model_digest"][:12],
                    "ollama_version": m["ollama_version"], "units": S(len(u)), "errors": S(u.error.notna().sum()),
                    "unparsed": S(u.answer.eq("UNPARSED").sum()), "compute_hours": round(u.seconds.sum() / 3600, 1)}
    return out


def pilot_facts():
    P = f"{D}/pilot_v3"
    base = None
    out = {"n": 500, "partition": "DEV"}
    for arm in ("v3", "v3_rerun", "v3_paraphrase_a", "v3_paraphrase_b", "v3_fewshot", "v3_context"):
        v = json.load(open(f"{P}/layout2/run_{arm}/manifest.json"))["variant"]
        k = load_input(f"{P}/pilot500_input.parquet", v)[["sid", "key"]]
        a = k.merge(units(f"pilot_v3/layout2/run_{arm}")[["key", "answer"]], on="key").set_index("sid").answer
        if base is None:
            base = a
            out["v3_answers"] = counts(a)
            continue
        a = a.loc[base.index]
        if arm == "v3_rerun":
            out["rerun_identical"] = S((a == base).sum())
        else:
            out[f"kappa_{arm}"] = kappa(base, a)
    return out


def disagreement_reasons(a):
    r = pd.read_parquet(LP.ANSWERS)
    txt = pd.read_parquet(f"{D}/liver_sentences_devtest_v3.parquet", columns=["hadm_id", "sid", "text"])
    r = r[r.hadm_id.isin(set(a.hadm_id))].merge(txt, on=["hadm_id", "sid"], how="left")
    low = r.text.fillna("").str.lower()
    r["tierA"] = [any(rx.search(t) for _, rx, tier, _ in TRIGGERS if tier == "A") for t in low]
    r["tierB"] = [any(rx.search(t) for _, rx, tier, _ in TRIGGERS if tier == "B") for t in low]
    r["fatword"] = low.str.contains(r"echogen|hyperecho|bright|attenuat|hounsfield|\bhu\b|\bfatty\b|\bfat\b|steato", regex=True)
    r = r.drop(columns="text")
    r["pos"] = r.answer.eq("YES") & r.timing.isin(["CURRENT", "PAST"])
    g = dict(tuple(r.groupby("hadm_id")))
    llm_only, rule_only = {}, {}
    for h in a.hadm_id[a.llm & ~a.rule]:
        p = g[h][g[h].pos]
        k = ("rule term present, rejected by the rule" if p.tierA.any() else
             "imaging sign only (outside the rule's primary definition)" if p.tierB.any() else
             "fat or imaging wording outside the rule's term list" if p.fatword.any() else
             "no fat-related word (unexplained)")
        llm_only[k] = llm_only.get(k, 0) + 1
    for h in a.hadm_id[~a.llm & a.rule]:
        d = g.get(h)
        hit = d[d.tierA] if d is not None else None
        k = ("no rule term in any kept sentence" if hit is None or hit.empty else
             "model answered UNCLEAR" if hit.answer.eq("UNCLEAR").any() else
             "model answered YES with FAMILY timing only" if hit.answer.eq("YES").any() else
             "model answered NO")
        rule_only[k] = rule_only.get(k, 0) + 1
    return {k: S(v) for k, v in llm_only.items()}, {k: S(v) for k, v in rule_only.items()}


def main():
    a = LP.load()
    scale = LP.subject_scale(a)
    rows = pd.read_parquet(LP.ANSWERS)
    res = {"status": "PRELIMINARY - not validated against human review", "scope": "dev/test notes subsample",
           "admissions": S(len(a)), "subjects": S(a.subject_id.nunique()),
           "subject_scale_to_all_dev_test": round(scale, 2)}
    res["runs"] = run_facts()
    res["pilot_dev"] = pilot_facts()
    res["filter"] = {sel: json.load(open(f"{D}/audit/filter_misses_{sel}.json"))
                     for sel in ("anatomy_only", "current")}
    res["sentences"] = {"rows": S(len(rows)), "answers": counts(rows.answer),
                        "yes_pct_by_note_type": {k: LP.pct((g.answer == "YES").sum(), len(g)) for k, g in rows.groupby("note_type")},
                        "yes_pct_by_reason": {k: LP.pct((g.answer == "YES").sum(), len(g)) for k, g in rows.groupby("reason")},
                        "rows_by_reason": counts(rows.reason)}
    res["admission_labels"] = {c: S(a[c].sum()) for c in ("llm", "llm_unclear", "llm_current", "llm_anatomy", "rule")}
    # LLM against the rule among UNCODED admissions only: the coded group's rule-by-LLM cells include counts
    # below 11, and publishing the comparison on all admissions would let them be recovered by subtraction.
    n = a[~a.code]
    res["llm_vs_rule_uncoded"] = {"admissions": S(len(n)), "both": S((n.llm & n.rule).sum()),
                                  "llm_only": S((n.llm & ~n.rule).sum()), "rule_only": S((~n.llm & n.rule).sum()),
                                  "neither": S((~n.llm & ~n.rule).sum()),
                                  "rule_positive_confirmed_by_llm_pct": LP.pct((n.llm & n.rule).sum(), n.rule.sum()),
                                  "rule_negative_llm_positive_pct": LP.pct((n.llm & ~n.rule).sum(), (~n.rule).sum())}
    c = a[a.code]
    res["coded_admissions"] = {"admissions": S(len(c)), "llm_positive": S(c.llm.sum()), "rule_positive": S(c.rule.sum())}
    subj = a.groupby("subject_id")
    anycode = subj.code.any()
    unc = {}
    for name, col in (("rule", a.rule), ("llm", a.llm), ("either", a.rule | a.llm), ("both", a.rule & a.llm)):
        adm = int((col & ~a.code).sum())
        s_pos = col.groupby(a.subject_id).any()
        sj = int((s_pos & ~anycode).sum())
        unc[name] = {"admissions": S(adm), "subjects": S(sj),
                     "admissions_scaled": int(round(adm * scale, -2)), "subjects_scaled": int(round(sj * scale, -2)),
                     "pct_uncoded_admissions": LP.pct(adm, col.sum()), "pct_uncoded_subjects": LP.pct(sj, s_pos.sum())}
    unc["coded_subjects_scaled"] = int(round(int(anycode.sum()) * scale, -2))
    res["documented_not_coded"] = unc
    pw = {}
    for coded, lab in ((False, "uncoded"), (True, "coded")):
        x = a[a.llm & (a.code == coded)]
        pw[lab] = {"n": S(len(x)), **{p: LP.pct((x.pathway == p).sum(), len(x)) for p in LP.PATHWAYS},
                   "past_only_pct": LP.pct((x.llm & ~x.llm_current).sum(), len(x))}
    res["documentation_pathway"] = pw
    lo, ro = disagreement_reasons(a[~a.code])
    res["disagreement"] = {"llm_only": lo, "rule_only": ro}
    res["coverage_pct_with_sentence"] = LP.pct(a.has_sentence.sum(), len(a))

    out = f"{LP.results_dir()}/llm_review_preliminary.json"
    json.dump(res, open(out, "w"), indent=1)
    write_doc(res, out)
    print(f"wrote {out} and docs/llm_review_preliminary.md")


def write_doc(r, src):
    u, lv, f = r["documented_not_coded"], r["llm_vs_rule_uncoded"], r["filter"]
    pw, pl = r["documentation_pathway"], r["pilot_dev"]
    L = ["# Local-LLM review of liver sentences: preliminary results\n",
         "> **PRELIMINARY and exploratory (analysis-plan amendment h).** Nothing here is validated against human review. "
         "Every number is written by `scripts/llm_review_results.py` into "
         f"`{src}`. Counts from 1 to 10 appear as <11.\n",
         f"Scope: the dev/test notes subsample, {r['admissions']:,} admissions of {r['subjects']:,} subjects (a simple random "
         f"sample of dev/test subjects). Scaled figures multiply by {r['subject_scale_to_all_dev_test']}, the ratio of all "
         "dev/test subjects to sampled subjects, and are rounded to the nearest 100. Method: `docs/llm_review_protocol.md`.\n",
         "## Documented in notes, never coded\n",
         "| Note phenotype | Admissions (sample) | Subjects (sample) | Subjects, scaled | Share of note-positive subjects uncoded |",
         "| --- | --: | --: | --: | --: |"]
    for k, lab in (("both", "Rule and LLM agree"), ("rule", "Frozen keyword rule"), ("llm", "Local LLM (v4)"), ("either", "Either")):
        x = u[k]
        L.append(f"| {lab} | {F(x['admissions'])} | {F(x['subjects'])} | ~{x['subjects_scaled']:,} | {x['pct_uncoded_subjects']}% |")
    L += [f"\nFor comparison, subjects with a MASLD code, scaled: ~{u['coded_subjects_scaled']:,}.\n",
          "## The LLM against the frozen rule, uncoded admissions\n",
          "Restricted to admissions without a MASLD code, where recovery happens; the coded group is reported only as totals, "
          "because its rule-by-LLM cells include counts below 11.\n",
          "| | Rule positive | Rule negative |", "| --- | --: | --: |",
          f"| **LLM positive** | {F(lv['both'])} | {F(lv['llm_only'])} |",
          f"| **LLM negative** | {F(lv['rule_only'])} | {F(lv['neither'])} |",
          f"\nThe LLM confirms {lv['rule_positive_confirmed_by_llm_pct']}% of the rule's uncoded positives and finds steatosis in "
          f"{lv['rule_negative_llm_positive_pct']}% of the admissions the rule calls negative. Coded admissions: "
          f"{F(r['coded_admissions']['admissions'])}, of which the LLM calls {F(r['coded_admissions']['llm_positive'])} positive "
          f"and the rule {F(r['coded_admissions']['rule_positive'])}.\n"]
    L += ["\nWhy the LLM alone calls an uncoded admission positive:\n"] + [f"- {k}: {F(v)}" for k, v in r["disagreement"]["llm_only"].items()]
    L += ["\nWhy the rule alone calls an uncoded admission positive:\n"] + [f"- {k}: {F(v)}" for k, v in r["disagreement"]["rule_only"].items()]
    L += ["\n## Where uncoded cases are documented\n",
          "| LLM-positive admissions | n | Discharge summary | Inpatient radiology only | Outpatient radiology only | Past mentions only |",
          "| --- | --: | --: | --: | --: | --: |"]
    for k in ("uncoded", "coded"):
        x = pw[k]
        L.append(f"| {k} | {F(x['n'])} | {x['discharge summary']}% | {x['inpatient radiology only']}% | "
                 f"{x['outpatient radiology only']}% | {x['past_only_pct']}% |")
    L += ["\n## Method checks\n",
          f"- Sentence selection: admissions whose steatosis statement never reached the model fell from "
          f"{f['anatomy_only']['admissions_strong_term_only_dropped']:,} (anatomy-only) to {f['current']['admissions_strong_term_only_dropped']:,}; "
          f"rule-positive admissions with no steatosis or echogenicity word in any kept sentence fell from "
          f"{f['anatomy_only']['rule_positive_no_term_in_kept']:,} to {f['current']['rule_positive_no_term_in_kept']}.",
          f"- Dev pilot of {pl['n']} sentences: identical answers on rerun {pl['rerun_identical']}/{pl['n']}; Cohen's kappa against v3 "
          f"for the paraphrases {pl['kappa_v3_paraphrase_a']} and {pl['kappa_v3_paraphrase_b']}, few-shot {pl['kappa_v3_fewshot']}, "
          f"neighbouring-sentence context {pl['kappa_v3_context']}.",
          f"- Full run (v3): {r['runs']['full_v3_devtest']['units']:,} distinct units, {r['runs']['full_v3_devtest']['errors']} errors, "
          f"{r['runs']['full_v3_devtest']['unparsed']} unparsed, {r['runs']['full_v3_devtest']['compute_hours']} model-hours; "
          f"v4 re-ask of YES/UNCLEAR units: {r['runs']['full_v4_reask']['units']:,} units, {r['runs']['full_v4_reask']['errors']} errors.",
          f"- YES rate by selection reason (sentence rows, %): " + ", ".join(f"{k} {v}" for k, v in r["sentences"]["yes_pct_by_reason"].items()) + ".",
          "\n## Caveats\n",
          "- The prompt was revised twice on information that included TEST (amendment h); TEST is not independent of prompt development.",
          "- Both phenotypes are automated readings of the same notes; neither is the reference standard. The 400-chart review decides.",
          "- Scaled figures assume the subsample's subjects represent all dev/test subjects (simple random sampling makes this reasonable; GOLD_HOLDOUT subjects are excluded)."]
    open("docs/llm_review_preliminary.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
