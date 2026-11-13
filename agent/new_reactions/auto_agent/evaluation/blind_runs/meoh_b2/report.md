# Industrial catalyst choice for CO2 hydrogenation to methanol

**Reaction:** CO2 + 3 H2 -> CH3OH + H2O  \
**Model basis:** 100,000 t/y saleable methanol, 8,000 h/y, purified CO2 and H2 at the battery limit.  \
**Artifacts:** `model.py`, `flowsheet.json`, `basis.json`, `sources.csv`, `records.csv`, `costs.csv`, `analysis.json`, `sensitivity.json`, and `evidence_debt.json`.

## Executive answer

The laboratory ranking is **not reliably the plant ranking**. Across 86 usable operating points from 13 papers, choosing the highest-productivity point in each paper disagreed with the minimum-cost plant point in 7/13 papers (53.8%); highest conversion disagreed in 6/13 (46.2%). Highest selectivity was much more predictive, disagreeing in only 1/13 (7.7%).

The minimum modeled cost is **$1355/t methanol** for **M-CZZ(16)** at 220 °C (DOI 10.1038/s41467-019-09072-6). The reference ZnO-ZrO2 point costs **$1932/t**, and 32 of 86 points are cheaper.

There are two complementary meanings of “controlling property.” Across the full observed property spread, the one-at-a-time attribution assigns **98.1% to activity**, 1.8% to selectivity, and only 0.1% to temperature; the activity range spans orders of magnitude. Locally at the reference plant, however, one selectivity point changes cost by **$16.75/t**, whereas doubling activity saves only **$4.77/t**. Thus activity controls cross-literature variance, while selectivity is the stronger marginal lever after activity is high enough that catalyst inventory and reactor capital are small.

The ranking changes because the plant optimizes per-pass conversion and recycle. Reported conversion is strongly contact-time- and equilibrium-dependent; recycle attenuates its value. High activity is also attenuated once catalyst and reactor charges become small relative to purchased H2/CO2. Low selectivity is not similarly rescued: it increases fresh H2 and CO2 consumption, CO generation, purge loss, recycle compression, cooling and separation. Temperature gains are offset by worse equilibrium and higher heat/compression duties. Stability and precious-metal identity matter little in the base result because catalyst replacement is a small cost share, but that conclusion is limited by sparse lifetime and loading data.

## 1. Literature search, screening and extraction

OpenAlex searches covered Cu/Zn/Zr, ZnZrOx, In2O3, Pd/In, Pd/Zn, Au/In, Pt and related heterogeneous thermocatalysts. The initial search produced 133 candidates; title/abstract screening retained 62 high- or medium-confidence experimental candidates. Selection favored diversity and complete fixed-bed data. Seventeen PDFs were actually downloaded and OCR-parsed (below the 20-PDF cap); failed access attempts were not counted as downloaded files.

**Inclusion criteria:** primary heterogeneous, gas-phase, thermocatalytic CO2+H2 experiments; methanol separately reported; catalyst identity; T, P and feed ratio; CO2 conversion; methanol selectivity; and reported or computable productivity on a catalyst-mass basis. Stability was extracted when available.

**Exclusion criteria:** reviews/perspectives; process simulation or TEA without catalyst records; homogeneous, electrochemical, photochemical, photothermal or plasma routes; liquid batch systems; methanol reforming/decomposition; DME/hydrocarbon tandem systems without separable methanol; CO- or methane-only studies; impurity-only studies without a pure-feed baseline; and records lacking conversion, selectivity or a flow/catalyst basis.

### Usable papers

| DOI | Short title | Usable records |
|---|---|---:|
| 10.1007/s10562-016-1960-x | Methanol Synthesis from Industrial CO2 Sources | 16 |
| 10.1016/j.jcou.2019.11.013 | Enhanced catalytic performance of Zr-modified CuO/ZnO/Al2O3 | 15 |
| 10.1021/acscatal.0c04371 | Stabilizing Cu+ in Cu/SiO2 with a shattuckite-like structure | 2 |
| 10.1021/jacs.9b10873 | Au-promoted In2O3 methanol synthesis study | 8 |
| 10.1038/s41467-019-09072-6 | Ternary interactions in Cu-ZnO-ZrO2 | 4 |
| 10.1038/s41467-019-11349-9 | Pd promotion of In2O3 | 2 |
| 10.1038/s41467-020-19438-w | Cu/UiO-66 catalysts for CO2-to-methanol | 3 |
| 10.1038/s41467-020-19634-8 | ZrO2/Cu interfacial catalysts | 5 |
| 10.1038/s41467-023-36407-1 | Nanoscale H supply chain on ZnZrOx | 4 |
| 10.1038/s41467-024-47447-6 | Low-nuclearity CuZn ensembles on ZnZrOx | 2 |
| 10.1039/c6fd00189k | PdZn/TiO2 for CO2 hydrogenation to methanol | 17 |
| 10.1126/sciadv.1701290 | Highly selective and stable ZnO-ZrO2 solid solution | 5 |
| 10.3390/catal12101104 | Cu/ZnO/Al materials derived from MOF/fumed alumina routes | 3 |

