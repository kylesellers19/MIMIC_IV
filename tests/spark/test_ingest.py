"""Step 1 (ingest) on synthetic fixtures: multi-line quoted notes, a duplicate note, types, gates, partitioning."""
import csv
import datetime as dt
import json
import shutil

import pyarrow.parquet as pq
import pytest
import yaml

from masld_spark import ingest as ING
from masld_spark.fingerprint import manifests, sha256_file
from masld_spark.runlog import RunLog, n
from masld_spark.schemas import SCHEMAS, TABLES, column_names
from pyspark.sql.types import LongType, TimestampNTZType

import synthetic as SY

_runs = iter(range(10_000))


def run_one(spark, cfg, table, **kw):
    log = RunLog(ING.C.paths(cfg)["runs_root"], f"t{next(_runs)}", "ingest", cfg)
    _, listed = manifests(ING.C.paths(cfg)["raw_root"])
    return ING.ingest_table(spark, cfg, table, log, listed, **kw), log


def setup_table(tmp_path, table, rows, quoting=csv.QUOTE_MINIMAL, **cfg_kw):
    cfg = SY.make_cfg(tmp_path, **cfg_kw)
    raw = ING.C.paths(cfg)["raw_root"]
    f = SY.write_csv_gz(raw / TABLES[table][0] / f"{table}.csv.gz", table, rows, quoting=quoting)
    SY.write_manifest(raw, [f])
    return cfg, f


def out_dir(cfg, table):
    return ING.C.paths(cfg)["out_root"] / "ingest" / table


def read_rows(spark, cfg, table):
    return spark.read.parquet(str(out_dir(cfg, table))).collect()


# ---------------------------------------------------------------- schemas
def test_schemas_cover_every_table_with_unique_columns():
    assert set(SCHEMAS) == set(TABLES) and len(TABLES) == 12
    for t, s in SCHEMAS.items():
        names = column_names(t)
        assert len(names) == len(set(names)), t
        for f in s.fields:
            if f.name in ("subject_id", "hadm_id", "labevent_id", "specimen_id", "pharmacy_id"):
                assert f.dataType == LongType(), (t, f.name)
            if f.name.endswith("time"):
                assert f.dataType == TimestampNTZType(), (t, f.name)
        assert TABLES[t][1][0] in names


def test_fixture_identifiers_are_never_eight_digits():
    rows = (SY.discharge_rows() + SY.radiology_rows() + SY.admissions_rows() + SY.labevents_rows()
            + SY.prescriptions_rows())
    for r in rows:
        for k in ("subject_id", "hadm_id", "labevent_id", "specimen_id", "pharmacy_id"):
            if r.get(k) is not None:
                assert r[k] < 10_000_000


# ---------------------------------------------------------------- multi-line quoted notes
@pytest.mark.parametrize("quoting", [csv.QUOTE_MINIMAL, csv.QUOTE_NOTNULL], ids=["minimal", "all-non-null-quoted"])
def test_multiline_quoted_notes_round_trip_exactly(spark, tmp_path, quoting):
    rows = SY.discharge_rows()
    cfg, _ = setup_table(tmp_path, "discharge", rows, quoting=quoting, expected={"discharge": len(rows)})
    rec, _ = run_one(spark, cfg, "discharge")
    assert rec["status"] == "PASS", rec.get("error")
    assert rec["rows"] == len(rows) == 7
    got = read_rows(spark, cfg, "discharge")
    by_id = {}
    for r in got:
        by_id.setdefault(r.note_id, []).append(r.text)
    for nid, text in SY.NOTE_TEXTS.items():
        assert all(t == text for t in by_id[nid]), nid          # byte-for-byte, including CRLF and edge spaces
    assert len(by_id["101-DS-1"]) == 2                          # the duplicate note is kept, not merged


def test_duplicate_note_ids_are_kept_and_countable(spark, tmp_path):
    rows = SY.discharge_rows(duplicate=True)
    cfg, _ = setup_table(tmp_path, "discharge", rows)
    run_one(spark, cfg, "discharge")
    df = spark.read.parquet(str(out_dir(cfg, "discharge")))
    dup = df.groupBy("note_id").count().filter("count > 1").count()
    assert df.count() == 7 and dup == 1


