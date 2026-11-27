#!/usr/bin/env python3
"""Cluster entry point for the PySpark pipeline: one step per job task, on the cluster's existing Spark session.

    python scripts/spark_job.py <step> --config conf/spark_cluster.local.yaml [step options]
    steps: ingest, ingest-verify, cohort, splits, notes, gates, scale   (parity runs locally; see docs/spark_cluster.md)

It puts the repository root on sys.path, ships masld_spark/ and scripts/*.py to the executors as one zip (the note
step's Python workers import the frozen rule and the text functions from there), then calls the step's main() with
the existing session, which it never stops. Locally, use the Makefile targets instead.
"""
import importlib
import sys
import tempfile
import zipfile
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
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    how = ship(spark, bundle(tempfile.mkdtemp(prefix="masld_spark_")))
    print(f"[job] {step}: code shipped to the executors ({how})", flush=True)
    return mod.main(rest + extra, spark=spark)


if __name__ == "__main__":
    sys.exit(main())
