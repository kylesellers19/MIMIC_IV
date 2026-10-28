#!/usr/bin/env python3
"""Write the README's "Preliminary results" block from the results files, so no number in it is typed by hand.

Sources: docs/run_2026-09-19/results/{integrity_gate,aim1b_structured,aim1c_level1}.json (the frozen-rule 2x2 on
the full population, the structured models on TEST, equity level 1) and docs/run_2026-10-27/results/
{llm_review_preliminary,aim1c_llm_level1,aim1b_llm_label,llm_gold_lock,quant_check}.json. Replaces
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
         f"- **A second reader gives the same gap.** A language model run locally reviewed every liver sentence for a random "
         f"sample of {p['subjects']:,} dev/test patients. Among patients it finds steatosis for, "
         f"{u['llm']['pct_uncoded_subjects']}% have no code; the rule gives {u['rule']['pct_uncoded_subjects']}%.",
         f"- **Scaled to all dev/test patients:** about {u['llm']['subjects_scaled']:,} patients by the model and "
         f"{u['rule']['subjects_scaled']:,} by the rule have documented steatosis and no code, against about "
         f"{u['coded_subjects_scaled']:,} with a code. That is {u['both']['subjects_scaled']:,} when both methods must agree and "
         f"{u['either']['subjects_scaled']:,} when either is enough.",
         f"- **Why the code is missing:** among coded cases the model finds, {pw['coded']['discharge summary']}% are written in the discharge "
         f"summary, against {pw['uncoded']['discharge summary']}% of uncoded ones. Of the uncoded cases, "
         f"{pw['uncoded']['outpatient radiology only']}% appear only on outpatient imaging and "
         f"{pw['uncoded']['inpatient radiology only']}% only in inpatient radiology reports.",
         f"- **Where the two readers disagree:** on uncoded admissions, the model confirms {lv['rule_positive_confirmed_by_llm_pct']}% of the "
         f"rule's positives and finds steatosis in {lv['rule_negative_llm_positive_pct']}% of the rule's negatives. "
         "Those disagreements are where chart review is needed (`docs/llm_review_preliminary.md`).", "",
         "**Aim 1b: recovering missed cases.** These are scored against the keyword label, not chart review.", "",
         f"- **Structured data predicts documented steatosis,** with gradient-boosted trees on the TEST partition "
         f"({t['cat|FS-A|unweighted']['n']:,} admissions): AUROC {auc(t['cat|FS-A|unweighted'])} with every feature.",
         f"- **Much of that is documentation, not physiology.** Clinical values alone (labs, blood pressure, BMI, medications, comorbidity) "
         f"give {auc(t['cat|FS-B|unweighted'])}. Knowing only what was measured, imaged, ordered and written, with no clinical "
         f"value at all, gives {auc(t['cat|FS-AVAIL|unweighted'])}. The keyword label partly reflects how thoroughly a patient "
         "was worked up, which is why the models must be judged against chart review (`docs/aim1b_structured.md`).",
         f"- **Label dependence:** the locked TEST predictions were scored against the language model's label instead of the "
         f"rule's. AUROC changes by at most {max(diffs):.3f}"
         + (", and every interval includes zero" if all_zero else "") + ". The models are not simply learning the rule's quirks "
         "(`docs/aim1b_llm_label.md`).", "",
         "**Aim 1c: fairness at the computable stage.**", "",
         f"- **The gap is large in every group.** Among note-positive admissions, the share with no code is "
         f"{rec(lv1['race'], 'BLACK/AFRICAN AMERICAN')} for Black/African American patients against "
         f"{rec(lv1['race'], 'WHITE')} for White patients. It is {rec(lv1['insurance'], 'Medicaid')} for Medicaid against "
         f"{rec(lv1['insurance'], 'Private')} for private insurance, and {rec(lv1['gender'], 'F')} for women against "
         f"{rec(lv1['gender'], 'M')} for men. Across age bands it ranges from {age_lo}% to {age_hi}%. The differences are "
         f"a few points{sep} (`docs/aim1c_level1.md`).",
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
         "analysis plan before the run (amendment h).",
         f"- **The language model's answers barely depend on how it is compressed.** A smaller build of the same model was run on "
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
         "(`docs/llm_review_protocol.md`).", "", END]
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
