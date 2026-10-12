"""Cholewa et al. (2024) Fe/Ru-CeO2 published final fitted Eqs 11/12 + NIST thermo.

ISOLATED and UNFROZEN: no Ru/C industrial fit, no NH3-FINAL-1.1 modification.
Paper: doi:10.1039/D4SE00254G; NIST WebBook Shomate; comparison:
Tripodi et al. doi:10.1021/acs.iecr.0c05350 (Ru/C, different material).
"""
from dataclasses import dataclass, replace
from functools import lru_cache
import math
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from eos import srk_phi

R = 8.314462618
# NIST 1-bar Shomate A..H: all studies >= 623.15 K
SHOMATE = {
    "N2": (19.50583, 19.88705, -8.598535, 1.369784, 0.527601, -4.935202, 212.3900, 0.0),
    "H2": (33.066178, -11.363417, 11.432816, -2.772874, -0.158558, -9.980797, 172.707974, 0.0),
    "NH3": (19.99563, 49.77119, -15.37599, 1.921168, 0.189174, -53.30667, 203.8591, -45.89806),
}

@dataclass(frozen=True)
class Catalyst:
    name: str
    k0: float
    ea: float
    alpha: float
    adsorption_h2: tuple | None = None
    adsorption_nh3: tuple | None = None

# Cholewa 2024 Table 2/3. Ru material is Ru/CeO2, not promoted Ru/C.
FE = Catalyst("Fe", 3.35e9, 144e3, 0.5, None, (-15.60e3, -24.4, 0.261))
RU_CEO2 = Catalyst("Ru/CeO2", 3.49e8, 106e3, 0.25,
                   (-87.10e3, -80.1, 0.116), (-11.84e3, -143.0, 0.414))

def shomate_h_s(species, T):
    if not 623.15 <= T <= 723.15:
        raise ValueError("Outside 350-450 C study window")
    A,B,C,D,E,F,G,H = SHOMATE[species]
    t = T/1000.
    inc = A*t + B*t*t/2 + C*t**3/3 + D*t**4/4 - E/t + F - H
    ent = A*math.log(t) + B*t + C*t*t/2 + D*t**3/3 - E/(2*t*t) + G
    return (H+inc)*1000., ent

@lru_cache(maxsize=128)
def kp_full(T):
    """For N2+3H2=2NH3; full-reaction Kp is squared half-reaction K."""
    hs = {sp: shomate_h_s(sp, T) for sp in SHOMATE}
    dg = 2*(hs["NH3"][0]-T*hs["NH3"][1]) - (
        hs["N2"][0]-T*hs["N2"][1]) - 3*(hs["H2"][0]-T*hs["H2"][1])
    return math.exp(-dg/(R*T))

def activities(T, P_bar, flow, eos="ideal", kij=0.):
    if eos not in ("ideal", "srk"):
        raise ValueError("Invalid EOS")
    phi = (1.,1.,1.) if eos == "ideal" else srk_phi(T,P_bar,flow,kij)
    return tuple(flow[i]/sum(flow)*P_bar*phi[i] for i in range(3))

def rate(cat, T, P_bar, flow, gain=1., eos="ideal", kij=0.):
    """Cholewa et al. (2024) *fitted* Eqs 11/12, mol NH3/(kg_cat s).

    Uses half-reaction K_eq=sqrt(K_full), aN2**0.5, H2**(1.5 alpha),
    and Ru hydrogen adsorption aH2**(1.5 f2). The old branch used
    Eq.3's full-reaction powers, which IS NOT Eq.11/12, and that
    version's 17.23x break-even must NOT be cited.
    The source Ru catalyst is Ru/CeO2; NOT commercial KAAP Ru/C.
    """
    if min(flow) <= 0 or P_bar <= 0 or gain <= 0:
        raise ValueError("Positive flows, P and gain required")
    n2,h2,nh3 = activities(T,P_bar,flow,eos,kij)
    z = nh3 / h2**1.5
    num = math.sqrt(kp_full(T))*math.sqrt(n2)*z**(-cat.alpha) - z**(1-cat.alpha)
    denominator = 1.
    if cat.adsorption_h2:
        dh, ds, exponent = cat.adsorption_h2
        denominator += math.exp(-dh/(R*T)+ds/R)*h2**(1.5*exponent)
    if cat.adsorption_nh3:
        dh, ds, exponent = cat.adsorption_nh3
        denominator += math.exp(-dh/(R*T)+ds/R)*nh3**exponent
    return gain*cat.k0*math.exp(-cat.ea/(R*T))*num/denominator

def equilibrium_extent(T, P_bar, inlet, eos="ideal", kij=0.):
    n2,h2,nh3 = inlet
    xmax = min(n2,h2/3)
    def objective(x):
        a,b,c = activities(T,P_bar,(n2-x,h2-3*x,nh3+2*x),eos,kij)
        return math.log(c*c/(a*b**3)) - math.log(kp_full(T))
    return brentq(objective,0.,xmax*(1-1e-11),xtol=1e-12) if (
        objective(0.)*objective(xmax*(1-1e-11)) < 0) else 0.

def stage(inlet, cat, T, P_bar, mass_kg, gain=1., eos="ideal", kij=0.):
    if mass_kg < 0:
        raise ValueError("Nonnegative mass required")
    if mass_kg == 0:
        return inlet
    n2,h2,nh3 = inlet
    xmax = min(n2,h2/3)
    def rhs(w,y):
        x = min(max(float(y[0]),0.),xmax*(1-1e-12))
        return [rate(cat,T,P_bar,(n2-x,h2-3*x,nh3+2*x),gain,eos,kij)/2]
    sol = solve_ivp(rhs,[0,mass_kg],[0.],method="LSODA",rtol=2e-8,
                    atol=1e-10,max_step=max(mass_kg/30,1e-5))
    if not sol.success:
        raise RuntimeError(sol.message)
    x=float(sol.y[0,-1])
    if x < -1e-9 or x > xmax+1e-9:
        raise ArithmeticError("Stoichiometry violated")
    return n2-x,h2-3*x,nh3+2*x

def bed_sequence(inlet, sequence, masses, temperatures, P_bar,
                 ru_gain=1., eos="ideal", kij=0., ru_h2_shift_j=0.):
    if not (len(sequence)==len(masses)==len(temperatures)):
        raise ValueError("Length mismatch")
    flow=inlet
    legs=[]
    for key,mass,T in zip(sequence,masses,temperatures):
        cat={"Fe":FE,"Ru":RU_CEO2}[key]
        if key=="Ru" and ru_h2_shift_j:
            if abs(ru_h2_shift_j)>30000:
                raise ValueError("Outside prespecified adsorption sensitivity")
            dH,dS,exponent=cat.adsorption_h2
            cat=replace(cat,adsorption_h2=(dH+ru_h2_shift_j,dS,exponent))
        newer=stage(flow,cat,T,P_bar,mass,ru_gain if key=="Ru" else 1.,eos,kij)
        legs.append(dict(catalyst=key,T_C=T-273.15,mass_kg=mass,inlet=flow,outlet=newer))
        flow=newer
    return dict(sequence=sequence,outlet=flow,X_N2=(inlet[0]-flow[0])/inlet[0],legs=legs)
