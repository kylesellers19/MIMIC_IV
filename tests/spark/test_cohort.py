"""Step 2 (cohort and linkage) on the invented hospital in cohort_fixture.py, one rule per test."""
import datetime as dt
import json
import math

import pytest
import yaml
from pyspark.sql import functions as F

from masld_spark import cohort as CO
from masld_spark import config as C
from masld_spark import definitions as D
from masld_spark.ingest import OK_JSON
from masld_spark.runlog import RunLog

import cohort_fixture as FX
import synthetic as SY


@pytest.fixture(scope="module")
def fx(spark):
    f = FX.frames(spark)
    dxs = CO.dx_summary(f["diagnoses_icd"]).cache()
    analysis = CO.analysis_admissions(f["admissions"], f["patients"], dxs, f["discharge"], f["radiology"]).cache()
    locked = CO.population_locked(analysis).cache()
    return {**f, "dxs": dxs, "analysis": analysis, "locked": locked}


def by(df, key="hadm_id"):
    return {r[key]: r.asDict() for r in df.collect()}


# ---------------------------------------------------------------- diagnoses and population
def test_dx_summary_counts_codes_and_eras(fx):
    d = by(fx["dxs"])
    assert d[2001]["n_diagnoses"] == 3                       # distinct (seq_num, icd_version): the padded duplicate collapses
    assert d[2001]["code_positive"] and d[2003]["code_positive"]
    assert not d[2004]["code_positive"]                      # '5718' under ICD-10 is not the ICD-9 code
    assert d[2001]["dg_code"] and d[2001]["htn_code"] and d[2003]["htn_code"] and d[2003]["cirrhosis"]
    assert d[2004]["alcohol"] and d[2004]["viral"] and d[2006]["ow_code"] and not d[2002]["tg_code"]
    assert d[2001]["minv"] == 10 and d[2003]["maxv"] == 9


def test_analysis_admissions_and_population(fx):
    a = by(fx["analysis"])
    assert set(a) == {2001, 2002, 2003, 2004, 2006}           # 2005 has no diagnosis row
    assert a[2003]["age"] == 91 and a[2003]["age_at_admit"] == 96
    assert a[2001]["los_days"] == 2.0 and a[2004]["los_days"] == -1.0
    assert a[2001]["icd_era"] == "ICD-10 only" and a[2003]["icd_era"] == "ICD-9 only"
    assert a[2001]["has_dc"] and not a[2001]["has_rad"] and a[2003]["has_rad"] and not a[2003]["has_dc"]
    assert not a[2002]["has_note"] and a[2002]["subj_has_note"]
    assert not a[2006]["has_note"] and not a[2006]["subj_has_note"]   # outpatient radiology does not count
    locked = by(fx["locked"])
    assert set(locked) == {2001, 2003, 2004}
    assert list(fx["locked"].columns) == CO.LOCKED_COLUMNS and len(CO.LOCKED_COLUMNS) == 22


# ---------------------------------------------------------------- cleaned covariates
def test_first_labs_skip_nulls_and_break_ties_by_labevent_id(fx):
    wide, e = CO.first_labs(fx["labevents"], fx["locked"].select("hadm_id"))
    w = by(wide)
    assert w[2001]["lab_ALT"] == 20.0                        # tie at 01:00: labevent 3 (20.0) beats 5 (10.0)
    assert w[2001]["lab_GGT"] == 30.0 and w[2001]["lab_HbA1c"] is None   # outpatient rows are not hadm-linked
    assert CO.tied_pairs(e, ["hadm_id", "itemid"]) == 1


def test_omr_clean_bounds_dbp_zero_and_death_date(fx):
    o = by(CO.omr_clean(fx["omr"], fx["patients"]), "subject_id")
    assert o[101]["omr_BMI"] == 27.5 and o[101]["omr_SBP"] == 122.5 and o[101]["omr_DBP"] == 80.0
    assert o[102]["omr_BMI"] == 35.0 and not o[102]["has_SBP"]           # readings after the death date dropped


def test_population_clean_nulls_flags_and_indicators(fx):
    wide, _ = CO.first_labs(fx["labevents"], fx["locked"].select("hadm_id"))
    clean = CO.population_clean(fx["locked"], fx["analysis"], wide, CO.omr_clean(fx["omr"], fx["patients"]),
                                fx["admissions"], fx["patients"])
    c = by(clean)
    assert len(c) == 3
    assert c[2001]["lab_Glucose"] is None and c[2001]["miss_lab_Glucose"]   # glucose 0 is impossible
    assert c[2004]["lab_ALT"] is None                                       # 60000 > 50000
    assert c[2004]["flag_neg_los"] and c[2004]["los_days"] is None and c[2004]["miss_los_days"]
    assert c[2003]["flag_disch_after_dod"] and c[2003]["flag_death_after_disch"] and c[2003]["miss_insurance"]
    assert not c[2001]["flag_neg_los"] and not c[2001]["flag_death_after_disch"] and not c[2001]["flag_disch_after_dod"]
    assert c[2004]["has_BMI"] is False and c[2004]["omr_BMI"] is None and c[2004]["miss_omr_BMI"]
    assert c[2001]["discharge_location"] == "HOME"
    for k in D.ANALYTE_IDS:
        assert f"lab_{k}" in clean.columns and f"miss_lab_{k}" in clean.columns
    assert {f"miss_{x}" for x in D.CAT_MISSING} <= set(clean.columns)


