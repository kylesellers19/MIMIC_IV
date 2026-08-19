#!/usr/bin/env python3
"""STEPS 3-6 — SLD subclassification, secondary recovery estimates, historical/current,
and docs/sld_subclassification.md assembly. Aggregate only.

Run (after cmrf.py and note_historical.py): python scripts/sld_report.py
"""
import os
import numpy as np
import pandas as pd
import duckdb

SCRATCH = os.environ.get("SCRATCH", "/tmp")
DOC = "docs/sld_subclassification.md"
con = duckdb.connect()
fr = con.execute("""SELECT hadm_id, code_positive, note_b, age, gender, race, insurance,
    los_days, n_diagnoses FROM read_parquet('data/processed/aim1a_frame.parquet')""").fetchdf()
cm = con.execute("SELECT * FROM read_parquet('data/processed/cmrf.parquet')").fetchdf()
hs = con.execute("SELECT * FROM read_parquet('data/processed/note_historical.parquet')").fetchdf()
df = fr.merge(cm, on="hadm_id", how="left").merge(hs, on="hadm_id", how="left")
for c in ["cmrf_ge1", "cmrf_unasc_all", "alcohol", "viral", "other_etio", "cirrhosis", "hcc",
          "pos_inp", "cur_inp", "pmh_hit", "nonpmh_hit"]:
    df[c] = df[c].fillna(False).astype(bool)
df["cell"] = df.apply(lambda r: ("code+" if r.code_positive else "code-") +
                      ("/note+" if r.note_b else "/note-"), axis=1)
CAVEAT = ("*MetALD caveat: MIMIC has no quantified alcohol intake, so the consensus "
          "thresholds (140–350 g/wk female, 210–420 g/wk male) cannot be applied. Alcohol "
          "status is proxied by ICD codes, which capture disorder-level use, not the moderate "
          "band the MetALD definition specifies. This is a proxy, not an implementation.*")

L = []
def w(s=""): L.append(s)

# ---------------- STEP 3 ----------------
def subclass(r):
    if r.cmrf_unasc_all: return "Unclassifiable"
    if r.cmrf_ge1: return "MetALD" if r.alcohol else "MASLD"
    return "ALD" if r.alcohol else "Cryptogenic"
npos = df[df.note_b].copy()
npos["sld"] = npos.apply(subclass, axis=1)
w("## Step 3 — SLD subclassification of note-positive admissions\n")
w(CAVEAT + "\n")
w("Subclassification applies only to note-positive (documented-steatosis) admissions. "
  "The two note-NEGATIVE cells have no note-documented steatosis and are not "
  "SLD-subclassifiable at the note level.\n")
w("| SLD class | code+/note+ | code−/note+ | all note+ |")
w("| --- | --: | --: | --: |")
cc = npos[npos.code_positive]; nn = npos[~npos.code_positive]
for sld in ["MASLD", "MetALD", "ALD", "Cryptogenic", "Unclassifiable"]:
    a = int((cc.sld == sld).sum()); b = int((nn.sld == sld).sum()); t = a + b
    w(f"| {sld} | {a:,} ({100*a/len(cc):.1f}%) | {b:,} ({100*b/len(nn):.1f}%) | {t:,} ({100*t/len(npos):.1f}%) |")
w("")
met = int((npos.sld == "MetALD").sum())
w(f"### MetALD — reported prominently and separately\n")
w(f"**{met:,} note-positive admissions are MetALD-consistent** "
  f"({100*met/len(npos):.1f}% of note-positive; code−/note+ {int((nn.sld=='MetALD').sum()):,}, "
  f"code+/note+ {int((cc.sld=='MetALD').sum()):,}). **MetALD has no ICD code at all**, so this "
  f"group cannot be captured by the code axis even in principle — it exists only in the "
  f"note/steatosis space. {CAVEAT}\n")

# ---------------- STEP 4 ----------------
w("## Step 4 — Primary 2×2 (steatosis level) + secondary analyses\n")
w("The primary 2×2 is **not** gated on CMRF (the code axis requires no CMRF; gating one "
  "axis only would compare non-comparable constructs). Recovery estimate = code−/note+ ÷ "
  "all note+.\n")
