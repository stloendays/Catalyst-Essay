"""Synchronize NH3 industrial stream reconstruction data with manuscript text.

Numbers are computed at test time from the pinned twelve-stream reference;
no main science or supplementary files are modified by this test.
"""
from pathlib import Path
import unittest
import species_reconstruct as S

ROOT=Path(__file__).resolve().parents[2]


class PaperTraceability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=S.source_observation_reconstruction()
        cls.main=(ROOT/"docs/MANUSCRIPT_MAIN_TEXT.md").read_text(encoding="utf-8")
        cls.si=(ROOT/"docs/SUPPLEMENTARY_INFORMATION.md").read_text(encoding="utf-8")

    def test_all_publication_metrics_derive_from_registered_source(self):
        d=self.data
        common={
            f"{d['reactor_converted_NH3_tpd']:,.2f} t/d",
            f"{d['industrial_reported_liquid_NH3_tpd']:,.2f} t/d",
            f"{d['first_separator_NH3_gas_pred_pct']:.3f}",
            f"{d['first_separator_NH3_gas_observed_pct']:.2f}",
            f"{max(x['max_species_residual_pct_feed'] for x in d['balance_groups']):.3f}%",
        }
        for metric in common:
            with self.subTest(metric=metric):
                self.assertIn(metric,self.main)

    def test_manuscript_refs_and_method_scope(self):
        self.assertIn("65. Appl, M. Ammonia, 2. Production Processes.",self.main)
        self.assertIn("doi:10.1002/14356007.o02_o11",self.main)
        self.assertIn("source-resolved plant data",self.main)
        self.assertIn("five-component steady-state process simulation",self.main)
        self.assertIn("process reconstruction",self.main)
        self.assertIn("ν_i ξ",self.main)
        self.assertIn("NH3-FINAL-1.2",self.si)
        self.assertIn("32/64",self.si)

    def test_supplement_matches_45_component_residuals(self):
        d=self.data
        self.assertEqual(len(d["balance_groups"])*len(d["components"]),45)
        self.assertIn("all 45 component residuals",self.si)
        self.assertIn(f"{max(x['max_species_residual_pct_feed'] for x in d['balance_groups']):.4f}%",self.si)
        self.assertIn("8.108 mol%",self.si)
        self.assertIn("4.097 mol%",self.si)
        self.assertIn("12 numbered streams",self.si)
        self.assertIn("11",self.si)  # stream 11 recovered hydrogen
        self.assertIn("does not replace",self.main)

    def test_published_scores_stay_unchanged(self):
        self.assertIn("11.516, 16.633 and 19.747",self.main)
        self.assertIn("11.516, 16.633 and 19.747",self.si)
        self.assertIn("Fe, Ru and Os",self.main)
        self.assertIn("original NH3-FINAL-1.2 preregistered external benchmark",self.si)


if __name__=="__main__":
    unittest.main()
