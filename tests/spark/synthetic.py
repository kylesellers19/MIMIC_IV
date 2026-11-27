"""Synthetic MIMIC-shaped files for the Spark tests.

Every value is invented. Identifiers are small integers (subject 101.., admission 2001..), so none can equal a real
8-digit MIMIC identifier, which the push gate checks for. Files are written to pytest temp directories at test time
and never committed (the repository ignores *.csv / *.csv.gz and the push gate rejects tabular files).
"""
import csv
import gzip
import hashlib
import io

from masld_spark import config as C
from masld_spark.schemas import TABLES, column_names

# Note texts that stress the CSV reader: embedded newlines, doubled quotes, commas, a line shaped like a CSV record,
# CRLF, backslashes before a quote and at the end, non-ASCII characters, edge whitespace.
NOTE_TEXTS = {
    "101-DS-1": "Synthetic discharge summary.\nDischarge Diagnosis:\nsynthetic finding\n\nBrief Hospital Course:\nInvented line two.\n",
    "102-DS-1": 'Synthetic note with "double quotes", commas, and a line shaped like a record:\n999,"x",2150-01-01 00:00:00\nend.',
    "103-DS-1": "CRLF inside\r\nthe text\r\nand a backslash before a quote \\\" here, and a trailing backslash \\",
    "104-DS-1": "Non-ASCII: 37.5 °C, 5 µg, naïve café — dash.\n\n\nTrailing blank lines\n\n",
    "105-DS-1": "  leading and trailing spaces  ",
    "106-DS-1": "IMPRESSION:\n1. Synthetic item.\n2. Another, with a comma.",
}
VALUE_FRAGMENTS = ["Synthetic", "double quotes", "°C", "naïve", "IMPRESSION", "Invented", "-DS-", "2150-"]


def discharge_rows(duplicate=True):
    rows = []
    for i, (nid, text) in enumerate(NOTE_TEXTS.items()):
        rows.append({"note_id": nid, "subject_id": 101 + i, "hadm_id": 2001 + i, "note_type": "DS", "note_seq": 1,
                     "charttime": "2150-03-08 02:30:00", "storetime": None if i == 0 else "2150-03-09 10:15:00",
                     "text": text})
    if duplicate:
        rows.append(dict(rows[0]))          # the same note twice: ingest must keep both
    return rows


def radiology_rows():
    return [{"note_id": f"{101 + i}-RR-{k}", "subject_id": 101 + i, "hadm_id": (2001 + i) if k == 1 else None,
             "note_type": "RR", "note_seq": k, "charttime": f"2150-0{k}-1{i} 08:00:00", "storetime": None,
             "text": f"Synthetic radiology report {i}-{k}.\nFINDINGS:\nInvented.\n\nIMPRESSION:\nInvented."}
            for i in range(4) for k in (1, 2)]


def admissions_rows():
    return [{"subject_id": 101 + i, "hadm_id": 2001 + i, "admittime": "2150-03-08 02:30:00",
             "dischtime": "2150-03-10 11:00:00", "deathtime": None, "admission_type": "EW EMER.",
             "admit_provider_id": "P0", "admission_location": "EMERGENCY ROOM", "discharge_location": "HOME",
             "insurance": "Other", "language": "English", "marital_status": None, "race": "UNKNOWN",
             "edregtime": None, "edouttime": None, "hospital_expire_flag": 0} for i in range(5)]


def labevents_rows(n_subjects=40, per_subject=5):
    rows, k = [], 0
    for s in range(n_subjects):
        for j in range(per_subject):
            k += 1
            rows.append({"labevent_id": k, "subject_id": 101 + (s * 7) % n_subjects, "hadm_id": None if j == 0 else 2001 + s,
                         "specimen_id": 5000 + k, "itemid": 50861, "order_provider_id": None,
                         "charttime": f"2150-01-{1 + j:02d} 0{j}:00:00", "storetime": None,
                         "value": "12", "valuenum": None if j == 4 else 12.0, "valueuom": "IU/L",
                         "ref_range_lower": 0.0, "ref_range_upper": 40.0, "flag": None, "priority": "ROUTINE",
                         "comments": "Synthetic comment\nwith a newline." if k == 3 else None})
    rows.reverse()                          # unsorted input
    return rows


def prescriptions_rows():
    return [{"subject_id": 101, "hadm_id": 2001, "pharmacy_id": 1, "poe_id": "101-1", "poe_seq": 1,
             "order_provider_id": None, "starttime": "2150-01-02 08:00:00", "stoptime": "2150-01-03 08:00:00.250",
             "drug_type": "MAIN", "drug": "Synthetic drug", "formulary_drug_cd": None, "gsn": None, "ndc": "0001",
             "prod_strength": None, "form_rx": None, "dose_val_rx": "1-2", "dose_unit_rx": "TAB",
             "form_val_disp": None, "form_unit_disp": None, "doses_per_24_hrs": 2.0, "route": "PO"}]


def write_csv_gz(path, table, rows, quoting=csv.QUOTE_MINIMAL, header=True):
    """quoting: csv.QUOTE_MINIMAL, or csv.QUOTE_NOTNULL (every non-null field quoted). None -> unquoted empty field."""
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO(newline="")
    w = csv.writer(buf, quoting=quoting, doublequote=True, lineterminator="\n")
    cols = column_names(table)
    if header:
        w.writerow(cols)
    for r in rows:
        w.writerow([r.get(c) for c in cols])
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())
    return path


def write_raw_gz(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(raw_root, files, override=None):
    """PhysioNet-style 'hash  relative/path' lines. override: {basename: hash} to plant a wrong digest."""
    override = override or {}
    lines = [f"{override.get(f.name, sha256(f))}  {f.relative_to(raw_root).as_posix()}" for f in files]
    (raw_root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def make_cfg(tmp_path, partitions=None, expected=None, tolerance_pct=0.0, require_manifest=True):
    cfg = {
        "run_name_prefix": "test",
        "paths": {"raw_root": str(tmp_path / "raw"), "out_root": str(tmp_path / "out"),
                  "runs_root": str(tmp_path / "runs"), "local_dir": str(tmp_path / "local")},
        "spark": {"master": "local[2]", "app_name": "masld-spark-tests", "conf": {}},
        "ingest": {"tolerance_pct": tolerance_pct, "require_manifest_match": require_manifest,
                   "partitions": {t: 1 for t in TABLES}, "expected_rows": {t: None for t in TABLES}},
    }
    cfg["ingest"]["partitions"].update(partitions or {})
    cfg["ingest"]["expected_rows"].update(expected or {})
    return C.check(cfg)
