"""Tests: global Fe main-loop and paired Fe-KAAP denominators differ."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ru_cost_reference_audit import audit


def fixtures():
    points = [
        dict(key="pure", cost="22", gap_to_Fe="7"),
        dict(key="fe_kaap", cost="19", gap_to_Fe="4"),
        dict(key="kaap90", cost="18", gap_to_Fe="3"),
        dict(key="kaap97", cost="17.5", gap_to_Fe="2.5"),
    ]
    beds, readings = [], []
    for loop in ("main", "KAAP"):
        fe_ref = 15 if loop == "main" else 19
        for w in (0.05, 0.08, 0.10):
            for rho in (430, 550):
                for rec in (0.90, 0.97):
                    key = ("kaap" if loop == "KAAP" else "supp_rec") + str(round(rec * 100))
                    cost = fe_ref + (0.3 if rec == 0.9 else -0.3) + (0.08 - w)
                    state = dict(
                        cost=str(cost), Fe_reference_cost=str(fe_ref),
                        P_bar="90", T_C="425", Tsep_C="-20", V_m3="10",
                    )
                    beds.append(dict(
                        key=key, w_Ru=str(w), rho_bed_kg_m3=str(rho),
                        gap_to_Fe_reference=str(cost-fe_ref),
                        alpha_star_supported_bed="1.25", **state,
                    ))
                    readings.append(dict(
                        set="R_all", reading="own_bed", loop=loop,
                        w_Ru=str(w), rho_bed_kg_m3=str(rho),
                        recovery=str(rec), gap_to_Fe=str(cost-fe_ref),
                        alpha_star="1.25", **state,
                    ))
    return points, beds, readings


class RuReferenceTests(unittest.TestCase):
    def test_pairwise_vs_global_gaps_and_grid_parity(self):
        points, beds, readings = fixtures()
        report, corrected = audit(points, beds, readings)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["R_all_own_bed_states_compared"], 24)
        self.assertEqual(report["Ru_8wt_percent_ranges"]["main"]["n_corners"], 4)
        self.assertEqual(report["Ru_8wt_percent_ranges"]["KAAP"]["n_corners"], 4)
        k = [x for x in corrected if x["key"] == "kaap90"][0]
        self.assertAlmostEqual(k["existing_gap_to_Fe_global_USD_t"], 3)
        self.assertAlmostEqual(k["derived_gap_to_Fe_same_loop_USD_t"], -1)
        self.assertTrue(k["global_reference_differs_from_same_loop"])

    def test_bad_bed_reference_detected(self):
        points, beds, readings = fixtures()
        beds[0]["Fe_reference_cost"] = "15.12345"
        report, _ = audit(points, beds, readings)
        self.assertTrue(any("Bed source Fe comparator wrong loop" in x for x in report["errors"]))

    def test_bad_global_gap_detected(self):
        points, beds, readings = fixtures()
        points[2]["gap_to_Fe"] = "99"
        report, _ = audit(points, beds, readings)
        self.assertTrue(any("Global Fe gap inconsistent" in x for x in report["errors"]))


if __name__ == "__main__":
    unittest.main()
