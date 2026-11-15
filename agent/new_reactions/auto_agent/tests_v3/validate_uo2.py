"""Offline UO-2.0 hand-calculation anchors; no API/LLM or plant records.

Each expected value cites physical tables or an explicit textbook equation.
Cost anchors independently evaluate Turton App A tables, NOT assertions that
these inputs reproduce a published worked plant example.
"""
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unitops as u
import unitops_equipment as e
import registry


class UO2(unittest.TestCase):
    def close(self,a,b,tol=1e-6): self.assertAlmostEqual(a,b,delta=tol*max(abs(b),1e-6))

    def test_cp_enthalpy(self):
        # NIST SRD69 Ar monatomic Cp=20.786 J/mol/K; 2 kmol * Cp *100K.
        self.close(u.cp_mix({'Ar':2},400)['cp_J_mol_K'],20.786,1e-6)
        self.close(u.enthalpy_stream({'Ar':2},400,300)['enthalpy_GJ_per_t'],.0041572,1e-6)
        # NIST N2 sensible H at 1000K: 21.46 kJ/mol.
        self.close(u.enthalpy_stream({'N2':1},1000,298.15)['enthalpy_GJ_per_t'],.02146,.002)

    def test_saturation(self):
        # NIST Antoine: 300K water 0.0353353bar, methanol .186e0bar.
        self.close(u.antoine_psat('H2O',300)['P_sat_bar'],.0353352783)
        self.close(u.vapor_pressure('CH3OH',300)['P_sat_bar'],.186, .01)
        # NIST normal boiling points at 1.01325 bar.
        for s,t in [('NH3',239.82),('C2H5OH',351.5),('CH4',111.66),('C2H6',184.55),('C3H8',231.04)]:
            self.close(u.vapor_pressure(s,t)['P_sat_bar'],1.01325,.025)
        # NIST CO2 at 293.15K 57.29bar; Lee-Kesler corresponding states within 2%.
        self.close(u.vapor_pressure('CO2',293.15)['P_sat_bar'],57.29,.02)
        with self.assertRaises(ValueError): u.vapor_pressure('CO2',195)
        with self.assertRaises(ValueError): u.antoine_psat('H2O',600)

    def test_rachford_rice(self):
        # Rachford & Rice, JPT 4 (1952) 327, equation; standard numerical
        # example z=(.5,.3,.2), K=(1.685,.742,.532): beta=.6907302628.
        feed={'CH4':.5,'C2H6':.3,'C3H8':.2}; k=dict(zip(feed,(1.685,.742,.532)))
        out=u.flash_pt(feed,300,1,henry_bar=k,ideal_liquid=True)
        self.close(out['vapor_fraction'],.6907302628)
        for s,n in feed.items(): self.close(out['vapor_kmol_per_t'][s]+out['liquid_kmol_per_t'][s],n)
        for beta,ks in [(1.,{s:2 for s in feed}),(0.,{s:.2 for s in feed})]:
            self.assertEqual(u.flash_pt(feed,300,1,ks)['vapor_fraction'],beta)
        self.assertEqual(u.flash_pt({'H2O':1,'CH3OH':1},300,1)['applicability']['status'],'out_of_domain')

    def test_dew_knockout(self):
        # Smith Van Ness Raoult: yw=.1 at 1bar -> dew psat=.1bar, T=318.96K.
        feed={'H2O':1.,'N2':9.}
        self.close(u.dew_point(feed,1,bracket=(304,333))['T_dew_K'],318.96,.0002)
        out=u.water_knockout(feed,300,1)
        # nwater_v=ndry*psat/(P-psat)=.32966636 kmol; CRC latent 40.65kJ/mol.
        self.close(out['vapor_kmol_per_t']['H2O'],.3296663574)
        self.close(out['cooling_duty_GJ_per_t'],(1-.3296663574)*.04065)
        self.assertGreater(out['purchased_energy_GJ_per_t'],0)

    def test_equilibrium(self):
        # NIST JANAF H/S at 700K -> Kp for N2+3H2=2NH3 =
        # 8.89e-5 (1bar standard, rounded). Analytic extent root at 100bar
        # x=.32943 from (2x)^2*(4-2x)^2/((1-x)*(3-3x)^3)/1e4=Kp.
        nu={'N2':-1,'H2':-3,'NH3':2}
        out=u.equilibrium_reactor({'N2':1,'H2':3},[nu],700,100)
        self.close(out['extents_kmol_per_t'][0],.32943,1e-4)
        # Independent total atom counts and Gibbs equilibrium residual.
        n=out['outlet_kmol_per_t']; self.close(n['H2']+1.5*n['NH3'],3)
        self.close(n['N2']+.5*n['NH3'],1)
        # Two independent reactions, no reaction-specific values in implementation.
        rx=[{'CO':-1,'H2O':-1,'CO2':1,'H2':1},{'CO':-1,'H2':-3,'CH4':1,'H2O':1}]
        out=u.equilibrium_reactor({'CO':1,'H2':3,'H2O':1},rx,900,1)
        n=out['outlet_kmol_per_t']; total=sum(n.values())
        for nu in rx:
            dg=sum(v*(u.species_thermo(s,900)[0]-900*u.species_thermo(s,900)[1]) for s,v in nu.items())
            lnq=sum(v*math.log(n[s]/total) for s,v in nu.items())
            self.assertLess(abs(lnq+dg/(u.R*900)),2e-4)
        with self.assertRaises(ValueError): u.equilibrium_reactor({'H2':1},[{'H2':-1,'H2O':1}],500,1)

    def test_adiabatic_staged(self):
        # NIST Shomate energy balance, 0.1 kmol H2 burned in diluted feed:
        # solving integrated Cp(T) gives Tad=527.242K (Fogler ch11).
        nu={'H2':-1,'O2':-.5,'H2O':1}; feed={'H2':1,'O2':.5,'N2':5}
        st=u.adiabatic_temperature_rise(feed,nu,.1,400)
        self.close(st['T_out_K'],527.24175)
        out=u.staged_cooled_reactor(2,400,550,feed,nu,1,conversions=[.1,.1])
        self.assertEqual(len(out['beds']),2)
        self.assertTrue(all(s['T_out_K']<=550+1e-7 for s in out['beds']))
        self.assertGreater(out['cooling_duty_GJ_per_t'],0)

    def test_rate_reactors(self):
        # Fogler ch4 first order dFA/dV=-.2FA: PFR e^(-.2), CSTR 1/1.2.
        feed={'H2':1,'O2':1}; nu=[{'H2':-1,'O2':-.5,'H2O':1}]
        rate=lambda f,t,p: [.2*f['H2']]
        pfr=u.pfr_isothermal(rate,feed,nu,400,1,1)
        cstr=u.cstr(rate,feed,nu,400,1,1)
        self.close(pfr['outlet_kmol_per_h']['H2'],math.exp(-.2))
        self.close(cstr['outlet_kmol_per_h']['H2'],1/1.2)
        self.assertLess(pfr['heat_duty_GJ_per_h'],0)

    def test_inventory_ergun(self):
        # Fogler activity-adjusted production/rate; Ergun 1952 eq(1).
        self.close(u.catalyst_inventory(1000,2,.5)['catalyst_kg'],1000)
        self.close(u.ergun_pressure_drop(1,.01,.4,1e-5,1,.1)['dP_Pa'],24.84375)

    def test_membrane(self):
        # Baker ch3 well mixed, z=.5,theta=.2,r=.1,alpha4:
        # -1.05*y^2+4.175*y-2.5=0, physical y=.73451...
        expected=(4.175-math.sqrt(4.175**2-4*1.05*2.5))/(2*1.05)
        out=u.membrane_two_component({'H2':.5,'N2':.5},4,10,1,.2,P_required=10)
        self.close(out['permeate_purity'],expected)
        for s in ('H2','N2'): self.close(out['permeate_kmol_per_t'][s]+out['retentate_kmol_per_t'][s],.5)
        self.assertGreater(out['power_GJ_per_t'],0)

    def test_psa(self):
        # Smith isentropic expression W=nRT/k*(r^k-1)/eta.
        # No feed compression; .5kmol tail at .5bar to1bar, single stage vacuum.
        out=u.psa_energy({'H2':1},.5,10,.5,P_feed=10)
        k=2/7; expected=.5*1000*u.R*313.15/k*(2**k-1)/.75/1e9
        self.close(out['power_GJ_per_t'],expected)
        self.close(out['feed_compression_GJ_per_t'],0)

    def test_kremser_stripper(self):
        # Seader ch7 A=2,N=3 -> yout/yin=1/(2^4-1)=1/15.
        self.close(u.absorber_kremser(.15,.01,2,1)['theoretical_stages'],3)
        self.close(u.absorber_kremser(.1,.025,1,1)['theoretical_stages'],3)
        with self.assertRaises(ValueError): u.absorber_kremser(.1,.01,.5,1)
        # 1000kg solvent *4kJ/kgK *50K +1kmol*50kJ/mol +2kmol*40kJ/mol=.33GJ.
        self.close(u.stripper_heat(1000,4,50,1,50,2,40)['heat_duty_GJ_per_t'],.33)

    def test_fug(self):
        # Seader ch9 binary Fenske: alpha2.5, xD=.95 xB=.05,
        # Nmin=ln(19^2)/ln(2.5)=6.4268. Underwood theta=10/7,
        # Rmin=1.10 (saturated liquid feed z=.5).
        out=u.distillation_fug({'C3H8':50,'C2H6':50},'C2H6','C3H8',{'C2H6':.95,'C3H8':.05},1,
                               relative_volatilities={'C2H6':2.5,'C3H8':1},latent_kJ_mol={'C2H6':15,'C3H8':20})
        self.close(out['N_min'],math.log(361)/math.log(2.5))
        self.close(out['R_min'],1.10)
        self.close(out['reboiler_duty_GJ_per_t'],(1+1.5*1.10)*50*15.25/1000)
        self.assertGreater(out['theoretical_stages'],out['N_min'])

    def test_heat_exchanger(self):
        # Incropera countercurrent LMTD: (100-80)/ln(100/80)=89.6284K;
        # Q=1000kW, U=500W/m2/K -> A=22.3144m2.
        out=u.heat_exchanger(1000,450,380,300,350,500)
        self.close(out['LMTD_K'],20/math.log(1.25)); self.close(out['area_m2'],100*math.log(1.25))
        self.close(u.heat_exchanger(100,450,350,300,400,500)['LMTD_K'],50)
        with self.assertRaises(ValueError): u.heat_exchanger(100,400,350,300,410,500)

    def test_problem_table(self):
        # Linnhoff 1982 heat-cascade method, four-stream hand exercise:
        # hot (453->313,CP2),(423->333,CP4); cold (293->428,CP3),
        # (353->413,CP2.6); deltaTmin10. Interval heats 30,-15,24,90,-20,-30
        # all kW. Cascade minimum 0 -> QHmin0, QCmin79kW.
        streams=[dict(Tin=453,Tout=313,CP_kW_K=2),dict(Tin=423,Tout=333,CP_kW_K=4),
                 dict(Tin=293,Tout=428,CP_kW_K=3),dict(Tin=353,Tout=413,CP_kW_K=2.6)]
        out=u.problem_table(streams,10)
        self.close(out['hot_utility_kW'],0); self.close(out['cold_utility_kW'],79)
        # Cold stream alone needs external heat, catches missing cascade shift.
        out=u.problem_table([dict(Tin=300,Tout=400,CP_kW_K=2)],10)
        self.close(out['hot_utility_kW'],200); self.close(out['cold_utility_kW'],0)

    def test_steam(self):
        # IAPWS-IF97 saturated 10bar latent=2014.4kJ/kg; 1GJ ->496.4257kg.
        self.close(u.steam_generation(1,10)['steam_kg_per_t'],1e6/2014.4)

    def test_costs(self):
        # Turton 5e Tables A.1/A.4/A.5, 2001USD. Hand evaluations of log
        # quadratic purchase cost times CS bare-module factor (1bar).
        expected={'compressor':(1000,782993.274),'pump':(100,41893.3423),
          'heat_exchanger':(100,77534.662),'vessel_vertical':(10,46014.4684),
          'vessel_horizontal':(10,31854.1848),'reactor_vessel':(10,46014.4684),
          'packed_column':(10,47844.4684),'tray_column':(10,47844.4684),
          'fired_heater':(10000,6554322.943)}
        for kind,(size,want) in expected.items():
            with self.subTest(kind=kind):
                out=u.turton_cost(kind,size,internals_purchase_usd=1000 if 'column' in kind else None,
                                   internals_bare_module_factor=1.83 if 'column' in kind else None)
                self.close(out['capex_usd'],want)
                self.assertTrue({'method','cost_year','installed','size_basis','source'}<=out['capex_basis'].keys())
                self.assertTrue(out['capex_basis']['installed'])
                # Actual gate capital ledger contract (no thresholds changed).
                from physics_gate import ledger_checks
                failures=[]
                ledger_checks([out],{},dict(capacity_t_per_y={'value':1}),failures)
                self.assertEqual(failures,[])
        # Turton Example 7.13 independently gives vessel SS FM3.11 and
        # P20barg,D3m -> FP6.47; shell FBM38.87, distinct tray FBM1.83.
        out=u.turton_cost('vessel_vertical',212.1,'SS',20,diameter_m=3)
        self.close(out['pressure_factor'],6.47,.001)
        self.close(out['bare_module_factor'],38.87,.001)
        # Explicit CEPCI escalation, no installation factor applied twice.
        self.close(u.cepci(2022)['index'],816)
        self.close(u.turton_cost('pump',100,cost_year=2022)['capex_usd'],41893.3422942*816/397)
        self.close(u.lang_factor_total({'a':1000,'b':2000},4,2022)['capex_usd'],12000)
        with self.assertRaises(ValueError): u.cepci(2026)
        with self.assertRaises(ValueError): u.turton_cost('pump',.01)
        with self.assertRaises(ValueError): u.turton_cost('tray_column',10)

    def test_registry(self):
        for name in e.UO2_FUNCTIONS:
            mid='unitops.'+name; self.assertIs(registry.resolve(mid),getattr(u,name))
            self.assertTrue(registry.describe_module(mid)['applicability_domain'])
        self.assertEqual(registry.describe_module('idaes_adapter.idaes_check')['tier'],'T1')


if __name__=='__main__': unittest.main(verbosity=2)
