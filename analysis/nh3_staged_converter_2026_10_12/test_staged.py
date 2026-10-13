"""Unit checks: equilibrium, loop closure and cost functions against NH3-FINAL-1.1, energy balance, quadrature.

With NH3_MODEL=1.2 the loop-closure and cost checks run against the NH3-FINAL-1.2 harness (its process states, with the
Newton-Cooper loop equilibrium); the Invariance checks (both modes) show that the converter's economic inputs are the
same in the 1.1 and 1.2 manifests, so every converter cost is bit-identical under the two models."""
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import converter as C  # noqa: E402
import kinetics as K  # noqa: E402

if C.NM.VERSION == "1.1":
    from harness_core import KineticContext, parse_activity_workbook  # noqa: E402

WORKBOOK = C.REPO / "provenance" / "nh3_final_1_1" / "source_harness" / "inputs" / "ammonia_activity_volcano_s1_v1.xlsx"


class Thermo(unittest.TestCase):
    def test_gillespie_beattie_matches_pr64_formula(self):
        for T in (673.15, 698.15, 723.15):
            pr64 = 10 ** (-2.691122 * math.log10(T) - 5.519265e-5 * T + 1.848863e-7 * T * T + 2001.6 / T + 2.6899) / 1.01325
            self.assertAlmostEqual(float(K.Ka(T)) / 1.01325, pr64, places=12)
        # ideal-gas equilibrium at 90 bar and 425 C equals the value of PR #64 (verify_2026_10_12_hybrid_bed)
        self.assertAlmostEqual(K.equilibrium_y_nh3(698.15, 90.0, fugacity=False), 0.17642782294535503, places=9)

    def test_heat_of_reaction(self):
        # NIST: -45.9 kJ/mol at 298 K; about -53 to -55 kJ/mol at 700 K
        self.assertAlmostEqual(float(K.heat_of_reaction(298.15)) / 1000, -45.90, places=1)
        self.assertTrue(-56 < float(K.heat_of_reaction(700.0)) / 1000 < -52)

    def test_adiabatic_energy_balance(self):
        n0 = (0.22, 0.66, 0.04, 0.08)
        T1 = C.adiabatic_T(673.15, n0, 0.0, 0.03)
        h0, _ = C._h_cp(C.moles(n0, [0.0]), np.array([673.15]))
        h1, _ = C._h_cp(C.moles(n0, [0.03]), np.array([T1]))
        self.assertLess(abs(h1[0] - h0[0]), 1e-3)
        self.assertGreater(T1, 673.15 + 50)


class Loop(unittest.TestCase):
    def setUp(self):
        if C.NM.VERSION != "1.1":
            # NH3-FINAL-1.2 harness with its thermo switches (loop equilibrium on fugacities); no process library is built
            class _Bare(C.NH3Harness):
                def _build_process_states(self):
                    return []
            self.h = _Bare(C.CFG, C.NM.root())
            return
        self.h = C.NH3Harness.__new__(C.NH3Harness)
        self.h.cfg = C.CFG
        self.h._init_controls()
        src = parse_activity_workbook(WORKBOOK)
        self.h.ctx = KineticContext(src["fits"], src["median_freqs"], src["gasrec"])

    def test_recycle_closure_and_process_costs_match_harness(self):
        for (T, P, Tsep) in ((425.0, 90.0, -20.0), (425.0, 180.0, 30.0), (400.0, 150.0, -20.0)):
            s = self.h.self_consistent_process_state(T, P, Tsep)
            X, ysep = s["X"], s["ysep"]
            ratio = ysep / (1 - ysep)
            nh3_rec = ratio * 2.0 * (1 - X) / X
            total_in = 2.0 / X + nh3_rec
            xi = 0.5 / total_in
            loop = C.Loop(P, Tsep, inerts=0.0)
            yA_h = nh3_rec / total_in
            self.assertAlmostEqual(loop.inlet(xi)[2], yA_h, places=12)
            pc = loop.process_costs(xi)
            for k in ("fresh_comp", "recycle_comp", "refrigeration", "compressor_capex"):
                self.assertAlmostEqual(pc[k], s[k], places=10, msg=k)

    def test_reactor_cost_matches_harness(self):
        for P, V in ((90.0, 12.0), (180.0, 40.0), (200.0, 0.1)):
            self.h.state_P = np.array([P])
            base = (self.h.REACTOR_FIXED + self.h.REACTOR_VAR * (V / self.h.REACTOR_REF) ** self.h.REACTOR_EXP) * self.h.crf / self.h.annual_output_t
            ref = base + float(self.h.vessel_pressure_premium(np.array([V]))[0])
            self.assertAlmostEqual(C.reactor_cost(V, P), ref, places=12)


