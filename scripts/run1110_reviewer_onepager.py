#!/usr/bin/env python3
"""run_2026-11-10 Phase 6.1 — one page about the chart review, written from results files, in two versions.

  docs/adjudication/reviewer_onepager.md   for prospective REVIEWERS. Says only what the draft criteria (§10)
                                           allow reviewers to be told: that a computable method for finding
                                           hepatic steatosis is being validated. It does not state the study
                                           question, the hypothesis or any result.
  docs/adjudication/study_onepager.md      for people who will NOT review charts (for example a department
                                           lead asked for clinicians' time). States the question and what the
                                           computable stage shows.

The split is option 2 of decision N-10 (docs/run_2026-11-10/DECISIONS_FOR_KYLE.md).
Reads docs/run_2026-09-19/results/{integrity_gate,reviewer_brief,reviewer_assignment}.json and the form's
answer options (scripts/make_adjudication_template.py). The numbers used are written to
docs/run_2026-11-10/results/reviewer_onepager.json. No number is typed here.
What reviewers are offered is not stated: that is decision N-08.
"""
import json, os, sys

sys.path.insert(0, os.getcwd())
from scripts.make_adjudication_template import OPTIONS

R19 = "docs/run_2026-09-19/results"
OUT_REVIEWER = "docs/adjudication/reviewer_onepager.md"
OUT_STUDY = "docs/adjudication/study_onepager.md"
RES = "docs/run_2026-11-10/results/reviewer_onepager.json"


def shared(use):
    """The sections both versions carry: the task, the time, the access, the blinding, what is fixed."""
    opts = ", ".join(o.lower() for o in use["answer_options"])
    return [
        "## What a reviewer does", "",
        f"- **Reads charts.** {use['charts_in_sample']} charts were sampled. Each of {use['reviewers']} reviewers reads {use['charts_per_reviewer']}; {use['charts_read_by_both']} charts are read by both, to measure agreement.",
        "- **A chart is one text file:** the discharge summary, the radiology reports, a short table of laboratory values, vital signs and medication orders.",
        f"- **Answers one main question per chart:** is hepatic steatosis documented? The choices are {opts}.",
        "- **Then a few short follow-ups:** whether it is current or historical, cardiometabolic risk factors, alcohol, any other stated cause, and a one-line reason.",
        f"- **Practice first:** {use['practice_charts']} practice charts. The criteria can be revised once after them; then they are frozen and the main set starts.", "",
        "## Time", "",
        f"- About {use['minutes_per_chart']} minutes per chart, from the length of the text at {use['reading_speed_words_per_minute']} words per minute plus time to fill the form.",
        f"- Main set: about {use['hours_main_set']} hours per reviewer. Practice set: about {use['hours_practice_set']} hours.",
        f"- If only the discharge summary and liver imaging reports are read closely: about {use['hours_main_set_focused_read']} hours for the main set.",
        "- The study team is timing a small pilot set to replace these estimates with measured minutes.", "",
        "## Access you need", "",
        "- Your own PhysioNet credentialed access to MIMIC-IV and MIMIC-IV-Note, with the data use agreement signed in your own name.",
        "- The study cannot send charts to anyone without it. Chart text may not be sent to online services such as chatbots; that is PhysioNet's rule.", "",
        "## Blinding", "",
        "- You will not see diagnosis codes, the output of any computer method, or why a chart was sampled.",
        "- The two reviewers work independently.", "",
        "## What is already fixed", "",
        "- The sample of charts.",
        "- The output of every computer method that will be compared with your answers. All of it was recorded, with file hashes, before any chart review.",
        "- **Not yet fixed:** the review criteria. They are a draft with open clinical questions that clinicians need to settle before review starts.", "",
        "## What reviewers are offered", "",
        "To be completed by the study lead.", ""]


