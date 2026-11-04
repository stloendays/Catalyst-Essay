"""No mixing of KAAP serial bed physics into frozen pure-metal model."""
import math
import unittest

from kaap_feasibility_math import (minimum_feasible_activity_multiplier,
                                   classify_feasibility, find_fe_activity_cost_parity)


class FeasibilityMathTests(unittest.TestCase):
    def test_alpha_feasibility_threshold(self):
        self.assertAlmostEqual(minimum_feasible_activity_multiplier(45,90), .5)
        self.assertAlmostEqual(minimum_feasible_activity_multiplier(180,90), 2.0)

    def test_volume_gate_is_not_engineering_certification(self):
        self.assertEqual(classify_feasibility(89.99,90), "within_frozen_volume_cap")
        self.assertEqual(classify_feasibility(90,90), "within_frozen_volume_cap")
        self.assertEqual(classify_feasibility(91,90), "no_volume_feasible_state")

    def test_exact_fe_cost_parity_linear(self):
        f = lambda alpha: 12.0 - 2.0*alpha
        r = find_fe_activity_cost_parity(f,9.0,lowest_feasible_alpha=.3,low=.25,high=3)
        self.assertEqual(r["status"],"cost_parity")
        self.assertAlmostEqual(r["alpha"],1.5,places=10)

    def test_fe_wins_immediately_when_feasible(self):
        r=find_fe_activity_cost_parity(lambda x: 10.0-x,12.0,lowest_feasible_alpha=1.5,low=.2,high=4)
        self.assertEqual(r["status"],"Fe_wins_at_first_feasible_alpha")
        self.assertIsNone(r["alpha"])

    def test_ru_dominates_a_finite_qualified_range(self):
        r=find_fe_activity_cost_parity(lambda x: 20.0-x, 5.0, .5, low=.2, high=3)
        self.assertEqual(r["status"],"Ru_wins_through_upper_activity_bound")

    def test_no_fe_volume_feasibility(self):
        r=find_fe_activity_cost_parity(lambda x: 10-x,8,5,low=.2,high=4)
        self.assertEqual(r["status"],"Fe_volume_infeasible_over_range")

    def test_jumpy_lower_envelope_reported_not_fictitious_root(self):
        f=lambda a: 10.0 if a<1.0 else 8.0
        r=find_fe_activity_cost_parity(f,9.0,.2,low=.2,high=2)
        self.assertEqual(r["status"],"discrete_state_switch_or_numerical_jump")

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            minimum_feasible_activity_multiplier(0,90)
        with self.assertRaises(ValueError):
            minimum_feasible_activity_multiplier(20,0)
        with self.assertRaises(ValueError):
            find_fe_activity_cost_parity(lambda x: 3,2,.1,low=4,high=2)
        with self.assertRaises(ValueError):
            find_fe_activity_cost_parity(lambda x: x,2,.1,low=.2,high=3)


if __name__=="__main__":
    unittest.main()