# ---------------------------------------------------------------- CMRF
def test_med_flags_route_filter_and_exclusions(fx):
    m = by(CO.med_flags(fx["prescriptions"], fx["locked"].select("hadm_id")))
    assert m[2001]["oral_ad"] and m[2001]["metformin"] and not m[2001]["lipid"]   # niacinamide is not niacin
    assert m[2003]["htn_qual"]                                                  # route null passes the filter
    assert 2004 not in m or not any(m[2004][k] for k in D.MED_FLAGS)            # eye route dropped; aspartame no flag
    assert 2002 not in m                                                        # not in the population


def test_cmrf_criteria(fx):
    wide, _ = CO.first_labs(fx["labevents"], fx["locked"].select("hadm_id"))
    clean = CO.population_clean(fx["locked"], fx["analysis"], wide, CO.omr_clean(fx["omr"], fx["patients"]),
                                fx["admissions"], fx["patients"])
    c = by(CO.cmrf(clean, CO.med_flags(fx["prescriptions"], fx["locked"].select("hadm_id")), fx["dxs"]))
    assert c[2001]["cmrf_ge1"] and not c[2001]["cmrf_unasc_all"]
    assert c[2003]["cmrf_ge1"] and c[2003]["cirrhosis"]
    assert not c[2004]["cmrf_ge1"] and c[2004]["cmrf_unasc_all"] and c[2004]["alcohol"] and c[2004]["viral"]


def test_low_hdl_threshold_depends_on_sex(spark):
    clean = spark.createDataFrame(
        [(1, "F", None, None, None, 45.0, None, None, None), (2, "M", None, None, None, 45.0, None, None, None)],
        "hadm_id long, gender string, lab_HbA1c double, lab_Glucose double, lab_Triglycerides double, "
        "lab_HDL double, omr_BMI double, omr_SBP double, omr_DBP double")
    meds = spark.createDataFrame([], "hadm_id long, " + ", ".join(f"{k} boolean" for k in D.MED_FLAGS))
    dxs = spark.createDataFrame([], "hadm_id long, " + ", ".join(f"{k} boolean" for k in D.CMRF_CODE_FLAGS))
    c = by(CO.cmrf(clean, meds, dxs))
    assert c[1]["cmrf_ge1"] and not c[2]["cmrf_ge1"]


# ---------------------------------------------------------------- labs and FIB-4
def test_lab_features_window_and_pre365(fx):
    feats, inadm, pre = CO.lab_features(fx["labevents"], fx["locked"])
    f = by(feats)
    assert f[2001]["first_val_ALT"] == 20.0 and f[2001]["last_val_ALT"] == 99.0 and f[2001]["n_ALT"] == 3
    assert f[2001]["pre365_HbA1c"] == 7.0                    # most recent in [admittime - 365 d, admittime)
    assert f[2004]["first_val_ALT"] == 60000.0               # the features are not cleaned (run0919_lab_features.py)
    assert f[2001]["first_val_Glucose"] == 0.0
    days = sorted(r.charttime for r in pre.where("analyte = 'HbA1c'").collect())
    assert days == [dt.datetime(2149, 6, 1), dt.datetime(2150, 5, 1)]   # -365 d included; admittime and earlier excluded


def test_fib4_values_and_categories(fx):
    wide, _ = CO.first_labs(fx["labevents"], fx["locked"].select("hadm_id"))
    clean = CO.population_clean(fx["locked"], fx["analysis"], wide, CO.omr_clean(fx["omr"], fx["patients"]),
                                fx["admissions"], fx["patients"])
    feats, _, _ = CO.lab_features(fx["labevents"], fx["locked"])
    outpt, _ = CO.outpatient_fib4_inputs(fx["labevents"], fx["locked"])
    f = by(CO.fib4(clean, feats, outpt))
    assert math.isclose(f[2001]["fib4_first"], 50 * 40 / (200 * math.sqrt(20)))
    assert f[2001]["fib4_first_cat"] == "indeterminate"
    assert math.isclose(f[2001]["fib4_last"], 50 * 40 / (200 * math.sqrt(99))) and f[2001]["fib4_last_cat"] == "below_low_cutoff"
    assert math.isclose(f[2001]["fib4_outpt"], 50 * 30 / (150 * 6))
    assert f[2003]["fib4_first"] is None                     # ALT 0
    assert f[2004]["fib4_first"] is None                     # AST and platelets missing


