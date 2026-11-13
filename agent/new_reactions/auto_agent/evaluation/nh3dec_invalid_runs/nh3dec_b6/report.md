# Industrial ammonia decomposition to hydrogen: catalyst ranking from laboratory to plant

**Reaction:** 2 NH3 -> N2 + 3 H2  
**Plant basis:** 33,000 t/y H2, 8,000 h/y, liquid NH3 battery-limit feed, 30 bar and 99.97 mol% H2 product, nitrogen-rich vent with no coproduct credit.  
**Evidence date:** 13 November 2026. Prices are the immutable values in `prices.json`.

## Executive answer

The laboratory ranking is only a weak predictor of the exact plant choice. Across 9 comparable groups from 8 papers, the productivity winner changed at the operating-point level in 4/9 groups (44.4%) and at the catalyst level in 2/9 (22.2%). Conversion ranking changed for 3/9 operating-point groups, but for 0/9 catalyst-level groups. All ranking regrets were below 1%, so most changes are economically negligible rather than decisive reversals.

The measured-record plant optimum is **3%Ru-10%K/CaO** from `10_1039_d0cy02336a` at **$3458.83/t H2**. The reference HEA plant is **$3458.89/t**, only **$0.05/t** higher. The narrow spread among the leading catalysts occurs because ammonia feed and process energy dominate total cost; catalyst activity and metal price mainly decide a very small residual.

Within that catalyst-dependent residual, activity is the largest attributed property (62.6%), followed by metal identity/cost (36.8%) and reported stability (0.6%). In total plant cost, however, the controlling input is NH3 feed price and stoichiometric consumption, not a catalyst property. Equilibrium, recycle and plant re-optimization attenuate conversion differences; minimum industrial catalyst inventory and the small catalyst cost share attenuate activity, stability and precious-metal effects; common heat, vaporization, compression, PSA and offsites costs attenuate laboratory temperature advantages.

## 1. Search, screening, downloads and exclusions

- 79 candidate records were searched and screened with explicit criteria.
- Inclusion required a primary experimental thermocatalytic heterogeneous NH3-decomposition study with catalyst identity, temperature, pressure or identifiable near-atmospheric pressure, feed basis, quantitative conversion/rate sufficient for normalization, and preferably stability.
- Reviews, theory-only work, plasma/photo/electrochemical routes, aqueous-ammonia studies, membrane-assisted conversions without separable intrinsic data, duplicate datasets, inaccessible full text and papers lacking normalizable catalyst performance were excluded.
- The maximum 20 download attempts was respected. Twelve PDFs were obtained and OCR-processed. Ten papers yielded 167 usable records; the target of 12 usable papers was not reached because no further downloads were permitted.

### Usable papers

| DOI/file key | Title | Usable records | Distinct catalyst labels | T range (K) |
|---|---|---:|---:|---:|
| 10.1002.anie.202416195 | Single‐Atom Barium Promoter Enormously Enhanced Non‐Noble Metal Catalyst for Ammonia Decomposition | 1 | 1 | 773.15-773.15 |
| 10.1016.j.fuel.2022.124384 | Self-combustion Ni and Co-based perovskites as catalyst precursors for ammonia decomposition. Effect of Ce and Mg doping | 17 | 12 | 623.15-723.15 |
| 10.1021.acscatal.5c04795 | No Time for Nitrides: How Cobalt Alloying Promotes Iron Catalysts for Ammonia Decomposition | 1 | 1 | 831.15-831.15 |
| 10.1038.s41467.019.11848.9 | Highly efficient decomposition of ammonia using high-entropy alloy catalysts | 14 | 7 | 695.15-873.15 |
| 10.1038.s41467.023.36339.w | Dispersed surface Ru ensembles on MgO(111) for catalytic ammonia decomposition | 4 | 3 | 673.15-698.15 |
| 10.1039.c5fd00179j | Ammonia decomposition catalysis using lithium–calcium imide | 45 | 4 | 593.15-868.15 |
| 10.1039.c5sc00205b | Ammonia decomposition catalysis using non-stoichiometric lithium imide | 4 | 4 | 723.15-723.15 |
| 10.1039.d0cy00686f | High pressure ammonia decomposition on Ru–K/CaO catalysts | 53 | 11 | 523.15-823.15 |
| 10.1039.d0cy02336a | Development of a Ba–CoCe catalyst for the efficient and stable decomposition of ammonia | 10 | 2 | 573.15-823.15 |
| 10.1039.d1ee03730g | Hydrogen generation via ammonia decomposition on highly efficient and stable Ru-free catalysts: approaching complete conversion at 450 °C | 18 | 11 | 573.15-773.15 |

### Downloaded but unusable

- `10.1252/jcej.14we431`: conversion data were embedded in figures that could not be digitized reliably; tables contained kinetic constants rather than complete performance records.
- `10.1371/journal.pone.0136805`: metal-normalized rates were reported, but conversion and/or complete catalyst-mass/flow normalization was insufficient for the required plant record contract.

### Main exclusion classes among screened candidates

