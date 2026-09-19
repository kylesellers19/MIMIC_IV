# Adjudication form — data dictionary

Produced by `scripts/run0919_phase6_docs.py`; column and option lists are imported from `scripts/make_adjudication_template.py` (the same constants that build the form); counts from `docs/run_2026-09-19/results/reviewer_assignment.json`. Template: `docs/adjudication/adjudication_template.xlsx` (blank; blinded IDs only). Criteria: `docs/adjudication_criteria.md` (Draft 1 — the option lists follow the draft and are regenerated if the clinician sign-off changes D1–D8).

## Workbook layout

- Sheet `sample`: one row per chart of the formal review, 400 rows (R0001–R0400 in master-key order in the template; in the reviewer's own shuffled order in the per-reviewer forms, 250 rows each).
- Sheet `training`: the 20-chart calibration round, T001–T020.
- Sheet `lists`: the dropdown options (do not edit). Sheet `README`: short instructions.
- The ID column is locked; every other cell is editable. Rows must not be added, deleted or reordered. No chart text may be pasted into the form.

## Columns (in order)

| column | type | allowed values | rule |
| --- | --- | --- | --- |
| `review_id` | blinded ID, pre-filled | R0001–R0400 or T001–T020 | do not edit |
| `primary_response` | dropdown | Definite / Probable / Possible / Absent / Insufficient information | criteria §2: evidence of hepatic steatosis during or before this admission. Definite + Probable collapse to positive in the primary analysis (D1) |
| `temporality` | dropdown | During this admission / Before this admission / Both / Not applicable | criteria §4; 'Not applicable' when the primary response is Absent or Insufficient information |
| `q6a_cardiometabolic` | dropdown | Yes / No / Insufficient / Not applicable | criteria §6a; asked only when Definite/Probable, else 'Not applicable' |
| `q6b_alcohol` | dropdown | (i) Below MetALD threshold / (ii) Within MetALD band (140-350 g/wk F, 210-420 g/wk M) / (iii) Above MetALD band / (iv) Not documented / insufficient / Not applicable | criteria §6b (g/week bands per Draft 1; D6 may replace them with a qualitative scale); asked only when Definite/Probable |
| `q6c_other_cause` | dropdown | Yes (specify) / No / Unclear / Not applicable | criteria §6c; asked only when Definite/Probable |
| `q6c_specify` | free text | — | required when q6c_other_cause is 'Yes (specify)' |
| `rationale` | free text | — | REQUIRED when primary_response is 'Possible' and whenever negation_override is 'Yes'; encouraged otherwise. Do not quote identifiers; brief paraphrase of the evidence is fine |
| `negation_override` | dropdown | Yes / No | criteria §5: 'Yes' when a newer explicit negative study was judged to override an older positive finding |
| `minutes_spent` | whole number ≥ 0 | — | minutes on the chart including form entry (D7) |
| `reviewer_initials` | free text | — | the reviewer's initials on every row; the estimator uses it to pair the double-reviewed charts |

## How the completed forms are consumed

- Both reviewer forms are passed to `scripts/aim1a_estimator.py` (`--adjudication form_reviewer1.xlsx --adjudication form_reviewer2.xlsx`). The script joins `review_id` to the untracked master key to obtain the cell and weight; reviewers never see either.
- A chart with one reviewer row is final. A double-reviewed chart whose two rows agree on the collapsed binary outcome is final (the less certain of two positive levels is kept for the 4-level tables). A binary disagreement is unresolved until a row for that ID is supplied in a resolution file (`--resolution`, same columns; the third-adjudicator or consensus outcome per D8); unresolved charts are excluded and counted.
- Kappa is computed on the pre-consensus reviewer rows of the double-reviewed charts; the resolution file never feeds kappa.
- 'Insufficient information' is reported both ways (excluded; counted negative). Blank or invalid `primary_response` cells are treated as not adjudicated and counted.
- The training sheet is never passed to the estimator; it is discussed by the reviewers and the criteria are revised once (criteria §9).
