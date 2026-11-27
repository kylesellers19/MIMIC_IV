"""Steps 5 (gates) and 6 (parity, scale), the cluster config and the job runner, on the whole invented pipeline."""
import json
import shutil
import zipfile

import duckdb
import pytest

from masld_spark import config as C
from masld_spark import gates as GA
from masld_spark import parity as PA
from masld_spark import scale as SC
from masld_spark.fingerprint import sha256_file
from masld_spark.runlog import RunLog

import pipeline_fixture as PF


@pytest.fixture(scope="module")
def built(spark, tmp_path_factory):
    root = tmp_path_factory.mktemp("pipeline")
    with pytest.MonkeyPatch.context() as mp:
        PF.build_full(spark, root, mp)
    return root


def copy_of(built, tmp_path):
    """A private copy of the built pipeline (configs hold absolute paths, so the config is rebuilt for the copy)."""
    dst = tmp_path / "p"
    shutil.copytree(built, dst, symlinks=True)
    cfg = PF.make_config(dst, PF._rows(True))
    shutil.copy(built / "splits_v1.parquet", dst / "splits_v1.parquet")   # make_config rewrote it identically
    return dst, cfg


def run_gates(spark, root, cfg, name="g", quarantine=True):
    log = RunLog(root / "runs", name, "gates", cfg)
    return GA.run_gates(spark, cfg, log, quarantine_on_fail=quarantine), log


def gate(log, text):
    return next(r for r in log.data["gates"] if text in r["gate"])


