#!/usr/bin/env python3
"""Cluster entry point for the PySpark pipeline: one step per invocation (one job task on Databricks).

    python scripts/spark_job.py <step> --config <yaml> [step options]
    steps: ingest, ingest-verify, cohort, splits, notes, gates, scale   (parity runs locally; see docs/spark_cluster.md)

Session: when the config names a master (spark.master, e.g. spark://host:7077 for a standalone cluster), the session
is built from the config, with the JVM log in runs/_job-<time>/private/; when spark.master is null (Databricks), the
cluster's existing session is used. Either way it ships masld_spark/ and scripts/*.py to the executors as one zip (the
note step's Python workers import the frozen rule and the text functions from there) and calls the step's main()
with that session. It stops only a session it built. Locally, use the Makefile targets instead.
"""
import argparse
import importlib
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# step -> (module, extra arguments); None = the module's main() takes no Spark session
STEPS = {"ingest": ("masld_spark.ingest", []), "ingest-verify": ("masld_spark.ingest", ["--verify-only"]),
         "cohort": ("masld_spark.cohort", []), "splits": ("masld_spark.splits", []),
         "notes": ("masld_spark.notes", []), "gates": ("masld_spark.gates", []),
         "parity": ("masld_spark.parity", None), "scale": ("masld_spark.scale", None)}


def bundle(dest_dir):
    """masld_spark/*.py and scripts/*.py in one zip; scripts/ gets an __init__.py inside the zip only."""
    z = Path(dest_dir) / "masld_spark_bundle.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for p in sorted((ROOT / "masld_spark").glob("*.py")):
            f.write(p, f"masld_spark/{p.name}")
        f.writestr("scripts/__init__.py", "")
        for p in sorted((ROOT / "scripts").glob("*.py")):
            f.write(p, f"scripts/{p.name}")
    return z


def ship(spark, z):
    """Classic compute: SparkContext.addPyFile. Spark Connect sessions have no SparkContext: addArtifacts instead."""
    try:
        spark.sparkContext.addPyFile(str(z))
        return "addPyFile"
    except Exception:   # noqa: BLE001
        spark.addArtifacts(str(z), pyfile=True)
        return "addArtifacts"


def session(rest):
    """-> (session, built_here)"""
    from pyspark.sql import SparkSession
    from masld_spark import config as C
    from masld_spark.session import build
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--config", default="conf/spark_local.yaml")
    a, _ = ap.parse_known_args(rest)
    cfg = C.load(a.config)
    if cfg["spark"]["master"]:
        private = C.paths(cfg)["runs_root"] / f"_job-{datetime.now():%Y%m%d-%H%M%S}" / "private"
        return build(cfg, private), True
    return SparkSession.builder.getOrCreate(), False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in STEPS:
        print(f"usage: spark_job.py <{'|'.join(STEPS)}> --config <yaml> [options]", flush=True)
        return 2
    step, rest = argv[0], argv[1:]
    module, extra = STEPS[step]
    mod = importlib.import_module(module)
    if extra is None:
        return mod.main(rest)
    spark, built = session(rest)
    try:
        how = ship(spark, bundle(tempfile.mkdtemp(prefix="masld_spark_")))
        print(f"[job] {step}: master {spark.sparkContext.master if built else 'cluster session'}; "
              f"code shipped to the executors ({how})", flush=True)
        return mod.main(rest + extra, spark=spark)
    finally:
        if built:
            spark.stop()


if __name__ == "__main__":
    sys.exit(main())
