"""Step 6a — parity: the Spark outputs against the current (DuckDB) pipeline's stored files, counts only.

The current pipeline is not re-run: its writers overwrite frozen files (clean_population.py, build_2x2.py,
run0919_phase2_splits.py). Its stored outputs, made from the same checksummed raw files, are compared instead. The
two that are frozen (analysis_population_clean, splits_v1) are compared only after their SHA-256 matches
docs/run_2026-11-10/results/frozen_hashes_end.json; every other stored file's SHA-256 is recorded in the run log.

The comparison runs in DuckDB, which reads both pipelines' Parquet (Spark refuses the nanosecond timestamps DuckDB
can write). Per table: rows on each side, keys only on one side, duplicate keys, and for every shared column the
number of keys whose values differ (numbers within parity.float_tolerance relative, NaN read as null, timestamps
compared as wall-clock values).

Expected differences. Where DuckDB's arg_min / arg_max meets two results at the same charttime, it keeps either one;
Spark keeps the lowest (first) or highest (last) labevent_id. The tied (admission, analyte) pairs are rebuilt here
from the ingested labevents with the same rules as Step 2, and a difference on a tied pair is counted as explained:
lab_* and miss_lab_* (cleaned first values), first_val_* / last_val_* / pre365_* (lab features), out_* (outpatient
FIB-4 inputs), and cmrf_ge1 / cmrf_unasc_all on admissions with a tied HbA1c, glucose, triglyceride or HDL value.
Any other difference is unexplained.

Labels (definitions a, b, c and code status) are also shown as agreement tables: both positive, Spark only, stored
only, both negative.

Requires data/spark/_GATES_OK.json. Exit 0 when every key set agrees and no difference is unexplained, else 1.
Console: aggregates only (counts 1-10 as <11). Reads nothing sealed (no GOLD_HOLDOUT language-model or locked
prediction file).
Run:  zsh scripts/spark_env.sh -m masld_spark.parity --config conf/spark_local.yaml
"""
import argparse
import json
import sys
import time
from datetime import datetime

import duckdb

from masld_spark import config as C
from masld_spark import definitions as D
from masld_spark.fingerprint import sha256_file
from masld_spark.gates import GATES_OK
from masld_spark.runlog import RunLog, n, say
from masld_spark.stageio import StageFailure

EXIT_OK, EXIT_FAIL = 0, 1
DEFAULTS = {
    "stored": {
        "locked_population": "data/processed/analysis_population.parquet",
        "clean_population": "data/processed/analysis_population_clean.parquet",
        "cmrf": "data/processed/cmrf.parquet",
        "lab_features": "data/processed/run_2026-09-19_lab_features.parquet",
        "outpatient_fib4_inputs": "data/processed/run_2026-11-10_outpt_fib4.parquet",
        "frame": "data/processed/aim1a_frame.parquet",
        "splits": "data/processed/splits_v1.parquet",
        "notes_index": ["data/processed/run_2026-09-19_notes_index/discharge.parquet",
                        "data/processed/run_2026-09-19_notes_index/radiology.parquet"],
    },
    "frozen_hashes": "docs/run_2026-11-10/results/frozen_hashes_end.json",
    "float_tolerance": 1e-9,
}
# name, Spark table (under out_root), stored file key, key columns, columns compared (None = every shared column)
COMPARISONS = [
    ("population_locked", "cohort/population_locked", "locked_population", ["hadm_id"], None),
    ("population_clean", "cohort/population_clean", "clean_population", ["hadm_id"], None),
    ("cmrf", "cohort/cmrf", "cmrf", ["hadm_id"], None),
    ("lab_features", "cohort/lab_features", "lab_features", ["hadm_id"], None),
    ("outpatient_fib4_inputs", "cohort/outpatient_fib4_inputs", "outpatient_fib4_inputs", ["hadm_id"], None),
    ("splits", "splits/admission_splits", "splits", ["hadm_id"], None),
    ("labels", "notes/labels_rule", "frame", ["hadm_id"], ["subject_id", "code_positive", "note_a", "note_b", "note_c"]),
    ("notes_index", "notes/notes", "notes_index", ["note_id"],
     ["hadm_id", "subject_id", "charttime", "n_chars", "a_pos", "b_pos", "c_hedged", "n_pos", "n_hist", "n_tierC",
      "n_neg", "liver_incl"]),
]
NUMERIC = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT",
           "FLOAT", "DOUBLE", "REAL", "DECIMAL")
CMRF_LAB_ANALYTES = ("HbA1c", "Glucose", "Triglycerides", "HDL")


def settings(cfg):
    s = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULTS.items()}
    over = cfg.get("parity") or {}
    s["stored"].update(over.get("stored") or {})
    for k in ("frozen_hashes", "float_tolerance"):
        if k in over:
            s[k] = over[k]
    return s


