"""Step 6b — scale report: wall-clock time per stage, peak memory, rows and notes processed, tokens per second.

Reads the latest successful run log of each step from runs/ (aggregates only) and sums Step 3's token counts (DuckDB
over data/spark/notes/token_counts). Writes runs/<name>/run.json with a `scale` section and prints the table.
The current pipeline did not record its stage timings in a comparable form, so no side-by-side timing is claimed.
Peak JVM heap is the sum of the heap pools' peaks, an upper bound on the true peak.

Run:  zsh scripts/spark_env.sh -m masld_spark.scale --config conf/spark_local.yaml
"""
import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime

from masld_spark import config as C
from masld_spark.runlog import RunLog, n, say, size

EXIT_OK, EXIT_FAIL = 0, 1
STEPS = ("ingest", "ingest-verify", "cohort", "splits", "notes", "gates", "parity")


def latest_runs(runs_root, exclude=None):
    best = {}
    for p in sorted(runs_root.glob("*/run.json")):
        if exclude and p.parent.name == exclude:
            continue
        try:
            d = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        step, code = d.get("step"), d.get("exit_code")
        ok = code == 0 or (step == "ingest" and code == 3)       # an ingest with unset expected counts still ran fully
        if step in STEPS and ok and d.get("started_utc", "") >= best.get(step, {}).get("started_utc", ""):
            best[step] = d
    return best


def machine():
    m = {"platform": platform.platform(), "machine": platform.machine(), "cores": os.cpu_count()}
    try:
        if sys.platform == "darwin":
            m["memory_bytes"] = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout)
        else:
            with open("/proc/meminfo") as fh:
                m["memory_bytes"] = int(fh.readline().split()[1]) * 1024
    except (OSError, ValueError):
        m["memory_bytes"] = None
    return m


def token_totals(out_root):
    d = out_root / "notes" / "token_counts"
    if not d.exists():
        return {}
    import duckdb
    con = duckdb.connect()
    glob = str(d / "**" / "*.parquet").replace("'", "''")
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{glob}', hive_partitioning = true)").fetchall()
            if r[0].startswith("n_tokens_")]
    if not cols:
        return {}
    rows = con.execute(f"SELECT variant, {', '.join(f'sum({c})' for c in cols)} FROM read_parquet('{glob}', hive_partitioning = true) "
                       "GROUP BY variant ORDER BY variant").fetchall()
    return {c[len("n_tokens_"):]: {r[0]: int(r[i + 1] or 0) for r in rows} for i, c in enumerate(cols)}


def build_report(cfg, exclude=None):
    p = C.paths(cfg)
    runs = latest_runs(p["runs_root"], exclude)
    rep = {"machine": machine(), "stages": {}, "totals": {}}
    for step in STEPS:
        d = runs.get(step)
        if not d:
            continue
        mem = d.get("memory") or {}
        rep["stages"][step] = {
            "run_name": d["run_name"], "elapsed_s": d.get("elapsed_s"), "status": d.get("status"),
            "versions": {k: d.get("versions", {}).get(k) for k in ("spark", "java", "python", "master", "duckdb")},
            "driver_python_peak_rss_bytes": mem.get("driver_python_peak_rss_bytes"),
            "jvm_heap_peak_bytes_upper_bound": mem.get("jvm_heap_peak_bytes_upper_bound"),
            "jvm_heap_max_bytes": mem.get("jvm_heap_max_bytes"),
            "tables": {t: {k: v.get(k) for k in ("rows", "bytes_out", "bytes", "seconds", "seconds_total",
                                                 "seconds_read_stage", "seconds_write") if k in v}
                       for t, v in (d.get("tables") or {}).items()},
            "timings_s": d.get("timings_s") or {},
        }
    ing = runs.get("ingest")
    if ing:
        rep["totals"]["raw_rows"] = sum((v.get("rows") or 0) for v in ing["tables"].values())
        rep["totals"]["raw_bytes"] = sum((v.get("bytes_in") or 0) for v in ing["tables"].values())
    nt = runs.get("notes")
    if nt:
        rep["totals"]["notes"] = (nt.get("tables", {}).get("notes") or {}).get("rows")
        rep["totals"]["notes_linked"] = (nt.get("summary") or {}).get("notes_in_population")
        tok = token_totals(p["out_root"])
        rep["totals"]["tokens"] = tok
        secs = (nt.get("timings_s") or {}).get("tokenize")
        total = sum(sum(v.values()) for v in tok.values())
        rep["totals"]["tokenize_seconds"] = secs
        rep["totals"]["tokens_all"] = total
        cores = rep["machine"]["cores"] or 1
        if secs:
            rep["totals"]["tokens_per_second"] = round(total / secs)
            rep["totals"]["tokens_per_second_per_core"] = round(total / secs / cores)
    return rep


def print_report(rep):
    m = rep["machine"]
    say("[scale] machine:", m["platform"], f"{m['cores']} cores",
        size(m["memory_bytes"]) if m.get("memory_bytes") else "memory n/a")
    say(f"{'step':<15}{'run':<36}{'elapsed':>10}{'JVM heap peak ≤':>18}{'driver Python':>15}")
    for step, s in rep["stages"].items():
        heap = s["jvm_heap_peak_bytes_upper_bound"]
        py = s["driver_python_peak_rss_bytes"]
        say(f"{step:<15}{s['run_name']:<36}{(s['elapsed_s'] or 0):>9,.0f}s"
            f"{(size(heap) if heap else 'n/a'):>18}{(size(py) if py else 'n/a'):>15}")
    t = rep["totals"]
    if "raw_rows" in t:
        say("[scale] raw rows ingested:", n(t["raw_rows"]), f"({size(t['raw_bytes'])} of .csv.gz)")
    if t.get("notes") is not None:
        say("[scale] notes processed:", n(t["notes"]), f"linked to the population and tokenized: {n(t.get('notes_linked'))}")
    for k, v in (t.get("tokens") or {}).items():
        say(f"[scale] tokens {k}:", *[f"{var} {n(x)}" for var, x in v.items()])
    if t.get("tokens_per_second"):
        say("[scale] tokenizing:", f"{n(t['tokens_all'])} tokens in {t['tokenize_seconds']:,.0f}s",
            f"= {n(t['tokens_per_second'])} tokens/s ({n(t['tokens_per_second_per_core'])} per core)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Step 6b: scale report from the run logs (aggregates only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
    except (OSError, C.ConfigError, ValueError) as e:
        say("[scale] config error:", e)
        return EXIT_FAIL
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-scale-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(C.paths(cfg)["runs_root"], name, "scale", cfg)
    code = EXIT_FAIL
    try:
        rep = build_report(cfg, exclude=name)
        log.data["scale"] = rep
        print_report(rep)
        code = EXIT_OK
    except Exception as e:   # noqa: BLE001
        log.private_error("scale", e)
        say("[scale] failed:", f"unexpected error ({type(e).__name__})")
    finally:
        log.finish("PASS" if code == EXIT_OK else "FAIL", code)
        say(f"[scale] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
