#!/usr/bin/env python3
"""Write the README's "Preliminary results" block from the results files, so no number in it is typed by hand.

Sources: docs/run_2026-09-19/results/{integrity_gate,aim1b_structured,aim1c_level1}.json (the frozen-rule 2x2 on
the full population, the structured models on TEST, equity level 1) and docs/run_2026-10-27/results/
{llm_review_preliminary,aim1c_llm_level1,aim1b_llm_label,llm_gold_lock,quant_check}.json, and, for the sub-block
"Exploratory, added 10 November 2026", docs/run_2026-11-10/results/{fib4_by_cell,later_outcomes,icd_era,
imaging_funnel,carryover_check}.json. Replaces
the text between the README markers <!-- preliminary-results:start --> and <!-- preliminary-results:end -->.
USAGE: scripts/run0919_env.sh scripts/readme_preliminary.py
"""
import json
import re

R = "docs/run_2026-10-27/results"
START, END = "<!-- preliminary-results:start -->", "<!-- preliminary-results:end -->"


def ci(x):
    return f"{x['est']}% [{x['lo']}–{x['hi']}]"


def auc(m):
    return f"{m['auroc']:.3f} ({m['auroc_ci'][0]:.3f}–{m['auroc_ci'][1]:.3f})"


def rec(rows, name):
    r = next(r for r in rows if r["stratum"] == name)
    return f"{r['recovery_share_pct']}% [{r['rec_ci'][0]}–{r['rec_ci'][1]}]"


R11 = "docs/run_2026-11-10/results"


