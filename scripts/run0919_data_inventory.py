#!/usr/bin/env python3
"""run_2026-09-19 Phase 10.6 — inventory of credentialed and derived data locations on this machine.

Emits docs/run_2026-09-19/results/data_inventory.json and docs/admin/data_inventory.md.
Names, sizes, git status and checksum status ONLY. Never opens data files except to
stream bytes through SHA-256; never prints file contents. The SHA256SUMS*.txt manifests
in data/raw/ are parsed by this script (hash + filename lines) and never echoed.

Run: scripts/run0919_env.sh scripts/run0919_data_inventory.py [--no-hash]
"""
import argparse, hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs/run_2026-09-19/results/data_inventory.json"
OUT_MD = ROOT / "docs/admin/data_inventory.md"
HF_HUB = Path.home() / ".cache/huggingface/hub"

# location -> (classification, note)
LOCATIONS = [
    ("data/raw", "credentialed", "PhysioNet MIMIC-IV v3.1 hosp, MIMIC-IV-Note v2.2 raw .csv.gz files (read-only); SHA256SUMS manifests are checksum text only"),
    ("data/processed", "credentialed derivative", "DuckDB/parquet extracts, note index and note text, embeddings, predictions, adjudication keys, private small-cell counts, scratch"),
    ("models", "credentialed derivative", "fitted model weights (git-ignored)"),
    ("logs/run_2026-09-19", "credentialed derivative (policy)", "run logs; aggregate output only by guardrail, but git-ignored as credentialed derivatives under the project's logs/ rule"),
    ("test files", "not credentialed", "open-access MIMIC-IV demo data (per .gitignore comment); git-ignored"),
    ("docs/tables", "aggregate derivative", "aggregate result tables; .md tracked, .csv git-ignored by the *.csv pattern; small cells suppressed by project rule"),
]


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:,.1f} {unit}"
        n /= 1024


def dir_size(p, follow=False):
    """Bytes under p. follow=True counts symlink targets (HF snapshots symlink into blobs/)."""
    total, seen = 0, set()
    for dp, _, fns in os.walk(p):
        for f in fns:
            try:
                st = os.stat(os.path.join(dp, f)) if follow else os.lstat(os.path.join(dp, f))
            except OSError:
                continue
            if (st.st_dev, st.st_ino) in seen:   # symlinked snapshots share blobs; count each blob once
                continue
            seen.add((st.st_dev, st.st_ino)); total += st.st_size
    return total


def tracked_set():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return {s.decode() for s in out.split(b"\0") if s}


