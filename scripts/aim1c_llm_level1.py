#!/usr/bin/env python3
"""Aim 1c level 1 with the LLM note phenotype (analysis-plan amendment i, S16). Exploratory.

In the dev/test notes subsample, by race, insurance, sex, language and age band:
    coverage  share of admissions with >=1 kept liver sentence (seen before amendment i; descriptive)
    E1        recovery share B/(A+B) under the frozen rule, the LLM phenotype and rule-or-LLM, and the
              paired difference LLM minus rule
    E2        among admissions positive by either method: share positive by exactly one, LLM only, rule only
    E3        among uncoded LLM-positive admissions: share whose YES evidence is in the discharge summary,
              inpatient radiology only, or outpatient radiology only
Subject-cluster bootstrap (500 replicates, seed 20260919), 95% percentile intervals. Disclosure control
for the public repository: only each stratum's admission count is shown, never the count behind a
percentage; a percentage is withheld when its count or complement is 1-10 (E3: all three withheld when
any is); strata under 11 admissions are not shown. A difference is described only when its interval is
no wider than 20 percentage points (level 1's rule). Writes docs/run_2026-10-27/results/aim1c_llm_level1.json
and docs/aim1c_llm_level1.md.
USAGE: scripts/run0919_env.sh scripts/aim1c_llm_level1.py
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts import llm_phenotype as LP

REPS, SEED, WIDE, FLOOR = 500, 20260919, 20.0, LP.FLOOR
STRATA = ["race", "insurance", "sex", "language", "age_band"]
ENCOUNTER_CHAR = {"UNKNOWN", "UNABLE TO OBTAIN", "PATIENT DECLINED TO ANSWER"}


def main():
    a = LP.load()
    codes, idx = np.unique(a.subject_id.to_numpy(), return_inverse=True)
    W = np.random.default_rng(SEED).multinomial(len(codes), np.full(len(codes), 1 / len(codes)), size=REPS).astype(float)

    def per_subject(mask):
        return np.bincount(idx, weights=mask.astype(float), minlength=len(codes))

    def ratio(num, den, within):
        """Point estimate and bootstrap interval of sum(num)/sum(den) within a stratum, in percent."""
        n_num, n_den = int((num & within).sum()), int((den & within).sum())
        if n_den < FLOOR or 0 < n_num < FLOOR or 0 < n_den - n_num < FLOOR:
            return None
        pn, pd_ = per_subject(num & within), per_subject(den & within)
        with np.errstate(divide="ignore", invalid="ignore"):
            bs = 100 * (W @ pn) / (W @ pd_)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        return {"est": round(100 * n_num / n_den, 1), "lo": round(float(lo), 1), "hi": round(float(hi), 1),
                "claim_supported": bool(hi - lo <= WIDE)}

    def paired_diff(num1, den1, num2, den2, within):
        """(num2/den2 - num1/den1) in percentage points, paired bootstrap; None if either side is withheld."""
        if ratio(num1, den1, within) is None or ratio(num2, den2, within) is None:
            return None
        a1, d1, a2, d2 = (per_subject(x & within) for x in (num1, den1, num2, den2))
        with np.errstate(divide="ignore", invalid="ignore"):
            bs = 100 * ((W @ a2) / (W @ d2) - (W @ a1) / (W @ d1))
        est = 100 * (float((num2 & within).sum()) / float((den2 & within).sum()) - float((num1 & within).sum()) / float((den1 & within).sum()))
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        return {"est": round(est, 1), "lo": round(float(lo), 1), "hi": round(float(hi), 1), "claim_supported": bool(hi - lo <= WIDE)}

    rule, llm, code, has = a.rule.to_numpy(), a.llm.to_numpy(), a.code.to_numpy(), a.has_sentence.to_numpy()
    either = rule | llm
    every = np.ones(len(a), bool)
    upos = llm & ~code
    paths = {p: (a.pathway == p).to_numpy() for p in LP.PATHWAYS}
    out = {"status": "exploratory (amendment i)", "scope": "dev/test notes subsample", "admissions": LP.suppress(len(a)),
           "bootstrap": {"reps": REPS, "seed": SEED}, "wide_pp": WIDE, "strata": {}}
    levels = [("overall", "all", every)] + [(v, lv, (a[v].astype(str) == lv).to_numpy())
                                           for v in STRATA for lv in sorted(a[v].astype(str).unique())]
    for var, lv, m in levels:
        n = int(m.sum())
        if n < FLOOR:
            continue
        e3 = {p: ratio(paths[p] & upos, upos, m) for p in LP.PATHWAYS}
        if any(0 < int((paths[p] & upos & m).sum()) < FLOOR for p in LP.PATHWAYS):
            e3 = {p: None for p in LP.PATHWAYS}
        out["strata"].setdefault(var, {})[lv] = {
            "admissions": LP.suppress(n), "encounter_characteristic": lv in ENCOUNTER_CHAR,
            "coverage": ratio(has, every, m),
            "E1_recovery_rule": ratio(rule & ~code, rule, m),
            "E1_recovery_llm": ratio(llm & ~code, llm, m),
            "E1_recovery_either": ratio(either & ~code, either, m),
            "E1_llm_minus_rule": paired_diff(rule & ~code, rule, llm & ~code, llm, m),
            "E2_discordant": ratio(either & (rule != llm), either, m),
            "E2_llm_only": ratio(llm & ~rule, either, m),
            "E2_rule_only": ratio(rule & ~llm, either, m),
            "E3_pathway": e3,
        }
        print(f"  {var}={lv} done", flush=True) if var == "overall" else None
    res = f"{LP.results_dir()}/aim1c_llm_level1.json"
    json.dump(out, open(res, "w"), indent=1)
    write_doc(out, res)
    print(f"wrote {res} and docs/aim1c_llm_level1.md")


def cell(x):
    if x is None:
        return "—"
    return f"{x['est']} ({x['lo']}–{x['hi']}){'' if x['claim_supported'] else ' †'}"


def write_doc(r, src):
    L = ["# Aim 1c level 1 with the LLM note phenotype\n",
         "> **Exploratory (analysis-plan amendment i, committed before any of these stratum results were computed).** "
         "Computable stage only: nothing here is validated against chart review. Numbers are written by "
         f"`scripts/aim1c_llm_level1.py` into `{src}`.\n",
         f"Scope: the dev/test notes subsample ({r['admissions']:,} admissions), a simple random sample of dev/test subjects. "
         "LLM phenotype: `docs/llm_review_protocol.md` (v4). Percentages with 95% subject-cluster bootstrap intervals "
         f"({r['bootstrap']['reps']} replicates).\n",
         "**Reading the tables.** "
         "Only each stratum's admission count is shown, never the count behind a percentage. "
         "— means withheld (the count or its complement is 1–10, or the denominator is under 11). "
         f"† means the interval is wider than {r['wide_pp']:.0f} percentage points, so no claim is made. "
         "* marks a category that describes the encounter rather than the person.\n"]
    sections = [
        ("Recovery share (E1): % of note-positive admissions with no MASLD code",
         [("Rule", "E1_recovery_rule"), ("LLM", "E1_recovery_llm"), ("Either", "E1_recovery_either"),
          ("LLM − rule (pp)", "E1_llm_minus_rule")]),
        ("Rule–LLM discordance (E2): % of admissions positive by either method",
         [("Exactly one", "E2_discordant"), ("LLM only", "E2_llm_only"), ("Rule only", "E2_rule_only")]),
        ("Where uncoded LLM-positive cases are documented (E3): %",
         [("Discharge summary", ("E3_pathway", LP.PATHWAYS[0])), ("Inpatient radiology only", ("E3_pathway", LP.PATHWAYS[1])),
          ("Outpatient radiology only", ("E3_pathway", LP.PATHWAYS[2]))]),
        ("Coverage (described before amendment i): % of admissions with ≥1 kept liver sentence", [("Coverage", "coverage")]),
    ]
    for title, cols in sections:
        L += [f"## {title}\n"]
        for var, levels in r["strata"].items():
            L += [f"**{var}**\n", "| Stratum | Admissions | " + " | ".join(c for c, _ in cols) + " |",
                  "| --- | --: | " + " | ".join("--:" for _ in cols) + " |"]
            for lv, x in sorted(levels.items(), key=lambda kv: -(kv[1]["admissions"] if isinstance(kv[1]["admissions"], int) else 0)):
                vals = [cell(x[k] if isinstance(k, str) else x[k[0]][k[1]]) for _, k in cols]
                adm = x["admissions"]
                L.append(f"| {lv}{' *' if x['encounter_characteristic'] else ''} | {adm:,} | " + " | ".join(vals) + " |"
                         if isinstance(adm, int) else f"| {lv} | {adm} | " + " | ".join(vals) + " |")
            L.append("")
    open("docs/aim1c_llm_level1.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
