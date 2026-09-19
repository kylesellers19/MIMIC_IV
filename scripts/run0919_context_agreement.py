#!/usr/bin/env python3
"""run_2026-09-19 stretch item 2 — agreement between this project's negation/context implementation
and the reference medspaCy ConText component.

The project reimplements ConText (Harkema et al. 2009) inside the frozen note rule. The manuscript
states this as a limitation. This script measures it: on a random sample of radiology reports it runs
both systems over the SAME lexicon matches and reports percent agreement by assertion class.

IT DOES NOT CHANGE THE FROZEN RULE. The lexicon, sentence splitter and screen terms are imported from
scripts/note_phenotype.py; only the iteration order is replicated here so that the two systems' hits
can be aligned one-to-one, and the alignment is verified by comparing trigger names position by
position (a note whose names do not line up is counted as unalignable and excluded, not guessed at).

Anatomical scoping has no ConText analogue and is reported separately, not as disagreement.
Outputs counts only — no note text, no identifiers. Writes docs/run_2026-09-19/results/context_agreement.json.
"""
import bisect, json, os, sys, time
from collections import Counter
import logging
import duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.getcwd())
os.environ.setdefault("SPACY_WARNING_IGNORE", "W008")

def _silence_third_party_logging():
    """PyRuSH (medspaCy's sentence splitter) emits per-token DEBUG records through loguru, which would
    write NOTE TEXT into the log file. Remove every loguru sink and clamp stdlib logging before any
    note is touched. This is a hard requirement, not a tidiness measure."""
    try:
        from loguru import logger as _loguru
        _loguru.remove()
        _loguru.disable("PyRuSH")
        _loguru.disable("medspacy")
    except ImportError:
        pass
    logging.disable(logging.INFO)
    for name in ("PyRuSH", "medspacy", "spacy"):
        lg = logging.getLogger(name); lg.setLevel(logging.ERROR); lg.propagate = False

_silence_third_party_logging()
from scripts.note_phenotype import _iter_hits, TRIGGERS, SENT_SPLIT, SCREEN, NOTE

SEED = 20260926
N_SAMPLE = 20000
IDX = "data/processed/run_2026-09-19_notes_index"
OUT = "docs/run_2026-09-19/results/context_agreement.json"


def ordered_hits(text):
    """Replicate ONLY the frozen rule's hit iteration order, returning (name, start, end) per kept hit.
    Mirrors _iter_hits: same segments, same triggers, same longest-span dedup."""
    out = []
    if text is None:
        return out
    low = text.lower()
    if not any(s in low for s in SCREEN):
        return out
    pos = 0
    for seg in SENT_SPLIT.split(text):
        start = text.find(seg, pos) if seg else pos
        if start < 0:
            start = pos
        pos = start + len(seg)
        slow = seg.lower()
        if not any(s in slow for s in SCREEN):
            continue
        hits = []
        for name, rgx, tier, scope in TRIGGERS:
            for m in rgx.finditer(seg):
                hits.append((m.start(), m.end(), name))
        if not hits:
            continue
        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        kept = []
        for h in hits:
            if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
                continue
            kept.append(h)
        for s, e, name in kept:
            out.append((name, start + s, start + e))
    return out


def project_labels(text):
    """Assertion class per hit from the FROZEN rule, in its own yield order."""
    labs = []
    for h in _iter_hits(text):
        d = h["disp"]
        if d == "suppressed":
            labs.append((h["name"], "suppressed"))
        elif d == "family":
            labs.append((h["name"], "family"))
        elif d == "negation":
            labs.append((h["name"], "negated"))
        elif d == "tierC":
            labs.append((h["name"], "uncertain"))
        else:
            labs.append((h["name"], "historical" if h.get("historical") else "affirmed"))
    return labs


def build_nlp():
    import medspacy  # noqa: F401 — importing medspacy registers its spaCy pipeline factories
    import spacy
    from spacy.tokens import Span
    _silence_third_party_logging()      # again: importing medspacy re-installs loguru's default sink
    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")
    nlp.add_pipe("medspacy_context")
    return nlp, Span


def medspacy_label(ent):
    if ent._.is_family:
        return "family"
    if ent._.is_negated:
        return "negated"
    if ent._.is_uncertain or ent._.is_hypothetical:
        return "uncertain"
    if ent._.is_historical:
        return "historical"
    return "affirmed"


