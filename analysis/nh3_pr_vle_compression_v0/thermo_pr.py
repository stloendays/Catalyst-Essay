#!/usr/bin/env python3
"""PR78 cubic-EOS research baseline for NH3/N2/H2/CH4/Ar.

No data fitting, NO binary interaction parameters, no plant-EOS validation
claimed. Used for falsification against independent Ullmann/BASF saturation
data and for source-conditioned Figure 57 phase/compression estimates.

Primary thermodynamic references:
  Peng, D.-Y. & Robinson, D. B. (1976), doi:10.1021/i160057a011.
Pure critical point + acentric data:
  CoolProp 8.0 individual fluid information:
  https://coolprop.org/fluid_properties/fluids/{Ammonia,Nitrogen,Hydrogen,Methane,Argon}.html

The zero-kij assumption is a deliberate hypothesis, NOT a fitted interaction
model. NH3 association + high-pressure H2 mixtures may invalidate it.
"""
from __future__ import annotations

import math
from typing import NamedTuple

R = 8.31446261815324  # J mol-1 K-1
SQRT2=math.sqrt(2.0)
COMPONENTS=("N2","H2","CH4","Ar","NH3")
# Tc [K], Pc [Pa], omega [-], sources above (CoolProp fluid information).
CRITICAL={
    "N2":  (126.192,    3_395_800.444647145,  0.0372),
    "H2":  (33.1443326883, 1_296_357.6060553,-0.219),
    "CH4": (190.5640026513, 4_599_200.4742824,0.01142),
    "Ar":  (150.687,    4_863_000.544876669,-0.00219),
    "NH3": (405.5599999733,11_363_391.157414673,0.2556905229865023),
}
PR_OMEGA_A=0.45724
PR_OMEGA_B=0.07780


class EosDomainError(ValueError):
    pass


class EosConvergenceError(RuntimeError):
    pass


def normalized(z: dict[str,float], *, allow_missing: bool=False) -> dict[str,float]:
    extra=set(z)-set(COMPONENTS)
    if extra or (not allow_missing and set(z)!=set(COMPONENTS)):
        raise EosDomainError(f"Component names differ from five-component model: extra={extra}")
    out={k:float(z.get(k,0.0)) for k in COMPONENTS}
    if not all(math.isfinite(v) and v>=0.0 for v in out.values()):
        raise EosDomainError("Invalid mixture fraction")
    sm=sum(out.values())
    if sm<=0.0:
        raise EosDomainError("Zero total gas")
    return {k:val/sm for k,val in out.items()}


def pure_parameters(T_K:float) -> tuple[dict[str,float],dict[str,float]]:
    if not (T_K>0 and math.isfinite(T_K)):
        raise EosDomainError("Temperature must be positive kelvin")
    a,b={},{}
    for k,(Tc,Pc,omega) in CRITICAL.items():
        kappa=0.37464+1.54226*omega-0.26992*omega*omega
        alpha=(1.0+kappa*(1.0-math.sqrt(T_K/Tc)))**2
        a[k]=PR_OMEGA_A*R**2*Tc**2/Pc*alpha
        b[k]=PR_OMEGA_B*R*Tc/Pc
    return a,b


def cubic_real_roots(A:float,B:float) -> list[float]:
    """Solve Z^3-(1-B)Z^2+(A-3B²-2B)Z-(AB-B²-B³)=0."""
    aa=-(1.0-B)
    bb=A-3.0*B*B-2.0*B
    cc=-A*B+B*B+B**3
    p=bb-aa*aa/3.0
    q=2.0*aa**3/27.0-aa*bb/3.0+cc
    disc=q*q/4.0+p**3/27.0
    if disc>=-1e-13:
        if disc>=0:
            sqrt_disc=math.sqrt(disc)
            return [math.cbrt(-q/2.0+sqrt_disc)+math.cbrt(-q/2.0-sqrt_disc)-aa/3.0]
        # Handle near-multiple roots without treating a complex pair as real.
    if p>=0:  # numerical boundary
        return [math.cbrt(-q)-aa/3.0]
    v=2.0*math.sqrt(-p/3.0)
    acos_arg=-q/(2.0*math.sqrt(-(p/3.0)**3))
    theta=math.acos(max(-1.0,min(1.0,acos_arg)))
    rr=sorted([v*math.cos((theta-2.0*math.pi*j)/3.0)-aa/3.0 for j in range(3)])
    out=[]
    for x in rr:
        if not out or abs(out[-1]-x)>1e-9:
            out.append(x)
    return out


