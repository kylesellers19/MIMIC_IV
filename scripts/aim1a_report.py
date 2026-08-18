#!/usr/bin/env python3
"""STEPS 2-5 — Aim 1a characterization, equity stratification, sampling frame, report.

Reads the per-admission cell frame from build_2x2 (no re-streaming). Uses the
PRIMARY definition (b) for cell assignment. Writes docs/aim1a_crosstab.md
(aggregate, safe) and data/processed/aim1a_sample.parquet (credentialed, gitignored).

Run (after build_2x2.py): python scripts/aim1a_report.py
"""
import numpy as np
import pandas as pd
import duckdb

FRAME = "data/processed/aim1a_frame.parquet"
SAMPLE_OUT = "data/processed/aim1a_sample.parquet"
DOC = "docs/aim1a_crosstab.md"
SEED = 20260818                     # fixed; recorded in doc
ALLOC = {"code-/note+": 150, "code+/note+": 80, "code+/note-": 70, "code-/note-": 100}
DOUBLE_REVIEW_FRAC = 0.25           # 25% overlap for Cohen's kappa (in 20-30% range)
FLOOR = 11
LAB_AVAIL = ["ALT", "AST", "Platelets", "Triglycerides", "HDL", "HbA1c",
             "Glucose", "Albumin", "Bilirubin_total", "Alkaline_phosphatase"]

df = duckdb.connect().execute(f"SELECT * FROM read_parquet('{FRAME}')").fetchdf()
N = len(df)
cp = df.code_positive.astype(bool)


def cell_of(notecol):
    nt = df[notecol].astype(bool)
    return np.select([cp & nt, ~cp & nt, cp & ~nt, ~cp & ~nt],
                     ["code+/note+", "code-/note+", "code+/note-", "code-/note-"],
                     default="")


df["cell_b"] = cell_of("note_b")

# ---------- SMD helpers ----------
def smd_cont(a, b):
    a, b = a.dropna(), b.dropna()
    d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return np.nan if d == 0 else (a.mean() - b.mean()) / d

def smd_bin(p1, p0):
    d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
    return np.nan if d == 0 else (p1 - p0) / d

def smd_multi(s1, s0):
    s1, s0 = s1.fillna("Missing"), s0.fillna("Missing")
    cats = sorted(set(s1) | set(s0))
    if len(cats) < 2:
        return np.nan
    p1 = np.array([(s1 == c).mean() for c in cats])[:-1]
    p2 = np.array([(s0 == c).mean() for c in cats])[:-1]
    def cov(P):
        S = -np.outer(P, P); S[np.diag_indices(len(P))] = P*(1-P); return S
    S = (cov(p1) + cov(p2)) / 2
    try:
        return float(np.sqrt(max((p1-p2) @ np.linalg.pinv(S) @ (p1-p2), 0)))
    except np.linalg.LinAlgError:
        return np.nan

def med_iqr(s):
    s = s.dropna()
    return f"{s.median():.1f} [{s.quantile(.25):.1f}, {s.quantile(.75):.1f}]"

L = []
def w(s=""):
    L.append(s)

# =====================================================================
w("# Aim 1a — Code × Note Cross-tabulation and Chart-Review Sampling Frame\n")
w("> **This 2×2 compares two COMPUTABLE PHENOTYPES (ICD code vs frozen note rule "
  "v1.1.0). It is NOT an adjudicated estimate.** The headline Aim 1a figure — the "
  "population-weighted fraction of gold-standard-positive admissions that codes "
  "miss — REQUIRES the chart review sampled below, which HAS NOT YET OCCURRED. No "
  "number here is a recovery estimate; the code−/note+ cell is a sampling stratum, "
  "not a count of missed cases.\n")
w(f"Population: cleaned locked analysis population, N = {N:,} admissions "
  f"({df.subject_id.nunique():,} subjects). Note-positive = Tier A definite. "
  f"Reproducers: `scripts/build_2x2.py`, `scripts/aim1a_report.py`.\n")