def main():
    t0 = time.time()
    con = duckdb.connect(); con.execute("SET memory_limit='8GB'")
    pool = con.execute(f"""SELECT note_id FROM read_parquet('{IDX}/radiology.parquet')
                           WHERE (n_pos + n_neg + n_tierC) > 0""").fetchdf()
    rng = np.random.default_rng(SEED)
    n_pool = len(pool)
    take = pool.iloc[rng.choice(n_pool, min(N_SAMPLE, n_pool), replace=False)]
    con.register("take", take)
    print(f"pool {n_pool:,} reports with >=1 asserted lexicon match; sampling {len(take):,}", flush=True)
    rows = con.execute(f"""SELECT r.text FROM read_csv_auto('{NOTE}/radiology.csv.gz') r
                           SEMI JOIN take t ON r.note_id = t.note_id""").fetchdf()
    print(f"loaded {len(rows):,} reports in {time.time()-t0:.0f}s", flush=True)

    nlp, Span = build_nlp()
    agree = Counter(); conf = Counter(); exc = Counter()
    n_notes = n_hits = n_unalignable = n_suppressed = 0
    for i, text in enumerate(rows.text):
        try:
            spans = ordered_hits(text)
            labs = project_labels(text)
            if len(spans) != len(labs) or any(s[0] != l[0] for s, l in zip(spans, labs)):
                n_unalignable += 1
                continue
            keep = [(s, l[1]) for s, l in zip(spans, labs) if l[1] != "suppressed"]
            n_suppressed += len(spans) - len(keep)
            if not keep:
                continue
            doc = nlp.make_doc(text)
            ents = []
            for (name, cs, ce), _lab in keep:
                sp = doc.char_span(cs, ce, label="TRIGGER", alignment_mode="expand")
                if sp is not None:
                    ents.append((sp, _lab))
            if not ents:
                continue
            # spaCy requires non-overlapping ents
            chosen, last_end = [], -1
            for sp, lab in sorted(ents, key=lambda x: (x[0].start, -(x[0].end - x[0].start))):
                if sp.start >= last_end:
                    chosen.append((sp, lab)); last_end = sp.end
            doc.ents = [sp for sp, _ in chosen]
            doc = nlp.get_pipe("medspacy_context")(nlp.get_pipe("medspacy_pyrush")(doc))
            for (sp, proj), ent in zip(chosen, doc.ents):
                ms = medspacy_label(ent)
                n_hits += 1
                agree[(proj, proj == ms)] += 1
                conf[(proj, ms)] += 1
            n_notes += 1
        except Exception as e:
            exc[type(e).__name__] += 1
        if (i + 1) % 2000 == 0:
            print(f"  {i+1:,} reports, {n_hits:,} aligned hits, {time.time()-t0:.0f}s", flush=True)

    classes = ["affirmed", "negated", "uncertain", "historical", "family"]
    by_class = {}
    for c in classes:
        tot = agree[(c, True)] + agree[(c, False)]
        by_class[c] = {"project_n": tot, "agree_n": agree[(c, True)],
                       "percent_agreement": round(100 * agree[(c, True)] / tot, 2) if tot else None}
    overall = sum(agree[(c, True)] for c in classes)
    res = {"purpose": "measures a stated limitation; the frozen rule is unchanged",
           "reference_implementation": "medspaCy ConText (default English rules), spaCy blank('en') + medspacy_pyrush sentence splitter",
           "seed": SEED, "sampling": "random sample of radiology reports having >=1 asserted lexicon match in the per-note index",
           "pool_reports": int(n_pool), "sampled_reports": int(len(take)), "reports_compared": n_notes,
           "reports_unalignable_excluded": n_unalignable, "aligned_hits": n_hits,
           "anatomically_suppressed_hits_excluded": n_suppressed,
           "note_on_suppression": "anatomical scoping has no ConText analogue; suppressed hits are excluded from the comparison rather than counted as disagreement",
           "overall_percent_agreement": round(100 * overall / n_hits, 2) if n_hits else None,
           "by_assertion_class": by_class,
           "confusion_project_rows_medspacy_columns": {f"{p}->{m}": n for (p, m), n in sorted(conf.items(), key=lambda x: -x[1])},
           "exceptions_by_class": dict(exc), "runtime_s": round(time.time() - t0)}
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ["reports_compared", "aligned_hits", "overall_percent_agreement", "by_assertion_class", "exceptions_by_class"]}, indent=1))


if __name__ == "__main__":
    main()
