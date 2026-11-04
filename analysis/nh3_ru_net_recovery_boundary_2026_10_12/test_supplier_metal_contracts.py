"""Contract cash-flow model tests: legal/financial meaning and no double counting."""
import math
import unittest

from lifecycle_cashflow import annualized_metal_multiplier, MetalCashflow
from supplier_metal_contracts import (SupplierMetalTerms, supplier_metal_multiplier,
                                      owned_metal_multiplier)


PRICE = 53852.5


def c(**kwargs):
    return SupplierMetalTerms(project_y=25, catalyst_life_y=10,
                              project_discount_rate=.12, gross_recovery=.9555,
                              **kwargs)


class SupplierContractTests(unittest.TestCase):
    def test_full_return_zero_fee_zero_rental_is_zero(self):
        x = SupplierMetalTerms(25, 10, .12, 1.0)
        self.assertAlmostEqual(supplier_metal_multiplier(x, PRICE), 0, places=13)

    def test_annual_rent_only_exact_annual_annuity(self):
        for fee in (.005, .02, .05, .12):
            x = SupplierMetalTerms(25, 10, .12, 1.0, annual_fee_fraction=fee)
            self.assertAlmostEqual(supplier_metal_multiplier(x, PRICE), 10.0 * fee, places=11)

    def test_supplier_owned_vs_owned_are_separate(self):
        sold = owned_metal_multiplier(project_y=25, catalyst_life_y=10,
                                      discount_rate=.12, metal_price_USD_kg=PRICE,
                                      gross_recovery=.9555)
        supplied = supplier_metal_multiplier(
            SupplierMetalTerms(25, 10, .12, .9555), PRICE)
        self.assertGreater(sold, supplied)
        self.assertGreater(supplied, 0.0)

    def test_loss_makeup_when_no_recovery(self):
        z = SupplierMetalTerms(20, 10, 0, 0)
        # shortage at years 10 and 20. M kg replacement after each cycle.
        self.assertAlmostEqual(supplier_metal_multiplier(z, PRICE), 1.0, places=12)

    def test_terminal_metal_is_owed_if_no_return(self):
        full = supplier_metal_multiplier(SupplierMetalTerms(25, 10, .12, .9555),
                                         PRICE)
        no_end = supplier_metal_multiplier(SupplierMetalTerms(
            25, 10, .12, .9555, terminal_return=False), PRICE)
        self.assertGreater(no_end, full)

    def test_deposit_refund_is_financing_and_not_shortage_double_count(self):
        base = supplier_metal_multiplier(c(), PRICE)
        secured = supplier_metal_multiplier(c(deposit_fraction=.25), PRICE)
        self.assertGreater(secured, base)
        self.assertAlmostEqual(
            supplier_metal_multiplier(SupplierMetalTerms(
                25, 10, 0.0, .9555, deposit_fraction=.25), PRICE),
            supplier_metal_multiplier(SupplierMetalTerms(25, 10, 0.0, .9555), PRICE),
            places=12)
        forfeited = supplier_metal_multiplier(c(deposit_fraction=.25,
                                                 deposit_refund_fraction=.9), PRICE)
        self.assertGreater(forfeited, secured)

    def test_metal_refining_loss_and_processing_charge(self):
        base = supplier_metal_multiplier(c(), PRICE)
        for terms in (c(refining_yield=.95), c(processing_fee_USD_kg_collected=500)):
            self.assertGreater(supplier_metal_multiplier(terms, PRICE), base)

    def test_cycle_fee_only_billed_on_new_loadings(self):
        x = SupplierMetalTerms(25, 10, 0.0, 1.0, cycle_fee_fraction=.03)
        self.assertAlmostEqual(supplier_metal_multiplier(x, PRICE),
                               10 / 25 * 3 * .03, places=12)

    def test_later_shortfall_settlement_reduces_operator_npv(self):
        self.assertLess(supplier_metal_multiplier(c(charge_delay_years=.5), PRICE),
                        supplier_metal_multiplier(c(), PRICE))

    def test_owned_contract_matches_prior_lifecycle(self):
        old = annualized_metal_multiplier(MetalCashflow(25, 10, .12, .9555),
                                           PRICE)
        new = owned_metal_multiplier(project_y=25, catalyst_life_y=10,
                                     discount_rate=.12, metal_price_USD_kg=PRICE,
                                     gross_recovery=.9555)
        self.assertAlmostEqual(old, new, places=13)

    def test_impossible_terms_raise(self):
        for terms in (SupplierMetalTerms(25, 10, .12, 1.1),
                      c(deposit_fraction=-.1), c(refining_yield=math.nan),
                      c(annual_fee_fraction=-.5), c(charge_delay_years=-1)):
            with self.assertRaises(ValueError):
                supplier_metal_multiplier(terms, PRICE)

    def test_noninteger_horizon_prorates_last_rental(self):
        zero_loss = SupplierMetalTerms(25.5, 10, 0, 1.0, annual_fee_fraction=.02)
        mult = supplier_metal_multiplier(zero_loss, PRICE)
        self.assertAlmostEqual(mult, .2, places=12)


if __name__ == "__main__":
    unittest.main()
