#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 — fibrosis index by cell (amendment l, S19). Exploratory.

FIB-4 = age x AST / (platelets x sqrt(ALT)), approved itemids, age as in Table 3 (age at admission from the
frame; computable when AST, ALT and platelets are present and ALT > 0 and platelets > 0).

  primary      first result per admission; by cell: computable n (%), median [IQR], share below 1.3,
               1.3-2.67, above 2.67
  sens 1       lower cutoff 2.0 at age 65 and over
  sens 2       last result per admission
  sens 3       excluding admissions with AST or ALT above 200 U/L and admissions flagged alcohol, viral,
               other etiology or cirrhosis in cmrf.parquet
  sens 4       most recent outpatient AST, ALT and platelets in the 365 days before admission, where all
               three exist (scripts/run1110_outpt_fib4_inputs.py)
  replicate    dev/test notes subsample with the language-model phenotype: uncoded positive against coded
               positive

Intervals: subject-cluster bootstrap, 500 replicates, seed 20260919, 95% percentile.
Writes docs/run_2026-11-10/results/fib4_by_cell.json. Counts and shares only.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.run1110_common import RES, CELLS, FLOOR, Boot, load_frame, med_iqr, share

FEATURES = "data/processed/run_2026-09-19_features.parquet"
OUTPT = "data/processed/run_2026-11-10_outpt_fib4.parquet"
LOW, HIGH, LOW_65 = 1.3, 2.67, 2.0
CATS = ("below_low_cutoff", "indeterminate", "above_2_67")


def fib4(age, ast, alt, plt):
    ok = ast.notna() & alt.notna() & plt.notna() & (alt > 0) & (plt > 0)
    return ((age * ast) / (plt * np.sqrt(alt.where(alt > 0)))).where(ok)


def summarise(d, f, group_col, groups, boot, age65_cutoff=False):
    """d: frame rows (aligned with boot); f: FIB-4 Series; -> {group: {...}}"""
    out = {}
    low_cut = np.where(d.age.to_numpy() >= 65, LOW_65, LOW) if age65_cutoff else np.full(len(d), LOW)
    fv = f.to_numpy(dtype=float)
    comp = ~np.isnan(fv)
    cat = {"below_low_cutoff": comp & (fv < low_cut), "indeterminate": comp & (fv >= low_cut) & (fv <= HIGH),
           "above_2_67": comp & (fv > HIGH)}
    for g in groups:
        in_g = (d[group_col] == g).to_numpy()
        n, nc = int(in_g.sum()), int((in_g & comp).sum())
        r = {"admissions": share(nc, n)["n"] if n < FLOOR else n,
             "computable": share(nc, n, boot.ratio_ci(in_g & comp, in_g) if n >= FLOOR else None)}
        if n >= FLOOR and nc >= FLOOR:
            r["fib4"] = med_iqr(fv[in_g & comp])
            xs = {c: int((in_g & m).sum()) for c, m in cat.items()}
            small = [c for c, x in xs.items() if 0 < x < FLOOR]
            hide = set(small)
            if len(small) == 1:                    # three shares partition the computable total
                hide.add(min((c for c in xs if c not in small and xs[c] > 0), key=lambda c: xs[c]))
            for c in CATS:
                r[c] = ({"n": nc, "x": "<11" if c in small else "withheld", "pct": "withheld", "reported": False}
                        if c in hide else share(xs[c], nc, boot.ratio_ci(in_g & cat[c], in_g & comp)))
        out[g] = r
    return out


