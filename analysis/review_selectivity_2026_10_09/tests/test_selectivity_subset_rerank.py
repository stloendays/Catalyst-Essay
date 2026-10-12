"""Read-only subset reranking: synthetic parity and completeness checks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from selectivity_subset_rerank import compare, strict_components, top1


def raw(entry, *, co=10, ch4=20):
    return dict(doi="doi:test", entry_label=entry, catalyst_name=entry,
                X_CO2_pct="10", X_CO2_q="=", X_CO2_src="text",
                S_MeOH_pct="70", S_MeOH_q="=", S_MeOH_src="text",
                S_CO_pct=str(co), S_CO_q="=", S_CO_src="text",
                S_CH4_pct="" if ch4 is None else str(ch4),
                S_CH4_q="" if ch4 is None else "=",
                S_CH4_src="" if ch4 is None else "text",
                T_K="523.15", P_bar="40")


def cand(entry, sty, lab, opt):
    return dict(base="thermo", mode="printed", doi="doi:test", entry=entry,
                catalyst=f"{entry} [{entry}]", group="g1", T_C="250",
                P_bar="40", SCO="0.1", SCH4="0.2",
                STY=str(sty), lab=str(lab), **{"cost_f0.95": str(opt)})


def group(cost_col, regret):
    return dict(base="thermo", mode="printed", doi="doi:test",
                group="g1", cost_col=cost_col, mismatch="True",
                regret=str(regret), sty_leader="A [A]", cost_leader="C [C]")


class SubsetTests(unittest.TestCase):
    def test_sty_ties_do_not_count_as_reversal(self):
        a = cand("A", 10, 100, 100)
        b = cand("B", 10, 90, 90)
        v = top1([a, b], "lab")
        self.assertFalse(v["mismatch"])
        self.assertAlmostEqual(v["regret"], 0)

    def test_partial_selectivity_cases_are_excluded(self):
        points = [cand("A", 10, 90, 80),
                  cand("B", 9, 95, 85),
                  cand("C", 8, 40, 39)]
        original = [raw("A"), raw("B"), raw("C", ch4=None)]
        regret_lab = (90 - 40) / 40
        regret_opt = (80 - 39) / 39
        groups = [group("lab", regret_lab), group("cost_f0.95", regret_opt)]
        summary, detailed = compare(points, groups, original)
        self.assertFalse(summary["errors"])
        self.assertEqual(summary["cohorts"]["full_printed_X_MeOH|lab"]["groups"], 1)
        self.assertEqual(summary["cohorts"]["full_printed_X_MeOH|lab"]["mismatches"], 1)
        fully_printed = summary["cohorts"]["CO_CH4_both_printed|lab"]
        self.assertEqual(fully_printed["groups"], 1)
        self.assertEqual(fully_printed["mismatches"], 0)
        self.assertEqual(fully_printed["full_mismatches_in_retained_groups"], 1)
        self.assertEqual(fully_printed["lost_mismatches_in_retained_groups"], 1)
        self.assertEqual(fully_printed["new_mismatches_in_retained_groups"], 0)
        strict = summary["cohorts"]["CO_CH4_exact_and_closed_within_1pp|lab"]
        self.assertEqual(strict["groups"], 1)
        self.assertEqual(strict["candidates_in_eligible_groups"], 2)
        self.assertEqual(strict["mismatches"], 0)

    def test_below_detection_limit_is_not_exact(self):
        s = dict(has_printed_CO=True, has_printed_CH4=True,
                 qualifier_CO="<", qualifier_CH4="=",
                 CO_closed_vs_reported_delta_pp="", modeled_CH4_pct=10,
                 reported_CH4_pct=10)
        self.assertFalse(strict_components(s))


if __name__ == "__main__":
    unittest.main()