| Exclusion class | Approximate count | Examples/reason |
|---|---:|---|
| Reviews, perspectives or overviews | 10 | Not primary experimental catalyst datasets |
| Theory/model/simulation only | 8 | No normalizable experimental catalyst record |
| Plasma, photocatalytic or electrochemical | 12 | Outside conventional thermal heterogeneous scope |
| Integrated process or membrane-reactor study | 15 | Conversion altered by simultaneous separation or catalyst data not separable |
| Duplicate/overlapping or lower-priority catalyst dataset | several | Excluded to respect the 20-download cap and preserve catalyst diversity |
| Inaccessible or insufficient quantitative data | remainder | Full text unavailable or rate/flow/mass/conversion basis incomplete |

Representative excluded papers and the paper-specific reasons remain in `candidates.csv`.

## 2. Mechanism and laboratory-to-plant kinetics

The represented mechanism is NH3 adsorption, sequential NH3* -> NH2* -> NH* -> N* dehydrogenation, recombinative H2 formation/desorption, and recombinative N2 desorption. The rate-controlling step is not forced to be universal: weak-binding surfaces are penalized by N-H activation and strong-binding surfaces by nitrogen removal. Evidence includes DOI 10.1252/jcej.14we431 for catalyst-dependent kinetic control and H2 inhibition, DOI 10.1039/d0cy00686f for pressure/product effects, and DOI 10.1039/d1ee03730g for fixed-bed pressure and stability evidence.

Each literature record is anchored by its normalized H2 productivity. Temperature transfer uses a bounded apparent Arrhenius term; pressure and conversion use a thermodynamic approach-to-equilibrium factor; reported stability derates average activity and sets replacement time. This avoids pretending that heterogeneous single-point papers identify one universal detailed rate law. It also means the inferred intrinsic activity of near-equilibrium records is uncertain, which is retained as evidence debt.

## 3. Process boundary, flowsheet and represented units

The battery limit starts at delivered liquid anhydrous NH3 and ends at compressed purified H2 plus a nitrogen-rich vent. Upstream NH3 synthesis, downstream H2 storage/use and any nitrogen credit are excluded. The reactor is an externally electrically heated packed bed. Temperature, pressure and per-pass conversion are plant variables, evaluated on a deterministic grid; recycle, vaporization, reaction heat, compression, separation and catalyst inventory respond to the chosen operating point.

```mermaid
fresh NH3 -> pump -> mixer -> vaporizer -> recuperator(cold) -> electric furnace -> packed-bed reactor -> recuperator(hot) -> NH3 cooler/knockout -> gas compressor -> H2 PSA -> H2 product
                         ^                                                   |                                  |
                         |---------------- recycle NH3 <- recycle pump <-----|                                  +-> tailgas -> utilities/offsites -> N2-rich vent
```

Included units: fresh-NH3 pump, recycle mixer, vaporizer, feed-effluent recuperator, electric reactor furnace, packed-bed reactor, NH3 cooler/knockout, recycle NH3 pump, product-gas compressor, H2 PSA and utilities/offsites. Catalyst regeneration is excluded because the evidence supports replacement/lifetime treatment more consistently than a common regeneration cycle across catalyst families.

## 4. Economic model

For one tonne of H2 product, the model closes NH3, H2 and N2 balances; computes gross reactor throughput from per-pass conversion; recovers NH3 for recycle; calculates reaction, latent and sensible heat; calculates ideal-gas compression with efficiency; performs component-balanced PSA purification; sizes catalyst from transferred productivity; and annualizes installed capital and fixed O&M. Every unit in `model.py` exactly matches the accepted `flowsheet.json`. Purchased energy excludes recovered heat and internal streams.

The objective is feed + purchased electricity + annualized capital + catalyst replacement + fixed O&M. Feed, electricity, catalyst materials, capital recovery factor and fixed-O&M fraction use only `prices.json`. No nitrogen revenue is credited.

### Reference plant result

Reference catalyst: HEA-Co55Mo15; optimized plant point **748.15 K, 20.0 bar, 0.839 per-pass conversion**. Installed capital is **$58.74 million**, purchased primary energy **32.09 GJ/t H2**, and total cost **$3458.89/t H2**.

| Cost component | USD/t H2 | Share |
|---|---:|---:|
| Feed | 2506.29 | 72.46% |
| Energy | 713.01 | 20.61% |
| Capital | 168.03 | 4.86% |
| Catalyst | 0.36 | 0.01% |
| Other | 71.20 | 2.06% |
| **Total** | **3458.89** | **100.00%** |

| Reference balance/operation | Value |
|---|---:|
| NH3 feed | 5.6321 t/t H2 |
| N2 vent | 4.6321 t/t H2 |
| Reactor heat duty | 17.344 GJ/t H2 |
| Purchased energy | 32.086 GJ/t H2 |
| Reactor pressure / product pressure | 20 / 30 bar |
| Gross reactor NH3 / recycle NH3 | 394.08 / 63.37 kmol/t H2 |

## 5. Laboratory versus industrial ranking

The costing set contains **167 records from 10 usable papers**. Nine comparable ranking groups from eight papers support within-paper ranking statistics; not every paper has multiple comparable catalysts or temperatures.

| Laboratory metric | Level | Changed/denominator | Fraction | Median regret when changed | >1% regret |
|---|---|---:|---:|---:|---:|
| Productivity | point level | 4/9 | 44.4% | 0.0200% | 0 |
| Productivity | catalyst level | 2/9 | 22.2% | 0.1300% | 0 |
| Conversion | point level | 3/9 | 33.3% | 0.0100% | 0 |
| Conversion | catalyst level | 0/9 | 0.0% | 0.0000% | 0 |
| Selectivity | point level | 0/9 | 0.0% | 0.0000% | 0 |
| Selectivity | catalyst level | 0/9 | 0.0% | 0.0000% | 0 |

