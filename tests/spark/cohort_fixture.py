"""One small invented hospital for the Step 2 tests. Every value is synthetic; identifiers are short (never 8 digits).

Admissions (admittime):
  2001  subject 101 (F, 50)  2150-06-01  discharge note, outpatient radiology around it; code+ (K760 padded)
  2002  subject 101          2151-01-01  diagnoses but no note -> not in the population (subject still has notes)
  2003  subject 102 (M, 91+) 2155-01-01  inpatient radiology only; code+ (ICD-9 5718); discharged after death date
  2004  subject 103 (M, 40)  2150-03-05  discharge note; dischtime before admittime; '5718' under ICD-10 (not code+)
  2005  subject 104 (F, 70)  2152-02-01  no diagnosis row -> not in the analysis admissions
  2006  subject 104          2153-05-01  diagnoses, outpatient radiology only -> not in the population
"""
import datetime as dt

from masld_spark.schemas import SCHEMAS


def T(s):
    return dt.datetime.fromisoformat(s) if s else None


def Dd(s):
    return dt.date.fromisoformat(s) if s else None


PATIENTS = [
    dict(subject_id=101, gender="F", anchor_age=50, anchor_year=2150, anchor_year_group="2008 - 2010", dod=None),
    dict(subject_id=102, gender="M", anchor_age=91, anchor_year=2150, anchor_year_group="2008 - 2010", dod=Dd("2155-01-05")),
    dict(subject_id=103, gender="M", anchor_age=40, anchor_year=2150, anchor_year_group="2011 - 2013", dod=None),
    dict(subject_id=104, gender="F", anchor_age=70, anchor_year=2150, anchor_year_group="2011 - 2013", dod=None),
]


def _adm(hadm, subj, admit, disch, death=None, insurance="Medicare"):
    return dict(subject_id=subj, hadm_id=hadm, admittime=T(admit), dischtime=T(disch), deathtime=T(death),
                admission_type="EW EMER.", admit_provider_id="P0", admission_location="EMERGENCY ROOM",
                discharge_location="HOME", insurance=insurance, language="English", marital_status="MARRIED",
                race="WHITE", edregtime=None, edouttime=None, hospital_expire_flag=0)


ADMISSIONS = [
    _adm(2001, 101, "2150-06-01 00:00:00", "2150-06-03 00:00:00"),
    _adm(2002, 101, "2151-01-01 00:00:00", "2151-01-02 12:00:00"),
    _adm(2003, 102, "2155-01-01 00:00:00", "2155-01-10 00:00:00", death="2155-01-12 00:00:00", insurance=None),
    _adm(2004, 103, "2150-03-05 10:00:00", "2150-03-04 10:00:00"),
    _adm(2005, 104, "2152-02-01 00:00:00", "2152-02-05 00:00:00"),
    _adm(2006, 104, "2153-05-01 00:00:00", "2153-05-04 00:00:00"),
]


def _dx(hadm, subj, seq, ver, code):
    return dict(subject_id=subj, hadm_id=hadm, seq_num=seq, icd_version=ver, icd_code=code)


DIAGNOSES = [
    _dx(2001, 101, 1, 10, "K760   "), _dx(2001, 101, 1, 10, "K760"), _dx(2001, 101, 2, 10, "E119"),
    _dx(2001, 101, 3, 10, "I10"),
    _dx(2002, 101, 1, 10, "E785"),
    _dx(2003, 102, 1, 9, "5718"), _dx(2003, 102, 2, 9, "5715"), _dx(2003, 102, 3, 9, "4019"),
    _dx(2004, 103, 1, 10, "5718"), _dx(2004, 103, 2, 10, "F1020"), _dx(2004, 103, 3, 10, "B182"),
    _dx(2006, 104, 1, 9, "27801"),
]

ALT, AST, PLT, HBA1C, GLU, HDL, GGT = 50861, 50878, 51265, 50852, 50931, 50904, 50927


def _lab(lid, subj, hadm, item, t, v):
    return dict(labevent_id=lid, subject_id=subj, hadm_id=hadm, specimen_id=9000 + lid, itemid=item,
                order_provider_id=None, charttime=T(t), storetime=None, value=None if v is None else str(v),
                valuenum=v, valueuom=None, ref_range_lower=None, ref_range_upper=None, flag=None,
                priority=None, comments=None)


