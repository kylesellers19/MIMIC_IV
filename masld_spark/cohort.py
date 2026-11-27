"""Step 2 — cohort and linkage, from the verified ingest, reproducing the version-of-record definitions.

Outputs (data/spark/cohort/<table>/), each with the DuckDB file it reproduces:
  dx_summary            per admission with a diagnosis: n_diagnoses, code status, ICD version range, CMRF and
                        etiology code flags                        (masld_config.analysis_admissions_sql; cmrf.py)
  analysis_admissions   admissions with >=1 diagnosis row, with note presence and population membership
                                                                   (lock_population.py, before the restriction)
  population_locked     >=1 linked discharge or radiology note     (data/processed/analysis_population.parquet)
  population_clean      cleaned covariates, nulled never dropped   (data/processed/analysis_population_clean.parquet)
  cmrf                  five CMRF criteria and etiology flags      (data/processed/cmrf.parquet)
  lab_features          first/last in-admission values, 365-day outpatient values
                                                                   (data/processed/run_2026-09-19_lab_features.parquet)
  outpatient_fib4_inputs  most recent outpatient AST/ALT/platelets in 365 days
                                                                   (data/processed/run_2026-11-10_outpt_fib4.parquet)
  fib4                  FIB-4 from first, last and outpatient values with the run1110 cutoffs (exploratory, amendment l)
  note_links            every discharge and radiology note linked to a population admission: by hadm_id, or
                        outpatient radiology (no hadm_id) for the same subject from 365 days before to 30 after
                        admittime, flagged for the 90/30 sensitivity window (note_phenotype.OUTPATIENT_WINDOWS)
  patients_flags        one row per population subject: admission counts and any-admission flags

Definitions come from masld_spark/definitions.py, which reads them from the scripts; nothing is re-decided.

One documented difference: where DuckDB's arg_min / arg_max meet two results at the same charttime, which one it
keeps is not defined. Here ties are broken by labevent_id (lowest for first values, highest for last values), and
the number of tied (admission, analyte) pairs is reported so the Step 6 parity check can account for them.

Checks: the population counts are compared with the documented values in cohort.reference (config) and the cleaned
row count with clean_population.N_EXPECT. All pass -> data/spark/cohort/_STAGE_OK.json; any fail -> exit 1 and no
marker (Step 5 adds the full validation gates and quarantine).

Console: aggregates only (counts 1-10 as <11). Exception messages are never printed.
Run:  zsh scripts/spark_env.sh -m masld_spark.cohort --config conf/spark_local.yaml [--force]
"""
import argparse
import json
import shutil
import sys
import time
from datetime import datetime

from pyspark.sql import Window
from pyspark.sql import functions as F

from masld_spark import config as C
from masld_spark import definitions as D
from masld_spark.ingest import describe_error
from masld_spark.runlog import RunLog, n, say, size, utc_now
from masld_spark.session import build as build_session
from masld_spark.stageio import StageFailure, ingested, write_table

EXIT_OK, EXIT_FAIL = 0, 1
STAGE_OK = "_STAGE_OK.json"
REFERENCE_KEYS = ("analysis_admissions", "analysis_code_positive", "population_admissions", "population_subjects",
                  "population_code_positive", "population_discharge_only_admissions",
                  "population_discharge_only_subjects", "population_discharge_only_code_positive")
LOCKED_COLUMNS = ["hadm_id", "subject_id", "code_positive", "n_diagnoses", "age", "gender", "race", "insurance",
                  "language", "marital_status", "admission_type", "admission_location", "hospital_expire_flag",
                  "los_days", "anchor_year_group", "admittime", "dischtime", "admit_year", "has_dc", "has_rad",
                  "has_note", "subj_has_note"]
CLEAN_BASE = ["hadm_id", "subject_id", "code_positive", "n_diagnoses", "age", "gender", "race", "insurance",
              "language", "marital_status", "admission_type", "admission_location", "hospital_expire_flag",
              "los_days", "icd_era"]
BP_RE = r"^\s*(\d+)\s*/\s*(\d+)"          # clean_population.py / make_tables.py, group 1 systolic, 2 diastolic


def _false(c):
    """pandas compares null as False; Spark gives null. Every boolean built from a comparison goes through this."""
    return F.coalesce(c, F.lit(False))


def _seconds(start, end):
    return F.expr(f"timestampdiff(SECOND, {start}, {end})")


