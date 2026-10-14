"""Source correctness + physical reasonableness + a usable closed process.

No requirement to reproduce all molecular simulations or force exact plant
outputs. These tests protect the equations and operating scope, not a score.
"""
import unittest
import numpy as np
from model import PARAMS, State, R, CP_IDEAL, fractions, interactions, compression
from loop import solve, Settings
from run_research import first_separator


class SourceAndPhysics(unittest.TestCase):
    def test_source_s27_exact_columns(self):
        self.assertEqual(PARAMS['PR']['H2'],[1.120,-.0070,.00001382,.931])
        self.assertEqual(PARAMS['PR']['N2'],[-.696,.0063,-.00001064,.863])
        self.assertEqual(PARAMS['PR']['Ar'],[2.172,-.0112,.00001641,.614])
        self.assertNotIn('CH4',PARAMS['PR'])
        self.assertIn('O2',PARAMS['PR'])

    def test_kelvin_and_symmetric_interactions(self):
        k,dk=interactions(298.15)
        np.testing.assert_allclose(k,k.T)
        self.assertAlmostEqual(k[0,4],-.696+.0063*298.15-.00001064*298.15**2)
        self.assertAlmostEqual(k[1,4],.26145709895,places=8)
        self.assertEqual(k[2,4],0.)
        self.assertAlmostEqual(interactions(298.15,.2)[0][2,4],.2)
        self.assertTrue(np.all(np.diag(k)==0))

    def test_not_pcsaft_coefficients_in_pr(self):
        k,_=interactions(298.15)
        a=PARAMS['PC_SAFT_reference_only']['H2']
        self.assertNotAlmostEqual(k[1,4],a[0]+a[1]*298.15+a[2]*298.15**2)

    def test_temperature_derivative(self):
        k,dk=interactions(294.15)
        fd=(interactions(294.151)[0]-interactions(294.149)[0])/.002
        np.testing.assert_allclose(fd,dk,atol=1e-10)

    def test_residual_enthalpy_keeps_dk_dT(self):
        T,P=294.15,18.02e6;z=np.array([.20,.50,.07,.03,.20])
        st=State(T,P);_,_,h=st.properties(z,'vapor')
        hdep=h-float(z@CP_IDEAL)*(T-298.15)
        gp=float(z@State(T+.001,P).properties(z,'vapor')[1])
        gm=float(z@State(T-.001,P).properties(z,'vapor')[1])
        derivative=-R*T*T*(gp-gm)/.002
        self.assertAlmostEqual(hdep,derivative,delta=1e-4)

    def test_first_stage_flash_material_and_fugacity_balance(self):
        st=State(294.15,18.02e6);z=np.array([.196,.4799,.0943,.0331,.1967])
        out=st.flash(z,stability=True)
        self.assertTrue(0<out.beta<1)
        self.assertEqual(out.phase,'two_phase')
        np.testing.assert_allclose(z,out.beta*out.y+(1-out.beta)*out.x,atol=1e-10)
        self.assertLess(out.residual,2e-8)
        self.assertLess(out.gibbs_improvement,0.)
        self.assertAlmostEqual(sum(out.x),1.,places=9)
        self.assertAlmostEqual(sum(out.y),1.,places=9)

    def test_si_prediction_direction_without_exact_matching_gate(self):
        zero,si=first_separator()
        self.assertLess(si['gas_NH3_pct'],zero['gas_NH3_pct'])
        self.assertLess(si['gas_NH3_abs_relative_error_pct'],zero['gas_NH3_abs_relative_error_pct'])
        self.assertNotAlmostEqual(si['gas_NH3_pct'],8.51,places=2)

    def test_lean_gas_remains_single_phase(self):
        r=State(294.15,18e6).flash([.24,.73,.02,.009,.001])
        self.assertEqual(r.beta,1.)
        self.assertEqual(r.phase,'single_vapor')

    def test_invalid_inputs_fail_clearly(self):
        for z in ([.5,.5],[-1,1,1,1,1],[0,0,0,0,0]):
            with self.assertRaises(ValueError):fractions(z)
        with self.assertRaises(ValueError):State(700.,18e6)
        with self.assertRaises(ValueError):State(300.,-1)
        with self.assertRaises(ValueError):Settings(purge=0)
        with self.assertRaises(ValueError):Settings(conversion=1.1)

    def test_work_units_and_efficiency(self):
        v=compression([2000,6000,10,5,0],298.15,3.23e6,18.2e6)
        self.assertGreater(v['shaft_MW'],0)
        self.assertAlmostEqual(v['shaft_MW']*.75,v['reversible_MW'],places=9)
        with self.assertRaises(ValueError):compression([1,3,0,0,0],300,2e6,1e6)


class OperableLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=solve()

    def test_full_loop_mass_closure_and_positive_flow(self):
        r=self.base
        self.assertLess(r['component_residual_rel_fresh'],1e-8)
        self.assertLess(r['fixed_point_residual_rel_fresh'],1e-8)
        for key in ('reactor_feed_kmol_h','purge_kmol_h','sep1_liquid_kmol_h','sep2_liquid_kmol_h'):
            self.assertTrue(min(r[key])>=0)
        self.assertTrue(0<r['NH3_product_recovery_fraction']<1)

    def test_stability_screen_performed(self):
        self.assertEqual(len(self.base['final_tpd_minima']),2)
        self.assertGreater(min(self.base['final_tpd_minima']),-1e-6)

    def test_initial_guess_does_not_set_production(self):
        other=solve(initial=np.array(self.base['reactor_feed_kmol_h'])*1.15)
        self.assertAlmostEqual(other['liquid_NH3_tpd'],self.base['liquid_NH3_tpd'],places=4)
        self.assertNotAlmostEqual(other['liquid_NH3_tpd'],1500.24,places=1)

    def test_purge_tradeoff_is_not_fitted(self):
        more=solve(Settings(purge=.06))
        self.assertGreater(more['H2_purge_kg_h'],self.base['H2_purge_kg_h'])
        self.assertLess(more['liquid_NH3_tpd'],self.base['liquid_NH3_tpd'])

    def test_colder_stage_changes_energy_and_composition(self):
        cold=solve(Settings(T2=263.15))
        self.assertLess(cold['feed_NH3_molpct'],self.base['feed_NH3_molpct'])
        self.assertGreater(cold['second_stage_refrigeration_MW_scenario'],self.base['second_stage_refrigeration_MW_scenario'])

    def test_pressure_work_changes_without_fake_reactor_kinetics(self):
        low=solve(Settings(P_reactor=18.18e6))
        self.assertLess(low['recycle_shaft_MW_scenario'],self.base['recycle_shaft_MW_scenario'])
        self.assertAlmostEqual(low['liquid_NH3_tpd'],self.base['liquid_NH3_tpd'],places=5)

    def test_missing_methane_pair_is_sensitivity_not_source(self):
        x=solve(Settings(methane_k=.2))
        self.assertEqual(x['settings']['methane_k'],.2)
        self.assertNotAlmostEqual(x['feed_inerts_molpct'],self.base['feed_inerts_molpct'],places=2)

    def test_zero_second_liquid_is_a_valid_operating_state(self):
        x=solve(Settings(T2=283.15,conversion=.325,purge=.06))
        self.assertLess(x['component_residual_rel_fresh'],1e-8)
        self.assertGreaterEqual(x['second_stage_refrigeration_MW_scenario'],0.)

    def test_economic_metric_has_a_declared_scope(self):
        x=self.base
        calculated=(x['compression_shaft_MW_scenario']+x['second_stage_refrigeration_MW_scenario'])/(x['liquid_NH3_tpd']/24)*50
        self.assertAlmostEqual(calculated,x['utility_USD_per_t_scenario'],places=9)
        self.assertIn('no new Fe/Ru kinetics',x['reactor_scope'])
        self.assertIn('no reactor heat',x['energy_scope'])


if __name__=='__main__':unittest.main()
