#!/usr/bin/env python3
"""run_2026-11-10 Phase 1 — how much of what is ALREADY public would the push gate's note-text rule flag?

Two audits, counts and file names only (no matched text is printed or stored):
  1. every text file at the remote base, scanned with the gate's checks (c) and (d) and WITHOUT the
     "already public" exemption  -> docs/run_2026-11-10/results/base_exposure_audit.json
  2. named local files the gate holds back (--held ...) -> docs/run_2026-11-10/results/held_back_files.json

For each flagged line: the longest verbatim overlap with any dev/test liver-extractor string, how many
distinct extractor strings contain that overlap, and whether a whole quoted string on the line is
exactly an extractor string. An overlap is not proof of copying: invented sentences written in
radiology phrasing overlap real reports. It is the quantity the gate's rule (d3) is defined on.
"""
import argparse, collections, io, json, os, re, subprocess, sys, tarfile

sys.path.insert(0, os.getcwd())
from scripts import run1110_push_gate as G
from scripts.run0919_final_audit import known_seeds

RES = "docs/run_2026-11-10/results"


def as_changes(files):
    return {name: {"added": list(enumerate(text.splitlines(), 1)), "removed": [], "binary": False, "status": "A"}
            for name, text in files.items()}


def detail(changes, d3, corpus):
    strings = set(corpus.split(b"\n"))
    per = collections.defaultdict(lambda: {"lines_flagged": 0, "longest_overlap_chars": 0, "overlap_in_one_extractor_string": 0,
                                           "overlap_in_2_to_10": 0, "overlap_in_11_or_more": 0,
                                           "one_string_and_40_or_more_chars": 0, "whole_quoted_string_is_an_extractor_string": 0})
    for f in d3:
        nl = G.norm(changes[f["file"]]["added"][f["line"] - 1][1]); e = nl.encode("utf-8", "replace")
        L, cnt = f["longest_match_chars"], 0
        while L >= G.WINDOW and not cnt:                    # the run can span two strings; shorten until one contains it
            for o in range(len(e) - L + 1):
                if corpus.find(e[o:o + L]) != -1:
                    cnt = corpus.count(e[o:o + L]); break
            if not cnt:
                L -= 1
        p = per[f["file"]]
        p["lines_flagged"] += 1; p["longest_overlap_chars"] = max(p["longest_overlap_chars"], L)
        p["overlap_in_one_extractor_string"] += cnt == 1; p["overlap_in_2_to_10"] += 1 < cnt < 11
        p["overlap_in_11_or_more"] += cnt >= 11; p["one_string_and_40_or_more_chars"] += cnt == 1 and L >= 40
        cands = [nl] + re.findall(r'"([^"]{30,})"', nl) + re.findall(r"'([^']{30,})'", nl)
        p["whole_quoted_string_is_an_extractor_string"] += any(c.encode() in strings or c.strip(" .,;:").encode() in strings for c in cands)
    return {k: dict(v) for k, v in sorted(per.items())}


def scan(changes, corpus, headings, ids, public=""):
    from scripts.note_phenotype import TRIGGERS
    found, stats = G.check_note_text(changes, corpus, headings, public, lexicon=[rx for _, rx, _, _ in TRIGGERS])
    idbad, idstats = G.check_ids(changes, ids, known_seeds())
    out = {"text_files_scanned": len(changes), "lines_scanned": stats["lines_scanned"]}
    for k, v in found.items():
        out[k] = {"lines_flagged": len(v), "by_file": dict(sorted(collections.Counter(f["file"] for f in v).items()))}
    out["d3_sentence_windows"]["per_file"] = detail(changes, found["d3_sentence_windows"], corpus)
    out["identifiers"] = {"lines_flagged": len(idbad), **idstats}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--held", nargs="*", default=[])
    a = ap.parse_args()
    corpus, headings, ids = G.load_corpus(), G.load_private_headings(), G.load_ids()
    base = subprocess.run(["git", "rev-parse", G.REMOTE], capture_output=True, text=True).stdout.strip()
    raw = subprocess.run(["git", "archive", "--format=tar", base], capture_output=True).stdout
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for m in tar.getmembers():
            if not m.isfile() or m.name.lower().endswith(G.TABULAR_EXT + (".png", ".jpg", ".pdf")):
                continue
            data = tar.extractfile(m).read()
            if b"\0" not in data[:4096]:
                files[m.name] = data.decode("utf-8", "replace")
    out = {"script": "scripts/run1110_exposure_audit.py", "base": base,
           "rule": "the push gate's checks (c) and (d), with no already-public exemption", **scan(as_changes(files), corpus, headings, ids)}
    json.dump(out, open(f"{RES}/base_exposure_audit.json", "w"), indent=1)
    print("base:", {k: v["lines_flagged"] for k, v in out.items() if isinstance(v, dict) and "lines_flagged" in v})
    if a.held:
        held = {p: open(p, encoding="utf-8", errors="replace").read() for p in a.held if os.path.exists(p)}
        public = G.base_blob(base)
        h = {"script": "scripts/run1110_exposure_audit.py --held", "base": base,
             "rule": "the push gate's checks (c) and (d), as the gate applies them (already-public text exempt)",
             **scan(as_changes(held), corpus, headings, ids, public)}
        json.dump(h, open(f"{RES}/held_back_files.json", "w"), indent=1)
        print("held:", h["d3_sentence_windows"]["per_file"])


if __name__ == "__main__":
    main()
