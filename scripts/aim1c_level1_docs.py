#!/usr/bin/env python3
"""Write docs/aim1c_level1.md and docs/tables/aim1c_level1_<variable>.md from the published (suppressed)
Aim 1c level 1 results. Called by scripts/run0919_aim1c_level1.py after it computes the results, and by
scripts/run1111_public_counts.py to re-render from the stored results without recomputing them."""
import os

from scripts.public_counts import FLOOR, cell

INTRO = [
    "# Aim 1c, level 1 — equity of recovery at the computable stage (run_2026-09-19)\n",
    "Produced by `scripts/run0919_aim1c_level1.py`; every number is read from `docs/run_2026-09-19/results/aim1c_level1.json`. Pre-specification: `docs/analysis_plan_prespecified.md` (H1c; amendment g). Definition (b), v1.1.0, −365/+30 outpatient window.\n",
    "**What is measured.** Recovery share = B ÷ (A + B): among note-positive admissions, the share with no MASLD code. Corroboration share = A ÷ (A + C): among code-positive admissions, the share whose notes also document steatosis. Both are computable-stage quantities about *documentation and coding*, not adjudicated disease. 95% CIs are subject-cluster bootstraps "
    "({reps} replicates; a subject's admissions are resampled together because one person can contribute several). Floors: no recovery share where B < {floor}; no corroboration share where A + C < {floor}; such strata are declared non-analyzable, not merged. A CI wider than {wide:.0f} percentage points is marked as too wide to support a claim (an analyst threshold, stated here so it can be argued with). No p-values. The SMD column is the one-versus-rest standardized difference in the coding rate among note-positive admissions (A ÷ (A + B)), a descriptive contrast.\n",
    "**Small counts.** Counts from 1 to 10 appear as <11. Where a stratum's n or a column's overall total would give such a count back by subtraction, a second cell is shown as *withheld*, and shares computed from a hidden cell are *withheld* too (`scripts/public_counts.py`).\n",
    "Levels 2 and 3 of the audit (weighted PPV by stratum against the gold standard; model calibration by stratum) require the adjudication and the models and are not attempted here.\n",
    "UNKNOWN, UNABLE TO OBTAIN and PATIENT DECLINED TO ANSWER are reported but are **encounter characteristics, not population groups** (marked †). Ages ≥ 89 are recoded to 91 in MIMIC-IV, so the 89+ band is an aggregate.\n"]


def fmt(v):
    return "—" if v is None else (f"{v}" if not isinstance(v, list) else f"{v[0]}–{v[1]}")


def size(r):
    """Sort key: the stratum n (published or not, the order is the same as by n)."""
    n = r["mech"]["n"]
    return n if isinstance(n, int) else 0


def share_cells(r, pct, ci, width, claim):
    held = r.get("withheld", [])
    if pct in held:
        return ["withheld"] * 4
    if r.get(pct) is None:
        return ["not analyzable", "", "", ""]
    return [fmt(r[pct]), fmt(r.get(ci)), fmt(r.get(width)), "yes" if r.get(claim) else "no — too wide"]


