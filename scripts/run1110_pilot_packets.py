#!/usr/bin/env python3
"""run_2026-11-10 Phase 6.2 — a timed pilot set for the study team. NOT adjudication.

Draws 30 DEV admissions (seed SEED_PILOT), 11 / 6 / 5 / 8 across cells B / A / C / D under definition (b),
the way the training draw was made (scripts/run0919_phase2_splits.py): a seeded draw within each cell, then a
seeded shuffle, then blinded IDs P001-P030, so neither the ID nor the order encodes the cell. DEV admissions
only: no subject of the 400-chart sample or the training set can be drawn, because those are GOLD_HOLDOUT.

Packets are built by the functions of scripts/make_reviewer_packets.py (same contents, same stripping, same
leak checks) into data/processed/pilot_packets_2026-11-10/, with a blank form that has the instrument's
columns, including minutes_spent. The key (blinded ID -> admission, cell) is written apart from the packets,
to data/processed/run_2026-11-10_private/pilot_key.parquet. Everything is untracked.

Purpose: let the study lead time the reading of real packets before clinicians are asked for hours.
Nothing produced from this set is a reference-standard label, and no result of the study uses it.

Nothing patient-level is printed. Writes counts to docs/run_2026-11-10/results/pilot_packets.json.
"""
import json, os, sys, time
from collections import Counter

import duckdb
import numpy as np
import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, os.getcwd())
from scripts.masld_config import LOCKED_POP, SPLITS_V1
from scripts import make_reviewer_packets as P
from scripts import make_adjudication_template as T

SEED_PILOT = 20261111
ALLOC = {"B": 11, "A": 6, "C": 5, "D": 8}
OUT = "data/processed/pilot_packets_2026-11-10"
KEY = "data/processed/run_2026-11-10_private/pilot_key.parquet"
RES = "docs/run_2026-11-10/results/pilot_packets.json"
LABEL = "STUDY-TEAM TIMED PILOT. NOT ADJUDICATION. Nothing recorded here is a reference-standard label."


