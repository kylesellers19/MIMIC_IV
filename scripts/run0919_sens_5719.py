#!/usr/bin/env python3
"""run_2026-09-19 Phase 4.1 — ICD-9 571.9 sensitivity. Computes; does NOT change the primary.
Writes docs/run_2026-09-19/results/sens_5719.json (aggregates; small cells <11 masked) and
data/processed/run_2026-09-19_private/sens_5719_exact.json (exact small counts, untracked)."""
import json, os, sys
import duckdb, pandas as pd, numpy as np
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP
FRAME = "data/processed/aim1a_frame.parquet"; SAMPLE = "data/processed/aim1a_sample.parquet"
ALLOC = {"code+/note+": 80, "code-/note+": 150, "code+/note-": 70, "code-/note-": 100}
con = duckdb.connect()
dx = con.execute(f"""
  SELECT hadm_id,
         max(CASE WHEN icd_version=9 AND trim(icd_code)='5719' THEN 1 ELSE 0 END) AS has_5719,
         max(CASE WHEN (icd_version=10 AND trim(icd_code) IN ('K760','K7581')) OR (icd_version=9 AND trim(icd_code)='5718') THEN 1 ELSE 0 END) AS has_other
  FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}) GROUP BY hadm_id""").fetchdf()
f = con.execute(f"SELECT hadm_id, subject_id, code_positive, note_a, note_b, note_c, note_d FROM read_parquet('{FRAME}')").fetchdf()
f = f.merge(dx, on="hadm_id", how="left").fillna({"has_5719": 0, "has_other": 0})
f["solely_5719"] = (f.code_positive) & (f.has_5719 == 1) & (f.has_other == 0)
f["code_pos_no5719"] = f.code_positive & ~f.solely_5719
assert (f.code_positive == ((f.has_5719 == 1) | (f.has_other == 1))).all()
def cells(cp, nt):
    return {"A": int((cp & nt).sum()), "B": int((~cp & nt).sum()), "C": int((cp & ~nt).sum()), "D": int((~cp & ~nt).sum())}
def shares(c):
    return {"recovery_share_pct": round(100*c["B"]/(c["A"]+c["B"]), 2), "corroboration_share_pct": round(100*c["A"]/(c["A"]+c["C"]), 2)}
res = {"solely_5719_admissions": int(f.solely_5719.sum()), "solely_5719_subjects": int(f[f.solely_5719].subject_id.nunique()),
       "any_5719_admissions": int((f.has_5719 == 1).sum()), "code_positive_current": int(f.code_positive.sum()),
       "code_positive_no5719": int(f.code_pos_no5719.sum()), "by_definition": {}}
for d in "abcd":
    nt = f[f"note_{d}"].astype(bool)
    s = f[f.solely_5719]
    res["by_definition"][d] = {"current": {**cells(f.code_positive, nt), **shares(cells(f.code_positive, nt))},
                               "no5719": {**cells(f.code_pos_no5719, nt), **shares(cells(f.code_pos_no5719, nt))},
                               "solely_5719_cells": {"A (->B)": int(s[f"note_{d}"].sum()), "C (->D)": int((~s[f"note_{d}"].astype(bool)).sum())}}
# sampled charts
smp = con.execute(f"SELECT hadm_id, cell FROM read_parquet('{SAMPLE}')").fetchdf().merge(f[["hadm_id", "solely_5719", "note_b"]], on="hadm_id")
ch = smp[smp.solely_5719]
n_change = int(len(ch)); n_A_to_B = int(ch.note_b.sum()); n_C_to_D = n_change - n_A_to_B
def mask(n): return "0" if n == 0 else ("1–10" if n < 11 else str(n))
b_new = res["by_definition"]["b"]["no5719"]
new_alloc = {"code+/note+": ALLOC["code+/note+"] - n_A_to_B, "code-/note+": ALLOC["code-/note+"] + n_A_to_B,
             "code+/note-": ALLOC["code+/note-"] - n_C_to_D, "code-/note-": ALLOC["code-/note-"] + n_C_to_D}
m = {"code+/note+": "A", "code-/note+": "B", "code+/note-": "C", "code-/note-": "D"}
res["sample"] = {"charts_changing_cell": mask(n_change), "A_to_B": mask(n_A_to_B), "C_to_D": mask(n_C_to_D),
                 "revised_allocation_if_dropped": {k: (mask(v) if 0 < v < 11 else v) for k, v in new_alloc.items()},
                 "revised_weights_if_dropped": {k: round(b_new[m[k]] / v, 4) for k, v in new_alloc.items()},
                 "current_weights": {k: round(res["by_definition"]["b"]["current"][m[k]] / ALLOC[k], 4) for k in ALLOC}}
os.makedirs("docs/run_2026-09-19/results", exist_ok=True)
json.dump(res, open("docs/run_2026-09-19/results/sens_5719.json", "w"), indent=1)
os.makedirs("data/processed/run_2026-09-19_private", exist_ok=True)
json.dump({"charts_changing_cell": n_change, "A_to_B": n_A_to_B, "C_to_D": n_C_to_D, "new_alloc": new_alloc},
          open("data/processed/run_2026-09-19_private/sens_5719_exact.json", "w"), indent=1)
print(json.dumps({k: res[k] for k in ["solely_5719_admissions", "solely_5719_subjects", "code_positive_no5719"]}), res["by_definition"]["b"], res["sample"]["charts_changing_cell"])
