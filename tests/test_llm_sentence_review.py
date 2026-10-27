"""Server-free checks for scripts/llm_sentence_review.py: deduplication keys, prompt building, reply
parsing, class probabilities, the output-location, cloud-model and manifest refusals, and resume
bookkeeping. Synthetic strings only."""
import json
import math
import os

import pandas as pd
import pytest
from scripts import llm_sentence_review as R


def test_key_ignores_case_and_whitespace_only():
    k = R.text_key("The liver is diffusely echogenic.")
    assert R.text_key("  THE LIVER   is diffusely\techogenic. ") == k
    assert R.text_key("The liver is not diffusely echogenic.") != k


def test_unit_key_includes_the_context_the_model_sees():
    row = {"text": "Increased echogenicity.", "note_type": "radiology_inpatient", "heading": "LIVER",
           "prev_text": "Normal size.", "next_text": ""}
    base = R.unit_key(row, R.VARIANTS["v3"][1])
    assert R.unit_key(dict(row, heading="SPLEEN"), R.VARIANTS["v3"][1]) != base
    assert R.unit_key(dict(row, prev_text="Other."), R.VARIANTS["v3"][1]) == base
    assert R.unit_key(dict(row, prev_text="Other."), R.VARIANTS["v3_context"][1]) != \
        R.unit_key(row, R.VARIANTS["v3_context"][1])


def test_prompt_shows_heading_and_neighbours_only_where_intended():
    row = {"text": "Increased echogenicity.", "note_type": "discharge", "heading": "LIVER",
           "prev_text": "Normal size.", "next_text": "No lesion."}
    p = R.build_prompt("v3", row)
    assert 'discharge summary under the heading "LIVER"' in p and "Normal size." not in p
    for v in R.VARIANTS:          # the fixed instructions come first, so the prompt cache can reuse them
        assert R.build_prompt(v, row).index("Increased echogenicity.") > len(R.build_prompt(v, row)) // 2
    assert "Before: Normal size." in R.build_prompt("v3_context", row)
    assert R.build_prompt("v3_fewshot", row).startswith("Examples (invented sentences)")


def test_parse_reply_is_strict_about_two_words():
    assert R.parse_reply("YES CURRENT") == ("YES", "CURRENT", True)
    assert R.parse_reply("no na.") == ("NO", "NA", True)
    assert R.parse_reply("UNCLEAR") == ("UNCLEAR", "UNPARSED", False)
    assert R.parse_reply("The answer is YES PAST") == ("YES", "PAST", False)
    assert R.parse_reply("Possibly") == ("UNPARSED", "UNPARSED", False)


def test_class_probs_from_first_token_alternatives():
    lp = [{"token": "UNC", "top_logprobs": [{"token": "UNC", "logprob": math.log(0.7)},
                                             {"token": "YES", "logprob": math.log(0.2)},
                                             {"token": " no", "logprob": math.log(0.05)},
                                             {"token": "**", "logprob": math.log(0.05)}]}]
    y, n, u = R.class_probs(lp)
    assert round(y, 3) == 0.2 and round(n, 3) == 0.05 and round(u, 3) == 0.7
    assert R.class_probs(None) == (None, None, None)


def test_cloud_models_are_refused_before_any_request():
    with pytest.raises(SystemExit):
        R.server_facts("http://localhost:1", "gemma4:cloud")


def test_out_must_be_under_data_or_outside_the_repo(tmp_path):
    with pytest.raises(SystemExit):
        R.check_out(os.path.join(R.REPO, "docs", "llm_out"))
    R.check_out(os.path.join(R.REPO, "data", "processed", "llm_out"))
    R.check_out(str(tmp_path))


def test_manifest_refuses_a_different_model_digest_or_ollama_version(tmp_path):
    first = {k: "a" for k in R.CHECKED}
    R.open_manifest(str(tmp_path), first)
    assert R.open_manifest(str(tmp_path), dict(first, created_utc="later")) is not None
    for k in ("model_digest", "ollama_version"):
        with pytest.raises(SystemExit):
            R.open_manifest(str(tmp_path), dict(first, **{k: "b"}))
    assert json.load(open(tmp_path / "manifest.json"))["model_digest"] == "a"


def test_resume_keeps_the_latest_answer_per_key(tmp_path):
    sh = tmp_path / "shards"
    sh.mkdir()
    row = lambda k, ans, err: {"key": k, "answer": ans, "reply": None, "error": err, "seconds": None}
    pd.DataFrame([row("k1", None, "TimeoutError"), row("k2", "NO", None)]).to_parquet(sh / "answers_00000.parquet")
    pd.DataFrame([row("k1", "YES", None)]).to_parquet(sh / "answers_00003.parquet")
    latest, nxt = R.load_answers(str(tmp_path))
    assert nxt == 4
    assert dict(zip(latest.key, latest.answer)) == {"k1": "YES", "k2": "NO"}
    assert latest.error.isna().all()


def test_unreachable_server_stops_instead_of_recording():
    with pytest.raises(R.ServerDown):
        R.ask("http://localhost:1", "any-model", "invented sentence")


def test_v4_adds_only_the_alcohol_rule():
    row = {"text": "Alcoholic cirrhosis.", "note_type": "discharge", "heading": ""}
    v3, v4 = R.build_prompt("v3", row), R.build_prompt("v4", row)
    assert "alcoholic hepatitis" in v4 and "alcoholic hepatitis" not in v3
    assert v4.replace(" " + R.ALCOHOL_RULE, "") == v3
    assert R.VARIANTS["v4"][1] == R.VARIANTS["v3"][1]      # same unit keys, so v3 answers map onto v4 units