# --- admissions and population
def dx_summary(dx):
    """Per hadm_id: diagnosis count = distinct (seq_num, icd_version); code status by MASLD_PREDICATE; ICD range;
    the ten CMRF/etiology code flags, cmrf.py's select list run as written (code = trim(icd_code))."""
    view = f"_masld_dx_{abs(hash(id(dx)))}"
    dx.createOrReplaceTempView(view)
    out = dx.sparkSession.sql(f"""
      WITH d AS (SELECT hadm_id, seq_num, icd_version, icd_code, trim(icd_code) AS code FROM {view})
      SELECT hadm_id,
             count(DISTINCT seq_num, icd_version) AS n_diagnoses,
             max(CASE WHEN {D.MASLD_PREDICATE} THEN 1 ELSE 0 END) = 1 AS code_positive,
             min(icd_version) AS minv, max(icd_version) AS maxv,
             {D.cmrf_code_flags_select()}
      FROM d GROUP BY hadm_id""")
    for c in D.CMRF_CODE_FLAGS:
        out = out.withColumn(c, F.col(c) == 1)
    return out


def analysis_admissions(adm, pat, dxs, discharge, radiology):
    """Admissions with >=1 diagnosis row (inner joins, as analysis_admissions_sql), with note presence by hadm_id."""
    a = (adm.join(dxs.select("hadm_id", "n_diagnoses", "code_positive", "minv", "maxv"), "hadm_id", "inner")
            .join(pat.select("subject_id", "gender", "anchor_age", "anchor_year", "anchor_year_group", "dod"),
                  "subject_id", "inner"))
    a = (a.withColumn("age_at_admit", F.col("anchor_age") + F.year("admittime") - F.col("anchor_year"))
          .withColumn("age", F.least(F.col("age_at_admit"), F.lit(91)))
          .withColumn("los_days", _seconds("admittime", "dischtime") / 86400.0)
          .withColumn("admit_year", F.year("admittime"))
          .withColumn("icd_era", F.when((F.col("minv") == 9) & (F.col("maxv") == 9), "ICD-9 only")
                                  .when((F.col("minv") == 10) & (F.col("maxv") == 10), "ICD-10 only")
                                  .otherwise("Both")))
    dc = discharge.where(F.col("hadm_id").isNotNull()).select("hadm_id").distinct().withColumn("has_dc", F.lit(True))
    rr = radiology.where(F.col("hadm_id").isNotNull()).select("hadm_id").distinct().withColumn("has_rad", F.lit(True))
    a = a.join(dc, "hadm_id", "left").join(rr, "hadm_id", "left").fillna(False, ["has_dc", "has_rad"])
    a = a.withColumn("has_note", F.col("has_dc") | F.col("has_rad"))
    a = a.withColumn("subj_has_note", F.max(F.col("has_note").cast("int")).over(Window.partitionBy("subject_id")) == 1)
    return a.withColumn("in_population", F.col("has_note")).drop("minv", "maxv")


def population_locked(analysis):
    return analysis.where("has_note").select(*LOCKED_COLUMNS)


# --- cleaned covariates
def first_labs(lab, hadm_ids):
    """make_tables.build_frame: per admission and analyte (ANALYTE_IDS, GGT included), the valuenum at the earliest
    charttime, hadm-linked rows with valuenum and charttime present. Returns (wide table, the events used)."""
    ids = D.ANALYTE_IDS
    e = (lab.where(F.col("itemid").isin(list(ids.values())) & F.col("hadm_id").isNotNull()
                   & F.col("valuenum").isNotNull() & F.col("charttime").isNotNull())
            .join(hadm_ids, "hadm_id", "left_semi"))
    g = e.groupBy("hadm_id", "itemid").agg(F.min_by("valuenum", F.struct("charttime", "labevent_id")).alias("v"))
    wide = g.groupBy("hadm_id").agg(*[F.max(F.when(F.col("itemid") == i, F.col("v"))).alias(f"lab_{k}")
                                      for k, i in ids.items()])
    return wide, e


def tied_pairs(e, keys, order="charttime", which="min"):
    """(keys) groups where the earliest (or latest) charttime holds more than one distinct value."""
    w = Window.partitionBy(*keys)
    ext = F.min(order).over(w) if which == "min" else F.max(order).over(w)
    at = e.withColumn("_ext", ext).where(F.col(order) == F.col("_ext"))
    return at.groupBy(*keys).agg(F.countDistinct("valuenum").alias("_k")).where("_k > 1").count()


