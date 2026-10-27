#!/usr/bin/env python3
"""Lock the LLM phenotype's GOLD_HOLDOUT answers before chart review (the audit trail for the LLM arm).

Reads the completed v4 run over the GOLD_HOLDOUT liver sentences (data/processed/llm_review/gold_v4/),
derives admission labels for every GOLD_HOLDOUT admission with llm_phenotype.admission_labels() (no kept
sentence = negative), writes them to data/processed/llm_review/gold_v4/gold_admission_labels_v4.parquet
(credentialed, untracked), and records SHA-256 hashes of that file, the sentence-level answers, the run
manifest and the input in docs/run_2026-10-27/results/llm_gold_lock.json and docs/llm_gold_lock.md.

The lock record holds hashes, the model and prompt identity, and run counts only. It does NOT report
how many GOLD_HOLDOUT admissions the LLM calls positive: nothing about the answers on the evaluation set
is looked at before the adjudication exists. Refuses to replace an existing lock unless --force.
USAGE: scripts/run0919_env.sh scripts/llm_gold_lock.py [--force]
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

import pandas as pd

sys.path.insert(0, ".")
from scripts import llm_phenotype as LP

G = "data/processed/llm_review/gold_v4"
RUN = f"{G}/run"
INPUT = f"{G}/liver_sentences_gold.parquet"
LABELS = f"{G}/gold_admission_labels_v4.parquet"
LOCK = "docs/run_2026-10-27/results/llm_gold_lock.json"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="replace an existing lock (only before any adjudication exists)")
    a = ap.parse_args()
    if os.path.exists(LOCK) and not a.force:
        sys.exit(f"REFUSING: {LOCK} already exists. Replacing it destroys the record that the LLM's GOLD_HOLDOUT answers "
                 "predate the adjudication; pass --force only if no adjudication exists yet.")
    if not os.path.exists(f"{RUN}/sentence_answers.parquet") or not glob.glob(f"{RUN}/shards/*.parquet"):
        sys.exit(f"REFUSING: the GOLD_HOLDOUT run in {RUN} is not finished and assembled yet")
    man = json.load(open(f"{RUN}/manifest.json"))
    if man["input_sha256"] != sha(INPUT):
        sys.exit("REFUSING: the run manifest does not match the GOLD_HOLDOUT input file")
    units = pd.concat([pd.read_parquet(f) for f in glob.glob(f"{RUN}/shards/*.parquet")]).drop_duplicates("key", keep="last")
    rows = pd.read_parquet(f"{RUN}/sentence_answers.parquet")
    missing = int(rows.answer.isna().sum())
    if missing:
        sys.exit(f"REFUSING: {missing:,} sentence rows have no answer; finish the run (and --retry-errors) first")

    sub = pd.read_parquet(LP.SUBSAMPLE, columns=["hadm_id", "subject_id", "partition"])
    gold = sub[sub.partition == "GOLD_HOLDOUT"][["hadm_id", "subject_id"]]
    lab, _ = LP.admission_labels(rows)
    out = gold.merge(lab, left_on="hadm_id", right_index=True, how="left")
    for c in lab.columns:
        out[c] = out[c].fillna(False).astype(bool)
    out["has_sentence"] = out.hadm_id.isin(set(rows.hadm_id))
    out.to_parquet(LABELS, index=False)

    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    lock = {
        "purpose": "LLM phenotype answers on GOLD_HOLDOUT, hashed before chart review; no answer distribution is reported",
        "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "code_commit": head,
        "files": {p: {"sha256": sha(p), "rows": LP.suppress(n)} for p, n in
                  ((LABELS, len(out)), (f"{RUN}/sentence_answers.parquet", len(rows)), (INPUT, len(rows)))},
        "manifest": {"path": f"{RUN}/manifest.json", "sha256": sha(f"{RUN}/manifest.json")},
        "label_columns": [c for c in out.columns if c not in ("hadm_id", "subject_id")],
        "definition": "llm = >=1 kept sentence YES with timing CURRENT or PAST (amendment h); admissions without a kept sentence are negative",
        "model": {"name": man["model"], "digest": man["model_digest"], "ollama_version": man["ollama_version"],
                  "quantization": (man.get("model_details") or {}).get("quantization_level"),
                  "parameter_size": (man.get("model_details") or {}).get("parameter_size")},
        "prompt": {"variant": man["variant"], "sha256": man["prompt_sha256"], "options": man["options"]},
        "run_counts": {"gold_admissions": LP.suppress(len(out)), "sentence_rows": LP.suppress(len(rows)),
                       "distinct_units": LP.suppress(len(units)), "errors": LP.suppress(units.error.notna().sum()),
                       "unparsed": LP.suppress(units.answer.eq("UNPARSED").sum()),
                       "not_two_word": LP.suppress((units.strict == False).sum())},
        "note": "Dev/test labels (docs/llm_review_preliminary.md) merge v4 answers for units v3 called YES or UNCLEAR with v3's "
                "other answers; GOLD_HOLDOUT is answered by v4 throughout.",
    }
    json.dump(lock, open(LOCK, "w"), indent=1)
    L = ["# LLM phenotype: locked GOLD_HOLDOUT answers\n",
         f"Written by `scripts/llm_gold_lock.py` into `{LOCK}` at {lock['written_utc']} (code at `{head[:12]}`), before chart review.\n",
         "Every GOLD_HOLDOUT admission was labelled by the local LLM, prompt v4 (`docs/llm_review_protocol.md`). "
         "The files below are untracked credentialed derivatives; their SHA-256 hashes are recorded here, so that when "
         "the adjudication exists it can be shown the LLM's answers were fixed first and nothing was tuned against them. "
         "**No answer distribution on GOLD_HOLDOUT is reported or was looked at.**\n",
         "| file | rows | SHA-256 |", "| --- | --: | --- |"]
    L += [f"| `{p}` | {v['rows']:,} | `{v['sha256']}` |" for p, v in lock["files"].items()]
    L += [f"| `{lock['manifest']['path']}` | — | `{lock['manifest']['sha256']}` |", "",
          f"Model: {lock['model']['name']} ({lock['model']['parameter_size']}, {lock['model']['quantization']}), digest "
          f"`{lock['model']['digest']}`, Ollama {lock['model']['ollama_version']}. Prompt {lock['prompt']['variant']}, "
          f"SHA-256 `{lock['prompt']['sha256']}`.", "",
          "Run counts: " + ", ".join(f"{k.replace('_', ' ')} {v:,}" if isinstance(v, int) else f"{k.replace('_', ' ')} {v}"
                                     for k, v in lock["run_counts"].items()) + ".", "",
          lock["note"]]
    open("docs/llm_gold_lock.md", "w").write("\n".join(L) + "\n")
    print(f"locked: {LOCK} and docs/llm_gold_lock.md written; labels file {LABELS}")


if __name__ == "__main__":
    main()
