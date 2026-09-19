#!/usr/bin/env python3
"""Aim 1a estimator — inverse-probability-weighted under-capture from a completed adjudication file.

Input: one or more reviewer forms (the schema of docs/adjudication/data_dictionary.md; CSV or the
'sample' sheet of an .xlsx), joined INSIDE this script to the master key (review_id -> cell, weight).
Output: aggregates only (JSON + optional Markdown). No patient-level row is ever printed or written.

Quantities
  under-capture  = (w_B x_B + w_D x_D) / (w_A x_A + w_B x_B + w_C x_C + w_D x_D)
  note-rule PPV  = (w_A x_A + w_B x_B) / (w_A n_A + w_B n_B)                     (cells A and B)
  sensitivity    = (w_A x_A + w_B x_B) / (w_A x_A + w_B x_B + w_C x_C + w_D x_D)  (all four cells)
where x_c = adjudicated positives (Definite + Probable by default) and n_c = adjudicated charts in cell c.
Written more generally as N_c p_c with N_c = w_c n_c (the population size of the cell) and p_c the
positive proportion, so that "Insufficient information" can be handled two ways: EXCLUDED
(p_c = x_c / (n_c - ins_c)) or counted NEGATIVE (p_c = x_c / n_c). Both are always computed and reported.

Uncertainty: stratified bootstrap (resampling within cells — implemented as a multinomial redraw of the
per-cell (positive, negative, insufficient) counts, which is exactly what resampling rows within a cell
with replacement produces for these statistics) and a linearized (delta-method) stratified variance for
the ratio, reported side by side as a cross-check.

Agreement: Cohen's kappa on the collapsed binary outcome and weighted kappa (linear and quadratic) on the
four ordinal levels, on PRE-CONSENSUS responses from the double-reviewed charts (review_ids with two
reviewer rows).

Final label per chart: a row in --resolution (if given) wins; else a single reviewer row; else two rows
that agree on the collapsed binary outcome; else the chart is UNRESOLVED and excluded (counted).

Usage
  scripts/run0919_env.sh scripts/aim1a_estimator.py --adjudication form1.xlsx --adjudication form2.xlsx \
      [--resolution resolved.csv] [--strata strata.parquet --group-col gender] --out results.json [--md summary.md]
"""
import argparse
import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())

MASTER_KEY = "data/processed/aim1a_sample.parquet"
CELLS = ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]
CELL_LETTER = {"code+/note+": "A", "code-/note+": "B", "code+/note-": "C", "code-/note-": "D"}
CODE_NEG = ("code-/note+", "code-/note-")
NOTE_POS = ("code+/note+", "code-/note+")
ORDINAL = ["Definite", "Probable", "Possible", "Absent"]
INSUFFICIENT = "Insufficient information"
RESPONSES = ORDINAL + [INSUFFICIENT]
POSITIVE_LEVELS = ("Definite", "Probable")
BOOTSTRAP_REPS = 500
SEED_BOOTSTRAP = 20260923
Z = 1.959963984540054
SMALL_CELL = 11          # reporting floor for tracked artifacts
MIN_STRATUM_N = 11       # a stratum estimate is reported only if it has >= this many adjudicated charts


# ----------------------------------------------------------------------------------------------
# Core arithmetic on per-cell counts (pure functions; used by the tests and the simulation)
# ----------------------------------------------------------------------------------------------
def cell_proportions(counts, insufficient="exclude"):
    """counts: {cell: {"n": adjudicated, "x": positives, "ins": insufficient}} -> {cell: p_c, n_eff}."""
    out = {}
    for c in CELLS:
        d = counts.get(c, {"n": 0, "x": 0, "ins": 0})
        n, x, ins = int(d["n"]), int(d["x"]), int(d.get("ins", 0))
        n_eff = n - ins if insufficient == "exclude" else n
        p = (x / n_eff) if n_eff > 0 else float("nan")
        out[c] = {"p": p, "n_eff": n_eff, "n": n, "x": x, "ins": ins}
    return out


