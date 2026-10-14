"""Twelve-stream multispecies process closure and evidence integrity tests.

These are source-table consistency and conservation tests. They do not
simulate a new independently validated catalytic production plant.
"""
import tempfile
import unittest
from pathlib import Path

import species_reconstruct as S

class FullUhdeFigure57(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st=S.load_streams()
        cls.report=S.source_observation_reconstruction()

    def test_all_twelve_source_streams_five_species(self):
        self.assertEqual(set(self.st),set(range(1,13)))
        for i,v in self.st.items():
            self.assertEqual(len(v["y"]),5)
            self.assertLess(abs(sum(v["y"].values())-1.0),.0002)
            self.assertEqual(v["source_doi"],S.DOI)

    def test_all_nine_observation_conditioned_control_volumes(self):
        self.assertEqual(len(self.report["balance_groups"]),9)
        self.assertEqual(
            {z["boundary"] for z in self.report["balance_groups"]},
            {"converter_first_two_beds","intervessel_cooling",
             "converter_third_bed","converter_overall","first_separator",
             "hydrogen_recovery_makeup_mixing","recycle_transport",
             "aggregate_separation_purge_mixing","overall_plant_external"})
        for b in self.report["balance_groups"]:
            self.assertLess(b["total_balance_abs_pct_feed"],.08)
            self.assertLess(b["max_species_residual_pct_feed"],.08)

    def test_no_nh3_mass_made_up_for_liquid_impurities(self):
        l={v["stream"]:v for v in self.report["reconstructed_liquid_NH3_component"]}
        self.assertEqual(set(l),{7,8,9})
        self.assertAlmostEqual(l[7]["source_printed_NH3_liquid_t_h"],51.36)
        self.assertAlmostEqual(l[8]["source_printed_NH3_liquid_t_h"],62.51)
        self.assertAlmostEqual(l[9]["source_printed_NH3_liquid_t_h"],.01)
        for v in l.values():
            self.assertLess(abs(v["computed_minus_printed_t_h"]),.035)
            self.assertGreater(v["total_stream_mass_t_h"],
                               v["computed_NH3_component_t_h"])

    def test_production_vs_reported(self):
        v=self.report
        self.assertAlmostEqual(v["reactor_converted_NH3_tpd"],1499.3560487808,places=3)
        self.assertAlmostEqual(v["industrial_reported_liquid_NH3_tpd"],1500.24,places=2)
        self.assertLess(abs(v["reactor_vs_reported_product_relative_pct"]),.08)

    def test_first_separator_independent_reconstruction(self):
        v=self.report
        self.assertLess(abs(v["first_separator_NH3_molpct_point_diff"]),.015)
        self.assertLess(abs(v["first_separator_NH3_gas_pred_pct"]-8.51),.015)
        for name,y in v["first_separator_pred_all_5_species_pct"].items():
            self.assertLess(abs(y-self.st[5]["y"][name]*100),.05)

    def test_separators_at_printed_gas_stream_pressures(self):
        values=self.report["source_stage_vle_crossmixture_reference"]
        self.assertEqual([v["stream"] for v in values],[5,6])
        self.assertAlmostEqual(values[0]["pressure_bar_from_printed_gas_stream"],180.2)
        self.assertAlmostEqual(values[1]["pressure_bar_from_printed_gas_stream"],178.8)
        self.assertAlmostEqual(values[0]["temperature_C"],21.0)
        self.assertAlmostEqual(values[1]["temperature_C"],0.0)
        self.assertAlmostEqual(values[0]["BASF_in_domain_1to3_N2H2_vapor_NH3_molpct"],8.10782,places=4)
        self.assertAlmostEqual(values[1]["BASF_in_domain_1to3_N2H2_vapor_NH3_molpct"],4.0968,places=4)
        self.assertTrue(all(v["relative_source_minus_BASF_pct"]<6.0 for v in values))

    def test_stream6_stream1_pressure_and_mixture(self):
        self.assertAlmostEqual(self.report["documented_loop_pressure_difference_bar"],9.2)
        self.assertEqual(self.report["stream6_stream1_NH3_pct"],(4.18,4.18))
        recirc=next(x for x in self.report["balance_groups"]
                    if x["boundary"]=="recycle_transport")
        self.assertLess(recirc["max_species_residual_pct_feed"],.02)

    def test_makeup_recovered_gas_and_aggregate_boundary(self):
        mix=next(x for x in self.report["balance_groups"]
                 if x["boundary"]=="hydrogen_recovery_makeup_mixing")
        self.assertEqual(mix["total_mole_balance_residual_kmol_h"],0)
        sep=next(x for x in self.report["balance_groups"]
                 if x["boundary"]=="first_separator")
        self.assertLess(abs(sep["total_mole_balance_residual_kmol_h"]),2)
        agg=next(x for x in self.report["balance_groups"]
                 if x["boundary"]=="aggregate_separation_purge_mixing")
        self.assertLess(abs(agg["total_mole_balance_residual_kmol_h"]),4)
        self.assertIn("NOT uniquely determine",agg["basis"])

    def test_output_traceability(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)
            S.write_report(self.report,output)
            for name in ("REPORT.md","species_summary.json",
                         "component_balance_9.csv","component_residuals_45.csv"):
                self.assertTrue((output/name).is_file())
            report=(output/"REPORT.md").read_text(encoding="utf-8")
            self.assertIn("industrial observations",report)
            self.assertIn("five species",report)
            with (output/"component_residuals_45.csv").open(encoding="utf-8") as f:
                self.assertEqual(len(f.readlines())-1,45)

    def test_locked_source_input(self):
        self.assertEqual(S.blob_sha(S.FILE),S.FILE_BLOB)


if __name__=="__main__":
    unittest.main()