class Invariance(unittest.TestCase):
    """The converter reads only economic controls and cost functions, which NH3-FINAL-1.2 leaves as in 1.1."""

    @classmethod
    def setUpClass(cls):
        import staged_invariance_1_2 as SI
        cls.h11, cls.h12, cls.ctl = SI.compare_controls()

    def test_only_the_calibration_factor_differs(self):
        self.assertEqual(self.ctl["differing_controls"], ["F_CAL"])
        self.assertTrue(all(self.ctl["same_function_source"].values()), self.ctl["same_function_source"])
        self.assertTrue(all(self.ctl["same_module_constants"].values()))

    def test_converter_costs_bit_identical(self):
        designs = [([480, 396, 400, 0.995, 0.995, 0.95], ("Fe", "Ru", "Ru"), C.Loop(90.0), C.Econ(), "adiabatic"),
                   ([400, 400, 390, 0.95, 0.9, 0.9], ("Fe", "Fe", "Ru"), C.Loop(150.0, -5.0),
                    C.Econ(accounting="dcf", fin_rate=0.12), "adiabatic"),
                   ([420, 410, 400, 0.9, 0.9, 0.9], ("Ru", "Ru", "Ru"), C.Loop(200.0, -5.0, 0.0),
                    C.Econ(c_Ru=500.0, c_Fe=0.96), "isothermal")]
        keep = C.H
        try:
            vals = []
            for h in (self.h11, self.h12):
                C.H = h
                vals.append([C.evaluate(*d) for d in designs])
        finally:
            C.H = keep
        self.assertEqual(vals[0], vals[1])
        self.assertTrue(all(math.isfinite(v) for v in vals[0]))


class Economics(unittest.TestCase):
    def test_multipliers(self):
        e = C.Econ(accounting="dcf", fin_rate=0.0, recovery=0.9555)
        self.assertAlmostEqual(e.multiplier(0.9555), 1.2 * (1 - 0.9555), places=12)
        self.assertAlmostEqual(e.multiplier(0.0), 1.2, places=12)
        f = C.Econ(accounting="frozen", recovery=0.9)
        self.assertAlmostEqual(f.ru_cost_per_kg_ru_year(), 53852.5 * 0.1 / 10, places=9)
        # audit value of the 25-year cash flow at 12 % (analysis/nh3_ru_net_recovery_boundary_2026_10_12)
        g = C.Econ(accounting="dcf", fin_rate=0.12, recovery=0.9555)
        self.assertAlmostEqual(g.multiplier(0.9555), 1.227487230441686, places=9)
        self.assertAlmostEqual(g.multiplier(0.0), 1.8176905717232812, places=9)


class Numerics(unittest.TestCase):
    def test_quadrature_converged(self):
        loop, econ = C.Loop(90.0), C.Econ()
        x = [400, 400, 390, 0.95, 0.9, 0.9]
        v41 = C.evaluate(x, ("Fe", "Fe", "Ru"), loop, econ, ngrid=41)
        v641 = C.evaluate(x, ("Fe", "Fe", "Ru"), loop, econ, ngrid=641)
        self.assertLess(abs(v41 - v641) / v641, 1e-6)

    def test_rates_vanish_at_equilibrium(self):
        T, P = 698.15, 90.0
        y = K.equilibrium_y_nh3(T, P)
        yN = (1 - y) / 4
        for f in (K.rate_fe_dyson_simon, K.rate_ru_rossetti, K.rate_fe_wustite):
            self.assertLess(abs(float(f(T, P, yN, 3 * yN, y))), 1e-9)


if __name__ == "__main__":
    unittest.main()
