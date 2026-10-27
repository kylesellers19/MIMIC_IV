# Sentence annotation guide: hepatic steatosis (for validating the LLM review)

**Status: DRAFT for clinician review.** This guide labels single sentences so the local language model's answers can be checked against people. It is separate from the 400-chart adjudication (`docs/adjudication_criteria.md`), which labels whole admissions and remains the study's reference standard. Where the two disagree, the adjudication criteria win, and this guide is revised to match them before annotation starts.

## Who annotates, and how

- **Credentials:** annotators must hold their own PhysioNet credentialing and a signed MIMIC data use agreement. The workbooks contain note text.
- **Independence:** two annotators label every item independently, without discussing items until both have finished. A third clinician adjudicates the items where they disagree.
- **Blinding:** the workbook shows no model answer, admission identifier, diagnosis code, sampling group or note-rule result. Do not look at any of these, or at the model's output files, before you finish.
- **Order:** items appear in a random order. Label them in the order shown.
- **What you see:** the note type, the nearest section heading, the previous sentence, the **SENTENCE**, and the next sentence. Label only the SENTENCE. Use the neighbouring sentences and heading only to understand it, for example to tell which organ "it" refers to.
- **Uncertainty:** when you cannot decide, choose the closer label and write why in `comment`. Do not leave ANSWER blank.

## ANSWER: does the SENTENCE state that this patient's liver is fatty?

### YES: the sentence states hepatic steatosis
- Steatosis, fatty liver, or fatty infiltration or fatty change **of the liver**.
- NAFLD, NAFL, NASH, MASLD, MASH, MAFLD or steatohepatitis.
- An imaging sign of liver fat:
  - a diffusely echogenic or hyperechoic liver
  - decreased liver attenuation, attenuation below the spleen, or below 40 HU
  - liver signal loss on out-of-phase MRI
- **Focal fatty sparing**, because it means the rest of the liver is fatty.
- "Consistent with" or "compatible with" steatosis counts as YES.

### NO: the sentence says the liver is not fatty, or says nothing about fat in the liver
- Explicit negation: "no hepatic steatosis", "liver normal in echogenicity".
- Fat only in another organ or tissue: pancreas, kidney, spleen, bone marrow, fat around the liver, the falciform ligament.
- Focal fat, or a single fatty lesion in the liver.
- A request to evaluate for or rule out fatty liver.
- Liver tests or other liver findings that do not mention fat: enzymes, cysts, vessels, size.

### UNCLEAR: the sentence suggests liver fat but is uncertain
- Hedged wording: likely, probable, suggestive of, possible, may represent, cannot exclude, borderline, questionable.
- Coarse or heterogeneous liver echotexture with no mention of fat. It can mean scarring rather than fat.

## TIMING: whose finding, and when

- **CURRENT:** about this patient now (this study, this admission, or an ongoing diagnosis).
- **PAST:** a prior study or the patient's history ("history of", "prior CT showed").
- **FAMILY:** about a relative.
- **NA:** use only when ANSWER is NO.

## Invented examples

These examples were written for this guide; none comes from MIMIC.

| Sentence | ANSWER | TIMING |
| --- | --- | --- |
| The liver is diffusely echogenic, compatible with steatosis. | YES | CURRENT |
| Diffuse fatty infiltration with focal sparing near the gallbladder. | YES | CURRENT |
| History of NASH on biopsy in 2015. | YES | PAST |
| Her mother has fatty liver disease. | YES | FAMILY |
| Fatty atrophy of the pancreas; the liver is unremarkable. | NO | NA |
| Focal fat adjacent to the falciform ligament. | NO | NA |
| Ultrasound requested to evaluate for fatty liver. | NO | NA |
| Liver function tests are pending. | NO | NA |
| Mildly increased hepatic echogenicity may represent steatosis. | UNCLEAR | CURRENT |
| The liver is coarse and heterogeneous in echotexture. | UNCLEAR | CURRENT |

## Open questions for the clinicians (resolve before annotation)

1. **"Likely" or "probable" steatosis.** Should these be UNCLEAR, as drafted here, or YES? Published studies differ.
2. **Coarse or heterogeneous echotexture.** Is it UNCLEAR, or NO unless fat is mentioned?
3. **Ongoing diagnoses.** Should a known diagnosis ("known MASLD, followed by hepatology") be CURRENT or PAST?
4. **Consistency.** All three answers must match the decisions taken in `docs/adjudication/criteria_revision_proposal.md` (items D1, D6 and the hedge conventions).
