"""Nonfitting source transfer of published HYSYS interactions to cold NH3 VLE."""
import tempfile
import unittest
from pathlib import Path

import thermo_pr as B
import thermo_published_bip as P
import run_published_interactions as R


class LiteratureBipTransfer(unittest.TestCase):
    def test_source_parameters_exact_and_no_extra_fit(self):
        self.assertEqual(P.interaction("N2","NH3"),.222)
        self.assertEqual(P.interaction("NH3","N2"),.222)
        self.assertEqual(P.interaction("H2","N2"),-.036)
        self.assertEqual(P.interaction("H2","NH3"),0.0)
        self.assertEqual(P.interaction("CH4","NH3"),0.0)
        self.assertEqual(len(P.PUBLISHED_BIP),2)
        self.assertIn("eng2.12506",P.PROVENANCE_URL)

    def test_no_kij_source_values_reduce_to_baseline_pure_fluid(self):
        for phase in ("liquid","vapor"):
            a=P.external_pr_phase(273.15,18e6,{"NH3":1.0},phase)
            b=B.eos_phase(273.15,18e6,{"NH3":1.0},phase)
            self.assertAlmostEqual(a["Z"],b["Z"],places=11)
            self.assertAlmostEqual(a["phi"]["NH3"],b["phi"]["NH3"],places=11)

    def test_h2_n2_ammonia_gas_differs_without_recalibration(self):
        z={"N2":.24,"H2":.72,"NH3":.04}
        a=P.external_pr_phase(273.15,18e6,z,"vapor")
        b=B.eos_phase(273.15,18e6,z,"vapor")
        self.assertGreater(abs(a["phi"]["NH3"]-b["phi"]["NH3"]),1e-4)

    def test_independent_external_28_and_2_records(self):
        result=R.evaluate()
        self.assertEqual(len(result["BASF_rows"]),28)
        self.assertEqual(len(result["plant_rows"]),2)
        self.assertTrue(result["no_industrial_recalibration"])
        self.assertTrue(all(v["source_row_id"] for v in result["BASF_rows"]))
        self.assertTrue(all(abs(v["fugacity_ln_residual"])<1e-8 for v in result["plant_rows"]))
        self.assertEqual(result["predeclared_science_gate"]["BASF_TABLE_REQUIRE_WITHIN_BAND"],24)

    def test_no_physics_failures_are_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary=R.run(Path(tmp))
            self.assertTrue((Path(tmp)/"BASF_28_published_kij.csv").exists())
            self.assertTrue((Path(tmp)/"Uhde_2_published_kij.csv").exists())
            self.assertEqual(summary["scientific_status"].startswith("PASS"),
                             summary["comparison"]["gate_pass"])
            self.assertEqual(summary["baseline_NH3_FINAL_1_2"],"32/64 unchanged")


if __name__=="__main__":
    unittest.main()
