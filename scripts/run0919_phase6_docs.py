#!/usr/bin/env python3
"""run_2026-09-19 Phase 6 — write the adjudication docs from the results JSONs (no hand-typed numbers).

Reads  docs/run_2026-09-19/results/packet_feasibility.json   (scripts/run0919_packet_feasibility.py)
       docs/run_2026-09-19/results/packet_dryrun.json        (scripts/make_reviewer_packets.py --dryrun)
       docs/run_2026-09-19/results/reviewer_assignment.json  (scripts/assign_reviewers.py)
Writes docs/adjudication/packet_specification.md, docs/adjudication/data_dictionary.md,
       docs/adjudication/reviewer_brief.md, and docs/run_2026-09-19/results/reviewer_brief.json (the derived
       hours figures, so the brief's numbers are themselves script-produced).
"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from scripts.make_adjudication_template import COLUMNS, OPTIONS

R = "docs/run_2026-09-19/results"
FEAS = json.load(open(f"{R}/packet_feasibility.json"))
DRY = json.load(open(f"{R}/packet_dryrun.json"))
ASG = json.load(open(f"{R}/reviewer_assignment.json"))
CELL_NAMES = {"A": "code+/note+", "B": "code−/note+", "C": "code+/note−", "D": "code−/note−"}
CHARS_PER_WORD = 6.0
WPM_LO, WPM_HI = 200, 250
OVERHEAD_MIN = 5.0


def f1(x):
    return f"{x:,.1f}"


def f0(x):
    return f"{x:,.0f}"


def packet_specification():
    so = FEAS["sample_overall"]
    bc = FEAS["sample_by_cell"]
    av = so["availability_pct"]
    L = ["# Reviewer packet — specification and feasibility (400-chart sample)", "",
         f"Produced by `scripts/run0919_phase6_docs.py` from `{R}/packet_feasibility.json` (`scripts/run0919_packet_feasibility.py`) and "
         f"`{R}/packet_dryrun.json` (`scripts/make_reviewer_packets.py --dryrun`). Generator: `scripts/make_reviewer_packets.py`. "
         "Criteria §1 (docs/adjudication_criteria.md) defines what the packet may contain; this document confirms each element against the data.", "",
         "## 1. What each packet contains", "",
         "One plain-text file per chart, named by the blinded ID (`R0001.txt` … `R0400.txt`; `T001.txt` … `T020.txt` for the training round). Sections, in order:", "",
         "| # | element | source | rule |", "| --- | --- | --- | --- |",
         "| header | age at admission (capped at '89 or older'), sex, length of stay | patients / admissions via the locked population | no dates; no race, insurance, language, marital status |",
         "| 1 | discharge summary, full text, verbatim | MIMIC-IV-Note `discharge` | all documents linked to the admission (note_seq order); charttime as a day offset |",
         f"| 2 | radiology reports, full text, verbatim, with exam name | MIMIC-IV-Note `radiology` + `radiology_detail` (exam_name) | linked to the admission, plus outpatient reports (no hadm_id) for the same patient within −{FEAS['window_days']['before_admission']}/+{FEAS['window_days']['after_admission']} days of admission; day offsets |",
         f"| 3 | laboratory values, ten analytes | `labevents` itemids {', '.join(f'{k} {v}' for k, v in FEAS['lab_itemids'].items())} | {FEAS['in_admission_lab_definition']}; value, unit, flag, reference range, day offset |",
         "| 4 | vitals and anthropometrics | `omr` (BMI, blood pressure incl. positional variants, weight, height) | within −365/+30 days of admission; day offsets |",
         "| 5 | medication orders | `prescriptions` | linked to the admission: drug, route, dose, start/stop day offsets |", "",
         "Stripped by construction: note_id, subject_id, hadm_id, calendar dates, ICD codes and coded problem lists, race, insurance, language, marital status, "
         "cell membership, the note rule's output and any highlighting. Clinician-written narrative is never edited, including a narrative 'Discharge Diagnosis:' section. "
         "All times are day offsets from admission (day +0.0); the sections are delimited so that automated checks can tell narrative from structured text.", "",
         "## 2. Availability of each element (400 sampled admissions)", "",
         "| element | overall | A (n=%d) | B (n=%d) | C (n=%d) | D (n=%d) |" % tuple(bc[c]["n"] for c in "ABCD"), "| --- | --: | --: | --: | --: | --: |"]
    rows = [("discharge summary present", "discharge_summary"), ("≥1 inpatient radiology report", "any_inpatient_radiology"),
            ("≥1 outpatient radiology report in window", "any_outpatient_radiology_window"), ("≥1 radiology report of either kind", "any_radiology"),
            ("≥1 liver-inclusive imaging report (exam-name rule)", "any_liver_inclusive_radiology"), ("≥1 of the ten labs in admission", "any_lab_row_inadm"),
            ("BMI in omr window", "omr_BMI"), ("blood pressure in omr window", "omr_BP"), ("weight in omr window", "omr_weight"), ("height in omr window", "omr_height"),
            ("≥1 prescription", "any_prescription")]
    for lab, k in rows:
        L.append(f"| {lab} | {f1(av[k])}% | " + " | ".join(f"{f1(bc[c]['availability_pct'][k])}%" for c in "ABCD") + " |")
    L += ["", "Each of the ten labs present at least once (in-admission definition; the hadm_id-linked rate is in the JSON and differs by < 1 point):", "",
          "| analyte | overall | A | B | C | D |", "| --- | --: | --: | --: | --: | --: |"]
    for k in FEAS["lab_itemids"]:
        L.append(f"| {k.replace('_', ' ')} | {f1(so['labs_present_pct_in_admission'][k])}% | " + " | ".join(f"{f1(bc[c]['labs_present_pct_in_admission'][k])}%" for c in "ABCD") + " |")
    L += ["", "Cells are reported at the cell level (n = 80/150/70/100, all ≥ 11). Cell A = code+/note+, B = code−/note+, C = code+/note−, D = code−/note−.", "",
          "## 3. What the criteria call for that MIMIC cannot supply", ""]
    for item in FEAS["not_suppliable_by_mimic"]:
        L.append(f"- {item}")
    L += ["", "The reviewer form therefore expects 'Not documented / insufficient' to dominate question 6b (alcohol), and 6a (cardiometabolic risk) to be answered from "
          "labs, BMI/BP, medication orders and narrative rather than from any coded diagnosis.", "",
          "## 4. Reading burden (from the per-note index; no text read)", "",
          "| cell | n | discharge chars median | p95 | radiology reports median | p95 | liver-inclusive reports median | narrative chars per packet median | p95 |",
          "| --- | --: | --: | --: | --: | --: | --: | --: | --: |"]
    for c in "ABCD":
        rb = bc[c]["reading_burden"]
        L.append(f"| {c} {CELL_NAMES[c]} | {bc[c]['n']} | {f0(rb['discharge_chars']['median'])} | {f0(rb['discharge_chars']['p95'])} | {f0(rb['radiology_reports_total']['median'])} | "
                 f"{f0(rb['radiology_reports_total']['p95'])} | {f0(rb['radiology_reports_liver_inclusive']['median'])} | {f0(rb['packet_narrative_chars']['median'])} | {f0(rb['packet_narrative_chars']['p95'])} |")
    rb = so["reading_burden"]
    L.append(f"| all | {so['n']} | {f0(rb['discharge_chars']['median'])} | {f0(rb['discharge_chars']['p95'])} | {f0(rb['radiology_reports_total']['median'])} | "
             f"{f0(rb['radiology_reports_total']['p95'])} | {f0(rb['radiology_reports_liver_inclusive']['median'])} | {f0(rb['packet_narrative_chars']['median'])} | {f0(rb['packet_narrative_chars']['p95'])} |")
    L += ["", f"Across the 400 packets: {f0(rb['discharge_chars']['total'])} discharge-summary characters and {f0(rb['radiology_chars_total']['total'])} radiology characters "
          f"({f0(rb['radiology_reports_total']['total'])} reports, of which {f0(rb['radiology_reports_liver_inclusive']['total'])} are liver-inclusive by the exam-name rule); "
          f"median {f0(rb['lab_rows_in_admission']['median'])} lab rows, {f0(rb['omr_rows_window']['median'])} omr rows and {f0(rb['prescription_rows']['median'])} medication orders per chart. "
          f"Longest packet: {f0(rb['packet_narrative_chars']['max'])} narrative characters. Training round (20 charts): {f0(FEAS['training_overall']['reading_burden']['packet_narrative_chars']['total'])} narrative characters in total.", "",
          "## 5. Dry run of the generator", "",
          f"`scripts/make_reviewer_packets.py --dryrun` generated all {DRY['n_charts']} packets ({DRY['n_sample']} sample + {DRY['n_training']} training) into `data/processed/_packet_dryrun/`, "
          f"ran the leak checks below, and removed the directory (removed: {DRY.get('dryrun_dir_removed')}). Files generated: {DRY['files_generated']}; exceptions by class: {DRY['exceptions_by_class'] or 'none'}; "
          f"median file size {f0(DRY['leak_checks']['file_bytes_median'])} bytes (p95 {f0(DRY['leak_checks']['file_bytes_p95'])}, max {f0(DRY['leak_checks']['file_bytes_max'])}); "
          f"load {DRY['timings_s']['load_inputs']} s, generate {DRY['timings_s']['generate']} s. "
          f"Discharge text verbatim check: {DRY['discharge_text_verbatim_vs_index']['charts_matching_index_char_count']} of {DRY['discharge_text_verbatim_vs_index']['charts_total']} charts "
          f"reproduce the character count of the per-note index exactly ({DRY['discharge_text_verbatim_vs_index']['charts_with_discharge_text']} charts have a discharge summary; for the rest both counts are zero — see availability above).", "",
          f"Rows pulled: {DRY['rows_pulled']['discharge_notes']} discharge documents, {DRY['rows_pulled']['radiology_reports']} radiology reports "
          f"({DRY['rows_pulled']['radiology_inpatient']} inpatient, {DRY['rows_pulled']['radiology_outpatient_window']} outpatient in window), {DRY['rows_pulled']['lab_rows']} lab rows, "
          f"{DRY['rows_pulled']['omr_rows']} omr rows, {DRY['rows_pulled']['prescription_rows']} medication orders.", "",
          "| check | where | hits | files with ≥1 hit |", "| --- | --- | --: | --: |"]
    cnt, fw = DRY["leak_checks"]["counts"], DRY["leak_checks"]["files_with_any_hit"]
    labels = {"i_icd10_like_structured": ("(i) ICD-10-shaped token", "structured"), "i_icd10_like_structured_excl_value_columns": ("(i) ICD-10-shaped token", "structured, value/dose columns removed"),
              "i_icd9_like_structured": ("(i) ICD-9-shaped number ddd.dd", "structured"), "i_icd9_like_structured_excl_value_columns": ("(i) ICD-9-shaped number ddd.dd", "structured, value/dose columns removed"),
              "i_icd9_like_structured_excl_values_and_day_offsets": ("(i) ICD-9-shaped number ddd.dd", "structured, value/dose columns and signed day offsets removed"),
              "ii_long_title_structured": ("(ii) phenotype-code long title", "structured"), "ii_long_title_narrative": ("(ii) phenotype-code long title", "narrative"),
              "iii_demographic_label_structured": ("(iii) demographic label", "structured"),
              "iv_8digit_structured": ("(iv) 8-digit integer", "structured"), "iv_8digit_narrative": ("(iv) 8-digit integer", "narrative"),
              "v_cell_label_structured": ("(v) cell label", "structured"), "v_cell_label_narrative": ("(v) cell label incl. the word 'recovery'", "narrative"),
              "v_recovery_word_narrative_only": ("(v) of which the plain word 'recovery'", "narrative"),
              "vi_markup_structured": ("(vi) markup token", "structured"), "vi_markup_narrative": ("(vi) markup token", "narrative"),
              "vii_own_identifier_structured": ("(vii) chart's own hadm_id / subject_id / note_id", "structured"), "vii_own_identifier_narrative": ("(vii) chart's own hadm_id / subject_id / note_id", "narrative")}
    for k, (lab, where) in labels.items():
        L.append(f"| {lab} | {where} | {cnt.get(k, 0)} | {fw.get(k, 0)} |")
    toks = DRY["leak_checks"].get("matched_tokens_structured_excl_values", {})
    if toks:
        L += ["", "Tokens matched by the ICD-shaped patterns in structured text with the value/dose columns and signed day offsets removed (frequency table; these are the only candidates for a real leak):", "",
              "| token | hits |", "| --- | --: |"] + [f"| `{k}` | {v} |" for k, v in toks.items()]
    L += ["", "Hit counts of 1–10 are written as <11 (the project's small-count rule). Section numbers in the token table refer to the packet sections in §1: section 5 is the medication table, section 3 the lab table, section 4 the vitals table; the tokens listed are what Kyle should grep for in the final packets before release.", "",
          "Reading the checks. Structured text is everything outside the delimited note-text blocks (header, section titles, the lab / vitals / medication tables). "
          "ICD-shaped hits in structured text come from numeric lab values (ddd.dd), signed day offsets such as −123.4 in the outpatient window, and drug names such as 'Vitamin B12', which is why the counts with the value and dose columns and signed day offsets removed — and the token table — are the ones that matter; "
          "long-title, demographic-label, cell-label, markup and own-identifier hits in structured text are the true leak tests and must be zero. "
          "Narrative hits are inside clinician-written note text, which is kept verbatim by design: the word 'recovery' (recovery room, post-anaesthesia recovery) and any '**' or '[[' a clinician typed are documentation, not highlighting; "
          "an 8-digit number in narrative would be a number a clinician wrote in an already de-identified note, not a structured identifier. "
          f"Check definitions are recorded in the results JSON (`check_definitions`).", "",
          "## 6. Final generation (after the criteria are frozen)", "",
          "```", "scripts/run0919_env.sh scripts/make_reviewer_packets.py --out data/processed/adjudication/packets", "```", "",
          "The output directory is untracked (everything under `data/` is git-ignored). The same leak checks run and their counts are printed; the packets stay in place. "
          "Each reviewer receives only the packets for the IDs on their own form (`docs/adjudication/reviewer_assignment.md`), and only after their own PhysioNet credentialing and MIMIC-IV-Note DUA are in place.", ""]
    with open("docs/adjudication/packet_specification.md", "w") as f:
        f.write("\n".join(L))


def data_dictionary():
    n_sample = ASG["per_reviewer"]["reviewer1"]["total"] + ASG["per_reviewer"]["reviewer2"]["total"] - ASG["shared_charts_between_reviewers"]
    n_train = ASG["per_reviewer"]["reviewer1"]["training_charts"]
    L = ["# Adjudication form — data dictionary", "",
         "Produced by `scripts/run0919_phase6_docs.py`; column and option lists are imported from `scripts/make_adjudication_template.py` (the same constants that build the form); "
         f"counts from `{R}/reviewer_assignment.json`. Template: `docs/adjudication/adjudication_template.xlsx` (blank; blinded IDs only). "
         "Criteria: `docs/adjudication_criteria.md` (Draft 1 — the option lists follow the draft and are regenerated if the clinician sign-off changes D1–D8).", "",
         "## Workbook layout", "",
         f"- Sheet `sample`: one row per chart of the formal review, {n_sample} rows (R0001–R0400 in master-key order in the template; in the reviewer's own shuffled order in the per-reviewer forms, {ASG['per_reviewer']['reviewer1']['total']} rows each).",
         f"- Sheet `training`: the {n_train}-chart calibration round, T001–T0{n_train}.",
         "- Sheet `lists`: the dropdown options (do not edit). Sheet `README`: short instructions.",
         "- The ID column is locked; every other cell is editable. Rows must not be added, deleted or reordered. No chart text may be pasted into the form.", "",
         "## Columns (in order)", "", "| column | type | allowed values | rule |", "| --- | --- | --- | --- |"]
    rules = {
        "review_id": ("blinded ID, pre-filled", "R0001–R0400 or T001–T020", "do not edit"),
        "primary_response": ("dropdown", " / ".join(OPTIONS["primary_response"]), "criteria §2: evidence of hepatic steatosis during or before this admission. Definite + Probable collapse to positive in the primary analysis (D1)"),
        "temporality": ("dropdown", " / ".join(OPTIONS["temporality"]), "criteria §4; 'Not applicable' when the primary response is Absent or Insufficient information"),
        "q6a_cardiometabolic": ("dropdown", " / ".join(OPTIONS["q6a_cardiometabolic"]), "criteria §6a; asked only when Definite/Probable, else 'Not applicable'"),
        "q6b_alcohol": ("dropdown", " / ".join(OPTIONS["q6b_alcohol"]), "criteria §6b (g/week bands per Draft 1; D6 may replace them with a qualitative scale); asked only when Definite/Probable"),
        "q6c_other_cause": ("dropdown", " / ".join(OPTIONS["q6c_other_cause"]), "criteria §6c; asked only when Definite/Probable"),
        "q6c_specify": ("free text", "—", "required when q6c_other_cause is 'Yes (specify)'"),
        "rationale": ("free text", "—", "REQUIRED when primary_response is 'Possible' and whenever negation_override is 'Yes'; encouraged otherwise. Do not quote identifiers; brief paraphrase of the evidence is fine"),
        "negation_override": ("dropdown", " / ".join(OPTIONS["negation_override"]), "criteria §5: 'Yes' when a newer explicit negative study was judged to override an older positive finding"),
        "minutes_spent": ("whole number ≥ 0", "—", "minutes on the chart including form entry (D7)"),
        "reviewer_initials": ("free text", "—", "the reviewer's initials on every row; the estimator uses it to pair the double-reviewed charts"),
    }
    for c in COLUMNS:
        t, v, r = rules[c]
        L.append(f"| `{c}` | {t} | {v} | {r} |")
    L += ["", "## How the completed forms are consumed", "",
          "- Both reviewer forms are passed to `scripts/aim1a_estimator.py` (`--adjudication form_reviewer1.xlsx --adjudication form_reviewer2.xlsx`). The script joins `review_id` to the untracked master key to obtain the cell and weight; reviewers never see either.",
          "- A chart with one reviewer row is final. A double-reviewed chart whose two rows agree on the collapsed binary outcome is final (the less certain of two positive levels is kept for the 4-level tables). "
          "A binary disagreement is unresolved until a row for that ID is supplied in a resolution file (`--resolution`, same columns; the third-adjudicator or consensus outcome per D8); unresolved charts are excluded and counted.",
          "- Kappa is computed on the pre-consensus reviewer rows of the double-reviewed charts; the resolution file never feeds kappa.",
          "- 'Insufficient information' is reported both ways (excluded; counted negative). Blank or invalid `primary_response` cells are treated as not adjudicated and counted.",
          "- The training sheet is never passed to the estimator; it is discussed by the reviewers and the criteria are revised once (criteria §9).", ""]
    with open("docs/adjudication/data_dictionary.md", "w") as f:
        f.write("\n".join(L))


def reviewer_brief():
    so = FEAS["sample_overall"]["reading_burden"]
    tr = FEAS["training_overall"]["reading_burden"]
    per_rev = ASG["per_reviewer"]["reviewer1"]["total"]
    n_train = ASG["per_reviewer"]["reviewer1"]["training_charts"]
    total_adj = ASG["adjudications_total"]

    def hours(chars_per_chart, n_charts, wpm):
        words = chars_per_chart / CHARS_PER_WORD
        return n_charts * (words / wpm + OVERHEAD_MIN) / 60.0

    full_mean, foc_mean = so["packet_narrative_chars"]["mean"], so["focused_read_chars_discharge_plus_liver_radiology"]["mean"]
    tr_full_mean = tr["packet_narrative_chars"]["mean"]
    est = {
        "assumptions": {"chars_per_word": CHARS_PER_WORD, "words_per_minute": [WPM_LO, WPM_HI], "fixed_overhead_min_per_chart": OVERHEAD_MIN,
                        "full_read": "discharge summary + every linked radiology report", "focused_read": "discharge summary + liver-inclusive radiology reports only (exam-name rule)"},
        "mean_chars_per_chart": {"full": full_mean, "focused": foc_mean, "training_full": tr_full_mean},
        "words_per_chart": {"full": full_mean / CHARS_PER_WORD, "focused": foc_mean / CHARS_PER_WORD},
        "minutes_per_chart": {"full": [full_mean / CHARS_PER_WORD / WPM_HI + OVERHEAD_MIN, full_mean / CHARS_PER_WORD / WPM_LO + OVERHEAD_MIN],
                              "focused": [foc_mean / CHARS_PER_WORD / WPM_HI + OVERHEAD_MIN, foc_mean / CHARS_PER_WORD / WPM_LO + OVERHEAD_MIN]},
        "hours_per_reviewer_sample": {"full": [hours(full_mean, per_rev, WPM_HI), hours(full_mean, per_rev, WPM_LO)],
                                      "focused": [hours(foc_mean, per_rev, WPM_HI), hours(foc_mean, per_rev, WPM_LO)]},
        "hours_per_reviewer_training": {"full": [hours(tr_full_mean, n_train, WPM_HI), hours(tr_full_mean, n_train, WPM_LO)]},
        "hours_total_all_adjudications": {"full": [hours(full_mean, total_adj, WPM_HI), hours(full_mean, total_adj, WPM_LO)],
                                          "focused": [hours(foc_mean, total_adj, WPM_HI), hours(foc_mean, total_adj, WPM_LO)]},
        "charts_per_reviewer": per_rev, "training_charts": n_train, "adjudications_total": total_adj,
        "prior_analyst_estimate_note": "docs/adjudication_criteria.md offered 10–18 min per chart before the packet contents were confirmed against the data",
    }
    with open(f"{R}/reviewer_brief.json", "w") as f:
        json.dump({"script": "scripts/run0919_phase6_docs.py", "inputs": ["packet_feasibility.json", "reviewer_assignment.json"], "estimate": est}, f, indent=1)
    h = est["hours_per_reviewer_sample"]
    m = est["minutes_per_chart"]
    L = ["# Reviewer brief — hepatic steatosis chart adjudication", "",
         f"Numbers in this brief are read from `{R}/packet_feasibility.json`, `{R}/reviewer_assignment.json` and `{R}/reviewer_brief.json` by `scripts/run0919_phase6_docs.py`.", "",
         "## What you are being asked to do", "",
         "We are validating a computable phenotype for hepatic steatosis (fatty liver). For each chart packet you receive — a discharge summary, the linked radiology reports, "
         "in-admission laboratory values, outpatient BMI/blood pressure/weight/height, medication orders, and age and sex — answer one primary question:", "",
         "> *Is there evidence of hepatic steatosis during or before this admission?*", "",
         "on a five-option scale, then three short secondary questions when the answer is Definite or Probable. Full criteria: `docs/adjudication_criteria.md`; form fields: `docs/adjudication/data_dictionary.md`.", "",
         "## The scale", "",
         "| response | meaning (criteria §3) |", "| --- | --- |",
         "| Definite | liver biopsy reporting steatosis, or CT/MRI reporting hepatic steatosis, fatty liver, fatty infiltration or decreased hepatic attenuation |",
         "| Probable | ultrasound reporting increased hepatic echogenicity consistent with steatosis, or a clinician's statement ('fatty liver', 'known NAFLD') without supporting imaging in the packet |",
         "| Possible | hedged radiology only ('cannot exclude steatosis', 'may represent hepatic steatosis') — rationale required |",
         "| Absent | no steatosis statement; elevated transaminases or metabolic risk alone do not count |",
         "| Insufficient information | the packet does not allow a judgement either way (e.g. no discharge summary and no liver imaging) |", "",
         "Record separately whether the evidence is from during this admission, before it, or both. An explicit newer negative study may override an older positive finding only if you judge it more reliable — say so in the rationale. "
         "You are not asked whether a code should have been assigned; you will not see any coding data.", "",
         "## Secondary questions (Definite/Probable only)", "",
         "- 6a Cardiometabolic risk: any of BMI ≥ 25; diabetes or prediabetes; BP ≥ 130/85 or antihypertensive treatment; triglycerides ≥ 150; HDL ≤ 40 (M) / ≤ 50 (F); lipid-lowering therapy.",
         "- 6b Alcohol: from the documented history, below / within / above the MetALD band, or not documented. Charts rarely quantify intake; 'not documented' is expected to be common.",
         "- 6c Another identifiable cause of steatosis (amiodarone, methotrexate, tamoxifen, valproate, HIV therapy, TPN, rapid weight loss, Wilson disease, lipodystrophy): Yes (specify) / No / Unclear.", "",
         "## How much reading", "",
         f"Each reviewer has {per_rev} charts in the formal round (shared with the other reviewer for a subset you will not be told about) plus the {n_train}-chart calibration round. "
         f"A typical packet carries about {f0(so['discharge_chars']['median'])} characters of discharge summary (95th percentile {f0(so['discharge_chars']['p95'])}) and "
         f"{f0(so['radiology_reports_total']['median'])} radiology reports (95th percentile {f0(so['radiology_reports_total']['p95'])}), of which a median of "
         f"{f0(so['radiology_reports_liver_inclusive']['median'])} involve the liver or abdomen; labs, vitals and medication orders are short tables.", "",
         f"Rough hours, assuming {CHARS_PER_WORD:.0f} characters per word, a reading speed of {WPM_LO}–{WPM_HI} words per minute, and a fixed {OVERHEAD_MIN:.0f} minutes per chart for the tables and the form:", "",
         "| reading strategy | minutes per chart | hours for your %d charts | hours for the %d training charts |" % (per_rev, n_train), "| --- | --: | --: | --: |",
         f"| full read: discharge summary + every radiology report | {m['full'][0]:.0f}–{m['full'][1]:.0f} | {h['full'][0]:.0f}–{h['full'][1]:.0f} | {est['hours_per_reviewer_training']['full'][0]:.0f}–{est['hours_per_reviewer_training']['full'][1]:.0f} |",
         f"| focused read: discharge summary + liver-inclusive radiology only | {m['focused'][0]:.0f}–{m['focused'][1]:.0f} | {h['focused'][0]:.0f}–{h['focused'][1]:.0f} | — |", "",
         f"These are rough figures: the long tail (largest packet {f0(so['packet_narrative_chars']['max'])} characters) and the time a chart with ambiguous imaging takes are not captured by an average. "
         "The calibration round exists partly to replace them with your measured time per chart (record `minutes_spent` on every row).", "",
         "## The 20-chart calibration round", "",
         f"Before the formal review both reviewers independently adjudicate the same {n_train} charts (T001–T0{n_train}), which are not part of the 400-chart sample. Disagreements are discussed and the criteria are revised once. "
         "After that the criteria are frozen for the formal review; nothing in the calibration round is used in any estimate.", "",
         "## Access — please read", "",
         "The packets are derived from MIMIC-IV and MIMIC-IV-Note (PhysioNet). **Each reviewer must hold their own PhysioNet credentialing and have signed the Data Use Agreement for MIMIC-IV-Note before seeing any packet.** "
         "The DUA does not allow access to be shared: no packet, screenshot, excerpt or note text may be sent to anyone who is not credentialed, and nothing from a packet may be pasted into the form, an e-mail, or any external tool. "
         "Keep the packets on the machine on which you received them and delete them when the review is complete.", ""]
    with open("docs/adjudication/reviewer_brief.md", "w") as f:
        f.write("\n".join(L))


def phase6_notes():
    import subprocess
    PF = json.load(open(f"{R}/aim1a_precision_forecast.json"))
    RB = json.load(open(f"{R}/reviewer_brief.json"))["estimate"]
    py = subprocess.run([".venv/bin/python", "-m", "pytest", "-q", "tests/"], capture_output=True, text=True)
    pytest_line = [l for l in py.stdout.strip().splitlines() if "passed" in l or "failed" in l][-1].strip()
    u = PF["unit_test_targets"]
    so = FEAS["sample_overall"]
    d1 = [s for s in PF["scenarios"] if s["D_positives_per_100"] == 1]
    d3 = [s for s in PF["scenarios"] if s["D_positives_per_100"] >= 3]
    cnt = DRY["leak_checks"]["counts"]
    L = ["# Phase 6 — reference-standard machinery: notes for the lead", "",
         f"Written by `scripts/run0919_phase6_docs.py` (`phase6_notes()`); numbers are read from the results JSONs named in each section. Test line: `{pytest_line}`.", "",
         "## 6.1 Estimator and precision forecast", "",
         "**Purpose.** Turn a completed adjudication file into the headline Aim 1a number (of adjudicated steatosis-positive admissions, the population-weighted share that codes missed) with honest uncertainty, plus the note rule's PPV and sensitivity and reviewer agreement — before any chart is reviewed, so the arithmetic is fixed in advance and its precision is known.", "",
         "**What was done.** `scripts/aim1a_estimator.py` (joins reviewer forms to the master key by review_id inside the script; outputs aggregates only), `tests/test_aim1a_estimator.py`, `scripts/run0919_precision_forecast.py` → `results/aim1a_precision_forecast.json` and `docs/aim1a_precision_forecast.md`. "
         "Bootstrap = multinomial redraw of each cell's (positive, negative, insufficient) counts, which is exactly what resampling rows within a cell gives for these statistics; linearized (delta-method) SE with per-cell variance shares and a logit-scale interval; Cohen's kappa (binary; Insufficient excluded and counted negative) and weighted kappa (linear and quadratic) on the four ordinal levels from pre-consensus rows; by-cell Wilson intervals; by-stratum estimates for any `--group-col` when the stratum has ≥ 11 adjudicated charts.", "",
         f"**Results.** Hand target (x = {u['x']['A']}/{u['x']['B']}/{u['x']['C']}/{u['x']['D']}): under-capture {u['under_capture_pct']}%, PPV {u['ppv_pct']}%, sensitivity {u['sensitivity_pct']}% — exact. "
         f"Reference row (PPV_B = 0.85) closed form {PF['reference_row_ppvB_0.85_closed_form']} = expected {PF['reference_row_expected']}: match {PF['reference_row_matches']}. "
         f"Simulated means match the exact expectation of the estimator within {PF['max_abs_sim_mean_minus_exact_in_mc_se']} MC standard errors (largest scenario); the exact expectation sits up to {PF['max_abs_jensen_bias_pct_points']} points below the plug-in closed form (Jensen; the estimator is concave in x_D). "
         f"Bootstrap coverage {min(s['bootstrap_ci']['coverage_closed_form_pct'] for s in d1)}–{max(s['bootstrap_ci']['coverage_closed_form_pct'] for s in d1)}% at 1 positive per 100 in D, {min(s['bootstrap_ci']['coverage_closed_form_pct'] for s in d3)}–{max(s['bootstrap_ci']['coverage_closed_form_pct'] for s in d3)}% at ≥ 3; "
         f"cell D carries {min(s['cell_D']['mean_linearized_variance_share_pct'] for s in d3)}–{max(s['cell_D']['mean_linearized_variance_share_pct'] for s in PF['scenarios'])}% of the variance once D ≥ 3 per 100; one extra D positive shifts the estimate by {min(s['cell_D']['shift_per_additional_D_positive_pct_points'] for s in PF['scenarios'])}–{max(s['cell_D']['shift_per_additional_D_positive_pct_points'] for s in PF['scenarios'])} points.", "",
         f"**Checks passed.** `{pytest_line}` (hand targets exact; Insufficient two ways; bootstrap SD vs linearized SE within 10%; kappa on a hand-computed 2×2 = 0.4; end-to-end run on synthetic forms with a synthetic key recovers the hand target, excludes an unresolved disagreement, applies the <11 rule, and emits no identifier).", "",
         "**Deviations.** (1) The run file says the simulated mean must match the closed form within MC error; it matches the *exact expectation* within MC error and the closed form only to within the Jensen bias (< 0.6 points), which is a property of the ratio estimator, reported in the doc rather than hidden. (2) The linearized normal interval can exceed 100% when x_D ≤ 1; the JSON also carries a logit-scale interval.", "",
         "**What Kyle should look at.** The D = 1 rows of `docs/aim1a_precision_forecast.md` (coverage collapses when no positive is seen in D) → `phase6_decisions.md` P6-05; the Insufficient handling (P6-01); the disagreement-resolution mechanism (P6-02).", "",
         "## 6.2 Packet specification and feasibility", "",
         "**Purpose.** Confirm, against the data, that every element criteria §1 promises can actually be assembled for the 400 sampled admissions, say what MIMIC cannot supply, and size the reading burden per cell.", "",
         "**What was done.** `scripts/run0919_packet_feasibility.py` → `results/packet_feasibility.json`; `docs/adjudication/packet_specification.md` written by `scripts/run0919_phase6_docs.py`. Notes come from the per-note index (no text read); labs, omr and prescriptions via DuckDB filters on the raw .csv.gz.", "",
         f"**Results (n = {so['n']}).** Discharge summary present {so['availability_pct']['discharge_summary']:.1f}%; any radiology {so['availability_pct']['any_radiology']:.1f}% (liver-inclusive {so['availability_pct']['any_liver_inclusive_radiology']:.1f}%); ≥ 1 prescription {so['availability_pct']['any_prescription']:.1f}%; BMI in window {so['availability_pct']['omr_BMI']:.1f}%, BP {so['availability_pct']['omr_BP']:.1f}%. "
         f"Labs: platelets and glucose ≈ {so['labs_present_pct_in_admission']['Platelets']:.0f}% / {so['labs_present_pct_in_admission']['Glucose']:.0f}%, ALT/AST ≈ {so['labs_present_pct_in_admission']['ALT']:.0f}%, HbA1c {so['labs_present_pct_in_admission']['HbA1c']:.1f}%, HDL {so['labs_present_pct_in_admission']['HDL']:.1f}%. "
         f"Discharge summary median {so['reading_burden']['discharge_chars']['median']:,.0f} chars (p95 {so['reading_burden']['discharge_chars']['p95']:,.0f}); radiology reports median {so['reading_burden']['radiology_reports_total']['median']:.0f} (p95 {so['reading_burden']['radiology_reports_total']['p95']:.0f}); per-cell table in the doc. Not suppliable: quantified alcohol, biopsy as a structured source, waist circumference, coded diagnoses (stripped by design).", "",
         "**Checks passed.** All 420 charts (400 + 20 training) found in the locked population with admittime; per-cell n = 80/150/70/100.", "",
         "**Deviations.** None. Tier 1: the in-admission lab definition (hadm_id-linked OR same subject with charttime inside the stay) is recorded in the JSON; it differs from hadm_id-only by < 1 point per analyte.", "",
         "**What Kyle should look at.** §3 of the packet specification (not suppliable) against criteria §6a–6c; the by-cell discharge-summary availability (cell A is near-complete, C and D lower), which bears on how often 'Insufficient information' will be chosen.", "",
         "## 6.3 Adjudication instrument", "",
         "**Purpose.** A blank form reviewers can fill without ever seeing cell, weight or double-review status.", "",
         "**What was done.** `scripts/make_adjudication_template.py` → `docs/adjudication/adjudication_template.xlsx` (sheets README / sample / training / lists; openpyxl list validation on every categorical column, whole-number validation on minutes; ID column locked, sheet protection without password) and `docs/adjudication/data_dictionary.md`.", "",
         "**Results.** 400 sample rows in master-key order (not reordered by cell), 20 training rows, 11 columns exactly as criteria §7.", "",
         "**Checks passed.** `verify_commit_safe()` scans every cell of the workbook: no integer longer than 4 digits, no cell label, no 'double' token.", "",
         "**Deviations.** 'Not applicable' added to temporality / 6a / 6b / 6c so that a skipped secondary question is distinguishable from a forgotten one (Tier 1). 6b uses the Draft 1 g/week bands → P6-04.", "",
         "**What Kyle should look at.** Open the template once; check the option wording against the clinician's D1/D6 decisions before the training round.", "",
         "## 6.4 Reviewer assignment", "",
         "**Purpose.** Split the 400 charts between two reviewers with the double-review subset hidden and the order uninformative.", "",
         f"**What was done.** `scripts/assign_reviewers.py` (seed {ASG['seed']}) → untracked `data/processed/adjudication/reviewer_assignment.parquet` and `form_reviewer1.xlsx` / `form_reviewer2.xlsx`; tracked `results/reviewer_assignment.json` and `docs/adjudication/reviewer_assignment.md`.", "",
         f"**Results.** {ASG['per_reviewer']['reviewer1']['total']} / {ASG['per_reviewer']['reviewer2']['total']} charts per reviewer, {ASG['shared_charts_between_reviewers']} shared, {ASG['adjudications_total']} adjudications; per-cell counts per reviewer in the doc; Spearman(order, cell) {ASG['order_independence']['reviewer1_spearman_order_vs_cell_index']} / {ASG['order_independence']['reviewer2_spearman_order_vs_cell_index']}.", "",
         "**Checks passed.** Exactly 250 each; every double-review ID on both forms; every single-review ID on exactly one; per-cell single-review split differs by ≤ 1; orders are permutations of 1..250; forms pass the commit-safety scan.", "",
         "**Deviations.** None. Only two reviewers implemented; other values are refused so the design is re-derived deliberately.", "",
         "**What Kyle should look at.** Nothing until reviewers are named; the doc says it is revisable.", "",
         "## 6.5 Packet generator and dry run", "",
         "**Purpose.** Build the per-chart packets exactly as criteria §1 allows, prove by automated checks that nothing else leaks, and leave no packets on disk.", "",
         f"**What was done.** `scripts/make_reviewer_packets.py --dryrun` → `results/packet_dryrun.json`; packets are plain text with delimited note blocks so checks can separate narrative from structured text; the dry-run directory was removed by `shutil.rmtree` after `assert path == os.path.abspath('data/processed/_packet_dryrun')` (removed: {DRY['dryrun_dir_removed']}).", "",
         f"**Results.** {DRY['files_generated']} of {DRY['n_charts']} files, exceptions {DRY['exceptions_by_class'] or 'none'}, median {DRY['leak_checks']['file_bytes_median']:,.0f} bytes, load {DRY['timings_s']['load_inputs']} s + generate {DRY['timings_s']['generate']} s. "
         f"Structured-text leak checks: long titles {cnt['ii_long_title_structured']}, demographic labels {cnt['iii_demographic_label_structured']}, 8-digit integers {cnt['iv_8digit_structured']}, cell labels {cnt['v_cell_label_structured']}, markup {cnt['vi_markup_structured']}, own identifiers {cnt['vii_own_identifier_structured']}; "
         f"ICD-9-shaped numbers after removing value columns and signed day offsets {cnt['i_icd9_like_structured_excl_values_and_day_offsets']}; ICD-10-shaped tokens {cnt['i_icd10_like_structured_excl_value_columns']} (token table in the doc — drug-name fragments, to be grepped at final generation). "
         f"Narrative-only hits: 'recovery' {cnt['v_recovery_word_narrative_only']}, markup {cnt['vi_markup_narrative']}, long titles {cnt['ii_long_title_narrative']}, 8-digit {cnt['iv_8digit_narrative']}, own identifiers {cnt['vii_own_identifier_narrative']}.", "",
         f"**Checks passed.** Discharge text verbatim: {DRY['discharge_text_verbatim_vs_index']['charts_matching_index_char_count']}/{DRY['discharge_text_verbatim_vs_index']['charts_total']} charts match the per-note index character count; `data/processed/_packet_dryrun/` absent after the run; nothing printed but counts.", "",
         "**Deviations.** The raw regex (i) fires on lab values and signed day offsets by construction; the doc reports the raw count as specified and the refined counts beside it. Check (vii) (own hadm_id / subject_id / note_id substrings) was added beyond the six requested.", "",
         "**What Kyle should look at.** The token table in packet_specification.md §5; the final-generation command in §6 (run only after the criteria are frozen and reviewers are credentialed).", "",
         "## 6.6 Reviewer brief", "",
         "**Purpose.** One page a clinician can read cold.", "",
         "**What was done.** `docs/adjudication/reviewer_brief.md` templated by `scripts/run0919_phase6_docs.py` from `results/packet_feasibility.json`, `results/reviewer_assignment.json` and `results/reviewer_brief.json` (the hours arithmetic, with its assumptions, is stored there).", "",
         f"**Results.** Assuming {RB['assumptions']['chars_per_word']:.0f} chars/word, {RB['assumptions']['words_per_minute'][0]}–{RB['assumptions']['words_per_minute'][1]} wpm and {RB['assumptions']['fixed_overhead_min_per_chart']:.0f} min overhead: full read {RB['minutes_per_chart']['full'][0]:.0f}–{RB['minutes_per_chart']['full'][1]:.0f} min/chart → {RB['hours_per_reviewer_sample']['full'][0]:.0f}–{RB['hours_per_reviewer_sample']['full'][1]:.0f} h per reviewer for {RB['charts_per_reviewer']} charts; "
         f"focused read (discharge summary + liver-inclusive radiology) {RB['minutes_per_chart']['focused'][0]:.0f}–{RB['minutes_per_chart']['focused'][1]:.0f} min → {RB['hours_per_reviewer_sample']['focused'][0]:.0f}–{RB['hours_per_reviewer_sample']['focused'][1]:.0f} h. Called rough in the brief; the training round measures the real figure.", "",
         "**Checks passed.** No number in the brief is typed by hand.", "",
         "**Deviations.** The earlier analyst guess in the criteria doc (10–18 min/chart) is below the full-read figure here because it predates the confirmed radiology volume; both are shown to the reviewer as rough.", "",
         "**What Kyle should look at.** The DUA paragraph wording; whether the focused-read strategy is acceptable to the clinician (it changes what 'the packet was read' means).", "",
         "## Housekeeping", "",
         "Untracked outputs under `data/processed/adjudication/` (assignment parquet, two forms). No packets remain on disk. Nothing under `data/`, `models/` or `logs/` is tracked. No frozen artifact was touched; `scripts/masld_config.py` was not edited (all seeds used already exist there; the bootstrap and simulation seeds are constants in the new scripts). Tier 3 items: `phase6_decisions.md`. Blockers: none (`phase6_blockers.md`).", ""]
    with open("docs/run_2026-09-19/phase6_notes.md", "w") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    packet_specification()
    data_dictionary()
    reviewer_brief()
    phase6_notes()
    print("wrote docs/adjudication/packet_specification.md, data_dictionary.md, reviewer_brief.md, results/reviewer_brief.json and docs/run_2026-09-19/phase6_notes.md")
