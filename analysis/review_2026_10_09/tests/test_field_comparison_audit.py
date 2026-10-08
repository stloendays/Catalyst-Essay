"""Synthetic regression tests for the independent read-only classification audit."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from field_comparison_audit import audit, canonical_catalyst, distinct_t


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.points = []
        self.groups = []

    def add_group(self, key, states, sty_winner, cost_winner, *, cost_col="lab", regret=0.12):
        for cat, temp in states:
            self.points.append({
                "base": "thermo", "mode": "printed", "group": key,
                "catalyst": cat, "T_C": str(temp),
            })
        self.groups.append({
            "base": "thermo", "mode": "printed", "cost_col": cost_col,
            "group": key, "mismatch": "True", "regret": str(regret),
            "doi": f"doi:{key}", "sty_leader": sty_winner,
            "cost_leader": cost_winner,
        })

    def test_category_partition_and_denominator(self):
        self.add_group("temperature", [("A [250]", 250), ("A [325]", 325)],
                       "A [325]", "A [250]")
        self.add_group("material", [("A [250]", 250), ("B [250]", 250)],
                       "A [250]", "B [250]")
        self.add_group("both", [("A [300]", 300), ("B [250]", 250)],
                       "A [300]", "B [250]")
        # Different TOS measurements on same catalyst/temperature.
        self.add_group("tos", [("A [t0]", 250), ("A [t10]", 250)],
                       "A [t0]", "A [t10]")
        # Under the old >=2 rows rule, this was falsely a temperature series.
        self.add_group("multi_duplicates",
                       [("A [p1]", 250), ("A [p2]", 250), ("B [p3]", 250)],
                       "A [p1]", "B [p3]")
        result, rows = audit(self.points, self.groups, cost_cols=("lab",))
        s = result["scenarios"]["lab"]
        self.assertEqual(s["groups"], 5)
        self.assertEqual(s["multi_catalyst_groups"], 3)
        self.assertEqual(s["temperature_series_groups_row_count"], 3)
        self.assertEqual(s["temperature_series_groups_strict"], 1)
        self.assertEqual(s["catalyst_changes"], 3)
        self.assertEqual(s["same_catalyst_temperature_changes"], 1)
        self.assertEqual(s["categories"]["same_catalyst_same_temperature_different_record"], 1)
        self.assertEqual(sum(r["temperature_false_positive"] for r in rows), 2)
        self.assertFalse(s["errors"])

    def test_missing_or_ambiguous_leader_is_flagged(self):
        self.add_group("amb", [("A [loc]", 250), ("A [loc]", 300), ("B [p]", 250)],
                       "A [loc]", "B [p]")
        result, rows = audit(self.points, self.groups, cost_cols=("lab",))
        s = result["scenarios"]["lab"]
        self.assertIn("unresolved_leader_temperature", s["categories"])
        self.assertEqual(len(s["errors"]), 1)
        self.assertIsNone(rows[0]["sty_T_C"])

    def test_tolerance_and_name_normalization(self):
        self.assertEqual(canonical_catalyst("Cu–Ba /Al2O3 [Table]"), "cu-ba/al2o3")
        self.assertEqual(distinct_t([250, 250.02, 325, 325.01]), [250, 325])


if __name__ == "__main__":
    unittest.main()