def november_block():
    """Sub-block "Exploratory, added 10 November 2026", from docs/run_2026-11-10/results/*.json (amendments k-o).
    Same rules as the rest of the block: script-written, small cells already masked in the results files."""
    import os
    load = lambda f: json.load(open(f"{R11}/{f}.json")) if os.path.exists(f"{R11}/{f}.json") else None
    fib, out, era, fun, car = load("fib4_by_cell"), load("later_outcomes"), load("icd_era"), load("imaging_funnel"), load("carryover_check")
    if not all((fib, out, era, fun)):
        return []
    pc = lambda s: f"{s['pct']}%" if isinstance(s.get("pct"), (int, float)) else str(s.get("pct", "not reported"))
    pci = lambda s: f"{s['pct']}% [{s['ci95'][0]}–{s['ci95'][1]}]" if isinstance(s.get("pct"), (int, float)) and s.get("ci95") else pc(s)
    p1, p4 = fib["analyses"]["primary_first_result"], fib["analyses"]["sens4_outpatient_365_days_before_admission"]
    U, C = out["groups"]["U"], out["groups"]["C"]
    yr = [r for r in era["by_anchor_year_group"] if r["primary_code_set"].get("reported")]
    icd = {r["stratum"]: r for r in era["by_icd_version"]}
    s4 = fun["stage4_coded_share"]
    L = ["**Exploratory, added 10 November 2026.** Four analyses on the frozen keyword rule and one check of the language model's labels. "
         "Their definitions (amendments k–o) were committed before any of them was computed. None is validated against chart review; "
         "tables and limitations are in `docs/preliminary_2026-11-10.md`.", "",
         f"- **Fibrosis index by cell.** FIB-4 can be computed for {pc(p1['B']['computable'])} of uncoded note-positive admissions and "
         f"{pc(p1['A']['computable'])} of coded note-positive ones, against {pc(p1['D']['computable'])} where neither codes nor notes are positive. "
         f"Among those, the share above 2.67 is {pci(p1['B']['above_2_67'])} uncoded, {pci(p1['A']['above_2_67'])} coded and "
         f"{pci(p1['D']['above_2_67'])} where neither is positive. FIB-4 is validated in outpatients, and acute illness tends to raise it: with the most "
         f"recent outpatient values the three shares are {pc(p4['B']['above_2_67'])}, {pc(p4['A']['above_2_67'])} and {pc(p4['D']['above_2_67'])}. "
         "Each cell is described on the admissions where FIB-4 could be computed, a differently selected subset in each "
         f"(`{R11}/fib4_by_cell.json`).",
         f"- **Later outcomes.** {U['subjects']:,} patients had a first note-positive admission with no code and no earlier code. "
         f"{pc(U['with_a_later_admission'])} returned to this hospital. Of those, {pci(U['later_cirrhosis_flag'])} later carried a cirrhosis code "
         f"and {pci(U['later_coded'])} were later given a MASLD code, a median of {U['later_coded']['days_from_index_discharge']['median']:,.0f} days "
         f"after discharge. Among patients coded at that first admission who returned, {pci(C['later_cirrhosis_flag'])} later carried a cirrhosis code. "
         f"Only returns to this hospital are seen, so each figure is a floor. The two groups differ in more than coding and nothing is adjusted, "
         f"so the comparison does not estimate what coding changes for a patient (`{R11}/later_outcomes.json`).",
         f"- **Coding by period.** The share of note-positive admissions with no code is {pci(icd['ICD-9 only']['primary_code_set'])} in admissions coded in "
         f"ICD-9 and {pci(icd['ICD-10 only']['primary_code_set'])} in ICD-10. By the patient's anchor year group it runs from "
         f"{pci(yr[0]['primary_code_set'])} ({yr[0]['stratum'].replace(' - ', '–')}) to {pci(yr[-1]['primary_code_set'])} ({yr[-1]['stratum'].replace(' - ', '–')}). "
         f"Period and ICD version change together, so this table cannot separate one from the other (`{R11}/icd_era.json`).",
         f"- **Where the liver was imaged.** Of {fun['stage1_imaging_observed']['x']:,} admissions with liver imaging, a radiology report is "
         f"rule-positive in {pci(fun['stage2_radiology_report_rule_positive'])}. The discharge summary is also rule-positive in "
         f"{pci(fun['stage3_discharge_summary_also_rule_positive'])} of those. When it is, {pci(s4['discharge_summary_rule_positive'])} are coded; "
         f"when it is not, {pci(s4['discharge_summary_not_rule_positive'])}. The two go together; this does not show that the summary is what gets "
         f"the admission coded (`{R11}/imaging_funnel.json`)."]
    if car:
        w, a = car["new_sample"]["population_weighted"], car["admissions"]
        f = lambda s: (f"{s['pct']}% (95% upper bound {s['wilson_hi_pct']}%)" if isinstance(s["pct"], str) else f"{s['pct']}% [{s['wilson_lo_pct']}–{s['wilson_hi_pct']}]")
        L.append(f"- **Carry-over check.** On dev/test, sentences the earlier prompt answered NO were not asked again with the final prompt. "
                 f"A stratified sample of {car['sample']['units_answered']:,} of them was asked: the answer was no longer NO for {f(w['v4_answer_not_no'])}, "
                 f"population-weighted. The expected number of admissions that would change label is {a['expected_admissions_changing_label']} of "
                 f"{a['admissions_dev_test_subsample']:,} (95% upper bound {a['upper_bound_wilson']}). No stored label was changed (`{R11}/carryover_check.json`).")
    else:
        L.append(f"- **Carry-over check.** Specified in amendment (k); its results file (`{R11}/carryover_check.json`) did not exist when this block was written.")
    return L + [""]


