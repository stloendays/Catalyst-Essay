"""Falsification tests for the NH3 source-only stoichiometric inlet bound."""
import unittest
import diagnose_source_flow_bound as S

class PlantInletConservation(unittest.TestCase):
    def test_makeup_1000_tpd(self):
        value=S.minimum_stoichiometric_makeup_Nm3_h(1000)
        self.assertTrue(109000 < value < 111000)

    def test_more_makeup_lowers_inlet_bound(self):
        self.assertGreater(S.single_separator_inlet_limit_pct(4,500000,100000),
                           S.single_separator_inlet_limit_pct(4,500000,150000))

    def test_dilution_bound_is_no_higher_than_separator(self):
        self.assertLess(S.single_separator_inlet_limit_pct(4,500000,100000),4)

    def test_invalid_bounds(self):
        with self.assertRaises(ValueError): S.minimum_stoichiometric_makeup_Nm3_h(0)
        with self.assertRaises(ValueError): S.single_separator_inlet_limit_pct(5,100,101)

    def test_source_rows_and_conditional_upper_bounds(self):
        records=S.records()
        self.assertEqual(len(records),3)
        self.assertEqual({x["case_id"] for x in records},set(S.CASES))
        self.assertTrue(all(x["source_inlet_greater_than_optimistic_bound"] for x in records))
        self.assertTrue(all(x["observed_over_optimistic_bound"]>1 for x in records))

if __name__ == "__main__":
    unittest.main()
