#!/usr/bin/env python3
"""Smoke test of the cluster path, on invented data only: every step as its own job through scripts/spark_job.py,
against a Spark standalone cluster (start one with `zsh scripts/spark_standalone.sh start`).

It writes the invented hospital of tests/spark/cohort_fixture.py as .csv.gz files with a manifest, a split file, the
reference files and a tiny tokenizer into runs/_standalone/smoke-<time>/, plus a config that extends
conf/spark_standalone.yaml, then runs ingest, cohort, splits, notes, gates and scale as separate driver processes
with no PYTHONPATH. It checks each exit status and that every step ran on the cluster's master, not in local mode.
No MIMIC file is read.

Run:  zsh scripts/spark_env.sh scripts/spark_cluster_smoke.py [--master spark://127.0.0.1:7077]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests" / "spark")]

import yaml  # noqa: E402

import pipeline_fixture as PF  # noqa: E402
import synthetic as SY  # noqa: E402
from masld_spark import config as C  # noqa: E402
from masld_spark.schemas import TABLES  # noqa: E402

STEPS = ["ingest", "cohort", "splits", "notes", "gates", "scale"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="spark://127.0.0.1:7077")
    a = ap.parse_args()
    root = ROOT / "runs" / "_standalone" / f"smoke-{datetime.now():%Y%m%d-%H%M%S}"
    root.mkdir(parents=True)
    rows = PF._rows(drop_mismatch=True)
    cfg = PF.make_config(root, rows)
    raw = C.paths(cfg)["raw_root"]
    SY.write_manifest(raw, [SY.write_csv_gz(raw / TABLES[t][0] / f"{t}.csv.gz", t, rows[t]) for t in TABLES])
    base = C.load("conf/spark_standalone.yaml")
    conf = dict(base["spark"]["conf"], **{"spark.driver.memory": "2g", "spark.executor.memory": "2g",
                                          "spark.executor.cores": 2, "spark.cores.max": 4,
                                          "spark.sql.shuffle.partitions": 8})
    cfg["spark"] = {"master": a.master, "app_name": "masld-spark-smoke", "conf": conf}
    cfg["cohort"]["clean_rows_expected"] = 3          # the invented hospital's cleaned population
    out = {k: v for k, v in cfg.items() if not k.startswith("_")}
    (root / "smoke.yaml").write_text(yaml.safe_dump(out, sort_keys=False))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYSPARK_PYTHON", "PYSPARK_DRIVER_PYTHON")}
    env["JAVA_HOME"] = env.get("SPARK_JAVA_HOME", "/opt/homebrew/opt/openjdk@21")
    print(f"[smoke] invented data and config in {root.relative_to(ROOT)}; master {a.master}", flush=True)
    results = {}
    for step in STEPS:
        t = time.time()
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "spark_job.py"), step, "--config",
                            str(root / "smoke.yaml"), "--run-name", f"smoke-{step}"],
                           cwd=str(root), env=env, capture_output=True, text=True)
        (root / f"{step}.out").write_text(p.stdout + "\n--- stderr ---\n" + p.stderr)
        run = root / "runs" / f"smoke-{step}" / "run.json"
        master = json.loads(run.read_text()).get("versions", {}).get("master") if run.exists() else None
        results[step] = {"exit": p.returncode, "master": master, "seconds": round(time.time() - t, 1)}
        print(f"[smoke] {step:<7} exit {p.returncode}  master {master}  {results[step]['seconds']}s", flush=True)
        if p.returncode != 0:
            print(f"[smoke] stopped: {step} failed; its output is in {(root / f'{step}.out').relative_to(ROOT)}")
            return 1
    on_cluster = all((r["master"] or "").startswith("spark://") for s, r in results.items() if s != "scale")
    print(f"[smoke] every step passed; ran on the standalone master: {'yes' if on_cluster else 'NO'}")
    return 0 if on_cluster else 1


if __name__ == "__main__":
    sys.exit(main())
