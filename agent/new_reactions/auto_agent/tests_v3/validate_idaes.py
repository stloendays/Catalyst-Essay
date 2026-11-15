"""Live IDAES cross-checks; missing env/solver skips explicitly, model errors fail.

Reference throughput 1 t/s. Numerical expected values are from UO-2.0 NIST
ideal-gas/ideal-Raoult methods, not supplied to the IDAES solver.
"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unitops as u
import idaes_adapter as adapter

DIFFERENCES=[]


class Protocol(unittest.TestCase):
    def test_unmapped_and_warnings(self):
        self.assertFalse(adapter.idaes_check({'physics':{'units':[{'name':'offsites','type':'offsites'}]}})['ok'])
        ref={'physics':{'units':[dict(name='c',type='compressor',inlet_kmol_per_t={'Ar':1},
              T_in_K=300,P_in_bar=1,P_out_bar=2,power_GJ_per_t=1.)]}}
        with patch.object(adapter,'run',return_value=dict(ok=True,solver_status='optimal',units=[dict(name='c',power_GJ_per_t=2.)])):
            out=adapter.idaes_check(ref)
        self.assertEqual(out['comparisons'][0]['relative_difference'],.5)
        self.assertEqual(out['status'],'WARNING')

    def test_errors(self):
        with patch.object(adapter.subprocess,'run',side_effect=adapter.subprocess.TimeoutExpired('idaes',300)):
            self.assertIn('timeout',adapter.run({'units':[]})['error'])
        with patch.dict(adapter.os.environ,{'IDAES_PYTHON':str(Path(__file__).with_name('missing_python.exe'))}):
            self.assertFalse(adapter.run({'units':[]})['ok'])


class IDAES(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        probe=adapter.run({'units':[]})
        if not probe.get('ok'):
            missing=('No such file','cannot find','not found','ModuleNotFoundError','ipopt unavailable','Unable to create process')
            if any(x in probe.get('error','') for x in missing): raise unittest.SkipTest('IDAES env/solver missing: '+probe['error'])
            raise RuntimeError(probe)

    def solve(self,spec):
        out=adapter.run({'units':[spec]})
        self.assertTrue(out.get('ok'),out)
        return out['units'][0]

    def compare(self,name,a,b):
        diff=abs(a-b)/max(abs(b),1e-10)
        DIFFERENCES.append(dict(check=name,harness=a,idaes=b,relative_difference=diff))
        print(f'{name}: UO2={a:.10g}, IDAES={b:.10g}, difference={100*diff:.6f}%')
        self.assertLessEqual(diff,.02)

    def test_compressor(self):
        # Monatomic argon Cp=20.786, gamma=Cp/(Cp-R), single isentropic stage.
        gamma=20.786/(20.786-u.R)
        expected=u.compressor(1,300,1,2,eta_isentropic=.8,max_stage_ratio=10,gamma=gamma)
        got=self.solve(dict(name='c',type='Compressor',feed={'Ar':1},T_in_K=300,P_in_bar=1,P_out_bar=2,eta_isentropic=.8))
        self.compare('compressor_work',expected['power_GJ_per_t'],got['power_GJ_per_t'])
        self.compare('compressor_T',expected['T_out_K'],got['T_out_K'])

    def test_heater(self):
        expected=u.enthalpy_stream({'N2':1},450,300)['enthalpy_GJ_per_t']
        got=self.solve(dict(name='h',type='Heater',feed={'N2':1},T_in_K=300,T_out_K=450,P_in_bar=1))
        self.compare('heater_duty',expected,got['heat_duty_GJ_per_t'])

    def test_flash(self):
        feed={'H2O':1,'N2':1}; expected=u.flash_pt(feed,350,1)
        got=self.solve(dict(name='f',type='Flash',feed=feed,T_in_K=350,T_out_K=350,P_in_bar=1))
        self.compare('flash_vapor_fraction',expected['vapor_fraction'],got['vapor_fraction'])
        for s in feed:
            self.compare('flash_vapor_'+s,expected['vapor_kmol_per_t'][s],got['vapor_kmol_per_t'][s])

    def test_equilibrium(self):
        nu=[{'N2':-1,'H2':-3,'NH3':2}]; feed={'N2':1,'H2':3}
        expected=u.equilibrium_reactor(feed,nu,700,100)
        got=self.solve(dict(name='r',type='EquilibriumReactor',feed=feed,T_in_K=700,T_out_K=700,P_in_bar=100,nu_list=nu))
        self.compare('equilibrium_conversion',expected['extents_kmol_per_t'][0],1-got['outlet_kmol_per_t']['N2'])
        self.compare('equilibrium_duty',expected['heat_duty_GJ_per_t'],got['heat_duty_GJ_per_t'])

    def test_other_units(self):
        got=self.solve(dict(name='s',type='Separator',feed={'H2':1,'N2':1},T_in_K=400,P_in_bar=1,split_fraction={'H2':.8,'N2':.1}))
        self.assertAlmostEqual(got['outlet_kmol_per_t']['H2'],.8,places=5)
        got=self.solve(dict(name='m',type='Mixer',feed={'Ar':1},T_in_K=300,P_in_bar=1,
                            inlets=[dict(feed={'Ar':1},T_in_K=300,P_in_bar=1),dict(feed={'Ar':1},T_in_K=400,P_in_bar=1)]))
        self.assertAlmostEqual(got['T_out_K'],350,places=3)
        nu=[{'H2':-1,'O2':-.5,'H2O':1}]
        got=self.solve(dict(name='s',type='StoichiometricReactor',feed={'H2':1,'O2':1},T_in_K=400,T_out_K=400,P_in_bar=1,
                            nu_list=nu,extents_kmol_per_t=[.1]))
        self.assertAlmostEqual(got['outlet_kmol_per_t']['H2O'],.1,places=5)


class Properties(unittest.TestCase):
    def test_independent_properties(self):
        property_cross_check()


def property_cross_check():
    """Independent property source (2026-11-15): the IDAES runs reuse the harness NIST table, so they check solvers and
    equations, not data. Compare the table with the `chemicals`/`thermo` database: 298 -> 700 K gas enthalpy within 2 %,
    formation enthalpy within 1.5 kJ/mol. This found the constant-Cp methanol fallback (26 % low at 700 K)."""
    import json, os, subprocess
    py = os.environ.get("IDAES_PYTHON", r"D:\Tools\idaes-env\Scripts\python.exe")
    if not os.path.exists(py):
        print("property cross-check skipped: IDAES env missing")
        return
    p = subprocess.run([py, str(Path(__file__).resolve().parents[1] / "idaes_runner" / "property_check.py")],
                       capture_output=True, text=True, timeout=300, env=dict(os.environ, PYTHONUTF8="1"))
    res = json.loads(p.stdout.strip().splitlines()[-1])
    bad = {s: r for s, r in res.items() if abs(r["dH_rel"]) > .02 or abs(r["Hf_diff_kJ"]) > 1.5}
    worst = max(res, key=lambda s: abs(res[s]["dH_rel"]))
    assert not bad, bad
    print(f"property cross-check vs chemicals: {len(res)} species, worst dH {worst} {100 * res[worst]['dH_rel']:.2f} %: PASS")


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    target=Path(__file__).with_name('uo2_idaes_results.json')
    target.write_text(json.dumps(dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                                     skipped=[str(x[1]) for x in result.skipped],differences=DIFFERENCES),indent=1),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
