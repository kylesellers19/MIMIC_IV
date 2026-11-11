#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 — shared pieces for the exploratory analyses (amendments l-o).

Common to (l)-(o), as the amendment says: admission grain unless stated; primary definition (b); cells
A (code+/note+), B (code-/note+), C (code+/note-), D (code-/note-); subject-cluster bootstrap, 500
replicates, seed 20260919, 95% percentile intervals; a stratum is reported when its denominator is at
least 11. No row-level record leaves these functions: callers write counts and shares only.

Small cells: a count of 1-10 is published as "<11"; a share whose numerator or complement is 1-10 is
withheld; where strata partition a public total and one of them is masked, the smallest other stratum's
counts are published rounded to the nearest 100 so the masked count cannot be recovered by subtraction.
"""
import os, sys

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.masld_config import CLEAN_POP, DATA, LOCKED_POP

RES = "docs/run_2026-11-10/results"
REPS, FLOOR, SEED = 500, 11, 20260919
FRAME = "data/processed/aim1a_frame.parquet"
CMRF = "data/processed/cmrf.parquet"
IDX = "data/processed/run_2026-09-19_notes_index"
CELLS = {"A": "code+/note+", "B": "code-/note+", "C": "code+/note-", "D": "code-/note-"}


def load_frame(with_5719=False, with_sources=False):
    """One row per admission of the analysis population, with the cell under definition (b)."""
    con = duckdb.connect()
    df = con.execute(f"""
        SELECT f.hadm_id, f.subject_id, f.code_positive, f.note_b, f.age, c.icd_era, c.hospital_expire_flag,
               l.admittime, l.dischtime, l.anchor_year_group,
               coalesce(m.alcohol, false) AS alcohol, coalesce(m.viral, false) AS viral,
               coalesce(m.other_etio, false) AS other_etio, coalesce(m.cirrhosis, false) AS cirrhosis,
               coalesce(m.hcc, false) AS hcc
        FROM read_parquet('{FRAME}') f JOIN read_parquet('{CLEAN_POP}') c USING (hadm_id)
        JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id) LEFT JOIN read_parquet('{CMRF}') m USING (hadm_id)""").fetchdf()
    cp, nt = df.code_positive.astype(bool), df.note_b.astype(bool)
    df["cell"] = np.select([cp & nt, ~cp & nt, cp & ~nt], ["A", "B", "C"], default="D")
    if with_5719:      # S7: the code-positive set with ICD-9 571.9 removed (as scripts/run0919_aim1c_level1.py)
        dx = con.execute(f"""SELECT hadm_id, max(CASE WHEN icd_version=9 AND trim(icd_code)='5719' THEN 1 ELSE 0 END) AS h5719,
               max(CASE WHEN (icd_version=10 AND trim(icd_code) IN ('K760','K7581')) OR (icd_version=9 AND trim(icd_code)='5718') THEN 1 ELSE 0 END) AS hoth
               FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}) GROUP BY hadm_id""").fetchdf()
        df = df.merge(dx, on="hadm_id", how="left").fillna({"h5719": 0, "hoth": 0})
        df["code_pos_no5719"] = cp & ~((df.h5719 == 1) & (df.hoth == 0))
    if with_sources:   # per-note rule flags and liver-inclusive imaging, as scripts/run0919_aim1c_level1.py
        dcs = con.execute(f"SELECT hadm_id, max(a_pos::INT) AS src_dc FROM read_parquet('{IDX}/discharge.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
        ri = con.execute(f"SELECT hadm_id, max(a_pos::INT) AS src_rad_inp, max(liver_incl::INT) AS liv_inp FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NOT NULL GROUP BY hadm_id").fetchdf()
        df = df.merge(dcs, on="hadm_id", how="left").merge(ri, on="hadm_id", how="left").fillna({"src_dc": 0, "src_rad_inp": 0, "liv_inp": 0})
        op = con.execute(f"SELECT subject_id, charttime, a_pos, liver_incl FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NULL AND (a_pos OR liver_incl)").fetchdf()
        m = df[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
        d = (pd.to_datetime(m.charttime) - pd.to_datetime(m.admittime)).dt.total_seconds() / 86400.0
        w = (d >= -365) & (d <= 30)
        df["src_rad_out"] = df.hadm_id.isin(set(m[w & m.a_pos].hadm_id))
        df["imaging_observed"] = df.liv_inp.astype(bool) | df.hadm_id.isin(set(m[w & m.liver_incl].hadm_id))
        for c in ("src_dc", "src_rad_inp"):
            df[c] = df[c].astype(bool)
    return df


class Boot:
    """Subject-cluster bootstrap: multinomial weights over the subjects of the frame it is built on."""

    def __init__(self, subject_ids, reps=REPS, seed=SEED):
        codes, self.idx = np.unique(np.asarray(subject_ids), return_inverse=True)
        self.ns = len(codes)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(self.ns, np.full(self.ns, 1.0 / self.ns), size=reps).astype(np.float64)

    def _by_subject(self, v):
        s = np.zeros(self.ns)
        np.add.at(s, self.idx, np.asarray(v, dtype=float))
        return s

    def ratio_ci(self, num, den):
        """95% percentile interval for sum(num)/sum(den), in percent. num, den: per-admission arrays."""
        n, d = self.W @ self._by_subject(num), self.W @ self._by_subject(den)
        with np.errstate(divide="ignore", invalid="ignore"):
            r = 100 * n / d
        lo, hi = np.nanpercentile(r, [2.5, 97.5])
        return [round(float(lo), 1), round(float(hi), 1)]


def mask(n):
    n = int(n)
    return "<11" if 0 < n < FLOOR else n


def wilson(x, n, z=1.96):
    c, h = (x + z * z / 2) / (n + z * z), z * np.sqrt(x * (n - x) / n + z * z / 4) / (n + z * z)
    return [round(100 * max(float(c - h), 0.0), 1), round(100 * min(float(c + h), 1.0), 1)]


def share(x, n, ci=None, digits=1):
    """Published form of x of n. Not reported when n < 11; share withheld when x or n-x is 1-10."""
    x, n = int(x), int(n)
    if n < FLOOR:
        return {"n": mask(n), "reported": False, "why": "denominator below 11"}
    if 0 < x < FLOOR or 0 < n - x < FLOOR:
        return {"n": n, "x": "<11" if 0 < x < FLOOR else "withheld", "pct": "withheld", "reported": False,
                "why": "numerator or its complement is 1-10"}
    out = {"n": n, "x": x, "pct": round(100 * x / n, digits), "reported": True}
    if ci is not None:
        out["ci95"] = ci
    return out


def protect_partition(counts):
    """counts: {stratum: n} partitioning a public total -> {stratum: published n}. A count of 1-10 is masked;
    then the smallest other non-zero stratum is rounded to the nearest 100 (returned as '~N')."""
    out = {k: mask(v) for k, v in counts.items()}
    hidden = [k for k, v in counts.items() if 0 < int(v) < FLOOR]
    if len(hidden) == 1:
        rest = [k for k, v in counts.items() if int(v) >= FLOOR]
        if rest:
            k = min(rest, key=lambda k: counts[k])
            out[k] = f"~{int(round(counts[k], -2)):,}"
    return out


def med_iqr(v):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < FLOOR:
        return None
    q = np.percentile(v, [25, 50, 75])
    return {"median": round(float(q[1]), 2), "q1": round(float(q[0]), 2), "q3": round(float(q[2]), 2)}