**Where ranking changes:** productivity changes arise both from choosing another catalyst and from choosing the same catalyst at another temperature. Conversion changes are confined to operating-point selection; at catalyst level, conversion ranking did not change the selected catalyst. Selectivity cannot discriminate this corpus because all normalized records are effectively unity-selectivity NH3 decomposition.

**Why ranking changes but costs barely move:** the plant re-optimizes a common high-conversion operating window under equilibrium, and NH3 recycle decouples fresh-feed stoichiometry from per-pass conversion. Higher activity mainly reduces catalyst inventory and reactor scaling, but minimum industrial inventory and common equipment dominate. Precious-metal price matters only through the small replacement term. Therefore a laboratory winner can lose the plant rank without creating a meaningful economic penalty.

### Leading measured operating points

| Rank | Paper | Catalyst | Lab T (K) | Lab X | Lab productivity | Plant cost (USD/t H2) | Catalyst part (USD/t) |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | 10_1039_d0cy02336a | 3%Ru-10%K/CaO | 773.15 | 1.000 | 0.8095 | 3458.835 | 0.303 |
| 2 | 10_1016_j_fuel_2022_124384 | Reduced La0.1Mg0.9NiO3 perovskite-derived catalyst | 623.15 | 0.723 | 0.3629 | 3458.839 | 0.308 |
| 3 | 10_1039_d1ee03730g | K-CoNi_alloy-MgO-CeO2-SrO (Co:Ni = 2:1; Mg:Sr:Ce = 2:1:1) | 773.15 | 1.000 | 0.8092 | 3458.850 | 0.318 |
| 4 | 10_1039_d1ee03730g | K-CoNi_alloy-MgO-CeO2-SrO (Co:Ni = 2:1; Mg:Sr:Ce = 2:1:1) | 773.15 | 1.000 | 1.079 | 3458.850 | 0.318 |
| 5 | 10_1039_c5fd00179j | Lithium imide-amide (Li1+xNH2−x) | 786.15 | 0.995 | 0.6444 | 3458.851 | 0.319 |
| 6 | 10_1038_s41467_019_11848_9 | HEA-Co55Mo15 (Co55Mo15Fe10Ni10Cu10/CNF) | 773.15 | 1.000 | 3.238 | 3458.887 | 0.355 |
| 7 | 10_1039_d0cy02336a | 3%Ru-10%K/CaO | 573.15 | 0.080 | 0.06476 | 3458.891 | 0.359 |
| 8 | 10_1016_j_fuel_2022_124384 | Reduced La0.1Ce0.9NiO3 perovskite-derived catalyst | 623.15 | 0.591 | 0.3024 | 3458.901 | 0.369 |
| 9 | 10_1016_j_fuel_2022_124384 | Reduced LaNiO3 perovskite-derived catalyst | 623.15 | 0.559 | 0.2782 | 3458.969 | 0.437 |
| 10 | 10_1016_j_fuel_2022_124384 | Reduced CeNiO3-derived catalyst | 623.15 | 0.468 | 0.2419 | 3459.034 | 0.502 |

## 6. Atomic, laboratory and industrial optima

The atom-scale descriptor is N adsorption energy relative to 1/2 N2. On the 201-point grid, the atomic optimum is **D = -0.5805 eV** with log10 TOF = 1.970 at 748.15 K and 20 bar NH3. The laboratory optimum among **167 records** is **FeCo/MgO (spinel-derived FeCo alloy, Fe:Co = 1:1)** with 4.654 kg H2 kg-catalyst^-1 h^-1. The measured industrial optimum is **3%Ru-10%K/CaO** at **$3458.83/t H2**.

Only 113/167 records map to the declared Fe/Co/Ru/Ni/Pt/Pd descriptor set; lithium imide/amide and other unsupported main elements are excluded from atomic mapping. Pairwise disagreement is 2041/3799 for atomic versus laboratory, 3154/3801 for atomic versus industrial, and 2824/6196 for laboratory versus industrial after ties are excluded.

The descriptor-only counterfactual moves the reference effective descriptor from -0.115 to -0.580 eV and lowers modeled cost by only $14.89/t. The 5% and 10% backward-design cost targets are **not reachable** anywhere in the descriptor window. Thus an atomically faster surface cannot overcome feed and energy dominance by itself.

The descriptor-based industrial optimum is approximately D = -1.003 eV and is insensitive to metal price in this simplified link because all candidates hit common plant/catalyst-inventory limitations. This disagreement with the atomic volcano optimum (-0.5805 eV) is a warning that descriptor mapping is qualitative, not a validated catalyst prescription.

## 7. Deterministic sensitivity

