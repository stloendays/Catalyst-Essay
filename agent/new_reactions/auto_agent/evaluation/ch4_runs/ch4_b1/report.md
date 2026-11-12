# CO2 methanation catalyst-to-plant ranking study

## Scope and dataset

Reaction card: **CO2 + 4 H2 -> CH4 + 2 H2O**.  The plant comparison used open-literature thermal heterogeneous CO2 methanation records only.  Electrochemical, photocatalytic, plasma-only, dry-reforming, review-only, process-only, and records without enough quantitative performance data to infer productivity were excluded.

Search/screening outcome:

- Candidate papers screened by title/abstract: 90.
- PDF downloads attempted for original experimental papers: 28 DOI attempts; 16 PDFs were successfully obtained and OCR'd.  The number of successful downloads stayed below the 20-paper ceiling.
- Extracted records from OCR: 340 rows before plausibility gates.
- Usable records after unit normalization and gates: **196**.
- Papers with at least one usable record: **13**.
- Main data losses: missing conversion, missing selectivity, or rate/flow/catalyst-mass combinations that could not support kg CH4 kg_cat^-1 h^-1.

Usable papers and records:

| paper key | usable / extracted | main note |
|---|---:|---|
| 10_1002_cctc_201701946 | 10 / 10 | zeolite-encapsulated Ni; full temperature series usable |
| 10_1007_s10562_019_03051_8 | 3 / 3 | Ni-Zn-Al/spinel records usable |
| 10_1007_s10562_022_04050_y | 23 / 72 | hydrotalcite-derived Ni; many rows lacked usable conversion |
| 10_1007_s11356_024_33327_5 | 35 / 35 | Ni/CeO2 monolith modelling/experiment records usable |
| 10_1016_j_apcatb_2018_12_063 | 6 / 8 | Ni/La-Al2O3; some conversion fields missing |
| 10_1016_j_ces_2017_09_027 | 30 / 30 | Ni/SBA-15 and related supports usable |
| 10_1021_acs_chemmater_3c01746 | 15 / 15 | Ru/Al2O3 solvent-free preparation records usable |
| 10_1021_acsaem_8b01681 | 11 / 18 | Ni/N-CNT; some rows lacked rate or flow+mass |
| 10_1021_acscatal_9b01968 | 3 / 39 | NiMn/TiO2; many rows lacked selectivity |
| 10_1038_s41467_024_47403_4 | 13 / 18 | structured CeAlOx/Ni/Ni-foam records usable |
| 10_1038_s41467_024_53909_8 | 22 / 22 | sulfate-modified Ru/TiO2 selectivity-switching dataset usable |
| 10_1038_s41563_023_01540_1 | 2 / 4 | RuOxCy@C low-temperature data partly usable |
| 10_3389_fchem_2022_1041843 | 23 / 23 | Ni/ETS-10 records usable |

Downloaded but not used in ranking:

| paper key | reason excluded from ranking |
|---|---|
| 10_1016_j_jcat_2019_12_045 | extracted records did not pass because conversion was missing for the performance entries |
| 10_1016_j_jcou_2023_102582 | extracted records did not pass because conversion was missing |
| 10_1021_acs_jpcc_6b06313 | mechanism/active-state study did not yield extractable complete productivity records |

Other screened exclusions included reviews, dry-reforming papers, electro/photo/plasma papers, sorption-enhanced or dual-function capture studies without ordinary flow methanation performance, process-design papers without catalyst records, and papers blocked or not available as open-access PDFs.

## Mechanism and transfer of lab activity to plant

The transfer model is deliberately simple and conservative:

1. **Equilibrium cap.**  The plant may not choose a per-pass CO2 conversion above gas-phase methanation equilibrium at the record temperature and plant loop pressure.  Equilibrium is calculated from NIST Shomate thermochemistry for CO2, H2, CH4 and H2O.
2. **Literature productivity sets catalyst inventory.**  The extracted rate `r` in kg CH4 kg_cat^-1 h^-1 is treated as the observed practical activity.  The packed-bed inventory scales inversely with `r`, with a mild correction when the optimized plant per-pass conversion exceeds the lab conversion.
3. **Selectivity is material.**  Methane selectivity is represented as the fraction of converted CO2 ending as CH4; the remainder is treated as CO byproduct via RWGS.  This makes low selectivity consume extra CO2/H2 and create a purge/separation burden.
4. **Deactivation.**  When `t_cycle_h` was reported, it reduces cycle-average activity and replacement interval; otherwise a 3-year catalyst life is assumed.  Few papers reported comparable deactivation, so stability attribution is weak.
5. **No hidden kinetic fit.**  The literature was too heterogeneous in catalyst form, feed dilution, GHSV, and temperature protocol to justify one universal intrinsic rate law.  A rate-law fit would create false precision; approach-to-equilibrium plus measured productivity is the evidence-supported transfer.

## Reactor and flowsheet

Accepted flowsheet hash: **8cd59226d11f4184**.

Reactor choice: cooled packed-bed methanation loop.  The reaction is strongly exothermic and equilibrium-favoured at low temperature and high pressure.  A cooled fixed bed with feed-effluent heat recovery, condensation, gas separation and recycle is the minimal industrial analogue that lets conversion, recycle and catalyst inventory trade off.

Accepted units:

1. CO2 feed compressor
2. H2 feed compressor
3. Feed mixer
4. Feed effluent heat exchanger
5. Trim feed heater
6. Methanation reactor
7. Reactor heat recovery
8. Product cooler condenser
9. Gas separation
10. Recycle compressor
11. Product compressor
12. Utilities and offsites

The submitted flowsheet includes feed preparation, reactor heat removal, product compression, water knockout, methane/reactant separation, recycle, heat recovery, and utilities/offsites.  Catalyst regeneration was explicitly excluded because the literature catalysts are run as reduced fixed beds; deactivation is represented by replacement/cycle-average activity rather than an in-situ regeneration unit.

## Parameter table

The full parameter table is in `sources.csv`.  Important values are:

| parameter | base | low-high | type/source note |
|---|---:|---:|---|
| plant capacity | 100000 t CH4/y | 10000-1000000 | assumption |
| capacity factor | 0.90 | 0.80-0.95 | assumption |
| H2 price | 2.5 USD/kg | 1-6 | assumption informed by IEA hydrogen cost ranges |
| CO2 feed price | 70 USD/t | 20-150 | assumption informed by IEA CCUS capture-cost ranges |
| electricity | 0.085 USD/kWh | 0.04-0.16 | measured; EIA Electric Power Monthly Table 5.3 |
| reactor loop pressure | 20 bar | 10-30 | assumption |
| pipeline CH4 pressure | 70 bar | 35-80 | assumption |
| compressor efficiency | 0.72 | 0.60-0.82 | assumption |
| methane recovery | 0.995 | 0.98-0.999 | assumption |
| reactant recovery | 0.98 | 0.90-0.995 | assumption |
| separation energy | 0.012 GJ/kmol dry feed | 0.0005-0.03 | assumption constrained by model mixing-minimum checks |
| base catalyst life | 3 y | 1-5 | assumption |
| Ni price | 20 USD/kg | 10-40 | published; USGS MCS 2024 |
| Co price | 35 USD/kg | 20-80 | published; USGS MCS 2024 |
| Ru price | 400000 USD/kg | 200000-800000 | assumption from PGM quotation basis |
| thermochemistry | NIST Shomate | fixed | published; NIST Chemistry WebBook |

## Checked model

`model.py` passed the independent model gate for the accepted flowsheet and all 196 usable records.  The checker verified positive finite costs, unit accounting, determinism, monotonicity, stoichiometry, mass/elements, equilibrium conversion limits, heat duty, compression and separation fields.