def test_types_nulls_and_timestamps_are_exact(spark, tmp_path):
    cfg, _ = setup_table(tmp_path, "discharge", SY.discharge_rows())
    run_one(spark, cfg, "discharge")
    t = pq.read_table(str(out_dir(cfg, "discharge")))
    assert str(t.schema.field("charttime").type) == "timestamp[us]"            # no time zone attached
    d = {r["note_id"]: r for r in t.to_pylist()}
    assert d["101-DS-1"]["charttime"] == dt.datetime(2150, 3, 8, 2, 30)        # a wall-clock time no zone can shift
    assert d["101-DS-1"]["storetime"] is None                                   # unquoted empty field -> null
    assert d["102-DS-1"]["subject_id"] == 102 and d["102-DS-1"]["note_seq"] == 1


def test_fractional_seconds_and_text_codes(spark, tmp_path):
    cfg, _ = setup_table(tmp_path, "prescriptions", SY.prescriptions_rows())
    rec, _ = run_one(spark, cfg, "prescriptions")
    assert rec["status"] == "UNSET", rec.get("error")
    r = read_rows(spark, cfg, "prescriptions")[0]
    assert r.starttime == dt.datetime(2150, 1, 2, 8, 0)
    assert r.stoptime == dt.datetime(2150, 1, 3, 8, 0, 0, 250000)
    assert r.ndc == "0001" and r.dose_val_rx == "1-2"                           # codes keep leading zeros, ranges stay text


def test_quoted_empty_string_is_read_as_null(spark, tmp_path):
    """Pins Spark's behaviour: a quoted empty field "" and an unquoted empty field are both null. DuckDB's read_csv
    default (allow_quoted_nulls) does the same, so the two pipelines agree here."""
    cfg = SY.make_cfg(tmp_path)
    raw = ING.C.paths(cfg)["raw_root"]
    head = ",".join(column_names("admissions"))
    line = '101,2001,2150-03-08 02:30:00,2150-03-10 11:00:00,,EW EMER.,,"",HOME,Other,English,,UNKNOWN,,,0'
    f = SY.write_raw_gz(raw / "hosp" / "admissions.csv.gz", f"{head}\n{line}\n")
    SY.write_manifest(raw, [f])
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["status"] == "UNSET", rec.get("error")
    r = read_rows(spark, cfg, "admissions")[0]
    assert r.admission_location is None and r.admit_provider_id is None


# ---------------------------------------------------------------- failures never print values
def _assert_no_values(text):
    for frag in SY.VALUE_FRAGMENTS + ["abc", "2001", "EW EMER"]:
        assert frag not in text, frag


def test_malformed_value_fails_without_printing_it(spark, tmp_path):
    rows = SY.admissions_rows()
    rows[2]["subject_id"] = "abc"
    cfg, _ = setup_table(tmp_path, "admissions", rows)
    rec, log = run_one(spark, cfg, "admissions")
    assert rec["status"] == "FAIL"
    assert rec["error"] == "a record does not fit the schema (FAILFAST)"
    _assert_no_values(json.dumps(rec))
    assert (log.private / "error.log").exists()                                 # the full traceback stays private
    assert not out_dir(cfg, "admissions").exists()


def test_short_row_fails(spark, tmp_path):
    cfg = SY.make_cfg(tmp_path)
    raw = ING.C.paths(cfg)["raw_root"]
    head = ",".join(column_names("patients"))
    f = SY.write_raw_gz(raw / "hosp" / "patients.csv.gz", f"{head}\n101,F,50,2150,2008 - 2010,\n102,M,40\n")
    SY.write_manifest(raw, [f])
    rec, _ = run_one(spark, cfg, "patients")
    assert rec["status"] == "FAIL" and "rows" not in rec


def test_unescaped_quote_fails(spark, tmp_path):
    cfg = SY.make_cfg(tmp_path)
    raw = ING.C.paths(cfg)["raw_root"]
    head = ",".join(column_names("d_labitems"))
    f = SY.write_raw_gz(raw / "hosp" / "d_labitems.csv.gz", f'{head}\n50861,"Synthetic "label" here",Blood,Chemistry\n')
    SY.write_manifest(raw, [f])
    rec, _ = run_one(spark, cfg, "d_labitems")
    assert rec["status"] == "FAIL"
    _assert_no_values(json.dumps(rec))


