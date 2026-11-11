#!/usr/bin/env python3
"""2026-11-11 — amendment (p) to docs/analysis_plan_prespecified.md: decision N-01, classifier only.

Appends "§7 Amendment dated 2026-11-11" once. The amendment text is the "classifier only" draft of
docs/run_2026-11-10/DECISIONS_FOR_KYLE.md (N-01). What had already been seen is written from
docs/run_2026-11-10/results/decisions_inputs.json. No existing amendment or registry row is edited.
Run only after Kyle has confirmed the choice: the section records it as his decision.
"""
import json

PLAN = "docs/analysis_plan_prespecified.md"
INPUTS = "docs/run_2026-11-10/results/decisions_inputs.json"
DATE = "2026-11-11"


def main():
    s = open(PLAN).read()
    if "## 7. Amendment dated 2026-11-11" in s:
        print("already present"); return
    d = json.load(open(INPUTS))["n01"]
    mx, no = d["options"]["max_p"], d["options"]["noisy_or"]
    same = all(o[k] == 0 for o in (mx, no) for k in ("at_or_above_0_5_but_primary_negative", "below_0_5_but_primary_positive"))
    block = "\n".join([
        "", "## 7. Amendment dated 2026-11-11", "",
        "> *Decided by Kyle Sellers on 2026-11-11 (decision N-01 of `docs/run_2026-11-10/DECISIONS_FOR_KYLE.md`), on the recommendation of Claude Code, which drafted this text. "
        "No adjudication exists and no GOLD_HOLDOUT answer or probability had been looked at when it was committed.*", "",
        "- **(p) The language-model arm is evaluated as a classifier.** "
        f"The language-model arm is evaluated as a classifier under the admission rule of amendment (h). No admission-level probability is defined for it, and no metric that needs one is reported. Fixed on {DATE}, before any adjudication result was seen.",
        "  - **Reported against chart review:** the classification measures reported for the frozen keyword rule (sensitivity, specificity and predictive values, with the sampling weights).",
        "  - **Not reported for this arm:** AUROC, AUPRC, calibration, or any other measure that needs a score. The arm does not enter a stacked model as a probability.",
        "  - **Options not taken:** the maximum P(YES) over kept sentences with timing CURRENT or PAST, and a noisy-OR over those sentences.",
        f"  - **Already seen (dev/test only):** the distribution of both candidate scores on the {d['admissions']:,} admissions of the dev/test notes subsample (`{INPUTS}`). "
        + ("Cutting either score at 0.5 gave exactly the admission rule's labels. " if same else "")
        + f"The rank correlation between the two scores was {d['noisy_or_minus_max']['spearman']}. Of the {d['classifier_only']['primary_positive_admissions']:,} positive admissions, {mx['admissions_above_0_99']:,} had a maximum above 0.99.",
        "  - **Reason:** the first-token probabilities are close to 0 or 1, so a score would add almost nothing to the label, and a discrimination or calibration measure on it would not be comparable with the continuous model arms.",
        "  - **What it does not change:** no stored answer, label, lock or result. The three probabilities remain in the locked answers file.", ""])
    open(PLAN, "w").write(s.rstrip("\n") + "\n" + block)
    print("appended §7, amendment (p)")


if __name__ == "__main__":
    main()
