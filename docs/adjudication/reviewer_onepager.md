# Chart review for a fatty-liver documentation study: one page for prospective reviewers

*Written by `scripts/run1110_reviewer_onepager.py` from the study's results files (`docs/run_2026-11-10/results/reviewer_onepager.json`). The hours are estimates from text length, not measured times.*

## The question

Fatty liver (hepatic steatosis; the disease is now called MASLD, formerly NAFLD) is often written in a hospital chart but left off the list of diagnosis codes. We want to know how often. That needs clinicians to read charts and say whether steatosis is documented, because a computer search of the text cannot settle it.

## What the computer stage shows so far

- The data are MIMIC-IV: de-identified records of 373,992 hospital stays at one Boston hospital.
- 5,740 stays carry a fatty-liver diagnosis code.
- A fixed keyword search finds a statement of fatty liver in the notes of 27,826 stays. 81.9% of those have no code.
- No clinician has checked any of this. The keyword search can be wrong in both directions. Your review is what turns these counts into an estimate.

## What a reviewer does

- **Reads charts.** 400 charts were sampled. Each of 2 reviewers reads 250; 100 charts are read by both, to measure agreement.
- **A chart is one text file:** the discharge summary, the radiology reports, a short table of laboratory values, vital signs and medication orders.
- **Answers one main question per chart:** is hepatic steatosis documented? The choices are definite, probable, possible, absent, insufficient information.
- **Then a few short follow-ups:** whether it is current or historical, cardiometabolic risk factors, alcohol, any other stated cause, and a one-line reason.
- **Practice first:** 20 practice charts. The criteria can be revised once after them; then they are frozen and the main set starts.

## Time

- About 18–21 minutes per chart, from the length of the text at 200–250 words per minute plus time to fill the form.
- Main set: about 74–87 hours per reviewer. Practice set: about 6–7 hours.
- If only the discharge summary and liver imaging reports are read closely: about 58–67 hours for the main set.
- The study team is timing a small pilot set to replace these estimates with measured minutes.

## Access you need

- Your own PhysioNet credentialed access to MIMIC-IV and MIMIC-IV-Note, with the data use agreement signed in your own name.
- The study cannot send charts to anyone without it. Chart text may not be sent to online services such as chatbots; that is PhysioNet's rule.

## Blinding

- You will not see diagnosis codes, the keyword search result, any model output, or why a chart was sampled.
- The two reviewers work independently.

## What is already fixed

- The keyword search, the sample of charts and its weights.
- The predictions of every model the study will compare with your answers, including a locally run language model. All were recorded, with file hashes, before any chart review.
- **Not yet fixed:** the review criteria. They are a draft with open clinical questions that clinicians need to settle before review starts.

## What reviewers are offered

To be completed by the study lead.

Contact: the study lead, through the repository this page is in.