def block(var, rows):
    name = lambda r: f"{r['stratum']}{' †' if r['encounter_characteristic'] else ''}"
    L = [f"## By {var}\n", "Cell counts first:\n",
         f"| {var} | A code+/note+ | B code−/note+ | C code+/note− | D code−/note− |", "| --- | --: | --: | --: | --: |"]
    for r in sorted(rows, key=lambda x: -size(x)):
        L.append(f"| {name(r)} | {cell(r['A'])} | {cell(r['B'])} | {cell(r['C'])} | {cell(r['D'])} |")
    L += ["", "Shares (analyzable strata only):\n",
          f"| {var} | recovery share % | 95% CI | width | claim supported? | corroboration share % | 95% CI | width | claim supported? | SMD coding rate vs rest | recovery share, 571.9 removed % (CI) |",
          "| --- | --: | --- | --: | --- | --: | --- | --: | --- | --: | --- |"]
    for r in sorted(rows, key=lambda x: -size(x)):
        held = r.get("withheld", [])
        rec = share_cells(r, "recovery_share_pct", "rec_ci", "rec_ci_width", "rec_claim_supported")
        cor = share_cells(r, "corroboration_share_pct", "cor_ci", "cor_ci_width", "cor_claim_supported")
        if rec[0] == cor[0] == "not analyzable":
            L.append(f"| {name(r)} | not analyzable | | | | not analyzable | | | | | |")
            continue
        smd = "withheld" if "smd_coding_rate_vs_rest" in held else fmt(r.get("smd_coding_rate_vs_rest"))
        alt = "withheld" if "recovery_share_no5719_pct" in held else f"{fmt(r.get('recovery_share_no5719_pct'))} ({fmt(r.get('rec_no5719_ci'))})"
        L.append(f"| {name(r)} | " + " | ".join(rec + cor + [smd, alt]) + " |")
    L += ["", "Mechanism measures (all admissions in the stratum):\n",
          f"| {var} | n | ALT available % | HbA1c available % | triglycerides available % | HDL available % | liver-inclusive imaging in window % | CMRF unascertainable (all five) % |",
          "| --- | --: | --: | --: | --: | --: | --: | --: |"]
    for r in sorted(rows, key=lambda x: -size(x)):
        mm = r["mech"]
        L.append(f"| {r['stratum']} | {cell(mm['n'])} | {mm['ALT_avail_pct']} | {mm['HbA1c_avail_pct']} | {mm['TG_avail_pct']} | {mm['HDL_avail_pct']} | {mm['liver_imaging_in_window_pct']} | {mm['cmrf_unascertainable_all_pct']} |")
    return L + [""]


def write(res):
    """res: the published results (scripts/public_counts.aim1c_public)."""
    os.makedirs("docs/tables", exist_ok=True)
    L = [INTRO[0], INTRO[1], INTRO[2].format(reps=res["reps"], floor=FLOOR, wide=res["wide_ci_threshold_pp"]), *INTRO[3:]]
    for var, rows in res["strata"].items():
        b = block(var, rows)
        L += b
        with open(f"docs/tables/aim1c_level1_{var}.md", "w") as fh:
            fh.write(f"# Aim 1c level 1 — by {var} (run_2026-09-19)\n\nSource: `docs/run_2026-09-19/results/aim1c_level1.json`. "
                     "Counts from 1 to 10 appear as <11; *withheld* cells and shares would otherwise give one back by subtraction.\n\n"
                     + "\n".join(b) + "\n")
    g = res["gee_exploratory"]
    L += ["## EXPLORATORY adjusted model (GEE) — among note-positive admissions, outcome = code-positive\n",
          f"**Exploratory.** Covariates fixed before fitting (amendment g): race, insurance, sex, age band, admission type, ICD version of the admission, note source (discharge / inpatient radiology / outpatient radiology). GEE with a binomial link, exchangeable working correlation, clustered on subject. Diagnosis count and laboratory availability are deliberately not adjusted for: they are the proposed mechanism. Fit: {g.get('note', g.get('full_model_error', 'failed'))}; n = {g.get('n')}. Reference levels: {g.get('reference_levels')}.\n"]
    if "terms" in g:
        L += ["| term | adjusted OR | 95% CI |", "| --- | --: | --- |"]
        for t in g["terms"]:
            L.append(f"| {t['term']} | {t['aOR']} | {t['ci_lo']}–{t['ci_hi']} |")
    else:
        L.append(f"Model did not fit: {g}")
    L += ["", "*Exploratory adjusted odds ratios describe association in the computable data; they are not estimates of adjudicated under-coding by group.*"]
    open("docs/aim1c_level1.md", "w").write("\n".join(L) + "\n")