Reference plant input: 100 kt/y CH4 plant, 20 wt% Ni/Al2O3-like reference catalyst, 573 K, 20 bar, X = 0.80, S = 0.995, r = 1 kg CH4 kg_cat^-1 h^-1.

Reference plant result:

| cost part | USD/t CH4 | share |
|---|---:|---:|
| feed | 1460.0 | 31.4% |
| energy | 113.1 | 2.4% |
| capital | 2939.8 | 63.2% |
| catalyst replacement | 1.4 | 0.03% |
| other | 135.4 | 2.9% |
| **total** | **4649.7** | **100%** |

Reference operating point: 573 K, 20 bar, optimized per-pass conversion 0.95.  The largest cost block is capital in this screening model because the model includes a full recycle/separation/compression plant at only 100 kt/y.  The absolute cost should not be read as a commercial quote; comparisons between catalysts are the intended output.

## Ranking results

Cheapest record:

- paper: **10_1038_s41467_024_47403_4**
- catalyst: **CeAlOx/Ni/Ni-foam**
- record temperature: **240 °C**
- modelled cost: **4601.5 USD/t CH4**

Records below the reference cost: **21 / 196**.

Top records by plant cost were dominated by high-selectivity structured Ni catalysts, especially CeAlOx/Ni/Ni-foam at 513 K.  The ten cheapest records all had S approximately 1.0 and sufficient activity that catalyst inventory was not a major cost driver.

Lab ranking versus plant ranking:

| laboratory metric | point-level changes | catalyst-level changes | interpretation |
|---|---:|---:|---|
| productivity/activity | 8 / 13 paper groups changed; 61.5% | 2 / 11 changed; 18.2% | activity often selects a different temperature than the plant because feed/capital dominate once activity is adequate |
| conversion | 10 / 13 paper groups changed; 76.9% | 3 / 11 changed; 27.3% | lab conversion is strongly confounded with GHSV and temperature; recycle/equilibrium make high one-pass lab conversion less decisive |
| selectivity | 0 / 13 changed; 0% | 0 / 11 changed; 0% | selectivity directly maps to H2 and CO2 consumption, so plant and lab rankings agree when selectivity is the ranking metric |

Regret magnitudes were usually modest.  For changed point-level productivity rankings, median regret was 0.86%; for conversion it was 0.94%.  Large ranking mistakes were rarer: conversion produced >10% regret in 1 paper group, while productivity produced none above 10%.

## What controls plant cost?

The attribution analysis across all usable records gave the following shares of catalyst-caused cost variation:

| effect | attribution share |
|---|---:|
| selectivity | 0.612 |
| activity/productivity | 0.336 |
| metal cost | 0.047 |
| temperature | 0.006 |
| stability | 0.000 |

At the reference point:

- +1 percentage point selectivity changes cost by **-6.87 USD/t CH4**.
- Doubling activity changes cost by only **-1.49 USD/t CH4**.

Interpretation: the plant chooses catalysts mainly by **selectivity once activity is adequate**.  Activity still matters for very slow catalysts because it inflates reactor size and catalyst inventory, but most active Ni records rapidly enter a regime where reactor/catalyst differences are diluted by feed, recycle/separation, compression, and fixed capital.  Selectivity remains powerful because each lost carbon atom also consumes hydrogen and creates CO/vent burden; feedstock cost amplifies this penalty.

## Why rankings change

