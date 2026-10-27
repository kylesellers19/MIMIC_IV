#!/usr/bin/env python3
"""DIAGNOSTIC: quantization check (protocol §6). Does Gemma 4's quantization-aware build answer like the
Q4_K_M build the study used?

    sample   draw a stratified sample of distinct DEV/TEST units, stratified by the stored (merged v4)
             answer: YES, UNCLEAR, NO with a fat or echogenicity word, other NO. Writes
             data/processed/llm_review/quant_check/sample_input.parquet (one row per unit) and
             sample_strata.parquet (key, stratum, stratum population).
    summary  after both builds have answered the sample with prompt v4, print counts only:
             1. each run: speed, reply format, errors
             2. QAT against a same-day Q4_K_M rerun, per stratum and population-weighted
             3. the Q4_K_M rerun against the stored answers (determinism after the Ollama restart, and
                whether v3's carried-over NO answers stay NO when v4 is asked)

Runs (sample only; GOLD_HOLDOUT is never touched):
    scripts/run0919_env.sh scripts/llm_sentence_review.py --input <Q>/sample_input.parquet --out <Q>/q4_rerun --variant v4
    scripts/run0919_env.sh scripts/llm_sentence_review.py --input <Q>/sample_input.parquet --out <Q>/qat --variant v4 \
        --model gemma4:26b-a4b-it-qat

PRIVACY: sentence text is read only to stratify and to build the run input; nothing but counts is printed.
USAGE: scripts/run0919_env.sh diagnostics/llm_review_audit/quant_check.py sample|summary
"""
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts.llm_sentence_review import load_input

D = "data/processed/llm_review"
Q = f"{D}/quant_check"
INPUT = f"{D}/liver_sentences_devtest_v3.parquet"
STORED = f"{D}/full_v4_merged/sentence_answers.parquet"
SEED = 20261027
TARGET = {"YES": 400, "UNCLEAR": 200, "NO, fat word": 400, "NO, other": 300}
FAT = re.compile(r"steato|fatty|\bfat\b|echogenic|attenuation|\b(?:nafld|nafl|nash|masld|mash|mafld|metald)\b")
RUNS = {"q4_rerun": "Q4_K_M rerun", "qat": "QAT"}


def sample():
    df = load_input(INPUT, "v4")
    df = df[df.partition.isin(["DEV", "TEST"])] if "partition" in df.columns else df
    units = df.drop_duplicates("key")
    stored = pd.read_parquet(STORED, columns=["key", "answer", "source"]).drop_duplicates("key")
    u = units.merge(stored, on="key", how="inner")
    fat = u.text.str.lower().str.contains(FAT)
    u["stratum"] = np.select([u.answer.eq("YES"), u.answer.eq("UNCLEAR"), u.answer.eq("NO") & fat, u.answer.eq("NO")],
                             list(TARGET), default="other")
    u = u[u.stratum != "other"]
    pop = u.stratum.value_counts()
    rng = np.random.default_rng(SEED)
    picks = []
    for s, n in TARGET.items():
        g = u[u.stratum == s]
        picks.append(g.iloc[np.sort(rng.choice(len(g), size=min(n, len(g)), replace=False))])
    smp = pd.concat(picks)
    os.makedirs(Q, exist_ok=True)
    smp.drop(columns=["key", "answer", "source", "stratum"]).to_parquet(f"{Q}/sample_input.parquet", index=False)
    smp[["key", "stratum", "answer", "source"]].assign(population=smp.stratum.map(pop)).to_parquet(
        f"{Q}/sample_strata.parquet", index=False)
    print(f"distinct DEV/TEST units with a stored answer: {len(u):,}; sample {len(smp):,} (seed {SEED})")
    for s in TARGET:
        print(f"  {s:<14} population {pop.get(s, 0):>7,} | sampled {int((smp.stratum == s).sum()):>4}")


def answers(run):
    files = sorted(glob.glob(f"{Q}/{run}/shards/*.parquet"))
    if not files:
        sys.exit(f"no answers in {Q}/{run} yet")
    return pd.concat([pd.read_parquet(f) for f in files]).drop_duplicates("key", keep="last")


