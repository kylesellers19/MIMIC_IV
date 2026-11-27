"""The hierarchical Bayesian fusion's model and sampler (scripts/hier_bayes.py) on simulated data only."""
import numpy as np
import pytest
import statsmodels.api as sm

from scripts import hier_bayes as HB


def simulate(sizes, mu=(-2.5, 0.8, 1.2), tau=(0.4, 0.3, 0.3), seed=1):
    rng = np.random.default_rng(seed)
    G = len(sizes)
    theta = np.asarray(mu) + np.asarray(tau) * rng.normal(size=(G, 3))
    g = np.repeat(np.arange(G), sizes)
    X = np.column_stack([np.ones(len(g)), rng.normal(size=(len(g), 2))])
    y = (rng.uniform(size=len(g)) < HB.expit(np.einsum("ij,ij->i", X, theta[g]))).astype(float)
    return X, y, g, theta


@pytest.mark.parametrize("form", ["marginal", "noncentered"])
def test_gradient_matches_finite_differences(form):
    X, y, g, _ = simulate([300, 200, 100])
    m = HB.HierLogit(X, y, g, 3, parameterization=form, tau_prior="gamma" if form == "marginal" else "halfnormal")
    q = np.random.default_rng(0).normal(0, 0.3, m.dim)
    _, grad = m.logp_grad(q)
    h = 1e-6
    num = np.array([(m.logp_grad(q + h * e)[0] - m.logp_grad(q - h * e)[0]) / (2 * h) for e in np.eye(m.dim)])
    assert np.allclose(grad, num, rtol=1e-4, atol=1e-4)


@pytest.fixture(scope="module")
def recovery():
    X, y, g, theta = simulate([4000, 3000, 2000, 1000])
    m = HB.HierLogit(X, y, g, 4)
    fit = HB.sample(m, chains=4, warmup=500, draws=500, seed=7)
    return m, fit, theta


def test_policy_reaches_the_criteria():
    """The pre-specified policy (forms and acceptance targets in order) stops at the first attempt that meets every
    criterion; on this simulated case it must get there, and the fit it returns must meet them."""
    X, y, g, _ = simulate([1500, 1000, 800, 500], seed=9)
    model, fit, d, log, ok = HB.fit_with_policy(lambda form: HB.HierLogit(X, y, g, 4, parameterization=form), seed=3)
    assert ok, log
    assert HB.converged(d) and d["rhat_max"] <= 1.01 and d["ess_min"] >= 400 and d["divergences"] == 0
    assert log[-1]["form"] == model.form and len(log) <= len(HB.ATTEMPTS)


def test_recovers_each_stratum(recovery):
    m, fit, theta = recovery
    s = HB.summarize(m, fit, ["a", "b1", "b2"])
    for gi in range(4):
        for j, k in enumerate(["a", "b1", "b2"]):
            est = s["theta"][gi][k]
            assert abs(est["mean"] - theta[gi, j]) < 4 * est["sd"] + 0.02, (gi, k, est, theta[gi, j])


def test_single_group_matches_maximum_likelihood():
    X, y, g, _ = simulate([8000], tau=(0.0, 0.0, 0.0), seed=3)
    m = HB.HierLogit(X, y, g, 1, prior_sd=[100.0, 100.0, 100.0])
    fit = HB.sample(m, chains=2, warmup=400, draws=400, seed=1)
    mle = sm.Logit(y, X).fit(disp=0).params
    post = HB.summarize(m, fit)["theta"][0]
    assert np.allclose([post[f"x{j}"]["mean"] for j in range(3)], mle, atol=0.03)


def test_small_stratum_is_pulled_toward_the_population():
    """Three large strata share one set of weights; a fourth, of 400 admissions, has a larger notes weight. Its
    estimate must land between its own maximum-likelihood fit and the population value."""
    rng = np.random.default_rng(5)
    sizes = [6000, 6000, 6000, 400]
    theta = np.array([[-2.0, 0.8, 1.0]] * 3 + [[-2.0, 0.8, 2.2]])
    g = np.repeat(np.arange(4), sizes)
    X = np.column_stack([np.ones(len(g)), rng.normal(size=(len(g), 2))])
    y = (rng.uniform(size=len(g)) < HB.expit(np.einsum("ij,ij->i", X, theta[g]))).astype(float)
    m = HB.HierLogit(X, y, g, 4)
    fit = HB.sample(m, chains=2, warmup=500, draws=500, seed=2)
    s = HB.summarize(m, fit)
    own = sm.Logit(y[g == 3], X[g == 3]).fit(disp=0).params[2]
    post, mu = s["theta"][3]["x2"]["mean"], s["mu"]["x2"]["mean"]
    assert min(own, mu) < post < max(own, mu), (own, post, mu)


def test_predictions_and_unseen_stratum(recovery):
    m, fit, theta = recovery
    X, y, g, _ = simulate([2000, 2000, 2000, 2000], seed=11)
    p = HB.predict(m, fit, X, g)
    assert np.all((p > 0) & (p < 1))
    base = y.mean()
    ll = lambda q: -np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))
    assert ll(p) < ll(np.full_like(p, base))
    p_new = HB.predict(m, fit, X[:50], np.full(50, -1))
    assert np.all((p_new > 0) & (p_new < 1))


def test_same_seed_same_draws():
    X, y, g, _ = simulate([500, 300])
    m = HB.HierLogit(X, y, g, 2)
    a = HB.sample(m, chains=1, warmup=100, draws=50, seed=4)["draws"]
    b = HB.sample(m, chains=1, warmup=100, draws=50, seed=4)["draws"]
    assert np.array_equal(a, b)


def test_rhat_and_ess_on_known_chains():
    rng = np.random.default_rng(0)
    iid = rng.normal(size=(4, 1000))
    assert abs(HB.split_rhat(iid) - 1) < 0.01 and 3000 < HB.ess(iid) < 5000
    stuck = iid + np.arange(4)[:, None] * 3.0
    assert HB.split_rhat(stuck) > 1.5
