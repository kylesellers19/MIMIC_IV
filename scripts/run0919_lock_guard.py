#!/usr/bin/env python3
"""run_2026-09-19 — refuse to overwrite files recorded in the GOLD_HOLDOUT prediction lock.
scripts/run0919_fusion_lock.py hashes every model file and every per-arm *_gold.parquet into LOCK_JSON. A model script that
rewrites one of them leaves the lock describing files that no longer exist, so each calls refuse_if_locked() with the names it
writes (fnmatch patterns over the lock's recorded basenames) before doing any work. --force overrides; re-lock afterwards with
scripts/run0919_fusion_lock.py --force, which records the superseded lock."""
import fnmatch, json, os, sys
LOCK_JSON = "docs/run_2026-09-19/results/locked_predictions.json"

def refuse_if_locked(patterns, force):
    if not os.path.exists(LOCK_JSON): return
    L = json.load(open(LOCK_JSON)); script = os.path.basename(sys.argv[0])
    hit = sorted(n for n in list(L["models"]) + list(L["prediction_files"]) if any(fnmatch.fnmatch(n, p) for p in patterns))
    if not hit: return
    if not force:
        sys.exit(f"REFUSING: {script} would overwrite {len(hit)} file(s) whose hashes the lock written {L['written_utc']} records ({LOCK_JSON}): "
                 f"{', '.join(hit)}. Pass --force only if the models must be refit and no adjudication exists yet; then re-lock with "
                 "scripts/run0919_fusion_lock.py --force.")
    print(f"--force: overwriting {len(hit)} locked file(s); {LOCK_JSON} no longer matches them until scripts/run0919_fusion_lock.py --force is re-run", flush=True)
