"""Step 4 — subject-level splits: the repository's splits_v1, verified and copied. Never redrawn.

splits_v1.parquet (scripts/run0919_phase2_splits.py, seed 20260920) is frozen: the GOLD_HOLDOUT predictions and the
language model's answers are locked against it. A hash-based reassignment would move subjects between partitions,
so this step only checks and copies it:
  * its SHA-256 equals the value recorded in docs/run_2026-11-10/results/frozen_hashes_end.json (else stop; the file is
    read only after this check);
  * it covers exactly the Step 2 population, one row per admission, with the same subject for each admission;
  * every subject sits in one partition (GOLD_HOLDOUT, TEST, DEV) and, within DEV, one fold (0-4); outside DEV the
    fold is null;
  * admissions, subjects and code-positive admissions per partition and per DEV fold equal
    docs/run_2026-09-19/results/phase2_splits.json.
A population subject missing from splits_v1 fails the step: no split is invented.

Outputs (data/spark/splits/): admission_splits (hadm_id, subject_id, partition, fold) and subject_splits
(subject_id, partition, fold); _STAGE_OK.json when every check passes.
Run:  zsh scripts/spark_env.sh -m masld_spark.splits --config conf/spark_local.yaml [--force]
"""
import argparse
import json
import sys
import time
from datetime import datetime

from pyspark.sql import functions as F

from masld_spark import config as C
from masld_spark.cohort import STAGE_OK
from masld_spark.fingerprint import sha256_file
from masld_spark.ingest import describe_error
from masld_spark.runlog import RunLog, n, say, size, utc_now
from masld_spark.session import build as build_session
from masld_spark.stageio import StageFailure, write_table

EXIT_OK, EXIT_FAIL = 0, 1
PARTITIONS = ("GOLD_HOLDOUT", "TEST", "DEV")
DEFAULTS = {"source": "data/processed/splits_v1.parquet",
            "frozen_hashes": "docs/run_2026-11-10/results/frozen_hashes_end.json",
            "frozen_key": "data/processed/splits_v1.parquet",
            "reference": "docs/run_2026-09-19/results/phase2_splits.json"}


def settings(cfg):
    s = dict(DEFAULTS)
    s.update((cfg.get("splits") or {}))
    return s


def stage_input(spark, cfg, stage, table):
    d = C.paths(cfg)["out_root"] / stage
    if not (d / STAGE_OK).exists():
        raise StageFailure(f"Step '{stage}' has not passed (no {STAGE_OK}); run it first")
    return spark.read.parquet(str(d / table))


def recorded_sha(s):
    rec = json.loads(C.resolve(s["frozen_hashes"]).read_text())
    entry = (rec.get("frozen") or {}).get(s["frozen_key"])
    if not entry or "sha256" not in entry:
        raise StageFailure(f"no recorded SHA-256 for {s['frozen_key']} in {s['frozen_hashes']}")
    return entry["sha256"]


def check_splits(sp, pop, ref):
    """-> list of (check, value, expected). sp: hadm_id, subject_id, partition, fold. pop: population_locked."""
    out = []
    n_pop = pop.count()
    out.append(("split rows = population admissions", sp.count(), n_pop))
    out.append(("split hadm_id unique", sp.select("hadm_id").distinct().count(), n_pop))
    out.append(("population admissions without a split", pop.join(sp, "hadm_id", "left_anti").count(), 0))
    out.append(("split admissions outside the population", sp.join(pop, "hadm_id", "left_anti").count(), 0))
    j = sp.alias("s").join(pop.alias("p"), "hadm_id")
    out.append(("admissions whose split subject differs", j.where(F.col("s.subject_id") != F.col("p.subject_id")).count(), 0))
    out.append(("rows with an unknown partition", sp.where(~F.col("partition").isin(*PARTITIONS)).count(), 0))
    out.append(("subjects in more than one partition",
                sp.groupBy("subject_id").agg(F.countDistinct("partition").alias("k")).where("k > 1").count(), 0))
    out.append(("subjects in more than one fold",
                sp.groupBy("subject_id").agg(F.countDistinct("fold").alias("k")).where("k > 1").count(), 0))
    out.append(("DEV rows with fold outside 0-4",
                sp.where((F.col("partition") == "DEV") & (F.col("fold").isNull() | ~F.col("fold").between(0, 4))).count(), 0))
    out.append(("non-DEV rows with a fold", sp.where((F.col("partition") != "DEV") & F.col("fold").isNotNull()).count(), 0))
    code = pop.select("hadm_id", "code_positive")
    stats = {r["partition"]: r for r in sp.join(code, "hadm_id").groupBy("partition").agg(
        F.count(F.lit(1)).alias("adm"), F.countDistinct("subject_id").alias("subj"),
        F.sum(F.col("code_positive").cast("int")).alias("code")).collect()}
    for p in PARTITIONS:
        r, e = stats.get(p), ref["partitions"][p]
        out.append((f"{p} admissions", r["adm"] if r else 0, e["admissions"]))
        out.append((f"{p} subjects", r["subj"] if r else 0, e["subjects"]))
        out.append((f"{p} code-positive admissions", (r["code"] or 0) if r else 0, e["code_positive"]))
    folds = {r["fold"]: r for r in sp.where("partition = 'DEV'").groupBy("fold").agg(
        F.count(F.lit(1)).alias("adm"), F.countDistinct("subject_id").alias("subj")).collect()}
    for k, e in sorted(ref["dev_folds"].items()):
        r = folds.get(int(k))
        out.append((f"DEV fold {k} admissions", r["adm"] if r else 0, e["admissions"]))
        out.append((f"DEV fold {k} subjects", r["subj"] if r else 0, e["subjects"]))
    return out


