"""Regression fixtures for the decision meaning of source-anchored STY leaders."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_fixed_sty_leader as audit  # noqa: E402


def group():
    # The ORIGINAL raw STY winner has row_id=0. Rows 1 and 2 are distinct catalysts.
    return pd.DataFrame([
        dict(row_id=0, group="doi | condition", doi="doi",
             catalyst="High STY", catalyst_key="catA", T_C=250., STY=10.),
        dict(row_id=1, group="doi | condition", doi="doi",
             catalyst="Intermediate STY", catalyst_key="catB", T_C=250., STY=8.),
        dict(row_id=2, group="doi | condition", doi="doi",
             catalyst="Low STY", catalyst_key="catC", T_C=250., STY=5.),
    ])


class FixedLaboratoryLeaderTests(unittest.TestCase):
    def test_original_champion_excluded_does_not_count_reversal(self):
        v = audit.classify_group(group(), pd.Series({0: np.nan, 1:100., 2:90.}))
        self.assertEqual(v["status"], "original_sty_leader_infeasible")
        self.assertFalse(v["mismatch"])
        self.assertFalse(v["material_gt5"])
        self.assertTrue(np.isnan(v["regret"]))

    def test_all_source_leaders_stay_and_real_material_regret(self):
        v = audit.classify_group(group(), pd.Series({0:150.,1:110.,2:100.}))
        self.assertEqual(v["status"], "original_sty_leader_feasible")
        self.assertTrue(v["mismatch"])
        self.assertAlmostEqual(v["regret"], .5)
        self.assertEqual(v["kind"], "other catalyst, same temperature")
        self.assertTrue(v["sameT_other_catalyst_gt5"])

    def test_one_survivor_not_rankable(self):
        v = audit.classify_group(group(), pd.Series({0:100.,1:np.nan,2:np.nan}))
        self.assertEqual(v["status"], "one_feasible_candidate")
        self.assertFalse(v["mismatch"])

    def test_none_survive(self):
        v = audit.classify_group(group(), pd.Series({0:np.nan,1:np.nan,2:np.nan}))
        self.assertEqual(v["status"], "no_feasible_candidates")

    def test_tied_raw_winner_cheapest_feasible_is_used(self):
        f = group()
        f.loc[1, "STY"] = 10.
        v = audit.classify_group(f, pd.Series({0:np.nan,1:100.,2:120.}))
        self.assertEqual(v["status"], "original_sty_leader_feasible")
        self.assertEqual(v["original_STY_top_entries"], 2)
        self.assertEqual(v["original_STY_top_entries_feasible"], 1)
        self.assertTrue(v["max_sty_ties_partially_excluded"])
        self.assertFalse(v["mismatch"])

    def test_same_catalyst_different_T_is_not_cross_catalyst(self):
        f = group()
        f.loc[2, "catalyst_key"] = "catA"
        f.loc[2, "T_C"] = 220.
        v = audit.classify_group(f, pd.Series({0:150.,1:140.,2:100.}))
        self.assertEqual(v["kind"], "other temperature")
        self.assertFalse(v["sameT_other_catalyst_gt5"])

    def test_cluster_resampling_uses_eligible_only(self):
        rec = pd.DataFrame([
            dict(doi="a", status="original_sty_leader_feasible", mismatch=True),
            dict(doi="a", status="original_sty_leader_feasible", mismatch=False),
            dict(doi="b", status="original_sty_leader_feasible", mismatch=True),
            dict(doi="c", status="original_sty_leader_infeasible", mismatch=False),
        ])
        b = audit.bootstrap_paper_cluster(rec, n=50)
        self.assertEqual((b["papers"], b["groups"]), (2,3))
        self.assertAlmostEqual(b["fraction"], 2/3)


if __name__ == "__main__":
    unittest.main()
