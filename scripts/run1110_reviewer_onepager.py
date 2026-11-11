#!/usr/bin/env python3
"""run_2026-11-10 Phase 6.1 — one page for prospective chart reviewers, written from results files.

Reads docs/run_2026-09-19/results/{integrity_gate,reviewer_brief,reviewer_assignment}.json and the form's
answer options (scripts/make_adjudication_template.py). Writes docs/adjudication/reviewer_onepager.md and
docs/run_2026-11-10/results/reviewer_onepager.json (the numbers it used). No number is typed here.
What reviewers are offered is not stated: that is decision N-08.
"""
import json, os, sys

sys.path.insert(0, os.getcwd())
from scripts.make_adjudication_template import OPTIONS

R19 = "docs/run_2026-09-19/results"
OUT = "docs/adjudication/reviewer_onepager.md"
RES = "docs/run_2026-11-10/results/reviewer_onepager.json"


def main():
    g = json.load(open(f"{R19}/integrity_gate.json"))["reproduced"]
    b = json.load(open(f"{R19}/reviewer_brief.json"))["estimate"]
    a = json.load(open(f"{R19}/reviewer_assignment.json"))
    rng = lambda v: f"{round(min(v))}–{round(max(v))}"
    cells = g["b"]
    use = {"script": "scripts/run1110_reviewer_onepager.py",
           "hospital_stays": g["pop_admissions"], "stays_with_code": g["code_positive"],
           "stays_with_note_statement": g["note_pos_primary"], "pct_of_those_without_code": g["recovery_share_pct"],
           "charts_in_sample": sum(g["alloc"].values()), "reviewers": a["n_reviewers"], "charts_read_by_both": a["double_review_total"],
           "charts_per_reviewer": b["charts_per_reviewer"], "practice_charts": b["training_charts"],
           "minutes_per_chart": rng(b["minutes_per_chart"]["full"]), "hours_main_set": rng(b["hours_per_reviewer_sample"]["full"]),
           "hours_practice_set": rng(b["hours_per_reviewer_training"]["full"]),
           "hours_main_set_focused_read": rng(b["hours_per_reviewer_sample"]["focused"]),
           "reading_speed_words_per_minute": rng(b["assumptions"]["words_per_minute"]),
           "answer_options": OPTIONS["primary_response"]}
    json.dump(use, open(RES, "w"), indent=1)
    opts = ", ".join(o.lower() for o in use["answer_options"])
    L = [
        "# Chart review for a fatty-liver documentation study: one page for prospective reviewers", "",
        f"*Written by `scripts/run1110_reviewer_onepager.py` from the study's results files (`{RES}`). The hours are estimates from text length, not measured times.*", "",
        "## The question", "",
        "Fatty liver (hepatic steatosis; the disease is now called MASLD, formerly NAFLD) is often written in a hospital chart but left off the list of diagnosis codes. "
        "We want to know how often. That needs clinicians to read charts and say whether steatosis is documented, because a computer search of the text cannot settle it.", "",
        "## What the computer stage shows so far", "",
        f"- The data are MIMIC-IV: de-identified records of {use['hospital_stays']:,} hospital stays at one Boston hospital.",
        f"- {use['stays_with_code']:,} stays carry a fatty-liver diagnosis code.",
        f"- A fixed keyword search finds a statement of fatty liver in the notes of {use['stays_with_note_statement']:,} stays. {use['pct_of_those_without_code']}% of those have no code.",
        "- No clinician has checked any of this. The keyword search can be wrong in both directions. Your review is what turns these counts into an estimate.", "",
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
        "- You will not see diagnosis codes, the keyword search result, any model output, or why a chart was sampled.",
        "- The two reviewers work independently.", "",
        "## What is already fixed", "",
        "- The keyword search, the sample of charts and its weights.",
        "- The predictions of every model the study will compare with your answers, including a locally run language model. All were recorded, with file hashes, before any chart review.",
        "- **Not yet fixed:** the review criteria. They are a draft with open clinical questions that clinicians need to settle before review starts.", "",
        "## What reviewers are offered", "",
        "To be completed by the study lead.", "",
        "Contact: the study lead, through the repository this page is in.", ""]
    open(OUT, "w").write("\n".join(L))
    words = sum(len(l.split()) for l in L)
    print("wrote", OUT, "words:", words)


if __name__ == "__main__":
    main()
