"""Run directory, run log and aggregate-only console output.

runs/<name>/run.json   aggregates only: inputs, fingerprints, config, versions, timings, counts, memory
runs/<name>/private/   the JVM log and Python tracebacks; these can quote record values, so they stay on this machine
                       and are never pasted anywhere
"""
import contextlib
import json
import os
import platform
import resource
import sys
import time
import traceback
from datetime import datetime, timezone

from scripts.public_counts import SMALL, is_small   # the repository's small-cell rule: counts 1-10 print as <11


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def n(v):
    """Format a count for the console under the small-cell rule."""
    if v is None:
        return "unset"
    return SMALL if is_small(v) else f"{v:,}"


def size(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024 or unit == "TB":
            return f"{b:,.0f} {unit}" if unit == "B" else f"{b:,.1f} {unit}"
        b /= 1024


def say(*parts):
    print("  ".join(str(p) for p in parts), flush=True)


class RunLog:
    def __init__(self, runs_root, name, step, cfg):
        self.dir = runs_root / name
        if self.dir.exists():
            raise FileExistsError(f"run directory already exists: {self.dir}")
        self.private = self.dir / "private"
        self.private.mkdir(parents=True)
        self.data = {"run_name": name, "step": step, "started_utc": utc_now(), "status": "running",
                     "config_file": cfg.get("_source"), "config": {k: v for k, v in cfg.items() if k != "_source"},
                     "versions": {"python": sys.version.split()[0], "platform": platform.platform(),
                                  "machine": platform.machine()},
                     "timings_s": {}, "tables": {}}
        self._t0 = time.time()
        self.write()

    @contextlib.contextmanager
    def timer(self, key):
        t = time.time()
        try:
            yield
        finally:
            self.data["timings_s"][key] = round(time.time() - t, 2)

    def private_error(self, where, exc):
        """Full traceback to private/error.log; nothing from the exception is printed."""
        with open(self.private / "error.log", "a") as fh:
            fh.write(f"--- {utc_now()} {where}\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=fh)

    def spark_versions(self, spark):
        v = self.data["versions"]
        v["spark"] = spark.version
        try:
            import pyspark
            v["pyspark"] = pyspark.__version__
        except Exception:
            pass
        try:
            v["java"] = spark.sparkContext._jvm.java.lang.System.getProperty("java.version")
            v["master"] = spark.sparkContext.master
        except Exception:   # Spark Connect sessions expose no JVM
            v["java"] = v["master"] = None

    def memory(self, spark=None):
        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        m = {"driver_python_peak_rss_bytes": int(ru if sys.platform == "darwin" else ru * 1024)}
        if spark is not None:
            try:
                mf = spark.sparkContext._jvm.java.lang.management.ManagementFactory
                pools = [p for p in mf.getMemoryPoolMXBeans() if p.getType().name() == "HEAP"]
                m["jvm_heap_peak_bytes_upper_bound"] = int(sum(p.getPeakUsage().getUsed() for p in pools))
                m["jvm_heap_max_bytes"] = int(mf.getMemoryMXBean().getHeapMemoryUsage().getMax())
            except Exception:
                m["jvm_heap_peak_bytes_upper_bound"] = m["jvm_heap_max_bytes"] = None
        self.data["memory"] = m
        return m

    def write(self):
        self.data["elapsed_s"] = round(time.time() - self._t0, 2)
        tmp = self.dir / "run.json.tmp"
        tmp.write_text(json.dumps(self.data, indent=1, default=str))
        os.replace(tmp, self.dir / "run.json")

    def finish(self, status, exit_code):
        self.data.update(status=status, exit_code=exit_code, ended_utc=utc_now())
        self.write()
