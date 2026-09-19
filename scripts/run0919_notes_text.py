#!/usr/bin/env python3
"""run_2026-09-19 Phase 3.1–3.3 — per-admission text assembly under the primary linkage, three variants.

Variants (lexicon imported from the frozen rule, never copied):
  U unmasked · M span-masked (every lexicon match, all tiers, any assertion status -> [MASK]) ·
  S sentence-deleted (every sentence containing any lexicon match removed).
Section-targeted extraction with the project's line-initial `Label:` header parser (corpus_explore.py).
Priority: liver-inclusive radiology (full) -> other radiology IMPRESSION -> discharge sections in a fixed order.
Budget: CHAR_BUDGET characters ≈ 12 chunks × 512 tokens. Output parquet is credentialed (untracked). No text is printed.

Modes:  --pilot            200 random DEV admissions (seed SEED_NOTES_SUBSAMPLE) -> pilot.parquet
        --subsample N      N random DEV+TEST subjects' admissions... (simple random sample of SUBJECTS, keeping partition/fold)
                           plus ALL GOLD_HOLDOUT admissions -> subsample.parquet
"""
import argparse, os, re, sys, time, json
from collections import Counter
import duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.getcwd())
from scripts.note_phenotype import TRIGGERS, SENT_SPLIT, SCREEN, NOTE
from scripts.masld_config import LOCKED_POP, SPLITS_V1, SEED_NOTES_SUBSAMPLE

IDX = "data/processed/run_2026-09-19_notes_index"
OUTDIR = "data/processed/run_2026-09-19_notes_text"
CHAR_BUDGET = 22000            # ≈ 12 × 512 tokens at ~3.6 chars/token for clinical text, with margin
HEADER_RE = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9 /,()'-]{1,45}?):")   # same pattern as corpus_explore.py
DC_PRIORITY = ["DISCHARGE DIAGNOSIS", "PAST MEDICAL HISTORY", "PERTINENT RESULTS", "BRIEF HOSPITAL COURSE",
               "HISTORY OF PRESENT ILLNESS", "CHIEF COMPLAINT", "IMPRESSION", "ABDOMEN", "ABD", "SOCIAL HISTORY",
               "MAJOR SURGICAL OR INVASIVE PROCEDURE", "PHYSICAL EXAM"]
DC_SKIP = {"NAME", "DATE OF BIRTH", "ADMISSION DATE", "DISCHARGE DATE", "SEX", "SERVICE", "ATTENDING", "ALLERGIES",
           "DISCHARGE INSTRUCTIONS", "FOLLOWUP INSTRUCTIONS", "DISCHARGE MEDICATIONS", "MEDICATIONS ON ADMISSION",
           "DISCHARGE DISPOSITION", "FACILITY", "DISCHARGE CONDITION", "MENTAL STATUS", "LEVEL OF CONSCIOUSNESS", "ACTIVITY STATUS"}
MASK = "[MASK]"

def sections(text):
    """-> list of (LABEL, body) in document order."""
    hs = [(m.start(), m.end(), m.group(1).strip().upper()) for m in HEADER_RE.finditer(text)]
    out = []
    for i, (s, e, lab) in enumerate(hs):
        body_end = hs[i + 1][0] if i + 1 < len(hs) else len(text)
        out.append((lab, text[e:body_end].strip()))
    if not hs:
        out.append(("BODY", text))
    return out

def dc_extract(text):
    secs = sections(text)
    by = {}
    for lab, body in secs:
        by.setdefault(lab, []).append(body)
    parts = []
    for lab in DC_PRIORITY:
        for b in by.pop(lab, []):
            if b: parts.append(f"{lab.title()}: {b}")
    for lab, bodies in by.items():          # remaining, in document order, boilerplate skipped
        if lab in DC_SKIP: continue
        for b in bodies:
            if b: parts.append(f"{lab.title()}: {b}")
    return parts

def rad_impression(text):
    i = text.upper().rfind("IMPRESSION:")
    return text[i:] if i >= 0 else text[-600:]

def mask_spans(text):
    for name, rx, tier, scope in TRIGGERS:
        text = rx.sub(MASK, text)
    return text

def delete_sentences(text):
    keep = []
    for seg in SENT_SPLIT.split(text):
        low = seg.lower()
        if any(s in low for s in SCREEN) and any(rx.search(seg) for _, rx, _, _ in TRIGGERS):
            continue
        keep.append(seg)
    return " ".join(k for k in keep if k)

