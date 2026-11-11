#!/usr/bin/env python3
"""run_2026-11-10 Phase 2 — correct the record (documents only).

Computes the facts from git and from file-system times, writes them to
    docs/run_2026-11-10/results/signoff_timeline.json
    docs/run_2026-11-10/results/extractor_cap.json
and inserts the dated text blocks into docs/llm_review_protocol.md (§2, §5, §6), appends a dated
clarification to docs/run_2026-10-27/RUN_LOG.md (existing lines untouched), and replaces the three
"pre-registered" lines in docs/reference_standard.md (decision D-05, option 1).

Idempotent: every inserted block carries a marker and is not inserted twice.
The sealed GOLD_HOLDOUT files are not opened: only their file-system times are read (os.stat).
"""
import datetime as dt, json, os, re, subprocess, sys

RES = "docs/run_2026-11-10/results"
SIGNOFF_NAME = "Kyle Sellers (study lead; not a clinician)"
GOLD = "data/processed/llm_review/gold_v4"
COMMITS = {"rule_text": "6338243", "lock_script": "27618b1", "lock": "41b155f", "signoff": "16033d9"}
EXTRACT_LOG = "data/processed/llm_review/extract_v3.log"       # the extractor's own count-only report
DOC_EXT = (".md",)


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc(s):
    return dt.datetime.fromisoformat(s).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def show(z):
    return z.replace("T", " ").replace("Z", " UTC")[:-7] + " UTC"


def timeline():
    out = {"script": "scripts/run1110_phase2_docs.py", "signoff_name": SIGNOFF_NAME, "commits": {}}
    for k, c in COMMITS.items():
        files = [l.split("\t") for l in sh("git", "show", "--name-status", "--format=", c).splitlines() if l]
        out["commits"][k] = {"hash": sh("git", "rev-parse", "--short=7", c), "committed_utc": utc(sh("git", "show", "-s", "--format=%cI", c)),
                             "files": [{"status": s, "path": p} for s, p in files]}
    st = os.stat(GOLD)
    out["gold_run"] = {"folder_created_utc": iso(st.st_birthtime),
                       "manifest_created_utc": iso(os.stat(f"{GOLD}/run/manifest.json").st_birthtime),
                       "answers_file_written_utc": iso(os.stat(f"{GOLD}/run/sentence_answers.parquet").st_mtime),
                       "source": "file-system creation and modification times (os.stat); the files were not opened"}
    lock = json.load(open("docs/run_2026-10-27/results/llm_gold_lock.json"))
    out["lock_written_utc"] = lock["written_utc"]
    t = lambda z: dt.datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ")
    rule, start = t(out["commits"]["rule_text"]["committed_utc"]), t(out["gold_run"]["folder_created_utc"])
    out["rule_text_committed_before_gold_run_started"] = rule < start
    out["minutes_between_rule_commit_and_gold_run_start"] = round((start - rule).total_seconds() / 60)
    out["lock_committed_after_lock_written"] = t(out["lock_written_utc"]) <= t(out["commits"]["lock"]["committed_utc"])
    so = out["commits"]["signoff"]["files"]
    out["signoff_commit"] = {"documents": [f["path"] for f in so if f["path"].endswith(DOC_EXT)],
                             "other_files": [f["path"] for f in so if not f["path"].endswith(DOC_EXT)],
                             "documents_only": all(f["path"].endswith(DOC_EXT) for f in so),
                             "touches_scripts_dir": any(f["path"].startswith("scripts/") for f in so)}
    later = sh("git", "log", "--format=%h", f"{COMMITS['lock']}..HEAD", "--", "scripts/llm_phenotype.py",
               "scripts/llm_sentence_review.py", "scripts/llm_gold_lock.py", "scripts/liver_sentences.py")
    out["label_or_prompt_code_changed_since_lock"] = bool(later)
    json.dump(out, open(f"{RES}/signoff_timeline.json", "w"), indent=1)
    return out


