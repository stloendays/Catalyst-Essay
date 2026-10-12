"""Contract tests for Re/TiO2 formulation-STY denominator and metal price."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import run_re_normalization_price as R  # noqa: E402


class ReNormalizationAndPriceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = R.load_group()
        cls.pair = cls.full.loc[cls.full.entry.isin(R.MATCHED_ENTRIES)]

    def test_source_unit_conversion_and_source_group(self):
        self.assertEqual((len(self.full), self.full.group.nunique()), (9, 1))
        self.assertEqual(self.full.doi.nunique(), 1)
        x = R.source_basis()
        self.assertEqual(x["matched_200C"]["one_wt_per_re"], 55.0)
        self.assertEqual(x["matched_200C"]["five_wt_per_re"], 18.0)
        self.assertEqual(x["matched_200C"]["one_wt_per_total"], 0.55)
        self.assertEqual(x["matched_200C"]["five_wt_per_total"], 0.90)
        self.assertIn("Table 4 row 4",
                      x["full_group"]["per_Re_STY_leader"])

    def test_normalization_changes_matched_pair_interpretation(self):
        # Independent economics from prior joint optimization; same pair,
        # 200 C, 100 bar, 500 C pre-reduction and CO2/H2 1:4.
        re1 = self.pair.loc[self.pair.entry == "Table 4 row 3"].iloc[0]
        re5 = self.pair.loc[self.pair.entry == "Table 4 row 11"].iloc[0]
        costs = pd.Series({int(re1.row_id): 892.739761204,
                           int(re5.row_id): 964.951231337})
        per_catalyst = R.F.classify_group(self.pair, costs)
        per_Re = R.F.classify_group(
            self.pair.assign(STY=self.pair.STY_per_g_Re), costs)
        self.assertTrue(per_catalyst["mismatch"])
        self.assertTrue(per_catalyst["sameT_other_catalyst_gt5"])
        self.assertEqual(per_catalyst["kind"], "other catalyst, same temperature")
        self.assertAlmostEqual(per_catalyst["regret"],
                               964.951231337 / 892.739761204 - 1.0, places=7)
        self.assertFalse(per_Re["mismatch"])
        self.assertEqual(per_Re["kind"], "agree")

    def test_replacement_cost_exact_optional_TEA_additivity(self):
        x = R.validate_additivity(self.full)
        self.assertGreater(x["penalty_model_EUR_t"], 0.)

    def test_replacement_cost_price_life_recovery_and_inventory(self):
        base = float(R.replacement_cost_eur_t(
            1500., .05, 2000., 5., 1.))
        self.assertGreater(base, 0)
        self.assertAlmostEqual(float(R.replacement_cost_eur_t(
            1500., .05, 0., 5., 1.)), 0)
        self.assertAlmostEqual(float(R.replacement_cost_eur_t(
            1500., .05, 2000., 5., 0.)), 0)
        self.assertAlmostEqual(float(R.replacement_cost_eur_t(
            3000., .05, 2000., 5., 1.)), base * 2)
        self.assertAlmostEqual(float(R.replacement_cost_eur_t(
            1500., .05, 4000., 5., 1.)), base * 2)
        self.assertAlmostEqual(float(R.replacement_cost_eur_t(
            1500., .05, 2000., 10., 1.)), base / 2)
        self.assertAlmostEqual(float(R.replacement_cost_eur_t(
            1500., .01, 2000., 5., 1.)), base / 5)

    def test_replacement_cost_rejects_invalid_arguments(self):
        for bad in (-.01, 1.01):
            with self.assertRaises(ValueError):
                R.replacement_cost_eur_t(100., .05, 1000., 5., bad)
        with self.assertRaises(ValueError):
            R.replacement_cost_eur_t(100., .05, 1000., 0., 1.)
        with self.assertRaises(ValueError):
            R.replacement_cost_eur_t(100., .05, -1., 5., 1.)

    def test_comparison_is_one_paper_not_three_independent_experiments(self):
        self.assertEqual(len(R.COMPARISONS), 4)
        self.assertEqual(set(R.MAX_M), {10., 25.})
        self.assertEqual(len(R.PRICE_PER_KG_RE_EUR), 5)
        self.assertEqual(len(R.CAP_NAMES), 5)
        self.assertTrue(all(self.full.doi == R.DOI))


if __name__ == "__main__":
    unittest.main()
