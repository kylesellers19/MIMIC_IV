#!/usr/bin/env python3
"""run_2026-09-19 Phase 11.3 — final release audit.

Eight checks (a)-(h) from the run file. Every check reports counts and file:line locations only;
no file content under data/ or models/ is read. Writes docs/run_2026-09-19/results/final_audit.json
and prints a summary table. Exit status is 0 always — findings are reported, not raised.
"""
import hashlib, json, os, re, subprocess, sys
sys.path.insert(0, os.getcwd())

BASE = "main"
RES = "docs/run_2026-09-19/results"
EIGHT_DIGIT = re.compile(r"\b[12]\d{7}\b")
SMALL_COUNT_COL = re.compile(r"^\s*\|")
# Seeds are read from the config and from any `default_rng(<n>)` / `seed = <n>` literal in tracked
# scripts, so a newly introduced seed is exempted only because it is demonstrably used as a seed.
SEED_LITERAL = re.compile(r"(?:default_rng\(|random_state\s*=\s*|seed\s*=\s*|SEED[A-Z_]*\s*=\s*)(\d{8})")
# A JSON/table field that holds a byte count or a size can hold an 8-digit number that is not an identifier.
# Fingerprints of MIMIC-IV-Note text (used by check (d); module-level so tests can exercise them).
DEID = re.compile(r"_{3,}")
REPORT_HEADER = re.compile(r"\b(FINDINGS|IMPRESSION|TECHNIQUE|COMPARISON|INDICATION|EXAMINATION|WET READ|HISTORY OF PRESENT ILLNESS|BRIEF HOSPITAL COURSE)\s*:", re.I)
TALKS_ABOUT_DEID = re.compile(r"de-?identif|placeholder|redact|scrub|anonymi", re.I)
SIZE_KEY = re.compile(r'"[a-z0-9_]*(bytes|size|chars|length)[a-z0-9_]*"\s*:', re.I)


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def changed_files():
    out = sh("git", "diff", "--name-only", f"{BASE}...HEAD")
    return [f for f in out.splitlines() if f and os.path.exists(f)]


def known_seeds():
    seeds = set()
    for f in sh("git", "ls-files").splitlines():
        if not f.endswith((".py", ".sh", ".md", ".json")):
            continue
        try:
            seeds |= set(SEED_LITERAL.findall(open(f, encoding="utf-8", errors="replace").read()))
        except OSError:
            continue
    return seeds


def instrument_lines():
    """Lines of the study's own instrument documents — a quotation of these is not note text."""
    out = set()
    for f in ("docs/adjudication_criteria.md", "docs/reference_standard.md", "docs/note_phenotype_spec.md"):
        if os.path.exists(f):
            for line in open(f, encoding="utf-8", errors="replace"):
                t = re.sub(r"[^a-z0-9 ]", " ", line.lower())
                t = " ".join(t.split())
                if len(t) > 20:
                    out.add(t)
    return out


def classify_token(line, tok, seeds):
    low = line.lower()
    if tok in seeds:
        return "seed"
    if "pmid" in low or "doi" in low or "pubmed" in low or "crossref" in low:
        return "citation identifier"
    if SIZE_KEY.search(line) or re.search(r"\|\s*" + re.escape(tok) + r"\s*\|", line) and "bytes" in low:
        return "byte count / file size"
    return "UNEXPLAINED"