def eos_phase(T_K:float,P_Pa:float,z:dict[str,float], phase:str="vapor")->dict:
    """Classical PR mixture with van der Waals one-fluid mixing, kij=0."""
    if not (0<P_Pa<1e10 and math.isfinite(P_Pa)):
        raise EosDomainError("Invalid absolute pressure (Pa)")
    if phase not in ("liquid","vapor"):
        raise EosDomainError("Phase selection must be liquid or vapor")
    x=normalized(z,allow_missing=True)
    a,b=pure_parameters(T_K)
    sums={i:sum(x[j]*math.sqrt(a[i]*a[j]) for j in COMPONENTS) for i in COMPONENTS}
    am=sum(x[i]*sums[i] for i in COMPONENTS)
    bm=sum(x[i]*b[i] for i in COMPONENTS)
    A=am*P_Pa/(R*R*T_K*T_K)
    B=bm*P_Pa/(R*T_K)
    roots=[v for v in cubic_real_roots(A,B) if v>B+1e-12]
    if not roots:
        raise EosConvergenceError(f"No physical PR root at T={T_K}, P={P_Pa}")
    zz=min(roots) if phase=="liquid" else max(roots)
    argument=(zz+(1.0+SQRT2)*B)/(zz+(1.0-SQRT2)*B)
    if zz<=B or argument<=0:
        raise EosConvergenceError("Invalid fugacity logarithm")
    logr=math.log(argument)
    c=A*logr/(2*SQRT2*B)
    phi={}
    for k in COMPONENTS:
        lnphi=b[k]/bm*(zz-1.0)-math.log(zz-B)-c*(2*sums[k]/am-b[k]/bm)
        if not math.isfinite(lnphi) or abs(lnphi)>700:
            raise EosConvergenceError("Nonfinite fugacity coefficient")
        phi[k]=math.exp(lnphi)
    return {"Z":zz,"phi":phi,"roots":roots,"A":A,"B":B,
            "phase_root_selection":phase,"binary_interaction_kij":"ZERO_ALL_PAIRS"}


def saturated_vapor_over_pure_liquid_nh3(
    T_K:float,P_Pa:float,dry:dict[str,float]
)->dict:
    """PR fugacity equality for NH3 vapor over pure, pressurized liquid NH3.

    Dry-gas ratios are supplied exogenously and never inferred from the target
    NH3 vapor mole fraction. Assumes NO N2/H2/CH4/Ar liquid solubility.
    This approximation is NOT a five-component TP flash.
    """
    dryx=normalized({**dry,"NH3":0.0},allow_missing=True)
    fl=eos_phase(T_K,P_Pa,{"NH3":1.0},phase="liquid")
    log_liq=math.log(fl["phi"]["NH3"])
    def residual(y:float)->float:
        vapor={k:(1.0-y)*dryx[k] for k in COMPONENTS}
        vapor["NH3"]=y
        v=eos_phase(T_K,P_Pa,vapor,phase="vapor")
        return math.log(y)+math.log(v["phi"]["NH3"])-log_liq
    left,right=1e-10,0.5
    vl,vr=residual(left),residual(right)
    if vl*vr>0:
        raise EosConvergenceError("NH3 saturated-vapor root not bracketed within 0–50 mol%")
    for _ in range(90):
        mid=(left+right)/2.0
        val=residual(mid)
        if val*vl>0:
            left=mid;vl=val
        else:
            right=mid
    y=0.5*(left+right)
    return {"y_NH3":y,
            "y_NH3_molpct":100*y,
            "vapor_fugacity_PR_Pa":eos_phase(
                T_K,P_Pa,{**{k:(1-y)*dryx[k] for k in dryx}, "NH3":y},"vapor"
            )["phi"]["NH3"]*y*P_Pa,
            "liquid_fugacity_PR_Pa":fl["phi"]["NH3"]*P_Pa,
            "model":"PR78_NO_KIJ_PURE_LIQUID_APPROXIMATION",
            "liquid_inert_dissolution_included":False,
            "converged":True}


def ideal_wilson_K(T_K:float,P_Pa:float)->dict[str,float]:
    if T_K<=0 or P_Pa<=0:
        raise EosDomainError("Invalid physical state")
    return {i:(Pc/P_Pa)*math.exp(5.373*(1.0+w)*(1.0-Tc/T_K))
            for i,(Tc,Pc,w) in CRITICAL.items()}


def _rr_beta(z:dict[str,float],k:dict[str,float]) -> float|None:
    """Rachford–Rice liquid/vapor split; None means no interior root."""
    def fn(beta):
        return sum(z[j]*(k[j]-1.0)/(1.0+beta*(k[j]-1.0)) for j in COMPONENTS)
    f0,f1=fn(0),fn(1)
    if f0<=0 or f1>=0:
        return None
    lo,hi=0.0,1.0
    for _ in range(80):
        m=(lo+hi)/2.0
        if fn(m)>0:
            lo=m
        else:
            hi=m
    return 0.5*(lo+hi)


