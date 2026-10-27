#!/usr/bin/env python3
"""The LLM note phenotype at admission grain, for the reports that use it (amendment h).

load() returns one row per dev/test admission in the notes subsample (a simple random sample of
dev/test subjects, SEED_NOTES_SUBSAMPLE) with:
    llm          primary: >=1 kept sentence answered YES with timing CURRENT or PAST
    llm_unclear  sensitivity: YES or UNCLEAR, CURRENT or PAST
    llm_current  sensitivity: YES, CURRENT only
    llm_anatomy  sensitivity: primary restricted to sentences selected by the anatomy test
    has_sentence the admission has >=1 kept liver sentence
    pathway      for llm-positive admissions, where the YES evidence sits: discharge summary,
                 inpatient radiology only, or outpatient radiology only
plus the frozen rule (note_b -> rule), code status (code), and the Aim 1c strata (race, insurance,
sex, language, age_band with the plan's bands). Answers come from the merged v4 run.

Also: suppress() for the public outputs, and the subject scale factor from the subsample to all
dev/test subjects. No text is read.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, ".")
from scripts.masld_config import SPLITS_V1

ANSWERS = "data/processed/llm_review/full_v4_merged/sentence_answers.parquet"
SUBSAMPLE = "data/processed/run_2026-09-19_notes_text/subsample.parquet"
FRAME = "data/processed/aim1a_frame.parquet"
FLOOR = 11
AGE_BINS = [-1, 17, 39, 54, 64, 74, 88, 200]
AGE_LABELS = ["<18", "18-39", "40-54", "55-64", "65-74", "75-88", "89+"]
PATHWAYS = ("discharge summary", "inpatient radiology only", "outpatient radiology only")


def suppress(n):
    """Counts of 1-10 are published as '<11' (CELL_FLOOR)."""
    n = int(n)
    return "<11" if 0 < n < FLOOR else n


def pct(num, den, digits=1):
    """A percentage, or None when the numerator or denominator would reveal a small cell."""
    num, den = int(num), int(den)
    if den < FLOOR or 0 < num < FLOOR or 0 < den - num < FLOOR:
        return None
    return round(100 * num / den, digits)


def _pathway(types):
    if "discharge" in types:
        return PATHWAYS[0]
    if "radiology_inpatient" in types:
        return PATHWAYS[1]
    return PATHWAYS[2]


def admission_labels(r):
    """Sentence answers -> (admission labels indexed by hadm_id, YES-evidence pathway per admission).
    Admissions with no kept sentence are absent; callers treat them as negative."""
    yes, unc = r.answer.eq("YES"), r.answer.eq("UNCLEAR")
    cp = r.timing.isin(["CURRENT", "PAST"])
    h = r.hadm_id
    lab = pd.DataFrame({
        "llm": (yes & cp).groupby(h).any(),
        "llm_unclear": ((yes | unc) & cp).groupby(h).any(),
        "llm_current": (yes & r.timing.eq("CURRENT")).groupby(h).any(),
        "llm_anatomy": (yes & cp & r.reason.eq("anatomy")).groupby(h).any(),
    })
    path = r[yes & cp].groupby("hadm_id").note_type.agg(lambda s: _pathway(set(s)))
    return lab, path


def load(answers=ANSWERS):
    sub = pd.read_parquet(SUBSAMPLE, columns=["hadm_id", "subject_id", "partition"])
    sub = sub[sub.partition.isin(["DEV", "TEST"])]
    fr = pd.read_parquet(FRAME, columns=["hadm_id", "note_b", "code_positive", "age", "gender", "race",
                                         "insurance", "language"])
    a = sub.merge(fr, on="hadm_id", how="left")
    r = pd.read_parquet(answers)
    r = r[r.hadm_id.isin(set(a.hadm_id))]
    lab, path = admission_labels(r)
    a = a.merge(lab, left_on="hadm_id", right_index=True, how="left")
    for c in lab.columns:
        a[c] = a[c].fillna(False).astype(bool)
    a["has_sentence"] = a.hadm_id.isin(set(r.hadm_id))
    a["pathway"] = a.hadm_id.map(path)
    a["rule"] = a.note_b.astype(bool)
    a["code"] = a.code_positive.astype(bool)
    a["sex"] = a.gender
    a["language"] = a.language.fillna("(missing)")
    a["insurance"] = a.insurance.fillna("(missing)")
    a["age_band"] = pd.cut(a.age, AGE_BINS, labels=AGE_LABELS).astype(str)
    return a.drop(columns=["note_b", "code_positive", "gender"])


def subject_scale(a):
    """All dev/test subjects divided by subsample subjects (the subsample samples subjects)."""
    sp = pd.read_parquet(SPLITS_V1, columns=["subject_id", "partition"])
    return sp[sp.partition.isin(["DEV", "TEST"])].subject_id.nunique() / a.subject_id.nunique()


def results_dir():
    d = "docs/run_2026-10-27/results"
    os.makedirs(d, exist_ok=True)
    return d
