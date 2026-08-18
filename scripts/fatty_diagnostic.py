#!/usr/bin/env python3
"""Pre-adjudication DIAGNOSTIC on the bare `fatty` Tier A trigger.

Read-only. Does NOT modify the frozen rule; imports its components and replicates
its per-hit loop (dedup + precedence) exactly, instrumenting only bare-`fatty`
affirmed-positive hits. No gold standard, no reference labels. Aggregate outputs
only (bigrams/trigrams are <=8-word fragments); no note text, no identifiers written.

Scope = inpatient-linked notes (hadm_id in locked population), matching the
frozen behavior report. Run: python scripts/fatty_diagnostic.py
"""
import bisect
from collections import Counter, defaultdict

import pandas as pd
import duckdb

from scripts.note_phenotype import (
    TRIGGERS, _tokenize, _anatomical, _context, SENT_SPLIT, SCREEN,
    TARGET_ORGANS, COMPETING_ORGANS, NOTE, POP, VERSION,
)

# phrase-class keyword sets (assign by token FOLLOWING bare `fatty`); user checks these
CLASS_A_NEXT = {"replacement", "deposition", "metamorphosis", "atrophy",
                "degeneration", "deposits", "deposit", "infiltrate", "infiltrates"}
CLASS_B_NEXT = {"acid", "acids", "food", "foods", "meal", "meals", "stool", "stools",
                "tissue", "tissues", "tumor", "tumour", "tumors", "hernia", "streak",
                "streaks", "plaque", "plaques", "cast", "casts", "diarrhea",
                "necrosis", "marrow", "cell", "cells"}

con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
pop = con.execute(f"SELECT hadm_id, code_positive FROM read_parquet('{POP}')").fetchdf()
locked_hadm = set(pop.hadm_id.astype("int64"))
code_pos = dict(zip(pop.hadm_id.astype("int64"), pop.code_positive))

# collectors
src_next = {"discharge": Counter(), "radiology": Counter()}
src_prev = {"discharge": Counter(), "radiology": Counter()}
src_tri = {"discharge": Counter(), "radiology": Counter()}
tierA_by_hadm = defaultdict(set)          # hadm -> set of affirmed Tier A trigger names
bf_hits = []                              # per bare-fatty affirmed hit
note_level_bf = 0                         # notes with >=1 affirmed bare-fatty (ties to 12,402)


def process(text, hadm, source):
    global note_level_bf
    if text is None:
        return
    low = text.lower()
    if not any(s in low for s in SCREEN):
        return
    note_has_bf = False
    for seg in SENT_SPLIT.split(text):
        slow = seg.lower()
        if not any(s in slow for s in SCREEN):
            continue
        hits = []
        for name, rgx, tier, self_anat in TRIGGERS:
            for m in rgx.finditer(seg):
                hits.append((m.start(), m.end(), name, tier, self_anat))
        if not hits:
            continue
        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        kept = []
        for h in hits:
            if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
                continue
            kept.append(h)
        toks = _tokenize(slow); words = [w for w, _ in toks]; starts = [s for _, s in toks]
        for cstart, cend, name, tier, self_anat in kept:
            hit_ti = bisect.bisect_right(starts, cstart) - 1
            if hit_ti < 0:
                hit_ti = 0
            if not self_anat:
                ok, _organ = _anatomical(words, hit_ti)
                if not ok:
                    continue          # suppressed (counted in frozen report; not here)
            f = _context(words, starts, slow, hit_ti, cstart)
            if f["family"] or f["negated"] or f["hedged"]:
                continue              # excluded / Tier C -> not a Tier A positive
            if tier != "A":
                continue
            tierA_by_hadm[hadm].add(name)
            if name == "fatty (bare)":
                note_has_bf = True
                prv = words[hit_ti - 1] if hit_ti > 0 else "<s>"
                nxt = words[hit_ti + 1] if hit_ti + 1 < len(words) else "</s>"
                src_next[source][nxt] += 1
                src_prev[source][prv] += 1
                src_tri[source][f"{prv} fatty {nxt}"] += 1
                comp_in_sent = any(w in COMPETING_ORGANS for w in words)
                dists = [abs(j - hit_ti) for j, w in enumerate(words) if w in TARGET_ORGANS]
                dist_t = min(dists) if dists else None
                bf_hits.append((hadm, source, prv, nxt, comp_in_sent, dist_t,
                                (dist_t is None and not comp_in_sent)))
    if note_has_bf:
        note_level_bf += 1


