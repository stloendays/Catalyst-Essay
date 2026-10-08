"""Synthetic regression tests for Pérez-Fortes cost-boundary reconciliation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pf_benchmark_audit import benchmark_cost_rows, calculate, weight_constants


def fixture():
    prefix = "B3 Perez-Fortes benchmark"
    cost = [
        dict(case=prefix, term=k, model=str(m), reference=str(r))
        for k, m, r in [
            ("H2", 613.6, 615.7),
            ("electricity + utilities", 20.23, 16.69),
            ("catalyst replacement", 9.615, 9.63),
            ("capital (annuity at 8 %, 20 y)", 38.14, 57.55),
            ("fixed O&M", 33.64, 24.57),
            ("residual direct + 10 % of NPC (anchor convention)", 126.2, 0),
            ("TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)", 706.1, 723.6),
            ("TOTAL, anchor convention", 841.4, 723.6),
        ]
    ]
    refs = dict(
        FCP_eur_t=24.57, H2_price=3090.0, CO2_price=0.0,
        VCP_eur_t=641.48, breakeven_MeOH_price_eur_t=723.6,
        production_cost_no_capital_eur_t=666.05,
        H2_t_per_t=0.199, carbon_efficiency=0.9385,
        recycle_ratio=4.7, electricity_compressors_MWh_t=0.305,
        electricity_net_MWh_t=0.169,
    )
    summary = dict(h2_eur_t=613.555, co2_eur_t=0,
                   elec_eur_t=20.232, cat_eur_t=9.615,
                   acc_eur_t=38.136, carbon_efficiency=.955,
                   co2_t_per_t=1.438)
    plant = dict(
        **{
            "H2 consumption (t/t MeOH)": 0.1986,
            "CO2 consumption (t/t MeOH)": 1.4383,
            "Carbon efficiency (MeOH C / fresh CO2)": .9549,
            "Recycle ratio (recycle / fresh feed, mol)": 5.3799,
            "Electricity, compression (MWh/t)": .2127,
        },
    )
    mw = dict(MeOH=32.04186, H2=2.01588, CO2=44.0095)
    return cost, refs, summary, 706.11, plant, mw


class BenchmarkTests(unittest.TestCase):
    def test_stoichiometry_removes_common_mode_hydrogen_floor(self):
        report, items = calculate(*fixture())
        self.assertFalse(report["errors"])
        c = report["cost_comparison"]
        self.assertAlmostEqual(c["model_like_for_like_EUR_t"], 706.108, places=3)
        self.assertAlmostEqual(c["own_OandM_vs_reference_gap_EUR_t"], 9.07, places=2)
        self.assertGreater(c["H2_stoichiometric_cost_floor_EUR_t"], 580)
        self.assertLess(c["H2_stoichiometric_cost_floor_EUR_t"], 590)
        self.assertGreater(abs(c["relative_nonfloor_residual_difference_pct"]),
                           abs(c["relative_total_difference_pct"]))
        self.assertEqual(len(items), 7)

    def test_substituting_model_fixed_om_changes_total(self):
        report, _ = calculate(*fixture())
        c = report["cost_comparison"]
        self.assertGreater(c["model_displayed_own_OandM_sum_EUR_t"],
                           c["model_like_for_like_EUR_t"])
        self.assertAlmostEqual(c["model_displayed_own_OandM_sum_EUR_t"] -
                               c["model_like_for_like_EUR_t"], 9.1, delta=0.1)

    def test_wrong_like_for_like_total_is_detected(self):
        args = list(fixture())
        args[0][6]["model"] = "999"
        report, _ = calculate(*args)
        self.assertTrue(any("like-for-like summation" in err
                            for err in report["errors"]))

    def test_missing_cost_term_fails_closed(self):
        args = list(fixture())
        args[0].pop(0)
        with self.assertRaisesRegex(ValueError, "Required B3 term absent"):
            benchmark_cost_rows(args[0])

    def test_model_molecular_weights_are_read_not_assumed(self):
        model = Path(__file__).resolve().parents[3] / "data" / "meoh" / "meoh_d01_model.py"
        mw = weight_constants(model)
        self.assertAlmostEqual(mw["MeOH"], 32.04186)
        self.assertAlmostEqual(mw["H2"], 2.01588)
        self.assertAlmostEqual(mw["CO2"], 44.0095)


if __name__ == "__main__":
    unittest.main()
