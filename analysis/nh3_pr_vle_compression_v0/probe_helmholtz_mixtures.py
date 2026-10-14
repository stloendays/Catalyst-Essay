#!/usr/bin/env python3
"""Read-only audit of published Helmholtz mixture backend availability.

Does not fabricate or add CoolProp binary mixing rules. The 2020 Neumann
mixture EOS study does not imply that all ten Figure57 five-fluid pairs are
implemented and validated in this installation.

References:
  Neumann et al, Fundamental Thermodynamic Models for Mixtures Containing
  Ammonia, Fluid Phase Equilibria 511 (2020) 112496,
  doi:10.1016/j.fluid.2020.112496.
  CoolProp mixture docs https://coolprop.org/fluid_properties/Mixtures.html
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


NAMES=("Nitrogen","Hydrogen","Methane","Argon","Ammonia")
SOURCE_2020="https://doi.org/10.1016/j.fluid.2020.112496"


def inspect()->dict:
    try:
        import CoolProp.CoolProp as CP
    except ImportError as exc:
        return {"environment_status":"COOLPROP_NOT_INSTALLED","reason":str(exc),
                "source":SOURCE_2020}
    version=CP.get_global_param_string("version")
    pairs=[]
    for a,b in itertools.combinations(NAMES,2):
        ca=CP.get_fluid_param_string(a,"CAS")
        cb=CP.get_fluid_param_string(b,"CAS")
        coefficients={}
        errors=[]
        for attr in ("betaT","gammaT","betaV","gammaV","F"):
            try:
                value=CP.get_mixture_binary_pair_data(ca,cb,attr)
                coefficients[attr]=value
            except Exception as e:
                errors.append(f"{attr}: {type(e).__name__}: {str(e)[:110]}")
        pairs.append({
            "a":a,"b":b,
            "CAS1":ca,"CAS2":cb,
            "has_all_reducing_coefficients":all(k in coefficients for k in ("betaT","gammaT","betaV","gammaV")),
            "source_parameters":coefficients,
            "missing_or_unsupported":errors,
            "status":"BUILT_IN_PAIR_REPORTED" if coefficients else "NO_BUILT_IN_PAIR_PARAMETERS",
            "provenance_caveat":"Pair presence is not proof the 2020 Neumann fluid binary model is loaded or valid for high P.",
        })
    candidate={"coolprop_version":version,
               "fluid_order":list(NAMES),
               "complete_10_pair_coverage":all(p["has_all_reducing_coefficients"] for p in pairs),
               "pair_count":len(pairs),
               "supported_pair_reducing_coefficients":sum(p["has_all_reducing_coefficients"] for p in pairs),
               "no_simple_mixing_rules_applied":True,
               "no_binary_pair_data_overwritten":True,
               "pairs":pairs,
               "2020_Ammonia_binary_EOS":SOURCE_2020,
               "source_scope":"published pair model NH3+N2/H2/CH4/Ar; additional six nonNH3 cross pairs are required for full five-component source stream",
               "high_pressure_mixture_PT_flash":{},
               "not_a_validated_predictive_model":True}
    if not candidate["complete_10_pair_coverage"]:
        candidate["status"]="INCOMPLETE_PAIR_LIBRARY__NO_UNSUPPORTED_MIXING_RULE_SUBSTITUTION"
        return candidate
    try:
        state=CP.AbstractState("HEOS","&".join(NAMES))
        # Only upstream Figure57 converter gas4 data; not a plant flash output.
        molefracs=[.1960,.4799,.0943,.0331,.1967]
        if abs(sum(molefracs)-1)>1e-6:
            raise AssertionError("Source feed4 mole-fraction record not normalised")
        state.set_mole_fractions(molefracs)
        state.update(CP.PT_INPUTS,18.02e6,294.15)
        candidate["high_pressure_mixture_PT_flash"]={
            "upstream_source_feed_stream":4,
            "T_K":294.15,"P_Pa":18.02e6,
            "Z":state.p()*state.molar_mass()/(state.rhomass()*8.31446261815324*state.T()),
            "state_phase_enum":state.phase(),
            "quality":state.Q(),
            "scope":"source4 feed composition TP diagnostic only; phase split not provided by default PT API"
        }
        candidate["status"]="HEOS_5_COMPONENT_TP_DIAGNOSTIC_COMPLETED__NOT_VALIDATED"
    except Exception as exc:
        candidate["status"]="HEOS_5_COMPONENT_PT_FAILED__NO_FALLBACK_ESTIMATED_INTERACTIONS"
        candidate["high_pressure_mixture_PT_flash"]={"exception":type(exc).__name__,
                                                      "message":str(exc)[:1200]}
    return candidate


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args()
    a.out_dir.mkdir(parents=True,exist_ok=True)
    d=inspect()
    (a.out_dir/"CoolProp_HEOS_pair_coverage.json").write_text(
        json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=[
        "# Five-component source mixture high-accuracy Helmholtz EOS availability gate",
        "",
        f"Source model: Neumann et al (2020), {SOURCE_2020}.",
        f"CoolProp version: {d.get('coolprop_version','NOT INSTALLED')}.",
        f"Internal pair count: {d.get('supported_pair_reducing_coefficients','n/a')}/{d.get('pair_count','n/a')}.",
        f"**Status: {d.get('status',d.get('environment_status','UNRESOLVED'))}**.",
        "",
        "No built-in interaction was overwritten, no interaction guessed, no validation target fitted. "
        "Any missing pair leaves a full five-component HEOS prediction blocked. "
        "A numerical PT solve does not prove accurate vapor-liquid flash under industrial feed composition.",
        ""
    ]
    (a.out_dir/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print("\n".join(lines))


if __name__=="__main__":
    main()
