#!/usr/bin/env python3
"""run_2026-11-10 Phase 4 — carry-over check for the v3 answers (amendment k, S18).

QUESTION
    Would the dev/test units that v3 answered NO, and that were carried into the merged v4 labels
    without being re-asked, still be answered NO by v4?

    sample   distinct dev/test units whose stored answer is a carried-over v3 NO, in the two NO strata of
             the quantization check ("NO, fat word", "NO, other"); 1,500 per stratum, seed 20261110,
             excluding units already in the quantization-check sample. Writes, under
             data/processed/llm_review/carryover_check/: sample_input.parquet, sample_strata.parquet.
    summary  after prompt v4 has answered the sample: per stratum and population-weighted (Wilson bounds
             as in diagnostics/llm_review_audit/quant_check.py), the share whose v4 answer is not NO and
             the share whose primary-label status changes; the quantization check's carried-over NO units
             separately and pooled; an estimate of how many dev/test admissions would change label.
             Writes docs/run_2026-11-10/results/carryover_check.json.

Run (sample only; GOLD_HOLDOUT is never touched; the review script refuses GOLD_HOLDOUT input):
    scripts/run0919_env.sh scripts/llm_sentence_review.py --input <C>/sample_input.parquet \
        --out <C>/v4_run --variant v4 --max-hours 2

WHAT IT DOES NOT CHANGE: no stored answer, label or result.
PRIVACY: sentence text is read only to stratify and to build the run input; only counts are printed.
SMALL CELLS: a count of 1-10 is published as "<11"; the shares that would reveal it are published as an
    upper bound computed at 10.
USAGE: scripts/run0919_env.sh scripts/run1110_carryover_check.py sample|summary
"""
import glob, json, os, sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts.llm_sentence_review import load_input
from diagnostics.llm_review_audit.quant_check import FAT, INPUT, STORED, Q, wilson

D = "data/processed/llm_review"
C = f"{D}/carryover_check"
RES = "docs/run_2026-11-10/results/carryover_check.json"
SEED_CARRYOVER = 20261110
PER_STRATUM = 1500
STRATA = ("NO, fat word", "NO, other")
FLOOR = 11


def carried_over_units():
    """Distinct dev/test units whose stored (merged v4) answer is v3's NO, carried over. -> DataFrame with text."""
    df = load_input(INPUT, "v4")
    units = df.drop_duplicates("key")
    stored = pd.read_parquet(STORED, columns=["key", "answer", "source"]).drop_duplicates("key")
    u = units.merge(stored, on="key", how="inner")
    u = u[(u.source == "v3") & (u.answer == "NO")].copy()
    fat = u.text.str.lower().str.contains(FAT)
    u["stratum"] = np.where(fat, STRATA[0], STRATA[1])
    return u


def sample():
    u = carried_over_units()
    qkeys = set(pd.read_parquet(f"{Q}/sample_strata.parquet", columns=["key"]).key)
    pop_all = u.stratum.value_counts()
    elig = u[~u.key.isin(qkeys)]
    pop = elig.stratum.value_counts()
    rng = np.random.default_rng(SEED_CARRYOVER)
    picks = []
    for s in STRATA:
        g = elig[elig.stratum == s]
        picks.append(g.iloc[np.sort(rng.choice(len(g), size=min(PER_STRATUM, len(g)), replace=False))])
    smp = pd.concat(picks)
    os.makedirs(C, exist_ok=True)
    smp.drop(columns=["key", "answer", "source", "stratum"]).to_parquet(f"{C}/sample_input.parquet", index=False)
    smp[["key", "stratum", "answer", "source"]].assign(population=smp.stratum.map(pop), population_all=smp.stratum.map(pop_all)) \
        .to_parquet(f"{C}/sample_strata.parquet", index=False)
    print(f"carried-over v3 NO units (distinct, dev/test): {len(u):,}; eligible after excluding the quantization-check sample: {len(elig):,}; "
          f"sampled {len(smp):,} (seed {SEED_CARRYOVER})")
    for s in STRATA:
        print(f"  {s:<14} population {int(pop_all.get(s, 0)):>7,} | eligible {int(pop.get(s, 0)):>7,} | sampled {int((smp.stratum == s).sum()):>5}")


def answers(path):
    files = sorted(glob.glob(f"{path}/shards/*.parquet"))
    if not files:
        sys.exit(f"no answers in {path} yet")
    return pd.concat([pd.read_parquet(f) for f in files]).drop_duplicates("key", keep="last")


