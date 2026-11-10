"""Write configs/<rxn>_ours.json for plant_framework.py from params.json (the hand-built parameter set), so the
framework can be checked against plant_models.py record by record (test_framework.py)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "params.json").read_text(encoding="utf-8"))
c = P["common"]
common = dict(metal_usd_per_kg=c["metal_usd_per_kg"],
              finance=dict(crf=c["crf"], fixed_om_frac=c["fixed_om_frac"]),
              prices=dict(gas_usd_per_GJ=c["gas_usd_per_GJ"], power_usd_kWh=c["power_usd_kWh"]))
cat_common = dict(recoverable_metals=c["recoverable_metals"], metal_recovery=c["metal_recovery"],
                  metal_financing=c["metal_financing"])

p = P["pdh"]
pdh = dict(
    name="non-oxidative propane dehydrogenation", parameter_set="ours", **common,
    species={"C3H8": {"MW": 44.097, "price_usd_t": p["prices"]["propane_usd_t"]}, "C3H6": {"MW": 42.081},
             "H2": {"MW": 2.016}},
    stoich=dict(nu={"C3H8": -1, "C3H6": 1, "H2": 1}, key="C3H8", product="C3H6"),
    thermo=dict(dH_J_mol=p["thermo"]["dH_J_mol"], dS_J_molK=p["thermo"]["dS_J_molK"]),
    plant=dict(capacity_t_per_y=p["plant"]["capacity_t_per_y"], hours_per_y=p["plant"]["hours_per_y"],
               P_bar=p["plant"]["P_bar"], feed_ratio={"H2": p["plant"]["h2_ratio"]}, inert_ratio=0.0,
               approach=p["plant"]["approach"], overall_conv=1.0),
    lab_feed=dict(default_y_key=1.0, default_ratio={"H2": 0.0}),
    switches=dict(selectivity_loss="lost"),
    fixed_credits=[dict(name="H2 burnt as fuel", t_per_t_product=2.016 / 42.081, GJ_per_t=p["h2_credit_GJ_per_t_H2"])],
    lost_key_fuel_GJ_per_t=p["light_ends_GJ_per_t"],
    energy=dict(pay_reaction_heat=True, furnace_eff=p["furnace_eff"], e_proc_GJ_per_t_reactor_feed=p["e_proc_GJ_per_t_feed"],
                power_kWh_per_t_fresh=p["power_kWh_per_t_feed"], power_kWh_per_t_recycle=p["power_kWh_per_t_feed"],
                fresh_basis="key"),
    capex=dict(usd=p["capex"]["usd"], fixed_share=p["capex"]["fixed_share"], throughput_share=p["capex"]["throughput_share"],
               reactor_share=p["capex"]["reactor_share"], reactor_basis="throughput"),
    catalyst=dict(base_usd_kg=p["catalyst_base_usd_kg"], life_y=p["catalyst_life_y"], **cat_common),
    regeneration=dict(enabled=True, t_regen_h=p["t_regen_h"], t_cycle_min_h=p["t_cycle_min_h"],
                      regen_GJ_per_t_cat=p["regen_GJ_per_t_cat"]),
    reference=dict(name=p["reference"]["name"], T_K=p["reference"]["T_K"], X=p["reference"]["X"], S=p["reference"]["S"],
                   r=p["reference"]["r"], t_cycle_h=p["reference"]["t_cycle_h"], elements=p["reference"]["elements"]),
    sources=p["_sources"], common_notes=c["_notes"])

q = P["ch4"]
ch4 = dict(
    name="CO2 methanation", parameter_set="ours", **common,
    species={"CO2": {"MW": 44.010, "price_usd_t": q["prices"]["co2_usd_t"]},
             "H2": {"MW": 2.016, "price_usd_t": q["prices"]["h2_usd_kg"] * 1000}, "CH4": {"MW": 16.043},
             "H2O": {"MW": 18.015}},
    stoich=dict(nu={"CO2": -1, "H2": -4, "CH4": 1, "H2O": 2}, key="CO2", product="CH4"),
    thermo=dict(dH_J_mol=q["thermo"]["dH_J_mol"], dS_J_molK=q["thermo"]["dS_J_molK"]),
    plant=dict(capacity_t_per_y=q["plant"]["capacity_t_per_y"], hours_per_y=q["plant"]["hours_per_y"],
               P_bar=q["plant"]["P_bar"], feed_ratio={"H2": 4.0}, inert_ratio=q["plant"]["inert_ratio"],
               approach=q["plant"]["approach"], overall_conv=q["plant"]["overall_conv"]),
    lab_feed=dict(default_y_key=0.2, default_ratio={"H2": 4.0}),
    switches=dict(selectivity_loss="converted_downstream"),
    fixed_credits=[], lost_key_fuel_GJ_per_t=0.0,
    energy=dict(pay_reaction_heat=False, furnace_eff=1.0, e_proc_GJ_per_t_reactor_feed=0.0,
                power_kWh_per_t_fresh=q["power_kWh_per_t_fresh"], power_kWh_per_t_recycle=q["power_kWh_per_t_recycle"],
                fresh_basis="all"),
    capex=dict(usd=q["capex"]["usd"], fixed_share=q["capex"]["fixed_share"], throughput_share=q["capex"]["recycle_share"],
               reactor_share=q["capex"]["reactor_share"], reactor_basis="catalyst"),
    catalyst=dict(base_usd_kg=q["catalyst_base_usd_kg"], life_y=q["catalyst_life_y"], **cat_common),
    regeneration=dict(enabled=False, t_regen_h=0.0, t_cycle_min_h=0.0, regen_GJ_per_t_cat=0.0),
    reference=dict(name=q["reference"]["name"], T_K=q["reference"]["T_K"], X=q["reference"]["X"], S=q["reference"]["S"],
                   r=q["reference"]["r"], t_cycle_h=None, elements=q["reference"]["elements"]),
    sources=q["_sources"], common_notes=c["_notes"])

(HERE / "configs").mkdir(exist_ok=True)
for name, cfg in (("pdh", pdh), ("ch4", ch4)):
    (HERE / "configs" / f"{name}_ours.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
print("written configs/pdh_ours.json, configs/ch4_ours.json")
