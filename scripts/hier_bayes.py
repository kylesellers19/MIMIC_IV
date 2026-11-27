#!/usr/bin/env python3
"""Hierarchical Bayesian logistic stacking ("fusion") with a self-contained Hamiltonian Monte Carlo sampler.

NumPy only. Validated in tests/test_hier_bayes.py: finite-difference gradients (both forms), recovery of known
parameters with convergence checks, the maximum-likelihood answer in the single-group limit, partial pooling of a
small stratum, seed determinism, and the R-hat / ESS estimators on known chains.

Model, for admissions i in strata g[i] = 0..G-1 and base-model logits z_i1..z_iK (standardised):
    y_i     ~ Bernoulli(sigmoid(x_i . theta_g[i])),     x_i = [1, z_i1, ..., z_iK],  P = K + 1
    theta_gj ~ Normal(mu_j, tau_j)                       each stratum's intercept and weights
    mu_j    ~ Normal(prior_mu_j, prior_sd_j)             (defaults: 0; sd 5 for the intercept, 2.5 for each weight)
    tau_j   ~ Gamma(2, rate 1/tau_scale_j)               (default; scale 0.5: mode 0.5, mean 1), or Half-Normal(1)
A large stratum keeps its own weights; a small one borrows from the rest, by an amount tau that the data set.

Forms (parameterization):
  "marginal" (default)  mu is integrated out analytically: for each j, theta_.j ~ Normal(prior_mu_j 1,
      tau_j^2 I + prior_sd_j^2 11'). HMC samples (log tau, theta); mu is then drawn from its exact Gaussian conditional
      for every draw. This removes the mu-tau funnel that appears when every stratum is well identified by its data.
  "noncentered"  theta_g = mu + tau * eps_g, eps_g ~ Normal(0, I); HMC samples (mu, log tau, eps). Better when strata
      are small and the data say little about each one.
The Gamma(2) prior keeps tau off zero (Chung et al., Psychometrika 2013): with few strata tau is weakly identified,
and a prior with mass at zero adds a funnel that HMC cannot cross. With thousands of admissions per stratum, the
data rather than this prior set each stratum's weights.

Sampler: HMC; per chain, warm-up adapts the step size by dual averaging (target acceptance 0.9) and a dense mass
matrix from two warm-up windows (Stan-style regularisation); trajectory length ~ `trajectory` / step size, the step
jittered by +-10% after warm-up. Diagnostics: split R-hat and effective sample size (Geyer's initial monotone
sequence) for every sampled parameter and mu; divergent transitions per chain.
"""
import numpy as np


def expit(x):
    return np.exp(-np.logaddexp(0.0, -x))


