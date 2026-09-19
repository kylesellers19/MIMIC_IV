#!/usr/bin/env python3
"""Reviewer packet generator — one self-contained plain-text file per chart under its blinded ID.

Contents (criteria §1 only): discharge summary full text; all linked radiology reports (inpatient, and
outpatient within -365/+30 days of admission) with charttime as day offsets from admission; laboratory
values for the ten approved analytes (in-admission: hadm_id-linked, or same subject with charttime inside
[admittime, dischtime]) as day offsets; vitals/anthropometrics from omr (BMI, blood pressure, weight, height)
within -365/+30 days; medication orders (drug, route, dose, start/stop day offsets); age at admission and sex.

Stripped by construction: note_id, subject_id, hadm_id, dates, ICD codes and coded problem lists, race,
insurance, language, marital status, cell membership, rule output and any trigger highlighting. Clinician-
written narrative — including a narrative "Discharge Diagnosis:" section — is kept verbatim.

Modes
  --dryrun          write all 420 packets (400 sample + 20 training) to data/processed/_packet_dryrun/, run the
                    leak checks (counts only) -> docs/run_2026-09-19/results/packet_dryrun.json, then delete
                    the directory (shutil.rmtree guarded by an assertion on the exact path).
  --out DIR         final generation into DIR (untracked; must not be under docs/). Leak checks run too and
                    their counts are printed; the packets are left in place. Run after the criteria are frozen:
                        scripts/run0919_env.sh scripts/make_reviewer_packets.py --out data/processed/adjudication/packets

Nothing patient-level is printed: counts, timings and exception class names only.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import sys
import time
from collections import Counter

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.masld_config import DATA, LOCKED_POP, LAB_ITEMIDS, TRAINING_KEY, lab_itemid_csv

NOTE = "data/raw/note"
MASTER_KEY = "data/processed/aim1a_sample.parquet"
IDX = "data/processed/run_2026-09-19_notes_index"
DRYRUN_DIR = "data/processed/_packet_dryrun"
DRYRUN_JSON = "docs/run_2026-09-19/results/packet_dryrun.json"
WIN_BEFORE, WIN_AFTER = 365, 30
ITEM_NAME = {v: k.replace("_", " ") for k, v in LAB_ITEMIDS.items()}
OMR_KEEP = {"BMI (kg/m2)": "BMI (kg/m2)", "BMI": "BMI", "Blood Pressure": "Blood pressure", "Blood Pressure Sitting": "Blood pressure (sitting)",
            "Blood Pressure Standing (1 min)": "Blood pressure (standing, 1 min)", "Blood Pressure Standing (3 mins)": "Blood pressure (standing, 3 min)",
            "Blood Pressure Standing": "Blood pressure (standing)", "Blood Pressure Lying": "Blood pressure (lying)",
            "Weight (Lbs)": "Weight (lb)", "Weight": "Weight", "Height (Inches)": "Height (in)", "Height": "Height"}
BEGIN, END = "----- BEGIN NOTE TEXT -----", "----- END NOTE TEXT -----"

# leak-check patterns
RX_ICD10 = re.compile(r"\b[A-TV-Z]\d{2}(\.\d{1,4})?\b")
RX_ICD9 = re.compile(r"\b\d{3}\.\d{1,2}\b")
RX_ICD9_UNSIGNED = re.compile(r"(?<![+\-.\d])\b\d{3}\.\d{1,2}\b(?!\.\d)")   # same shape, but not a signed day offset
LONG_TITLES = ["fatty (change of) liver", "nonalcoholic steatohepatitis", "other chronic nonalcoholic liver disease",
               "unspecified chronic liver disease without mention of alcohol"]
RX_DEMO = re.compile(r"\b(race|insurance|language|ethnicity|marital)\b", re.I)
RX_8DIG = re.compile(r"\b[12]\d{7}\b")
CELL_LABELS = ["code+/note", "code-/note", "recovery"]
MARKUP = ["<mark", "**", "[MASK]", "[["]


def day(ts, admit):
    if pd.isna(ts):
        return "n/a"
    d = (pd.Timestamp(ts) - admit).total_seconds() / 86400.0
    return f"{d:+.1f}"


def fmt_val(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def load_inputs(charts, con, t0):
    con.register("charts", charts[["review_id", "hadm_id", "subject_id", "admittime", "dischtime", "win_lo", "win_hi"]])
    dc = con.execute(f"""SELECT c.review_id, d.note_seq, d.charttime, d.text
                         FROM read_csv_auto('{NOTE}/discharge.csv.gz') d JOIN charts c ON d.hadm_id = c.hadm_id""").fetchdf()
    print(f"discharge notes: {len(dc):,} rows  {time.time()-t0:.0f}s", flush=True)
    rad = con.execute(f"""SELECT c.review_id, r.note_id, r.hadm_id, r.charttime, r.text,
                                 CASE WHEN r.hadm_id = c.hadm_id THEN 'inpatient' ELSE 'outpatient' END AS setting
                          FROM read_csv_auto('{NOTE}/radiology.csv.gz') r JOIN charts c ON r.subject_id = c.subject_id
                          WHERE r.hadm_id = c.hadm_id OR (r.hadm_id IS NULL AND r.charttime >= c.win_lo AND r.charttime <= c.win_hi)""").fetchdf()
    con.register("rad", rad[["note_id"]])
    ex = con.execute(f"""SELECT d.note_id, string_agg(d.field_value, ' | ' ORDER BY d.field_ordinal) AS exam_name
                         FROM read_csv_auto('{NOTE}/radiology_detail.csv.gz') d WHERE d.field_name = 'exam_name' AND d.note_id IN (SELECT note_id FROM rad)
                         GROUP BY d.note_id""").fetchdf()
    rad = rad.merge(ex, on="note_id", how="left")
    print(f"radiology reports: {len(rad):,} rows  {time.time()-t0:.0f}s", flush=True)
    labs = con.execute(f"""SELECT c.review_id, l.itemid, l.charttime, l.valuenum, l.valueuom, l.flag, l.ref_range_lower, l.ref_range_upper
                           FROM read_csv('{DATA}/labevents.csv.gz', types={{'hadm_id':'BIGINT','itemid':'INTEGER','subject_id':'BIGINT'}}) l
                           JOIN charts c ON l.subject_id = c.subject_id
                           WHERE l.itemid IN ({lab_itemid_csv()}) AND l.valuenum IS NOT NULL
                             AND (l.hadm_id = c.hadm_id OR (l.hadm_id IS NULL AND l.charttime BETWEEN c.admittime AND c.dischtime))""").fetchdf()
    print(f"lab rows: {len(labs):,}  {time.time()-t0:.0f}s", flush=True)
    omr = con.execute(f"""SELECT c.review_id, o.chartdate, o.result_name, o.result_value
                          FROM read_csv_auto('{DATA}/omr.csv.gz') o JOIN charts c ON o.subject_id = c.subject_id
                          WHERE o.chartdate >= c.win_lo::DATE AND o.chartdate <= c.win_hi::DATE""").fetchdf()
    omr = omr[omr.result_name.isin(OMR_KEEP)]
    print(f"omr rows: {len(omr):,}  {time.time()-t0:.0f}s", flush=True)
    rx = con.execute(f"""SELECT c.review_id, p.drug, p.route, p.starttime, p.stoptime, p.dose_val_rx, p.dose_unit_rx
                         FROM read_csv_auto('{DATA}/prescriptions.csv.gz') p JOIN charts c ON p.hadm_id = c.hadm_id""").fetchdf()
    print(f"prescription rows: {len(rx):,}  {time.time()-t0:.0f}s", flush=True)
    return dc, rad, labs, omr, rx


def build_packet(row, dc, rad, labs, omr, rx):
    """Return the packet text for one chart. `row` is a namedtuple from charts.itertuples()."""
    admit = pd.Timestamp(row.admittime)
    los = (pd.Timestamp(row.dischtime) - admit).total_seconds() / 86400.0
    age = int(row.age)
    age_s = "89 or older" if age >= 89 else str(age)
    sex = {"F": "Female", "M": "Male"}.get(row.gender, "Not recorded")
    L = [f"HEPATIC STEATOSIS CHART REVIEW  --  PACKET {row.review_id}", "",
         f"Age at admission: {age_s}    Sex: {sex}    Length of stay: {los:.1f} days",
         "All times are day offsets from the admission time (day +0.0); negative values are before admission.",
         "Blank underscores (___) in note text are de-identification placeholders in the source data.", ""]
    # discharge summary
    d = dc.sort_values("note_seq")
    L += ["=" * 78, f"SECTION 1 -- DISCHARGE SUMMARY ({len(d)} document{'s' if len(d) != 1 else ''})", "=" * 78]
    if len(d) == 0:
        L.append("(no discharge summary linked to this admission)")
    for k, r in enumerate(d.itertuples(), start=1):
        L += [f"--- Discharge document {k} of {len(d)} -- written day {day(r.charttime, admit)} ---", BEGIN, r.text if isinstance(r.text, str) else "", END, ""]
    # radiology
    r_in = rad[rad.setting == "inpatient"].sort_values("charttime")
    r_out = rad[rad.setting == "outpatient"].sort_values("charttime")
    L += ["=" * 78, f"SECTION 2 -- RADIOLOGY REPORTS ({len(r_in)} during this admission; {len(r_out)} outpatient within -{WIN_BEFORE}/+{WIN_AFTER} days)", "=" * 78]
    if len(rad) == 0:
        L.append("(no radiology reports linked to this admission or its window)")
    k = 0
    for setting, sub in (("during this admission", r_in), ("outpatient", r_out)):
        for r in sub.itertuples():
            k += 1
            exam = r.exam_name if isinstance(r.exam_name, str) else "(exam name not recorded)"
            L += [f"--- Report {k} of {len(rad)} -- {setting} -- day {day(r.charttime, admit)} -- Exam: {exam} ---", BEGIN, r.text if isinstance(r.text, str) else "", END, ""]
    # labs
    L += ["=" * 78, "SECTION 3 -- LABORATORY VALUES (ten analytes, this admission)", "=" * 78,
          "day | analyte | value | unit | flag | reference range"]
    if len(labs) == 0:
        L.append("(none of the ten analytes measured during this admission)")
    for r in labs.sort_values(["charttime", "itemid"]).itertuples():
        ref = f"{fmt_val(r.ref_range_lower)}-{fmt_val(r.ref_range_upper)}" if not (pd.isna(r.ref_range_lower) and pd.isna(r.ref_range_upper)) else ""
        L.append(f"{day(r.charttime, admit)} | {ITEM_NAME.get(int(r.itemid), 'analyte')} | {fmt_val(r.valuenum)} | {fmt_val(r.valueuom)} | {fmt_val(r.flag)} | {ref}")
    L.append("")
    # omr
    L += ["=" * 78, f"SECTION 4 -- VITALS AND ANTHROPOMETRICS (outpatient measurements within -{WIN_BEFORE}/+{WIN_AFTER} days)", "=" * 78,
          "day | measure | value"]
    if len(omr) == 0:
        L.append("(no BMI, blood pressure, weight or height recorded in the window)")
    for r in omr.sort_values(["chartdate", "result_name"]).itertuples():
        L.append(f"{day(pd.Timestamp(r.chartdate), admit)} | {OMR_KEEP[r.result_name]} | {fmt_val(r.result_value)}")
    L.append("")
    # medications
    L += ["=" * 78, "SECTION 5 -- MEDICATION ORDERS (this admission)", "=" * 78, "drug | route | start day | stop day | dose"]
    if len(rx) == 0:
        L.append("(no medication orders recorded for this admission)")
    for r in rx.sort_values(["starttime", "drug"]).itertuples():
        dose = f"{fmt_val(r.dose_val_rx)} {fmt_val(r.dose_unit_rx)}".strip()
        L.append(f"{fmt_val(r.drug)} | {fmt_val(r.route)} | {day(r.starttime, admit)} | {day(r.stoptime, admit)} | {dose}")
    L += ["", "=" * 78, "END OF PACKET", "=" * 78, ""]
    return "\n".join(L)


# ----------------------------------------------------------------------------------------------
# Leak checks (counts only)
# ----------------------------------------------------------------------------------------------
def split_sections(txt):
    """Return (narrative_segments, structured_text, structured_without_values)."""
    narrative, structured = [], []
    inside = False
    for line in txt.split("\n"):
        if line == BEGIN:
            inside = True
            narrative.append([])
            continue
        if line == END:
            inside = False
            continue
        (narrative[-1] if inside else structured).append(line)
    structured_txt = "\n".join(structured)
    # drop the numeric value / dose / reference-range columns of the tabular sections
    no_val = []
    section = None
    for line in structured:
        if line.startswith("SECTION 3"):
            section = 3
        elif line.startswith("SECTION 4"):
            section = 4
        elif line.startswith("SECTION 5"):
            section = 5
        elif line.startswith("END OF PACKET"):
            section = None
        parts = line.split(" | ")
        if section == 3 and len(parts) == 6:
            no_val.append(" | ".join([parts[0], parts[1], parts[3], parts[4]]))
        elif section == 4 and len(parts) == 3:
            no_val.append(" | ".join([parts[0], parts[1]]))
        elif section == 5 and len(parts) == 5:
            no_val.append(" | ".join(parts[:4]))
        else:
            no_val.append(line)
    return ["\n".join(s) for s in narrative], structured_txt, "\n".join(no_val)


def leak_checks(paths, ids_by_file):
    c = Counter()
    files_with = Counter()
    tokens = Counter()
    sizes = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        sizes.append(len(txt.encode("utf-8")))
        narr, struct, struct_nv = split_sections(txt)
        narr_txt = "\n".join(narr)
        hits = Counter()
        hits["i_icd10_like_structured"] += len(RX_ICD10.findall(struct))
        hits["i_icd10_like_structured_excl_value_columns"] += len(RX_ICD10.findall(struct_nv))
        hits["i_icd9_like_structured"] += len(RX_ICD9.findall(struct))
        hits["i_icd9_like_structured_excl_value_columns"] += len(RX_ICD9.findall(struct_nv))
        hits["i_icd9_like_structured_excl_values_and_day_offsets"] += len(RX_ICD9_UNSIGNED.findall(struct_nv))
        sec = "header"
        for line in struct_nv.split("\n"):
            if line.startswith("SECTION "):
                sec = "section " + line[8]
            for mobj in RX_ICD10.finditer(line):
                tokens[f"icd10-shaped: {mobj.group(0)} ({sec})"] += 1
            for mobj in RX_ICD9_UNSIGNED.finditer(line):
                tokens[f"icd9-shaped: {mobj.group(0)} ({sec})"] += 1
        low_s, low_n = struct.lower(), narr_txt.lower()
        for t in LONG_TITLES:
            hits["ii_long_title_structured"] += low_s.count(t)
            hits["ii_long_title_narrative"] += low_n.count(t)
        hits["iii_demographic_label_structured"] += len(RX_DEMO.findall(struct))
        hits["iv_8digit_structured"] += len(RX_8DIG.findall(struct))
        hits["iv_8digit_narrative"] += len(RX_8DIG.findall(narr_txt))
        for t in CELL_LABELS:
            hits["v_cell_label_structured"] += low_s.count(t)
            hits["v_cell_label_narrative"] += low_n.count(t)
            if t == "recovery":
                hits["v_recovery_word_narrative_only"] += low_n.count(t)
        for t in MARKUP:
            hits["vi_markup_structured"] += struct.count(t)
            hits["vi_markup_narrative"] += narr_txt.count(t)
        for ident in ids_by_file[p]:
            hits["vii_own_identifier_structured"] += struct.count(ident)
            hits["vii_own_identifier_narrative"] += narr_txt.count(ident)
        for k, v in hits.items():
            c[k] += v
            if v:
                files_with[k] += 1
    def small(v):
        return "<11" if 0 < v < 11 else int(v)
    return {"counts": {k: small(v) for k, v in sorted(c.items())}, "files_with_any_hit": {k: small(v) for k, v in sorted(files_with.items())},
            "matched_tokens_structured_excl_values": {k: small(v) for k, v in tokens.most_common(15)},
            "small_count_rule": "counts of 1-10 are written as <11",
            "n_files": len(paths), "file_bytes_median": statistics.median(sizes) if sizes else 0,
            "file_bytes_p95": float(np.percentile(sizes, 95)) if sizes else 0, "file_bytes_max": max(sizes) if sizes else 0,
            "file_bytes_total": sum(sizes)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dryrun", action="store_true")
    g.add_argument("--out", default=None)
    a = ap.parse_args()
    t0 = time.time()
    out_dir = DRYRUN_DIR if a.dryrun else a.out
    assert not os.path.abspath(out_dir).startswith(os.path.abspath("docs")), "packets must not be written under docs/"
    if a.dryrun and os.path.exists(DRYRUN_DIR):
        assert os.path.abspath(DRYRUN_DIR) == os.path.abspath("data/processed/_packet_dryrun")
        shutil.rmtree(DRYRUN_DIR)
    os.makedirs(out_dir, exist_ok=True)

    key = pd.read_parquet(MASTER_KEY)[["review_id", "hadm_id", "subject_id"]]
    tr = pd.read_parquet(TRAINING_KEY).rename(columns={"training_id": "review_id"})[["review_id", "hadm_id", "subject_id"]]
    charts = pd.concat([key, tr], ignore_index=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='16GB'")
    pop = con.execute(f"SELECT hadm_id, admittime, dischtime, age, gender FROM read_parquet('{LOCKED_POP}')").fetchdf()
    charts = charts.merge(pop, on="hadm_id", how="left")
    assert len(charts) == 420 and charts.admittime.notna().all()
    charts["win_lo"] = charts.admittime - pd.Timedelta(days=WIN_BEFORE)
    charts["win_hi"] = charts.admittime + pd.Timedelta(days=WIN_AFTER)
    dc, rad, labs, omr, rx = load_inputs(charts, con, t0)
    idx_chars = con.execute(f"SELECT hadm_id, sum(n_chars) AS n FROM read_parquet('{IDX}/discharge.parquet') WHERE hadm_id IN (SELECT hadm_id FROM charts) GROUP BY 1").fetchdf()
    idx_chars = dict(zip(idx_chars.hadm_id, idx_chars.n))

    exc = Counter()
    written = []
    ids_by_file = {}
    verbatim_ok = 0
    n_dc_chars = 0
    t1 = time.time()
    for row in charts.itertuples():
        try:
            rid = row.review_id
            d = dc[dc.review_id == rid]
            txt = build_packet(row, d, rad[rad.review_id == rid], labs[labs.review_id == rid], omr[omr.review_id == rid], rx[rx.review_id == rid])
            p = os.path.join(out_dir, f"{rid}.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            written.append(p)
            ids_by_file[p] = [str(int(row.hadm_id)), str(int(row.subject_id))] + [str(n) for n in rad[rad.review_id == rid].note_id.tolist()]
            got = int(sum(len(t) for t in d.text if isinstance(t, str)))
            n_dc_chars += got
            verbatim_ok += int(got == int(idx_chars.get(row.hadm_id, 0)))
        except Exception as e:
            exc[type(e).__name__] += 1
    gen_s = time.time() - t1
    print(f"packets written: {len(written)} of {len(charts)} in {gen_s:.0f}s; exceptions by class: {dict(exc)}", flush=True)
    checks = leak_checks(written, ids_by_file)
    res = {"script": "scripts/make_reviewer_packets.py", "mode": "dryrun" if a.dryrun else "final", "n_charts": int(len(charts)),
           "n_sample": int(len(key)), "n_training": int(len(tr)), "files_generated": len(written), "exceptions_by_class": dict(exc),
           "discharge_text_verbatim_vs_index": {"charts_matching_index_char_count": verbatim_ok, "charts_with_discharge_text": int(dc.review_id.nunique()), "charts_total": int(len(charts)), "discharge_chars_total": n_dc_chars},
           "rows_pulled": {"discharge_notes": int(len(dc)), "radiology_reports": int(len(rad)), "radiology_inpatient": int((rad.setting == "inpatient").sum()),
                           "radiology_outpatient_window": int((rad.setting == "outpatient").sum()), "lab_rows": int(len(labs)), "omr_rows": int(len(omr)), "prescription_rows": int(len(rx))},
           "leak_checks": checks,
           "check_definitions": {
               "i": "ICD-code-like patterns in structured (non-narrative) text: ICD-10 \\b[A-TV-Z]\\d{2}(\\.\\d{1,4})?\\b and ICD-9 \\b\\d{3}\\.\\d{1,2}\\b; also reported with the numeric value/dose/reference columns of the lab, vitals and medication tables removed, since lab values (e.g. 145.0) legitimately match the ICD-9 shape and drug names such as 'Vitamin B12' match the ICD-10 shape",
               "ii": "long titles of the four phenotype codes, case-insensitive, narrative and structured counted separately",
               "iii": "demographic field labels (race, insurance, language, ethnicity, marital) as whole words in structured text",
               "iv": "8-digit integers \\b[12]\\d{7}\\b, structured and narrative counted separately (narrative hits would be numbers inside de-identified note text, not leaked identifiers)",
               "v": "cell labels 'code+/note', 'code-/note', 'recovery' anywhere; the plain word 'recovery' occurs in clinical narrative (e.g. 'recovery room') and is counted separately",
               "vi": "markup/highlighting tokens '<mark', '**', '[MASK]', '[[' anywhere, structured and narrative counted separately",
               "vii": "the chart's own hadm_id, subject_id and radiology note_ids as substrings, structured and narrative counted separately"},
           "timings_s": {"load_inputs": round(t1 - t0, 1), "generate": round(gen_s, 1), "total": round(time.time() - t0, 1)}}
    if a.dryrun:
        os.makedirs(os.path.dirname(DRYRUN_JSON), exist_ok=True)
        with open(DRYRUN_JSON, "w") as f:
            json.dump(res, f, indent=1)
        path = os.path.abspath(DRYRUN_DIR)
        assert path == os.path.abspath("data/processed/_packet_dryrun")
        shutil.rmtree(path)
        res["dryrun_dir_removed"] = not os.path.exists(path)
        with open(DRYRUN_JSON, "w") as f:
            json.dump(res, f, indent=1)
        print(f"dry run: {len(written)} files, median {checks['file_bytes_median']:.0f} bytes; directory removed: {res['dryrun_dir_removed']}")
    else:
        print(f"final: {len(written)} packets in {out_dir} (untracked). Leak-check counts: {checks['counts']}")
    print(json.dumps(checks["counts"]))
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
