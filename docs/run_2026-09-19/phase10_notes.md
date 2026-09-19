# Phase 10.4–10.6 working notes (run_2026-09-19)

**Appendix B not available.** The run file's Appendix B (the intended citation list) was truncated in transmission and was not
available to this subagent. The citation registry was therefore built from citation strings found in the repository's own
tracked documents and script docstrings, plus the items the Phase 10.4 brief named explicitly (marked `search_basis: brief`
in the registry). When Appendix B is recovered, add its entries to `docs/references/registry.yaml` and re-run
`scripts/verify_citations.py`; nothing else needs to change.

## 10.4 Citation verification

**Purpose.** Verify every citation the repo relies on against PubMed / Crossref so that no bibliographic field in the
manuscript is written from memory.

**What was done.**
- Grepped `README.md`, `docs/**/*.md`, `scripts/*.py`, `sql/*.sql`, `tests/*.py` for author-year strings, journal references, DOIs and PMIDs.
  Repo-sourced entries (8): Hagström 2021; Rinella 2023; Kahn 2016; Chapman 2001 (NegEx); Harkema 2009 (ConText); Quan 2005; Charlson 1987;
  the unattributed "VA/VACS-based hepatic-steatosis NLP algorithm (Hepatology Communications, 2024)" in `docs/note_phenotype_spec.md`.
  Brief-sourced entries (5), for which the repo names only a product/model/dataset (no citation): Alsentzer 2019 Bio_ClinicalBERT;
  Li 2022 Clinical-Longformer; Johnson 2023 MIMIC-IV (Sci Data); Johnson MIMIC-IV-Note; Collins 2024 TRIPOD+AI (BMJ; nothing in the repo mentions TRIPOD at all).
  `comorbidipy` is a software package, not a citation, and was left out.
- Wrote `docs/references/registry.yaml` (13 entries: id, verbatim repo string, source files, identifiers the repo gives, allowed search fields).
- Wrote `scripts/verify_citations.py` (urllib only; `requests` is not installed in `.venv`). Order: PubMed by PMID → PubMed by DOI → PubMed by exact
  title (quoted, then all title words with PubMed stopwords removed) → PubMed by first-author + year (+ journal / volume / page / keywords) →
  Crossref `/works/<doi>` → Crossref `query.bibliographic` title, rows=5 → Crossref author/keyword query. 0.34 s between calls; one retry after 30 s;
  descriptive User-Agent. Acceptance: identifier resolves directly (and any second identifier in the repo agrees), or normalised title is identical,
  or — only when the repo gives neither title nor identifier — exactly one candidate is returned and first author, year and (if given) journal match.
  Author-only queries exclude `"published erratum"[pt]` and `"retraction of publication"[pt]` (a standard PubMed publication-type filter; without it
  the MIMIC-IV paper returned itself plus its two author corrections). Crossref-confirmed records get a PMID only if PubMed-by-DOI returns a record
  whose DOI and normalised title both agree. Candidates that were seen but not accepted are listed under each unresolved entry, clearly labelled.
- Raw API responses saved under `data/processed/run_2026-09-19_scratch/citations/` (32 files; no patient data).

**Results** (`docs/run_2026-09-19/results/citations.json`): registry 13 · verified 9 · unresolved 4.
Verified by source: PubMed by PMID 2 (Hagström, Rinella) · PubMed by DOI 1 (Kahn) · PubMed by title 2 (Chapman, Harkema) ·
PubMed by author+year+journal, unique candidate 3 (Quan 2005, Johnson 2023 MIMIC-IV, Collins 2024 TRIPOD+AI) · PubMed by author+year+keywords, unique candidate 1 (Charlson 1987).
Unresolved: R08 VA/VACS steatosis NLP (no author in the repo; PubMed returned exactly one candidate for journal+year+keywords, listed for the study team, not accepted);
R09 Alsentzer 2019 (not in PubMed; Crossref has a 2019 proceedings-article by Alsentzer E, DOI 10.18653/v1/w19-1909, but Crossref's stored title is truncated to
"Publicly Available Clinical", so the keyword rule fails — listed as a candidate, not accepted); R10 Li 2022 Clinical-Longformer (0 PubMed hits; no Crossref candidate
with first author Li, year 2022 and "Clinical-Longformer" in the title); R12 MIMIC-IV-Note (PhysioNet resource; its DOI is a DataCite DOI, which neither PubMed nor Crossref indexes, and DataCite is outside the allowed network list).

**Checks.** Every field in `verified_references.md` is copied from the efetch XML / Crossref JSON (see the `Trail` line per entry). The two repo entries that carried
DOI+PMID (Hagström, Rinella) resolved with both identifiers agreeing. Chapman/Harkema titles matched PubMed exactly after normalisation; their volume/issue/pages
agree with the repo strings. Quan 2005 was additionally constrained by volume 43 and first page 1130 from the repo string.