### Downloaded but not usable

- **10.1021/acscatal.2c06029:** two records extracted, but conversion was missing, so neither passed normalization.
- **10.1021/acscatal.6b02928:** no complete gas-phase CO2-to-methanol operating point meeting all required fields.
- **10.1021/acscatal.9b03305:** no complete record with conversion, selectivity and normalized productivity on a common basis.
- **10.1038/s41467-022-33391-w:** quantitative information could not be normalized into a complete usable record from the parsed paper.

Other screened exclusions were predominantly reviews/TEAs, non-methanol targets, non-thermal routes, or papers missing the catalyst-mass/flow basis. `candidates.csv` preserves the title/abstract decision and reason for every screened candidate.

## 2. Scientific and modeling choices

### Mechanism and activity transfer

- Carbon selectivity is represented as methanol versus CO from RWGS for material, recycle and purge balances. The declared model thermochemistry follows the contract’s methanol reaction; RWGS is not separately parameterized in reactor heat, a limitation discussed below.
- Each record’s measured methanol productivity anchors catalyst activity. A reversible approach-to-equilibrium factor corrects activity between the laboratory and optimized plant per-pass conversion; equilibrium is a hard ceiling.
- Reported conversion is not treated as intrinsic activity. The plant chooses per-pass conversion to trade catalyst inventory against recycle compression, heat exchange and separation.
- Stability uses reported time to 10% activity loss when available; otherwise a bounded default life is used. Sparse lifetime reporting prevents a strong cross-family deactivation model.

### Reactor and flowsheet

A pressurized multi-bed fixed-bed reactor with thermal management was selected because the evidence base is continuous fixed-bed catalysis and methanol synthesis is equilibrium-limited and exothermic. The complete accepted flowsheet (SHA-256 `550b3fa7b806a7c2`) was defined before parameter sourcing or code:

```mermaid
CO2 -> [CO2 Feed Compressor] --\
                                  > [Feed Mixer] -> [Feed-Effluent Exchanger] -> [Synthesis Reactor] -> [Reactor Heat Management] --hot side--> [Feed-Effluent Exchanger] -> [Effluent Cooler] -> [Condensate Knockout] --liquid--> [Crude Methanol Distillation] -> CH3OH product
H2  -> [H2 Feed Compressor] --/                                                                                                                                        |                                      \-> [Utilities and Offsites] -> treated water
                                                                                                                                                                      \--gas--> [Recycle Purge Splitter] --purge--> boundary
                                                                                                                                                                                        \-> [Recycle Compressor] -> recycle to Feed Mixer
```

Included units are CO2 and H2 feed compressors, mixer, feed-effluent exchanger, synthesis reactor, reactor heat management, effluent cooler, condensate knockout, purge splitter, recycle compressor, methanol-water distillation, and utilities/offsites. No in-situ regenerator is modeled because the papers do not define a common regeneration protocol; catalyst replacement is costed. No product compressor is needed because condensed methanol leaves above the 2 bar battery-limit specification. Feed vaporization is unnecessary for gaseous feeds.

### Boundary and exclusions

The boundary starts with pure CO2 and H2 and ends with saleable methanol, water-rich effluent and purge. CO2 capture, H2 production/electrolysis, oxygen handling, transport, storage and distribution are excluded. Their influence enters only through fixed price-table feed prices. Feed purity was revised to 1.000 after independent critique so no unrepresented inert species accumulate.

### Atomic-scale treatment

No universal DFT or site-density descriptor is imposed. The papers do not consistently report comparable dispersion, oxidation state, in-situ surface area or active-site counts. Measured productivity carries the net active-site-density and intrinsic-rate information; elemental composition affects only catalyst material cost.

## 3. Parameter basis and sources

All prices, capital recovery and fixed O&M are frozen entries from `prices.json`. Other process and equipment values are bounded assumptions unless a paper-specific measured record supplies them. This is deliberately transparent: several process-level parameters lack defensible universal literature values across all catalyst records and are propagated through deterministic sensitivity.

