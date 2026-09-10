"""Independent hand-calculation audit of the NH3-FINAL-1.1 pressure CAPEX chain.
Does NOT import harness_core. Reads only the manifest numbers and the run's stored optimum (V, P, T, Tsep) plus the
harness' reported pools, then recomputes every pool from explicit formulas and compares."""
import json, math, sys, yaml
from pathlib import Path
ROOT = Path(r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1")
cfg = yaml.safe_load((ROOT / "configs/nh3_final_1.1_candidate.yaml").read_text(encoding="utf-8"))
res = json.load(open(ROOT / "outputs/nh3_final_1_1_20260905T113727Z/results.json", encoding="utf-8"))
det = res["deterministic"]["metals"]

econ = cfg["economics"]; pc = econ["pressure_capex"]; plant = cfg["plant"]; eng = cfg["engineering"]; proc = cfg["process"]
R = 8.314462618; T_COMP = 298.15; MW_NH3 = 0.01703052
PRICE = {"Fe": 8.0, "Ru": 53852.5}  # USD/kg, frozen constants in harness_core.PRICE (copied by hand)

r, n = econ["discount_rate"], econ["plant_life_y"]
crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
annual_t = plant["production_tpd"] * 365.0 * plant["capacity_factor"]
n_per_t = 1000.0 / MW_NH3
idx = pc["cost_index_current"] / pc["cost_index_base"]
print(f"CRF = {r}*(1+{r})^{n}/((1+{r})^{n}-1) = {crf:.6f} 1/y ; annual output = {plant['production_tpd']}*365*{plant['capacity_factor']} = {annual_t:,.1f} t/y")
print(f"mol NH3 per t = 1000/{MW_NH3} = {n_per_t:,.2f} ; CEPCI ratio = {pc['cost_index_current']}/{pc['cost_index_base']} = {idx:.5f}\n")

def cp0(K, A, Amin, Amax, nexp):
    Ac = min(max(A, Amin), Amax); la = math.log10(Ac)
    return 10 ** (K[0] + K[1] * la + K[2] * la * la) * (A / Ac) ** nexp

v = pc["vessel"]; c = pc["compressor"]
for m in ("Fe", "Ru"):
    f = det[m]["feasible"]; bd = f["breakdown"]
    V, P, T, Ts = f["V_m3"], f["P_bar"], f["T_C"], f["Tsep_C"]
    print("=" * 100); print(f"{m}: optimum T {T:.0f} C, P {P:.0f} bar, Tsep {Ts:.0f} C, bed V = {V:.5f} m3, logTOF {f['logTOF']:.4f}")
    # ---- metal inventory
    active_kg = V * eng["active_fraction"] * eng["bed_density_kg_m3"]
    metal = active_kg * PRICE[m] * (1 - econ["metal_recovery_fraction"]) / econ["catalyst_life_y"] / annual_t
    print(f"  metal: active kg = {V:.5f}*{eng['active_fraction']}*{eng['bed_density_kg_m3']} = {active_kg:,.2f} kg ; USD/t = kg*{PRICE[m]}*(1-0)/{econ['catalyst_life_y']}/{annual_t:,.0f} = {metal:.6f}   [harness {bd['metal_cost']:.6f}]")
    # ---- 1.0 reactor volume proxy
    rbase_capex = econ["reactor_fixed_USD"] + econ["reactor_variable_USD"] * (V / econ["reactor_reference_m3"]) ** econ["reactor_exponent"]
    rbase = rbase_capex * crf / annual_t
    print(f"  reactor volume proxy: {econ['reactor_fixed_USD']} + {econ['reactor_variable_USD']}*({V:.4f}/20)^0.52 = {rbase_capex:,.0f} USD ; *crf/annual = {rbase:.6f}   [harness {bd['reactor_base']:.6f}]")
    # ---- vessel pressure premium
    Vd = max(V, v["A_min_m3"]); D = (4 * Vd / (math.pi * v["L_over_D"])) ** (1 / 3)
    t = P * D / (2 * (v["allowable_stress_x_weld_eff_bar"] - 0.6 * P)) + v["corrosion_allowance_m"]
    Fp = max(t / v["min_thickness_m"], 1.0)
    C0 = cp0(v["K"], Vd, v["A_min_m3"], v["A_max_m3"], v["extrapolation_exponent"])
    dC = C0 * v["B2"] * v["Fm"] * (Fp - 1) * idx
    prem = dC * crf / annual_t
    print(f"  vessel: V_cost = max({V:.4f},{v['A_min_m3']}) = {Vd:.4f} m3 ; D = (4V/(pi*{v['L_over_D']}))^(1/3) = {D:.4f} m")
    print(f"          t = {P:.0f}*{D:.4f}/(2*({v['allowable_stress_x_weld_eff_bar']}-0.6*{P:.0f})) + {v['corrosion_allowance_m']} = {t:.5f} m ; Fp = t/{v['min_thickness_m']} = {Fp:.3f}")
    print(f"          Cp0 = 10^({v['K'][0]} + {v['K'][1]}*log10 V + {v['K'][2]}*(log10 V)^2) = {C0:,.0f} USD (2001)")
    print(f"          dC = Cp0*B2*Fm*(Fp-1)*idx = {C0:,.0f}*{v['B2']}*{v['Fm']}*{Fp-1:.3f}*{idx:.4f} = {dC:,.0f} USD ; USD/t = {prem:.6f}   [harness {bd['vessel_pressure_premium']:.6f}]")
    # ---- electricity pools from physics
    P0 = plant["fresh_feed_pressure_bar"]; eta = econ["compressor_efficiency"]; elec = econ["electricity_USD_MWh"]
    E_fresh = 2 * n_per_t * R * T_COMP * math.log(P / P0) / eta   # J per t NH3 (2 mol reactive gas per mol NH3)
    fresh = E_fresh / 3.6e9 * elec
    print(f"  fresh compression: E = 2*{n_per_t:,.0f}*R*{T_COMP}*ln({P:.0f}/{P0})/{eta} = {E_fresh/3.6e6:,.1f} kWh/t ; USD/t = {fresh:.6f}   [harness {bd['fresh_comp']:.6f}]")
    dP = proc["recycle_pressure_rise_bar"]
    E_rec = bd["recycle_comp"] / elec * 3.6e9
    rec_ratio = E_rec * eta / (n_per_t * R * T_COMP * math.log(P / (P - dP)))
    print(f"  recycle compression: harness {bd['recycle_comp']:.6f} USD/t -> {E_rec/3.6e6:,.1f} kWh/t -> implied recycle {rec_ratio:.2f} mol/mol NH3 (dP {dP} bar)")
    # ---- refrigeration
    if Ts < proc["refrigeration_sink_C"]:
        Tc, Th = Ts + 273.15, proc["refrigeration_sink_C"] + 273.15
        Wact = proc["ammonia_heat_of_vaporization_kJ_mol"] * 1000 * (Th - Tc) / Tc / proc["refrigeration_efficiency_fraction_carnot"]
        refrig = Wact * n_per_t / 3.6e9 * elec
    else:
        refrig = 0.0
    print(f"  refrigeration (Tsep {Ts:.0f} C): {refrig:.6f}   [harness {bd['refrigeration']:.6f}]")
    # ---- compressor CAPEX (two services)
    tot_comp = 0.0
    for name, usd_t in (("fresh", bd["fresh_comp"]), ("recycle", bd["recycle_comp"])):
        if usd_t <= 0:
            print(f"  {name} compressor: no duty -> 0"); continue
        kwh_t = usd_t / elec * 1000.0
        W = kwh_t * plant["production_tpd"] / 24.0          # kW at design capacity (electrical/shaft basis)
        nunit = max(1, math.ceil(W / c["A_max_kW"])); Wu = W / nunit
        C0c = cp0(c["K"], Wu, c["A_min_kW"], c["A_max_kW"], c["extrapolation_exponent"])
        CBM = nunit * C0c * c["F_BM"] * idx
        usd = CBM * crf / annual_t; tot_comp += usd
        print(f"  {name} compressor: {usd_t:.4f} USD/t /{elec} *1000 = {kwh_t:.2f} kWh/t ; W = kWh/t*{plant['production_tpd']}/24 = {W:,.0f} kW ; n = {nunit}, W/unit = {Wu:,.0f} kW")
        print(f"          Cp0/unit = 10^({c['K'][0]} + {c['K'][1]}*log10 W + {c['K'][2]}*(log10 W)^2) = {C0c:,.0f} USD ; C_BM = {nunit}*Cp0*{c['F_BM']}*{idx:.4f} = {CBM:,.0f} USD ; USD/t = {usd:.6f}")
        # what the number would be if Turton's 'fluid power' (= shaft power * eta) were used instead
        Wf = W * eta; nf = max(1, math.ceil(Wf / c["A_max_kW"])); C0f = cp0(c["K"], Wf / nf, c["A_min_kW"], c["A_max_kW"], c["extrapolation_exponent"])
        print(f"          (if sized on fluid power {Wf:,.0f} kW: n = {nf}, USD/t = {nf*C0f*c['F_BM']*idx*crf/annual_t:.6f})")
    print(f"  compressor CAPEX total = {tot_comp:.6f}   [harness {bd['compressor_capex']:.6f}]")
    total = metal + rbase + prem + fresh + bd["recycle_comp"] + refrig + tot_comp
    print(f"  TOTAL (hand) = {metal:.4f} + {rbase:.4f} + {prem:.4f} + {fresh:.4f} + {bd['recycle_comp']:.4f} + {refrig:.4f} + {tot_comp:.4f} = {total:.6f}   [harness total {f['total_cost']:.6f}]")