**Deviations.** (1) `requests` not installed → urllib (Tier 1). (2) Added a stopword-stripped title-word fallback because PubMed's quoted-phrase search failed for both
JBI titles (Tier 1). (3) Erratum exclusion in author-only queries (Tier 1; documented above). (4) Four "lower confidence" acceptances (author+year+journal/keywords with a
unique hit) are labelled as such in `verified_references.md`; if Kyle prefers a stricter policy, delete those four from the verified list — the unresolved trail for
each is in the JSON/raw responses.

**What Kyle should look at.** (a) The four lower-confidence entries (R06, R07, R11, R13). (b) R08: `docs/note_phenotype_spec.md` says "exact reference to be confirmed by
study team" — the single PubMed candidate is listed in `unresolved.md`; confirm or replace, then add author/title to the spec. (c) R09/R10: decide whether the paper versions
(ACL Anthology 2019 proceedings; Clinical-Longformer 2022) or the Hugging Face model cards are the intended citations, and add a full citation string to the docs so the
verifier can check it. (d) R12: cite MIMIC-IV-Note by its PhysioNet DOI from the resource page; not verifiable through PubMed/Crossref. (e) Appendix B, when recovered.

## 10.5 PhysioNet 403 email draft

**Purpose.** A short, plain email to contact@physionet.org about the failed command-line downloads.

**What was done.** Grepped `docs/`, `README.md`, `scripts/download_mimic.sh.broken` for 403/wget/curl/Basic/download. Wrote `docs/admin/physionet_403_email_draft.md`
(body 173 words, subject line, no credentials or names).

**Results / Deviations.** The repo's record is thinner than the brief's description: the only artefacts are `scripts/download_mimic.sh.broken` (curl with
credentials via a curl config on stdin — a pre-emptive Basic header — against `physionet.org/files/mimiciv/3.1/hosp/` and `physionet.org/files/mimic-iv-note/2.2/note/`,
`--fail --location`, SHA256SUMS verification) and a stale README line ("No data is downloaded — PhysioNet credentialing pending"). No file in the repo records the "403",
the "regardless of endpoint / user agent / credential format" observation, the missing-401-challenge diagnosis, that browser downloads worked, or that wget was unavailable.
The email follows the repo where it has a record and marks each brief-only statement `[confirm]` for Kyle to verify before sending. The checksum result in the email
(browser-downloaded files verify against SHA256SUMS) is supported by Phase 10.6 (12/12 match).

**What Kyle should look at.** Remove the `[confirm]` tags after checking each statement; add name; consider whether README line 13 should be updated (it is a tracked doc; not edited here).

## 10.6 Data inventory

**Purpose.** Enumerate every credentialed and derived data location on this machine for the DUA conversation.

**What was done.** Wrote `scripts/run0919_data_inventory.py` → `docs/run_2026-09-19/results/data_inventory.json` and `docs/admin/data_inventory.md`.
Covers `data/raw/**`, `data/processed/**`, `models/**`, `logs/run_2026-09-19/**`, `test files/`, `docs/tables/*`, the Hugging Face hub cache, `.venv`.
Names, sizes, git-tracked status, checksum status only. SHA-256 of each `.csv.gz` in `data/raw/` compared by file name against all five `SHA256SUMS*.txt` manifests
(parsed by the script; contents never displayed).

**Results.** `data/raw`: 18 files, 4.9 GB, 12 `.csv.gz` — **12 match / 0 mismatch / 0 not listed / 0 unreadable**; every file is listed in two manifests (the
project's subset manifest and the PhysioNet original) and both agree. 25 names in the original manifests are absent on disk (tables not downloaded — expected).
`data/processed`: 58 files, ~0.65 GB, all untracked (includes the 32-file citation scratch dir and inventory log). `models/`: empty. `logs/run_2026-09-19`: 16 files, 8 KB.
`test files/`: 46 files, 31 MB (open-access demo). `docs/tables`: 32 files (16 `.md` tracked, 16 `.csv` git-ignored). HF cache: one model dir
(`models--emilyalsentzer--Bio_ClinicalBERT`), 831 MB. `.venv`: 1.7 GB.

**Checks.** One digest (admissions.csv.gz) independently recomputed with `shasum -a 256` — identical. Hashing 4.9 GB took ~4 s (hardware SHA-256 on this
machine; not a skipped read — `hashed: true` and per-file digests are in the JSON). The Markdown was scanned for 6+-digit runs (none) so no id-like strings appear.

**Deviations.** HF cache sizing initially counted only symlinks (209 KB); fixed to resolve symlinks and count each blob once (Tier 1). The script's classification of
`logs/` follows `.gitignore` ("credentialed derivatives") even though the guardrails make logs aggregate-only; both statements are in the Markdown.

**What Kyle should look at.** The "listed but absent" names (confirm those tables are intentionally not downloaded); whether `docs/tables/*.csv` should be treated
as shareable aggregates or kept local; the scratch dir `data/processed/run_2026-09-19_scratch/` can be deleted after audit (it holds only API responses and the inventory log).
