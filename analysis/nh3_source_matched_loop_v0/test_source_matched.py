"""Falsification and source-drift gates for NH3-STREAM-V0 (stdlib only).

Numerical assertions check the known source rounding and algebraic invariants.
They are retrospective source-internal consistency tests, NOT preregistered
independent physical holdout validation.
"""
from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import source_matched as S


class SourceMatchedConverter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = S.load_source_ledger()
        cls.cases = S.all_converters(cls.db)
        cls.uhde = S.uhde_stream_closure(
            cls.db, next(x for x in cls.cases if x["case_id"] == "UHDE188")
        )

    def test_primary_ledger_present_and_source_groups_distinct(self):
        self.assertGreaterEqual(len(self.db), 1500)
        self.assertEqual(len(self.cases), 3)
        self.assertEqual(len({c["source_group"] for c in self.cases}), 2)
        self.assertEqual(
            sum(c["source_resolution"] == "stream_resolved_figure_57" for c in self.cases),
            1,
        )
        self.assertEqual(
            sum(bool(c["reprinted_crossrefs"]) for c in self.cases),
            2,
        )

    def test_stoichiometric_flow_identity_without_feed_refitting(self):
        for fin in (1000.0, 28344.0):
            for yin, yout in ((0.01, 0.08), (0.0418, 0.1967), (0.10, 0.30)):
                made = S.ammonia_formed_kmol_h(fin, yin, yout)
                fout = fin - made
                self.assertAlmostEqual(fout * yout - fin * yin, made, places=9)
                self.assertAlmostEqual(2 * (made / 2) - made, 0.0, places=10)

    def test_invalid_converter_and_separator_inputs_falsified(self):
        for values in ((-1,0.01,0.1), (1000,.5,.1), (1000,.2,.2)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                S.ammonia_formed_kmol_h(*values)
        with self.assertRaises(ValueError):
            S.stage_liquid_from_gas(1000, 5.0, 6.0)

    def test_source_converter_capacity_internal_accounting(self):
        # Source publishes rounded molar fractions and nominal design output.
        # This is a retrospective internal consistency gate, not a predictive fit.
        by_id = {c["case_id"]: c for c in self.cases}
        self.assertAlmostEqual(by_id["UHDE188"]["new_NH3_tpd"], 1499.611135695, places=4)
        self.assertLess(max(abs(c["throughput_vs_nominal_pct"]) for c in self.cases), 2.0)
        for c in self.cases:
            self.assertLess(abs(c["stoichiometric_molar_residual_kmol_h"]), 1e-8)

    def test_first_separator_gas_and_liquid_source_cross_checks(self):
        u = self.uhde
        self.assertAlmostEqual(u["first_stage_gas_NH3_predicted_pct"], 8.48555861583, places=6)
        self.assertAlmostEqual(u["source_stage1_vapor_NH3_pct"], 8.51, places=8)
        self.assertAlmostEqual(u["first_liquid_source_t_h"], 51.36, places=8)
        self.assertAlmostEqual(u["first_liquid_inferred_from_gas_t_h"], 51.2614536249, places=5)
        self.assertLess(abs(u["first_stage_gas_relative_difference_pct"]), 1.0)
        self.assertLess(
            abs(u["converter_formation_minus_liquid_product_tpd"])
            / u["final_product_assumed_pure_tpd"], .005
        )

    def test_source_thermo_stage_boundaries_are_mapped_separately(self):
        u = self.uhde
        self.assertAlmostEqual(u["stage1_source_T_C"], 21.0)
        self.assertAlmostEqual(u["stage1_P_bar_from_same_vessel_liquid_R0014"], 180.2)
        self.assertAlmostEqual(u["stage2_source_T_C"], 0.0)
        self.assertAlmostEqual(u["stage2_gas_P_bar_R0015"], 178.8)
        self.assertTrue(8.0 < u["stage1_BASF_NH3_pct"] < 8.3)
        self.assertTrue(4.0 < u["stage2_BASF_NH3_pct"] < 4.2)
        self.assertGreater(u["stage1_source_over_BASF_ratio"], 1.0)
        self.assertGreater(u["stage2_source_over_BASF_ratio"], 1.0)
        self.assertIn("same-separator pressure assumption", u["stage1_P_basis"])

    def test_hydraulic_boundary_not_replaced_by_adjusted_3bar(self):
        u = self.uhde
        self.assertAlmostEqual(u["source_recycle_pressure_loss_bar"], 9.2)
        self.assertEqual(u["model_fixed_recycle_pressure_loss_bar"], 3.0)
        self.assertTrue(0.0 < u["cold_gas_isothermal_reversible_compression_MW"] < 5.0)

    def test_combined_makeup_and_recovery_accounting(self):
        u = self.uhde
        self.assertEqual(u["makeup_stream_10_kmol_h"], 7667)
        self.assertEqual(u["recovered_H2_stream_11_kmol_h"], 374)
        self.assertEqual(u["combined_makeup_stream_12_kmol_h"], 8041)
        self.assertEqual(u["fuel_stream_9_kmol_h"], 320)
        self.assertAlmostEqual(u["raw_makeup_external_closure_pct"], .10182498316, places=6)
        self.assertLess(abs(u["network_residual_minus_recovered_plus_fuel_kmol_h"]), 20.0)

    def test_wrong_after_final_separator_topology(self):
        u = self.uhde
        self.assertTrue(0.0 < u["counterfactual_after_final_sep_yin_pct"] < 4.18)
        self.assertGreater(u["counterfactual_after_final_sep_shortfall_pct_points"], 1.0)
        self.assertIn("only rules out THAT assumed connection", u["counterfactual_qualification"])

    def test_reported_precision_bounds_and_product_purity_sensitivity(self):
        u = self.uhde
        lo, hi = u["converter_NH3_tpd_printed_rounding_interval"]
        self.assertLess(lo, 1499.611135695)
        self.assertGreater(hi, 1499.611135695)
        self.assertTrue(u["printed_rounding_intervals_overlap_pure_NH3_assumption"])
        self.assertEqual(u["final_product_NH3_purity_note_molpct"], 99.82)
        product_lo, product_hi = u["hypothetical_product_NH3_tpd_impurity_MW_H2_to_Ar"]
        self.assertLess(product_lo, product_hi)
        self.assertLess(product_hi, u["final_product_assumed_pure_tpd"])
        self.assertTrue(1490 < product_lo < product_hi < 1501)
        with self.assertRaises(ValueError):
            S.ammonia_product_tpd_given_unknown_impurity(62.51, 1.02, 2.016)

    def test_source_wording_and_missing_information_preserved(self):
        self.assertIn("99.82", self.db["R0002"]["note"])
        self.assertIn("17.88 MPa", self.db["R0015"]["note"])
        self.assertIn("recovered H2", self.db["R0017"]["note"])
        self.assertIn("converter feed", self.db["R0015"]["note"])
        self.assertIn("source reactor", self.cases[2]["scope"])

    def test_report_files_and_no_main_or_provenance_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "reports"
            result = S.run(out)
            self.assertEqual(result["distinct_source_groups"], 2)
            for name in ("REPORT.md", "converter_source_3.csv",
                         "uhde_stream_closure.json", "summary.json"):
                self.assertTrue((out / name).exists(), name)
            self.assertIn("NOT an independently validated", (out/"REPORT.md").read_text())
            self.assertEqual(len(S.rows(out/"converter_source_3.csv")), 3)


if __name__ == "__main__":
    unittest.main()