def run(table, source):
    reader = con.execute(
        f"SELECT hadm_id, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            h = d["hadm_id"][k]
            if h is None or int(h) not in locked_hadm:
                continue
            process(d["text"][k], int(h), source)


print(f"fatty_diagnostic (frozen rule v{VERSION}); scope = inpatient-linked notes")
print("scanning discharge ..."); run("discharge", "discharge")
print("scanning radiology ..."); run("radiology", "radiology")

# ---------------- assemble report ----------------
H = pd.DataFrame(bf_hits, columns=["hadm", "source", "prev", "next", "comp_in_sent",
                                   "dist_target", "no_target_clean"])
tierA_hadm_all = {h for h, s in tierA_by_hadm.items() if s}
bf_hadms = {h for h, s in tierA_by_hadm.items() if "fatty (bare)" in s}
only = {h for h in bf_hadms if tierA_by_hadm[h] == {"fatty (bare)"}}
redundant = bf_hadms - only

L = []
def w(s=""): L.append(s)

w(f"# Bare `fatty` Trigger Diagnostic (pre-adjudication)\n")
w(f"Frozen rule v{VERSION}. Read-only; no gold standard, no code changes. Scope = "
  f"inpatient-linked notes on the locked population. Aggregate only.\n")
w("## Headline counts\n")
w(f"- Notes with ≥1 affirmed bare-`fatty` Tier A hit: **{note_level_bf:,}** "
  f"(this is the 12,402 figure — a note count, not admissions).")
w(f"- Affirmed bare-`fatty` hits (hit level): **{len(H):,}**.")
w(f"- Admissions positive by any Tier A trigger: **{len(tierA_hadm_all):,}**.")
w(f"- Admissions with a bare-`fatty` Tier A positive: **{len(bf_hadms):,}**.\n")

# STEP 2
w("## Step 2 — How much is bare `fatty` actually adding?\n")
onc = sum(1 for h in only if code_pos.get(h)); onn = len(only) - onc
rdc = sum(1 for h in redundant if code_pos.get(h)); rdn = len(redundant) - rdc
w(f"- Admissions positive by bare `fatty` **ONLY** (no other Tier A trigger in any "
  f"linked note): **{len(only):,}**  (code+ {onc:,} / code− {onn:,}).")
w(f"- Admissions where bare `fatty` is **redundant** with another Tier A trigger: "
  f"**{len(redundant):,}**  (code+ {rdc:,} / code− {rdn:,}).\n")

# STEP 1
def dump_bigrams(counter, title, n):
    w(f"### {title} (top {n})\n")
    w("| # | fragment | count |")
    w("| ---: | --- | ---: |")
    for i, (g, c) in enumerate(counter.most_common(n), 1):
        w(f"| {i} | {g} | {c:,} |")
    w("")

w("## Step 1 — What phrases is bare `fatty` firing on?\n")
for src in ["discharge", "radiology"]:
    w(f"### Source: {src}\n")
    dump_bigrams(Counter({f"fatty {k}": v for k, v in src_next[src].items()}),
                 f"`fatty` + following token", 50)
    dump_bigrams(Counter({f"{k} fatty": v for k, v in src_prev[src].items()}),
                 f"preceding token + `fatty`", 50)
    dump_bigrams(src_tri[src], f"trigrams centered on `fatty`", 30)

# STEP 3
w("## Step 3 — Characterize the unique contributors (bare-`fatty`-ONLY admissions)\n")
Honly = H[H.hadm.isin(only)]
w(f"Bare-`fatty` hits in ONLY admissions: {len(Honly):,}.\n")
w("### Producing `fatty`+next bigrams, ranked\n")
w("| # | fragment | count |")
w("| ---: | --- | ---: |")
for i, (g, c) in enumerate(Counter("fatty " + Honly["next"]).most_common(40), 1):
    w(f"| {i} | {g} | {c:,} |")
w("")
# source split (per admission)
src_by_hadm = Honly.groupby("hadm")["source"].agg(lambda s: set(s))
d_only = sum(1 for s in src_by_hadm if s == {"discharge"})
r_only = sum(1 for s in src_by_hadm if s == {"radiology"})
both = sum(1 for s in src_by_hadm if s == {"discharge", "radiology"})
w(f"- Source of ONLY admissions: discharge-only {d_only:,} · radiology-only {r_only:,} "
  f"· both {both:,}.")
oc = sum(1 for h in only if code_pos.get(h)); on = len(only) - oc
w(f"- Code split of ONLY admissions: code+ {oc:,} · code− {on:,}.\n")
# phrase classes
def classify_next(nxt):
    if nxt in CLASS_A_NEXT:
        return "a"
    if nxt in CLASS_B_NEXT:
        return "b"
    return "c"
Honly = Honly.assign(cls=Honly["next"].map(classify_next))
w("### Phrase classes (assigned by token following `fatty`; you verify/reassign)\n")
w("| class | description | hits |")
w("| --- | --- | ---: |")
labels = {"a": "plausible steatosis phrasing", "b": "clearly not steatosis",
          "c": "ambiguous / organ-uncertain"}
for cl in ["a", "b", "c"]:
    w(f"| {cl} | {labels[cl]} | {int((Honly.cls==cl).sum()):,} |")
w("")
for cl in ["a", "b", "c"]:
    phrs = Counter("fatty " + Honly[Honly.cls == cl]["next"]).most_common(30)
    w(f"**Class {cl} ({labels[cl]}) — phrases assigned:** "
      + ", ".join(f"{g} ({c})" for g, c in phrs) + "\n")

# STEP 4
w("## Step 4 — Stress the anatomical scoping\n")
tot = len(H)
comp_yes = int(H.comp_in_sent.sum())
notarget = int(H.no_target_clean.sum())
w(f"- Non-suppressed bare-`fatty` hits with a competing-organ token **somewhere in "
  f"the same sentence** (not nearest): **{comp_yes:,} / {tot:,} ({100*comp_yes/tot:.1f}%)**.")
w(f"- Hits that passed with **NO liver/hepatic token in the sentence** (passed only "
  f"because no competing organ present): **{notarget:,} ({100*notarget/tot:.1f}%)**.\n")
w("### Distance from `fatty` to nearest liver/hepatic token\n")
w("| distance (tokens) | hits |")
w("| ---: | ---: |")
dc = Counter(H.dist_target.dropna().astype(int))
for dist in range(0, 11):
    w(f"| {dist} | {dc.get(dist,0):,} |")
w(f"| none in sentence | {int(H.dist_target.isna().sum()):,} |")
w("")

# STEP 5 cost statement
w("## Step 5 — What dropping bare `fatty` would cost\n")
w(f"Dropping the bare-`fatty` trigger would remove the **{len(only):,} admissions** "
  f"that are note-positive by bare `fatty` ONLY (code+ {onc:,} / code− {onn:,}); the "
  f"other {len(redundant):,} bare-`fatty` admissions remain positive via other Tier A "
  f"triggers. No recommendation is made and no code is changed.")

with open("docs/fatty_trigger_diagnostic.md", "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"\nwrote docs/fatty_trigger_diagnostic.md")
print(f"note_level_bf={note_level_bf:,} hit_level={len(H):,} "
      f"bf_hadms={len(bf_hadms):,} only={len(only):,} redundant={len(redundant):,}")
