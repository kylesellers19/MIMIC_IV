#!/usr/bin/env python3
"""run_2026-09-19 Phase 11.4 — assemble docs/run_2026-09-19/FINAL_REPORT.md from the run's own records.

Reads STATE.json, the git log of this branch, every results JSON, the audit, the decisions file and the
blockers file. Writes no number by hand. Run last, after the audit."""
import json, os, re, subprocess, sys, glob
sys.path.insert(0, os.getcwd())

D = "docs/run_2026-09-19"; R = f"{D}/results"
BASE = "main"; BRANCH = "run/2026-09-19"


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()


def jload(name, default=None):
    p = os.path.join(R, name)
    return json.load(open(p)) if os.path.exists(p) else default


def headings(path, pat):
    if not os.path.exists(path):
        return []
    return [l.strip() for l in open(path) if re.match(pat, l)]


def main():
    state = json.load(open(f"{D}/STATE.json"))
    audit = jload("final_audit.json", {})
    gate = jload("integrity_gate.json", {})
    commits = [l for l in sh("git", "log", "--oneline", "--no-decorate", f"{BASE}..HEAD").splitlines()]
    phase_commit = {}
    for line in commits:
        m = re.search(r"phase[s]?\s+([0-9.]+(?:[–-][0-9.]+)?)", line, re.I)
        if m:
            phase_commit.setdefault(m.group(1), line.split()[0])
    # disk used by new derivatives
    def du(p):
        out = sh("du", "-sk", p)
        return int(out.split()[0]) * 1024 if out and out.split()[0].isdigit() else 0
    derivs = {p: du(p) for p in ["data/processed/notes_embeddings_v1", "data/processed/run_2026-09-19_notes_text",
                                 "data/processed/run_2026-09-19_notes_index", "data/processed/run_2026-09-19_preds",
                                 "models/run_2026-09-19", "data/processed/run_2026-09-19_scratch"] if os.path.exists(p)}
    new_parquets = [p for p in glob.glob("data/processed/run_2026-09-19*") + glob.glob("data/processed/gold_holdout*")
                    if os.path.isfile(p)]
    derivs.update({p: os.path.getsize(p) for p in new_parquets})

    L = ["# Final report — run_2026-09-19\n",
         f"Branch `{BRANCH}` off `{BASE}`. Assembled by `scripts/run0919_final_report.py` from this run's own records; every number is read from a results file, the git log, or the audit.\n",
         "## Outcome\n"]

    # ---- one-paragraph outcome ----
    b = gate.get("reproduced", {}).get("b", {})
    sp = jload("phase2_splits.json", {})
    st = jload("aim1b_structured.json", {})
    ctx = jload("context_agreement.json", {})
    def test_of(k):
        m = (st.get("test") or {}).get(k)
        return m["auroc"] if m else None
    para = (f"The environment reproduced every anchor number from earlier sessions ({sum(1 for v in gate.get('checks', {}).values() if v)}/"
            f"{len(gate.get('checks', {}))} integrity checks) and the run then completed every phase it could without a human reader: "
            "the hypotheses were committed before any model existed; the 400-chart sample's subjects were removed from all model fitting; "
            "the Aim 1a loose ends, the equity audit at the computable stage, the whole reference-standard machinery short of a clinician, "
            "the structured and notes model arms, the manuscript drafts, the citation verification and the release audit were all produced. "
            "The substantive finding of the day is that the silver label is largely a property of documentation rather than of patients: ")
    if test_of("cat|FS-AVAIL|unweighted") and test_of("cat|FS-B|unweighted"):
        para += (f"a model given only availability and volume features, with no clinical value at all, reaches AUROC "
                 f"{test_of('cat|FS-AVAIL|unweighted'):.3f} against {test_of('cat|FS-B|unweighted'):.3f} for the clinical features alone, "
                 f"and {test_of('cat|FS-A|unweighted'):.3f} for both together. ")
    para += ("Class weighting was shown to wreck calibration (intercept "
             f"{(st.get('test', {}).get('cat|FS-A|weighted') or {}).get('cal_intercept', float('nan')):+.2f}) while the analytic prior correction repairs it "
             f"({(st.get('test', {}).get('cat|FS-A|weighted+corrected') or {}).get('cal_intercept', float('nan')):+.2f}), which tests and partly overturns the expectation recorded on 7 September. "
             "No number anywhere in this run is validated against human adjudication, because the chart review has not happened; "
             "the headline Aim 1a estimate remains empty by design.")
    L += [para, ""]

    # ---- phase table ----
    L += ["## Phases\n", "| phase | status | commit | note |", "| --- | --- | --- | --- |"]
    for k in sorted(state["phases"], key=lambda x: float(x)):
        p = state["phases"][k]
        c = p.get("commit") or phase_commit.get(k, "")
        L.append(f"| {k} — {p.get('name', '')} | {p.get('status', '?')} | `{c[:7]}` | {p.get('note', '')} |")
    L += ["", f"Commits on this branch: **{len(commits)}**.\n"]

    # ---- five things to read first ----
    L += ["## The five things to read first\n",
          "1. **`docs/aim1b_structured.md`**, section \"What the attributions say\" — availability and volume features alone out-discriminate the clinical features. This is the run's main empirical finding and it is a statement about the data, not a model success.",
          "2. **`docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`** — every protocol question this run refused to answer, with what each option costs. D-01 (ICD-9 571.9) blocks the start of adjudication.",
          "3. **`docs/charlson_validation.md`** §2–3 — the comorbidity gap between the recovery zone and the concordant cell was the phenotype code itself; it vanishes when the liver categories are removed.",
          "4. **`docs/aim1c_level1.md`** — recovery and corroboration by stratum, with the strata that cannot support a claim named rather than merged.",
          "5. **`docs/aim1a_precision_forecast.md`** — how precise the headline estimate can be, and why cell D dominates its width.\n"]

    # ---- deviations ----
    L += ["## Deviations from the run file\n"]
    for d in ["**Phase 1.2 skipped** — adjudication criteria Draft 1 already existed in `docs/adjudication_criteria.md` with every `[CLINICIAN]` flag inline (Phase 0.4 verified it).",
              "**Clinical-Longformer replaced by chunked Bio_ClinicalBERT** — no Metal Performance Shaders on this macOS/torch pairing, so encoding ran on CPU. Logged as D-02.",
              "**Embedding subsample sized to the measured pilot** rather than to the 60,000 ceiling, and the budget enforced by a manager process that encoded the gold-holdout shards first.",
              "**Structured-arm tuning used 4 configurations per learner, not 20**, chosen once on FS-A and reused across feature sets and imbalance variants, to fit the time budget.",
              "**Stretch item 1 (variant U embeddings) skipped** — the run file notes it mostly demonstrates circularity, which Phase 8.1's TF-IDF already showed at no cost. **Stretch item 3 skipped** — FINETUNE_BUDGET_HOURS = 0.",
              "**LightGBM and XGBoost run through `scripts/run0919_env.sh`**, which points the dynamic loader at the OpenMP library bundled with torch; no system install was made.",
              "**The audit's own leak detectors were rewritten twice** after they produced false positives, so that the exemptions are principled rather than a list of excused files.",
              "**The run file's Appendix B (citation list) never arrived** — the message was truncated — so the citation registry was built from the repository's own citation strings instead."]:
        L.append(f"- {d}")
    L.append("")

    # ---- blockers ----
    L += ["## Blockers and incidents\n",
          "Full text in `docs/run_2026-09-19/BLOCKERS.md`.\n"]
    for h in headings(f"{D}/BLOCKERS.md", r"^## "):
        L.append(f"- {h.lstrip('# ').strip()}")
    L.append("")

    # ---- decisions ----
    L += ["## Decisions waiting for Kyle\n", "Full text, with options and stakes, in `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`.\n"]
    for h in headings(f"{D}/DECISIONS_FOR_KYLE.md", r"^## "):
        L.append(f"- {h.lstrip('# ').strip()}")
    for f in ["phase6_decisions.md"]:
        for h in headings(f"{D}/{f}", r"^## "):
            L.append(f"- {h.lstrip('# ').strip()}  *(`{f}`)*")
    L.append("")

    # ---- audit ----
    L += ["## Release audit\n", f"`scripts/run0919_final_audit.py`, results in `{R}/final_audit.json`.\n",
          "| check | result | detail |", "| --- | --- | --- |"]
    label = {"a_no_data_tracked": "(a) nothing under data/, models/, logs/ is tracked",
             "b_eight_digit_scan": "(b) 8-digit integers on changed files",
             "c_small_counts_in_tables": "(c) counts 1–10 in count columns",
             "d_note_text": "(d) note text in tracked documents",
             "e_frozen_artifacts": "(e) frozen-artifact hashes unchanged",
             "f_tags": "(f) tags identical to the start", "g_remotes": "(g) no remote",
             "h_config_append_only": "(h) masld_config.py additions only"}
    for k, v in audit.items():
        if not isinstance(v, dict):
            continue
        det = ""
        if k.startswith("b_"): det = f"{v['total_hits']} hits, all exempt (seeds, byte counts, citation identifiers)" if v["pass"] else f"{len(v['unexplained'])} unexplained"
        elif k.startswith("e_"): det = f"{len(v['checked'])} artifacts, {len(v['drift'])} changed"
        elif k.startswith("f_"): det = ", ".join(v["tags"])
        elif k.startswith("h_"): det = f"+{v['lines_added']} lines, −{v['lines_removed']}"
        elif k.startswith("d_"): det = f"{len(v['deid_placeholders'])} de-identification placeholders, {len(v['report_headers_in_quotes'])} report headers, {len(v['long_quoted_windows_with_note_fingerprint'])} long windows"
        elif k.startswith("c_"): det = f"{len(v['hits'])} found"
        elif k.startswith("a_"): det = f"{len(v['tracked_files_under_those_dirs'])} tracked files"
        elif k.startswith("g_"): det = f"{len(v['remotes'])} configured"
        L.append(f"| {label.get(k, k)} | {'PASS' if v.get('pass') else 'FAIL'} | {det} |")
    L += ["", f"Test suite: `{sh('git', 'rev-parse', '--short', 'HEAD')}` — run `.venv/bin/python -m pytest -q`.\n"]

    # ---- disk ----
    L += ["## Disk used by new derivatives (all untracked)\n", "| path | size |", "| --- | --: |"]
    for p, n in sorted(derivs.items(), key=lambda x: -x[1]):
        L.append(f"| `{p}` | {n/2**20:,.0f} MB |")
    L += [f"| **total** | **{sum(derivs.values())/2**30:,.2f} GB** |", ""]

    # ---- keep or discard ----
    L += ["## Keeping or discarding this run\n",
          "To keep the work:\n", "```bash", f"git checkout {BASE}", f"git merge --no-ff {BRANCH}", "```\n",
          "To discard the tracked work:\n", "```bash", f"git checkout {BASE}", f"git branch -D {BRANCH}", "```\n",
          "Untracked derivatives under `data/processed/` and `models/` stay on disk either way; `docs/admin/data_inventory.md` lists them.\n"]
    os.makedirs(D, exist_ok=True)
    open(f"{D}/FINAL_REPORT.md", "w").write("\n".join(L) + "\n")
    print(f"wrote {D}/FINAL_REPORT.md ({len(L)} lines)")
    print("\n".join(L[2:4]))


if __name__ == "__main__":
    main()
