"""Source-rate plug-flow bridge, independent of the cold SI k(T) model.

Exact rate expressions follow existing repository kinetics.py at commit
463bfd261d27cd3bb4567d4a69ad3439f1cfbfdf. Fe: Dyson-Simon KM1;
Ru: Rossetti 2006 promoted 3.2 wt% Ru/C, NOT a generic metal or 8 wt% surrogate.
No FCAL or dispersion multiplier is introduced. N2/H2/NH3 activities use
Newton-Cooper with pressure in atm. Rate units are mol NH3 / m3 bed / s.
"""
from __future__ import annotations
import math
from functools import lru_cache
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

NAMES=("N2","H2","CH4","Ar","NH3")
NU=np.array([-.5,-1.5,0.,0.,1.])
R_CAL=1.98720425864083
BAR_PER_ATM=1.01325
DENSITY={"Fe":2850.,"Ru":590.}
RU_WT=.032
PARAMETER_SOURCE="analysis/nh3_staged_converter_2026_10_12/parameters.yaml"
RATE_SOURCE="analysis/nh3_staged_converter_2026_10_12/kinetics.py"
SOURCE_COMMIT="463bfd261d27cd3bb4567d4a69ad3439f1cfbfdf"
SHOMATE={
    "N2":(19.50583,19.88705,-8.598535,1.369784,.527601,-4.935202,212.3900,0.),
    "H2":(33.066178,-11.363417,11.432816,-2.772874,-.158558,-9.980797,172.707974,0.),
    "NH3":(19.99563,49.77119,-15.37599,1.921168,.189174,-53.30667,203.8591,-45.89806),
    "CH4":(-.703029,108.4773,-42.52157,5.862788,.678565,-76.84376,158.7163,-74.87310),
    "Ar":(20.78600,2.825911e-7,-1.464191e-7,1.092131e-8,-3.661371e-8,-6.197350,179.9990,0.)}
DHF={"N2":0.,"H2":0.,"NH3":-45.90,"CH4":-74.87,"Ar":0.}


def equilibrium_constant(T):
    if not 600 <= T <= 820: raise ValueError("Hot-side engineering envelope 600-820 K")
    return 10**(-2.691122*math.log10(T)-5.519265e-5*T+1.848863e-7*T*T+2001.6/T+2.6899)


def activities(T, P_bar, flow):
    if not math.isfinite(P_bar) or not 0<P_bar<=400: raise ValueError("Hot-side pressure envelope 0-400 bar")
    f=np.asarray(flow,dtype=float)
    if f.shape[-1]!=5 or not np.all(np.isfinite(f)) or np.min(f)<-1e-10 or np.any(f.sum(axis=-1)<=0):
        raise ValueError("Invalid five-species flow")
    y=np.maximum(f,0)/f.sum(axis=-1,keepdims=True);p=P_bar/BAR_PER_ATM
    pn=.93431737+.3101804e-3*T+.295896e-3*p-.2707279e-6*T*T+.4775207e-6*p*p
    pa=.1438996+.2028538e-2*T-.4487672e-3*p-.1142945e-5*T*T+.2761216e-6*p*p
    ph=math.exp(math.exp(-3.8402*T**.125+.541)*p-math.exp(-.1263*T**.5-15.980)*p*p+300*math.exp(-.011901*T-5.941)*(math.exp(-p/300)-1))
    if min(pn,pa,ph)<=0:raise ValueError("Nonpositive hot-side fugacity coefficient")
    return (np.maximum(y[...,0],1e-12)*pn*p,
            np.maximum(y[...,1],1e-12)*ph*p,
            np.maximum(y[...,4],1e-12)*pa*p)


def affinity_ratio(T,P,flow):
    an,ah,aa=activities(T,P,flow)
    return aa/(equilibrium_constant(T)*an**.5*ah**1.5)


def rate_m3(catalyst,T,P,flow,activity=1.):
    """No mass-basis conversion guess: both returned rates are per m3 bed."""
    if not math.isfinite(activity) or activity<=0:raise ValueError("Positive activity required")
    an,ah,aa=activities(T,P,flow);K=equilibrium_constant(T)
    if catalyst=="Fe":
        k=8.849e14*math.exp(-40765./(R_CAL*T))
        rate=2*k*(K*K*an*(ah**3/aa**2)**.5-(aa**2/ah**3)**.5)*1000/3600
    elif catalyst=="Ru":
        k=9.02e8*math.exp(-23000./(R_CAL*T))
        kh=math.exp(-13.6/R_CAL+9000./(R_CAL*T))
        ka=math.exp(-8.3/R_CAL+7000./(R_CAL*T))
        numerator=an**.5*ah**.375/aa**.25-aa**.75/(K*ah**1.125)
        # Source gives mol N2/Lcat/hour; multiply 2 NH3/N2, 1000 L/m3, /3600.
        rate=2*k*numerator/(1+kh*ah**.3+ka*aa**.2)*1000/3600
    else:raise ValueError("Measured kinetics available only for Fe and Ru formulations")
    return activity*rate