def point_estimates(counts, weights, insufficient="exclude"):
    """Return under_capture, ppv, sensitivity (as proportions) from per-cell counts and weights."""
    pr = cell_proportions(counts, insufficient)
    N = {c: weights[c] * pr[c]["n"] for c in CELLS}
    Np = {c: N[c] * pr[c]["p"] if pr[c]["n_eff"] > 0 else 0.0 for c in CELLS}
    total_pos = sum(Np[c] for c in CELLS)
    codeneg_pos = sum(Np[c] for c in CODE_NEG)
    notepos_pos = sum(Np[c] for c in NOTE_POS)
    notepos_N = sum(N[c] for c in NOTE_POS)
    return {
        "under_capture": codeneg_pos / total_pos if total_pos > 0 else float("nan"),
        "ppv": notepos_pos / notepos_N if notepos_N > 0 else float("nan"),
        "sensitivity": notepos_pos / total_pos if total_pos > 0 else float("nan"),
    }


def linearized_se(counts, weights, insufficient="exclude"):
    """Delta-method SE for the three ratios, with each cell's share of the variance.

    R = Y/X with Y = sum_c a_c N_c p_c, X = sum_c N_c p_c (a_c = 1 for the numerator cells).
    dR = sum_c N_c (a_c - R) dp_c / X  =>  Var(R) = sum_c [N_c (a_c - R)]^2 Var(p_c) / X^2,
    Var(p_c) = p_c (1 - p_c) / n_eff_c (binomial within cell; no finite-population correction).
    PPV has a fixed denominator: Var = sum_{A,B} N_c^2 Var(p_c) / (sum_{A,B} N_c)^2.
    """
    pr = cell_proportions(counts, insufficient)
    est = point_estimates(counts, weights, insufficient)
    N = {c: weights[c] * pr[c]["n"] for c in CELLS}
    var_p = {c: (pr[c]["p"] * (1 - pr[c]["p"]) / pr[c]["n_eff"]) if pr[c]["n_eff"] > 0 else 0.0 for c in CELLS}
    X = sum(N[c] * pr[c]["p"] for c in CELLS if pr[c]["n_eff"] > 0)
    out = {}
    NN = sum(N[c] for c in NOTE_POS)
    if not (X > 0) or not (NN > 0):   # nothing adjudicated yet
        return {k: {"se": float("nan"), "variance_share": {c: 0.0 for c in CELLS}} for k in ("under_capture", "sensitivity", "ppv")}
    for name, num_cells in (("under_capture", CODE_NEG), ("sensitivity", NOTE_POS)):
        R = est[name]
        contrib = {c: (N[c] * ((1.0 if c in num_cells else 0.0) - R)) ** 2 * var_p[c] / (X ** 2) for c in CELLS}
        v = sum(contrib.values())
        out[name] = {"se": float(np.sqrt(v)), "variance_share": {c: (contrib[c] / v if v > 0 else 0.0) for c in CELLS}}
    contrib = {c: (N[c] ** 2 * var_p[c] / NN ** 2) if c in NOTE_POS else 0.0 for c in CELLS}
    v = sum(contrib.values())
    out["ppv"] = {"se": float(np.sqrt(v)), "variance_share": {c: (contrib[c] / v if v > 0 else 0.0) for c in CELLS}}
    return out