| Parameter | Value | Unit | Type | Source/location | Low–high |
|---|---:|---|---|---|---|
| `thermo.methanol_reaction_enthalpy_kJ_per_mol` | -49.5 | kJ/mol | assumption | — | -52 to -47 |
| `thermo.methanol_reaction_entropy_J_per_mol_K` | -177.0 | J/mol/K | assumption | — | -185 to -169 |
| `thermo.rwgs_reaction_enthalpy_kJ_per_mol` | 41.2 | kJ/mol | assumption | — | 39 to 43 |
| `process.default_h2_co2_ratio` | 3.0 | mol/mol | assumption | — | 2.8 to 4.0 |
| `process.equilibrium_safety_fraction` | 0.5 | fraction | assumption | — | 0.4 to 0.8 |
| `process.minimum_per_pass_conversion` | 0.02 | fraction | assumption | — | 0.005 to 0.08 |
| `process.maximum_per_pass_conversion` | 0.45 | fraction | assumption | — | 0.2 to 0.65 |
| `process.purge_fraction` | 0.05 | fraction | assumption | — | 0.01 to 0.15 |
| `process.loop_pressure_drop_fraction` | 0.05 | fraction | assumption | — | 0.02 to 0.12 |
| `process.methanol_condensation_recovery` | 0.995 | fraction | assumption | — | 0.97 to 0.999 |
| `process.water_condensation_recovery` | 0.995 | fraction | assumption | — | 0.97 to 0.999 |
| `process.co2_liquid_carryover_fraction` | 0.01 | fraction | assumption | — | 0.002 to 0.05 |
| `process.distillation_methanol_recovery` | 0.995 | fraction | assumption | — | 0.98 to 0.999 |
| `process.distillation_reboiler_GJ_per_t_crude` | 1.3 | GJ/t crude | assumption | — | 0.8 to 2.5 |
| `process.distillation_electricity_GJ_per_t_crude` | 0.05 | GJ/t crude | assumption | — | 0.02 to 0.12 |
| `process.feed_effluent_heat_recovery_fraction` | 0.65 | fraction | assumption | — | 0.4 to 0.85 |
| `process.reactor_heat_recovery_fraction` | 0.5 | fraction | assumption | — | 0.2 to 0.8 |
| `process.cooling_COP` | 15.0 | GJ cooling/GJ electricity | assumption | — | 8.0 to 25.0 |
| `process.gas_heat_capacity_kJ_per_kmol_K` | 31.0 | kJ/kmol/K | assumption | — | 27.0 to 38.0 |
| `process.methanol_latent_heat_kJ_per_kg` | 1100.0 | kJ/kg | assumption | — | 1000.0 to 1200.0 |
| `process.water_latent_heat_kJ_per_kg` | 2257.0 | kJ/kg | assumption | — | 2100.0 to 2350.0 |
| `process.condensation_temperature_K` | 313.15 | K | assumption | — | 303.15 to 323.15 |
| `process.recycle_compressor_inlet_temperature_K` | 313.15 | K | assumption | — | 298.15 to 333.15 |
| `process.compressor_heat_capacity_ratio` | 1.3 | dimensionless | assumption | — | 1.25 to 1.4 |
| `process.driving_force_floor` | 0.05 | fraction | assumption | — | 0.01 to 0.2 |
| `process.default_catalyst_life_y` | 2.0 | y | assumption | — | 0.5 to 5.0 |
| `process.cycle_to_replacement_multiplier` | 6.0 | dimensionless | assumption | — | 3.0 to 10.0 |
| `process.minimum_catalyst_life_y` | 0.25 | y | assumption | — | 0.1 to 1.0 |
| `process.maximum_catalyst_life_y` | 5.0 | y | assumption | — | 3.0 to 10.0 |
| `process.unknown_component_wt_fraction` | 0.05 | fraction | assumption | — | 0.01 to 0.2 |
| `process.catalyst_working_fraction` | 0.9 | fraction | assumption | — | 0.7 to 0.98 |
| `capex.scale_exponent` | 0.65 | dimensionless | assumption | — | 0.55 to 0.8 |
| `capex.compressor_reference_cost_usd` | 2000000.0 | USD at reference power | assumption | — | 1000000.0 to 4000000.0 |
| `capex.compressor_reference_power_kW` | 1000.0 | kW | assumption | — | 800.0 to 1500.0 |
| `capex.mixer_reference_cost_usd` | 300000.0 | USD | assumption | — | 150000.0 to 800000.0 |
| `capex.heat_exchanger_reference_cost_usd` | 1500000.0 | USD at reference duty | assumption | — | 750000.0 to 3000000.0 |
| `capex.heat_exchanger_reference_duty_MW` | 5.0 | MW | assumption | — | 3.0 to 10.0 |
| `capex.reactor_base_cost_usd` | 12000000.0 | USD | assumption | — | 6000000.0 to 30000000.0 |
| `capex.knockout_reference_cost_usd` | 2000000.0 | USD | assumption | — | 1000000.0 to 5000000.0 |
| `capex.splitter_reference_cost_usd` | 250000.0 | USD | assumption | — | 100000.0 to 750000.0 |
| `capex.distillation_reference_cost_usd` | 18000000.0 | USD | assumption | — | 9000000.0 to 40000000.0 |
| `capex.offsites_fraction_direct_capex` | 0.2 | fraction | assumption | — | 0.1 to 0.4 |
| `capex.reference_loop_kmol_per_t` | 500.0 | kmol/t product | assumption | — | 250.0 to 1000.0 |
| `capex.reference_crude_t_per_t_product` | 1.6 | t crude/t product | assumption | — | 1.2 to 3.0 |
| `capex.minimum_unit_cost_usd` | 100000.0 | USD | assumption | — | 50000.0 to 300000.0 |
| `price.natural_gas` | 2.5 | USD/GJ | price_table | prices.json:natural_gas; prices.natural_gas | 2.0 to 12.0 |
| `price.electricity` | 80.0 | USD/MWh | price_table | prices.json:electricity; prices.electricity | 40.0 to 150.0 |
| `price.hydrogen` | 3.0 | USD/kg | price_table | prices.json:hydrogen; prices.hydrogen | 1.5 to 7.0 |
| `price.carbon_dioxide` | 100.0 | USD/t | price_table | prices.json:carbon_dioxide; prices.carbon_dioxide | 20.0 to 200.0 |
| `price.catalyst_support_and_manufacturing` | 20.0 | USD/kg | price_table | prices.json:catalyst_support_and_manufacturing; prices.catalyst_support_and_manufacturing | 5.0 to 100.0 |
| `price.metal_Cu` | 13.889122517655 | USD/kg | price_table | prices.json:metal_Cu; prices.metal_Cu | 6.9445612588275 to 27.77824503531 |
| `price.metal_Zn` | 3.2849 | USD/kg | price_table | prices.json:metal_Zn; prices.metal_Zn | 1.64245 to 6.5698 |
| `price.metal_Zr` | 22.0 | USD/kg | price_table | prices.json:metal_Zr; prices.metal_Zr | 11.0 to 44.0 |
| `price.metal_In` | 370.0 | USD/kg | price_table | prices.json:metal_In; prices.metal_In | 185.0 to 740.0 |
| `price.metal_Pd` | 40670.694409279 | USD/kg | price_table | prices.json:metal_Pd; prices.metal_Pd | 20335.3472046395 to 81341.388818558 |
| `price.metal_Pt` | 51508.71107755406 | USD/kg | price_table | prices.json:metal_Pt; prices.metal_Pt | 25754.35553877703 to 103017.42215510811 |
| `price.metal_Ru` | 53852.5 | USD/kg | price_table | prices.json:metal_Ru; prices.metal_Ru | 26926.25 to 107705.0 |
| `price.metal_Mg` | 2.5 | USD/kg | price_table | prices.json:metal_Mg; prices.metal_Mg | 1.25 to 5.0 |
| `price.capital_recovery_factor` | 0.0944 | 1/y | price_table | prices.json:capital_recovery_factor; prices.capital_recovery_factor | 0.08 to 0.13 |
| `price.fixed_om_fraction_of_capex` | 0.04 | 1/y | price_table | prices.json:fixed_om_fraction_of_capex; prices.fixed_om_fraction_of_capex | 0.02 to 0.06 |
| `basis.capacity_t_per_y` | 100000 | — | assumption | — | 50000 to 500000 |
| `basis.operating_hours_per_y` | 8000 | — | assumption | — | 7500 to 8400 |
| `basis.feeds.CO2.T_K` | 298.15 | — | assumption | — | 288.15 to 313.15 |
| `basis.feeds.CO2.P_bar` | 0.5 | — | assumption | — | 0.1 to 1.0 |
| `basis.feeds.CO2.purity_mol_frac` | 1.0 | — | assumption | — | 1.0 to 1.0 |
| `basis.feeds.H2.T_K` | 298.15 | — | assumption | — | 288.15 to 313.15 |
| `basis.feeds.H2.P_bar` | 0.5 | — | assumption | — | 0.1 to 1.0 |
| `basis.feeds.H2.purity_mol_frac` | 1.0 | — | assumption | — | 1.0 to 1.0 |
| `basis.product.CH3OH.P_bar` | 2.0 | — | assumption | — | 1.2 to 5.0 |
| `basis.product.CH3OH.purity_mol_frac` | 0.997 | — | assumption | — | 0.995 to 0.999 |
| `basis.utilities.compressor_isentropic_efficiency` | 0.75 | fraction | assumption | — | 0.65 to 0.85 |
| `basis.utilities.motor_efficiency` | 0.95 | fraction | assumption | — | 0.9 to 0.98 |
| `basis.utilities.cooling_water_supply_T_K` | 298.15 | K | assumption | — | 288.15 to 303.15 |
| `basis.utilities.steam_temperature_K` | 453.15 | K | assumption | — | 423.15 to 523.15 |
| `basis.utilities.steam_generation_efficiency` | 0.85 | fraction | assumption | — | 0.75 to 0.92 |
| `basis.utilities.primary_energy_factor_electricity` | 2.5 | GJ_primary/GJ_electric | assumption | — | 1.8 to 3.0 |
| `capex.reactor_reference_catalyst_inventory_kg` | 500000.0 | kg | assumption | — | 100000.0 to 2000000.0 |
| `thermo.methanol_reaction_deltaCp_kJ_per_mol_K` | -0.05 | kJ/mol/K | assumption | — | -0.08 to -0.02 |
| `capex.minimum_compressor_usd_per_kW` | 300.0 | USD/kW installed | assumption | — | 200.0 to 1000.0 |