def main():
    g = json.load(open("docs/run_2026-09-19/results/integrity_gate.json"))["anchor"]
    p = json.load(open(f"{R}/llm_review_preliminary.json"))
    c = json.load(open(f"{R}/aim1c_llm_level1.json"))["strata"]
    b = json.load(open(f"{R}/aim1b_llm_label.json"))
    t = json.load(open("docs/run_2026-09-19/results/aim1b_structured.json"))["test"]
    lv1 = json.load(open("docs/run_2026-09-19/results/aim1c_level1.json"))["strata"]
    lock = json.load(open(f"{R}/llm_gold_lock.json"))["run_counts"]
    qcj = json.load(open(f"{R}/quant_check.json"))
    qc = qcj["qat_vs_q4_rerun"]
    ages = [r for r in lv1["age_band"] if r.get("rec_claim_supported")]
    pair = lambda var, x, y: [next(r for r in lv1[var] if r["stratum"] == n)["rec_ci"] for n in (x, y)]
    apart = [lab for lab, (p, q) in (("race", pair("race", "BLACK/AFRICAN AMERICAN", "WHITE")),
                                     ("insurance", pair("insurance", "Medicaid", "Private")),
                                     ("sex", pair("gender", "F", "M"))) if p[0] > q[1] or q[0] > p[1]]
    sep = f", and the intervals separate for {' and '.join(apart)}" if apart else ", with overlapping intervals"
    age_lo, age_hi = min(r["recovery_share_pct"] for r in ages), max(r["recovery_share_pct"] for r in ages)
    u, lv, pw, f = p["documented_not_coded"], p["llm_vs_rule_uncoded"], p["documentation_pathway"], p["filter"]
    diffs = [abs(a["all"]["AUROC"]["llm_minus_rule"]) for a in b["arms"].values()]
    all_zero = all(a["all"]["AUROC"]["diff_ci"][0] <= 0 <= a["all"]["AUROC"]["diff_ci"][1] for a in b["arms"].values())
    e2 = lambda var, lv_: c[var][lv_]["E2_discordant"]
    L = [START, "",
         "> **Computable stage only — not yet validated by chart review.** Exploratory. Every number in this block is written by "
         "`scripts/readme_preliminary.py` from the results files it cites; counts from 1 to 10 appear as <11. The 400-chart "
         "clinician review, which sets the headline estimates, has not happened.", "",
         "**Aim 1a: steatosis documented in notes but never coded.**", "",
         f"- **Frozen keyword rule, full population:** {g['b']['B']:,} of {g['note_pos_primary']:,} "
         f"note-positive admissions ({g['recovery_share_pct']}%) carry no MASLD code. The population is "
         f"{g['pop_admissions']:,} admissions of {g['pop_subjects']:,} patients "
         "(`docs/run_2026-09-19/results/integrity_gate.json`).",
         f"- **A second reader gives a similar estimate.** A language model run locally reviewed every liver sentence for a random "
         f"sample of {p['subjects']:,} dev/test patients. Among patients it finds steatosis for, "
         f"{u['llm']['pct_uncoded_subjects']}% have no code; the rule gives {u['rule']['pct_uncoded_subjects']}%.",
         f"- **Scaled to all dev/test patients:** about {u['llm']['subjects_scaled']:,} patients by the model and "
         f"{u['rule']['subjects_scaled']:,} by the rule have documented steatosis and no code, against about "
         f"{u['coded_subjects_scaled']:,} with a code. That is {u['both']['subjects_scaled']:,} when both methods must agree and "
         f"{u['either']['subjects_scaled']:,} when either is enough.",
         f"- **Where the finding is written, by code status:** among coded cases the model finds, {pw['coded']['discharge summary']}% are written in the discharge "
         f"summary, against {pw['uncoded']['discharge summary']}% of uncoded ones. Of the uncoded cases, "
         f"{pw['uncoded']['outpatient radiology only']}% appear only on outpatient imaging and "
         f"{pw['uncoded']['inpatient radiology only']}% only in inpatient radiology reports. This is an association. It does not show that where a finding "
         "is written decides whether it is coded.",
         f"- **Where the two readers disagree:** on uncoded admissions, the model confirms {lv['rule_positive_confirmed_by_llm_pct']}% of the "
         f"rule's positives and finds steatosis in {lv['rule_negative_llm_positive_pct']}% of the rule's negatives. "
         "Only chart review can settle those disagreements (`docs/llm_review_preliminary.md`).", "",
         "**Aim 1b: recovering missed cases.** These are scored against the keyword label, not chart review.", "",
         f"- **Structured data predicts documented steatosis,** with gradient-boosted trees on the TEST partition "
         f"({t['cat|FS-A|unweighted']['n']:,} admissions): AUROC {auc(t['cat|FS-A|unweighted'])} with every feature.",
         f"- **Much of the discrimination comes from what was recorded, not from the clinical values.** Clinical values alone (labs, blood pressure, BMI, medications, comorbidity) "
         f"give {auc(t['cat|FS-B|unweighted'])}. Knowing only what was measured, imaged, ordered and written, with no clinical "
         f"value at all, gives {auc(t['cat|FS-AVAIL|unweighted'])}. One reading is that the keyword label partly reflects how thoroughly a patient "
         "was worked up. That is why the models must be judged against chart review (`docs/aim1b_structured.md`).",
         f"- **Label dependence:** the locked TEST predictions were scored against the language model's label instead of the "
         f"rule's. AUROC changes by at most {max(diffs):.3f}"
         + (", and every interval includes zero" if all_zero else "") + ". That is evidence against the models merely reproducing the rule's "
         "particulars. Neither label has been checked against chart review (`docs/aim1b_llm_label.md`).", "",
         "**Aim 1c: fairness at the computable stage.**", "",
         f"- **The gap is large in every group.** Among note-positive admissions, the share with no code is "
         f"{rec(lv1['race'], 'BLACK/AFRICAN AMERICAN')} for Black/African American patients against "
         f"{rec(lv1['race'], 'WHITE')} for White patients. It is {rec(lv1['insurance'], 'Medicaid')} for Medicaid against "
         f"{rec(lv1['insurance'], 'Private')} for private insurance, and {rec(lv1['gender'], 'F')} for women against "
         f"{rec(lv1['gender'], 'M')} for men. Across age bands it ranges from {age_lo}% to {age_hi}%. The differences are "
         f"a few points{sep}. They are unadjusted: the groups also differ in case mix and in how often the liver is imaged, and no cause is "
         "attributed to the differences (`docs/aim1c_level1.md`).",
         f"- **The two readers disagree unevenly.** Of the admissions either the rule or the language model calls positive, "
         f"they disagree on {ci(e2('insurance', 'Medicare'))} for Medicare patients against {ci(e2('insurance', 'Private'))} "
         f"for privately insured patients, and on {ci(e2('age_band', '75-88'))} for ages 75–88 against "
         f"{ci(e2('age_band', '40-54'))} for ages 40–54. Note-based ascertainment is less consistent for older and Medicare "
         "patients, so the chart review should check those groups closely. Swapping the rule for the language model raises the "
         f"overall recovery share by only {c['overall']['all']['E1_llm_minus_rule']['est']} points "
         f"({c['overall']['all']['E1_llm_minus_rule']['lo']}–{c['overall']['all']['E1_llm_minus_rule']['hi']}) "
         "(`docs/aim1c_llm_level1.md`).", "",
         "**Ready for the chart review.**", "",
         "- **Every model's held-out predictions are hashed and locked** before any chart is reviewed "
         "(`docs/aim1b_locked_predictions.md`).",
         f"- **So are the language model's answers:** it labelled all {lock['gold_admissions']:,} held-out admissions "
         f"({lock['distinct_units']:,} distinct sentences, {lock['errors']} errors), and its answers were hashed. Nothing about those "
         "answers has been looked at (`docs/llm_gold_lock.md`). The rule turning sentence answers into admission labels was in the "
         "analysis plan before the run (amendment h)."
         + (" Against the chart review the language model will be scored as a classifier only: no admission-level probability is defined "
            "for it, a choice fixed on 11 November 2026 before any chart was reviewed (amendment p)."
            if "## 7. Amendment dated 2026-11-11" in open("docs/analysis_plan_prespecified.md").read() else ""),
         f"- **The language model's answers change little with how it is compressed.** A smaller build of the same model was run on "
         f"a stratified sample of {qcj['units_sampled']:,} dev/test sentences. Weighted back to all {qcj['units_population']:,}, it "
         f"changed an estimated {qc['answer_differs']['pct']}% of answers (conservative 95% bounds {qc['answer_differs']['lo']}–"
         f"{qc['answer_differs']['hi']}%). Whether a sentence counts toward the label changed for "
         f"{qc['primary_status_differs']['pct']}% ({qc['primary_status_differs']['lo']}–{qc['primary_status_differs']['hi']}%), "
         "about evenly in each direction (`docs/llm_review_protocol.md` §6).", "",
         f"**Method notes.** The sentence filter was widened to admit NAFLD-type abbreviations, unnamed steatosis and sentences under "
         f"liver headings. That cut the admissions whose steatosis statement never reached the model from "
         f"{f['anatomy_only']['admissions_strong_term_only_dropped']:,} to {f['current']['admissions_strong_term_only_dropped']:,}. "
         f"Prompt rewordings agree with the main prompt at Cohen's kappa {p['pilot_dev']['kappa_v3_paraphrase_a']}–"
         f"{p['pilot_dev']['kappa_v3_context']} on a 500-sentence development pilot "
         "(`docs/llm_review_protocol.md`).", ""] + november_block() + [END]
    text = open("README.md").read()
    block = "\n".join(L)
    if START in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    else:
        text = text.replace("## Obtaining and verifying the data", "## Preliminary results\n\n" + block + "\n\n## Obtaining and verifying the data", 1)
    open("README.md", "w").write(text)
    print("README.md preliminary-results block written")


if __name__ == "__main__":
    main()