# ---------------------------------------------------------------- Step 5
def test_gates_pass_on_a_clean_pipeline(spark, built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    code, log = run_gates(spark, root, cfg)
    assert code == GA.EXIT_OK, [r for r in log.data["gates"] if not r["pass"]]
    assert (C.paths(cfg)["out_root"] / GA.GATES_OK).exists()
    assert gate(log, "radiology notes whose hadm_id is not an admission")["value"] == 50.0   # 777-RR-1 of two
    assert log.data["null_rates"]["radiology"]["hadm_id"]["nulls"] == 6
    assert gate(log, "chunks_tiny: (note, variant) groups with broken chunk indexes")["pass"]


def test_duplicate_note_id_quarantines_everything_and_restore_moves_it_back(spark, built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    d = C.paths(cfg)["out_root"] / "ingest" / "discharge"
    part = next(d.glob("*.parquet"))
    shutil.copy(part, d / ("dup-" + part.name))                  # every discharge note now appears twice
    code, log = run_gates(spark, root, cfg, "g-dup")
    assert code == GA.EXIT_FAIL
    assert not gate(log, "discharge: duplicate note_id")["pass"]
    assert log.data["quarantined"] == ["ingest", "cohort", "splits", "notes"]
    out = C.paths(cfg)["out_root"]
    assert not (out / "ingest").exists() and (out / "_quarantine" / "g-dup" / "notes").exists()
    assert not (out / GA.GATES_OK).exists()
    assert GA.restore(cfg, "g-dup") == ["ingest", "cohort", "splits", "notes"]
    assert (out / "notes" / "notes").exists()


def test_gold_subject_under_another_partition_quarantines_only_notes(spark, built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    ch = C.paths(cfg)["out_root"] / "notes" / "chunks_tiny"
    gold = next((ch / "partition=GOLD_HOLDOUT").glob("*.parquet"))
    shutil.copy(gold, ch / "partition=DEV" / ("leak-" + gold.name))
    code, log = run_gates(spark, root, cfg, "g-leak")
    assert code == GA.EXIT_FAIL
    assert gate(log, "chunks_tiny: GOLD_HOLDOUT subjects outside partition=GOLD_HOLDOUT")["value"] > 0
    assert log.data["quarantined"] == ["notes"]
    assert (C.paths(cfg)["out_root"] / "cohort").exists()


def test_changed_raw_file_fails_the_ingest_gate(spark, built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    f = C.paths(cfg)["raw_root"] / "hosp" / "d_labitems.csv.gz"
    f.write_bytes(f.read_bytes() + b"")                          # same bytes: still passes
    f2 = C.paths(cfg)["raw_root"] / "hosp" / "omr.csv.gz"
    with open(f2, "ab") as fh:
        fh.write(b"\x00")
    code, log = run_gates(spark, root, cfg, "g-raw", quarantine=False)
    assert code == GA.EXIT_FAIL
    assert not gate(log, "omr: input file unchanged since ingest")["pass"]
    assert gate(log, "d_labitems: input file unchanged since ingest")["pass"]
    assert (C.paths(cfg)["out_root"] / "ingest").exists()        # --no-quarantine moves nothing


# ---------------------------------------------------------------- Step 6a parity
def stored_copies(root, cfg, edit=None):
    """Stand-ins for the DuckDB pipeline's files, written by DuckDB from the Spark outputs; `edit` mutates them."""
    out = C.paths(cfg)["out_root"]
    st = root / "stored"
    st.mkdir(exist_ok=True)
    con = duckdb.connect()
    src = {
        "locked_population": f"SELECT * FROM read_parquet('{out}/cohort/population_locked/*.parquet')",
        "clean_population": f"SELECT * FROM read_parquet('{out}/cohort/population_clean/*.parquet')",
        "cmrf": f"SELECT * FROM read_parquet('{out}/cohort/cmrf/*.parquet')",
        "lab_features": f"SELECT * FROM read_parquet('{out}/cohort/lab_features/*.parquet')",
        "outpatient_fib4_inputs": f"SELECT * FROM read_parquet('{out}/cohort/outpatient_fib4_inputs/*.parquet')",
        "frame": f"SELECT hadm_id, subject_id, code_positive, note_a, note_b, note_c, note_a AS note_d "
                 f"FROM read_parquet('{out}/notes/labels_rule/*.parquet')",
        "notes_dc": f"SELECT note_id, hadm_id, subject_id, charttime, n_chars, a_pos, b_pos, c_hedged, n_pos, n_hist, "
                    f"n_tierC, n_neg, liver_incl FROM read_parquet('{out}/notes/notes/**/*.parquet', hive_partitioning=true) "
                    f"WHERE note_table = 'discharge'",
        "notes_rr": f"SELECT note_id, hadm_id, subject_id, charttime, n_chars, a_pos, b_pos, c_hedged, n_pos, n_hist, "
                    f"n_tierC, n_neg, liver_incl FROM read_parquet('{out}/notes/notes/**/*.parquet', hive_partitioning=true) "
                    f"WHERE note_table = 'radiology'",
    }
    for k, q in src.items():
        con.execute(f"CREATE TABLE {k} AS {q}")
    for stmt in (edit or []):
        con.execute(stmt)
    for k in src:
        con.execute(f"COPY {k} TO '{st}/{k}.parquet' (FORMAT parquet)")
    cfg["parity"]["stored"] = {k: str(st / f"{k}.parquet") for k in src if not k.startswith("notes_")}
    cfg["parity"]["stored"]["splits"] = str(root / "splits_v1.parquet")
    cfg["parity"]["stored"]["notes_index"] = [str(st / "notes_dc.parquet"), str(st / "notes_rr.parquet")]
    frozen = {str(st / "clean_population.parquet"): {"sha256": sha256_file(st / "clean_population.parquet")},
              str(root / "splits_v1.parquet"): {"sha256": sha256_file(root / "splits_v1.parquet")}}
    (root / "parity_frozen.json").write_text(json.dumps({"frozen": frozen}))
    cfg["parity"]["frozen_hashes"] = str(root / "parity_frozen.json")
    return cfg


def run_parity(root, cfg, name):
    (C.paths(cfg)["out_root"] / GA.GATES_OK).write_text("{}")
    log = RunLog(root / "runs", name, "parity", cfg)
    return PA.run_parity(cfg, log), log


def test_parity_identical_copies_agree(built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    code, log = run_parity(root, stored_copies(root, cfg), "p-same")
    assert code == PA.EXIT_OK
    assert log.data["ties"]["ties_clean"] == 1 and log.data["ties"]["ties_first"] == 1
    for name, r in log.data["parity"].items():
        assert r["only_spark"] == r["only_stored"] == 0, name
        assert all(v["differ"] == 0 for v in r["columns"].values()), name
    lab = log.data["parity"]["labels"]["agreement"]["note_b"]
    assert lab == {"both": 2, "spark_only": 0, "stored_only": 0, "neither": 1}
    assert len(log.data["parity"]["population_clean"]["columns"]) > 40
    assert "partition" in log.data["parity"]["splits"]["columns"]            # a real column there, not a directory


def test_parity_difference_on_a_tied_result_is_explained(built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    cfg = stored_copies(root, cfg, ["UPDATE lab_features SET first_val_ALT = 10.0 WHERE hadm_id = 2001",
                                    "UPDATE clean_population SET lab_ALT = 10.0 WHERE hadm_id = 2001"])
    code, log = run_parity(root, cfg, "p-tie")
    assert code == PA.EXIT_OK
    c = log.data["parity"]["lab_features"]["columns"]["first_val_ALT"]
    assert c == {"differ": 1, "explained_by_ties": 1, "unexplained": 0}
    assert log.data["parity"]["population_clean"]["columns"]["lab_ALT"]["explained_by_ties"] == 1


def test_parity_unexplained_difference_and_missing_key_fail(built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    cfg = stored_copies(root, cfg, ["UPDATE clean_population SET lab_AST = 41.0 WHERE hadm_id = 2001",
                                    "DELETE FROM cmrf WHERE hadm_id = 2004",
                                    "UPDATE notes_rr SET a_pos = NOT a_pos WHERE note_id = '101-RR-a'",
                                    "UPDATE frame SET note_b = false WHERE hadm_id = 2001"])
    code, log = run_parity(root, cfg, "p-diff")
    assert code == PA.EXIT_FAIL
    p = log.data["parity"]
    assert p["population_clean"]["columns"]["lab_AST"]["unexplained"] == 1
    assert p["cmrf"]["only_spark"] == 1
    assert p["notes_index"]["columns"]["a_pos"]["unexplained"] == 1
    assert p["labels"]["agreement"]["note_b"]["spark_only"] == 1


def test_parity_refuses_a_frozen_file_that_changed(built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    cfg = stored_copies(root, cfg)
    f = root / "stored" / "clean_population.parquet"
    with open(f, "ab") as fh:
        fh.write(b"\x00")
    with pytest.raises(PA.StageFailure, match="frozen SHA-256"):
        run_parity(root, cfg, "p-frozen")


# ---------------------------------------------------------------- Step 6b scale, cluster config, job runner
def test_scale_report(built, tmp_path):
    root, cfg = copy_of(built, tmp_path)
    rep = SC.build_report(cfg)
    assert {"ingest", "cohort", "splits", "notes"} <= set(rep["stages"])
    assert rep["totals"]["raw_rows"] == sum(len(r) for r in PF._rows(True).values())
    assert rep["totals"]["notes"] == 10 and rep["totals"]["tokens_all"] > 0
    assert set(rep["totals"]["tokens"]) == {"tiny", "tiny_counts"}


def test_cluster_config_extends_local():
    local, cl = C.load("conf/spark_local.yaml"), C.load("conf/spark_cluster.yaml")
    assert cl["spark"]["master"] is None and "spark.driver.memory" not in cl["spark"]["conf"]
    assert cl["paths"]["raw_root"].startswith("/Volumes/")
    assert cl["ingest"]["expected_rows"] == local["ingest"]["expected_rows"]
    assert cl["cohort"]["reference"] == local["cohort"]["reference"]
    assert cl["ingest"]["partitions"]["labevents"] == 128 and cl["ingest"]["partitions"]["admissions"] == 1
    bert = cl["notes"]["tokenizers"]["bio_clinicalbert"]
    assert bert["chunk"] == {"window": 512, "stride": 64} and bert["revision"] is None
    assert local["spark"]["conf"]["spark.driver.memory"] == "16g"        # the local file is unchanged by the merge


def test_job_runner_bundle_and_ship(spark, tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("spark_job", str(C.ROOT / "scripts" / "spark_job.py"))
    job = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job)
    z = job.bundle(tmp_path)
    names = set(zipfile.ZipFile(z).namelist())
    assert {"masld_spark/notes.py", "scripts/__init__.py", "scripts/note_phenotype.py", "scripts/liver_sentences.py",
            "scripts/run0919_notes_text.py", "scripts/run0919_notes_index.py", "scripts/masld_config.py"} <= names
    assert job.ship(spark, z) == "addPyFile"
    for module, _ in job.STEPS.values():
        __import__(module)
    assert job.main([]) == 2
