#!/usr/bin/env python3
"""run_2026-11-10 Phase 0 — preflight facts, written to docs/run_2026-11-10/results/preflight.json.

Facts only: git position, uncommitted/untracked path names, the frozen-hash result, the integrity gate,
the test suite, and the local-model checks (Ollama version, study-model digest, cloud-disabled log line,
listener address, disk encryption). No data file is read.
"""
import json, os, re, subprocess, sys, urllib.request

RES = "docs/run_2026-11-10/results"
EXPECT = {"ollama_version": "0.34.2", "model": "gemma4:26b", "digest_prefix": "08ae7ec1"}


def sh(*a, **k):
    r = subprocess.run(a, capture_output=True, text=True, **k)
    return (r.stdout + r.stderr).strip()


def get(path):
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=15) as r:
        return json.load(r)


def main():
    out = {"script": "scripts/run1110_preflight.py"}
    out["branch"] = sh("git", "branch", "--show-current")
    out["head"] = sh("git", "rev-parse", "HEAD")
    out["origin_head"] = sh("git", "rev-parse", "origin/run/2026-09-19")
    base = sh("git", "merge-base", "HEAD", "origin/run/2026-09-19")
    out["local_contains_origin"] = base == out["origin_head"]
    st = [l for l in sh("git", "status", "--porcelain", "--untracked-files=all").splitlines() if l.strip()]
    out["uncommitted_paths"] = sorted(l.split(maxsplit=1)[1] for l in st if not l.lstrip().startswith("??"))
    out["untracked_paths"] = sorted(l.split(maxsplit=1)[1] for l in st if l.lstrip().startswith("??"))
    fh = json.load(open(f"{RES}/frozen_hashes_start.json"))
    out["frozen_hashes"] = {"n_frozen": fh["n_frozen"], "n_locked": fh["n_locked"],
                            "lock_mismatches": len(fh["lock_mismatches"]), "missing": len(fh["missing"]),
                            "all_pass": fh["all_pass"]}
    ig = json.load(open("docs/run_2026-09-19/results/integrity_gate.json"))
    out["integrity_gate"] = {"checks": len(ig["checks"]), "passed": sum(ig["checks"].values()), "all_pass": ig["all_pass"]}
    t = sh("zsh", "scripts/run0919_env.sh", "-m", "pytest", "-q")
    m = re.search(r"(\d+) passed", t); f = re.search(r"(\d+) failed", t)
    out["pytest"] = {"passed": int(m.group(1)) if m else 0, "failed": int(f.group(1)) if f else 0}
    try:
        ver = get("/api/version")["version"]
        tag = next((x for x in get("/api/tags")["models"] if x["name"] == EXPECT["model"]), None)
        out["ollama"] = {"version": ver, "model": EXPECT["model"], "digest": tag and tag["digest"],
                         "matches_run_file": ver == EXPECT["ollama_version"] and bool(tag)
                         and tag["digest"].startswith(EXPECT["digest_prefix"])}
    except Exception as e:
        out["ollama"] = {"error": type(e).__name__, "matches_run_file": False}
    log = os.path.expanduser("~/.ollama/logs/server.log")
    cloud = [l for l in open(log, errors="replace") if "Ollama cloud disabled" in l] if os.path.exists(log) else []
    out["ollama"]["cloud_disabled_log_line"] = cloud[-1].split("msg=")[-1].strip().strip('"') if cloud else None
    ls = [l.split() for l in sh("lsof", "-nP", "-iTCP:11434", "-sTCP:LISTEN").splitlines()[1:]]
    out["ollama"]["listeners_11434"] = sorted({l[8] for l in ls if len(l) > 8})
    out["ollama"]["loopback_only"] = bool(ls) and all(l[8].startswith("127.0.0.1:") for l in ls if len(l) > 8)
    out["filevault"] = sh("fdesetup", "status")
    issues = []
    if out["branch"] != "run/2026-09-19": issues.append("not on run/2026-09-19")
    if not out["local_contains_origin"]: issues.append("local does not contain origin/run/2026-09-19")
    if not out["frozen_hashes"]["all_pass"]: issues.append("frozen/locked hash mismatch (HARD HALT)")
    if not out["integrity_gate"]["all_pass"]: issues.append("integrity gate not 14/14")
    if out["pytest"]["failed"] or not out["pytest"]["passed"]: issues.append("pytest failures")
    if not out["ollama"].get("matches_run_file"): issues.append("Ollama version/digest differs: Phase 4 will be skipped")
    if not out["ollama"].get("loopback_only"): issues.append("port 11434 not loopback-only")
    if out["ollama"].get("cloud_disabled_log_line") != "Ollama cloud disabled: true": issues.append("cloud-disabled line not found")
    if "On" not in out["filevault"]: issues.append("FileVault not on")
    out["issues"] = issues
    json.dump(out, open(f"{RES}/preflight.json", "w"), indent=1)
    print("PREFLIGHT PASSED — safe to leave" if not issues else "PREFLIGHT ISSUES: " + "; ".join(issues))


if __name__ == "__main__":
    main()
