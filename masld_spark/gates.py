"""Step 5 — validation gates over every stage, before anything downstream reads the output.

Each gate belongs to a stage (ingest -> cohort -> splits -> notes). If any gate fails, the earliest failing stage
and every stage after it (they are built from it) are moved to data/spark/_quarantine/<run>/, data/spark/_GATES_OK.json
is removed, and the run exits 1. When every gate passes, _GATES_OK.json records the stage markers and table counts;
anything downstream (the parity report, a training job) requires it. `--restore <run>` moves quarantined stages back
after review; the gates must then pass again.

Gates
  ingest  every table verified by the ingest; its input file still has the SHA-256 recorded at ingest; rows equal
          ingest.expected_rows; no nulls in identifier and time keys that the published DDL declares NOT NULL;
          no duplicate hadm_id (admissions), subject_id (patients), note_id (discharge, radiology, and across both);
          orphans at most gates.max_orphan_pct percent: discharge notes whose hadm_id is not an admission,
          radiology notes whose non-null hadm_id is not an admission, notes whose subject is not a patient,
          diagnoses whose hadm_id is not an admission, admissions whose subject is not a patient
  cohort  the Step 2 marker; population counts against cohort.reference (the counts the current pipeline recorded);
          no nulls in the population's key fields; one row per admission in every admission-level table
  splits  the Step 4 marker; the source SHA-256 recorded in it is the frozen one; one split row per population admission
  notes   the Step 3 marker; one row per note and note_id unique; one label per population admission, none null;
          GOLD_HOLDOUT isolation: no GOLD_HOLDOUT subject under any other partition directory and no other subject
          under partition=GOLD_HOLDOUT, in every partitioned table; only known partition values; token counts for
          every linked note x variant, none null; chunks: every chunk at most its window, every (note, variant) has
          chunk indexes 0..n_chunks-1 exactly once, all chunks open with one id and close with one id
Null rates of every ingest column are reported in the run log (informational; only the keys above are gated).
Membership agreement with the current pipeline's stored files is Step 6 (masld_spark/parity.py).

Console: aggregates only (counts 1-10 as <11).
Run:  zsh scripts/spark_env.sh -m masld_spark.gates --config conf/spark_local.yaml
      zsh scripts/spark_env.sh -m masld_spark.gates --config conf/spark_local.yaml --restore <run name>
"""
import argparse
import json
import shutil
import sys
import time
from datetime import datetime

from pyspark.sql import functions as F

from masld_spark import config as C
from masld_spark.cohort import REFERENCE_KEYS, STAGE_OK
from masld_spark.fingerprint import sha256_file
from masld_spark.ingest import OK_JSON, SOURCE_JSON, describe_error
from masld_spark.runlog import RunLog, n, say, utc_now
from masld_spark.schemas import TABLES
from masld_spark.session import build as build_session
from masld_spark.splits import recorded_sha, settings as split_settings
from masld_spark.stageio import StageFailure

EXIT_OK, EXIT_FAIL = 0, 1
STAGES = ("ingest", "cohort", "splits", "notes")
GATES_OK = "_GATES_OK.json"
PARTITION_VALUES = ("DEV", "TEST", "GOLD_HOLDOUT", "NONE")
# Identifier and time keys the published DDL declares NOT NULL (gated at zero nulls).
KEY_NOT_NULL = {
    "admissions": ["subject_id", "hadm_id", "admittime"],
    "patients": ["subject_id"],
    "diagnoses_icd": ["subject_id", "hadm_id", "seq_num"],
    "d_icd_diagnoses": ["icd_code", "icd_version"],
    "labevents": ["labevent_id", "subject_id", "itemid"],
    "d_labitems": ["itemid"],
    "omr": ["subject_id", "chartdate"],
    "prescriptions": ["subject_id", "hadm_id"],
    "discharge": ["note_id", "subject_id", "hadm_id", "charttime"],
    "discharge_detail": ["note_id", "subject_id"],
    "radiology": ["note_id", "subject_id", "charttime"],
    "radiology_detail": ["note_id", "subject_id"],
}
POP_KEYS = ["hadm_id", "subject_id", "admittime", "code_positive", "has_note"]