class HierLogit:
    def __init__(self, X, y, g, n_groups, prior_mu=None, prior_sd=None, tau_prior="gamma", tau_scale=None,
                 parameterization="marginal"):
        X, y, g = np.asarray(X, float), np.asarray(y, float), np.asarray(g, int)
        if X.ndim != 2 or not (len(X) == len(y) == len(g)):
            raise ValueError("X must be n x P with one y and one group per row")
        if len(g) and (g.min() < 0 or g.max() >= n_groups):
            raise ValueError("group index out of range")
        if parameterization not in ("marginal", "noncentered"):
            raise ValueError("parameterization must be marginal or noncentered")
        if tau_prior not in ("gamma", "halfnormal"):
            raise ValueError("tau_prior must be gamma or halfnormal")
        self.X, self.y, self.g, self.G, self.P = X, y, g, int(n_groups), X.shape[1]
        self.form, self.tau_prior = parameterization, tau_prior
        P = self.P
        self.prior_mu = np.zeros(P) if prior_mu is None else np.asarray(prior_mu, float)
        self.prior_sd = np.r_[5.0, np.full(P - 1, 2.5)] if prior_sd is None else np.asarray(prior_sd, float)
        self.tau_scale = (np.full(P, 0.5 if tau_prior == "gamma" else 1.0) if tau_scale is None
                          else np.asarray(tau_scale, float))
        self.dim = (P if self.form == "marginal" else 2 * P) + self.G * P

    # ---- parameters ---------------------------------------------------------------------------------------------
    def unpack(self, q):
        """-> (mu or None, log tau, theta (marginal) or eps (noncentered)); q may be one vector or draws x dim."""
        P, G = self.P, self.G
        q = np.asarray(q)
        lead = q.shape[:-1]
        if self.form == "marginal":
            return None, q[..., :P], q[..., P:].reshape(*lead, G, P)
        return q[..., :P], q[..., P:2 * P], q[..., 2 * P:].reshape(*lead, G, P)

    def _tau_prior(self, lt):
        tau = np.exp(lt)
        if self.tau_prior == "gamma":           # density ~ tau exp(-tau/scale), plus the log-Jacobian of tau = e^lt
            return float(np.sum(2.0 * lt - tau / self.tau_scale)), 2.0 - tau / self.tau_scale
        return float(np.sum(lt - 0.5 * (tau / self.tau_scale) ** 2)), 1.0 - (tau / self.tau_scale) ** 2

    def _lik(self, th):
        eta = np.einsum("ij,ij->i", self.X, th[self.g])
        ll = float(np.sum(self.y * eta - np.logaddexp(0.0, eta)))
        S = self.X * (self.y - expit(eta))[:, None]
        g_th = np.stack([np.bincount(self.g, weights=S[:, k], minlength=self.G) for k in range(self.P)], axis=1)
        return ll, g_th

    # ---- log posterior and gradient -----------------------------------------------------------------------------
    def logp_grad(self, q):
        mu, lt, rest = self.unpack(q)
        if np.any(np.abs(lt) > 30):                      # tau outside exp(+-30): zero density, rejected
            return -np.inf, np.zeros_like(q)
        lp_tau, g_lt = self._tau_prior(lt)
        G = self.G
        if self.form == "marginal":
            th = rest
            ll, g_th = self._lik(th)
            t, s = np.exp(2.0 * lt), self.prior_sd ** 2
            d = th - self.prior_mu
            sum_d, ss = d.sum(0), (d * d).sum(0)
            den = t + G * s
            lp_th = -0.5 * ((G - 1) * np.log(t) + np.log(den)) - 0.5 * (ss / t - s * sum_d ** 2 / (t * den))
            g_prior = -(d - (s * sum_d / den)[None, :]) / t
            dlp_dt = (-0.5 * ((G - 1) / t + 1.0 / den) + 0.5 * ss / t ** 2
                      - 0.5 * s * sum_d ** 2 * (2.0 * t + G * s) / (t ** 2 * den ** 2))
            lp = ll + lp_tau + float(lp_th.sum())
            return lp, np.concatenate([g_lt + 2.0 * t * dlp_dt, (g_th + g_prior).ravel()])
        eps = rest
        tau = np.exp(lt)
        z = (mu - self.prior_mu) / self.prior_sd
        ll, g_th = self._lik(mu + tau * eps)
        lp = ll + lp_tau - 0.5 * float(z @ z) - 0.5 * float(np.sum(eps * eps))
        g_mu = g_th.sum(0) - z / self.prior_sd
        g_lt = g_lt + (g_th * eps).sum(0) * tau
        return lp, np.concatenate([g_mu, g_lt, (g_th * tau - eps).ravel()])

    # ---- start and derived draws --------------------------------------------------------------------------------
    def pooled_init(self, iters=50):
        """Penalised pooled logistic regression (IRLS); every stratum starts at the pooled fit, tau at 0.2."""
        b = self.prior_mu.copy()
        for _ in range(iters):
            p = expit(self.X @ b)
            w = p * (1 - p) + 1e-9
            H = self.X.T @ (self.X * w[:, None]) + np.diag(1 / self.prior_sd ** 2)
            step = np.linalg.solve(H, self.X.T @ (self.y - p) - (b - self.prior_mu) / self.prior_sd ** 2)
            b = b + step
            if np.max(np.abs(step)) < 1e-10:
                break
        lt = np.full(self.P, np.log(0.2))
        if self.form == "marginal":
            return np.concatenate([lt, np.tile(b, self.G)])
        return np.concatenate([b, lt, np.zeros(self.G * self.P)])

    def hyper(self, D, rng):
        """draws x dim -> (mu, tau, theta): draws x P, draws x P, draws x G x P. In the marginal form mu is drawn from
        its exact conditional Normal given theta and tau."""
        mu, lt, rest = self.unpack(D)
        tau = np.exp(lt)
        if self.form == "marginal":
            t, s = tau ** 2, self.prior_sd ** 2
            prec = self.G / t + 1.0 / s
            mean = (rest.sum(axis=1) / t + self.prior_mu / s) / prec
            mu = mean + rng.normal(size=mean.shape) / np.sqrt(prec)
            return mu, tau, rest
        return mu, tau, mu[:, None, :] + tau[:, None, :] * rest


