# Note-Based Hepatic-Steatosis Phenotype — Frozen Specification

**VERSION 1.0.0 · FROZEN 2026-08-17**

> **This rule is FROZEN prior to 2×2 construction and chart adjudication.**
> Development on the full corpus is expected and was used to build this rule;
> iteration against the gold standard is **not** permitted after this freeze.
> Tuning a note-positive rule against adjudicated charts and then reporting
> performance on those charts would be circular and would invalidate Aim 1a.

Implementation: [`scripts/note_phenotype.py`](../scripts/note_phenotype.py)
(`classify_note()` is the frozen classifier; the module version string and date
match this document). Text-handling: aggregate outputs only; no raw note text is
printed or written anywhere.

## 1. Purpose

Assign each admission a **note-positive** status for documented hepatic steatosis,
using linked discharge and radiology notes. The construct is *"was steatosis
documented and available to the clinician at this admission."* This is a
computable phenotype, **not** an adjudicated label.

## 2. Lexicon (approved, three tiers)

### Tier A — definite steatosis (PRIMARY)
- **Stems** (case-insensitive, word-boundary): `steatosis`, `steatotic`,
  `steatohepatit`* (→ steatohepatitis / steatohepatitic).
- **Phrases**: `fatty liver`, `fatty infiltration`, `fatty change`,
  `fatty sparing`, `focal fat`, `hepatic steatosis`.
- **Abbreviations**: `NAFLD`, `NASH`, `MASLD`, `MASH`, `NAFL`.
- **Spelled-out** (all hyphenation variants via `non[- ]?alcoholic`,
  `metabolic dysfunction[- ]associated`): non-alcoholic / nonalcoholic fatty
  liver (disease), non-alcoholic / nonalcoholic steatohepatitis,
  metabolic dysfunction-associated.
- **Bare `fatty`**: counts **only** when it passes anatomical scoping (§3).

### Tier B — imaging signs (SENSITIVITY ANALYSIS ONLY, never primary)
`increased hepatic echogenicity`, `echogenic liver`, `increased echogenicity`
(liver/hepatic within 10 tokens), `decreased hepatic attenuation`,
`low attenuation` (liver within 10 tokens). Nonspecific — fibrosis and other
chronic liver disease also produce these; reported separately, never folded into
the primary definition.

### Tier C — hedged Tier A hits (reported separately, merged neither way)
A Tier A trigger that passes scoping and negation but falls under a hedge cue:
`may represent`, `cannot be excluded`, `cannot exclude`, `concerning for`,
`suggestive of`, `possible`, `question of`, `versus`, `differential includes`
(plus documented variants: `possibly`, `suspicious for`, `could represent`,
`rule out` / `r/o`, `worrisome for`). Radiologists hedge routinely, so many are
likely true positives — a question chart review answers, not this rule.

## 3. Anatomical scoping (mandatory)

Follows published VA/VACS-based steatosis NLP work (Hepatology Communications,
2024, as specified by the study team): `fatty` / `steatosis` / `steatotic` and
the scoping-required phrases must refer to the liver, not adjacent anatomy.
Triggers that are *inherently hepatic* (contain "liver"/"hepatic", or the
abbreviations/spelled-out forms) skip scoping. For every other Tier A/B hit, with
target organs {liver, hepatic} and competing organs {pancreas, pancreatic,
gallbladder, marrow, omentum, omental, mesenteric, mesentery, spleen, splenic,
renal, kidney, breast, thymus, thymic}:

1. Find nearest target and nearest competing organ token (token distance).
2. **If the nearest organ is a competing organ → SUPPRESS** (attributed to that organ).
3. Else if a target (liver/hepatic) is within **10 tokens** → PASS.
4. Else if the enclosing sentence has **no competing organ** → PASS.
5. Else (no target within 10, competing organ present but not nearest) → SUPPRESS
   (ambiguous, attributed to nearest competing organ).

**Suppression is a reportable result** (size of the false-positive class):

| nearest organ | suppressed hits |
|---|--:|
| pancreas | 406 |
| gallbladder | 274 |
| pancreatic | 97 |
| spleen | 80 |
| marrow | 75 |
| renal | 53 |
| kidney | 33 |
| splenic | 9 |
| mesenteric | 8 |
| breast | 7 |
| mesentery | 4 |
| thymic | 2 |
| omentum | 2 |
| omental | 1 |
| **total** | **1,051** |

## 4. Negation & context assertion