def bootstrap_counts(counts, weights, reps=BOOTSTRAP_REPS, seed=SEED_BOOTSTRAP, insufficient="exclude", rng=None):
    """Stratified bootstrap: within each cell redraw (positive, negative, insufficient) as a multinomial
    of size n_c with the observed proportions. Returns arrays (reps,) for each statistic."""
    rng = rng if rng is not None else np.random.default_rng(seed)
    draws = {}
    for c in CELLS:
        d = counts.get(c, {"n": 0, "x": 0, "ins": 0})
        n, x, ins = int(d["n"]), int(d["x"]), int(d.get("ins", 0))
        if n == 0:
            draws[c] = np.zeros((reps, 3), dtype=int)
            continue
        probs = np.array([x, n - x - ins, ins], dtype=float) / n
        draws[c] = rng.multinomial(n, probs, size=reps)
    res = {"under_capture": np.empty(reps), "ppv": np.empty(reps), "sensitivity": np.empty(reps)}
    # vectorized version of point_estimates
    N = np.array([weights[c] * counts.get(c, {"n": 0})["n"] for c in CELLS], dtype=float)
    X = np.stack([draws[c][:, 0] for c in CELLS], axis=1).astype(float)
    INS = np.stack([draws[c][:, 2] for c in CELLS], axis=1).astype(float)
    n_eff = np.array([counts.get(c, {"n": 0})["n"] for c in CELLS], dtype=float)[None, :] - (INS if insufficient == "exclude" else 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        P = np.where(n_eff > 0, X / n_eff, 0.0)
    Np = N[None, :] * P
    is_codeneg = np.array([c in CODE_NEG for c in CELLS])
    is_notepos = np.array([c in NOTE_POS for c in CELLS])
    tot = Np.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        res["under_capture"] = Np[:, is_codeneg].sum(axis=1) / tot
        res["sensitivity"] = Np[:, is_notepos].sum(axis=1) / tot
        res["ppv"] = Np[:, is_notepos].sum(axis=1) / N[is_notepos].sum()
    return res


def percentile_ci(arr, alpha=0.05):
    a = np.asarray(arr, dtype=float)
    a = a[~np.isnan(a)]
    if a.size == 0:
        return [float("nan"), float("nan")]
    return [float(np.percentile(a, 100 * alpha / 2)), float(np.percentile(a, 100 * (1 - alpha / 2)))]


def wilson(x, n, z=Z):
    if n == 0:
        return [float("nan"), float("nan")]
    p = x / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [float(centre - half), float(centre + half)]


def logit_ci(p, se, z=Z):
    """Normal CI on the logit scale (delta method), mapped back; respects the [0, 1] bounds."""
    if not (0 < p < 1) or se == 0:
        return [p, p]
    lo, hi = np.log(p / (1 - p)) - z * se / (p * (1 - p)), np.log(p / (1 - p)) + z * se / (p * (1 - p))
    return [float(1 / (1 + np.exp(-lo))), float(1 / (1 + np.exp(-hi)))]


def full_estimate(counts, weights, reps=BOOTSTRAP_REPS, seed=SEED_BOOTSTRAP, insufficient="exclude"):
    """Point estimates + bootstrap percentile CI + linearized normal CI, all as percentages."""
    est = point_estimates(counts, weights, insufficient)
    lin = linearized_se(counts, weights, insufficient)
    boot = bootstrap_counts(counts, weights, reps=reps, seed=seed, insufficient=insufficient)
    out = {}
    for k in ("under_capture", "ppv", "sensitivity"):
        se = lin[k]["se"]
        out[k] = {
            "estimate_pct": 100 * est[k],
            "bootstrap_ci_pct": [100 * v for v in percentile_ci(boot[k])],
            "bootstrap_sd_pct": 100 * float(np.nanstd(boot[k], ddof=1)) if reps > 1 else float("nan"),
            "linearized_se_pct": 100 * se,
            "linearized_ci_pct": [100 * (est[k] - Z * se), 100 * (est[k] + Z * se)],
            "linearized_logit_ci_pct": [100 * v for v in logit_ci(est[k], se)],
            "linearized_variance_share": {CELL_LETTER[c]: lin[k]["variance_share"][c] for c in CELLS},
        }
    out["bootstrap_reps"] = reps
    out["bootstrap_seed"] = seed
    out["insufficient_handling"] = insufficient
    return out


# ----------------------------------------------------------------------------------------------
# Agreement
# ----------------------------------------------------------------------------------------------
def cohen_kappa(a, b, categories, weights=None):
    """Cohen's kappa for paired ratings a, b over `categories` (ordered). weights: None | 'linear' | 'quadratic'."""
    k = len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    a = [idx[v] for v in a]
    b = [idx[v] for v in b]
    n = len(a)
    if n == 0:
        return float("nan")
    O = np.zeros((k, k))
    for i, j in zip(a, b):
        O[i, j] += 1
    O /= n
    E = np.outer(O.sum(axis=1), O.sum(axis=0))
    ii, jj = np.meshgrid(np.arange(k), np.arange(k), indexing="ij")
    if weights is None:
        W = (ii != jj).astype(float)
    elif weights == "linear":
        W = np.abs(ii - jj) / (k - 1)
    elif weights == "quadratic":
        W = ((ii - jj) ** 2) / ((k - 1) ** 2)
    else:
        raise ValueError(weights)
    den = (W * E).sum()
    if den == 0:
        return float("nan")
    return float(1 - (W * O).sum() / den)


# ----------------------------------------------------------------------------------------------
# Adjudication-file handling (patient-level rows stay inside these functions)
# ----------------------------------------------------------------------------------------------
SCHEMA = ["review_id", "primary_response", "temporality", "q6a_cardiometabolic", "q6b_alcohol",
          "q6c_other_cause", "q6c_specify", "rationale", "negation_override", "minutes_spent", "reviewer_initials"]


def read_form(path, sheet="sample"):
    if path.lower().endswith((".xlsx", ".xlsm")):
        df = pd.read_excel(path, sheet_name=sheet, dtype=str)
    elif path.lower().endswith(".parquet"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, dtype=str)
    missing = [c for c in ("review_id", "primary_response") if c not in df.columns]
    if missing:
        raise SystemExit(f"adjudication file lacks columns {missing}")
    df = df.copy()
    for c in SCHEMA:
        if c not in df.columns:
            df[c] = None
    df["review_id"] = df["review_id"].astype(str).str.strip()
    df["primary_response"] = df["primary_response"].where(df["primary_response"].notna(), None)
    df["primary_response"] = df["primary_response"].map(lambda v: str(v).strip() if v is not None and str(v).strip() != "" and str(v) != "nan" else None)
    return df


def collapse(resp, positive_levels=POSITIVE_LEVELS):
    """'pos' / 'neg' / 'ins' / None."""
    if resp is None:
        return None
    if resp == INSUFFICIENT:
        return "ins"
    if resp in positive_levels:
        return "pos"
    if resp in ORDINAL:
        return "neg"
    return None   # invalid value: treated as not adjudicated and counted


def resolve_final(rows, resolution=None, positive_levels=POSITIVE_LEVELS):
    """rows: DataFrame of reviewer rows (may contain 2 rows per review_id). Returns (final DataFrame with
    columns review_id, response, status ∈ {resolved, unresolved, unadjudicated}, n_reviewer_rows), and a
    Counter of statuses."""
    rows = rows[rows["review_id"].str.match(r"^R\d{4}$")]
    valid = rows[rows["primary_response"].map(lambda v: collapse(v, positive_levels)).notna()]
    res_map = {}
    if resolution is not None:
        for _, r in resolution.iterrows():
            if collapse(r["primary_response"], positive_levels) is not None:
                res_map[r["review_id"]] = r["primary_response"]
    out = []
    for rid, g in valid.groupby("review_id", sort=False):
        responses = list(g["primary_response"])
        if rid in res_map:
            out.append((rid, res_map[rid], "resolved", len(responses)))
        elif len(responses) == 1:
            out.append((rid, responses[0], "resolved", 1))
        else:
            bins = {collapse(r, positive_levels) for r in responses}
            if len(set(responses)) == 1:
                out.append((rid, responses[0], "resolved", len(responses)))
            elif len(bins) == 1:
                # same collapsed outcome, different level: keep the LESS certain level for the 4-level tables
                order = {v: i for i, v in enumerate(RESPONSES)}
                out.append((rid, max(responses, key=lambda r: order[r]), "resolved", len(responses)))
            else:
                out.append((rid, None, "unresolved", len(responses)))
    for rid in res_map:
        if rid not in {o[0] for o in out}:
            out.append((rid, res_map[rid], "resolved", 0))
    final = pd.DataFrame(out, columns=["review_id", "response", "status", "n_reviewer_rows"])
    return final


def counts_by_cell(final_keyed, positive_levels=POSITIVE_LEVELS):
    """final_keyed: resolved rows joined to the master key (cell). Returns {cell: {n, x, ins}}."""
    counts = {}
    for c in CELLS:
        g = final_keyed[final_keyed["cell"] == c]
        b = g["response"].map(lambda v: collapse(v, positive_levels))
        counts[c] = {"n": int(len(g)), "x": int((b == "pos").sum()), "ins": int((b == "ins").sum())}
    return counts


def small(v):
    """Reporting rule for tracked artifacts: counts below SMALL_CELL are written as '<11'."""
    if isinstance(v, (int, np.integer)) and 0 < v < SMALL_CELL:
        return "<11"
    return int(v) if isinstance(v, (int, np.integer)) else v


def kappa_block(rows, positive_levels=POSITIVE_LEVELS):
    """Pre-consensus agreement on review_ids with exactly two reviewer rows (the double-review subset)."""
    rows = rows[rows["review_id"].str.match(r"^R\d{4}$")]
    rows = rows[rows["primary_response"].isin(RESPONSES)]
    pairs = []
    for rid, g in rows.groupby("review_id", sort=False):
        if len(g) == 2:
            pairs.append(tuple(g["primary_response"]))
    n_pairs = len(pairs)
    out = {"n_double_reviewed_pairs": n_pairs}
    if n_pairs == 0:
        out.update({"kappa_binary_insufficient_excluded": float("nan"), "kappa_binary_insufficient_negative": float("nan"),
                    "weighted_kappa_linear_4level": float("nan"), "weighted_kappa_quadratic_4level": float("nan"),
                    "n_pairs_4level": 0, "raw_agreement_binary_pct": float("nan")})
        return out
    # binary, insufficient excluded (pairs where either is insufficient dropped)
    b_ex = [(collapse(a, positive_levels), collapse(b, positive_levels)) for a, b in pairs]
    b_ex = [(a, b) for a, b in b_ex if a != "ins" and b != "ins"]
    out["n_pairs_binary_insufficient_excluded"] = len(b_ex)
    out["kappa_binary_insufficient_excluded"] = cohen_kappa([a for a, _ in b_ex], [b for _, b in b_ex], ["pos", "neg"]) if b_ex else float("nan")
    b_neg = [("pos" if collapse(a, positive_levels) == "pos" else "neg", "pos" if collapse(b, positive_levels) == "pos" else "neg") for a, b in pairs]
    out["kappa_binary_insufficient_negative"] = cohen_kappa([a for a, _ in b_neg], [b for _, b in b_neg], ["pos", "neg"])
    out["raw_agreement_binary_pct"] = 100 * float(np.mean([a == b for a, b in b_neg]))
    four = [(a, b) for a, b in pairs if a in ORDINAL and b in ORDINAL]
    out["n_pairs_4level"] = len(four)
    out["weighted_kappa_linear_4level"] = cohen_kappa([a for a, _ in four], [b for _, b in four], ORDINAL, "linear") if four else float("nan")
    out["weighted_kappa_quadratic_4level"] = cohen_kappa([a for a, _ in four], [b for _, b in four], ORDINAL, "quadratic") if four else float("nan")
    out["unweighted_kappa_4level"] = cohen_kappa([a for a, _ in four], [b for _, b in four], ORDINAL) if four else float("nan")
    return out


def stratum_supported(sub):
    return len(sub) >= MIN_STRATUM_N


def run(adjudication_paths, resolution_path=None, strata_path=None, group_cols=(), master_key=MASTER_KEY,
        reps=BOOTSTRAP_REPS, seed=SEED_BOOTSTRAP, positive_levels=POSITIVE_LEVELS, sheet="sample"):
    forms = [read_form(p, sheet) for p in adjudication_paths]
    rows = pd.concat(forms, ignore_index=True)
    resolution = read_form(resolution_path, sheet) if resolution_path else None
    key = pd.read_parquet(master_key)[["review_id", "cell", "weight"] + ([] if strata_path else [])]
    weights = key.groupby("cell")["weight"].first().to_dict()
    n_per_cell = key.groupby("cell").size().to_dict()

    final = resolve_final(rows, resolution, positive_levels)
    status = Counter(final["status"])
    resolved = final[final["status"] == "resolved"].merge(key, on="review_id", how="inner")
    n_not_in_key = int((~final["review_id"].isin(key["review_id"])).sum())
    n_key_missing = int((~key["review_id"].isin(final[final["status"] == "resolved"]["review_id"])).sum())

    counts = counts_by_cell(resolved, positive_levels)
    result = {
        "inputs": {"n_adjudication_files": len(adjudication_paths), "n_reviewer_rows": int(len(rows)),
                   "n_rows_with_valid_response": int(rows["primary_response"].isin(RESPONSES).sum()),
                   "resolution_file": bool(resolution_path), "positive_levels": list(positive_levels),
                   "master_key_cells": {CELL_LETTER[c]: int(n_per_cell.get(c, 0)) for c in CELLS},
                   "weights": {CELL_LETTER[c]: float(weights.get(c, float("nan"))) for c in CELLS}},
        "resolution": {"resolved": int(status.get("resolved", 0)), "unresolved_excluded": int(status.get("unresolved", 0)),
                       "review_ids_not_in_master_key": n_not_in_key, "master_key_charts_without_final_label": n_key_missing},
        "counts_by_cell": {CELL_LETTER[c]: {k: small(v) for k, v in counts[c].items()} for c in CELLS},
        "response_distribution_by_cell": {},
        "estimates": {},
        "agreement": kappa_block(rows, positive_levels),
        "by_cell": {},
        "by_stratum": {},
    }
    for c in CELLS:
        g = resolved[resolved["cell"] == c]
        dist = Counter(g["response"])
        result["response_distribution_by_cell"][CELL_LETTER[c]] = {r: small(int(dist.get(r, 0))) for r in RESPONSES}
    for ins in ("exclude", "negative"):
        result["estimates"][f"insufficient_{ins}d" if ins == "exclude" else "insufficient_counted_negative"] = \
            full_estimate(counts, weights, reps=reps, seed=seed, insufficient=ins)
    for c in CELLS:
        d = counts[c]
        for ins in ("exclude", "negative"):
            n_eff = d["n"] - d["ins"] if ins == "exclude" else d["n"]
            result["by_cell"].setdefault(CELL_LETTER[c], {})[ins] = {
                "n_eff": n_eff, "positive_pct": (100 * d["x"] / n_eff) if n_eff else float("nan"),
                "wilson95_pct": [100 * v for v in wilson(d["x"], n_eff)]}
    # optional strata
    if group_cols:
        strata = pd.read_parquet(strata_path) if strata_path and strata_path.endswith(".parquet") else (pd.read_csv(strata_path, dtype=str) if strata_path else None)
        joined = resolved
        if strata is not None:
            joined = joined.merge(strata, on="review_id", how="left")
        for gc in group_cols:
            if gc not in joined.columns:
                result["by_stratum"][gc] = {"error": "column not present"}
                continue
            block = {}
            for level, sub in joined.groupby(gc, dropna=False):
                lev = str(level)
                if not stratum_supported(sub):
                    block[lev] = {"n": small(int(len(sub))), "supported": False}
                    continue
                cts = counts_by_cell(sub, positive_levels)
                block[lev] = {"n": int(len(sub)), "supported": True,
                              "counts_by_cell": {CELL_LETTER[c]: {k: small(v) for k, v in cts[c].items()} for c in CELLS},
                              "estimates": {ins: full_estimate(cts, weights, reps=reps, seed=seed, insufficient=ins) for ins in ("exclude", "negative")}}
            result["by_stratum"][gc] = block
    return result


def to_markdown(res):
    L = ["# Aim 1a estimator output (aggregates only)", ""]
    L.append(f"Reviewer rows: {res['inputs']['n_reviewer_rows']}; resolved charts: {res['resolution']['resolved']}; "
             f"unresolved (excluded): {res['resolution']['unresolved_excluded']}.")
    L.append("")
    L.append("| cell | n adjudicated | positives | insufficient |")
    L.append("| --- | --: | --: | --: |")
    for c in "ABCD":
        d = res["counts_by_cell"][c]
        L.append(f"| {c} | {d['n']} | {d['x']} | {d['ins']} |")
    L.append("")
    for key, lab in (("insufficient_excluded", "Insufficient information EXCLUDED"), ("insufficient_counted_negative", "Insufficient information counted NEGATIVE")):
        e = res["estimates"][key]
        L.append(f"## {lab}")
        L.append("")
        L.append("| quantity | estimate % | bootstrap 95% CI | linearized 95% CI |")
        L.append("| --- | --: | --: | --: |")
        for q in ("under_capture", "ppv", "sensitivity"):
            x = e[q]
            L.append(f"| {q} | {x['estimate_pct']:.2f} | [{x['bootstrap_ci_pct'][0]:.2f}, {x['bootstrap_ci_pct'][1]:.2f}] | [{x['linearized_ci_pct'][0]:.2f}, {x['linearized_ci_pct'][1]:.2f}] |")
        L.append("")
    a = res["agreement"]
    L.append("## Agreement (pre-consensus, double-reviewed charts)")
    L.append("")
    L.append(f"Pairs: {a['n_double_reviewed_pairs']}. Binary kappa (Insufficient excluded): {a['kappa_binary_insufficient_excluded']:.3f}; "
             f"(Insufficient negative): {a['kappa_binary_insufficient_negative']:.3f}. Weighted kappa 4-level linear {a['weighted_kappa_linear_4level']:.3f}, "
             f"quadratic {a['weighted_kappa_quadratic_4level']:.3f}.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adjudication", action="append", required=True, help="reviewer form (csv/xlsx/parquet); repeat per reviewer")
    ap.add_argument("--resolution", default=None, help="optional file of final labels for disagreements (same schema)")
    ap.add_argument("--strata", default=None, help="optional review_id-keyed parquet/csv with grouping columns")
    ap.add_argument("--group-col", action="append", default=[], help="grouping column for by-stratum estimates")
    ap.add_argument("--master-key", default=MASTER_KEY)
    ap.add_argument("--reps", type=int, default=BOOTSTRAP_REPS)
    ap.add_argument("--seed", type=int, default=SEED_BOOTSTRAP)
    ap.add_argument("--positive-levels", default="Definite,Probable")
    ap.add_argument("--sheet", default="sample")
    ap.add_argument("--out", required=True, help="results JSON (aggregates only)")
    ap.add_argument("--md", default=None, help="optional Markdown summary")
    a = ap.parse_args()
    res = run(a.adjudication, a.resolution, a.strata, a.group_col, a.master_key, a.reps, a.seed,
              tuple(v.strip() for v in a.positive_levels.split(",")), a.sheet)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    if a.md:
        with open(a.md, "w") as f:
            f.write(to_markdown(res))
    e = res["estimates"]["insufficient_excluded"]
    print(f"resolved {res['resolution']['resolved']} charts; unresolved {res['resolution']['unresolved_excluded']}; "
          f"under-capture {e['under_capture']['estimate_pct']:.2f}% "
          f"[{e['under_capture']['bootstrap_ci_pct'][0]:.2f}, {e['under_capture']['bootstrap_ci_pct'][1]:.2f}] (Insufficient excluded)")


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------------------------------
# Design-stage helpers (used by scripts/run0919_precision_forecast.py and the tests)
# ----------------------------------------------------------------------------------------------
def closed_form(p, n_pop):
    """Plug-in values from true per-cell positive proportions p and population cell sizes n_pop."""
    tot = sum(n_pop[c] * p[c] for c in CELLS)
    notepos = sum(n_pop[c] * p[c] for c in NOTE_POS)
    return {"under_capture_pct": 100 * sum(n_pop[c] * p[c] for c in CODE_NEG) / tot,
            "ppv_pct": 100 * notepos / sum(n_pop[c] for c in NOTE_POS),
            "sensitivity_pct": 100 * notepos / tot}


def exact_expectation(p, n_sample, n_pop):
    """Exact expectation of the ratio estimators over the binomial draws of cells D, B and A (enumerated;
    cell C held at its mean — its weight is ~10 so its variation moves the denominator by < 0.2%)."""
    from scipy.stats import binom
    A, B, C, D = CELLS
    xa = np.arange(n_sample[A] + 1); xb = np.arange(n_sample[B] + 1); xd = np.arange(n_sample[D] + 1)
    pa, pb, pd_ = binom.pmf(xa, n_sample[A], p[A]), binom.pmf(xb, n_sample[B], p[B]), binom.pmf(xd, n_sample[D], p[D])
    wA, wB, wC, wD = (n_pop[c] / n_sample[c] for c in CELLS)
    xc = n_sample[C] * p[C]
    XA, XB, XD = np.meshgrid(xa, xb, xd, indexing="ij")
    PR = pa[:, None, None] * pb[None, :, None] * pd_[None, None, :]
    num_cn = wB * XB + wD * XD
    num_np = wA * XA + wB * XB
    tot = wA * XA + wB * XB + wC * xc + wD * XD
    with np.errstate(invalid="ignore", divide="ignore"):
        uc = np.where(tot > 0, num_cn / tot, np.nan)
        se = np.where(tot > 0, num_np / tot, np.nan)
    ok = ~np.isnan(uc)
    return {"under_capture_pct": 100 * float((uc[ok] * PR[ok]).sum() / PR[ok].sum()),
            "sensitivity_pct": 100 * float((se[ok] * PR[ok]).sum() / PR[ok].sum()),
            "ppv_pct": 100 * float(((num_np / (wA * n_sample[A] + wB * n_sample[B])) * PR).sum())}
