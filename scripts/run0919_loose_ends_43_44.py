#!/usr/bin/env python3
"""run_2026-09-19 Phase 4.3 (discharge-summary-only population) and 4.4 (Tier C hedged counted positive).
Reads the frame and the per-note index (flags only). Writes docs/run_2026-09-19/results/loose_ends_43_44.json."""
import json, os, sys
import duckdb, pandas as pd, numpy as np
sys.path.insert(0, os.getcwd())
from scripts.masld_config import LOCKED_POP
IDX = "data/processed/run_2026-09-19_notes_index"
con = duckdb.connect()
f = con.execute(f"""SELECT f.hadm_id, f.subject_id, f.code_positive, f.note_a, f.note_b, f.has_dc, f.has_rad, l.admittime
                    FROM read_parquet('data/processed/aim1a_frame.parquet') f JOIN read_parquet('{LOCKED_POP}') l USING (hadm_id)""").fetchdf()
def cells(cp, nt):
    cp = cp.astype(bool); nt = nt.astype(bool)
    c = {"A": int((cp & nt).sum()), "B": int((~cp & nt).sum()), "C": int((cp & ~nt).sum()), "D": int((~cp & ~nt).sum())}
    c["recovery_share_pct"] = round(100*c["B"]/(c["A"]+c["B"]), 2); c["corroboration_share_pct"] = round(100*c["A"]/(c["A"]+c["C"]), 2); return c
res = {}
# ---- 4.3 discharge-only ----
d = f[f.has_dc]
res["discharge_only"] = {"admissions": int(len(d)), "subjects": int(d.subject_id.nunique()), "code_positive": int(d.code_positive.sum()),
                         "a": cells(d.code_positive, d.note_a), "b": cells(d.code_positive, d.note_b),
                         "full_population_for_reference": {"a": cells(f.code_positive, f.note_a), "b": cells(f.code_positive, f.note_b)}}
# ---- 4.4 Tier C counted positive ----
inp = con.execute(f"""SELECT hadm_id, max(a_pos::INT) AS a, max(c_hedged::INT) AS c FROM (
        SELECT hadm_id, a_pos, c_hedged FROM read_parquet('{IDX}/discharge.parquet') WHERE hadm_id IS NOT NULL
        UNION ALL SELECT hadm_id, a_pos, c_hedged FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NOT NULL) GROUP BY hadm_id""").fetchdf()
f = f.merge(inp, on="hadm_id", how="left").fillna({"a": 0, "c": 0})
# consistency check: index-derived inpatient Tier A == frame note_a
res["check_index_note_a_matches_frame"] = bool((f.a.astype(bool) == f.note_a.astype(bool)).all())
res["check_mismatch_count"] = int((f.a.astype(bool) != f.note_a.astype(bool)).sum())
op = con.execute(f"SELECT subject_id, charttime, a_pos, c_hedged FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NULL AND (a_pos OR c_hedged)").fetchdf()
op = op[op.subject_id.isin(set(f.subject_id))]
m = f[["hadm_id", "subject_id", "admittime"]].merge(op, on="subject_id", how="inner")
dt = (pd.to_datetime(m.charttime) - pd.to_datetime(m.admittime)).dt.total_seconds() / 86400.0
win = (dt >= -365) & (dt <= 30)
out_a = set(m[win & m.a_pos].hadm_id); out_c = set(m[win & m.c_hedged].hadm_id)
f["note_b_rebuilt"] = f.a.astype(bool) | f.hadm_id.isin(out_a)
res["check_index_note_b_matches_frame"] = bool((f.note_b_rebuilt == f.note_b.astype(bool)).all())
f["tierC_a"] = f.c.astype(bool)                      # inpatient-linked hedged
f["tierC_b"] = f.c.astype(bool) | f.hadm_id.isin(out_c)
f["note_a_withC"] = f.note_a.astype(bool) | f.tierC_a
f["note_b_withC"] = f.note_b.astype(bool) | f.tierC_b
res["tierC_positive"] = {"a": {"primary": cells(f.code_positive, f.note_a), "tierC_counted_positive": cells(f.code_positive, f.note_a_withC),
                               "admissions_added": int((f.note_a_withC & ~f.note_a.astype(bool)).sum())},
                         "b": {"primary": cells(f.code_positive, f.note_b), "tierC_counted_positive": cells(f.code_positive, f.note_b_withC),
                               "admissions_added": int((f.note_b_withC & ~f.note_b.astype(bool)).sum())},
                         "any_tierC_b_by_primary_cell": {}}
cellb = np.select([f.code_positive & f.note_b, ~f.code_positive & f.note_b, f.code_positive & ~f.note_b], ["A", "B", "C"], "D")
for c in "ABCD":
    sel = cellb == c
    res["tierC_positive"]["any_tierC_b_by_primary_cell"][c] = {"n": int(sel.sum()), "with_tierC": int(f.tierC_b[sel].sum())}
json.dump(res, open("docs/run_2026-09-19/results/loose_ends_43_44.json", "w"), indent=1)
print(json.dumps(res, indent=1)[:2500])
