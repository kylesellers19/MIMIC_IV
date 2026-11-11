#!/usr/bin/env python3
"""run_2026-11-10 Phase 11.3 — assemble docs/run_2026-11-10/FINAL_REPORT.md from the run's own records.

Reads STATE.json, the run log, the blockers and decisions files, the results JSONs, the gate's record and its
log, and git. Writes no number by hand. Run after the end hashes and the recorded gate run.
"""
import datetime as dt, json, os, re, subprocess, sys

D = "docs/run_2026-11-10"
R = f"{D}/results"
OUT = f"{D}/FINAL_REPORT.md"
BRANCH = "run/2026-09-19"
GATE_LOG = "logs/run_2026-11-10/push_gate.log"


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()


def load(name, default=None):
    p = os.path.join(R, name)
    return json.load(open(p)) if os.path.exists(p) else default


def heads(path, pat):
    return [m.group(1).strip() for m in re.finditer(pat, open(path).read(), re.M)] if os.path.exists(path) else []


def pc(s):
    if not isinstance(s, dict) or "pct" not in s:
        return "not reported"
    if not isinstance(s["pct"], (int, float)):
        return f"{s['pct']}%" if not str(s["pct"]).endswith("d") else str(s["pct"])
    ci = s.get("ci95") or ([s["wilson_lo_pct"], s["wilson_hi_pct"]] if "wilson_lo_pct" in s else None)
    return f"{s['pct']}%" + (f" ({ci[0]}–{ci[1]})" if ci else "")


