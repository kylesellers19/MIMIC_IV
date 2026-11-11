#!/usr/bin/env python3
"""DIAGNOSTIC COPY of scripts/liver_sentences.py with the per-admission cap as a parameter.

    Selection, section assignment, ordering and linkage are copied unchanged. Differences from the
    production file: --cap (0 = no cap), the note pass factored into collect() so several caps can
    be measured on one pass, and a --sweep mode that (1) checks cap 40 against a production
    --out parquet and the production report, then (2) writes count-only tables for caps
    40/80/160/320/none to diagnostics/liver_sentence_cap/cap_sweep_summary.csv.

    scripts/run0919_env.sh diagnostics/liver_sentence_cap/liver_sentences_cap.py --cap 80
    scripts/run0919_env.sh diagnostics/liver_sentence_cap/liver_sentences_cap.py --sweep \\
        --prod-parquet <production --out parquet> --prod-log <production stdout>

Production docstring follows.

Liver-sentence extractor that does not know the disease vocabulary.

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
import contextlib
import hashlib
import io
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


# Anatomical / regional sub-headings that may appear INSIDE a findings block and continue it.
# This is a HEADING vocabulary and is deliberately separate from the frozen rule's token-level
# organ sets (TARGET_ORGANS, COMPETING_ORGANS), which classify words inside sentences and must not
# be reused for section structure.
FINDINGS_SUBHEADINGS = {
    "LIVER", "HEPATOBILIARY", "GALLBLADDER", "BILIARY", "BILE DUCTS",
    "PANCREAS", "SPLEEN", "KIDNEY", "KIDNEYS", "ADRENAL", "ADRENALS", "ADRENAL GLANDS",
    "BOWEL", "STOMACH", "APPENDIX", "BLADDER", "PELVIS", "ABDOMEN", "PERITONEUM",
    "LYMPH NODES", "VASCULATURE", "VESSELS", "AORTA",
    "LUNG BASES", "LUNGS", "HEART", "BONES", "OSSEOUS STRUCTURES", "SOFT TISSUES",
}
QUALIFIER_RE = re.compile(r"^(?:RIGHT|LEFT|BILATERAL)\s+")
HEADING_SPLIT_RE = re.compile(r"\s*/\s*|\s*,\s*|\s*&\s*|\s+AND\s+")


def normalise_heading(label):
    """Uppercase, drop a trailing colon, collapse internal whitespace."""
    return " ".join(label.strip().upper().rstrip(":").split())


def continues_findings_block(label):
    """True when every part of a compound heading is an anatomical sub-heading.

    'LIVER/GALLBLADDER' -> LIVER, GALLBLADDER (both listed, continues).
    'RIGHT KIDNEY'      -> KIDNEY after the qualifier is stripped (continues).
    'LIVER AND SPINE'   -> SPINE is not listed, so the block closes."""
    lab = normalise_heading(label)
    if not lab:
        return False
    parts = [QUALIFIER_RE.sub("", p).strip() for p in HEADING_SPLIT_RE.split(lab)]
    parts = [p for p in parts if p]
    return bool(parts) and all(p in FINDINGS_SUBHEADINGS for p in parts)


def is_recognised_heading(label):
    return any(label == c or label.startswith(c) for c in BLOCK_TERMINATORS)


def section_spans(text):
    """Cover the note with (start, end, category).

    A findings block opens at a heading containing FINDING. While it is open, an unrecognised
    heading continues it ONLY when every part of that heading is in FINDINGS_SUBHEADINGS; such a
    heading inherits `findings`, because organ sub-headings like HEPATOBILIARY or LIVER are findings
    content. IMPRESSION/CONCLUSION, a heading on the recognised lists, or any other unlisted heading
    closes the block, and sentences under it are `other`.

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
        elif in_findings_block and continues_findings_block(label):
            cat = "findings"                      # anatomical sub-heading; block stays open
        else:
            cat = "other"; in_findings_block = False   # any other heading closes the block
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
    """cap=None keeps every sentence, in the same order a cap would truncate."""
    ordered = sorted(rows, key=lambda r: (SECTION_RANK.get(r["section"], 2), r["_order"]))
    if cap is None:
        return ordered, len(ordered), False
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