def rec(mask_notepos):
    d = df[mask_notepos]
    npp = int(((~d.code_positive)).sum()); pp = len(d) - npp
    return len(d), npp, (100 * npp / len(d) if len(d) else float("nan"))
defs = [
    ("PRIMARY: steatosis (note+, as built)", df.note_b),
    ("(i) steatosis excluding alcohol-related codes", df.note_b & ~df.alcohol),
    ("(ii) steatosis + ≥1 CMRF (MASLD-consistent)", df.note_b & df.cmrf_ge1),
    ("(iii) steatosis excl. ALL competing etiologies [NAFLD-era]",
     df.note_b & ~(df.alcohol | df.viral | df.other_etio | df.cirrhosis | df.hcc)),
]
w("| definition | note+ (all) | code−/note+ | recovery % |")
w("| --- | --: | --: | --: |")
for lab, mask in defs:
    n, npp, r = rec(mask)
    w(f"| {lab} | {n:,} | {npp:,} | {r:.1f}% |")
w("\n(iii) is labeled the **NAFLD-era comparison**: NAFLD was defined by exclusion of other "
  "liver disease, whereas **MASLD is defined POSITIVELY** (steatosis + ≥1 CMRF) and does NOT "
  "require ruling out competing etiologies. Under current nomenclature (Rinella 2023), "
  "definition (iii) is therefore NOT the primary phenotype.\n")

# ---------------- STEP 5 ----------------
w("## Step 5 — Recovery zone: historical vs current triggering mention\n")
rz = df[(df.cell == "code-/note+")].copy()
# (A) frozen-rule ConText temporality flag
rz["ctx_current"] = rz.cur_inp | (rz.note_b & ~rz.pos_inp)
ctx_hist = int((~rz.ctx_current).sum())
# (B) section-based: hit only in a PAST MEDICAL/SURGICAL HISTORY section (no current/imaging)
rz["current"] = rz.nonpmh_hit | (rz.note_b & ~rz.pos_inp)
rz["hist_only"] = ~rz.current
nc = int(rz.current.sum()); nh = int(rz.hist_only.sum())
w(f"Recovery zone n={len(rz):,}. Two 'historical' measures (they support different claims):\n")
w(f"- **(A) Frozen-rule ConText temporality flag** ('history of', 'h/o'…): historical-only "
  f"{ctx_hist:,} ({100*ctx_hist/len(rz):.1f}%). Strict — fires only on an explicit temporal cue.")
w(f"- **(B) Section-based** — triggering hit only in a PAST MEDICAL/SURGICAL HISTORY section, "
  f"with no current-section or imaging mention: **historical-only {nh:,} ({100*nh/len(rz):.1f}%)**; "
  f"**current {nc:,} ({100*nc/len(rz):.1f}%)**.\n")
w("Comparison below uses (B), the 'documented prior diagnosis (still uncoded) vs new finding "
  "(uncoded)' distinction.\n")
def smd_c(a, b):
    a, b = a.dropna(), b.dropna()
    d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return np.nan if d == 0 else (a.mean() - b.mean()) / d
def smd_b(p1, p0):
    d = np.sqrt((p1*(1-p1) + p0*(1-p0)) / 2)
    return np.nan if d == 0 else (p1 - p0) / d
cur, his = rz[rz.current], rz[rz.hist_only]
w("| variable | current | historical-only | SMD |")
w("| --- | --- | --- | --: |")
for lab, col in [("Age median [IQR]", "age"), ("LOS median [IQR]", "los_days"),
                 ("Distinct diagnoses median [IQR]", "n_diagnoses")]:
    def mi(s): s = s.dropna(); return f"{s.median():.1f} [{s.quantile(.25):.1f}, {s.quantile(.75):.1f}]"
    w(f"| {lab} | {mi(cur[col])} | {mi(his[col])} | {smd_c(cur[col], his[col]):+.3f} |")
w(f"| Male % | {100*(cur.gender=='M').mean():.1f}% | {100*(his.gender=='M').mean():.1f}% | "
  f"{smd_b((cur.gender=='M').mean(),(his.gender=='M').mean()):+.3f} |")