def omr_clean(omr, pat):
    """clean_population.py STEP 2b: subject-level medians of BMI, SBP and DBP within bounds, DBP 0 excluded, readings
    after the date of death excluded; has_* = any usable reading."""
    lo_b, hi_b = D.OMR_BOUNDS["BMI"]
    lo_s, hi_s = D.OMR_BOUNDS["SBP"]
    lo_d, hi_d = D.OMR_BOUNDS["DBP"]
    o = omr.join(pat.select("subject_id", "dod"), "subject_id", "left")
    alive = F.col("dod").isNull() | (F.col("chartdate") <= F.col("dod"))
    num = F.col("result_value").try_cast("double")
    is_bp = F.col("result_name") == "Blood Pressure"
    sbp = F.regexp_extract("result_value", BP_RE, 1).try_cast("int")
    dbp = F.regexp_extract("result_value", BP_RE, 2).try_cast("int")
    dbp_nz = F.when(dbp != 0, dbp)
    v = o.select(
        "subject_id",
        F.when(F.col("result_name").isin("BMI (kg/m2)", "BMI") & num.between(lo_b, hi_b) & alive, num).alias("bmi"),
        F.when(is_bp & sbp.between(lo_s, hi_s) & alive, sbp).alias("sbp"),
        F.when(is_bp & dbp_nz.between(lo_d, hi_d) & alive, dbp).alias("dbp"))
    return v.groupBy("subject_id").agg(
        F.median("bmi").alias("omr_BMI"), F.max(F.col("bmi").isNotNull()).alias("has_BMI"),
        F.median("sbp").alias("omr_SBP"), F.max(F.col("sbp").isNotNull()).alias("has_SBP"),
        F.median("dbp").alias("omr_DBP"), F.max(F.col("dbp").isNotNull()).alias("has_DBP"))


def population_clean(locked, analysis, labs_wide, omr_c, adm, pat):
    """clean_population.py: impossible lab values nulled, cleaned OMR, temporal flags, missingness indicators."""
    df = (locked.select(*[c for c in CLEAN_BASE if c != "icd_era"])
                .join(analysis.select("hadm_id", "icd_era"), "hadm_id", "left")
                .join(labs_wide, "hadm_id", "left"))
    for name in D.ANALYTE_IDS:
        col, (lo, hi) = f"lab_{name}", D.LAB_BOUNDS[name]
        v = F.col(col)
        imp = (v < lo) | (v > hi)
        if name == "Glucose":
            imp = imp | (v <= 0)
        df = df.withColumn(col, F.when(_false(imp), F.lit(None)).otherwise(v))
    df = df.join(omr_c, "subject_id", "left").fillna(False, ["has_BMI", "has_SBP", "has_DBP"])
    t = adm.select("hadm_id", "subject_id", "admittime", "dischtime", "deathtime", "discharge_location") \
           .join(pat.select("subject_id", "dod"), "subject_id", "left").drop("subject_id")
    df = df.join(t, "hadm_id", "left")
    neg = _false(F.col("admittime") > F.col("dischtime"))
    df = (df.withColumn("flag_neg_los", neg)
            .withColumn("los_days", F.when(neg, F.lit(None)).otherwise(F.col("los_days")))
            .withColumn("flag_death_after_disch", F.col("deathtime").isNotNull()
                        & (_false(F.col("deathtime") < F.col("admittime")) | _false(F.col("deathtime") > F.col("dischtime"))))
            .withColumn("flag_disch_after_dod", F.col("dod").isNotNull() & _false(F.to_date("dischtime") > F.col("dod"))))
    ind = ([F.col(f"lab_{k}").isNull().alias(f"miss_lab_{k}") for k in D.ANALYTE_IDS]
           + [F.col(f"omr_{m}").isNull().alias(f"miss_omr_{m}") for m in ("BMI", "SBP", "DBP")]
           + [F.col("los_days").isNull().alias("miss_los_days")]
           + [F.col(c).isNull().alias(f"miss_{c}") for c in D.CAT_MISSING])
    keep = (CLEAN_BASE + [f"lab_{k}" for k in D.ANALYTE_IDS]
            + ["omr_BMI", "has_BMI", "omr_SBP", "has_SBP", "omr_DBP", "has_DBP", "discharge_location",
               "flag_neg_los", "flag_death_after_disch", "flag_disch_after_dod"])
    return df.select(*keep, *ind)