def sha256_file(p, chunk=8 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_manifests(raw_dir):
    """Return {basename: {manifest_name: hash}} from data/raw/SHA256SUMS*.txt. Hash lines only."""
    listed = {}
    manifests = sorted(raw_dir.glob("SHA256SUMS*.txt"))
    for m in manifests:
        try:
            for line in m.read_text(errors="replace").splitlines():
                parts = line.strip().split()
                if len(parts) < 2 or len(parts[0]) != 64:
                    continue
                base = os.path.basename(parts[-1].lstrip("*"))
                listed.setdefault(base, {})[m.name] = parts[0].lower()
        except OSError:
            pass
    return [m.name for m in manifests], listed


def list_files(rel, tracked, hash_raw):
    base = ROOT / rel
    entries = []
    if not base.exists():
        return entries
    for dp, dns, fns in os.walk(base):
        dns.sort()
        for f in sorted(fns):
            p = Path(dp) / f
            r = p.relative_to(ROOT).as_posix()
            try:
                size = p.lstat().st_size
            except OSError:
                size = None
            entries.append({"path": r, "bytes": size, "tracked": r in tracked})
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-hash", action="store_true", help="skip SHA-256 of data/raw (fast listing only)")
    args = ap.parse_args()
    t0 = time.time()
    tracked = tracked_set()
    inv = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "machine_note": "paths relative to repository root unless absolute", "locations": []}

    for rel, cls, note in LOCATIONS:
        files = list_files(rel, tracked, False)
        loc = {"path": rel, "classification": cls, "note": note, "exists": (ROOT / rel).exists(),
               "n_files": len(files), "bytes": sum(f["bytes"] or 0 for f in files),
               "n_tracked": sum(f["tracked"] for f in files), "files": files}
        # directory subtotals one level down
        subs = {}
        for f in files:
            parts = f["path"].split("/")
            key = "/".join(parts[: len(rel.split("/")) + 1]) if len(parts) > len(rel.split("/")) + 1 else f["path"]
            subs.setdefault(key, [0, 0])
            subs[key][0] += 1; subs[key][1] += f["bytes"] or 0
        loc["subtotals"] = [{"path": k, "n_files": v[0], "bytes": v[1]} for k, v in sorted(subs.items())]
        inv["locations"].append(loc)

    # ---- checksums for data/raw ----
    raw = ROOT / "data/raw"
    manifest_names, listed = parse_manifests(raw)
    checks = []
    if not args.no_hash:
        for f in inv["locations"][0]["files"]:
            if not f["path"].endswith(".csv.gz"):
                continue
            p = ROOT / f["path"]
            base = os.path.basename(f["path"])
            try:
                digest = sha256_file(p)
            except OSError as e:
                checks.append({"path": f["path"], "status": "unreadable", "error_class": type(e).__name__})
                continue
            refs = listed.get(base, {})
            if not refs:
                status = "not_listed"
            elif all(v == digest for v in refs.values()):
                status = "match"
            elif any(v == digest for v in refs.values()):
                status = "match_some_manifests"
            else:
                status = "mismatch"
            checks.append({"path": f["path"], "status": status, "sha256": digest,
                           "manifests_listing_file": sorted(refs), "manifest_agree": len(set(refs.values())) <= 1})
            f["checksum_status"] = status
    inv["checksums"] = {"manifests": manifest_names, "hashed": not args.no_hash, "files": checks,
                        "summary": {s: sum(c["status"] == s for c in checks) for s in
                                    ("match", "match_some_manifests", "mismatch", "not_listed", "unreadable")}}
    # files listed in manifests but absent on disk (names only)
    on_disk = {os.path.basename(f["path"]) for f in inv["locations"][0]["files"]}
    inv["checksums"]["listed_but_absent"] = sorted(b for b in listed if b not in on_disk)

    # ---- non-data locations: size only ----
    hf_models = []
    if HF_HUB.exists():
        for d in sorted(HF_HUB.glob("models--*")):
            hf_models.append({"path": str(d), "bytes": dir_size(d, follow=True)})
    inv["other"] = {
        "huggingface_cache": {"path": str(HF_HUB), "classification": "not credentialed (public model checkpoints)",
                              "models": hf_models, "bytes": sum(m["bytes"] for m in hf_models),
                              "hub_total_bytes": dir_size(HF_HUB) if HF_HUB.exists() else 0},
        "venv": {"path": ".venv", "classification": "not credentialed (Python environment)",
                 "bytes": dir_size(ROOT / ".venv") if (ROOT / ".venv").exists() else 0},
        "docs_and_code": {"classification": "not credentialed (tracked docs, scripts, sql, tests; aggregates only by guardrail)",
                          "n_tracked_files": len(tracked)},
    }
    inv["elapsed_s"] = round(time.time() - t0, 1)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(inv, indent=1))
    write_md(inv)
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)} in {inv['elapsed_s']} s; "
          f"checksums {inv['checksums']['summary']}")


