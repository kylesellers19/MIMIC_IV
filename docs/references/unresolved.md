# Unresolved references — run_2026-11-10 Phase 8 (registry first built in run_2026-09-19 Phase 10.4)

Generated 2026-11-11T03:44:15+00:00 by `scripts/verify_citations.py`. Each entry lists exactly what was tried and what came back. No guess is recorded; these need a human decision or a fuller citation string in the source document.

## R12_johnson_mimic_iv_note

- **As cited in repo:** MIMIC-IV-Note 2.2  
  files: `docs/note_coverage.md`, `README.md`, `docs/reference_standard.md`, `scripts/note_schema.py`
- **As named in the task brief:** Johnson et al. MIMIC-IV-Note
- **Registry note:** PhysioNet resource; no year or title in the repo or the brief. The DOI is a candidate from the 10 November run file. PhysioNet DOIs may not be registered with Crossref, in which case the verifier's two APIs cannot confirm it.
- **Tried:**
  1. esearch by DOI 10.13026/1n74-ne17: 0 results
  2. Crossref /works/10.13026/1n74-ne17: HTTP 404

## R16_physionet_2025_llm_guidance

- **As cited in repo:** PhysioNet. Use of MIMIC data with large language models and online services. 24 Sep 2025. https://physionet.org/news/post/llm-responsible-use/  
  files: `docs/llm_review_protocol.md`
- **Registry note:** A news post with no author, DOI or PMID. Neither PubMed nor Crossref indexes it; it cannot be accepted by rule. The URL is as given in the protocol and was not fetched.
- **Tried:**
  1. esearch by journal/year/keywords [2025[dp] AND PhysioNet[tiab] AND "large language models"[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 1 result(s); not acceptable by rule (no first author in registry)
- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**
  - PubMed | Chetla N | 2025 | Cureus | 'Intracranial Hemorrhage Detection and Subtype Classification on CT Imaging Using a Large Language Model' | DOI 10.7759/cureus.98029 | PMID 41466907

## R22_sclar_2024_prompt_formatting

- **As cited in repo:** Sclar M et al. Prompt formatting sensitivity. ICLR 2024 (arXiv:2310.11324)  
  files: `docs/llm_review_protocol.md`
- **Registry note:** Conference paper cited by arXiv identifier. arXiv identifiers are not registered with Crossref and the paper is not in PubMed, so the verifier's two APIs are unlikely to confirm it.
- **Tried:**
  1. esearch by author/year [Sclar[1au] AND 2024[dp] AND prompt[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 0 result(s) — not exactly one, rejected
  2. Crossref by author/year [Sclar 2024  prompt]: 5 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
  3. Crossref by keywords [prompt]: 10 candidates, 0 pass first-author+year+keyword filter — not exactly one, rejected (none)
- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**
  - Crossref (author query) | Sclar David | None | Encyclopedia of the Bible Online | 'Maggid, Maggidism' | DOI 10.1515/ebr.maggidmaggidism | PMID —
  - Crossref (author query) | Sclar David Alexander | 1999 | Clinical Therapeutics | 'Editorial comment' | DOI 10.1016/s0149-2918(99)80057-5 | PMID —
  - Crossref (author query) | Sclar David | 2024 | Judaica Librarianship | 'A Personal Reflection on the Life and Work of Menahem Schmelzer (1934–2022)' | DOI 10.14263/23/2024/1439 | PMID —
