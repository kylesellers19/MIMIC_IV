#!/usr/bin/env python3
"""run_2026-11-10 Phase 1.4 — the push gate. The repository is public; nothing is pushed unless this exits 0.

WHAT IT INSPECTS
    Every file that differs between the remote branch and the index, and, for the text checks, the ADDED
    lines of every unpushed commit taken one by one plus everything staged. A line added in one commit and
    removed in the next would still be published in history, so each commit is checked on its own.

CHECKS (exit status 1 if any fails)
    (a) a path under data/, models/ or logs/;
    (b) a new tabular or binary file (.csv, .parquet, .duckdb, .xlsx, .pkl, ... or any binary content);
    (c) an 8-digit number equal to a real hadm_id or subject_id (seeds, byte counts and citation
        identifiers exempt, classified by the September audit's classify_token);
    (d) note text: d1 de-identification marks; d2 report headers on a line that also matches the frozen
        rule's lexicon; d3 any window of 30 or more characters that matches a liver-extractor sentence,
        its neighbours or its heading; d4 any heading value of four or more words from the private
        heading tables;
    (e) counts 1-10 in count columns (markdown tables and count-like JSON keys);
    (f) scripts/masld_config.py: any deleted or changed line;
    (g) a frozen or locked artifact whose hash differs from this run's start.

EXEMPTIONS FOR (d3) AND (d4), each narrow and stated
    1. the same text already appears in a tracked file at the remote base (it is already public and
       study-authored, so the push discloses nothing);
    2. the line carries the `# audit-fixture` marker (negative controls for these detectors);
    3. the match is a term listed in TERMINOLOGY below (published disease names that notes also use),
       with fewer than ten characters of other text beside it.
    Nothing else is exempt: a flagged line is reworded, not excused.

LIMITS
    The comparison text is the dev/test liver-extractor output. GOLD_HOLDOUT sentences are sealed and
    are not read; no script in this run reads GOLD_HOLDOUT text.

PRIVACY
    Note-derived text is read in memory only. Output is counts and file:line. A matched token or
    window is never printed or stored.

USAGE
    scripts/run0919_env.sh scripts/run1110_push_gate.py            # gate the unpushed range + staged
    ... --base <commit>      compare against another base (Phase 11: the run's first parent)
    ... --record             also write docs/run_2026-11-10/results/push_gate.json
"""
import argparse, hashlib, io, json, os, re, subprocess, sys, tarfile, time

sys.path.insert(0, os.getcwd())
from scripts.run0919_final_audit import (AUDIT_FIXTURE, DEID, EIGHT_DIGIT, REPORT_HEADER,
                                         TALKS_ABOUT_DEID, classify_token, known_seeds)

REMOTE = "origin/run/2026-09-19"
RES = "docs/run_2026-11-10/results"
LOG = "logs/run_2026-11-10/push_gate.log"
SCRATCH = "data/processed/run_2026-11-10_scratch"
WINDOW = 30
SENTENCE_FILES = ["data/processed/llm_review/liver_sentences_devtest_v3.parquet",
                  "data/processed/llm_review/liver_sentences_devtest_cap160.parquet",
                  "data/processed/llm_review/liver_sentences_devtest_cap160_rejoined.parquet"]
TEXT_COLUMNS = ("text", "prev_text", "next_text", "heading")
PRIVATE_HEADINGS = "data/processed/section_rule_v2_private"
FORBIDDEN_DIRS = ("data/", "models/", "logs/")
TABULAR_EXT = (".csv", ".tsv", ".parquet", ".duckdb", ".wal", ".db", ".sqlite", ".xlsx", ".xls", ".pkl",
               ".pickle", ".feather", ".arrow", ".npy", ".npz", ".h5", ".hdf5", ".gz", ".zip", ".joblib",
               ".cbm", ".bin", ".pt", ".safetensors", ".dta", ".sav", ".rds")
