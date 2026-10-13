"""Reproduction anchors, checked before any revealed-preference statistic (pytest, or `python test_anchors.py`).

  printed  S5 15/40, S6 28/40 (freeze/field-2026-10-12), S6-TI 18/40 (analysis/meoh_inlet_definition_2026_10_12)
  extended S5 35/83, S6 54/82 (83 -> 40 ledger of the same folder)
  cohort sizes: printed 40 groups / 310 entries / 28 papers; extended 83 / 909 / 44
  S6-TI printed costs equal the committed entry_costs.csv of the inlet-definition folder (1e-6 relative)
  composition subsets equal the pre-registered subsets_*.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rp_common import ANCHORS, HERE, INLET, SCENARIOS, load, scored  # noqa: E402


def test_field_anchors():
    for (cohort, sc), (k, n) in ANCHORS.items():
        _, s, _ = scored(load(cohort), SCENARIOS[sc])
        assert (s["top1_mismatch_groups"], s["groups"]) == (k, n), (cohort, sc, s["top1_mismatch_groups"], s["groups"])


def test_cohort_sizes():
    for cohort, want in {"printed": (40, 310, 28), "extended": (83, 909, 44)}.items():
        _, s, _ = scored(load(cohort), SCENARIOS["S5"])
        assert (s["groups"], s["entries"], s["papers"]) == want, (cohort, s["groups"], s["entries"], s["papers"])


def test_true_inert_matches_committed():
    ref = pd.read_csv(INLET / "entry_costs.csv")
    d = load("printed")
    assert (ref.entry.astype(str).to_numpy() == d.entry.astype(str).to_numpy()).all()
    a, b = d.cost_S6TI.to_numpy(float), ref["cost_true_inert_6.86"].to_numpy(float)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    ok = np.isfinite(a)
    assert np.max(np.abs(a[ok] / b[ok] - 1.0)) < 1e-6


def test_subsets_unchanged():
    for cohort in ("printed", "extended"):
        pre = pd.read_csv(HERE / f"subsets_{cohort}.csv")
        d = load(cohort)
        d = d[d.group.isin(pre.group)]
        assert (d.entry.astype(str).to_numpy() == pre.entry.astype(str).to_numpy()).all()
        for c in ("family", "scale", "scale_alt"):
            assert (d[c].to_numpy() == pre[c].to_numpy()).all(), (cohort, c)


if __name__ == "__main__":
    for f in (test_field_anchors, test_cohort_sizes, test_true_inert_matches_committed, test_subsets_unchanged):
        f()
        print("ok", f.__name__)
