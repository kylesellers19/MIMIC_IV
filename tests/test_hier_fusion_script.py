"""scripts/run1127_hier_fusion.py end to end on synthetic files, and its refusal to touch real data before amendment (q)."""
import json

import numpy as np
import pandas as pd
import pytest

from scripts import run1127_hier_fusion as HF


def synthetic(tmp_path, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for part, n in (("DEV", 4000), ("TEST", 2000)):
        subj = rng.integers(1, n // 2, size=n) + (0 if part == "DEV" else 10 ** 6)
        stratum = rng.integers(0, 8, size=n)
        latent = rng.normal(size=n)
        w_notes = np.where(stratum >> 1 & 1, 1.6, 0.6)               # notes matter more where the liver was imaged
        eta = -2.6 + 0.8 * latent + w_notes * rng.normal(size=n)
        y = rng.uniform(size=n) < 1 / (1 + np.exp(-eta))
        p_s = 1 / (1 + np.exp(-(-2.6 + 0.8 * latent + rng.normal(0, 0.5, n))))
        p_n = 1 / (1 + np.exp(-(eta - 0.8 * latent + rng.normal(0, 0.5, n))))
        for i in range(n):
            rows.append((f"{part}{i}", int(subj[i]), part, bool(y[i]), bool(rng.uniform() < 0.2), int(stratum[i]),
                         float(p_s[i]), float(p_n[i])))
    df = pd.DataFrame(rows, columns=["key", "subject_id", "partition", "note_b", "code_positive", "stratum", "ps", "pn"])
    df["hadm_id"] = np.arange(len(df)) + 1
    pre = tmp_path / "preds"
    pre.mkdir()
    df[["hadm_id", "subject_id", "partition", "note_b", "code_positive"]].to_parquet(tmp_path / "sub.parquet")
    for part, suffix in (("DEV", "oof"), ("TEST", "test")):
        d = df[df.partition == part]
        d[["hadm_id"]].assign(**{"cat|FS-B|unweighted": d.ps}).to_parquet(pre / f"structured_{suffix}.parquet")
        d[["hadm_id"]].assign(**{"tfidf|S|unweighted": d.pn}).to_parquet(pre / f"notes_tfidf_{suffix}.parquet")
    s = df.stratum.to_numpy()
    feat = pd.DataFrame({"hadm_id": df.hadm_id, "n_notes_dc": s >> 2 & 1, "liver_imaging_any_pre": s >> 1 & 1,
                         "first_val_AST": np.where(s & 1, 30.0, np.nan), "first_val_ALT": 25.0, "first_val_Platelets": 200.0})
    feat.to_parquet(tmp_path / "feat.parquet")
    (tmp_path / "layer0.json").write_text(json.dumps({"layer0": {"structured_FS-B": "cat|FS-B|unweighted",
                                                                 "structured_FS-A": "cat|FS-A|unweighted",
                                                                 "notes": "tfidf|S|unweighted", "notes_source": "tfidf"}}))
    return ["--sub", str(tmp_path / "sub.parquet"), "--preddir", str(pre), "--features", str(tmp_path / "feat.parquet"),
            "--layer0", str(tmp_path / "layer0.json"), "--results", str(tmp_path / "out" / "res.json"),
            "--doc", str(tmp_path / "out" / "doc.md"), "--processed", str(tmp_path / "proc")]


@pytest.fixture
def never_run(monkeypatch):
    """The real-path tests must never reach the fit, whatever the committed plan says."""
    def boom(a):
        raise AssertionError("run() reached with real inputs")
    monkeypatch.setattr(HF, "run", boom)


def test_refuses_real_data_without_the_amendment(monkeypatch, never_run):
    monkeypatch.setattr(HF, "amendment_committed", lambda: False)
    with pytest.raises(SystemExit, match="amendment \\(q\\)"):
        HF.main([])


def test_refuses_quick_on_real_data(monkeypatch, never_run):
    monkeypatch.setattr(HF, "amendment_committed", lambda: True)
    with pytest.raises(SystemExit, match="synthetic tests only"):
        HF.main(["--quick"])


def test_s23_writes_beside_the_primary(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(HF, "real_inputs", lambda a: False)
    monkeypatch.setattr(HF, "run", lambda a: seen.update(results=a.results, doc=a.doc, tag=a.tag) or 0)
    monkeypatch.chdir(tmp_path)
    HF.main(["--structured", "FS-A"])
    assert seen == {"results": "docs/run_2026-11-27/results/hier_fusion_S23.json",
                    "doc": "docs/aim1b_hier_fusion_S23.md", "tag": "_S23"}


def test_synthetic_end_to_end(tmp_path):
    args = synthetic(tmp_path)
    code = HF.main(args + ["--quick", "--draws", "1000"])
    res = json.loads((tmp_path / "out" / "res.json").read_text())
    assert len(res["posterior"]["strata"]) == 8
    assert res["convergence"]["attempts"][0]["target_accept"] == 0.9
    assert code == 0, res["convergence"]["attempts"]        # deterministic: this seed converges within the policy
    if code == 0:
        t = res["test"]
        assert t["hierarchical"]["all"]["n"] == 2000 and 0.5 < t["hierarchical"]["all"]["auroc"] <= 1
        assert set(t["paired_differences_hierarchical_minus_stacked"]) == {"auroc", "auprc", "brier"}
        imaged = [s for s in res["posterior"]["strata"] if "liver imaging yes" in s["stratum"]]
        plain = [s for s in res["posterior"]["strata"] if "liver imaging no" in s["stratum"]]
        assert np.mean([s["w_notes"]["mean"] for s in imaged]) > np.mean([s["w_notes"]["mean"] for s in plain])
        assert (tmp_path / "proc" / "run_2026-11-27_hier_fusion_test.parquet").exists()
    assert "Weights by stratum" in (tmp_path / "out" / "doc.md").read_text()
    with pytest.raises(SystemExit, match="scored once"):
        HF.main(args + ["--quick"])
