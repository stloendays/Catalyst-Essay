"""Fast independent reference tests; full frozen-harness regression is in run_audit."""
import math
import unittest

from thermo_ref import (
    equilibrium_y_nh3, full_kp, gform_nist_ev,
    gform_gb_ev, reference_summary, nist_h_s,
)


class ReferenceTests(unittest.TestCase):
    def test_nist_425c_90bar(self):
        x = reference_summary(698.15, 90.0)
        # Previously checked independently in exploratory PR #68.
        self.assertAlmostEqual(x["NIST"]["ideal_y_NH3"], 0.18572, delta=0.00008)
        self.assertAlmostEqual(
            x["Gillespie-Beattie"]["ideal_y_NH3"], 0.17643, delta=0.00008)
        self.assertAlmostEqual(
            x["NIST"]["ideal_y_NH3"] - x["Gillespie-Beattie"]["ideal_y_NH3"],
            0.00929, delta=0.00015)

    def test_nist_shomate_physics(self):
        for temp in (623.15, 673.15, 698.15, 723.15):
            for species in ("NH3", "N2", "H2"):
                h, s = nist_h_s(species, temp)
                self.assertTrue(math.isfinite(h) and math.isfinite(s))
                self.assertTrue(s > 0)
            for g in (gform_nist_ev(temp), gform_gb_ev(temp)):
                # At 350-450 C the ideal-gas standard Gibbs of NH3 formation is positive;
                # exothermic enthalpy does not imply negative Gibbs at high T.
                self.assertGreater(g, 0)
                k = full_kp(g, temp)
                self.assertGreater(k, 0)
                y = equilibrium_y_nh3(temp, 90, g)
                self.assertGreater(y, 0)
                self.assertLess(y, 1)

    def test_pressure_increases_equilibrium_fraction(self):
        T = 698.15
        g = gform_nist_ev(T)
        self.assertGreater(
            equilibrium_y_nh3(T, 180, g),
            equilibrium_y_nh3(T, 90, g))
        self.assertGreater(
            equilibrium_y_nh3(T, 90, g),
            equilibrium_y_nh3(T, 45, g))

    def test_reference_domain(self):
        with self.assertRaises(ValueError):
            gform_nist_ev(600.0)
        with self.assertRaises(ValueError):
            gform_gb_ev(750.0)
        with self.assertRaises(ValueError):
            equilibrium_y_nh3(698.15, -90.0, gform_nist_ev(698.15))


if __name__ == "__main__":
    unittest.main()