def test_header_mismatch_names_only_schema_columns(spark, tmp_path):
    cfg = SY.make_cfg(tmp_path)
    raw = ING.C.paths(cfg)["raw_root"]
    f = SY.write_csv_gz(raw / "note" / "discharge.csv.gz", "discharge", SY.discharge_rows(), header=False)
    SY.write_manifest(raw, [f])
    rec, _ = run_one(spark, cfg, "discharge")                                   # first line is a data row
    assert rec["status"] == "FAIL" and rec["error"] == "header mismatch: the first line is not a CSV header"

    cols = column_names("patients")
    renamed = ",".join(c if c != "dod" else "Synthetic_dod" for c in cols)
    f = SY.write_raw_gz(raw / "hosp" / "patients.csv.gz", f"{renamed}\n101,F,50,2150,2008 - 2010,\n")
    SY.write_manifest(raw, [f])
    rec, _ = run_one(spark, cfg, "patients")
    assert rec["status"] == "FAIL"
    assert rec["error"] == "header mismatch: missing ['dod']; 1 unexpected column name(s) (not shown)"
    _assert_no_values(rec["error"])


# ---------------------------------------------------------------- fingerprints
def test_sha256_matches_hashlib(tmp_path):
    f = SY.write_csv_gz(tmp_path / "x.csv.gz", "patients", [])
    assert sha256_file(f) == SY.sha256(f)


def test_manifest_mismatch_stops_before_reading(spark, tmp_path):
    cfg, f = setup_table(tmp_path, "admissions", SY.admissions_rows())
    SY.write_manifest(ING.C.paths(cfg)["raw_root"], [f], override={f.name: "0" * 64})
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["status"] == "FAIL" and rec["error"] == "SHA-256 differs from the PhysioNet manifest"
    assert not out_dir(cfg, "admissions").exists()


def test_file_missing_from_manifest(spark, tmp_path):
    cfg, _ = setup_table(tmp_path, "admissions", SY.admissions_rows())
    (ING.C.paths(cfg)["raw_root"] / "SHA256SUMS.txt").write_text("")
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["status"] == "FAIL" and "not listed" in rec["error"]
    cfg2 = SY.make_cfg(tmp_path, require_manifest=False)
    rec2, _ = run_one(spark, cfg2, "admissions")
    assert rec2["status"] == "UNSET" and rec2["manifest"]["status"] == "missing"


# ---------------------------------------------------------------- count gate, quarantine, verify, rerun
def test_count_gate_pass_fail_and_tolerance(spark, tmp_path):
    rows = SY.admissions_rows()
    cfg, _ = setup_table(tmp_path, "admissions", rows, expected={"admissions": len(rows)})
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["status"] == "PASS" and (out_dir(cfg, "admissions") / ING.OK_JSON).exists()

    shutil.rmtree(out_dir(cfg, "admissions"))
    cfg_bad = SY.make_cfg(tmp_path, expected={"admissions": len(rows) + 1})
    rec, log = run_one(spark, cfg_bad, "admissions")
    assert rec["status"] == "FAIL" and "quarantine" in rec["error"]
    assert not out_dir(cfg, "admissions").exists()
    q = ING.C.paths(cfg)["out_root"] / "_quarantine" / log.data["run_name"] / "admissions"
    assert q.exists() and not (q / ING.OK_JSON).exists()

    cfg_tol = SY.make_cfg(tmp_path, expected={"admissions": len(rows) + 1}, tolerance_pct=50.0)
    rec, _ = run_one(spark, cfg_tol, "admissions")
    assert rec["status"] == "PASS"


def test_unset_then_verify_only_writes_marker_without_rewriting(spark, tmp_path):
    rows = SY.admissions_rows()
    cfg, _ = setup_table(tmp_path, "admissions", rows)
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["status"] == "UNSET" and not (out_dir(cfg, "admissions") / ING.OK_JSON).exists()
    before = sorted(p.name for p in out_dir(cfg, "admissions").iterdir())
    cfg2 = SY.make_cfg(tmp_path, expected={"admissions": len(rows)})
    rec2, _ = run_one(spark, cfg2, "admissions", verify_only=True)
    assert rec2["status"] == "PASS" and rec2["action"] == "verified existing"
    after = sorted(p.name for p in out_dir(cfg, "admissions").iterdir() if p.name != ING.OK_JSON)
    assert before == after