def main():
    df = load_frame()
    feat = pd.read_parquet(FEATURES, columns=["hadm_id", "first_val_AST", "first_val_ALT", "first_val_Platelets",
                                              "last_val_AST", "last_val_ALT", "last_val_Platelets"])
    df = df.merge(feat, on="hadm_id", how="left")
    have_out = os.path.exists(OUTPT)
    if have_out:
        df = df.merge(pd.read_parquet(OUTPT), on="hadm_id", how="left")
    boot = Boot(df.subject_id)
    cells = list(CELLS)
    first = fib4(df.age, df.first_val_AST, df.first_val_ALT, df.first_val_Platelets)
    last = fib4(df.age, df.last_val_AST, df.last_val_ALT, df.last_val_Platelets)
    res = {"script": "scripts/run1110_fib4_by_cell.py", "amendment": "l (S19)", "exploratory": True,
           "definition": {"fib4": "age x AST / (platelets x sqrt(ALT))", "cutoffs": {"low": LOW, "high": HIGH, "low_at_age_65_and_over_sens1": LOW_65},
                          "cells": CELLS, "note_definition": "b (primary)", "age": "age at admission, as in Table 3 (MIMIC caps ages 89 and over)"},
           "bootstrap": {"replicates": int(boot.W.shape[0]), "seed": 20260919, "cluster": "subject", "interval": "95% percentile"},
           "population_admissions": int(len(df)), "analyses": {}}
    res["analyses"]["primary_first_result"] = summarise(df, first, "cell", cells, boot)
    res["analyses"]["sens1_low_cutoff_2_0_at_age_65_and_over"] = summarise(df, first, "cell", cells, boot, age65_cutoff=True)
    res["analyses"]["sens2_last_result"] = summarise(df, last, "cell", cells, boot)
    for c in cells:       # a count that sits 1-10 away from the primary count is withheld; its share stays
        a, b = res["analyses"]["primary_first_result"][c]["computable"], res["analyses"]["sens2_last_result"][c]["computable"]
        if isinstance(a.get("x"), int) and isinstance(b.get("x"), int) and 0 < abs(a["x"] - b["x"]) < FLOOR:
            b["x"] = "withheld"; b["why_x_withheld"] = "differs from the primary count by fewer than 11"
            for k in ("below_low_cutoff", "indeterminate", "above_2_67"):
                if k in res["analyses"]["sens2_last_result"][c]:
                    res["analyses"]["sens2_last_result"][c][k]["n"] = "withheld"
    excl = ((df.first_val_AST > 200) | (df.first_val_ALT > 200) | df.alcohol | df.viral | df.other_etio | df.cirrhosis).to_numpy()
    d3 = df.assign(cell3=np.where(excl, "excluded", df.cell))
    s3 = summarise(d3, first, "cell3", cells, boot)
    for c in cells:
        n_all = int((df.cell == c).sum())
        s3[c]["excluded"] = share(int((excl & (df.cell == c).to_numpy()).sum()), n_all)
    res["analyses"]["sens3_excluding_high_enzymes_and_other_etiologies"] = s3
    if have_out:
        outp = fib4(df.age, df.out_AST, df.out_ALT, df.out_Platelets)
        res["analyses"]["sens4_outpatient_365_days_before_admission"] = summarise(df, outp, "cell", cells, boot)
    else:
        res["analyses"]["sens4_outpatient_365_days_before_admission"] = {"status": "not run: outpatient inputs missing"}

    # replicate: dev/test notes subsample, language-model phenotype (no GOLD_HOLDOUT admission is in load())
    from scripts.llm_phenotype import load
    a = load()[["hadm_id", "subject_id", "code", "llm"]].merge(df[["hadm_id", "age", "first_val_AST", "first_val_ALT", "first_val_Platelets"]], on="hadm_id", how="left")
    a["group"] = np.select([a.llm & a.code, a.llm & ~a.code], ["coded, LLM-positive", "uncoded, LLM-positive"], default="other")
    fa = fib4(a.age, a.first_val_AST, a.first_val_ALT, a.first_val_Platelets)
    res["replicate_llm_phenotype"] = {"scope": "dev/test notes subsample", "admissions_in_subsample": int(len(a)),
                                      "groups": summarise(a, fa, "group", ["coded, LLM-positive", "uncoded, LLM-positive"], Boot(a.subject_id))}
    json.dump(res, open(f"{RES}/fib4_by_cell.json", "w"), indent=1)
    p = res["analyses"]["primary_first_result"]
    for c in cells:
        print(c, p[c]["admissions"], p[c]["computable"].get("pct"), p[c].get("fib4"), {k: p[c][k].get("pct") for k in CATS if k in p[c]})


if __name__ == "__main__":
    main()
