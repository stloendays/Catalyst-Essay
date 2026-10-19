"""Post-outcome source operating-GHSV forward-integrator guards."""
from __future__ import annotations
import math
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import g2_forward_diagnostic as F
import g2_adiabatic as G


class OriginalSourceGHSVForwardTests(unittest.TestCase):
    def test_source_GHSV_is_input_and_integration_preserves_heat(self):
        for catalyst in (G.FE,G.RU):
            b=G.Bed("literal_source","nist_ideal")
            z=F.measured_GHSV_forward(b,catalyst)
            self.assertGreater(z["model_forward_fraction_of_own_adiabatic_eq_extent"],0)
            self.assertLess(z["model_forward_fraction_of_own_adiabatic_eq_extent"],.995)
            self.assertLess(abs(z["model_energy_residual_J_per_inlet_mol"]),1e-4)
            self.assertTrue(z["target_GHSV_only_used_as_forward_operating_configuration"])

    def test_forward_fraction_matches_reverse_design_target_when_using_predictions(self):
        b=G.Bed("ideal","nist_ideal")
        for material in (G.FE,G.RU):
            predicted=b.reactor(material,profile_points=3)
            value=G.SOURCE_REPORT_GHSV[material.catalyst]
            try:
                G.SOURCE_REPORT_GHSV[material.catalyst]=predicted["predicted_GHSV_h"]
                forward=F.measured_GHSV_forward(b,material)
            finally:
                G.SOURCE_REPORT_GHSV[material.catalyst]=value
            self.assertAlmostEqual(
                forward["model_forward_fraction_of_own_adiabatic_eq_extent"],
                G.TARGET_EQUIL_FRACTION,delta=1e-5
            )

    def test_original_GHSV_not_used_as_kinetic_fit(self):
        b=G.Bed("ideal","nist_ideal")
        for m in (G.FE,G.RU):
            f=F.measured_GHSV_forward(b,m)
            self.assertTrue(f["fixed_original_kinetics_factors"])
            self.assertTrue(f["cannot_be_called_independent_bed_size_prediction"])
            self.assertEqual(f["authors_reported_adiabatic_equilibrium_fraction"],.9)
            self.assertEqual(f["authors_printed_GHSV_per_h"],
                             G.SOURCE_REPORT_GHSV[m.catalyst])


if __name__=="__main__":
    unittest.main()
