"""Step 3 — note preparation: note table, frozen-rule flags, sections, rule labels, token counts and chunks.

Outputs (data/spark/notes/); tables marked [P] are split into partition=<DEV|TEST|GOLD_HOLDOUT|NONE>/ directories by
the subject's split (Step 4), so a training job can read DEV and TEST and never open a GOLD_HOLDOUT file:
  notes [P]          every discharge and radiology note: ids, times, n_chars, liver_incl (radiology exam name, as
                     run0919_notes_index.py), the frozen rule's per-note flags (run0919_notes_index.flags, which calls
                     note_phenotype._iter_hits), sections, in_population (linked to a population admission)
  labels_rule        one row per population admission: note_a (an inpatient-linked note is Tier A positive),
                     note_b = note_a or an outpatient radiology report in the primary window (definition b, the
                     study's silver label), note_c (90/30 window), code status, the 2x2 cell, partition and fold
  token_counts [P]   population-linked notes x text variant: token count under every configured tokenizer
  chunks_<tok> [P]   population-linked notes x variant x chunk, for tokenizers with a chunk window: input_ids with
                     [CLS]/[SEP] (or the tokenizer's equivalents), chunked exactly as run0919_embed.chunk_ids

Text variants (functions imported from run0919_notes_text.py): U unmasked, M every lexicon match replaced by [MASK],
S every sentence with a lexicon match deleted. M and S exist because the silver label comes from the same lexicon:
a model given U can score well by relearning the keywords.

Sections: liver_sentences.section_spans (impression / findings / other), each span with its normalised heading, so
discharge sections such as DISCHARGE DIAGNOSIS and BRIEF HOSPITAL COURSE are found by label. Offsets are 0-based
character positions in the note text, end exclusive. No note text is written to any output; chunks hold token ids.

Checks: note rows = discharge + radiology rows; no rule, section or variant errors; every population admission
labelled; note-positive admissions per partition and per DEV fold equal phase2_splits.json; the code x note 2x2 cells
equal the run of 10 November (fib4_by_cell.json). All pass -> _STAGE_OK.json.

Tokenizers are loaded offline (HF_HUB_OFFLINE=1) from the local Hugging Face cache, at pinned revisions.
Console: aggregates only (counts 1-10 as <11). Exception messages are never printed.
Run:  zsh scripts/spark_env.sh -m masld_spark.notes --config conf/spark_local.yaml [--force]
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from pyspark.sql import functions as F

from masld_spark import config as C
from masld_spark.cohort import STAGE_OK
from masld_spark.ingest import describe_error
from masld_spark.runlog import RunLog, n, say, size, utc_now
from masld_spark.session import build as build_session
from masld_spark.splits import stage_input
from masld_spark.stageio import StageFailure, ingested, write_table

EXIT_OK, EXIT_FAIL = 0, 1
VARIANTS = ("U", "M", "S")
NOTE_META = ["note_id", "note_table", "subject_id", "hadm_id", "note_type", "note_seq", "charttime", "storetime",
             "n_chars"]
RULE_SCHEMA = ("note_id string, note_table string, subject_id bigint, hadm_id bigint, note_type string, note_seq int, "
               "charttime timestamp_ntz, storetime timestamp_ntz, n_chars int, "
               "a_pos boolean, b_pos boolean, c_hedged boolean, n_pos int, n_hist int, n_tierC int, n_neg int, "
               "rule_error string, "
               "sections array<struct<start:int,end:int,label:string,category:string>>, section_error string")
RULE_COLS = ["a_pos", "b_pos", "c_hedged", "n_pos", "n_hist", "n_tierC", "n_neg", "rule_error", "sections",
             "section_error"]


# --- per-note rule flags and sections
def rule_and_sections(batches):
    """mapInPandas: metadata passes through; adds the frozen rule's flags and the sections. Per-note errors are
    recorded as the exception class only."""
    import pandas as pd
    from scripts.liver_sentences import HEADER_RE, section_spans
    from scripts.run0919_notes_index import flags
    cols = NOTE_META + RULE_COLS
    for pdf in batches:
        out = {c: [] for c in RULE_COLS}
        for txt in pdf["text"]:
            txt = txt or ""
            try:
                a, b, c, npos, nhist, ntc, nneg = flags(txt)
                vals, err = [a, b, c, npos, nhist, ntc, nneg], None
            except Exception as e:   # noqa: BLE001
                vals, err = [None] * 7, type(e).__name__
            for k, v in zip(RULE_COLS[:7], vals):
                out[k].append(v)
            out["rule_error"].append(err)
            try:
                secs = []
                for s, e_, cat in section_spans(txt):
                    m = HEADER_RE.match(txt, s)
                    label = " ".join(m.group(1).strip().upper().split()) if m else ""
                    secs.append({"start": s, "end": e_, "label": label, "category": cat})
                out["sections"].append(secs)
                out["section_error"].append(None)
            except Exception as e:   # noqa: BLE001
                out["sections"].append(None)
                out["section_error"].append(type(e).__name__)
        res = pdf[NOTE_META].copy()
        for k in RULE_COLS:
            res[k] = out[k]
        yield res[cols]


def liver_inclusive(radiology_detail):
    """run0919_notes_index.py: exam_name names a cross-sectional or ultrasound modality AND an abdominal/liver region."""
    from scripts.run0919_notes_index import MOD, REGION
    up = F.upper("field_value")
    return (radiology_detail.where(F.col("field_name") == "exam_name")
            .groupBy("note_id").agg(F.max(up.rlike(MOD) & up.rlike(REGION)).alias("liver_incl")))


# --- rule labels (definitions a, b, c)
def rule_labels(links, note_flags, pop, adm_splits):
    l = links.join(note_flags.select("note_id", "note_table", "a_pos"), ["note_id", "note_table"], "left") \
             .withColumn("pos", F.coalesce(F.col("a_pos"), F.lit(False)))
    i = lambda c: c.cast("int")
    agg = l.groupBy("hadm_id").agg(
        (F.max(i((F.col("link") == "inpatient") & F.col("pos"))) == 1).alias("note_a"),
        (F.max(i(F.col("in_window_primary") & F.col("pos"))) == 1).alias("note_b"),
        (F.max(i(F.col("in_window_sensitivity") & F.col("pos"))) == 1).alias("note_c"),
        F.countDistinct("note_id").alias("n_linked_notes"),
        F.countDistinct(F.when(F.col("pos"), F.col("note_id"))).alias("n_linked_positive"))
    d = (pop.select("hadm_id", "subject_id", "code_positive").join(agg, "hadm_id", "left")
            .fillna(False, ["note_a", "note_b", "note_c"]).fillna(0, ["n_linked_notes", "n_linked_positive"])
            .join(adm_splits.select("hadm_id", "partition", "fold"), "hadm_id", "left"))
    cp, nb = F.col("code_positive"), F.col("note_b")
    return d.withColumn("cell", F.when(cp & nb, "A").when(~cp & nb, "B").when(cp & ~nb, "C").otherwise("D"))


# --- tokens and chunks
def chunk(ids, cls_id, sep_id, window, stride, max_chunks=None):
    """run0919_embed.chunk_ids on already-tokenized ids (tests/spark/test_notes.py checks it against the original)."""
    body = window - 2
    step = body - stride
    out = []
    for s in range(0, max(len(ids), 1), step):
        piece = ids[s:s + body]
        if not piece:
            break
        out.append([cls_id] + piece + [sep_id])
        if (max_chunks and len(out) >= max_chunks) or s + body >= len(ids):
            break
    return out


def tokenizer_specs(cfg):
    specs = []
    for key, t in ((cfg.get("notes") or {}).get("tokenizers") or {}).items():
        if not key.isidentifier():
            raise C.ConfigError(f"tokenizer key '{key}' must be an identifier")
        ch = t.get("chunk") or None
        if ch and not (isinstance(ch.get("window"), int) and isinstance(ch.get("stride"), int)
                       and 0 <= ch["stride"] < ch["window"] - 2):
            raise C.ConfigError(f"tokenizer {key}: chunk needs integer window and stride with 0 <= stride < window - 2")
        specs.append({"key": key, "name": t.get("local_path") or t["name"], "revision": t.get("revision"),
                      "chunk": ch})
    if not specs:
        raise C.ConfigError("notes.tokenizers is empty")
    return specs


def token_schema(specs):
    cols = ["note_id string", "note_table string", "subject_id bigint", "partition string", "variant string",
            "variant_error string"]
    cols += [f"n_tokens_{s['key']} int" for s in specs]
    cols += [f"chunks_{s['key']} array<array<int>>" for s in specs if s["chunk"]]
    return ", ".join(cols)


def make_token_udf(specs, variants, max_chunks):
    def tokens(batches):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"     # Spark already runs one worker per core
        os.environ["TRANSFORMERS_VERBOSITY"] = "error"     # silences the import-time "PyTorch was not found" notice
        import pandas as pd
        from transformers import AutoTokenizer
        from transformers.utils import logging as hf_logging
        hf_logging.set_verbosity_error()
        from scripts.run0919_notes_text import delete_sentences, mask_spans
        transform = {"U": lambda t: t, "M": mask_spans, "S": delete_sentences}
        toks = {s["key"]: AutoTokenizer.from_pretrained(s["name"], revision=s["revision"]) for s in specs}
        for pdf in batches:
            if pdf.empty:
                continue
            parts = []
            for v in variants:
                texts, errs = [], []
                for t in pdf["text"]:
                    try:
                        texts.append(transform[v](t or "")); errs.append(None)
                    except Exception as e:   # noqa: BLE001
                        texts.append(""); errs.append(type(e).__name__)
                res = pdf[["note_id", "note_table", "subject_id", "partition"]].copy()
                res["variant"] = v
                res["variant_error"] = errs
                for s in specs:
                    tok = toks[s["key"]]
                    ids = tok(texts, add_special_tokens=False, return_attention_mask=False,
                              return_token_type_ids=False)["input_ids"]
                    res[f"n_tokens_{s['key']}"] = [len(x) for x in ids]
                    if s["chunk"]:
                        w, st = s["chunk"]["window"], s["chunk"]["stride"]
                        res[f"chunks_{s['key']}"] = [chunk(x, tok.cls_token_id, tok.sep_token_id, w, st, max_chunks)
                                                     for x in ids]
                parts.append(res)
            yield pd.concat(parts, ignore_index=True)
    return tokens


def tokenizer_fingerprints(specs):
    """SHA-256 of each tokenizer's files in the local cache (model weights excluded). Offline."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    from huggingface_hub import snapshot_download
    out = {}
    for s in specs:
        p = Path(s["name"])
        d = p if p.is_dir() else Path(snapshot_download(s["name"], revision=s["revision"], local_files_only=True))
        files = sorted(f for f in d.iterdir() if f.is_file() and f.suffix not in (".bin", ".safetensors", ".h5", ".msgpack"))
        out[s["key"]] = {"name": s["name"], "revision": s["revision"], "chunk": s["chunk"],
                         "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    return out


# --- run
def _ref(cfg):
    r = (cfg.get("notes") or {}).get("reference") or {}
    for k in ("splits", "cells"):
        if k not in r:
            raise C.ConfigError(f"notes.reference.{k} is missing")
    return json.loads(C.resolve(r["splits"]).read_text()), json.loads(C.resolve(r["cells"]).read_text())


def run_notes(spark, cfg, log, force=False):
    nc = cfg.get("notes") or {}
    specs = tokenizer_specs(cfg)
    variants = tuple(nc.get("variants") or VARIANTS)
    if not set(variants) <= set(VARIANTS):
        raise C.ConfigError(f"notes.variants must be drawn from {VARIANTS}")
    files = nc.get("files") or {}
    ref_splits, ref_cells = _ref(cfg)
    out = C.paths(cfg)["out_root"] / "notes"
    if out.exists() and any(p for p in out.iterdir() if not p.name.startswith(".")) and not force:
        raise StageFailure("notes output exists; pass --force to rebuild it")
    (out / STAGE_OK).unlink(missing_ok=True)
    run_name = log.data["run_name"]
    spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", str(int(nc.get("arrow_batch_rows", 256))))

    t = time.time()
    log.data["tokenizers"] = tokenizer_fingerprints(specs)
    say("[notes] tokenizers (offline, pinned):", *[f"{k} {v['revision'] or 'local'}" for k, v in log.data["tokenizers"].items()])
    dc, rr, rd = (ingested(spark, cfg, t_) for t_ in ("discharge", "radiology", "radiology_detail"))
    links = stage_input(spark, cfg, "cohort", "note_links")
    pop = stage_input(spark, cfg, "cohort", "population_locked")
    adm_sp = stage_input(spark, cfg, "splits", "admission_splits")
    subj_sp = stage_input(spark, cfg, "splits", "subject_splits")

    def save(name, df, sort_keys, partition_by=None):
        t0 = time.time()
        rec = write_table(spark, df, out, name, run_name, n_files=int(files.get(name, 1)), sort_keys=sort_keys,
                          partition_by=partition_by)
        rec["seconds"] = round(time.time() - t0, 1)
        log.data["tables"][name] = rec
        log.write()
        say(f"[{name}]".ljust(27), f"rows {n(rec['rows'])}", f"{rec['n_files']} file(s) {size(rec['bytes'])}",
            f"{rec['seconds']:.1f}s")
        return spark.read.parquet(str(out / name))

    cols = ["note_id", "subject_id", "hadm_id", "note_type", "note_seq", "charttime", "storetime", "text"]
    base = (dc.select(*cols).withColumn("note_table", F.lit("discharge"))
              .unionByName(rr.select(*cols).withColumn("note_table", F.lit("radiology")))
              .withColumn("n_chars", F.length("text").cast("int")))
    linked = links.select("note_id", "note_table").distinct().withColumn("in_population", F.lit(True))
    flagged = base.select(*NOTE_META, "text").mapInPandas(rule_and_sections, RULE_SCHEMA)
    notes_df = (flagged.join(liver_inclusive(rd), "note_id", "left")
                .withColumn("liver_incl", F.when(F.col("note_table") == "radiology",
                                                 F.coalesce(F.col("liver_incl"), F.lit(False))))
                .join(linked, ["note_id", "note_table"], "left").fillna(False, ["in_population"])
                .join(subj_sp.select("subject_id", "partition"), "subject_id", "left")
                .withColumn("partition", F.coalesce(F.col("partition"), F.lit("NONE"))))
    notes = save("notes", notes_df, ("subject_id", "note_id"), partition_by="partition")

    labels = save("labels_rule", rule_labels(links, notes, pop, adm_sp), ("hadm_id",))

    tok_in = (base.join(linked, ["note_id", "note_table"], "left_semi")
                  .join(subj_sp.select("subject_id", "partition"), "subject_id", "left")
                  .withColumn("partition", F.coalesce(F.col("partition"), F.lit("NONE")))
                  .select("note_id", "note_table", "subject_id", "partition", "text"))
    stage = out / f".note_tokens-{run_name}"
    shutil.rmtree(stage, ignore_errors=True)
    t0 = time.time()
    tok_in.mapInPandas(make_token_udf(specs, variants, nc.get("max_chunks")), token_schema(specs)) \
          .write.mode("overwrite").parquet(str(stage))
    log.data["timings_s"]["tokenize"] = round(time.time() - t0, 1)
    say("[tokenize]".ljust(27), f"{log.data['timings_s']['tokenize']:.1f}s")
    nt = spark.read.parquet(str(stage))
    counts_cols = ["note_id", "note_table", "subject_id", "partition", "variant", "variant_error"] + \
                  [f"n_tokens_{s['key']}" for s in specs]
    save("token_counts", nt.select(*counts_cols), ("subject_id", "note_id", "variant"), partition_by="partition")
    for s in specs:
        if s["chunk"]:
            k = s["key"]
            ch = nt.select("note_id", "note_table", "subject_id", "partition", "variant",
                           F.size(f"chunks_{k}").alias("n_chunks"),
                           F.posexplode(f"chunks_{k}").alias("chunk_index", "input_ids")) \
                   .withColumn("n_tokens", F.size("input_ids"))
            save(f"chunks_{k}", ch, ("subject_id", "note_id", "variant", "chunk_index"), partition_by="partition")
    try:
        results, summary = _checks_and_summary(spark, cfg, notes, labels, nt, specs, variants, dc, rr,
                                               pop, links, adm_sp, ref_splits, ref_cells)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    log.data["checks"], log.data["summary"] = results, summary
    log.data["timings_s"]["stage"] = round(time.time() - t, 1)
    ok = all(r["pass"] for r in results)
    if ok:
        (out / STAGE_OK).write_text(json.dumps({"stage": "notes", "run_name": run_name, "verified_utc": utc_now(),
                                                "tokenizers": log.data["tokenizers"]}, indent=1))
    return EXIT_OK if ok else EXIT_FAIL


def _checks_and_summary(spark, cfg, notes, labels, nt, specs, variants, dc, rr, pop, links, adm_sp,
                        ref_splits, ref_cells):
    checks = []
    n_notes = notes.count()
    checks.append(("note rows = discharge + radiology rows", n_notes, dc.count() + rr.count()))
    lp = links.join(adm_sp.select("hadm_id", F.col("partition").alias("adm_partition")), "hadm_id") \
              .join(notes.select("note_id", "note_table", "partition"), ["note_id", "note_table"])
    checks.append(("linked notes stored under another partition", lp.where("partition != adm_partition").count(), 0))
    checks.append(("notes with a rule error", notes.where(F.col("rule_error").isNotNull()).count(), 0))
    checks.append(("notes with a section error", notes.where(F.col("section_error").isNotNull()).count(), 0))
    n_tok_notes = notes.where("in_population").count()
    checks.append(("token rows = linked notes x variants", nt.count(), n_tok_notes * len(variants)))
    checks.append(("token rows with a variant error", nt.where(F.col("variant_error").isNotNull()).count(), 0))
    checks.append(("labelled admissions = population", labels.count(), pop.count()))
    checks.append(("labelled admissions without a partition", labels.where(F.col("partition").isNull()).count(), 0))
    by_p = {r["partition"]: r["k"] for r in labels.groupBy("partition").agg(
        F.sum(F.col("note_b").cast("int")).alias("k")).collect()}
    for p, e in ref_splits["partitions"].items():
        checks.append((f"{p} note-positive admissions (definition b)", by_p.get(p) or 0, e["note_positive"]))
    by_f = {r["fold"]: r["k"] for r in labels.where("partition = 'DEV'").groupBy("fold").agg(
        F.sum(F.col("note_b").cast("int")).alias("k")).collect()}
    for k, e in sorted(ref_splits["dev_folds"].items()):
        checks.append((f"DEV fold {k} note-positive admissions", by_f.get(int(k)) or 0, e["note_positive"]))
    cells = {r["cell"]: r["count"] for r in labels.groupBy("cell").count().collect()}
    for c in ("A", "B", "C", "D"):
        checks.append((f"2x2 cell {c} admissions", cells.get(c, 0), ref_cells["analyses"]["primary_first_result"][c]["admissions"]))
    results = []
    for name, value, exp in checks:
        ok = value == exp
        results.append({"check": name, "value": value, "expected": exp, "pass": ok})
        say("[check]", f"{name:<48}", f"{n(value):>12}", f"reference {n(exp):>12}", "PASS" if ok else "FAIL")

    s = {"notes_by_partition": {r["partition"]: r["count"] for r in notes.groupBy("partition").count().collect()},
         "notes_in_population": n_tok_notes}
    flags = notes.agg(*[F.sum(F.col(c).cast("int")).alias(c) for c in ("a_pos", "b_pos", "c_hedged")]).first()
    s["notes_flagged"] = flags.asDict()
    secs = notes.select("note_table", F.explode("sections").alias("s"))
    s["sections"] = {
        "discharge_with_discharge_diagnosis": notes.where("note_table = 'discharge'").where(
            F.exists("sections", lambda x: x["label"].startswith("DISCHARGE DIAGNOS"))).count(),
        "discharge_with_hospital_course": notes.where("note_table = 'discharge'").where(
            F.exists("sections", lambda x: x["label"].contains("HOSPITAL COURSE"))).count(),
        "radiology_with_findings": notes.where("note_table = 'radiology'").where(
            F.exists("sections", lambda x: x["category"] == "findings")).count(),
        "radiology_with_impression": notes.where("note_table = 'radiology'").where(
            F.exists("sections", lambda x: x["category"] == "impression")).count(),
        "spans_by_category": {r["category"]: r["count"] for r in secs.groupBy(F.col("s.category").alias("category")).count().collect()},
    }
    s["tokens"] = {}
    for sp in specs:
        k = sp["key"]
        col = f"n_tokens_{k}"
        window = (sp["chunk"] or {}).get("window")
        for v in variants:
            r = nt.where(F.col("variant") == v).agg(
                F.percentile_approx(col, [0.5, 0.9, 0.99], 10000).alias("q"),
                F.sum((F.col(col) > 510).cast("int")).alias("over_510"),
                F.sum((F.col(col) > 4094).cast("int")).alias("over_4094"),
                F.sum((F.col(col) == 0).cast("int")).alias("empty")).first()
            s["tokens"][f"{k}|{v}"] = {"p50": r["q"][0], "p90": r["q"][1], "p99": r["q"][2],
                                      "over_510": r["over_510"], "over_4094": r["over_4094"], "empty": r["empty"],
                                      "window": window}
    s["chunks"] = {}
    for sp in specs:
        if sp["chunk"]:
            ch = spark.read.parquet(str(C.paths(cfg)["out_root"] / "notes" / f"chunks_{sp['key']}"))
            s["chunks"][sp["key"]] = {f"{r['partition']}|{r['variant']}": r["count"]
                                      for r in ch.groupBy("partition", "variant").count().collect()}
    say("[summary] notes by partition:", *[f"{k} {n(v)}" for k, v in sorted(s["notes_by_partition"].items())],
        f"linked to the population {n(n_tok_notes)}")
    say("[summary] notes flagged by the frozen rule:", *[f"{k} {n(v)}" for k, v in s["notes_flagged"].items()])
    say("[summary] sections:", *[f"{k} {n(v)}" for k, v in s["sections"].items() if k != "spans_by_category"])
    for key, d in s["tokens"].items():
        say(f"[summary] tokens {key}:", f"p50 {d['p50']}", f"p90 {d['p90']}", f"p99 {d['p99']}",
            f"> 510 {n(d['over_510'])}", f"> 4094 {n(d['over_4094'])}", f"empty {n(d['empty'])}")
    for key, d in s["chunks"].items():
        say(f"[summary] chunks {key}:", *[f"{k} {n(v)}" for k, v in sorted(d.items())])
    return results, s


def main(argv=None, spark=None):
    ap = argparse.ArgumentParser(description="Step 3: note preparation (aggregates only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    ap.add_argument("--force", action="store_true", help="rebuild the notes output")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
        tokenizer_specs(cfg)
        _ref(cfg)
    except (OSError, C.ConfigError, ValueError) as e:
        say("[notes] config error:", e)
        return EXIT_FAIL
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-notes-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(C.paths(cfg)["runs_root"], name, "notes", cfg)
    own, code = spark is None, EXIT_FAIL
    try:
        if own:
            spark = build_session(cfg, log.private)
        log.spark_versions(spark)
        v = log.data["versions"]
        say(f"[notes] run {name}", f"Spark {v['spark']}", f"Java {v.get('java')}", f"master {v.get('master')}")
        code = run_notes(spark, cfg, log, force=a.force)
    except StageFailure as e:
        say("[notes] stopped:", e)
    except Exception as e:   # noqa: BLE001 — classified, never printed
        log.private_error("notes", e)
        say("[notes] run failed:", describe_error(e))
    finally:
        m = log.memory(spark)
        heap = m.get("jvm_heap_peak_bytes_upper_bound")
        say("[notes] peak memory:", f"driver Python {size(m['driver_python_peak_rss_bytes'])}",
            f"JVM heap ≤ {size(heap)} of {size(m['jvm_heap_max_bytes'])}" if heap is not None else "JVM heap n/a",
            f"elapsed {time.time() - log._t0:,.0f}s")
        if own and spark is not None:
            spark.stop()
        log.finish("PASS" if code == EXIT_OK else "FAIL", code)
        say(f"[notes] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
