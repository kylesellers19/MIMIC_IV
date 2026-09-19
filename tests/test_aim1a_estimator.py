"""Unit tests for scripts/aim1a_estimator.py — hand-checked targets with the locked weights.

No credentialed data: a synthetic master key with the same structure is written to a temp dir.
"""
import numpy as np
import pandas as pd
import pytest

from scripts import aim1a_estimator as E

W = {"code+/note+": 62.8375, "code-/note+": 151.9933, "code+/note-": 10.1857, "code-/note-": 3454.53}
NPOP = {"code+/note+": 5027, "code-/note+": 22799, "code+/note-": 713, "code-/note-": 345453}
NS = {"code+/note+": 80, "code-/note+": 150, "code+/note-": 70, "code-/note-": 100}
HAND = {"code+/note+": {"n": 80, "x": 76, "ins": 0}, "code-/note+": {"n": 150, "x": 128, "ins": 0},
        "code+/note-": {"n": 70, "x": 35, "ins": 0}, "code-/note-": {"n": 100, "x": 1, "ins": 0}}


def test_hand_targets():
    est = E.point_estimates(HAND, W)
    assert round(100 * est["under_capture"], 3) == 81.698
    assert round(100 * est["ppv"], 2) == 87.08
    assert round(100 * est["sensitivity"], 3) == 86.409


def test_insufficient_two_ways():
    c = {k: dict(v) for k, v in HAND.items()}
    c["code-/note-"] = {"n": 100, "x": 1, "ins": 20}
    ex = E.point_estimates(c, W, "exclude")
    ng = E.point_estimates(c, W, "negative")
    assert ex["under_capture"] > ng["under_capture"]          # excluding raises p_D from 1/100 to 1/80
    assert round(100 * ng["under_capture"], 3) == 81.698        # counted negative == hand target (x_D still 1 of 100)


def test_bootstrap_and_linearized_agree():
    fe = E.full_estimate(HAND, W, reps=4000, seed=1)
    for q in ("under_capture", "ppv", "sensitivity"):
        b = fe[q]["bootstrap_ci_pct"]
        assert b[0] <= fe[q]["estimate_pct"] <= b[1]
        # bootstrap SD and linearized SE agree (same binomial variance model)
        assert abs(fe[q]["bootstrap_sd_pct"] - fe[q]["linearized_se_pct"]) / fe[q]["linearized_se_pct"] < 0.10
        lo, hi = fe[q]["linearized_logit_ci_pct"]
        assert 0 <= lo <= fe[q]["estimate_pct"] <= hi <= 100
    # under-capture with x_D = 1/100: percentile and normal interval widths within 25%
    b, l = fe["under_capture"]["bootstrap_ci_pct"], fe["under_capture"]["linearized_ci_pct"]
    assert abs((b[1] - b[0]) - (l[1] - l[0])) / (l[1] - l[0]) < 0.25
    # a better-populated cell D (x_D = 5): all three intervals agree in width within 15%
    c5 = {k: dict(v) for k, v in HAND.items()}; c5["code-/note-"] = {"n": 100, "x": 5, "ins": 0}
    fe5 = E.full_estimate(c5, W, reps=4000, seed=2)
    for q in ("under_capture", "ppv", "sensitivity"):
        b, l = fe5[q]["bootstrap_ci_pct"], fe5[q]["linearized_ci_pct"]
        assert abs((b[1] - b[0]) - (l[1] - l[0])) / (l[1] - l[0]) < 0.15
    share = fe["under_capture"]["linearized_variance_share"]
    assert abs(sum(share.values()) - 1) < 1e-9
    assert share["D"] > 0.5   # the single positive in D dominates the interval


def test_simulation_reference_row():
    """PPV_B = 0.85, A = 0.95, C = 0.50, D in {0,1,2,3,5}/100: mean of 2,000 simulated adjudications
    must match the closed form 79.06, 81.65, 83.67, 85.28, 87.72 within Monte-Carlo error."""
    rng = np.random.default_rng(20260924)
    ref = {0: 79.06, 1: 81.65, 2: 83.67, 3: 85.28, 5: 87.72}
    for d, target in ref.items():
        p = {"code+/note+": 0.95, "code-/note+": 0.85, "code+/note-": 0.50, "code-/note-": d / 100}
        closed = 100 * sum(NPOP[c] * p[c] for c in E.CODE_NEG) / sum(NPOP[c] * p[c] for c in E.CELLS)
        assert round(closed, 2) == target
        ests = []
        for _ in range(2000):
            cts = {c: {"n": NS[c], "x": int(rng.binomial(NS[c], p[c])), "ins": 0} for c in E.CELLS}
            ests.append(100 * E.point_estimates(cts, W)["under_capture"])
        ests = np.array(ests)
        mc_se = ests.std(ddof=1) / np.sqrt(len(ests))
        # The estimator is concave in x_D (each D positive stands for ~3,455 admissions), so its expectation
        # sits a little BELOW the plug-in closed form (Jensen). The simulated mean must match the exact
        # expectation within MC error, and the closed form within that bias (< 0.6 pp here).
        exact = E.exact_expectation(p, NS, NPOP)["under_capture_pct"]
        assert abs(ests.mean() - exact) < 4 * mc_se, (d, ests.mean(), exact, mc_se)
        assert exact <= target + 1e-9 and target - exact < 0.6, (d, exact, target)


