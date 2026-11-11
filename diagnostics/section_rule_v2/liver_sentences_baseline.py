#!/usr/bin/env python3
"""Liver-sentence extractor that does not know the disease vocabulary.

WHAT THIS IS
    Given a note, keep only the sentences that mention the liver, and record where each one came
    from. It selects on ANATOMY alone. It has no idea what steatosis, fatty change or echogenicity
    are, and cannot be tuned toward them, because it never sees the trigger lexicon.

WHAT IT REUSES FROM THE FROZEN RULE (scripts/note_phenotype.py)
    SENT_SPLIT     the sentence splitter, unchanged - no new splitter is written here
    TARGET_ORGANS  {liver, hepatic, hepatis}, used to derive and document the prefixes below
    _tokenize      the same word tokenizer the rule uses

WHAT IT DELIBERATELY DOES NOT IMPORT
    TRIGGERS and SCREEN. The module asserts at import time that neither name reached its namespace.
    _anatomical is also not used: its strict=False branch returns True for a sentence with NO liver
    word whenever no competing organ is present, which would admit sentences this extractor must
    reject. The liver word must be in the sentence itself.

ANATOMY TEST
    Two modes, both computed in a single pass so they can be compared on identical input:
      prefix (default)  a token CONTAINING "hepat", or a token STARTING WITH "liver". Catches
                        hepatomegaly, hepatitis, intrahepatic, perihepatic, hepatocellular,
                        hepatobiliary, liver's.
      token             a token equal to a TARGET_ORGANS member. The narrower original behaviour.
    The wide set is a strict superset of the narrow set.

    WHY THE TWO SIDES ARE NOT SYMMETRIC. "hepat" is matched anywhere in the token because the
    requested examples include intrahepatic and perihepatic, which contain it rather than start with
    it, and no common English word outside the liver contains "hepat". "liver" is matched only at the
    start of a token, because containment would match deliver, delivery and delivered, which are
    common in discharge summaries and have nothing to do with the liver.

    NOTE ON COMPETING ORGANS. This extractor has never applied COMPETING_ORGANS suppression and none
    is added here. Selection is liver-presence only: a sentence naming both the pancreas and the
    liver is kept. Suppression lives in the frozen rule's _anatomical, which this file does not use.
    Adding it would change what is selected and is not done silently.

    PREFIX SIDE EFFECTS, STATED RATHER THAN HIDDEN. "hepat" also matches hepatitis, which is a
    different disease, and hepatic flexure, which is colon. The instruction was to match those
    strings; they are kept and counted, not filtered.

OUTPUT PER ADMISSION
    Kept sentences with note type (discharge / radiology_inpatient / radiology_outpatient), section
    category (impression / findings / other), character offsets within the source note, and a stable
    opaque sentence id. Capped at CAP sentences per admission, impression first, then findings, then
    others, in document order within each group; whether the cap bound is recorded.

OUTPUT SHAPE (--mode)
    per_sentence (default)  one row per kept sentence
    per_admission           one row per admission, the kept sentences joined with newlines in the
                            order already defined. Selection and ordering are identical; only the
                            shape of the emitted rows differs.

PRIVACY
    No sentence text is ever printed. The reporting path emits counts and distributions only. Text is
    carried in memory to measure it and is written out only when --out is passed explicitly.

USAGE
    scripts/run0919_env.sh scripts/liver_sentences.py --selftest
    scripts/run0919_env.sh scripts/liver_sentences.py
    scripts/run0919_env.sh scripts/liver_sentences.py --mode per_admission --out <path.parquet>
"""
import argparse
import hashlib
import re
import sys
import time
from collections import Counter, defaultdict

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts.note_phenotype import SENT_SPLIT, TARGET_ORGANS, _tokenize, NOTE

assert "TRIGGERS" not in globals() and "SCREEN" not in globals(), \
    "liver_sentences must not import the trigger lexicon"