## 4. Reference plant result

The reference is the published 13% ZnO-ZrO2 record at 300 °C and 20 bar. The optimized per-pass CO2 conversion is 4.79%. Installed capital is **$95.5 million**, purchased primary energy is **30.69 GJ/t**, and pure CO2 feed is **3.480 t/t methanol**.

| Cost component | USD/t methanol | Share |
|---|---:|---:|
| feed | 1604.61 | 83.0% |
| energy | 191.48 | 9.9% |
| capital | 90.18 | 4.7% |
| catalyst | 7.76 | 0.4% |
| other | 38.21 | 2.0% |
| **Total** | **1932.25** | **100%** |

Fresh feed is the dominant cost. The reference consumes 3.48 t CO2/t and 0.419 t H2/t because selectivity loss and purge amplify the stoichiometric requirement. This is why catalyst improvements that reduce inventory alone have limited local value.

### Reference unit energy and capital

| Unit | Type | Purchased energy (GJ/t primary) | Capex (USD million) |
|---|---|---:|---:|
| CO2 Feed Compressor | compressor | 4.002 | 6.099 |
| H2 Feed Compressor | compressor | 10.515 | 11.427 |
| Feed Mixer | other | 0.000 | 0.985 |
| Feed-Effluent Exchanger | heat_exchanger | 0.000 | 7.172 |
| Synthesis Reactor | reactor | 0.000 | 13.111 |
| Reactor Heat Management | heat_exchanger | 10.884 | 5.026 |
| Effluent Cooler | heat_exchanger | 1.435 | 4.796 |
| Condensate Knockout | knockout | 0.431 | 6.568 |
| Recycle Purge Splitter | other | 0.000 | 0.821 |
| Recycle Compressor | compressor | 1.333 | 2.985 |
| Crude Methanol Distillation | separation | 2.089 | 20.616 |
| Utilities and Offsites | offsites | 0.000 | 15.921 |