class Gates:
    def __init__(self):
        self.rows = []

    def add(self, stage, name, value, limit, kind="eq"):
        """kind: eq (value must equal limit), max (value at most limit), flag (yes/no: value 1 must equal limit 1)."""
        ok = value <= limit if kind == "max" else value == limit
        self.rows.append({"stage": stage, "gate": name, "value": value, "limit": limit, "kind": kind, "pass": ok})
        rel = "≤" if kind == "max" else "="
        if kind == "flag":       # a yes/no gate is not a count; the small-count rule does not apply
            shown_value, shown_limit = ("yes" if value else "no"), ("yes" if limit else "no")
        else:
            shown_value = f"{value:.4f}%" if isinstance(value, float) else n(value)
            shown_limit = f"{limit:.4f}%" if isinstance(limit, float) else n(limit)
        say(f"[{stage}]".ljust(9), f"{name:<58}", f"{shown_value:>12}", f"{rel} {shown_limit:>12}", "PASS" if ok else "FAIL")

    def failed_stages(self):
        return [s for s in STAGES if any(r["stage"] == s and not r["pass"] for r in self.rows)]


def _stage_dir(cfg, stage):
    return C.paths(cfg)["out_root"] / stage


# --- ingest
def gate_ingest(spark, cfg, g, log):
    root = _stage_dir(cfg, "ingest")
    raw_root = C.paths(cfg)["raw_root"]
    exp = cfg["ingest"]["expected_rows"]
    tol = cfg["ingest"]["tolerance_pct"]
    nulls_report = {}
    tables = {}
    for t, (module, _) in TABLES.items():
        d = root / t
        ok = (d / OK_JSON).exists()
        g.add("ingest", f"{t}: verified by the ingest", int(ok), 1, "flag")
        if not ok:
            continue
        src = json.loads((d / SOURCE_JSON).read_text())
        f = raw_root / module / f"{t}.csv.gz"
        same = int(f.exists() and sha256_file(f) == src["sha256"])
        g.add("ingest", f"{t}: input file unchanged since ingest (SHA-256)", same, 1, "flag")
        df = spark.read.parquet(str(d))
        tables[t] = df
        cols = df.columns
        agg = df.agg(F.count(F.lit(1)).alias("_n"), *[F.sum(F.col(c).isNull().cast("long")).alias(c) for c in cols]).first()
        rows = agg["_n"]
        if exp[t] is None:
            g.add("ingest", f"{t}: expected row count set in the config", 0, 1, "flag")
        elif tol == 0:
            g.add("ingest", f"{t}: rows", rows, exp[t])
        else:
            g.add("ingest", f"{t}: |rows - expected| (tolerance {tol}%)", abs(rows - exp[t]), int(exp[t] * tol / 100.0), "max")
        nulls_report[t] = {c: {"nulls": agg[c], "pct": round(100.0 * agg[c] / rows, 4) if rows else None} for c in cols}
        for c in KEY_NOT_NULL[t]:
            g.add("ingest", f"{t}.{c}: nulls", agg[c] or 0, 0)
    log.data["null_rates"] = nulls_report
    need = {"admissions", "patients", "diagnoses_icd", "discharge", "radiology"}
    if not need <= set(tables):
        return
    adm, pat, dx, dc, rr = (tables[t] for t in ("admissions", "patients", "diagnoses_icd", "discharge", "radiology"))
    dup = lambda df, k: df.groupBy(k).count().where("count > 1").count()
    g.add("ingest", "admissions: duplicate hadm_id", dup(adm, "hadm_id"), 0)
    g.add("ingest", "patients: duplicate subject_id", dup(pat, "subject_id"), 0)
    g.add("ingest", "discharge: duplicate note_id", dup(dc, "note_id"), 0)
    g.add("ingest", "radiology: duplicate note_id", dup(rr, "note_id"), 0)
    g.add("ingest", "note_id shared by a discharge and a radiology note",
          dc.select("note_id").distinct().join(rr.select("note_id").distinct(), "note_id").count(), 0)
    lim = float(cfg.get("gates", {}).get("max_orphan_pct", 0.1))
    hadm, subj = adm.select("hadm_id").distinct(), pat.select("subject_id").distinct()

    def pct(part, whole):
        w = whole.count()
        return round(100.0 * part.count() / w, 4) if w else 0.0

    g.add("ingest", "discharge notes whose hadm_id is not an admission (%)", pct(dc.join(hadm, "hadm_id", "left_anti"), dc), lim, "max")
    rr_h = rr.where(F.col("hadm_id").isNotNull())
    g.add("ingest", "radiology notes whose hadm_id is not an admission (%)", pct(rr_h.join(hadm, "hadm_id", "left_anti"), rr_h), lim, "max")
    notes = dc.select("subject_id").unionAll(rr.select("subject_id"))
    g.add("ingest", "notes whose subject is not a patient (%)", pct(notes.join(subj, "subject_id", "left_anti"), notes), lim, "max")
    g.add("ingest", "diagnoses whose hadm_id is not an admission (%)", pct(dx.join(hadm, "hadm_id", "left_anti"), dx), lim, "max")
    g.add("ingest", "admissions whose subject is not a patient (%)", pct(adm.join(subj, "subject_id", "left_anti"), adm), lim, "max")
    n_rr = rr.count()
    log.data["informational"] = {"radiology_hadm_null_pct": round(100.0 * rr.where(F.col("hadm_id").isNull()).count() / n_rr, 3) if n_rr else None}