# --- CMRF and etiology
def med_flags(rx, hadm_ids, match=None):
    """cmrf.py: distinct lower(drug) over population prescriptions with a non-ophthalmic route, flagged by match(),
    then any flag per admission. match() runs on the driver over distinct drug names only (no UDF)."""
    match = match or D.cmrf_match()
    spark = rx.sparkSession
    r = rx.join(hadm_ids, "hadm_id", "left_semi").where(D.RTFILTER).withColumn("drug_l", F.lower("drug"))
    drugs = [row.drug_l for row in r.where(F.col("drug").isNotNull()).select("drug_l").distinct().collect()]
    rows = [(d, *[bool(f[k]) for k in D.MED_FLAGS]) for d, f in ((d, match(d)) for d in drugs)]
    schema = "drug_l string, " + ", ".join(f"{k} boolean" for k in D.MED_FLAGS)
    d2c = spark.createDataFrame(rows, schema)
    return r.join(F.broadcast(d2c), "drug_l", "inner").groupBy("hadm_id").agg(
        *[F.max(k).alias(k) for k in D.MED_FLAGS])


def cmrf(clean, meds, dxs):
    """cmrf.py STEP 2: five criteria, each positive by code OR lab/vital over threshold OR qualifying medication;
    cmrf_ge1 = any positive; cmrf_unasc_all = no criterion ascertainable (no code, no medication, no measurement)."""
    m = (clean.select("hadm_id", "gender", "lab_HbA1c", "lab_Glucose", "lab_Triglycerides", "lab_HDL",
                      "omr_BMI", "omr_SBP", "omr_DBP")
              .join(meds, "hadm_id", "left").join(dxs.select("hadm_id", *D.CMRF_CODE_FLAGS), "hadm_id", "left")
              .fillna(False, list(D.MED_FLAGS) + list(D.CMRF_CODE_FLAGS)))
    c = F.col
    male = _false(c("gender") == "M")
    pos = [c("ow_code") | _false(c("omr_BMI") >= 25),
           c("dg_code") | _false(c("lab_HbA1c") >= 5.7) | _false(c("lab_Glucose") >= 100) | c("oral_ad"),
           c("htn_code") | _false(c("omr_SBP") >= 130) | _false(c("omr_DBP") >= 85) | c("htn_qual"),
           c("tg_code") | _false(c("lab_Triglycerides") >= 150) | c("lipid"),
           c("hdl_code") | (male & _false(c("lab_HDL") <= 40)) | (~male & _false(c("lab_HDL") <= 50)) | c("lipid")]
    asc = [c("ow_code") | c("omr_BMI").isNotNull(),
           c("dg_code") | c("oral_ad") | c("lab_HbA1c").isNotNull() | c("lab_Glucose").isNotNull(),
           c("htn_code") | c("htn_qual") | c("omr_SBP").isNotNull(),
           c("tg_code") | c("lipid") | c("lab_Triglycerides").isNotNull(),
           c("hdl_code") | c("lipid") | c("lab_HDL").isNotNull()]
    any_pos, any_asc = pos[0], asc[0]
    for p, a in zip(pos[1:], asc[1:]):
        any_pos, any_asc = any_pos | p, any_asc | a
    return m.select("hadm_id", any_pos.alias("cmrf_ge1"), (~any_asc).alias("cmrf_unasc_all"),
                    "alcohol", "viral", "other_etio", "cirrhosis", "hcc")


# --- labs and FIB-4
def _name_case(ids):
    expr = F.lit(None).cast("string")
    for k, i in ids.items():
        expr = F.when(F.col("itemid") == i, k).otherwise(expr)
    return expr


def lab_features(lab, locked):
    """run0919_lab_features.py: in-admission first/last value and count per analyte (charttime <= dischtime), and the
    most recent outpatient HbA1c, triglycerides and HDL in the 365 days before admittime. Admissions with no value
    are absent, as in the DuckDB output."""
    ids = D.LAB_ITEMIDS
    ev = lab.where(F.col("itemid").isin(list(ids.values())) & F.col("valuenum").isNotNull()) \
            .withColumn("analyte", _name_case(ids))
    pop = locked.select("hadm_id", "subject_id", "admittime", "dischtime")
    inadm_ev = ev.where(F.col("hadm_id").isNotNull()).join(pop.select("hadm_id", "dischtime"), "hadm_id") \
                 .where(F.col("charttime") <= F.col("dischtime"))
    order = F.struct("charttime", "labevent_id")
    g = inadm_ev.groupBy("hadm_id", "analyte").agg(F.min_by("valuenum", order).alias("first_val"),
                                                     F.max_by("valuenum", order).alias("last_val"),
                                                     F.count(F.lit(1)).alias("n"))
    wide = g.groupBy("hadm_id").agg(*[F.max(F.when(F.col("analyte") == k, F.col(v))).alias(f"{v}_{k}")
                                      for v in ("first_val", "last_val", "n") for k in ids])
    pre_ev = _outpatient_window(ev.where(F.col("analyte").isin(*D.PRE365_ANALYTES)), pop)
    pre = pre_ev.groupBy("hadm_id", "analyte").agg(F.max_by("valuenum", order).alias("v")) \
                .groupBy("hadm_id").agg(*[F.max(F.when(F.col("analyte") == k, F.col("v"))).alias(f"pre365_{k}")
                                          for k in D.PRE365_ANALYTES])
    return wide.join(pre, "hadm_id", "full_outer"), inadm_ev, pre_ev


