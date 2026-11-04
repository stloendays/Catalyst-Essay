"""Source-matched experimental holdout + unfrozen structural sensitivity tests."""
from __future__ import annotations
import math
import unittest
from experimental_holdout import (ACS,SA,comparable_tracks,mass_ghsv,model_x,
                                  fitted_beta,evaluate_holdouts)
from conditional_stress import kinetic_states,shift_selectivity,methanol_sty_under_selectivity,SCENARIOS


class SourceAlignedTests(unittest.TestCase):
    def test_mass_ghsv_cannot_mix_volumetric_and_mass_normalized(self):
        self.assertEqual(mass_ghsv("12 NL/g/h"),12)
        self.assertEqual(mass_ghsv("10 NL/g/h"),10)
        self.assertIsNone(mass_ghsv("18000 h-1"))
        self.assertIsNone(mass_ghsv("not reported"))

    def test_source_pretreat_explicitly_prevents_acs_collapsing_states(self):
        cohorts,_=comparable_tracks()
        assert len(cohorts)==9,(len(cohorts),[(r["doi"],r["catalyst"]) for r in cohorts])
        acs=[c for c in cohorts if c["doi"]==ACS]
        sa=[c for c in cohorts if c["doi"]==SA]
        self.assertEqual(len(acs),2)
        self.assertEqual(len(sa),7)
        self.assertEqual({c["pretreatment"] for c in acs},
                         {"reduction_250C_paper_table","reduction_500C_paper_table"})
        self.assertEqual(len([r for c in acs for r in c["holdouts"]]),5)
        self.assertEqual(len([r for c in sa for r in c["holdouts"]]),7)
        for c in cohorts:
            self.assertGreater(min(g for g,_ in c["holdouts"]),c["ghsv_anchor"])

    def test_source_holdout_anchor_and_measured_selectivity_not_synthetic(self):
        rows,tracks,_=evaluate_holdouts()
        self.assertEqual(len(rows),12)
        self.assertEqual(len({r["doi"] for r in rows}),2)
        pairs={r["catalyst"]:r for r in rows if r["doi"]==SA and r["T_C"]==300 and r["P_bar"]==40 and r["H2_CO2"]==3}
        self.assertEqual(len(pairs),4)
        x=pairs["inni3c0.5/m-zro2"]
        self.assertAlmostEqual(x["measured_X_anchor"],0.112)
        self.assertAlmostEqual(x["measured_X_holdout"],0.085)
        self.assertAlmostEqual(x["measured_SMeOH_anchor"],0.854)
        self.assertAlmostEqual(x["measured_SMeOH_holdout"],0.879)
        # Same source paper reports 11.6% feed-equilibrium conversion; use it
        # separately from the original repo equilibrium.
        self.assertAlmostEqual(x["X_pred_beta1_paper_eq"],0.094459340771462,places=12)
        y=pairs["inni3c0.5/sio2"]
        self.assertAlmostEqual(y["X_pred_beta1_paper_eq"],0.0132576036876694,places=12)
        self.assertAlmostEqual(y["measured_X_holdout"],0.022)

    def test_generalized_kinetic_model_preserves_exact_anchor(self):
        self.assertAlmostEqual(model_x(.2,.6,1,1),.2,places=15)
        self.assertAlmostEqual(model_x(.2,.6,2,1),.6*(1-(1-.2/.6)**2),places=14)
        for beta in (.5,.75,1,1.25):
            states=kinetic_states(.2,.6,beta)
            self.assertTrue(any(m==1 and x==.2 for m,x,_ in states))
            self.assertTrue(all(0<x<.6 for _,x,_ in states))
        self.assertEqual(kinetic_states(.65,.6,1),[(1.0,.65,"above_feed_eq_only_measured")])

    def test_paper_holdout_beta_is_in_sample_not_new_validation(self):
        x0=.112
        xt=.085
        eq=.116
        beta=fitted_beta(x0,xt,eq,.5)
        self.assertIsNotNone(beta)
        self.assertAlmostEqual(model_x(x0,eq,.5,beta),xt,places=13)
        self.assertNotAlmostEqual(beta,1,places=2)

    def test_selectivity_changes_are_closed_and_anchored(self):
        self.assertEqual(shift_selectivity(.65,.01,.34,1,-.05),(.65,.01,.34))
        for m in (.25,.5,2,10):
            for gamma in (-.15,-.05,.05):
                s,co,ch4=shift_selectivity(.65,.01,.34,m,gamma)
                self.assertTrue(0<s<=1 and co>=0 and ch4>=0)
                self.assertAlmostEqual(s+co+ch4,1,places=13)
        sm,co,ch4=shift_selectivity(1.,0.,0.,2,-.05)
        self.assertAlmostEqual(sm+co+ch4,1,places=13)

    def test_methanol_productivity_tracks_methanol_not_co2_conversion_only(self):
        self.assertAlmostEqual(methanol_sty_under_selectivity(2.0,.2,.8,.3,.8,2),
                               2.0*.3/(.2*2),places=14)
        self.assertAlmostEqual(methanol_sty_under_selectivity(2.0,.2,.8,.3,.4,2),
                               2.0*.3/(.2*2)*(.4/.8),places=14)
        self.assertAlmostEqual(methanol_sty_under_selectivity(2.0,.2,.8,.3,.95,2),
                               2.0*.3/(.2*2)*(.95/.8),places=14)
        self.assertAlmostEqual(methanol_sty_under_selectivity(2.0,.2,.8,.2,.8,1),
                               2.0,places=14)
        with self.assertRaises(ValueError):
            methanol_sty_under_selectivity(2,.2,.8,.3,-.1,2)

    def test_stress_scenarios_are_distinct_unfrozen_conditions(self):
        self.assertEqual(len(SCENARIOS),10)
        self.assertEqual(SCENARIOS[0],("reference",1.0,0.0,None))
        self.assertTrue(all(x[1]>0 and (x[3] is None or x[3]>0) for x in SCENARIOS))


if __name__=="__main__":
    unittest.main()
