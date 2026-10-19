"""Independently falsifiable thermodynamic, SRK and adiabatic-PFR unit tests."""
from __future__ import annotations
import json
import math
import pathlib
import sys
import unittest
import numpy as np

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import g2_srk as S
import g2_adiabatic as P
import kinetics as K


class G2ThermodynamicSource(unittest.TestCase):
    def test_original_Fe_SI_mathias_parameter_pinned(self):
        self.assertEqual(S.SOURCE_SI_SHA256,
            "b43f9988b4b5f69d824409e706c1c1b8862afb523a2b18cb053f7c286465773a")
        self.assertAlmostEqual(S.POLAR[2],-.23677368013887007,delta=1e-13)
        self.assertEqual(tuple(S.SPECIES),("N2","H2","NH3"))
        self.assertAlmostEqual(S.KIJ[0,2],.225700005888939,places=13)
        self.assertTrue(np.allclose(S.KIJ,S.KIJ.T,rtol=1e-12))

    def test_mathias_srk_limits_and_logphi(self):
        for rule in ("literal_source","conventional"):
            yi={"N2":.25,"H2":.65,"NH3":.10}
            dilute=S.evaluate(yi,673.15,.0001,rule=rule)
            self.assertAlmostEqual(dilute.compressibility,1.,delta=1e-6)
            for phi in dilute.phi:self.assertAlmostEqual(phi,1.,delta=1e-5)
            hi=S.evaluate(yi,673.15,100.,rule=rule)
            self.assertTrue(hi.compressibility>0)
            self.assertGreater(min(hi.phi),0)
            self.assertGreater(min(hi.fugacity_bar),0)

    def test_cubic_root_is_a_real_gas_root(self):
        yi=S.normalize({"N2":.27384615384615385,"H2":.6161538461538462,"NH3":.11})
        for rule in ("literal_source","conventional"):
            T=673.15
            _,b,a,bmix,_=S.mixed(yi,T,rule)
            A=a*1e7/(S.R*S.R*T*T)
            B=bmix*1e7/(S.R*T)
            Z=S.gas_root(A,B)
            resid=Z**3-Z**2+Z*(A-B-B*B)-A*B
            self.assertLess(abs(resid),1e-9)
            self.assertGreater(Z,B)

    def test_source_extra_alpha_is_detectable_and_not_silently_removed(self):
        yi=S.normalize([.25,.65,.10])
        _,_,am_l,_,_=S.mixed(yi,673.15,"literal_source")
        _,_,am_c,_,_=S.mixed(yi,673.15,"conventional")
        self.assertGreater(abs(am_l/am_c-1),.005)
        # For this source comparison keep BOTH readings explicit.
        with self.assertRaises(ValueError):
            S.evaluate(yi,673.15,100,rule="retrofitted_to_bed_target")

    def test_analytical_am_derivative_against_finite_difference(self):
        yi=S.normalize([.25,.65,.10])
        for rule in ("literal_source","conventional"):
            h=.002
            up=S.mixed(yi,673.15+h,rule)[2]
            dn=S.mixed(yi,673.15-h,rule)[2]
            num=(up-dn)/(2*h)
            ana=S.mixed(yi,673.15,rule)[4]
            self.assertAlmostEqual(num/ana,1.,delta=5e-5)

    def test_srk_residual_enthalpy_dilute_limit(self):
        yi={"N2":.25,"H2":.65,"NH3":.1}
        for rule in ("literal_source","conventional"):
            lo=S.evaluate(yi,673.15,.00001,rule=rule)
            hi=S.evaluate(yi,673.15,100.,rule=rule)
            self.assertLess(abs(lo.gas_enthalpy_departure_J_per_mol),.01)
            self.assertTrue(math.isfinite(hi.gas_enthalpy_departure_J_per_mol))

    def test_reject_nonphysical_gas_and_temperature(self):
        with self.assertRaises(ValueError):
            S.evaluate({"N2":.2,"H2":.6,"NH3":.1},673.15,100.)
        with self.assertRaises(ValueError):
            S.evaluate({"N2":.2,"H2":.8,"NH3":.0},300.,100.)
        with self.assertRaises(ValueError):
            S.evaluate({"N2":.2,"H2":.8,"NH3":.0},673.15,-100.)


