# Table 2 — Laboratory & anthropometric characteristics

| Panel | Analyte | code-positive | code-negative | Overall | SMD |
| --- | --- | --- | --- | --- | --- |
| A: availability | Alk phosphatase | 62.1% (3,562) | 38.8% (142,954) | 39.2% (146,516) | +0.478 |
| A: availability | Total bilirubin | 62.0% (3,561) | 38.8% (142,948) | 39.2% (146,509) | +0.477 |
| A: availability | AST/ALT ratio | 62.5% (3,587) | 39.6% (145,663) | 39.9% (149,250) | +0.471 |
| A: availability | ALT | 62.5% (3,589) | 39.7% (146,054) | 40.0% (149,643) | +0.470 |
| A: availability | AST | 62.6% (3,593) | 39.8% (146,484) | 40.1% (150,077) | +0.469 |
| A: availability | Albumin | 45.7% (2,623) | 29.1% (107,256) | 29.4% (109,879) | +0.348 |
| A: availability | Diastolic BP | 87.4% (5,016) | 74.0% (272,465) | 74.2% (277,481) | +0.344 |
| A: availability | Systolic BP | 87.4% (5,016) | 74.0% (272,468) | 74.2% (277,484) | +0.344 |
| A: availability | BMI | 88.9% (5,103) | 76.5% (281,775) | 76.7% (286,878) | +0.332 |
| A: availability | Glucose | 86.9% (4,987) | 82.2% (302,758) | 82.3% (307,745) | +0.129 |
| A: availability | GGT | 2.5% (142) | 1.0% (3,562) | 1.0% (3,704) | +0.116 |
| A: availability | Platelets | 87.1% (5,002) | 83.4% (307,110) | 83.5% (312,112) | +0.106 |
| A: availability | Triglycerides | 9.4% (539) | 7.8% (28,607) | 7.8% (29,146) | +0.058 |
| A: availability | HbA1c | 9.3% (535) | 8.0% (29,489) | 8.0% (30,024) | +0.047 |
| A: availability | HDL | 5.0% (289) | 5.7% (20,825) | 5.6% (21,114) | -0.028 |
| B: value (among available) | ALT | 34.0 [20.0, 64.0] | 23.0 [15.0, 42.0] | 23.0 [15.0, 43.0] |  |
| B: value (among available) | AST | 42.0 [27.0, 75.0] | 27.0 [19.0, 50.0] | 27.0 [19.0, 50.0] |  |
| B: value (among available) | AST/ALT ratio | 1.3 [0.9, 1.8] | 1.2 [0.9, 1.7] | 1.2 [0.9, 1.7] |  |
| B: value (among available) | Platelets | 182.0 [115.0, 251.8] | 218.0 [166.0, 280.0] | 217.0 [165.0, 280.0] |  |
| B: value (among available) | Albumin | 3.4 [3.0, 3.9] | 3.5 [3.0, 3.9] | 3.5 [3.0, 3.9] |  |
| B: value (among available) | Total bilirubin | 0.8 [0.5, 1.6] | 0.5 [0.3, 0.9] | 0.5 [0.3, 0.9] |  |
| B: value (among available) | Alk phosphatase | 98.0 [71.0, 145.0] | 84.0 [64.0, 123.0] | 85.0 [64.0, 124.0] |  |
| B: value (among available) | GGT | 151.5 [52.2, 399.5] | 118.0 [37.0, 300.0] | 119.0 [37.0, 301.2] |  |
| B: value (among available) | Glucose | 120.0 [98.0, 159.0] | 110.0 [94.0, 139.0] | 110.0 [94.0, 140.0] |  |
| B: value (among available) | HbA1c | 6.3 [5.6, 8.1] | 5.9 [5.5, 7.1] | 6.0 [5.5, 7.1] |  |
| B: value (among available) | Triglycerides | 141.0 [86.0, 236.5] | 112.0 [79.0, 164.0] | 112.0 [79.0, 164.0] |  |
| B: value (among available) | HDL | 38.0 [27.0, 49.0] | 45.0 [35.0, 56.0] | 44.0 [35.0, 56.0] |  |
| B: value (among available) | BMI | 31.9 [27.1, 38.0] | 27.5 [23.9, 32.2] | 27.6 [23.9, 32.3] |  |
| B: value (among available) | Systolic BP | 128.0 [120.0, 136.0] | 128.0 [119.0, 137.0] | 128.0 [119.0, 137.0] |  |
| B: value (among available) | Diastolic BP | 74.0 [68.0, 80.0] | 73.0 [67.0, 80.0] | 73.0 [67.0, 80.0] |  |

- Panel A (availability) is a RESULT: differential availability by coding status. Sorted by |SMD| descending. Availability indicator SMD is a proportion SMD.
- Labs are linked per-admission by hadm_id (a result recorded during that admission). omr (BMI, BP) has no hadm_id and is summarized at SUBJECT level (median across the subject's readings), attached to each admission — patient-level context, not per-encounter.
- Panel B is CONDITIONAL on availability, and availability differs between groups (Panel A), so these medians are NOT directly comparable across groups.
- Blood Pressure parsed from the non-atomic 'NNN/NNN' string; 907 diastolic-zero readings excluded (DQ item P2). BP parse diagnostics printed to terminal.
- Cells with 0<n<11 suppressed as '<11*' (our own threshold).
