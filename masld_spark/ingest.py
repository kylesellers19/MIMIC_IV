"""Step 1 — ingest the 12 raw .csv.gz files into Parquet, with fingerprints and row-count gates.

Per table:
  1. SHA-256 of the input, checked against the PhysioNet SHA256SUMS*.txt manifests in the raw root. A mismatch stops
     the table before it is read; a file missing from every manifest stops it while ingest.require_manifest_match.
  2. Header check against the published column list. Names outside the schema are counted, never printed (a file
     without a header would otherwise print a data row).
  3. Read with the explicit schema (masld_spark/schemas.py): multi-line records, '"' as both quote and escape
     (RFC 4180 doubled quotes), FAILFAST on any record that does not fit the schema, an error on any unescaped quote.
  4. Stage to Parquet in one pass over the gzip (gzip cannot be split, so this read is one task), then
     range-partition and sort from the staged copy, and move the result into place.
  5. Row count against ingest.expected_rows within ingest.tolerance_pct (percent of the expected count).
       PASS   writes _INGEST_OK.json, which every later step requires
       FAIL   moves the table to data/spark/_quarantine/<run>/<table>/
       UNSET  leaves the table in place, unverified; fill the count in the config and run --verify-only

Partitioning. There is no directory (Hive-style) partitioning at ingest: every later stage joins or aggregates on
subject_id / hadm_id, and no low-cardinality column is filtered on. A table with a subject_id is range-partitioned on
it into ingest.partitions[table] files and sorted by its keys inside each file, so each file covers a disjoint
subject_id range and Parquet min/max statistics let a subject filter skip whole files and row groups. The two
dictionaries are one file each. The note and chunk tables of Step 3 are split into directories by split partition
(DEV / TEST / GOLD_HOLDOUT), so a training job can be pointed at DEV and TEST paths only.

Layout:  data/spark/ingest/<table>/part-*.parquet, _source.json, _INGEST_OK.json
Console: aggregates only (counts 1-10 as <11); no row, value, identifier or note text. Exception messages are never
         printed (Spark can quote the record that failed); tracebacks go to runs/<name>/private/error.log.
Exit:    0 every table verified · 1 any table failed · 3 nothing failed, but some expected counts are unset

Run:  zsh scripts/spark_env.sh -m masld_spark.ingest --config conf/spark_local.yaml [--tables a,b] [--force]
      zsh scripts/spark_env.sh -m masld_spark.ingest --config conf/spark_local.yaml --verify-only
"""
import argparse
import csv
import gzip
import json
import os
import shutil
import sys
import time
from datetime import datetime

from masld_spark import config as C
from masld_spark.fingerprint import check as manifest_check, manifests, sha256_file
from masld_spark.runlog import RunLog, n, say, size, utc_now
from masld_spark.schemas import SCHEMAS, TABLES, column_names, schema_fingerprint
from masld_spark.session import build as build_session

EXIT_OK, EXIT_FAIL, EXIT_UNSET = 0, 1, 3
CSV_OPTIONS = {
    "header": "true", "multiLine": "true", "quote": '"', "escape": '"', "mode": "FAILFAST",
    "unescapedQuoteHandling": "RAISE_ERROR", "nullValue": "", "maxCharsPerColumn": "-1",
    "ignoreLeadingWhiteSpace": "false", "ignoreTrailingWhiteSpace": "false", "encoding": "UTF-8",
}
STAGE_RECORDS_PER_FILE = 5_000_000
SOURCE_JSON, OK_JSON = "_source.json", "_INGEST_OK.json"


class TableFailure(Exception):
    """A failure whose message is safe to print: it never contains a record value."""


def header_problem(path, table):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        first = fh.readline()
    try:
        found = next(csv.reader([first], strict=True), [])
    except csv.Error:   # e.g. a data row whose quoted text continues past the first line
        return "header mismatch: the first line is not a CSV header"
    expected = column_names(table)
    if found == expected:
        return None
    known = set(expected)
    missing = [c for c in expected if c not in found]
    unexpected = sum(1 for c in found if c not in known)
    parts = []
    if missing:
        parts.append(f"missing {missing}")
    if unexpected:
        parts.append(f"{unexpected} unexpected column name(s) (not shown)")
    if not parts:
        parts.append("columns out of order or repeated")
    return "header mismatch: " + "; ".join(parts)


def describe_error(exc):
    """A fixed phrase for the console. The exception text is inspected here and never printed."""
    msg = f"{type(exc).__name__} {exc}"
    if "MALFORMED_RECORD" in msg or "Malformed records" in msg or "BadRecordException" in msg:
        return "a record does not fit the schema (FAILFAST)"
    if "TextParsingException" in msg or "nescaped quote" in msg:
        return "CSV parser error (for example an unescaped quote)"
    if "OutOfMemoryError" in msg or "Java heap space" in msg:
        return "out of memory"
    if "EOFException" in msg or "end of input stream" in msg or "Not in GZIP format" in msg:
        return "truncated or corrupt gzip"
    return f"unexpected error ({type(exc).__name__})"


