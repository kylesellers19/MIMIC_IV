#!/usr/bin/env python3
"""DIAGNOSTIC: why the LLM's primary admission label and the frozen note rule (note_b) disagree.

Applies the frozen rule's own trigger list (scripts/note_phenotype.py TRIGGERS: Tier A definite terms,
Tier B imaging signs) to the kept sentences, and classifies each disagreeing admission by what its
sentences contain and how the LLM answered them. Counts only; text stays in memory.

USAGE: scripts/run0919_env.sh diagnostics/llm_review_audit/disagreement_reasons.py [<sentence_answers.parquet>]
       (default: the full v3 run)
"""
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, ".")
from scripts.note_phenotype import TRIGGERS

D = "data/processed/llm_review"
FOCAL = {"focal fat", "fatty sparing"}


def terms(text):
    low = text.lower()
    a = {name for name, rx, tier, _ in TRIGGERS if tier == "A" and rx.search(low)}
    b = any(rx.search(low) for _, rx, tier, _ in TRIGGERS if tier == "B")
    return a, b


def main():
    ans = pd.read_parquet(sys.argv[1] if len(sys.argv) > 1 else f"{D}/full_v3_devtest/sentence_answers.parquet")
    txt = pd.read_parquet(f"{D}/liver_sentences_devtest_v3.parquet", columns=["hadm_id", "sid", "text"])
    s = ans.merge(txt, on=["hadm_id", "sid"], how="left")
    ab = [terms(t or "") for t in s.text]
    s["tierA"] = [x[0] for x in ab]
    s["tierB"] = [x[1] for x in ab]
    s = s.drop(columns="text")
    s["llm_pos"] = s.answer.eq("YES") & s.timing.isin(["CURRENT", "PAST"])

    sub = pd.read_parquet("data/processed/run_2026-09-19_notes_text/subsample.parquet", columns=["hadm_id", "partition"])
    sub = sub[sub.partition.isin(["DEV", "TEST"])]
    fr = pd.read_parquet("data/processed/aim1a_frame.parquet", columns=["hadm_id", "note_b"])
    adm = sub.merge(fr, on="hadm_id")
    llm = s.groupby("hadm_id").llm_pos.any()
    adm["llm"] = adm.hadm_id.map(llm).fillna(False).astype(bool)
    adm["rule"] = adm.note_b.astype(bool)
    g = dict(tuple(s.groupby("hadm_id")))

    # model yes, rule no
    why = Counter()
    for h in adm.hadm_id[adm.llm & ~adm.rule]:
        pos = g[h][g[h].llm_pos]
        if any(len(a) for a in pos.tierA):
            why["a rule term is in a sentence the model called YES (the rule rejected it: negation, hedge, organ or scoping)"] += 1
        elif pos.tierB.any():
            why["imaging sign only, e.g. echogenic liver (the rule's primary definition leaves these out)"] += 1
        else:
            why["wording outside the rule's term list"] += 1
    n1 = int((adm.llm & ~adm.rule).sum())
    print(f"model YES, rule no: {n1} admissions")
    for k, v in why.most_common():
        print(f"  {v:>4}  {k}")
    pos_all = pd.concat([g[h][g[h].llm_pos] for h in adm.hadm_id[adm.llm & ~adm.rule]])
    print(f"  timing of those YES sentences: {pos_all.timing.value_counts().to_dict()}")

    # rule yes, model no
    why = Counter()
    for h in adm.hadm_id[~adm.llm & adm.rule]:
        d = g.get(h)
        if d is None:
            why["no kept sentence at all"] += 1
            continue
        hit = d[[len(a) > 0 for a in d.tierA]]
        if hit.empty:
            why["no rule term in any kept sentence (the rule's hit is elsewhere in the note)"] += 1
        elif hit.answer.eq("YES").any():
            why["model said YES but FAMILY only (not counted)"] += 1
        elif all(a <= FOCAL for a in hit.tierA):
            why["only focal fat / fatty sparing (rule counts focal fat; the model's rules say focal fat = NO)"] += 1
        elif hit.answer.eq("UNCLEAR").any():
            why["model called the rule's sentence UNCLEAR (hedged)"] += 1
        else:
            why["model called the rule's sentence NO"] += 1
    n2 = int((~adm.llm & adm.rule).sum())
    print(f"\nrule yes, model no: {n2} admissions")
    for k, v in why.most_common():
        print(f"  {v:>4}  {k}")


if __name__ == "__main__":
    main()
