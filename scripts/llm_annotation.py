#!/usr/bin/env python3
"""Blinded human annotation of LLM-reviewed liver sentences: build the workbooks, then score them.

BUILD
    From a sentence file (liver_sentences.py output, or a pilot drawn from it) write one workbook per
    annotator: items in a random order (seed), each with the note type, heading, previous sentence,
    the SENTENCE, the next sentence, and blank cells for ANSWER (YES / NO / UNCLEAR), TIMING (CURRENT /
    PAST / FAMILY / NA) and a comment. No model output, admission id or sampling stratum appears in a
    workbook. A separate key file links item ids to sentence ids; it stays with the analyst. Optional
    --weights-from carries each item's sampling weight (e.g. `occurrences`) into the key file.
    Annotators follow docs/adjudication/llm_sentence_annotation_guide.md and must be PhysioNet-credentialed.

SCORE
    Reads the completed workbooks and one or more LLM run directories, and prints counts only:
      - agreement between annotators (Cohen's kappa on ANSWER, raw agreement on TIMING);
      - consensus = the two annotators where they agree; disagreements are listed by item id for an
        adjudicator, whose workbook (--adjudicated) overrides them;
      - for each LLM run: confusion matrix against consensus, sensitivity / PPV / specificity with
        Wilson 95% intervals, under both UNCLEAR mappings (UNCLEAR counted negative, and positive), and
        weighted by the key file's weight column when present.

PRIVACY
    Workbooks hold sentence text and live under data/ (git-ignored). The scorer prints no text.

USAGE
    scripts/run0919_env.sh scripts/llm_annotation.py build --input <sentences.parquet> \\
        --out data/processed/llm_review/annotation/<set> --annotators A B --weights-from occurrences
    scripts/run0919_env.sh scripts/llm_annotation.py score --set data/processed/llm_review/annotation/<set> \\
        --runs <run dir> [<run dir> ...] [--adjudicated <workbook>]
"""
import argparse
import glob
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts.llm_sentence_review import ANSWERS, TIMINGS, VARIANTS, check_out, unit_key

SEED = 20260923
COLUMNS = ["item_id", "note_type", "heading", "previous_sentence", "SENTENCE", "next_sentence",
           "ANSWER", "TIMING", "comment"]
NOTE_LABEL = {"discharge": "discharge summary", "radiology_inpatient": "radiology report",
              "radiology_outpatient": "radiology report"}


def build(a):
    check_out(a.out)
    df = pd.read_parquet(a.input).reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(df))
    items = df.iloc[order].reset_index(drop=True)
    items["item_id"] = [f"S{i + 1:04d}" for i in range(len(items))]
    os.makedirs(a.out, exist_ok=False)
    key_cols = ["item_id", "hadm_id", "sid"] + [c for c in ("note_type", "heading", "reason") if c in items.columns]
    key = items[key_cols].copy()
    for f in ("text", "note_type", "heading", "prev_text", "next_text"):
        if f not in items.columns:
            items[f] = ""
    key["text_unit_keys"] = [{v: unit_key(r, VARIANTS[v][1]) for v in VARIANTS}
                             for r in items[["text", "note_type", "heading", "prev_text", "next_text"]].to_dict("records")]
    key["weight"] = items[a.weights_from].astype(float) if a.weights_from else 1.0
    key.to_pickle(os.path.join(a.out, "key.pkl"))
    sheet = pd.DataFrame({
        "item_id": items.item_id,
        "note_type": items.note_type.map(NOTE_LABEL).fillna(items.note_type),
        "heading": items.heading, "previous_sentence": items.prev_text, "SENTENCE": items.text,
        "next_sentence": items.next_text, "ANSWER": "", "TIMING": "", "comment": ""})
    for who in a.annotators:
        path = os.path.join(a.out, f"annotator_{who}.xlsx")
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            sheet.to_excel(w, index=False, sheet_name="items")
            pd.DataFrame({"field": ["ANSWER", "TIMING"],
                          "allowed values": [", ".join(ANSWERS), ", ".join(TIMINGS)],
                          "instructions": ["docs/adjudication/llm_sentence_annotation_guide.md"] * 2}
                         ).to_excel(w, index=False, sheet_name="read me")
    print(f"wrote {len(a.annotators)} workbook(s) of {len(sheet):,} items and key.pkl to {a.out}")


def read_sheet(path):
    s = pd.read_excel(path, sheet_name="items", dtype=str).fillna("")
    s["ANSWER"] = s.ANSWER.str.strip().str.upper()
    s["TIMING"] = s.TIMING.str.strip().str.upper()
    bad = s[(s.ANSWER != "") & ~s.ANSWER.isin(ANSWERS) | (s.TIMING != "") & ~s.TIMING.isin(TIMINGS)]
    if len(bad):
        sys.exit(f"{path}: {len(bad)} item(s) with values outside the allowed lists, e.g. {', '.join(bad.item_id.head(5))}")
    return s[["item_id", "ANSWER", "TIMING"]]