def share(x, n):
    """Published form of x of n: exact when x is 0 or >= 11, otherwise an upper bound computed at 10."""
    x, n = int(x), int(n)
    if n == 0:
        return {"n": 0}
    if 0 < x < FLOOR:
        hi = wilson(FLOOR - 1, n)[1]
        return {"n": n, "x": "<11", "pct": f"under {100 * FLOOR / n:.2f}", "wilson_hi_pct_at_10": round(100 * float(hi), 2)}
    lo, hi = wilson(x, n)
    return {"n": n, "x": x, "pct": round(100 * x / n, 2), "wilson_lo_pct": round(100 * max(float(lo), 0), 2), "wilson_hi_pct": round(100 * float(hi), 2)}


def weighted(rows):
    """rows: [(x, n, N)] per stratum -> population-weighted share with conservative bounds (population-weighted
    per-stratum Wilson bounds, as in quant_check.weighted). Masked strata enter at 10 and the result is an upper bound."""
    Ntot = sum(N for _, _, N in rows)
    masked = any(0 < x < FLOOR for x, _, _ in rows)
    xs = [(FLOOR - 1 if 0 < x < FLOOR else x, n, N) for x, n, N in rows]
    est = sum(N / Ntot * x / n for x, n, N in xs)
    lo = sum(N / Ntot * max(float(wilson(x, n)[0]), 0) for x, n, N in xs)
    hi = sum(N / Ntot * float(wilson(x, n)[1]) for x, n, N in xs)
    units = sum(N * x / n for x, n, N in xs)
    if masked:
        return {"pct": f"at most {100 * est:.2f}", "wilson_hi_pct": round(100 * hi, 2), "units_approx": f"at most {int(round(units, -1)):,}",
                "note": "a stratum count of 1-10 enters at 10, so these are upper bounds"}
    return {"pct": round(100 * est, 2), "wilson_lo_pct": round(100 * lo, 2), "wilson_hi_pct": round(100 * hi, 2),
            "units_approx": int(round(units, -1))}


def block(m, pop_col):
    """m: one row per sampled unit with stratum, new answer `a`, new timing `t`, population column."""
    not_no = m.a != "NO"
    counts = m.a.eq("YES") & m.t.isin(["CURRENT", "PAST"])          # a stored NO never counts; this is a status change
    out = {"per_stratum": {}, "units_answered": int(len(m))}
    rows_nn, rows_c = [], []
    for s in STRATA:
        g = m.stratum == s
        n, N = int(g.sum()), int(m.loc[g, pop_col].iloc[0]) if g.any() else 0
        out["per_stratum"][s] = {"population_units": N, "v4_answer_not_no": share(not_no[g].sum(), n),
                                 "primary_label_status_changes": share(counts[g].sum(), n)}
        if n:
            rows_nn.append((int(not_no[g].sum()), n, N)); rows_c.append((int(counts[g].sum()), n, N))
    out["population_weighted"] = {"v4_answer_not_no": weighted(rows_nn), "primary_label_status_changes": weighted(rows_c)}
    return out, rows_c


def admissions_changing(rows_c):
    """Expected number of dev/test admissions (notes subsample) whose primary label would change if every
    carried-over NO unit were re-asked with v4. A change can only be negative -> positive. Each currently
    negative admission with k_s carried-over NO sentences in stratum s changes with probability
    1 - prod_s (1 - p_s)^k_s, sentences treated as independent. p_s: the per-stratum share whose status changes,
    from this run's sample."""
    from scripts.llm_phenotype import load
    adm = load()
    neg = set(adm.hadm_id[~adm.llm]) if "hadm_id" in adm.columns else set(adm.index[~adm.llm])
    df = load_input(INPUT, "v4")
    stored = pd.read_parquet(STORED, columns=["key", "answer", "source"]).drop_duplicates("key")
    r = df[["hadm_id", "key", "text"]].merge(stored, on="key")
    r = r[(r.source == "v3") & (r.answer == "NO") & r.hadm_id.isin(neg)].drop_duplicates(["hadm_id", "key"])
    r["stratum"] = np.where(r.text.str.lower().str.contains(FAT), STRATA[0], STRATA[1])
    k = r.groupby(["hadm_id", "stratum"]).size().unstack(fill_value=0).reindex(columns=list(STRATA), fill_value=0)
    masked = any(0 < x < FLOOR for x, _, _ in rows_c)
    res = {"admissions_currently_negative_with_a_carried_over_no": int(len(k)),
           "admissions_dev_test_subsample": int(len(adm)), "assumption": "sentences within an admission treated as independent"}

    def expected(ps):
        keep = np.ones(len(k))
        for s, p in zip(STRATA, ps):
            keep *= (1 - p) ** k[s].to_numpy()
        return float((1 - keep).sum())
    xs = [(FLOOR - 1 if 0 < x < FLOOR else x, n) for x, n, _ in rows_c]
    hi = expected([float(wilson(x, n)[1]) for x, n in xs])
    if masked:
        res["expected_admissions_changing_label"] = f"at most {int(round(expected([x / n for x, n in xs]))):,}"
        res["note"] = "a stratum count of 1-10 enters at 10, so the estimate is an upper bound"
    else:
        res["expected_admissions_changing_label"] = int(round(expected([x / n for x, n in xs])))
        res["lower_bound_wilson"] = int(round(expected([max(float(wilson(x, n)[0]), 0) for x, n in xs])))
    res["upper_bound_wilson"] = int(round(hi))
    return res


