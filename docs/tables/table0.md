# Table 0 — Cohort derivation / flow counts

| Step | Admissions (n) | Distinct subjects (n) |
| --- | --- | --- |
| All admissions (MIMIC-IV v3.1 hosp) | 546,028 | 223,452 |
| − Admissions with zero diagnosis rows (excluded) | −531 | (490 affected) |
| = Analysis population | 545,497 | 223,291 |
|   · MASLD code-positive | 9,143 | 5,580 |
|   · MASLD code-negative | 536,354 | 221,396 |
| − Note exclusion (a): release-lineage (subject absent from Note 2.2) | −100,029 | (62,172 subj) |
| − Note exclusion (b): encounter-level (subject in notes, this admission has none) | −71,476 | — |
| = LOCKED analysis population (≥1 linked note) | 373,992 | 161,119 |
|   · MASLD code-positive | 5,740 | — |
|   · MASLD code-negative | 368,252 | — |

- Grain = admission (hadm_id). Zero-diagnosis admissions excluded per locked decision.
- Distinct-subject counts overlap across code+/code− (a subject may have both coded and uncoded admissions), so 5,580 + 221,396 > 223,291.
- **Note-coverage restriction = ≥1 linked note (discharge OR radiology), linked by hadm_id.** Removes 171,505 admissions (31.4%). Code-positive drops from 9,143 to 5,740 (−37.2%).
- **There is NO admission-year window.** Coverage by derived admission year (`year(admittime)`) is flat at ~67–70% across 2110–2207 and only tapers in the sparse tail (~1,100 admissions). The earlier "2008–2019 window" was an `anchor_year_group` (per-patient) artifact; at admission level the missingness is not temporal.
- Exclusion decomposes into **(a) release-lineage** — subject absent from Note 2.2 entirely (100,029 adm / 62,172 subj; includes all 42,412 anchor-2020–2022 admissions plus ~57.6k from earlier anchor groups) — and **(b) encounter-level** — subject has notes on other admissions but not this one (71,476 adm; concentrated in short observation stays, LOS<1d 41% vs 17%). Both are differential by coding status (see docs/analysis_population.md).
- Sensitivity (discharge-only): 331,604 admissions / 145,817 subjects / 5,552 code-positive.
- Subject-level "—" cells omitted where code+/code− subject sets overlap.
