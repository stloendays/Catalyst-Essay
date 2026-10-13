"""No scientific input files needed: analytic regression tests for the new overlay."""
import math
import unittest

from boundary_math import effective_credit, same_loop_gap, threshold_credit


class BoundaryMathTests(unittest.TestCase):
    def test_credit_separates_collection_from_value(self):
        self.assertAlmostEqual(effective_credit(0.9555, 0.90), 0.85995)
        self.assertEqual(effective_credit(0.0, 1.0), 0.0)
        for rec, value in ((-0.1, 1), (1.01, 1), (0.5, 1.01), (math.nan, 0.5)):
            with self.assertRaises(ValueError):
                effective_credit(rec, value)

    def test_same_loop_must_not_use_global_fe_baseline(self):
        # KAAP-loop Ru/C at 95.55 % recovery (benchmark bed), Fe in the KAAP loop, Fe optimum
        # (figures/composite/fig2[/nh3_1_2]/fig2_ru_actual_cost_points.csv)
        cases = {"NH3-FINAL-1.1": (18.33659372776672, 19.06868861189332, 15.291704676621144),
                 "NH3-FINAL-1.2": (16.2728065463168, 16.97956884800555, 11.515783597179267)}
        for model, (ru_kaap, fe_kaap, fe_global) in cases.items():
            with self.subTest(model=model):
                self.assertLess(same_loop_gap(ru_kaap, fe_kaap), 0)
                self.assertGreater(same_loop_gap(ru_kaap, fe_global), 0)

    def test_threshold(self):
        self.assertAlmostEqual(threshold_credit(lambda q: 10.0 - 4.0*q, 7.0), 0.75, places=10)
        self.assertEqual(threshold_credit(lambda q: 10.0 - 4*q, 11.0), 0.0)
        self.assertIsNone(threshold_credit(lambda q: 10.0 - 4*q, 5.0))

    def test_piecewise_reoptimisation(self):
        # Two process states switch optimality; lower envelope stays monotone.
        c = lambda q: min(10.0 - 4.0*q, 9.0 - 2.0*q)
        self.assertAlmostEqual(threshold_credit(c, 7.0), 0.75, places=10)

    def test_wrong_direction_rejected(self):
        with self.assertRaises(ValueError):
            threshold_credit(lambda q: 10+q, 9)


if __name__ == "__main__":
    unittest.main()