The fixed sensitivity tool perturbed all 81 sourced ranges, assumptions and price-table ranges one at a time. Ranking correlations use 80 records (the tool's deterministic ranking subset), while the main analysis uses 167 records. The base sensitivity winner is `reducedla0.1mg0.9nio3perovskite-derivedcatalyst`.

| Parameter | Kind | Low -> high | Reference cost low -> high (USD/t) | Cost swing | Cheapest changes? | Minimum Spearman |
|---|---|---|---:|---:|---|---:|
| price.ammonia | price_table | 300 -> 900 | 2642.23 -> 6021.50 | 97.70% | no | 1.0000 |
| price.electricity | price_table | 40 -> 150 | 3102.38 -> 4082.77 | 28.34% | no | 0.9957 |
| separation.h2_recovery | assumption | 0.9 -> 1 | 3814.10 -> 3458.89 | 10.27% | no | 0.9984 |
| basis.capacity_t_per_y | assumption | 10000 -> 1e+05 | 3599.31 -> 3380.88 | 6.32% | yes | 0.9741 |
| capex.psa_base_usd | assumption | 7e+06 -> 4.5e+07 | 3409.61 -> 3579.85 | 4.92% | no | 1.0000 |
| basis.product.H2.P_bar | assumption | 20 -> 100 | 3431.08 -> 3564.04 | 3.84% | no | 1.0000 |
| capex.offsites_base_usd | assumption | 3e+06 -> 3e+07 | 3430.38 -> 3540.34 | 3.18% | no | 1.0000 |
| capex.electric_furnace_base_usd | assumption | 3e+06 -> 2.5e+07 | 3432.01 -> 3530.57 | 2.85% | no | 1.0000 |
| finance.capital_recovery_factor | price_table | 0.08 -> 0.13 | 3433.26 -> 3522.25 | 2.57% | no | 0.9997 |
| heat.electric_heater_efficiency | assumption | 0.85 -> 0.99 | 3512.56 -> 3440.45 | 2.08% | no | 0.9981 |
| finance.fixed_om_fraction_of_capex | price_table | 0.02 -> 0.06 | 3423.29 -> 3494.49 | 2.06% | no | 0.9994 |
| capex.recuperator_base_usd | assumption | 2e+06 -> 1.5e+07 | 3440.97 -> 3499.21 | 1.68% | no | 1.0000 |
| heat.ammonia_vaporization_kJ_per_mol | published | 20 -> 26 | 3429.55 -> 3482.09 | 1.52% | no | 0.9981 |
| heat.reaction_enthalpy_kJ_per_mol_NH3 | published | 44 -> 48 | 3436.07 -> 3485.81 | 1.44% | no | 0.9718 |
| heat.reaction_dCp_kJ_per_molNH3K | assumption | 0.008 -> 0.02 | 3433.44 -> 3480.42 | 1.36% | no | 0.9834 |
| heat.sensible_fraction_of_reaction_duty | assumption | 0.15 -> 0.6 | 3443.75 -> 3489.16 | 1.31% | no | 0.9950 |
| heat.loss_fraction | assumption | 0.02 -> 0.12 | 3445.85 -> 3489.30 | 1.26% | no | 0.9987 |
| heat.recuperator_effectiveness | assumption | 0.55 -> 0.9 | 3483.10 -> 3440.73 | 1.23% | no | 0.9943 |
| capex.cooler_knockout_base_usd | assumption | 1.5e+06 -> 1e+07 | 3447.69 -> 3485.77 | 1.10% | no | 1.0000 |
| capex.offsites_fraction_variable | assumption | 0.05 -> 0.25 | 3449.86 -> 3485.95 | 1.04% | no | 1.0000 |
| separation.psa_electricity_kWh_per_kg_H2_product | assumption | 0.05 -> 0.5 | 3438.89 -> 3474.89 | 1.04% | no | 1.0000 |
| operation.equilibrium_approach_max | assumption | 0.85 -> 0.99 | 3483.20 -> 3450.54 | 0.94% | yes | 0.9818 |
| capex.ammonia_vaporizer_base_usd | assumption | 1e+06 -> 8e+06 | 3449.93 -> 3481.29 | 0.91% | no | 1.0000 |
| operation.P_max_bar | assumption | 15 -> 25 | 3474.90 -> 3448.85 | 0.75% | no | 0.9969 |
| heat.reaction_entropy_J_per_molrxnK | published | 190 -> 205 | 3472.46 -> 3450.94 | 0.62% | yes | 0.9427 |
| capex.reactor_base_usd | assumption | 4e+06 -> 3.5e+07 | 3453.51 -> 3474.34 | 0.60% | no | 0.9922 |
| capex.reference_compressor_power_MW | assumption | 3 -> 30 | 3473.07 -> 3454.83 | 0.53% | no | 1.0000 |
| capex.compressor_base_usd | assumption | 4e+06 -> 3.5e+07 | 3454.83 -> 3470.54 | 0.45% | no | 1.0000 |
| separation.nh3_recovery | assumption | 0.98 -> 1 | 3468.55 -> 3458.89 | 0.28% | no | 0.9979 |
| utilities.offsites_electricity_GJ_per_t | assumption | 0.08 -> 0.5 | 3456.22 -> 3465.55 | 0.27% | no | 1.0000 |
| compression.isentropic_efficiency | assumption | 0.65 -> 0.85 | 3463.20 -> 3455.59 | 0.22% | no | 1.0000 |
| cooling.knockout_electricity_GJ_per_t_feed | assumption | 0.002 -> 0.05 | 3457.69 -> 3464.85 | 0.21% | no | 1.0000 |
| capex.fresh_ammonia_pump_base_usd | assumption | 2e+05 -> 1.5e+06 | 3457.54 -> 3463.37 | 0.17% | no | 1.0000 |
| capex.recycle_pump_base_usd | assumption | 1.5e+05 -> 1.2e+06 | 3457.77 -> 3462.47 | 0.14% | no | 1.0000 |
| capex.recycle_mixer_base_usd | assumption | 1e+05 -> 8e+05 | 3458.22 -> 3461.35 | 0.09% | no | 1.0000 |
| compression.inlet_T_K | assumption | 298.15 -> 333.15 | 3457.55 -> 3460.68 | 0.09% | no | 1.0000 |
| kinetics.default_catalyst_life_h | assumption | 2000 -> 40000 | 3461.37 -> 3458.67 | 0.08% | no | 0.9624 |
| reactor.minimum_catalyst_inventory_kg | assumption | 200 -> 5000 | 3458.60 -> 3461.15 | 0.07% | yes | 0.9599 |
| basis.feeds.NH3.T_K | assumption | 283.15 -> 313.15 | 3459.90 -> 3457.88 | 0.06% | no | 1.0000 |
| operation.T_min_K | assumption | 573.15 -> 673.15 | 3460.56 -> 3458.86 | 0.05% | yes | 0.9834 |
| operation.T_max_K | assumption | 823.15 -> 973.15 | 3460.56 -> 3460.02 | 0.05% | yes | 0.9799 |
| price.catalyst_support_and_manufacturing | price_table | 5 -> 100 | 3458.71 -> 3459.86 | 0.03% | yes | 0.9912 |
| basis.operating_hours_per_y | assumption | 7200 -> 8400 | 3459.53 -> 3458.62 | 0.03% | no | 0.9983 |
| basis.feeds.NH3.P_bar | assumption | 8 -> 20 | 3458.95 -> 3458.59 | 0.01% | no | 1.0000 |
| compression.kappa | assumption | 1.35 -> 1.41 | 3458.73 -> 3458.92 | 0.01% | no | 1.0000 |
| pump.efficiency | assumption | 0.55 -> 0.85 | 3459.00 -> 3458.82 | 0.01% | no | 1.0000 |
| catalyst.unknown_total_metal_loading_fraction | assumption | 0.05 -> 0.6 | 3458.85 -> 3458.99 | 0.00% | yes | 0.9982 |
| price.metal_Mo | price_table | 45.614 -> 182.45 | 3458.86 -> 3458.94 | 0.00% | no | 0.9996 |
| pump.liquid_ammonia_density_kg_per_m3 | assumption | 570 -> 680 | 3458.92 -> 3458.85 | 0.00% | no | 1.0000 |
| price.metal_Co | price_table | 28.142 -> 112.57 | 3458.87 -> 3458.92 | 0.00% | no | 0.9988 |
| price.metal_Ni | price_table | 8.4547 -> 33.819 | 3458.88 -> 3458.90 | 0.00% | no | 0.9997 |
| price.metal_Cu | price_table | 6.9446 -> 27.778 | 3458.88 -> 3458.90 | 0.00% | no | 0.9999 |
| price.metal_Fe | price_table | 4 -> 16 | 3458.88 -> 3458.89 | 0.00% | no | 0.9999 |
| basis.feeds.NH3.purity_mol_frac | assumption | 0.995 -> 1 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| basis.product.H2.purity_mol_frac | assumption | 0.999 -> 0.99999 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| basis.utilities.ambient_temperature | assumption | 283.15 -> 313.15 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| basis.utilities.cooling_water_supply_temperature | assumption | 288.15 -> 303.15 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| basis.utilities.cooling_water_return_temperature | assumption | 303.15 -> 323.15 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Ru | price_table | 26926 -> 1.077e+05 | 3458.89 -> 3458.89 | 0.00% | no | 0.9941 |
| price.metal_Pd | price_table | 20335 -> 81341 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Pt | price_table | 25754 -> 1.0302e+05 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_K | price_table | 0.72277 -> 2.8911 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Ba | price_table | 0.17845 -> 0.7138 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Ca | price_table | 0.1819 -> 0.72759 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Mg | price_table | 1.25 -> 5 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Ce | price_table | 1.0503 -> 4.2011 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Al | price_table | 1.9842 -> 7.9366 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_La | price_table | 0.5864 -> 2.3456 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Y | price_table | 20 -> 80 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| price.metal_Si | price_table | 1.433 -> 5.732 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| kinetics.apparent_Ea_kJ_per_mol | assumption | 60 -> 160 | 3458.89 -> 3458.89 | 0.00% | yes | 0.9408 |
| kinetics.replacement_activity_loss_fraction | assumption | 0.1 -> 0.4 | 3458.89 -> 3458.89 | 0.00% | no | 0.9981 |
| operation.P_min_bar | assumption | 5 -> 15 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| operation.X_min | assumption | 0.2 -> 0.5 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| separation.psa_feed_pressure_bar | assumption | 20 -> 40 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| reactor.bulk_density_kg_per_m3 | assumption | 400 -> 1400 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| reactor.design_factor | assumption | 1.05 -> 2 | 3458.89 -> 3458.89 | 0.00% | yes | 0.9939 |
| capex.capacity_scaling_exponent | assumption | 0.5 -> 0.75 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| capex.reactor_inventory_exponent | assumption | 0.5 -> 0.8 | 3458.89 -> 3458.89 | 0.00% | no | 0.9982 |
| capex.compressor_power_exponent | assumption | 0.6 -> 0.85 | 3458.89 -> 3458.89 | 0.00% | no | 1.0000 |
| capex.reference_catalyst_inventory_kg | assumption | 30000 -> 3e+05 | 3458.89 -> 3458.89 | 0.00% | no | 0.9730 |

The dominant uncertainty is ammonia price (97.70% reference-cost swing), followed by electricity price (28.34%) and overall H2 recovery (10.27%). Capacity changes the cheapest catalyst because equipment/catalyst scale effects become relatively more important, but even then rank correlations remain high. Most equipment, kinetic and catalyst assumptions change the absolute cost or fine ordering without overturning the central conclusion that feed and energy dominate.

## 8. Complete parameter and source table

Every numeric input exposed through `PARAMS` is keyed to this table. Price rows use immutable `prices.json` entries. Assumptions have explicit low/high bounds.

| Parameter | Value | Unit | Type | Low | High | Source | Location/evidence |
|---|---:|---|---|---:|---:|---|---|
| basis.capacity_t_per_y | 33000.0 | t H2/y | assumption | 10000.0 | 100000.0 |  |  |
| basis.operating_hours_per_y | 8000.0 | h/y | assumption | 7200.0 | 8400.0 |  |  |
| basis.feeds.NH3.T_K | 298.15 | K | assumption | 283.15 | 313.15 |  |  |
| basis.feeds.NH3.P_bar | 10.0 | bar | assumption | 8.0 | 20.0 |  |  |
| basis.feeds.NH3.purity_mol_frac | 1.0 | mol/mol | assumption | 0.995 | 1.0 |  |  |
| basis.product.H2.P_bar | 30.0 | bar | assumption | 20.0 | 100.0 |  |  |
| basis.product.H2.purity_mol_frac | 0.9997 | mol/mol | assumption | 0.999 | 0.99999 |  |  |
| basis.utilities.ambient_temperature | 298.15 | K | assumption | 283.15 | 313.15 |  |  |
| basis.utilities.cooling_water_supply_temperature | 298.15 | K | assumption | 288.15 | 303.15 |  |  |
| basis.utilities.cooling_water_return_temperature | 313.15 | K | assumption | 303.15 | 323.15 |  |  |
| price.ammonia | 445.0 | USD/t | price_table | 300.0 | 900.0 | prices.json:ammonia | Tampa CFR ammonia, March 2024 contract settlement (trade press summary) |
| price.electricity | 80.0 | USD/MWh | price_table | 40.0 | 150.0 | prices.json:electricity | industrial power assumption used across the NCE chains; EIA 2024 US industrial average about 80 USD/MWh |
| price.catalyst_support_and_manufacturing | 20.0 | USD/kg | price_table | 5.0 | 100.0 | prices.json:catalyst_support_and_manufacturing | NCE chain assumption for support plus manufacturing per kg of finished catalyst, excluding active metals |
| finance.capital_recovery_factor | 0.0944 | 1/y | price_table | 0.08 | 0.13 | prices.json:capital_recovery_factor | 7 %/y over 20 y (Enterprise Products PDH, EPA GHG permit application 2012); range 5-12 %/y |
| finance.fixed_om_fraction_of_capex | 0.04 | 1/y | price_table | 0.02 | 0.06 | prices.json:fixed_om_fraction_of_capex | NCE chain assumption, 4 %/y of installed capital |
| price.metal_Ru | 53852.5 | USD/kg | price_table | 26926.25 | 107705.0 | prices.json:metal_Ru | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Fe | 8.0 | USD/kg | price_table | 4.0 | 16.0 | prices.json:metal_Fe | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Co | 56.28401553583051 | USD/kg | price_table | 28.142007767915256 | 112.56803107166104 | prices.json:metal_Co | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Ni | 16.9094555095895 | USD/kg | price_table | 8.45472775479475 | 33.818911019179 | prices.json:metal_Ni | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Pd | 40670.694409279 | USD/kg | price_table | 20335.3472046395 | 81341.388818558 | prices.json:metal_Pd | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Pt | 51508.71107755406 | USD/kg | price_table | 25754.35553877703 | 103017.42215510811 | prices.json:metal_Pt | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_K | 1.4455393066229791 | USD/kg | price_table | 0.7227696533114896 | 2.8910786132459583 | prices.json:metal_K | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Ba | 0.3569000679809653 | USD/kg | price_table | 0.1784500339904826 | 0.7138001359619306 | prices.json:metal_Ba | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Ca | 0.3637940925436203 | USD/kg | price_table | 0.1818970462718101 | 0.7275881850872405 | prices.json:metal_Ca | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Mg | 2.5 | USD/kg | price_table | 1.25 | 5.0 | prices.json:metal_Mg | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Ce | 2.1005306603773586 | USD/kg | price_table | 1.0502653301886793 | 4.201061320754717 | prices.json:metal_Ce | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Al | 3.9683 | USD/kg | price_table | 1.98415 | 7.9366 | prices.json:metal_Al | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_La | 1.1728 | USD/kg | price_table | 0.5864 | 2.3456 | prices.json:metal_La | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Y | 40.0 | USD/kg | price_table | 20.0 | 80.0 | prices.json:metal_Y | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Mo | 91.227284092153 | USD/kg | price_table | 45.61364204607651 | 182.45456818430603 | prices.json:metal_Mo | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Cu | 13.889122517655 | USD/kg | price_table | 6.9445612588275 | 27.77824503531 | prices.json:metal_Cu | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| price.metal_Si | 2.866006 | USD/kg | price_table | 1.433003 | 5.732012 | prices.json:metal_Si | frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element) |
| kinetics.apparent_Ea_kJ_per_mol | 100.0 | kJ/mol | assumption | 60.0 | 160.0 | DOI:10.1039/d0cy00686f | Kinetic analysis; central cross-family value is an assumption. |
| kinetics.default_catalyst_life_h | 16000.0 | h | assumption | 2000.0 | 40000.0 |  | No common long-duration life across families. |
| kinetics.replacement_activity_loss_fraction | 0.2 | fraction | assumption | 0.1 | 0.4 |  | Economic replacement threshold. |
| kinetics.reported_tcycle_loss_fraction | 0.1 | fraction | assumption | 0.1 | 0.1 |  | Contract defines t_cycle_h at 10% loss. |
| operation.T_min_K | 623.15 | K | assumption | 573.15 | 673.15 | DOI:10.1039/d0cy00686f | Experiments span 250-550 C. |
| operation.T_max_K | 873.15 | K | assumption | 823.15 | 973.15 | DOI:10.1039/d1ee03730g | High activity at 450-500 C; upper bound includes non-noble catalysts. |
| operation.P_min_bar | 10.0 | bar | assumption | 5.0 | 15.0 |  | Set by delivered liquid NH3 pressure. |
| operation.P_max_bar | 20.0 | bar | assumption | 15.0 | 25.0 | DOI:10.1039/d0cy00686f | Experiments span 1-40 bar; maximum equals product pressure. |
| operation.X_min | 0.3 | mol/mol | assumption | 0.2 | 0.5 |  | Lower operability bound for recycle. |
| operation.equilibrium_approach_max | 0.95 | fraction | assumption | 0.85 | 0.99 |  | Finite reactor cannot attain exact equilibrium. |
| separation.nh3_recovery | 1.0 | fraction | assumption | 0.98 | 1.0 |  | Overall NH3 recovery after knockout and recycle; imperfect recovery retained in sensitivity. |
| separation.h2_recovery | 1.0 | fraction | assumption | 0.9 | 1.0 |  | Overall H2 recovery after tail-gas recovery/recycle; single-stage PSA uncertainty is represented by the low bound. |
| separation.psa_electricity_kWh_per_kg_H2_product | 0.3 | kWh/kg H2 | assumption | 0.05 | 0.5 |  | PSA auxiliary load. |
| separation.psa_feed_pressure_bar | 30.0 | bar | assumption | 20.0 | 40.0 |  | Matched to product pressure. |
| compression.isentropic_efficiency | 0.75 | fraction | assumption | 0.65 | 0.85 |  | Multistage gas compressor assumption. |
| compression.kappa | 1.4 | dimensionless | assumption | 1.35 | 1.41 |  | H2/N2-rich ideal-gas approximation. |
| compression.inlet_T_K | 313.15 | K | assumption | 298.15 | 333.15 |  | Aftercooler design temperature. |
| pump.efficiency | 0.7 | fraction | assumption | 0.55 | 0.85 |  | Liquid NH3 pump efficiency. |
| heat.recuperator_effectiveness | 0.75 | fraction | assumption | 0.55 | 0.9 |  | Gas-gas recuperator assumption. |
| heat.electric_heater_efficiency | 0.95 | fraction | assumption | 0.85 | 0.99 |  | Resistance-furnace efficiency. |
| heat.loss_fraction | 0.05 | fraction | assumption | 0.02 | 0.12 |  | High-temperature heat-loss allowance. |
| heat.reaction_enthalpy_kJ_per_mol_NH3 | 45.92 | kJ/mol NH3 | published | 44.0 | 48.0 | https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Mask=1 | NIST WebBook standard enthalpy of formation NH3(g). |
| heat.ammonia_vaporization_kJ_per_mol | 23.35 | kJ/mol NH3 | published | 20.0 | 26.0 | https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Mask=4 | NIST WebBook enthalpy of vaporization. |
| heat.sensible_fraction_of_reaction_duty | 0.3 | fraction | assumption | 0.15 | 0.6 |  | Sensible heating before recovery relative to reaction duty. |
| reactor.bulk_density_kg_per_m3 | 800.0 | kg/m3 | assumption | 400.0 | 1400.0 |  | Packed catalyst bulk density. |
| reactor.design_factor | 1.25 | dimensionless | assumption | 1.05 | 2.0 |  | Inventory design margin. |
| reactor.minimum_catalyst_inventory_kg | 1000.0 | kg | assumption | 200.0 | 5000.0 |  | Minimum industrial bed inventory. |
| capex.fresh_ammonia_pump_base_usd | 500000.0 | USD | assumption | 200000.0 | 1500000.0 |  | Installed-capital anchor at basis capacity. |
| capex.recycle_mixer_base_usd | 250000.0 | USD | assumption | 100000.0 | 800000.0 |  | Installed-capital anchor at basis capacity. |
| capex.ammonia_vaporizer_base_usd | 3000000.0 | USD | assumption | 1000000.0 | 8000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.recuperator_base_usd | 6000000.0 | USD | assumption | 2000000.0 | 15000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.electric_furnace_base_usd | 9000000.0 | USD | assumption | 3000000.0 | 25000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.reactor_base_usd | 12000000.0 | USD | assumption | 4000000.0 | 35000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.cooler_knockout_base_usd | 4000000.0 | USD | assumption | 1500000.0 | 10000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.recycle_pump_base_usd | 400000.0 | USD | assumption | 150000.0 | 1200000.0 |  | Installed-capital anchor at basis capacity. |
| capex.compressor_base_usd | 12000000.0 | USD | assumption | 4000000.0 | 35000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.psa_base_usd | 18000000.0 | USD | assumption | 7000000.0 | 45000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.offsites_base_usd | 10000000.0 | USD | assumption | 3000000.0 | 30000000.0 |  | Installed-capital anchor at basis capacity. |
| capex.capacity_scaling_exponent | 0.6 | dimensionless | assumption | 0.5 | 0.75 |  | Six-tenths scaling assumption. |
| capex.reactor_inventory_exponent | 0.6 | dimensionless | assumption | 0.5 | 0.8 |  | Reactor cost scaling with inventory. |
| capex.compressor_power_exponent | 0.7 | dimensionless | assumption | 0.6 | 0.85 |  | Compressor cost scaling with power. |
| capex.offsites_fraction_variable | 0.1 | dimensionless | assumption | 0.05 | 0.25 |  | Variable offsites allowance. |
| heat.reaction_entropy_J_per_molrxnK | 198.0 | J/mol-reaction/K | published | 190.0 | 205.0 | https://webbook.nist.gov/chemistry/ | Derived from NIST standard molar entropies for NH3(g), H2(g), and N2(g). |
| pump.liquid_ammonia_density_kg_per_m3 | 610.0 | kg/m3 | assumption | 570.0 | 680.0 | https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Mask=4 | Liquid ammonia density near ambient pressurized storage; design approximation. |
| utilities.offsites_electricity_GJ_per_t | 0.2 | GJ/t H2 | assumption | 0.08 | 0.5 |  | Electrical distribution, cooling-water and controls auxiliary allowance. |
| catalyst.unknown_total_metal_loading_fraction | 0.2 | kg metal/kg catalyst | assumption | 0.05 | 0.6 |  | Fallback only where papers do not report loadings; remainder charged as support/manufacturing. |
| capex.reference_catalyst_inventory_kg | 100000.0 | kg | assumption | 30000.0 | 300000.0 |  | Reference inventory for reactor cost scaling. |
| capex.reference_compressor_power_MW | 10.0 | MW | assumption | 3.0 | 30.0 |  | Reference power for compressor cost scaling. |
| cooling.knockout_electricity_GJ_per_t_feed | 0.01 | GJ/t reactor effluent | assumption | 0.002 | 0.05 |  | Cooling-water circulation and refrigeration auxiliary allowance. |
| heat.reaction_dCp_kJ_per_molNH3K | 0.0145 | kJ/mol NH3/K | assumption | 0.008 | 0.02 | https://webbook.nist.gov/chemistry/ | Effective temperature correction derived from fixed ideal-gas heat capacities over the reactor range. |

