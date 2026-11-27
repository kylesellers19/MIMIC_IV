"""Definitions Step 2 takes from the version-of-record scripts. Nothing here is re-typed.

Each value is read at run time from the script that defines it:
  * imported where the module has no side effects (scripts/masld_config.py);
  * read with ast.literal_eval from the top-level assignment where importing would run the script
    (clean_population.py, note_phenotype.py, run1110_fib4_by_cell.py, cmrf.py);
  * SQL text cut from scripts/cmrf.py and run in Spark with one translation (DuckDB regexp_matches -> Spark
    regexp_like, both a partial match), exactly as run0919_features.py reuses the same text;
  * the drug lists and match() of scripts/cmrf.py executed from its source, the way run0919_features.py does it.
The one exception, GGT's itemid, is an item assignment in make_tables.py; tests/spark/test_cohort_definitions.py
checks that copy against the source line.
"""
import ast
import os
import re
import zipfile
from pathlib import Path

from scripts.masld_config import LAB_ITEMIDS, MASLD_PREDICATE  # noqa: F401 — re-exported

ROOT = Path(__file__).resolve().parents[1]


def repo_text(relpath):
    """A repository file's text: from the checkout, or, on a cluster executor that imported this package from the
    zip that scripts/spark_job.py ships, from the same path inside that zip."""
    p = ROOT / relpath
    if p.exists():
        return p.read_text()
    here = str(Path(__file__))
    i = here.find(".zip" + os.sep)
    if i < 0:
        raise FileNotFoundError(relpath)
    with zipfile.ZipFile(here[:i + 4]) as z:
        return z.read(relpath).decode("utf-8")


def literal_from(relpath, name):
    """The literal value assigned to `name` at the top level of a repository file (also `A, B = 1, 2` forms)."""
    tree = ast.parse(repo_text(relpath))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id == name:
                return ast.literal_eval(node.value)
            if isinstance(tgt, ast.Tuple) and isinstance(node.value, ast.Tuple):
                for t, v in zip(tgt.elts, node.value.elts):
                    if isinstance(t, ast.Name) and t.id == name:
                        return ast.literal_eval(v)
    raise KeyError(f"{name} is not assigned at the top level of {relpath}")


# ---- cleaning (scripts/clean_population.py) ---------------------------------------------------------------------
LAB_BOUNDS = literal_from("scripts/clean_population.py", "LAB_BOUNDS")      # impossible if < lo or > hi
OMR_BOUNDS = literal_from("scripts/clean_population.py", "OMR_BOUNDS")
CAT_MISSING = literal_from("scripts/clean_population.py", "CAT_MISSING")
CLEAN_N_EXPECT = literal_from("scripts/clean_population.py", "N_EXPECT")

# ---- first-value labs of the cleaned frame (scripts/make_tables.py build_frame) ---------------------------------
GGT_ITEMID = 50927                                   # make_tables.py: ANALYTE_IDS["GGT"] = 50927
ANALYTE_IDS = {**LAB_ITEMIDS, "GGT": GGT_ITEMID}

# ---- lab features and FIB-4 ----------------------------------------------------------------------------------
PRE365_ANALYTES = ("HbA1c", "Triglycerides", "HDL")  # scripts/run0919_lab_features.py, `pre` query
OUTPT_FIB4_ANALYTES = ("AST", "ALT", "Platelets")    # scripts/run1110_outpt_fib4_inputs.py
FIB4_LOW = literal_from("scripts/run1110_fib4_by_cell.py", "LOW")
FIB4_HIGH = literal_from("scripts/run1110_fib4_by_cell.py", "HIGH")
FIB4_LOW_65 = literal_from("scripts/run1110_fib4_by_cell.py", "LOW_65")

# ---- outpatient radiology windows (scripts/note_phenotype.py; days before, days after admittime) ---------------
OUTPATIENT_WINDOWS = literal_from("scripts/note_phenotype.py", "OUTPATIENT_WINDOWS")

# ---- CMRF and etiology (scripts/cmrf.py) ------------------------------------------------------------------------
RTFILTER = literal_from("scripts/cmrf.py", "RTFILTER")   # non-ophthalmic route; valid Spark SQL as written
CMRF_CODE_FLAGS = ("ow_code", "dg_code", "htn_code", "tg_code", "hdl_code",
                   "alcohol", "viral", "other_etio", "cirrhosis", "hcc")
MED_FLAGS = ("insulin", "metformin", "oral_ad", "bb", "htn_qual", "htn_excl", "lipid")


def cmrf_code_flags_select():
    """The select list of cmrf.py's code-flag query (`max(...) ow_code, ...`), translated to Spark SQL."""
    src = repo_text("scripts/cmrf.py")
    m = re.search(r"SELECT hadm_id,\n(.*?)\n\s*FROM d GROUP BY hadm_id", src, re.S)
    if not m:
        raise ValueError("code-flag query not found in scripts/cmrf.py")
    body = m.group(1)
    names = re.findall(r"::INT\)\s*(\w+)\s*(?:,|$)", body)
    if tuple(names) != CMRF_CODE_FLAGS:
        raise ValueError(f"cmrf.py code flags changed: {names}")
    return body.replace("regexp_matches(", "regexp_like(")


def cmrf_match():
    """cmrf.py's drug lists and match(d), executed from its source (the slice run0919_features.py executes)."""
    src = repo_text("scripts/cmrf.py")
    i0 = src.index("INSULIN = ")
    i1 = src.index("def match")
    i2 = src.index("\n\n", i1)
    ns = {"re": re}
    exec(src[i0:i2], ns)  # noqa: S102 — repository source, unchanged
    return ns["match"]