def assemble(adm):
    """adm: DataFrame hadm_id, subject_id, admittime. Returns DataFrame with texts + counts."""
    con = duckdb.connect(); con.execute("SET memory_limit='16GB'")
    con.register("adm", adm[["hadm_id", "subject_id", "admittime"]])
    dc = con.execute(f"""SELECT n.hadm_id, n.text FROM read_csv_auto('{NOTE}/discharge.csv.gz') n
                         WHERE n.hadm_id IN (SELECT hadm_id FROM adm)""").fetchdf()
    rad = con.execute(f"""SELECT n.note_id, n.hadm_id, n.subject_id, n.charttime, n.text FROM read_csv_auto('{NOTE}/radiology.csv.gz') n
                          WHERE n.hadm_id IN (SELECT hadm_id FROM adm)
                             OR (n.hadm_id IS NULL AND n.subject_id IN (SELECT subject_id FROM adm))""").fetchdf()
    liv = con.execute(f"SELECT note_id, liver_incl FROM read_parquet('{IDX}/radiology.parquet')").fetchdf()
    rad = rad.merge(liv, on="note_id", how="left"); rad["liver_incl"] = rad.liver_incl.fillna(False).astype(bool)
    rad["charttime"] = pd.to_datetime(rad.charttime)
    dc_by = dc.groupby("hadm_id").text.apply(list).to_dict()
    inp_by = rad[rad.hadm_id.notna()].groupby("hadm_id").apply(lambda g: list(zip(g.charttime, g.liver_incl, g.text))).to_dict()
    outp = rad[rad.hadm_id.isna()]
    out_by = outp.groupby("subject_id").apply(lambda g: list(zip(g.charttime, g.liver_incl, g.text))).to_dict()
    rows = []; exc = Counter()
    for r in adm.itertuples(index=False):
        try:
            at = pd.Timestamp(r.admittime)
            rads = list(inp_by.get(r.hadm_id, []))
            n_out = 0
            for ct, li, tx in out_by.get(r.subject_id, []):
                d = (ct - at).total_seconds() / 86400.0
                if -365 <= d <= 30:
                    rads.append((ct, li, tx)); n_out += 1
            rads.sort(key=lambda x: x[0], reverse=True)
            parts = [tx for ct, li, tx in rads if li] + [rad_impression(tx) for ct, li, tx in rads if not li]
            for t in dc_by.get(r.hadm_id, []):
                parts += dc_extract(t)
            U = ""
            for p in parts:
                if len(U) >= CHAR_BUDGET: break
                U += p[:CHAR_BUDGET - len(U)] + "\n\n"
            U = U.strip()
            M = mask_spans(U); S = delete_sentences(U)
            rows.append((r.hadm_id, r.subject_id, len(dc_by.get(r.hadm_id, [])), len(inp_by.get(r.hadm_id, [])), n_out,
                         sum(1 for _, li, _ in rads if li), len(U), len(M), len(S), M.count(MASK), U, M, S))
        except Exception as e:
            exc[type(e).__name__] += 1
    print(f"assembled {len(rows):,} admissions; exceptions by class: {dict(exc)}", flush=True)
    return pd.DataFrame(rows, columns=["hadm_id", "subject_id", "n_dc", "n_rad_inp", "n_rad_out", "n_rad_liver",
                                       "len_U", "len_M", "len_S", "n_masked", "text_U", "text_M", "text_S"])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pilot", action="store_true"); ap.add_argument("--subsample", type=int, default=0)
    a = ap.parse_args(); t0 = time.time()
    con = duckdb.connect()
    base = con.execute(f"""SELECT s.hadm_id, s.subject_id, s.partition, s.fold, f.note_b, f.code_positive, l.admittime
                           FROM read_parquet('{SPLITS_V1}') s JOIN read_parquet('data/processed/aim1a_frame.parquet') f USING (hadm_id)
                           JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""").fetchdf()
    rng = np.random.default_rng(SEED_NOTES_SUBSAMPLE)
    if a.pilot:
        dev = base[base.partition == "DEV"]
        sel = dev.iloc[rng.choice(len(dev), 200, replace=False)]
        out = f"{OUTDIR}/pilot.parquet"
    else:
        subj = base[base.partition != "GOLD_HOLDOUT"].subject_id.drop_duplicates().to_numpy()
        pick = set(rng.choice(subj, a.subsample, replace=False))
        sel = pd.concat([base[base.subject_id.isin(pick)], base[base.partition == "GOLD_HOLDOUT"]])
        out = f"{OUTDIR}/subsample.parquet"
    df = assemble(sel).merge(sel[["hadm_id", "partition", "fold", "note_b", "code_positive"]], on="hadm_id")
    con.register("df", df); con.execute(f"COPY df TO '{out}' (FORMAT parquet)")
    summ = {"n": int(len(df)), "by_partition": {str(k): int(v) for k, v in df.partition.value_counts().items()},
            "prevalence_pct": round(100 * float(df.note_b.mean()), 2),
            "len_U_median": int(df.len_U.median()), "len_S_median": int(df.len_S.median()), "len_M_median": int(df.len_M.median()),
            "pct_at_budget": round(100 * float((df.len_U >= CHAR_BUDGET - 50).mean()), 1),
            "n_masked_median": float(df.n_masked.median()), "pct_with_liver_rad": round(100 * float((df.n_rad_liver > 0).mean()), 1),
            "seconds": round(time.time() - t0)}
    json.dump(summ, open(f"{out}.summary.json", "w"), indent=1); print(json.dumps(summ))