CAP = 40
HEPAT_SUBSTRING = "hepat"   # matched anywhere in a token: intrahepatic, perihepatic
LIVER_PREFIX = "liver"      # matched at token start only: containment would catch "delivered"
assert all(HEPAT_SUBSTRING in o or o.startswith(LIVER_PREFIX) for o in TARGET_ORGANS), \
    "the wide test must cover every TARGET_ORGANS member"
SECTION_RANK = {"impression": 0, "findings": 1, "other": 2}
HEADER_RE = re.compile(r"(?m)^[ \t]*([A-Za-z][A-Za-z0-9 ,/&'()-]{1,58}?)[ \t]*:")
SUBSAMPLE = "data/processed/run_2026-09-19_notes_text/subsample.parquet"
FRAME = "data/processed/aim1a_frame.parquet"
LOCKED_POP = "data/processed/analysis_population.parquet"


# ----------------------------------------------------------------------------- core extraction
# Headings that close a findings block. Union of the radiology and discharge lists, applied to
# both note types, because section_spans sees only the text and not the note type.
RECOGNISED_RADIOLOGY = ["CLINICAL INFORMATION", "EXAMINATION", "COMPARISON", "INDICATION",
                        "TECHNIQUE", "HISTORY", "RECOMMENDATION(S)"]
RECOGNISED_DISCHARGE = ["HISTORY OF PRESENT ILLNESS", "BRIEF HOSPITAL COURSE",
                        "DISCHARGE INSTRUCTIONS", "PAST MEDICAL HISTORY", "DISCHARGE DIAGNOSIS",
                        "PERTINENT RESULTS", "PHYSICAL EXAM"]
BLOCK_TERMINATORS = sorted(set(RECOGNISED_RADIOLOGY) | set(RECOGNISED_DISCHARGE),
                           key=len, reverse=True)


def is_recognised_heading(label):
    return any(label == c or label.startswith(c) for c in BLOCK_TERMINATORS)


def section_spans(text):
    """Cover the note with (start, end, category).

    A findings block opens at a heading containing FINDING and closes at the next heading that is
    IMPRESSION/CONCLUSION or on the recognised lists, or at end of note. An unrecognised heading
    inside an open block inherits `findings`, because organ sub-headings such as HEPATOBILIARY or
    LIVER sit inside a structured findings section and are findings content, not preamble.

    Labels have internal whitespace collapsed before matching the recognised lists; this cannot
    affect the IMPRESSION/FINDING containment tests, which are substring checks."""
    heads = [(m.start(), " ".join(m.group(1).strip().upper().split()))
             for m in HEADER_RE.finditer(text)]
    if not heads:
        return [(0, len(text), "other")]
    spans = []
    if heads[0][0] > 0:
        spans.append((0, heads[0][0], "other"))
    in_findings_block = False
    for i, (start, label) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        if "IMPRESSION" in label or "CONCLUSION" in label:
            cat = "impression"; in_findings_block = False
        elif "FINDING" in label:
            cat = "findings"; in_findings_block = True
        elif is_recognised_heading(label):
            cat = "other"; in_findings_block = False
        elif in_findings_block:
            cat = "findings"                      # inherited from the open block
        else:
            cat = "other"
        spans.append((start, end, cat))
    return spans


def sentence_spans(text):
    """Character spans of sentences, derived from SENT_SPLIT's separator matches."""
    out, pos = [], 0
    for m in SENT_SPLIT.finditer(text):
        if m.start() > pos:
            out.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        out.append((pos, len(text)))
    return out


def category_at(spans, pos):
    for s, e, cat in spans:
        if s <= pos < e:
            return cat
    return "other"


def anatomy_hits(fragment):
    """-> (token_hit, prefix_hit). prefix_hit is a superset of token_hit."""
    tok = pre = False
    for w, _ in _tokenize(fragment.lower()):
        if w in TARGET_ORGANS:
            tok = pre = True
        elif HEPAT_SUBSTRING in w or w.startswith(LIVER_PREFIX):
            pre = True
    return tok, pre


def sentence_id(note_key, start):
    return hashlib.sha1(f"{note_key}|{start}".encode()).hexdigest()[:16]


