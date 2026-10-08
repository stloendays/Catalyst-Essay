"""Regression tests: imputed species versus genuinely printed CO/CH4 values."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from selectivity_source_audit import audit, candidate_report, match_record, printed


def original(entry, *, meoh=60.0, co=None, ch4=None):
    return dict(
        doi="doi:test", entry_label=entry, catalyst_name=entry,
        T_K="523.15", P_bar="40", X_CO2_pct="10", X_CO2_q="=",
        X_CO2_src="main", S_MeOH_pct=str(meoh), S_MeOH_q="=",
        S_MeOH_src="main", S_CO_pct="" if co is None else str(co),
        S_CO_q="" if co is None else "=", S_CO_src="" if co is None else "main",
        S_CH4_pct="" if ch4 is None else str(ch4),
        S_CH4_q="" if ch4 is None else "=", S_CH4_src="" if ch4 is None else "main",
    )


def point(entry, sco, sch4):
    return dict(
        base="thermo", mode="printed", group="g1", doi="doi:test",
        entry=entry, catalyst=f"{entry} [{entry}]", T_C="250",
        P_bar="40", SCO=str(sco), SCH4=str(sch4),
    )


def group(cost_col):
    return dict(base="thermo", mode="printed", group="g1",
                cost_col=cost_col, doi="doi:test",
                mismatch="True", regret="0.125",
                sty_leader="A [A]", cost_leader="B [B]")


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.records = [original("A", co=10, ch4=20),
                        original("B", co=10, ch4=None)]
        # A: printed CO 10%, but closure makes it 20%.
        # B: CO printed, CH4 unknown; its value is inferred from carbon closure.
        self.points = [point("A", 0.2, 0.2), point("B", 0.1, 0.3)]
        self.groups = [group("lab"), group("cost_f0.95")]

    def test_missing_CH4_is_imputation_and_reported_CO_override_is_visible(self):
        summary, candidates, groups = audit(self.points, self.groups, self.records)
        self.assertEqual(summary["candidates"]["candidates"], 2)
        self.assertEqual(summary["candidates"]["source_unique"], 2)
        self.assertEqual(summary["candidates"]["missing_CH4"], 1)
        self.assertEqual(summary["candidates"]["reported_CO_closed_delta_gt5pp"], 1)
        self.assertEqual(summary["scenario"]["lab"]["mismatch_winner_either_closure"], 1)
        self.assertEqual(summary["scenario"]["lab"]["gt5pct_winner_either_closure"], 1)
        self.assertFalse(summary["scenario"]["lab"]["errors"])
        self.assertTrue(groups[0]["either_leader_missing_CO_or_CH4"])
        self.assertTrue(groups[0]["either_leader_reported_CO_shift_gt5pp"])

    def test_missing_both_channels_detected(self):
        x = candidate_report(point("Z", 0.4, 0.0),
                             original("Z", co=None, ch4=None), "unique")
        self.assertEqual(x["source_completeness"], "only_MeOH_printed")
        self.assertTrue(x["missing_CO"] and x["missing_CH4"])

    def test_plot_read_co_is_not_a_printed_component(self):
        a = original("A", co=10, ch4=20)
        a["S_CO_src"] = "plot"
        self.assertFalse(printed(a, "S_CO"))

    def test_match_duplicate_label_is_not_silently_chosen(self):
        p = point("A", .2, .2)
        records = {("doi:test", "A"): [original("A"), original("A")]}
        found, status = match_record(p, records)
        self.assertIsNone(found)
        self.assertEqual(status, "ambiguous")

    def test_reported_below_limit_is_not_treated_as_exact_CO(self):
        a = original("A", co=0.4, ch4=20)
        a["S_CO_q"] = "<"
        x = candidate_report(point("A", 0.2, 0.2), a, "unique")
        self.assertEqual(x["reported_CO_pct"], 0.4)
        self.assertEqual(x["CO_closed_vs_reported_delta_pp"], "")
        self.assertFalse(x["CO_delta_gt5pp"])


if __name__ == "__main__":
    unittest.main()
