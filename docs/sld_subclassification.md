# SLD Subclassification and MASLD-Consistent Recovery — MIMIC-IV

> **MASLD is defined POSITIVELY** (hepatic steatosis + ≥1 cardiometabolic risk factor);
> unlike NAFLD it does **not** require excluding other liver disease. The primary 2×2
> stays at the steatosis level; CMRF and etiology enter only as pre-specified secondary
> analyses.

**Nomenclature source:** Rinella ME, Lazarus JV, Ratziu V, et al. A multisociety Delphi
consensus statement on new fatty liver disease nomenclature. *J Hepatol.* 2023
Dec;79(6):1542–1556. doi:10.1016/j.jhep.2023.06.003. PMID: 37364790.

**Data limitation (prescriptions-only):** medication treatment status is established from
`prescriptions` (drug name, GSN, NDC, dose, route, dates) — MIMIC-IV's medication-order
table and sufficient for "current treatment" as the consensus specifies. `pharmacy` (adds
dispensing-level detail relevant to adherence/dosing, not treatment status) was not
fetched; documented here as a completeness limitation.

## Approved drug-class lists — exclusions & rationale (Step 1b)

Matching is drug-name-based (GSN/NDC present for audit), restricted to the locked
population, ophthalmic route excluded. Corrections kept: ophthalmic timolol /
dorzolamide-timolol excluded on route; clopidogrel & ticlopidine excluded from
lipid-lowering (antiplatelets); aspartame & niacinamide excluded.

- **Beta-blockers — EXCLUDED from criterion 3.** The 13,080 admissions positive by
  beta-blocker alone have no HTN code and no BP ≥130/85 anywhere in the stay; a
  hypertensive inpatient would generate one or the other. Residual = heart failure,
  arrhythmia/rate-control, post-MI.
- **Insulin — EXCLUDED from criterion 2.** The 8,251 positive by insulin alone have no
  dysglycemia code, no HbA1c ≥5.7, no glucose ≥100; a diabetic on insulin would exceed
  glucose 100 at some point. prescriptions cannot separate home insulin from inpatient
  sliding-scale, so the class is excluded; explicit "insulin for hyperkalemia" strings
  excluded on indication regardless.
- **Metformin — INCLUDED** (102 positive by metformin alone; overwhelmingly diabetes/prediabetes).
- **Hydralazine, metolazone, alpha-blockers (doxazosin/terazosin/prazosin) — EXCLUDED
  from criterion 3** (IV hypertensive-urgency & HFrEF regimens; HF diuresis/ascites — and
  12.8% of the recovery zone carries cirrhosis codes, so metolazone would preferentially
  misclassify the group of most interest; alpha-blockers are BPH-dominant).

## Step 1a — Counting error diagnosed and corrected

**Cause:** the Step-1 class totals summed each drug string's DISTINCT-admission count across the class, so an admission on ≥2 drugs in a class (e.g. metoprolol AND lisinopril) was counted once per drug → the antihypertensive total (449,087) exceeded the population (373,992). The matching WAS already restricted to the locked population. **Fix:** count DISTINCT admissions per class from the per-admission flags.

| class | DISTINCT admissions | % of pop |
| --- | --: | --: |
| Antidiabetic (all, incl insulin) | 117,269 | 31.4% |
|   — oral antidiabetic (crit-2 qualifying, insulin excl) | 17,835 | 4.8% |
|   — metformin (incl in oral) | 12,355 | 3.3% |
|   — insulin (EXCLUDED from crit 2) | 115,035 | 30.8% |
| Antihypertensive (all) | 210,374 | 56.3% |
|   — qualifying antihypertensive (crit-3) | 145,676 | 39.0% |
|   — beta-blockers (EXCLUDED) | 149,140 | 39.9% |
|   — hydralazine/metolazone/alpha (EXCLUDED) | 47,074 | 12.6% |
| Lipid-lowering (crit 4/5) | 135,009 | 36.1% |

All class totals ≤ 373,992. ✔

### Ruling principle (recorded)

Criteria 2 and 3 are already satisfied by a code OR a lab/vital, so **medications operate only in the residual where neither exists**. Being restrictive there costs little and protects specificity. Beta-blockers, insulin, hydralazine, metolazone, and alpha-blockers are therefore excluded (see Step 6 for per-class rationale).

## Step 2 — Five CMRF criteria (Rinella 2023), per-source contribution

Each criterion: positive = code OR lab/vital-over-threshold OR qualifying med; unascertainable = no code, no med, no measurement.

| criterion | positive % | unasc % | by code | by lab | by vital | by med | **med-ONLY** |
| --- | --: | --: | --: | --: | --: | --: | --: |
| Overweight/obesity | 53.6 | 22.0 | 10.0 | 0.0 | 52.1 | 0.0 | 0 (0.00%) |
| Dysglycemia | 61.2 | 14.7 | 26.2 | 54.6 | 0.0 | 4.8 | 325 (0.09%) |
| Hypertension | 68.6 | 11.8 | 54.9 | 0.0 | 35.0 | 39.0 | 15,337 (4.10%) |
| Hypertriglyceridemia | 37.3 | 60.1 | 0.4 | 2.4 | 0.0 | 36.1 | 129,672 (34.67%) |
| Low HDL | 37.2 | 61.8 | 0.0 | 2.8 | 0.0 | 36.1 | 128,378 (34.33%) |

