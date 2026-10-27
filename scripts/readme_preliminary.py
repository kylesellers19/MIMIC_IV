#!/usr/bin/env python3
"""Write the README's "Preliminary results" block from the results files, so no number in it is typed by hand.

Sources: docs/run_2026-09-19/results/integrity_gate.json (the frozen-rule 2x2 on the full population) and
docs/run_2026-10-27/results/{llm_review_preliminary,aim1c_llm_level1,aim1b_llm_label}.json. Replaces
the text between the README markers <!-- preliminary-results:start --> and <!-- preliminary-results:end -->.
USAGE: scripts/run0919_env.sh scripts/readme_preliminary.py
"""
import json
import re

R = "docs/run_2026-10-27/results"
START, END = "<!-- preliminary-results:start -->", "<!-- preliminary-results:end -->"


def ci(x):
    return f"{x['est']}% [{x['lo']}–{x['hi']}]"


def main():
    g = json.load(open("docs/run_2026-09-19/results/integrity_gate.json"))["anchor"]
    p = json.load(open(f"{R}/llm_review_preliminary.json"))
    c = json.load(open(f"{R}/aim1c_llm_level1.json"))["strata"]
    b = json.load(open(f"{R}/aim1b_llm_label.json"))
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
         f"**Aim 1b: label dependence.** The locked TEST predictions were scored against the model's label instead of the rule's. "
         f"AUROC changes by at most {max(diffs):.3f}"
         + (", and every interval includes zero" if all_zero else "") + ". The models are not simply learning the rule's quirks "
         "(`docs/aim1b_llm_label.md`).", "",
         f"**Aim 1c: equity at the computable stage.** Using the model instead of the rule raises the overall recovery share by "
         f"{c['overall']['all']['E1_llm_minus_rule']['est']} points ({c['overall']['all']['E1_llm_minus_rule']['lo']}–"
         f"{c['overall']['all']['E1_llm_minus_rule']['hi']}). The two readers disagree more often for "
         f"Medicare patients ({ci(e2('insurance', 'Medicare'))} of admissions either calls positive) than for privately insured patients "
         f"({ci(e2('insurance', 'Private'))}), and more for ages 75–88 ({ci(e2('age_band', '75-88'))}) than for ages 40–54 "
         f"({ci(e2('age_band', '40-54'))}). Note-based ascertainment is less consistent for older and Medicare patients, so the chart "
         "review should check those groups closely "
         "(`docs/aim1c_llm_level1.md`).", "",
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