1. **Same catalyst, other temperature dominates point-level changes.**  Most productivity and conversion ranking reversals were not a plant switching to a completely different chemistry; they were the plant preferring a different temperature for the same catalyst.  Lab conversion/activity usually improve with temperature, while methanation equilibrium and selectivity can worsen.
2. **Recycle attenuates conversion.**  Low per-pass conversion increases recycle compressor and separation loads, but it does not necessarily waste all feed.  Therefore lab conversion is less decisive than once-through conversion would imply.
3. **Feedstock cost amplifies selectivity.**  Poor selectivity consumes expensive H2 and purchased CO2 per tonne of CH4.  That penalty is not recoverable by larger reactors.
4. **Equipment attenuates activity.**  Higher activity lowers catalyst inventory and reactor-size terms, but the rest of the plant remains: feed compressors, heat exchangers, separator, recycle compressor, product compressor, offsites, and feed costs.
5. **Equilibrium attenuates high-temperature activity.**  The model caps per-pass conversion by equilibrium at the record T and loop P.  Very hot records cannot buy their way to arbitrary conversion by adding catalyst.
6. **Separation and recycle attenuate temperature effects.**  Heat is mostly removed/recovered rather than bought as fuel, so reactor temperature appears weak after equilibrium and selectivity are handled.
7. **Metal price is usually attenuated.**  Precious Ru can be expensive, but highly active low-loading catalysts require little inventory.  Metal cost mattered mainly for slow or high-precious-metal records.
8. **Stability could not be ranked strongly.**  Few records reported comparable time-to-deactivation metrics, so the model mostly used the default life.

## Sensitivity to uncertain parameters

Sensitivity runs changed the absolute cost but not the identity of the cheapest record.

| scenario | best cost USD/t | best catalyst | tenth-best cost USD/t | conclusion |
|---|---:|---|---:|---|
| base | 4601.5 | CeAlOx/Ni/Ni-foam | 4611.6 | base ranking |
| H2 low 1 USD/kg | 3820.0 | CeAlOx/Ni/Ni-foam | 3830.1 | absolute cost falls; selectivity still valuable |
| H2 high 6 USD/kg | 6424.9 | CeAlOx/Ni/Ni-foam | 6435.0 | feed dominates more strongly |
| CO2 low 20 USD/t | 4459.2 | CeAlOx/Ni/Ni-foam | 4469.3 | small ranking effect |
| CO2 high 150 USD/t | 4829.1 | CeAlOx/Ni/Ni-foam | 4839.2 | selectivity penalty increases |
| electricity high 0.16 USD/kWh | 4697.7 | CeAlOx/Ni/Ni-foam | 4707.8 | recycle/separation costs rise but ranking robust |
| capex high x1.7 | 6662.5 | CeAlOx/Ni/Ni-foam | 6676.6 | absolute cost very sensitive to plant scale/capital assumptions |
| reactant recovery low 0.90 | 4612.5 | CeAlOx/Ni/Ni-foam | 4622.6 | good selectivity still dominates |
| separation energy high x3 | 4647.8 | CeAlOx/Ni/Ni-foam | 4657.9 | modest absolute penalty |
| default catalyst life 1 y | 4601.8 | CeAlOx/Ni/Ni-foam | 4616.5 | top active base-metal catalysts remain insensitive to replacement |

The conclusion is robust over the tested uncertainty ranges: **the plant would not simply choose the highest lab conversion or highest productivity point; it would choose a high-selectivity catalyst/condition with adequate activity, and the best screened option was the structured CeAlOx/Ni/Ni-foam record.**

## What the evidence could not support

- A universal intrinsic kinetic model across all catalysts: supports, metals, feed dilution, catalyst shapes and GHSV protocols were too heterogeneous.
- A rigorous catalyst lifetime ranking: deactivation tests were not reported consistently and often used different durations and criteria.
- Commercial cost certainty: many plant parameters are assumptions with ranges, not vendor quotes.
- Full dynamic operation: the model is steady-state and does not represent renewable-H2 intermittency, startup/shutdown, hot-spot control, or transient deactivation.
- Full product-quality specification: the separator is a screening representation of methane recovery and reactant recycle, not a detailed PSA/membrane design.
- Side-product chemistry beyond CO: low selectivity was represented as RWGS CO, which is the dominant simple carbon-loss route; other trace products were not modelled.