def test_rerun_keeps_same_source_and_refuses_a_different_one(spark, tmp_path):
    rows = SY.admissions_rows()
    cfg, f = setup_table(tmp_path, "admissions", rows)
    run_one(spark, cfg, "admissions")
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["action"] == "kept existing (same file and schema)"
    SY.write_csv_gz(f, "admissions", rows[:3])
    SY.write_manifest(ING.C.paths(cfg)["raw_root"], [f])
    rec, _ = run_one(spark, cfg, "admissions")
    assert rec["status"] == "FAIL" and "--force" in rec["error"]
    rec, _ = run_one(spark, cfg, "admissions", force=True)
    assert rec["action"] == "ingested" and rec["rows"] == 3


def test_verify_only_refuses_a_changed_input(spark, tmp_path):
    rows = SY.admissions_rows()
    cfg, f = setup_table(tmp_path, "admissions", rows, expected={"admissions": len(rows)})
    run_one(spark, cfg, "admissions")
    SY.write_csv_gz(f, "admissions", rows[:3])
    SY.write_manifest(ING.C.paths(cfg)["raw_root"], [f])
    rec, _ = run_one(spark, cfg, "admissions", verify_only=True)
    assert rec["status"] == "FAIL" and "different file" in rec["error"]


# ---------------------------------------------------------------- partitioning
def test_range_partitioning_gives_disjoint_sorted_files(spark, tmp_path):
    rows = SY.labevents_rows()
    cfg, _ = setup_table(tmp_path, "labevents", rows, partitions={"labevents": 4}, expected={"labevents": len(rows)})
    rec, _ = run_one(spark, cfg, "labevents")
    assert rec["status"] == "PASS" and 2 <= rec["n_files"] <= 4
    ranges = []
    for f in sorted(out_dir(cfg, "labevents").glob("*.parquet")):
        t = pq.read_table(f).to_pylist()
        keys = [(r["subject_id"], r["charttime"], r["labevent_id"]) for r in t]
        assert keys == sorted(keys)                                             # sorted within the file
        ranges.append((keys[0][0], keys[-1][0]))
    ranges.sort()
    for (_, hi), (lo, _) in zip(ranges, ranges[1:]):
        assert hi < lo                                                          # files cover disjoint subject ranges
    got = spark.read.parquet(str(out_dir(cfg, "labevents")))
    assert got.filter("comments IS NOT NULL").count() == 1                      # the multi-line comment survived


# ---------------------------------------------------------------- the command line prints aggregates only
def test_cli_prints_no_values_and_exits_3_when_counts_unset(spark, tmp_path, capsys):
    cfg = SY.make_cfg(tmp_path)
    raw = ING.C.paths(cfg)["raw_root"]
    f1 = SY.write_csv_gz(raw / "note" / "discharge.csv.gz", "discharge", SY.discharge_rows())
    f2 = SY.write_csv_gz(raw / "note" / "radiology.csv.gz", "radiology", SY.radiology_rows())
    SY.write_manifest(raw, [f1, f2])
    conf = tmp_path / "conf.yaml"
    conf.write_text(yaml.safe_dump({k: v for k, v in cfg.items() if k != "_source"}))
    code = ING.main(["--config", str(conf), "--tables", "discharge,radiology", "--run-name", "cli"], spark=spark)
    out = capsys.readouterr().out
    assert code == ING.EXIT_UNSET
    assert "unset 2" in out and "rows <11" in out                               # small counts print as <11
    _assert_no_values(out)
    run = json.loads((ING.C.paths(cfg)["runs_root"] / "cli" / "run.json").read_text())
    assert run["status"] == "UNSET" and run["tables"]["discharge"]["rows"] == 7
    assert run["versions"]["spark"] and run["versions"]["java"]
    assert run["memory"]["jvm_heap_peak_bytes_upper_bound"] > 0 and run["memory"]["driver_python_peak_rss_bytes"] > 0


def test_small_count_formatting():
    assert n(7) == "<11" and n(0) == "0" and n(11) == "11" and n(1234567) == "1,234,567" and n(None) == "unset"
