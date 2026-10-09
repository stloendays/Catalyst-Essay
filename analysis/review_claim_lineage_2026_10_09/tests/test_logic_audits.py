"""Regression tests for cross-document scientific claim lineage checks."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_claim_lineage import catalyst, has_temperature_series, inspect_docs, classify_leader_change_temperatures
from paired_paper_bootstrap import paired_ci, percentile


class LogicTests(unittest.TestCase):
    def test_temperature_series_counts_distinct_temperatures(self):
        self.assertFalse(has_temperature_series([250,250,250.02]))
        self.assertTrue(has_temperature_series([250,325]))
        self.assertEqual(catalyst("Pd–In [SI line 3]"), "pd-in")

    def test_old_main_text_and_SI_table_are_submission_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"docs").mkdir()
            (root/"figures/extended_data").mkdir(parents=True)
            (root/"docs/MANUSCRIPT_MAIN_TEXT.md").write_text(
                "We saw 33/83 cases and 44/124 ammonia cases. "
                "Among transition-metal alloys, only cheap 3d–group-6 pairs win. "
                "The agent transcribes printed values exactly.",
                encoding="utf-8")
            (root/"docs/SI_TABLES.md").write_text(
                "the baseline reproduces the frozen headline (54/82, 2989/8285)",
                encoding="utf-8")
            expected = {
                "methanol": {
                    "mismatches": 15, "groups": 40, "papers": 28,
                    "different_catalyst_lab": 10, "multi_catalyst_groups": 32,
                    "same_catalyst_temperature_lab": 5,
                    "temperature_series_groups_strict": 22,
                    "old_benchmark_baseline": "33/83",
                },
                "ammonia": {"mismatches": 7, "groups": 33},
                "extraction": {
                    "SI_meoh_selectivity": [123, 128], "SI_STY": [116,121],
                },
                "alloy": {"transition_below_Fe": 13},
            }
            issues = inspect_docs(root, expected)
            labels = {i["rule"] for i in issues}
            for kind in ("ME_OH_PRIMARY", "NH3_PRIMARY", "SI5F_SOURCE_MISMATCH",
                         "EXTRACTION_OVERCLAIM", "ALLOY_DOMAIN"):
                self.assertIn(kind, labels)
            self.assertTrue(all(x["severity"] == "BLOCKER" for x in issues))

    def test_joint_material_temperature_winner_is_not_pure_material_evidence(self):
        points = []
        group_rows = []
        for group, a_label, a_temp, b_label, b_temp in (
            ("same_temp", "A [a]", 250, "B [b]", 250),
            ("joint", "A [a]", 250, "B [b]", 275),
            ("temp_only", "A [a]", 250, "A [b]", 275),
        ):
            for cat, t in ((a_label,a_temp),(b_label,b_temp)):
                points.append(dict(group=group,catalyst=cat,T_C=str(t)))
            for condition in ("lab","cost_f0.95"):
                group_rows.append(dict(group=group,sty_leader=a_label,
                                       cost_leader=b_label,mismatch="True",
                                       base="thermo",mode="printed",cost_col=condition))
        res = classify_leader_change_temperatures(points,group_rows)
        for r in res.values():
            self.assertEqual(r["different_material_same_winner_T"], 1)
            self.assertEqual(r["different_material_and_winner_T"], 1)
            self.assertEqual(r["same_material_different_T"], 1)

    def test_percentile_linear_and_case_sensitivity(self):
        self.assertAlmostEqual(percentile([1,3,5],0.5), 3)
        self.assertAlmostEqual(percentile([1,3,5],0.25), 2)

    def test_bootstrap_resamples_papers_not_individual_groups(self):
        cases = []
        for col in ("lab","cost_f0.95"):
            for doi, group, mismatch in (
                ("d1","a",True), ("d1","b",True),
                ("d2","c",False), ("d2","d",False),
            ):
                cases.append(dict(doi=doi,group=group,mismatch=str(mismatch),
                                  regret="0.11" if mismatch else "0",
                                  cost_col=col,base="thermo",mode="printed"))
        out1=paired_ci(cases,seed=71,draws=500)
        out2=paired_ci(cases,seed=71,draws=500)
        self.assertEqual(out1, out2)
        self.assertEqual(out1["observed"]["lab"]["mismatches"],2)
        self.assertEqual(out1["observed"]["lab"]["groups"],4)
        self.assertEqual(out1["observed"]["lab"]["papers"],2)
        self.assertEqual(out1["paired_difference"]["cluster_ci95"],[0.0,0.0])
        self.assertEqual(out1["bootstrap_group_count_range"],[4,4])

    def test_paired_bootstrap_rejects_changed_comparison_population(self):
        base=[
            dict(doi="d1", group="a", base="thermo", mode="printed",
                 cost_col="lab", mismatch="True", regret="0.1"),
            dict(doi="d1", group="b", base="thermo", mode="printed",
                 cost_col="cost_f0.95", mismatch="False", regret="0"),
        ]
        with self.assertRaisesRegex(ValueError, "not identical"):
            paired_ci(base,draws=101)


if __name__ == "__main__":
    unittest.main()
