"""The frozen and measured-kinetics optima reproduce before any benchmark run.

    python -m unittest test_reproduce -v      (about 1-2 min)

  * NH3-FINAL-1.1, descriptor kinetics: Fe 15.291705 USD/t (425 C, 180 bar, 30 C), Ru 22.030595 (450 C, 425 bar, 25 C),
    to 1e-9 (kinetics_swap.frozen_reference asserts the same).
  * Measured kinetics (Dyson-Simon Fe, plug flow, source rates): Fe 15.578802 USD/t at 425 C, 170 bar, 30 C, to 1e-5.
  * The state model evaluated off-grid equals the grid state where both exist (same function, same numbers).
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
        self.assertAlmostEqual(self.r["frozen_Fe"]["cost"], 15.291704676621144, places=9)
        self.assertAlmostEqual(self.r["frozen_Ru"]["cost"], 22.03059478781101, places=9)
        self.assertEqual((self.r["frozen_Fe"]["T_C"], self.r["frozen_Fe"]["P_bar"], self.r["frozen_Fe"]["Tsep_C"]),
                         (425.0, 180.0, 30.0))
        self.assertEqual((self.r["frozen_Ru"]["T_C"], self.r["frozen_Ru"]["P_bar"], self.r["frozen_Ru"]["Tsep_C"]),
                         (450.0, 425.0, 25.0))

    def test_measured_fe(self):
        fe = self.r["measured"]["Fe"]
        self.assertAlmostEqual(fe["cost"], 15.578802, places=5)
        self.assertEqual((fe["T_C"], fe["P_bar"], fe["Tsep_C"]), (425.0, 170.0, 30.0))
        self.assertAlmostEqual(fe["V_m3"], 25.59425, places=3)

    def test_point_equals_grid_state(self):
        h = self.h
        i = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == (425.0, 170.0, 30.0))
        p = M.state_point(h, 425.0, 170.0, 30.0)
        self.assertAlmostEqual(p["process_cost_USD_t"], float(h.state_process_cost[i]), places=12)
        self.assertAlmostEqual(p["Fe_bed_m3"], self.r["measured"]["Fe"]["V_m3"], places=3)


if __name__ == "__main__":
    unittest.main()
