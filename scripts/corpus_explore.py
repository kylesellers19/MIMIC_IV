#!/usr/bin/env python3
"""PROMPT 2 — unsupervised corpus exploration of hepatic-steatosis documentation.

TEXT-HANDLING RULE (non-negotiable): note text is streamed through DuckDB and
processed in memory only. Nothing raw is printed or written. All outputs are
aggregate frequency tables (headers, terms, n-grams, cue proportions). No
identifiers. No windows are emitted — only token/bigram frequencies derived
from them.

Run: python scripts/corpus_explore.py   (writes docs/corpus_exploration.md)
"""
import bisect
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import duckdb

NOTE = "data/raw/note"
POP = "data/processed/analysis_population.parquet"
OUT = "docs/corpus_exploration.md"
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# ---- patterns ----
HEADER_RE = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9 /,()'-]{1,45}?):")
TOKEN_RE = re.compile(r"[a-z0-9']+")
SEEDS = {
    "steatosis": r"steatosis", "steatotic": r"steatotic",
    "fatty liver": r"fatty liver", "fatty infiltration": r"fatty infiltration",
    "hepatic steatosis": r"hepatic steatosis", "NAFLD": r"nafld", "NASH": r"nash",
    "MASLD": r"masld", "MASH": r"mash", "hepatic echogenicity": r"hepatic echogenicity",
    "fatty change": r"fatty change",
}
SEED_RE = {k: re.compile(r"\b" + v + r"\b") for k, v in SEEDS.items()}
SCREEN = ("steato", "fatty", "nafld", "nash", "masld", "mash", "echogenic")  # fast pre-filter
HEDGES = ["cannot exclude", "cannot be excluded", "may represent", "no evidence of",
          "query", "concerning for", "suggestive of", "consistent with", "likely represents"]
NEG_SINGLE = ["no", "without", "denies", "versus", "vs"]
NEG_MULTI = ["negative for", "family history of", "history of", "ruled out", "rule out"]
STOP = set("the a an and or of to in on for with is are was were be been being at by "
           "as from this that these those it its his her their no not without which who "
           "he she they we you i s".split())


def enclosing_section(header_starts, header_labels, pos):
    i = bisect.bisect_right(header_starts, pos) - 1
    return header_labels[i] if i >= 0 else "<preamble>"