def count_status(rows, expected, tolerance_pct):
    if expected is None:
        return "UNSET"
    return "PASS" if abs(rows - expected) <= expected * tolerance_pct / 100.0 else "FAIL"


def file_stats(d):
    files = [f for f in d.iterdir() if f.name.endswith(".parquet")]
    return len(files), sum(f.stat().st_size for f in files)


def _read_json(p):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def _ingest(spark, cfg, table, src, final, stage, rec, run_name):
    keys = TABLES[table][1]
    n_parts = cfg["ingest"]["partitions"][table]
    tmp = final.parent / f".{table}.tmp-{run_name}"
    final.parent.mkdir(parents=True, exist_ok=True)
    try:
        t = time.time()
        df = spark.read.format("csv").schema(SCHEMAS[table]).options(**CSV_OPTIONS).load(str(src))
        df.write.mode("overwrite").option("maxRecordsPerFile", STAGE_RECORDS_PER_FILE).parquet(str(stage))
        rec["seconds_read_stage"] = round(time.time() - t, 2)
        staged = spark.read.parquet(str(stage))
        rows = staged.count()
        t = time.time()
        out = staged.repartitionByRange(n_parts, keys[0]) if n_parts > 1 else staged.coalesce(1)
        out.sortWithinPartitions(*keys).write.mode("overwrite").parquet(str(tmp))
        rec["seconds_write"] = round(time.time() - t, 2)
        if spark.read.parquet(str(tmp)).count() != rows:
            raise TableFailure("row count changed between staging and output")
        (tmp / SOURCE_JSON).write_text(json.dumps({
            "table": table, "source": rec["source"], "bytes_in": rec["bytes_in"], "sha256": rec["sha256"],
            "schema_sha256": rec["schema_sha256"], "rows": rows, "partitions": n_parts, "sort_keys": keys,
            "csv_options": CSV_OPTIONS, "run_name": run_name, "written_utc": utc_now()}, indent=1))
        if final.exists():
            shutil.rmtree(final)
        os.replace(tmp, final)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


def ingest_table(spark, cfg, table, log, listed, force=False, verify_only=False):
    """Ingest (or, with verify_only, re-verify) one table. Returns its record, also stored in the run log."""
    run_name = log.data["run_name"]
    p = C.paths(cfg)
    module, _ = TABLES[table]
    src = p["raw_root"] / module / f"{table}.csv.gz"
    final = p["out_root"] / "ingest" / table
    rec = {"source": f"{module}/{table}.csv.gz", "output": str(final), "status": None}
    log.data["tables"][table] = rec
    t_all = time.time()
    try:
        if not src.exists():
            raise TableFailure("input file not found")
        rec["bytes_in"] = src.stat().st_size
        t = time.time()
        rec["sha256"] = sha256_file(src)
        rec["seconds_hash"] = round(time.time() - t, 2)
        rec["manifest"] = manifest_check(src.name, rec["sha256"], listed)
        if rec["manifest"]["status"] == "mismatch":
            raise TableFailure("SHA-256 differs from the PhysioNet manifest")
        if rec["manifest"]["status"] == "missing" and cfg["ingest"]["require_manifest_match"]:
            raise TableFailure("file not listed in any SHA256SUMS manifest")
        problem = header_problem(src, table)
        if problem:
            raise TableFailure(problem)
        rec["schema_sha256"] = schema_fingerprint(table)

        prior = _read_json(final / SOURCE_JSON) if final.exists() else None
        same = bool(prior) and prior.get("sha256") == rec["sha256"] and prior.get("schema_sha256") == rec["schema_sha256"]
        if verify_only:
            if not prior:
                raise TableFailure("not ingested yet (no _source.json)")
            if not same:
                raise TableFailure("ingested from a different file or schema; run the ingest again with --force")
            rec["action"] = "verified existing"
        elif final.exists() and same and not force:
            rec["action"] = "kept existing (same file and schema)"
        elif final.exists() and not force:
            raise TableFailure("output exists from a different file or schema; pass --force to replace it")
        else:
            rec["action"] = "ingested"
            _ingest(spark, cfg, table, src, final, p["out_root"] / "_staging" / run_name / table, rec, run_name)

        rows = spark.read.parquet(str(final)).count()
        if rec["action"] != "ingested" and rows != prior.get("rows"):
            raise TableFailure("row count differs from the one recorded at ingest")
        rec["rows"] = rows
        rec["n_files"], rec["bytes_out"] = file_stats(final)
        expected, tol = cfg["ingest"]["expected_rows"][table], cfg["ingest"]["tolerance_pct"]
        rec.update(expected_rows=expected, tolerance_pct=tol, count_status=count_status(rows, expected, tol))
        (final / OK_JSON).unlink(missing_ok=True)
        if rec["count_status"] == "PASS":
            (final / OK_JSON).write_text(json.dumps({
                "table": table, "sha256": rec["sha256"], "schema_sha256": rec["schema_sha256"], "rows": rows,
                "expected_rows": expected, "tolerance_pct": tol, "run_name": run_name, "verified_utc": utc_now()}, indent=1))
            rec["status"] = "PASS"
        elif rec["count_status"] == "UNSET":
            rec["status"] = "UNSET"
        else:
            q = p["out_root"] / "_quarantine" / run_name / table
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(final), str(q))
            rec.update(status="FAIL", error="row count outside tolerance; table moved to quarantine", quarantined_to=str(q))
    except TableFailure as e:
        rec.update(status="FAIL", error=str(e))
    except Exception as e:   # noqa: BLE001 — classified, never printed
        rec.update(status="FAIL", error=describe_error(e))
        log.private_error(table, e)
    finally:
        rec["seconds_total"] = round(time.time() - t_all, 2)
        log.write()
    return rec


