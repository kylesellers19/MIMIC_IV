#!/usr/bin/env python3
"""run_2026-11-10 Phase 9 — write docs/run_2026-11-10/DECISIONS_FOR_KYLE.md.

Tier 3 items only: question, options, what each changes, what is blocked, and draft amendment text for
every option. No recommendation anywhere. Numbers are computed here or read from results files and are
written to docs/run_2026-11-10/results/decisions_inputs.json.

N-01 is described on dev/test only (distribution; no gold). GOLD_HOLDOUT files are not opened.
"""
import json, os, re, sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.run1110_common import FLOOR, mask

R19, R10, R11 = "docs/run_2026-09-19/results", "docs/run_2026-10-27/results", "docs/run_2026-11-10/results"
OUT = "docs/run_2026-11-10/DECISIONS_FOR_KYLE.md"
INPUTS = f"{R11}/decisions_inputs.json"
SIGNOFF_NAME = "Kyle Sellers (study lead; not a clinician)"
SEPT = "docs/run_2026-09-19/DECISIONS_FOR_KYLE.md"


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


def n(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


# ----------------------------------------------------------------------------- N-01 on dev/test
def n01():
    """Admission-level scores on the dev/test notes subsample. Distribution only."""
    from scripts.llm_phenotype import ANSWERS, load as load_adm
    adm = load_adm()
    r = pd.read_parquet(ANSWERS, columns=["hadm_id", "key", "answer", "timing", "p_yes"])
    r = r[r.hadm_id.isin(set(adm.hadm_id)) & r.timing.isin(["CURRENT", "PAST"])].drop_duplicates(["hadm_id", "key"])
    r["p"] = r.p_yes.fillna(0.0).clip(0, 1)
    g = r.groupby("hadm_id").p
    s = pd.DataFrame({"max_p": g.max(), "noisy_or": 1 - g.apply(lambda v: float(np.prod(1 - v.to_numpy()))), "k": g.size()})
    a = adm[["hadm_id", "llm"]].merge(s, left_on="hadm_id", right_index=True, how="left").fillna({"max_p": 0.0, "noisy_or": 0.0, "k": 0})
    have = a.k > 0
    q = lambda v: {f"p{int(x)}": round(float(np.percentile(v, x)), 3) for x in (10, 25, 50, 75, 90)}
    out = {"scope": "dev/test notes subsample; merged v4 answers; distinct units per admission; sentences with timing CURRENT or PAST",
           "admissions": int(len(a)), "admissions_with_an_eligible_sentence": int(have.sum()),
           "admissions_scored_zero_by_definition": int((~have).sum()),
           "eligible_sentences_per_admission_median": float(np.median(a.k[have])),
           "admissions_with_two_or_more_eligible_sentences": mask(int((a.k >= 2).sum())), "options": {}}
    for name in ("max_p", "noisy_or"):
        v = a.loc[have, name].to_numpy()
        pos, neg = a.loc[have & a.llm, name].to_numpy(), a.loc[have & ~a.llm, name].to_numpy()
        out["options"][name] = {
            "quantiles_among_admissions_with_an_eligible_sentence": q(v),
            "quantiles_primary_positive": q(pos) if len(pos) >= FLOOR else None,
            "quantiles_primary_negative_with_an_eligible_sentence": q(neg) if len(neg) >= FLOOR else None,
            "admissions_at_or_above_0_5": mask(int((a[name] >= 0.5).sum())),
            "admissions_above_0_99": mask(int((a[name] > 0.99).sum())),
            "at_or_above_0_5_but_primary_negative": mask(int(((a[name] >= 0.5) & ~a.llm).sum())),
            "below_0_5_but_primary_positive": mask(int(((a[name] < 0.5) & a.llm).sum())),
            "distinct_score_values_rounded_to_3_decimals": int(pd.Series(np.round(v, 3)).nunique())}
    for k in ("admissions_at_or_above_0_5", "admissions_above_0_99", "at_or_above_0_5_but_primary_negative", "below_0_5_but_primary_positive"):
        x, y = out["options"]["max_p"][k], out["options"]["noisy_or"][k]     # the two counts differ by a count of admissions
        if isinstance(x, int) and isinstance(y, int) and 0 < abs(x - y) < FLOOR:
            out["options"]["noisy_or"][k] = "withheld (within 10 of the maximum's count)"
    d = (a.noisy_or - a.max_p)[have]
    out["noisy_or_minus_max"] = {"spearman": round(float(a.loc[have, ["max_p", "noisy_or"]].corr(method="spearman").iloc[0, 1]), 3),
                                 "admissions_where_noisy_or_exceeds_max_by_more_than_0_10": mask(int((d > 0.10).sum())),
                                 "admissions_where_they_are_equal": mask(int((d.abs() < 1e-12).sum()))}
    out["classifier_only"] = {"primary_positive_admissions": int(a.llm.sum()),
                              "note": "no score; discrimination and calibration measures that need a probability are not reported for this arm"}
    return out


# ----------------------------------------------------------------------------- the document
def fq(d):
    return "—" if not d else " / ".join(f"{d[k]:.3f}" for k in ("p10", "p25", "p50", "p75", "p90"))


def sept_table():
    heads = re.findall(r"^## ((?:D|P6)-\d+) · (.+)$", open(SEPT).read(), re.M)
    status = {
        "D-01": "**Open. Blocks the start of adjudication:** the sampling weights are fixed at sampling time.",
        "D-03": "Open. The repository is public and has no license file.",
        "D-04": "Open. Updated by N-07 above.",
        "D-05": "Partly closed on 2026-11-10: the three lines in `docs/reference_standard.md` now follow option 1. The sentence in the older draft outside this repository, and any slide or abstract reusing it, are untouched.",
    }
    L = ["| Item | Question | Where it stands |", "| --- | --- | --- |"]
    seen = set()
    for i, t in heads:
        if i in seen:
            continue
        seen.add(i)
        t = re.sub(r"\s*\((Phase [^)]*|criteria [^)]*|design finding[^)]*)\)", "", t).replace(" — supported, not decided", "")
        L.append(f"| {i} | {t} | {status.get(i, 'Open.')} |")
    return L


def main():
    d1 = n01()
    c = load(f"{R11}/carryover_check.json")
    q = load(f"{R10}/quant_check.json")
    cap = load(f"{R11}/extractor_cap.json")
    held, base = load(f"{R11}/held_back_files.json"), load(f"{R11}/base_exposure_audit.json")
    sh = load(f"{R11}/diag_section_study_headers.json")
    lock = load(f"{R10}/llm_gold_lock.json")
    prel = load(f"{R10}/llm_review_preliminary.json")
    inputs = {"script": "scripts/run1110_decisions.py", "n01": d1}

    # N-02 arithmetic
    if c:
        units = sum(v["population_units"] for v in c["new_sample"]["per_stratum"].values()) if False else sum(
            v["population_units"] for v in c["pooled"]["per_stratum"].values())
        sp_now, sp_oct = c["sample"]["speed_per_s"], q["speed_per_s"]["q4_rerun"]
        hrs = {"units_to_re_ask": units, "speed_this_run_per_s": sp_now, "hours_at_this_runs_speed": round(units / sp_now / 3600, 1),
               "speed_october_rerun_per_s": sp_oct, "hours_at_octobers_speed": round(units / sp_oct / 3600, 1)}
        inputs["n02"] = hrs
        w, a = c["new_sample"]["population_weighted"], c["admissions"]
        shr = lambda s: (f"{s['pct']}%" + (f" (95% upper bound {s['wilson_hi_pct']}%)" if isinstance(s["pct"], str) else f" ({s['wilson_lo_pct']}–{s['wilson_hi_pct']})"))
        p4 = (f"Phase 4 asked {n(c['sample']['units_answered'])} carried-over NO units with v4 (`{R11}/carryover_check.json`). "
              f"Population-weighted, the answer was not NO for {shr(w['v4_answer_not_no'])} and the unit would change its admission's status for {shr(w['primary_label_status_changes'])}. "
              f"Expected dev/test admissions changing label if all were re-asked: {n(a['expected_admissions_changing_label'])} of {n(a['admissions_dev_test_subsample'])} (upper bound {n(a['upper_bound_wilson'])}).")
        cost = (f"About {n(units)} units. At this run's measured speed ({sp_now} per second, with other jobs running) that is about {hrs['hours_at_this_runs_speed']} hours; "
                f"at October's rerun speed ({sp_oct} per second) about {hrs['hours_at_octobers_speed']} hours.")
    else:
        p4 = "[PENDING] Phase 4 had not finished when this file was written; rerun `scripts/run1110_decisions.py` once `carryover_check.json` exists."
        cost = "[PENDING] The unit count and hours are written from Phase 4's results file."
    json.dump(inputs, open(INPUTS, "w"), indent=1)

    mx, no = d1["options"]["max_p"], d1["options"]["noisy_or"]
    hb = held["d3_sentence_windows"]["per_file"] if held else {}
    tfile, pfile = "scripts/llm_timing_test.py", "docs/adjudication/criteria_revision_proposal.md"
    top = max(base["d3_sentence_windows"]["per_file"].items(), key=lambda kv: kv[1]["lines_flagged"]) if base else (None, {})
    L = [
        "# Decisions for Kyle — run_2026-11-10", "",
        "Tier 3 items: anything that changes a definition, a population, a primary analysis, or what the paper claims. Each entry gives the question, the options, what each option changes, "
        "what is blocked until it is decided, and draft amendment text for every option, so the chosen one can be committed as written. **No recommendation is made anywhere in this file.**", "",
        f"Written by `scripts/run1110_decisions.py`. Numbers come from results files; the ones computed for this file are in `{INPUTS}`.", "",
        "## At a glance", "",
        "| Item | Decision | Blocks |", "| --- | --- | --- |",
        "| N-01 | Admission-level probability for the language-model arm | Any probability-based metric for that arm; must be fixed before an adjudication result is seen |",
        "| N-02 | Prompt-version difference between dev/test and GOLD_HOLDOUT | What the manuscript says about the merged dev/test labels |",
        "| N-03 | Sample admissions with no kept sentence | How the language-model arm's errors are tabulated against chart review |",
        "| N-04 | Note axis for Aim 1a | Which computable phenotype the headline comparison uses |",
        "| N-05 | The alternative section-closing rule | Nothing computational |",
        "| N-06 | Reviewer criteria against the locked prompt | The chart criteria, and so the start of adjudication |",
        "| N-07 | Registration (updates D-04) | The manuscript's timing claims |",
        "| N-08 | What prospective reviewers are offered | Sending the one-pager |",
        "| N-09 | Material the push gate flags: two held-back files, and lines already public | Two files stay local; possible clean-up of public documents |",
        "| N-10 | The one-pager states the study question; criteria §10 says reviewers are not told it | Sending the one-pager to a prospective reviewer |",
        "| D-01 (September) | Keep or drop ICD-9 571.9 | **The start of adjudication** |", "",

        "## N-01 · Admission-level probability for the language-model arm", "",
        "**Question.** The locked answers hold three probabilities per sentence. The admission rule is a classification (at least one YES, current or past). "
        "Which admission-level probability, if any, represents this arm when it is scored against chart review? It must be fixed before any adjudication result is seen.", "",
        f"**What was computed (dev/test only; distribution only; no gold).** `{INPUTS}`, field `n01`. "
        f"Of {n(d1['admissions'])} dev/test admissions, {n(d1['admissions_with_an_eligible_sentence'])} have at least one sentence with timing CURRENT or PAST; "
        f"the other {n(d1['admissions_scored_zero_by_definition'])} score zero under both formulas. The median number of such sentences, where there is one, is {d1['eligible_sentences_per_admission_median']:g}. "
        "A sentence answered NO has timing NA, so only YES and UNCLEAR sentences enter either formula.", "",
        "| | Maximum P(YES) | Noisy-OR |", "| --- | --: | --: |",
        f"| Percentiles 10 / 25 / 50 / 75 / 90, admissions with an eligible sentence | {fq(mx['quantiles_among_admissions_with_an_eligible_sentence'])} | {fq(no['quantiles_among_admissions_with_an_eligible_sentence'])} |",
        f"| Same, primary-positive admissions | {fq(mx['quantiles_primary_positive'])} | {fq(no['quantiles_primary_positive'])} |",
        f"| Same, primary-negative admissions with an eligible sentence | {fq(mx['quantiles_primary_negative_with_an_eligible_sentence'])} | {fq(no['quantiles_primary_negative_with_an_eligible_sentence'])} |",
        f"| Admissions at or above 0.5 | {n(mx['admissions_at_or_above_0_5'])} | {n(no['admissions_at_or_above_0_5'])} |",
        f"| Admissions above 0.99 | {n(mx['admissions_above_0_99'])} | {n(no['admissions_above_0_99'])} |",
        f"| At or above 0.5 but negative by the rule | {n(mx['at_or_above_0_5_but_primary_negative'])} | {n(no['at_or_above_0_5_but_primary_negative'])} |",
        f"| Below 0.5 but positive by the rule | {n(mx['below_0_5_but_primary_positive'])} | {n(no['below_0_5_but_primary_positive'])} |",
        f"| Distinct score values (3 decimals) | {n(mx['distinct_score_values_rounded_to_3_decimals'])} | {n(no['distinct_score_values_rounded_to_3_decimals'])} |", "",
        f"Rank correlation between the two scores: {d1['noisy_or_minus_max']['spearman']}. Admissions where noisy-OR exceeds the maximum by more than 0.10: {n(d1['noisy_or_minus_max']['admissions_where_noisy_or_exceeds_max_by_more_than_0_10'])}. "
        f"Primary-positive admissions under the classification rule: {n(d1['classifier_only']['primary_positive_admissions'])}."
        + (" On dev/test, cutting either score at 0.5 gives exactly the classification rule's labels." if all(
            d1["options"][o][k] == 0 for o in ("max_p", "noisy_or") for k in ("at_or_above_0_5_but_primary_negative", "below_0_5_but_primary_positive")) else ""), "",
        "**Options and what each changes.**",
        "- *Maximum P(YES) over sentences with CURRENT or PAST timing.* One sentence decides the score, as one sentence decides the label. Many admissions share a score near 1, so ranking among them is coarse and calibration rests on few distinct values.",
        "- *Noisy-OR over those sentences.* The score rises with the number of supporting sentences. It treats sentences as independent, which repeated statements of one finding are not, so long charts score higher for the same evidence.",
        "- *Report the arm as a classifier only.* No probability is defined. Sensitivity, specificity and predictive values are reported; AUROC, AUPRC, calibration and any comparison that needs a score are not, and the arm cannot enter a stacked model as a probability.", "",
        "**Blocked until decided.** Every probability-based metric for the language-model arm against chart review. Nothing in this run.", "",
        "**Draft amendment text.**",
        "- *Maximum:* \"The language-model arm's admission-level probability is the maximum P(YES) over kept sentences whose timing is CURRENT or PAST, and zero when there is none. Fixed on [date], before any adjudication result was seen. Its distribution on dev/test had been seen.\"",
        "- *Noisy-OR:* \"The language-model arm's admission-level probability is one minus the product of (1 − P(YES)) over the distinct kept sentences whose timing is CURRENT or PAST, and zero when there is none. Fixed on [date], before any adjudication result was seen. Its distribution on dev/test had been seen.\"",
        "- *Classifier only:* \"The language-model arm is evaluated as a classifier under the admission rule of amendment (h). No admission-level probability is defined for it, and no metric that needs one is reported. Fixed on [date], before any adjudication result was seen.\"", "",

        "## N-02 · Prompt-version difference between dev/test and GOLD_HOLDOUT", "",
        "**Question.** On dev/test, units v3 answered NO were carried into the merged labels without being asked with v4. On GOLD_HOLDOUT, v4 answered every unit. What is done about the difference?", "",
        f"**What Phase 4 found.** {p4}", "",
        "**Options and what each changes.**",
        f"- *Re-ask all carried-over NO units with v4.* {cost} Dev/test labels would then come from one prompt throughout, like GOLD_HOLDOUT. Every dev/test table that uses the language-model phenotype would be recomputed and dated, and the earlier figures kept beside them.",
        "- *Keep the merged labels and report Phase 4.* Nothing is recomputed. The manuscript states the design, the estimated share of units and admissions affected, and its bounds.",
        "- *Keep language-model output out of stacked-model training.* Can be combined with either option above. The arm is then compared with the other arms but is never an input to a model evaluated on GOLD_HOLDOUT, so no model is trained on labels produced under one design and tested on labels produced under another.", "",
        "**Blocked until decided.** The wording of the methods on the merged labels. Whether the language-model phenotype may be a model input.", "",
        "**Draft amendment text.**",
        "- *Re-ask:* \"All dev/test units whose stored answer was v3's NO were asked with prompt v4 on the pinned model on [dates]. The merged labels were replaced; tables computed from the earlier labels are retained and marked superseded. The carry-over check of 10 November 2026 had been seen.\"",
        "- *Keep and report:* \"Dev/test labels remain the merged v4 labels. The carry-over check (amendment k) is reported with its bounds as the estimate of what re-asking would change.\"",
        "- *Not a model input:* \"No label or probability from the language-model arm is used to fit, tune or select any model that is evaluated on GOLD_HOLDOUT.\"", "",

        "## N-03 · Sample admissions with no kept sentence", "",
        "**Question.** The run file states that 80 of the 400 sampled admissions have no kept sentence, all in the two note-negative strata. The language-model arm labels them negative by construction. "
        "If chart review finds steatosis in one of them, whose error is it? *(The figure is quoted from the run file. It was not recomputed here: that would mean opening a sealed file.)*", "",
        "**Options and what each changes.**",
        "- *Report them as extractor misses, separately.* The arm's sensitivity is given twice: over all sampled admissions, and over those with a kept sentence. A positive chart with no kept sentence is counted against the extractor.",
        "- *Pool them into the language-model arm's error.* One sensitivity figure for the pipeline as a whole. A miss by the extractor and a miss by the model are not distinguished.", "",
        "**What each changes.** The headline comparison between arms is unchanged in the pooled figure. The separate table needs the count of positive charts among those admissions, which may be below 11 and would then be masked.", "",
        "**Blocked until decided.** The layout of the language-model arm's error table. Must be fixed before adjudication results are seen.", "",
        "**Draft amendment text.**",
        "- *Separate:* \"For the language-model arm, admissions with no kept sentence are reported as a separate row. Sensitivity is reported for the whole pipeline and for admissions with at least one kept sentence. Counts from 1 to 10 are masked.\"",
        "- *Pooled:* \"For the language-model arm, an admission with no kept sentence is a negative prediction, and any error on it is counted as the arm's error.\"", "",

        "## N-04 · Note axis for Aim 1a", "",
        "**Question.** Aim 1a compares a code axis with a note axis. The note axis has been the frozen keyword rule. A second computable note phenotype now exists. Which is the note axis?", "",
        "**Options and what each changes.**",
        "- *The frozen rule.* Nothing changes. The sample, its strata and its weights were drawn on this axis. The language-model phenotype stays an exploratory second phenotype (S15).",
        "- *The language model.* The computable cross-tabulation would be rebuilt on a phenotype that exists only for the dev/test notes subsample and GOLD_HOLDOUT, not for the whole population. The sample was not stratified on it, so the weights do not match its cells.",
        "- *Both.* The frozen rule remains the axis the sample was drawn on and the primary comparison. The language model is reported beside it wherever it exists, and the adjudicated estimates are computed for both, with the sample's weights applied to each.", "",
        "**Blocked until decided.** The framing of the Aim 1a result. Nothing computational.", "",
        "**Draft amendment text.**",
        "- *Frozen rule:* \"The note axis of Aim 1a is the frozen keyword rule, version 1.1.0, as sampled. The language-model phenotype is reported as an exploratory comparison (S15) and does not define a cell.\"",
        "- *Language model:* \"The note axis of Aim 1a is the language-model phenotype of amendment (h). The sample was stratified on the frozen rule; estimates on the new axis use the original sampling weights and are reported with that limitation.\"",
        "- *Both:* \"Aim 1a is reported on two note axes. The frozen keyword rule, on which the sample was stratified, is primary. The language-model phenotype is secondary and uses the same sample and weights.\"", "",

        "## N-05 · The alternative section-closing rule", "",
        "**Question.** A different rule for closing a findings block was examined on 23–26 September and not adopted. Is it dropped, or run as a dev/test-only sensitivity analysis?", "",
        f"**What is known.** Section labels only set priority under the {cap['cap']}-sentence cap, and the cap bound {n(cap['admissions_cap_bound'])} of {n(cap['admissions_dev_test_subsample'])} dev/test admissions (`{R11}/extractor_cap.json`). "
        "For every other admission a different closing rule changes a label that nothing uses. Aggregate counts from the September examination are in `" + R11 + "/diag_section_study_headers.json` and `diag_section_tableB.json`.", "",
        "**Options and what each changes.**",
        "- *Drop it.* The protocol already says it was examined and not adopted. Nothing is run.",
        "- *Run it as a dev/test-only sensitivity analysis.* The extractor is rerun with the alternative rule, the changed sentences are asked with v4, and the admission labels are compared. GOLD_HOLDOUT is not touched, so the result cannot be scored against chart review.", "",
        "**Blocked until decided.** Nothing.", "",
        "**Draft amendment text.**",
        "- *Drop:* \"The alternative section-closing rule examined on 23–26 September 2026 is not part of any analysis.\"",
        "- *Sensitivity:* \"Sensitivity analysis S23: the extractor's section-closing rule is replaced by the alternative examined on 23–26 September 2026, on dev/test only. Reported: sentences whose section label changes, admissions whose kept sentences change, admissions whose label changes. Already seen: the aggregate counts of the September examination.\"", "",

        "## N-06 · Reviewer criteria against the locked prompt", "",
        "**Question.** Chart reviewers will answer on the scale Definite, Probable, Possible, Absent, Insufficient information (`docs/adjudication_criteria.md`, Draft 1). The locked prompt answers YES, UNCLEAR or NO for a sentence, with a timing word. "
        "The two were written separately. Where they differ, the language-model arm is scored against a standard that defines the finding differently. Are the chart criteria written from the clinical definition, with the differences reported, or aligned to the prompt?", "",
        f"**Who has reviewed what.** The admission rule was signed off by {SIGNOFF_NAME}. No clinician has reviewed the admission rule or the prompt's rules. The chart criteria are a draft with open clinician decisions (D1–D8 in that document).", "",
        "**Crosswalk.** Chart levels are from Draft 1, where Definite and Probable are positive. Prompt answers are from `RULES` and `ALCOHOL_RULE` in `scripts/llm_sentence_review.py`; an admission is positive when one sentence is YES with timing CURRENT or PAST.", "",
        "| Evidence | Chart criteria, Draft 1 | Locked prompt, v4 | Same result? |", "| --- | --- | --- | --- |",
        "| CT or MRI reporting steatosis, fatty liver, fatty infiltration or decreased attenuation | Definite | YES. Also names attenuation below the spleen or below 40 HU, and signal loss on out-of-phase MRI | Yes. The prompt names signs the criteria do not list |",
        "| Liver biopsy reporting steatosis | Definite | YES when a kept sentence says so. Pathology reports are not among the notes read | Yes, where a sentence exists |",
        "| Ultrasound: increased echogenicity \"consistent with steatosis\" | Probable (open decision D2) | YES | Yes |",
        "| **Ultrasound echogenicity reported, interpretation absent** | Not listed. Row (c) requires the interpretation | YES: \"a diffusely echogenic or hyperechoic liver\" | **Differs.** The prompt counts it; the criteria are silent |",
        "| Clinician statement (\"fatty liver\", \"known NAFLD\") without imaging | Probable | YES (the abbreviations are listed) | Yes |",
        "| **Hedged wording: \"likely\", \"probable\", \"suggestive of\"** | Not listed as hedged. The criteria's examples of hedging are \"cannot exclude\" and \"may represent\" | UNCLEAR, which is not positive | **May differ.** A reviewer could reasonably read \"likely steatosis\" as Probable, which is positive |",
        "| Hedged wording: \"cannot exclude\", \"may represent\", \"possible\" | Possible (open decision D3) | UNCLEAR | Yes under the draft. Differs if D3 moves hedged imaging to Probable |",
        "| \"Consistent with\", \"compatible with\" | Row (c) uses \"consistent with\" for Probable | YES | Yes |",
        "| Coarse or heterogeneous echotexture only | Not listed | UNCLEAR | Prompt only |",
        "| Focal fatty sparing | Not listed | YES (\"the rest of the liver is fatty\") | Prompt only |",
        "| Focal fat, or a single fatty lesion | Not listed | NO | Prompt only |",
        "| A request to evaluate for or rule out fatty liver | Not listed | NO | Prompt only |",
        "| Alcohol-related liver disease, alcoholic hepatitis, and cirrhosis or liver fibrosis; fat not stated | Not addressed. Alcohol is a secondary question (6b) | NO. Alcoholic fatty liver and alcoholic steatohepatitis are YES | Prompt only. The criteria do not say how cirrhosis without a statement of fat is read |",
        "| Raised liver enzymes or metabolic risk alone | Absent | NO | Yes |",
        "| **Ongoing diagnosis listed in the history** (\"history of NAFLD\") | Positive in the draft; recorded as before, during or both (open decision D4) | PAST or CURRENT, at the model's reading. Both count | Same label. The timing field can differ, which matters only for the CURRENT-only sensitivity definition |",
        "| Family history | Not addressed | FAMILY, never positive | Prompt only |",
        "| **A newer study stating no steatosis** | Can override an older positive, at the reviewer's judgement (open decision D5) | No override. One YES sentence anywhere makes the admission positive | **Differs in structure** |",
        "| **Not enough information** | Insufficient information | No equivalent. An admission with no kept sentence is negative | **Differs in structure** (see N-03 and P6-01) |",
        "| Unit read | The whole packet: summary, radiology reports, laboratory values, medication orders | One sentence, with its note type and heading; liver-related sentences only | Differs in structure |", "",
        "**Options and what each changes.**",
        "- *Write the chart criteria from the clinical definition and report the differences.* Clinicians settle D1–D8 without reference to the prompt. The crosswalk above is frozen with the criteria and published as the list of known construct differences. "
        "The language-model arm is then scored against a standard defined independently of it, and part of its disagreement is attributable to rows marked \"differs\".",
        "- *Align the chart criteria to the prompt's construct.* The rows marked \"differs\" and \"prompt only\" are written into the criteria in the prompt's direction (for example, echogenicity reported without interpretation counts as Probable). "
        "Agreement between the arm and chart review rises by construction. The reference standard is then partly defined by one of the arms it evaluates, and the frozen keyword rule and the other models are scored against a standard shaped to a competitor. The prompt is locked, so alignment can only run in that direction.", "",
        "**Blocked until decided.** The chart criteria, and through them the start of adjudication. Clinician review of the admission rule is outstanding under either option.", "",
        "**Draft amendment text.**",
        "- *Independent criteria:* \"The adjudication criteria were finalised by clinicians from the clinical definition of hepatic steatosis, without reference to the language-model prompt. The crosswalk between the chart scale and the prompt's answers, frozen with the criteria, lists every known difference in construct; disagreement on those rows is reported separately.\"",
        "- *Aligned criteria:* \"The adjudication criteria were aligned to the construct of the locked language-model prompt on the following rows: [list]. The prompt was locked first. Agreement between the language-model arm and chart review on those rows is therefore partly by construction, and comparisons between that arm and the other arms are reported with and without them.\"", "",

        "## N-07 · Registration (updates D-04)", "",
        "**Question.** D-04 asked whether to register publicly or rely on the git history. What has changed since September?", "",
        "**What has changed.**",
        f"- The language-model arm's GOLD_HOLDOUT answers are locked, with SHA-256 hashes in `docs/llm_gold_lock.md`, and the lock commit carries the annotated tag `llm-gold-lock-v1`, which is on the remote. A registration made now could cite the tag and the hashes ({n(lock['run_counts']['gold_admissions'])} admissions, {n(lock['run_counts']['distinct_units'])} units).",
        "- The repository is public, so a reader can already check the history.",
        "- The two rule tags, `note-phenotype-v1.0.0` and `note-phenotype-v1.1.0`, exist only on this machine. `git ls-remote --tags` shows one tag on the remote. D-04 cites those tags as part of the audit trail. This run did not push them, because it was told to push one tag.",
        "- The dev/test results of the language-model arm, the carry-over check and the four exploratory analyses of this run have been computed. A registration made now would post-date them and would have to say so.", "",
        "**Options and what each changes.** As in D-04 (register now; rely on the git history; register only what has not yet been run), with two additions.",
        "- *Any registration made now* can include the lock hashes and the tag, which gives the gold-standard comparison a third-party timestamp before adjudication starts.",
        "- *Under any option,* the two rule tags can be pushed so that the trail D-04 describes is visible on the remote, or left local and the manuscript's claim narrowed to what the remote shows.", "",
        "**Blocked until decided.** The manuscript's timing claims.", "",
        "**Draft amendment text.**",
        "- *Register now:* \"The analysis plan, the locked-prediction hashes of both model locks and the tag `llm-gold-lock-v1` were registered at [registry, identifier] on [date]. The registration post-dates the computable-stage results, the dev/test language-model results and the exploratory analyses of 10 November 2026, and says so.\"",
        "- *Git history only:* \"This study is not registered. Its timing claims rest on the public git history: rule tags, the pre-specification commit, the amendment commits and the lock tag.\"",
        "- *Register the unrun part:* \"The adjudication criteria, the estimator and the gold-standard comparison, with both lock hashes, were registered at [registry, identifier] on [date], before any chart was adjudicated. Everything computed before that date is described as preceding registration.\"", "",

        "## N-08 · What prospective reviewers are offered", "",
        "**Question.** What does the study offer a clinician who reviews charts? `docs/adjudication/reviewer_onepager.md` leaves this section empty.", "",
        "**Options.** Left blank for Kyle, as the run file instructs.", "",
        "**Blocked until decided.** Sending the one-pager to anyone.", "",
        "**Draft text.** None drafted.", "",

        "## N-09 · Material the push gate flags", "",
        "**Question.** The gate's note-text rule is a 30-character overlap with a dev/test extractor sentence. It flags two files this run was asked to commit, and it flags lines in documents that were already public when the run began. What is done with each?", "",
        "**What is known (counts only; no flagged line was read).**",
        f"- `{tfile}`: {n(hb.get(tfile, {}).get('lines_flagged', '—'))} lines flagged, longest overlap {n(hb.get(tfile, {}).get('longest_overlap_chars', '—'))} characters; "
        f"{n(hb.get(tfile, {}).get('whole_quoted_string_is_an_extractor_string', '—'))} quoted probe sentences equal a whole extractor string (`{R11}/held_back_files.json`).",
        f"- `{pfile}`: {n(hb.get(pfile, {}).get('lines_flagged', '—'))} lines flagged, longest overlap {n(hb.get(pfile, {}).get('longest_overlap_chars', '—'))} characters, none equal to a whole extractor string. The overlaps are inside the study's own criteria prose.",
        f"- Already public at the start of this run: {n(base['d3_sentence_windows']['lines_flagged'])} lines across {len(base['d3_sentence_windows']['per_file'])} files (`{R11}/base_exposure_audit.json`). "
        f"The file with the most is `{top[0]}`: {n(top[1].get('lines_flagged', '—'))} lines, of which {n(top[1].get('overlap_in_one_extractor_string', '—'))} overlap exactly one extractor string. No real identifier was found in any tracked file.",
        "- September's audit allowed short context windows around a keyword match and passed these documents. The rule in force now is stricter, and the repository has since become public.", "",
        "**Options and what each changes.**",
        "- *Review and replace.* Someone entitled to read the notes checks each flagged line against its matching sentence. Lines that are note text are replaced in a new commit. Git history keeps the old text unless history is rewritten, which this run's rules forbid and which would break the timestamps the audit trail relies on.",
        "- *Accept short overlaps as stock phrasing.* The gate's rule is relaxed for study-authored files by a stated criterion, for example an overlap that occurs in at least 11 extractor strings. The two held-back files may then pass or not, depending on the criterion; the counts needed to judge that are in the two results files.",
        "- *Keep the two files local and leave the public lines as they are.* Nothing changes. The README does not link the criteria proposal.",
        "- *Reword the two files.* The four criteria lines and the probe sentences are reworded until the gate passes, then committed. The probe set would no longer be the one the v1 prompt was timed on.", "",
        "**Blocked until decided.** The two files stay untracked. Whether any public document needs replacing.", "",
        "**Draft amendment text.** Not an analysis-plan matter. If the gate's rule is changed, the change belongs in the docstring of `scripts/run1110_push_gate.py` and in a dated line of the run log.", "",

        "## N-10 · The one-pager states the study question; the criteria say reviewers are not told it", "",
        "**Question.** The run file asked for a one-pager that gives the question and what the computable stage shows. `docs/adjudication_criteria.md` §10 says reviewers are told only that a computable phenotype for hepatic steatosis is being validated, and nothing more of the hypothesis. "
        "The one-pager as written tells a prospective reviewer that the study is about fatty liver being documented but not coded, and gives the uncoded share. Which document gives way?", "",
        "**What is known.** The page carries a notice at its top pointing here. The repository is public and its README states the purpose, so a reviewer who looks will find it either way.", "",
        "**Options and what each changes.**",
        "- *Keep the one-pager; revise §10.* Reviewers know the question. Blinding then covers code status, rule output, model output and cell membership, but not the hypothesis. The manuscript must say so.",
        "- *Cut the question and the computable-stage section from the page given to reviewers.* The page says what §10 allows. The fuller page can still be used for people who will not review, such as a department lead being asked for time.",
        "- *Keep both as they are and use the page only for non-reviewers.* A second, shorter page would be needed for reviewers.", "",
        "**Blocked until decided.** Sending the one-pager to a prospective reviewer.", "",
        "**Draft amendment text (criteria §10).**",
        "- *Revise §10:* \"Reviewers are told the study question. They are blinded to code status, to the output of the keyword rule and of every model, and to the stratum a chart was sampled from.\"",
        "- *Keep §10:* no change to the criteria; `docs/adjudication/reviewer_onepager.md` is regenerated without its first two sections for reviewers.", "",

        "## Decisions still open from September", "",
        f"From `{SEPT}`. Full text, options and stakes are there.", ""]
    L += sept_table()
    L += ["", "**D-01 is the one that blocks the start of adjudication.** N-06 and the clinician sign-off on the criteria block it as well."]
    open(OUT, "w").write("\n".join(L) + "\n")
    print("wrote", OUT, "| N-02:", "filled" if c else "[PENDING]")
    print(json.dumps(d1, indent=0)[:1800])


if __name__ == "__main__":
    main()
