"""Push gate (scripts/run1110_push_gate.py): every check, on synthetic fixtures only.

No test reads data/. Identifier-shaped and note-shaped strings are built at run time from invented
pieces, so this file itself holds nothing the gate would flag.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.getcwd())
from scripts import run1110_push_gate as G

FAKE_ID = "2" + "7" * 7                       # invented; shaped like an admission identifier
FAKE_SEED = "2026" + "0101"
MARK = "_" * 3                                # the de-identification mark, built here on purpose
SENTENCE = "the zorblax gland shows violet lattice flux across every quadrant today"
HEADING = "zorblax gland lattice survey"      # four invented words
CORPUS = "\n".join([SENTENCE, "another invented line about the quux organ", HEADING]).encode()


def changes(path, lines, status="A", removed=(), binary=False):
    return {path: {"added": list(enumerate(lines, 1)), "removed": list(removed), "binary": binary, "status": status}}


def note(lines, public="", headings=(), terms=(), path="docs/x.md", lexicon=None):
    found, stats = G.check_note_text(changes(path, lines), CORPUS, set(headings), public, terms=terms, lexicon=lexicon)
    return found, stats


# ----------------------------------------------------------------------------- diff parsing
def test_parse_diff_reads_added_lines_with_numbers_and_binary_files():
    diff = "\n".join([
        "diff --git a/docs/a.md b/docs/a.md", "--- a/docs/a.md", "+++ b/docs/a.md",
        "@@ -3,0 +4,2 @@", "+first new", "+second new", "@@ -9 +11 @@", "-old", "+changed",
        "diff --git a/x.bin b/x.bin", "Binary files a/x.bin and b/x.bin differ"])
    d = G.parse_diff(diff)
    assert d["docs/a.md"]["added"] == [(4, "first new"), (5, "second new"), (11, "changed")]
    assert d["docs/a.md"]["removed"] == ["old"]
    assert d["x.bin"]["binary"] is True


# ----------------------------------------------------------------------------- (a) (b)
def test_a_paths_under_data_models_logs_fail():
    bad = G.check_paths(["data/processed/x.json", "models/m.txt", "logs/run.log", "docs/ok.md", "scripts/data_tool.py"])
    assert [b["file"] for b in bad] == ["data/processed/x.json", "logs/run.log", "models/m.txt"]


def test_b_new_tabular_file_and_binary_content_fail_text_passes():
    ch = {}
    ch.update(changes("diagnostics/t.csv", ["a,b"]))
    ch.update(changes("docs/t.parquet", [], binary=True))
    ch.update(changes("docs/fig.png", [], status="M", binary=True))
    ch.update(changes("docs/ok.md", ["fine"]))
    bad = {b["file"]: b["problem"] for b in G.check_filetypes(ch)}
    assert set(bad) == {"diagnostics/t.csv", "docs/t.parquet", "docs/fig.png"}
    assert bad["docs/fig.png"] == "binary content"


# ----------------------------------------------------------------------------- (c)
def test_c_real_identifier_fails_and_is_not_echoed():
    bad, stats = G.check_ids(changes("docs/x.md", [f"admission {FAKE_ID} was odd"]), {FAKE_ID}, set())
    assert bad == [{"file": "docs/x.md", "line": 1}]
    assert FAKE_ID not in json.dumps(bad)


def test_c_seed_byte_count_and_citation_are_exempt_and_unknown_numbers_pass():
    lines = [f"seed {FAKE_SEED}", f'"bytes": {FAKE_ID},', f"PMID {FAKE_ID}", "count 20000001"]
    bad, stats = G.check_ids(changes("docs/x.md", lines), {FAKE_ID, FAKE_SEED}, {FAKE_SEED})
    assert bad == []
    assert stats["equal_to_an_id_but_exempt"] == 3 and stats["eight_digit_tokens"] == 4


# ----------------------------------------------------------------------------- (d)
def test_d1_deid_mark_fails_unless_the_line_is_about_deidentification():
    found, _ = note([f"seen by Dr. {MARK} on the ward", f"the de-identification placeholder is {MARK}"])
    assert found["d1_deid_marks"] == [{"file": "docs/x.md", "line": 1}]


def test_d2_report_header_with_a_lexicon_match_fails():
    lex = [re.compile("steatosis", re.I)]
    header = "IMPRESSION" + ":"                # joined here so this file holds no header-plus-lexicon line
    found, _ = note([f"{header} mild steatosis", f"{header} nothing", "about steatosis in general"], lexicon=lex)
    assert found["d2_report_headers"] == [{"file": "docs/x.md", "line": 1}]


def test_d3_thirty_character_window_of_a_sentence_fails_and_twenty_nine_passes():
    w30, w29 = SENTENCE[5:35], SENTENCE[5:34]
    found, _ = note([f"He wrote: {w30.upper()}!", f"he wrote: {w29}#", "nothing in common with the corpus at all here"])
    assert [f["line"] for f in found["d3_sentence_windows"]] == [1]
    assert found["d3_sentence_windows"][0]["longest_match_chars"] == 30
    assert SENTENCE[5:35] not in json.dumps(found)


def test_d3_reports_the_longest_match_and_ignores_whitespace_and_case():
    found, _ = note(["  " + SENTENCE.replace(" ", "   ").title()])
    assert found["d3_sentence_windows"][0]["longest_match_chars"] == len(SENTENCE)


def test_d3_exemptions_public_text_fixture_marker_and_terminology():
    line = f"quoted: {SENTENCE}"
    assert note([line], public=SENTENCE)[0]["d3_sentence_windows"] == []
    assert note([line + "  # audit-fixture"])[0]["d3_sentence_windows"] == []
    assert note([line], terms=(SENTENCE,))[0]["d3_sentence_windows"] == []
    # a term exempts only matches lying wholly inside it
    assert len(note([line], terms=(SENTENCE[:40],))[0]["d3_sentence_windows"]) == 1


def test_d4_private_heading_of_four_words_fails_three_words_never_loaded():
    found, _ = note([f"under the heading {HEADING.upper()}:", "zorblax gland lattice only"], headings={HEADING})
    assert found["d4_private_headings"] == [{"file": "docs/x.md", "line": 1}]
    found, stats = note([f"under {HEADING}"], headings={HEADING}, public=f"x {HEADING} y")
    assert found["d4_private_headings"] == [] and stats["d4_exempt_public"] == 1


def test_d4_heading_must_end_at_a_word_boundary():
    found, _ = note([f"{HEADING}s are plural"], headings={HEADING})
    assert found["d4_private_headings"] == []


# ----------------------------------------------------------------------------- (e)
def test_e_small_count_in_a_markdown_count_column_fails_only_on_added_lines():
    md = "\n".join(["| stratum | n | share |", "| --- | --: | --: |", "| a | 7 | 50% |", "| b | <11 | 5% |",
                    "| c | 4 | 9% |", "| d | 1,204 | 3% |"])
    bad = G.check_small_counts("docs/t.md", md, {3, 4, 6})
    assert [(b["line"], b["column"]) for b in bad] == [(3, "n")]


def test_e_small_count_in_a_count_like_json_key_fails_and_non_patient_keys_pass():
    js = "\n".join(['{', ' "n_admissions": 4,', ' "subjects": 12,', ' "n_files": 3,', ' "checks": 7,', ' "units": "<11"', '}'])
    bad = G.check_small_counts("docs/r.json", js, set(range(1, 8)))
    assert [(b["line"], b["key"]) for b in bad] == [(2, "n_admissions")]


# ----------------------------------------------------------------------------- (f) (g)
def test_f_config_deletion_fails_and_pure_addition_passes():
    assert G.check_config(changes("scripts/masld_config.py", ["NEW = 1"], status="M")) == []
    bad = G.check_config(changes("scripts/masld_config.py", ["X = 2"], status="M", removed=["X = 1"]))
    assert bad and bad[0]["removed_or_changed_lines"] == 1


def test_g_changed_or_missing_frozen_file_fails(tmp_path):
    f = tmp_path / "frozen.txt"
    f.write_text("locked content")
    start = {"frozen": {str(f): {"sha256": G.sha(str(f))}}, "locked": {str(tmp_path / "gone.bin"): {"sha256": "0" * 64}}}
    assert [d["problem"] for d in G.check_frozen(start)] == ["missing"]
    f.write_text("tampered")
    assert sorted(d["problem"] for d in G.check_frozen(start)) == ["hash changed", "missing"]