def _outpatient_window(ev, pop):
    """Outpatient (hadm_id null) events of the same subject with admittime - 365 days <= charttime < admittime."""
    o = ev.where(F.col("hadm_id").isNull()).drop("hadm_id")
    j = o.join(pop.select("hadm_id", "subject_id", "admittime"), "subject_id")
    return j.where((F.col("charttime") < F.col("admittime"))
                   & (F.col("charttime") >= F.col("admittime") - F.expr("INTERVAL 365 DAYS")))


def outpatient_fib4_inputs(lab, locked):
    """run1110_outpt_fib4_inputs.py: most recent outpatient AST, ALT and platelets in the 365 days before admission."""
    ids = {k: D.LAB_ITEMIDS[k] for k in D.OUTPT_FIB4_ANALYTES}
    ev = lab.where(F.col("itemid").isin(list(ids.values())) & F.col("valuenum").isNotNull()) \
            .withColumn("analyte", _name_case(ids))
    w = _outpatient_window(ev, locked.select("hadm_id", "subject_id", "admittime"))
    g = w.groupBy("hadm_id", "analyte").agg(F.max_by("valuenum", F.struct("charttime", "labevent_id")).alias("v"))
    return g.groupBy("hadm_id").agg(*[F.max(F.when(F.col("analyte") == k, F.col("v"))).alias(f"out_{k}")
                                      for k in D.OUTPT_FIB4_ANALYTES]), w


def fib4_value(age, ast, alt, plt):
    """run1110_fib4_by_cell.fib4: age x AST / (platelets x sqrt(ALT)); null unless all present, ALT > 0, platelets > 0."""
    ok = ast.isNotNull() & alt.isNotNull() & plt.isNotNull() & (alt > 0) & (plt > 0)
    return F.when(ok, (age * ast) / (plt * F.sqrt(alt)))


def fib4_category(v, low):
    return (F.when(v.isNull(), F.lit(None)).when(v < low, "below_low_cutoff")
             .when(v <= D.FIB4_HIGH, "indeterminate").otherwise("above_2_67"))


def fib4(clean, feats, outpt):
    d = (clean.select("hadm_id", "subject_id", "age")
              .join(feats.select("hadm_id", "first_val_AST", "first_val_ALT", "first_val_Platelets",
                                 "last_val_AST", "last_val_ALT", "last_val_Platelets"), "hadm_id", "left")
              .join(outpt, "hadm_id", "left"))
    age = F.col("age")
    d = (d.withColumn("fib4_first", fib4_value(age, F.col("first_val_AST"), F.col("first_val_ALT"), F.col("first_val_Platelets")))
          .withColumn("fib4_last", fib4_value(age, F.col("last_val_AST"), F.col("last_val_ALT"), F.col("last_val_Platelets")))
          .withColumn("fib4_outpt", fib4_value(age, F.col("out_AST"), F.col("out_ALT"), F.col("out_Platelets"))))
    low65 = F.when(age >= 65, F.lit(D.FIB4_LOW_65)).otherwise(F.lit(D.FIB4_LOW))
    return d.select("hadm_id", "subject_id", "age", "fib4_first", "fib4_last", "fib4_outpt",
                    fib4_category(F.col("fib4_first"), F.lit(D.FIB4_LOW)).alias("fib4_first_cat"),
                    fib4_category(F.col("fib4_first"), low65).alias("fib4_first_cat_age65"),
                    fib4_category(F.col("fib4_last"), F.lit(D.FIB4_LOW)).alias("fib4_last_cat"),
                    fib4_category(F.col("fib4_outpt"), F.lit(D.FIB4_LOW)).alias("fib4_outpt_cat"))


