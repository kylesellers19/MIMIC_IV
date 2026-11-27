"""Step 2 definitions are read from the version-of-record scripts; these tests fail if that link breaks."""
from scripts import masld_config

from masld_spark import definitions as D


def test_lab_and_code_constants_are_the_config_ones():
    assert D.LAB_ITEMIDS is masld_config.LAB_ITEMIDS and D.MASLD_PREDICATE is masld_config.MASLD_PREDICATE
    assert set(D.ANALYTE_IDS) == set(masld_config.LAB_ITEMIDS) | {"GGT"}


def test_ggt_itemid_matches_make_tables():
    src = (D.ROOT / "scripts/make_tables.py").read_text()
    assert f'ANALYTE_IDS["GGT"] = {D.GGT_ITEMID}' in src


def test_bounds_and_windows_are_read_from_source():
    assert set(D.LAB_BOUNDS) == set(D.ANALYTE_IDS)          # every first-value lab has cleaning bounds
    assert set(D.OMR_BOUNDS) == {"BMI", "SBP", "DBP"}
    assert set(D.OUTPATIENT_WINDOWS) == {"primary", "sensitivity"}
    assert D.FIB4_LOW < D.FIB4_LOW_65 < D.FIB4_HIGH
    assert isinstance(D.CLEAN_N_EXPECT, int)


def test_code_flag_sql_is_cmrf_text_with_one_translation():
    src = (D.ROOT / "scripts/cmrf.py").read_text()
    sel = D.cmrf_code_flags_select()
    assert sel.replace("regexp_like(", "regexp_matches(") in src
    assert "regexp_matches" not in sel


def test_drug_matcher_is_cmrf_match():
    m = D.cmrf_match()
    assert m("metformin 500 mg")["oral_ad"] and m("metformin")["metformin"]
    assert m("insulin glargine")["insulin"] and not m("aspartame")["insulin"]
    assert m("niacin er")["lipid"] and not m("niacinamide")["lipid"]
    assert not any(m("metamucil")[k] for k in D.MED_FLAGS)
    assert set(m("x")) == set(D.MED_FLAGS)


def test_route_filter_is_the_cmrf_one():
    assert "EYE" in D.RTFILTER and D.RTFILTER in (D.ROOT / "scripts/cmrf.py").read_text()