# (name, synthetic note, [(probe marker, expected section), ...]). All text invented here; every
# probe sentence names the liver so the extractor selects it, which is what lets us read its section.
SECTION_TESTS = [
    ("a  FINDINGS > HEPATOBILIARY",
     "EXAMINATION: CT abdomen.\nFINDINGS:\nHEPATOBILIARY:\nProbe alpha mentions the liver.\n",
     [("alpha", "findings")]),
    ("b  FINDINGS > LIVER > IMPRESSION",
     "FINDINGS:\nLIVER:\nProbe alpha mentions the liver.\nIMPRESSION:\n"
     "Probe bravo mentions the liver.\n",
     [("alpha", "findings"), ("bravo", "impression")]),
    ("c  FINDINGS > HEPATOBILIARY > RECOMMENDATION(S)",
     "FINDINGS:\nHEPATOBILIARY:\nProbe alpha mentions the liver.\nRECOMMENDATION(S):\n"
     "Probe bravo mentions the liver.\n",
     [("alpha", "findings"), ("bravo", "other")]),
    ("d  PERTINENT RESULTS > FINDINGS > LIVER > DISCHARGE LABS",
     "Pertinent Results:\nFINDINGS:\nLIVER:\nProbe alpha mentions the liver.\nDISCHARGE LABS:\n"
     "Probe bravo mentions the liver.\n",
     [("alpha", "findings"), ("bravo", "other")]),
    ("e  FINDINGS > LIVER > RIGHT KIDNEY > LIVER/GALLBLADDER > IMPRESSION",
     "FINDINGS:\nLIVER:\nProbe alpha mentions the liver.\nRIGHT KIDNEY:\n"
     "Probe bravo mentions the liver.\nLIVER/GALLBLADDER:\nProbe charlie mentions the liver.\n"
     "IMPRESSION:\nProbe delta mentions the liver.\n",
     [("alpha", "findings"), ("bravo", "findings"), ("charlie", "findings"), ("delta", "impression")]),
    ("f  FINDINGS > LIVER > COMPARISON NOTE",
     "FINDINGS:\nLIVER:\nProbe alpha mentions the liver.\nCOMPARISON NOTE:\n"
     "Probe bravo mentions the liver.\n",
     [("alpha", "findings"), ("bravo", "other")]),
    # f closes via the recognised list (COMPARISON). g closes via the new rule: ADDENDUM is on no
    # list and is not an anatomical sub-heading, so it exercises the path f does not reach.
    ("g  FINDINGS > LIVER > ADDENDUM (unlisted, non-anatomical)",
     "FINDINGS:\nLIVER:\nProbe alpha mentions the liver.\nADDENDUM:\n"
     "Probe bravo mentions the liver.\n",
     [("alpha", "findings"), ("bravo", "other")]),
    ("h  compound heading with a non-anatomical part closes the block",
     "FINDINGS:\nLIVER AND SPINE:\nProbe alpha mentions the liver.\n",
     [("alpha", "other")]),
    ("i  plain FINDINGS", "FINDINGS:\nProbe alpha mentions the liver.\n", [("alpha", "findings")]),
    ("j  plain IMPRESSION", "IMPRESSION:\nProbe alpha mentions the liver.\n", [("alpha", "impression")]),
    ("k  no headings at all", "Probe alpha mentions the liver.\n", [("alpha", "other")]),
    ("l  INDICATION before any FINDINGS",
     "INDICATION:\nProbe alpha mentions the liver.\n", [("alpha", "other")]),
    ("m  sub-heading with no open block does not become findings",
     "EXAMINATION: CT abdomen.\nLIVER:\nProbe alpha mentions the liver.\n", [("alpha", "other")]),
]


def section_selftest():
    print("\nsection-assignment fixtures (synthetic text, no MIMIC data)")
    bad = total = 0
    for name, doc, probes in SECTION_TESTS:
        rows = extract_from_note(doc, "selftest")
        results = []
        for marker, want in probes:
            hit = [r for r in rows if marker in r["text"].lower()]
            got = hit[0]["section"] if hit else "(probe not selected)"
            total += 1
            if got != want:
                bad += 1
            results.append(f"{marker}:{got}{'' if got == want else f' (want {want})'}")
        flag = "ok  " if all("want" not in r for r in results) else "FAIL"
        print(f"  [{flag}] {name:<58} {'  '.join(results)}")
    print(f"  {total - bad}/{total} assertions across {len(SECTION_TESTS)} fixtures")
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