def extract_from_note(text, note_key):
    """Kept sentences in document order. `token_hit` marks those the narrow mode would also keep."""
    if not text:
        return []
    secs = section_spans(text)
    kept = []
    for start, end in sentence_spans(text):
        frag = text[start:end]
        tok, pre = anatomy_hits(frag)
        if not pre:
            continue
        kept.append({"sid": sentence_id(note_key, start), "char_start": start, "char_end": end,
                     "section": category_at(secs, start), "n_chars": end - start,
                     "n_tokens": len(_tokenize(frag.lower())), "token_hit": tok, "text": frag})
    return kept


def cap_admission(rows, cap=CAP):
    ordered = sorted(rows, key=lambda r: (SECTION_RANK.get(r["section"], 2), r["_order"]))
    return ordered[:cap], len(ordered), len(ordered) > cap


# ----------------------------------------------------------------------------- self test
SELFTEST = [
    # (invented sentence, keep under token mode, keep under prefix mode)
    ("The liver is diffusely echogenic.", True, True),
    ("There is decreased hepatic attenuation relative to the spleen.", True, True),
    ("No evidence of hepatic steatosis.", True, True),
    ("The pancreas is diffusely echogenic.", False, False),
    ("Fatty marrow replacement within the vertebral bodies.", False, False),
    ("The spleen is enlarged.", False, False),
    ("Porta hepatis lymph nodes are not enlarged.", True, True),
    ("Liver function tests are pending.", True, True),
    ("The patient reports abdominal pain.", False, False),
    # newly matched by the prefix change
    ("Hepatomegaly is noted.", False, True),
    ("There is a history of hepatitis C.", False, True),
    ("Intrahepatic ducts are not dilated.", False, True),
    ("A small perihepatic fluid collection is present.", False, True),
    ("Hepatocellular carcinoma was resected.", False, True),
    ("The liver's contour is nodular.", False, True),
    # the stated side effect: colon, not liver
    ("The hepatic flexure is decompressed.", True, True),
    # "liver" is prefix-only so these obstetric words must NOT match
    ("The infant was delivered at term.", False, False),
    ("Delivery was uncomplicated.", False, False),
    ("She was delivered by caesarean section.", False, False),
]


# (name, synthetic note, expected section of the probe sentence). All text invented here.
SECTION_TESTS = [
    ("a  FINDINGS > HEPATOBILIARY > sentence",
     "EXAMINATION: CT abdomen.\nFINDINGS:\nHEPATOBILIARY:\nProbe sentence about the liver.\n",
     "findings"),
    ("b  FINDINGS > LIVER > IMPRESSION > sentence",
     "FINDINGS:\nLIVER:\nNo focal lesion.\nIMPRESSION:\nProbe sentence about the liver.\n",
     "impression"),
    ("c  FINDINGS > HEPATOBILIARY > RECOMMENDATION(S) > sentence",
     "FINDINGS:\nHEPATOBILIARY:\nNo focal lesion.\nRECOMMENDATION(S):\n"
     "Probe sentence about the liver.\n",
     "other"),
    ("d  PERTINENT RESULTS > FINDINGS > LIVER > DISCHARGE LABS > sentence",
     "Pertinent Results:\nFINDINGS:\nLIVER:\nNo focal lesion.\nDISCHARGE LABS:\n"
     "Probe sentence about the liver.\n",
     "other"),
    ("e  plain FINDINGS > sentence",
     "FINDINGS:\nProbe sentence about the liver.\n", "findings"),
    ("f  plain IMPRESSION > sentence",
     "IMPRESSION:\nProbe sentence about the liver.\n", "impression"),
    ("g  no headings at all",
     "Probe sentence about the liver.\n", "other"),
    ("h  INDICATION before any FINDINGS > sentence",
     "INDICATION:\nProbe sentence about the liver.\n", "other"),
]


def section_selftest():
    print("\nsection-assignment fixtures (synthetic text, no MIMIC data)")
    bad = 0
    for name, doc, want in SECTION_TESTS:
        rows = [r for r in extract_from_note(doc, "selftest") if "probe" in r["text"].lower()]
        got = rows[0]["section"] if rows else "(probe sentence not selected)"
        flag = "ok  " if got == want else "FAIL"
        if got != want:
            bad += 1
        print(f"  [{flag}] {name:<52} expected {want:<11} got {got}")
    print(f"  {len(SECTION_TESTS) - bad}/{len(SECTION_TESTS)} as expected")
    return bad == 0