# Published names that notes also use. A d3/d4 match is exempt only when it lies wholly inside one of these.
TERMINOLOGY = (
    "nonalcoholic fatty liver disease", "non-alcoholic fatty liver disease",
    "nonalcoholic steatohepatitis", "non-alcoholic steatohepatitis",
    "metabolic dysfunction-associated steatotic liver disease",
    "metabolic dysfunction-associated steatohepatitis",
    "metabolic dysfunction-associated fatty liver disease",
)
COUNT_HEADER = re.compile(r"\bn\b|count|charts|admissions|subjects|positives|hits|units|sentences|patients")
COUNT_KEY_TOKENS = {"n", "x", "count", "counts", "charts", "admissions", "subjects", "positives", "hits", "units",
                    "sentences", "patients", "notes"}
NOT_PATIENT_TOKENS = {"files", "checks", "phases", "replicates", "strata", "scripts", "commits", "tests", "seeds",
                      "hours", "bins", "folds", "options", "frozen", "locked", "versions", "stages", "words",
                      "decisions", "references", "floor", "pct", "share", "min", "minimum"}
JSON_INT = re.compile(r'^\s*"([^"]+)"\s*:\s*(-?\d+)\s*,?\s*$')


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, errors="replace").stdout


def norm(s):
    return " ".join((s or "").lower().split())


# ----------------------------------------------------------------------------- what changed
def parse_diff(text):
    """unified diff (-U0) -> {path: {"added": [(lineno, line)], "removed": [line], "binary": bool}}"""
    out, path, lineno = {}, None, 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            path = None
        elif line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            if path:
                out.setdefault(path, {"added": [], "removed": [], "binary": False})
        elif line.startswith("Binary files "):
            m = re.search(r" and b/(.+?) differ$", line)
            if m:
                out.setdefault(m.group(1), {"added": [], "removed": [], "binary": True})["binary"] = True
        elif line.startswith("@@") and path:
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif path and line.startswith("+") and not line.startswith("+++"):
            out[path]["added"].append((lineno, line[1:]))
            lineno += 1
        elif path and line.startswith("-") and not line.startswith("---"):
            out[path]["removed"].append(line[1:])
    return out


def collect(base):
    """Everything that differs between `base` and the index: unpushed commits plus staged changes."""
    diff = parse_diff(sh("git", "diff", "--cached", "-U0", "--no-color", "--no-ext-diff", "--no-renames", base))
    status = {}
    for line in sh("git", "diff", "--cached", "--name-status", "--no-renames", base).splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            status[parts[1]] = parts[0]
            diff.setdefault(parts[1], {"added": [], "removed": [], "binary": False})
    for line in sh("git", "diff", "--cached", "--numstat", "--no-renames", base).splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0] == "-":
            diff.setdefault(parts[2], {"added": [], "removed": [], "binary": True})["binary"] = True
    for p, rec in diff.items():
        rec["status"] = status.get(p, "M")
    return diff


def index_text(path):
    return sh("git", "show", f":{path}")