## 5. Catalyst and operating-point ranking

### Ten lowest-cost operating points

| Rank | Catalyst | DOI | T (°C) | P (bar) | Lab X | Lab S | Productivity (kg/kgcat/h) | Optimized X/pass | Cost (USD/t) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | M-CZZ(16) | 10.1038/s41467-019-09072-6 | 220 | 30.0 | 0.182 | 0.802 | 0.305 | 0.125 | 1355 |
| 2 | FSP-Cu/SiO2 | 10.1021/acscatal.0c04371 | 190 | 30.0 | 0.052 | 0.793 | 0.029 | 0.159 | 1372 |
| 3 | Cu-ZnZrOx | 10.1038/s41467-024-47447-6 | 300 | 50.0 | 0.090 | 0.900 | 0.590 | 0.122 | 1402 |
| 4 | Cu-ZnZrOx | 10.1038/s41467-024-47447-6 | 300 | 50.0 | 0.090 | 0.900 | 0.550 | 0.122 | 1402 |
| 5 | M-CZZ(19) | 10.1038/s41467-019-09072-6 | 220 | 30.0 | 0.160 | 0.760 | 0.254 | 0.125 | 1406 |
| 6 | ZrO2/Cu-0.9 (Cu/ZrO2-0.1) | 10.1038/s41467-020-19634-8 | 220 | 30.0 | 0.012 | 0.775 | 0.159 | 0.125 | 1417 |
| 7 | ZrO2/Cu-0.5 | 10.1038/s41467-020-19634-8 | 220 | 30.0 | 0.030 | 0.750 | 0.410 | 0.125 | 1425 |
| 8 | M-CZZ(24) | 10.1038/s41467-019-09072-6 | 220 | 30.0 | 0.135 | 0.720 | 0.203 | 0.125 | 1463 |
| 9 | ZrO2/Cu-0.2 | 10.1038/s41467-020-19634-8 | 220 | 30.0 | 0.030 | 0.715 | 0.400 | 0.125 | 1471 |
| 10 | FHI-standard Cu/ZnO/Al2O3 catalyst | 10.1007/s10562-016-1960-x | 200 | 30.0 | 0.035 | 0.660 | 0.280 | 0.164 | 1479 |

The winner, M-CZZ(16), is not the maximum-activity, maximum-conversion or maximum-selectivity record. It combines high enough activity with 80.2% selectivity at a comparatively favorable 220 °C and 30 bar. By contrast, the maximum-productivity Cu/UiO-66 point (3.26 kg/kgcat/h) costs about $4,878/t because selectivity is only 18%; the maximum-conversion point (45.6%) costs about $9,901/t at 6.9% selectivity; and the maximum-selectivity PdZn/TiO2 point (94%) costs about $4,658/t because activity is low and the precious-metal catalyst is expensive.

### Ranking disagreement, with denominators

| Laboratory metric | Point-level changes | Catalyst-level changes | Median regret when changed |
|---|---:|---:|---:|
| productivity | 7/13 (53.8%; 95% bootstrap CI 23.1–76.9%) | 6/9 (66.7%) | 12.5% |
| conversion | 6/13 (46.2%; 95% bootstrap CI 23.1–69.2%) | 4/9 (44.4%) | 87.2% |
| selectivity | 1/13 (7.7%; 95% bootstrap CI 0.0–23.1%) | 1/9 (11.1%) | 5.1% |

Productivity reversals were mostly a different catalyst (6 papers) rather than only a different temperature (1 paper). Conversion reversals included four different-catalyst and two same-catalyst/different-temperature choices. This directly shows that neither apparent activity nor single-pass conversion is a sufficient plant objective.

## 6. Why effects are attenuated