def selftest():
    print("self test on invented strings (no MIMIC data)")
    bad = 0
    for sentence, want_tok, want_pre in SELFTEST:
        tok, pre = anatomy_hits(sentence)
        if tok != want_tok or pre != want_pre:
            bad += 1
            print(f"  MISMATCH: expected token={want_tok} prefix={want_pre}, got token={tok} prefix={pre}")
    print(f"  {len(SELFTEST) - bad}/{len(SELFTEST)} as expected")
    doc = ("EXAMINATION: Abdominal ultrasound.\nFINDINGS: The liver is normal in size. "
           "The spleen is unremarkable.\nIMPRESSION: Echogenic liver.\n")
    rows = extract_from_note(doc, "selftest")
    flat = [dict(r, _order=i) for i, r in enumerate(rows)]
    keep, _, _ = cap_admission(flat)
    print(f"  sections found: {[r['section'] for r in rows]}")
    print(f"  cap ordering:   {[r['section'] for r in keep]}")
    ok_sections = section_selftest()
    return bad == 0 and ok_sections


# ----------------------------------------------------------------------------- corpus run
def build_admission_set(con, partitions):
    q = f"""
      SELECT s.hadm_id, s.subject_id, l.admittime
      FROM read_parquet('{SUBSAMPLE}') s
      JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)
      WHERE s.partition IN ({','.join("'" + p + "'" for p in partitions)})
    """
    adm = con.execute(q).fetchdf()
    adm["admittime"] = pd.to_datetime(adm["admittime"])
    return adm


def per_admission_stats(adm, rows_by_adm, narrow):
    """Order, cap and measure. narrow=True restricts to token-equality hits."""
    recs, kept_all = [], []
    for hadm in adm.hadm_id.astype("int64"):
        notes = sorted(rows_by_adm.get(hadm, []), key=lambda x: (str(x[0]), str(x[1])))
        flat, order = [], 0
        for ct, key, kept in notes:
            for r in kept:
                if narrow and not r["token_hit"]:
                    continue
                flat.append(dict(r, _order=order))
                order += 1
        keep, n_before, bound = cap_admission(flat)
        recs.append({"hadm_id": hadm, "n_sentences": len(keep), "n_before_cap": n_before,
                     "cap_bound": bound, "n_tokens": sum(r["n_tokens"] for r in keep),
                     "n_chars": sum(r["n_chars"] for r in keep)})
        if not narrow:
            for r in keep:
                kept_all.append({"hadm_id": hadm, "sid": r["sid"], "note_type": r["note_type"],
                                 "section": r["section"], "char_start": r["char_start"],
                                 "char_end": r["char_end"], "text": r["text"]})
    return pd.DataFrame(recs), kept_all