def kappa(x, y, labels):
    x, y = np.asarray(x), np.asarray(y)
    po = float((x == y).mean())
    pe = sum(float((x == l).mean()) * float((y == l).mean()) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def score(a):
    key = pd.read_pickle(os.path.join(a.set, "key.pkl"))
    sheets = sorted(glob.glob(os.path.join(a.set, "annotator_*.xlsx")))
    if len(sheets) < 2:
        sys.exit("need two completed annotator workbooks")
    s1, s2 = read_sheet(sheets[0]), read_sheet(sheets[1])
    m = key.merge(s1, on="item_id").merge(s2, on="item_id", suffixes=("_1", "_2"))
    done = m[(m.ANSWER_1 != "") & (m.ANSWER_2 != "")]
    print(f"items {len(m):,} | annotated by both {len(done):,}")
    print(f"ANSWER: raw agreement {100 * (done.ANSWER_1 == done.ANSWER_2).mean():.1f}% | "
          f"Cohen's kappa {kappa(done.ANSWER_1, done.ANSWER_2, ANSWERS):.3f}")
    both_yes = done[(done.ANSWER_1 == "YES") & (done.ANSWER_2 == "YES")]
    if len(both_yes):
        print(f"TIMING on items both called YES: agreement {100 * (both_yes.TIMING_1 == both_yes.TIMING_2).mean():.1f}%")
    done = done.copy()
    done["truth"] = np.where(done.ANSWER_1 == done.ANSWER_2, done.ANSWER_1, "")
    if a.adjudicated:
        adj = read_sheet(a.adjudicated).set_index("item_id").ANSWER
        fill = done.item_id.map(adj).fillna("")
        done.loc[done.truth == "", "truth"] = fill[done.truth == ""]
    open_items = done.item_id[done.truth == ""].tolist()
    print(f"consensus available {int((done.truth != '').sum()):,} | awaiting adjudication {len(open_items):,}"
          + (f": {', '.join(open_items[:40])}{' ...' if len(open_items) > 40 else ''}" if open_items else ""))
    gold = done[done.truth != ""]
    print("consensus labels: " + " | ".join(f"{k} {v:,}" for k, v in gold.truth.value_counts().items()))
    for run in a.runs:
        variant = pd.read_json(os.path.join(run, "manifest.json"), typ="series")["variant"]
        ans = pd.concat([pd.read_parquet(f) for f in glob.glob(os.path.join(run, "shards", "*.parquet"))]) \
            .drop_duplicates("key", keep="last").set_index("key").answer
        g = gold.copy()
        g["model"] = [ans.get(k[variant]) for k in g.text_unit_keys]
        g = g[g.model.notna()]
        print(f"\n== {os.path.basename(run.rstrip('/'))} (variant {variant}), {len(g):,} items with both labels")
        print(pd.crosstab(g.truth.rename("human"), g.model.rename("model"), margins=True).to_string())
        for mapping, pos in (("UNCLEAR counted negative", {"YES"}), ("UNCLEAR counted positive", {"YES", "UNCLEAR"})):
            t, p, w = g.truth.isin(pos), g.model.isin(pos), g.weight.astype(float)
            tp, fn, fp, tn = (t & p), (t & ~p), (~t & p), (~t & ~p)
            sens, sl, sh = wilson(int(tp.sum()), int(t.sum()))
            ppv, pl, ph = wilson(int(tp.sum()), int(p.sum()))
            spec, cl, ch = wilson(int(tn.sum()), int((~t).sum()))
            ws = float(w[tp].sum() / w[t].sum()) if w[t].sum() else float("nan")
            wp = float(w[tp].sum() / w[p].sum()) if w[p].sum() else float("nan")
            print(f"  {mapping:<26} sensitivity {sens:.3f} ({sl:.3f}-{sh:.3f}) | PPV {ppv:.3f} ({pl:.3f}-{ph:.3f}) | "
                  f"specificity {spec:.3f} ({cl:.3f}-{ch:.3f}) | weighted sens {ws:.3f} PPV {wp:.3f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--input", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--annotators", nargs="+", default=["A", "B"])
    b.add_argument("--weights-from", default=None)
    s = sub.add_parser("score")
    s.add_argument("--set", required=True)
    s.add_argument("--runs", nargs="+", required=True)
    s.add_argument("--adjudicated", default=None)
    a = ap.parse_args()
    build(a) if a.cmd == "build" else score(a)


if __name__ == "__main__":
    main()