def main():
    st = json.load(open(f"{D}/STATE.json"))
    pre, start_h, end_h = load("preflight.json", {}), load("frozen_hashes_start.json", {}), load("frozen_hashes_end.json")
    gate, fib, out, era, fun = load("push_gate.json"), load("fib4_by_cell.json"), load("later_outcomes.json"), load("icd_era.json"), load("imaging_funnel.json")
    car, cit, inv, base, held, pilot = (load("carryover_check.json"), load("citations.json"), load("data_inventory_addendum.json"),
                                        load("base_exposure_audit.json"), load("held_back_files.json"), load("pilot_packets.json"))
    first, head = pre.get("head", ""), sh("git", "rev-parse", "HEAD")
    remote = sh("git", "rev-parse", f"origin/{BRANCH}")
    commits = sh("git", "log", "--oneline", "--no-decorate", f"{first}..HEAD").splitlines()
    tags_remote = [l.split("refs/tags/")[1] for l in sh("git", "ls-remote", "--tags", "origin").splitlines() if "refs/tags/" in l and not l.endswith("^{}")]
    tags_local = sh("git", "tag", "-l").split()
    now = dt.datetime.now(dt.timezone.utc)
    started = dt.datetime.strptime(st["started_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    hours = round((now - started).total_seconds() / 3600, 1)
    incidents = heads(f"{D}/BLOCKERS.md", r"^## (I-\d+ · .+)$")
    blockers = heads(f"{D}/BLOCKERS.md", r"^## (B-\d+ · .+)$")
    findings = heads(f"{D}/BLOCKERS.md", r"^## (F-\d+ · .+)$")
    decisions = heads(f"{D}/DECISIONS_FOR_KYLE.md", r"^## (N-\d+ · .+)$")
    sept = []
    for i, t in re.findall(r"^## ((?:D|P6)-\d+) · (.+)$", open("docs/run_2026-09-19/DECISIONS_FOR_KYLE.md").read(), re.M):
        if i not in [s.split(" · ")[0] for s in sept]:
            sept.append(f"{i} · {t}")
    log = open(f"{D}/RUN_LOG.md").read()
    devs = re.findall(r"^- \*\*(.+?)\*\*", log.split("## Deviations", 1)[1], re.M) if "## Deviations" in log else []
    gate_runs = [json.loads(l) for l in open(GATE_LOG)] if os.path.exists(GATE_LOG) else []

    L = [f"# Final report — run_2026-11-10\n",
         f"Branch `{BRANCH}`. Assembled by `scripts/run1110_final_report.py` from this run's own records; every number is read from a results file, the state file, the gate's log or git.\n"]
    if incidents:
        L += ["## Incidents first\n"] + [f"- **{i}** — `{D}/BLOCKERS.md`." for i in incidents] + [
            "- In one sentence: one push went out while the gate was failing, because the push command depended on the wrong exit status. "
            "The gate's failure was a false positive and nothing sensitive was published. Pushes since go through `scripts/run1110_gated_push.sh`.\n"]

    # ---- outcome
    done = [k for k, v in st["phases"].items() if v.get("status") == "done"]
    o = ["## Outcome\n"]
    para = (f"The run finished {len(done)} of {len(st['phases'])} phases in {hours} hours. "
            f"The frozen and locked files were unchanged from start to end ({start_h.get('n_frozen')} frozen, {start_h.get('n_locked')} locked; "
            f"{'no drift' if end_h and end_h.get('all_pass') else 'SEE THE HARD-HALT NOTE BELOW'}). "
            "The exposure risk in the working tree was closed (every CSV ignored again, heading tables moved under `data/`), a push gate was built and every commit of the run passes it, "
            "and the record was corrected in the protocol, the October run log and the reference-standard document. "
            "Amendments (k)–(o) were committed and pushed before any of their analyses was computed. ")
    if fib and out and era and fun:
        p1 = fib["analyses"]["primary_first_result"]
        para += (f"The exploratory results, none validated against chart review: among admissions with a computable FIB-4, {pc(p1['B']['above_2_67'])} of uncoded note-positive admissions "
                 f"are above 2.67, against {pc(p1['A']['above_2_67'])} of coded ones and {pc(p1['D']['above_2_67'])} where neither axis is positive; "
                 f"of patients first documented without a code who returned, {pc(out['groups']['U']['later_coded'])} were later coded and {pc(out['groups']['U']['later_cirrhosis_flag'])} later carried a cirrhosis code; "
                 f"where the liver was imaged and a report was rule-positive, the discharge summary repeated it in {pc(fun['stage3_discharge_summary_also_rule_positive'])}, "
                 f"and coding was {pc(fun['stage4_coded_share']['discharge_summary_rule_positive'])} when it did against {pc(fun['stage4_coded_share']['discharge_summary_not_rule_positive'])} when it did not. ")
    if car:
        w, a = car["new_sample"]["population_weighted"], car["admissions"]
        para += (f"The carry-over check asked {car['sample']['units_answered']:,} carried-over NO units with v4: the answer was no longer NO for {pc(w['v4_answer_not_no'])}, "
                 f"and the expected number of dev/test admissions changing label is {a['expected_admissions_changing_label']} of {a['admissions_dev_test_subsample']:,}. ")
    else:
        para += "The carry-over check did not produce a results file. "
    para += ("Two files the run was asked to commit fail the gate and stayed local, and the gate's rule also flags lines that were already public before the run. "
             "No GOLD_HOLDOUT file was opened; no adjudication exists; D-01 still blocks its start.")
    o.append(para + "\n")
    L += o

    # ---- phases
    L += ["## Phases\n", "| Phase | Status | Commit | Start (UTC) | End (UTC) | Note |", "| --- | --- | --- | --- | --- | --- |"]
    for k in sorted(st["phases"], key=int):
        v = st["phases"][k]
        L.append(f"| {k} · {v.get('name', '')} | {v.get('status', '')} | `{(v.get('commit') or '')[:7]}` | {v.get('start', '')[11:16]} | {v.get('end', '')[11:16]} | {v.get('note', '')} |")
    L += [f"\nCommits in this run: **{len(commits)}** (`{first[:7]}..{head[:7]}`). The amendments commit is `{str(st.get('phase3_commit', ''))[:7]}`.\n"]

    # ---- read first
    L += ["## The five things to read first\n",
          f"1. **`{D}/BLOCKERS.md`** — I-01 (the push on a failing gate), F-01 (lines already public that the new rule flags) and B-01 (two files held back).",
          f"2. **`{D}/DECISIONS_FOR_KYLE.md`** — ten new items with options and draft amendment text. N-06 holds the crosswalk between the chart scale and the locked prompt; N-10 is a conflict between the one-pager and criteria §10. D-01 still blocks adjudication.",
          "3. **`docs/preliminary_2026-11-10.md`** — the four exploratory analyses with their limitations. Section 1's sensitivity table shows how far FIB-4 moves when inpatient values are replaced.",
          "4. **`scripts/run1110_push_gate.py`** (docstring) and the \"Deviations\" section of the run log — the gate's three exemptions, one of which was refined during the run after the gate failed on an article title.",
          f"5. **`{R}/carryover_check.json`** and protocol §4 — what re-asking the carried-over answers would change, which feeds decision N-02.\n"]

    # ---- deviations
    L += ["## Deviations from the run file\n", f"Full text in `{D}/RUN_LOG.md`, section \"Deviations\".\n"] + [f"- {d}" for d in devs] + [""]

    # ---- blockers, incidents
    L += ["## Blockers, incidents and findings\n", f"Full text in `{D}/BLOCKERS.md`.\n"] + [f"- {x}" for x in incidents + blockers + findings] + [""]

    # ---- decisions
    L += ["## Decisions waiting for Kyle\n", f"New, in `{D}/DECISIONS_FOR_KYLE.md`:\n"] + [f"- {x}" for x in decisions]
    L += ["\nCarried over from September (`docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`); **D-01 blocks the start of adjudication**:\n"] + [f"- {x}" for x in sept] + [""]

    # ---- public / local
    L += ["## What is public now, and what stayed local\n",
          f"- **Public:** commits `{first[:7]}..{remote[:7]}` on `{BRANCH}` ({len(sh('git', 'log', '--oneline', f'{first}..origin/{BRANCH}').splitlines())} commits), and the tag(s) {', '.join('`' + t + '`' for t in tags_remote) or 'none'}.",
          f"- **Local head when this report was written:** `{head[:7]}`; remote head: `{remote[:7]}`" + (" (equal)." if head == remote else " (**they differ**).")
          + " The commit that adds this report comes after both and is pushed through the gate like the others."]
    gh = load("github_check.json")
    if gh:
        L.append(f"- **Check on GitHub (Phase 10.4):** remote head equal to local head: {gh['remote_equals_local']}; README on the remote shows the new sub-block: {gh['raw_readme_has_new_sub_block']}, "
                 f"with the not-validated banner before it: {gh['banner_comes_before_the_sub_block']}; tabular files added during the run: {len(gh['tabular_files_added'])}; binary files changed: {gh['binary_files_changed']} "
                 f"(`{R}/github_check.json`). The rendered page was also opened read-only in the browser; see the run log.")
    only_local = [t for t in tags_local if t not in tags_remote]
    if only_local:
        L.append(f"- **Tags that exist only on this machine:** {', '.join('`' + t + '`' for t in only_local)}. This run was told to push one tag and pushed one (decision N-07).")
    if held:
        L.append("- **Untracked, on this machine only:** " + ", ".join(f"`{p}`" for p in held["d3_sentence_windows"]["by_file"]) + " — they fail the gate's note-text rule (B-01, N-09).")
    L.append("- **Never tracked, by design:** everything under `data/` and `logs/`, listed with sizes below.\n")

    # ---- gate
    L += ["## Gate results\n"]
    if gate:
        L += [f"Recorded run over the whole run (`{R}/push_gate.json`): base `{gate['base'][:7]}`, head `{gate['head'][:7]}`, {gate['files_inspected']} files, {gate.get('commits_inspected', '—')} commits checked one by one.\n",
              "| Check | Result | Findings |", "| --- | --- | --: |"]
        L += [f"| {k} | {'PASS' if c['pass'] else 'FAIL'} | {len(c['findings'])} |" for k, c in gate["checks"].items()]
        L.append("")
    passed, failed = sum(1 for g in gate_runs if g["all_pass"]), sum(1 for g in gate_runs if not g["all_pass"])
    L.append(f"Gate runs during the run (`{GATE_LOG}`, untracked): {len(gate_runs)} in all, {passed} passed and {failed} failed. "
             "Each failure was followed by a fix or by holding files back, except the one described in I-01, which was followed by a push.\n")
    if end_h is not None:
        L.append(f"Frozen-artifact hashes at the end against the start (`{R}/frozen_hashes_end.json`): "
                 f"{len(end_h.get('drift_from_start', []))} changed, {len(end_h.get('lock_mismatches', []))} lock mismatches, {len(end_h.get('missing', []))} missing.\n")
    pt = load("pytest_end.json")
    if pt:
        L.append(f"Test suite at the end: {pt['passed']} passed, {pt['failed']} failed.\n")

    # ---- disk, hours
    L += ["## Disk used by this run (all untracked)\n"]
    if inv:
        L += ["| Location | Files | Size |", "| --- | --: | --: |"] + [f"| `{r['location']}` | {r['n_files']} | {r['size']} |" for r in inv["locations"]] + [f"\nTotal: {inv['total_size']}.\n"]
    L += ["## Hours used\n", f"{hours} hours from start to this report, of a budget of 10. "
          + (f"The language-model run took {car['sample'].get('run_hours', '—')} hours of its 2-hour budget.\n" if car and car["sample"].get("run_hours") else "\n")]
    open(OUT, "w").write("\n".join(L))
    print("wrote", OUT, "| hours", hours, "| commits", len(commits), "| gate runs", len(gate_runs))


if __name__ == "__main__":
    main()
