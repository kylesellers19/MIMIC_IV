#!/usr/bin/env python3
"""run_2026-11-10 Phase 5 — documentation funnel where the liver was imaged (amendment o, S22). Exploratory.

Population: imaging-observed admissions (S3: at least one liver-inclusive study, inpatient-linked or in the
outpatient window of -365/+30 days).
Stages: (1) imaging-observed; (2) rule-positive in at least one radiology report, inpatient-linked or in the
outpatient window; (3) of those, the discharge summary is also rule-positive; (4) the coded share among
stage-3 yes and among stage-3 no. Stage 2 is also split by inpatient against outpatient-only source.
Subject-cluster bootstrap, 500 replicates, seed 20260919, 95% percentile intervals.
Writes docs/run_2026-11-10/results/imaging_funnel.json. Counts and shares only.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.getcwd())
from scripts.run1110_common import RES, Boot, load_frame, share


def main():
    df = load_frame(with_sources=True)
    boot = Boot(df.subject_id)
    img = df.imaging_observed.to_numpy()
    rad = img & (df.src_rad_inp | df.src_rad_out).to_numpy()
    inp = rad & df.src_rad_inp.to_numpy()
    out_only = rad & ~df.src_rad_inp.to_numpy()
    dc = df.src_dc.to_numpy()
    code = df.code_positive.astype(bool).to_numpy()
    s3y, s3n = rad & dc, rad & ~dc

    def sh(num, den):
        return share(int(num.sum()), int(den.sum()), boot.ratio_ci(num, den))

    rule_any = (df.src_dc | df.src_rad_inp | df.src_rad_out).to_numpy()
    out = {"script": "scripts/run1110_imaging_funnel.py", "amendment": "o (S22)", "exploratory": True,
           "bootstrap": {"replicates": int(boot.W.shape[0]), "seed": 20260919, "cluster": "subject", "interval": "95% percentile"},
           "check_sources_reproduce_definition_b": bool((rule_any == df.note_b.astype(bool).to_numpy()).all()),
           "population_admissions": int(len(df)),
           "stage1_imaging_observed": sh(img, np.ones(len(df), dtype=bool)),
           "stage2_radiology_report_rule_positive": sh(rad, img),
           "stage2_split": {"inpatient_linked_report": sh(inp, rad), "outpatient_window_report_only": sh(out_only, rad)},
           "stage3_discharge_summary_also_rule_positive": sh(s3y, rad),
           "stage3_by_stage2_source": {"inpatient_linked_report": sh(s3y & inp, inp), "outpatient_window_report_only": sh(s3y & out_only, out_only)},
           "stage4_coded_share": {"discharge_summary_rule_positive": sh(s3y & code, s3y), "discharge_summary_not_rule_positive": sh(s3n & code, s3n)},
           "stage4_coded_share_by_source": {
               "inpatient_linked_report": {"discharge_summary_rule_positive": sh(s3y & inp & code, s3y & inp),
                                           "discharge_summary_not_rule_positive": sh(s3n & inp & code, s3n & inp)},
               "outpatient_window_report_only": {"discharge_summary_rule_positive": sh(s3y & out_only & code, s3y & out_only),
                                                 "discharge_summary_not_rule_positive": sh(s3n & out_only & code, s3n & out_only)}}}
    json.dump(out, open(f"{RES}/imaging_funnel.json", "w"), indent=1)
    print(json.dumps(out, indent=0)[:3000])


if __name__ == "__main__":
    main()
