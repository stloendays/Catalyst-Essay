"""Tests for the finite-project metal lifecycle overlay (no frozen data mutation)."""
import math
import unittest

from lifecycle_cashflow import (MetalCashflow, annualized_metal_multiplier,
                                capital_recovery_factor, discount_factor, lifecycle_dates)


class LifecycleCashflowTests(unittest.TestCase):
    def test_cashflow_events_at_noninteger_horizon(self):
        self.assertEqual(lifecycle_dates(10, 25), ([0, 10, 20], [10, 20, 25]))
        self.assertEqual(lifecycle_dates(10, 25, terminal_recovery=False), ([0, 10, 20], [10, 20]))
        self.assertEqual(lifecycle_dates(5, 25), ([0, 5, 10, 15, 20], [5, 10, 15, 20, 25]))
        self.assertEqual(lifecycle_dates(10, 20), ([0, 10], [10, 20]))

    def test_no_discount_20year_matches_original_replacement_accounting(self):
        for r in (0.0, 0.9, 0.9555, 1.0):
            case = MetalCashflow(project_y=20, catalyst_life_y=10, discount_rate=0, gross_recovery=r)
            self.assertAlmostEqual(annualized_metal_multiplier(case, 53852.5), 1 - r, places=13)

    def test_25year_project_explicit_last_bed(self):
        no_salvage = MetalCashflow(project_y=25, catalyst_life_y=10, discount_rate=0, gross_recovery=0)
        self.assertAlmostEqual(annualized_metal_multiplier(no_salvage, 8), 1.2, places=13)
        full_sale = MetalCashflow(project_y=25, catalyst_life_y=10, discount_rate=0, gross_recovery=1)
        self.assertAlmostEqual(annualized_metal_multiplier(full_sale, 53852.5), 0.0, places=12)
        no_terminal = MetalCashflow(project_y=25, catalyst_life_y=10, discount_rate=0,
                                    gross_recovery=1, terminal_recovery=False)
        self.assertAlmostEqual(annualized_metal_multiplier(no_terminal, 53852.5), 0.4, places=12)

    def test_financing_rate_and_delay_raise_ru_cost(self):
        base = MetalCashflow(25, 10, 0.0, .9555)
        financed = MetalCashflow(25, 10, .12, .9555)
        delayed = MetalCashflow(25, 10, .12, .9555, sale_delay_y=1)
        self.assertGreater(annualized_metal_multiplier(financed, 53852.5),
                           annualized_metal_multiplier(base, 53852.5))
        self.assertGreater(annualized_metal_multiplier(delayed, 53852.5),
                           annualized_metal_multiplier(financed, 53852.5))

    def test_refining_fee_and_metal_yield_separate(self):
        base = MetalCashflow(25, 10, .12, .9555)
        fee = MetalCashflow(25, 10, .12, .9555, processing_fee_USD_kg_collected=500)
        lower_yield = MetalCashflow(25, 10, .12, .9555, refining_yield=.9)
        lower_payout = MetalCashflow(25, 10, .12, .9555, sale_price_fraction=.9)
        for changed in (fee, lower_yield, lower_payout):
            self.assertGreater(annualized_metal_multiplier(changed, 53852.5),
                               annualized_metal_multiplier(base, 53852.5))

    def test_invalid_inputs(self):
        for bad in (MetalCashflow(25, 10, .12, 1.01),
                    MetalCashflow(25, 10, .12, .9, refining_yield=-.01),
                    MetalCashflow(25, 10, .12, .9, sale_price_fraction=math.nan),
                    MetalCashflow(25, 10, .12, .9, processing_fee_USD_kg_collected=-1)):
            with self.assertRaises(ValueError):
                annualized_metal_multiplier(bad, 53852.5)
        with self.assertRaises(ValueError):
            capital_recovery_factor(-.1, 25)
        with self.assertRaises(ValueError):
            lifecycle_dates(0, 25)

    def test_crf_and_discount_factor(self):
        self.assertAlmostEqual(capital_recovery_factor(0, 25), .04)
        self.assertAlmostEqual(discount_factor(.12, 25), (1.12)**-25)
        self.assertGreater(capital_recovery_factor(.12, 25), .12)


if __name__ == "__main__":
    unittest.main()