def _q(p):
    return "'" + str(p).replace("'", "''") + "'"


def _paths(v):
    return [C.resolve(x) for x in (v if isinstance(v, list) else [v])]


def _kind(t):
    t = t.upper()
    if t.startswith(NUMERIC):
        return "num"
    if t == "BOOLEAN":
        return "bool"
    if t.startswith("TIMESTAMP") or t == "DATE":
        return "time"
    return "str"


def _cmp(col, ks, kd, tol):
    a, b = f's."{col}"', f'd."{col}"'
    if ks == "bool" and kd == "num":
        a = f"CAST({a} AS INTEGER)"; ks = "num"
    if kd == "bool" and ks == "num":
        b = f"CAST({b} AS INTEGER)"; kd = "num"
    if ks == kd == "num":
        x = f"(CASE WHEN isnan(CAST({a} AS DOUBLE)) THEN NULL ELSE CAST({a} AS DOUBLE) END)"
        y = f"(CASE WHEN isnan(CAST({b} AS DOUBLE)) THEN NULL ELSE CAST({b} AS DOUBLE) END)"
        return f"(({x} IS NULL AND {y} IS NULL) OR abs({x} - {y}) <= {tol} * greatest(1.0, abs({y})))"
    if ks == kd == "time":
        return f"(CAST({a} AS TIMESTAMP) IS NOT DISTINCT FROM CAST({b} AS TIMESTAMP))"
    if ks == kd:
        return f"({a} IS NOT DISTINCT FROM {b})"
    return f"(CAST({a} AS VARCHAR) IS NOT DISTINCT FROM CAST({b} AS VARCHAR))"


# --- tied lab results (the same rules as Step 2)
def build_tie_tables(con, out_root):
    lab = _q(out_root / "ingest" / "labevents" / "*.parquet")
    pop = _q(out_root / "cohort" / "population_locked" / "*.parquet")

    def case(ids):
        return "CASE itemid " + " ".join(f"WHEN {i} THEN '{k}'" for k, i in ids.items()) + " END"

    con.execute(f"CREATE TEMP TABLE pop AS SELECT hadm_id, subject_id, admittime, dischtime FROM read_parquet({pop})")
    con.execute(f"""CREATE TEMP TABLE ev AS SELECT labevent_id, subject_id, hadm_id, itemid, charttime, valuenum
                    FROM read_parquet({lab}) WHERE valuenum IS NOT NULL
                      AND itemid IN ({",".join(str(i) for i in D.ANALYTE_IDS.values())})""")

    def ties(name, rows_sql, extreme):
        con.execute(f"""CREATE TEMP TABLE {name} AS
          WITH r AS ({rows_sql}),
               x AS (SELECT hadm_id, analyte, {extreme}(charttime) AS t FROM r GROUP BY ALL)
          SELECT r.hadm_id, r.analyte FROM r JOIN x USING (hadm_id, analyte)
          WHERE r.charttime = x.t GROUP BY ALL HAVING count(DISTINCT r.valuenum) > 1""")
        return con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]

    clean_rows = f"""SELECT e.hadm_id, {case(D.ANALYTE_IDS)} AS analyte, e.charttime, e.valuenum FROM ev e
                     WHERE e.hadm_id IN (SELECT hadm_id FROM pop) AND e.charttime IS NOT NULL"""
    inadm_rows = f"""SELECT e.hadm_id, {case(D.LAB_ITEMIDS)} AS analyte, e.charttime, e.valuenum FROM ev e
                     JOIN pop p USING (hadm_id) WHERE e.itemid IN ({",".join(str(i) for i in D.LAB_ITEMIDS.values())})
                       AND e.charttime <= p.dischtime"""

    def window_rows(names):
        ids = {k: D.LAB_ITEMIDS[k] for k in names}
        return f"""SELECT p.hadm_id, {case(ids)} AS analyte, e.charttime, e.valuenum
                   FROM ev e JOIN pop p ON e.subject_id = p.subject_id AND e.hadm_id IS NULL
                   WHERE e.itemid IN ({",".join(str(i) for i in ids.values())})
                     AND e.charttime < p.admittime AND e.charttime >= p.admittime - INTERVAL 365 DAY"""

    return {"ties_clean": ties("ties_clean", clean_rows, "min"),
            "ties_first": ties("ties_first", inadm_rows, "min"),
            "ties_last": ties("ties_last", inadm_rows, "max"),
            "ties_pre": ties("ties_pre", window_rows(D.PRE365_ANALYTES), "max"),
            "ties_out": ties("ties_out", window_rows(D.OUTPT_FIB4_ANALYTES), "max")}