# ---------------- STEP 1: four 2x2 ----------------
def cells(notecol):
    nt = df[notecol].astype(bool)
    return {"code+/note+": int((cp & nt).sum()), "code-/note+": int((~cp & nt).sum()),
            "code+/note-": int((cp & ~nt).sum()), "code-/note-": int((~cp & ~nt).sum())}
def subj_cells(notecol):
    g = df.groupby("subject_id").agg(c=("code_positive", "max"), n=(notecol, "max"))
    c = g.c.astype(bool); nt = g.n.astype(bool)
    return {"code+/note+": int((c & nt).sum()), "code-/note+": int((~c & nt).sum()),
            "code+/note-": int((c & ~nt).sum()), "code-/note-": int((~c & ~nt).sum())}, len(g)

CONF = [("note_a", "(a) v1.1.0 inpatient-linked"),
        ("note_b", "(b) v1.1.0 + outpatient 365/30  — **PRIMARY**"),
        ("note_c", "(c) v1.1.0 + outpatient 90/30  (sensitivity)"),
        ("note_d", "(d) v1.0.0 inpatient-linked  (rule-version sensitivity)")]
w("## Step 1 — The 2×2 (four versions)\n")
w("### Admission grain (primary), n (% of population)\n")
w("| version | code+/note+ | code−/note+ | code+/note− | code−/note− |")
w("| --- | --: | --: | --: | --: |")
for col, lab in CONF:
    c = cells(col)
    w(f"| {lab} | {c['code+/note+']:,} ({100*c['code+/note+']/N:.2f}%) "
      f"| {c['code-/note+']:,} ({100*c['code-/note+']/N:.2f}%) "
      f"| {c['code+/note-']:,} ({100*c['code+/note-']/N:.2f}%) "
      f"| {c['code-/note-']:,} ({100*c['code-/note-']/N:.2f}%) |")
w("")
w("### Subject grain (secondary)\n")
w("Collapse rule: a subject is **code+** if ANY of their admissions is code+, and "
  "**note+** if ANY admission is note+ (under that version).\n")
w("| version | subjects | code+/note+ | code−/note+ | code+/note− | code−/note− |")
w("| --- | --: | --: | --: | --: | --: |")
for col, lab in CONF:
    c, ns = subj_cells(col)
    w(f"| {lab} | {ns:,} | {c['code+/note+']:,} | {c['code-/note+']:,} "
      f"| {c['code+/note-']:,} | {c['code-/note-']:,} |")
w("")
ra = cells("note_a")["code-/note+"]; rd = cells("note_d")["code-/note+"]
rb = cells("note_b")["code-/note+"]
w(f"**Rule-version dependence (isolated — both inpatient-linked, code−/note+ cell):** "
  f"v1.1.0 (a) = {ra:,} vs v1.0.0 (d) = {rd:,}. The pre-revision lexicon would have made "
  f"this cell **{rd-ra:+,} larger ({100*(rd-ra)/ra:+.1f}%)**, driven by bare-`fatty` false "
  f"positives (predominantly code-negative). The primary headline uses (b) = {rb:,}; (d) is "
  f"a sensitivity reference so the manuscript can state how much the count depends on the "
  f"lexicon revision — NOT a competing estimate.\n")

# ---------------- STEP 2: recovery zone + code+/note- ----------------
w("## Step 2 — Recovery zone & code+/note− (descriptive; SMDs, not p-values)\n")
rz = df[df.cell_b == "code-/note+"]      # recovery zone
cc = df[df.cell_b == "code+/note+"]      # concordant positives
w(f"### code−/note+ (recovery zone, n={len(rz):,}) vs code+/note+ (n={len(cc):,})\n")
w("| variable | code−/note+ | code+/note+ | SMD |")
w("| --- | --- | --- | --: |")
for lab, col in [("Age at admission, median [IQR]", "age"),
                 ("Length of stay (days)", "los_days"),
                 ("Distinct diagnoses", "n_diagnoses")]:
    w(f"| {lab} | {med_iqr(rz[col])} | {med_iqr(cc[col])} | {smd_cont(rz[col], cc[col]):+.3f} |")
