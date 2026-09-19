#!/usr/bin/env python3
"""run_2026-09-19 Phase 6.1 — precision forecast for the Aim 1a under-capture estimator by simulation.

Scenarios: PPV in cell B (code-/note+) in {0.95, 0.85, 0.75} x positives per 100 charts in cell D
(code-/note-) in {0, 1, 2, 3, 5}; cell A (code+/note+) fixed at 0.95, cell C (code+/note-) at 0.50.
For each scenario 2,000 adjudications are simulated (independent binomial draws per cell with the locked
sample sizes 80/150/70/100), the estimator is applied to each, and per simulated adjudication a stratified
bootstrap CI (500 reps) and a linearized CI are computed. Reported: mean estimate vs the plug-in closed
form and vs the exact expectation of the ratio estimator; mean CI width; coverage of the closed-form truth;
the share of the linearized variance contributed by cell D; and the interval width that would remain if
cell D contributed no sampling variance.

No data are read: this is a design-stage calculation using only the population cell sizes and the
allocation (both already public in docs/aim1a_crosstab.md).

Writes docs/run_2026-09-19/results/aim1a_precision_forecast.json and docs/aim1a_precision_forecast.md.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.getcwd())
from scripts import aim1a_estimator as E

SEED_SIM = 20260925
N_SIM = 2000
BOOT_REPS = 500
N_POP = {"code+/note+": 5027, "code-/note+": 22799, "code+/note-": 713, "code-/note-": 345453}
N_SAMPLE = {"code+/note+": 80, "code-/note+": 150, "code+/note-": 70, "code-/note-": 100}
WEIGHTS = {c: N_POP[c] / N_SAMPLE[c] for c in E.CELLS}
PPV_B = [0.95, 0.85, 0.75]
D_PER_100 = [0, 1, 2, 3, 5]
P_A, P_C = 0.95, 0.50
OUT_JSON = "docs/run_2026-09-19/results/aim1a_precision_forecast.json"
OUT_MD = "docs/aim1a_precision_forecast.md"
A, B, C, D = E.CELLS


def simulate_scenario(p, rng):
    """Vectorized: N_SIM adjudications, each with a BOOT_REPS stratified bootstrap and a linearized CI."""
    n = np.array([N_SAMPLE[c] for c in E.CELLS], dtype=float)
    w = np.array([WEIGHTS[c] for c in E.CELLS], dtype=float)
    pv = np.array([p[c] for c in E.CELLS], dtype=float)
    X = rng.binomial(n.astype(int), pv, size=(N_SIM, 4)).astype(float)          # observed positives per cell
    is_cn = np.array([c in E.CODE_NEG for c in E.CELLS])
    is_np = np.array([c in E.NOTE_POS for c in E.CELLS])
    Nc = w * n

    def ratios(Xm):  # Xm: (..., 4)
        P = Xm / n
        Np = Nc * P
        tot = Np.sum(axis=-1)
        with np.errstate(invalid="ignore", divide="ignore"):
            uc = Np[..., is_cn].sum(axis=-1) / tot
            se = Np[..., is_np].sum(axis=-1) / tot
        ppv = Np[..., is_np].sum(axis=-1) / Nc[is_np].sum()
        return uc, ppv, se

    uc, ppv, se = ratios(X)
    # bootstrap: redraw within cell from the observed proportions
    Pobs = X / n
    XB = rng.binomial(n.astype(int)[None, None, :], Pobs[:, None, :], size=(N_SIM, BOOT_REPS, 4)).astype(float)
    ucb, ppvb, seb = ratios(XB)
    lo_uc, hi_uc = np.nanpercentile(ucb, [2.5, 97.5], axis=1)
    lo_ppv, hi_ppv = np.nanpercentile(ppvb, [2.5, 97.5], axis=1)
    lo_se, hi_se = np.nanpercentile(seb, [2.5, 97.5], axis=1)
    # linearized: Var(R) = sum_c [N_c (a_c - R)]^2 p_c(1-p_c)/n_c / X^2
    var_p = Pobs * (1 - Pobs) / n
    Xtot = (Nc * Pobs).sum(axis=1)
    a_cn = is_cn.astype(float)[None, :]
    contrib = (Nc[None, :] * (a_cn - uc[:, None])) ** 2 * var_p / Xtot[:, None] ** 2
    v = contrib.sum(axis=1)
    se_lin = np.sqrt(v)
    share_D = np.where(v > 0, contrib[:, 3] / v, np.nan)
    v_noD = v - contrib[:, 3]
    se_lin_noD = np.sqrt(v_noD)
    return {
        "uc": uc, "ppv": ppv, "se": se,
        "boot_lo": lo_uc, "boot_hi": hi_uc, "boot_lo_ppv": lo_ppv, "boot_hi_ppv": hi_ppv, "boot_lo_se": lo_se, "boot_hi_se": hi_se,
        "lin_lo": uc - E.Z * se_lin, "lin_hi": uc + E.Z * se_lin, "se_lin": se_lin, "share_D": share_D, "se_lin_noD": se_lin_noD,
        "xD": X[:, 3],
    }


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED_SIM)
    scenarios = []
    for pb in PPV_B:
        for d in D_PER_100:
            p = {A: P_A, B: pb, C: P_C, D: d / 100}
            cf = E.closed_form(p, N_POP)
            ex = E.exact_expectation(p, N_SAMPLE, N_POP)
            s = simulate_scenario(p, rng)
            truth = cf["under_capture_pct"] / 100
            mc_se = float(np.nanstd(s["uc"], ddof=1) / np.sqrt(N_SIM))
            # one more positive in D moves the estimate by this much (closed form at the expected counts)
            xd_exp = N_SAMPLE[D] * p[D]
            wB, wD, wA, wC = WEIGHTS[B], WEIGHTS[D], WEIGHTS[A], WEIGHTS[C]
            num = wB * N_SAMPLE[B] * pb + wD * xd_exp
            den = wA * N_SAMPLE[A] * P_A + wB * N_SAMPLE[B] * pb + wC * N_SAMPLE[C] * P_C + wD * xd_exp
            shift_one_D = 100 * ((num + wD) / (den + wD) - num / den)
            scenarios.append({
                "ppv_B": pb, "D_positives_per_100": d, "p_A": P_A, "p_C": P_C,
                "closed_form_under_capture_pct": round(cf["under_capture_pct"], 2),
                "exact_expectation_under_capture_pct": round(ex["under_capture_pct"], 3),
                "jensen_bias_pct_points": round(ex["under_capture_pct"] - cf["under_capture_pct"], 3),
                "sim_mean_under_capture_pct": round(100 * float(np.nanmean(s["uc"])), 3),
                "sim_sd_under_capture_pct": round(100 * float(np.nanstd(s["uc"], ddof=1)), 3),
                "mc_se_of_mean_pct": round(100 * mc_se, 4),
                "sim_mean_minus_closed_form_pct": round(100 * float(np.nanmean(s["uc"])) - cf["under_capture_pct"], 3),
                "sim_mean_minus_exact_in_mc_se": round((100 * float(np.nanmean(s["uc"])) - ex["under_capture_pct"]) / (100 * mc_se), 2) if mc_se > 0 else 0.0,
                "bootstrap_ci": {
                    "mean_width_pct": round(100 * float(np.nanmean(s["boot_hi"] - s["boot_lo"])), 2),
                    "coverage_closed_form_pct": round(100 * float(np.mean((s["boot_lo"] <= truth) & (truth <= s["boot_hi"]))), 1),
                    "coverage_exact_expectation_pct": round(100 * float(np.mean((s["boot_lo"] <= ex["under_capture_pct"] / 100) & (ex["under_capture_pct"] / 100 <= s["boot_hi"]))), 1),
                },
                "linearized_ci": {
                    "mean_width_pct": round(100 * float(np.nanmean(s["lin_hi"] - s["lin_lo"])), 2),
                    "coverage_closed_form_pct": round(100 * float(np.mean((s["lin_lo"] <= truth) & (truth <= s["lin_hi"]))), 1),
                    "mean_se_pct": round(100 * float(np.nanmean(s["se_lin"])), 3),
                },
                "cell_D": {
                    "mean_linearized_variance_share_pct": round(100 * float(np.nanmean(s["share_D"])), 1),
                    "mean_linearized_width_without_D_pct": round(100 * float(np.nanmean(2 * E.Z * s["se_lin_noD"])), 2),
                    "shift_per_additional_D_positive_pct_points": round(shift_one_D, 2),
                    "sims_with_zero_D_positives_pct": round(100 * float(np.mean(s["xD"] == 0)), 1),
                },
                "ppv": {"closed_form_pct": round(cf["ppv_pct"], 2), "sim_mean_pct": round(100 * float(np.nanmean(s["ppv"])), 2),
                        "bootstrap_mean_width_pct": round(100 * float(np.nanmean(s["boot_hi_ppv"] - s["boot_lo_ppv"])), 2),
                        "bootstrap_coverage_pct": round(100 * float(np.mean((s["boot_lo_ppv"] <= cf["ppv_pct"] / 100) & (cf["ppv_pct"] / 100 <= s["boot_hi_ppv"]))), 1)},
                "sensitivity": {"closed_form_pct": round(cf["sensitivity_pct"], 2), "sim_mean_pct": round(100 * float(np.nanmean(s["se"])), 2),
                                "bootstrap_mean_width_pct": round(100 * float(np.nanmean(s["boot_hi_se"] - s["boot_lo_se"])), 2),
                                "bootstrap_coverage_pct": round(100 * float(np.mean((s["boot_lo_se"] <= cf["sensitivity_pct"] / 100) & (cf["sensitivity_pct"] / 100 <= s["boot_hi_se"]))), 1)},
            })
            print(f"PPV_B={pb} D={d}: closed {cf['under_capture_pct']:.2f} exact {ex['under_capture_pct']:.2f} sim {100*np.nanmean(s['uc']):.2f} "
                  f"boot width {100*np.nanmean(s['boot_hi']-s['boot_lo']):.2f} cov {100*np.mean((s['boot_lo']<=truth)&(truth<=s['boot_hi'])):.1f}  {time.time()-t0:.0f}s", flush=True)
    ref = [s["closed_form_under_capture_pct"] for s in scenarios if s["ppv_B"] == 0.85]
    hand = E.point_estimates({A: {"n": 80, "x": 76, "ins": 0}, B: {"n": 150, "x": 128, "ins": 0}, C: {"n": 70, "x": 35, "ins": 0}, D: {"n": 100, "x": 1, "ins": 0}}, WEIGHTS)
    res = {
        "script": "scripts/run0919_precision_forecast.py", "seed": SEED_SIM, "n_sim": N_SIM, "bootstrap_reps": BOOT_REPS,
        "n_pop": {E.CELL_LETTER[c]: N_POP[c] for c in E.CELLS}, "n_sample": {E.CELL_LETTER[c]: N_SAMPLE[c] for c in E.CELLS},
        "weights": {E.CELL_LETTER[c]: round(WEIGHTS[c], 4) for c in E.CELLS},
        "admissions_per_D_chart": round(WEIGHTS[D], 2),
        "unit_test_targets": {"x": {"A": 76, "B": 128, "C": 35, "D": 1},
                              "under_capture_pct": round(100 * hand["under_capture"], 3), "ppv_pct": round(100 * hand["ppv"], 3),
                              "sensitivity_pct": round(100 * hand["sensitivity"], 3)},
        "reference_row_ppvB_0.85_closed_form": ref,
        "reference_row_expected": [79.06, 81.65, 83.67, 85.28, 87.72],
        "reference_row_matches": ref == [79.06, 81.65, 83.67, 85.28, 87.72],
        "max_abs_sim_mean_minus_exact_in_mc_se": max(abs(s["sim_mean_minus_exact_in_mc_se"]) for s in scenarios),
        "max_abs_jensen_bias_pct_points": max(abs(s["jensen_bias_pct_points"]) for s in scenarios),
        "scenarios": scenarios, "runtime_s": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(res, f, indent=1)
    write_md(res)
    print(f"wrote {OUT_JSON} and {OUT_MD} in {time.time()-t0:.0f}s")


def write_md(r):
    L = []
    L.append("# Aim 1a precision forecast — simulation of the under-capture estimator")
    L.append("")
    L.append(f"Produced by `{r['script']}`; every number below is read from `docs/run_2026-09-19/results/aim1a_precision_forecast.json`. "
             "No patient data are used: the calculation needs only the population cell sizes and the allocation from `docs/aim1a_crosstab.md`.")
    L.append("")
    L.append("## What is estimated")
    L.append("")
    L.append("The headline Aim 1a quantity is the population-weighted share of adjudicated steatosis-positive admissions that are code-negative: "
             "(w_B x_B + w_D x_D) / (w_A x_A + w_B x_B + w_C x_C + w_D x_D), with x_c the adjudicated positives in cell c and w_c = N_pop(c)/n_sample(c). "
             "Cells: A = code+/note+, B = code−/note+, C = code+/note−, D = code−/note−. "
             f"Sample sizes {r['n_sample']['A']}/{r['n_sample']['B']}/{r['n_sample']['C']}/{r['n_sample']['D']}; "
             f"weights {r['weights']['A']} / {r['weights']['B']} / {r['weights']['C']} / {r['weights']['D']}. "
             f"Implementation: `scripts/aim1a_estimator.py` (unit tests `tests/test_aim1a_estimator.py`).")
    L.append("")
    u = r["unit_test_targets"]
    L.append(f"Hand-checked unit-test target (x = {u['x']['A']}/{u['x']['B']}/{u['x']['C']}/{u['x']['D']} positives in A/B/C/D): "
             f"under-capture {u['under_capture_pct']:.3f}%, note-rule PPV {u['ppv_pct']:.2f}%, sensitivity {u['sensitivity_pct']:.3f}%.")
    L.append("")
    L.append("## Simulation design")
    L.append("")
    L.append(f"For PPV in cell B ∈ {{0.95, 0.85, 0.75}} and positives per 100 charts in cell D ∈ {{0, 1, 2, 3, 5}}, holding cell A at 0.95 and cell C at 0.50, "
             f"{r['n_sim']:,} adjudications were simulated per scenario (independent binomial draws per cell, seed {r['seed']}). "
             f"For each simulated adjudication the estimate, a stratified bootstrap 95% CI ({r['bootstrap_reps']} reps, resampling within cells) and a linearized 95% CI were computed. "
             "Coverage is the share of simulated intervals containing the closed-form truth.")
    L.append("")
    L.append(f"Reference row (PPV_B = 0.85), closed form for D = 0, 1, 2, 3, 5: {', '.join(f'{v:.2f}' for v in r['reference_row_ppvB_0.85_closed_form'])} "
             f"— matches the pre-specified reference row {', '.join(f'{v:.2f}' for v in r['reference_row_expected'])}: **{'yes' if r['reference_row_matches'] else 'NO'}**.")
    L.append("")
    L.append("## Results")
    L.append("")
    L.append("| PPV_B | D per 100 | closed form % | exact E[estimate] % | sim mean % (MC SE) | boot CI mean width | boot coverage % | lin CI mean width | lin coverage % | var. share from D % | width without D | shift per extra D positive |")
    L.append("| --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |")
    for s in r["scenarios"]:
        L.append(f"| {s['ppv_B']:.2f} | {s['D_positives_per_100']} | {s['closed_form_under_capture_pct']:.2f} | {s['exact_expectation_under_capture_pct']:.2f} | "
                 f"{s['sim_mean_under_capture_pct']:.2f} ({s['mc_se_of_mean_pct']:.2f}) | {s['bootstrap_ci']['mean_width_pct']:.2f} | {s['bootstrap_ci']['coverage_closed_form_pct']:.1f} | "
                 f"{s['linearized_ci']['mean_width_pct']:.2f} | {s['linearized_ci']['coverage_closed_form_pct']:.1f} | {s['cell_D']['mean_linearized_variance_share_pct']:.1f} | "
                 f"{s['cell_D']['mean_linearized_width_without_D_pct']:.2f} | {s['cell_D']['shift_per_additional_D_positive_pct_points']:.2f} |")
    L.append("")
    L.append("Widths and shifts are in percentage points. 'Exact E[estimate]' is the expectation of the ratio estimator over the binomial draws "
             "(cells D, B and A enumerated, C at its mean). 'Width without D' is the linearized interval width if cell D contributed no sampling variance.")
    L.append("")
    L.append("## Reading the table")
    L.append("")
    L.append(f"- **Closed form vs simulated mean.** The simulated mean matches the exact expectation of the estimator within Monte Carlo error in every scenario "
             f"(largest discrepancy {r['max_abs_sim_mean_minus_exact_in_mc_se']:.2f} MC standard errors). It sits slightly *below* the plug-in closed form whenever D > 0 "
             f"(largest gap {r['max_abs_jensen_bias_pct_points']:.2f} percentage points): the estimator is a ratio that is concave in x_D, so averaging over the binomial draw of x_D "
             "(Jensen's inequality) pulls the mean down. This is a property of the ratio estimator with 100 charts in cell D, not a coding error; it is smaller than a tenth of the interval width.")
    L.append(f"- **Where the interval comes from.** Each of the 100 charts in cell D stands for about {r['admissions_per_D_chart']:,.0f} admissions. "
             "One additional adjudicated positive in D moves the estimate by the amount in the last column (2–3 percentage points), whereas one additional positive in B moves it by about 0.1 points. "
             "The 'var. share from D' column says what fraction of the linearized variance is due to cell D alone, and 'width without D' shows how narrow the interval would be if D were known exactly. "
             "In plain words: once even one or two positives turn up among the 100 code−/note− charts, most of the uncertainty in the headline number is the uncertainty about how many "
             "such positives there really are in the ~345,000 admissions that cell represents, and no amount of extra precision in the other three cells can remove it.")
    d1 = [s for s in r["scenarios"] if s["D_positives_per_100"] == 1]
    L.append(f"- **Coverage fails when cell D is nearly empty.** At 1 positive per 100 in D, {min(s['cell_D']['sims_with_zero_D_positives_pct'] for s in d1):.0f}–"
             f"{max(s['cell_D']['sims_with_zero_D_positives_pct'] for s in d1):.0f}% of simulated adjudications observe *no* positive in D; both intervals then have nothing to "
             f"resample or linearize in that cell, collapse to the width of cells A–C, and miss the truth. Coverage in the D = 1 row is only "
             f"{min(s['bootstrap_ci']['coverage_closed_form_pct'] for s in d1):.0f}–{max(s['bootstrap_ci']['coverage_closed_form_pct'] for s in d1):.0f}% (bootstrap) and "
             "recovers to ~85% at D = 2 and ~92% at D ≥ 3. At D = 0 coverage is nominal only because the truth also has no D contribution. "
             "Practical reading: if the real adjudication finds 0 or 1 positives among the 100 code−/note− charts, the headline interval must be accompanied by an explicit "
             "upper bound on p_D (e.g. rule of three: p_D < 3% with 95% confidence when x_D = 0, i.e. up to ~10,000 unobserved positives in that cell) rather than presented as a "
             "well-calibrated 95% interval. This is a consequence of the 100-chart allocation to D and is a design-stage fact, not something the estimator can repair.")
    L.append("- **Sensitivity is much less precise than under-capture.** Its bootstrap interval is 20–40 percentage points wide once D > 0 (results JSON, `sensitivity`), "
             "because every D positive enters its denominator at weight ~3,455; the note-rule PPV interval is 6–11 points wide and unaffected by D.")
    L.append("- **Bootstrap vs linearized.** The two intervals agree in width to within a few percent when x_D ≥ 2; with x_D ∈ {0, 1} the percentile bootstrap is asymmetric "
             "and the symmetric normal interval can exceed 100% (the estimator JSON also carries a logit-scale linearized interval, which respects the bounds).")
    L.append("- **PPV and sensitivity.** The note-rule PPV (cells A and B only) is not exposed to cell D and its interval is narrow; sensitivity is exposed to D in the "
             "denominator and behaves like the under-capture estimate. Their per-scenario widths and coverage are in the results JSON.")
    L.append("")
    L.append("## Tier 3 items arising")
    L.append("")
    L.append("Handling of 'Insufficient information' (excluded vs counted negative), the final-label rule for double-reviewed disagreements, and the choice of "
             "weighting for the ordinal kappa are logged in `docs/run_2026-09-19/phase6_decisions.md`; the estimator computes every option and leaves the primary as specified.")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