def summary():
    st = pd.read_parquet(f"{C}/sample_strata.parquet")
    a = answers(f"{C}/v4_run")
    man = json.load(open(f"{C}/v4_run/manifest.json"))
    m = st.merge(a[["key", "answer", "timing", "error"]].rename(columns={"answer": "a", "timing": "t"}), on="key")
    m = m[m.error.isna()]
    new, rows_new = block(m, "population")

    # the quantization check's carried-over NO units: same model, prompt v4, answered 2026-10-27
    qs = pd.read_parquet(f"{Q}/sample_strata.parquet")
    qa = answers(f"{Q}/q4_rerun")
    q = qs[(qs.source == "v3") & (qs.answer == "NO") & qs.stratum.isin(STRATA)].merge(
        qa[["key", "answer", "timing"]].rename(columns={"answer": "a", "timing": "t"}), on="key")
    pop_all = dict(st.groupby("stratum").population_all.first())
    q["population_all"] = q.stratum.map(pop_all)
    quant, _ = block(q, "population_all")
    both = pd.concat([m[["key", "stratum", "a", "t"]], q[["key", "stratum", "a", "t"]]]).drop_duplicates("key")
    both["population_all"] = both.stratum.map(pop_all)
    pooled, rows_pooled = block(both, "population_all")
    # pooled minus new = the quantization check's count. Where that count is 1-10 (masked) and the new count is
    # exact, the pooled figure is withheld, or the masked count could be recovered by subtraction.
    for metric in ("v4_answer_not_no", "primary_label_status_changes"):
        leak = False
        for s_ in STRATA:
            qx, nx = quant["per_stratum"][s_][metric].get("x"), new["per_stratum"][s_][metric].get("x")
            if qx == "<11" and isinstance(nx, int):
                pooled["per_stratum"][s_][metric] = {"n": pooled["per_stratum"][s_][metric]["n"], "x": "withheld", "pct": "withheld",
                                                     "why": "would reveal the quantization check's count of 1-10 by subtraction"}
                leak = True
        if leak:
            pooled["population_weighted"][metric] = {"pct": "withheld", "why": "a stratum is withheld"}

    out = {"script": "scripts/run1110_carryover_check.py", "amendment": "k (S18)", "prompt": "v4", "seed": SEED_CARRYOVER,
           "model": {"name": man["model"], "digest": man["model_digest"], "ollama_version": man["ollama_version"], "options": man["options"]},
           "strata": list(STRATA), "bounds": "Wilson 95%; population-weighted per-stratum bounds (conservative), as in quant_check.py",
           "sample": {"per_stratum_target": PER_STRATUM, "units_sampled": int(len(st)), "units_answered": int(len(m)),
                      "errors": int(a.error.notna().sum()), "unparsed": int(a.answer.eq("UNPARSED").sum()),
                      "not_two_word": int((a.strict == False).sum()),
                      "speed_per_s": round(1 / a.seconds.iloc[10:].mean(), 2) if len(a) > 20 else None},
           "new_sample": new, "quantization_check_carried_over_no": quant, "pooled": pooled,
           "admissions": dict(admissions_changing(rows_new), rates_from="the new sample (this run)"),
           "changes_nothing": "no stored answer, label or result is modified"}
    for k in ("errors", "unparsed", "not_two_word"):                 # small-cell rule applies to these counts too
        if 0 < out["sample"][k] < FLOOR:
            out["sample"][k] = "<11"
    os.makedirs(os.path.dirname(RES), exist_ok=True)
    json.dump(out, open(RES, "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("sample", "new_sample", "pooled", "admissions")}, indent=1))


if __name__ == "__main__":
    {"sample": sample, "summary": summary}[sys.argv[1] if len(sys.argv) > 1 else "summary"]()
