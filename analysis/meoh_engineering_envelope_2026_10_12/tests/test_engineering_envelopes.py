"""Tests for reference-normalized equipment screens; no numerical claims baked in."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_engineering_envelopes as E  # noqa: E402


class EngineeringEnvelopeTests(unittest.TestCase):
    def test_reference_and_scenarios_are_distinct(self):
        self.assertAlmostEqual(E.ANCHORS["catalyst_inventory_t"], 6 * 478.13, places=5)
        self.assertAlmostEqual(E.ANCHORS["assumed_loop_pressure_drop_bar"], 1.5)
        self.assertGreater(E.ANCHORS["recycle_compressor_MW"], 0)
        self.assertEqual(len(E.LOADING_MAX) * len(E.INLETS) * len(E.CAPS), 56)
        self.assertIn("uncapped", E.CAPS)
        self.assertIn(25., E.LOADING_MAX)

    def test_mask_requires_independent_feasibility_conditions(self):
        # Cheaper index 0 is thermodynamically feasible but exceeds all
        # equipment ratios. Reoptimizing selects index 1 rather than merely
        # discarding this candidate.
        e = {
            "cost_eur_t": np.array([80., 100., 130.]),
            "co2_hyd_approach": np.array([0.8, 0.8, 1.1]),
            "catalyst_t": E.ANCHORS["catalyst_inventory_t"] * np.array([3., 0.9, 0.8]),
            "reactor_inlet_kmol_h": E.ANCHORS["reactor_inlet_kmol_h"] * np.array([3., 0.9, 0.8]),
            "P_rec_MW": E.ANCHORS["recycle_compressor_MW"] * np.array([3., 0.9, 0.8]),
            "nonreactive_fraction": np.array([0.02, 0.04, 0.02]),
        }
        open_mask = E.feasible_mask(e, None, E.CAPS["uncapped"])
        self.assertTrue(open_mask[0])
        self.assertTrue(open_mask[1])
        self.assertFalse(open_mask[2])
        mask = E.feasible_mask(e, 0.0492, E.CAPS["anchor_1x"])
        self.assertEqual(list(mask), [False, True, False])
        self.assertEqual(int(np.argmin(np.where(mask, e["cost_eur_t"], np.inf))), 1)

    def test_inlet_limit_filters_inert_carbon(self):
        e = {
            "cost_eur_t": np.array([80., 110.]),
            "co2_hyd_approach": np.array([0.9, 0.9]),
            "catalyst_t": E.ANCHORS["catalyst_inventory_t"] * np.array([1., 1.]),
            "reactor_inlet_kmol_h": E.ANCHORS["reactor_inlet_kmol_h"] * np.array([1., 1.]),
            "P_rec_MW": E.ANCHORS["recycle_compressor_MW"] * np.array([1., 1.]),
            "nonreactive_fraction": np.array([0.07, 0.045]),
        }
        self.assertEqual(list(E.feasible_mask(e, .0492, E.CAPS["uncapped"])), [False, True])
        self.assertEqual(list(E.feasible_mask(e, .10249, E.CAPS["uncapped"])), [True, True])

    def test_missing_equipment_metrics_must_not_pass_screen(self):
        e = {
            "cost_eur_t": np.array([100.]),
            "co2_hyd_approach": np.array([0.5]),
            "catalyst_t": np.array([np.nan]),
            "reactor_inlet_kmol_h": np.array([2.]),
            "P_rec_MW": np.array([0.2]),
            "nonreactive_fraction": np.array([0.02]),
        }
        self.assertFalse(E.feasible_mask(e, None, E.CAPS["uncapped"])[0])

    def test_surrogate_m25_is_not_claimed_as_kinetic_validation(self):
        self.assertIn(25, E.LOADING_GRID)
        self.assertEqual(E.M.LOOP_DP_BAR, 1.5)


if __name__ == "__main__":
    unittest.main()
