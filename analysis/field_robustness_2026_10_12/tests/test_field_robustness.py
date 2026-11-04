"""Regression and contract tests for independent field robustness analysis."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from analysis.field_robustness_2026_10_12 import (
    audit_inversion_robustness as audit,
    joint_inventory_purge as joint,
)


class FieldRobustnessTests(unittest.TestCase):
    def test_frozen_intersection_is_source_aligned(self):
        with tempfile.TemporaryDirectory() as temp:
            report = audit.audit(audit.ROOT, Path(temp))
            self.assertEqual(report["methanol"]["scenarios"]["S5"]["mismatch"], 15)
            self.assertEqual(report["methanol"]["inlet_intersection"]["regret_gt5"], 16)
            self.assertEqual(report["methanol"]["inlet_intersection"]["regret_gt5_without_bansode"], 12)
            self.assertEqual(report["methanol"]["inlet_intersection"]["same_temperature_other_catalyst"], 7)
            self.assertEqual(report["methanol"]["inlet_intersection"]["fully_printed_leader_pairs_at_anchor"], 2)
            self.assertEqual(report["ammonia"]["different_metal"], 3)

    def test_loading_surrogate_anchor_and_thermodynamic_boundary(self):
        values = joint.states(0.2, 0.6)
        self.assertTrue(any(abs(m - 1) < 1e-12 and abs(x - 0.2) < 1e-12 for m, x, _ in values))
        self.assertTrue(all(x < 0.6 for m, x, _ in values))
        self.assertTrue(all(x > 0.0 for m, x, _ in values))
        self.assertEqual(joint.states(0.65, 0.6), [(1.0, 0.65, "above_feed_eq_only_measured")])

    def test_group_and_entry_denominators_do_not_drift(self):
        candidates = joint.candidates()
        self.assertEqual(len(candidates), 310)
        self.assertEqual(candidates.group.nunique(), 40)
        self.assertEqual(candidates.doi.nunique(), 28)
        self.assertEqual(int(candidates.row_id.nunique()), 310)

    def test_inlet_limit_is_applied_per_purge_and_loading(self):
        row = SimpleNamespace(row_id=0, group="g", doi="doi", catalyst="cat",
                              X=0.2, STY=1.0, SMeOH=0.8, SCO=0.2, SCH4=0.0,
                              P_bar=70.0, T_C=220.0, h2_co2=3.0, y_co2=0.25)
        n = len(joint.GRID)
        # The cheaper purge is invalid for every published inlet limit.
        cost = np.full(n, 100.0)
        cost[0] = 1.0
        cost[-1] = 5.0
        nonreactive = np.full(n, 0.90)
        nonreactive[-1] = 0.03
        dummy = {"cost_eur_t": cost, "nonreactive_fraction": nonreactive,
                 "catalyst_t": np.full(n, 10.0),
                 "recycle_kmol_h": np.full(n, 100.0),
                 "carbon_efficiency": np.full(n, 0.8),
                 "fresh_h2_co2": np.full(n, 2.0),
                 "co2_hyd_approach": np.full(n, 0.5)}
        with patch.object(joint, "feed_eq", return_value=(0.6, 1)), (
             patch.object(joint, "evaluate_array", return_value=dummy)):
            result = joint.evaluate(row)
        self.assertEqual(result["open_cost"], 1.0)
        self.assertEqual(result["inlet_4p92_cost"], 5.0)
        self.assertEqual(result["inlet_10p25_cost"], 5.0)
        self.assertLessEqual(result["inlet_4p92_nonreactive"], 0.0492)
        self.assertGreaterEqual(result["states_tested"], 2)


if __name__ == "__main__":
    unittest.main()
