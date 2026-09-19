# Charlson index validation and the liver-excluded index (Phase 4.2, run_2026-09-19)

Produced by `scripts/run0919_charlson_validation.py`; numbers from `docs/run_2026-09-19/results/charlson_validation.json`.

## Why this check exists

The project's Charlson Comorbidity Index (`scripts/comorbid_cluster.py`) is a hand-written implementation of the Quan 2005 ICD-9-CM/ICD-10 crosswalk with Charlson 1987 weights. Before it feeds a model it was flagged for checking against an independent implementation. A second, separate concern: the Quan *mild liver disease* category contains K76.0 and the whole 571.x block — the phenotype's own codes — so the full index would leak the code axis into a model whose label is the note axis.

## 1. Agreement with comorbidipy (full locked population)

- Implementation compared: `comorbidipy` charlson weighting, Quan mapping, hierarchy on (`assign0=True`), ICD-9 and ICD-10 rows scored under their own version. Available weightings in the package: quan, charlson, shmi, shmi_modified, van_walraven, swiss.
- Admissions compared: 373,992.
- **Admissions with identical scores: 100.0%.** Difference distribution (project − comorbidipy): {'0': 373992}.
- Mean score: project 2.1231 vs comorbidipy 2.1231.

Per-category agreement (flag-level, after hierarchy):

| project category | comorbidipy column | % agree | n project | n comorbidipy |
| --- | --- | --: | --: | --: |
| mi | None | — | — | — |
| chf | chf | 100.0 | 62515 | 62515 |
| pvd | pvd | 100.0 | 28389 | 28389 |
| cevd | cevd | 100.0 | 27885 | 27885 |
| dementia | dementia | 100.0 | 11200 | 11200 |
| copd | copd | 100.0 | 74531 | 74531 |
| rheum | rheumd | 100.0 | 12065 | 12065 |
| pud | pud | 100.0 | 5333 | 5333 |
| mild_liver | mld | 100.0 | 22458 | 22458 |
| dm | diab | 100.0 | 64707 | 64707 |
| dm_comp | diabwc | 100.0 | 33202 | 33202 |
| hemi | hp | 100.0 | 7050 | 7050 |
| renal | rend | 100.0 | 63543 | 63543 |
| malig | canc | 100.0 | 35525 | 35525 |
| severe_liver | msld | 100.0 | 10206 | 10206 |
| mets | metacanc | 100.0 | 20772 | 20772 |
| hiv | aids | 100.0 | 2968 | 2968 |

## 2. Does the recovery-zone-versus-concordant SMD move?

| index | SMD, code−/note+ vs code+/note+ |
| --- | --: |
| project full index (reported earlier as −0.356) | -0.3563 |
| comorbidipy full index | -0.3563 |
| project index with both liver categories removed | +0.0037 |

## 3. The leak, verified against the project's own crosswalk

Does the mild-liver regex fire on each phenotype code?

| code | in mild_liver? |
| --- | --- |
| 10:K760 | yes |
| 10:K7581 | no |
| 9:5718 | yes |
| 9:5719 | yes |

K76.0, 571.8 and 571.9 all fall inside the Quan mild-liver category (K75.81 does not, because K75.8 is not in Quan's list). So every code-positive admission gets at least one Charlson point from the phenotype code itself. The consequence is visible in §2: the entire −0.356 comorbidity gap between the recovery zone and the concordant cell disappears (to about zero) once the liver categories are removed — the 'higher comorbidity burden' of coded patients was, to the resolution of this index, the code.

## 4. charlson_noliver

`charlson_noliver` = the same index with `mild_liver` and `severe_liver` removed. Mean 2.1231 → 1.9812; 8.734% of admissions change score. Stored per admission (untracked) at `data/processed/run_2026-09-19_charlson.parquet` for the modeling phases. The full index is never a feature (Phase 7 exclusion list).

## 5. Structural self-check

Weights match Charlson 1987 (1/1/1/1/1/1/1/1/1/1/2/2/2/2/3/6/6): True. Each category's regex fires on a synthetic code built from its first prefix in both ICD versions: all pass. Hierarchy rules (complicated > uncomplicated diabetes; severe > mild liver; metastatic > primary malignancy) are applied in the project script and by comorbidipy's `assign0`, and the two agree as shown above.