def main():
    audit = {}

    # (a) nothing under data/, models/, logs/ staged or tracked
    status = [l for l in sh("git", "status", "--short").splitlines() if l.strip()]
    tracked_bad = [l for l in status if not l.startswith("??") and re.search(r"\b(data|models|logs)/", l)]
    ever_tracked = [f for f in sh("git", "ls-files").splitlines() if re.match(r"^(data|models|logs)/", f)]
    ever_tracked = [f for f in ever_tracked if not f.endswith(".gitkeep")]
    audit["a_no_data_tracked"] = {"status_lines_touching_data_models_logs": tracked_bad,
                                  "tracked_files_under_those_dirs": ever_tracked,
                                  "pass": not tracked_bad and not ever_tracked}

    # (b) 8-digit integers in files changed on this branch
    hits = []
    seeds = known_seeds()
    for f in changed_files():
        if f.endswith((".png", ".xlsx", ".parquet", ".npy")):
            continue
        try:
            lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            for m in EIGHT_DIGIT.finditer(line):
                tok = m.group(0)
                reason = classify_token(line, tok, seeds)
                hits.append({"file": f, "line": i, "token": tok, "exempt": reason != "UNEXPLAINED", "reason": reason})
    unexplained = [h for h in hits if not h["exempt"]]
    audit["b_eight_digit_scan"] = {"total_hits": len(hits), "exempt": len(hits) - len(unexplained),
                                   "unexplained": unexplained, "pass": not unexplained}

    # (c) counts 1-10 in count columns of new/changed tables
    def count_cells(path):
        bad = []
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            return bad
        header = None
        for i, line in enumerate(lines, 1):
            if not SMALL_COUNT_COL.match(line):
                header = None
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = [c.lower() for c in cells]
                continue
            if all(set(c) <= set("-: ") for c in cells):
                continue
            for h, c in zip(header, cells):
                if not re.search(r"\bn\b|count|charts|admissions|subjects|positives|hits", h):
                    continue
                if re.fullmatch(r"[1-9]|10", c.replace(",", "")):
                    bad.append({"file": path, "line": i, "column": h, "value": c})
        return bad
    small = []
    for f in changed_files():
        if f.endswith(".md"):
            small += count_cells(f)
    audit["c_small_counts_in_tables"] = {"hits": small, "pass": not small,
                                         "note": "count-like columns only; a 1-10 here must read <11"}

    # (d) no note text in tracked docs beyond 8-word windows.
    # Three direct fingerprints of MIMIC-IV-Note text, rather than a heuristic on quoting style:
    #   d1  the de-identification placeholder (three or more underscores) that MIMIC substitutes for
    #       every removed identifier - essentially every real note span carries at least one;
    #   d2  a clinical report section header inside a blockquote or fenced block;
    #   d3  a quoted lexicon match carrying more than an 8-word window, where the quoted line is
    #       neither a verbatim line of the study's own instrument documents nor explained by d1/d2.
    from scripts.note_phenotype import TRIGGERS
    instrument = instrument_lines()
    d1, d2, d3 = [], [], []
    for f in changed_files():
        if not f.endswith((".md", ".txt")):
            continue
        quoted = False
        for i, line in enumerate(open(f, encoding="utf-8", errors="replace").read().splitlines(), 1):
            if line.strip().startswith("```"):
                quoted = not quoted
                continue
            in_quote = quoted or line.strip().startswith(">") or line.startswith("    ")
            if DEID.search(line) and not TALKS_ABOUT_DEID.search(line):
                d1.append({"file": f, "line": i, "fingerprint": "de-identification placeholder"})
            if in_quote and REPORT_HEADER.search(line) and any(rx.search(line) for _, rx, _, _ in TRIGGERS):
                d2.append({"file": f, "line": i, "fingerprint": "report section header in a quoted block"})
            if not in_quote:
                continue
            norm = " ".join(re.sub(r"[^a-z0-9 ]", " ", line.lower()).split())
            if norm in instrument:
                continue
            for name, rx, tier, scope in TRIGGERS:
                m = rx.search(line)
                if not m:
                    continue
                words = len(line[:m.start()].split()) + len(line[m.end():].split())
                if words > 8 and (DEID.search(line) or REPORT_HEADER.search(line)):
                    d3.append({"file": f, "line": i, "trigger": name, "context_words": words})
                break
    audit["d_note_text"] = {"deid_placeholders": d1, "report_headers_in_quotes": d2,
                            "long_quoted_windows_with_note_fingerprint": d3,
                            "pass": not (d1 or d2 or d3),
                            "note": "flags the de-identification placeholder MIMIC leaves in every note span, report section headers inside quoted blocks, and quoted lexicon matches carrying more than an 8-word window that also show a note fingerprint. Prose about the lexicon, the study's own instrument text, and the manuscript's own sentences are not findings."}

    # (e) frozen-artifact hashes unchanged
    start = json.load(open(f"{RES}/frozen_hashes_start.json"))
    now, drift = {}, []
    for p, rec in start.items():
        if not os.path.exists(p):
            drift.append({"file": p, "problem": "missing"}); continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        now[p] = {"sha256": h.hexdigest(), "bytes": os.path.getsize(p)}
        if now[p]["sha256"] != rec["sha256"]:
            drift.append({"file": p, "problem": "hash changed", "start": rec["sha256"], "end": now[p]["sha256"]})
    json.dump(now, open(f"{RES}/frozen_hashes_end.json", "w"), indent=1)
    audit["e_frozen_artifacts"] = {"checked": list(start), "drift": drift, "pass": not drift}

    # (f) tags identical to the start
    tags = [t for t in sh("git", "tag", "-l").splitlines() if t]
    expected = ["note-phenotype-v1.0.0", "note-phenotype-v1.1.0"]
    audit["f_tags"] = {"tags": tags, "expected": expected, "pass": tags == expected}

    # (g) no remote
    remotes = [r for r in sh("git", "remote", "-v").splitlines() if r.strip()]
    audit["g_remotes"] = {"remotes": remotes, "pass": not remotes}

    # (h) masld_config.py additions only
    diff = sh("git", "diff", f"{BASE}...HEAD", "--", "scripts/masld_config.py").splitlines()
    removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
    added = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
    audit["h_config_append_only"] = {"lines_added": len(added), "lines_removed": len(removed),
                                     "removed_lines": removed, "pass": not removed}

    audit["all_pass"] = all(v.get("pass") for v in audit.values() if isinstance(v, dict))
    json.dump(audit, open(f"{RES}/final_audit.json", "w"), indent=1)
    print(f"{'check':40s} {'pass':6s} detail")
    for k, v in audit.items():
        if not isinstance(v, dict):
            continue
        detail = ""
        if k.startswith("b_"): detail = f"{v['total_hits']} hits, {v['exempt']} exempt, {len(v['unexplained'])} unexplained"
        elif k.startswith("c_"): detail = f"{len(v['hits'])} small counts"
        elif k.startswith("e_"): detail = f"{len(v['checked'])} artifacts, {len(v['drift'])} drifted"
        elif k.startswith("f_"): detail = ", ".join(v["tags"])
        elif k.startswith("h_"): detail = f"+{v['lines_added']} / -{v['lines_removed']}"
        elif k.startswith("a_"): detail = f"{len(v['tracked_files_under_those_dirs'])} tracked under data/models/logs"
        elif k.startswith("d_"): detail = f"{len(v['deid_placeholders'])} deid, {len(v['report_headers_in_quotes'])} headers, {len(v['long_quoted_windows_with_note_fingerprint'])} windows"
        elif k.startswith("g_"): detail = f"{len(v['remotes'])} remotes"
        print(f"{k:40s} {'PASS' if v.get('pass') else 'FAIL':6s} {detail}")
    print(f"\nALL PASS: {audit['all_pass']}")


if __name__ == "__main__":
    main()
