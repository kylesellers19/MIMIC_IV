# Note-Based Hepatic-Steatosis Phenotype — Frozen Specification

**VERSION 1.1.0 · FROZEN 2026-08-17**  (supersedes v1.0.0; see §8 CHANGELOG)

> **This rule is FROZEN prior to 2×2 construction and chart adjudication.**
> The v1.1.0 revision was made **on the basis of the rule's own behavior**
> (docs/fatty_trigger_diagnostic.md) — **no adjudicated, gold-standard, or
> reference-standard data was involved at any point.** Development on the full
> corpus is expected; iteration against the gold standard is not permitted.
> Tuning a note-positive rule against adjudicated charts and reporting
> performance on those charts would be circular and would invalidate Aim 1a.

Implementation: [`scripts/note_phenotype.py`](../scripts/note_phenotype.py)
(`classify_note()`; the module version/date match this document). Text-handling:
aggregate outputs only; no raw note text is printed or written.

## 1. Purpose

Assign each admission a **note-positive** status for documented hepatic steatosis
from linked discharge and radiology notes. Construct: *"was steatosis documented
and available to the clinician at this admission."* Computable phenotype, not an
adjudicated label.

## 2. Lexicon (three tiers) with scope modes

Each trigger carries a **scope mode**: `none` (inherently hepatic — no anatomical
scoping), `standard` (pass if liver/hepatic within 10 tokens **or** the sentence
has no competing organ), or `strict` (pass **only** with affirmative liver/hepatic
within 10 tokens — the "no competing organ" fallback does **not** apply).

### Tier A — definite steatosis (PRIMARY)
| trigger | scope |
|---|---|
| hepatic steatosis; fatty liver | none |
| non-/nonalcoholic fatty liver (disease); non-/nonalcoholic steatohepatitis; metabolic dysfunction-associated (hyphenation variants) | none |
| NAFLD, NASH, MASLD, MASH, NAFL | none |
| **fatty replacement, fatty deposition, fatty degeneration, fatty metamorphosis, fatty infiltrate/-s/-d** (promoted in v1.1.0) | **strict** |
| **fatty infiltration** (tightened in v1.1.0, researcher ruling) | **strict** |
| fatty change, fatty sparing, focal fat | standard |
| steatosis, steatotic, steatohepatit* (stems; self-evidently hepatic) | standard |

**Bare `fatty` was REMOVED in v1.1.0** (see §8 and docs/fatty_trigger_diagnostic.md).

### Tier B — imaging signs (SENSITIVITY ONLY, never primary)
`increased hepatic echogenicity`, `echogenic liver` (none); `increased
echogenicity`, `low attenuation` (standard; liver within 10); `decreased hepatic
attenuation` (none). Nonspecific — fibrosis and other chronic liver disease also
produce these; reported separately.

### Tier C — hedged Tier A hits (reported separately, merged neither way)
A Tier A trigger passing scoping and negation but under a hedge cue: `may
represent`, `cannot be excluded`, `cannot exclude`, `concerning for`, `suggestive
of`, `possible`, `question of`, `versus`, `differential includes` (plus documented
variants). Radiologists hedge routinely, so many are likely true positives — a
question for chart review, not this rule.

## 3. Anatomical scoping (mandatory)

Follows published VA/VACS-based steatosis NLP work (Hepatology Communications,
2024, as specified by the study team). Target organs {liver, hepatic}; competing
organs {pancreas, pancreatic, gallbladder, marrow, omentum, omental, mesenteric,
mesentery, spleen, splenic, renal, kidney, breast, thymus, thymic}. For a scoped
trigger:

1. If the **nearest** organ token is a competing organ → SUPPRESS (attributed to it).
2. Else if a target is within **10 tokens** → PASS (`affirmative`).
3. **standard only:** else if the sentence has no competing organ → PASS (`fallback`).
4. **strict:** the fallback in (3) is disabled → SUPPRESS as `no_liver_evidence`
   (or the nearest competing organ if one is present).

## 4. Negation & context assertion

**Algorithm: ConText (Harkema et al. 2009), extending NegEx (Chapman et al.
2001)**, reimplemented in-repo with the published trigger lexicons (no external
dependency, for Python 3.14 reproducibility). Sentence/segment-scoped (segments
split at termination terms `but, however, although, though, yet, except, aside
from, nevertheless, otherwise`); pre-cues act forward, post-negation cues backward.

- **Negation** (NegEx pre/post triggers; pseudo-negation blocked, e.g. `no change`,
  `cannot be excluded`): explicitly negates *"no evidence of hepatic steatosis"*,
  *"no fatty change in the liver"*.
- **Family (experiencer)** → EXCLUDE. **Historical (temporality)** → **FLAG, not
  exclude** (reported separately). **Hedged (hypothetical)** → Tier C.
- **Cue matching is token-level (word-boundary).** *(Fixed in v1.1.0 — v1.0.0
  matched cues by substring, so `no` fired inside "normal"/"known"; see §8.)*

**Classification precedence** (per hit): anatomical suppression → family →
negation → hedged (Tier C) → affirmed positive (with optional historical flag).

