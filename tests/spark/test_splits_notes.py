"""Steps 4 (splits) and 3 (notes) on the invented hospital: cohort -> splits -> notes, plus one test per failure."""
import ast
import json

import pytest
import yaml

from masld_spark import cohort as CO
from masld_spark import config as C
from masld_spark import definitions as D
from masld_spark import notes as NO
from masld_spark import splits as SP
from masld_spark.runlog import RunLog

import cohort_fixture as FX
import pipeline_fixture as PF

TEXT_FRAGMENTS = ["fatty liver", "hepatic steatosis", "Invented", "CT ABDOMEN", "Synthetic note"]


def setup(spark, tmp_path, monkeypatch, split_rows=PF.SPLIT_ROWS, drop_mismatch=True, sha_override=None):
    return PF.build_through_cohort(spark, tmp_path, monkeypatch, drop_mismatch=drop_mismatch,
                                   split_rows=split_rows, sha_override=sha_override)


def log_for(tmp_path, cfg, name):
    return RunLog(tmp_path / "runs", name, name, cfg)


# ---------------------------------------------------------------- Step 4
def test_splits_pass_and_copy(spark, tmp_path, monkeypatch):
    cfg = setup(spark, tmp_path, monkeypatch)
    log = log_for(tmp_path, cfg, "splits")
    assert SP.run_splits(spark, cfg, log) == SP.EXIT_OK
    assert all(c["pass"] for c in log.data["checks"])
    out = C.paths(cfg)["out_root"] / "splits"
    assert (out / CO.STAGE_OK).exists()
    subj = {r.subject_id: (r.partition, r.fold) for r in spark.read.parquet(str(out / "subject_splits")).collect()}
    assert subj == {101: ("DEV", 0), 102: ("TEST", None), 103: ("GOLD_HOLDOUT", None)}


def test_splits_stop_on_hash_mismatch_before_reading(spark, tmp_path, monkeypatch):
    cfg = setup(spark, tmp_path, monkeypatch, sha_override="0" * 64)
    with pytest.raises(SP.StageFailure, match="recorded SHA-256"):
        SP.run_splits(spark, cfg, log_for(tmp_path, cfg, "splits"))
    assert not (C.paths(cfg)["out_root"] / "splits" / "admission_splits").exists()


@pytest.mark.parametrize("rows,failing", [
    ([(2001, 101, "DEV", 0), (2003, 102, "TEST", None)], "population admissions without a split"),
    ([(2001, 101, "DEV", 0), (2003, 102, "TEST", None), (2004, 103, "DEV", None)], "DEV rows with fold outside 0-4"),
    ([(2001, 101, "DEV", 0), (2003, 101, "TEST", None), (2004, 103, "GOLD_HOLDOUT", None)], "admissions whose split subject differs"),
])
def test_splits_fail_without_marker(spark, tmp_path, monkeypatch, rows, failing):
    cfg = setup(spark, tmp_path, monkeypatch, split_rows=rows)
    log = log_for(tmp_path, cfg, "splits")
    assert SP.run_splits(spark, cfg, log) == SP.EXIT_FAIL
    assert not next(c for c in log.data["checks"] if c["check"] == failing)["pass"]
    assert not (C.paths(cfg)["out_root"] / "splits" / CO.STAGE_OK).exists()


# ---------------------------------------------------------------- Step 3
def test_chunk_matches_run0919_embed_chunk_ids():
    src = (D.ROOT / "scripts/run0919_embed.py").read_text()
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "chunk_ids")
    for window, stride, cap in [(512, 64, 12), (8, 2, 10**9), (10, 0, 3)]:
        ns = {"MAX_LEN": window, "STRIDE": stride, "MAX_CHUNKS": cap}
        exec(ast.get_source_segment(src, fn), ns)    # the original function, unchanged

        class Stub:
            cls_token_id, sep_token_id = 101, 102

            def __init__(self, ids):
                self.ids = ids

            def __call__(self, text, **kw):
                return {"input_ids": self.ids}
        for length in [0, 1, 5, 6, 7, 13, 100, 2000, 6143]:
            ids = list(range(1000, 1000 + length))
            want, _ = ns["chunk_ids"](Stub(ids), "x")
            assert NO.chunk(ids, 101, 102, window, stride, cap) == want, (window, stride, length)


