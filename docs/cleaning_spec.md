# Cleaning Specification — MIMIC-IV hosp (MASLD phenotyping)

**Status: SPECIFICATION FOR APPROVAL. No changes have been applied to any data.**
Each item states the issue, the rule I would adopt if you approve it, the number
of rows affected, and the alternative. Nothing here is executed; `data/raw/` is
untouched and no `.csv.gz` was decompressed.

## Framework

Tests are organized and labeled using the harmonized data-quality framework of
**Kahn MG, Callahan TJ, Barnard J, et al. "A Harmonized Data Quality Assessment
Terminology and Framework for the Secondary Use of Electronic Health Record
Data." EGEMS (Wash DC). 2016;4(1):1244. doi:10.13063/2327-9214.1244**, whose
three top-level categories are **Conformance** (value, relational, computational),
**Completeness**, and **Plausibility** (uniqueness, atemporal, temporal).

## Locked decisions encoded (not revisited)

- **Grain:** admission (`hadm_id`).
- **Zero-diagnosis admissions:** EXCLUDED → analysis population **545,497**
  admissions (**9,143** code-positive / **536,354** code-negative).
- **Race:** value recorded at that admission; the non-informative categories
  (UNKNOWN, OTHER, UNABLE TO OBTAIN, PATIENT DECLINED, MULTIPLE RACE/ETHNICITY)
  kept as an **explicit** category.
- **Diagnosis count:** distinct `(seq_num, icd_version)`.
- **Age:** `anchor_age + year(admittime) − anchor_year` (anchor_age capped at 91
  for ages ≥89; cap propagates).
- **Lab analytes (blood/serum):** ALT 50861, AST 50878, Platelets 51265,
  Triglycerides 51000, HDL 50904, HbA1c 50852, Glucose 50931, Albumin 50862,
  Bilirubin total 50885, Alk phos 50863.
- **GGT:** decision pending (see item G1).

Reproducers: `scripts/conformance.py`, `scripts/plausibility_atemporal.py`,
`scripts/plausibility_temporal.py`, `scripts/completeness_differential.py`,
`sql/analysis_population.sql`.

---

## Summary of items

| # | Kahn category | Issue | Rows affected |
|---|---|---|---|
| C1 | Conformance · value | Non-numeric lab `value` w/ null `valuenum` | ~5 total |
| C2 | Conformance · value (units) | Multiple units per analyte | 0 (no action) |
| C3 | Conformance · relational | labevents `hadm_id` null (outpatient) | 73,768,897 |
| C4 | Conformance · value | omr `Blood Pressure` not atomic; stray Height | 2,827,801 + 1 |
| P1 | Plausibility · atemporal | Lab impossible / extreme values | see table |
| P2 | Plausibility · atemporal | omr impossible / extreme values | see table |
| T1 | Plausibility · temporal | `admittime > dischtime` (neg LOS) | 175 |
| T2 | Plausibility · temporal | `deathtime` outside stay | 771 |
| T3 | Plausibility · temporal | `dischtime` after `dod` | 32 |
| T4 | Plausibility · temporal | lab `charttime` outside admit window; storetime<charttime | 3,421,479 + 1,372 |
| T5 | Plausibility · temporal | omr `chartdate` after `dod` | 91 |
| K1 | Completeness · differential | MNAR metabolic covariates linked to coding + demographics | structural |
| G1 | Conformance · value | GGT itemid approval | n/a |
| S5 | — | Note-coverage window (Step 5) | SKIPPED — no note data |

---

## Conformance

### C1 — Non-numeric lab values (value conformance)
**Finding.** Among the 10 analytes, `value` is non-numeric with null `valuenum`
in **≤1 row each**: ALT `-` (1), AST `-` (1), Platelets `___` (1),
Triglycerides `E` (1), Alk phos `-` (1); all others 0. Units are otherwise a
single valid unit per analyte.
**Rule (proposed).** Treat these specific rows as missing numeric results
(`valuenum` already null); exclude from numeric summaries. **~5 rows.**
**Alternative.** Leave untouched — they are already null in `valuenum` and never
enter numeric features, so impact is nil either way.

### C2 — Units (value conformance) — NO ACTION
**Finding.** Exactly one unit per analyte (ALT/AST/ALP IU/L, Platelets K/uL,
Trig/HDL/Glucose/Bili mg/dL, HbA1c %, Albumin g/dL). No unit mixing.
**Rule.** None required. **0 rows.** **Alternative.** n/a.