w(f"| ≥1 CMRF % | {100*cur.cmrf_ge1.mean():.1f}% | {100*his.cmrf_ge1.mean():.1f}% | "
  f"{smd_b(cur.cmrf_ge1.mean(),his.cmrf_ge1.mean()):+.3f} |")
w("")
for grp in ["race", "insurance"]:
    cr = (cur[grp].value_counts(normalize=True) * 100).round(1)
    hr = (his[grp].value_counts(normalize=True) * 100).round(1)
    top = df[grp].value_counts().head(4).index
    w(f"- **{grp}** (top): " + "; ".join(
        f"{v} cur {cr.get(v,0):.0f}%/hist {hr.get(v,0):.0f}%" for v in top))
w("")

# ---------------- assemble doc ----------------
with open(os.path.join(SCRATCH, "frag_cmrf.md")) as fh:
    cmrf_frag = fh.read()
header = f"""# SLD Subclassification and MASLD-Consistent Recovery — MIMIC-IV

> **MASLD is defined POSITIVELY** (hepatic steatosis + ≥1 cardiometabolic risk factor);
> unlike NAFLD it does **not** require excluding other liver disease. The primary 2×2
> stays at the steatosis level; CMRF and etiology enter only as pre-specified secondary
> analyses.

**Nomenclature source:** Rinella ME, Lazarus JV, Ratziu V, et al. A multisociety Delphi
consensus statement on new fatty liver disease nomenclature. *J Hepatol.* 2023
Dec;79(6):1542–1556. doi:10.1016/j.jhep.2023.06.003. PMID: 37364790.

**Data limitation (prescriptions-only):** medication treatment status is established from
`prescriptions` (drug name, GSN, NDC, dose, route, dates) — MIMIC-IV's medication-order
table and sufficient for "current treatment" as the consensus specifies. `pharmacy` (adds
dispensing-level detail relevant to adherence/dosing, not treatment status) was not
fetched; documented here as a completeness limitation.

## Approved drug-class lists — exclusions & rationale (Step 1b)

Matching is drug-name-based (GSN/NDC present for audit), restricted to the locked
population, ophthalmic route excluded. Corrections kept: ophthalmic timolol /
dorzolamide-timolol excluded on route; clopidogrel & ticlopidine excluded from
lipid-lowering (antiplatelets); aspartame & niacinamide excluded.

- **Beta-blockers — EXCLUDED from criterion 3.** The 13,080 admissions positive by
  beta-blocker alone have no HTN code and no BP ≥130/85 anywhere in the stay; a
  hypertensive inpatient would generate one or the other. Residual = heart failure,
  arrhythmia/rate-control, post-MI.
- **Insulin — EXCLUDED from criterion 2.** The 8,251 positive by insulin alone have no
  dysglycemia code, no HbA1c ≥5.7, no glucose ≥100; a diabetic on insulin would exceed
  glucose 100 at some point. prescriptions cannot separate home insulin from inpatient
  sliding-scale, so the class is excluded; explicit "insulin for hyperkalemia" strings
  excluded on indication regardless.
- **Metformin — INCLUDED** (102 positive by metformin alone; overwhelmingly diabetes/prediabetes).
- **Hydralazine, metolazone, alpha-blockers (doxazosin/terazosin/prazosin) — EXCLUDED
  from criterion 3** (IV hypertensive-urgency & HFrEF regimens; HF diuresis/ascites — and
  12.8% of the recovery zone carries cirrhosis codes, so metolazone would preferentially
  misclassify the group of most interest; alpha-blockers are BPH-dominant).

"""
with open(DOC, "w") as fh:
    fh.write(header + cmrf_frag + "\n" + "\n".join(L) + "\n")
print(f"wrote {DOC}")
print(f"MetALD note+ = {met:,} | recovery primary={rec(df.note_b)[2]:.1f}% "
      f"MASLD-consistent(ii)={rec(df.note_b & df.cmrf_ge1)[2]:.1f}%")
print(f"recovery zone current={nc:,} historical-only={nh:,}")
