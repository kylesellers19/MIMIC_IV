"""The public repository publishes no count from 1 to 10 (CELL_FLOOR = 11), and none can be recovered from a
published total by subtraction. Runs over every tracked document and results file, so a regenerated report
that brings a small count back fails here as well as at the push gate."""
import json
import subprocess

from scripts import run1110_push_gate as G
from scripts.public_counts import FLOOR, suppress_table

RES = "docs/run_2026-09-19/results"
# numbers in count-like columns or keys that are not counts of people, admissions, notes, values or mentions
NOT_COUNTS = {
    ("docs/predefinition_descriptives.md", "admissions"): "bin labels: admissions contributed per subject",
    (f"{RES}/aim1a_precision_forecast.json", "D_positives_per_100"): "design: positives per 100 sampled charts",
    (f"{RES}/aim1b_structured.json", "n_configs_per_learner"): "tuning configurations",
    (f"{RES}/reviewer_assignment.json", "n_reviewers"): "reviewers",
}


def tracked(*patterns):
    return subprocess.run(["git", "ls-files", *patterns], capture_output=True, text=True).stdout.split()


def small(v):
    return isinstance(v, int) and not isinstance(v, bool) and 0 < v < FLOOR


def test_no_small_count_in_any_count_column_of_a_tracked_file():
    bad = []
    for p in tracked("*.md", "*.json"):
        text = open(p, encoding="utf-8").read()
        for b in G.check_small_counts(p, text, set(range(1, text.count("\n") + 2))):
            if (p, b.get("column") or b.get("key")) not in NOT_COUNTS:
                bad.append((p, b["line"]))
    assert bad == []


def test_cell_tables_in_results_files_hold_no_small_count():
    a = json.load(open(f"{RES}/aim1c_level1.json"))
    cells = [r[c] for rows in a["strata"].values() for r in rows for c in "ABCD"] + \
            [r["mech"]["n"] for rows in a["strata"].values() for r in rows]
    s = json.load(open(f"{RES}/sens_5719.json"))
    for d in s["by_definition"].values():
        cells += list(d["solely_5719_cells"].values()) + list(d["no5719"].values()) + list(d["current"].values())
    c = json.load(open(f"{RES}/context_agreement.json"))
    cells += list(c["confusion_project_rows_medspacy_columns"].values())
    assert not [v for v in cells if small(v)]


def test_a_share_is_published_only_when_its_cells_are():
    a = json.load(open(f"{RES}/aim1c_level1.json"))
    for rows in a["strata"].values():
        for r in rows:
            if r.get("recovery_share_pct") is not None:
                assert isinstance(r["A"], int) and isinstance(r["B"], int), r["stratum"]
            if r.get("corroboration_share_pct") is not None:
                assert isinstance(r["A"], int) and isinstance(r["C"], int), r["stratum"]


def test_suppression_leaves_no_row_or_column_with_one_hidden_cell():
    rows = [{"s": "a", "A": 4, "B": 300, "C": 12, "D": 900},
            {"s": "b", "A": 50, "B": 7, "C": 3, "D": 400},
            {"s": "c", "A": 80, "B": 260, "C": 40, "D": 1200},
            {"s": "d", "A": 0, "B": 2, "C": 0, "D": 15}]
    m = suppress_table(rows, "ABCD", key="s")
    for r in rows:
        assert all(m[r["s"]].get(c) == "small" for c in "ABCD" if small(r[c]))
        hid = m[r["s"]]
        assert not hid or (len(hid) >= 2 and sum(r[c] for c in hid) >= FLOOR), r["s"]
    for c in "ABCD":
        hid = [r for r in rows if c in m[r["s"]]]
        assert not hid or (len(hid) >= 2 and sum(r[c] for r in hid) >= FLOOR), c


def test_raw_results_stay_out_of_the_repository():
    assert not [p for p in tracked() if p.startswith("data/")]
