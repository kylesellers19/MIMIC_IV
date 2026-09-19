#!/usr/bin/env python3
"""run_2026-09-19 Phase 6.2 — packet feasibility and reading burden for the 400 sampled admissions
(+ the 20 training charts, overall only).

For each packet element the availability rate per cell (n = 80/150/70/100, all >= 11) is computed from the
data: discharge summary present; count of inpatient radiology reports; count of outpatient radiology reports
within -365/+30 days of admission; each of the ten approved labs present (hadm_id-linked, and the wider
"in-admission" definition used by the packet generator: hadm_id-linked OR same subject with charttime inside
[admittime, dischtime]); BMI / SBP-DBP / weight / height from omr within -365/+30 days; >= 1 prescription.
Reading burden: median and 95th percentile of discharge-summary characters and of the number (and characters)
of linked radiology reports, by cell, from the per-note index (no text is read).

Aggregates only. Writes docs/run_2026-09-19/results/packet_feasibility.json.
"""
import json
import os
import sys
import time

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, LOCKED_POP, LAB_ITEMIDS, TRAINING_KEY, lab_itemid_csv

MASTER_KEY = "data/processed/aim1a_sample.parquet"
IDX = "data/processed/run_2026-09-19_notes_index"
OUT = "docs/run_2026-09-19/results/packet_feasibility.json"
CELLS = ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]
LETTER = {"code+/note+": "A", "code-/note+": "B", "code+/note-": "C", "code-/note-": "D"}
WIN_BEFORE, WIN_AFTER = 365, 30
BMI_NAMES = ("BMI (kg/m2)", "BMI")
BP_NAMES = ("Blood Pressure", "Blood Pressure Sitting", "Blood Pressure Standing (1 min)", "Blood Pressure Lying",
            "Blood Pressure Standing (3 mins)", "Blood Pressure Standing")
WT_NAMES = ("Weight (Lbs)", "Weight")
HT_NAMES = ("Height (Inches)", "Height")


def q(a, p):
    return float(np.percentile(a, p)) if len(a) else float("nan")


def burden(v):
    v = np.asarray(v, dtype=float)
    return {"median": q(v, 50), "p95": q(v, 95), "mean": float(v.mean()) if len(v) else float("nan"),
            "max": float(v.max()) if len(v) else float("nan"), "total": float(v.sum())}


