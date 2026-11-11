#!/usr/bin/env python3
"""run_2026-11-10 Phase 7 — the manuscript drafts catch up with the language-model arm.

Edits three documents, each between markers so a rerun replaces its own block and nothing else:
  docs/manuscript_methods_draft.md     §14 "Local language-model review" (from the protocol and results files),
                                       and one sentence on when the model-selection metric was fixed
  docs/manuscript_results_skeleton.md  Table 6 (language-model arm, preliminary) and Table 7 (the Phase 5
                                       exploratory analyses), plus two provenance rows
  docs/tripod_ai_checklist.md          the TRIPOD-LLM items of protocol §8

Every number comes from a results JSON or from a constant of the script that ran the analysis. The
carry-over check is written from its results file when it exists and as [PENDING] when it does not.
"""
import json, os, re, sys

sys.path.insert(0, os.getcwd())
from scripts.liver_sentences import CAP
from scripts.llm_sentence_review import OPTIONS, TOP_LOGPROBS
from scripts import run1110_preliminary_doc as PD

R10 = "docs/run_2026-10-27/results"
R11 = "docs/run_2026-11-10/results"
START = "<!-- run_2026-11-10 language-model arm: start -->"
END = "<!-- run_2026-11-10 language-model arm: end -->"
METHODS, RESULTS, CHECK = "docs/manuscript_methods_draft.md", "docs/manuscript_results_skeleton.md", "docs/tripod_ai_checklist.md"


