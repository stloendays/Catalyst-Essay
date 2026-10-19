"""Independent unit/sign/identity gates for source-anchored preliminary kinetics."""
from __future__ import annotations
import math,sys,unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import kinetics as k
import run_audit as a


class SourceUnitsAndPhysics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fe=k.KineticModel.from_locked("Fe")
        cls.ru=k.KineticModel.from_locked("Ru_CeO2")

    def test_identity_correctness(self):
        self.assertEqual(self.fe.bcat,1.0)
        self.assertEqual(self.fe.bN,1.0)
        self.assertEqual(self.ru.bcat,1.0)
        self.assertEqual(self.ru.bN,1.0)
        self.assertTrue("Ru/CeO2" in k.CONFIG["sourceRu"]["bcatReference"])

    def test_published_global_coefficients(self):
        self.assertEqual(self.fe.kA,2.215e13)
        self.assertEqual(self.fe.kB,100700)
        self.assertEqual(self.fe.NB,-17950)
        self.assertEqual(self.ru.kA,2.211e8)
        self.assertEqual(self.ru.kB,112800)
        self.assertEqual(self.ru.NB,-49520)

    def test_equilibrium_temperature_and_positive_constant(self):
        self.assertAlmostEqual(k.eq_constant(673.15),1.3628e-6*math.exp(51111/(8.3145*673.15)),places=12)
        self.assertGreater(k.eq_constant(623.15),k.eq_constant(723.15))
        self.assertGreater(k.eq_constant(673.15),.01)
        self.assertLess(k.eq_constant(673.15),.015)

    def test_source_detailed_balance_at_kf(self):
        # Independently impose fNH3=Kf sqrt(fN2 fH2^3).
        for catalyst in (self.fe,self.ru):
            for Tc in (350.,400.,450.):
                T=Tc+273.15
                fn,fh=15.,45.
                fa=k.eq_constant(T)*math.sqrt(fn*fh**3)
                r=k.published_rate_mol_kg_s(catalyst,T,{"N2":fn,"H2":fh,"NH3":fa})
                self.assertLess(abs(r),1e-10)

    def test_beyond_equilibrium_reverse_rate_is_negative(self):
        T=400+273.15
        fn,fh=15.,45.
        eqfa=k.eq_constant(T)*math.sqrt(fn*fh**3)
        for catalyst in (self.fe,self.ru):
            rate=k.published_rate_mol_kg_s(catalyst,T,{"N2":fn,"H2":fh,"NH3":1.1*eqfa})
            self.assertLess(rate,0)

    def test_pressure_and_gauge_are_explicit(self):
        self.assertAlmostEqual(a.P80,81.01325,places=7)
        f=k.ideal_fugacity_bar(a.P80,k.inlet_composition())
        self.assertAlmostEqual(f["N2"],a.P80/4)
        self.assertAlmostEqual(f["H2"],a.P80*3/4)

    def test_no_unproven_promoted_ru_identity(self):
        with self.assertRaises(ValueError):
            k.KineticModel.from_locked("Ru_Ba_K_C")
        self.assertIsNone(k.CONFIG["referenceTarget100Bar"]["Ru_Ba_K_C_bcat"])
        self.assertIsNone(k.CONFIG["referenceTarget100Bar"]["Ru_Ba_K_C_bN"])

    def test_invalid_pressures_compositions_and_fugacities(self):
        with self.assertRaises(ValueError):
            k.ideal_fugacity_bar(-5,{"N2":.25,"H2":.75,"NH3":0})
        with self.assertRaises(ValueError):
            k.ideal_fugacity_bar(80,{"N2":.25,"H2":.75,"NH3":.01})
        with self.assertRaises(ValueError):
            k.published_rate_mol_kg_s(self.ru,673.15,{"N2":10,"H2":-20,"NH3":1})
        with self.assertRaises(ValueError):
            k.eq_constant(-1000)

    def test_golden_initial_rates_400C_are_from_published_coefficients(self):
        rf=k.rate_from_ideal_gas(self.fe,400,a.P80)
        rr=k.rate_from_ideal_gas(self.ru,400,a.P80)
        # Golden values independently calculated from Table 2 / Table 3 at fNH3=0
        # using the explicit denominator 1 + sqrtKH(T)*sqrt(fH2).
        self.assertAlmostEqual(rf,0.1801675057464236,delta=1e-12)
        self.assertAlmostEqual(rr,0.0013072446370389376,delta=1e-12)
        self.assertGreater(rf,rr)

    def test_matching_experimental_qualitative_direction_at_three_temperatures(self):
        results=a.audit()
        self.assertEqual(len(results["kinetic_rows"]),3)
        self.assertEqual(results["G1"]["status"],"PASS_QUALITATIVE_IN_FAMILY_DIRECTION")
        self.assertTrue(results["G1"]["dataset_in_training"])
        for row in results["kinetic_rows"]:
            self.assertGreater(row["Fe_initial_r_mol_kg_s"],row["Ru_CeO2_initial_r_mol_kg_s"])
            self.assertGreater(row["Fe_ideal_isothermal_outlet_yNH3"],row["Ru_CeO2_ideal_isothermal_outlet_yNH3"])

    def test_isothermal_integrator_numerical_convergence(self):
        lo=k.isothermal_ideal_pfr(self.fe,400,a.P80,nsteps=1600)
        hi=k.isothermal_ideal_pfr(self.fe,400,a.P80,nsteps=3200)
        self.assertAlmostEqual(lo["outlet_yNH3"],hi["outlet_yNH3"],delta=5e-5)
        self.assertTrue(0 < hi["outlet_yNH3"]<1)

    def test_published_table4_dimensional_ratios_are_not_model_predictions(self):
        result=a.audit()
        a4=result["G2"]["source_output_arithmetic_check"]
        self.assertEqual(a4["status"],"PASS_PUBLISHED_OUTPUT_ARITHMETIC_ONLY")
        self.assertTrue(a4["never_independent_kinetic_prediction"])
        self.assertTrue(a4["not_used_as_input_to_any_kinetic_rate_fit"])
        self.assertAlmostEqual(a4["Fe_Ru_bed_volume_ratio_from_published_GHSV"],
                               130000.0/22250.0, places=10)
        self.assertAlmostEqual(a4["Fe_Ru_bed_mass_ratio_from_published_GHSV_and_densities"],
                               (130000.0/22250.0)*(2500.0/750.0),places=10)
        self.assertAlmostEqual(a4["Fe_Ru_bed_volume_ratio_from_published_GHSV"],5.8,delta=.1)
        self.assertAlmostEqual(a4["Fe_Ru_bed_mass_ratio_from_published_GHSV_and_densities"],19.,delta=.6)
        self.assertEqual(result["G2"]["status"],"BLOCKED")

    def test_1996_training_overlap_is_explicit(self):
        src=k.CONFIG["sourceTrainingOverlap"]
        self.assertTrue(src["Kowalczyk1996"]["in_Keestra_Ru_training"])
        self.assertTrue(src["Cholewa2024"]["in_Keestra_Ru_training"])
        self.assertEqual(a.audit()["G4"]["all_external_sources_numerically_predicted"],False)

    def test_100bar_industrial_gate_really_blocked(self):
        x=a.audit()
        self.assertEqual(x["G2"]["status"],"BLOCKED")
        self.assertEqual(x["G3"]["status"],"BLOCKED_G2_REQUIRED")
        self.assertNotIn("cost",x)
        self.assertFalse(x["G2"]["no_fitted_source_catalyst_factors"] is False)
        self.assertTrue(x["original_manuscript_unchanged"])

if __name__=="__main__":
    unittest.main()