def main():
    g = json.load(open(f"{R19}/integrity_gate.json"))["reproduced"]
    b = json.load(open(f"{R19}/reviewer_brief.json"))["estimate"]
    a = json.load(open(f"{R19}/reviewer_assignment.json"))
    rng = lambda v: f"{round(min(v))}–{round(max(v))}"
    use = {"script": "scripts/run1110_reviewer_onepager.py",
           "hospital_stays": g["pop_admissions"], "stays_with_code": g["code_positive"],
           "stays_with_note_statement": g["note_pos_primary"], "pct_of_those_without_code": g["recovery_share_pct"],
           "charts_in_sample": sum(g["alloc"].values()), "reviewers": a["n_reviewers"], "charts_read_by_both": a["double_review_total"],
           "charts_per_reviewer": b["charts_per_reviewer"], "practice_charts": b["training_charts"],
           "minutes_per_chart": rng(b["minutes_per_chart"]["full"]), "hours_main_set": rng(b["hours_per_reviewer_sample"]["full"]),
           "hours_practice_set": rng(b["hours_per_reviewer_training"]["full"]),
           "hours_main_set_focused_read": rng(b["hours_per_reviewer_sample"]["focused"]),
           "reading_speed_words_per_minute": rng(b["assumptions"]["words_per_minute"]),
           "answer_options": OPTIONS["primary_response"],
           "versions": {OUT_REVIEWER: "for prospective reviewers; states no study question, hypothesis or result (criteria §10)",
                        OUT_STUDY: "for people who will not review charts; states the question and the computable-stage counts"}}
    json.dump(use, open(RES, "w"), indent=1)
    note = f"*Written by `scripts/run1110_reviewer_onepager.py` from the study's results files (`{RES}`). The hours are estimates from text length, not measured times.*"

    reviewer = [
        "# Chart review for a hepatic steatosis study: one page for prospective reviewers", "", note, "",
        "> **Not ready to send.** What reviewers are offered is still open (decision N-08 in `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`).", "",
        "## What the study is", "",
        "We are validating a computable phenotype for hepatic steatosis: a computer method that reads hospital records and says whether steatosis is documented. "
        "To know how well it works, clinicians need to read a sample of charts and give their own answer. That is the review. "
        f"The records are MIMIC-IV, de-identified records of {use['hospital_stays']:,} hospital stays at one Boston hospital.", "",
        "The page says no more than this about the study on purpose. Reviewers are asked to judge each chart on what it documents, without knowing what the study expects to find. "
        "Ask the study lead for the full description once your review is finished.", ""] + shared(use) + [
        "Contact: the study lead, through the repository this page is in.", ""]

    study = [
        "# The chart review, for people who will not review charts", "", note, "",
        "> **Do not give this page to a prospective reviewer.** It states the study question and a result. The review criteria (§10) say reviewers are told only that a method for finding hepatic steatosis is being validated. "
        "The page for reviewers is `docs/adjudication/reviewer_onepager.md`.", "",
        "## The question", "",
        "Fatty liver (hepatic steatosis; the disease is now called MASLD, formerly NAFLD) is often written in a hospital chart but left off the list of diagnosis codes. "
        "We want to know how often. That needs clinicians to read charts and say whether steatosis is documented, because a computer search of the text cannot settle it.", "",
        "## What the computer stage shows so far", "",
        f"- The data are MIMIC-IV: de-identified records of {use['hospital_stays']:,} hospital stays at one Boston hospital.",
        f"- {use['stays_with_code']:,} stays carry a fatty-liver diagnosis code.",
        f"- A fixed keyword search finds a statement of fatty liver in the notes of {use['stays_with_note_statement']:,} stays. {use['pct_of_those_without_code']}% of those have no code.",
        "- No clinician has checked any of this. The keyword search can be wrong in both directions. The review is what turns these counts into an estimate.", ""] + shared(use) + [
        "Contact: the study lead, through the repository this page is in.", ""]

    open(OUT_REVIEWER, "w").write("\n".join(reviewer))
    open(OUT_STUDY, "w").write("\n".join(study))
    for p, L in ((OUT_REVIEWER, reviewer), (OUT_STUDY, study)):
        print("wrote", p, "words:", sum(len(l.split()) for l in L))


if __name__ == "__main__":
    main()
