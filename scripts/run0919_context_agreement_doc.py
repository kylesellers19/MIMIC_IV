#!/usr/bin/env python3
"""Writes docs/context_agreement.md from docs/run_2026-09-19/results/context_agreement.json."""
import json
r = json.load(open("docs/run_2026-09-19/results/context_agreement.json"))
bc = r["by_assertion_class"]; conf = r["confusion_project_rows_medspacy_columns"]
CLASSES = ["affirmed", "negated", "uncertain", "historical", "family"]
def g(p, m): return conf.get(f"{p}->{m}", 0)
L = ["# Agreement between this project's context handling and medspaCy ConText\n",
"Produced by `scripts/run0919_context_agreement.py`; every number is read from `docs/run_2026-09-19/results/context_agreement.json`. Stretch item of run_2026-09-19. **The frozen note rule is unchanged by this analysis.**\n",
"## Why this exists\n",
"The frozen note phenotype reimplements ConText (Harkema et al. 2009, which extends NegEx, Chapman et al. 2001) inside `scripts/note_phenotype.py`, rather than running the reference software. The manuscript states that as a limitation. This measures it, turning a stated limitation into a quantified one.\n",
"**medspaCy ConText is not a gold standard.** It is an independent implementation with its own default rule set, its own sentence segmentation (PyRuSH) and its own scope rules. A disagreement is a difference between two rule systems, not an error attributable to either. The value of the number is that it bounds how much the choice of implementation could matter.\n",
"## What was compared\n",
f"- Sample: **{r['sampled_reports']:,} radiology reports**, drawn at random (seed {r['seed']}) from the {r['pool_reports']:,} reports in the locked population that carry at least one asserted lexicon match. Restricting to reports with a match is what makes the comparison informative; it is not a random sample of all reports, and the percentages below are per matched mention, not per report.",
f"- Both systems were run over **the same lexicon matches**. The lexicon, sentence splitter and screen terms are imported from the frozen rule; only its hit-iteration order is replicated, and the alignment is verified by comparing trigger names position by position. **{r['reports_unalignable_excluded']} reports failed that check** ({r['reports_compared']:,} compared), so the one-to-one alignment holds throughout.",
f"- **{r['aligned_hits']:,} mentions** were compared. A further **{r['anatomically_suppressed_hits_excluded']:,}** were excluded because the project suppressed them by anatomical scoping (for example a fatty change attributed to the pancreas), which ConText has no analogue for; counting those as disagreement would misattribute a scoping decision to context handling.",
f"- Runtime {r['runtime_s']} s. Exceptions during row-level work: {r['exceptions_by_class'] or 'none'}.\n",
"## Agreement by assertion class\n",
"| assertion class (project) | mentions | agree with ConText | percent agreement |", "| --- | --: | --: | --: |"]
for c in CLASSES:
    v = bc[c]
    pa = "not estimable (no mentions)" if v["percent_agreement"] is None else f"{v['percent_agreement']}%"
    L.append(f"| {c} | {v['project_n']:,} | {v['agree_n']:,} | {pa} |")
L += [f"| **all classes** | **{r['aligned_hits']:,}** | | **{r['overall_percent_agreement']}%** |", "",
"## Where the two systems part company\n",
"Rows are the project's label, columns medspaCy's. Counts of mentions.\n",
"| project ↓ / ConText → | " + " | ".join(CLASSES) + " |", "| --- | " + " | ".join("--:" for _ in CLASSES) + " |"]
for p in CLASSES:
    L.append(f"| {p} | " + " | ".join(f"{g(p, m):,}" for m in CLASSES) + " |")
L += ["", "Reading the table:\n",
f"- **Negation is where the two agree most** ({bc['negated']['percent_agreement']}% of the project's negated mentions). The larger asymmetry runs the other way: **{g('affirmed','negated'):,} mentions the project treats as affirmed are negated by ConText**, against {g('negated','affirmed'):,} in the opposite direction. On this corpus the project's rule is the more conservative negator — it asserts presence where the reference implementation would not.",
f"- **Hedging is the weakest class** ({bc['uncertain']['percent_agreement']}%). ConText marks {g('affirmed','uncertain'):,} project-affirmed mentions as uncertain, while {g('uncertain','affirmed'):,} project-hedged mentions come back affirmed and {g('uncertain','negated'):,} come back negated. This matters for the study because hedged mentions are exactly the Tier C category the project reports separately, and because Phase 4.4 shows counting Tier C positive moves the primary recovery share by about a third of a point.",
f"- **Historical** agrees {bc['historical']['percent_agreement']}% of the time; the project flags historical mentions but does not exclude them, so this difference does not propagate to note-positive status.",
f"- **Family history does not arise in this corpus**: the project found {bc['family']['project_n']} family-attributed mentions in {r['sampled_reports']:,} radiology reports, which is expected — family history is a discharge-summary phenomenon, not a radiology one. The class is therefore not estimable here, and a discharge-summary sample would be needed to measure it.\n",
"## What this licenses the manuscript to say\n",
f"The limitation can move from \"negation and context handling were reimplemented rather than run from the reference distribution\" to \"...; on {r['sampled_reports']:,} radiology reports the reimplementation agreed with medspaCy ConText on {r['overall_percent_agreement']}% of {r['aligned_hits']:,} lexicon mentions, with agreement highest for negation ({bc['negated']['percent_agreement']}%) and lowest for hedging ({bc['uncertain']['percent_agreement']}%)\". The disagreement is concentrated in the hedged category that the phenotype already reports separately, which is the reassuring part; the {g('affirmed','negated'):,} affirmed-versus-negated disagreements are the part that would change note-positive status and deserve a sentence of their own.\n",
"This analysis changed nothing. The rule, its tags and the 2×2 are exactly as they were.\n"]
open("docs/context_agreement.md", "w").write("\n".join(L) + "\n")
print("wrote docs/context_agreement.md")
