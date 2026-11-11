#!/usr/bin/env python3
"""run_2026-11-10 Phase 0.4 / 11.1 — hash the frozen artifacts; verify the two GOLD_HOLDOUT locks.

Files are only hashed (opened in binary mode, streamed into SHA-256); nothing is parsed, so the
sealed GOLD_HOLDOUT files are never read as data. Writes
  docs/run_2026-11-10/results/frozen_hashes_{start,end}.json
and, with --when end, compares against the start file. Exit status 1 on any mismatch (hard halt).
"""
import argparse, hashlib, json, os, sys

RES = "docs/run_2026-11-10/results"
LLM_LOCK = "docs/run_2026-10-27/results/llm_gold_lock.json"
PRED_LOCK = "docs/run_2026-09-19/results/locked_predictions.json"
MODEL_DIR = "models/run_2026-09-19"
PRED_DIR = "data/processed/run_2026-09-19_preds"

# Guardrail 5: the frozen rule, the sample, the splits, the locked predictions, the lock files.
FROZEN = [
    "scripts/note_phenotype.py", "docs/note_phenotype_spec.md", "sql/masld_coded.sql",
    "data/processed/analysis_population_clean.parquet",
    "data/processed/aim1a_sample.parquet",
    "data/processed/aim1a_training_key.parquet",
    "data/processed/splits_v1.parquet",
    LLM_LOCK, PRED_LOCK, "docs/llm_gold_lock.md", "docs/aim1b_locked_predictions.md",
]
APPEND_ONLY = ["scripts/masld_config.py"]  # hashed for the record; checked by diff, not by equality


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def locked_expectations():
    """path -> recorded sha256, from the two lock files."""
    exp = {}
    L = json.load(open(LLM_LOCK))
    for p, rec in L["files"].items():
        exp[p] = rec["sha256"]
    exp[L["manifest"]["path"]] = L["manifest"]["sha256"]
    P = json.load(open(PRED_LOCK))
    exp[P["file"]] = P["sha256"]
    for name, rec in P["models"].items():
        exp[os.path.join(MODEL_DIR, name)] = rec["sha256"]
    for name, h in P["prediction_files"].items():
        exp[os.path.join(PRED_DIR, name)] = h
    return exp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--when", choices=["start", "end"], required=True)
    a = ap.parse_args()
    exp = locked_expectations()
    out = {"frozen": {}, "append_only": {}, "locked": {}, "lock_mismatches": [], "missing": []}
    for p in FROZEN:
        if not os.path.exists(p):
            out["missing"].append(p); continue
        out["frozen"][p] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
    for p in APPEND_ONLY:
        out["append_only"][p] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
    for p, want in sorted(exp.items()):
        if not os.path.exists(p):
            out["missing"].append(p); continue
        got = sha(p)
        out["locked"][p] = {"sha256": got, "bytes": os.path.getsize(p), "matches_lock": got == want}
        if got != want:
            out["lock_mismatches"].append(p)
    out["n_frozen"] = len(out["frozen"]); out["n_locked"] = len(out["locked"])
    drift = []
    if a.when == "end":
        start = json.load(open(f"{RES}/frozen_hashes_start.json"))
        for grp in ("frozen", "locked"):
            for p, rec in start[grp].items():
                now = out[grp].get(p)
                if now is None or now["sha256"] != rec["sha256"]:
                    drift.append(p)
        out["drift_from_start"] = drift
    out["all_pass"] = not out["lock_mismatches"] and not out["missing"] and not drift
    json.dump(out, open(f"{RES}/frozen_hashes_{a.when}.json", "w"), indent=1)
    print(f"frozen {out['n_frozen']} · locked {out['n_locked']} · lock mismatches {len(out['lock_mismatches'])} "
          f"· missing {len(out['missing'])} · drift {len(drift)} · all_pass {out['all_pass']}")
    for p in out["lock_mismatches"] + out["missing"] + drift:
        print("  PROBLEM:", p)
    sys.exit(0 if out["all_pass"] else 1)


if __name__ == "__main__":
    main()
