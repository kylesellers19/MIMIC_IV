# Supplementary Table S1 — Data quality summary (Kahn 2016)

| Kahn category | Test | n affected | % of population | Proposed rule | Applied |
| --- | --- | --- | --- | --- | --- |
| Conformance · value | Lab value non-numeric (valuenum null) | ~5 | ≈0% (labevents) | Treat as missing (already null) | No |
| Conformance · value (units) | Multiple units per analyte | 0 | 0% | None needed | n/a |
| Conformance · relational | labevents hadm_id null (outpatient) | 73,768,897 | 46.6% (labevents) | Keep; link by subject+window for outpatient labs | No |
| Conformance · value | omr Blood Pressure non-atomic | 2,827,801 | 100% of BP rows | Parse NNN/NNN into sbp/dbp | Yes (this pass) |
| Plausibility · atemporal | Lab impossible values (glucose ≤0) | 3 | ≈0% | Null impossible; flag extremes | No |
| Plausibility · atemporal | omr impossible (incl. 907 diastolic zeros) | 1,151 | row-level | Null impossible; diastolic zeros excluded | Partial (dbp zeros: Yes) |
| Plausibility · temporal | admittime > dischtime (neg LOS) | 175 | 0.047% (adm) | Null/flag LOS | No |
| Plausibility · temporal | deathtime outside stay | 771 | 0.206% (adm) | Accept midnight artifact; flag | No |
| Plausibility · temporal | dischtime after dod | 32 | 0.0086% (adm) | Flag; dod unreliable for these | No |
| Plausibility · temporal | lab charttime outside admit window | 3,421,479 | 4.04% (linked labs) | Define window tolerance per feature | No |
| Plausibility · temporal | omr chartdate after dod | 91 | row-level | Null/flag | No |
| Completeness · differential | MNAR metabolic covariates (BMI/ALT/HbA1c/TG/HDL/dischg) | 6 covariates | structural | Missing-indicators; missingness-tolerant criterion; 1c sensitivity analysis | No |
| Conformance · value | Age cap at 91 (≥89 collapsed) | n/a | upper tail | Cap age at 91; footnote | Yes (this pass) |

- Rules per docs/cleaning_spec.md. 'Applied' refers to THIS descriptive pass only; the cleaning spec is otherwise not executed. Denominators noted inline.
- BP parse success this pass: 2,827,801/2,827,801 (100.0%); diastolic zeros excluded: 907.
