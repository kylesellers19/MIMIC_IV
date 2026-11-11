# Chart review for a hepatic steatosis study: one page for prospective reviewers

*Written by `scripts/run1110_reviewer_onepager.py` from the study's results files (`docs/run_2026-11-10/results/reviewer_onepager.json`). The hours are estimates from text length, not measured times.*

> **Not ready to send.** What reviewers are offered is still open (decision N-08 in `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`).

## What the study is

We are validating a computable phenotype for hepatic steatosis: a computer method that reads hospital records and says whether steatosis is documented. To know how well it works, clinicians need to read a sample of charts and give their own answer. That is the review. The records are MIMIC-IV, de-identified records of 373,992 hospital stays at one Boston hospital.

The page says no more than this about the study on purpose. Reviewers are asked to judge each chart on what it documents, without knowing what the study expects to find. Ask the study lead for the full description once your review is finished.

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

- You will not see diagnosis codes, the output of any computer method, or why a chart was sampled.
- The two reviewers work independently.

## What is already fixed

- The sample of charts.
- The output of every computer method that will be compared with your answers. All of it was recorded, with file hashes, before any chart review.
- **Not yet fixed:** the review criteria. They are a draft with open clinical questions that clinicians need to settle before review starts.

## What reviewers are offered

To be completed by the study lead.

Contact: the study lead, through the repository this page is in.