**Citations**
- Chapman WW, et al. *A simple algorithm for identifying negated findings and
  diseases in discharge summaries.* J Biomed Inform. 2001;34(5):301-310.
- Harkema H, Dowling JN, Thornblade T, Chapman WW. *ConText: An algorithm for
  determining negation, experiencer, and temporal status from clinical reports.*
  J Biomed Inform. 2009;42(5):839-851.
- VA/VACS-based hepatic-steatosis NLP algorithm (Hepatology Communications, 2024)
  — basis for anatomical scoping (exact reference to be confirmed by study team).

## 5. Outpatient radiology window

Radiology notes with NULL `hadm_id` (outpatient imaging) linked to an admission by
`subject_id` and note `charttime` vs `admittime`:
- **Primary: 365 days before, 30 days after.**
- **Sensitivity: 90 days before, 30 days after.**

Rationale: the construct is availability to the clinician *at this admission* —
hence lookback-dominant, with only a short forward window so post-admission /
post-coding information cannot define the phenotype.

## 6. Behavior report (v1.1.0, locked population N = 373,992)

Behavior only — **no sensitivity, PPV, or accuracy metric** (no reference standard).

| measure | n | % |
|---|--:|--:|
| Tier A definite (inpatient-linked) | 18,417 | 4.9 |
| Tier A + B | 22,248 | 5.9 |
| Tier C (hedged) | 1,030 | 0.3 |

- **Source of Tier A:** discharge only 7,726 · radiology only 4,215 · both 6,476.
- **Top triggers:** hepatic steatosis 7,173 · fatty liver 6,862 · echogenic liver
  6,854 (B) · steatosis 6,836 · NASH 4,825 · low attenuation 4,099 (B) ·
  steatohepatitis 3,655 · fatty infiltration 3,578 · fatty deposition 681 ·
  fatty sparing 627 · fatty change 264 · fatty infiltrate 120 · focal fat 57 ·
  fatty replacement 32 · fatty metamorphosis 1.
- **Excluded/suppressed:** negation 941 · family 106 · historical **flagged** 1,998
  · anatomical 6,540 (of which `no_liver_evidence` 4,590 [strict], pancreas 883,
  gallbladder 305, renal 257, pancreatic 148, spleen 132, kidney 125, marrow 66, …).
- **Outpatient radiology:** primary window +9,409 → 27,826; sensitivity +4,342 → 22,759.

## 7. Freeze statement

This specification and `scripts/note_phenotype.py` (VERSION 1.1.0) are frozen prior
to 2×2 construction and chart adjudication. The revision used only the rule's own
behavior — no adjudicated/reference data. Any further change requires a new version
string and must be development, never tuning against adjudicated charts.

## 8. CHANGELOG — v1.0.0 → v1.1.0

Justification: [`docs/fatty_trigger_diagnostic.md`](fatty_trigger_diagnostic.md)
(a behavioral diagnostic on the frozen v1.0.0 rule; no gold standard). Same-day
revision (both dated 2026-08-17); the version string is the distinguishing marker.
v1.0.0 remains tagged `note-phenotype-v1.0.0`.

1. **Removed bare `fatty` as a Tier A trigger.** It uniquely made 8,142
   admissions note-positive, of which 98.9% were code-negative; the phrase
   composition was dominated by `fatty acids` (3,915 hits, a lab/dietary term);
   and 82% of hits passed scoping with no liver/hepatic token in the sentence.
2. **Promoted the plausible phrasings to explicit Tier A phrases** —
   `fatty replacement`, `fatty deposition`, `fatty degeneration`,
   `fatty metamorphosis`, `fatty infiltrate` — with **strict** scoping.
   `fatty atrophy` was deliberately **not** included (in radiology it more often
   describes muscle/pancreas/marrow).
3. **Tightened scoping for the promoted phrases to `strict`** (affirmative
   liver/hepatic within 10 tokens required; no "no competing organ" fallback).
4. **`fatty infiltration` tightened to `strict`** per researcher ruling (Step 2d
   fallback audit: 42.2% of its positives passed via the fallback with no liver
   token). `fatty change`, `fatty sparing`, `focal fat` were reviewed in the same
   audit and **kept at `standard`** by researcher ruling.
5. **Correctness bugfix (approved): token-level cue matching in ConText.** v1.0.0
   matched negation/context cues by substring, so `no` fired inside "normal"/"known",
   falsely negating true positives (e.g. "Normal liver with hepatic steatosis").
   Fixed to word-boundary token matching. Net effect +855 admissions (incl. 47
   code-positive); negation-exclusion count fell 2,287 → 941.

**Aggregate effect (inpatient-linked Tier A):** 27,293 (v1.0.0) → 18,417 (v1.1.0).
Net vs frozen v1.0.0: **lost 9,105 (code+ 92 / code− 9,013)**, gained 229
(code+ 47 / code− 182). The revision shrinks the note-positive cohort by removing
a predominantly code-negative false-positive surface while recovering a small
number of true positives from the negation fix. Reported to show how the revision
moves the recovery zone — **not** as validation.