def flash_isothermal_isobaric_no_kij(
    T_K:float,P_Pa:float,z_input:dict[str,float],
    maxiter:int=320
)->dict:
    """No-fitted-parameter PR phi-phi flash.

    Returns explicit failure/no-two-phase status; no silent substitution of
    the industrial measured liquid split or staged-component quantities.
    The method is a *screening* calculation; liquid stability in polar gases
    at very high pressure is not guaranteed by root selection alone.
    """
    z=normalized(z_input,allow_missing=True)
    k=ideal_wilson_K(T_K,P_Pa)
    beta0=_rr_beta(z,k)
    if beta0 is None:
        return {"status":"NO_TWO_PHASE_BRACKET_FROM_WILSON_K",
                "screening_accepted":False,"z":z,
                "model":"PR78_ZERO_KIJ_NO_SOURCED_INTERACTION_DATA"}
    beta=beta0
    for it in range(maxiter):
        beta=_rr_beta(z,k)
        if beta is None:
            return {"status":"NO_TWO_PHASE_BRACKET_DURING_ITERATION",
                    "screening_accepted":False,"iteration":it,"z":z}
        x={j:z[j]/(1.0+beta*(k[j]-1.0)) for j in COMPONENTS}
        y={j:k[j]*x[j] for j in COMPONENTS}
        sx,sy=sum(x.values()),sum(y.values())
        if abs(sx-1)>1e-6 or abs(sy-1)>1e-6:
            raise EosConvergenceError("Rachford-Rice phase mole fractions not normalised")
        vl=eos_phase(T_K,P_Pa,x,"liquid")
        vv=eos_phase(T_K,P_Pa,y,"vapor")
        kratio={j:vl["phi"][j]/vv["phi"][j] for j in COMPONENTS}
        err=max(abs(math.log(k[j]/kratio[j])) for j in COMPONENTS)
        if err<1e-8:
            return {
                "status":"CONVERGED_TWO_PHASE_CANDIDATE",
                "screening_accepted":True,
                "iteration":it+1,
                "beta_vapor":beta,
                "vapor_y":y,
                "liquid_x":x,
                "Z_vapor":vv["Z"],"Z_liquid":vl["Z"],
                "fugacity_log_ratio_error_max":err,
                "phase_K":k,
                "mixture_model":"PR78_ZERO_KIJ",
                "stability_analysis_performed":False,
            }
        # The damping is a numerical solver control, not a binary interaction
        # or phase-property fit.
        for j in COMPONENTS:
            k[j]*=math.exp(0.5*math.log(kratio[j]/k[j]))
    return {"status":"FLASH_NO_CONVERGENCE","screening_accepted":False,
            "iteration":maxiter,"last_max_logK_error":err,
            "model":"PR78_ZERO_KIJ"}


def isothermal_compression_work(
    T_K:float,P1_Pa:float,P2_Pa:float,flow_kmol_h:float,
    z:dict[str,float], nseg:int=80,
)->dict:
    """Thermodynamic ∫ZRTdlnP reference for one fixed-T flow path.

    This is NOT a measured compressor shaft power, not a compressor-efficiency
    map, and not an unconditional plant energetic lower bound.
    """
    if not (0<P1_Pa<P2_Pa<1e10 and flow_kmol_h>0 and nseg>0 and nseg%2==0):
        raise EosDomainError("Invalid source compressor boundary/Simpson integration")
    z=normalized(z,allow_missing=True)
    lo,hi=math.log(P1_Pa),math.log(P2_Pa)
    step=(hi-lo)/nseg
    terms=[]
    for i in range(nseg+1):
        P=math.exp(lo+i*step)
        terms.append(eos_phase(T_K,P,z,"vapor")["Z"])
    integrate=(step/3.0)*(terms[0]+terms[-1]+4*sum(terms[1:-1:2])+2*sum(terms[2:-1:2]))
    n_mol_s=flow_kmol_h*1000.0/3600.0
    pr_MW=n_mol_s*R*T_K*integrate/1e6
    ideal_MW=n_mol_s*R*T_K*(hi-lo)/1e6
    return {
        "PR_isothermal_reversible_MW":pr_MW,
        "ideal_gas_isothermal_reversible_MW":ideal_MW,
        "PR_over_ideal":pr_MW/ideal_MW,
        "start_Z":terms[0],
        "end_Z":terms[-1],
        "inlet_P_bar":P1_Pa/1e5,
        "outlet_P_bar":P2_Pa/1e5,
        "T_C":T_K-273.15,
        "flow_kmol_h":flow_kmol_h,
        "eos":"PR78_ZERO_BINARY_INTERACTIONS",
        "scope":"fixed-T reversible compression path; excludes multistage temperature history, mechanical efficiency, auxiliary losses"
    }
