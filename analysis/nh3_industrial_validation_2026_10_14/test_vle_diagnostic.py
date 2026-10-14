"""Independent checks of the source-only VLE analysis: no parameter fitting."""
import unittest

import diagnose_separator_vle as D


class SourceVLE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grid = D.grid_from_printed_sources()

    def test_exact_source_nodes(self):
        self.assertEqual(len(self.grid), 28)
        for (t, p), r in self.grid.items():
            self.assertAlmostEqual(D.source_interpolation(self.grid, t, p * 10.0), r["source_y_pct"], places=12)

    def test_no_extrapolation(self):
        for t, p in ((-35, 150), (35, 150), (0, 80), (0, 325)):
            with self.subTest(T=t, P=p), self.assertRaises(ValueError):
                D.source_interpolation(self.grid, t, p)

    def test_monotone_pressure_bias_and_no_single_factor(self):
        records, summary = D.source_diagnostic(self.grid)
        self.assertEqual(len(records), 28)
        self.assertTrue(summary["all_temperatures_have_monotonic_pressure_bias"])
        self.assertFalse(summary["constant_multiplicative_correction_within_20pct_possible"])
        self.assertTrue(all(not x["constant_correction_feasible"] for x in summary["by_temperature"]))

    def test_plant_proxies_all_labelled_nonscoring(self):
        proxies = D.inlet_proxies(self.grid)
        self.assertEqual(len(proxies), 5)
        self.assertEqual({x["metric_id"] for x in proxies}, set(D.INLETS))
        self.assertTrue(all("not a re-scored case" in x["interpretation"] for x in proxies))
        self.assertEqual(sum(x["source_only_within_20pct"] for x in proxies), 5)


if __name__ == "__main__":
    unittest.main()
