"""2025 Keestra Fe/Ru source equations: G0/G1 ideal-fugacity screening ONLY.

The mathematical form and global coefficients come from Keestra CEJ
2025 164593 Eq.15/Table 2 and 2025 168541 Eqs.10-12/Table 3.
Source-specific factors are *not interchangeable between formulations*.
The full original fugacity model is polarity-corrected SRK; this module
does NOT claim to reproduce that EOS, the adiabatic final-bed example
or validated commercial plant kinetics.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import math
from pathlib import Path

R = 8.3145
ATM_BAR = 1.01325
HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class KineticModel:
    catalyst: str
    kA: float
    kB: float
    NA: float
    NB: float
    sqrtHA: float
    sqrtHB: float
    bcat: float
    bN: float

    @classmethod
    def from_locked(cls, name: str) -> "KineticModel":
        if name not in ("Fe", "Ru_CeO2", "Ru_Ba_K_C"):
            raise ValueError("Unknown catalyst identity: must use source-registered formulation")
        e = CONFIG["sourceFe"] if name == "Fe" else CONFIG["sourceRu"]
        p = e["parameters"]
        if name=="Ru_Ba_K_C":
            # Source-verified ORIGINAL SI A-1-4 Model D, Table 8, Liu (2013).
            # These are not tuned to the 5.8x/19x published reactor outputs.
            si = CONFIG["referenceTarget100Bar"]
            bcat = si["Ru_Ba_K_C_bcat"]
            bN = si["Ru_Ba_K_C_bN"]
            if si["specific_ru_parameters_source"]["source_sha256"] != (
                "a6137d61860d2c55905a12544d7792437592a02fcbed6b0d05c237d4a1569598"):
                raise ValueError("Original SI source hash pin changed")
            if bcat != 76.25 or bN != .8514:
                raise ValueError("Ru-Ba-K/C SI correction factor transcription changed")
        else:
            bcat=e["bcat"]
            bN=e.get("bN",1.0)
        return cls(name, p["k_A"], p["k_B_J_mol"], p["KN_A"], p["KN_B_J_mol"],
                   p["sqrtKH_A"], p["sqrtKH_B_J_mol"],bcat,bN)


def eq_constant(T_K: float) -> float:
    """Keestra Fe CEJ Eq.4; double negative in exponent => POSITIVE."""
    if not 400 < T_K < 1500 or not math.isfinite(T_K):
        raise ValueError("temperature outside safe numerical research envelope")
    return 1.3628e-6 * math.exp(51111.0 / (R * T_K))


def arrhenius(A: float, B: float, T_K: float, *, scale: float = 1.0) -> float:
    if not (math.isfinite(A) and math.isfinite(B) and math.isfinite(scale)):
        raise ValueError("nonfinite parameter")
    if A <= 0 or scale <= 0:
        raise ValueError("A and scale must be positive")
    return A * math.exp(-scale * B / (R * T_K))


def ideal_fugacity_bar(P_abs_bar: float, fractions: dict[str, float]) -> dict[str, float]:
    """f_i=y_i*P; explicitly not the authors' corrected-SRK fugacity."""
    if not math.isfinite(P_abs_bar) or P_abs_bar <= 0:
        raise ValueError("positive absolute pressure required")
    if any(not math.isfinite(v) or v < 0 for v in fractions.values()):
        raise ValueError("nonphysical gas fractions")
    if set(fractions) != {"N2", "H2", "NH3"} or not math.isclose(sum(fractions.values()),1.0,abs_tol=1e-10):
        raise ValueError("requires an explicitly normalized N2/H2/NH3 gas without inerts")
    return {k: P_abs_bar * v for k,v in fractions.items()}


