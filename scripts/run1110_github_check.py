#!/usr/bin/env python3
"""run_2026-11-10 Phase 10.4 — what can be checked about the remote without a browser, written to
docs/run_2026-11-10/results/github_check.json: the remote head against local HEAD, whether the raw README on
the remote carries the new sub-block and keeps the not-validated banner before it, and the file types added on
the remote since the run began. Read-only: git ls-remote, git diff against the fetched remote, one HTTPS GET of
the raw README. The browser observations are recorded in the run log by hand, as observations, not numbers."""
import collections, json, subprocess, urllib.request

RES = "docs/run_2026-11-10/results"
RAW = "https://raw.githubusercontent.com/kylesellers19/MIMIC_IV/run/2026-09-19/README.md"
TABULAR = (".csv", ".tsv", ".parquet", ".duckdb", ".xlsx", ".xls", ".pkl", ".npy", ".npz", ".gz", ".zip", ".db")


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()


def main():
    first = json.load(open(f"{RES}/preflight.json"))["head"]
    sh("git", "fetch", "-q", "origin")
    head, remote = sh("git", "rev-parse", "HEAD"), sh("git", "ls-remote", "origin", "refs/heads/run/2026-09-19").split()[0]
    readme = urllib.request.urlopen(urllib.request.Request(RAW, headers={"User-Agent": "repo-readme-check"}), timeout=30).read().decode("utf-8", "replace")
    names = sh("git", "diff", "--name-status", "--no-renames", first, remote).splitlines()
    added = [l.split("\t")[1] for l in names if l.startswith("A")]
    ext = collections.Counter(("." + p.rsplit(".", 1)[1]) if "." in p.rsplit("/", 1)[-1] else "(none)" for p in added)
    binary = [l for l in sh("git", "diff", "--numstat", "--no-renames", first, remote).splitlines() if l.startswith("-\t")]
    banner, block = readme.find("Computable stage only"), readme.find("Exploratory, added 10 November 2026")
    out = {"script": "scripts/run1110_github_check.py", "local_head": head, "remote_head": remote, "remote_equals_local": head == remote,
           "raw_readme_has_new_sub_block": block != -1, "banner_comes_before_the_sub_block": 0 <= banner < block,
           "files_added_on_remote_since_run_start": len(added), "added_by_extension": dict(sorted(ext.items())),
           "tabular_files_added": sorted(p for p in added if p.lower().endswith(TABULAR)), "binary_files_changed": len(binary),
           "tags_on_remote": sorted({l.split("refs/tags/")[1].replace("^{}", "") for l in sh("git", "ls-remote", "--tags", "origin").splitlines()})}
    json.dump(out, open(f"{RES}/github_check.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k not in ("added_by_extension",)})


if __name__ == "__main__":
    main()
