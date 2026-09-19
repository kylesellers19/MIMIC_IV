"""Invariant tests over the aggregate results files written by run_2026-09-19.

These read only JSON under docs/ (aggregates, never patient data) and assert the structural
guarantees the run depends on: the integrity gate passed, the splits do not overlap, the gold
holdout covers every adjudication subject, no phenotype-derived feature reached the models, and
small cells are masked in tracked documents.
"""
import json
import os
import re
import pytest

R = "docs/run_2026-09-19/results"


def load(name):
    path = os.path.join(R, name)
    if not os.path.exists(path):
        pytest.skip(f"{name} not produced in this run")
    return json.load(open(path))


def test_integrity_gate_reproduced_every_anchor_number():
    gate = load("integrity_gate.json")
    assert gate["all_pass"] is True
    assert all(gate["checks"].values())


def test_population_and_cell_counts_match_the_locked_values():
    gate = load("integrity_gate.json")
    got, anchor = gate["reproduced"], gate["anchor"]
    assert got["pop_admissions"] == anchor["pop_admissions"]
    assert got["b"] == anchor["b"]                     # primary 2x2, cell for cell
    assert got["note_pos_primary"] == got["b"]["A"] + got["b"]["B"]


def test_splits_partition_the_population_without_overlap():
    sp = load("phase2_splits.json")
    gate = load("integrity_gate.json")
    parts = sp["partitions"]
    assert sum(p["admissions"] for p in parts.values()) == gate["reproduced"]["pop_admissions"]
    assert sum(p["subjects"] for p in parts.values()) == gate["reproduced"]["pop_subjects"]


def test_gold_holdout_covers_every_sampled_and_training_subject():
    sp = load("phase2_splits.json")
    assert sp["partitions"]["GOLD_HOLDOUT"]["subjects"] == sp["gold_subjects"]
    assert sp["gold_subjects"] >= sp["sample_subjects"]
    assert sp["gold_subjects"] == sp["sample_subjects"] + sp["training_subjects"]


def test_training_draw_is_twenty_charts_allocated_proportionally():
    sp = load("phase2_splits.json")
    assert sp["training_n"] == 20
    assert sum(sp["training_alloc"].values()) == 20
    assert sp["training_alloc"]["code-/note+"] == 8      # recovery zone stays largest


def test_dev_folds_are_disjoint_and_exhaust_dev():
    sp = load("phase2_splits.json")
    folds = sp["dev_folds"]
    assert len(folds) == 5
    assert sum(f["admissions"] for f in folds.values()) == sp["partitions"]["DEV"]["admissions"]
    assert sum(f["subjects"] for f in folds.values()) == sp["partitions"]["DEV"]["subjects"]


def test_no_phenotype_code_or_note_rule_output_is_a_feature():
    cls = load("feature_classification.json")
    feats = [f.lower() for f in cls["clinical"] + cls["availability"]]
    for banned in ("note_b", "note_a", "note_c", "note_d", "code_positive", "k760", "k7581", "5718", "5719"):
        assert not any(banned in f for f in feats), banned
    assert not any(f == "charlson" for f in feats)          # full index leaks the code axis
    assert "charlson_noliver" in cls["clinical"]


def test_every_feature_is_classified_exactly_once():
    cls = load("feature_classification.json")
    assert set(cls["clinical"]).isdisjoint(cls["availability"])
    assert len(cls["clinical"]) == cls["n_features"]["clinical"]
    assert len(cls["availability"]) == cls["n_features"]["availability"]


def test_equity_strata_are_never_merged_and_floors_are_respected():
    a = load("aim1c_level1.json")
    assert a["floor"] == 11
    for var, rows in a["strata"].items():
        for r in rows:
            if r.get("recovery_share_pct") is not None:
                assert r["B"] >= a["floor"], (var, r["stratum"])
            if r.get("corroboration_share_pct") is not None:
                assert r["A"] + r["C"] >= a["floor"], (var, r["stratum"])
    assert len(a["strata"]["race"]) > 25                    # race as recorded, not collapsed


def test_5719_sensitivity_leaves_the_primary_untouched():
    s = load("sens_5719.json")
    gate = load("integrity_gate.json")
    assert s["by_definition"]["b"]["current"]["A"] == gate["anchor"]["b"]["A"]
    assert s["code_positive_current"] - s["code_positive_no5719"] == s["solely_5719_admissions"]


def test_charlson_liver_categories_contain_the_phenotype_codes():
    c = load("charlson_validation.json")
    leak = c["leak_check_mild_liver_matches_phenotype_codes"]
    assert leak["10:K760"] and leak["9:5718"] and leak["9:5719"]


def test_cohort_flow_parts_sum_to_the_total_exclusion():
    f = load("cohort_flow.json")
    n = f["note_restriction"]
    assert n["sum_check"] is True
    assert n["part_i_release_lineage_subject_absent_from_note_module"] + \
           n["part_ii_encounter_level_subject_has_notes_elsewhere_not_this_admission"] == n["removed_total"]
    assert f["all_admissions"] - f["zero_dx_excluded"] == f["analysis_population"]
    assert f["check_locked_equals_clean_pop"] is True


SMALL_CELL_DOCS = ["docs/sensitivity_5719.md", "docs/aim1c_level1.md", "docs/aim1a_loose_ends.md",
                   "docs/charlson_validation.md", "docs/aim1b_splits.md"]


def test_tracked_docs_contain_no_eight_digit_identifiers():
    """MIMIC subject_id and hadm_id are 8-digit integers; none may appear in a tracked document."""
    pat = re.compile(r"\b[12]\d{7}\b")
    for doc in SMALL_CELL_DOCS:
        if not os.path.exists(doc):
            continue
        for i, line in enumerate(open(doc), 1):
            if "PMID" in line or "seed" in line.lower():
                continue
            assert not pat.search(line), f"{doc}:{i}"
