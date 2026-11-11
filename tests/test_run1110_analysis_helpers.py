"""Helpers behind the 10 November analyses: small-cell masking, secondary suppression, the subject-cluster
bootstrap, FIB-4, and the carry-over check's published shares. Synthetic inputs only; no test reads data/."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.getcwd())
from scripts import run1110_common as C
from scripts import run1110_diagnostics_json as DJ


# ----------------------------------------------------------------------------- run1110_common
def test_mask_hides_one_to_ten_and_nothing_else():
    assert [C.mask(v) for v in (0, 1, 10, 11, 250)] == [0, "<11", "<11", 11, 250]


def test_share_is_not_reported_below_the_floor():
    s = C.share(3, 9)
    assert s["reported"] is False and s["n"] == "<11" and "pct" not in s


def test_share_withholds_the_percentage_when_numerator_or_complement_is_small():
    low, high = C.share(4, 200), C.share(195, 200)
    assert low["pct"] == "withheld" and low["x"] == "<11"
    assert high["pct"] == "withheld" and high["x"] == "withheld"        # 200 - 195 = 5 would be recoverable
    ok = C.share(50, 200, ci=[20.0, 30.0])
    assert ok == {"n": 200, "x": 50, "pct": 25.0, "reported": True, "ci95": [20.0, 30.0]}
    assert C.share(0, 200)["pct"] == 0.0                                 # zero is not a small cell


def test_protect_partition_rounds_a_second_stratum_when_one_is_masked():
    out = C.protect_partition({"a": 5000, "b": 1234, "c": 3})
    assert out["c"] == "<11" and out["b"] == "~1,200" and out["a"] == 5000
    assert C.protect_partition({"a": 5000, "b": 1234, "c": 0}) == {"a": 5000, "b": 1234, "c": 0}


def test_med_iqr_needs_eleven_values():
    assert C.med_iqr(np.arange(10.0)) is None
    assert C.med_iqr(np.arange(11.0)) == {"median": 5.0, "q1": 2.5, "q3": 7.5}


def test_wilson_interval_is_in_percent_and_bounded():
    lo, hi = C.wilson(0, 50)
    assert lo == 0.0 and 0 < hi < 10
    lo, hi = C.wilson(50, 50)
    assert hi == 100.0 and 90 < lo < 100


def test_bootstrap_resamples_subjects_not_admissions_and_is_reproducible():
    subj = np.repeat(np.arange(200), 3)                                  # three admissions per subject
    rng = np.random.default_rng(1)
    flag_by_subject = rng.random(200) < 0.3
    num = np.repeat(flag_by_subject, 3)                                  # perfectly clustered outcome
    den = np.ones(len(subj), dtype=bool)
    a, b = C.Boot(subj, reps=300, seed=7).ratio_ci(num, den), C.Boot(subj, reps=300, seed=7).ratio_ci(num, den)
    assert a == b                                                        # same seed, same interval
    naive = C.Boot(np.arange(len(subj)), reps=300, seed=7).ratio_ci(num, den)   # pretends admissions are independent
    assert (a[1] - a[0]) > (naive[1] - naive[0])                         # clustering widens the interval
    point = 100 * num.mean()
    assert a[0] < point < a[1]


# ----------------------------------------------------------------------------- diagnostics suppression
def test_suppress_masks_small_cells_and_blocks_recovery_from_row_and_column_totals():
    table = {"r1": {"YES": 4, "NO": 40, "UNCLEAR": 56, "All": 100},
             "r2": {"YES": 30, "NO": 50, "UNCLEAR": 20, "All": 100},
             "All": {"YES": 34, "NO": 90, "UNCLEAR": 76, "All": 200}}
    out, masked, held = DJ.suppress(table)
    assert out["r1"]["YES"] == "<11" and masked == 1
    # along row r1 a second cell must go, or 100 - 40 - 56 gives the 4 back
    assert sum(1 for c in ("YES", "NO", "UNCLEAR") if isinstance(out["r1"][c], str)) >= 2
    # down column YES the total 34 and r2's 30 would give it back too
    assert isinstance(out["r2"]["YES"], str) or isinstance(out["All"]["YES"], str)
    assert held >= 2


def test_suppress_leaves_a_table_without_small_cells_alone():
    table = {"r1": {"YES": 20, "NO": 80, "All": 100}, "All": {"YES": 20, "NO": 80, "All": 100}}
    out, masked, held = DJ.suppress(table)
    assert (masked, held) == (0, 0) and out["r1"] == {"YES": 20, "NO": 80, "All": 100}


# ----------------------------------------------------------------------------- FIB-4
def test_fib4_formula_and_computability():
    from scripts.run1110_fib4_by_cell import fib4
    age = pd.Series([50.0, 50.0, 50.0, 50.0])
    ast = pd.Series([40.0, 40.0, np.nan, 40.0])
    alt = pd.Series([25.0, 0.0, 25.0, 25.0])
    plt_ = pd.Series([200.0, 200.0, 200.0, 0.0])
    f = fib4(age, ast, alt, plt_)
    assert f.iloc[0] == pytest.approx(50 * 40 / (200 * 5))               # = 2.0
    assert f.iloc[1:].isna().all()                                       # ALT of zero, missing AST, platelets of zero


# ----------------------------------------------------------------------------- carry-over check
def test_carryover_share_publishes_an_upper_bound_for_small_counts():
    from scripts import run1110_carryover_check as K
    small = K.share(3, 1500)
    assert small["x"] == "<11" and small["pct"].startswith("under") and "wilson_hi_pct_at_10" in small
    assert "3" not in str(small["pct"]).replace("0.73", "")              # nothing that pins the count down
    zero, big = K.share(0, 1500), K.share(30, 1500)
    assert zero["x"] == 0 and zero["pct"] == 0.0 and zero["wilson_hi_pct"] > 0
    assert big["x"] == 30 and big["pct"] == 2.0


def test_carryover_weighted_share_is_an_upper_bound_when_a_stratum_is_masked():
    from scripts import run1110_carryover_check as K
    exact = K.weighted([(30, 1500, 2000), (15, 1500, 80000)])
    assert isinstance(exact["pct"], float) and exact["wilson_lo_pct"] < exact["pct"] < exact["wilson_hi_pct"]
    masked = K.weighted([(30, 1500, 2000), (3, 1500, 80000)])
    assert str(masked["pct"]).startswith("at most") and "wilson_lo_pct" not in masked
    same_at_ten = K.weighted([(30, 1500, 2000), (10, 1500, 80000)])
    assert masked == same_at_ten                                         # 3 and 10 are indistinguishable in the output