def test_cohen_kappa_known_values():
    a = ["pos"] * 25 + ["neg"] * 25
    b = ["pos"] * 20 + ["neg"] * 5 + ["pos"] * 10 + ["neg"] * 15
    assert round(E.cohen_kappa(a, b, ["pos", "neg"]), 6) == 0.4
    assert E.cohen_kappa(a, a, ["pos", "neg"]) == 1.0
    o = E.ORDINAL
    r1 = [o[0]] * 10 + [o[1]] * 10 + [o[2]] * 10 + [o[3]] * 10
    assert E.cohen_kappa(r1, r1, o, "linear") == 1.0
    assert E.cohen_kappa(r1, r1, o, "quadratic") == 1.0
    # quadratic weights penalise a 3-step disagreement 9x a 1-step one, so the shifted rater scores lower under linear
    r2 = [o[1]] * 10 + [o[2]] * 10 + [o[3]] * 10 + [o[0]] * 10
    assert E.cohen_kappa(r1, r2, o, "quadratic") < E.cohen_kappa(r1, r1, o, "quadratic")


def _synthetic_key(tmp_path):
    rows = []
    i = 0
    for c in E.CELLS:
        for _ in range(NS[c]):
            i += 1
            rows.append((f"R{i:04d}", 30000000 + i, 40000000 + i, c, False, W[c]))
    key = pd.DataFrame(rows, columns=["review_id", "hadm_id", "subject_id", "cell", "double_review", "weight"])
    p = tmp_path / "key.parquet"
    key.to_parquet(p)
    return key, str(p)


def test_end_to_end_run_with_synthetic_forms(tmp_path):
    key, kp = _synthetic_key(tmp_path)
    # reviewer 1 adjudicates everything with the hand-target positives per cell; reviewer 2 re-reviews the first
    # 10 of each cell and agrees except on one chart in cell B (binary disagreement -> unresolved -> excluded)
    resp = []
    for c in E.CELLS:
        ids = key[key.cell == c].review_id.tolist()
        x = HAND[c]["x"]
        resp += [(rid, "Definite" if k < x else "Absent") for k, rid in enumerate(ids)]
    f1 = pd.DataFrame(resp, columns=["review_id", "primary_response"]); f1["reviewer_initials"] = "AA"
    second = []
    for c in E.CELLS:
        ids = key[key.cell == c].review_id.tolist()[:10]
        for k, rid in enumerate(ids):
            r = f1.loc[f1.review_id == rid, "primary_response"].iloc[0]
            if c == "code-/note+" and k == 0:
                r = "Absent"
            second.append((rid, r))
    f2 = pd.DataFrame(second, columns=["review_id", "primary_response"]); f2["reviewer_initials"] = "BB"
    p1, p2 = tmp_path / "f1.csv", tmp_path / "f2.csv"
    f1.to_csv(p1, index=False); f2.to_csv(p2, index=False)
    res = E.run([str(p1), str(p2)], master_key=kp, reps=200, seed=3)
    assert res["resolution"]["resolved"] == 399 and res["resolution"]["unresolved_excluded"] == 1
    assert res["agreement"]["n_double_reviewed_pairs"] == 40
    assert res["agreement"]["kappa_binary_insufficient_excluded"] < 1.0
    # with a resolution file the disagreement is settled and the hand target is recovered exactly
    rp = tmp_path / "res.csv"
    pd.DataFrame([(f2.review_id.iloc[10], "Definite")], columns=["review_id", "primary_response"]).to_csv(rp, index=False)
    res2 = E.run([str(p1), str(p2)], resolution_path=str(rp), master_key=kp, reps=200, seed=3)
    assert res2["resolution"]["unresolved_excluded"] == 0
    assert round(res2["estimates"]["insufficient_excluded"]["under_capture"]["estimate_pct"], 3) == 81.698
    # the output contains no hadm_id / subject_id values anywhere
    import json
    txt = json.dumps(res2, default=float)
    assert not any(str(v) in txt for v in key.hadm_id.tolist() + key.subject_id.tolist())
    # small-count rule
    assert res2["counts_by_cell"]["D"]["x"] == "<11"