def load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def n(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def put_block(text, block, before):
    """Insert (or replace) the marked block immediately before the line `before`."""
    block = f"{START}\n\n{block.rstrip()}\n\n{END}\n\n"
    if START in text:
        return text[:text.index(START)] + block + text[text.index(END) + len(END):].lstrip("\n")
    assert before in text, f"anchor not found: {before}"
    i = text.index(before)
    return text[:i] + block + text[i:]


def pc(s):
    """a share dict from the carry-over file -> text"""
    if not s or "pct" not in s:
        return "not reported"
    if isinstance(s["pct"], str):
        hi = s.get("wilson_hi_pct_at_10", s.get("wilson_hi_pct"))
        return f"{s['pct']}%" + (f" (95% upper bound {hi}%)" if hi is not None else "")
    return f"{s['pct']}% ({s['wilson_lo_pct']}–{s['wilson_hi_pct']})"


def carryover_methods(c):
    if not c:
        return ("**Carry-over check (amendment k).** [PENDING] The check was specified in amendment (k) before it was run; "
                f"its results file (`{R11}/carryover_check.json`) did not exist when this section was written.")
    s, w, a = c["sample"], c["new_sample"]["population_weighted"], c["admissions"]
    return ("**Carry-over check (amendment k).** On dev/test, v3's NO answers were carried into the merged labels without being re-asked. "
            f"To test that, {n(s['units_answered'])} of those units, drawn in two strata, were asked with v4 on the pinned model. "
            f"Population-weighted, the v4 answer was not NO for {pc(w['v4_answer_not_no'])} of carried-over units, and the unit would change "
            f"whether its admission counts as positive for {pc(w['primary_label_status_changes'])}. "
            f"Applied to the admissions that are currently negative, that is an expected {n(a['expected_admissions_changing_label'])} "
            f"of {n(a['admissions_dev_test_subsample'])} dev/test admissions changing label (upper bound {n(a['upper_bound_wilson'])}). "
            f"No stored answer or label was changed. Source: `{R11}/carryover_check.json`.")


def methods_block():
    lock, q, prel = load(f"{R10}/llm_gold_lock.json"), load(f"{R10}/quant_check.json"), load(f"{R10}/llm_review_preliminary.json")
    cap, c = load(f"{R11}/extractor_cap.json"), load(f"{R11}/carryover_check.json")
    rc, m, d = lock["run_counts"], lock["model"], q["qat_vs_q4_rerun"]
    runs = prel["runs"]
    return "\n".join([
        "## 14. Local language-model review of liver sentences (exploratory; added 2026-11-10)", "",
        "This arm was not in the 7 September plan. Amendments (h)–(k) of `docs/analysis_plan_prespecified.md` govern it, and `docs/llm_review_protocol.md` describes it in full. "
        "It assigns no reference-standard label. Written by `scripts/run1110_manuscript_llm.py` from the protocol and the results files named below.", "",
        "**Sentence selection.** `scripts/liver_sentences.py` reads discharge summaries, inpatient radiology reports, and outpatient radiology reports from 365 days before to 30 days after admission. "
        "Hard-wrapped lines are rejoined into sentences. A sentence is kept when it names the liver, when its nearest heading names the liver, when it contains one of a fixed list of disease abbreviations "
        "(NAFLD, NAFL, NASH, MASLD, MASH, MAFLD, MetALD), or when it contains a steatosis term and names no competing organ. The extractor does not import the frozen rule's trigger lexicon. "
        f"At most {CAP} sentences are kept per admission, impression first; the cap bound {n(cap['admissions_cap_bound'])} of {n(cap['admissions_dev_test_subsample'])} dev/test admissions "
        f"(`{R11}/extractor_cap.json`). Each sentence is stored with its note type, nearest heading and neighbouring sentences.", "",
        f"**Model and pinning.** Gemma 4 26B ({m['parameter_size']}, {m['quantization']} quantization), served by Ollama {m['ollama_version']} on the study laptop; model digest `{m['digest'][:12]}`. "
        "The digest, model details, Ollama version and hardware are written to each run's manifest, and a run refuses to resume if any of them changes. "
        "Cloud-served models are refused; automatic updates and Ollama cloud are switched off; the server listens on the local interface only. No note text leaves the machine.", "",
        f"**Decoding.** Temperature {OPTIONS['temperature']}, seed {OPTIONS['seed']}, reasoning off, at most {OPTIONS['num_predict']} output tokens, one request at a time. "
        "The reply is two words: YES, NO or UNCLEAR, then CURRENT, PAST, FAMILY or NA. It is parsed strictly. "
        f"P(YES), P(NO) and P(UNCLEAR) are read from the first token's top {TOP_LOGPROBS} alternatives. "
        "A unit is the sentence text plus the context fields shown to the model; each distinct unit is asked once.", "",
        "**Prompts and how they were developed.** Four versions; the texts are in the protocol and in `scripts/llm_sentence_review.py`.", "",
        f"- v1 and v2 were compared on a {n(prel['pilot_dev']['n'])}-sentence pilot drawn from DEV and TEST.",
        "- v3 gives the note type and heading, states explicit answer rules, and adds the timing word. It was developed against invented sentences and DEV only.",
        "- v4 is v3 plus one NO rule: alcohol-related liver disease, alcoholic hepatitis, and cirrhosis or liver fibrosis are NO unless the sentence also says the liver is fatty.",
        "- **Two disclosures about TEST.** First, the v1-to-v2 pilot included TEST sentences. Second, the v4 rule was decided from count-level diagnostics over DEV and TEST sentences. "
        "TEST is therefore not independent of prompt development for this arm. GOLD_HOLDOUT was never used for prompt development.",
        f"- **How v4 was applied.** On dev/test, v3 answered all {n(runs['full_v3_devtest']['units'])} distinct units; v4 then re-asked the {n(runs['full_v4_reask']['units'])} units v3 had answered YES or UNCLEAR, "
        "and v3's NO answers were carried over. On GOLD_HOLDOUT, v4 answered every unit.", "",
        "**Admission rule.** An admission is positive when at least one kept sentence is YES with timing CURRENT or PAST. FAMILY never counts. UNCLEAR is not positive. "
        "Sensitivity definitions: UNCLEAR counted positive; CURRENT only; anatomy-only selection. The rule text was committed before the GOLD_HOLDOUT run started "
        f"(`{R11}/signoff_timeline.json`). It was signed off on 2026-10-27 by the study lead, who is not a clinician. Clinician review of the rule is outstanding.", "",
        f"**Lock.** Before any chart review, v4 answered all {n(rc['distinct_units'])} distinct units of the {n(rc['gold_admissions'])} GOLD_HOLDOUT admissions "
        f"({n(rc['sentence_rows'])} sentence rows, {n(rc['errors'])} errors). The sentence-answers file with its three probabilities, the admission labels, the extractor output and the run manifest were hashed "
        "(`docs/llm_gold_lock.md`). The lock commit carries the tag `llm-gold-lock-v1`. The per-shard answer files are not hashed. No answer distribution on GOLD_HOLDOUT has been looked at.", "",
        f"**Quantization check.** {n(q['units_sampled'])} distinct dev/test units, stratified by stored answer, were answered on the same day by the study build and by Gemma 4's quantization-aware build. "
        f"The answer differed for an estimated {d['answer_differs']['pct']}% of units (conservative 95% bounds {d['answer_differs']['lo']}–{d['answer_differs']['hi']}%). "
        f"Whether a unit counts toward the admission label differed for {d['primary_status_differs']['pct']}% ({d['primary_status_differs']['lo']}–{d['primary_status_differs']['hi']}%). "
        f"The study keeps the {m['quantization']} build. Source: `{R10}/quant_check.json`.", "",
        carryover_methods(c), "",
        "**What the arm is used for.** A second computable note phenotype, compared with the frozen rule on the dev/test notes subsample (`docs/llm_review_preliminary.md`). "
        "It is scored against chart review only through the locked GOLD_HOLDOUT answers. Reviewers never see its output. "
        "Sentence-level validation by two credentialed annotators has not started."])


def demote(lines, tag):
    out = []
    for l in lines:
        if l.startswith("## "):
            out.append("### " + tag.pop(0) + " " + re.sub(r"^\d+\.\s*", "", l[3:]))
        elif l.startswith("### "):
            out.append("#### " + l[4:])
        else:
            out.append(l)
    return out


def results_block():
    prel, lab, lock, q = load(f"{R10}/llm_review_preliminary.json"), load(f"{R10}/aim1b_llm_label.json"), load(f"{R10}/llm_gold_lock.json"), load(f"{R10}/quant_check.json")
    c = load(f"{R11}/carryover_check.json")
    r, al, u, dn = prel["runs"], prel["admission_labels"], prel["llm_vs_rule_uncoded"], prel["documented_not_coded"]
    L = ["## Table 6. Local language-model arm (preliminary; dev/test notes subsample)", "",
         "> **PRELIMINARY and exploratory (amendments h–k).** Nothing in Table 6 is validated against human review. Filled by `scripts/run1110_manuscript_llm.py` from the files named in the provenance index. Counts from 1 to 10 appear as <11.", "",
         f"Scope: {n(prel['admissions'])} admissions of {n(prel['subjects'])} subjects, a simple random sample of dev/test subjects.", "",
         "### 6a. Runs", "", "| Run | Prompt | Distinct units | Errors | Unparsed | Compute hours |", "| --- | --- | --: | --: | --: | --: |",
         f"| Dev/test, all units | {r['full_v3_devtest']['variant']} | {n(r['full_v3_devtest']['units'])} | {n(r['full_v3_devtest']['errors'])} | {n(r['full_v3_devtest']['unparsed'])} | {r['full_v3_devtest']['compute_hours']} |",
         f"| Dev/test, re-ask of YES and UNCLEAR | {r['full_v4_reask']['variant']} | {n(r['full_v4_reask']['units'])} | {n(r['full_v4_reask']['errors'])} | {n(r['full_v4_reask']['unparsed'])} | {r['full_v4_reask']['compute_hours']} |",
         f"| GOLD_HOLDOUT, all units (locked) | {lock['prompt']['variant']} | {n(lock['run_counts']['distinct_units'])} | {n(lock['run_counts']['errors'])} | {n(lock['run_counts']['unparsed'])} | not recorded |", "",
         "### 6b. Admissions positive under each definition", "", "| Definition | Admissions |", "| --- | --: |",
         f"| Language model, primary (YES, current or past) | {n(al['llm'])} |", f"| Language model, UNCLEAR counted positive | {n(al['llm_unclear'])} |",
         f"| Language model, current only | {n(al['llm_current'])} |", f"| Language model, anatomy-only selection | {n(al['llm_anatomy'])} |",
         f"| Frozen keyword rule | {n(al['rule'])} |", "",
         "### 6c. Language model against the frozen rule, uncoded admissions", "",
         f"Restricted to the {n(u['admissions'])} admissions without a MASLD code. The coded group is reported only as totals, because its cells include counts below 11.", "",
         "| | Rule positive | Rule negative |", "| --- | --: | --: |",
         f"| **Model positive** | {n(u['both'])} | {n(u['llm_only'])} |", f"| **Model negative** | {n(u['rule_only'])} | {n(u['neither'])} |", "",
         f"The model confirms {u['rule_positive_confirmed_by_llm_pct']}% of rule-positive uncoded admissions and adds {u['rule_negative_llm_positive_pct']}% of rule-negative ones.", "",
         "### 6d. Documented in notes, not coded", "", "| Note phenotype | Admissions | Subjects | Share of note-positive subjects uncoded |", "| --- | --: | --: | --: |"]
    for key, name in (("both", "Rule and model agree"), ("rule", "Frozen keyword rule"), ("llm", "Language model"), ("either", "Either")):
        L.append(f"| {name} | {n(dn[key]['admissions'])} | {n(dn[key]['subjects'])} | {dn[key]['pct_uncoded_subjects']}% |")
    L += ["", "### 6e. Aim 1b label dependence (amendment j): locked TEST predictions scored against each label", "",
          f"TEST admissions of the subsample: {n(lab['test_admissions'])}. No model was retrained.", "",
          "| Arm | AUROC, rule label | AUROC, model label | Difference (95% CI) | AUPRC, rule label | AUPRC, model label |", "| --- | --: | --: | --: | --: | --: |"]
    for arm, v in lab["arms"].items():
        a, p = v["all"]["AUROC"], v["all"]["AUPRC"]
        L.append(f"| {arm} | {a['rule']} | {a['llm']} | {a['llm_minus_rule']:+} ({a['diff_ci'][0]:+} to {a['diff_ci'][1]:+}) | {p['rule']} | {p['llm']} |")
    d = q["qat_vs_q4_rerun"]
    L += ["", "### 6f. Stability checks", "", "| Check | Units | Answer differs | Admission-label status differs |", "| --- | --: | --: | --: |",
          f"| Quantization-aware build against the study build | {n(q['units_sampled'])} | {d['answer_differs']['pct']}% ({d['answer_differs']['lo']}–{d['answer_differs']['hi']}) | "
          f"{d['primary_status_differs']['pct']}% ({d['primary_status_differs']['lo']}–{d['primary_status_differs']['hi']}) |"]
    if c:
        w = c["new_sample"]["population_weighted"]
        L.append(f"| Carried-over v3 NO answers re-asked with v4 (amendment k) | {n(c['sample']['units_answered'])} | {pc(w['v4_answer_not_no'])} | {pc(w['primary_label_status_changes'])} |")
        a = c["admissions"]
        L += ["", f"Carry-over check: expected dev/test admissions changing label if every carried-over NO were re-asked: {n(a['expected_admissions_changing_label'])} "
              f"of {n(a['admissions_dev_test_subsample'])} (upper bound {n(a['upper_bound_wilson'])})."]
    else:
        L.append("| Carried-over v3 NO answers re-asked with v4 (amendment k) | [PENDING] | [PENDING] | [PENDING] |")
    L += ["", "### 6g. Language-model arm against the gold standard", "",
          "**[PENDING ADJUDICATION].** The GOLD_HOLDOUT answers are locked (`docs/llm_gold_lock.md`, tag `llm-gold-lock-v1`) and have not been looked at.", "",
          "---", "",
          "## Table 7. Exploratory analyses of 10 November 2026 (amendments l–o)", "",
          "> **PRELIMINARY and exploratory.** Not validated against chart review. The same tables, with their limitations, are in `docs/preliminary_2026-11-10.md`. "
          "The amendments were committed before the analyses were computed.", ""]
    L += demote(PD.fib4_section(load(f"{R11}/fib4_by_cell.json")), ["7a."]) + demote(PD.outcomes_section(load(f"{R11}/later_outcomes.json")), ["7b."]) \
        + demote(PD.era_section(load(f"{R11}/icd_era.json")), ["7c."]) + demote(PD.funnel_section(load(f"{R11}/imaging_funnel.json")), ["7d."])
    L += ["---"]
    return "\n".join(L)


def checklist_block():
    rows = [
        ("Model name, version, training cutoff (TRIPOD-LLM 6a)", "Methods §14 \"Model and pinning\"; protocol §3; run manifest", "satisfied"),
        ("Inference settings and output consistency (6c)", "Methods §14 \"Decoding\", \"Quantization check\", \"Carry-over check\"; protocol §3 and §6; a full rerun in every pilot", "satisfied"),
        ("Raw against parsed output, thresholds (6d, 6e)", "Protocol §3 and §5; the stored reply, strict flag, stop reason and probabilities", "satisfied"),
        ("Annotation (7d, 8a–c)", "Annotation guide; `scripts/llm_annotation.py`", "pending: needs two credentialed annotators and an adjudicator"),
        ("Prompt development data (9a, 9b; MI-CLAIM-GEN Part 2)", "Methods §14 \"Prompts and how they were developed\", with both disclosures about TEST; protocol §4", "satisfied"),
        ("Compute (12)", "Run manifest (hardware); compute hours in results Table 6a", "partial: no compute record for the GOLD_HOLDOUT run in a tracked file"),
        ("Fairness (TRIPOD+AI 14, 23a; TRIPOD-LLM 19a)", "Protocol §6; sentence coverage by stratum in `docs/aim1c_llm_level1.md`", "partial: error rates by stratum need the annotated sentences or the adjudication"),
        ("Selection algorithm (RECORD 6.1, 7.1)", "Methods §14 \"Sentence selection\"; protocol §2; `scripts/liver_sentences.py`", "satisfied"),
    ]
    L = ["## TRIPOD-LLM items for the language-model arm (added 2026-11-10)", "",
         "These rows are the reporting map of `docs/llm_review_protocol.md` §8. The item numbers are the ones listed there. They were gathered by literature search and "
         "**have not been checked against the published TRIPOD-LLM checklist**; verify them before submission. Statuses use the vocabulary defined at the top of this file.", "",
         "| Item (source) | Where it is reported | Status |", "| --- | --- | --- |"]
    L += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    L += ["", "---"]
    return "\n".join(L)


def main():
    # the constants this script quotes, written out so the number check can attribute them
    json.dump({"script": "scripts/run1110_manuscript_llm.py", "sentence_cap": CAP, "decoding_options": OPTIONS, "top_logprobs": TOP_LOGPROBS,
               "sources": {"sentence_cap": "scripts/liver_sentences.py CAP", "decoding_options": "scripts/llm_sentence_review.py OPTIONS",
                           "top_logprobs": "scripts/llm_sentence_review.py TOP_LOGPROBS"}},
              open(f"{R11}/manuscript_llm_constants.json", "w"), indent=1)
    s = open(METHODS).read()
    s = put_block(s, methods_block() + "\n\n---", "### Reference notes")
    anchor = "which is the selection rule specified before the arm was run."
    add = (" The selection metric itself, development out-of-fold AUPRC, was fixed during the 19 September 2026 run and not in the 7 September plan: "
           "it appears neither in the hypotheses recorded on 7 September nor in the pre-specification commit (`e2a4e1e`). *(Sentence added 2026-11-10.)*")
    if "was fixed during the 19 September 2026 run" not in s:
        assert anchor in s
        s = s.replace(anchor, anchor + add, 1)
    open(METHODS, "w").write(s)

    s = open(RESULTS).read()
    s = put_block(s, results_block(), "## Provenance index")
    rows = ("| 6a–6g | `docs/run_2026-10-27/results/llm_review_preliminary.json`, `aim1b_llm_label.json`, `llm_gold_lock.json`, `quant_check.json`; `docs/run_2026-11-10/results/carryover_check.json` |\n"
            "| 7a–7d | `docs/run_2026-11-10/results/fib4_by_cell.json`, `later_outcomes.json`, `icd_era.json`, `imaging_funnel.json` → `docs/preliminary_2026-11-10.md` |\n")
    if "| 6a–6g |" not in s:
        last = "| 5b–5e | **do not exist**: require the chart adjudication |\n"
        assert last in s
        s = s.replace(last, last + rows, 1)
    open(RESULTS, "w").write(s)

    s = open(CHECK).read()
    s = put_block(s, checklist_block(), "## Summary of what blocks completion")
    open(CHECK, "w").write(s)
    print("methods §14, results Tables 6-7, checklist TRIPOD-LLM rows written; carry-over:",
          "filled" if os.path.exists(f"{R11}/carryover_check.json") else "[PENDING]")


if __name__ == "__main__":
    main()
