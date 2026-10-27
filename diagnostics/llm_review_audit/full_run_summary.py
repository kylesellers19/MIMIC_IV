#!/usr/bin/env python3
"""DIAGNOSTIC: count-only summary of a full LLM review run (default: full_v3_devtest).

    1. distinct units and sentence rows: answers, timing, reply format, stop reasons, low confidence
    2. sentence rows by note type, selection reason and partition
    3. admission labels under the proposed rules (docs/llm_review_protocol.md §5) for every dev/test
       admission in the notes subsample (no kept sentence = negative), by partition
    4. primary admission label against the frozen note rule (note_b) and against code status

PRIVACY: counts only. No text is read.
USAGE: scripts/run0919_env.sh diagnostics/llm_review_audit/full_run_summary.py [<run dir>]
"""
import glob
import json
import sys

import pandas as pd

sys.path.insert(0, ".")
from scripts.masld_config import SPLITS_V1

RUN = sys.argv[1] if len(sys.argv) > 1 else "data/processed/llm_review/full_v3_devtest"


def main():
    man = json.load(open(f"{RUN}/manifest.json"))
    units = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{RUN}/shards/*.parquet"))]).drop_duplicates("key", keep="last")
    rows = pd.read_parquet(f"{RUN}/sentence_answers.parquet")
    sp = pd.read_parquet(SPLITS_V1, columns=["hadm_id", "partition"])
    rows = rows.merge(sp, on="hadm_id", how="left")
    print(f"run {RUN} | variant {man['variant']} | model {man['model']} ({man['model_digest'][:12]}) | ollama {man['ollama_version']}")
    print(f"distinct units {len(units):,} | sentence rows {len(rows):,} | admissions with a sentence {rows.hadm_id.nunique():,}")
    print(f"partitions in rows: {rows.partition.value_counts().to_dict()}")

    pmax = units[["p_yes", "p_no", "p_unclear"]].max(axis=1)
    print(f"\nunits: two-word {int(units.strict.sum()):,} | errors {int(units.error.notna().sum())} | "
          f"stop reasons {units.done_reason.value_counts().to_dict()} | first-word p<0.90 {int((pmax < 0.9).sum()):,} | "
          f"mean seconds {units.seconds.mean():.2f}")
    for name, d in (("distinct units", units), ("sentence rows", rows)):
        print(f"{name:<15} " + " | ".join(f"{k} {v:,} ({100 * v / len(d):.2f}%)" for k, v in d.answer.value_counts().items()))
    pos = rows[rows.answer.isin(["YES", "UNCLEAR"])]
    print("timing among YES/UNCLEAR rows:")
    print(pd.crosstab(pos.answer, pos.timing).to_string())

    for col in ("note_type", "reason", "partition"):
        t = pd.crosstab(rows[col], rows.answer, margins=True)
        t["YES %"] = (100 * t.get("YES", 0) / t["All"]).round(2)
        print(f"\nsentence rows by {col}:\n{t.to_string()}")

    sub = pd.read_parquet("data/processed/run_2026-09-19_notes_text/subsample.parquet", columns=["hadm_id", "partition"])
    sub = sub[sub.partition.isin(["DEV", "TEST"])]
    fr = pd.read_parquet("data/processed/aim1a_frame.parquet", columns=["hadm_id", "note_b", "code_positive"])
    g = rows.groupby("hadm_id")
    yes, unc = rows.answer.eq("YES"), rows.answer.eq("UNCLEAR")
    cur_past = rows.timing.isin(["CURRENT", "PAST"])
    lab = pd.DataFrame({
        "primary (YES current/past)": (yes & cur_past).groupby(rows.hadm_id).any(),
        "UNCLEAR counted": ((yes | unc) & cur_past).groupby(rows.hadm_id).any(),
        "CURRENT only": (yes & rows.timing.eq("CURRENT")).groupby(rows.hadm_id).any(),
        "anatomy-only selection": (yes & cur_past & rows.reason.eq("anatomy")).groupby(rows.hadm_id).any(),
        "any FAMILY mention": (yes & rows.timing.eq("FAMILY")).groupby(rows.hadm_id).any(),
    })
    adm = sub.merge(lab, left_on="hadm_id", right_index=True, how="left").fillna(False)
    adm = adm.merge(fr, on="hadm_id", how="left")
    print(f"\nadmission labels, {len(adm):,} dev/test subsample admissions (no kept sentence = negative):")
    rules = [c for c in lab.columns]
    t = adm.groupby("partition")[rules].sum().astype(int)
    t.loc["All"] = t.sum()
    t["admissions"] = adm.groupby("partition").size().reindex(t.index[:-1]).tolist() + [len(adm)]
    print(t.to_string())
    adm["note_b"] = adm.note_b.astype(bool)
    print("\nprimary LLM label (rows) vs frozen note rule note_b (columns):")
    print(pd.crosstab(adm["primary (YES current/past)"].rename("LLM primary"), adm.note_b.rename("note rule"), margins=True).to_string())
    adm["code_positive"] = adm.code_positive.astype(bool)
    print("\nprimary LLM label (rows) vs MASLD code (columns):")
    print(pd.crosstab(adm["primary (YES current/past)"].rename("LLM primary"), adm.code_positive.rename("code"), margins=True).to_string())
    print("\nLLM primary-positive admissions by 2x2 cell (code x note rule):")
    adm["cell"] = (adm.code_positive.map({True: "code+", False: "code-"}) + "/" + adm.note_b.map({True: "note+", False: "note-"}))
    print(pd.crosstab(adm.cell, adm["primary (YES current/past)"].rename("LLM primary"), margins=True).to_string())


if __name__ == "__main__":
    main()