def main():
    t0 = time.time()
    con = duckdb.connect(); con.execute("SET memory_limit='12GB'")
    df = con.execute(f"""SELECT f.hadm_id, f.subject_id,
           CASE WHEN f.code_positive AND f.note_b THEN 'A' WHEN NOT f.code_positive AND f.note_b THEN 'B'
                WHEN f.code_positive AND NOT f.note_b THEN 'C' ELSE 'D' END AS cell
           FROM read_parquet('data/processed/aim1a_frame.parquet') f JOIN read_parquet('{SPLITS_V1}') s USING (hadm_id)
           WHERE s.partition = 'DEV' ORDER BY f.hadm_id""").fetchdf()
    rng = np.random.default_rng(SEED_PILOT)
    parts = []
    for cell, n in ALLOC.items():
        p = df[df.cell == cell]
        parts.append(df.loc[rng.choice(p.index.values, size=n, replace=False)])
    key = pd.concat(parts, ignore_index=True)
    key = key.iloc[rng.permutation(len(key))].reset_index(drop=True)
    key["review_id"] = [f"P{i + 1:03d}" for i in range(len(key))]
    assert len(key) == 30 and key.hadm_id.is_unique
    gold = con.execute(f"SELECT count(*) FROM read_parquet('{SPLITS_V1}') WHERE partition = 'GOLD_HOLDOUT' AND subject_id IN (SELECT subject_id FROM key)").fetchone()[0]
    assert gold == 0, "a pilot subject is in GOLD_HOLDOUT"
    os.makedirs(os.path.dirname(KEY), exist_ok=True)
    key[["review_id", "hadm_id", "subject_id", "cell"]].to_parquet(KEY, index=False)

    pop = con.execute(f"SELECT hadm_id, admittime, dischtime, age, gender FROM read_parquet('{LOCKED_POP}')").fetchdf()
    charts = key.merge(pop, on="hadm_id", how="left")
    charts["win_lo"] = charts.admittime - pd.Timedelta(days=P.WIN_BEFORE)
    charts["win_hi"] = charts.admittime + pd.Timedelta(days=P.WIN_AFTER)
    dc, rad, labs, omr, rx = P.load_inputs(charts, con, t0)
    os.makedirs(OUT, exist_ok=True)
    exc, written, ids_by_file, sizes = Counter(), [], {}, []
    for row in charts.itertuples():
        try:
            rid = row.review_id
            txt = P.build_packet(row, dc[dc.review_id == rid], rad[rad.review_id == rid], labs[labs.review_id == rid],
                                 omr[omr.review_id == rid], rx[rx.review_id == rid])
            path = os.path.join(OUT, f"{rid}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt)
            written.append(path); sizes.append(len(txt))
            ids_by_file[path] = [str(int(row.hadm_id)), str(int(row.subject_id))] + [str(n) for n in rad[rad.review_id == rid].note_id.tolist()]
        except Exception as e:                       # class name only; no message, no value
            exc[type(e).__name__] += 1
    checks = P.leak_checks(written, ids_by_file)
    # with 30 packets, a "files with a hit" count of 20-29 gives a count under 11 by subtraction; the largest
    # file size and the 95th percentile describe single packets. Neither is published.
    n_files = checks["n_files"]
    checks["files_with_any_hit"] = {k: ("withheld" if isinstance(v, int) and 0 < n_files - v < 11 else v)
                                    for k, v in checks["files_with_any_hit"].items()}
    for k in ("file_bytes_max", "file_bytes_p95"):
        checks.pop(k, None)

    # blank form: the instrument's columns (minutes_spent included), one row per blinded ID
    wb = Workbook(); wb.remove(wb.active)
    ws = wb.create_sheet("PILOT_README")
    for i, line in enumerate([LABEL, "Blinded IDs P001-P030. Record minutes_spent for every packet, start to finish.",
                              "Columns and options follow docs/adjudication/data_dictionary.md.",
                              "Drawn by scripts/run1110_pilot_packets.py (DEV admissions only)."], start=1):
        ws.cell(row=i, column=1, value=line)
    ws.column_dimensions["A"].width = 110
    ranges = T._lists_sheet(wb)
    T._form_sheet(wb, "pilot", key.review_id.tolist(), ranges)
    wb.move_sheet("lists", offset=len(wb.sheetnames))
    form = os.path.join(OUT, "pilot_form_blank.xlsx")
    wb.save(form)
    with open(os.path.join(OUT, "README.txt"), "w") as f:
        f.write(LABEL + "\n\nPackets P001-P030 and pilot_form_blank.xlsx. Untracked; credentialed data; do not copy off this machine.\n")

    cpw, wpm = 6.0, (200, 250)                       # the reading assumptions of results/reviewer_brief.json
    mean_chars = float(np.mean(sizes)) if sizes else 0.0
    res = {"script": "scripts/run1110_pilot_packets.py", "label": LABEL, "seed": SEED_PILOT, "partition": "DEV",
           "allocation_design": ALLOC, "packets_written": len(written), "exceptions_by_class": dict(exc),
           "form_columns": T.COLUMNS, "form_has_minutes_spent": "minutes_spent" in T.COLUMNS,
           "gold_holdout_subjects_drawn": int(gold),
           "packet_chars_mean": round(mean_chars), "packet_chars_median": int(np.median(sizes)) if sizes else 0,
           "predicted_reading_minutes_per_packet": [round(mean_chars / cpw / w + 5.0, 1) for w in (wpm[1], wpm[0])],
           "prediction_assumptions": {"chars_per_word": cpw, "words_per_minute": list(wpm), "fixed_overhead_min_per_chart": 5.0,
                                      "source": "docs/run_2026-09-19/results/reviewer_brief.json"},
           "leak_checks": checks, "folder": OUT, "key": KEY + " (apart from the packets)",
           "timings_s": {"total": round(time.time() - t0, 1)}}
    json.dump(res, open(RES, "w"), indent=1)
    print(f"pilot packets written: {len(written)} of {len(charts)}; exceptions by class: {dict(exc)}; form: {os.path.basename(form)}; {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