def published_rate_mol_kg_s(model: KineticModel, T_K: float, fug_bar: dict[str, float]) -> float:
    """The 2025 Eq 15 / Eq 10-12, with a user-supplied fugacity model.

    NH3 production rate may be NEGATIVE beyond equilibrium; never clip
    to manufacture a positive forward or suppress decomposition.
    """
    Kf = eq_constant(T_K)
    fn, fh, fa = (float(fug_bar[s]) for s in ("N2", "H2", "NH3"))
    if not all(math.isfinite(z) for z in (fn, fh, fa)) or fn<=0 or fh<=0 or fa<0:
        raise ValueError("fN2,fH2 must be positive; fNH3 nonnegative; all finite")
    if not math.isfinite(model.bcat) or not math.isfinite(model.bN) or model.bcat<=0 or model.bN<=0:
        raise ValueError("invalid source catalyst-specific parameters")
    k = arrhenius(model.kA,model.kB,T_K)
    KN = arrhenius(model.NA,model.NB,T_K,scale=model.bN)
    sqrtKH = arrhenius(model.sqrtHA,model.sqrtHB,T_K)
    Q = (fa*fa)/(Kf*Kf*fn*fh**3)
    site_block = 1.0 + fa/(KN*fh**1.5) + sqrtKH*math.sqrt(fh)
    return model.bcat*k*fn*(1.0-Q)/(site_block*site_block)


def inlet_composition(*, ammonia_mole_fraction: float = 0.0, h2_n2_ratio: float = 3.0) -> dict[str, float]:
    if not (0.0 <= ammonia_mole_fraction < 1.0 and h2_n2_ratio > 0):
        raise ValueError("invalid inlet")
    free = 1.0-ammonia_mole_fraction
    yN2=free/(1.0+h2_n2_ratio)
    return {"N2":yN2,"H2":free-yN2,"NH3":ammonia_mole_fraction}


def rate_from_ideal_gas(model: KineticModel, Tc: float, P_bar_abs: float,
                        *, inlet_NH3: float=0.0, h2_n2_ratio: float=3.0) -> float:
    f=ideal_fugacity_bar(P_bar_abs,inlet_composition(
      ammonia_mole_fraction=inlet_NH3,h2_n2_ratio=h2_n2_ratio))
    return published_rate_mol_kg_s(model,Tc+273.15,f)


def isothermal_ideal_pfr(model: KineticModel, Tc: float, P_bar_abs: float,
                         W_over_F0_kg_s_per_mol: float=12.0, nsteps: int=3200) -> dict:
    """Illustrative ideal-fugacity, ISOTHERMAL PFR at H2/N2=3, no inlet NH3.

    Reaction extent x = mol NH3 produced / original mol gas feed:
       nN2=0.25-0.5*x; nH2=0.75-1.5*x; nNH3=x; n_total=1-x.
    For F0=1 mol/s, dx/d(W/F0) = r_NH3 in mol/kg/s.
    This is NOT Cholewa's measured adiabatic/axial temperature profile,
    and is NOT Keestra's adiabatic final-bed reproduction.
    """
    if W_over_F0_kg_s_per_mol<=0 or not math.isfinite(W_over_F0_kg_s_per_mol):
        raise ValueError("W/F0 must be positive")
    if nsteps<32:raise ValueError("nsteps too small")
    T=Tc+273.15
    def f(x:float):
        if not (0<=x<0.49):
            raise ValueError(f"reactor extent crossed chemical feasibility, x={x}")
        n={"N2":.25-.5*x,"H2":.75-1.5*x,"NH3":x}
        total=1.0-x
        fractions={a:b/total for a,b in n.items()}
        return published_rate_mol_kg_s(model,T,ideal_fugacity_bar(P_bar_abs,fractions))
    x=0.0
    step=W_over_F0_kg_s_per_mol/nsteps
    for _ in range(nsteps):
        k1=f(x)
        k2=f(x+0.5*step*k1)
        k3=f(x+0.5*step*k2)
        k4=f(x+step*k3)
        x+=step*(k1+2*k2+2*k3+k4)/6
        if x<0 or x>=.49:
            raise ValueError("nonphysical integrated reactor extent")
    return {"x_mol_NH3_per_mol_inlet":x,
            "outlet_yNH3":x/(1.-x),
            "N2_fraction_converted":x/(2*.25),
            "W_over_F0_kg_s_per_mol":W_over_F0_kg_s_per_mol,
            "nsteps":nsteps,
            "physical_classification":"ideal-fugacity, isothermal screening, not externally validated absolute yield"}