### C3 — labevents `hadm_id` null (relational conformance)
**Finding.** **0 orphan** `hadm_id` (every linked lab points to a real
admission). **73,768,897 rows (46.6%) have null `hadm_id`** = outpatient labs.
**Rule (proposed).** Do **not** drop null-`hadm_id` rows. For admission-linked
lab features, either (a) restrict to non-null `hadm_id`, or (b) link by
`subject_id` + time window (see T4). State which per feature.
**Alternative.** Drop null-`hadm_id` labs entirely — simpler, but discards ~47%
of all lab data including pre-admission/outpatient metabolic labs central to the
metabolic criterion.

### C4 — omr `Blood Pressure` not atomic (value conformance)
**Finding.** BMI/Weight/Height parse as numeric (100%; one stray `.` in Height).
`Blood Pressure` is **0% numeric** but **100%** in `systolic/diastolic` string
form (`120/80`), 2,827,801 rows.
**Rule (proposed).** Parse `Blood Pressure` into integer `sbp`/`dbp` via
`^\d+/\d+$`; treat the 1 non-parsing Height (`.`) as missing. **2,827,801 + 1.**
**Alternative.** Keep BP as raw string (blocks numeric use) — not viable if BP
feeds the metabolic criterion.

---

## Plausibility — atemporal

Bounds: reference intervals from **Tietz Clinical Guide to Laboratory Tests**;
marker cutoffs **ADA** (glucose, HbA1c) and **NCEP ATP III** (lipids); **WHO**
(BMI); plausibility ceilings are pragmatic physiologic maxima. "Impossible" =
negative or zero-where-impossible; "extreme" = positive but outside the plausible
range.

### P1 — Lab values
| Analyte | plausible | impossible | extreme | notable max |
|---|---|--:|--:|--:|
| ALT | 0–10000 | 0 | 160 | 61,854 |
| AST | 0–10000 | 0 | 701 | 42,606 |
| Platelets | 0–2000 | 0 | 74 | 2,989 |
| Triglycerides | 0–10000 | 0 | 5 | 12,496 |
| HDL | 0–200 | 0 | 32 | 335 |
| HbA1c | 2–20 | 0 | 3 | 23.1 |
| Glucose | 10–2000 | 3 | 260 | 23,200 |
| Albumin | 0.5–7 | 0 | 25 | 36 |
| Bilirubin total | 0–75 | 0 | 13 | 87.2 |
| Alk phos | 0–5000 | 0 | 4 | 5,965 |

**Rule (proposed).** Set **impossible** values to null (3 glucose ≤0). For
**extreme** values, add a per-analyte out-of-range flag but do **not** delete —
most are genuine critical-illness values (e.g., ALT/AST >10,000 in ischemic
hepatitis); a few are clear errors (Glucose 23,200; Albumin 36 g/dL).
**Alternative.** Winsorize extremes to the plausible bound (changes values), or
leave all raw (impossible values then pollute means/SDs).

### P2 — omr values
| Measure | plausible | impossible | extreme | notable max |
|---|---|--:|--:|--:|
| BMI | 10–100 | 9 | 1,006 | 321,697 |
| Weight (lb) | 50–1000 | 197 | 557 | 2.10e8 |
| Height (in) | 24–90 | 33 | 573 | 73,252 |
| Systolic BP | 50–300 | 5 | 12 | 250 |
| Diastolic BP | 20–200 | 907 | 573 | 200 |

**Rule (proposed).** Null the impossible values (incl. the **907 diastolic
zeros** — the `SBP/0` palpated/missing-diastolic pattern) and flag extremes
without deletion. **Alternative.** Winsorize to plausible bounds, or derive BMI
from same-day height/weight and cross-check (heavier, and does not resolve the
data-entry outliers).

---

## Plausibility — temporal

### T1 — `admittime > dischtime` (negative LOS)
**Finding.** **175** admissions, **175 distinct subjects** (no subject
clustering); concentrated in early year-groups (2008–2013 = 113) and
emergency/observation types; magnitude ~20–22 h, consistent with a
**midnight-placeholder discharge timestamp**.
**Rule (proposed).** Set `los_days` to null (or flag) for these 175; retain the
admission. **Alternative.** Drop the 175 admissions (removes them from the code±
denominator), or attempt timestamp repair (not supported by any second source).

### T2 — `deathtime` outside `[admittime, dischtime]`
**Finding.** **771** of 11,790 admissions-with-deathtime; sample shows death a
few hours after a midnight `dischtime` (same placeholder as T1).
**Rule (proposed).** Accept as the known midnight artifact; flag but do not
alter. **Alternative.** Clamp `dischtime` to `deathtime` when death is same-day
(changes LOS for 771).

