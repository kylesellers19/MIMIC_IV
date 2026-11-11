#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 — later outcomes after an uncoded mention (amendment m, S20). Exploratory.

Grain: subject. Index: the subject's earliest note-positive admission (definition b).
Groups: U, index code-negative with no earlier code-positive admission; C, index code-positive.
Excluded: subjects with a cirrhosis or HCC flag (cmrf.parquet) at or before index, and subjects who died
during the index admission.
Per group: subjects; subjects with at least one later admission; among those, the share with a later
cirrhosis flag and with a later HCC flag, and median [IQR] days from index discharge to the first later
admission carrying the flag. U only: the share later coded, days from index discharge to the first coded
admission, and the number of admissions after the index and before the first coded one.
Intervals: Wilson 95%. No survival model. Only returns to this hospital are observed: every figure is a floor.
Writes docs/run_2026-11-10/results/later_outcomes.json. Counts and shares only.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from scripts.run1110_common import RES, FLOOR, load_frame, mask, med_iqr, share, wilson


def main():
    df = load_frame()
    df["admittime"], df["dischtime"] = pd.to_datetime(df.admittime), pd.to_datetime(df.dischtime)
    df = df.sort_values(["subject_id", "admittime", "hadm_id"]).reset_index(drop=True)
    pos = df[df.note_b.astype(bool)]
    idx = pos.groupby("subject_id", sort=False).head(1)[["subject_id", "hadm_id", "admittime", "dischtime", "code_positive", "hospital_expire_flag"]]
    idx.columns = ["subject_id", "index_hadm", "index_admit", "index_disch", "index_coded", "index_died"]
    d = df.merge(idx, on="subject_id", how="inner")
    before = d[d.admittime < d.index_admit]
    at_or_before = d[d.admittime <= d.index_admit]
    later = d[d.admittime > d.index_admit]
    prior_code = set(before[before.code_positive.astype(bool)].subject_id)
    prior_cirr_hcc = set(at_or_before[at_or_before.cirrhosis | at_or_before.hcc].subject_id)
    s = idx.copy()
    s["group"] = np.where(s.index_coded.astype(bool), "C", np.where(s.subject_id.isin(prior_code), "neither", "U"))
    s["excl_cirr_hcc"] = s.subject_id.isin(prior_cirr_hcc)
    s["excl_died"] = s.index_died.astype(int) == 1
    flow = {"subjects_with_a_note_positive_admission": int(len(s)),
            "index_uncoded_but_coded_earlier_in_neither_group": mask(int((s.group == "neither").sum())),
            "excluded_cirrhosis_or_hcc_at_or_before_index": mask(int((s.excl_cirr_hcc & (s.group != "neither")).sum())),
            "excluded_died_during_index_admission_only": mask(int((s.excl_died & ~s.excl_cirr_hcc & (s.group != "neither")).sum()))}
    s = s[(s.group != "neither") & ~s.excl_cirr_hcc & ~s.excl_died]
    later = later[later.subject_id.isin(set(s.subject_id))].copy()
    later["days"] = (later.admittime - later.index_disch).dt.total_seconds() / 86400.0
    later["order"] = later.groupby("subject_id").cumcount()            # 0 = first admission after the index

    def first_event(flag):
        ev = later[later[flag].astype(bool)].groupby("subject_id", sort=False).head(1)
        return ev.set_index("subject_id")[["days", "order"]]

    has_later = set(later.subject_id)
    out = {"script": "scripts/run1110_later_outcomes.py", "amendment": "m (S20)", "exploratory": True, "grain": "subject",
           "intervals": "Wilson 95%", "flow": flow, "groups": {},
           "definitions": {"U": "index admission code-negative, no earlier code-positive admission", "C": "index admission code-positive",
                           "index": "earliest note-positive admission (definition b)", "later": "admitted after the index admission began",
                           "days": "from index discharge to admission of the first later admission with the event",
                           "admissions_before_first_coded": "admissions after the index and before the first coded admission (0 = the next admission was coded)"},
           "limitation": "only returns to this hospital are observed, so every figure is a floor"}
    for g in ("U", "C"):
        sg = s[s.group == g]
        n = int(len(sg))
        ret = sg[sg.subject_id.isin(has_later)]
        nr = int(len(ret))
        r = {"subjects": mask(n), "with_a_later_admission": share(nr, n, wilson(nr, n) if n else None)}
        events = [("later_cirrhosis_flag", "cirrhosis"), ("later_hcc_flag", "hcc")] + ([("later_coded", "code_positive")] if g == "U" else [])
        for name, flag in events:
            ev = first_event(flag)
            ev = ev[ev.index.isin(set(ret.subject_id))]
            x = int(len(ev))
            r[name] = share(x, nr, wilson(x, nr) if nr else None)
            if x >= FLOOR:
                r[name]["days_from_index_discharge"] = med_iqr(ev.days.to_numpy())
                if name == "later_coded":
                    r[name]["admissions_before_first_coded"] = med_iqr(ev.order.to_numpy())
        out["groups"][g] = r
    json.dump(out, open(f"{RES}/later_outcomes.json", "w"), indent=1)
    print(json.dumps(out["flow"]), "\n", json.dumps(out["groups"], indent=1))


if __name__ == "__main__":
    main()