# --- HMC
class _DualAveraging:
    def __init__(self, eps0, delta, gamma=0.05, t0=10.0, kappa=0.75):
        self.mu, self.delta, self.gamma, self.t0, self.kappa = np.log(10 * eps0), delta, gamma, t0, kappa
        self.hbar, self.log_bar, self.t = 0.0, np.log(eps0), 0

    def update(self, accept):
        self.t += 1
        t = self.t
        self.hbar = (1 - 1 / (t + self.t0)) * self.hbar + (self.delta - accept) / (t + self.t0)
        log_eps = self.mu - np.sqrt(t) / self.gamma * self.hbar
        w = t ** -self.kappa
        self.log_bar = w * log_eps + (1 - w) * self.log_bar
        return float(np.exp(log_eps))

    def final(self):
        return float(np.exp(self.log_bar))


class _Metric:
    """Kinetic energy 0.5 p' S p with S an estimate of the posterior covariance (dense), momentum p ~ N(0, S^-1)."""

    def __init__(self, cov):
        self.cov = cov
        self.chol = np.linalg.cholesky(cov)

    def draw(self, rng):
        return np.linalg.solve(self.chol.T, rng.normal(size=len(self.cov)))

    def velocity(self, p):
        return self.cov @ p

    def kinetic(self, p):
        return 0.5 * float(p @ self.cov @ p)


def _leapfrog_transition(model, q, lp, gr, eps, n_steps, metric, rng):
    p0 = metric.draw(rng)
    h0 = -lp + metric.kinetic(p0)
    qn, p = q.copy(), p0 + 0.5 * eps * gr
    lpn, gn = lp, gr
    for step in range(n_steps):
        qn = qn + eps * metric.velocity(p)
        lpn, gn = model.logp_grad(qn)
        if not np.isfinite(lpn) or not np.all(np.isfinite(gn)):
            return q, lp, gr, 0.0, True
        if step < n_steps - 1:
            p = p + eps * gn
    p = p + 0.5 * eps * gn
    dh = (-lpn + metric.kinetic(p)) - h0
    if not np.isfinite(dh):
        return q, lp, gr, 0.0, True
    accept = float(min(1.0, np.exp(-dh)))
    if rng.uniform() < accept:
        return qn, lpn, gn, accept, dh > 1000.0
    return q, lp, gr, accept, dh > 1000.0


def _initial_step(model, q, lp, gr, metric, rng, eps=0.1):
    """Hoffman & Gelman (2014), algorithm 4: double or halve the step until one-step acceptance crosses 0.5,
    kept within [1e-4, 5]."""
    _, _, _, a, _ = _leapfrog_transition(model, q, lp, gr, eps, 1, metric, rng)
    direction = 1.0 if a > 0.5 else -1.0
    for _ in range(40):
        eps_try = eps * (2.0 ** direction)
        if not 1e-4 <= eps_try <= 5.0:
            break
        _, _, _, a, _ = _leapfrog_transition(model, q, lp, gr, eps_try, 1, metric, rng)
        if (direction > 0 and a < 0.5) or (direction < 0 and a > 0.5):
            break
        eps = eps_try
    return eps


def _regularised_cov(window):
    w = np.asarray(window)
    k = len(w)
    return (k / (k + 5.0)) * np.cov(w, rowvar=False) + 1e-3 * (5.0 / (k + 5.0)) * np.eye(w.shape[1])


