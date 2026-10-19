#!/usr/bin/env python3
"""Quantitative source-anchored 80bar(g) screen with 100bar final-bed FAIL-CLOSED gate."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import kinetics as K

HERE=Path(__file__).resolve().parent
SOURCE=K.CONFIG
TGRID=(350,400,450)
P80=80.0+K.ATM_BAR
F0=12.0


def audit():
    fe=K.KineticModel.from_locked("Fe")
    ru=K.KineticModel.from_locked("Ru_CeO2")
    results=[]
    for temp in TGRID:
        fr=K.rate_from_ideal_gas(fe,temp,P80,inlet_NH3=0,h2_n2_ratio=3)
        rr=K.rate_from_ideal_gas(ru,temp,P80,inlet_NH3=0,h2_n2_ratio=3)
        fbed=K.isothermal_ideal_pfr(fe,temp,P80,W_over_F0_kg_s_per_mol=F0)
        rbed=K.isothermal_ideal_pfr(ru,temp,P80,W_over_F0_kg_s_per_mol=F0)
        results.append(dict(T_C=temp,P_bar_gauge=80.0,P_bar_absolute=P80,
            Fe_formulation="AmoMax10 (Keestra Fe bcat 1)",
            Ru_formulation="FREA-AIST Ru/CeO2 (Keestra Ru bcat=bN=1)",
            inlet_NH3_mol_frac=0.,inlet_H2_N2=3.,
            Fe_initial_r_mol_kg_s=fr,Ru_CeO2_initial_r_mol_kg_s=rr,
            Fe_divided_by_Ru_initial_rate=fr/rr if rr>0 else None,
            Fe_ideal_isothermal_outlet_yNH3=fbed["outlet_yNH3"],
            Ru_CeO2_ideal_isothermal_outlet_yNH3=rbed["outlet_yNH3"],
            W_divided_by_F0_kg_s_mol=F0,
            Cholewa_source_direction="Fe faster than Ru/CeO2",
            predicted_initial_direction="Fe faster" if fr>rr else "Ru/CeO2 faster" if rr>fr else "tied",
            predicted_pfr_direction="Fe higher yNH3" if fbed["outlet_yNH3"]>rbed["outlet_yNH3"] else "Ru/CeO2 higher yNH3" if fbed["outlet_yNH3"]<rbed["outlet_yNH3"] else "tied"))
    target=SOURCE["referenceTarget100Bar"]
    # Do not invoke source-promoted rate when no source-specific factors.
    sufficient=target["Ru_Ba_K_C_bcat"] is not None and target["Ru_Ba_K_C_bN"] is not None
    assert not sufficient,"Not ready to run promoted G2: EOS and adiabatic balance must also be audited"
    matching=all(x["predicted_initial_direction"]=="Fe faster" and
                 x["predicted_pfr_direction"]=="Fe higher yNH3" for x in results)
    g0=dict(status="PASS",source_equations="Keestra Fe Eq15 and Ru Eqs10-12",
        equilibrium_definition="Keestra Fe Eq4 Kf(T)=1.3628e-6 exp(+51111/RT)",
        kinetics_source_params_locked=True,uses_published_Keestra_modified_SRK=False,
        physical_approximations=["ideal fugacities for rate screening",
            "isothermal PFR temperature", "fixed common W/F0=12 kg s per mol feed"])
    g1=dict(status="PASS_QUALITATIVE_IN_FAMILY_DIRECTION" if matching else "FAILED_QUALITATIVE_DIRECTION",
       dataset_in_training=True,matched_actual_materials="AmoMax10 Fe and FREA-AIST Ru/CeO2",
       no_Ru_Ba_K_C_substitution=True,pressures_bar_gauge=[80],
       pressures_bar_absolute=[P80],temperatures_C=list(TGRID),
       all_three_fe_direction_reproduced=matching,
       not_experimental_quantitative_replication=True,
       literature_direction="Cholewa 2024 Fig 4, Fe faster than Ru/CeO2",
       experimental_concentration_traces_available=False)
    g2=dict(status="BLOCKED",material="4 wt% Ru-Ba-K/C",
       missing=target["missing"],
       published_target_volume_ratio_Fe_div_Ru=5.8,
       published_target_mass_ratio_Fe_div_Ru=19,
       no_fitted_source_catalyst_factors=True,
       no_adabatic_srk_replication=True)
    g3=dict(status="BLOCKED_G2_REQUIRED",no_new_process_economics_or_phase_claim=True,
       original_PR111_unchanged=True)
    g4=dict(status="PARTIAL",Cholewa_2024_in_fit_cohort=True,
       Kowalczyk_1996="source identity and training overlap not fully checked; no numerical claims",
       Pan_2011="source identity and training overlap not fully checked; no numerical claims")
    return dict(study="source-anchored preliminary published-kinetics audit",
       interpretation="MODEL-CONDITIONAL ideal fugacity, isothermal, IN-FAMILY test ONLY",
       source_dois=["10.1016/j.cej.2025.164593","10.1016/j.cej.2025.168541","10.1039/D4SE00254G",
                    "10.1016/0926-860X(95)00251-0","10.1016/S1004-9541(11)60165-1"],
       G0=g0,G1=g1,G2=g2,G3=g3,G4=g4,
       experiment_geometry_class="source Cholewa 80bar(g) matched pressure; W/F illustrative",
       measured_absolute_rates_used=False,kinetic_rows=results,
       original_manuscript_unchanged=True,frozen_results_unchanged=True)


def print_report(x):
    s=[
      "# Keestra 2025 Fe/Ru pressure applicability — source-anchored study",
      "",
      "**Status:** G0 verified source global rate equations; G1 qualitative source-anchor screening; G2 100bar promoted Ru-Ba-K/C final-bed replication **BLOCKED** for missing SI factors, source-modified SRK and adiabatic model; G3 economic decision atlas NOT executed.",
      "",
      "## Source-matched same-pressure screen, NOT the 100bar commercial example",
      "",
      "Keestra Fe reference is AmoMax 10 (bcat=1) and Ru reference is FREA-AIST Ru/CeO2 (bcat=bN=1), measured in Cholewa et al. 2024 under overlapping 80bar(g) = 81.01325 bar(a). The test uses published 2025 global rate constants but **ideal-gas fugacities**, single-gas inlet N2:H2=1:3 with zero NH3, and a schematic *isothermal* reactor at W/F0=12 kg*s/mol. The original papers instead fitted with a modified SRK EOS. The direction found here is in-family because Cholewa contributed to the 2025 training sets; it is NOT an independent holdout.",
      "",
      "| T | Fe initial rate | Ru/CeO2 initial rate | Fe/Ru initial rate | ideal isothermal Fe outlet NH3 | ideal isothermal Ru/CeO2 outlet NH3 |",
      "|---|---:|---:|---:|---:|---:|"
    ]
    for t in x["kinetic_rows"]:
        s.append("| %d C | %.7g | %.7g | %.4g | %.4f | %.4f |" %
            (t["T_C"],t["Fe_initial_r_mol_kg_s"],t["Ru_CeO2_initial_r_mol_kg_s"],
            t["Fe_divided_by_Ru_initial_rate"],t["Fe_ideal_isothermal_outlet_yNH3"],
            t["Ru_CeO2_ideal_isothermal_outlet_yNH3"]))
    s.extend(["",
        "**Fe and Ru/CeO2 initial rates are in mol NH3 kg-cat^-1 s^-1, the same rate-unit definition but for different catalysts. The outlet concentrations are exploratory model predictions, not Cholewa's experimentally printed measurements.**",
        "",
        "## Separate 100bar Keestra benchmark",
        "",
        "Keestra Ru 2025 Table 4: 400C, 100bar(a), H2/N2=2.25, inlet 11mol% NH3, 4wt% Ru-Ba-K/C vs Fe AmoMax10, target 90% of adiabatic equilibrium. Authors report ~5.8x less Ru bed volume and ~19x less Ru bed mass. **We have not reproduced those values.**",
        "The exact Ru-Ba-K/C bcat and bN correction factors in supporting information A-1 remain unavailable for independent transcription. Published Ru/CeO2 factors of 1 are not substitutes. The original modified SRK fugacities and adiabatic energy balance also need faithful implementation. G2 remains BLOCKED even though G0/G1 tests are green.",
        "",
        "## Source provenance and independence",
        "",
        "- Fe: https://doi.org/10.1016/j.cej.2025.164593 (Table 2, Eq.15).",
        "- Ru: https://doi.org/10.1016/j.cej.2025.168541 (Table 3, Eqs.10-12).",
        "- Cholewa: https://doi.org/10.1039/D4SE00254G (Fe and FREA-AIST Ru/CeO2; 80bar is gauge).",
        "- Kowalczyk 1996: https://doi.org/10.1016/0926-860X(95)00251-0 (promoted carbon-Ru formulation must be disambiguated).",
        "- Pan 2011: https://doi.org/10.1016/S1004-9541(11)60165-1 (A301 Fe vs carbon-Ru).",
        "",
        "## Decision gate",
        "",
        "The pressure mismatch of OLD Dyson–Simon Fe and Rossetti promoted Ru/C rate laws is not repaired merely by using newer pooled global models. Same-pressure validation requires matching the **specific catalyst**, reported source parameters, correctly converted pressure, and joint EOS/adiabatic reactor reproducibility. NO NH3 industrial economic conclusion or new Fe/Ru phase boundary is produced here.",
        ""
    ])
    return "\n".join(s)


def make_plot(x,out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    temps=[r["T_C"] for r in x["kinetic_rows"]]
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout="constrained")
    axes[0].plot(temps,[r["Fe_initial_r_mol_kg_s"] for r in x["kinetic_rows"]],"o-",label="Fe AmoMax10")
    axes[0].plot(temps,[r["Ru_CeO2_initial_r_mol_kg_s"] for r in x["kinetic_rows"]],"o-",label="FREA-AIST Ru/CeO2")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Initial model rate (mol NH3 / kg-cat / s)")
    axes[0].set_xlabel("Temperature (°C)")
    axes[0].legend(fontsize=8)
    axes[1].plot(temps,[100*r["Fe_ideal_isothermal_outlet_yNH3"] for r in x["kinetic_rows"]],"o-",label="Fe AmoMax10")
    axes[1].plot(temps,[100*r["Ru_CeO2_ideal_isothermal_outlet_yNH3"] for r in x["kinetic_rows"]],"o-",label="FREA-AIST Ru/CeO2")
    axes[1].set_ylabel("Schematic isothermal PFR outlet NH3 (mol %)")
    axes[1].set_xlabel("Temperature (°C)")
    axes[1].legend(fontsize=8)
    fig.suptitle("Published kinetics, ideal-fugacity screening only | Cholewa 80 bar(g)",fontsize=11)
    fig.savefig(out/"screen_80barg_preliminary.png",dpi=220)
    fig.savefig(out/"screen_80barg_preliminary.svg")
    plt.close(fig)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plot",action="store_true")
    p.add_argument("--require-100bar-completion",action="store_true",
                   help="Fail closed (exit2) if true promoted-formulation industrial source benchmark is unverified")
    args=p.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    x=audit()
    (out/"readiness.json").write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (out/"REPORT.md").write_text(print_report(x),encoding="utf-8")
    with (out/"screen_80barg_preliminary.csv").open("w",newline="",encoding="utf-8") as f:
        rows=x["kinetic_rows"]
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    if args.plot:make_plot(x,out)
    print(json.dumps({k:v for k,v in x.items() if k in ("G0","G1","G2","G3","G4")},indent=2))
    if args.require_100bar_completion and x["G2"]["status"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