# --- note linkage and patients
def note_links(discharge, radiology, locked):
    """Notes linked to population admissions. Inpatient: same hadm_id (discharge and radiology). Outpatient: radiology
    with no hadm_id, same subject, charttime from `before` days before to `after` days after admittime (fractional
    days, both ends included, as build_2x2.py and run0919_notes_text.py)."""
    (b1, a1), (b2, a2) = D.OUTPATIENT_WINDOWS["primary"], D.OUTPATIENT_WINDOWS["sensitivity"]
    pop = locked.select("hadm_id", F.col("subject_id").alias("adm_subject_id"), "admittime")
    cols = ["hadm_id", "subject_id", "note_id", "note_table", "link", "charttime", "days_from_admit",
            "in_window_primary", "in_window_sensitivity", "subject_matches"]

    def inpatient(notes, table):
        j = notes.where(F.col("hadm_id").isNotNull()).select("note_id", "subject_id", "hadm_id", "charttime") \
                 .withColumnRenamed("subject_id", "note_subject_id").join(pop, "hadm_id")
        return j.select("hadm_id", F.col("adm_subject_id").alias("subject_id"), "note_id",
                        F.lit(table).alias("note_table"), F.lit("inpatient").alias("link"), "charttime",
                        (_seconds("admittime", "charttime") / 86400.0).alias("days_from_admit"),
                        F.lit(True).alias("in_window_primary"), F.lit(True).alias("in_window_sensitivity"),
                        _false(F.col("note_subject_id") == F.col("adm_subject_id")).alias("subject_matches"))

    o = radiology.where(F.col("hadm_id").isNull()).select("note_id", "subject_id", "charttime") \
                 .join(pop, F.col("subject_id") == F.col("adm_subject_id"))
    o = o.withColumn("days_from_admit", _seconds("admittime", "charttime") / 86400.0)
    o = o.where((F.col("days_from_admit") >= -b1) & (F.col("days_from_admit") <= a1))
    outp = o.select("hadm_id", F.col("adm_subject_id").alias("subject_id"), "note_id",
                    F.lit("radiology").alias("note_table"), F.lit("outpatient_window").alias("link"), "charttime",
                    "days_from_admit", F.lit(True).alias("in_window_primary"),
                    ((F.col("days_from_admit") >= -b2) & (F.col("days_from_admit") <= a2)).alias("in_window_sensitivity"),
                    F.lit(True).alias("subject_matches"))
    return inpatient(discharge, "discharge").unionByName(inpatient(radiology, "radiology")).unionByName(outp).select(*cols)


def patients_flags(locked, cm, links):
    a = locked.select("hadm_id", "subject_id", "code_positive", "has_dc", "has_rad", "admittime").join(cm, "hadm_id", "left")
    outp = links.where("link = 'outpatient_window'").groupBy("subject_id") \
                .agg(F.countDistinct("note_id").alias("n_outpatient_rad_linked"))
    i = lambda c: F.col(c).cast("int")
    p = a.groupBy("subject_id").agg(
        F.count(F.lit(1)).alias("n_admissions"), F.sum(i("code_positive")).alias("n_code_positive"),
        F.sum(i("has_dc")).alias("n_with_discharge"), F.sum(i("has_rad")).alias("n_with_radiology_inpatient"),
        *[(F.max(i(c)) == 1).alias(f"any_{c}") for c in ("code_positive", "cmrf_ge1", "alcohol", "viral",
                                                         "other_etio", "cirrhosis", "hcc")],
        F.min("admittime").alias("first_admittime"), F.max("admittime").alias("last_admittime"))
    return p.join(outp, "subject_id", "left").fillna(0, ["n_outpatient_rad_linked"])


# --- run
def _reference(cfg):
    ref = (cfg.get("cohort") or {}).get("reference") or {}
    if set(ref) != set(REFERENCE_KEYS):
        raise C.ConfigError(f"cohort.reference must list {list(REFERENCE_KEYS)}")
    return ref


