#!/usr/bin/env python3
"""Post-outcome source-GHSV forward diagnostic, NOT target-fitting.

At authors' printed GHSV h^-1 (22,250 Fe, 130,000 Ru), integrate each
locked source kinetic model forward to predict NH3 composition and the
fraction of our *model's* adiabatic equilibrium extent reached. Do NOT
adjust reaction-rate factors, heat capacities, EOS parameters or GHSV
to match the paper. Compare with the authors' stated ~90% criterion.

This is a POST-OUTCOME diagnostic added after the G2 calculations
failed for the Ru catalyst, not a preregistered independent validation.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
from pathlib import Path
from scipy.integrate import quad
from scipy.optimize import brentq

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import g2_adiabatic as G
import kinetics as K


def measured_GHSV_forward(bed:G.Bed, model:K.KineticModel):
    """Evaluate a forward reactor at an author-PUBLISHED bed GHSV.

    Published GHSV is used as the specified operating configuration ONLY
    in THIS forward audit. It is not a parameter or output target for
    independent, previous GHSV sizing calculations.
    """
    source_GHSV=float(G.SOURCE_REPORT_GHSV[model.catalyst])
    implied_W_over_F0=G.RHO[model.catalyst]*G.VM_NTP*3600./source_GHSV
    assert implied_W_over_F0>0 and math.isfinite(implied_W_over_F0)
    xe=bed.eq_extent()
    def inverse_rhs(x):
        st=bed.state(x)
        f={k:st["f_"+k+"_bar"] for k in ("N2","H2","NH3")}
        r=K.published_rate_mol_kg_s(model,st["T_K"],f)
        if r<=0 or not math.isfinite(r):
            raise ArithmeticError("kinetics sign invalid inside forward integration")
        return 2./r
    def wneeded(x):
        if x<=0:return 0.
        ans,err=quad(inverse_rhs,0,x,epsabs=1e-7,epsrel=2e-6,limit=160)
        return ans
    lo=0.
    hi=.995*xe
    if wneeded(hi)<=implied_W_over_F0:
        raise ArithmeticError("source GHSV demand not bracketed before equilibrium")
    x=brentq(lambda p:wneeded(p)-implied_W_over_F0,lo,hi,xtol=1e-12)
    current=wneeded(x)
    st=bed.state(x)
    frac=x/xe
    assert abs(current/implied_W_over_F0-1)<.00001
    return {
      "gas_mode":bed.gas_mode,"energy_mode":bed.energy_mode,
      "source_catalyst":model.catalyst,
      "authors_printed_GHSV_per_h":source_GHSV,
      "W_over_F0_kg_s_mol_implied_by_published_GHSV":implied_W_over_F0,
      "model_forward_reacted_extent_N2_mol_per_feed_mol":x,
      "model_forward_fraction_of_own_adiabatic_eq_extent":frac,
      "authors_reported_adiabatic_equilibrium_fraction":G.TARGET_EQUIL_FRACTION,
      "model_forward_reactor_outlet_NH3_mol_fraction":st["y_NH3"],
      "model_forward_reactor_outlet_temperature_C":st["T_C"],
      "model_forward_reactor_outlet_Keq_reaction_ratio":st["equilibrium_ratio"],
      "model_equilibrium_temperature_C":bed.state(xe)["T_C"],
      "model_energy_residual_J_per_inlet_mol":st["energy_residual_J_per_inlet_mol"],
      "fixed_original_kinetics_factors":True,
      "target_GHSV_only_used_as_forward_operating_configuration":True,
      "cannot_be_called_independent_bed_size_prediction":True
    }


def run(out:Path):
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for gas in G.GAS_MODES:
        for energy in G.THERMO_MODES:
            if gas=="ideal" and energy!="nist_ideal":continue
            bed=G.Bed(gas,energy)
            for catalyst in (G.FE,G.RU):
                records.append(measured_GHSV_forward(bed,catalyst))
    output={
      "status":"EXPLORATORY_POST_OUTCOME_MISMATCH_LOCALIZATION_NOT_SOURCE_VALIDATION",
      "method":"Forward prediction at authors' printed source-GHSV configuration, with frozen original Fe/Ru kinetics, source SRK and NIST enthalpy variants.",
      "readiness":"G2 STILL BLOCKED, NONIDENTICAL ASPEN CALORIC MODEL AND UNRESOLVED RU DISCREPANCY",
      "source_GHSV_values_used_only_as_forward_inputs":True,
      "all_source_parameters_unmodified":True,
      "not_rerunning_old_NH3_economic_phase_map":True,
      "source_Keestra_Fe_SI_SHA256":G.S.SOURCE_SI_SHA256,
      "records":records
    }
    (out/"g2_forward_source_GHSV_readiness.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
    with (out/"g2_forward_published_GHSV_predicted_outlets.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]))
        w.writeheader();w.writerows(records)
    text=[
      "# POST-OUTCOME forward reactor diagnostic at published GHSV",
      "",
      "In this diagnostic ALONE, set physical reactor GHSV to authors' printed 22,250 h^-1 for Fe and 130,000 h^-1 for promoted Ru/C. Use pre-existing published rate factors, 100bar feed, original source SRK fugacities and NIST enthalpy sensitivity modes. Solve the adiabatic reactor composition and fraction of OUR model's adiabatic equilibrium extent. Do not fit anything.",
      "",
      "| Fugacity variant | Caloric closure | Catalyst | Authors' GHSV h^-1 | Predicted fraction of own equilibrium | Desired fraction in paper | Predicted NH3 outlet mol% | Predicted T_out C |",
      "|---|---|---|---:|---:|---:|---:|---:|"
    ]
    for a in records:
        text.append(f"| {a['gas_mode']} | {a['energy_mode']} | {a['source_catalyst']} | {a['authors_printed_GHSV_per_h']:.0f} | {a['model_forward_fraction_of_own_adiabatic_eq_extent']:.4f} | 0.9000 | {a['model_forward_reactor_outlet_NH3_mol_fraction']*100:.3f}% | {a['model_forward_reactor_outlet_temperature_C']:.2f} |")
    text.extend(["",
     "**Purpose and interpretation:** this is a deliberately different check from the independently-predicted bed-size/GHSV in g2_adiabatic.py. The published GHSV is an *input* here; do NOT cite the inferred bed volume as reproduced. If Ru's forward equilibrium fraction is much less than 90%, its earlier independent GHSV mismatch corresponds to an actual predicted outlet shortfall, not just a reporting-unit conversion.",
     "",
     "Possible explanations include mismatched reported reaction-rate normalization (authors' source paper Eq.13 uses stoichiometric coefficients ν_i with r_NH3), model calibration or material specific kinetics, Aspen Plus vs NIST gas caloric model, 90% equilibrium conversion definition, and SRK mixing implementation. None is established as *the* cause. No kinetic parameters are adjusted to make any number look closer to 90%.",
     "",
     "G2 industrial source replication remains unverified; G3 commercial cost phase map is not run.",
     ""])
    (out/"G2_FORWARD_DIAGNOSTIC.md").write_text("\n".join(text),encoding="utf-8")
    print(json.dumps([{k:r[k] for k in ("gas_mode","energy_mode","source_catalyst","model_forward_fraction_of_own_adiabatic_eq_extent","model_forward_reactor_outlet_NH3_mol_fraction","model_forward_reactor_outlet_temperature_C")} for r in records],indent=2))
    return output


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.out)
