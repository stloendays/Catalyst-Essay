"""No fitted source pressure overlap and no false Fe-first audit pass.

Math and protocol checks must succeed regardless of which technology wins. A
positive Ru−Fe margin is a *scientific result*, not a CI pass requirement.
"""
from __future__ import annotations
import unittest
from dataclasses import replace
from pathlib import Path
import source_domains as S


class SourceWindowTests(unittest.TestCase):
    def test_reported_pressure_intervals_are_disjoint(self):
        f=S.EXPERIMENTAL["Fe"];r=S.EXPERIMENTAL["Ru"]
        self.assertAlmostEqual(f[0],150.97425,places=5)
        self.assertAlmostEqual(f[1],313.09425,places=5)
        self.assertEqual(r,(50.,100.))
        self.assertGreater(f[0],r[1])

    def test_kinetic_temperature_intersection_is_not_full_domain(self):
        self.assertEqual(S.COMMON_T,(370.,460.))
        self.assertTrue(S.ensure_source_domain("Fe",430.,220.))
        self.assertFalse(S.ensure_source_domain("Ru",430.,220.))
        self.assertTrue(S.ensure_source_domain("Ru",445.,100.))
        self.assertFalse(S.ensure_source_domain("Fe",445.,100.))
        self.assertFalse(S.ensure_source_domain("Ru",470.,100.))

    def test_equal_product_and_no_undisclosed_inert_cap(self):
        self.assertEqual(S.PRICE.product_tpd,1500.)
        self.assertEqual(S.PRICE.max_bed_m3,90.)
        self.assertEqual(S.MAX_INERT_PCT,15.)
        self.assertEqual(S.PRICE.ru_recovery,.90)
        self.assertEqual(S.PRICE.H2_USD_kg,3.)
        self.assertEqual(S.PRICE.N2_USD_kg,.06)

    def test_price_counterfactual_does_not_reprice_bed_by_hand(self):
        changed=replace(S.PRICE,Ru_USD_kg_metal=0.)
        self.assertEqual(changed.Ru_USD_kg_metal,0.)
        self.assertEqual(changed.Fe_USD_kg_catalyst,S.PRICE.Fe_USD_kg_catalyst)
        self.assertEqual(changed.equipment_rate,S.PRICE.equipment_rate)

    def test_purge_and_conversion_sampling_are_symmetric_in_constraints(self):
        self.assertEqual(set(S.ADDITIONS),{"Fe","Ru"})
        for metal,points in S.ADDITIONS.items():
            self.assertTrue(all(S.EXPERIMENTAL[metal][0]<=x<=S.EXPERIMENTAL[metal][1] for x in points["P"]))
            self.assertTrue(all(0<x<1 for x in points["X"]))
            self.assertTrue(all(0<x<1 for x in points["purge"]))
            self.assertTrue(all(-30<x<30 for x in points["T2"]))

    def test_eligible_denies_inerts_outside_cap(self):
        fake={"eligible":True,"bed_m3":30.,"passes_inert_bound":False}
        self.assertIsNone(S.repriced(fake,{},S.PRICE))

    def test_eligible_denies_equipment_outside_cap(self):
        fake={"eligible":True,"bed_m3":120.,"passes_inert_bound":True}
        self.assertIsNone(S.repriced(fake,{},S.PRICE))

    def test_input_catalyst_name_and_pfd_preserved(self):
        path=Path(__file__).resolve().parents[1]/"nh3_kinetic_cost_coupling_v1"/"kinetic_bridge.py"
        s=path.read_text(encoding="utf-8")
        self.assertIn("3.2 wt% Ru/C",s)
        self.assertIn("Rossetti",s)
        self.assertIn("Dyson",s)


if __name__=="__main__":
    unittest.main()