pm1 = (rz.gender == "M").mean(); pm0 = (cc.gender == "M").mean()
w(f"| Male, % | {100*pm1:.1f}% | {100*pm0:.1f}% | {smd_bin(pm1, pm0):+.3f} |")
for lab, col in [("Race (multinomial)", "race"), ("Insurance (multinomial)", "insurance"),
                 ("Language (multinomial)", "language"), ("Admission type (multinomial)", "admission_type")]:
    w(f"| {lab} | — | — | {smd_multi(rz[col], cc[col]):+.3f} |")
w("")
w("Lab availability (available = has ≥1 result; SMD of availability):\n")
w("| analyte | code−/note+ avail% | code+/note+ avail% | SMD |")
w("| --- | --: | --: | --: |")
for a in LAB_AVAIL:
    mc = f"miss_lab_{a}"
    if mc not in df.columns:
        continue
    av1 = (~rz[mc]).mean(); av0 = (~cc[mc]).mean()
    w(f"| {a} | {100*av1:.1f}% | {100*av0:.1f}% | {smd_bin(av1, av0):+.3f} |")
w("")
# code+/note-
cn = df[df.cell_b == "code+/note-"]
w(f"### code+/note− (n={len(cn):,}) — coded, no detectable note evidence (describe, do not adjudicate)\n")
w(f"- **Note-source availability:** {100*cn.has_dc.mean():.1f}% have a linked discharge "
  f"note, {100*cn.has_rad.mean():.1f}% a radiology note "
  f"({100*(cn.has_dc | cn.has_rad).mean():.1f}% either) — so a share have documents that "
  f"simply lack detectable steatosis language; the remainder have no linked note at all.")
w(f"- **LOS:** median {med_iqr(cn.los_days)} days.")
w(f"- **MASLD code seq_num:** principal (seq=1) {100*(cn.masld_min_seq==1).mean():.1f}%; "
  f"median seq {cn.masld_min_seq.median():.0f} [{cn.masld_min_seq.quantile(.25):.0f}, "
  f"{cn.masld_min_seq.quantile(.75):.0f}]. seq_num distribution (min MASLD seq):")
sd = cn.masld_min_seq.value_counts().sort_index()
w("")
w("| min MASLD seq_num | n |")
w("| --: | --: |")
for s, n in sd.head(15).items():
    w(f"| {int(s)} | {n:,} |")
if len(sd) > 15:
    w(f"| >15 | {int(sd[sd.index > 15].sum()):,} |")
w("")

# ---------------- STEP 3: equity, cell sizes FIRST ----------------
w("## Step 3 — Equity stratification (CELL SIZES FIRST; floor = 11 for code−/note+)\n")
w("Using the primary (b) definition. **No recovery rates are computed.** Strata are "
  "NOT collapsed — failures are listed for the researcher to decide on.\n")
def strat(colname, title):
    w(f"### By {title}\n")
    w("| stratum | code+/note+ | code−/note+ | code+/note− | code−/note− | code−/note+ ≥11? |")
    w("| --- | --: | --: | --: | --: | :--: |")
    analysable, failing = [], []
    for val, g in df.groupby(colname):
        c = {"pp": int(((g.code_positive) & g.note_b).sum()),
             "np": int(((~g.code_positive) & g.note_b).sum()),
             "pn": int(((g.code_positive) & ~g.note_b).sum()),
             "nn": int(((~g.code_positive) & ~g.note_b).sum())}
        ok = c["np"] >= FLOOR
        (analysable if ok else failing).append((str(val), c["np"]))
        w(f"| {str(val)[:40]} | {c['pp']:,} | {c['np']:,} | {c['pn']:,} | {c['nn']:,} "
          f"| {'yes' if ok else 'NO'} |")
    w("")
    w(f"**Analysable ({title}, code−/note+ ≥ {FLOOR}):** "
      + ", ".join(f"{v} ({n})" for v, n in sorted(analysable, key=lambda x: -x[1])) + ".")
    w(f"\n**NOT analysable (below floor):** "
      + (", ".join(f"{v} ({n})" for v, n in sorted(failing, key=lambda x: -x[1])) or "none")
      + ".\n")
    return analysable, failing