def per_admission_stats(adm, rows_by_adm, narrow, cap=CAP):
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
        keep, n_before, bound = cap_admission(flat, cap)
        recs.append({"hadm_id": hadm, "n_sentences": len(keep), "n_before_cap": n_before,
                     "cap_bound": bound, "n_tokens": sum(r["n_tokens"] for r in keep),
                     "n_chars": sum(r["n_chars"] for r in keep)})
        if not narrow:
            for r in keep:
                kept_all.append({"hadm_id": hadm, "sid": r["sid"], "note_type": r["note_type"],
                                 "section": r["section"], "char_start": r["char_start"],
                                 "char_end": r["char_end"], "text": r["text"]})
    return pd.DataFrame(recs), kept_all


def collect(partitions, limit):
    """One pass over the note files -> uncapped liver sentences per in-scope admission."""
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
    return adm, rows_by_adm, con, exc, t0


def run(partitions, limit, out_path, mode, cap=CAP):
    adm, rows_by_adm, con, exc, t0 = collect(partitions, limit)
    wide, kept_rows = per_admission_stats(adm, rows_by_adm, narrow=False, cap=cap)
    narrow, _ = per_admission_stats(adm, rows_by_adm, narrow=True, cap=cap)

    if out_path:
        df = pd.DataFrame(kept_rows)
        if mode == "per_admission":
            df = (df.groupby("hadm_id")
                    .agg(n_sentences=("sid", "size"), text=("text", "\n".join))
                    .reset_index())
        df.to_parquet(out_path, index=False)
        print(f"wrote {out_path} ({len(df):,} rows, mode {mode})")

    report(wide, narrow, kept_rows, con, exc, time.time() - t0, cap)


def q(s, p):
    return float(np.percentile(s, p)) if len(s) else float("nan")


def dist(label, s):
    print(f"  {label:<34} median {q(s,50):>5.0f} | Q1 {q(s,25):>5.0f} | Q3 {q(s,75):>5.0f} | "
          f"p90 {q(s,90):>6.0f} | max {int(s.max()) if len(s) else 0:>5}")


