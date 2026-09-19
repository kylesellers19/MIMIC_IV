# Blockers — run_2026-09-19

Each entry: what failed · what was tried (max three attempts / 20 minutes) · what was skipped as a result.

## B-01 · Run file truncated in transmission (Appendix A tail and all of Appendix B missing)
- **What failed.** The launch message was cut at the 50,000-character limit in the middle of Appendix A §3 ("Liver biopsy reporting s…"). Appendix B (the citation list) was never received.
- **What was tried.** Nothing can recover it from here. Appendix A is unaffected in practice: Phase 0.4 found the identical Draft 1 already stored in `docs/adjudication_criteria.md` (with the collated D1–D8 table), so Phase 1.2 was skipped as verified-existing.
- **What was skipped / changed.** Phase 10.4 builds `docs/references/registry.yaml` from the citation strings present in the repository's own docs and script docstrings instead of from Appendix B. Kyle should diff that registry against Appendix B and add any missing entries; `scripts/verify_citations.py` can then be re-run.

## B-02 · LightGBM / XGBoost could not load libomp
- **What failed.** Both wheels link `@rpath/libomp.dylib`, absent system-wide; Homebrew installs are forbidden.
- **What was tried.** (1) ctypes preload of the torch-bundled libomp — dyld still fails on rpath resolution. (2) `DYLD_LIBRARY_PATH` pointing at `.venv/.../torch/lib` — works. Adopted via `scripts/run0919_env.sh`.
- **Skipped.** Nothing.

## B-03 · MPS unavailable
- **What failed.** torch 2.11 reports MPS built but not available on macOS 13.3.1.
- **What was tried.** Checked `is_built()`/`is_available()`; no fix without a macOS or torch change (a torch downgrade is not on the allow-list path and was not attempted).
- **Skipped / changed.** Embedding runs on CPU (8 threads). The pilot showed the 5-hour budget still covers ~33k admissions, so the transformer arm proceeds at that size instead of the 60k ceiling.