def run(partitions, limit, out_path, mode):
    t0 = time.time()
    con = duckdb.connect()
    con.execute("SET memory_limit='12GB'")
    adm = build_admission_set(con, partitions)
    if limit:
        adm = adm.head(limit)
    hadms = set(adm.hadm_id.astype("int64"))
    subs = set(adm.subject_id.astype("int64"))
    print(f"admissions in scope: {len(adm):,} (partitions {', '.join(partitions)})", flush=True)

    rows_by_adm = defaultdict(list)
    out_by_subject = defaultdict(list)
    exc = Counter()
    n_notes = 0
    for table, is_disch in (("discharge", True), ("radiology", False)):
        reader = con.execute(
            f"SELECT note_id, hadm_id, subject_id, charttime, text "
            f"FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
        ).fetch_record_batch(4000)
        for batch in reader:
            d = batch.to_pydict()
            for k in range(len(d["text"])):
                h, sj = d["hadm_id"][k], d["subject_id"][k]
                inpatient = h is not None and int(h) in hadms
                outpatient = (not is_disch) and h is None and sj is not None and int(sj) in subs
                if not (inpatient or outpatient):
                    continue
                n_notes += 1
                try:
                    key = d["note_id"][k]
                    kept = extract_from_note(d["text"][k], key)
                    if not kept:
                        continue
                    ntype = "discharge" if is_disch else ("radiology_inpatient" if inpatient
                                                          else "radiology_outpatient")
                    for r in kept:
                        r["note_type"] = ntype
                    target = rows_by_adm[int(h)] if inpatient else out_by_subject[int(sj)]
                    target.append((d["charttime"][k], key, kept))
                except Exception as e:
                    exc[type(e).__name__] += 1
        print(f"  scanned {table}; notes in scope so far {n_notes:,}  ({time.time()-t0:.0f}s)", flush=True)

    for r in adm.itertuples(index=False):
        for ct, key, kept in out_by_subject.get(int(r.subject_id), []):
            if ct is None:
                continue
            dt = (pd.Timestamp(ct) - r.admittime).total_seconds() / 86400.0
            if -365 <= dt <= 30:
                rows_by_adm[int(r.hadm_id)].append((ct, key, kept))

    wide, kept_rows = per_admission_stats(adm, rows_by_adm, narrow=False)
    narrow, _ = per_admission_stats(adm, rows_by_adm, narrow=True)

    if out_path:
        df = pd.DataFrame(kept_rows)
        if mode == "per_admission":
            df = (df.groupby("hadm_id")
                    .agg(n_sentences=("sid", "size"), text=("text", "\n".join))
                    .reset_index())
        df.to_parquet(out_path, index=False)
        print(f"wrote {out_path} ({len(df):,} rows, mode {mode})")

    report(wide, narrow, kept_rows, con, exc, time.time() - t0)


def q(s, p):
    return float(np.percentile(s, p)) if len(s) else float("nan")


def dist(label, s):
    print(f"  {label:<34} median {q(s,50):>5.0f} | Q1 {q(s,25):>5.0f} | Q3 {q(s,75):>5.0f} | "
          f"p90 {q(s,90):>6.0f} | max {int(s.max()) if len(s) else 0:>5}")


