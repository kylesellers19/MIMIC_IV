"""Explicit schemas for the 12 MIMIC-IV v3.1 (hosp) and MIMIC-IV-Note v2.2 (note) files the study uses.

Column names and order follow the published DDL (MIT-LCP/mimic-code, mimic-iv/buildmimic/postgres/create.sql
and mimic-iv-note/buildmimic/postgres/create.sql, main branch, read 2026-11-26). No schema is inferred.

Type choices:
  * every identifier is LongType (BIGINT, as the DuckDB pipeline reads them);
  * codes stay strings (icd_code keeps MIMIC's trailing-space padding; trimming is a cohort-stage decision);
  * timestamps are TimestampNTZType: MIMIC times are shifted, zone-less wall-clock values, so no session time
    zone may move them (a zone-aware type would shift or reject times inside a daylight-saving gap);
  * DDL NOT NULL is not enforced here; null rates are reported by the validation gates (Step 5).

`TABLES` also fixes, per table, the module folder under the raw root and the sort / range-partition keys.
"""
import hashlib
import json

from pyspark.sql.types import (DateType, DoubleType, IntegerType, LongType, StringType, StructField,
                               StructType, TimestampNTZType)

S, I, L, D, TS, DT = StringType(), IntegerType(), LongType(), DoubleType(), TimestampNTZType(), DateType()


def _schema(*cols):
    return StructType([StructField(name, typ, True) for name, typ in cols])


SCHEMAS = {
    # ---- hosp ------------------------------------------------------------------------------------
    "admissions": _schema(
        ("subject_id", L), ("hadm_id", L), ("admittime", TS), ("dischtime", TS), ("deathtime", TS),
        ("admission_type", S), ("admit_provider_id", S), ("admission_location", S),
        ("discharge_location", S), ("insurance", S), ("language", S), ("marital_status", S), ("race", S),
        ("edregtime", TS), ("edouttime", TS), ("hospital_expire_flag", I)),
    "patients": _schema(
        ("subject_id", L), ("gender", S), ("anchor_age", I), ("anchor_year", I), ("anchor_year_group", S),
        ("dod", DT)),
    "diagnoses_icd": _schema(
        ("subject_id", L), ("hadm_id", L), ("seq_num", I), ("icd_code", S), ("icd_version", I)),
    "d_icd_diagnoses": _schema(
        ("icd_code", S), ("icd_version", I), ("long_title", S)),
    "labevents": _schema(
        ("labevent_id", L), ("subject_id", L), ("hadm_id", L), ("specimen_id", L), ("itemid", I),
        ("order_provider_id", S), ("charttime", TS), ("storetime", TS), ("value", S), ("valuenum", D),
        ("valueuom", S), ("ref_range_lower", D), ("ref_range_upper", D), ("flag", S), ("priority", S),
        ("comments", S)),
    "d_labitems": _schema(
        ("itemid", I), ("label", S), ("fluid", S), ("category", S)),
    "omr": _schema(
        ("subject_id", L), ("chartdate", DT), ("seq_num", I), ("result_name", S), ("result_value", S)),
    "prescriptions": _schema(
        ("subject_id", L), ("hadm_id", L), ("pharmacy_id", L), ("poe_id", S), ("poe_seq", I),
        ("order_provider_id", S), ("starttime", TS), ("stoptime", TS), ("drug_type", S), ("drug", S),
        ("formulary_drug_cd", S), ("gsn", S), ("ndc", S), ("prod_strength", S), ("form_rx", S),
        ("dose_val_rx", S), ("dose_unit_rx", S), ("form_val_disp", S), ("form_unit_disp", S),
        ("doses_per_24_hrs", D), ("route", S)),
    # ---- note ------------------------------------------------------------------------------------
    "discharge": _schema(
        ("note_id", S), ("subject_id", L), ("hadm_id", L), ("note_type", S), ("note_seq", I),
        ("charttime", TS), ("storetime", TS), ("text", S)),
    "discharge_detail": _schema(
        ("note_id", S), ("subject_id", L), ("field_name", S), ("field_value", S), ("field_ordinal", I)),
    "radiology": _schema(
        ("note_id", S), ("subject_id", L), ("hadm_id", L), ("note_type", S), ("note_seq", I),
        ("charttime", TS), ("storetime", TS), ("text", S)),
    "radiology_detail": _schema(
        ("note_id", S), ("subject_id", L), ("field_name", S), ("field_value", S), ("field_ordinal", I)),
}

# module folder, sort keys (the first key is the range-partition key when the table has >1 partition)
TABLES = {
    "admissions":       ("hosp", ["subject_id", "hadm_id"]),
    "patients":         ("hosp", ["subject_id"]),
    "diagnoses_icd":    ("hosp", ["subject_id", "hadm_id", "seq_num", "icd_version"]),
    "d_icd_diagnoses":  ("hosp", ["icd_version", "icd_code"]),
    "labevents":        ("hosp", ["subject_id", "charttime", "labevent_id"]),
    "d_labitems":       ("hosp", ["itemid"]),
    "omr":              ("hosp", ["subject_id", "chartdate", "seq_num", "result_name"]),
    "prescriptions":    ("hosp", ["subject_id", "hadm_id", "starttime", "pharmacy_id"]),
    "discharge":        ("note", ["subject_id", "hadm_id", "note_seq", "note_id"]),
    "discharge_detail": ("note", ["subject_id", "note_id", "field_ordinal"]),
    "radiology":        ("note", ["subject_id", "charttime", "note_id"]),
    "radiology_detail": ("note", ["subject_id", "note_id", "field_ordinal"]),
}
assert set(TABLES) == set(SCHEMAS)


def column_names(table):
    return [f.name for f in SCHEMAS[table].fields]


def schema_fingerprint(table):
    """SHA-256 of the schema JSON: an ingested table is reusable only while its schema is unchanged."""
    return hashlib.sha256(json.dumps(SCHEMAS[table].jsonValue(), sort_keys=True).encode()).hexdigest()