def print_table(table, rec):
    head = f"[{table}]".ljust(19) + f"{rec['status']:<6}"
    if rec["status"] == "FAIL" and "rows" not in rec:
        say(head, rec.get("error", ""))
        return
    tol = rec.get("tolerance_pct")
    parts = [head, f"rows {n(rec['rows'])}", f"expected {n(rec.get('expected_rows'))} (±{tol}%)",
             f"manifest {rec['manifest']['status']}", f"{rec['n_files']} file(s) {size(rec['bytes_out'])}",
             f"in {size(rec['bytes_in'])}", rec["action"]]
    t = [f"{k} {rec[f'seconds_{k}']:.1f}s" for k in ("hash", "read_stage", "write") if f"seconds_{k}" in rec]
    parts.append(" ".join(t))
    if rec["status"] == "FAIL":
        parts.append(rec.get("error", ""))
    say(*parts)


def main(argv=None, spark=None):
    ap = argparse.ArgumentParser(description="Step 1: ingest raw MIMIC-IV .csv.gz files into Parquet (aggregates only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    ap.add_argument("--tables", help="comma-separated subset (default: all 12)")
    ap.add_argument("--force", action="store_true", help="replace a table ingested from a different file or schema")
    ap.add_argument("--verify-only", action="store_true",
                    help="re-hash inputs and re-check row counts of tables already ingested; reads no CSV")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
    except (OSError, C.ConfigError, ValueError) as e:   # config problems only; no data is involved yet
        say("[ingest] config error:", e)
        return EXIT_FAIL
    tables = list(TABLES) if not a.tables else [t.strip() for t in a.tables.split(",") if t.strip()]
    unknown = [t for t in tables if t not in TABLES]
    if unknown:
        say("[ingest] unknown table name(s):", ", ".join(unknown))
        return EXIT_FAIL
    p = C.paths(cfg)
    step = "ingest-verify" if a.verify_only else "ingest"
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-{step}-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(p["runs_root"], name, step, cfg)
    log.data["arguments"] = {"tables": tables, "force": a.force, "verify_only": a.verify_only}
    own_session = spark is None
    code, status = EXIT_FAIL, "FAIL"
    try:
        with log.timer("session_start"):
            if own_session:
                spark = build_session(cfg, log.private)
        log.spark_versions(spark)
        v = log.data["versions"]
        say(f"[{step}] run {name}", f"Spark {v['spark']}", f"Java {v.get('java')}", f"master {v.get('master')}",
            f"Python {v['python']}")
        names, listed = manifests(p["raw_root"])
        log.data["manifests"] = names
        say(f"[{step}] manifests found: {len(names)}", f"tables: {len(tables)}")
        with log.timer("tables"):
            for t in tables:
                print_table(t, ingest_table(spark, cfg, t, log, listed, force=a.force, verify_only=a.verify_only))
        recs = [log.data["tables"][t] for t in tables]
        fails = [t for t, r in zip(tables, recs) if r["status"] == "FAIL"]
        unset = [t for t, r in zip(tables, recs) if r["status"] == "UNSET"]
        ok = len(tables) - len(fails) - len(unset)
        code = EXIT_FAIL if fails else EXIT_UNSET if unset else EXIT_OK
        status = "FAIL" if fails else "UNSET" if unset else "PASS"
        say(f"[{step}] verified {ok} · unset {len(unset)} · failed {len(fails)} of {len(tables)} table(s)")
        if fails:
            say(f"[{step}] failed:", ", ".join(fails))
        if unset:
            say(f"[{step}] expected count not set for:", ", ".join(unset),
                "— check the counts above, put them in ingest.expected_rows, then run make spark-ingest-verify")
    except Exception as e:   # noqa: BLE001
        log.private_error("run", e)
        say(f"[{step}] run failed:", describe_error(e))
    finally:
        m = log.memory(spark)
        heap = m.get("jvm_heap_peak_bytes_upper_bound")
        say(f"[{step}] peak memory: driver Python {size(m['driver_python_peak_rss_bytes'])}",
            f"JVM heap ≤ {size(heap)} of {size(m['jvm_heap_max_bytes'])}" if heap is not None else "JVM heap not available",
            f"elapsed {time.time() - log._t0:,.0f}s")
        if own_session and spark is not None:
            spark.stop()
        log.finish(status, code)
        say(f"[{step}] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
