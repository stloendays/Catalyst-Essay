#!/usr/bin/env python3
"""Physically explicit, parameter-gated packed-bed Ergun pressure-drop layer.

No default reactor pellet size, packing void fraction, length/diameter, bulk
density, mixture viscosity or mean molecular weight is fabricated.

Analytical integrated isothermal, constant-composition/compressibility form:
   -dP/dz = 150*mu*(1-eps)^2/(phi*dp)^2/eps^3 * u
            + 1.75*rho*(1-eps)/(phi*dp)/eps^3 * u^2
with u(z) proportional to 1/P(z), rho(z) proportional to P(z).
Hence Pout^2=Pin^2 - 2 Pin |dP/dz|_in L.

For candidate-dependent reaction composition and non-isothermal reactor
behaviour, use a distributed reactor model instead: this is an inlet-property
hydraulic feasibility SCREEN, not a pressure-drop-validated reactor model.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

R_J_MOL_K = 8.31446261815324
PA_PER_BAR = 100000.
MOL_PER_KMOL = 1000.
SECONDS_PER_H = 3600.


@dataclass(frozen=True)
class BedGeometry:
    parallel_beds: int
    length_m: float
    inner_diameter_m: float
    pellet_diameter_m: float
    pellet_sphericity: float
    void_fraction: float
    packed_bulk_density_kg_m3: float

    def __post_init__(self):
        if isinstance(self.parallel_beds, bool) or not isinstance(self.parallel_beds, int) or self.parallel_beds <= 0:
            raise ValueError("parallel_beds must be a positive integer")
        for key in ("length_m", "inner_diameter_m", "pellet_diameter_m",
                    "pellet_sphericity", "void_fraction", "packed_bulk_density_kg_m3"):
            v = getattr(self, key)
            if not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                raise ValueError(f"{key} must be a finite positive measured value")
        for key in ("pellet_sphericity", "void_fraction"):
            if not 0 < getattr(self, key) < 1:
                raise ValueError(f"{key} must be in (0,1)")

    @property
    def one_bed_area_m2(self):
        return math.pi * self.inner_diameter_m ** 2 / 4.

    @property
    def volume_m3(self):
        return self.parallel_beds * self.one_bed_area_m2 * self.length_m

    @property
    def total_catalyst_capacity_t(self):
        return self.volume_m3 * self.packed_bulk_density_kg_m3 / 1000.


@dataclass(frozen=True)
class GasInlet:
    pressure_bar: float
    temperature_K: float
    total_flow_kmol_h: float
    viscosity_Pa_s: float
    mean_molecular_weight_kg_mol: float
    compressibility_Z: float

    def __post_init__(self):
        for key in ("pressure_bar", "temperature_K", "viscosity_Pa_s",
                    "mean_molecular_weight_kg_mol", "compressibility_Z"):
            x = getattr(self, key)
            if not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0:
                raise ValueError(f"{key} must be positive and measured/specified")
        if not isinstance(self.total_flow_kmol_h, (int, float)) or not math.isfinite(self.total_flow_kmol_h) or self.total_flow_kmol_h < 0:
            raise ValueError("total_flow_kmol_h must be finite and >=0")


def ergun(geometry: BedGeometry, gas: GasInlet):
    """Return Ergun integrated isothermal pressure drop and bed capacity.

    At large losses, return isothermal_no_positive_outlet=False rather than
    silently clipping sqrt(P_out^2) or claiming the bed is feasible.
    """
    pin = gas.pressure_bar * PA_PER_BAR
    dp_eff = geometry.pellet_diameter_m * geometry.pellet_sphericity
    flow_mol_s = gas.total_flow_kmol_h * MOL_PER_KMOL / SECONDS_PER_H
    q_m3_s = (flow_mol_s * gas.compressibility_Z * R_J_MOL_K *
              gas.temperature_K / pin)
    superficial_u_m_s = q_m3_s / (geometry.parallel_beds * geometry.one_bed_area_m2)
    rho_kg_m3 = pin * gas.mean_molecular_weight_kg_mol / (
        gas.compressibility_Z * R_J_MOL_K * gas.temperature_K)
    eps = geometry.void_fraction
    viscous_gradient_Pa_m = (150. * gas.viscosity_Pa_s * (1.-eps)**2 /
                              (eps**3 * dp_eff**2) * superficial_u_m_s)
    inertial_gradient_Pa_m = (1.75 * rho_kg_m3 * (1.-eps) /
                               (eps**3 * dp_eff) * superficial_u_m_s**2)
    inlet_gradient_Pa_m = viscous_gradient_Pa_m + inertial_gradient_Pa_m
    radicand = pin**2 - 2. * pin * inlet_gradient_Pa_m * geometry.length_m
    valid = radicand > 0
    p_out = math.sqrt(radicand) if valid else math.nan
    drop_bar = (pin-p_out)/PA_PER_BAR if valid else math.nan
    return {
        "model": "Ergun; isothermal idealized packed bed with constant mu, MW, Z, T and molar flow",
        "reactor_inlet_pressure_bar": gas.pressure_bar,
        "reactor_outlet_pressure_bar": p_out/PA_PER_BAR if valid else None,
        "predicted_bed_pressure_drop_bar": drop_bar if valid else None,
        "constant_inlet_gradient_pressure_drop_bar": inlet_gradient_Pa_m *
            geometry.length_m/PA_PER_BAR,
        "isothermal_positive_outlet_exists": valid,
        "superficial_velocity_m_s": superficial_u_m_s,
        "inlet_mixture_density_kg_m3": rho_kg_m3,
        "inlet_viscous_dPdz_Pa_m": viscous_gradient_Pa_m,
        "inlet_inertial_dPdz_Pa_m": inertial_gradient_Pa_m,
        "inlet_total_dPdz_Pa_m": inlet_gradient_Pa_m,
        "bed_volume_total_m3": geometry.volume_m3,
        "catalyst_capacity_total_t": geometry.total_catalyst_capacity_t,
        "parallel_beds": geometry.parallel_beds,
        "all_parameters_from_verified_source": False,
    }


def ensure_feasible(hydraulic_result, *, maximum_dp_bar, required_catalyst_t):
    """Check BOTH a physically specified allowable pressure loss and bed inventory."""
    for key, val in (("maximum_dp_bar", maximum_dp_bar), ("required_catalyst_t", required_catalyst_t)):
        if not isinstance(val, (int,float)) or not math.isfinite(val) or val <= 0:
            raise ValueError(key + " must be explicitly supplied as a positive number")
    if not hydraulic_result["isothermal_positive_outlet_exists"]:
        return dict(feasible=False, reason="no positive outlet pressure under model")
    dp = hydraulic_result["predicted_bed_pressure_drop_bar"]
    capacity = hydraulic_result["catalyst_capacity_total_t"]
    allowed_dp = dp <= maximum_dp_bar + 1e-12
    allowed_mass = required_catalyst_t <= capacity + 1e-12
    return dict(feasible=allowed_dp and allowed_mass,
                pressure_drop_ok=allowed_dp, catalyst_bed_capacity_ok=allowed_mass,
                computed_pressure_drop_bar=dp, allowed_pressure_drop_bar=maximum_dp_bar,
                computed_inventory_t=required_catalyst_t, physical_bed_capacity_t=capacity,
                reason=("both pass" if allowed_dp and allowed_mass
                        else "pressure and/or catalyst volume constraint fails"))


# Explicitly mirror the original generalized methanol economy cost structure.
# Repricing the RECYCLE compressor with Ergun DeltaP is a one-way sensitivity:
# the original reaction/outlet equilibrium is not yet recomputed at P_out.
def recost_recycle_from_dP(existing_model_state, inlet_pressure_bar, hydraulic_drop_bar):
    """Reprice compressor electricity and module CAPEX without mutating source model.

    When hydraulic_drop_bar equals original M.LOOP_DP_BAR, should reproduce the
    original G.cost exactly. This is a regression check, not validation of the
    isothermal Ergun assumptions or the flow-composition-dependent kinetics.
    """
    import numpy as np
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "data/meoh"))
    import meoh_general_model as G
    M=G.M
    if not math.isfinite(hydraulic_drop_bar) or hydraulic_drop_bar < 0:
        raise ValueError("hydraulic drop must be finite >=0")
    if hydraulic_drop_bar >= inlet_pressure_bar - 1:
        raise ValueError("hydraulic drop leaves no valid recycle compressor suction")
    original_rec_power=np.asarray(existing_model_state["P_rec_MW"], dtype=float)
    recycle_kmol_h=np.asarray(existing_model_state["recycle_kmol_h"], dtype=float)
    new_rec_power=G.compressor_power_MW(
        recycle_kmol_h, max(1., inlet_pressure_bar-hydraulic_drop_bar), inlet_pressure_bar)
    ref_power=float(M.REF_POWERS[2])
    ref_ec=float(M.EC_REF["Recycle/reflux compressor"])
    old_rec_ec=ref_ec * (original_rec_power/ref_power)**M.EXP_COMP
    new_rec_ec=ref_ec * (new_rec_power/ref_power)**M.EXP_COMP
    ec_new=np.asarray(existing_model_state["EC_MEUR"], dtype=float) - old_rec_ec + new_rec_ec
    fci_new=M.LF * ec_new
    acc_new=fci_new*M.CRF + fci_new/9.*M.IR
    direct_new=(np.asarray(existing_model_state["direct_MEUR_Y"],dtype=float)
                +(new_rec_power-original_rec_power)*M.HOURS_Y*M.ELEC_EUR_MWH/1e6)
    npc_new=(acc_new+direct_new+2.2125*M.SOURCE_OL_MEUR_Y+.081*fci_new)/.90
    return {
        "original_recycle_MW": original_rec_power,
        "hydraulic_repriced_recycle_MW": new_rec_power,
        "hydraulic_repriced_NPC_EUR_t": npc_new*1e6/M.PROD_TPY,
        "delta_NPC_EUR_t": npc_new*1e6/M.PROD_TPY -
            np.asarray(existing_model_state["cost_eur_t"],dtype=float),
        "recycle_compressor_capex_old_MEUR": old_rec_ec,
        "recycle_compressor_capex_new_MEUR": new_rec_ec,
        "deltaP_input_bar": hydraulic_drop_bar,
        "warning": "Partial compressor correction only; reaction pressure, bed kinetics and heat transfer not reoptimized."
    }


REQUIRED_GEOMETRY = (
    "parallel_beds", "length_m", "inner_diameter_m", "pellet_diameter_m",
    "pellet_sphericity", "void_fraction", "packed_bulk_density_kg_m3",
)
REQUIRED_FLUID = (
    "pressure_bar", "temperature_K", "total_flow_kmol_h",
    "viscosity_Pa_s", "mean_molecular_weight_kg_mol", "compressibility_Z",
)
REQUIRED_CONSTRAINTS = ("maximum_allowable_bed_deltaP_bar", "required_catalyst_inventory_t")


def inspect_inputs(values: dict[str, Any]):
    missing=[]
    for section, names in (("geometry",REQUIRED_GEOMETRY),("fluid",REQUIRED_FLUID),
                           ("physical_constraints",REQUIRED_CONSTRAINTS)):
        data=values.get(section)
        if not isinstance(data,dict):
            missing.extend(section+"."+name for name in names)
            continue
        missing.extend(section+"."+name for name in names if data.get(name) is None)
    return missing


def process(values: dict[str, Any]):
    missing=inspect_inputs(values)
    if missing:
        return {
            "status":"blocked_missing_physical_measurements",
            "missing_required_source_fields":missing,
            "model_1p5_bar": "The frozen 1.5-bar loop pressure loss is an ASSUMPTION; it cannot fill measured reactor geometry or allowable bed loss.",
            "n_experimentally_validated_geometry_designs":0,
            "any_pressure_drop_claim":False,
        }
    geometry=BedGeometry(**{k:values["geometry"][k] for k in REQUIRED_GEOMETRY})
    fluid=GasInlet(**{k:values["fluid"][k] for k in REQUIRED_FLUID})
    result=ergun(geometry,fluid)
    constraint=values["physical_constraints"]
    feasible=ensure_feasible(result,
        maximum_dp_bar=constraint["maximum_allowable_bed_deltaP_bar"],
        required_catalyst_t=constraint["required_catalyst_inventory_t"])
    return {
        "status":"parameterized_hydraulic_screen_not_independent_reactor_validation",
        "ergun":result, "design_feasibility":feasible,
        "n_experimentally_validated_geometry_designs": (
            1 if values.get("source_verified",False) is True else 0),
        "any_pressure_drop_claim":True,
        "source_verified":bool(values.get("source_verified",False)),
        "source_note":values.get("source_note") or "",
        "warning":"Screen depends on user-supplied bed/mixture state and isothermal approximation; cannot substitute for fully coupled compressor and kinetic reactor model.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--require-complete",action="store_true",
                   help="Fail closed rather than inventing geometry or gas properties.")
    args=p.parse_args()
    values=json.loads(args.input.read_text(encoding="utf-8"))
    out=process(values)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,default=float)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,default=float))
    if args.require_complete and out["status"]=="blocked_missing_physical_measurements":
        raise SystemExit("Required measured bed/mixture inputs missing: NO physical feasibility claim permitted")


if __name__=="__main__":
    main()
