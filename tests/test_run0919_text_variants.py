"""Tests for the Phase 3 text-variant construction (run_2026-09-19).

Synthetic strings only — no patient data. The lexicon and sentence splitter are imported from the
frozen rule; these tests check the masking/deletion wrappers, not the rule itself.
"""
import pytest
from scripts.run0919_notes_text import mask_spans, delete_sentences, sections, dc_extract, rad_impression, MASK
from scripts.note_phenotype import classify_note


def test_mask_replaces_every_lexicon_match_regardless_of_assertion():
    affirmed = "Findings compatible with hepatic steatosis."
    negated = "No evidence of hepatic steatosis."
    hedged = "May represent hepatic steatosis."
    for t in (affirmed, negated, hedged):
        assert MASK in mask_spans(t), t
        assert "steatosis" not in mask_spans(t).lower()


def test_masking_is_not_assertion_aware_so_the_mask_cannot_encode_the_label():
    """If only affirmed mentions were masked, the mask itself would encode the label."""
    a = mask_spans("Findings compatible with hepatic steatosis.")
    n = mask_spans("No evidence of hepatic steatosis.")
    assert a.count(MASK) == n.count(MASK) == 1


def test_sentence_deletion_removes_the_bearing_sentence_and_keeps_the_rest():
    txt = "The kidneys are unremarkable. There is hepatic steatosis. No focal lesion."
    out = delete_sentences(txt)
    assert "kidneys are unremarkable" in out
    assert "No focal lesion" in out
    assert "steatosis" not in out.lower()


def test_sentence_deletion_ignores_assertion_status():
    assert "steatosis" not in delete_sentences("No evidence of hepatic steatosis.").lower()
    assert "steatosis" not in delete_sentences("Cannot exclude hepatic steatosis.").lower()


def test_deleted_text_no_longer_fires_the_frozen_rule():
    txt = "Liver shows diffuse fatty infiltration of the liver. Spleen normal."
    assert classify_note(txt)["a_pos"] is True
    assert classify_note(delete_sentences(txt))["a_pos"] is False


def test_masked_text_no_longer_fires_the_frozen_rule():
    txt = "Findings consistent with hepatic steatosis."
    assert classify_note(txt)["a_pos"] is True
    assert classify_note(mask_spans(txt))["a_pos"] is False


def test_non_lexicon_sentences_survive_both_variants():
    txt = "Patient reports abdominal pain. Alkaline phosphatase is elevated."
    assert delete_sentences(txt).strip() != ""
    assert MASK not in mask_spans(txt)
    assert "abdominal pain" in delete_sentences(txt)


def test_section_parser_splits_on_line_initial_labels():
    txt = "History of Present Illness:\nPatient with pain.\n\nPertinent Results:\nSodium 140.\n"
    labs = [lab for lab, _ in sections(txt)]
    assert "HISTORY OF PRESENT ILLNESS" in labs
    assert "PERTINENT RESULTS" in labs


def test_section_parser_returns_whole_body_when_no_headers():
    out = sections("Free text with no headers at all")
    assert len(out) == 1 and out[0][0] == "BODY"


def test_dc_extract_puts_priority_sections_first_and_drops_boilerplate():
    txt = ("Name:\nRedacted\n\nAllergies:\nNone\n\nDischarge Instructions:\nTake meds\n\n"
           "Brief Hospital Course:\nUneventful.\n\nDischarge Diagnosis:\nFatty liver\n")
    parts = dc_extract(txt)
    joined = "\n".join(parts)
    assert parts[0].startswith("Discharge Diagnosis")          # highest priority first
    assert "Brief Hospital Course" in joined
    assert "Discharge Instructions" not in joined              # boilerplate skipped
    assert "Allergies" not in joined


def test_rad_impression_prefers_the_impression_section():
    txt = "FINDINGS: lots of detail here.\nIMPRESSION: Hepatic steatosis."
    assert rad_impression(txt).startswith("IMPRESSION")


def test_rad_impression_falls_back_to_the_tail_when_absent():
    txt = "x" * 1000
    assert len(rad_impression(txt)) == 600
