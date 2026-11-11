#!/usr/bin/env python3
"""run_2026-11-10 — addendum to docs/admin/data_inventory.md: the untracked locations this run created or
changed. Names, file counts and sizes only. Writes docs/run_2026-11-10/results/data_inventory_addendum.json
and replaces the marked addendum section at the end of the inventory document (September's content is
left as generated)."""
import json, os, subprocess, time

MD = "docs/admin/data_inventory.md"
RES = "docs/run_2026-11-10/results/data_inventory_addendum.json"
START, END = "<!-- run_2026-11-10 addendum: start -->", "<!-- run_2026-11-10 addendum: end -->"
LOCATIONS = [
    ("data/processed/pilot_packets_2026-11-10", "credentialed derivative", "STUDY-TEAM TIMED PILOT, NOT ADJUDICATION: 30 blinded DEV packets (P001–P030), a blank form with `minutes_spent`, a README"),
    ("data/processed/run_2026-11-10_private", "credentialed derivative", "key from pilot IDs to admissions and cells, kept apart from the packets"),
    ("data/processed/section_rule_v2_private", "credentialed derivative", "six diagnostic tables whose `heading` field holds text from notes; moved out of `diagnostics/section_rule_v2/` on 2026-11-10"),
    ("data/processed/llm_review/carryover_check", "credentialed derivative", "carry-over check (amendment k): sample input, strata, model answers, run log"),
    ("data/processed/run_2026-11-10_outpt_fib4.parquet", "credentialed derivative", "most recent outpatient AST, ALT and platelets in the 365 days before each admission (amendment l, sensitivity 4)"),
    ("data/processed/run_2026-11-10_scratch", "credentialed derivative", "push-gate cache of normalised dev/test extractor text; safe to delete"),
    ("logs/run_2026-11-10", "credentialed derivative (policy)", "this run's logs: counts and timings only"),
]


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def measure(p):
    if os.path.isfile(p):
        return 1, os.path.getsize(p)
    files = size = 0
    for root, _, names in os.walk(p):
        for nm in names:
            files += 1; size += os.path.getsize(os.path.join(root, nm))
    return files, size


def main():
    tracked = set(subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.splitlines())
    rows, total = [], 0
    for p, cls, what in LOCATIONS:
        if not os.path.exists(p):
            continue
        files, size = measure(p)
        total += size
        rows.append({"location": p, "classification": cls, "what": what, "n_files": files, "bytes": size, "size": human(size),
                     "tracked_files": sum(1 for t in tracked if t == p or t.startswith(p.rstrip("/") + "/"))})
    out = {"script": "scripts/run1110_data_inventory_addendum.py", "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "locations": rows, "total_bytes": total, "total_size": human(total)}
    json.dump(out, open(RES, "w"), indent=1)
    L = [START, "", "## Added by run_2026-11-10", "",
         f"Generated {out['generated_utc']} by `scripts/run1110_data_inventory_addendum.py` (JSON: `{RES}`). "
         "The sections above are September's inventory, unchanged. Everything below is untracked and git-ignored.", "",
         "| Location | Classification | What it is | Files | Size | Tracked files |", "| --- | --- | --- | --: | --: | --: |"]
    L += [f"| `{r['location']}` | {r['classification']} | {r['what']} | {r['n_files']} | {r['size']} | {r['tracked_files']} |" for r in rows]
    L += ["", f"Total added: {out['total_size']}.", "", END]
    s = open(MD).read()
    if START in s:
        s = s[:s.index(START)].rstrip("\n") + "\n\n"
    else:
        s = s.rstrip("\n") + "\n\n"
    open(MD, "w").write(s + "\n".join(L) + "\n")
    print("addendum:", len(rows), "locations,", out["total_size"])


if __name__ == "__main__":
    main()
