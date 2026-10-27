#!/usr/bin/env python3
"""DIAGNOSTIC: count-only summary of the v3 development pilot (data/processed/llm_review/pilot_v3/).

    1. each run: answers, timing, reply format, stop reason, speed, low-confidence share
    2. determinism: v3 against its rerun
    3. prompt sensitivity: each variant against v3 (agreement, kappa, direction of changes)
    4. v3 answers by selection reason and note type, weighted and unweighted by occurrences
    5. admission sample: admission labels under the proposed rules, against the frozen note rule

PRIVACY: counts only; no text is read beyond what the runner already keyed.
USAGE: scripts/run0919_env.sh diagnostics/llm_review_audit/pilot_v3_summary.py [<runs dir>]
       (default runs dir: the pilot folder itself; the second, cache-friendly layout is in layout2/)
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts.llm_sentence_review import ANSWERS, load_input

P = "data/processed/llm_review/pilot_v3"          # inputs
RUNS = sys.argv[1] if len(sys.argv) > 1 else P   # run directories
ARMS = ["v3", "v3_rerun", "v3_paraphrase_a", "v3_paraphrase_b", "v3_fewshot", "v3_context"]


def answers(run):
    s = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{RUNS}/{run}/shards/*.parquet"))])
    return s.drop_duplicates("key", keep="last")


def kappa(x, y):
    x, y = np.asarray(x), np.asarray(y)
    po = float((x == y).mean())
    labels = sorted(set(x) | set(y))
    pe = sum(float((x == l).mean()) * float((y == l).mean()) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    rows = {}
    for arm in ARMS:
        variant = json.load(open(f"{RUNS}/run_{arm}/manifest.json"))["variant"]
        inp = load_input(f"{P}/pilot500_input.parquet", variant)
        a = inp[["sid", "hadm_id", "reason", "note_type", "occurrences", "key"]].merge(answers(f"run_{arm}"), on="key")
        rows[arm] = a.set_index("sid")
        sec = a.seconds.iloc[10:].mean()
        pmax = a[["p_yes", "p_no", "p_unclear"]].max(axis=1)
        print(f"\n== {arm} (variant {variant}) n={len(a)} | {1 / sec:.2f}/s | two-word {int(a.strict.sum())} | "
              f"stop reasons {a.done_reason.value_counts().to_dict()} | first-word p<0.90: {int((pmax < 0.9).sum())}")
        print("   answers: " + " | ".join(f"{k} {v}" for k, v in a.answer.value_counts().items())
              + "   timing (YES/UNCLEAR): " + " | ".join(f"{k} {v}" for k, v in a[a.answer.isin(['YES', 'UNCLEAR'])].timing.value_counts().items()))

    base = rows["v3"]
    rr = rows["v3_rerun"].loc[base.index]
    print(f"\ndeterminism: v3 vs rerun identical answer {(base.answer == rr.answer).sum()}/500, "
          f"identical answer+timing {((base.answer == rr.answer) & (base.timing == rr.timing)).sum()}/500, "
          f"max |p_yes difference| {np.nanmax(np.abs(base.p_yes.astype(float) - rr.p_yes.astype(float))):.4f}")

    print("\nprompt sensitivity, each variant against v3 (answer word):")
    for arm in ARMS[2:]:
        o = rows[arm].loc[base.index]
        same = int((o.answer == base.answer).sum())
        ch = pd.crosstab(base.answer.rename("v3"), o.answer.rename(arm))
        moves = {f"{i}->{j}": int(ch.loc[i, j]) for i in ch.index for j in ch.columns if i != j and ch.loc[i, j]}
        print(f"  {arm:<16} agree {same}/500 | kappa {kappa(base.answer, o.answer):.3f} | changes {moves}")
    yes_any = pd.concat([rows[a].loc[base.index].answer.eq("YES") for a in ["v3", *ARMS[2:]]], axis=1)
    print(f"  sentences YES under v3: {int(yes_any.iloc[:, 0].sum())} | YES under any variant: {int(yes_any.any(axis=1).sum())} | "
          f"YES under all variants: {int(yes_any.all(axis=1).sum())}")

    print("\nv3 answers by selection reason (distinct units; occurrence-weighted share YES in brackets):")
    t = pd.crosstab(base.reason, base.answer, margins=True)
    print(t.to_string())
    w = base.occurrences.astype(float)
    print(f"  occurrence-weighted: YES {100 * w[base.answer == 'YES'].sum() / w.sum():.1f}% | "
          f"UNCLEAR {100 * w[base.answer == 'UNCLEAR'].sum() / w.sum():.1f}% (unweighted YES {100 * (base.answer == 'YES').mean():.1f}%)")
    print(pd.crosstab(base.note_type, base.answer, margins=True).to_string())

    # admission sample
    inp = load_input(f"{P}/admissions100_input.parquet", "v3")
    a = inp[["hadm_id", "reason", "key"]].merge(answers("adm100_v3"), on="key", how="left")
    g = a.groupby("hadm_id")
    lab = pd.DataFrame({
        "primary (YES current/past)": g.apply(lambda d: bool(((d.answer == "YES") & d.timing.isin(["CURRENT", "PAST"])).any())),
        "UNCLEAR counted": g.apply(lambda d: bool((d.answer.isin(["YES", "UNCLEAR"]) & d.timing.isin(["CURRENT", "PAST"])).any())),
        "CURRENT only": g.apply(lambda d: bool(((d.answer == "YES") & (d.timing == "CURRENT")).any())),
        "anatomy-only selection": g.apply(lambda d: bool(((d.answer == "YES") & d.timing.isin(["CURRENT", "PAST"]) & (d.reason == "anatomy")).any())),
    })
    fr = pd.read_parquet("data/processed/aim1a_frame.parquet", columns=["hadm_id", "note_b"])
    lab = lab.join(fr.set_index("hadm_id").note_b.astype(bool).rename("frozen note rule"))
    print(f"\nadmission sample: {len(lab)} DEV admissions, {len(a)} sentences, unanswered {int(a.answer.isna().sum())}")
    for c in lab.columns:
        print(f"  {c:<28} positive {int(lab[c].sum())}")
    print("  primary vs frozen note rule:")
    print(pd.crosstab(lab["primary (YES current/past)"].rename("LLM primary"), lab["frozen note rule"]).to_string())


if __name__ == "__main__":
    main()