def test_notes_end_to_end(spark, tmp_path, monkeypatch, capsys):
    cfg = setup(spark, tmp_path, monkeypatch)
    assert SP.run_splits(spark, cfg, log_for(tmp_path, cfg, "splits")) == SP.EXIT_OK
    conf = tmp_path / "conf.yaml"
    conf.write_text(yaml.safe_dump({k: v for k, v in cfg.items() if k != "_source"}))
    capsys.readouterr()
    code = NO.main(["--config", str(conf), "--run-name", "notes"], spark=spark)
    out = capsys.readouterr().out
    assert code == NO.EXIT_OK, out
    for frag in TEXT_FRAGMENTS + FX.VALUE_FRAGMENTS:
        assert frag not in out, frag
    root = C.paths(cfg)["out_root"] / "notes"
    assert (root / CO.STAGE_OK).exists()
    assert sorted(p.name for p in (root / "notes").iterdir() if p.is_dir()) == \
        ["partition=DEV", "partition=GOLD_HOLDOUT", "partition=NONE", "partition=TEST"]

    notes = {r.note_id: r.asDict(recursive=True) for r in spark.read.parquet(str(root / "notes")).collect()}
    assert len(notes) == 10
    assert notes["103-DS-1"]["a_pos"] and notes["101-RR-a"]["a_pos"] and not notes["102-RR-1"]["a_pos"]
    assert notes["102-RR-1"]["n_neg"] == 1 and notes["102-RR-1"]["liver_incl"] is True
    assert notes["101-RR-a"]["liver_incl"] is False and notes["103-DS-1"]["liver_incl"] is None
    assert [s["label"] for s in notes["103-DS-1"]["sections"]] == ["DISCHARGE DIAGNOSIS", "BRIEF HOSPITAL COURSE"]
    assert [s["category"] for s in notes["102-RR-1"]["sections"]] == ["findings", "impression"]
    s0 = notes["102-RR-1"]["sections"][1]
    assert FX.TEXTS["102-RR-1"][s0["start"]:s0["end"]].startswith("IMPRESSION:")
    assert notes["101-RR-b"]["partition"] == "DEV" and not notes["101-RR-b"]["in_population"]
    assert notes["104-RR-a"]["partition"] == "NONE"
    assert notes["101-DS-1"]["charttime"].year == 2150                     # timestamps survive the Python workers

    labels = {r.hadm_id: r.asDict() for r in spark.read.parquet(str(root / "labels_rule")).collect()}
    assert (labels[2001]["note_a"], labels[2001]["note_b"], labels[2001]["note_c"]) == (False, True, False)
    assert labels[2004]["note_a"] and labels[2004]["cell"] == "B" and labels[2003]["cell"] == "C"
    assert labels[2001]["partition"] == "DEV" and labels[2001]["fold"] == 0

    tc = spark.read.parquet(str(root / "token_counts"))
    assert tc.count() == 6 * 3
    by = {(r.note_id, r.variant): r for r in tc.collect()}
    assert by[("103-DS-1", "M")].n_tokens_tiny == by[("103-DS-1", "M")].n_tokens_tiny_counts
    assert by[("103-DS-1", "S")].n_tokens_tiny < by[("103-DS-1", "U")].n_tokens_tiny   # the trigger sentence is gone
    ch = spark.read.parquet(str(root / "chunks_tiny"))
    rows = [r for r in ch.collect() if r.note_id == "103-DS-1" and r.variant == "U"]
    assert {r.n_chunks for r in rows} == {len(rows)} and all(r.input_ids[0] == 2 and r.input_ids[-1] == 3 for r in rows)
    assert all(len(r.input_ids) <= 8 for r in ch.collect())
    assert {r.partition for r in ch.collect()} == {"DEV", "TEST", "GOLD_HOLDOUT"}
    run = json.loads((tmp_path / "runs" / "notes" / "run.json").read_text())
    assert set(run["tokenizers"]) == {"tiny", "tiny_counts"} and "vocab.txt" in run["tokenizers"]["tiny"]["files"]


def test_notes_flag_a_linked_note_stored_under_another_partition(spark, tmp_path, monkeypatch):
    cfg = setup(spark, tmp_path, monkeypatch, drop_mismatch=False)   # 999-DS-1: subject 999, admission of 101
    assert SP.run_splits(spark, cfg, log_for(tmp_path, cfg, "splits")) == SP.EXIT_OK
    log = log_for(tmp_path, cfg, "notes")
    assert NO.run_notes(spark, cfg, log) == NO.EXIT_FAIL
    bad = next(c for c in log.data["checks"] if c["check"] == "linked notes stored under another partition")
    assert bad["value"] == 1 and not bad["pass"]


def test_notes_require_passed_splits(spark, tmp_path, monkeypatch):
    cfg = setup(spark, tmp_path, monkeypatch)
    with pytest.raises(NO.StageFailure, match="splits"):
        NO.run_notes(spark, cfg, log_for(tmp_path, cfg, "notes"))