def report(wide, narrow, kept_rows, con, exc, secs, cap=CAP):
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
    print(f"\n{cap if cap is not None else 'no'}-sentence cap bound          {nb:,} admissions ({100*nb/n:.2f}%)   "
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


# ----------------------------------------------------------------------------- cap sweep (diagnostic)
# Counts only. No sentence, note or heading text is printed or written by anything below.
SWEEP_CAPS = [40, 80, 160, 320, None]
CELLS = ["A", "B", "C", "D"]
NOTE_TYPES = ["radiology_outpatient", "radiology_inpatient", "discharge"]
SECTIONS = ["impression", "findings", "other"]
SWEEP_CSV = "diagnostics/liver_sentence_cap/cap_sweep_summary.csv"
COMPARE = ["sid", "note_type", "section", "char_start", "char_end", "text"]
RULE = "=" * 74


def cap_name(cap):
    return f"cap_{cap}" if cap is not None else "no_cap"


def two_by_two_cells(con, adm):
    """build_2x2.py's primary cell: code_positive x note_b (v1.1.0 + outpatient 365/30), read from
    the frame build_2x2.py wrote. The same assignment the production report uses."""
    fr = con.execute(f"SELECT hadm_id, code_positive, note_b FROM read_parquet('{FRAME}')").fetchdf()
    c = adm[["hadm_id"]].merge(fr, on="hadm_id", how="left", indicator=True)
    assert (c._merge == "both").all(), "admission missing from the 2x2 frame"
    cp, nb = c.code_positive.astype(bool), c.note_b.astype(bool)
    c["cell"] = np.select([cp & nb, ~cp & nb, cp & ~nb], ["A", "B", "C"], "D")
    return c[["hadm_id", "code_positive", "note_b", "cell"]]


def icd_definition(con, cells):
    """Which code set reproduces code_positive on these admissions: with or without ICD-9 571.9."""
    from scripts.masld_config import DATA, MASLD_PREDICATE
    con.register("sample_adm", cells[["hadm_id"]])
    dx = con.execute(f"""
      SELECT d.hadm_id,
             max(CASE WHEN icd_version=9 AND trim(icd_code)='5719' THEN 1 ELSE 0 END) AS has_5719,
             max(CASE WHEN {MASLD_PREDICATE} AND NOT (icd_version=9 AND trim(icd_code)='5719')
                      THEN 1 ELSE 0 END) AS has_other
      FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}) d
      JOIN sample_adm USING (hadm_id) GROUP BY d.hadm_id""").fetchdf()
    m = cells.merge(dx, on="hadm_id", how="left").fillna({"has_5719": 0, "has_other": 0})
    with_ = (m.has_5719 == 1) | (m.has_other == 1)
    without = m.has_other == 1
    solely = with_ & ~without
    return {"disagree_with_5719": int((with_ != m.code_positive).sum()),
            "disagree_without_5719": int((without != m.code_positive).sum()),
            "solely_5719_by_cell": {k: int(solely[m.cell == k].sum()) for k in CELLS}}


def report_block(lines):
    """The production report from its first rule line to its last, minus the runtime line."""
    idx = [i for i, l in enumerate(lines) if l == RULE]
    return [l for l in lines[idx[0]:idx[-1] + 1] if not l.startswith("runtime")]


def verify_cap40(adm, rows_by_adm, con, exc, prod_parquet, prod_log):
    """Copy at cap 40 vs the production run: kept rows per admission, and the printed report."""
    wide, kept40 = per_admission_stats(adm, rows_by_adm, narrow=False, cap=40)
    narrow, _ = per_admission_stats(adm, rows_by_adm, narrow=True, cap=40)
    p, c = pd.read_parquet(prod_parquet), pd.DataFrame(kept40)

    def by_adm(df):
        return {h: list(g[COMPARE].itertuples(index=False, name=None))
                for h, g in df.groupby("hadm_id", sort=False)}
    pl, cl = by_adm(p), by_adm(c)
    res = {"prod_rows": len(p), "copy_rows": len(c), "prod_admissions": len(pl),
           "copy_admissions": len(cl), "columns_equal": list(p.columns) == list(c.columns),
           "admission_mismatches": sum(pl.get(h) != cl.get(h) for h in set(pl) | set(cl))}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        report(wide, narrow, kept40, con, exc, 0, 40)
    mine = report_block(buf.getvalue().splitlines())
    theirs = report_block(open(prod_log).read().splitlines())
    res["report_lines"] = len(theirs)
    res["report_line_mismatches"] = (sum(a != b for a, b in zip(mine, theirs))
                                     + abs(len(mine) - len(theirs)))
    return res, {h: [r[0] for r in v] for h, v in cl.items()}


def positive_in(text, iter_hits):
    """(Tier A, Tier A or B): an affirmed v1.1.0 hit in this sentence - not negated, not family,
    not hedged (those never reach disp 'positive'), and not flagged historical."""
    a = ab = False
    for h in iter_hits(text):
        if h["disp"] == "positive" and not h["historical"]:
            ab = True
            a = a or h["tier"] == "A"
    return a, ab


def pct(n, d):
    return round(100 * n / d, 2) if d else float("nan")


def sweep(adm, rows_by_adm, cells, caps):
    """-> (item-2 rows, item-3 rows, uncapped per-admission sid order, errors)."""
    from scripts.note_phenotype import _iter_hits   # measurement only, after selection is fixed
    recs, rows = per_admission_stats(adm, rows_by_adm, narrow=False, cap=None)
    U = pd.DataFrame(rows)
    U["rank"] = U.groupby("hadm_id", sort=False).cumcount()   # rows arrive in cap order per admission
    U["cell"] = U.hadm_id.map(cells.set_index("hadm_id").cell)
    U["n_chars"] = U.char_end - U.char_start
    U["is_dc"] = U.note_type == "discharge"
    errs, flags = Counter(), {}
    ab = U.cell.isin(["A", "B"])
    for sid, text in U.loc[ab, ["sid", "text"]].drop_duplicates("sid").itertuples(index=False):
        try:
            flags[sid] = positive_in(text, _iter_hits)
        except Exception as e:
            errs[type(e).__name__] += 1
            flags[sid] = (False, False)
    U["posA"] = ab & U.sid.map(lambda s: flags.get(s, (False, False))[0])
    U["posAB"] = ab & U.sid.map(lambda s: flags.get(s, (False, False))[1])
    order = {h: list(g.sid) for h, g in U.groupby("hadm_id", sort=False)}
    U = U.drop(columns="text")

    A = pd.DataFrame(recs)[["hadm_id", "n_before_cap"]].merge(cells, on="hadm_id")
    A["n_dc"] = A.hadm_id.map(U[U.is_dc].groupby("hadm_id").size()).fillna(0).astype(int)
    strata = [("overall", A)] + [(k, A[A.cell == k]) for k in CELLS]

    item2 = []
    for name, s in strata:
        for subset, x in (("all admissions", s.n_before_cap), ("admissions with >=1", s.n_before_cap[s.n_before_cap > 0])):
            item2.append({"stratum": name, "subset": subset, "n": len(x),
                          **{lab: q(x, p) for lab, p in (("median", 50), ("p75", 75), ("p90", 90),
                                                         ("p95", 95), ("p99", 99))},
                          "max": int(x.max()) if len(x) else float("nan")})

    item3 = defaultdict(dict)    # (item, metric, stratum, denominator) -> {cap column: value}
    for cap in caps:
        col = cap_name(cap)
        kept = U["rank"] < cap if cap is not None else pd.Series(True, index=U.index)
        K, D = U[kept], U[~kept]
        g = K.groupby("hadm_id").agg(n=("sid", "size"), chars=("n_chars", "sum"), dc=("is_dc", "sum"),
                                     posA=("posA", "max"), posAB=("posAB", "max"))
        a = A.merge(g, on="hadm_id", how="left").fillna({"n": 0, "chars": 0, "dc": 0,
                                                         "posA": False, "posAB": False})
        for name, s in strata:
            s = a[a.hadm_id.isin(s.hadm_id)]
            reach = int((s.n_before_cap >= cap).sum()) if cap is not None else float("nan")
            over = int((s.n_before_cap > cap).sum()) if cap is not None else float("nan")
            item3[("3a", "admissions reaching cap (n >= cap), n", name, len(s))][col] = reach
            item3[("3a", "admissions reaching cap (n >= cap), %", name, len(s))][col] = pct(reach, len(s)) if cap else float("nan")
            item3[("3a", "admissions exceeding cap (>=1 dropped), n", name, len(s))][col] = over
            item3[("3a", "admissions exceeding cap (>=1 dropped), %", name, len(s))][col] = pct(over, len(s)) if cap else float("nan")
        item3[("3b", "sentences kept, n", "overall", len(U))][col] = len(K)
        item3[("3b", "sentences dropped, n", "overall", len(U))][col] = len(D)
        for t in NOTE_TYPES:
            item3[("3c", "sentences dropped, n", f"note type: {t}", int((U.note_type == t).sum()))][col] = int((D.note_type == t).sum())
        for sct in SECTIONS:
            item3[("3c", "sentences dropped, n", f"section: {sct}", int((U.section == sct).sum()))][col] = int((D.section == sct).sum())
        has_dc = a[a.n_dc > 0]
        lost = int((has_dc.dc == 0).sum())
        item3[("3d", "admissions with every discharge-summary liver sentence dropped, n", "admissions with >=1 discharge liver sentence", len(has_dc))][col] = lost
        item3[("3d", "admissions with every discharge-summary liver sentence dropped, %", "admissions with >=1 discharge liver sentence", len(has_dc))][col] = pct(lost, len(has_dc))
        for k in ("A", "B"):
            s = a[a.cell == k]
            for flag, lab in (("posA", "Tier A"), ("posAB", "Tier A or B")):
                n = int(s[flag].sum())
                item3[("3e", f">=1 kept sentence with affirmed non-historical {lab} term, n", k, len(s))][col] = n
                item3[("3e", f">=1 kept sentence with affirmed non-historical {lab} term, %", k, len(s))][col] = pct(n, len(s))
        nz = a[a.n > 0]
        joined = nz.chars + nz.n - 1                 # sentences joined with "\n", as --mode per_admission
        for unit, x in (("characters", joined), ("estimated tokens (characters / 4)", joined / 4)):
            for lab, p in (("median", 50), ("p90", 90), ("p99", 99)):
                item3[("3f", f"kept text per admission, {unit}, {lab}", "admissions with >=1 kept sentence", len(nz))][col] = round(q(x, p), 1)
            item3[("3f", f"kept text per admission, {unit}, max", "admissions with >=1 kept sentence", len(nz))][col] = round(float(x.max()), 1)
    return pd.DataFrame(item2), item3, order, errs


def run_sweep(partitions, prod_parquet, prod_log, caps=SWEEP_CAPS):
    t0 = time.time()
    adm, rows_by_adm, con, exc, _ = collect(partitions, 0)
    t_pass = time.time() - t0
    print(f"note pass {t_pass:.0f}s; extraction exceptions: {dict(exc) or 'none'}")

    t1 = time.time()
    check, kept40_sids = verify_cap40(adm, rows_by_adm, con, exc, prod_parquet, prod_log)
    print(f"\n[1] copy at cap 40 vs production ({time.time()-t1:.0f}s)")
    for k, v in check.items():
        print(f"    {k:<26} {v:,}" if isinstance(v, int) and not isinstance(v, bool) else f"    {k:<26} {v}")

    cells = two_by_two_cells(con, adm)
    icd = icd_definition(con, cells)
    print(f"\ncell assignment: build_2x2.py primary (code_positive x note_b) from {FRAME}")
    print(f"    code_positive disagrees with the code set WITH 571.9 on {icd['disagree_with_5719']:,} "
          f"admissions, WITHOUT 571.9 on {icd['disagree_without_5719']:,}")
    print(f"    admissions coded by 571.9 alone, by cell: {icd['solely_5719_by_cell']}")

    t2 = time.time()
    item2, item3, order, errs = sweep(adm, rows_by_adm, cells, caps)
    internal = sum(order.get(h, [])[:40] != v for h, v in kept40_sids.items()) + \
        sum(1 for h, v in order.items() if v and h not in kept40_sids)
    print(f"\nsweep {time.time()-t2:.0f}s; rule-classification exceptions: {dict(errs) or 'none'}; "
          f"sweep cap-40 vs copy cap-40 admission mismatches: {internal}")

    pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
    pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 200)
    print(f"\n[2] liver sentences per admission, no cap\n{item2.to_string(index=False)}")
    cols = [cap_name(c) for c in caps]
    t3 = pd.DataFrame([{"item": k[0], "metric": k[1], "stratum": k[2], "denominator": k[3],
                        **{c: v.get(c, float('nan')) for c in cols}} for k, v in item3.items()])
    print(f"\n[3] cap sweep\n{t3.to_string(index=False)}")

    i2 = item2.assign(item="2", metric=lambda d: "sentences per admission (" + d.subset + ")",
                      denominator=item2.n)
    long2 = i2.melt(id_vars=["item", "metric", "stratum", "denominator"],
                    value_vars=["median", "p75", "p90", "p95", "p99", "max"], var_name="stat")
    long2["metric"] = long2.metric + ", " + long2.stat
    long2 = long2.drop(columns="stat").rename(columns={"value": "no_cap"})
    out = pd.concat([long2, t3], ignore_index=True)[["item", "metric", "stratum", "denominator"] + cols]
    for c in cols:                               # counts as integers; blank where not applicable
        out[c] = out[c].map(lambda v: "" if pd.isna(v) else int(v) if float(v).is_integer() else v)
    out.to_csv(SWEEP_CSV, index=False)
    print(f"\nwrote {SWEEP_CSV} ({len(out)} rows, counts and distributions only)")
    print(f"total runtime {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--partitions", nargs="*", default=["DEV", "TEST"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--mode", choices=["per_sentence", "per_admission"], default="per_sentence")
    ap.add_argument("--out", default=None, help="optional parquet of kept sentences (credentialed)")
    ap.add_argument("--cap", type=int, default=CAP, help="sentences kept per admission; 0 = no cap")
    ap.add_argument("--sweep", action="store_true", help="caps 40/80/160/320/none, counts-only CSV")
    ap.add_argument("--prod-parquet", help="production --out parquet (per_sentence) to check cap 40")
    ap.add_argument("--prod-log", help="production stdout from the same run")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.sweep:
        run_sweep(a.partitions, a.prod_parquet, a.prod_log)
    else:
        run(a.partitions, a.limit, a.out, a.mode, a.cap or None)
