"""configs/<rxn>_ours.json for the three new reactions. Reused NCE modules: NH3 equilibrium from the NH3 harness
(Gillespie-Beattie), Ru price and recovery convention from the NCE Ru-cost analysis, RWGS equilibrium from the methanol
loop model. Every value has a 'sources' entry; values without an open source are marked 'assumption' and listed in
'uncertain' with a range. Common finance, power price and metal prices are the same as for PDH and methanation."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = json.loads((HERE / "configs" / "pdh_ours.json").read_text(encoding="utf-8"))
COMMON = dict(metal_usd_per_kg=base["metal_usd_per_kg"], finance=base["finance"])
GBP_USD_2019, EUR_USD_2011, EUR_USD_2012 = 1.277, 1.392, 1.285          # annual averages (Federal Reserve H.10)
CAT = lambda life, base_kg, rec=0.9555: dict(base_usd_kg=base_kg, life_y=life, recoverable_metals=base["catalyst"]["recoverable_metals"],  # noqa: E731
                                            metal_recovery=rec, metal_financing=0.08)
NOREGEN = dict(enabled=False, t_regen_h=0.0, t_cycle_min_h=0.0, regen_GJ_per_t_cat=0.0)
HS420 = ("Ecuity/Engie/STFC HS420 'Ammonia to Green Hydrogen' (BEIS 2020), "
         "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/880826/HS420_-_Ecuity_-_Ammonia_to_Green_Hydrogen.pdf")

# ------------------------------------------------------------------ ammonia decomposition (H2 from NH3)
nh3_price = 445.0
nh3dec = dict(
    name="ammonia decomposition (cracking) to hydrogen", parameter_set="ours", **COMMON,
    prices=dict(gas_usd_per_GJ=round(nh3_price / 18.6, 2), power_usd_kWh=0.08),
    species={"NH3": {"MW": 17.031, "price_usd_t": nh3_price}, "N2": {"MW": 28.014}, "H2": {"MW": 2.016}},
    stoich=dict(nu={"NH3": -1, "N2": 0.5, "H2": 1.5}, key="NH3", product="H2"),
    thermo=dict(source="nce_nh3_gillespie_beattie", dH_J_mol=45900.0),
    plant=dict(capacity_t_per_y=66700, hours_per_y=8000, P_bar=5.0, feed_ratio={}, inert_ratio=0.0, approach=0.98, overall_conv=1.0),
    lab_feed=dict(default_y_key=1.0, default_ratio={"H2": 0.0}),
    switches=dict(selectivity_loss="lost"), fixed_credits=[], lost_key_fuel_GJ_per_t=18.6,
    energy=dict(pay_reaction_heat=True, furnace_eff=0.931, e_proc_GJ_per_t_reactor_feed=5.27, power_kWh_per_t_fresh=50.0,
                power_kWh_per_t_recycle=50.0, fresh_basis="key"),
    capex=dict(usd=368e6 * GBP_USD_2019, fixed_share=0.5, throughput_share=0.3, reactor_share=0.2, reactor_basis="catalyst"),
    catalyst=CAT(3.0, 20.0), regeneration=NOREGEN,
    reference=dict(name="Ni catalyst, fired cracker (HS420 design)", T_K=973.15, X=0.846, S=1.0, r=0.34, t_cycle_h=None,
                   elements=[["Ni", 20.0]]),
    uncertain=[dict(path="species.NH3.price_usd_t", low=400.0, high=563.0, why="Tampa 2024 400-450 USD/t; HS420 green NH3 0.44 GBP/kg"),
               dict(path="prices.gas_usd_per_GJ", low=3.0, high=30.3, why="natural-gas firing vs NH3 firing at 563 USD/t"),
               dict(path="capex.usd", low=0.5 * 368e6 * GBP_USD_2019, high=1.5 * 368e6 * GBP_USD_2019, why="assumption +-50 %"),
               dict(path="plant.P_bar", low=2.0, high=15.0, why="HS420: 15 bar feed, 2.3 bar product"),
               dict(path="reference.r", low=0.1, high=1.0, why="assumption: GHSV 1000-10000 h-1"),
               dict(path="catalyst.life_y", low=1.0, high=5.0, why="assumption"),
               dict(path="catalyst.metal_recovery", low=0.90, high=0.9555, why="NCE Ru recovery range")],
    sources={
        "thermo": "NH3 harness gillespie_beattie_dG_form (provenance/nh3_final_1_2/source_harness/harness_core.py), K = exp(dG_f/kT) per NH3, ideal gas; dH 45.9 kJ/mol NH3 (standard enthalpy of formation) for the reaction heat",
        "species.NH3.price_usd_t": "445 USD/t, Tampa CFR March 2024 (Argus/CRU, search summary) (S)",
        "prices.gas_usd_per_GJ": "the cracker burns NH3 and off-gas (HS420 Table 3: reformer fuel 85 % NH3 / 15 % H2): NH3 price / LHV 18.6 GJ/t",
        "plant.capacity_t_per_y": "200 t/d H2 (HS420 p.24) x 333 d",
        "plant.P_bar": "assumption, 5 bar (Ru membrane demo at 5 bar, HS420 s3.2; fired design 15 bar feed / 2.3 bar product, HS420 Table 3)",
        "reference.X": "84.6 % per pass, HS420 p.24: 'thermal efficiency of this design reaches 93.1% at a 84.6% conversion rate'",
        "reference.T_K": "assumption 700 C within 600-950 C for Ni (Ammogen/Gemserv HYS2204, DESNZ 2025)",
        "reference.elements": "Ni catalyst (Topsoe DNK-20/DNK-30 Ni grades, H2Retake page); 20 wt % Ni is an assumption",
        "reference.r": "assumption: GHSV 3000 h-1 pure NH3, bed 1.0 kg/L, X 0.846",
        "energy.furnace_eff": "93.1 % thermal efficiency, HS420 p.24",
        "energy.e_proc_GJ_per_t_reactor_feed": "calibrated: heater duty 119 MWth for 200 t/d H2 (HS420 p.24) = 51.4 GJ/t H2 = reaction heat / 0.931 + 5.27 GJ x 6.66 t NH3 through the reactor per t H2",
        "energy.power": "assumption 50 kWh/t NH3 (compression to 250 bar excluded)",
        "capex.usd": "TCI 368 M GBP (HS420 p.33, centralised 200 t/d unit incl. cryogenic purification) x 1.277 USD/GBP (2019)",
        "capex.shares": "assumption",
        "catalyst": "Ru price 53,852.5 USD/kg and recovery 0.9555 (range 0.90-0.9555) as in the NCE NH3 analysis (figures/composite/fig2/fig2_ru_actual_cost.py); life 3 y assumption; base 20 USD/kg as for the other reactions",
        "finance": "7 %/y, 20 y (as PDH, Enterprise Products EPA application); fixed O&M 4 %/y",
        "check": "HS420 p.33: levelised cost 4.72-5.19 GBP/kg H2 including NH3 and compression to 250 bar; NH3 is ~54 % (10 % NH3 price -> +5.4 % H2 cost)",
        "upstream": HS420})

# ------------------------------------------------------------------ RWGS (CO for e-fuels)
rwgs = dict(
    name="reverse water-gas shift to CO", parameter_set="ours", **COMMON,
    prices=dict(gas_usd_per_GJ=8.0, power_usd_kWh=0.08),
    species={"CO2": {"MW": 44.010, "price_usd_t": 100.0}, "H2": {"MW": 2.016, "price_usd_t": 3000.0},
             "CO": {"MW": 28.010}, "H2O": {"MW": 18.015}},
    stoich=dict(nu={"CO2": -1, "H2": -1, "CO": 1, "H2O": 1}, key="CO2", product="CO"),
    thermo=dict(source="nce_meoh_K_rwgs", dH_J_mol=41200.0),
    plant=dict(capacity_t_per_y=100000, hours_per_y=8000, P_bar=11.0, feed_ratio={"H2": 2.25}, inert_ratio=0.0, approach=0.95,
               overall_conv=0.98),
    lab_feed=dict(default_y_key=0.25, default_ratio={"H2": 3.0}),
    switches=dict(selectivity_loss="lost"), fixed_credits=[], lost_key_fuel_GJ_per_t=0.0,
    energy=dict(pay_reaction_heat=True, furnace_eff=0.85, e_proc_GJ_per_t_reactor_feed=2.0, power_kWh_per_t_fresh=60.0,
                power_kWh_per_t_recycle=40.0, fresh_basis="all"),
    capex=dict(usd=76e6, fixed_share=0.5, throughput_share=0.3, reactor_share=0.2, reactor_basis="catalyst"),
    catalyst=CAT(3.0, 20.0), regeneration=NOREGEN,
    reference=dict(name="Ni/ZrO2 on FeCrAl, electrified RWGS (Topsoe eREACT)", T_K=1173.15, X=0.60, S=0.995, r=1.0, t_cycle_h=None,
                   elements=[["Ni", 10.0]]),
    uncertain=[dict(path="species.H2.price_usd_t", low=2000.0, high=6000.0, why="grey ~2 USD/kg; electrolytic 5-7 USD/kg (DOE Liftoff 2024, S)"),
               dict(path="species.CO2.price_usd_t", low=17.3, high=104.0, why="Zang 2021 17.3-38.6 USD/t; Enterprise CCS 104 USD/t"),
               dict(path="capex.usd", low=38e6, high=152e6, why="capacity basis of the 76 M USD not stated: x0.5-2"),
               dict(path="prices.gas_usd_per_GJ", low=2.5, high=22.2, why="US gas to electric heating at 0.08 USD/kWh"),
               dict(path="reference.r", low=0.3, high=3.0, why="assumption"),
               dict(path="plant.P_bar", low=1.0, high=25.0, why="Adelung 1-5 bar optimum (S); Zang 24.5 bar")],
    sources={
        "thermo": "K_rwgs(T) from data/meoh/meoh_general_model.py (methanol loop model), ideal gas; dH 41.2 kJ/mol for the heat duty",
        "plant": "Topsoe eREACT whitepaper: 900 C, 10 barg, H2:CO2 = 2.25, CH4 slip < 0.2 % above 900 C (https://www.topsoe.com/hubfs/DOWNLOADS/DOWNLOADS%20-%20White%20papers/19549%20Electrical%20Reverse%20Shift%20Whitepaper_FINAL.pdf)",
        "plant.capacity_t_per_y": "assumption 100 kt/y CO",
        "reference.S": "CH4 slip < 0.2 % (eREACT whitepaper) -> CO selectivity 0.995",
        "reference.X": "assumption 0.60 per pass (equilibrium about 0.66 at 900 C, 11 bar, H2/CO2 2.25 in this model)",
        "reference.elements": "Ni on ZrO2-coated FeCrAl (eREACT whitepaper); 10 wt % assumption",
        "species.H2.price_usd_t": "3 USD/kg, the anchor of the methanation model (Becker, Penev & Braun 2019)",
        "species.CO2.price_usd_t": "100 USD/t as in the methanation model (Enterprise Products EPA application: 104 USD/t captured)",
        "capex.usd": "RWGS reaction area installed equipment 76 M USD (Zang, Sun, Elgowainy, Wang, Environ. Sci. Technol. 2021, doi 10.1021/acs.est.0c08674, OSTI 1807681 l.361-366); plant capacity basis not stated -> range x0.5-2",
        "energy": "assumptions: fired heater 85 %, 2 GJ/t CO2 preheat/separation, power 60 + 40 x recycle kWh/t",
        "catalyst": "life 3 y (Zang l.255: catalysts replaced every three years); base 20 USD/kg assumption",
        "check": "no open per-tonne CO cost with a breakdown was found; the check is the stoichiometric floor (H2 + CO2) and the share of capital"})

# ------------------------------------------------------------------ ethanol dehydration (bio-ethylene)
etoh_price = round(0.565 / 0.789 * 1000, 1)        # Brazil 0.51-0.62 USD/L (Haro 2013 Table 9, Sept 2012) midpoint
etoh = dict(
    name="ethanol dehydration to ethylene", parameter_set="ours", **COMMON,
    prices=dict(gas_usd_per_GJ=8.0, power_usd_kWh=0.08),
    species={"C2H5OH": {"MW": 46.069, "price_usd_t": etoh_price}, "C2H4": {"MW": 28.054}, "H2O": {"MW": 18.015}},
    stoich=dict(nu={"C2H5OH": -1, "C2H4": 1, "H2O": 1}, key="C2H5OH", product="C2H4"),
    thermo=dict(dH_J_mol=45600.0, dS_J_molK=125.2),
    plant=dict(capacity_t_per_y=200000, hours_per_y=8000, P_bar=2.0, feed_ratio={}, inert_ratio=0.0, approach=0.98, overall_conv=1.0),
    lab_feed=dict(default_y_key=0.1, default_ratio={"H2O": 0.0}),
    switches=dict(selectivity_loss="lost"), fixed_credits=[], lost_key_fuel_GJ_per_t=26.8,
    energy=dict(pay_reaction_heat=True, furnace_eff=0.85, e_proc_GJ_per_t_reactor_feed=1.3, power_kWh_per_t_fresh=40.0,
                power_kWh_per_t_recycle=40.0, fresh_basis="key"),
    capex=dict(usd=333600000.0, fixed_share=0.5, throughput_share=0.3, reactor_share=0.2,
               reactor_basis="catalyst"),
    catalyst=CAT(2.0, 5.0), regeneration=NOREGEN,
    reference=dict(name="activated alumina (Chematur-type)", T_K=673.15, X=0.99, S=0.97, r=0.3, t_cycle_h=None, elements=[["Al", 52.9]]),
    uncertain=[dict(path="species.C2H5OH.price_usd_t", low=646.0, high=1190.0, why="Brazil 0.51 USD/L to EU 0.74 EUR/L (Haro Table 9, 2012)"),
               dict(path="capex.usd", low=round(21.3e6 * EUR_USD_2011 * (200 / 470) ** 0.6, -5), high=500300000.0,
                    why="from Haro's fixed capital alone (no other fixed costs) to 1.5 x the calibrated value"),
               dict(path="energy.e_proc_GJ_per_t_reactor_feed", low=0.6, high=2.6, why="assumption x0.5-2"),
               dict(path="reference.r", low=0.1, high=1.0, why="assumption: LHSV 0.3-2 h-1"),
               dict(path="catalyst.life_y", low=0.5, high=5.0, why="assumption")],
    sources={
        "thermo": "standard data: dH298 +45.6 kJ/mol; dG298 = 68.4 - 228.6 + 168.5 = +8.3 kJ/mol (gas-phase formation free energies) -> dS 125.2 J/mol/K; constant-dH van 't Hoff",
        "species.C2H5OH.price_usd_t": "Brazil 0.51-0.62 USD/L (Haro et al., Fuel Process. Technol. 114 (2013) 35, Table 9, Sept 2012) midpoint / 0.789 kg/L; no 2023-2025 open series found",
        "reference.X, S": "99 % conversion, 97 % selectivity (IRENA/IEA-ETSAP Tech Brief I13, 2013, p.6, citing Chematur)",
        "reference.elements": "alumina or silica-alumina (IRENA p.6); activated alumina, Al content of Al2O3",
        "ethanol use check": "1.74 t hydrated ethanol per t C2H4 (IRENA p.6) vs 1.64 t/t stoichiometric",
        "plant.capacity_t_per_y": "200 kt/y (Braskem Triunfo, IRENA p.6)",
        "plant.P_bar": "assumption 2 bar",
        "energy": "minimum 1.6 GJ/t (IRENA); e_proc calibrated to Haro's steam generator 38 MWth for 2386 kmol/h ethanol (Table 6) ~ 1.3 GJ per t ethanol feed; power assumption",
        "capex.usd": "calibrated: 333.6 M USD makes the reference plant cost equal Haro's ~1,760 EUR/t C2H4 with EU ethanol 0.73 EUR/L (Fig. 10, 2012, x 1.285 USD/EUR); it carries all non-ethanol fixed costs (Haro's FCI alone, Fig. 8, 21.3 M EUR for ~470 kt/y scaled to 200 kt/y = 17.8 M USD, is the low end)",
        "catalyst": "base 5 USD/kg (alumina), life 2 y: assumptions; Haro Table 8 catalyst 113 EUR/kg (zeolite) as upper bound",
        "check": "Haro: about 1.76 EUR/kg C2H4 with EU ethanol (2012), ethanol 85-91 % of the cost; IRENA: Brazil ~1200 USD/t, ethanol 60-75 %"})

for name, cfg in (("nh3dec", nh3dec), ("rwgs", rwgs), ("etoh", etoh)):
    (HERE / "configs" / f"{name}_ours.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
print("written nh3dec_ours.json, rwgs_ours.json, etoh_ours.json")