- **Feedstock cost:** once activity is adequate, H2 and CO2 purchases dominate. The base reference feed share is 83.0%; catalyst replacement is only 0.4%.
- **Equilibrium:** higher temperature can raise laboratory rate while lowering equilibrium conversion, forcing lower optimized per-pass conversion and more recycle.
- **Recycle:** recycle rescues low single-pass conversion, so laboratory conversion is weakly predictive; it also imposes compressor and exchanger duties, so conversion is not valueless.
- **Separation:** methanol/water condensation and distillation costs change with crude flow, but their economic effect is smaller than feed loss. Distillation duty uncertainty changes reference cost by only about 0.5%.
- **Equipment:** low activity increases catalyst inventory and reactor capital, but nth-of-a-kind capital annualization is small beside feed. Capacity and most unit-capex ranges do not change the winner.
- **Operation:** the plant does not accept the laboratory contact time; it optimizes per-pass conversion. This attenuates both reported conversion and activity differences.
- **Stability and metal:** their attribution is near zero in this dataset because few records report comparable deactivation and catalyst cost is a small share. This is an evidence limitation, not proof that lifetime and critical-metal supply never matter.

## 7. Deterministic sensitivity

Sensitivity varied every sourced range, assumption and price-table range one at a time. The base winner remained unchanged for 70/77 parameters; the minimum rank correlation was 0.987. Seven parameters changed the identity of the cheapest point, but overall ranking correlations remained high.

