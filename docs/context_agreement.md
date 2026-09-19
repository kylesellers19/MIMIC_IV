# Agreement between this project's context handling and medspaCy ConText

Produced by `scripts/run0919_context_agreement.py`; every number is read from `docs/run_2026-09-19/results/context_agreement.json`. Stretch item of run_2026-09-19. **The frozen note rule is unchanged by this analysis.**

## Why this exists

The frozen note phenotype reimplements ConText (Harkema et al. 2009, which extends NegEx, Chapman et al. 2001) inside `scripts/note_phenotype.py`, rather than running the reference software. The manuscript states that as a limitation. This measures it, turning a stated limitation into a quantified one.

**medspaCy ConText is not a gold standard.** It is an independent implementation with its own default rule set, its own sentence segmentation (PyRuSH) and its own scope rules. A disagreement is a difference between two rule systems, not an error attributable to either. The value of the number is that it bounds how much the choice of implementation could matter.

## What was compared

- Sample: **20,000 radiology reports**, drawn at random (seed 20260926) from the 45,355 reports in the locked population that carry at least one asserted lexicon match. Restricting to reports with a match is what makes the comparison informative; it is not a random sample of all reports, and the percentages below are per matched mention, not per report.
- Both systems were run over **the same lexicon matches**. The lexicon, sentence splitter and screen terms are imported from the frozen rule; only its hit-iteration order is replicated, and the alignment is verified by comparing trigger names position by position. **0 reports failed that check** (20,000 compared), so the one-to-one alignment holds throughout.
- **35,268 mentions** were compared. A further **2,182** were excluded because the project suppressed them by anatomical scoping (for example a fatty change attributed to the pancreas), which ConText has no analogue for; counting those as disagreement would misattribute a scoping decision to context handling.
- Runtime 958 s. Exceptions during row-level work: none.

## Agreement by assertion class

| assertion class (project) | mentions | agree with ConText | percent agreement |
| --- | --: | --: | --: |
| affirmed | 33,049 | 30,256 | 91.55% |
| negated | 1,017 | 975 | 95.87% |
| uncertain | 841 | 518 | 61.59% |
| historical | 361 | 261 | 72.3% |
| family | 0 | 0 | not estimable (no mentions) |
| **all classes** | **35,268** | | **90.76%** |

## Where the two systems part company

Rows are the project's label, columns medspaCy's. Counts of mentions.

| project ↓ / ConText → | affirmed | negated | uncertain | historical | family |
| --- | --: | --: | --: | --: | --: |
| affirmed | 30,256 | 1,556 | 963 | 267 | 7 |
| negated | 39 | 975 | 3 | 0 | 0 |
| uncertain | 216 | 103 | 518 | 4 | 0 |
| historical | 90 | 5 | 5 | 261 | 0 |
| family | 0 | 0 | 0 | 0 | 0 |

Reading the table:

- **Negation is where the two agree most** (95.87% of the project's negated mentions). The larger asymmetry runs the other way: **1,556 mentions the project treats as affirmed are negated by ConText**, against 39 in the opposite direction. On this corpus the project's rule is the more conservative negator — it asserts presence where the reference implementation would not.
- **Hedging is the weakest class** (61.59%). ConText marks 963 project-affirmed mentions as uncertain, while 216 project-hedged mentions come back affirmed and 103 come back negated. This matters for the study because hedged mentions are exactly the Tier C category the project reports separately, and because Phase 4.4 shows counting Tier C positive moves the primary recovery share by about a third of a point.
- **Historical** agrees 72.3% of the time; the project flags historical mentions but does not exclude them, so this difference does not propagate to note-positive status.
- **Family history does not arise in this corpus**: the project found 0 family-attributed mentions in 20,000 radiology reports, which is expected — family history is a discharge-summary phenomenon, not a radiology one. The class is therefore not estimable here, and a discharge-summary sample would be needed to measure it.

## What this licenses the manuscript to say

The limitation can move from "negation and context handling were reimplemented rather than run from the reference distribution" to "...; on 20,000 radiology reports the reimplementation agreed with medspaCy ConText on 90.76% of 35,268 lexicon mentions, with agreement highest for negation (95.87%) and lowest for hedging (61.59%)". The disagreement is concentrated in the hedged category that the phenotype already reports separately, which is the reassuring part; the 1,556 affirmed-versus-negated disagreements are the part that would change note-positive status and deserve a sentence of their own.

This analysis changed nothing. The rule, its tags and the 2×2 are exactly as they were.

