"""Pure-EOS math checks, no fitted P/T/industrial values, and source reproducibility."""
import math
import tempfile
import unittest
from pathlib import Path

import thermo_pr as M
import run_screen as S


class PengRobinsonNoFit(unittest.TestCase):
    def test_components_have_traceable_physical_constants(self):
        self.assertEqual(len(M.CRITICAL),5)
        for name, (Tc,Pc,omega) in M.CRITICAL.items():
            self.assertGreater(Tc,0)
            self.assertGreater(Pc,0)
            self.assertTrue(-.5<omega<.5)

    def test_real_cubic_roots_satisfy_original_polynomial(self):
        for T,P,z,ph in (
            (273.15,18e6,{"NH3":1},"liquid"),
            (273.15,18e6,{"H2":3,"N2":1},"vapor"),
            (294.15,18.02e6,{"NH3":.1967,"H2":.4799,"N2":.196,"CH4":.0943,"Ar":.0331},"vapor")
        ):
            e=M.eos_phase(T,P,z,ph)
            A,B=e["A"],e["B"]
            for zz in e["roots"]:
                residual=zz**3-(1-B)*zz**2+(A-3*B*B-2*B)*zz-(A*B-B*B-B**3)
                self.assertLess(abs(residual),2e-7)

    def test_ideal_gas_limit_Z_and_phi(self):
        e=M.eos_phase(420.0,1e3,{"NH3":.1,"N2":.2,"H2":.65,"Ar":.05},"vapor")
        self.assertLess(abs(e["Z"]-1),.01)
        for value in e["phi"].values():
            self.assertLess(abs(value-1),.01)

    def test_pure_ammonia_high_pressure_has_dense_liquid_root(self):
        l=M.eos_phase(273.15,18e6,{"NH3":1},"liquid")
        v=M.eos_phase(273.15,18e6,{"NH3":1},"vapor")
        self.assertLess(l["Z"],v["Z"]+.01)
        self.assertGreater(l["phi"]["NH3"],0)
        self.assertGreater(v["phi"]["NH3"],0)

    def test_source_vapor_fugacity_equality(self):
        for T,P in ((243.15,10e6),(273.15,17.88e6),(303.15,30e6)):
            e=M.saturated_vapor_over_pure_liquid_nh3(T,P,{"N2":1,"H2":3})
            self.assertTrue(e["converged"])
            self.assertGreater(e["y_NH3"],0)
            self.assertLess(e["y_NH3"],.5)
            self.assertLess(abs(e["vapor_fugacity_PR_Pa"]/e["liquid_fugacity_PR_Pa"]-1),1e-8)

    def test_normalisation_does_not_mutate_observations(self):
        orig={"N2":1.,"H2":3.}
        a=M.normalized(orig,allow_missing=True)
        self.assertEqual(orig,{"N2":1.,"H2":3.})
        self.assertAlmostEqual(sum(a.values()),1)
        with self.assertRaises(M.EosDomainError):
            M.normalized({"N2":-1,"H2":3},allow_missing=True)
        with self.assertRaises(M.EosDomainError):
            M.normalized({"ammonia":1},allow_missing=True)

    def test_compression_ideal_reference_and_source_pressure_units(self):
        v=M.isothermal_compression_work(300,3.23e6,18.2e6,7667,{"N2":.26,"H2":.72,"Ar":.02})
        ideal=7667*1000/3600*M.R*300*math.log(18.2/3.23)/1e6
        self.assertAlmostEqual(v["ideal_gas_isothermal_reversible_MW"],ideal,places=9)
        self.assertGreater(v["PR_isothermal_reversible_MW"],0)
        self.assertTrue(.5<v["PR_over_ideal"]<2.0)
        with self.assertRaises(M.EosDomainError):
            M.isothermal_compression_work(300,18.2e6,3.23e6,7667,{"N2":1})

    def test_flash_does_not_use_measured_phase_outlets(self):
        result=S.first_separator_flash_source_only()
        self.assertEqual(result["fixed_industrial_feed_stream"],4)
        self.assertEqual(result["observed_vapor_stream"],5)
        self.assertFalse(result["uses_observed_phase_values_to_predict"])
        self.assertIn(result["flash_status"],{
            "CONVERGED_TWO_PHASE_CANDIDATE",
            "NO_TWO_PHASE_BRACKET_FROM_WILSON_K",
            "NO_TWO_PHASE_BRACKET_DURING_ITERATION",
            "FLASH_NO_CONVERGENCE"
        })
        if result["full_candidate"].get("screening_accepted"):
            self.assertLess(result["flash_fugacity_residual_max"],1e-7)

    def test_all_28_BASF_values_pinned_and_acceptance_rules_do_not_autotune(self):
        tab,verdict,plants=S.report_saturation()
        self.assertEqual(len(tab),28)
        self.assertEqual(len(plants),2)
        self.assertEqual(len(set(x["reference_row"] for x in tab)),28)
        self.assertEqual(verdict["n_BASF_under_20pct"]+verdict["n_BASF_over_20pct"],28)
        self.assertEqual(verdict["predeclared_science_gate"]["BASF_TABLE_REQUIRE_WITHIN_BAND"],24)
        self.assertEqual(verdict["binary_interaction"].split(" ")[0],"kij=0")
        self.assertEqual(verdict["science_gate_verdict"]=="PASS_EXTERNAL_SCREEN_ONLY",
                         verdict["gate_BASF_pass"] and verdict["gate_plant_pass"])

    def test_source_energy_work_not_claimed_as_actual_machine(self):
        c=S.source_conditioned_compression()
        self.assertEqual(set(c["per_boundary"]),{
            "raw_makeup_10_to_12",
            "recovered_H2_11_to_12",
            "cold_recycle_6_to_1"})
        self.assertGreater(c["separate_makeup_plus_cold_recycle_PR_isothermal_MW"],0)
        self.assertLess(*c["scenario_shaft_power_at_eta_0p65_to_0p85_MW"])
        self.assertIn("NOT_COMPARABLE",c["comparison_to_E01_external_13MW"])
        self.assertIn("BLOCKED",c["engineering_equipment_validation"])

    def test_all_outputs_present_even_on_failed_physics_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            d=S.run(out)
            self.assertIn("phase_validation",d)
            self.assertEqual(d["baseline_catalyst_model_unchanged"].split(";")[0],
                             "NH3-FINAL-1.2 32/64")
            for x in ("REPORT.md","BASF_28_PR_no_fit.csv",
                      "uhde_2_sep_PR_no_fit.csv",
                      "source_first_sep_TP_flash.json",
                      "source_compression_Z_integral.json","summary.json"):
                self.assertTrue((out/x).is_file(),x)


if __name__=="__main__":
    unittest.main()