def sample(model, chains=4, warmup=1000, draws=1000, seed=0, target_accept=0.9, trajectory=1.5, max_leapfrog=256):
    """-> dict(draws: chains x draws x dim, mu: chains x draws x P, stats: per-chain step size, acceptance,
    divergences, leapfrog steps).

    Warm-up per chain: step size only in the first 15%; a dense covariance estimated from the draws in [15%, 40%),
    then again from [40%, 85%); step size alone in the last 15%. Dual averaging restarts after each update."""
    rng = np.random.default_rng(seed)
    q_start = model.pooled_init()
    out = np.empty((chains, draws, model.dim))
    stats = []
    windows = [(int(0.15 * warmup), int(0.40 * warmup)), (int(0.40 * warmup), int(0.85 * warmup))]
    for c in range(chains):
        q = q_start + rng.normal(0.0, 0.05, model.dim)
        lp, gr = model.logp_grad(q)
        metric = _Metric(np.eye(model.dim))
        eps = _initial_step(model, q, lp, gr, metric, rng)
        da = _DualAveraging(eps, target_accept)
        window, acc, div, steps = [], [], 0, []
        for it in range(warmup + draws):
            step = eps if it < warmup else eps * rng.uniform(0.9, 1.1)
            n_steps = int(np.clip(round(trajectory / step), 1, max_leapfrog))
            q, lp, gr, a, diverged = _leapfrog_transition(model, q, lp, gr, step, n_steps, metric, rng)
            if it < warmup:
                eps = da.update(a)
                if any(lo <= it < hi for lo, hi in windows):
                    window.append(q.copy())
                if any(it == hi - 1 for _, hi in windows) and len(window) > 2 * model.dim:
                    metric = _Metric(_regularised_cov(window))
                    window = []
                    eps = _initial_step(model, q, lp, gr, metric, rng)
                    da = _DualAveraging(eps, target_accept)
                if it == warmup - 1:
                    eps = da.final()
            else:
                out[c, it - warmup] = q
                acc.append(a)
                div += int(diverged)
                steps.append(n_steps)
        stats.append({"step_size": eps, "accept_mean": float(np.mean(acc)) if acc else None,
                      "divergences": div, "leapfrog_mean": float(np.mean(steps)) if steps else None})
    mu, _, _ = model.hyper(out.reshape(-1, model.dim), rng)
    return {"draws": out, "mu": mu.reshape(chains, draws, model.P), "stats": stats}


# --- diagnostics and summaries
def split_rhat(x):
    """x: chains x draws."""
    n = x.shape[1] // 2
    s = np.concatenate([x[:, :n], x[:, n:2 * n]], axis=0)
    w = s.var(axis=1, ddof=1).mean()
    b = n * s.mean(axis=1).var(ddof=1)
    var_plus = (n - 1) / n * w + b / n
    return float(np.sqrt(var_plus / w)) if w > 0 else float("nan")


def ess(x):
    """Effective sample size of x (chains x draws), Geyer's initial monotone sequence on the combined autocorrelation."""
    m, n = x.shape
    xc = x - x.mean(axis=1, keepdims=True)
    f = np.fft.rfft(xc, 2 * n, axis=1)
    acov = np.fft.irfft(f * np.conj(f), axis=1)[:, :n] / n
    w = (acov[:, 0] * n / (n - 1)).mean()
    var_plus = w * (n - 1) / n + (x.mean(axis=1).var(ddof=1) if m > 1 else 0.0)
    if var_plus <= 0:
        return float("nan")
    rho = 1.0 - (w - acov.mean(axis=0)) / var_plus
    rho[0] = 1.0
    pairs = []
    for k in range(0, n - 1, 2):
        s = rho[k] + rho[k + 1]
        if s <= 0:
            break
        pairs.append(s)
    pairs = np.minimum.accumulate(np.asarray(pairs)) if pairs else np.asarray([1.0])
    tau = -1.0 + 2.0 * pairs.sum()
    return float(m * n / max(tau, 1e-12))