def explanation(name, col):
    """SQL predicate (over the joined row `s`) under which a difference in this column is expected, or None."""
    def tie(table, analytes):
        lst = ",".join(f"'{a}'" for a in analytes)
        return f"EXISTS (SELECT 1 FROM {table} t WHERE t.hadm_id = s.hadm_id AND t.analyte IN ({lst}))"
    for prefix, table, names in (("lab_", "ties_clean", D.ANALYTE_IDS), ("miss_lab_", "ties_clean", D.ANALYTE_IDS),
                                 ("first_val_", "ties_first", D.LAB_ITEMIDS), ("last_val_", "ties_last", D.LAB_ITEMIDS),
                                 ("pre365_", "ties_pre", D.PRE365_ANALYTES), ("out_", "ties_out", D.OUTPT_FIB4_ANALYTES)):
        if col.startswith(prefix) and col[len(prefix):] in names:
            if prefix == "lab_" and name != "population_clean":
                continue
            return tie(table, [col[len(prefix):]])
    if name == "cmrf" and col in ("cmrf_ge1", "cmrf_unasc_all"):
        return tie("ties_clean", CMRF_LAB_ANALYTES)
    return None


# --- one comparison
def compare(con, name, spark_dir, stored_paths, keys, cols, tol):
    hive = any(p.is_dir() and p.name.startswith("partition=") for p in spark_dir.iterdir())
    glob = spark_dir / "**" / "*.parquet" if hive else spark_dir / "*.parquet"
    con.execute(f"CREATE OR REPLACE TEMP VIEW s AS SELECT * FROM read_parquet({_q(glob)}, hive_partitioning = {str(hive).lower()})")
    files = "[" + ", ".join(_q(p) for p in stored_paths) + "]"
    con.execute(f"CREATE OR REPLACE TEMP VIEW d AS SELECT * FROM read_parquet({files}, union_by_name = true)")
    ts = {r[0]: r[1] for r in con.execute("DESCRIBE s").fetchall()}
    td = {r[0]: r[1] for r in con.execute("DESCRIBE d").fetchall()}
    if hive:                                   # the directory column is a storage detail, not a compared value
        ts.pop("partition", None)
    shared = [c for c in ts if c in td and c not in keys]
    if cols is not None:
        shared = [c for c in cols if c in ts and c in td]
    k = ", ".join(keys)
    on = " AND ".join(f"s.{x} = d.{x}" for x in keys)
    r = {"spark_rows": con.execute("SELECT count(*) FROM s").fetchone()[0],
         "stored_rows": con.execute("SELECT count(*) FROM d").fetchone()[0],
         "spark_duplicate_keys": con.execute(f"SELECT count(*) - count(DISTINCT ({k})) FROM s").fetchone()[0],
         "stored_duplicate_keys": con.execute(f"SELECT count(*) - count(DISTINCT ({k})) FROM d").fetchone()[0],
         "only_spark": con.execute(f"SELECT count(*) FROM s WHERE NOT EXISTS (SELECT 1 FROM d WHERE {on})").fetchone()[0],
         "only_stored": con.execute(f"SELECT count(*) FROM d WHERE NOT EXISTS (SELECT 1 FROM s WHERE {on})").fetchone()[0],
         "columns_spark_only": sorted(c for c in ts if c not in td),
         "columns_stored_only": sorted(c for c in td if c not in ts),
         "columns": {}}
    for c in shared:
        cond = _cmp(c, _kind(ts[c]), _kind(td[c]), tol)
        ex = explanation(name, c)
        sel = f"sum(CASE WHEN NOT {cond} THEN 1 ELSE 0 END)"
        sel_ex = f", sum(CASE WHEN NOT {cond} AND {ex} THEN 1 ELSE 0 END)" if ex else ""
        row = con.execute(f"SELECT {sel}{sel_ex} FROM s JOIN d ON {on}").fetchone()
        diff = int(row[0] or 0)
        expl = int(row[1] or 0) if ex else 0
        r["columns"][c] = {"differ": diff, "explained_by_ties": expl, "unexplained": diff - expl}
    return r


def agreement(con, keys, cols):
    on = " AND ".join(f"s.{x} = d.{x}" for x in keys)
    out = {}
    for c in cols:
        row = con.execute(f"""SELECT sum(CASE WHEN s.{c} AND d.{c} THEN 1 ELSE 0 END),
                                     sum(CASE WHEN s.{c} AND NOT d.{c} THEN 1 ELSE 0 END),
                                     sum(CASE WHEN NOT s.{c} AND d.{c} THEN 1 ELSE 0 END),
                                     sum(CASE WHEN NOT s.{c} AND NOT d.{c} THEN 1 ELSE 0 END)
                              FROM s JOIN d ON {on}""").fetchone()
        out[c] = dict(zip(("both", "spark_only", "stored_only", "neither"), (int(x or 0) for x in row)))
    return out