def run_cohort(spark, cfg, log, force=False):
    p = C.paths(cfg)
    out = p["out_root"] / "cohort"
    ref = _reference(cfg)
    parts = (cfg.get("cohort") or {}).get("partitions") or {}
    if out.exists() and any(out.iterdir()) and not force:
        raise StageFailure("cohort output exists; pass --force to rebuild it")
    (out / STAGE_OK).unlink(missing_ok=True)
    run_name = log.data["run_name"]
    raw = {t: ingested(spark, cfg, t) for t in ("admissions", "patients", "diagnoses_icd", "labevents", "omr",
                                                "prescriptions", "discharge", "radiology")}

    def save(name, df, sort_keys=("hadm_id",)):
        t = time.time()
        rec = write_table(spark, df, out, name, run_name, n_files=int(parts.get(name, 1)), sort_keys=sort_keys)
        rec["seconds"] = round(time.time() - t, 1)
        log.data["tables"][name] = rec
        log.write()
        say(f"[{name}]".ljust(25), f"rows {n(rec['rows'])}", f"{rec['n_files']} file(s) {size(rec['bytes'])}",
            f"{rec['seconds']:.1f}s")
        return spark.read.parquet(str(out / name))

    dxs = save("dx_summary", dx_summary(raw["diagnoses_icd"]))
    analysis = save("analysis_admissions", analysis_admissions(raw["admissions"], raw["patients"], dxs,
                                                               raw["discharge"], raw["radiology"]))
    locked = save("population_locked", population_locked(analysis))
    hadm = locked.select("hadm_id")
    labs_wide, lab_e = first_labs(raw["labevents"], hadm)
    clean = save("population_clean", population_clean(locked, analysis, labs_wide, omr_clean(raw["omr"], raw["patients"]),
                                                      raw["admissions"], raw["patients"]))
    cm = save("cmrf", cmrf(clean, med_flags(raw["prescriptions"], hadm), dxs))
    feats_df, inadm_ev, pre_ev = lab_features(raw["labevents"], locked)
    feats = save("lab_features", feats_df)
    outpt_df, outpt_ev = outpatient_fib4_inputs(raw["labevents"], locked)
    outpt = save("outpatient_fib4_inputs", outpt_df)
    fb = save("fib4", fib4(clean, feats, outpt))
    links = save("note_links", note_links(raw["discharge"], raw["radiology"], locked), sort_keys=("hadm_id", "note_id"))
    pf = save("patients_flags", patients_flags(locked, cm, links), sort_keys=("subject_id",))

    # ---- checks against the documented values --------------------------------------------------------------
    t = time.time()
    dc_only = locked.where("has_dc")
    got = {
        "analysis_admissions": analysis.count(),
        "analysis_code_positive": analysis.where("code_positive").count(),
        "population_admissions": locked.count(),
        "population_subjects": locked.select("subject_id").distinct().count(),
        "population_code_positive": locked.where("code_positive").count(),
        "population_discharge_only_admissions": dc_only.count(),
        "population_discharge_only_subjects": dc_only.select("subject_id").distinct().count(),
        "population_discharge_only_code_positive": dc_only.where("code_positive").count(),
    }
    checks = [(k, got[k], ref[k]) for k in REFERENCE_KEYS]
    npop = got["population_admissions"]
    checks += [("population hadm_id unique", locked.select("hadm_id").distinct().count(), npop),
               ("population_clean rows (clean_population.N_EXPECT)", clean.count(),
                # cohort.clean_rows_expected exists only for synthetic smoke tests; real runs use the frozen value
                int((cfg.get("cohort") or {}).get("clean_rows_expected", D.CLEAN_N_EXPECT))),
               ("cmrf rows", cm.count(), npop), ("fib4 rows", fb.count(), npop),
               ("patients_flags rows", pf.count(), got["population_subjects"])]
    results = []
    for name, value, expected in checks:
        ok = value == expected
        results.append({"check": name, "value": value, "expected": expected, "pass": ok})
        say("[check]", f"{name:<52}", f"{n(value):>12}", f"reference {n(expected):>12}", "PASS" if ok else "FAIL")
    log.data["checks"] = results

    # ---- aggregate summaries ----------------------------------------------------------------------------------
    s = {}
    s["code_negative"] = npop - got["population_code_positive"]
    for c in ("cmrf_ge1", "cmrf_unasc_all", "alcohol", "viral", "other_etio", "cirrhosis", "hcc"):
        s[f"population_{c}"] = cm.where(F.col(c)).count()
    for c in ("fib4_first", "fib4_last", "fib4_outpt"):
        s[f"{c}_computable"] = fb.where(F.col(c).isNotNull()).count()
    s["fib4_first_cat"] = {r["fib4_first_cat"]: r["count"] for r in fb.groupBy("fib4_first_cat").count().collect()
                           if r["fib4_first_cat"] is not None}
    s["ties_clean_first_labs"] = tied_pairs(lab_e, ["hadm_id", "itemid"], which="min")
    s["ties_lab_features_first"] = tied_pairs(inadm_ev, ["hadm_id", "analyte"], which="min")
    s["ties_lab_features_last"] = tied_pairs(inadm_ev, ["hadm_id", "analyte"], which="max")
    s["ties_pre365"] = tied_pairs(pre_ev, ["hadm_id", "analyte"], which="max")
    s["ties_outpatient_fib4"] = tied_pairs(outpt_ev, ["hadm_id", "analyte"], which="max")
    lk = {f"{r['note_table']}|{r['link']}": r["count"] for r in links.groupBy("note_table", "link").count().collect()}
    s["links"] = lk
    s["links_outpatient_sensitivity_window"] = links.where("link = 'outpatient_window' AND in_window_sensitivity").count()
    s["links_subject_mismatch"] = links.where("NOT subject_matches").count()
    s["seconds_checks"] = round(time.time() - t, 1)
    log.data["summary"] = s
    say("[summary]", f"code-positive {n(got['population_code_positive'])}", f"code-negative {n(s['code_negative'])}")
    say("[summary]", "flags:", *[f"{c} {n(s[f'population_{c}'])}" for c in
                                 ("cmrf_ge1", "cmrf_unasc_all", "alcohol", "viral", "other_etio", "cirrhosis", "hcc")])
    say("[summary]", "FIB-4 computable:", f"first {n(s['fib4_first_computable'])}",
        f"last {n(s['fib4_last_computable'])}", f"outpatient {n(s['fib4_outpt_computable'])}")
    say("[summary]", "FIB-4 first, categories:", *[f"{k} {n(v)}" for k, v in sorted(s["fib4_first_cat"].items())])
    say("[summary]", "ties at the same charttime (admission x analyte):",
        f"clean first {n(s['ties_clean_first_labs'])}", f"features first {n(s['ties_lab_features_first'])}",
        f"last {n(s['ties_lab_features_last'])}", f"pre365 {n(s['ties_pre365'])}",
        f"outpatient FIB-4 {n(s['ties_outpatient_fib4'])}")
    say("[summary]", "note links:", *[f"{k} {n(v)}" for k, v in sorted(lk.items())],
        f"outpatient in 90/30 window {n(s['links_outpatient_sensitivity_window'])}",
        f"inpatient links whose note subject differs {n(s['links_subject_mismatch'])}")

    ok = all(r["pass"] for r in results)
    if ok:
        (out / STAGE_OK).write_text(json.dumps({"stage": "cohort", "run_name": run_name, "verified_utc": utc_now(),
                                                "checks": results}, indent=1, default=str))
    return EXIT_OK if ok else EXIT_FAIL