def diagnostics(model, fit):
    cols = [fit["draws"][:, :, j] for j in range(model.dim)] + [fit["mu"][:, :, j] for j in range(model.P)]
    rh = np.array([split_rhat(x) for x in cols])
    es = np.array([ess(x) for x in cols])
    return {"rhat_max": float(np.nanmax(rh)), "ess_min": float(np.nanmin(es)),
            "divergences": int(sum(s["divergences"] for s in fit["stats"])), "chains": fit["stats"]}


def _flat(fit):
    return fit["draws"].reshape(-1, fit["draws"].shape[-1]), fit["mu"].reshape(-1, fit["mu"].shape[-1])


def _split(model, D, mu):
    _, lt, rest = model.unpack(D)
    tau = np.exp(lt)
    th = rest if model.form == "marginal" else mu[:, None, :] + tau[:, None, :] * rest
    return mu, tau, th


def summarize(model, fit, names=None):
    """Posterior mean, sd and 95% interval of mu, tau and every stratum's theta."""
    names = names or [f"x{j}" for j in range(model.P)]
    D, M = _flat(fit)
    mu, tau, th = _split(model, D, M)

    def s(v):
        return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)),
                "q2.5": float(np.percentile(v, 2.5)), "q97.5": float(np.percentile(v, 97.5))}
    return {"mu": {n: s(mu[:, j]) for j, n in enumerate(names)},
            "tau": {n: s(tau[:, j]) for j, n in enumerate(names)},
            "theta": [{n: s(th[:, g, j]) for j, n in enumerate(names)} for g in range(model.G)]}


def predict(model, fit, X, g, seed=0, chunk=500):
    """Posterior mean probability per row. A group index of -1 (a stratum unseen in fitting) draws a new stratum
    from the population: theta = mu + tau * N(0, I)."""
    X, g = np.asarray(X, float), np.asarray(g, int)
    D, M = _flat(fit)
    rng = np.random.default_rng(seed)
    total = np.zeros(len(X))
    for a in range(0, len(D), chunk):
        mu, tau, th = _split(model, D[a:a + chunk], M[a:a + chunk])       # th: draws x G x P
        new = mu + tau * rng.normal(size=mu.shape)
        th_rows = np.where((g >= 0)[None, :, None], th[:, np.clip(g, 0, None), :], new[:, None, :])
        total += expit(np.einsum("dnp,np->dn", th_rows, X)).sum(axis=0)
    return total / len(D)


# --- the pre-specified convergence policy
# The two forms are reparameterizations of one model: they target the same posterior and differ only in how well
# HMC moves through it, so choosing the form that converges does not change what is estimated.
CRITERIA = {"rhat_max": 1.01, "ess_min": 400.0, "divergences": 0}
ATTEMPTS = ({"form": "marginal", "target_accept": 0.9, "warmup": 1000},
            {"form": "noncentered", "target_accept": 0.9, "warmup": 1000},
            {"form": "marginal", "target_accept": 0.99, "warmup": 2000},
            {"form": "noncentered", "target_accept": 0.99, "warmup": 2000})


def converged(d):
    return (d["rhat_max"] <= CRITERIA["rhat_max"] and d["ess_min"] >= CRITERIA["ess_min"]
            and d["divergences"] <= CRITERIA["divergences"])


def fit_with_policy(make_model, seed=0, chains=4, draws=1000, attempts=ATTEMPTS):
    """make_model(form) -> HierLogit. Runs the attempts in order and stops at the first that meets CRITERIA.
    -> (model, fit, diagnostics, log, converged). A fit that never meets them comes back with converged=False;
    the caller must not evaluate it."""
    log = []
    for a in attempts:
        model = make_model(a["form"])
        fit = sample(model, chains=chains, warmup=a["warmup"], draws=draws, seed=seed, target_accept=a["target_accept"])
        d = diagnostics(model, fit)
        log.append({**a, "rhat_max": d["rhat_max"], "ess_min": d["ess_min"], "divergences": d["divergences"]})
        if converged(d):
            return model, fit, d, log, True
    return model, fit, d, log, False
