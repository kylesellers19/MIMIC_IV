# Unresolved references — run_2026-09-19 Phase 10.4

Generated 2026-09-19T16:58:00+00:00 by `scripts/verify_citations.py`. Each entry lists exactly what was tried and what came back. No guess is recorded; these need a human decision or a fuller citation string in the source document.

## R08_vacs_steatosis_nlp_2024

- **As cited in repo:** VA/VACS-based hepatic-steatosis NLP algorithm (Hepatology Communications, 2024) — basis for anatomical scoping (exact reference to be confirmed by study team).  
  files: `docs/note_phenotype_spec.md`
- **Registry note:** No author, title or identifier in the repo; the spec itself says the exact reference is to be confirmed. Cannot be accepted by rule; search recorded for the study team.
- **Tried:**
  1. esearch by journal/year/keywords [2024[dp] AND "Hepatology Communications"[ta] AND "hepatic steatosis"[tiab] AND "natural language processing"[tiab] AND veterans[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 1 result(s); not acceptable by rule (no first author in registry)
- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**
  - PubMed | Torgersen J | 2024 | Hepatology communications | 'Identification of hepatic steatosis among persons with and without HIV using natural language processing' | DOI 10.1097/HC9.0000000000000468 | PMID 38896066

## R09_alsentzer_2019_bio_clinicalbert

- **As cited in repo:** emilyalsentzer/Bio_ClinicalBERT  
  files: `scripts/run0919_embed.py`, `docs/run_2026-09-19/RUN_LOG.md`, `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`, `scripts/aim1b_gold_cv.py`
- **As named in the task brief:** Alsentzer et al. 2019 Bio_ClinicalBERT
- **Registry note:** Repo names only the Hugging Face model id; author and year come from the task brief.
- **Tried:**
  1. esearch by author/year [Alsentzer[1au] AND 2019[dp] AND clinical[tiab] AND BERT[tiab] AND embeddings[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 0 result(s) — not exactly one, rejected
  2. Crossref by author/year [Alsentzer 2019  clinical BERT embeddings]: 5 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
  3. Crossref by keywords [clinical BERT embeddings]: 10 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**
  - Crossref (author query) | Alsentzer Harry A. | 1963 | Journal AWWA | 'Ion Exchange in Water Treatment' | DOI 10.1002/j.1551-8833.1963.tb01083.x | PMID —
  - Crossref (author query) | Alsentzer Emily | 2019 | Proceedings of the 2nd Clinical Natural Language Processing Workshop | 'Publicly Available Clinical' | DOI 10.18653/v1/w19-1909 | PMID —

## R10_li_2022_clinical_longformer

- **As cited in repo:** Clinical-Longformer  
  files: `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`, `docs/run_2026-09-19/RUN_LOG.md`
- **As named in the task brief:** Li et al. Clinical-Longformer 2022
- **Registry note:** Repo names only the model; author and year come from the task brief.
- **Tried:**
  1. esearch by author/year [Li[1au] AND 2022[dp] AND Clinical-Longformer[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 0 result(s) — not exactly one, rejected
  2. Crossref by author/year [Li 2022  Clinical-Longformer]: 5 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
  3. Crossref by keywords [Clinical-Longformer]: 10 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**
  - Crossref (author query) | Li Shilong | 2022 | Journal of Clinical Investigation | 'Concerns about the interpretation of subgroup analysis. Reply' | DOI 10.1172/jci156711 | PMID —
  - Crossref (author query) | Liang Meng | 2022 | World Journal of Clinical Cases | 'Nanotechnology in diagnosis and therapy of gastrointestinal cancer' | DOI 10.12998/wjcc.v10.i16.5146 | PMID —

## R12_johnson_mimic_iv_note

- **As cited in repo:** MIMIC-IV-Note 2.2  
  files: `docs/note_coverage.md`, `README.md`, `docs/reference_standard.md`, `scripts/note_schema.py`
- **As named in the task brief:** Johnson et al. MIMIC-IV-Note
- **Registry note:** PhysioNet resource; no year, title or identifier in the repo or the brief. Expected to be unresolvable by rule (no unique match criterion can be met without a year).
- **Tried:**
  1. esearch by author/year [Johnson[1au] AND MIMIC-IV-Note[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 0 result(s) — not exactly one, rejected
  2. Crossref by author/year [Johnson   MIMIC-IV-Note]: 5 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
  3. Crossref by keywords [MIMIC-IV-Note]: 10 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**
  - Crossref (author query) | Johnson Douglas L. | 2003 | Geographical Review | 'Editor's Note' | DOI 10.1111/j.1931-0846.2003.tb00017.x | PMID —
  - Crossref (author query) | Johnson G.E. | 1993 | IEEE Transactions on Neural Networks | 'Mimic nets' | DOI 10.1109/72.248458 | PMID —
  - Crossref (author query) | Johnson Prof. | 1882 | The Analyst | 'Note by Prof. Johnson' | DOI 10.2307/2635991 | PMID —