def run_parity(cfg, log):
    out_root = C.paths(cfg)["out_root"]
    if not (out_root / GATES_OK).exists():
        raise StageFailure("the validation gates have not passed (no data/spark/_GATES_OK.json); run make spark-gates")
    s = settings(cfg)
    frozen = json.loads(C.resolve(s["frozen_hashes"]).read_text()).get("frozen") or {}
    log.data["stored_files"] = {}
    for key, v in s["stored"].items():
        for p, raw in zip(_paths(v), (v if isinstance(v, list) else [v])):
            if not p.exists():
                raise StageFailure(f"stored file not found: {raw}")
            digest = sha256_file(p)
            rec = {"sha256": digest, "bytes": p.stat().st_size}
            if raw in frozen:
                rec["frozen_sha256"] = frozen[raw]["sha256"]
                if digest != frozen[raw]["sha256"]:
                    raise StageFailure(f"{raw} differs from its frozen SHA-256; parity against it would be meaningless")
            log.data["stored_files"][raw] = rec
    say("[parity] stored files:", f"{len(log.data['stored_files'])} hashed;",
        "the frozen ones match their record")
    con = duckdb.connect()
    con.execute("SET memory_limit='12GB'")
    t = time.time()
    log.data["ties"] = build_tie_tables(con, out_root)
    say("[parity] tied lab results rebuilt:", *[f"{k} {n(v)}" for k, v in log.data["ties"].items()],
        f"({time.time() - t:.0f}s)")
    tol = float(s["float_tolerance"])
    results, bad = {}, []
    for name, rel, key, keys, cols in COMPARISONS:
        t = time.time()
        r = compare(con, name, out_root / rel, _paths(s["stored"][key]), keys, cols, tol)
        if name == "labels":
            r["agreement"] = agreement(con, keys, ["code_positive", "note_a", "note_b", "note_c"])
        r["seconds"] = round(time.time() - t, 1)
        results[name] = r
        log.data["parity"] = results
        log.write()
        unexplained = {c: v["unexplained"] for c, v in r["columns"].items() if v["unexplained"]}
        explained = {c: v["explained_by_ties"] for c, v in r["columns"].items() if v["explained_by_ties"]}
        keys_ok = r["only_spark"] == 0 and r["only_stored"] == 0 and r["spark_duplicate_keys"] == 0
        if not keys_ok or unexplained:
            bad.append(name)
        say(f"[{name}]".ljust(25), f"rows {n(r['spark_rows'])} / {n(r['stored_rows'])}",
            f"only Spark {n(r['only_spark'])}", f"only stored {n(r['only_stored'])}",
            f"duplicate keys {n(r['spark_duplicate_keys'])} / {n(r['stored_duplicate_keys'])}",
            f"{len(r['columns'])} columns compared",
            "all agree" if not unexplained and not explained and keys_ok else "")
        if explained:
            say(" " * 25, "differences on tied results:", *[f"{c} {n(v)}" for c, v in sorted(explained.items())])
        if unexplained:
            say(" " * 25, "UNEXPLAINED differences:", *[f"{c} {n(v)}" for c, v in sorted(unexplained.items())])
        if r["columns_spark_only"] or r["columns_stored_only"]:
            say(" " * 25, f"columns only in Spark: {len(r['columns_spark_only'])}",
                f"only stored: {len(r['columns_stored_only'])} (listed in the run log)")
        if name == "labels":
            for c, a in r["agreement"].items():
                say(" " * 25, f"{c:<14}", f"both {n(a['both'])}", f"Spark only {n(a['spark_only'])}",
                    f"stored only {n(a['stored_only'])}", f"neither {n(a['neither'])}")
    say(f"[parity] {len(COMPARISONS) - len(bad)} of {len(COMPARISONS)} tables agree"
        + (" (differences only on tied lab results)" if not bad else f"; check: {', '.join(bad)}"))
    return EXIT_OK if not bad else EXIT_FAIL


def main(argv=None):
    ap = argparse.ArgumentParser(description="Step 6a: parity with the current pipeline's stored files (counts only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
    except (OSError, C.ConfigError, ValueError) as e:
        say("[parity] config error:", e)
        return EXIT_FAIL
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-parity-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(C.paths(cfg)["runs_root"], name, "parity", cfg)
    log.data["versions"]["duckdb"] = duckdb.__version__
    code = EXIT_FAIL
    try:
        say(f"[parity] run {name}", f"DuckDB {duckdb.__version__}")
        code = run_parity(cfg, log)
    except StageFailure as e:
        say("[parity] stopped:", e)
    except Exception as e:   # noqa: BLE001 — class only; DuckDB messages can quote values
        log.private_error("parity", e)
        say("[parity] run failed:", f"unexpected error ({type(e).__name__})")
    finally:
        log.memory()
        log.finish("PASS" if code == EXIT_OK else "FAIL", code)
        say(f"[parity] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