| Parameter | Low cost / winner | High cost / winner | Reference cost swing | Winner changes? | Min Spearman |
|---|---|---|---:|---|---:|
| `process.purge_fraction` | $1232/t; cu-znzrox | $3701/t; fsp-cu/sio2 | 127.8% | yes | 0.990 |
| `price.hydrogen` | $1304/t; m-czz(16) | $3608/t; fsp-cu/sio2 | 119.2% | yes | 0.996 |
| `thermo.methanol_reaction_entropy_J_per_mol_K` | $2486/t; fsp-cu/sio2 | $1588/t; m-czz(16) | 46.5% | yes | 0.992 |
| `process.equilibrium_safety_fraction` | $2193/t; fsp-cu/sio2 | $1552/t; m-czz(16) | 33.2% | yes | 0.993 |
| `price.carbon_dioxide` | $1654/t; m-czz(16) | $2280/t; m-czz(16) | 32.4% | no | 0.998 |
| `thermo.methanol_reaction_enthalpy_kJ_per_mol` | $1724/t; m-czz(16) | $2202/t; fsp-cu/sio2 | 24.7% | yes | 0.998 |
| `price.electricity` | $1852/t; m-czz(16) | $2072/t; m-czz(16) | 11.4% | no | 1.000 |
| `process.co2_liquid_carryover_fraction` | $1901/t; m-czz(16) | $2086/t; m-czz(16) | 9.6% | no | 1.000 |
| `price.natural_gas` | $1926/t; m-czz(16) | $2053/t; m-czz(16) | 6.6% | no | 1.000 |
| `basis.feeds.H2.P_bar` | $2014/t; m-czz(16) | $1905/t; m-czz(16) | 5.6% | no | 1.000 |
| `basis.capacity_t_per_y` | $1967/t; m-czz(16) | $1877/t; m-czz(16) | 4.7% | no | 1.000 |
| `capex.distillation_reference_cost_usd` | $1916/t; m-czz(16) | $1973/t; m-czz(16) | 3.0% | no | 1.000 |
| `process.feed_effluent_heat_recovery_fraction` | $1963/t; m-czz(16) | $1906/t; m-czz(16) | 2.9% | no | 1.000 |
| `process.methanol_condensation_recovery` | $1980/t; m-czz(16) | $1925/t; m-czz(16) | 2.9% | no | 1.000 |
| `capex.compressor_reference_cost_usd` | $1916/t; m-czz(16) | $1965/t; m-czz(16) | 2.6% | no | 1.000 |
| `price.capital_recovery_factor` | $1918/t; m-czz(16) | $1966/t; m-czz(16) | 2.5% | no | 1.000 |
| `basis.utilities.compressor_isentropic_efficiency` | $1957/t; m-czz(16) | $1913/t; m-czz(16) | 2.3% | no | 1.000 |
| `basis.feeds.CO2.P_bar` | $1965/t; m-czz(16) | $1921/t; m-czz(16) | 2.2% | no | 1.000 |
| `capex.scale_exponent` | $1918/t; m-czz(16) | $1961/t; m-czz(16) | 2.2% | no | 1.000 |
| `capex.reactor_base_cost_usd` | $1922/t; m-czz(16) | $1964/t; m-czz(16) | 2.2% | no | 1.000 |
| `capex.heat_exchanger_reference_cost_usd` | $1919/t; m-czz(16) | $1960/t; m-czz(16) | 2.1% | no | 1.000 |
| `price.fixed_om_fraction_of_capex` | $1913/t; m-czz(16) | $1951/t; m-czz(16) | 2.0% | no | 1.000 |
| `process.distillation_methanol_recovery` | $1961/t; m-czz(16) | $1925/t; m-czz(16) | 1.9% | no | 1.000 |
| `price.catalyst_support_and_manufacturing` | $1927/t; fsp-cu/sio2 | $1961/t; m-czz(16) | 1.8% | yes | 0.992 |
| `capex.offsites_fraction_direct_capex` | $1922/t; m-czz(16) | $1954/t; m-czz(16) | 1.7% | no | 1.000 |
| `process.loop_pressure_drop_fraction` | $1923/t; m-czz(16) | $1954/t; m-czz(16) | 1.6% | no | 1.000 |
| `process.default_catalyst_life_y` | $1956/t; m-czz(16) | $1928/t; fsp-cu/sio2 | 1.4% | yes | 0.987 |
| `process.compressor_heat_capacity_ratio` | $1923/t; m-czz(16) | $1951/t; m-czz(16) | 1.4% | no | 1.000 |
| `capex.knockout_reference_cost_usd` | $1927/t; m-czz(16) | $1948/t; m-czz(16) | 1.1% | no | 1.000 |
| `process.cooling_COP` | $1947/t; m-czz(16) | $1926/t; m-czz(16) | 1.1% | no | 1.000 |
| `capex.heat_exchanger_reference_duty_MW` | $1943/t; m-czz(16) | $1922/t; m-czz(16) | 1.1% | no | 1.000 |
| `process.gas_heat_capacity_kJ_per_kmol_K` | $1925/t; m-czz(16) | $1945/t; m-czz(16) | 1.1% | no | 1.000 |
| `capex.reference_crude_t_per_t_product` | $1939/t; m-czz(16) | $1921/t; m-czz(16) | 0.9% | no | 1.000 |
| `basis.utilities.motor_efficiency` | $1941/t; m-czz(16) | $1927/t; m-czz(16) | 0.7% | no | 1.000 |
| `capex.compressor_reference_power_kW` | $1937/t; m-czz(16) | $1925/t; m-czz(16) | 0.7% | no | 1.000 |
| `capex.reference_loop_kmol_per_t` | $1940/t; m-czz(16) | $1927/t; m-czz(16) | 0.7% | no | 1.000 |
| `process.distillation_reboiler_GJ_per_t_crude` | $1929/t; m-czz(16) | $1939/t; m-czz(16) | 0.5% | no | 1.000 |
| `basis.feeds.H2.T_K` | $1929/t; m-czz(16) | $1937/t; m-czz(16) | 0.4% | no | 1.000 |
| `capex.reactor_reference_catalyst_inventory_kg` | $1939/t; m-czz(16) | $1931/t; m-czz(16) | 0.4% | no | 1.000 |
| `basis.utilities.steam_generation_efficiency` | $1936/t; m-czz(16) | $1930/t; m-czz(16) | 0.3% | no | 1.000 |
| `basis.operating_hours_per_y` | $1935/t; m-czz(16) | $1930/t; m-czz(16) | 0.3% | no | 1.000 |
| `capex.minimum_compressor_usd_per_kW` | $1932/t; m-czz(16) | $1937/t; m-czz(16) | 0.3% | no | 1.000 |
| `process.distillation_electricity_GJ_per_t_crude` | $1931/t; m-czz(16) | $1935/t; m-czz(16) | 0.2% | no | 1.000 |
| `process.condensation_temperature_K` | $1934/t; m-czz(16) | $1930/t; m-czz(16) | 0.2% | no | 1.000 |
| `process.reactor_heat_recovery_fraction` | $1934/t; m-czz(16) | $1930/t; m-czz(16) | 0.2% | no | 1.000 |
| `process.catalyst_working_fraction` | $1935/t; m-czz(16) | $1931/t; m-czz(16) | 0.2% | no | 0.998 |
| `capex.mixer_reference_cost_usd` | $1931/t; m-czz(16) | $1935/t; m-czz(16) | 0.2% | no | 1.000 |
| `capex.splitter_reference_cost_usd` | $1931/t; m-czz(16) | $1935/t; m-czz(16) | 0.2% | no | 1.000 |
| `basis.feeds.CO2.T_K` | $1931/t; m-czz(16) | $1934/t; m-czz(16) | 0.2% | no | 1.000 |
| `process.unknown_component_wt_fraction` | $1932/t; m-czz(16) | $1934/t; m-czz(16) | 0.1% | no | 1.000 |
| `process.recycle_compressor_inlet_temperature_K` | $1932/t; m-czz(16) | $1933/t; m-czz(16) | 0.1% | no | 1.000 |
| `thermo.methanol_reaction_deltaCp_kJ_per_mol_K` | $1932/t; m-czz(16) | $1933/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_Zr` | $1932/t; m-czz(16) | $1933/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.water_condensation_recovery` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.methanol_latent_heat_kJ_per_kg` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.water_latent_heat_kJ_per_kg` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_Zn` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `thermo.rwgs_reaction_enthalpy_kJ_per_mol` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.default_h2_co2_ratio` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.minimum_per_pass_conversion` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.maximum_per_pass_conversion` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.driving_force_floor` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.cycle_to_replacement_multiplier` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 0.999 |
| `process.minimum_catalyst_life_y` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `process.maximum_catalyst_life_y` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `capex.minimum_unit_cost_usd` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_Cu` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_In` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_Pd` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 0.995 |
| `price.metal_Pt` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_Ru` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `price.metal_Mg` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `basis.product.CH3OH.P_bar` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `basis.product.CH3OH.purity_mol_frac` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `basis.utilities.cooling_water_supply_T_K` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `basis.utilities.steam_temperature_K` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |
| `basis.utilities.primary_energy_factor_electricity` | $1932/t; m-czz(16) | $1932/t; m-czz(16) | 0.0% | no | 1.000 |