def main():
    t0 = time.time()
    con = duckdb.connect()
    con.execute("SET memory_limit='16GB'")
    key = pd.read_parquet(MASTER_KEY)[["review_id", "hadm_id", "subject_id", "cell"]]
    key["set"] = "sample"
    tr = pd.read_parquet(TRAINING_KEY).rename(columns={"training_id": "review_id"})[["review_id", "hadm_id", "subject_id", "cell"]]
    tr["set"] = "training"
    charts = pd.concat([key, tr], ignore_index=True)
    pop = con.execute(f"SELECT hadm_id, admittime, dischtime FROM read_parquet('{LOCKED_POP}')").fetchdf()
    charts = charts.merge(pop, on="hadm_id", how="left")
    assert charts.admittime.notna().all() and len(charts) == 420
    charts["win_lo"] = charts.admittime - pd.Timedelta(days=WIN_BEFORE)
    charts["win_hi"] = charts.admittime + pd.Timedelta(days=WIN_AFTER)
    con.register("charts", charts[["review_id", "hadm_id", "subject_id", "set", "admittime", "dischtime", "win_lo", "win_hi"]])

    # --- notes from the index (no text)
    dc = con.execute(f"""SELECT c.review_id, count(n.note_id) AS n_dc, coalesce(sum(n.n_chars),0) AS dc_chars, coalesce(max(n.n_chars),0) AS dc_chars_max
                         FROM charts c LEFT JOIN read_parquet('{IDX}/discharge.parquet') n ON n.hadm_id = c.hadm_id GROUP BY 1""").fetchdf()
    rin = con.execute(f"""SELECT c.review_id, count(n.note_id) AS n_rad_in, coalesce(sum(n.n_chars),0) AS rad_in_chars, coalesce(sum(n.liver_incl::INT),0) AS n_rad_in_liver,
                                 coalesce(sum(CASE WHEN n.liver_incl::INT = 1 THEN n.n_chars ELSE 0 END),0) AS rad_in_liver_chars
                          FROM charts c LEFT JOIN read_parquet('{IDX}/radiology.parquet') n ON n.hadm_id = c.hadm_id GROUP BY 1""").fetchdf()
    rout = con.execute(f"""SELECT c.review_id, count(n.note_id) AS n_rad_out, coalesce(sum(n.n_chars),0) AS rad_out_chars, coalesce(sum(n.liver_incl::INT),0) AS n_rad_out_liver,
                                  coalesce(sum(CASE WHEN n.liver_incl::INT = 1 THEN n.n_chars ELSE 0 END),0) AS rad_out_liver_chars
                           FROM charts c LEFT JOIN read_parquet('{IDX}/radiology.parquet') n
                             ON n.subject_id = c.subject_id AND n.hadm_id IS NULL AND n.charttime >= c.win_lo AND n.charttime <= c.win_hi GROUP BY 1""").fetchdf()
    print(f"notes index joined {time.time()-t0:.0f}s", flush=True)

    # --- labs (one pass over labevents; subject filter first, then link)
    labs = con.execute(f"""SELECT l.subject_id, l.hadm_id, l.itemid, l.charttime
                           FROM read_csv('{DATA}/labevents.csv.gz', types={{'hadm_id':'BIGINT','itemid':'INTEGER','subject_id':'BIGINT'}}) l
                           WHERE l.itemid IN ({lab_itemid_csv()}) AND l.valuenum IS NOT NULL
                             AND l.subject_id IN (SELECT DISTINCT subject_id FROM charts)""").fetchdf()
    con.register("labs", labs)
    print(f"labevents filtered {time.time()-t0:.0f}s", flush=True)
    lab_link = con.execute("""SELECT c.review_id, l.itemid,
                                     max(CASE WHEN l.hadm_id = c.hadm_id THEN 1 ELSE 0 END) AS linked,
                                     max(CASE WHEN l.hadm_id = c.hadm_id OR (l.hadm_id IS NULL AND l.charttime BETWEEN c.admittime AND c.dischtime) THEN 1 ELSE 0 END) AS inadm
                              FROM charts c JOIN labs l ON l.subject_id = c.subject_id
                              GROUP BY 1, 2""").fetchdf()
    lab_n = con.execute("""SELECT c.review_id, count(*) AS n_lab_rows FROM charts c JOIN labs l ON l.subject_id = c.subject_id
                           WHERE l.hadm_id = c.hadm_id OR (l.hadm_id IS NULL AND l.charttime BETWEEN c.admittime AND c.dischtime) GROUP BY 1""").fetchdf()

    # --- omr within window
    omr = con.execute(f"""SELECT c.review_id, o.result_name
                          FROM charts c JOIN read_csv_auto('{DATA}/omr.csv.gz') o ON o.subject_id = c.subject_id
                          WHERE o.chartdate >= c.win_lo::DATE AND o.chartdate <= c.win_hi::DATE""").fetchdf()
    omr_n = omr.groupby("review_id").size().rename("n_omr_rows").reset_index()
    # --- prescriptions
    rx = con.execute(f"""SELECT c.review_id, count(*) AS n_rx FROM charts c JOIN read_csv_auto('{DATA}/prescriptions.csv.gz') p ON p.hadm_id = c.hadm_id GROUP BY 1""").fetchdf()
    print(f"omr + prescriptions {time.time()-t0:.0f}s", flush=True)

    # --- assemble per chart (stays in memory; never written)
    df = charts[["review_id", "cell", "set"]].merge(dc, on="review_id", how="left").merge(rin, on="review_id", how="left") \
        .merge(rout, on="review_id", how="left").merge(lab_n, on="review_id", how="left").merge(omr_n, on="review_id", how="left").merge(rx, on="review_id", how="left")
    for c in ("n_dc", "dc_chars", "dc_chars_max", "n_rad_in", "rad_in_chars", "n_rad_in_liver", "n_rad_out", "rad_out_chars", "n_rad_out_liver", "rad_in_liver_chars", "rad_out_liver_chars", "n_lab_rows", "n_omr_rows", "n_rx"):
        df[c] = df[c].fillna(0).astype(float)
    for name, itemid in LAB_ITEMIDS.items():
        sub = lab_link[lab_link.itemid == itemid][["review_id", "linked", "inadm"]]
        df = df.merge(sub.rename(columns={"linked": f"lab_{name}_linked", "inadm": f"lab_{name}_inadm"}), on="review_id", how="left")
        df[f"lab_{name}_linked"] = df[f"lab_{name}_linked"].fillna(0).astype(int)
        df[f"lab_{name}_inadm"] = df[f"lab_{name}_inadm"].fillna(0).astype(int)
    for lab, names in (("BMI", BMI_NAMES), ("BP", BP_NAMES), ("weight", WT_NAMES), ("height", HT_NAMES)):
        ids = set(omr[omr.result_name.isin(names)].review_id)
        df[f"omr_{lab}"] = df.review_id.isin(ids).astype(int)
    df["any_omr"] = (df.n_omr_rows > 0).astype(int)
    df["rad_total"] = df.n_rad_in + df.n_rad_out
    df["rad_total_chars"] = df.rad_in_chars + df.rad_out_chars
    df["packet_chars"] = df.dc_chars + df.rad_total_chars
    df["rad_liver_total"] = df.n_rad_in_liver + df.n_rad_out_liver
    df["rad_liver_chars"] = df.rad_in_liver_chars + df.rad_out_liver_chars
    df["focused_chars"] = df.dc_chars + df.rad_liver_chars

    def block(g):
        n = int(len(g))
        out = {"n": n,
               "availability_pct": {
                   "discharge_summary": 100 * float((g.n_dc > 0).mean()),
                   "any_inpatient_radiology": 100 * float((g.n_rad_in > 0).mean()),
                   "any_outpatient_radiology_window": 100 * float((g.n_rad_out > 0).mean()),
                   "any_radiology": 100 * float((g.rad_total > 0).mean()),
                   "any_liver_inclusive_radiology": 100 * float(((g.n_rad_in_liver + g.n_rad_out_liver) > 0).mean()),
                   "any_lab_row_inadm": 100 * float((g.n_lab_rows > 0).mean()),
                   "any_omr_window": 100 * float((g.any_omr > 0).mean()),
                   "omr_BMI": 100 * float(g.omr_BMI.mean()), "omr_BP": 100 * float(g.omr_BP.mean()),
                   "omr_weight": 100 * float(g.omr_weight.mean()), "omr_height": 100 * float(g.omr_height.mean()),
                   "any_prescription": 100 * float((g.n_rx > 0).mean()),
               },
               "labs_present_pct_hadm_linked": {k: 100 * float(g[f"lab_{k}_linked"].mean()) for k in LAB_ITEMIDS},
               "labs_present_pct_in_admission": {k: 100 * float(g[f"lab_{k}_inadm"].mean()) for k in LAB_ITEMIDS},
               "reading_burden": {
                   "discharge_chars": burden(g.dc_chars), "discharge_notes_per_admission": burden(g.n_dc),
                   "radiology_reports_inpatient": burden(g.n_rad_in), "radiology_reports_outpatient_window": burden(g.n_rad_out),
                   "radiology_reports_total": burden(g.rad_total), "radiology_chars_total": burden(g.rad_total_chars),
                   "packet_narrative_chars": burden(g.packet_chars),
                   "radiology_reports_liver_inclusive": burden(g.rad_liver_total), "radiology_chars_liver_inclusive": burden(g.rad_liver_chars),
                   "focused_read_chars_discharge_plus_liver_radiology": burden(g.focused_chars),
                   "lab_rows_in_admission": burden(g.n_lab_rows), "omr_rows_window": burden(g.n_omr_rows), "prescription_rows": burden(g.n_rx),
               }}
        return out

    s = df[df.set == "sample"]
    res = {"script": "scripts/run0919_packet_feasibility.py", "window_days": {"before_admission": WIN_BEFORE, "after_admission": WIN_AFTER},
           "lab_itemids": LAB_ITEMIDS, "omr_result_names": {"BMI": BMI_NAMES, "BP": BP_NAMES, "weight": WT_NAMES, "height": HT_NAMES},
           "in_admission_lab_definition": "labevents row with hadm_id = the admission, OR hadm_id NULL for the same subject with charttime in [admittime, dischtime]",
           "sample_overall": block(s), "sample_by_cell": {LETTER[c]: block(s[s.cell == c]) for c in CELLS},
           "training_overall": block(df[df.set == "training"]),
           "not_suppliable_by_mimic": [
               "quantified alcohol intake (g/week) — only narrative mentions in notes; no structured field",
               "liver biopsy / pathology reports as a structured source — MIMIC-IV-Note has discharge and radiology notes only; biopsy results appear only if narrated in the discharge summary",
               "waist circumference — not in omr (omr carries BMI, weight, height, blood pressure, eGFR)",
               "structured diabetes / hypertension / dyslipidaemia diagnoses — ICD codes are stripped by design; reviewers infer from HbA1c, glucose, lipids, BP, medication orders and narrative",
               "outpatient laboratory values in the -365/+30 window — labevents rows without hadm_id exist but are not part of the packet (criteria §1 lists in-admission labs); computable later if the criteria ask",
               "elastography / FIB-4 / imaging-derived fat fraction as structured values — only if narrated in a radiology report",
           ],
           "runtime_s": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    so = res["sample_overall"]
    print(f"sample n={so['n']}: discharge {so['availability_pct']['discharge_summary']:.1f}%  any radiology {so['availability_pct']['any_radiology']:.1f}%  "
          f"rx {so['availability_pct']['any_prescription']:.1f}%  BMI {so['availability_pct']['omr_BMI']:.1f}%  "
          f"discharge chars median {so['reading_burden']['discharge_chars']['median']:.0f} p95 {so['reading_burden']['discharge_chars']['p95']:.0f}  "
          f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
