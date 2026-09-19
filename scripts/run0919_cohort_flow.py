#!/usr/bin/env python3
"""run_2026-09-19 Phase 4.5 — exact cohort-flow counts from raw admissions + the per-note index (no note text).
Writes docs/run_2026-09-19/results/cohort_flow.json."""
import json, os, sys
import duckdb, pandas as pd
sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, CLEAN_POP, analysis_admissions_sql
IDX = "data/processed/run_2026-09-19_notes_index"
con = duckdb.connect(); con.execute("SET memory_limit='16GB'")
n_all = con.execute(f"SELECT count(*), count(DISTINCT subject_id) FROM read_csv_auto('{DATA}/admissions.csv.gz')").fetchone()
con.execute(f"CREATE TEMP VIEW ap AS {analysis_admissions_sql()}")
df = con.execute("SELECT hadm_id, subject_id, code_positive, anchor_year_group FROM ap").fetchdf()
dc = set(con.execute(f"SELECT DISTINCT hadm_id FROM read_parquet('{IDX}/discharge.parquet') WHERE hadm_id IS NOT NULL").fetchdf().hadm_id.astype("int64"))
rd = set(con.execute(f"SELECT DISTINCT hadm_id FROM read_parquet('{IDX}/radiology.parquet') WHERE hadm_id IS NOT NULL").fetchdf().hadm_id.astype("int64"))
df["has_dc"] = df.hadm_id.isin(dc); df["has_rad"] = df.hadm_id.isin(rd); df["has_note"] = df.has_dc | df.has_rad
df["subj_has_note"] = df.groupby("subject_id").has_note.transform("any")
rel = ~df.subj_has_note; enc = df.subj_has_note & ~df.has_note
# alternative framing requested by the run file: outside the note module's covered window vs inside with no linked note.
# The project found NO admission-year window (docs/analysis_population.md); the closest window-like quantity is anchor_year_group
# 2020-2022, which the earlier note_coverage.md called "uncovered". Report both framings.
outside = df.anchor_year_group.isin(["2020 - 2022"])
res = {"all_admissions": int(n_all[0]), "all_subjects": int(n_all[1]),
       "zero_dx_excluded": int(n_all[0] - len(df)), "analysis_population": int(len(df)), "analysis_subjects": int(df.subject_id.nunique()),
       "code_positive_pre_note_restriction": int(df.code_positive.sum()),
       "note_restriction": {"removed_total": int((~df.has_note).sum()),
                            "part_i_release_lineage_subject_absent_from_note_module": int(rel.sum()),
                            "part_ii_encounter_level_subject_has_notes_elsewhere_not_this_admission": int(enc.sum()),
                            "sum_check": int(rel.sum() + enc.sum()) == int((~df.has_note).sum())},
       "window_framing": {"anchor_year_groups": {str(k): int(v) for k, v in df.anchor_year_group.value_counts().sort_index().items()},
                          "removed_with_anchor_2020_2022": int((~df.has_note & outside).sum()),
                          "removed_with_anchor_before_2020": int((~df.has_note & ~outside).sum()),
                          "coverage_pct_by_anchor_group": {str(k): round(100*float(v), 2) for k, v in df.groupby("anchor_year_group").has_note.mean().items()}},
       "locked_population": int(df.has_note.sum()), "locked_subjects": int(df[df.has_note].subject_id.nunique()),
       "locked_code_positive": int(df[df.has_note].code_positive.sum()),
       "check_locked_equals_clean_pop": int(df.has_note.sum()) == con.execute(f"SELECT count(*) FROM read_parquet('{CLEAN_POP}')").fetchone()[0],
       "discharge_only": {"admissions": int(df.has_dc.sum()), "subjects": int(df[df.has_dc].subject_id.nunique()), "code_positive": int(df[df.has_dc].code_positive.sum())}}
json.dump(res, open("docs/run_2026-09-19/results/cohort_flow.json", "w"), indent=1)
print(json.dumps(res, indent=1))