def main(argv=None, spark=None):
    ap = argparse.ArgumentParser(description="Step 2: cohort and linkage (aggregates only).")
    ap.add_argument("--config", default="conf/spark_local.yaml")
    ap.add_argument("--run-name")
    ap.add_argument("--force", action="store_true", help="rebuild the cohort output")
    a = ap.parse_args(argv)
    try:
        cfg = C.load(a.config)
        _reference(cfg)
    except (OSError, C.ConfigError, ValueError) as e:
        say("[cohort] config error:", e)
        return EXIT_FAIL
    p = C.paths(cfg)
    name = a.run_name or f"{cfg.get('run_name_prefix', 'run')}-cohort-{datetime.now():%Y%m%d-%H%M%S}"
    log = RunLog(p["runs_root"], name, "cohort", cfg)
    own = spark is None
    code = EXIT_FAIL
    try:
        if own:
            spark = build_session(cfg, log.private)
        log.spark_versions(spark)
        v = log.data["versions"]
        say(f"[cohort] run {name}", f"Spark {v['spark']}", f"Java {v.get('java')}", f"master {v.get('master')}")
        code = run_cohort(spark, cfg, log, force=a.force)
    except StageFailure as e:
        say("[cohort] stopped:", e)
    except Exception as e:   # noqa: BLE001 — classified, never printed
        log.private_error("cohort", e)
        say("[cohort] run failed:", describe_error(e))
    finally:
        m = log.memory(spark)
        heap = m.get("jvm_heap_peak_bytes_upper_bound")
        say("[cohort] peak memory:", f"driver Python {size(m['driver_python_peak_rss_bytes'])}",
            f"JVM heap ≤ {size(heap)} of {size(m['jvm_heap_max_bytes'])}" if heap is not None else "JVM heap n/a",
            f"elapsed {time.time() - log._t0:,.0f}s")
        if own and spark is not None:
            spark.stop()
        log.finish("PASS" if code == EXIT_OK else "FAIL", code)
        say(f"[cohort] exit {code}; run log {log.dir / 'run.json'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