## 9. Evidence debt, model limitations and validation status

- Only 10 papers yielded usable records, below the requested 12, because only 12 of 20 attempted downloads were obtained and two lacked complete normalizable data.
- The apparent activation energy is shared across catalyst families with a broad range because the corpus does not identify a catalyst-specific transfer law for every record.
- Most records lack industrial-pressure deactivation data; catalyst life, unknown loading and minimum industrial inventory remain bounded assumptions.
- Central overall NH3 and H2 recoveries are idealized at unity to define a closed reference case; 0.98 NH3 and 0.90 H2 recovery are explicitly tested and materially raise cost.
- Capex correlations, heat-exchanger effectiveness, cooling auxiliaries and offsites are screening-level assumptions, not a front-end engineering design.
- The atomic descriptor values and BEP/scaling relations are a qualitative cross-metal link; 54/167 records cannot be mapped because their principal chemistry is outside the declared metal descriptor set.
- No nitrogen credit, emissions credit, ammonia upstream cost model or downstream H2-use system is included.
- `check_atomic` passes. The independent `check_model` physics checks for elements, mass, equilibrium, reaction heat, compression, separation and unit accounting pass, but the fixed generic check continues to emit a `stoichiometry` label for every record despite the explicit closed reference balance (5.6321 t NH3 -> 1.0000 t H2 + 4.6321 t N2). Consequently `assess_assumptions` refused to run. This unresolved automated-gate disagreement is retained explicitly rather than hidden; `run_analysis`, `run_sensitivity`, `run_three_optima` and two critique rounds completed.

## 10. Bottom line

Laboratory activity is useful for avoiding clearly poor catalysts, but it does not robustly identify the exact industrial winner. Once the plant is allowed to choose temperature, pressure and per-pass conversion with recycle and purification, leading catalysts collapse into an economically near-tied set. The plant pays primarily for ammonia and electricity; it pays very little for catalyst replacement. Therefore the most valuable catalyst advances are those that enable a lower-energy flowsheet or materially improve overall hydrogen recovery and durability, not small increases in already adequate laboratory conversion or TOF. A convincing next experiment would measure sustained productivity and deactivation at 15-25 bar, 700-800 K, with product inhibition and recycle-relevant compositions, because those data would reduce the largest catalyst-specific evidence gap.