def wilson(x, n, z=1.96):
    c, h = (x + z * z / 2) / (n + z * z), z * np.sqrt(x * (n - x) / n + z * z / 4) / (n + z * z)
    return c - h, c + h


def weighted(flags, strata):
    """Population-weighted share of True, the implied number of distinct units, and conservative 95% bounds
    (population-weighted per-stratum Wilson bounds; a stratum with no change still contributes its upper bound)."""
    t = pd.DataFrame({"f": flags.astype(float), "s": strata.stratum, "N": strata.population})
    g = t.groupby("s").agg(x=("f", "sum"), n=("f", "size"), N=("N", "first"))
    W = g.N / g.N.sum()
    lo, hi = wilson(g.x, g.n)
    return float((W * g.x / g.n).sum()), float((g.N * g.x / g.n).sum()), float((W * lo).sum()), float((W * hi).sum())


def summary():
    st = pd.read_parquet(f"{Q}/sample_strata.parquet")
    runs = {r: answers(r) for r in RUNS}
    print("1. runs")
    for r, a in runs.items():
        print(f"  {RUNS[r]:<14} answered {len(a):,}/{len(st):,} | {1 / a.seconds.iloc[10:].mean():.2f}/s | "
              f"two-word {int(a.strict.sum()):,} | unparsed {int(a.answer.eq('UNPARSED').sum())} | "
              f"errors {int(a.error.notna().sum())}")
    m = st.merge(runs["q4_rerun"][["key", "answer", "timing"]].rename(columns={"answer": "q4", "timing": "q4_t"}), on="key")
    m = m.merge(runs["qat"][["key", "answer", "timing"]].rename(columns={"answer": "qat", "timing": "qat_t"}), on="key")
    print(f"  units answered by both: {len(m):,}")

    def label(a, t):
        return np.where(a.eq("YES") & t.isin(["CURRENT", "PAST"]), "YES (counts)", a)

    m["q4_lab"], m["qat_lab"] = label(m.q4, m.q4_t), label(m.qat, m.qat_t)
    print("\n2. QAT against the Q4_K_M rerun (prompt v4)")
    for s in TARGET:
        g = m[m.stratum == s]
        moves = pd.crosstab(g.q4, g.qat)
        ch = {f"{i}->{j}": int(moves.loc[i, j]) for i in moves.index for j in moves.columns if i != j and moves.loc[i, j]}
        print(f"  {s:<14} n {len(g):>4} | same answer {int((g.q4 == g.qat).sum()):>4} | "
              f"same answer+timing {int(((g.q4 == g.qat) & (g.q4_t == g.qat_t)).sum()):>4} | changes {ch}")
    yes4, yesq = m.q4_lab.eq("YES (counts)"), m.qat_lab.eq("YES (counts)")
    print(f"  {len(st):,} sampled of {int(st.groupby('stratum').population.first().sum()):,} distinct DEV/TEST units; "
          "population-weighted, conservative 95% bounds:")
    for name, flags in (("answer differs", m.q4 != m.qat), ("primary-rule status differs", yes4 != yesq),
                        ("  of which QAT counts, Q4_K_M does not", yesq & ~yes4), ("  of which Q4_K_M counts, QAT does not", yes4 & ~yesq)):
        est, units, lo, hi = weighted(flags, m)
        print(f"  {name:<40} {100 * est:5.2f}% ({100 * lo:.2f}-{100 * hi:.2f}) | about {units:,.0f} units")
    print(f"  primary-rule YES in the sample: Q4_K_M {int(yes4.sum())}, QAT {int(yesq.sum())}, both {int((yes4 & yesq).sum())}")

    print("\n3. Q4_K_M rerun against the stored answers")
    for src, txt in (("v4", "units re-asked with v4 in the full run"), ("v3", "units whose stored answer is v3's NO, carried over")):
        g = m[m.source == src]
        moves = pd.crosstab(g.answer, g.q4)
        ch = {f"{i}->{j}": int(moves.loc[i, j]) for i in moves.index for j in moves.columns if i != j and moves.loc[i, j]}
        print(f"  {txt}: n {len(g):,} | same answer {int((g.answer == g.q4).sum()):,} | changes {ch}")


if __name__ == "__main__":
    {"sample": sample, "summary": summary}[sys.argv[1] if len(sys.argv) > 1 else "summary"]()
