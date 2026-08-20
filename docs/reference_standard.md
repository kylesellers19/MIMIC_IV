# Reference-Standard Specification — MASLD Phenotyping on MIMIC-IV

## Study context

Cross-sectional MASLD phenotyping study on **MIMIC-IV / MIMIC-IV-Note / MIMIC-IV-ED**.

**Central question:** do clinical notes recover MASLD cases that structured ICD coding systematically misses?

**Sub-aims:**
- **1a** — quantify the ICD under-capture gap (codes-vs-gold disagreement).
- **1b** — three-arm ML comparison: structured baseline vs notes-augmented vs stacked fusion.
- **1c** — equity audit of differential recovery across demographic subgroups.

**Design choice — Approach A.** A computable **"silver"** label drives model development at scale; a stratified, human-adjudicated **"gold"** standard (a few hundred charts) provides validation. This follows the current published norm (e.g., ADAPT OUD 2025; multi-system OUD ED phenotype).

**Unusual feature.** The silver/structured label is itself the object under indictment — it is alleged to be systematically biased. It must therefore be framed explicitly as a **weak/biased label**, and the **code-vs-gold disagreement analysis (1a) is the centerpiece**, not a validation footnote.

---

## 1. Design rationale

Human-adjudicated chart review is the **irreducible reference standard** because it is the only label **independent of both methods under comparison**:

- If we judged the ICD gap against an ICD-derived truth, the **1a gap collapses to zero** by construction.
- If we judged the notes arm against a notes-derived truth, the **1b notes arm grades itself** — circular.

Only an independent gold standard breaks both circularities and lets 1a measure a real gap and 1b compare arms fairly. Chart review is expensive, hence sampled rather than exhaustive — but it cannot be substituted by either candidate signal.

---

## 2. Pre-registered adjudication criteria

> **🚧 DRAFT 1 — drafted, NOT yet locked. Requires clinician sign-off before any
> chart review begins.** Full criteria in
> [docs/adjudication_criteria.md](adjudication_criteria.md). This remains the gate
> (see Status): the criteria may be revised **only** at the 20-chart training set
> (§9 of that doc); once formal review of the 400-chart sample begins they are frozen.

Draft 1 specifies, replacing the earlier stubs:
- **2.1 Imaging / histology evidence** — an evidence hierarchy (biopsy / CT-MRI →
  Definite; ultrasound echogenicity → Probable; note statement → Probable; hedged
  imaging → Possible) on a Definite/Probable/Possible/Absent/Insufficient scale.
- **2.2 Metabolic criteria** — secondary question 6a: ≥1 of BMI≥25, T2D/prediabetes,
  BP≥130/85 or antihypertensive, TG≥150, HDL≤40/≤50, or lipid-lowering therapy
  (matching the computable operationalization in docs/sld_subclassification.md).
- **2.3 Alcohol** — secondary question 6b: MetALD g/wk bands vs a qualitative scale
  (open decision; MIMIC lacks quantified intake — expect "not documented" to dominate).
- **2.4 Ambiguous / insufficient** — an explicit *Insufficient information* level plus
  a *Possible* tier; temporality (during/before/both) recorded separately.

Open clinician decisions (D1–D8) and an analyst cross-consistency check are collated
in the linked document.

---

## 3. Sampling frame

Two pre-specified stratification axes:

- **Code status** — structured ICD label positive/negative for MASLD.
- **Note trigger** — a simple, pre-specified rule flagging MASLD-relevant note content (deliberately crude; see §7a).

Crossing them gives a 2×2 frame:

| | **Note +** | **Note −** |
|---|---|---|
| **Code +** | code+/note+ | code+/note− |
| **Code −** | **code−/note+ (recovery zone)** | code−/note− |

The **code−/note+ cell is the recovery zone** — cases the codes miss but the notes flag. It is the **heart of the study** and the empirical basis for the 1a gap.

---

## 4. Allocation table

For a **~400-chart** budget:

| Cell | Allocation | Role |
|---|---:|---|
| code−/note+ | **~150** | Recovery zone — largest by design |
| code−/note− | ~100 | True-negative / residual-miss check |
| code+/note+ | ~80 | Concordant positives |
| code+/note− | ~70 | Code-only positives |
| **Total** | **~400** | |

Counts are **adjustable**, but the **recovery zone stays largest**. ~400 sits within the published range and supports **1c subgroup confidence intervals**.

---

## 5. Integrity rules

1. **Blinding** — reviewers are blinded to **both** code status and note-trigger status, so cell membership cannot bias adjudication.
2. **Double review + kappa** — two reviewers independently adjudicate an overlapping **~20–30%** subset, with **Cohen's kappa** reported; the remainder is single-reviewed; a **third adjudicator** resolves disagreements.
3. **Pre-registration** — adjudication criteria (§2) are **finalized and pre-registered before review starts**.

---

## 6. Estimation / reweighting note

Sampling is **disproportionate** (cells deliberately over/under-sampled), so cells must be **reweighted by their true population frequency** for the headline 1a estimate.

**Headline 1a estimate:** of all **gold-standard-positive** patients, what **population-weighted fraction were code-negative** — i.e., *"codes miss X%"* — reported **with a confidence interval**.

> **Requirement:** **cell sizes and per-cell sampling fractions MUST be stored** at sampling time. Without them the reweighting cannot be reconstructed and the headline estimate is uninterpretable.

---

## 7. Flagged design decisions (still open)

**(a) Note trigger ≠ notes model.** The stratification note trigger is a **deliberately crude, transparent, pre-specified** rule. It is **distinct from, and never reused as, the 1b notes model**, to avoid leakage between the sampling instrument and the method under evaluation.

**(b) Optional LLM pre-screen — ranking only.** An LLM may **rank** charts *within* the recovery cell to improve reviewer hit-rate, but it **never assigns labels**. Reviewers adjudicate independently, keeping the reference standard **non-circular**.

---

## 8. Open decisions owned by the researcher

- **Who performs the review** (reviewer recruitment / clinical qualification).
- **Final stratification thresholds** (cell boundaries).
- **Exact note-trigger definition** (the §7a rule).

---

## Status

This specification **resolves the reference-standard blocker at the design level.** The remaining gate before review can begin is **finalization and pre-registration of the adjudication criteria (§2).**
