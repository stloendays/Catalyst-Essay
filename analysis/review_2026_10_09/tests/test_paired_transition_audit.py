"""Synthetic paired-transition tests for independent methanol classification."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_transition_audit import pair_rows


def case(group, condition, kind, *, cost_leader="B", regret=0.1):
    return {
        "base": "thermo", "mode": "printed", "group": group,
        "doi": "doi:" + group, "cost_col": condition,
        "classification": kind, "sty_leader": "A", "cost_leader": cost_leader,
        "n_catalysts": 2, "temp_series_strict": True, "regret": regret,
    }


class PairedTests(unittest.TestCase):
    def test_new_lost_and_kind_change_are_separate(self):
        rows = [
            case("a", "lab", "different_catalyst_same_temperature", cost_leader="B"),
            case("a", "cost_f0.95", "same_catalyst_different_temperature", cost_leader="A250"),
            case("b", "lab", "no_winner_change", cost_leader="A"),
            case("b", "cost_f0.95", "different_catalyst_and_temperature", cost_leader="B250"),
            case("c", "lab", "same_catalyst_different_temperature", cost_leader="A250"),
            case("c", "cost_f0.95", "no_winner_change", cost_leader="A"),
            case("d", "lab", "no_winner_change", cost_leader="A"),
            case("d", "cost_f0.95", "no_winner_change", cost_leader="A"),
        ]
        summary, cases = pair_rows(rows)
        self.assertEqual(summary["counts"]["groups"], 4)
        self.assertEqual(summary["counts"]["lab_mismatches"], 2)
        self.assertEqual(summary["counts"]["adjusted_mismatches"], 2)
        self.assertEqual(summary["counts"]["new_mismatch"], 1)
        self.assertEqual(summary["counts"]["lost_mismatch"], 1)
        self.assertEqual(summary["counts"]["changed_disagreement_type"], 1)
        self.assertFalse(summary["errors"])
        self.assertEqual(len(cases), 4)

    def test_mismatched_upstream_leader_is_a_hard_error(self):
        a = case("a", "lab", "no_winner_change")
        b = case("a", "cost_f0.95", "different_catalyst_same_temperature")
        b["sty_leader"] = "C"
        summary, _ = pair_rows([a, b])
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("Upstream STY leader", summary["errors"][0])

    def test_missing_paired_case_reported(self):
        summary, _ = pair_rows([case("a", "lab", "no_winner_change")])
        self.assertIn("Missing paired", summary["errors"][0])


if __name__ == "__main__":
    unittest.main()