# --- cohort and splits
def gate_cohort(spark, cfg, g):
    d = _stage_dir(cfg, "cohort")
    ok = (d / STAGE_OK).exists()
    g.add("cohort", "Step 2 passed (marker present)", int(ok), 1, "flag")
    if not ok:
        return
    ref = cfg["cohort"]["reference"]
    an = spark.read.parquet(str(d / "analysis_admissions"))
    pop = spark.read.parquet(str(d / "population_locked"))
    dc_only = pop.where("has_dc")
    got = {"analysis_admissions": an.count(), "analysis_code_positive": an.where("code_positive").count(),
           "population_admissions": pop.count(), "population_subjects": pop.select("subject_id").distinct().count(),
           "population_code_positive": pop.where("code_positive").count(),
           "population_discharge_only_admissions": dc_only.count(),
           "population_discharge_only_subjects": dc_only.select("subject_id").distinct().count(),
           "population_discharge_only_code_positive": dc_only.where("code_positive").count()}
    for k in REFERENCE_KEYS:
        g.add("cohort", f"{k} (recorded by the current pipeline)", got[k], ref[k])
    nulls = pop.agg(*[F.sum(F.col(c).isNull().cast("long")).alias(c) for c in POP_KEYS]).first()
    for c in POP_KEYS:
        g.add("cohort", f"population_locked.{c}: nulls", nulls[c] or 0, 0)
    npop = got["population_admissions"]
    for t in ("population_locked", "population_clean", "cmrf", "fib4"):
        df = spark.read.parquet(str(d / t))
        g.add("cohort", f"{t}: rows", df.count(), npop)
        g.add("cohort", f"{t}: duplicate hadm_id", df.groupBy("hadm_id").count().where("count > 1").count(), 0)


def gate_splits(spark, cfg, g):
    d = _stage_dir(cfg, "splits")
    ok = (d / STAGE_OK).exists()
    g.add("splits", "Step 4 passed (marker present)", int(ok), 1, "flag")
    if not ok:
        return
    marker = json.loads((d / STAGE_OK).read_text())
    g.add("splits", "source SHA-256 in the marker is the frozen one", int(marker.get("source_sha256") == recorded_sha(split_settings(cfg))), 1, "flag")
    pop = spark.read.parquet(str(_stage_dir(cfg, "cohort") / "population_locked"))
    sp = spark.read.parquet(str(d / "admission_splits"))
    g.add("splits", "split rows", sp.count(), pop.count())
    g.add("splits", "population admissions without a split", pop.join(sp, "hadm_id", "left_anti").count(), 0)


