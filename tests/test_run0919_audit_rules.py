"""Negative controls for the release audit's leak detectors (run_2026-09-19 Phase 11.3).

The audit must FIRE on text that looks like a clinical note and must NOT fire on the study's own
prose. These tests use synthetic strings only — no patient data, and nothing copied from the corpus.
"""
import re
import pytest
from scripts.run0919_final_audit import DEID, REPORT_HEADER, TALKS_ABOUT_DEID, SIZE_KEY, EIGHT_DIGIT, SEED_LITERAL


# --- must fire on note-like text -------------------------------------------------------------
def test_deid_placeholder_is_detected():
    assert DEID.search("Patient seen on ___ with abdominal pain.")
    assert DEID.search("Dr. ___ signed the report.")


def test_report_headers_are_detected():
    for h in ["FINDINGS:", "IMPRESSION:", "TECHNIQUE:", "COMPARISON:", "INDICATION:",
              "EXAMINATION:", "History of Present Illness:", "Brief Hospital Course:"]:
        assert REPORT_HEADER.search(h + " something"), h


def test_a_pasted_radiology_span_trips_at_least_one_fingerprint():
    span = "IMPRESSION: Diffuse hepatic steatosis. Comparison ___ shows no change."
    assert REPORT_HEADER.search(span) and DEID.search(span)


def test_eight_digit_identifier_shape_is_detected():
    assert EIGHT_DIGIT.search("subject 10004235 admitted")
    assert EIGHT_DIGIT.search("hadm 29079034")


# --- must NOT fire on the study's own prose ---------------------------------------------------
def test_prose_about_deidentification_is_not_a_finding():
    line = "MIMIC-IV-Note replaces every removed identifier with a de-identification placeholder."
    assert TALKS_ABOUT_DEID.search(line)


def test_manuscript_sentence_about_steatosis_has_no_note_fingerprint():
    line = ("Among admissions adjudicated as having documented hepatic steatosis, the "
            "population-weighted proportion carrying no MASLD diagnosis code was [PENDING].")
    assert not DEID.search(line)
    assert not REPORT_HEADER.search(line)


def test_prose_naming_a_section_without_quoting_one_is_not_flagged_as_a_header_block():
    """The header regex may match prose, but check (d) only counts it inside a quoted block
    that also contains a lexicon match; this asserts the regex alone is not the whole rule."""
    line = "Reading order prioritises the impression of each radiology report."
    assert not REPORT_HEADER.search(line)     # no colon, so not a header


# --- exemption rules must be narrow ------------------------------------------------------------
def test_size_key_exemption_only_covers_size_valued_fields():
    assert SIZE_KEY.search('  "bytes": 19928140,')
    assert SIZE_KEY.search('  "file_bytes_total": 10734498')
    assert SIZE_KEY.search('  "n_chars": 12345678')
    assert not SIZE_KEY.search('  "subject_id": 10004235')
    assert not SIZE_KEY.search('  "hadm_id": 29079034')


def test_seed_literal_exemption_matches_only_seed_usage():
    assert SEED_LITERAL.findall("rng = np.random.default_rng(20260919)") == ["20260919"]
    assert SEED_LITERAL.findall("SEED_SPLIT = 20260920") == ["20260920"]
    assert SEED_LITERAL.findall("random_state=20260921") == ["20260921"]
    assert SEED_LITERAL.findall("subject_id = 10004235") == []