def extractor_cap():
    """The cap line of the extractor's own report; a count of 1-10 is written as '<11'."""
    sys.path.insert(0, os.getcwd())
    from scripts.liver_sentences import CAP
    out = {"script": "scripts/run1110_phase2_docs.py", "source": EXTRACT_LOG + " (git-ignored; counts only)", "cap": CAP}
    line = next((l for l in open(EXTRACT_LOG) if re.match(rf"{CAP}-sentence cap bound", l)), None)
    m = re.search(r"cap bound\s+([\d,]+) admissions", line or "")
    n = int(m.group(1).replace(",", "")) if m else None
    out["admissions_cap_bound"] = None if n is None else "<11" if 0 < n < 11 else n
    out["admissions_dev_test_subsample"] = json.load(open("docs/run_2026-09-19/results/notes_subsample.json"))["admissions_dev_test"]
    json.dump(out, open(f"{RES}/extractor_cap.json", "w"), indent=1)
    return out


def insert_after(text, anchor, block, marker):
    if marker in text:
        return text
    assert anchor in text, f"anchor not found: {anchor[:60]}"
    return text.replace(anchor, anchor + block, 1)


def main():
    T, C = timeline(), extractor_cap()
    c = T["commits"]
    other = ", ".join(f"`{p}`" for p in T["signoff_commit"]["other_files"])
    fmt_n = lambda v: v if isinstance(v, str) else f"{v:,}"

    # ---- protocol
    p = "docs/llm_review_protocol.md"
    s = open(p).read()
    s = insert_after(s, "- **Per-admission cap:** 160 sentences, impression first.\n",
        "- **Section labels, as run (added 2026-11-10):** each kept sentence carries a section label: impression, findings or other.\n"
        "  - A findings block opens at a heading containing FINDING. It continues under a later heading only when every part of that heading is on the organ sub-heading list `FINDINGS_SUBHEADINGS` in `scripts/liver_sentences.py`. Any other heading closes it.\n"
        "  - The label has one use: it sets priority under the cap (impression, then findings, then other). It is not shown to the model, and the admission rule (§5) does not use it.\n"
        f"  - The cap bound {fmt_n(C['admissions_cap_bound'])} of the {fmt_n(C['admissions_dev_test_subsample'])} dev/test admissions in the notes subsample, by the extractor's own report (`docs/run_2026-11-10/results/extractor_cap.json`). For every other admission the section label changed nothing.\n"
        "  - An alternative rule for closing a findings block was examined on 23–26 September 2026 (`diagnostics/section_rule_v2/`) and not adopted. Whether to run it as a dev/test-only sensitivity analysis is decision N-05 in `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`.\n",
        "Section labels, as run (added 2026-11-10)")
    s = insert_after(s, "The primary definition is the one in amendment (h) of `docs/analysis_plan_prespecified.md` and the one `scripts/llm_gold_lock.py` locked.\n",
        f"- **Who signed off (added 2026-11-10):** {SIGNOFF_NAME}. No clinician has reviewed the admission rule. That review is outstanding (decision N-06 in `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`).\n"
        "- **Timeline, from git and file times** (`docs/run_2026-11-10/results/signoff_timeline.json`, written by `scripts/run1110_phase2_docs.py`):\n"
        f"  - the rule text, amendment (h), was committed in `{c['rule_text']['hash']}` at {show(c['rule_text']['committed_utc'])};\n"
        f"  - the GOLD_HOLDOUT run started at {show(T['gold_run']['folder_created_utc'])}, {T['minutes_between_rule_commit_and_gold_run_start']} minutes after that commit;\n"
        f"  - the lock was written at {show(T['lock_written_utc'])} and committed in `{c['lock']['hash']}`;\n"
        f"  - the sign-off commit `{c['signoff']['hash']}` ({show(c['signoff']['committed_utc'])}) changed this protocol and the run log, and added one diagnostic script ({other}). It changed no prompt, no label definition, no file under `scripts/` and no locked file.\n",
        "Who signed off (added 2026-11-10)")
    s = insert_after(s, "No answer distribution on GOLD_HOLDOUT is looked at before the adjudication exists.\n",
        "- **What the lock binds (added 2026-11-10):** `docs/llm_gold_lock.md` records the SHA-256 of four files and three identifiers.\n"
        "  - The sentence-answers file: answer, timing and the three probabilities, P(YES), P(NO) and P(UNCLEAR), for every sentence row.\n"
        "  - The admission labels.\n"
        "  - The extractor output for GOLD_HOLDOUT.\n"
        "  - The run manifest, which holds the prompt text and the decoding settings.\n"
        "  - The model digest, the Ollama version and the commit of the code.\n"
        "  - **Not hashed:** the per-shard answer files under `run/shards/`. The assembled sentence-answers file is the record.\n",
        "What the lock binds (added 2026-11-10)")
    open(p, "w").write(s)

    # ---- October run log: append only
    p = "docs/run_2026-10-27/RUN_LOG.md"
    s = open(p).read()
    if "Clarification appended 2026-11-10" not in s:
        s = s.rstrip("\n") + "\n\n" + (
            "## Clarification appended 2026-11-10 (run_2026-11-10, Phase 2)\n\n"
            "The lines above are unchanged. This section adds what they left out.\n\n"
            f"- **Who signed off the admission rule (item 8):** {SIGNOFF_NAME}. Clinician review of the rule is outstanding.\n"
            f"- **Order of events, from git and file times:** rule text committed in `{c['rule_text']['hash']}`; the GOLD_HOLDOUT run started {T['minutes_between_rule_commit_and_gold_run_start']} minutes later; lock committed in `{c['lock']['hash']}`; sign-off recorded in `{c['signoff']['hash']}`. Times: `docs/run_2026-11-10/results/signoff_timeline.json`.\n"
            f"- **What the sign-off commit changed:** two documents (the protocol and this log) and one new diagnostic script ({other}). No prompt, label definition, file under `scripts/` or locked file.\n"
            "- **What the lock binds:** protocol §6 now lists it. The per-shard answer files are not hashed.\n")
        open(p, "w").write(s)

    # ---- reference standard: D-05 option 1
    p = "docs/reference_standard.md"
    s = open(p).read()
    swaps = [
        ("## 2. Pre-registered adjudication criteria", "## 2. Adjudication criteria, frozen in the repository before review"),
        ("3. **Pre-registration** — adjudication criteria (§2) are **finalized and pre-registered before review starts**.",
         "3. **Criteria frozen before review** — adjudication criteria (§2) are **finalized and frozen in this repository before review starts**, and the freeze is identifiable by its commit. No registry is claimed."),
        ("**finalization and pre-registration of the adjudication criteria (§2).**",
         "**finalization of the adjudication criteria (§2) and their freeze in this repository, identifiable by commit.** No registry is claimed."),
    ]
    done = 0
    for old, new in swaps:
        if old in s:
            s = s.replace(old, new, 1); done += 1
    note = "*Wording corrected 2026-11-10 (decision D-05, option 1):"
    if note not in s:
        s = s.rstrip("\n") + ("\n\n" + note + " three lines of this document said the criteria are \"pre-registered\". "
                              "No registration exists. They now say what is true: the criteria are frozen in the repository before review starts, identifiable by commit.*\n")
    open(p, "w").write(s)
    left = sh("git", "grep", "-n", "-i", "-E", "pre-?regist(ered|ration|er)", "--", "docs/reference_standard.md")
    print("timeline:", {k: T[k] for k in ("rule_text_committed_before_gold_run_started", "minutes_between_rule_commit_and_gold_run_start",
                                         "lock_committed_after_lock_written", "label_or_prompt_code_changed_since_lock")}, T["signoff_commit"])
    print("cap:", C["admissions_cap_bound"], "of", C["admissions_dev_test_subsample"], "| reference_standard swaps", done)
    print("remaining 'pre-regist' lines in reference_standard.md (working tree):", len([l for l in open(p) if re.search(r"pre-?regist(ered|ration|er)", l, re.I)]))


if __name__ == "__main__":
    main()