def run_splits(spark, cfg, log, force=False):
    s = settings(cfg)
    out = C.paths(cfg)["out_root"] / "splits"
    if out.exists() and any(out.iterdir()) and not force:
        raise StageFailure("splits output exists; pass --force to rebuild it")
    (out / STAGE_OK).unlink(missing_ok=True)
    pop = stage_input(spark, cfg, "cohort", "population_locked")
    src = C.resolve(s["source"])
    if not src.exists():
        raise StageFailure(f"split file not found: {s['source']}")
    t = time.time()
    digest, expected = sha256_file(src), recorded_sha(s)
    log.data["splits_source"] = {"path": s["source"], "bytes": src.stat().st_size, "sha256": digest,
                                 "recorded_sha256": expected, "seconds_hash": round(time.time() - t, 2)}
    if digest != expected:
        raise StageFailure(f"{s['source']} differs from its recorded SHA-256; it is frozen and must not change")
    say("[splits] source", s["source"], f"{size(src.stat().st_size)}", "SHA-256 matches the frozen record")
    sp = spark.read.parquet(str(src)).select("hadm_id", "subject_id", "partition",
                                             F.col("fold").cast("int").alias("fold"))
    ref = json.loads(C.resolve(s["reference"]).read_text())
    results = []
    for name, value, exp in check_splits(sp, pop, ref):
        ok = value == exp
        results.append({"check": name, "value": value, "expected": exp, "pass": ok})
        say("[check]", f"{name:<44}", f"{n(value):>10}", f"reference {n(exp):>10}", "PASS" if ok else "FAIL")
    log.data["checks"] = results
    for name, df, keys in [("admission_splits", sp, ("hadm_id",)),
                           ("subject_splits", sp.select("subject_id", "partition", "fold").distinct(), ("subject_id",))]:
        rec = write_table(spark, df, out, name, log.data["run_name"], sort_keys=keys)
        log.data["tables"][name] = rec
        say(f"[{name}]".ljust(20), f"rows {n(rec['rows'])}", f"{rec['n_files']} file(s) {size(rec['bytes'])}")
    log.write()
    ok = all(r["pass"] for r in results)
    if ok:
        (out / STAGE_OK).write_text(json.dumps({"stage": "splits", "run_name": log.data["run_name"],
                                                "source_sha256": digest, "verified_utc": utc_now()}, indent=1))
    return EXIT_OK if ok else EXIT_FAIL


def main(argv=None, spark=None):
    ap = argparse.ArgumentParser(description="Step 4: verify and copy splits_v1 (aggregates only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    ap.add_argument("--force", action="store_true", help="rebuild the splits output")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
    except (OSError, C.ConfigError, ValueError) as e:
        say("[splits] config error:", e)
        return EXIT_FAIL
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-splits-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(C.paths(cfg)["runs_root"], name, "splits", cfg)
    own, code = spark is None, EXIT_FAIL
    try:
        if own:
            spark = build_session(cfg, log.private)
        log.spark_versions(spark)
        say(f"[splits] run {name}", f"Spark {log.data['versions']['spark']}")
        code = run_splits(spark, cfg, log, force=a.force)
    except StageFailure as e:
        say("[splits] stopped:", e)
    except Exception as e:   # noqa: BLE001 — classified, never printed
        log.private_error("splits", e)
        say("[splits] run failed:", describe_error(e))
    finally:
        log.memory(spark)
        if own and spark is not None:
            spark.stop()
        log.finish("PASS" if code == EXIT_OK else "FAIL", code)
        say(f"[splits] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