# --- notes
def gate_notes(spark, cfg, g):
    d = _stage_dir(cfg, "notes")
    ok = (d / STAGE_OK).exists()
    g.add("notes", "Step 3 passed (marker present)", int(ok), 1, "flag")
    if not ok:
        return
    ing = _stage_dir(cfg, "ingest")
    n_dc_rr = spark.read.parquet(str(ing / "discharge")).count() + spark.read.parquet(str(ing / "radiology")).count()
    notes = spark.read.parquet(str(d / "notes"))
    g.add("notes", "notes: rows = discharge + radiology", notes.count(), n_dc_rr)
    g.add("notes", "notes: duplicate note_id", notes.groupBy("note_id").count().where("count > 1").count(), 0)
    pop = spark.read.parquet(str(_stage_dir(cfg, "cohort") / "population_locked"))
    lab = spark.read.parquet(str(d / "labels_rule"))
    g.add("notes", "labels_rule: rows", lab.count(), pop.count())
    g.add("notes", "labels_rule: duplicate hadm_id", lab.groupBy("hadm_id").count().where("count > 1").count(), 0)
    g.add("notes", "labels_rule: null note_b", lab.where(F.col("note_b").isNull()).count(), 0)
    subj = spark.read.parquet(str(_stage_dir(cfg, "splits") / "subject_splits")).select(
        "subject_id", F.col("partition").alias("subject_partition"))
    variants = (cfg.get("notes") or {}).get("variants") or ["U", "M", "S"]
    partitioned = ["notes", "token_counts"] + sorted(p.name for p in d.iterdir() if p.name.startswith("chunks_"))
    for t in partitioned:
        df = spark.read.parquet(str(d / t))
        g.add("notes", f"{t}: rows under an unknown partition", df.where(~F.col("partition").isin(*PARTITION_VALUES)).count(), 0)
        j = df.select("subject_id", "partition").join(subj, "subject_id", "left")
        g.add("notes", f"{t}: GOLD_HOLDOUT subjects outside partition=GOLD_HOLDOUT",
              j.where((F.col("subject_partition") == "GOLD_HOLDOUT") & (F.col("partition") != "GOLD_HOLDOUT")).count(), 0)
        g.add("notes", f"{t}: other subjects inside partition=GOLD_HOLDOUT",
              j.where((F.col("partition") == "GOLD_HOLDOUT") & (F.coalesce(F.col("subject_partition"), F.lit("NONE")) != "GOLD_HOLDOUT")).count(), 0)
    tc = spark.read.parquet(str(d / "token_counts"))
    linked = notes.where("in_population").count()
    g.add("notes", "token_counts: rows = linked notes x variants", tc.count(), linked * len(variants))
    ncols = [c for c in tc.columns if c.startswith("n_tokens_")]
    g.add("notes", "token_counts: null token counts", tc.where(" OR ".join(f"{c} IS NULL" for c in ncols)).count(), 0)
    tok_cfg = (cfg.get("notes") or {}).get("tokenizers") or {}
    for t in partitioned:
        if not t.startswith("chunks_"):
            continue
        key = t[len("chunks_"):]
        window = ((tok_cfg.get(key) or {}).get("chunk") or {}).get("window")
        ch = spark.read.parquet(str(d / t))
        if window:
            g.add("notes", f"{t}: chunks longer than the window ({window})", ch.where(F.col("n_tokens") > window).count(), 0)
        grp = ch.groupBy("note_id", "variant").agg(F.count(F.lit(1)).alias("k"), F.min("chunk_index").alias("lo"),
                                                    F.max("chunk_index").alias("hi"), F.countDistinct("chunk_index").alias("d"),
                                                    F.min("n_chunks").alias("m1"), F.max("n_chunks").alias("m2"))
        g.add("notes", f"{t}: (note, variant) groups with broken chunk indexes",
              grp.where("lo != 0 OR hi != m1 - 1 OR d != k OR k != m1 OR m1 != m2").count(), 0)
        ends = ch.agg(F.countDistinct(F.element_at("input_ids", 1)).alias("a"),
                      F.countDistinct(F.element_at("input_ids", -1)).alias("b")).first()
        g.add("notes", f"{t}: distinct opening token ids", ends["a"], 1)
        g.add("notes", f"{t}: distinct closing token ids", ends["b"], 1)