def validity(catalyst,T,P,flow):
    tc=T-273.15;ratio=float(flow[1]/flow[0])
    if catalyst=="Fe":
        tfit=330<=tc<=495;pfit=149<=P/BAR_PER_ATM<=309
    else:
        tfit=370<=tc<=460;pfit=50<=P<=100
    return {"rate_T_inside_source_range":tfit,"rate_P_inside_source_range":pfit,
            "rate_H2_N2_ratio":ratio,
            "rate_domain":"within_reported_TP_not_full_validation" if tfit and pfit else "engineering_TP_extrapolation",
            "rate_ratio_scope":"Ru lambda=1 (source ratio 3); continuously varying loop ratio is an engineering transfer"}


def equilibrium_extent(T,P,feed):
    f=np.asarray(feed,dtype=float)
    hi=min(2*f[0],2*f[1]/3)*(1-1e-10)
    if affinity_ratio(T,P,f)>=1:return 0.
    return brentq(lambda e:float(affinity_ratio(T,P,f+NU*e)-1),0.,hi,xtol=1e-10)


@lru_cache(maxsize=4)
def integration_nodes(n):
    return np.polynomial.legendre.leggauss(n)


def size_bed(catalyst,T,P,feed_kmol_h,extent_kmol_h,activity=1.,n=96):
    """Inverse PFR: V = int_0^xi dxi / r(T,P,F0+nu*xi).

    Conversions are optimized design coordinates, not asserted catalyst
    predictions. A forward ODE verifies the selected bed/loop afterwards.
    """
    f=np.asarray(feed_kmol_h,dtype=float)/3.6;xi=extent_kmol_h/3.6
    if xi<=0:raise ValueError("Positive production required")
    out=f+NU*xi
    if np.min(out)<0:raise ValueError("Specified conversion violates reactant availability")
    qend=float(affinity_ratio(T,P,out))
    if qend>=1.-1e-9:
        return {"feasible":False,"reason":"conversion_at_or_beyond_hot_equilibrium","affinity_out_Q_over_K":qend}
    knots,weights=integration_nodes(n)
    ext=.5*xi*(1+knots)
    r=rate_m3(catalyst,T,P,f[None,:]+ext[:,None]*NU,activity)
    if np.any(r<=0) or not np.all(np.isfinite(r)):
        return {"feasible":False,"reason":"nonpositive_rate_on_bed_path","affinity_out_Q_over_K":qend}
    vol=.5*xi*float(np.dot(weights,1/r))
    q0=float(affinity_ratio(T,P,f))
    return {"feasible":True,"bed_m3":vol,"catalyst_kg":vol*DENSITY[catalyst],
            "ru_metal_kg":vol*DENSITY[catalyst]*RU_WT if catalyst=="Ru" else 0.,
            "affinity_out_Q_over_K":qend,"affinity_in_Q_over_K":q0,
            "rate_in_mol_m3_s":float(rate_m3(catalyst,T,P,f,activity)),
            "rate_out_mol_m3_s":float(rate_m3(catalyst,T,P,out,activity)),
            **validity(catalyst,T,P,f)}


def forward_bed(catalyst,T,P,feed_kmol_h,volume_m3,activity=1.,rtol=2e-8):
    """Predict extent for a fixed bed; no target conversion is used as input."""
    f=np.asarray(feed_kmol_h,dtype=float)/3.6
    if volume_m3<0 or not math.isfinite(volume_m3):raise ValueError("Invalid bed size")
    if volume_m3==0:return {"extent_kmol_h":0.,"out_kmol_h":np.asarray(feed_kmol_h).copy(),"X_N2":0.,"nfev":0}
    max_e=equilibrium_extent(T,P,f)
    if max_e==0:raise ValueError("Feed is at/beyond synthesis equilibrium")
    def ode(v,e):
        amount=float(e[0])
        # Limit only trial iterates outside chemical domain, never the reported output.
        if amount>=max_e:return [-max(0.,amount-max_e)/max(volume_m3,.1)]
        return [float(rate_m3(catalyst,T,P,f+NU*max(amount,0.),activity))]
    sol=solve_ivp(ode,(0.,volume_m3),[0.],rtol=rtol,atol=max(1e-9,max_e*1e-10),max_step=volume_m3/12)
    if not sol.success:raise RuntimeError(sol.message)
    e=float(sol.y[0,-1])
    if not 0<=e<=max_e*(1+1e-7):raise RuntimeError("Nonphysical PFR solution")
    return {"extent_kmol_h":e*3.6,"out_kmol_h":(f+NU*e)*3.6,
            "X_N2":e/(2*f[0]),"nfev":sol.nfev,"equilibrium_extent_kmol_h":max_e*3.6}


def hot_heat_per_mol_NH3(T):
    def enthalpy(name):
        A,B,C,D,E,F,G,H=SHOMATE[name];t=T/1000
        return 1000*(DHF[name]+A*t+B*t*t/2+C*t**3/3+D*t**4/4-E/t+F-H)
    return enthalpy("NH3")-.5*enthalpy("N2")-1.5*enthalpy("H2")
