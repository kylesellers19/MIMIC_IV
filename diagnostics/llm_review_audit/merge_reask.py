#!/usr/bin/env python3
"""DIAGNOSTIC: merge the v4 re-ask of the v3 YES/UNCLEAR units into the full v3 run, and compare.

The v4 prompt only adds a NO rule (alcohol-related liver disease, alcoholic hepatitis, cirrhosis or
fibrosis without a fat word), so only units v3 called YES or UNCLEAR were re-asked; v3's NO and
UNPARSED answers are carried over unchanged. Writes data/processed/llm_review/full_v4_merged/
sentence_answers.parquet (no text) and prints counts only:
    1. re-asked units: v3 answer x v4 answer
    2. sentence rows and admission labels, v3 against merged v4
    3. merged primary label against the frozen note rule and by code x note-rule cell

USAGE: scripts/run0919_env.sh diagnostics/llm_review_audit/merge_reask.py
"""
import glob
import json
import os
import sys

import pandas as pd

sys.path.insert(0, ".")
D = "data/processed/llm_review"
OUT = f"{D}/full_v4_merged"


def units(run):
    return pd.concat([pd.read_parquet(f) for f in glob.glob(f"{D}/{run}/shards/*.parquet")]).drop_duplicates("key", keep="last")


def labels(rows):
    yes, unc = rows.answer.eq("YES"), rows.answer.eq("UNCLEAR")
    cp = rows.timing.isin(["CURRENT", "PAST"])
    h = rows.hadm_id
    return pd.DataFrame({
        "primary (YES current/past)": (yes & cp).groupby(h).any(),
        "UNCLEAR counted": ((yes | unc) & cp).groupby(h).any(),
        "CURRENT only": (yes & rows.timing.eq("CURRENT")).groupby(h).any(),
        "anatomy-only selection": (yes & cp & rows.reason.eq("anatomy")).groupby(h).any(),
    })


def main():
    v3, v4 = units("full_v3_devtest"), units("full_v4_reask")
    t = v3[["key", "answer"]].merge(v4[["key", "answer"]], on="key", suffixes=("_v3", "_v4"))
    print(f"re-asked units {len(t):,} (v4 answered {len(v4):,}, errors {int(v4.error.notna().sum())})")
    print(pd.crosstab(t.answer_v3.rename("v3"), t.answer_v4.rename("v4"), margins=True).to_string())

    cols = ["key", "answer", "timing", "p_yes", "p_no", "p_unclear", "strict", "error"]
    merged = pd.concat([v4[cols].assign(source="v4"), v3[~v3.key.isin(v4.key)][cols].assign(source="v3")])
    rows3 = pd.read_parquet(f"{D}/full_v3_devtest/sentence_answers.parquet")
    rows4 = rows3.drop(columns=[c for c in cols if c != "key"]).merge(merged, on="key", how="left")
    os.makedirs(OUT, exist_ok=True)
    rows4.to_parquet(f"{OUT}/sentence_answers.parquet", index=False)
    json.dump({"composition": "v4 answers for units v3 called YES or UNCLEAR; v3 answers for all other units",
               "v3_run": f"{D}/full_v3_devtest", "v4_run": f"{D}/full_v4_reask"}, open(f"{OUT}/README.json", "w"), indent=1)

    print("\nsentence rows:")
    print(pd.DataFrame({"v3": rows3.answer.value_counts(), "merged v4": rows4.answer.value_counts()}).fillna(0).astype(int).to_string())

    sub = pd.read_parquet("data/processed/run_2026-09-19_notes_text/subsample.parquet", columns=["hadm_id", "partition"])
    sub = sub[sub.partition.isin(["DEV", "TEST"])]
    fr = pd.read_parquet("data/processed/aim1a_frame.parquet", columns=["hadm_id", "note_b", "code_positive"])
    a3 = sub.merge(labels(rows3), left_on="hadm_id", right_index=True, how="left").fillna(False)
    a4 = sub.merge(labels(rows4), left_on="hadm_id", right_index=True, how="left").fillna(False)
    rules = list(labels(rows3).columns)
    print(f"\nadmission labels, {len(sub):,} dev/test admissions:")
    print(pd.DataFrame({"v3": a3[rules].sum(), "merged v4": a4[rules].sum()}).astype(int).to_string())

    a4 = a4.merge(fr, on="hadm_id")
    a4["note_b"], a4["code_positive"] = a4.note_b.astype(bool), a4.code_positive.astype(bool)
    p = "primary (YES current/past)"
    print("\nmerged v4 primary (rows) vs frozen note rule (columns):")
    print(pd.crosstab(a4[p].rename("LLM v4"), a4.note_b.rename("note rule"), margins=True).to_string())
    a4["cell"] = a4.code_positive.map({True: "code+", False: "code-"}) + "/" + a4.note_b.map({True: "note+", False: "note-"})
    print("\nmerged v4 primary-positive by code x note-rule cell:")
    print(pd.crosstab(a4.cell, a4[p].rename("LLM v4"), margins=True).to_string())
    print(f"\nmodel-positive admissions without a MASLD code: {int((a4[p] & ~a4.code_positive).sum()):,} of {int(a4[p].sum()):,}")


if __name__ == "__main__":
    main()