def write_md(inv):
    L = []
    w = L.append
    w("# Data inventory — credentialed and derived data on this machine (run_2026-09-19, Phase 10.6)\n")
    w(f"Generated {inv['generated_utc']} by `scripts/run0919_data_inventory.py` (JSON: `docs/run_2026-09-19/results/data_inventory.json`). "
      "Names, sizes, git status and checksum status only; no file contents were read except to stream bytes through SHA-256. "
      "Paths are relative to the repository root. `tracked` = present in `git ls-files`; everything else is untracked and, "
      "for the data locations below, git-ignored by `.gitignore`.\n")
    w("## Summary\n")
    w("| Location | Classification | Files | Size | Tracked files |")
    w("|---|---|---:|---:|---:|")
    for loc in inv["locations"]:
        w(f"| `{loc['path']}` | {loc['classification']} | {loc['n_files']} | {human(loc['bytes'])} | {loc['n_tracked']} |")
    o = inv["other"]
    w(f"| `{o['huggingface_cache']['path']}` (model checkpoints) | {o['huggingface_cache']['classification']} | {len(o['huggingface_cache']['models'])} model dirs | {human(o['huggingface_cache']['bytes'])} (hub dir total {human(o['huggingface_cache'].get('hub_total_bytes', 0))}) | 0 |")
    w(f"| `.venv` | {o['venv']['classification']} | — | {human(o['venv']['bytes'])} | 0 |")
    w(f"| tracked docs / code | {o['docs_and_code']['classification']} | {o['docs_and_code']['n_tracked_files']} | — | all |\n")
    w("## What is credentialed PhysioNet data (or a derivative of it)\n")
    w("- **Raw**: every `.csv.gz` under `data/raw/` (MIMIC-IV v3.1 hosp tables; MIMIC-IV-Note v2.2 discharge and radiology notes). Read-only; never decompressed to disk.")
    w("- **Processed derivatives** under `data/processed/`: DuckDB databases and parquet extracts, the note index and extracted note text, chunked Bio_ClinicalBERT embeddings, model predictions, adjudication master keys and sampling frames, private small-cell counts, and scratch outputs. All are patient-level or re-identifiable derivatives and are covered by the PhysioNet DUA.")
    w("- **Fitted models** under `models/` (empty at inventory time if listed as 0 files) and any model weights written elsewhere in `data/processed/` are credentialed derivatives.")
    w("- **Run logs** under `logs/run_2026-09-19/`: aggregate by guardrail, but treated as credentialed derivatives by the project's `.gitignore` policy.")
    w("- **Aggregate tables** `docs/tables/*.csv` and `*.md`: aggregate results with small cells suppressed; the `.csv` copies are git-ignored by the `*.csv` pattern, the `.md` copies are tracked. Not patient-level.\n")
    w("## What is not credentialed data\n")
    w("- `test files/` — open-access MIMIC-IV demo releases (per `.gitignore`), git-ignored.")
    w("- Tracked documentation, scripts, SQL and tests (aggregates only by guardrail).")
    w("- `.venv/` (Python packages) and the Hugging Face cache (public model checkpoints; `HF_HUB_DISABLE_TELEMETRY=1`).\n")
    c = inv["checksums"]
    w("## `data/raw/` checksum verification\n")
    w(f"Manifests found in `data/raw/`: {', '.join('`'+m+'`' for m in c['manifests']) or 'none'}. "
      f"Each `.csv.gz` was hashed with SHA-256 and compared, by file name, against every manifest that lists it. "
      f"Hashed: {c['hashed']}.\n")
    s = c["summary"]
    w(f"**Summary:** match {s['match']} · match in some manifests only {s['match_some_manifests']} · mismatch {s['mismatch']} · not listed {s['not_listed']} · unreadable {s['unreadable']}.\n")
    if c["listed_but_absent"]:
        w("Listed in a manifest but not present on disk (names only): " + ", ".join(f"`{b}`" for b in c["listed_but_absent"]) + ".\n")
    w("| File | Size | Status | Manifests listing it |")
    w("|---|---:|---|---|")
    sizes = {f["path"]: f["bytes"] for f in inv["locations"][0]["files"]}
    for f in c["files"]:
        w(f"| `{f['path']}` | {human(sizes.get(f['path'], 0))} | {f['status']} | {', '.join(f.get('manifests_listing_file', [])) or '—'} |")
    w("")
    for loc in inv["locations"]:
        w(f"## `{loc['path']}` — {loc['classification']}\n")
        w(loc["note"] + "\n")
        if not loc["exists"]:
            w("_Directory not present._\n"); continue
        if loc["path"] in ("data/processed", "test files") and loc["subtotals"]:
            w("| Sub-path | Files | Size |")
            w("|---|---:|---:|")
            for s_ in loc["subtotals"]:
                w(f"| `{s_['path']}` | {s_['n_files']} | {human(s_['bytes'])} |")
            w("")
        w("| File | Size | Tracked |")
        w("|---|---:|---|")
        for f in loc["files"]:
            w(f"| `{f['path']}` | {human(f['bytes'] or 0)} | {'yes' if f['tracked'] else 'no'} |")
        w("")
    w("## Hugging Face cache (model checkpoints only)\n")
    w("| Model directory | Size |")
    w("|---|---:|")
    for m in inv["other"]["huggingface_cache"]["models"]:
        w(f"| `{m['path']}` | {human(m['bytes'])} |")
    w("")
    w(f"## `.venv`\n\nPython environment, {human(inv['other']['venv']['bytes'])}. Not data.\n")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L))


if __name__ == "__main__":
    main()