def stream(table, is_discharge):
    """One pass; returns aggregate structures. No text retained."""
    n_notes = 0
    header_notecount = Counter()          # header -> n notes containing
    section_len = defaultdict(list)       # header -> [body char lengths]
    seed_notes = Counter()                # seed -> n notes
    seed_hadm = defaultdict(set)          # seed -> {hadm}
    seed_section = defaultdict(Counter)   # seed -> Counter(section)
    win_uni = Counter(); win_bi = Counter()
    lh_bi = Counter(); lh_tri = Counter()
    hedge = Counter()
    neg_total = 0; neg_cue = Counter()
    hit_hadm = set()                      # hadm with >=1 seed hit
    hit_subj_nullhadm = set()             # subject with seed hit on a null-hadm note

    cols = "note_id, hadm_id" + (", subject_id" if not is_discharge else "") + ", text"
    reader = con.execute(
        f"SELECT {cols} FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)

    for batch in reader:
        d = batch.to_pydict()
        texts = d["text"]; hadms = d["hadm_id"]
        subs = d.get("subject_id", [None] * len(texts))
        for k in range(len(texts)):
            t = texts[k]
            if t is None:
                continue
            n_notes += 1
            low = t.lower()

            # ---- Step 1: section headers (discharge only) ----
            hstarts = []; hlabels = []
            if is_discharge:
                seen = set()
                for m in HEADER_RE.finditer(t):
                    lab = " ".join(m.group(1).split()).upper()
                    hstarts.append(m.start()); hlabels.append(lab)
                    if lab not in seen:
                        header_notecount[lab] += 1; seen.add(lab)
                for j in range(len(hstarts)):
                    body_start = hstarts[j] + len(hlabels[j])
                    body_end = hstarts[j + 1] if j + 1 < len(hstarts) else len(t)
                    section_len[hlabels[j]].append(max(body_end - body_start, 0))

            # ---- fast screen ----
            has_seed = any(s in low for s in SCREEN)
            has_lh = ("liver" in low) or ("hepatic" in low)
            if not (has_seed or has_lh):
                continue

            toks = [(mo.group(0), mo.start()) for mo in TOKEN_RE.finditer(low)]
            words = [w for w, _ in toks]; starts = [s for _, s in toks]

            # ---- Step 3b: liver/hepatic bigrams/trigrams ----
            if has_lh:
                for i, w in enumerate(words):
                    if w == "liver" or w == "hepatic":
                        if i > 0:
                            lh_bi[(words[i-1], w)] += 1
                        if i + 1 < len(words):
                            lh_bi[(w, words[i+1])] += 1
                        if i > 0 and i + 1 < len(words):
                            lh_tri[(words[i-1], w, words[i+1])] += 1
                for h in HEDGES:
                    if h in low:
                        hedge[h] += 1

            # ---- Steps 2/3a/4: seed processing ----
            if has_seed:
                for name, rgx in SEED_RE.items():
                    m = rgx.search(low)
                    if not m:
                        continue
                    seed_notes[name] += 1
                    if hadms[k] is not None:
                        seed_hadm[name].add(int(hadms[k])); hit_hadm.add(int(hadms[k]))
                    elif not is_discharge and subs[k] is not None:
                        hit_subj_nullhadm.add(int(subs[k]))
                    if is_discharge:
                        seed_section[name][enclosing_section(hstarts, hlabels, m.start())] += 1
                    # window + negation from FIRST hit
                    ti = bisect.bisect_right(starts, m.start()) - 1
                    if ti < 0:
                        ti = 0
                    lo, hi = max(0, ti - 4), min(len(words), ti + 5)
                    for w in words[lo:ti] + words[ti+1:hi]:
                        if w not in STOP and len(w) > 1:
                            win_uni[w] += 1
                    for a, b in zip(words[lo:hi], words[lo+1:hi]):
                        win_bi[(a, b)] += 1
                    prev5 = words[max(0, ti-5):ti]
                    neg_total += 1
                    pset = set(prev5); pstr = " ".join(prev5)
                    for c in NEG_SINGLE:
                        if c in pset:
                            neg_cue[c] += 1
                    for c in NEG_MULTI:
                        if c in pstr:
                            neg_cue[c] += 1

    return dict(n_notes=n_notes, header_notecount=header_notecount, section_len=section_len,
                seed_notes=seed_notes, seed_hadm=seed_hadm, seed_section=seed_section,
                win_uni=win_uni, win_bi=win_bi, lh_bi=lh_bi, lh_tri=lh_tri, hedge=hedge,
                neg_total=neg_total, neg_cue=neg_cue, hit_hadm=hit_hadm,
                hit_subj_nullhadm=hit_subj_nullhadm)


print("streaming discharge ...")
DC = stream("discharge", True)
print(f"  discharge notes processed: {DC['n_notes']:,}")
print("streaming radiology ...")
RAD = stream("radiology", False)
print(f"  radiology notes processed: {RAD['n_notes']:,}")

# ---------------- write report ----------------
L = []
def w(s=""): L.append(s)

w("# Corpus Exploration — Hepatic Steatosis Documentation (unsupervised)\n")
w("Aggregate frequency tables only. No note text, no windows, no identifiers were "
  "written. Reproducer: `scripts/corpus_explore.py`. Scope = full note corpus "
  f"(discharge n={DC['n_notes']:,}; radiology n={RAD['n_notes']:,}).\n")

# STEP 1
w("## Step 1 — Discharge section structure\n")
w(f"Header candidates = line-initial `Label:` patterns. Top 40 of "
  f"{len(DC['header_notecount']):,} distinct, by % of {DC['n_notes']:,} discharge notes.\n")
w("| header | notes | % notes | body len median | body p95 | body max |")
w("| --- | ---: | ---: | ---: | ---: | ---: |")
for lab, c in DC["header_notecount"].most_common(40):
    ls = DC["section_len"].get(lab, [])
    arr = np.array(ls) if ls else np.array([0])
    w(f"| {lab} | {c:,} | {100*c/DC['n_notes']:.1f} | {int(np.median(arr)):,} | "
      f"{int(np.quantile(arr,0.95)):,} | {int(arr.max()):,} |")
w("")

# STEP 2
w("## Step 2 — Seed-term frequency\n")
w("Case-insensitive, word-boundary. 'section' = modal enclosing discharge section.\n")
w("| term | DC notes | DC % | DC adm | top DC section | RAD notes | RAD % | RAD adm |")
w("| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |")
for name in SEEDS:
    dcn = DC["seed_notes"].get(name, 0); rdn = RAD["seed_notes"].get(name, 0)
    sec = DC["seed_section"].get(name)
    topsec = sec.most_common(1)[0][0] if sec else "-"
    w(f"| {name} | {dcn:,} | {100*dcn/DC['n_notes']:.2f} | {len(DC['seed_hadm'].get(name,())):,} "
      f"| {topsec} | {rdn:,} | {100*rdn/RAD['n_notes']:.2f} | {len(RAD['seed_hadm'].get(name,())):,} |")
w("")

# STEP 3
def combine(a, b):
    c = Counter(); c.update(a); c.update(b); return c
w("## Step 3 — Discovered terms (I did not seed these)\n")
w("### 3a. Content unigrams in ±4-word windows around seed hits (stopwords removed), top 100\n")
uni = combine(DC["win_uni"], RAD["win_uni"])
w("| # | unigram | count | | # | unigram | count |")
w("| ---: | --- | ---: | --- | ---: | --- | ---: |")
top = uni.most_common(100)
for i in range(0, 100, 2):
    a = top[i] if i < len(top) else ("", "")
    b = top[i+1] if i+1 < len(top) else ("", "")
    av = f"{a[1]:,}" if a[0] else ""; bv = f"{b[1]:,}" if b[0] else ""
    w(f"| {i+1} | {a[0]} | {av} | | {i+2} | {b[0]} | {bv} |")
w("")
w("### 3b. Bigrams in seed windows, top 100\n")
bi = combine(DC["win_bi"], RAD["win_bi"])
w("| # | bigram | count |")
w("| ---: | --- | ---: |")
for i, (g, c) in enumerate(bi.most_common(100), 1):
    w(f"| {i} | {g[0]} {g[1]} | {c:,} |")
w("")
w("### 3c. Corpus bigrams/trigrams containing 'liver' or 'hepatic', top 150\n")
lh = combine(DC["lh_bi"], RAD["lh_bi"])
lht = combine(DC["lh_tri"], RAD["lh_tri"])
allng = Counter()
for g, c in lh.items():
    allng[" ".join(g)] += c
for g, c in lht.items():
    allng[" ".join(g)] += c
w("| # | n-gram | count |")
w("| ---: | --- | ---: |")
for i, (g, c) in enumerate(allng.most_common(150), 1):
    w(f"| {i} | {g} | {c:,} |")
w("")
w("### 3d. Hedging / uncertainty phrases (note frequency, corpus)\n")
hd = combine(DC["hedge"], RAD["hedge"])
w("| phrase | notes |")
w("| --- | ---: |")
for h in HEDGES:
    w(f"| {h} | {hd.get(h,0):,} |")
w("")

# STEP 4
w("## Step 4 — Negation / context cues in preceding 5 tokens of seed hits\n")
tot = DC["neg_total"] + RAD["neg_total"]
w(f"Total seed hits scanned (first hit per note): {tot:,}.\n")
w("| cue | hits with cue | % of hits |")
w("| --- | ---: | ---: |")
negc = combine(DC["neg_cue"], RAD["neg_cue"])
for c in NEG_SINGLE + NEG_MULTI:
    n = negc.get(c, 0)
    w(f"| {c} | {n:,} | {100*n/tot:.1f} |")
w("")

# STEP 5
w("## Step 5 — Coverage sanity check (NOT a recovery estimate)\n")
pop = con.execute(f"SELECT hadm_id, code_positive FROM read_parquet('{POP}')").fetchdf()
hit = DC["hit_hadm"] | RAD["hit_hadm"]
pop["seed_hit"] = pop.hadm_id.astype("int64").isin(hit)
cp = pop[pop.code_positive]; cn = pop[~pop.code_positive]
w(f"- Code-positive locked admissions with ≥1 seed hit in any linked note: "
  f"**{int(cp.seed_hit.sum()):,} / {len(cp):,} ({100*cp.seed_hit.mean():.1f}%)** "
  f"— face-validity check on the seed set.")
w(f"- Code-NEGATIVE locked admissions with ≥1 seed hit (raw count): "
  f"**{int(cn.seed_hit.sum()):,}** of {len(cn):,}.")
w(f"- Outpatient (null-hadm) radiology added seed hits for "
  f"{len(RAD['hit_subj_nullhadm']):,} distinct subjects (not counted above; "
  f"subject-linked, for later).")
w("\n> This is UNADJUDICATED and UNNEGATED and is NOT the 2×2 or the Aim-1a "
  "recovery estimate. It is only a face-validity check on the seed set. The "
  "code-negative count includes negated and historical mentions and is not a "
  "count of missed cases.")

with open(OUT, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"\nwrote {OUT}")
print(f"Step 5: code+ seed-hit {100*cp.seed_hit.mean():.1f}% ; code- seed-hit raw "
      f"{int(cn.seed_hit.sum()):,}")