def collect_units(base):
    """Every unit a push would publish, each checked on its own: one per unpushed commit (its diff against
    its first parent) plus the staged changes. A line added in one commit and removed in the next is still
    published in history, so the net difference alone is not enough.
    -> [(label, changes, text_getter)]"""
    units = []
    for c in [x for x in sh("git", "rev-list", "--reverse", "--first-parent", f"{base}..HEAD").split() if x]:
        diff = parse_diff(sh("git", "diff", "-U0", "--no-color", "--no-ext-diff", "--no-renames", f"{c}^", c))
        for line in sh("git", "diff", "--name-status", "--no-renames", f"{c}^", c).splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                diff.setdefault(parts[1], {"added": [], "removed": [], "binary": False})["status"] = parts[0]
        for line in sh("git", "diff", "--numstat", "--no-renames", f"{c}^", c).splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0] == "-":
                diff.setdefault(parts[2], {"added": [], "removed": [], "binary": True})["binary"] = True
        for rec in diff.values():
            rec.setdefault("status", "M")
        units.append((c[:7], diff, (lambda p, c=c: sh("git", "show", f"{c}:{p}"))))
    staged = parse_diff(sh("git", "diff", "--cached", "-U0", "--no-color", "--no-ext-diff", "--no-renames", "HEAD"))
    for line in sh("git", "diff", "--cached", "--name-status", "--no-renames", "HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            staged.setdefault(parts[1], {"added": [], "removed": [], "binary": False})["status"] = parts[0]
    for line in sh("git", "diff", "--cached", "--numstat", "--no-renames", "HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0] == "-":
            staged.setdefault(parts[2], {"added": [], "removed": [], "binary": True})["binary"] = True
    for rec in staged.values():
        rec.setdefault("status", "M")
    if staged:
        units.append(("staged", staged, index_text))
    return units


# ----------------------------------------------------------------------------- (a) (b)
def check_paths(paths):
    return [{"file": p} for p in sorted(paths) if p.startswith(FORBIDDEN_DIRS)]


def check_filetypes(changes):
    bad = []
    for p, rec in sorted(changes.items()):
        if rec.get("status") == "D":
            continue
        if rec.get("status") == "A" and p.lower().endswith(TABULAR_EXT):
            bad.append({"file": p, "problem": "new tabular or binary file type"})
        elif rec.get("binary"):
            bad.append({"file": p, "problem": "binary content"})
    return bad


# ----------------------------------------------------------------------------- (c)
def load_ids():
    """Every real hadm_id and subject_id. In memory only."""
    import duckdb
    con = duckdb.connect()
    ids = set()
    raw = [("data/raw/hosp/admissions.csv.gz", "hadm_id"), ("data/raw/hosp/patients.csv.gz", "subject_id")]
    if all(os.path.exists(f) for f, _ in raw):
        for f, c in raw:
            ids |= {str(r[0]) for r in con.execute(f"SELECT DISTINCT {c} FROM read_csv_auto('{f}')").fetchall()}
    for c in ("hadm_id", "subject_id"):
        ids |= {str(r[0]) for r in con.execute(
            f"SELECT DISTINCT {c} FROM read_parquet('data/processed/splits_v1.parquet')").fetchall()}
    return ids


def check_ids(changes, ids, seeds):
    bad, seen, exempt = [], 0, 0
    for p, rec in changes.items():
        for lineno, line in rec["added"]:
            for m in EIGHT_DIGIT.finditer(line):
                seen += 1
                if m.group(0) not in ids:
                    continue
                if classify_token(line, m.group(0), seeds) != "UNEXPLAINED":
                    exempt += 1
                    continue
                bad.append({"file": p, "line": lineno})      # the token itself is never recorded
    return bad, {"eight_digit_tokens": seen, "equal_to_an_id_but_exempt": exempt}


# ----------------------------------------------------------------------------- (d)
def window_hashes(buf):
    """numpy uint64 polynomial hash of every WINDOW-byte window of a bytes object."""
    import numpy as np
    b = np.frombuffer(buf, dtype=np.uint8).astype(np.uint64)
    n = len(b) - WINDOW + 1
    if n <= 0:
        return np.zeros(0, dtype=np.uint64)
    h = np.zeros(n, dtype=np.uint64)
    mult = np.uint64(1)
    P = np.uint64(1099511628211)
    with np.errstate(over="ignore"):
        for k in range(WINDOW):
            h += b[k:k + n] * mult
            mult = mult * P
    return h


def load_corpus():
    """Normalised dev/test liver-extractor text (sentence, neighbours, heading), one string per line.
    Cached under data/ (git-ignored); the cache is note text and never leaves that folder."""
    src = [f for f in SENTENCE_FILES if os.path.exists(f)]
    stamp = hashlib.sha256("|".join(f"{f}:{os.path.getsize(f)}:{int(os.path.getmtime(f))}" for f in src).encode()).hexdigest()[:16]
    cache = os.path.join(SCRATCH, f"gate_corpus_{stamp}.bin")
    if os.path.exists(cache):
        return open(cache, "rb").read()
    import pandas as pd
    import pyarrow.parquet as pq
    strings = set()
    for f in src:
        cols = [c for c in TEXT_COLUMNS if c in pq.ParquetFile(f).schema_arrow.names]
        df = pd.read_parquet(f, columns=cols)
        for c in cols:
            strings |= {norm(s) for s in df[c].dropna().unique()}
    blob = "\n".join(sorted(s for s in strings if s)).encode("utf-8", "replace")
    os.makedirs(SCRATCH, exist_ok=True)
    with open(cache, "wb") as fh:
        fh.write(blob)
    return blob


def load_private_headings():
    """Heading values of four or more words from the private heading tables. In memory only."""
    import glob
    import pandas as pd
    out = set()
    for f in sorted(glob.glob(os.path.join(PRIVATE_HEADINGS, "*.csv"))):
        df = pd.read_csv(f)
        if "heading" in df.columns:
            out |= {norm(h) for h in df.heading.dropna().astype(str)}
    return {h for h in out if len(h.split()) >= 4}


def base_blob(base):
    """Normalised text of every tracked file at the base commit: what is already public."""
    raw = subprocess.run(["git", "archive", "--format=tar", base], capture_output=True).stdout
    parts = []
    if raw:
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            for m in tar.getmembers():
                if not m.isfile() or m.name.lower().endswith(TABULAR_EXT + (".png", ".jpg", ".pdf")):
                    continue
                data = tar.extractfile(m).read()
                if b"\0" in data[:4096]:
                    continue
                parts.extend(norm(l) for l in data.decode("utf-8", "replace").splitlines())
    return "\n".join(p for p in parts if p)


TERM_CONTEXT_MIN = 10


def inside_term(nline, start, end, terms):
    """True when fewer than TERM_CONTEXT_MIN characters of [start, end) lie outside a listed term. A window
    that is a published disease name plus a word fragment such as "with " discloses nothing; ten or more
    characters of other matching text beside the name are still a finding."""
    covered = [False] * (end - start)
    for t in terms:
        i = nline.find(t)
        while i != -1:
            for k in range(max(i, start), min(i + len(t), end)):
                covered[k - start] = True
            i = nline.find(t, i + 1)
    return covered.count(False) < TERM_CONTEXT_MIN


def check_note_text(changes, corpus, headings, public, terms=TERMINOLOGY, lexicon=None):
    """-> (findings, stats). corpus: bytes blob (normalised strings, newline-separated); headings: set of
    normalised heading values (>= 4 words); public: normalised text already at the base."""
    import numpy as np
    d1, d2, d3, d4 = [], [], [], []
    stats = {"lines_scanned": 0, "d3_windows_matched": 0, "d3_exempt_public": 0, "d3_exempt_term": 0,
             "d3_exempt_fixture": 0, "d4_exempt_public": 0, "d4_exempt_term": 0, "d4_exempt_fixture": 0}
    lines = []                                         # (file, lineno, raw, normalised)
    for p, rec in changes.items():
        if rec.get("binary"):
            continue
        for lineno, line in rec["added"]:
            lines.append((p, lineno, line, norm(line)))
    stats["lines_scanned"] = len(lines)
    for p, lineno, line, nline in lines:
        if DEID.search(line) and not TALKS_ABOUT_DEID.search(line) and not AUDIT_FIXTURE.search(line):
            d1.append({"file": p, "line": lineno})
        if REPORT_HEADER.search(line) and not AUDIT_FIXTURE.search(line) and lexicon and any(rx.search(line) for rx in lexicon):
            d2.append({"file": p, "line": lineno})

    # d3: 30-character windows against the corpus
    enc = [(i, nl.encode("utf-8", "replace")) for i, (_, _, _, nl) in enumerate(lines) if len(nl) >= WINDOW]
    if enc and len(corpus) >= WINDOW:
        buf = b"\n".join(e for _, e in enc)
        fh = window_hashes(buf)
        arr = np.frombuffer(buf, dtype=np.uint8)
        nl_pos = np.flatnonzero(arr == 10)
        valid = np.ones(len(fh), dtype=bool)
        for q in nl_pos:                               # windows that span two lines are not real windows
            valid[max(0, q - WINDOW + 1):q + 1] = False
        cand = np.unique(fh[valid])
        hit = np.zeros(len(cand), dtype=bool)
        step = 4 << 20
        for s in range(0, len(corpus), step):
            ch = window_hashes(corpus[s:s + step + WINDOW - 1])
            hit |= np.isin(cand, ch)
        matched = set(cand[hit].tolist())
        if matched:
            starts = np.concatenate([[0], nl_pos + 1])
            pos = np.flatnonzero(valid & np.isin(fh, np.fromiter(matched, dtype=np.uint64)))
            per_line = {}
            for q in pos.tolist():
                li = int(np.searchsorted(starts, q, side="right") - 1)
                per_line.setdefault(li, []).append(q - int(starts[li]))
            for li, offs in per_line.items():
                idx, e = enc[li]
                p, lineno, line, nline = lines[idx]
                real = [o for o in offs if corpus.find(e[o:o + WINDOW]) != -1]     # exact check, not just the hash
                if not real:
                    continue
                stats["d3_windows_matched"] += len(real)
                if AUDIT_FIXTURE.search(line):
                    stats["d3_exempt_fixture"] += len(real); continue
                left = []
                for o in real:
                    w = e[o:o + WINDOW].decode("utf-8", "replace")
                    if w in public:
                        stats["d3_exempt_public"] += 1
                    elif inside_term(nline, o, o + WINDOW, terms):
                        stats["d3_exempt_term"] += 1
                    else:
                        left.append(o)
                if left:
                    run, best, prev = 1, 1, None       # longest run of consecutive matching offsets
                    for o in left:
                        run = run + 1 if prev is not None and o == prev + 1 else 1
                        best, prev = max(best, run), o
                    d3.append({"file": p, "line": lineno, "matching_windows": len(left),
                               "longest_match_chars": best + WINDOW - 1})

    # d4: private heading values of four or more words
    if headings:
        by_first = {}
        for h in headings:
            by_first.setdefault(h.split()[0], []).append(h)
        for p, lineno, line, nline in lines:
            words = nline.split(" ")
            off, found = 0, None
            for w in words:
                for h in by_first.get(w, ()):
                    if nline.startswith(h, off) and (off + len(h) == len(nline) or not nline[off + len(h)].isalnum()):
                        if AUDIT_FIXTURE.search(line):
                            stats["d4_exempt_fixture"] += 1
                        elif h in public:
                            stats["d4_exempt_public"] += 1
                        elif inside_term(nline, off, off + len(h), terms):
                            stats["d4_exempt_term"] += 1
                        else:
                            found = True
                off += len(w) + 1
            if found:
                d4.append({"file": p, "line": lineno})
    return {"d1_deid_marks": d1, "d2_report_headers": d2, "d3_sentence_windows": d3, "d4_private_headings": d4}, stats


# ----------------------------------------------------------------------------- (e)
def count_like_key(key):
    if "/" in key or re.search(r"\.[a-z0-9]{1,5}$", key.lower()):
        return False                     # a file path used as a key: its value counts lines or files, not people
    toks = set(re.split(r"[^a-z0-9]+", key.lower()))
    return bool(toks & COUNT_KEY_TOKENS) and not (toks & NOT_PATIENT_TOKENS)


def check_small_counts(path, text, added_linenos):
    """Counts 1-10 in count columns of markdown tables, and in count-like JSON keys. Only added lines."""
    bad = []
    lines = text.splitlines()
    if path.endswith(".md"):
        header = None
        for i, line in enumerate(lines, 1):
            if not line.lstrip().startswith("|"):
                header = None
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = [c.lower() for c in cells]
                continue
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if i not in added_linenos:
                continue
            for h, c in zip(header, cells):
                if COUNT_HEADER.search(h) and re.fullmatch(r"[1-9]|10", c.replace(",", "").replace("*", "")):
                    bad.append({"file": path, "line": i, "column": h})
    elif path.endswith(".json"):
        for i, line in enumerate(lines, 1):
            m = JSON_INT.match(line)
            if m and i in added_linenos and count_like_key(m.group(1)) and 1 <= int(m.group(2)) <= 10:
                bad.append({"file": path, "line": i, "key": m.group(1)})
    return bad


# ----------------------------------------------------------------------------- (f) (g)
def check_config(changes, name="scripts/masld_config.py"):
    rec = changes.get(name)
    return [] if not rec else [{"file": name, "removed_or_changed_lines": len(rec["removed"])}] if rec["removed"] else []


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check_frozen(start):
    drift = []
    for grp in ("frozen", "locked"):
        for p, rec in start.get(grp, {}).items():
            if not os.path.exists(p):
                drift.append({"file": p, "problem": "missing"})
            elif sha(p) != rec["sha256"]:
                drift.append({"file": p, "problem": "hash changed"})
    return drift


# ----------------------------------------------------------------------------- main
def run_gate(base):
    from scripts.note_phenotype import TRIGGERS
    net = collect(base)                                   # base against the index: paths, types, config
    units = collect_units(base)                           # each commit and the staged changes: text checks
    res = {"base": sh("git", "rev-parse", base).strip(), "head": sh("git", "rev-parse", "HEAD").strip(),
           "files_inspected": len(net), "commits_inspected": len([u for u in units if u[0] != "staged"]), "checks": {}}
    merged, paths, types, small, config = {}, set(net), dict(net), [], check_config(net)
    for label, ch, text_of in units:
        for p, rec in ch.items():
            paths.add(p)
            if rec.get("status") != "D":
                merged[f"{label}::{p}"] = rec
                if rec.get("binary") or (rec.get("status") == "A" and p.lower().endswith(TABULAR_EXT)):
                    types.setdefault(p, rec)
                    types[p] = dict(types[p], status=rec.get("status") if types[p].get("status") != "A" else "A",
                                    binary=types[p].get("binary") or rec.get("binary"))
                if p.endswith((".md", ".json")) and not rec.get("binary"):
                    small += [dict(f, file=f"{label}::{p}") for f in check_small_counts(p, text_of(p), {n for n, _ in rec["added"]})]
        config += [dict(f, file=f"{label}::{f['file']}") for f in check_config(ch)]
    res["checks"]["a_forbidden_paths"] = {"findings": check_paths(paths)}
    res["checks"]["b_tabular_or_binary"] = {"findings": check_filetypes(types)}
    ids_bad, ids_stats = check_ids(merged, load_ids(), known_seeds())
    res["checks"]["c_identifiers"] = {"findings": ids_bad, **ids_stats}
    found, stats = check_note_text(merged, load_corpus(), load_private_headings(), base_blob(base),
                                   lexicon=[rx for _, rx, _, _ in TRIGGERS])
    res["checks"]["d_note_text"] = {"findings": [dict(f, kind=k) for k, v in found.items() for f in v], **stats,
                                    **{k: len(v) for k, v in found.items()}}
    res["checks"]["e_small_counts"] = {"findings": small}
    res["checks"]["f_config_append_only"] = {"findings": config}
    start = json.load(open(f"{RES}/frozen_hashes_start.json"))
    res["checks"]["g_frozen_hashes"] = {"findings": check_frozen(start),
                                        "artifacts_checked": len(start["frozen"]) + len(start["locked"])}
    for c in res["checks"].values():
        c["pass"] = not c["findings"]
    res["all_pass"] = all(c["pass"] for c in res["checks"].values())
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=REMOTE)
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args()
    res = run_gate(a.base)
    res["checked_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"push gate: base {res['base'][:7]} -> head {res['head'][:7]} (+ staged) | files inspected {res['files_inspected']} | commits checked one by one {res['commits_inspected']}")
    for name, c in res["checks"].items():
        print(f"  {name:<24} {'PASS' if c['pass'] else 'FAIL'}  findings {len(c['findings'])}")
        for f in c["findings"][:40]:
            loc = f["file"] + (f":{f['line']}" if "line" in f else "")
            print(f"      {loc}  {f.get('kind', f.get('problem', ''))}")
    print("GATE PASSED" if res["all_pass"] else "GATE FAILED — do not push")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(json.dumps({"utc": res["checked_utc"], "base": res["base"][:12], "head": res["head"][:12],
                             "files": res["files_inspected"], "all_pass": res["all_pass"],
                             "findings": {k: len(c["findings"]) for k, c in res["checks"].items()}}) + "\n")
    if a.record:
        json.dump(res, open(f"{RES}/push_gate.json", "w"), indent=1)
    sys.exit(0 if res["all_pass"] else 1)


if __name__ == "__main__":
    main()