def report(wide, narrow, kept_rows, con, exc, secs):
    n = len(wide)
    wa = wide[wide.n_sentences > 0]
    na = narrow[narrow.n_sentences > 0]
    print("\n" + "=" * 74)
    print("ANATOMY = WIDE: token contains 'hepat', or starts with 'liver'"
          "   [bracketed = previous behaviour, token equality]")
    print("=" * 74)
    print(f"admissions processed            {n:,}")
    print(f"with >=1 liver sentence         {len(wa):,}  ({100*len(wa)/n:.1f}%)   "
          f"[was {len(na):,}  ({100*len(na)/n:.1f}%)]")
    print("\nsentences per admission")
    dist("all admissions", wide.n_sentences)
    dist("  [token equality]", narrow.n_sentences)
    dist("those with >=1", wa.n_sentences)
    dist("  [token equality]", na.n_sentences)
    nb, nb0 = int(wide.cap_bound.sum()), int(narrow.cap_bound.sum())
    print(f"\n{CAP}-sentence cap bound          {nb:,} admissions ({100*nb/n:.2f}%)   "
          f"[was {nb0:,} ({100*nb0/n:.2f}%)]")
    if nb:
        over = wide[wide.cap_bound].n_before_cap
        print(f"  of those, uncapped count: median {q(over,50):.0f} | p90 {q(over,90):.0f} | max {int(over.max())}")
    print("\nword tokens of extracted text per admission (admissions with >=1 sentence)")
    dist("prefix", wa.n_tokens)
    dist("  [token equality]", na.n_tokens)
    print(f"  total {int(wa.n_tokens.sum()):,} word tokens over {len(wa):,} admissions "
          f"[was {int(na.n_tokens.sum()):,} over {len(na):,}]")
    print(f"  characters: median {q(wa.n_chars,50):.0f} | p90 {q(wa.n_chars,90):.0f} | "
          f"total {int(wa.n_chars.sum()):,} [was {int(na.n_chars.sum()):,}]")
    print("  (word tokens from the frozen _tokenize; a subword tokenizer runs higher)")

    # --- what the prefix change moved -----------------------------------------------------
    m = wide[["hadm_id", "n_sentences"]].merge(
        narrow[["hadm_id", "n_sentences"]], on="hadm_id", suffixes=("_pre", "_tok"))
    newly = int(((m.n_sentences_tok == 0) & (m.n_sentences_pre > 0)).sum())
    more = int((m.n_sentences_pre > m.n_sentences_tok).sum())
    print(f"\neffect of the prefix change")
    print(f"  admissions newly non-empty (0 -> >=1)                 {newly:,}  ({100*newly/n:.1f}%)")
    print(f"  admissions with at least one additional sentence      {more:,}  ({100*more/n:.1f}%)")

    # --- the reverse cases ------------------------------------------------------------------
    fr = con.execute(f"SELECT hadm_id, code_positive, note_b FROM read_parquet('{FRAME}')").fetchdf()
    mm = m.merge(fr, on="hadm_id", how="left")
    mm["rule"] = mm.note_b.astype(bool)
    rev_tok = mm[(mm.n_sentences_tok == 0) & mm.rule]
    rev_pre = mm[(mm.n_sentences_pre == 0) & mm.rule]
    resolved = int(len(rev_tok) - len(rev_pre))
    print(f"\nreverse cases: rule fired a Tier A trigger, extractor found no liver sentence")
    print(f"  under token equality                                  {len(rev_tok):,}")
    print(f"  under prefix                                          {len(rev_pre):,}")
    print(f"  resolved by the prefix change                         {resolved:,}")
    print(f"  (stratification only; no quality claim is made against note_b)")

    # --- breakdowns over kept sentences ------------------------------------------------------
    ks = pd.DataFrame(kept_rows)
    tot = len(ks)
    print(f"\nkept sentences (post-cap, prefix mode): {tot:,}")
    print("  by note type")
    for k, v in ks.note_type.value_counts().items():
        print(f"    {k:<26} {v:>9,}  ({100*v/tot:5.1f}%)")
    print("  by section")
    label = {"impression": "impression / conclusion", "findings": "findings", "other": "other"}
    for k, v in ks.section.value_counts().items():
        print(f"    {label.get(k,k):<26} {v:>9,}  ({100*v/tot:5.1f}%)")

    # --- capped admissions across the 2x2 -----------------------------------------------------
    cells = mm.copy()
    cells["cell"] = np.select(
        [cells.code_positive & cells.rule, ~cells.code_positive & cells.rule,
         cells.code_positive & ~cells.rule],
        ["A code+/note+", "B code-/note+", "C code+/note-"], "D code-/note-")
    capped_ids = set(wide[wide.cap_bound].hadm_id)
    cells["capped"] = cells.hadm_id.isin(capped_ids)
    print(f"\ncapped admissions across the 2x2 cells (cells are a stratification, not an evaluation)")
    print(f"  {'cell':<16} {'subsample':>12} {'capped':>10} {'% of cell':>11} {'% of capped':>13}")
    ncap = int(cells.capped.sum())
    for c in ["A code+/note+", "B code-/note+", "C code+/note-", "D code-/note-"]:
        sub = cells[cells.cell == c]
        cap = int(sub.capped.sum())
        print(f"  {c:<16} {len(sub):>12,} {cap:>10,} {100*cap/max(len(sub),1):>10.2f}% "
              f"{100*cap/max(ncap,1):>12.1f}%")
    print(f"  {'total':<16} {len(cells):>12,} {ncap:>10,} {100*ncap/len(cells):>10.2f}% {100.0:>12.1f}%")

    print(f"\nexceptions during row-level work: {dict(exc) or 'none'}")
    print(f"runtime {secs:.0f}s")
    print("=" * 74)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--partitions", nargs="*", default=["DEV", "TEST"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--mode", choices=["per_sentence", "per_admission"], default="per_sentence")
    ap.add_argument("--out", default=None, help="optional parquet of kept sentences (credentialed)")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    run(a.partitions, a.limit, a.out, a.mode)
