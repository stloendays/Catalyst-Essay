"""Audit behavior under controlled perturbations; intentionally no model re-fitting."""
import csv
import tempfile
import unittest
from pathlib import Path
import audit_industrial as A

class EvidenceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary, cls.rows = A.audit()

    def test_registered_counts(self):
        self.assertEqual(len(self.rows), 64)
        self.assertEqual(sum(x["unchanged_verdict"] == "PASS" for x in self.rows), 32)
        self.assertEqual(sum(self.summary["failure_groups"].values()), 32)

    def test_source_all_rows_pinned(self):
        self.assertEqual(len(set(x["metric_id"] for x in self.rows)), 64)
        self.assertTrue(all(x["source_row_ids"] or x["metric_id"] == "V01" for x in self.rows))

    def test_replay_against_committed_snapshot(self):
        result = A.verify_recomputed(self.rows_from_csv(), A.V12 / "results_metrics.csv")
        self.assertEqual(result["same_verdicts"], 64)

    def rows_from_csv(self):
        return A.rows(A.V12 / "results_metrics.csv")

    def test_bad_rule_is_rejected(self):
        with self.assertRaises(ValueError):
            A.independent_judge("unknown:10", "1.0", 1.0, None, None, {})

    def test_no_tolerance_relaxation(self):
        self.assertFalse(A.independent_judge("rel:0.15", "120", 100.0, None, None, {}))
        self.assertTrue(A.independent_judge("rel:0.15", "115", 100.0, None, None, {}))
        self.assertFalse(A.independent_judge("factor:2", "2.001", 1.0, None, None, {}))

    def test_no_hidden_reclassification(self):
        fail_ids = {x["metric_id"] for x in self.rows if x["unchanged_verdict"] == "FAIL"}
        assigned = {k for v in A.GROUPS.values() for k in v["ids"].split()}
        self.assertEqual(fail_ids, assigned)

    def test_csv_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            A.emit_report(self.summary, self.rows, Path(tmp))
            report = Path(tmp, "REPORT.md").read_text()
            self.assertIn("32/64", report)
            self.assertIn("not proven cause", report)
            self.assertEqual(len(A.rows(Path(tmp, "triage_64.csv"))), 64)

if __name__ == "__main__":
    unittest.main()
