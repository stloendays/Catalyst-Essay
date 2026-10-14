"""Physics, accounting and independent fixed-bed feedback checks."""
import importlib.util,math,os,sys,unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
import kinetic_bridge as K
import coupling as C
import economics as E

ROOT=Path(__file__).resolve().parents[2]

class MeasuredReactor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed=np.array([.23,.61,.08,.03,.05])*28000
    def test_rate_units_against_existing_repository_implementation(self):
        p=ROOT/K.RATE_SOURCE
        if not p.exists():
            if os.environ.get('GITHUB_ACTIONS'):self.fail('Source kinetics.py missing in GitHub checkout')
            self.skipTest('Upstream source module is not bundled in this local standalone package')
        spec=importlib.util.spec_from_file_location('legacy_kinetic_reference',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for T in [673.15,698.15,723.15]:
            for P in [100.,188.,220.]:
                f=self.feed;yn,yh,ya=(f/f.sum())[[0,1,4]]
                self.assertAlmostEqual(K.rate_m3('Fe',T,P,f),float(module.rate_fe_dyson_simon(T,P,yn,yh,ya,per='m3')),places=9)
                self.assertAlmostEqual(K.rate_m3('Ru',T,P,f),float(module.rate_ru_rossetti(T,P,yn,yh,ya))*590,places=9)
    def test_common_equilibrium_and_no_negative_feasible_rate(self):
        f=self.feed;T=698.15;P=188
        eq=K.equilibrium_extent(T,P,f)
        for cat in ['Fe','Ru']:
            self.assertGreater(float(K.rate_m3(cat,T,P,f)),0)
            self.assertAlmostEqual(float(K.affinity_ratio(T,P,f+K.NU*eq)),1.,places=8)
            self.assertLess(abs(float(K.rate_m3(cat,T,P,f+K.NU*eq))),1e-6)
            bad=K.size_bed(cat,T,P,f,eq*1.01)
            self.assertFalse(bad['feasible'])
    def test_forward_inverse_plug_flow(self):
        for cat in ['Fe','Ru']:
            xi=.2*2*self.feed[0]
            b=K.size_bed(cat,698.15,188,self.feed,xi)
            r=K.forward_bed(cat,698.15,188,self.feed,b['bed_m3'])
            self.assertAlmostEqual(r['extent_kmol_h']/xi,1.,places=6)
            self.assertAlmostEqual(r['X_N2'],.2,places=6)
    def test_activity_and_equal_throughput_scaling(self):
        f=self.feed;xi=.2*2*f[0]
        for cat in ['Fe','Ru']:
            a=K.size_bed(cat,698.15,188,f,xi)
            b=K.size_bed(cat,698.15,188,f,xi,activity=2.)
            c=K.size_bed(cat,698.15,188,2*f,2*xi)
            self.assertAlmostEqual(a['bed_m3']/b['bed_m3'],2.,places=10)
            self.assertAlmostEqual(c['bed_m3']/a['bed_m3'],2.,places=10)
    def test_quadrature_convergence(self):
        for cat in ['Fe','Ru']:
            a=K.size_bed(cat,698.15,188,self.feed,.22*2*self.feed[0],n=48)
            b=K.size_bed(cat,698.15,188,self.feed,.22*2*self.feed[0],n=128)
            self.assertLess(abs(a['bed_m3']/b['bed_m3']-1),1e-5)
    def test_formulation_and_domain_labels(self):
        self.assertEqual(K.RU_WT,.032)
        self.assertEqual(K.DENSITY['Ru'],590.)
        self.assertTrue(K.validity('Ru',698.15,100,self.feed)['rate_P_inside_source_range'])
        self.assertFalse(K.validity('Ru',698.15,220,self.feed)['rate_P_inside_source_range'])
        self.assertTrue(K.validity('Fe',698.15,220,self.feed)['rate_P_inside_source_range'])
        self.assertFalse(K.validity('Fe',698.15,100,self.feed)['rate_P_inside_source_range'])
    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):K.rate_m3('Os',698.15,188,self.feed)
        with self.assertRaises(ValueError):K.rate_m3('Fe',300,188,self.feed)
        with self.assertRaises(ValueError):K.forward_bed('Ru',698.15,188,self.feed,-1)
        with self.assertRaises(ValueError):K.rate_m3('Fe',698.15,188,self.feed,activity=0)
    def test_reaction_heat_is_exothermic_per_mol_nh3(self):
        self.assertTrue(-65000<K.hot_heat_per_mol_NH3(698.15)<-40000)

class KineticColdEconomicChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings=C.cold_settings(188.,.2,0.,.03)
        cls.raw=C.cold.solve(cls.settings,check_stability=False)
        cls.record=C.flow_record(cls.settings,cls.raw)
    def test_equal_actual_product_not_equal_raw_feed(self):
        r=self.record
        self.assertAlmostEqual(r['products_kmol_h'][4]*C.MW[4]*24/1000,1500.,places=7)
        self.assertLess(r['component_residual_rel_fresh'],1e-7)
        self.assertLess(r['flash_log_fugacity_error'],1e-7)
    def test_forward_recycle_ignores_prescribed_conversion(self):
        for cat in ['Fe','Ru']:
            b=K.size_bed(cat,698.15,188,self.record['feed_kmol_h'],self.record['extent_kmol_h'])
            r=C.forward_closed_loop(cat,425.,replace(self.settings,conversion=.77),b['bed_m3'],
                self.record['scale_to_equal_product'],np.array(self.record['feed_kmol_h'])*.8)
            self.assertFalse(r['conversion_used_as_input'])
            self.assertAlmostEqual(r['calculated_X_N2'],.2,places=6)
            self.assertLess(abs(r['calculated_NH3_tpd']-1500),.02)
            self.assertLess(r['material_residual_relative'],1e-6)
            self.assertTrue(all(v>-1e-6 for v in r['phase_stability_minima']))
    def test_no_double_counted_feed_loss(self):
        for cat in ['Fe','Ru']:
            q=E.evaluate(cat,30,188,self.record)
            self.assertLess(abs(q['feed_cost_decomposition_residual_USD_t']),1e-4)
            self.assertAlmostEqual(q['modeled_loop_cost_USD_t']-q['decision_relevant_cost_USD_t'],q['stoichiometric_feed_USD_t'],places=8)
            self.assertGreater(q['excess_feed_USD_t'],0)
    def test_inventory_recovers_metal_not_support(self):
        f=E.EconomicSettings()
        a=E.evaluate('Ru',30,188,self.record,replace(f,ru_recovery=0.))
        b=E.evaluate('Ru',30,188,self.record,replace(f,ru_recovery=1.))
        self.assertGreater(a['inventory_USD_t'],b['inventory_USD_t'])
        self.assertAlmostEqual(a['support_USD_t'],b['support_USD_t'],places=10)
        self.assertGreater(b['ru_metal_USD_t'],0)
    def test_perfect_recovery_still_pays_capital_carry(self):
        self.assertAlmostEqual(E.annual_inventory_factor(.12,10,25,1.),.12,places=12)
        self.assertAlmostEqual(E.annual_inventory_factor(0.,10,25,1.),0.,places=12)
    def test_fair_pressure_and_production_normalisation(self):
        s=C.cold_settings(100,.2,0,.03)
        r=C.flow_record(s,self.raw)
        self.assertAlmostEqual(r['makeup_delivery_pressure_bar'],94.0)
        self.assertNotEqual(r['makeup_delivery_pressure_bar'],182.0)
        self.assertGreater(self.record['compressor_shaft_MW_by_service'][0],r['compressor_shaft_MW_by_service'][0])
    def test_same_finite_volume_cap_for_both_candidates(self):
        for cat in ['Fe','Ru']:
            limited=E.EconomicSettings(max_bed_m3=.01)
            r=C.candidate(cat,425.,188.,self.settings,self.record,limited)
            self.assertFalse(r['feasible'])
            self.assertIn('shared_90m3_cap',r['reason'])
    def test_formulation_cost_changes_with_kinetics(self):
        fe=C.candidate('Fe',425,188,self.settings,self.record)
        ru=C.candidate('Ru',425,188,self.settings,self.record)
        self.assertTrue(fe['feasible']);self.assertTrue(ru['feasible'])
        self.assertNotAlmostEqual(fe['bed_m3'],ru['bed_m3'])
        self.assertNotAlmostEqual(fe['inventory_USD_t'],ru['inventory_USD_t'])
    def test_power_and_capital_units(self):
        self.assertEqual(E.compressor_capex(0),0)
        self.assertGreater(E.compressor_capex(2.),E.compressor_capex(1.))
        self.assertGreater(E.vessel_cost(30,220),E.vessel_cost(30,100))
        self.assertAlmostEqual(E.crf(0,25),.04)
        with self.assertRaises(ValueError):E.EconomicSettings(H2_USD_kg=-1)

if __name__=='__main__':unittest.main()
