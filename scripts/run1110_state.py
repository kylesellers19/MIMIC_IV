#!/usr/bin/env python3
"""run_2026-11-10 — update docs/run_2026-11-10/STATE.json after a phase (status, commit, start, end).

usage: run1110_state.py <phase> <status> [--start] [--commit HASH] [--note TEXT] [--key K=V ...]
"""
import argparse, json, os, subprocess, time

PATH = "docs/run_2026-11-10/STATE.json"
NAMES = {"0": "preflight", "1": "exposure risk closed + push gate", "2": "record corrected (documents)",
         "3": "amendments (k)-(o), S18-S22", "4": "carry-over check (background)", "5": "exploratory analyses (l)-(o)",
         "6": "materials for prospective reviewers", "7": "manuscript drafts: language-model arm",
         "8": "citations", "9": "decisions file", "10": "README, push, check on GitHub",
         "11": "final audit, report, notification"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase"); ap.add_argument("status")
    ap.add_argument("--start", action="store_true"); ap.add_argument("--commit"); ap.add_argument("--note")
    ap.add_argument("--key", action="append", default=[])
    a = ap.parse_args()
    s = json.load(open(PATH)) if os.path.exists(PATH) else {
        "run_id": "run_2026-11-10", "run_branch": "run/2026-09-19", "started_utc": now(), "push": True, "phases": {}}
    p = s["phases"].setdefault(a.phase, {"name": NAMES.get(a.phase, "")})
    p["status"] = a.status
    if a.start or "start" not in p:
        p["start"] = now()
    if a.status in ("done", "skipped", "partial", "blocked"):
        p["end"] = now()
    if a.commit:
        p["commit"] = subprocess.run(["git", "rev-parse", a.commit], capture_output=True, text=True).stdout.strip()
    if a.note:
        p["note"] = a.note
    for kv in a.key:
        k, v = kv.split("=", 1)
        s[k] = {"true": True, "false": False}.get(v, v)
    json.dump(s, open(PATH, "w"), indent=1)
    print(a.phase, p)


if __name__ == "__main__":
    main()