### T3 — `dischtime` after `dod`
**Finding.** **32** admissions discharge *after* the recorded date of death
(by years in some cases) — a cross-source `dod` inconsistency.
**Rule (proposed).** Flag these 32; treat their `dod` as unreliable for
mortality-timing features. **Alternative.** Exclude the 32 admissions, or null
`dod` for the affected subjects.

### T4 — lab `charttime` outside admission window; `storetime < charttime`
**Finding.** Of 84,605,867 admission-linked labs, **3,421,479 (4.04%)** have
`charttime` outside `[admittime, dischtime]` (pre-admission ED draws /
discharge-day results). **1,372** rows have `storetime < charttime` (impossible
order).
**Rule (proposed).** For any time-windowed lab feature, define an explicit
tolerance (e.g., include labs from ED arrival, and up to +24–48 h post-discharge)
and state it; flag the 1,372 storetime<charttime rows.
**Alternative.** Strict in-window only (drops 3.42M labs, biasing toward
inpatient-only), or ignore the window (mixes unrelated encounters).

### T5 — omr `chartdate` after `dod`
**Finding.** **91** omr subject-dates after death (impossible). 288,702 omr
dates belong to subjects with no admission; 1,096,191 fall outside admission
spans — both expected for outpatient data, **not** errors.
**Rule (proposed).** Null/flag the 91 post-death omr dates; keep outpatient omr.
**Alternative.** Drop all outpatient omr (loses the metabolic history that
motivates using omr at all).

---

## Completeness — differential (the Aim-1c threat)

### K1 — MNAR metabolic covariates linked to both coding and demographics
**Finding.** Missingness both predicts coding (|SMD|≥0.1) **and** varies ≥10 pts
across race/insurance for six covariates:

| Covariate | miss% code+ | miss% code− | SMD | race range | insurance range |
|---|--:|--:|--:|--:|--:|
| discharge_location | 17.8 | 27.6 | −0.236 | 29.4 | 14.1 |
| BMI (any) | 14.5 | 26.3 | −0.296 | 71.4 | 7.5 |
| ALT (any) | 2.3 | 14.8 | −0.458 | 18.9 | 12.9 |
| HbA1c (any) | 25.3 | 48.9 | −0.504 | 37.3 | 16.8 |
| Triglycerides | 28.1 | 46.6 | −0.388 | 48.5 | 13.6 |
| HDL | 32.3 | 49.8 | −0.362 | 53.1 | 13.9 |

The metabolic features that define MASLD are systematically **less missing in
coded-positive admissions** and their missingness **tracks race and insurance**.
Highest metabolic-lab missingness falls in the UNKNOWN / UNABLE-TO-OBTAIN race
strata and several Asian/Hispanic groups; Private/Other insurance are missing
more than Medicare/Medicaid. `marital_status` varies by race (range 52.3) but
does **not** predict coding (SMD −0.06) → MAR-like, lower threat.

**This is not fixable by cleaning — no row edit removes the bias.**
**Rule (proposed).** (a) Never complete-case on these covariates; (b) carry an
explicit missing-indicator for each into any 1b/1c model; (c) define the MASLD
metabolic criterion to be evaluable under missing labs (e.g., "any available
evidence" rather than "all labs present"); (d) run a 1c sensitivity analysis
under differing missingness assumptions (MAR vs MNAR).
**Alternative.** Complete-case or impute-then-ignore — both bias Aim 1c because
the missingness is differential on exactly the axes 1c measures.

### G1 — GGT approval (conformance · value)
**Finding.** Two GGT itemids: **50927** `Gamma Glutamyltransferase` (Blood/
Chemistry, 20,860 rows, single unit IU/L, 0 non-numeric) and **53093** (misspelt
duplicate, 69 rows). Not in the approved analyte set.
**Rule (proposed, pending your approval).** If GGT is wanted, use **50927 only**
(ignore 53093); coverage among coded-positive subjects to be reported before use.
**Alternative.** Omit GGT.

---

## Step 5 — Note-coverage window: SKIPPED
`data/raw/note/` (and `data/raw/ed/`) are empty — no note files present. The
analysable note window cannot be determined. Re-run Step 5 once MIMIC-IV-Note is
downloaded.

---

*End of specification. Nothing applied. Awaiting approval of the rules above,
then a separate execution step would materialize a cleaned derivative to
`data/processed/` (never modifying `data/raw/`).*