LABS = [
    # 2001: ALT null earliest, a tie at 01:00 (ids 5 and 3), a later value, one after discharge
    _lab(1, 101, 2001, ALT, "2150-06-01 00:30:00", None),
    _lab(5, 101, 2001, ALT, "2150-06-01 01:00:00", 10.0),
    _lab(3, 101, 2001, ALT, "2150-06-01 01:00:00", 20.0),
    _lab(7, 101, 2001, ALT, "2150-06-02 00:00:00", 99.0),
    _lab(8, 101, 2001, ALT, "2150-06-04 00:00:00", 60000.0),
    _lab(9, 101, 2001, AST, "2150-06-01 02:00:00", 40.0),
    _lab(10, 101, 2001, PLT, "2150-06-01 02:00:00", 200.0),
    _lab(11, 101, 2001, GGT, "2150-06-01 03:00:00", 30.0),
    _lab(12, 101, 2001, GLU, "2150-06-01 03:00:00", 0.0),
    _lab(13, 101, 2001, HDL, "2150-06-01 03:00:00", 45.0),
    # subject 101 outpatient (no hadm_id): HbA1c at exactly -365 d, a more recent one, one at admittime, one too early
    _lab(20, 101, None, HBA1C, "2149-06-01 00:00:00", 6.0),
    _lab(21, 101, None, HBA1C, "2150-05-01 00:00:00", 7.0),
    _lab(22, 101, None, HBA1C, "2150-06-01 00:00:00", 8.0),
    _lab(23, 101, None, HBA1C, "2149-05-31 23:00:00", 9.0),
    _lab(24, 101, None, AST, "2150-05-01 00:00:00", 30.0),
    _lab(25, 101, None, ALT, "2150-05-01 00:00:00", 36.0),
    _lab(26, 101, None, PLT, "2150-05-01 00:00:00", 150.0),
    # 2003: ALT 0 -> FIB-4 not computable
    _lab(30, 102, 2003, AST, "2155-01-02 00:00:00", 80.0),
    _lab(31, 102, 2003, ALT, "2155-01-02 00:00:00", 0.0),
    _lab(32, 102, 2003, PLT, "2155-01-02 00:00:00", 100.0),
    # 2004: an impossible ALT (nulled by cleaning, kept by the lab features), inside the (negative) stay
    _lab(40, 103, 2004, ALT, "2150-03-04 09:00:00", 60000.0),
]


def _omr(subj, date, seq, name, value):
    return dict(subject_id=subj, chartdate=Dd(date), seq_num=seq, result_name=name, result_value=value)


OMR = [
    _omr(101, "2150-01-01", 1, "BMI", "7"), _omr(101, "2150-01-02", 1, "BMI", "25"),
    _omr(101, "2150-01-03", 1, "BMI (kg/m2)", "30"),
    _omr(101, "2150-01-01", 1, "Blood Pressure", "120/80"), _omr(101, "2150-01-02", 1, "Blood Pressure", "125/0"),
    _omr(101, "2150-01-03", 1, "Blood Pressure", "abc"), _omr(101, "2150-01-03", 1, "Weight (Lbs)", "150"),
    _omr(102, "2154-12-01", 1, "BMI", "35"), _omr(102, "2155-01-06", 1, "BMI", "40"),
    _omr(102, "2155-01-06", 1, "Blood Pressure", "200/100"),
]


def _rx(subj, hadm, pid, drug, route):
    return dict(subject_id=subj, hadm_id=hadm, pharmacy_id=pid, poe_id=None, poe_seq=None, order_provider_id=None,
                starttime=None, stoptime=None, drug_type="MAIN", drug=drug, formulary_drug_cd=None, gsn=None,
                ndc=None, prod_strength=None, form_rx=None, dose_val_rx=None, dose_unit_rx=None,
                form_val_disp=None, form_unit_disp=None, doses_per_24_hrs=None, route=route)


