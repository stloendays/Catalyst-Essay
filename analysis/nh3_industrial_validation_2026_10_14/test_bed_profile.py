"""Check source-aligned S-200 bed-local misfit without kinetic refitting."""
import unittest
import diagnose_bed_profile as D

class BedProfiles(unittest.TestCase):
    def test_bed_specific_mismatch_reproduced(self):
        data = D.diagnose()
        self.assertEqual(len(data), 4)
        for group in ("LIU919A", "LIU919B"):
            one = next(x for x in data if x["case"] == group and x["bed"] == 1)
            two = next(x for x in data if x["case"] == group and x["bed"] == 2)
            self.assertGreater(one["required_volume_over_installed"], 1.5)
            self.assertLess(abs(two["required_volume_over_installed"] - 1), 0.1)

if __name__ == "__main__":
    unittest.main()
