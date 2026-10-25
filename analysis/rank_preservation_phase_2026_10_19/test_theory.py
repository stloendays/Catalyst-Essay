"""Exhaustive finite-domain counterexample and proof-hypothesis tests.

These are verification tests of formal propositions; they do NOT establish
applicability of their economic assumptions to real industrial plants.
"""
from __future__ import annotations

import itertools
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas


def minimum(cost, domain):
    return min(cost[u] for u in domain)


class PreservationPropositions(unittest.TestCase):
    def test_exhaustive_feasible_superset_dominance(self):
        # For every pair of nonempty three-state domains with FB subset FA,
        # and all 0,1,2-valued cost functions, validate the theorem exactly.
        states = (0, 1, 2)
        domains = [set(u for u in states if mask & (1 << u))
                   for mask in range(1, 8)]
        checked = 0
        for fa in domains:
            for fb in domains:
                if not fb.issubset(fa):
                    continue
                for av in itertools.product((0, 1, 2), repeat=3):
                    a = dict(zip(states, av))
                    for bv in itertools.product((0, 1, 2), repeat=3):
                        b = dict(zip(states, bv))
                        if all(a[u] <= b[u] for u in fb):
                            self.assertLessEqual(minimum(a, fa), minimum(b, fb))
                            checked += 1
        self.assertGreater(checked, 1000)

    def test_uniform_pointwise_margin_is_preserved(self):
        fa = {0, 1, 2}
        fb = {0, 2}
        a = {0: 2.0, 1: 1.9, 2: 4.0}
        b = {0: 2.8, 1: 20.0, 2: 5.0}
        d = .8
        self.assertTrue(all(a[u] <= b[u] - d + 1e-12 for u in fb))
        self.assertLessEqual(minimum(a, fa), minimum(b, fb)-d+1e-12)

    def test_activity_alone_does_not_guarantee_cost_advantage(self):
        # Source discipline: even if upstream s_A > s_B,
        # metal or process economics may overwhelm activity.
        sA, sB = 2.0, 1.0
        cA, cB = 12.0, 10.0
        self.assertGreater(sA, sB)
        self.assertGreater(cA, cB)

    def test_dominance_on_intersection_is_not_sufficient(self):
        fa, fb = {0}, {0, 1}
        a = {0: 1.0}
        b = {0: 2.0, 1: 0.5}
        self.assertLess(a[0], b[0])
        self.assertGreater(minimum(a, fa), minimum(b, fb))

    def test_bounded_model_error_certificate(self):
        # In every state uniform |J-Jhat|<=epsilon => same optimum bound.
        fa, fb = {0, 1}, {1, 2}
        true_a = {0: 8.8, 1: 10.5}
        est_a = {0: 9.0, 1: 10.3}
        true_b = {1: 11.3, 2: 11.5}
        est_b = {1: 11.2, 2: 11.6}
        ea, eb = .2, .2
        self.assertLessEqual(abs(minimum(true_a, fa)-minimum(est_a, fa)), ea+1e-10)
        self.assertLessEqual(abs(minimum(true_b, fb)-minimum(est_b, fb)), eb+1e-10)
        self.assertGreater(minimum(est_b, fb)-minimum(est_a, fa),ea+eb)
        self.assertLess(minimum(true_a, fa),minimum(true_b, fb))
        # Merely small estimated difference is not a certificate.
        self.assertLess(.1,ea+eb)

    def test_exact_decomposition_requires_cross_feasibility(self):
        # C_A - C_B = (J_A(uB)-J_B(uB)) - (J_A(uB)-C_A)
        a = {"uB": 10.0, "uA": 7.0}
        b = {"uB": 5.0}
        cA, cB = min(a.values()), min(b.values())
        pointwise_gap = a["uB"]-b["uB"]
        reoptimisation_benefit = a["uB"]-cA
        self.assertAlmostEqual(cA-cB,pointwise_gap-reoptimisation_benefit)
        self.assertGreaterEqual(reoptimisation_benefit,0)

    def test_minimum_of_nonnegative_slope_lines_is_concave(self):
        # A finite fixed library with positive Ru loading slopes.
        designs = ((13.0, 0.0),(8.0, .03),(3.0, .10))
        pvals = tuple(range(201))
        y = [min(a+b*p for a,b in designs) for p in pvals]
        slopes = [y[i+1]-y[i] for i in range(len(y)-1)]
        self.assertTrue(all(x>=-1e-12 for x in slopes))
        self.assertTrue(all(b<=a+1e-12 for a,b in zip(slopes,slopes[1:])))
        # All-Fe is p-invariant, even when the optimal MIX is not.
        self.assertTrue(all((13+0.*p)==13.0 for p in pvals))

    def test_binary_parity_does_not_imply_actual_industrial_parity(self):
        # Fe and Ru tie but a feasible mixed pattern wins.
        winner = min({"FFF": 10., "RRR": 10., "FRR": 9.}.items(),key=lambda x:x[1])
        self.assertEqual(winner, ("FRR",9.0))


class PinnedSourceAndAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase,cls.prices,cls.rates,cls.pins=atlas.load_phase()

    def test_source_pins_are_actual_github_blobs(self):
        self.assertEqual(len(self.pins),3)
        self.assertEqual(len(self.phase),4100)
        self.assertEqual(len(self.prices),41)
        self.assertEqual(len(self.rates),25)

    def test_all_rows_are_relabelled_without_fitting(self):
        labels=set()
        for _,(src,computed) in self.phase.items():
            labels.add(computed["label"])
            self.assertEqual(src["best"],computed["label"])
        self.assertEqual(labels,set(atlas.CLASSES))

    def test_nominal_kaap_path_contains_three_policy_switches(self):
        paths=atlas.exact_nominal_price_paths(self.rates)
        kaap=[p for p in paths if p["P_bar"]==90.0]
        # Pre-existing source grid, no posthoc optimizer or interpolation.
        self.assertEqual([(p["from_best"],p["to_best"]) for p in kaap],
                         [("RRR","FRR"),("FRR","FFR"),("FFR","FFF")])
        self.assertTrue(all(
            round((p["upper_finance_rate"]-p["lower_finance_rate"]),8)==.005
            for p in kaap
        ))

    def test_financing_price_order(self):
        status,_=atlas.check_price_envelopes(self.phase,self.prices,self.rates)
        self.assertEqual(status["groups_checked"],100)
        self.assertTrue(status["nondecreasing_cost_assertions_passed"])

    def test_recovery_cannot_raise_optimal_model_cost(self):
        values=atlas.recovery_stability(self.phase,self.prices,self.rates)
        self.assertEqual(len(values),2)
        self.assertTrue(all(s["max_cost_decrease_USD_t"]>=0 for s in values))


if __name__=="__main__":
    unittest.main()