**Algorithm: ConText (Harkema et al. 2009), which extends NegEx (Chapman et al.
2001).** Reimplemented in-repo with the published trigger lexicons (no external
dependency, for Python 3.14 reproducibility). ConText assigns each trigger three
axes — negation, temporality (→ historical), experiencer (→ family) — plus
hypothetical (→ Tier C). Sentence/segment-scoped: a cue affects a trigger within
the same segment (segments split at termination terms `but, however, although,
though, yet, except, aside from, nevertheless, otherwise`), forward for
pre-cues, backward for post-cues.

- **Negation** (NegEx): pre-triggers (`no`, `not`, `without`, `denies`,
  `negative for`, `no evidence of`, `absence of`, `free of`, …) and post-triggers
  (`is negative`, `not seen`, `ruled out`, `unremarkable`, `resolved`, …).
  Explicitly negates *"no evidence of hepatic steatosis"*, *"no fatty change in
  the liver"*. **Pseudo-negation** phrases are blocked from negating
  (`no change`, `no significant change`, `no interval change`, `not necessarily`,
  `cannot be excluded`, …).
- **Family history (experiencer)** → **EXCLUDE**: `family history of`,
  `mother/father/sibling/…`, `maternal/paternal`.
- **Historical (temporality)** → **FLAG, not exclude**: `history of`, `hx of`,
  `h/o`, `status post`, `s/p`, `prior`, `previously`, `remote`. Reported
  separately (see §6).
- **Hedged (hypothetical)** → **Tier C** (§2).

**Classification precedence** (per hit): anatomical suppression → family →
negation → hedged (Tier C) → affirmed positive (with optional historical flag).

**Citations**
- Chapman WW, Bridewell W, Hanbury P, Cooper GF, Buchanan BG. *A simple algorithm
  for identifying negated findings and diseases in discharge summaries.* J Biomed
  Inform. 2001;34(5):301-310.
- Harkema H, Dowling JN, Thornblade T, Chapman WW. *ConText: An algorithm for
  determining negation, experiencer, and temporal status from clinical reports.*
  J Biomed Inform. 2009;42(5):839-851.
- VA/VACS-based hepatic-steatosis NLP algorithm (Hepatology Communications, 2024)
  — basis for the anatomical-scoping rule (exact reference to be confirmed by the
  study team).

## 5. Outpatient radiology window

Radiology notes with NULL `hadm_id` are outpatient imaging, linked to an
admission by `subject_id` and note `charttime` relative to `admittime`:

- **Primary: 365 days before, 30 days after.**
- **Sensitivity: 90 days before, 30 days after.**

**Rationale (recorded per instruction):** the construct is "was steatosis
documented and available to the clinician at this admission" — hence
**lookback-dominant**, with only a short (30-day) forward window so that
post-admission / post-coding information cannot define the phenotype.

## 6. Behavior report (locked population, N = 373,992 admissions)

Behavior only — **no sensitivity, PPV, or accuracy metric** (no reference
standard exists yet).

| measure | n | % of pop |
|---|--:|--:|
| Tier A definite (inpatient-linked) | 27,293 | 7.3 |
| Tier A + B | 30,649 | 8.2 |
| Tier C (hedged) group | 1,347 | 0.4 |

- **Source of Tier A positives:** discharge only 12,575 · radiology only 6,964 · both 7,754.
- **Top triggers (positive):** fatty (bare) 12,402 · hepatic steatosis 7,103 ·
  echogenic liver 6,764 (B) · steatosis 6,728 · fatty liver 6,721 · fatty
  infiltration 5,722 · NASH 4,690 · low attenuation 3,844 (B) · steatohepatitis
  3,621 · NAFLD 634. (Bare `fatty` is the single largest contributor — flagged
  for the study team's attention; it is anatomically scoped but broad.)
- **Excluded / suppressed (hit-level, linked notes):** negation 2,287 · family 97
  · anatomical 1,051 (per organ, §3) · historical **flagged** (not excluded) 2,144.
- **Outpatient radiology:** primary window adds **17,162** admissions to Tier A
  (outpatient-inclusive total 44,455); sensitivity window adds 7,533 (total 34,826).

## 7. Freeze statement

This specification and `scripts/note_phenotype.py` (VERSION 1.0.0, 2026-08-17)
are **frozen prior to 2×2 construction and chart adjudication**. Any change after
this point requires a new version string and must be justified as development
(full-corpus), never as tuning against adjudicated charts. The 2×2 (Aim 1a) and
the sampling frame are built on top of this frozen rule without modifying it.