PRESCRIPTIONS = [
    _rx(101, 2001, 1, "Metformin", "PO"), _rx(101, 2001, 2, "Metamucil", "PO"),
    _rx(101, 2001, 3, "Niacinamide", "PO"),
    _rx(102, 2003, 4, "Lisinopril", None),
    _rx(103, 2004, 5, "Timolol Maleate 0.5%", "BOTH EYES"), _rx(103, 2004, 6, "Aspartame", "PO"),
    _rx(101, 2002, 7, "Atorvastatin", "PO"),
]


# Texts for the Step 3 tests (frozen rule, sections). Notes not listed read "Synthetic note."
TEXTS = {
    "103-DS-1": "Discharge Diagnosis:\nDiffuse fatty liver.\n\nBrief Hospital Course:\nInvented course.\n",
    "102-RR-1": ("FINDINGS: "
                 "Invented, no hepatic steatosis.\n"
                 "IMPRESSION: Invented normal study."),
    "101-RR-a": "LIVER: Invented hepatic steatosis.",
}


def _note(nid, subj, hadm, kind, t):
    return dict(note_id=nid, subject_id=subj, hadm_id=hadm, note_type=kind, note_seq=1, charttime=T(t),
                storetime=None, text=TEXTS.get(nid, "Synthetic note."))


DISCHARGE = [
    _note("101-DS-1", 101, 2001, "DS", "2150-06-03 00:00:00"),
    _note("999-DS-1", 999, 2001, "DS", "2150-06-03 00:00:00"),       # subject differs from the admission's
    _note("103-DS-1", 103, 2004, "DS", "2150-03-04 10:00:00"),
]
RADIOLOGY = [
    _note("102-RR-1", 102, 2003, "RR", "2155-01-02 00:00:00"),
    _note("101-RR-a", 101, None, "RR", "2149-06-01 00:00:00"),       # exactly -365 days: linked, not in 90/30
    _note("101-RR-b", 101, None, "RR", "2149-05-31 23:00:00"),       # -365 days - 1 hour: not linked
    _note("101-RR-c", 101, None, "RR", "2150-03-03 00:00:00"),       # -90 days: linked, in 90/30
    _note("101-RR-d", 101, None, "RR", "2150-07-01 00:00:00"),       # +30 days: linked, in 90/30
    _note("101-RR-e", 101, None, "RR", "2150-07-01 00:00:01"),       # +30 days + 1 s: not linked
    _note("104-RR-a", 104, None, "RR", "2153-04-20 00:00:00"),       # subject has no population admission
    _note("777-RR-1", 101, 9999, "RR", "2150-06-02 00:00:00"),       # hadm_id not an admission
]

RADIOLOGY_DETAIL = [
    dict(note_id="102-RR-1", subject_id=102, field_name="exam_name", field_value="CT ABDOMEN W/CONTRAST", field_ordinal=1),
    dict(note_id="101-RR-a", subject_id=101, field_name="exam_name", field_value="CHEST (PA & LAT)", field_ordinal=1),
    dict(note_id="101-RR-c", subject_id=101, field_name="cpt_code", field_value="74177", field_ordinal=1),
]

TABLE_ROWS = {"patients": PATIENTS, "admissions": ADMISSIONS, "diagnoses_icd": DIAGNOSES, "labevents": LABS,
              "omr": OMR, "prescriptions": PRESCRIPTIONS, "discharge": DISCHARGE, "radiology": RADIOLOGY,
              "radiology_detail": RADIOLOGY_DETAIL}
VALUE_FRAGMENTS = ["Metformin", "Lisinopril", "Timolol", "999-DS", "101-RR", "WHITE", "2150-", "Synthetic note"]

REFERENCE = {"analysis_admissions": 5, "analysis_code_positive": 2, "population_admissions": 3,
             "population_subjects": 3, "population_code_positive": 2, "population_discharge_only_admissions": 2,
             "population_discharge_only_subjects": 2, "population_discharge_only_code_positive": 1}


def frames(spark):
    out = {}
    for t, rows in TABLE_ROWS.items():
        cols = [f.name for f in SCHEMAS[t].fields]
        out[t] = spark.createDataFrame([tuple(r.get(c) for c in cols) for r in rows], SCHEMAS[t])
    return out
