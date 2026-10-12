"""Frozen cohort and thermodynamic isolation tests for Hou Ar feed correction."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import recheck_source_argon as R


class HouArgonFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=R.J.candidates()
        cls.hou=R.hou_candidates(cls.base)

    def test_exact_original_comparison_scope_and_labels(self):
        self.assertEqual(len(self.base),310)
        self.assertEqual(self.base.group.nunique(),40)
        self.assertEqual((len(self.hou),self.hou.group.nunique()),(6,2))
        bare=self.hou[self.hou.entry.map(R.is_bare)]
        decorated=self.hou[~self.hou.entry.map(R.is_bare)]
        self.assertEqual((len(bare),len(decorated)),(3,3))
        np.testing.assert_allclose(bare.y_co2.to_numpy(),.2)
        np.testing.assert_allclose(decorated.y_co2.to_numpy(),1/6,atol=2e-10)
        self.assertTrue(all(self.hou.sty_printed))
        self.assertEqual(self.hou.doi.nunique(),1)
        self.assertTrue(np.allclose(self.hou.h2_co2,4.))

    def test_source_verified_H2_CO2_Ar_fraction(self):
        self.assertEqual(R.FEED_RATIO,(4.,1.,1.))
        self.assertAlmostEqual(R.Y_CO2_SOURCE,1/6,places=14)
        self.assertAlmostEqual(R.ARGON_PR_CRIT[0],150.687,places=3)
        self.assertAlmostEqual(R.ARGON_PR_CRIT[1],48.63,places=2)
        self.assertAlmostEqual(R.ARGON_PR_CRIT[2],-.002,places=5)
        self.assertNotIn("Ar",R.G.PR_CRIT)

    def test_real_argon_lab_equilibrium_separate_from_N2_standin(self):
        bare=self.hou[self.hou.entry.map(R.is_bare)].iloc[0]
        y=R.Y_CO2_SOURCE
        old=R.J.feed_eq(float(bare.h2_co2),.2,float(bare.T_C),float(bare.P_bar))
        n2=R.J.feed_eq(float(bare.h2_co2),y,float(bare.T_C),float(bare.P_bar))
        self.assertTrue(0<old[0]<1 and 0<n2[0]<1)
        self.assertNotIn("Ar",R.G.PR_CRIT)
        with R.isolated_argon_solver():
            ar=R.J.feed_eq(float(bare.h2_co2),y,float(bare.T_C),float(bare.P_bar))
            self.assertNotIn("Ar",R.G.PR_CRIT)
            self.assertTrue(0<ar[0]<1)
            self.assertGreater(ar[1],0)
        self.assertNotIn("Ar",R.G.PR_CRIT)
        self.assertNotEqual(old,n2)
        self.assertNotEqual(n2,ar)

    def test_argon_species_and_function_restored_on_error(self):
        baseline=R.J.feed_eq
        with self.assertRaisesRegex(ValueError,"forced isolation"):
            with R.isolated_argon_solver():
                self.assertIs(R.J.feed_eq,R.argon_equilibrium)
                raise ValueError("forced isolation")
        self.assertIs(R.J.feed_eq,baseline)
        self.assertNotIn("Ar",R.G.PR_CRIT)

    def test_bare_lab_measured_STY_not_recomputed_from_space_velocity(self):
        bare=self.hou[self.hou.entry.map(R.is_bare)]
        values={r.entry:float(r.STY) for r in bare.itertuples()}
        self.assertAlmostEqual(values["SI Table S5 row In2O3-HM"],.12)
        self.assertAlmostEqual(values["SI Table S5 row In2O3-NP"],.15)
        self.assertAlmostEqual(values["SI Table S5 row In2O3-NS"],.17)
        self.assertAlmostEqual(float(bare.loc[bare.entry.str.endswith("NS"),"X"].iloc[0]),.0915)
        self.assertAlmostEqual(float(bare.loc[bare.entry.str.endswith("HM"),"X"].iloc[0]),.0543)

    def test_prior_original_champion_leaderboard_is_unchanged(self):
        bare=self.hou[self.hou.entry.map(R.is_bare)]
        lab=bare.loc[bare.STY.idxmax()]
        self.assertIn("In2O3-NS",lab.catalyst)
        self.assertEqual(len(bare.catalyst_key.unique()),3)
        self.assertEqual(len(R.VARIANTS),3)
        self.assertEqual(len(R.E.CAPS)*len(R.E.INLETS)*len(R.E.LOADING_MAX),56)


if __name__=="__main__":
    unittest.main()