class G2BedSource(unittest.TestCase):
    def test_NIST_nist_shomate_plausibility(self):
        for s,reference in (("N2",30.0),("H2",29.45),("NH3",51.0)):
            cp,h=P.shomate_cp_h(s,700.)
            self.assertAlmostEqual(cp,reference,delta=15.)
            self.assertTrue(math.isfinite(h))
        self.assertAlmostEqual(P.shomate_cp_h("NH3",298.15)[1],
              -45898.06,delta=2.)

    def test_stoichiometric_balance_and_NTP_units(self):
        out,ntot,y=P.flows(.01)
        self.assertAlmostEqual(out["NH3"]-P.INLET["NH3"],.02)
        self.assertAlmostEqual(out["H2"]-P.INLET["H2"],-.03)
        self.assertAlmostEqual(out["N2"]-P.INLET["N2"],-.01)
        self.assertAlmostEqual(ntot,1-.02)
        self.assertAlmostEqual(sum(y.values()),1.)
        self.assertAlmostEqual(P.VM_NTP,.0244654,delta=.00001)

    def test_adiabatic_heat_balance_multiple_extents(self):
        for gas,energy in (("ideal","nist_ideal"),
                           ("literal_source","nist_ideal"),
                           ("literal_source","nist_plus_srk_residual"),
                           ("conventional","nist_plus_srk_residual")):
            b=P.Bed(gas,energy)
            for x in (0.,.003,.012):
                st=b.state(x)
                self.assertGreaterEqual(st["T_C"],400.)
                self.assertLess(abs(st["energy_residual_J_per_inlet_mol"]),1e-4)
                self.assertLess(st["T_C"],950.)

    def test_equilibrium_is_source_Keq_and_adiabatic_path(self):
        for gas,energy in (("ideal","nist_ideal"),
                           ("literal_source","nist_plus_srk_residual")):
            b=P.Bed(gas,energy)
            x=b.eq_extent()
            self.assertTrue(0<x<P.X_LIM)
            self.assertAlmostEqual(b.state(x)["equilibrium_ratio"],1.,delta=1e-8)
            target=.9*x
            self.assertLess(b.state(target)["equilibrium_ratio"],1.)
            self.assertGreater(b.state(target)["T_K"],P.T0)

    def test_bed_integration_dimension_and_no_calibration_to_GHSV(self):
        bed=P.Bed("ideal","nist_ideal")
        original=P.SOURCE_REPORT_GHSV.copy()
        result=bed.reactor(P.FE,profile_points=3)
        self.assertGreater(result["catalyst_W_over_F0_kg_s_mol"],0)
        self.assertTrue(100<result["predicted_GHSV_h"]<1e8)
        try:
            P.SOURCE_REPORT_GHSV["Fe"]=19.
            other=P.Bed("ideal","nist_ideal").reactor(P.FE,profile_points=3)
            self.assertAlmostEqual(other["predicted_GHSV_h"],result["predicted_GHSV_h"],delta=1e-7)
        finally:
            P.SOURCE_REPORT_GHSV.update(original)

    def test_exact_commercial_factors_and_industry_claim_blocked(self):
        self.assertEqual(P.RU.bcat,76.25)
        self.assertEqual(P.RU.bN,.8514)
        self.assertEqual(P.FE.bcat,1.)
        self.assertEqual(P.TARGET_EQUIL_FRACTION,.9)
        self.assertEqual(P.SOURCE_REPORT_GHSV,{"Fe":22250.,"Ru_Ba_K_C":130000.})

    def test_model_output_contains_source_specific_T_domain_warning(self):
        bed=P.Bed("ideal","nist_ideal")
        z=bed.reactor(P.RU,profile_points=3)
        self.assertIn("non_mixture_kinetic_T_global_caution",z)
        self.assertEqual(z["source_fit_Ru_global_max_C"],465.)
        self.assertTrue(0<z["target_state"]["y_NH3"]<1)


if __name__=="__main__":
    unittest.main()
