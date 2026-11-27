"""Shared input/output for the steps after the ingest.

ingested()     returns a raw table only if the ingest verified it (_INGEST_OK.json present).
write_table()  writes to a hidden temporary directory, counts the rows from the written files, then renames it into
               place, so a failed write never leaves a half-written table under the final name.
"""
import os
import shutil

from masld_spark import config as C
from masld_spark.ingest import OK_JSON


class StageFailure(Exception):
    """A failure whose message is safe to print: it never contains a record value."""


def ingested(spark, cfg, table):
    d = C.paths(cfg)["out_root"] / "ingest" / table
    if not (d / OK_JSON).exists():
        raise StageFailure(f"{table} has not been verified by the ingest (run make spark-ingest-verify)")
    return spark.read.parquet(str(d))


def write_table(spark, df, out_dir, name, run_name, n_files=1, sort_keys=("hadm_id",), partition_by=None):
    """One file: repartition(1) keeps the upstream stages parallel (coalesce(1) would not).
    Several files: range-partitioned on the first sort key, sorted within each file.
    partition_by: also split into <column>=<value>/ directories (range-partitioned on that column first)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    final, tmp = out_dir / name, out_dir / f".{name}.tmp-{run_name}"
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        if partition_by:
            out = df.repartitionByRange(n_files, partition_by, sort_keys[0])
            out.sortWithinPartitions(partition_by, *sort_keys).write.mode("overwrite") \
               .partitionBy(partition_by).parquet(str(tmp))
        else:
            out = df.repartitionByRange(n_files, sort_keys[0]) if n_files > 1 else df.repartition(1)
            out.sortWithinPartitions(*sort_keys).write.mode("overwrite").parquet(str(tmp))
        rows = spark.read.parquet(str(tmp)).count()
        if final.exists():
            shutil.rmtree(final)
        os.replace(tmp, final)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    files = list(final.rglob("*.parquet"))
    return {"rows": rows, "n_files": len(files), "bytes": sum(f.stat().st_size for f in files)}