strat("race", "race")
strat("insurance", "insurance")

# ---------------- STEP 4: sampling frame ----------------
w("## Step 4 — Chart-review sampling frame\n")
sizes = cells("note_b")
w(f"Allocation (per docs/reference_standard.md, ~400 charts), cell assignment by "
  f"PRIMARY (b). Random seed **{SEED}** (also in `scripts/aim1a_report.py`).\n")
w("| cell | population N | allocation | enough to sample? |")
w("| --- | --: | --: | :--: |")
stop = False
for cell, alloc in ALLOC.items():
    n_pop = sizes[cell]
    ok = n_pop >= alloc
    stop = stop or not ok
    w(f"| {cell} | {n_pop:,} | {alloc} | {'yes' if ok else 'NO — too small'} |")
w("")
if stop:
    w("**STOP: a cell is smaller than its allocation; sampling not drawn.**")
    with open(DOC, "w") as fh:
        fh.write("\n".join(L) + "\n")
    raise SystemExit("A cell is smaller than its allocation — see doc.")

rng = np.random.default_rng(SEED)
parts = []
for cell, alloc in ALLOC.items():
    pool = df[df.cell_b == cell]
    idx = rng.choice(pool.index.values, size=alloc, replace=False)
    s = df.loc[idx, ["hadm_id", "subject_id"]].copy()
    s["cell"] = cell
    s["weight"] = sizes[cell] / alloc          # population-weight for reweighting
    parts.append(s)
sample = pd.concat(parts, ignore_index=True)
# blinded review IDs: shuffle so order/ID do not encode cell
perm = rng.permutation(len(sample))
sample = sample.iloc[perm].reset_index(drop=True)
sample["review_id"] = [f"R{ i+1:04d}" for i in range(len(sample))]
# double-review overlap subset (not reviewer-visible)
n_dr = int(round(DOUBLE_REVIEW_FRAC * len(sample)))
dr_idx = rng.choice(sample.index.values, size=n_dr, replace=False)
sample["double_review"] = sample.index.isin(dr_idx)

sample = sample[["review_id", "hadm_id", "subject_id", "cell", "double_review", "weight"]]
duckdb.connect().register("s", sample)  # noqa
con2 = duckdb.connect(); con2.register("s", sample)
con2.execute(f"COPY s TO '{SAMPLE_OUT}' (FORMAT parquet)")

w(f"**Drawn: {len(sample)} charts** written to `{SAMPLE_OUT}` (credentialed, gitignored). "
  f"Blinded IDs R0001–R{len(sample):04d} assigned AFTER a seeded shuffle, so neither the "
  f"ID nor the row order encodes cell membership; the reviewer-facing view excludes `cell` "
  f"and `double_review`.\n")
w(f"**Double review (Cohen's κ):** {n_dr} charts ({100*DOUBLE_REVIEW_FRAC:.0f}%) flagged "
  f"`double_review` in the master key only.\n")
w("### Sampling weights (population reweighting)\n")
w("Disproportionate sampling → each cell reweighted to its population frequency. For a "
  "sampled chart in cell *c*: **weight = N_pop(c) / n_sample(c)**. The headline 1a estimate "
  "(of adjudicated gold-positive admissions, the population-weighted fraction that are "
  "code-negative) is computed as Σ wᵢ·[code−] / Σ wᵢ over gold-positive sampled charts.\n")
w("| cell | N_pop | n_sample | weight = N_pop / n_sample |")
w("| --- | --: | --: | --: |")
for cell, alloc in ALLOC.items():
    w(f"| {cell} | {sizes[cell]:,} | {alloc} | {sizes[cell]/alloc:,.1f} |")
w("")
w("---\n")
w("*This document reports a computable-phenotype comparison and a sampling design only. "
  "The Aim 1a recovery estimate is not final and requires the chart adjudication that "
  "this frame is built to enable.*")

with open(DOC, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {DOC} and {SAMPLE_OUT} (sample n={len(sample)}, seed={SEED})")
print(f"cell sizes (primary b): {sizes}")