def test_fib4_age65_cutoff(spark):
    df = spark.createDataFrame([(1.5, 70), (1.5, 60)], "v double, age int")
    low65 = F.when(F.col("age") >= 65, F.lit(D.FIB4_LOW_65)).otherwise(F.lit(D.FIB4_LOW))
    got = [r.c for r in df.select(CO.fib4_category(F.col("v"), low65).alias("c")).collect()]
    assert got == ["below_low_cutoff", "indeterminate"]


# ---------------------------------------------------------------- note links and patients
def test_note_links_windows_and_subjects(fx):
    links = CO.note_links(fx["discharge"], fx["radiology"], fx["locked"])
    rows = {r.note_id: r.asDict() for r in links.collect()}
    assert set(rows) == {"101-DS-1", "999-DS-1", "103-DS-1", "102-RR-1", "101-RR-a", "101-RR-c", "101-RR-d"}
    assert rows["999-DS-1"]["subject_matches"] is False and rows["999-DS-1"]["subject_id"] == 101
    assert rows["101-RR-a"]["link"] == "outpatient_window" and rows["101-RR-a"]["days_from_admit"] == -365.0
    assert not rows["101-RR-a"]["in_window_sensitivity"]
    assert rows["101-RR-c"]["in_window_sensitivity"] and rows["101-RR-d"]["in_window_sensitivity"]
    assert rows["102-RR-1"]["link"] == "inpatient" and rows["102-RR-1"]["note_table"] == "radiology"


def test_patients_flags(fx):
    links = CO.note_links(fx["discharge"], fx["radiology"], fx["locked"])
    cm = fx["dxs"].select("hadm_id").withColumn("cmrf_ge1", F.lit(True))
    for c in ("alcohol", "viral", "other_etio", "cirrhosis", "hcc"):
        cm = cm.join(fx["dxs"].select("hadm_id", c), "hadm_id")
    p = by(CO.patients_flags(fx["locked"], cm, links), "subject_id")
    assert set(p) == {101, 102, 103}
    assert p[101]["n_admissions"] == 1 and p[101]["n_outpatient_rad_linked"] == 3 and p[101]["any_code_positive"]
    assert p[103]["any_alcohol"] and not p[103]["any_code_positive"]


# ---------------------------------------------------------------- the whole step
def _ingest_dir(spark, cfg):
    out = C.paths(cfg)["out_root"] / "ingest"
    for t, df in FX.frames(spark).items():
        df.write.mode("overwrite").parquet(str(out / t))
        (out / t / OK_JSON).write_text("{}")


def _cfg(tmp_path, reference):
    cfg = SY.make_cfg(tmp_path)
    cfg["cohort"] = {"partitions": {"note_links": 2}, "reference": dict(reference)}
    return cfg


def test_run_cohort_passes_and_writes_marker(spark, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(D, "CLEAN_N_EXPECT", 3)
    cfg = _cfg(tmp_path, FX.REFERENCE)
    _ingest_dir(spark, cfg)
    conf = tmp_path / "conf.yaml"
    conf.write_text(yaml.safe_dump({k: v for k, v in cfg.items() if k != "_source"}))
    code = CO.main(["--config", str(conf), "--run-name", "c1"], spark=spark)
    out = capsys.readouterr().out
    assert code == CO.EXIT_OK, out
    marker = json.loads((tmp_path / "out" / "cohort" / CO.STAGE_OK).read_text())
    assert all(c["pass"] for c in marker["checks"])
    for name in ("dx_summary", "analysis_admissions", "population_locked", "population_clean", "cmrf", "lab_features",
                 "outpatient_fib4_inputs", "fib4", "note_links", "patients_flags"):
        assert (tmp_path / "out" / "cohort" / name).exists(), name
    for frag in FX.VALUE_FRAGMENTS:
        assert frag not in out, frag
    run = json.loads((tmp_path / "runs" / "c1" / "run.json").read_text())
    assert run["summary"]["ties_clean_first_labs"] == 1 and run["summary"]["links_subject_mismatch"] == 1
    assert run["tables"]["note_links"]["rows"] == 7 and run["tables"]["population_locked"]["rows"] == 3


def test_run_cohort_fails_on_reference_mismatch_and_refuses_rerun(spark, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(D, "CLEAN_N_EXPECT", 3)
    bad = dict(FX.REFERENCE, population_admissions=4)
    cfg = _cfg(tmp_path, bad)
    _ingest_dir(spark, cfg)
    log = RunLog(tmp_path / "runs", "c2", "cohort", cfg)
    assert CO.run_cohort(spark, cfg, log) == CO.EXIT_FAIL
    assert not (tmp_path / "out" / "cohort" / CO.STAGE_OK).exists()
    log2 = RunLog(tmp_path / "runs", "c3", "cohort", cfg)
    with pytest.raises(CO.StageFailure):
        CO.run_cohort(spark, cfg, log2)                       # output exists, no --force


def test_run_cohort_requires_verified_ingest(spark, tmp_path):
    cfg = _cfg(tmp_path, FX.REFERENCE)
    log = RunLog(tmp_path / "runs", "c4", "cohort", cfg)
    with pytest.raises(CO.StageFailure, match="not been verified"):
        CO.run_cohort(spark, cfg, log)
