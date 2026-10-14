"""Algebraic invariants of the source NH3-free makeup / recycle loop closure."""
import unittest
from invert_separator_requirement import reactor_inlet_fraction


class ReactorInletClosure(unittest.TestCase):
    def test_equivalence_to_source_mole_balance(self):
        for ysep in (0.01, 0.04, 0.15):
            for x in (0.1, 0.3, 0.6):
                ratio = ysep / (1.0-ysep)
                nh3_recycled = ratio * 2 * (1-x) / x
                total_in = 2 / x + nh3_recycled
                self.assertAlmostEqual(reactor_inlet_fraction(ysep, x),
                                       nh3_recycled / total_in, places=14)

    def test_nh3_free_makeup_dilutes_separator_vapor(self):
        for x in (0.1, 0.3, 0.7):
            for ysep in (0.01, 0.05, 0.25):
                self.assertLess(reactor_inlet_fraction(ysep, x), ysep)

    def test_higher_separator_vapor_for_fixed_conversion_increases_inlet(self):
        for x in (0.1, 0.3, 0.7):
            points=[reactor_inlet_fraction(ysep,x) for ysep in (0.005,0.02,0.05,0.2)]
            self.assertTrue(all(a < b for a,b in zip(points[:-1],points[1:])))

    def test_invalid_domain_rejected(self):
        for args in ((-0.1,0.2),(1.0,0.2),(0.05,0.0),(0.05,1.0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                reactor_inlet_fraction(*args)


if __name__ == "__main__":
    unittest.main()
