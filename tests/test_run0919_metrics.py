"""Tests for the shared metric and prior-correction maths used by Phases 7-9 (run_2026-09-19).

Pure numeric tests — no data files.
"""
import numpy as np
import pytest
from scripts.aim1b_evaluate_gold import wmetrics


def logit(p): return np.log(p / (1 - p))
def sigmoid(z): return 1 / (1 + np.exp(-z))


def corrected(p, w):
    """The analytic prior correction applied to a class-weighted model (Phases 7-9)."""
    return sigmoid(logit(p) - np.log(w))


def test_prior_correction_shifts_the_logit_by_minus_log_weight():
    p = np.array([0.1, 0.5, 0.9])
    w = 12.0
    assert np.allclose(logit(corrected(p, w)), logit(p) - np.log(w))


def test_prior_correction_lowers_predicted_risk_and_preserves_ranking():
    p = np.array([0.2, 0.4, 0.7])
    c = corrected(p, 12.0)
    assert np.all(c < p)
    assert np.all(np.diff(c) > 0)


def test_prior_correction_is_identity_at_weight_one():
    p = np.array([0.05, 0.5, 0.95])
    assert np.allclose(corrected(p, 1.0), p)


def test_weighted_metrics_recover_perfect_discrimination():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    m = wmetrics(y, p, np.ones(4))
    assert m["auroc"] == pytest.approx(1.0)
    assert m["n"] == 4 and m["pos"] == 2


def test_weighted_metrics_respect_weights():
    """Upweighting the misranked pair must reduce AUROC below the unweighted value."""
    y = np.array([0, 1, 1, 0])
    p = np.array([0.9, 0.8, 0.7, 0.1])
    flat = wmetrics(y, p, np.ones(4))["auroc"]
    heavy = wmetrics(y, p, np.array([50.0, 1.0, 1.0, 1.0]))["auroc"]
    assert heavy < flat


def test_calibration_slope_is_one_for_self_consistent_predictions():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 4000)
    y = (rng.uniform(size=4000) < p).astype(int)
    m = wmetrics(y, p, np.ones(4000))
    assert m["cal_slope"] == pytest.approx(1.0, abs=0.15)
    assert m["cal_intercept"] == pytest.approx(0.0, abs=0.15)


def test_calibration_intercept_detects_systematic_overprediction():
    rng = np.random.default_rng(1)
    truth = rng.uniform(0.05, 0.6, 4000)
    y = (rng.uniform(size=4000) < truth).astype(int)
    inflated = sigmoid(logit(truth) + 1.0)          # every prediction shifted up by one logit
    m = wmetrics(y, inflated, np.ones(4000))
    assert m["cal_intercept"] < -0.5                 # offset model pulls the predictions back down
