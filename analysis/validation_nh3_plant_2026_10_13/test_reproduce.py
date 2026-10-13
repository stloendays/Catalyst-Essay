"""The frozen and measured-kinetics optima reproduce before any benchmark run.

    python -m unittest test_reproduce -v      (about 1-2 min)

  * NH3-FINAL-1.1, descriptor kinetics: Fe 15.291705 USD/t (425 C, 180 bar, 30 C), Ru 22.030595 (450 C, 425 bar, 25 C),
    to 1e-9 (kinetics_swap.frozen_reference asserts the same).
  * Measured kinetics (Dyson-Simon Fe, plug flow, source rates): Fe 15.578802 USD/t at 425 C, 170 bar, 30 C, to 1e-5.
  * The state model evaluated off-grid equals the grid state where both exist (same function, same numbers).

NH3_MODEL=1.2: the same tests against NH3-FINAL-1.2 (frozen Fe 11.515784 at 425 C, 105 bar, 30 C and Ru 16.632749 at
450 C, 220 bar, 30 C from the canonical results.json, to 1e-9; 14,510 states; measured-kinetics Fe 14.925644 USD/t at
450 C, 140 bar, 30 C, to 1e-5).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nh3_model as M  # noqa: E402


class Anchors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = M.build_frozen()
        cls.r = M.reproduce_anchors(cls.h)

    def test_frozen_fe_ru(self):
        if M.VERSION != "1.1":
            self._test_frozen_selected()
            return
        self.assertAlmostEqual(self.r["frozen_Fe"]["cost"], 15.291704676621144, places=9)
        self.assertAlmostEqual(self.r["frozen_Ru"]["cost"], 22.03059478781101, places=9)
        self.assertEqual((self.r["frozen_Fe"]["T_C"], self.r["frozen_Fe"]["P_bar"], self.r["frozen_Fe"]["Tsep_C"]),
                         (425.0, 180.0, 30.0))
        self.assertEqual((self.r["frozen_Ru"]["T_C"], self.r["frozen_Ru"]["P_bar"], self.r["frozen_Ru"]["Tsep_C"]),
                         (450.0, 425.0, 25.0))

    def _test_frozen_selected(self):
        A = M.NM.anchors()
        self.assertEqual(self.h.NSTATE, A["NSTATE"])
        for m in ("Fe", "Ru"):
            self.assertAlmostEqual(self.r[f"frozen_{m}"]["cost"], A[m], places=9)
            f = self.r[f"frozen_{m}"]
            self.assertEqual((f["T_C"], f["P_bar"], f["Tsep_C"]), tuple(A[f"{m}_optimum"]))

    def test_measured_fe(self):
        fe, ref = self.r["measured"]["Fe"], M.MEASURED_FE
        self.assertAlmostEqual(fe["cost"], ref["cost"], places=5)
        self.assertEqual((fe["T_C"], fe["P_bar"], fe["Tsep_C"]), (ref["T_C"], ref["P_bar"], ref["Tsep_C"]))
        self.assertAlmostEqual(fe["V_m3"], ref["V_m3"], places=3)
        if M.VERSION == "1.1":
            self.assertEqual((ref["cost"], ref["T_C"], ref["P_bar"], ref["Tsep_C"], ref["V_m3"]),
                             (15.578802, 425.0, 170.0, 30.0, 25.59425))

    def test_point_equals_grid_state(self):
        h, ref = self.h, M.MEASURED_FE
        opt = (ref["T_C"], ref["P_bar"], ref["Tsep_C"])
        i = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == opt)
        p = M.state_point(h, *opt)
        self.assertAlmostEqual(p["process_cost_USD_t"], float(h.state_process_cost[i]), places=12)
        self.assertAlmostEqual(p["Fe_bed_m3"], self.r["measured"]["Fe"]["V_m3"], places=3)


if __name__ == "__main__":
    unittest.main()
