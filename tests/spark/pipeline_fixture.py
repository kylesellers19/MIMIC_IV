"""The whole Spark pipeline on the invented hospital (cohort_fixture.py), for the Step 3-6 tests.

build_through_cohort(): ingest dirs written straight from the fixture frames, then Step 2 (fast; Steps 3-4 tests).
build_full():           invented .csv.gz files and a manifest -> Step 1 ingest -> Steps 2, 4, 3 (Steps 5-6 tests).
"""
import json

import pyarrow as pa
import pyarrow.parquet as pq

from masld_spark import cohort as CO
from masld_spark import config as C
from masld_spark import definitions as D
from masld_spark import ingest as ING
from masld_spark import notes as NO
from masld_spark import splits as SP
from masld_spark.fingerprint import manifests, sha256_file
from masld_spark.ingest import OK_JSON
from masld_spark.runlog import RunLog
from masld_spark.schemas import TABLES

import cohort_fixture as FX
import synthetic as SY

# subject -> (partition, fold): 101 DEV fold 0 (adm 2001), 102 TEST (2003), 103 GOLD_HOLDOUT (2004)
SPLIT_ROWS = [(2001, 101, "DEV", 0), (2003, 102, "TEST", None), (2004, 103, "GOLD_HOLDOUT", None)]
# Frozen rule on the fixture texts: 2001 positive via outpatient radiology at -365 d (definition b, not c);
# 2003's inpatient report is negated; 2004's discharge diagnosis is Tier A.
REF_SPLITS = {
    "partitions": {"GOLD_HOLDOUT": {"admissions": 1, "subjects": 1, "code_positive": 0, "note_positive": 1},
                   "TEST": {"admissions": 1, "subjects": 1, "code_positive": 1, "note_positive": 0},
                   "DEV": {"admissions": 1, "subjects": 1, "code_positive": 1, "note_positive": 1}},
    "dev_folds": {"0": {"admissions": 1, "subjects": 1, "note_positive": 1},
                  **{str(k): {"admissions": 0, "subjects": 0, "note_positive": 0} for k in range(1, 5)}},
}
REF_CELLS = {"analyses": {"primary_first_result": {"A": {"admissions": 1}, "B": {"admissions": 1},
                                                   "C": {"admissions": 1}, "D": {"admissions": 0}}}}


def tiny_tokenizer(path):
    from transformers import BertTokenizerFast
    words = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "discharge", "diagnosis", "diffuse", "fatty", "liver",
             "brief", "hospital", "course", "findings", "no", "hepatic", "steatosis", "impression", "normal",
             "study", "invented", "synthetic", "note", ":", ".", "[", "]", "mask"]
    path.mkdir(parents=True, exist_ok=True)
    (path / "vocab.txt").write_text("\n".join(words) + "\n")
    BertTokenizerFast(vocab_file=str(path / "vocab.txt"), do_lower_case=True).save_pretrained(str(path))
    return str(path)


def _rows(drop_mismatch):
    rows = {t: list(r) for t, r in FX.TABLE_ROWS.items()}
    if drop_mismatch:
        rows["discharge"] = [r for r in rows["discharge"] if r["note_id"] != "999-DS-1"]
    for t in TABLES:
        rows.setdefault(t, [])
    return rows


def _write_splits(root, split_rows, sha_override=None):
    src = root / "splits_v1.parquet"
    pq.write_table(pa.table({"hadm_id": pa.array([r[0] for r in split_rows], pa.int64()),
                             "subject_id": pa.array([r[1] for r in split_rows], pa.int64()),
                             "partition": [r[2] for r in split_rows],
                             "fold": pa.array([r[3] for r in split_rows], pa.int64())}), src)
    hashes = root / "frozen_hashes.json"
    hashes.write_text(json.dumps({"frozen": {str(src): {"sha256": sha_override or sha256_file(src)}}}))
    (root / "phase2.json").write_text(json.dumps(REF_SPLITS))
    (root / "cells.json").write_text(json.dumps(REF_CELLS))
    return src, hashes


def make_config(root, rows, sha_override=None, split_rows=SPLIT_ROWS):
    cfg = SY.make_cfg(root, expected={t: len(r) for t, r in rows.items()})
    ref = dict(FX.REFERENCE)
    cfg["cohort"] = {"partitions": {}, "reference": ref}
    src, hashes = _write_splits(root, split_rows, sha_override)
    cfg["splits"] = {"source": str(src), "frozen_hashes": str(hashes), "frozen_key": str(src),
                     "reference": str(root / "phase2.json")}
    tok = tiny_tokenizer(root / "tok")
    cfg["notes"] = {"arrow_batch_rows": 2, "variants": ["U", "M", "S"], "max_chunks": None,
                    "files": {"notes": 2, "token_counts": 2, "chunks_tiny": 2},
                    "tokenizers": {"tiny": {"name": tok, "revision": None, "chunk": {"window": 8, "stride": 2}},
                                   "tiny_counts": {"name": tok, "revision": None, "chunk": None}},
                    "reference": {"splits": str(root / "phase2.json"), "cells": str(root / "cells.json")}}
    cfg["gates"] = {"max_orphan_pct": 60.0}        # one of two hadm-linked radiology reports points nowhere (777-RR-1)
    cfg["parity"] = {"frozen_hashes": str(hashes)}
    return C.check(cfg)


def build_through_cohort(spark, root, monkeypatch, drop_mismatch=True, **kw):
    monkeypatch.setattr(D, "CLEAN_N_EXPECT", 3)
    rows = _rows(drop_mismatch)
    cfg = make_config(root, rows, **kw)
    out = C.paths(cfg)["out_root"] / "ingest"
    for t, df in FX.frames(spark).items():
        if t == "discharge" and drop_mismatch:
            df = df.where("note_id != '999-DS-1'")
        df.write.mode("overwrite").parquet(str(out / t))
        (out / t / OK_JSON).write_text("{}")
    assert CO.run_cohort(spark, cfg, RunLog(root / "runs", "cohort", "cohort", cfg)) == CO.EXIT_OK
    return cfg


def build_full(spark, root, clean_n_expect_patch):
    """Steps 1, 2, 4, 3 from invented CSV files. clean_n_expect_patch: a context that sets D.CLEAN_N_EXPECT = 3."""
    rows = _rows(drop_mismatch=True)
    cfg = make_config(root, rows)
    raw = C.paths(cfg)["raw_root"]
    files = [SY.write_csv_gz(raw / TABLES[t][0] / f"{t}.csv.gz", t, rows[t]) for t in TABLES]
    SY.write_manifest(raw, files)
    log = RunLog(root / "runs", "ingest", "ingest", cfg)
    _, listed = manifests(raw)
    for t in TABLES:
        assert ING.ingest_table(spark, cfg, t, log, listed)["status"] == "PASS", t
    clean_n_expect_patch.setattr(D, "CLEAN_N_EXPECT", 3)
    for name, fn, code in (("cohort", CO.run_cohort, CO.EXIT_OK), ("splits", SP.run_splits, SP.EXIT_OK),
                           ("notes", NO.run_notes, NO.EXIT_OK)):
        lg = RunLog(root / "runs", name, name, cfg)
        assert fn(spark, cfg, lg) == code, name
        lg.finish("PASS", 0)
    log.finish("PASS", 0)
    return cfg