The largest uncertainties are purge fraction (127.8% cost swing), H2 price (119.2%), effective reaction entropy/equilibrium (46.5%), equilibrium safety margin (33.2%), CO2 price (32.4%) and effective enthalpy (24.7%). Purge, H2 price and equilibrium assumptions can switch the winner among M-CZZ(16), FSP-Cu/SiO2 and Cu-ZnZrOx. Electricity, CO2 carryover, natural-gas price, feed pressure, capacity and individual unit-capex assumptions move absolute cost but generally preserve the winner.

## 8. Evidence debt, critique and limitations

The following high-impact items remain explicitly **kept as uncertainty** after targeted literature searches:
- `thermo.methanol_reaction_enthalpy_kJ_per_mol`: Final-fingerprint disposition: retained because the reduced equilibrium model lacks a full property package and the sensitivity is material. Cost swing 24.7%.
- `thermo.methanol_reaction_entropy_J_per_mol_K`: Final-fingerprint disposition: retained because one effective constant cannot represent all record temperatures and compositions without unsupported precision. Cost swing 46.5%.
- `process.equilibrium_safety_fraction`: Final-fingerprint disposition: retained because this combined practical margin is model- and reactor-specific and cannot be universally narrowed. Cost swing 33.2%.
- `process.purge_fraction`: Final-fingerprint disposition: retained because CO generation and inert-control requirements vary among catalysts and process configurations. Cost swing 127.8%.
- `process.co2_liquid_carryover_fraction`: Final-fingerprint disposition: retained because flash VLE and crude-phase CO2 carryover are not consistently reported for the catalyst records. Cost swing 9.6%.
- `process.distillation_reboiler_GJ_per_t_crude`: Final-fingerprint disposition: retained because crude composition, product specification and integration differ across published processes. Cost swing 0.5%.
- `process.feed_effluent_heat_recovery_fraction`: Final-fingerprint disposition: retained because exchanger recovery depends on catalyst-specific recycle flow and temperature approaches. Cost swing 2.9%.
- `process.gas_heat_capacity_kJ_per_kmol_K`: Final-fingerprint disposition: retained as a bounded reduced-mixture-property approximation over changing loop compositions. Cost swing 1.1%.
- `basis.feeds.CO2.P_bar`: Final-fingerprint disposition: retained because CO2 delivery pressure is set by the excluded capture and transport interface. Cost swing 2.2%.
- `basis.feeds.H2.P_bar`: Final-fingerprint disposition: retained because H2 delivery pressure is set by excluded production, storage and transport systems. Cost swing 5.6%.
- `basis.utilities.compressor_isentropic_efficiency`: Final-fingerprint disposition: retained because machine technology, scale and pressure ratio vary across candidate operating points. Cost swing 2.3%.
- `basis.utilities.primary_energy_factor_electricity`: Final-fingerprint disposition: retained because primary-energy accounting is grid- and method-dependent and does not alter monetary cost. Cost swing 0.0%.

Independent artifact critique raised six major issues. Feed purity was fixed by defining pure battery-limit feeds. Compression magnitude, heat-integration accounting, boundary methanol aggregation and reference catalyst-life sensitivity were reconciled and rejected with explicit calculations. One important limitation remains: fixed reactor thermochemistry follows the declared methanol reaction required by the model contract, while CO selectivity loss is used for material/recycle balances but RWGS heat is not separately parameterized.

Additional unsupported or weakly supported areas are: sparse comparable stability data; incomplete catalyst elemental weight fractions; generic installed-capital scaling rather than vendor quotes; reduced ideal-gas equilibrium rather than a fugacity/property package; constant mixture heat capacity and latent heats; simplified VLE/CO2 carryover; no explicit pressure-control device for the 2 bar product boundary; and no upstream capture/electrolysis design. These limitations affect absolute cost more than the broad conclusion that laboratory productivity and conversion alone are unreliable plant-ranking metrics.

## 9. Conclusions

1. **No:** laboratory activity or conversion ranking does not reliably predict the plant choice; reversals occur in roughly one-half to two-thirds of comparisons. Selectivity ranking is much more predictive.
2. The plant selects a balanced catalyst/condition, M-CZZ(16) at 220 °C and 30 bar, not any single-metric champion.
3. Across the observed dataset, activity dominates attributed variation because its range is enormous. At an already competent catalyst, selectivity is the stronger marginal economic property because it controls purchased feed and purge loss.
4. Feedstock price, equilibrium and purge dominate uncertainty. Recycle attenuates low conversion; feed dominance attenuates further activity, stability and metal-cost improvements; heat integration attenuates temperature and separation penalties.
5. The exact cheapest catalyst is not fully robust to purge, H2 price and equilibrium assumptions, but the ranking as a whole is robust (minimum Spearman 0.987), and the conclusion that single laboratory metrics are insufficient is unchanged.