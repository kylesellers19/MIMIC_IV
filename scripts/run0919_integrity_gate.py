#!/usr/bin/env python3
"""run_2026-09-19 Phase 0.2/0.3 — frozen-artifact hashes and anchor-number reproduction.

Reads stored derivatives only (no raw notes). Writes aggregates only:
  docs/run_2026-09-19/results/frozen_hashes_start.json   (sha256 + sizes)
  docs/run_2026-09-19/results/integrity_gate.json        (anchor vs reproduced)
"""
import hashlib, json, os, sys
import duckdb
sys.path.insert(0, os.getcwd())
from scripts.masld_config import CLEAN_POP

FROZEN = ["scripts/note_phenotype.py", "docs/note_phenotype_spec.md", "sql/masld_coded.sql",
          CLEAN_POP, "data/processed/aim1a_sample.parquet"]  # aim1a_sample.parquet IS the master key
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
hashes = {p: {"sha256": sha(p), "bytes": os.path.getsize(p)} for p in FROZEN}
json.dump(hashes, open("docs/run_2026-09-19/results/frozen_hashes_start.json", "w"), indent=1)

ANCHOR = {
 "pop_admissions": 373992, "pop_subjects": 161119, "code_positive": 5740,
 "b": {"A": 5027, "B": 22799, "C": 713, "D": 345453},
 "a": {"A": 4805, "B": 13612, "C": 935, "D": 354640},
 "c": {"A": 4908, "B": 17851, "C": 832, "D": 350401},
 "d": {"A": 4850, "B": 22443, "C": 890, "D": 345809},
 "note_pos_primary": 27826, "recovery_share_pct": 81.9, "corroboration_share_pct": 87.6,
 "alloc": {"B": 150, "A": 80, "C": 70, "D": 100},
 "weights": {"A": 62.8375, "B": 151.9933, "C": 10.1857, "D": 3454.53},
 "imaging_observed": 138603,
}
con = duckdb.connect()
got = {}
r = con.execute(f"SELECT count(*), count(DISTINCT subject_id), sum(code_positive::INT) FROM read_parquet('{CLEAN_POP}')").fetchone()
got["pop_admissions"], got["pop_subjects"], got["code_positive"] = int(r[0]), int(r[1]), int(r[2])
r2 = con.execute("SELECT count(*), count(DISTINCT subject_id) FROM read_parquet('data/processed/aim1a_frame.parquet')").fetchone()
got["frame_admissions"], got["frame_subjects"] = int(r2[0]), int(r2[1])
for d in "abcd":
    q = f"""SELECT sum((code_positive AND note_{d})::INT), sum((NOT code_positive AND note_{d})::INT),
                   sum((code_positive AND NOT note_{d})::INT), sum((NOT code_positive AND NOT note_{d})::INT)
            FROM read_parquet('data/processed/aim1a_frame.parquet')"""
    A,B,C,D = [int(x) for x in con.execute(q).fetchone()]
    got[d] = {"A":A,"B":B,"C":C,"D":D}
b = got["b"]
got["note_pos_primary"] = b["A"]+b["B"]
got["recovery_share_pct"] = round(100*b["B"]/(b["A"]+b["B"]), 1)
got["corroboration_share_pct"] = round(100*b["A"]/(b["A"]+b["C"]), 1)
cellmap = {"code+/note+":"A","code-/note+":"B","code+/note-":"C","code-/note-":"D"}
rows = con.execute("SELECT cell, count(*), round(min(weight),4), round(max(weight),4), sum(double_review::INT) FROM read_parquet('data/processed/aim1a_sample.parquet') GROUP BY cell").fetchall()
got["alloc"] = {cellmap[c]: int(n) for c,n,_,_,_ in rows}
got["weights"] = {cellmap[c]: float(w1) for c,_,w1,w2,_ in rows}
got["weights_min_eq_max"] = all(w1==w2 for _,_,w1,w2,_ in rows)
got["double_review_total"] = int(sum(x[4] for x in rows))
# sample cells agree with frame under definition (b)
got["sample_cell_matches_frame_b"] = int(con.execute(f"""
  SELECT count(*) FROM read_parquet('data/processed/aim1a_sample.parquet') s
  JOIN read_parquet('data/processed/aim1a_frame.parquet') f USING (hadm_id)
  WHERE s.cell = CASE WHEN f.code_positive AND f.note_b THEN 'code+/note+'
                      WHEN NOT f.code_positive AND f.note_b THEN 'code-/note+'
                      WHEN f.code_positive AND NOT f.note_b THEN 'code+/note-' ELSE 'code-/note-' END""").fetchone()[0])
got["imaging_observed"] = None  # filled from imaging_denominator outputs if a derivative exists; else doc-only check
checks = {}
for k in ["pop_admissions","pop_subjects","code_positive","note_pos_primary","recovery_share_pct","corroboration_share_pct"]:
    checks[k] = (ANCHOR[k] == got[k])
for d in "abcd":
    checks[f"cells_{d}"] = ANCHOR[d] == got[d]
checks["alloc"] = ANCHOR["alloc"] == got["alloc"]
checks["weights"] = all(abs(ANCHOR["weights"][k]-got["weights"][k]) < 0.01 for k in "ABCD")
checks["sample_cells_consistent"] = got["sample_cell_matches_frame_b"] == 400
checks["double_review_100"] = got["double_review_total"] == 100
out = {"anchor": ANCHOR, "reproduced": got, "checks": checks, "all_pass": all(checks.values())}
json.dump(out, open("docs/run_2026-09-19/results/integrity_gate.json", "w"), indent=1)
print(json.dumps({"checks": checks, "all_pass": out["all_pass"]}, indent=1))
print("reproduced:", {k: got[k] for k in got if k not in ("weights",)})
