"""UO-2.0 generic methods. Flows kmol/t, heat GJ/t, T K, absolute P bar.

Sizing additionally requires a time basis: duty_kW, kg/h, kmol/h, m3 and SI
transport properties are explicitly named. No plant or reaction parameters.
References: NIST SRD69; Smith, Van Ness & Abbott (7e), ch 10/13/14;
Seader, Henley & Roper (3e), ch 5/7/9; Fogler (5e), ch 2/4/11;
Linnhoff et al., User Guide on Process Integration (1982); Turton (5e), App A.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, least_squares, minimize, LinearConstraint
from physics_gate import (R, THERMO, SHOMATE, species_thermo, formula_elements)


def _positive(**values):
    for key, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(key + ' must be finite and positive')


def _stream(stream):
    if not stream or any(not math.isfinite(n) or n < 0 for n in stream.values()) or sum(stream.values()) <= 0:
        raise ValueError('nonnegative stream with positive total required')
    return sum(stream.values())


def _result(function_name, kind='other', **fields):
    result = dict(name=function_name, type=kind, computed_by=['unitops.'+function_name],
                  boundary_role={'reactor':'reaction','separation':'separation','knockout':'separation',
                                 'heat_exchanger':'heat_integration'}.get(kind,'utilities'),
                  purchased_energy_GJ_per_t=0.,capex_usd=0.,
                  applicability={'status': 'within_domain', 'warnings': []})
    result.update(fields)
    return result


def cp_mix(stream, T):
    """NIST Shomate molar Cp (J/mol/K) and stream Cp (GJ/t/K)."""
    total = _stream(stream)
    cps = {}
    for s in stream:
        species_thermo(s, T)  # same range contract as gate
        if s in SHOMATE:
            a,b,c,d,e,*_ = next(row[2] for row in SHOMATE[s] if T <= row[1])
            t = T/1000
            cps[s] = a+b*t+c*t*t+d*t**3+e/t**2
        else:
            cps[s] = THERMO[s][2]
    c = sum(stream[s]*cps[s] for s in stream)
    return _result('cp_mix', cp_J_mol_K=c/total, heat_capacity_GJ_per_t_K=c/1e6, T_K=T)


def enthalpy_stream(stream, T, reference_T=None):
    """Ideal gas enthalpy, formation basis or sensible relative to reference_T."""
    _stream(stream)
    h = sum(n*(species_thermo(s,T)[0]-(species_thermo(s,reference_T)[0] if reference_T else 0))
            for s,n in stream.items())/1e6
    return _result('enthalpy_stream', enthalpy_GJ_per_t=h, T_K=T, phase='gas')


# NIST WebBook SRD69, Type=ANTOINE, SI: log10(P/bar)=A-B/(T/K+C).
# Each row Tmin,Tmax,A,B,C,source (CAS URL unambiguously identifies table).
ANTOINE = {
 'H2O': [(273,303,5.40221,1838.675,-31.737), (304,333,5.20389,1733.926,-39.485),
         (334,363,5.0768,1659.793,-45.854), (344,373,5.08354,1663.125,-45.622),
         (379,573,3.55959,643.748,-198.043)],
 'CH3OH': [(288.1,356.83,5.20409,1581.341,-33.50)],
 'NH3': [(239.6,371.5,4.86886,1113.928,-10.409)],
 'C2H5OH': [(273,351.70,5.37229,1670.409,-40.191), (292.77,366.63,5.24677,1598.673,-46.424)],
 'CH4': [(90.99,189.99,3.9895,443.028,-0.49)],
 'C2H6': [(135.74,199.91,3.93835,659.739,-16.719)],
 'C3H8': [(166.02,231.41,4.01158,834.26,-22.763),(230.6,320.7,3.98292,819.296,-24.417)],
}
CAS = dict(H2O='7732185', CH3OH='67561', NH3='7664417', C2H5OH='64175',
           CH4='74828', C2H6='74840', C3H8='74986', CO2='124389')
# Critical data and acentric factor: Poling et al., Properties of Gases and
# Liquids (5e), App A. CO2 liquid psat uses Lee-Kesler corresponding states,
# never the NIST *solid sublimation* Antoine row.
CO2_CRITICAL = (304.1282, 73.773, .22394)
PERMANENT = {'H2','N2','O2','CO','Ar'}


def antoine_psat(species, T):
    """Pure liquid saturation pressure in bar; reject extrapolation and solids."""
    _positive(T=T)
    rows = ANTOINE.get(species, [])
    row = next((r for r in rows if r[0] <= T <= r[1]), None)
    if row is None:
        raise ValueError(f'no liquid Antoine fit for {species} at {T} K; use vapor_pressure for CO2')
    _,_,a,b,c = row
    return _result('antoine_psat', P_sat_bar=10**(a-b/(T+c)), T_K=T,
                   source=f'https://webbook.nist.gov/cgi/cbook.cgi?ID=C{CAS[species]}&Type=ANTOINE')


def vapor_pressure(species, T):
    """Antoine, or CO2 Lee-Kesler liquid correlation (216.592 <= T < Tc)."""
    if species != 'CO2':
        out = antoine_psat(species,T)
        out['computed_by'] = ['unitops.vapor_pressure']
        return out
    tc,pc,w = CO2_CRITICAL
    if not 216.592 <= T < tc:
        raise ValueError('CO2 liquid vapor pressure requires 216.592 <= T < 304.1282 K')
    tr = T/tc
    f0 = 5.92714-6.09648/tr-1.28862*math.log(tr)+.169347*tr**6
    f1 = 15.2518-15.6875/tr-13.4721*math.log(tr)+.43577*tr**6
    return _result('vapor_pressure', P_sat_bar=pc*math.exp(f0+w*f1), T_K=T,
                   source='Lee & Kesler, AIChE J 21 (1975) 510; Poling 5e ch 7', correlation='Lee-Kesler')


def _k_values(stream,T,P,henry_bar=None):
    _positive(T=T,P=P)
    k = {}
    for s in stream:
        if henry_bar and s in henry_bar:
            _positive(Henry=henry_bar[s])
            k[s] = henry_bar[s]/P
        elif s in PERMANENT or (s=='CO2' and T>=CO2_CRITICAL[0]) or (s=='CH4' and T>=190.564):
            k[s] = 1e12  # insoluble ideal gas, explicitly no dissolution model
        else:
            k[s] = vapor_pressure(s,T)['P_sat_bar']/P
    return k


def flash_pt(stream, T, P, henry_bar=None, ideal_liquid=False):
    """Rachford-Rice PT flash; Raoult liquid, insoluble gas or supplied H/x Henry.

    Smith/Van Ness 7e ch13. Low/moderate P <=10 bar screening. Default flags
    multicomponent polar liquids unless caller explicitly justifies ideal_liquid.
    Henry constants (bar) are caller-sourced, solvent- and temperature-specific.
    """
    total = _stream(stream)
    k = _k_values(stream,T,P,henry_bar)
    z = {s:n/total for s,n in stream.items()}
    def rr(beta):
        return sum(z[s]*(k[s]-1)/(1+beta*(k[s]-1)) for s in z)
    f0,f1 = rr(0),rr(1)
    beta = 0. if f0<=0 else 1. if f1>=0 else brentq(rr,0,1,xtol=1e-14)
    liquid = {s:n*(1-beta)/(1+beta*(k[s]-1)) for s,n in stream.items()}
    vapor = {s:stream[s]-liquid[s] for s in stream}
    warnings = []
    cond = [s for s in stream if k[s]<1e10 and stream[s]>0]
    if P>10: warnings.append('P > 10 bar: ideal gas/Raoult screening outside recommended domain')
    if not ideal_liquid and len(cond)>1 and any(s in cond for s in ('H2O','CH3OH','C2H5OH','NH3')):
        warnings.append('nonideal polar liquid mixture requires activity/fugacity model')
    out = _result('flash_pt','separation', T_K=T,P_bar=P,vapor_fraction=beta, K=k,
                  vapor_kmol_per_t=vapor, liquid_kmol_per_t=liquid,
                  feed=dict(kmol_per_t=total,mol_frac=z,P_bar=P),
                  outlets=[dict(kmol_per_t=sum(v.values()),mol_frac={s:n/sum(v.values()) for s,n in v.items()} if sum(v.values()) else {},P_bar=P)
                           for v in (vapor,liquid)])
    out['applicability'] = dict(status='out_of_domain' if warnings else 'within_domain', warnings=warnings)
    return out


def dew_point(stream, P, bracket=(298.15,373.0), henry_bar=None):
    """Ideal dew T from sum(y_i/K_i)=1; bracket must stay in psat domains."""
    total = _stream(stream)
    def f(t):
        k = _k_values(stream,t,P,henry_bar)
        return sum(n/total/k[s] for s,n in stream.items())-1
    return _result('dew_point', T_dew_K=brentq(f,*bracket),P_bar=P)


def water_knockout(stream, T, P, T_in=None):
    """PT flash plus condensed latent heat and optional ideal-gas sensible cooling.

    Latent constants from legacy CRC table; utilities purchased separately.
    """
    from unitops import latent_heat, sensible_heat, cooling_utility
    out = flash_pt(stream,T,P)
    if T_in is not None and T_in<T: raise ValueError('knockout T_in must be >= T')
    duty = sum(latent_heat(s,n) for s,n in out['liquid_kmol_per_t'].items() if n>1e-9)
    if T_in is not None: duty += sensible_heat(stream,T,T_in)
    out.update(name='water_knockout',type='knockout',computed_by=['unitops.water_knockout'],
               cooling_duty_GJ_per_t=duty,T_process_out_K=T)
    out.update(cooling_utility(duty,T))
    return out


def _stoich(feed, nu_list):
    _stream(feed)
    if not nu_list: raise ValueError('reactions required')
    species = sorted(set(feed).union(*(set(nu) for nu in nu_list)))
    a = np.array([[nu.get(s,0) for nu in nu_list] for s in species],dtype=float)
    if np.linalg.matrix_rank(a)<len(nu_list): raise ValueError('reactions must be independent')
    for nu in nu_list:
        atoms = {}
        for s,v in nu.items():
            for el,n in formula_elements(s).items(): atoms[el]=atoms.get(el,0)+n*v
        if any(abs(v)>1e-10 for v in atoms.values()): raise ValueError('unbalanced reaction')
    return species,a,np.array([feed.get(s,0.) for s in species])


def equilibrium_reactor(feed, nu_list, T, P):
    """Ideal gas constrained Gibbs minimization in reaction extents, 1 bar standard.

    NIST H/S from physics_gate; SLSQP objective n*g0/RT + sum(n ln(y P)).
    """
    _positive(T=T,P=P)
    species,a,n0 = _stoich(feed,nu_list)
    scale = float(sum(n0))
    n0 = n0/scale
    g = np.array([(species_thermo(s,T)[0]-T*species_thermo(s,T)[1])/(R*T) for s in species])
    def objective(x):
        n = np.maximum(n0+a@x,1e-30)
        return float(n@g+np.sum(n*np.log(n/sum(n)*P)))
    def grad(x):
        n=np.maximum(n0+a@x,1e-30)
        return a.T@(g+np.log(n/sum(n)*P))
    sol=minimize(objective,np.zeros(a.shape[1]),jac=grad,method='SLSQP',
                 constraints=[LinearConstraint(a,-n0,np.inf)],options=dict(ftol=1e-12,maxiter=1000))
    if not sol.success or min(n0+a@sol.x)<-1e-8:
        raise ValueError('Gibbs minimization failed: '+sol.message)
    n=np.maximum(n0+a@sol.x,0)*scale
    outlet=dict(zip(species,map(float,n)))
    q=enthalpy_stream(outlet,T)['enthalpy_GJ_per_t']-enthalpy_stream(feed,T)['enthalpy_GJ_per_t']
    out=_result('equilibrium_reactor','reactor',inlet_kmol_per_t=dict(feed),outlet_kmol_per_t=outlet,
                 extents_kmol_per_t=(sol.x*scale).tolist(),T_K=T,P_bar=P,phase='gas',
                 heat_duty_GJ_per_t=q,cooling_duty_GJ_per_t=max(-q,0),solver_status=sol.message)
    if P>10: out['applicability']=dict(status='out_of_domain',warnings=['ideal gas at P >10 bar; fugacity correction required'])
    return out


def adiabatic_temperature_rise(feed, nu, extent, inlet_T, bracket=(298.15,2500.)):
    """Solve Hout(Tad)=Hin(Tin), no constant-Cp approximation (Fogler ch11)."""
    species,a,n0=_stoich(feed,[nu])
    n=n0+a[:,0]*extent
    if min(n)<-1e-10: raise ValueError('extent consumes more than available feed')
    outlet=dict(zip(species,map(float,np.maximum(n,0))))
    hin=enthalpy_stream(feed,inlet_T)['enthalpy_GJ_per_t']
    tad=brentq(lambda t:enthalpy_stream(outlet,t)['enthalpy_GJ_per_t']-hin,*bracket)
    return _result('adiabatic_temperature_rise','reactor',T_out_K=tad,delta_T_K=tad-inlet_T,
                   inlet_kmol_per_t=dict(feed),outlet_kmol_per_t=outlet,heat_duty_GJ_per_t=0.)


def staged_cooled_reactor(n_beds, inlet_T, max_T, feed, nu, P, conversions=None, bracket=(298.15,2500.)):
    """Adiabatic beds, cool to inlet_T between beds; extent limited by max_T.

    conversions: per-bed fraction of limiting stoichiometric feed; None solves
    adiabatic equilibrium. Even specified conversions are equilibrium limited.
    """
    if not isinstance(n_beds,int) or n_beds<1 or max_T<=inlet_T: raise ValueError('invalid beds/temperature limit')
    if conversions is not None and len(conversions)!=n_beds: raise ValueError('one conversion per bed')
    if sum(v*species_thermo(s,inlet_T)[0] for s,v in nu.items())>=0:
        raise ValueError('cooled adiabatic beds require an exothermic reaction')
    current=dict(feed); beds=[]; cooling=0.
    for j in range(n_beds):
        limit=min(current.get(s,0)/(-v) for s,v in nu.items() if v<0)
        def state(x): return adiabatic_temperature_rise(current,nu,x,inlet_T,bracket)
        def residual(x):
            st=state(x); n=st['outlet_kmol_per_t']; total=sum(n.values()); t=st['T_out_K']
            dg=sum(v*(species_thermo(s,t)[0]-t*species_thermo(s,t)[1]) for s,v in nu.items())/(R*t)
            return dg+sum(v*math.log(max(n[s]/total*P,1e-30)) for s,v in nu.items())
        # Bound extent by the *energy balance at max_T* before solving Tad.
        # This avoids evaluating full-conversion Tad outside the thermo range.
        hin=enthalpy_stream(current,inlet_T)['enthalpy_GJ_per_t']
        def energy_at_max(x):
            species=set(current)|set(nu)
            n={s:max(0.,current.get(s,0)+x*nu.get(s,0)) for s in species}
            return enthalpy_stream(n,max_T)['enthalpy_GJ_per_t']-hin
        thermal_limit=limit
        if energy_at_max(limit)<0: thermal_limit=brentq(energy_at_max,0,limit)
        eps=max(limit*1e-10,1e-14)
        if thermal_limit<=eps or residual(eps)>=0: x=0.
        elif residual(min(thermal_limit,limit-eps))<=0: x=min(thermal_limit,limit-eps)
        else: x=brentq(residual,eps,min(thermal_limit,limit-eps))
        if conversions is not None:
            if not 0<=conversions[j]<=1: raise ValueError('conversion outside [0,1]')
            x=min(x,limit*conversions[j])
        if state(x)['T_out_K']>max_T:
            x=brentq(lambda z:state(z)['T_out_K']-max_T,0,x)
        st=state(x); st['extent_kmol_per_t']=x; beds.append(st)
        current=st['outlet_kmol_per_t']
        if j<n_beds-1:
            cooling+=enthalpy_stream(current,st['T_out_K'],inlet_T)['enthalpy_GJ_per_t']
    return _result('staged_cooled_reactor','reactor',beds=beds,outlet_kmol_per_t=current,
                   inlet_kmol_per_t=dict(feed),cooling_duty_GJ_per_t=cooling,T_out_K=beds[-1]['T_out_K'],P_bar=P)


def pfr_isothermal(rate_fn, feed, nu_list, T, P, volume_m3):
    """dF/dV=nu*r; feed kmol/h, rate_fn(F,T,P) -> kmol/m3/h per reaction.

    Explicit hourly rate basis, NOT the ledger's kmol/t. Fogler ch4.
    """
    _positive(T=T,P=P,volume_m3=volume_m3)
    species,a,f0=_stoich(feed,nu_list)
    def rhs(v,f):
        rates=np.atleast_1d(rate_fn(dict(zip(species,np.maximum(f,0))),T,P)).astype(float)
        if len(rates)!=len(nu_list) or not np.all(np.isfinite(rates)): raise ValueError('invalid rate vector')
        return a@rates
    sol=solve_ivp(rhs,(0,volume_m3),f0,rtol=1e-9,atol=1e-11)
    if not sol.success or np.min(sol.y)<-1e-7: raise ValueError('PFR integration failed or negative flow')
    out=dict(zip(species,map(float,np.maximum(sol.y[:,-1],0))))
    q=enthalpy_stream(out,T)['enthalpy_GJ_per_t']-enthalpy_stream(feed,T)['enthalpy_GJ_per_t']
    return _result('pfr_isothermal','reactor',outlet_kmol_per_h=out,heat_duty_GJ_per_h=q,T_K=T,P_bar=P,volume_m3=volume_m3)


def cstr(rate_fn, feed, nu_list, T, P, volume_m3):
    """Steady CSTR Fout-Fin=V*nu*r(Fout,T,P); hourly basis, as PFR."""
    _positive(T=T,P=P,volume_m3=volume_m3)
    species,a,f0=_stoich(feed,nu_list)
    def residual(f):
        rates=np.atleast_1d(rate_fn(dict(zip(species,f)),T,P))
        return (f-f0-volume_m3*a@rates)/max(sum(f0),1)
    sol=least_squares(residual,np.maximum(f0,1e-6),bounds=(0,np.inf),gtol=1e-12,ftol=1e-12,xtol=1e-12)
    if not sol.success or max(abs(residual(sol.x)))>1e-7: raise ValueError('CSTR balance did not converge')
    out=dict(zip(species,map(float,sol.x)))
    q=enthalpy_stream(out,T)['enthalpy_GJ_per_t']-enthalpy_stream(feed,T)['enthalpy_GJ_per_t']
    return _result('cstr','reactor',outlet_kmol_per_h=out,heat_duty_GJ_per_h=q,T_K=T,P_bar=P,volume_m3=volume_m3)


def catalyst_inventory(production, rate, deactivation=1.):
    """kg catalyst = production kg/h / (rate kg/kgcat/h * mean activity).

    deactivation is cycle-mean activity in (0,1], supplied by a sourced model.
    """
    _positive(production=production,rate=rate,deactivation=deactivation)
    if deactivation>1: raise ValueError('mean activity <=1 required')
    return _result('catalyst_inventory','reactor',catalyst_kg=production/rate/deactivation,
                   production_kg_per_h=production,rate_kg_per_kgcat_h=rate,mean_activity=deactivation)


def ergun_pressure_drop(length_m, particle_diameter_m, void_fraction, viscosity_Pa_s, density_kg_m3, velocity_m_s):
    """Ergun (1952), Chem Eng Prog 48, 89: superficial velocity, SI."""
    _positive(length=length_m,diameter=particle_diameter_m,viscosity=viscosity_Pa_s,density=density_kg_m3)
    if not 0<void_fraction<1 or velocity_m_s<0: raise ValueError('invalid porosity/velocity')
    e=void_fraction; d=particle_diameter_m; v=velocity_m_s
    dp=length_m*(150*viscosity_Pa_s*(1-e)**2*v/(e**3*d*d)+1.75*density_kg_m3*(1-e)*v*v/(e**3*d))
    return _result('ergun_pressure_drop',dP_Pa=dp,dP_bar=dp/1e5)


def membrane_two_component(feed, permeance_ratio, P_feed, P_permeate, stage_cut, T=313.15, P_required=None):
    """Well-mixed binary membrane. First species is faster; relative permeance >=1.

    Solve y/(1-y)=alpha*(xr-r*y)/(1-xr-r*(1-y)), xr=(z-theta*y)/(1-theta).
    Baker, Membrane Technology and Applications 3e ch3. No area prediction.
    """
    from unitops import separator_energy
    total=_stream(feed)
    if len(feed)!=2 or permeance_ratio<1 or not 0<stage_cut<1 or not 0<P_permeate<P_feed:
        raise ValueError('binary feed, alpha>=1, theta in (0,1), 0<Pperm<Pfeed required')
    fast,slow=list(feed); z=feed[fast]/total; th=stage_cut; r=P_permeate/P_feed
    if not 0<z<1: raise ValueError('both components must be present')
    def f(y):
        x=(z-th*y)/(1-th)
        return y*(1-x-r*(1-y))-permeance_ratio*(1-y)*(x-r*y)
    lo=max(0.,(z+th-1)/th); hi=min(1.,z/th)
    y=brentq(f,lo,hi); x=(z-th*y)/(1-th)
    if min(x-r*y,1-x-r*(1-y)) < -1e-9: raise ValueError('reverse flux: chosen stage cut/pressure not feasible')
    perm={fast:total*th*y,slow:total*th*(1-y)}; ret={s:feed[s]-perm[s] for s in feed}
    outlets=[dict(kmol_per_t=sum(perm.values()),P_out_bar=P_permeate,P_required_bar=P_required or P_permeate),
             dict(kmol_per_t=sum(ret.values()),P_out_bar=P_feed,P_required_bar=P_feed)]
    energy=separator_energy(P_feed,outlets,T)
    out=_result('membrane_two_component','separation',stage_cut=th,permeate_purity=y,retentate_purity=x,
                   permeate_kmol_per_t=perm,retentate_kmol_per_t=ret,T_K=T,
                   feed=dict(kmol_per_t=total,mol_frac={s:n/total for s,n in feed.items()},P_bar=P_feed),
                   outlets=[dict(kmol_per_t=sum(v.values()),mol_frac={s:n/sum(v.values()) for s,n in v.items()}) for v in (perm,ret)])
    out.update(energy)
    return out


def psa_energy(feed, recovery, P_ads, P_des, T=313.15, P_feed=1., product_P=None, tail_P=1.):
    """Pressure swing work; recovery maps product component fractions (or total).

    Include feed compression to adsorption P, product delivery and tail vacuum.
    Adsorption selectivity and recovery are caller decisions, not predictions.
    """
    from unitops import compressor,separator_energy
    total=_stream(feed)
    _positive(P_ads=P_ads,P_des=P_des,P_feed=P_feed,tail_P=tail_P)
    if P_des>=P_ads or P_feed>P_ads: raise ValueError('require Pdes<Pads and Pfeed<=Pads')
    rec=recovery if isinstance(recovery,dict) else {s:recovery for s in feed}
    if set(rec)-set(feed) or any(not 0<=v<=1 for v in rec.values()): raise ValueError('invalid recoveries')
    product={s:n*rec.get(s,0) for s,n in feed.items()}; tail={s:feed[s]-product[s] for s in feed}
    outlets=[dict(kmol_per_t=sum(product.values()),P_out_bar=P_ads,P_required_bar=product_P or P_ads),
             dict(kmol_per_t=sum(tail.values()),P_out_bar=P_des,P_required_bar=tail_P)]
    e=separator_energy(P_ads,outlets,T)
    feed_work=compressor(total,T,P_feed,P_ads)['power_GJ_per_t']
    e['power_GJ_per_t']+=feed_work; e['purchased_energy_GJ_per_t']+=feed_work
    return _result('psa_energy','separation',**e,feed_compression_GJ_per_t=feed_work,T_K=T,
                   product_kmol_per_t=product,tail_kmol_per_t=tail,
                   feed=dict(kmol_per_t=total,mol_frac={s:n/total for s,n in feed.items()},P_bar=P_ads))


def absorber_kremser(y_in, y_out, L_over_G, equilibrium_slope, x_in=0.):
    """Dilute countercurrent absorber theoretical stages, constant molar L/G.

    Seader 3e ch7: (yout-m*xin)/(yin-m*xin)=(A-1)/(A**(N+1)-1).
    """
    _positive(L_over_G=L_over_G,equilibrium_slope=equilibrium_slope)
    floor=equilibrium_slope*x_in
    if not 0<=floor<y_out<y_in<1: raise ValueError('need mxin<yout<yin<1')
    a=L_over_G/equilibrium_slope; ratio=(y_out-floor)/(y_in-floor)
    if abs(a-1)<1e-10: n=1/ratio-1
    else:
        if a<1 and ratio<=1-a: raise ValueError('target below absorption pinch')
        n=math.log1p((a-1)/ratio)/math.log(a)-1
    return _result('absorber_kremser','separation',absorption_factor=a,theoretical_stages=n,stages=math.ceil(n-1e-12))


def stripper_heat(solvent_kg_per_t, cp_kJ_kg_K, delta_T_K, solute_kmol_per_t, desorption_kJ_mol, boilup_kmol_per_t=0., latent_kJ_mol=40.65):
    """Solvent sensible + desorption + boilup latent heat; Seader ch7/9.

    Default latent water at normal boiling point (CRC), use sourced solvent data.
    """
    vals=(solvent_kg_per_t,cp_kJ_kg_K,delta_T_K,solute_kmol_per_t,desorption_kJ_mol,boilup_kmol_per_t,latent_kJ_mol)
    if any(not math.isfinite(v) or v<0 for v in vals): raise ValueError('nonnegative inputs required')
    q=solvent_kg_per_t*cp_kJ_kg_K*delta_T_K/1e6+(solute_kmol_per_t*desorption_kJ_mol+boilup_kmol_per_t*latent_kJ_mol)/1e3
    return _result('stripper_heat','regenerator',heat_duty_GJ_per_t=q,service='heating')


def distillation_fug(feed, light_key, heavy_key, recoveries, P, relative_volatilities=None, reflux_factor=1.5, q=1., latent_kJ_mol=None, T=None):
    """Fenske/Underwood/Gilliland screening: total condenser, saturated liquid feed.

    Recoveries are fraction of EACH component to distillate (explicit required).
    Constant relative volatilities supplied or psat ratios at T. No azeotropes.
    Gilliland via Eduljee (1975). Duties constant molar overflow, not rigorous MESH.
    """
    from unitops import LATENT_KJ_PER_MOL
    total=_stream(feed); _positive(P=P,reflux_factor=reflux_factor)
    if q!=1 or reflux_factor<=1: raise ValueError('currently saturated liquid feed q=1 and reflux_factor>1 only')
    if set(recoveries)!=set(feed) or any(not 0<v<1 for v in recoveries.values()): raise ValueError('recoveries (0,1) for every species required')
    d={s:n*recoveries[s] for s,n in feed.items()}; b={s:feed[s]-d[s] for s in feed}
    dt=sum(d.values()); bt=sum(b.values()); xd={s:n/dt for s,n in d.items()}; xb={s:n/bt for s,n in b.items()}
    if relative_volatilities is None:
        if T is None: raise ValueError('T or sourced relative_volatilities required')
        relative_volatilities={s:vapor_pressure(s,T)['P_sat_bar']/vapor_pressure(heavy_key,T)['P_sat_bar'] for s in feed}
    a={s:relative_volatilities[s]/relative_volatilities[heavy_key] for s in feed}
    if a[light_key]<=1 or any(v<=0 for v in a.values()): raise ValueError('light key alpha must exceed heavy key')
    nmin=math.log((xd[light_key]/xd[heavy_key])/(xb[light_key]/xb[heavy_key]))/math.log(a[light_key])
    if nmin<=0: raise ValueError('key recoveries do not describe a distillation')
    if any(1<v<a[light_key] for s,v in a.items() if s not in (light_key,heavy_key)):
        raise ValueError('intermediate key requires multi-root Underwood model')
    theta=brentq(lambda th:sum(a[s]*feed[s]/total/(a[s]-th) for s in feed)-(1-q),1+1e-9,a[light_key]-1e-9)
    rmin=sum(a[s]*xd[s]/(a[s]-theta) for s in feed)-1
    if rmin<=0: raise ValueError('nonpositive minimum reflux: inappropriate key split')
    reflux=reflux_factor*rmin; x=(reflux-rmin)/(reflux+1)
    y=1-math.exp((1+54.4*x)/(11+117.2*x)*(x-1)/math.sqrt(x))
    n=(nmin+y)/(1-y)
    latent=latent_kJ_mol or LATENT_KJ_PER_MOL
    lam=sum(xd[s]*latent[s] for s in feed)
    qc=(reflux+1)*dt*lam/1e3
    return _result('distillation_fug','separation',N_min=nmin,R_min=rmin,reflux_ratio=reflux,theoretical_stages=n,
                   stages=math.ceil(n),distillate_kmol_per_t=d,bottoms_kmol_per_t=b,
                   condenser_duty_GJ_per_t=qc,reboiler_duty_GJ_per_t=qc,heat_duty_GJ_per_t=qc,
                   cooling_duty_GJ_per_t=qc,P_bar=P,theta=theta,
                   method='FUG constant alpha, q=1; total condenser; equilibrium stages incl reboiler')


def heat_exchanger(duty, T_hot_in, T_hot_out, T_cold_in, T_cold_out, U):
    """Countercurrent LMTD; duty kW, U W/m2/K; Smith 2016 ch10."""
    _positive(duty=duty,U=U)
    if T_hot_in<=T_hot_out or T_cold_out<=T_cold_in: raise ValueError('invalid hot/cold direction')
    d1=T_hot_in-T_cold_out; d2=T_hot_out-T_cold_in
    if min(d1,d2)<=0: raise ValueError('temperature crossing/pinch')
    lm=d1 if math.isclose(d1,d2,rel_tol=1e-10) else (d1-d2)/math.log(d1/d2)
    return _result('heat_exchanger','heat_exchanger',LMTD_K=lm,area_m2=duty*1000/U/lm,duty_kW=duty,U_W_m2_K=U)


def problem_table(streams, dT_min):
    """Linnhoff shifted-temperature heat cascade. Streams {Tin,Tout,CP_kW_K}."""
    if dT_min<0: raise ValueError('dT_min >=0 required')
    shifted=[]
    for s in streams:
        ti,to,cp=s['Tin'],s['Tout'],s['CP_kW_K']; _positive(Tin=ti,Tout=to,CP=cp)
        if ti==to: raise ValueError('isothermal latent streams require separate interval treatment')
        hot=ti>to; shift=-dT_min/2 if hot else dT_min/2
        shifted.append((max(ti,to)+shift,min(ti,to)+shift,cp*(1 if hot else -1)))
    levels=sorted({t for hi,lo,cp in shifted for t in (hi,lo)},reverse=True)
    cascade=[0.]; rows=[]
    for hi,lo in zip(levels,levels[1:]):
        net=sum(cp for top,bot,cp in shifted if bot<=(hi+lo)/2<=top)
        q=net*(hi-lo); cascade.append(cascade[-1]+q); rows.append(dict(high_K=hi,low_K=lo,net_CP_kW_K=net,heat_kW=q))
    hot=max(0.,-min(cascade)); cold=cascade[-1]+hot
    return _result('problem_table','heat_exchanger',hot_utility_kW=hot,cold_utility_kW=cold,
                   intervals=rows,cascade_kW=[x+hot for x in cascade],shifted_temperatures_K=levels)


def steam_generation(duty, P_steam, latent_kJ_kg=None):
    """Saturated steam from saturated boiler water; duty GJ/t, absolute P bar.

    IAPWS-IF97 saturation table (rounded, linear interpolation 1-40 bar).
    No feedwater preheat/blowdown; supply latent_kJ_kg for external steam table.
    """
    _positive(duty=duty,P_steam=P_steam)
    p=[1,2,5,10,20,40]; hfg=[2257.5,2201.6,2108.,2014.4,1889.8,1713.5]
    if latent_kJ_kg is None:
        if not 1<=P_steam<=40: raise ValueError('steam table covers 1-40 bar only')
        latent_kJ_kg=float(np.interp(P_steam,p,hfg))
    _positive(latent=latent_kJ_kg)
    return _result('steam_generation','other',steam_kg_per_t=duty*1e6/latent_kJ_kg,
                   recovered_heat_GJ_per_t=duty,latent_kJ_kg=latent_kJ_kg,P_bar=P_steam)


# CEPCI annual averages, Chemical Engineering magazine, Economic Indicators.
# Published historical values only; do not extrapolate a future cost year.
CEPCI = {2001:397.,2005:468.2,2010:550.8,2015:556.8,2018:603.1,2019:607.5,
         2020:596.2,2021:708.0,2022:816.0,2023:797.9}


def cepci(year):
    """Chemical Engineering Plant Cost Index annual average; explicit tabulated year."""
    if year not in CEPCI: raise ValueError('CEPCI year not tabulated; provide a documented index explicitly')
    return _result('cepci',year=year,index=CEPCI[year],source='Chemical Engineering, Economic Indicators, annual CEPCI averages')


# Turton 5e App A Tables A.1/A.4/A.5: K1 K2 K3 min max unit B1 B2.
# compressor = centrifugal (FBM=2.8, includes drive); heater = fired furnace.
COST_TABLE = {
 'compressor': (2.2897,1.3604,-.1027,450,3000,'kW',2.8,0.),
 'pump': (3.3892,.0536,.1538,1,300,'kW',1.89,1.35),
 'heat_exchanger': (4.3247,-.3030,.1634,10,1000,'m2',1.63,1.66),
 'vessel_vertical': (3.4974,.4485,.1074,.3,520,'m3',2.25,1.82),
 'vessel_horizontal': (3.5565,.3776,.0905,.1,628,'m3',1.49,1.52),
 'reactor_vessel': (3.4974,.4485,.1074,.3,520,'m3',2.25,1.82),
 'packed_column': (3.4974,.4485,.1074,.3,520,'m3',2.25,1.82),
 'tray_column': (3.4974,.4485,.1074,.3,520,'m3',2.25,1.82),
 'fired_heater': (2.7660,.9222,0.,1000,100000,'kW',2.3,0.),
}


def turton_cost(equipment_type, size_param, material='CS', pressure_barg=0., cost_year=2001,
                diameter_m=None, internals_purchase_usd=None, internals_bare_module_factor=None):
    """Installed bare-module cost, USD (not total grass-roots investment).

    Turton 5e App A, 2001 USD CEPCI397. Columns require sourced internals
    purchase cost in 2001 USD (trays/packing) and its own bare-module factor,
    in addition to shell volume. Shell pressure/material FBM is NOT used for
    internals (Turton Example 7.13: stainless sieve trays FBM=1.83).
    Vessel pressure factor needs diameter (App A eq A.3); material CS/SS only.
    """
    if equipment_type not in COST_TABLE: raise ValueError('unsupported equipment')
    _positive(size=size_param)
    k1,k2,k3,lo,hi,unit,b1,b2=COST_TABLE[equipment_type]
    if not lo<=size_param<=hi: raise ValueError(f'size outside Turton range {lo}-{hi} {unit}')
    if material not in ('CS','SS') or pressure_barg<0: raise ValueError('CS/SS and nonnegative gauge pressure required')
    column=equipment_type in ('packed_column','tray_column')
    if column and (internals_purchase_usd is None or internals_purchase_usd<0 or internals_bare_module_factor is None):
        raise ValueError('columns require sourced internals_purchase_usd (2001 USD) and internals_bare_module_factor')
    if column: _positive(internals_factor=internals_bare_module_factor)
    vessel=equipment_type.startswith('vessel') or equipment_type=='reactor_vessel' or column
    fm=1. if material=='CS' else (3.11 if vessel else 2.3 if equipment_type=='pump' else 2.73)
    fp=1.
    if equipment_type in ('compressor','fired_heater') and (material!='CS' or pressure_barg>0):
        raise ValueError('compressor/heater base correlation only: special material/pressure requires vendor basis')
    if vessel and pressure_barg>0:
        if diameter_m is None: raise ValueError('vessel pressure correction needs diameter_m')
        _positive(diameter=diameter_m)
        if pressure_barg>=100: raise ValueError('vessel correlation pressure <100 barg')
        fp=max(1.,((pressure_barg+1)*diameter_m/(2*(850-.6*(pressure_barg+1)))+.00315)/.0063)
    elif equipment_type in ('pump','heat_exchanger') and pressure_barg>0:
        threshold=10 if equipment_type=='pump' else 5
        if pressure_barg>100: raise ValueError('pressure correlation limited to 100 barg')
        if pressure_barg>=threshold:
            c=(-.3935,.3957,-.00226) if equipment_type=='pump' else (.03881,-.11272,.08183)
            lp=math.log10(pressure_barg); fp=max(1.,10**(c[0]+c[1]*lp+c[2]*lp*lp))
    lp=math.log10(size_param); purchase=10**(k1+k2*lp+k3*lp*lp)
    fbm=b1+b2*fm*fp
    base=purchase*fbm+(internals_purchase_usd or 0)*(internals_bare_module_factor or 1.)
    index=cepci(cost_year)['index']; installed=base*index/397.
    return _result('turton_cost',capex_usd=installed,purchase_cost_2001_usd=purchase,
                   bare_module_factor=fbm,pressure_factor=fp,material_factor=fm,
                   capex_basis=dict(method='size_based',correlation='Turton bare module',cost_year=cost_year,
                     installed=True,installation_factor=1.,size_basis=f'{equipment_type}: {size_param:g} {unit}',
                     source='Turton et al., Analysis Synthesis and Design of Chemical Processes 5e, Appendix A Tables A.1-A.5',
                     internals_purchase_2001_usd=internals_purchase_usd,
                     internals_bare_module_factor=internals_bare_module_factor,
                     cost_index_base=397.,cost_index_now=index))


def lang_factor_total(purchased_equipment_usd, factor, cost_year):
    """Installed investment via caller-sourced Lang factor; Peters/Timmerhaus ch6.

    Purchased equipment mapping ONLY. Already-installed result dicts rejected.
    All purchase costs must be in the declared common year/currency.
    """
    _positive(factor=factor,cost_year=cost_year)
    if factor<1 or not purchased_equipment_usd or any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in purchased_equipment_usd.values()):
        raise ValueError('nonnegative purchased costs and factor>=1 required; no installed dicts')
    return _result('lang_factor_total',capex_usd=sum(purchased_equipment_usd.values())*factor,
                   capex_basis=dict(method='size_based',cost_year=cost_year,installed=True,installation_factor=1.,
                     lang_factor=factor,size_basis='sum purchased equipment USD',source='Peters Timmerhaus West, Plant Design and Economics 5e ch6; caller supplies factor'))


UO2_FUNCTIONS = ('cp_mix enthalpy_stream antoine_psat vapor_pressure flash_pt dew_point water_knockout '
 'equilibrium_reactor adiabatic_temperature_rise staged_cooled_reactor pfr_isothermal cstr '
 'catalyst_inventory ergun_pressure_drop membrane_two_component psa_energy absorber_kremser stripper_heat '
 'distillation_fug heat_exchanger problem_table steam_generation turton_cost cepci lang_factor_total').split()
