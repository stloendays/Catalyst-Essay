"""Harness-free checks of the evidence tables and the vendored PR #61 module."""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PR61_BLOB = "c2f24bb9a5c64235017bfc8758caa304b1b6338f"  # branch nh3-ru-commercial-terms-2026-10-12
CRLF, LF = bytes([13, 10]), bytes([10])


def rows(name):
    with (HERE / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class EvidenceTables(unittest.TestCase):
    def test_pbf_contracts(self):
        contracts = rows("pbf_catalyst_lease_contracts.csv")
        self.assertEqual(len(contracts), 32)
        self.assertEqual(len({c["contract_id"] for c in contracts}), 32)
        rates = [float(c["annual_rate_pct"]) for c in contracts]
        self.assertEqual((min(rates), statistics.median(rates), max(rates)), (1.35, 2.10, 5.10))
        for c in contracts:
            self.assertTrue(c["source_url"].startswith("https://www.sec.gov/Archives/edgar/data/"))
            self.assertEqual(c["rate_type"], "fixed")

    def test_documented_rates_have_sources(self):
        rates = rows("documented_rates.csv")
        self.assertEqual(len({r["rate_id"] for r in rates}), len(rates))
        for r in rates:
            self.assertTrue(r["source_id"], r["rate_id"])
            if r["rate_pct"]:
                self.assertGreaterEqual(float(r["rate_pct"]), 0.0)

    def test_vendored_pr61_module_is_byte_identical(self):
        # Compare as git stores it (LF), so a CRLF checkout on Windows also passes.
        data = (HERE / "supplier_metal_contracts_pr61.py").read_bytes().replace(CRLF, LF)
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        self.assertEqual(blob, PR61_BLOB)

    def test_summary_threshold_classification(self):
        path = HERE / "summary.json"
        if not path.exists():
            self.skipTest("run_documented_rates.py has not been run")
        s = json.loads(path.read_text(encoding="utf-8"))
        owned_t = s["regressions"]["owned_parity_rate"]
        lease_t = s["regressions"]["lease_parity_rent"]
        self.assertAlmostEqual(owned_t, 0.005604190907647176, places=12)
        self.assertEqual(round(100 * lease_t, 2), 0.92)
        for key, h in s["headline"].items():
            rate = h["rate_pct"] / 100
            self.assertEqual(h["owned_gap_USD_t"] <= 0, rate <= owned_t, key)
            self.assertEqual(h["lease_gap_USD_t"] <= 0, rate <= lease_t, key)


if __name__ == "__main__":
    unittest.main()
