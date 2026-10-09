"""Source-grounded regression tests for safe editorial corrections.

These tests verify narrow facts already supported by committed evidence.
They intentionally do NOT certify S5 publication statistics, the source-data
freeze, or the manuscript as ready for submission.
"""
from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT/path).read_text(encoding="utf-8")


def csv_rows(path: str) -> list[dict]:
    with (ROOT/path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class EditorialSourceGrounding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = read("docs/MANUSCRIPT_MAIN_TEXT.md")
        cls.maincap = read("docs/MAIN_FIGURE_CAPTIONS.md")
        cls.supp = read("docs/SUPPLEMENTARY_INFORMATION.md")
        cls.extcap = read("figures/extended_data/ED_CAPTIONS.md")

    def test_01_alloy_claim_respects_model_domain(self):
        data = json.loads(read("analysis/nh3_alloy_extension_2026_10_05/summary.json"))
        screened = data["extended_excluding_sp_and_group3to5"]
        self.assertEqual(screened["costed"], 372)
        self.assertTrue(screened["below_Fe_either_route_all_3d_plus_group6"])
        self.assertEqual(data["extended_transition_metals_only"]["below_Fe"], 13)
        self.assertIn("Within the 372-surface subset containing only transition metals outside groups 3–5",self.main)
        self.assertNotIn("Among transition-metal alloys, only cheap 3d–group-6 pairs undercut Fe.",self.main)

    def test_02_accuracy_and_recall_not_equated(self):
        s = {(x["source_type"],x["field"]):x for x in
             csv_rows("agent/extraction/eval/field_accuracy_by_source.csv")}
        for field in ("X_CO2","S_MeOH","STY"):
            v = s["SI",field]
            correct, total = int(v["n_correct_strict"]),int(v["n_extracted"])
            self.assertIn(f"{correct} of {total}",self.main)
            self.assertIn(f"{correct} of {total}",self.supp)
        self.assertIn("curated-entry recall",self.main)
        self.assertNotIn("transcribes printed values exactly",self.main)
        self.assertNotIn("exact transcription of printed values",self.main)
        self.assertNotIn("remaining errors are plot readings",self.main)

    def test_03_manual_audit_scope_not_overstated(self):
        self.assertIn("150 of 179",self.main)
        self.assertIn("random sample of 87",self.main)
        self.assertNotIn("random sample of 90",self.main)
        self.assertIn("29 are not yet reviewed",self.supp)

    def test_04_material_and_temperature_are_distinct(self):
        self.assertIn("they do not require identical test temperatures",self.main)
        self.assertIn("a different economic winner need not imply a different catalyst material",self.main)
        self.assertIn("the comparison unit is a measured catalyst",self.supp.lower())

    def test_05_agent_pruning_bounds_are_reaction_specific(self):
        self.assertIn("descriptor-based lower bound restricts full optimization for ammonia",self.maincap)
        self.assertIn("purge-wise process-cost lower bound does so for methanol",self.maincap)
        self.assertIn("descriptor-only lower bound decides which ammonia candidates",self.main)
        self.assertIn("purge-wise plant bound decides which methanol candidates",self.main)

    def test_06_backward_design_panel_map_and_lower_bounds(self):
        self.assertNotIn("Fig. 4d,e",self.supp)
        self.assertIn("201.22-fold activity increase (Fig. 4a)",self.supp)
        self.assertIn("which remains above the Fe cost (Fig. 4b)",self.supp)
        self.assertIn("75-fold lies within the 70.78–462-fold target band",self.supp)
        self.assertIn("65-fold lies below its lower edge",self.supp)
        self.assertIn("the **>30×** lower bound",self.maincap)
        self.assertIn("does not by itself establish entry",self.maincap)

    def test_07_ed_ammonia_corpus_has_pure_metals(self):
        data = json.loads(read("analysis/nh3_alloy_extension_2026_10_05/summary.json"))
        v = data["extended_with_usgs_prices"]
        self.assertEqual(v["feasible"],406)
        self.assertEqual(v["bimetallic_feasible"],401)
        self.assertIn("401 bimetallic and 5 pure-metal",self.extcap)
        self.assertNotIn("406 ammonia bimetallic surfaces",self.extcap)

    def test_08_perez_fortes_reference_substitution_is_named(self):
        costs = [x for x in csv_rows(
            "analysis/meoh_plant_benchmark_2026_10_06/reconciliation_cost.csv")
            if x["case"].startswith("B3 Perez-Fortes") and x["term"]=="fixed O&M"]
        self.assertEqual(len(costs),1)
        own,reference=float(costs[0]["model"]),float(costs[0]["reference"])
        self.assertAlmostEqual(own,33.64,places=2)
        self.assertAlmostEqual(reference,24.57,places=2)
        self.assertIn(f"{reference:.2f} EUR",self.extcap)
        self.assertIn(f"{own:.2f} EUR",self.extcap)
        self.assertIn("harmonized model total substitutes the reference fixed operating cost",self.extcap)


if __name__ == "__main__":
    unittest.main()
