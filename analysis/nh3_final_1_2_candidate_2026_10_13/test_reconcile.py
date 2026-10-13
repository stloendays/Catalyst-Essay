"""Integration falsification tests: truthful adverse outcomes do not fail CI.

Test inputs are freshly recomputed GH Actions artifacts, NOT pinned desired
scientific outcomes. Only numerical integrity and frozen anchors are gated.
"""
from __future__ import annotations
import copy
import os
import unittest
from pathlib import Path

import reconcile as R

THERMO = Path(os.environ.get("NH3_FINAL12_THERMO", "/tmp/audit-thermo/summary.json"))
KINETICS = Path(os.environ.get("NH3_FINAL12_KINETICS", "/tmp/audit-kinetics/kinetics_swap.json"))
DOMAIN = Path(os.environ.get("NH3_FINAL12_DOMAIN", "/tmp/audit-kinetics/source_domain.json"))

class ScienceFalsificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = R.load(THERMO)
        cls.swap = R.load(KINETICS)
        cls.domain = R.load(DOMAIN)

    def test_independent_artifacts_agree(self):
        self.assertEqual(set(R.check(self.base, self.swap, self.domain)),
                         {"frozen", "NIST", "GB"})

    def test_real_ranking_change_is_reportable_not_hidden_or_failed(self):
        thermo = copy.deepcopy(self.base)
        x = thermo["results"]["NIST"]
        # Counterfactual, visibly isolated in a test only; not a claim
        # about any real result or a modified manuscript figure.
        x["Fe_cost_USD_t"] = 40.0
        x["metals"]["Fe"]["feasible"]["cost_USD_t"] = 40.0
        x["feasible_economic_order"] = sorted(
            (m for m, d in x["metals"].items() if d["feasible"] is not None),
            key=lambda m: x["metals"][m]["feasible"]["cost_USD_t"])
        x["Ru_minus_Fe_USD_t"] = x["Ru_cost_USD_t"] - x["Fe_cost_USD_t"]
        x["Fe_minus_Ru_USD_t"] = -x["Ru_minus_Fe_USD_t"]
        x["Fe_Ru_Os_order_matches_frozen"] = False
        x["model_inversion_Ru_Os_Fe_to_Fe_Ru_Os"] = False
        self.assertFalse(x["model_inversion_Ru_Os_Fe_to_Fe_Ru_Os"])
        self.assertEqual(R.check(thermo, self.swap, self.domain)["NIST"], x)

    def test_stale_inversion_flag_is_rejected(self):
        thermo = copy.deepcopy(self.base)
        x = thermo["results"]["NIST"]
        x["model_inversion_Ru_Os_Fe_to_Fe_Ru_Os"] = not x["model_inversion_Ru_Os_Fe_to_Fe_Ru_Os"]
        with self.assertRaises(AssertionError):
            R.check(thermo, self.swap, self.domain)

    def test_inconsistent_supported_ru_financing_is_rejected(self):
        swap = copy.deepcopy(self.swap)
        v = swap["variants"][0]["Ru_C_supported"]["cashflow 12% r 0.9"]
        v["Ru_minus_Fe_global"] += 1.0
        with self.assertRaises(AssertionError):
            R.check(self.base, swap, self.domain)

    def test_missing_fitted_source_support_is_rejected(self):
        domain = copy.deepcopy(self.domain)
        domain["n_variants"] = 7
        with self.assertRaises(AssertionError):
            R.check(self.base, self.swap, domain)

if __name__ == "__main__":
    unittest.main()