# --- quarantine
def quarantine(cfg, run_name, first_failed):
    moved = []
    q = C.paths(cfg)["out_root"] / "_quarantine" / run_name
    for s in STAGES[STAGES.index(first_failed):]:
        src = _stage_dir(cfg, s)
        if src.exists():
            q.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(q / s))
            moved.append(s)
    return moved


def restore(cfg, run_name):
    q = C.paths(cfg)["out_root"] / "_quarantine" / run_name
    if not q.exists():
        raise StageFailure(f"nothing quarantined under run {run_name}")
    back = []
    for s in STAGES:
        if (q / s).exists():
            if _stage_dir(cfg, s).exists():
                raise StageFailure(f"{s} exists again; remove or rename it before restoring")
            shutil.move(str(q / s), str(_stage_dir(cfg, s)))
            back.append(s)
    return back


def run_gates(spark, cfg, log, quarantine_on_fail=True):
    out = C.paths(cfg)["out_root"]
    (out / GATES_OK).unlink(missing_ok=True)
    g = Gates()
    for stage, fn in (("ingest", lambda: gate_ingest(spark, cfg, g, log)), ("cohort", lambda: gate_cohort(spark, cfg, g)),
                      ("splits", lambda: gate_splits(spark, cfg, g)), ("notes", lambda: gate_notes(spark, cfg, g))):
        t = time.time()
        fn()
        log.data["timings_s"][f"gates_{stage}"] = round(time.time() - t, 1)
        log.data["gates"] = g.rows
        log.write()
    failed = g.failed_stages()
    n_pass = sum(r["pass"] for r in g.rows)
    say(f"[gates] {n_pass} of {len(g.rows)} gates pass")
    if not failed:
        markers = {s: json.loads((out / s / STAGE_OK).read_text()).get("run_name") for s in STAGES[1:]}
        (out / GATES_OK).write_text(json.dumps({"run_name": log.data["run_name"], "verified_utc": utc_now(),
                                                "stage_runs": markers, "gates": len(g.rows)}, indent=1, default=str))
        return EXIT_OK
    say("[gates] failed in:", ", ".join(failed))
    if quarantine_on_fail:
        moved = quarantine(cfg, log.data["run_name"], failed[0])
        log.data["quarantined"] = moved
        say("[gates] quarantined:", ", ".join(moved), f"-> data/spark/_quarantine/{log.data['run_name']}/",
            f"(review, then: make spark-gates-restore RUN={log.data['run_name']})")
    return EXIT_FAIL


def main(argv=None, spark=None):
    ap = argparse.ArgumentParser(description="Step 5: validation gates (aggregates only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    ap.add_argument("--restore", metavar="RUN", help="move the stages quarantined by run RUN back into place")
    ap.add_argument("--no-quarantine", action="store_true", help="diagnosis only: report failures, move nothing")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
    except (OSError, C.ConfigError, ValueError) as e:
        say("[gates] config error:", e)
        return EXIT_FAIL
    if a.restore:
        try:
            say("[gates] restored:", ", ".join(restore(cfg, a.restore)) or "nothing", "— run the gates again")
            return EXIT_OK
        except StageFailure as e:
            say("[gates] restore stopped:", e)
            return EXIT_FAIL
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-gates-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(C.paths(cfg)["runs_root"], name, "gates", cfg)
    own, code = spark is None, EXIT_FAIL
    try:
        if own:
            spark = build_session(cfg, log.private)
        log.spark_versions(spark)
        say(f"[gates] run {name}", f"Spark {log.data['versions']['spark']}")
        code = run_gates(spark, cfg, log, quarantine_on_fail=not a.no_quarantine)
    except StageFailure as e:
        say("[gates] stopped:", e)
    except Exception as e:   # noqa: BLE001 — classified, never printed
        log.private_error("gates", e)
        say("[gates] run failed:", describe_error(e))
    finally:
        log.memory(spark)
        if own and spark is not None:
            spark.stop()
        log.finish("PASS" if code == EXIT_OK else "FAIL", code)
        say(f"[gates] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
