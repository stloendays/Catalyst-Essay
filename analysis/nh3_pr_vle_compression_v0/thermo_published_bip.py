"""Published binary interaction PR case, independent of BASF/industrial targets.

Source: Binous & Bellagi (2022), Engineering Reports, doi:10.1002/eng2.12506,
Table 8, binary PR parameters stated by authors as "obtained from Aspen-HYSYS":
  H2–N2   -0.036
  H2–NH3   0.000
  N2–NH3  +0.222

Only the H2/N2/NH3 entries are published by that table; missing 5-component
CH4/Ar cross pairs remain assumed k=0. NOT a source-validated cold-separator
mixture model. Values are EXTERNAL (not fitted to the BASF 28/Uhde stages).
"""
from __future__ import annotations
import math

from thermo_pr import (
    COMPONENTS, R, SQRT2, EosDomainError, EosConvergenceError,
    pure_parameters, normalized, cubic_real_roots,
)

PUBLISHED_BIP={frozenset(("H2","N2")):-0.036,
               frozenset(("N2","NH3")):0.222}
PROVENANCE_URL="https://doi.org/10.1002/eng2.12506"
SOURCE_SCOPE="2022 Table 8 Aspen-HYSYS PR for Haber synthesis conditions; cold 0-30C industrial separator transfer is unvalidated"
MISSING_PAIR_POLICY="All pairs involving CH4/Ar are assumed kij=0, NOT source measured"


def interaction(i:str,j:str)->float:
    if i==j:return 0.0
    if i not in COMPONENTS or j not in COMPONENTS:
        raise EosDomainError("Unknown interaction component")
    return PUBLISHED_BIP.get(frozenset((i,j)),0.0)


def external_pr_phase(T_K:float,P_Pa:float,z:dict[str,float],phase:str="vapor")->dict:
    """Exactly PR78 phi_i as baseline, with sourced k_ij instead of all-zero."""
    if not(0<P_Pa<1e10 and math.isfinite(P_Pa)):
        raise EosDomainError("Invalid absolute source pressure")
    if phase not in ("liquid","vapor"):
        raise EosDomainError("Invalid phase request")
    x=normalized(z,allow_missing=True)
    a,b=pure_parameters(T_K)
    sums={i:sum(x[j]*math.sqrt(a[i]*a[j])*(1.0-interaction(i,j))
                for j in COMPONENTS) for i in COMPONENTS}
    am=sum(x[i]*sums[i] for i in COMPONENTS)
    bm=sum(x[i]*b[i] for i in COMPONENTS)
    A=am*P_Pa/(R**2*T_K**2)
    B=bm*P_Pa/(R*T_K)
    zz_candidates=[z for z in cubic_real_roots(A,B) if z>B+1e-12]
    if not zz_candidates:
        raise EosConvergenceError("No real PR Z root under external BIP")
    Z=min(zz_candidates) if phase=="liquid" else max(zz_candidates)
    logterm=math.log((Z+(1+SQRT2)*B)/(Z+(1-SQRT2)*B))
    scalar=A*logterm/(2*SQRT2*B)
    phi={}
    for k in COMPONENTS:
        lnphi=b[k]/bm*(Z-1)-math.log(Z-B)-scalar*(2*sums[k]/am-b[k]/bm)
        if not math.isfinite(lnphi):
            raise EosConvergenceError("Nonfinite PR external phi")
        phi[k]=math.exp(lnphi)
    return {
        "Z":Z,"phi":phi,"A":A,"B":B,
        "binary_interaction":"PUBLISHED_HYSYS_TABLE8_2022__MISSING_PAIRS_ZERO",
        "phase":phase,
    }


def external_nh3_vapor_over_pure_liquid(T_K:float,P_Pa:float,dry:dict[str,float])->dict:
    """NH3 vapor fugacity equals pure-NH3 liquid fugacity at source P,T.

    Missing liquid solubility and NH3 association remains a known structural
    approximation; external kij alone cannot correct the pure-liquid model.
    """
    drygas=normalized({**dry, "NH3":0.0},allow_missing=True)
    liquid=external_pr_phase(T_K,P_Pa,{"NH3":1},"liquid")
    logliq=math.log(liquid["phi"]["NH3"])
    def fn(y):
        z={k:drygas[k]*(1-y) for k in COMPONENTS}
        z["NH3"]=y
        return (math.log(y)+math.log(external_pr_phase(T_K,P_Pa,z,"vapor")["phi"]["NH3"])-logliq)
    lo,hi=1e-10,.5
    vlo,vhi=fn(lo),fn(hi)
    if vlo*vhi>0:
        raise EosConvergenceError("NH3 source mixture 0–50% root not bracketed")
    for _ in range(90):
        mid=(lo+hi)/2
        if fn(mid)*vlo>0:
            lo=mid;vlo=fn(mid)
        else:
            hi=mid
    y=(lo+hi)/2
    return {"y_NH3_molpct":100*y,
            "fugacity_log_residual":fn(y),
            "external_source":PROVENANCE_URL,
            "model_scope":"published HYSYS 3component BIP transfer + 5component missing pairs zero",
            "no_target_fitting":True}