### Headline — did medications move the ≥1-CMRF proportion?

- ≥1 CMRF **without** medications (5-criteria, code|lab|vital): **88.4%**
- ≥1 CMRF **with** qualifying medications: **89.8%** (Δ +1.42 pts; 5,301 admissions added by meds alone)
- Unascertainable for ALL five: 2.7%

(For reference, the earlier 4-criteria without-meds figure was 89.5%.) The medication contribution is small: the CMRF requirement is **nearly non-binding** in this inpatient population — a reportable finding for the discussion.


## Step 3 — SLD subclassification of note-positive admissions

*MetALD caveat: MIMIC has no quantified alcohol intake, so the consensus thresholds (140–350 g/wk female, 210–420 g/wk male) cannot be applied. Alcohol status is proxied by ICD codes, which capture disorder-level use, not the moderate band the MetALD definition specifies. This is a proxy, not an implementation.*

Subclassification applies only to note-positive (documented-steatosis) admissions. The two note-NEGATIVE cells have no note-documented steatosis and are not SLD-subclassifiable at the note level.

| SLD class | code+/note+ | code−/note+ | all note+ |
| --- | --: | --: | --: |
| MASLD | 4,332 (86.2%) | 17,877 (78.4%) | 22,209 (79.8%) |
| MetALD | 592 (11.8%) | 3,716 (16.3%) | 4,308 (15.5%) |
| ALD | 37 (0.7%) | 349 (1.5%) | 386 (1.4%) |
| Cryptogenic | 61 (1.2%) | 687 (3.0%) | 748 (2.7%) |
| Unclassifiable | 5 (0.1%) | 170 (0.7%) | 175 (0.6%) |

### MetALD — reported prominently and separately

**4,308 note-positive admissions are MetALD-consistent** (15.5% of note-positive; code−/note+ 3,716, code+/note+ 592). **MetALD has no ICD code at all**, so this group cannot be captured by the code axis even in principle — it exists only in the note/steatosis space. *MetALD caveat: MIMIC has no quantified alcohol intake, so the consensus thresholds (140–350 g/wk female, 210–420 g/wk male) cannot be applied. Alcohol status is proxied by ICD codes, which capture disorder-level use, not the moderate band the MetALD definition specifies. This is a proxy, not an implementation.*

## Step 4 — Primary 2×2 (steatosis level) + secondary analyses

The primary 2×2 is **not** gated on CMRF (the code axis requires no CMRF; gating one axis only would compare non-comparable constructs). Recovery estimate = code−/note+ ÷ all note+.

| definition | note+ (all) | code−/note+ | recovery % |
| --- | --: | --: | --: |
| PRIMARY: steatosis (note+, as built) | 27,826 | 22,799 | 81.9% |
| (i) steatosis excluding alcohol-related codes | 23,068 | 18,673 | 80.9% |
| (ii) steatosis + ≥1 CMRF (MASLD-consistent) | 26,517 | 21,593 | 81.4% |
| (iii) steatosis excl. ALL competing etiologies [NAFLD-era] | 18,749 | 15,646 | 83.4% |

(iii) is labeled the **NAFLD-era comparison**: NAFLD was defined by exclusion of other liver disease, whereas **MASLD is defined POSITIVELY** (steatosis + ≥1 CMRF) and does NOT require ruling out competing etiologies. Under current nomenclature (Rinella 2023), definition (iii) is therefore NOT the primary phenotype.

## Step 5 — Recovery zone: historical vs current triggering mention

Recovery zone n=22,799. Two 'historical' measures (they support different claims):

- **(A) Frozen-rule ConText temporality flag** ('history of', 'h/o'…): historical-only 197 (0.9%). Strict — fires only on an explicit temporal cue.
- **(B) Section-based** — triggering hit only in a PAST MEDICAL/SURGICAL HISTORY section, with no current-section or imaging mention: **historical-only 1,924 (8.4%)**; **current 20,875 (91.6%)**.

Comparison below uses (B), the 'documented prior diagnosis (still uncoded) vs new finding (uncoded)' distinction.

| variable | current | historical-only | SMD |
| --- | --- | --- | --: |
| Age median [IQR] | 58.0 [48.0, 67.0] | 59.0 [50.0, 68.0] | -0.068 |
| LOS median [IQR] | 3.7 [1.8, 7.0] | 3.1 [1.8, 5.5] | +0.186 |
| Distinct diagnoses median [IQR] | 12.0 [8.0, 18.0] | 12.0 [8.0, 17.0] | -0.011 |
| Male % | 53.4% | 48.7% | +0.093 |
| ≥1 CMRF % | 94.4% | 98.0% | -0.191 |

- **race** (top): WHITE cur 65%/hist 64%; BLACK/AFRICAN AMERICAN cur 11%/hist 10%; OTHER cur 3%/hist 4%; UNKNOWN cur 2%/hist 1%
- **insurance** (top): Medicare cur 38%/hist 41%; Private cur 36%/hist 39%; Medicaid cur 23%/hist 19%; Other cur 3%/hist 2%

