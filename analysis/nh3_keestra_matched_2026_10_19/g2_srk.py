"""Independent NH3/H2/N2 SRK fugacity replication from original Fe 2025 SI.

Source: Keestra et al. (2025) CEJ 518, 164593, Supplement A-5-1
Python EOS, and A-6 Tables 17-18. Publisher SI SHA256:
b43f9988b4b5f69d824409e706c1c1b8862afb523a2b18cb053f7c286465773a
Exact source snippet is audited separately in g2_fe_source_audit.py.

Important SOURCE ANOMALY: source code computes
  a_ij = sqrt(alpha_i alpha_j)*sqrt(a_i a_j)*(1-kij)
with a_i = a_ci * alpha_i, thus adding EXTRA alpha_i alpha_j^0.5
on top of the conventional SRK square-root mixing rule. Both
literal_source and conventional are retained as distinct scenarios;
nothing is "corrected" post hoc for target GHSV reproduction.

Only three gas species appear in the source Table 4 final-bed feed:
N2, H2, NH3. The original SI also covers Ar, He, H2O, whose
printed species-order commentary and properties appear inconsistent.
No unreported inerts are invented for the final-bed reproduction.

The source did not provide its Aspen PLUS enthalpy-model selection in
the same Python snippet. See g2_adiabatic.py for independently
sourced NIST Cp model and a separately labelled SRK departure mode.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

R=8.31446261815324
SPECIES=("N2","H2","NH3")
P_CRIT=np.array([3.4e6,1.313e6,11.28e6],dtype=float)
T_CRIT=np.array([126.2,33.19,405.65],dtype=float)
ACENTRIC=np.array([0.0377215,-0.215993,0.252608],dtype=float)
POLAR=np.array([0.0,0.0,-0.23677368013887007],dtype=float)
KIJ=np.array([
   [0.0,-1.00000004749745e-03,0.225700005888939],
   [-1.00000004749745e-03,0.0,0.0],
   [0.225700005888939,0.0,0.0]
],dtype=float)
SOURCE_SI_SHA256="b43f9988b4b5f69d824409e706c1c1b8862afb523a2b18cb053f7c286465773a"


@dataclass(frozen=True)
class SRKState:
    compressibility: float
    mole_fractions: tuple[float,float,float]
    phi: tuple[float,float,float]
    fugacity_bar: tuple[float,float,float]
    a_mix: float
    b_mix: float
    da_mix_dT: float
    gas_enthalpy_departure_J_per_mol: float
    source_mix_rule: str


def normalize(y):
    v=np.array([float(y[t]) if isinstance(y,dict) else float(y[i])
                 for i,t in enumerate(SPECIES)],dtype=float)
    if v.shape!=(3,) or not np.all(np.isfinite(v)) or np.any(v<0):
        raise ValueError("N2/H2/NH3 mixture nonfinite or negative")
    if abs(np.sum(v)-1.)>1e-10:raise ValueError("gas fractions not normalized")
    return v


def pure(T_K:float):
    """Source SI A-5-1, lines 47-52; also analytical temperature derivative."""
    T=float(T_K)
    if not (400<T<1500 and math.isfinite(T)):raise ValueError("T outside kinetic study")
    a_c=.42747*R**2*T_CRIT**2/P_CRIT
    m=.4810+1.5963*ACENTRIC-.2963*ACENTRIC**2+.1223*ACENTRIC**3
    b=.08664*R*T_CRIT/P_CRIT
    tr=T/T_CRIT
    sq=np.sqrt(tr)
    g=1+m*(1-sq)-POLAR*(1-tr)*(.7-tr)
    gp=(-m/(2*T_CRIT*sq))-POLAR*((-1.7+2*tr)/T_CRIT)
    alpha=g**2
    dalpha=2*g*gp
    if np.any(alpha<=0) or not np.all(np.isfinite(alpha)):raise ArithmeticError("bad Mathias alpha")
    return a_c,b,alpha,dalpha


def mixed(y,T,rule):
    if rule not in ("literal_source","conventional"):
        raise ValueError("must name source literal or conventional mixing rule")
    ac,b,alpha,dalpha=pure(T)
    sqrt_aa=np.sqrt(np.outer(ac,ac))
    if rule=="literal_source":
        # EXACT AS PRINTED in A-5-1: sqrt(outer(alpha))*sqrt(outer(ac*alpha)).
        aa=sqrt_aa*np.outer(alpha,alpha)*(1-KIJ)
        dln=np.outer(dalpha/alpha,np.ones(3))+np.outer(np.ones(3),dalpha/alpha)
    else:
        # Standard mixing rule as in SI A-5 text: sqrt(a_i*a_j)*(1-kij).
        aa=sqrt_aa*np.sqrt(np.outer(alpha,alpha))*(1-KIJ)
        dln=.5*(np.outer(dalpha/alpha,np.ones(3))+np.outer(np.ones(3),dalpha/alpha))
    daa=aa*dln
    am=float(y@aa@y)
    bm=float(y@b)
    dam=float(y@daa@y)
    if min(am,bm)<=0:raise ArithmeticError("nonphysical SRK mixture coefficients")
    return aa,b,am,bm,dam


def gas_root(A,B):
    """Max physically acceptable REAL root for the source SRK cubic.

    The original SI tries brent [0.5,3], then returns a possibly complex
    numpy root, finally 1 on failure. This implementation fails CLOSED
    rather than replacing an invalid state by Z=1.
    """
    if not (math.isfinite(A) and math.isfinite(B) and A>=0 and 0<=B<1):
        raise ArithmeticError(f"nonphysical A,B={A},{B}")
    roots=np.roots([1.,-1.,A-B-B*B,-A*B])
    real=sorted(float(x.real) for x in roots if abs(x.imag)<1e-8 and x.real>B+1e-12)
    if not real:raise ArithmeticError("no gas SRK Z root")
    return real[-1]


def evaluate(y,T_K:float,P_bar:float,*,rule="literal_source")->SRKState:
    """Vapor phase mixture fugacities at absolute P, exactly source EOS constants.

    Enthalpy departure is canonical SRK analytical formula; it is NOT
    claimed to reproduce unspecified Aspen HYSYS enthalpy conventions.
    """
    frac=normalize(y)
    P=float(P_bar)*1e5
    if not (math.isfinite(P) and P>0 and P<1.5e8):
        raise ValueError("absolute P must be finite, positive, SI-consistent")
    aa,b,am,bm,dam=mixed(frac,T_K,rule)
    A=am*P/(R*R*T_K*T_K)
    B=bm*P/(R*T_K)
    Z=gas_root(A,B)
    if Z<=B:raise ArithmeticError("invalid logarithm Z<=B")
    xja=frac@aa
    lnphi=(b/bm)*(Z-1.)-math.log(Z-B)\
       -(A/B)*((2.*xja/am)-(b/bm))*math.log1p(B/Z)
    if not np.all(np.isfinite(lnphi)):raise ArithmeticError("nonfinite log-phi")
    phi=np.exp(lnphi)
    fug=phi*frac*(P/1e5)
    if np.any(phi<=0) or not np.all(np.isfinite(phi)):raise ArithmeticError("bad phi")
    hres=R*T_K*(Z-1.)+(T_K*dam-am)/bm*math.log1p(B/Z)
    return SRKState(Z,tuple(frac),tuple(phi),tuple(fug),am,bm,dam,
                    float(hres),rule)
