#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 — write docs/preliminary_2026-11-10.md from the four results files.

Reads docs/run_2026-11-10/results/{fib4_by_cell,later_outcomes,icd_era,imaging_funnel}.json. Every number in
the document comes from those files; nothing is typed here. Counts from 1 to 10 arrive already masked.
"""
import json, os

RES = "docs/run_2026-11-10/results"
OUT = "docs/preliminary_2026-11-10.md"
CELL_NAME = {"A": "A · coded, in notes", "B": "B · not coded, in notes", "C": "C · coded, not in notes", "D": "D · neither"}


def n(v):
    return f"{v:,}" if isinstance(v, int) else ("—" if v is None else str(v))


def pct(s, ci=True):
    """'61.5% (60.6–62.3)' from a share dict; 'withheld' or 'not reported' otherwise."""
    if not isinstance(s, dict) or "pct" not in s:
        return "not reported"
    if not isinstance(s["pct"], (int, float)):
        return str(s["pct"])
    out = f"{s['pct']}%"
    if ci and s.get("ci95"):
        out += f" ({s['ci95'][0]}–{s['ci95'][1]})"
    return out


def xn(s):
    if not isinstance(s, dict) or "x" not in s:
        return "—"
    return f"{n(s['x'])} of {n(s['n'])}"


def miq(m, digits=2):
    if not m:
        return "—"
    f = (lambda v: f"{v:,.0f}") if digits == 0 else (lambda v: f"{v:.{digits}f}".rstrip("0").rstrip(".") if digits else str(v))
    return f"{f(m['median'])} [{f(m['q1'])}, {f(m['q3'])}]"


def fib4_section(d):
    L = ["## 1. Fibrosis index by cell (amendment l, S19)", "",
         f"Written by `scripts/run1110_fib4_by_cell.py` into `{RES}/fib4_by_cell.json`.", "",
         f"- **Measure:** FIB-4 = {d['definition']['fib4']}. Age is the age at admission, as in Table 3.",
         f"- **Cutoffs:** below {d['definition']['cutoffs']['low']} (low), above {d['definition']['cutoffs']['high']} (high).",
         "- **Cells:** definition (b), as in `docs/aim1a_crosstab.md`. A = coded and in notes, B = in notes only, C = coded only, D = neither.",
         f"- **Intervals:** subject-cluster bootstrap, {d['bootstrap']['replicates']} replicates, 95% percentile.", "",
         "### Primary: first result of each admission", "",
         "| Cell | Admissions | FIB-4 computable | Median [IQR] | Below 1.3 | 1.3–2.67 | Above 2.67 |",
         "| --- | --: | --: | --: | --: | --: | --: |"]
    p = d["analyses"]["primary_first_result"]
    for c in "ABCD":
        r = p[c]
        L.append(f"| {CELL_NAME[c]} | {n(r['admissions'])} | {pct(r['computable'])} | {miq(r.get('fib4'))} | "
                 f"{pct(r.get('below_low_cutoff'))} | {pct(r.get('indeterminate'))} | {pct(r.get('above_2_67'))} |")
    L += ["", "The three right-hand columns are shares of the admissions with a computable FIB-4, not of all admissions.", "",
          "### Sensitivity analyses", "",
          "Each row repeats the primary table under one change. Shown: the computable share, the median, and the share above 2.67.", "",
          "| Analysis | Cell | Admissions kept | FIB-4 computable | Median [IQR] | Below the low cutoff | Above 2.67 |",
          "| --- | --- | --: | --: | --: | --: | --: |"]
    names = [("sens1_low_cutoff_2_0_at_age_65_and_over", f"1 · low cutoff {d['definition']['cutoffs']['low_at_age_65_and_over_sens1']} at age 65 and over"),
             ("sens2_last_result", "2 · last result of the admission"),
             ("sens3_excluding_high_enzymes_and_other_etiologies", "3 · excluding AST or ALT above 200 U/L, and alcohol, viral, other-etiology or cirrhosis flags"),
             ("sens4_outpatient_365_days_before_admission", "4 · most recent outpatient values, 365 days before admission")]
    for key, label in names:
        a = d["analyses"].get(key, {})
        if "status" in a:
            L.append(f"| {label} | — | — | {a['status']} | — | — | — |")
            continue
        for c in "ABCD":
            r = a[c]
            L.append(f"| {label if c == 'A' else ''} | {c} | {n(r['admissions'])} | {pct(r['computable'])} | {miq(r.get('fib4'))} | "
                     f"{pct(r.get('below_low_cutoff'))} | {pct(r.get('above_2_67'))} |")
    s3 = d["analyses"]["sens3_excluding_high_enzymes_and_other_etiologies"]
    L += ["", "Analysis 3 removes these shares of each cell before anything is computed: "
          + "; ".join(f"{c} {pct(s3[c]['excluded'], ci=False)}" for c in "ABCD") + ".", "",
          "### Replicate with the language-model phenotype", "",
          f"Dev/test notes subsample only ({n(d['replicate_llm_phenotype']['admissions_in_subsample'])} admissions). First result of each admission.", "",
          "| Group | Admissions | FIB-4 computable | Median [IQR] | Below 1.3 | 1.3–2.67 | Above 2.67 |", "| --- | --: | --: | --: | --: | --: | --: |"]
    for g, r in d["replicate_llm_phenotype"]["groups"].items():
        L.append(f"| {g[0].upper() + g[1:]} | {n(r['admissions'])} | {pct(r['computable'])} | {miq(r.get('fib4'))} | "
                 f"{pct(r.get('below_low_cutoff'))} | {pct(r.get('indeterminate'))} | {pct(r.get('above_2_67'))} |")
    L += ["", "**Limitations.** FIB-4 is validated in outpatients. Acute illness raises AST and lowers platelets, so an inpatient value overstates fibrosis risk; "
          "analyses 2, 3 and 4 show how far the figures move when that is partly removed. FIB-4 can be computed for different shares of each cell, "
          "so the cells are compared on differently selected admissions. Admissions are not independent: one patient can contribute several. "
          "The cells rest on the frozen keyword rule, which has not been checked against chart review. Nothing here says who has fibrosis.", ""]
    return L


def outcomes_section(d):
    f, g = d["flow"], d["groups"]
    L = ["## 2. Later outcomes after an uncoded mention (amendment m, S20)", "",
         f"Written by `scripts/run1110_later_outcomes.py` into `{RES}/later_outcomes.json`. Grain: subject. Intervals: Wilson 95%. No survival model.", "",
         "- **Index:** the subject's earliest admission in which the notes are positive under definition (b).",
         "- **Group U:** the index admission has no MASLD code, and no earlier admission has one.",
         "- **Group C:** the index admission has a MASLD code.",
         "- **A later admission** is any admission of the analysis population that begins after the index admission began.",
         "- **Days** run from the index discharge to the start of the first later admission that carries the flag.", "",
         "| Step | Subjects |", "| --- | --: |",
         f"| With a note-positive admission | {n(f['subjects_with_a_note_positive_admission'])} |",
         f"| Index uncoded but coded earlier (in neither group) | {n(f['index_uncoded_but_coded_earlier_in_neither_group'])} |",
         f"| Excluded: cirrhosis or HCC flag at or before index | {n(f['excluded_cirrhosis_or_hcc_at_or_before_index'])} |",
         f"| Excluded: died during the index admission | {n(f['excluded_died_during_index_admission_only'])} |",
         f"| Group U | {n(g['U']['subjects'])} |", f"| Group C | {n(g['C']['subjects'])} |", "",
         "| Measure | Group U (uncoded at index) | Group C (coded at index) |", "| --- | --: | --: |",
         f"| Subjects with a later admission | {pct(g['U']['with_a_later_admission'])} | {pct(g['C']['with_a_later_admission'])} |"]
    for key, label in (("later_cirrhosis_flag", "cirrhosis flag"), ("later_hcc_flag", "HCC flag")):
        L.append(f"| Of those, a later {label} | {pct(g['U'][key])} | {pct(g['C'][key])} |")
        L.append(f"| Days to the first later {label}, median [IQR] | {miq(g['U'][key].get('days_from_index_discharge'), 0)} | {miq(g['C'][key].get('days_from_index_discharge'), 0)} |")
    lc = g["U"]["later_coded"]
    L += [f"| Of those, later given a MASLD code | {pct(lc)} | not applicable |",
          f"| Days to the first coded admission, median [IQR] | {miq(lc.get('days_from_index_discharge'), 0)} | not applicable |",
          f"| Admissions after the index and before the first coded one, median [IQR] | {miq(lc.get('admissions_before_first_coded'), 0)} | not applicable |", "",
          "**Limitations.** Only returns to this hospital are observed, so every figure is a floor: a patient diagnosed or coded elsewhere counts as never diagnosed or coded. "
          "The two groups differ in more than coding, and nothing here adjusts for it. Follow-up length differs by patient and is not modelled. "
          "The cirrhosis and HCC flags come from diagnosis codes. A flag at a later admission can describe disease that was already present at index but not coded. "
          "The index rests on the frozen keyword rule, unchecked against chart review.", ""]
    return L


def era_section(d):
    L = ["## 3. Coding by period (amendment n, S21)", "",
         f"Written by `scripts/run1110_icd_era.py` into `{RES}/icd_era.json`.", "",
         "- **Measure:** among note-positive admissions, the share with no MASLD code, B ÷ (A + B).",
         f"- **Intervals:** subject-cluster bootstrap, {d['bootstrap']['replicates']} replicates, 95% percentile.",
         "- **Second column:** the same share with ICD-9 571.9 removed from the code set (S7).", ""]
    for key, title, first in (("by_anchor_year_group", "By the patient's anchor year group", "Anchor year group"),
                              ("by_icd_version", "By the ICD version of the admission's diagnoses", "ICD version")):
        L += [f"### {title}", "", f"| {first} | Note-positive admissions | Share uncoded | Share uncoded, 571.9 removed |", "| --- | --: | --: | --: |"]
        for r in d[key]:
            L.append(f"| {r['stratum']} | {n(r['note_positive_admissions'])} | {pct(r['primary_code_set'])} | {pct(r['with_571_9_removed'])} |")
        L.append("")
    o = d["overall"]
    L += [f"All note-positive admissions ({n(d['note_positive_admissions'])}): {pct(o['primary_code_set'])}; with 571.9 removed, {pct(o['with_571_9_removed'])}. "
          "A stratum is reported when it has at least 11 note-positive admissions.", "",
          "**Limitations.** The anchor year group is a three-year window assigned once per patient. It is not the calendar year of the admission, "
          "and a patient's admissions can fall years after it. Period and ICD version move together, so neither table isolates one from the other. "
          "Case mix, note volume and imaging use also changed over these years. The note axis is the frozen keyword rule, unchecked against chart review.", ""]
    return L


def funnel_section(d):
    s2, s3, s4 = d["stage2_split"], d["stage3_by_stage2_source"], d["stage4_coded_share_by_source"]
    L = ["## 4. Documentation funnel where the liver was imaged (amendment o, S22)", "",
         f"Written by `scripts/run1110_imaging_funnel.py` into `{RES}/imaging_funnel.json`.", "",
         "- **Population:** imaging-observed admissions (S3): at least one liver-inclusive study, linked to the admission or in the outpatient window of 365 days before to 30 days after admission.",
         "- **Rule-positive** means the frozen keyword rule fires in that document.",
         f"- **Intervals:** subject-cluster bootstrap, {d['bootstrap']['replicates']} replicates, 95% percentile.", "",
         "| Stage | Admissions | Share of the stage above |", "| --- | --: | --: |",
         f"| 1 · Imaging-observed | {xn(d['stage1_imaging_observed'])} | {pct(d['stage1_imaging_observed'])} |",
         f"| 2 · A radiology report is rule-positive | {xn(d['stage2_radiology_report_rule_positive'])} | {pct(d['stage2_radiology_report_rule_positive'])} |",
         f"| 3 · The discharge summary is also rule-positive | {xn(d['stage3_discharge_summary_also_rule_positive'])} | {pct(d['stage3_discharge_summary_also_rule_positive'])} |", "",
         "| Stage 4 · coded share | Admissions coded | Share coded |", "| --- | --: | --: |",
         f"| Discharge summary rule-positive (stage 3 yes) | {xn(d['stage4_coded_share']['discharge_summary_rule_positive'])} | {pct(d['stage4_coded_share']['discharge_summary_rule_positive'])} |",
         f"| Discharge summary not rule-positive (stage 3 no) | {xn(d['stage4_coded_share']['discharge_summary_not_rule_positive'])} | {pct(d['stage4_coded_share']['discharge_summary_not_rule_positive'])} |", "",
         "### Stage 2 split by where the positive radiology report sits", "",
         "| Source of the positive report | Share of stage 2 | Discharge summary also positive | Coded, summary positive | Coded, summary not positive |",
         "| --- | --: | --: | --: | --: |"]
    for key, label in (("inpatient_linked_report", "A report linked to the admission"), ("outpatient_window_report_only", "Outpatient-window reports only")):
        L.append(f"| {label} | {pct(s2[key])} | {pct(s3[key])} | {pct(s4[key]['discharge_summary_rule_positive'])} | {pct(s4[key]['discharge_summary_not_rule_positive'])} |")
    L += ["", "**Limitations.** A rule-positive report is a keyword match, not a confirmed finding, and the rule has not been checked against chart review. "
          "An outpatient-window report can be up to a year old, so its absence from the discharge summary is not an omission in itself. "
          "The funnel is restricted to admissions where the liver was imaged, which is a selected group. "
          "The stages describe documents; they do not say why a finding was not carried forward or not coded.", ""]
    return L


def main():
    load = lambda f: json.load(open(f"{RES}/{f}.json"))
    L = ["# Exploratory analyses, 10 November 2026", "",
         "> **PRELIMINARY and exploratory (analysis-plan amendments l–o, registry S19–S22).** Nothing here is validated against chart review. "
         "Every number is written by the script named in each section into `docs/run_2026-11-10/results/`. Counts from 1 to 10 appear as <11, and a share that would reveal one is withheld.", "",
         "The amendments were committed before any of these analyses was computed (`docs/analysis_plan_prespecified.md` §6; commit in `docs/run_2026-11-10/STATE.json`, `phase3_commit`). "
         "None of them changes a primary analysis. All four use the frozen keyword rule for the note axis; section 1 also repeats one table with the language-model phenotype on the dev/test notes subsample.", ""]
    L += fib4_section(load("fib4_by_cell")) + outcomes_section(load("later_outcomes")) + era_section(load("icd_era")) + funnel_section(load("imaging_funnel"))
    open(OUT, "w").write("\n".join(L).rstrip("\n") + "\n")
    print("wrote", OUT, len(L), "lines")


if __name__ == "__main__":
    main()
