# CO2 methanation catalyst-to-plant ranking report

## Scope and screening

Reaction modelled: `CO2 + 4 H2 -> CH4 + 2 H2O`, with lower-selectivity carbon represented as RWGS CO byproduct to preserve mass balance. The search targeted primary open-access experimental thermal CO2 methanation papers with catalyst identity plus enough quantitative data to recover temperature, pressure or atmospheric pressure, feed ratio, CO2 conversion, CH4 selectivity and CH4 productivity or flow/catalyst data.

Screening inclusion criteria were: heterogeneous thermal CO2 hydrogenation to methane; flow/fixed-bed or otherwise steady catalytic data; catalyst composition or at least named catalyst; quantitative X, S and rate/productivity or enough feed/space-velocity/catalyst-mass information to calculate productivity. Exclusions were reviews, thermodynamic/process-only papers, electro/photo/plasma-only papers without a thermal record, dry reforming/CO2 reforming of methane, methanol or higher-alcohol synthesis, CO-only methanation, and records without enough conversion/selectivity/activity data.

Downloaded/OCR-parsed papers: 16. Papers with at least one usable record: 13. Usable records: 163.

| paper stem / DOI form | extracted records | usable | main reason unusable records were dropped |
|---|---:|---:|---|
| 10_1007_s11244_023_01823_6 | 19 | 18 | one missing conversion |
| 10_1007_s11356_024_33327_5 | 36 | 36 | none |
| 10_1016_j_apcatb_2018_12_063 | 6 | 5 | one missing conversion |
| 10_1016_j_fuel_2018_07_157 | 10 | 10 | none |
| 10_1021_acs_chemmater_3c01746 | 15 | 15 | none |
| 10_1021_acscatal_7b01896 | 28 | 27 | selectivity missing for one record |
| 10_1021_acscatal_9b01968 | 49 | 3 | most records lacked selectivity |
| 10_1038_s41467_024_53909_8 | 25 | 16 | several lacked selectivity |
| 10_1038_s41563_023_01540_1 | 5 | 2 | missing conversion |
| 10_1038_s41598_023_31958_1 | 6 | 5 | one missing selectivity |
| 10_3389_fchem_2022_1041843 | 10 | 10 | none |
| 10_3390_nano13030506 | 15 | 15 | none |
| 10_9767_bcrec_20108 | 20 | 1 | most records lacked conversion |
| 10_1002_anie_202007228 | 15 | 0 | no rate or flow plus mass for productivity |
| 10_1021_acs_iecr_1c00389 | 13 | 0 | selectivity missing |
| 10_1038_s41467_019_10464_x | 8 | 0 | conversion missing |

Six extracted records were rejected by plausibility gates as printed-rate/unit outliers above 50 kg CH4 kgcat-1 h-1.

## Mechanism and kinetics transfer

The literature set is too heterogeneous for a single defensible microkinetic law: Ni, Ni-alloys, Ru and supported/structured catalysts report apparent rates under different temperatures, pressures, feed ratios and space velocities. I therefore used an empirical transfer model:

1. The reported CH4 productivity is the apparent plant space-time yield at the record temperature and pressure.
2. Plant per-pass CO2 conversion is optimized but capped by the lower of the reported lab conversion, 95%, and 98% of equilibrium conversion.
3. If the plant chooses a conversion below the reported lab conversion, catalyst requirement scales approximately as `X_plant / X_lab`, a plug-flow/differential approximation before severe equilibrium slowdown.
4. Selectivity below one creates CO by RWGS and therefore increases fresh CO2/H2 demand, purge, recycle and separation load.
5. Reported time to 10% deactivation is converted into a replacement-equivalent catalyst life; otherwise a 3-year base catalyst life is used.

This transfer uses what the evidence supports directly: apparent productivity, X and S. It deliberately avoids inventing metal/support-specific rate laws not reported consistently across the corpus.

## Reactor and flowsheet

The submitted flowsheet hash is `10dd8b9b13c72c4e`. The process is a cooled catalytic methanation loop:

`CO2/H2 compression -> feed/recycle mixing -> feed-effluent heat exchange -> trim preheat -> cooled methanation reactor -> heat recovery -> effluent cooler/water knockout -> methane membrane purification -> product compression -> purge/recycle split -> recycle compression`.

Included units, matching `flowsheet.json` and `model.py`, are:

- CO2 feed compressor
- H2 feed compressor
- Recycle compressor
- Feed mixer
- Feed effluent heat exchanger
- Trim preheater
- Cooled methanation reactor
- Effluent cooler and water knockout
- Methane purification membrane
- Product compressor
- Recycle purge splitter
- Utilities and offsites

Catalyst regeneration is not modelled as a unit because the screened papers mostly provide short stability tests or no regeneration protocol. Deactivation enters as replacement cost only.

## Parameters

All parameters are in `sources.csv`; published or measured entries include URL and location, while conceptual engineering choices are marked as assumptions with low/high bounds. Key base values are:

| parameter | base | low-high | type |
|---|---:|---:|---|
| plant capacity | 100000 t CH4/y | 20000-500000 | assumption |
| operating hours | 8000 h/y | 7000-8400 | assumption |
| capital recovery factor | 0.10 y-1 | 0.07-0.15 | assumption |
| H2 price | 5.0 USD/kg | 2.0-7.0 | published DOE basis |
| CO2 price | 50 USD/t | 0-120 | assumption |
| electricity price | 0.0964 USD/kWh | 0.06-0.18 | published EIA basis |
| natural gas price | 5.0 USD/MMBtu | 3.0-9.0 | published EIA basis |
| compressor efficiency | 0.75 | 0.65-0.85 | assumption |
| minimum loop pressure | 10 bar | 1-30 | assumption |
| CH4 membrane recovery | 0.995 | 0.97-0.999 | assumption |
| recycle purge fraction | 0.02 | 0.005-0.1 | assumption |
| base catalyst life | 3 y | 1-5 | assumption |
| catalyst manufacturing factor | 3x raw materials | 1.5-6 | assumption |

## Checked model

`model.py` passed the independent contract and physics checks on the reference case and all 163 usable records. The model reports unit-level duties and capital, boundary mass flows, reactor heat duty, recycle and separation streams. Compressor work, separation work, equilibrium caps, reaction heat, mass/elements, stoichiometry, monotonicity and determinism passed.

Reference plant: 100 kt/y catalytic CO2 methanation reference plant, reference 20 wt% Ni/Al2O3-like record at 573.15 K, 10 bar, X = 0.80, S = 0.99, r = 1 kg CH4 kgcat-1 h-1.

Reference cost from the model: **2895.6 USD/t CH4**.

| cost part | USD/t CH4 | share |
|---|---:|---:|
| feed | 2672.1 | 92.3% |
| energy | 135.1 | 4.7% |
| capital | 86.0 | 3.0% |
| catalyst replacement | 2.5 | 0.1% |
| other | 0.0 | 0.0% |

Reference balances: capacity 100000 t/y; purchased primary energy 7.50 GJ/t CH4; installed capex 61.4 million USD; CO2 feed 2.785 t/t CH4. The largest absolute cost is H2-rich feedstock, not the reactor.

## Plant choice and ranking changes

Cheapest screened operating point: **Ni14LA** from `10_1016_j_apcatb_2018_12_063`, at 350 °C, model cost **2874.1 USD/t CH4**. Twelve records are below the reference cost.

Ranking agreement between simple lab metrics and plant cost:

| lab ranking metric | level | denominator | changed | fraction changed | notable regrets |
|---|---|---:|---:|---:|---|
| productivity | operating point | 14 groups / 12 papers | 6 | 0.4286 | 2 changes >1%, 1 >5%, 1 >10%; median changed regret 0.43% |
| productivity | catalyst | 13 groups / 11 papers | 3 | 0.2308 | no changes >1%; median changed regret 0.12% |
| conversion | operating point | 14 groups / 12 papers | 5 | 0.3571 | 1 change >1%; median changed regret 0.43% |
| conversion | catalyst | 13 groups / 11 papers | 3 | 0.2308 | 1 change >1%; median changed regret 0.57% |
| selectivity | operating point | 14 groups / 12 papers | 0 | 0.0 | none |
| selectivity | catalyst | 13 groups / 11 papers | 0 | 0.0 | none |

Interpretation: lab productivity and conversion partially predict plant choice but not reliably at the operating-point level. The plant sometimes chooses a different catalyst and sometimes the same catalyst at a different temperature. Selectivity ranking did not change in this data set because most high-performing records already had high CH4 selectivity; however, selectivity still has strong cost leverage when varied around the reference.

## Why the ranking changes

- **Feedstock cost attenuates lab differences.** H2 and CO2 feed are more than 90% of reference cost. Large changes in catalyst activity only affect the small capital/catalyst/recycle portion once the catalyst is active enough.
- **Recycle attenuates conversion.** Lower per-pass conversion increases recycle compression and separation, but the recycle loop lets the plant still reach the same net production. Therefore the highest lab conversion is not always the cheapest point.
- **Equilibrium attenuates high-temperature activity.** A hotter catalyst may show good intrinsic productivity but is capped by methanation equilibrium and pays additional recycle/heat penalties.
- **Separation and purge penalize low selectivity.** CO byproduct must be purged, which raises fresh feed demand and recycle/separation loads.
- **Metal cost is usually secondary.** Even expensive metals have small replacement cost unless the record has low productivity or high PGM loading; activity affects reactor/catalyst inventory more than raw metal price in the fitted corpus.

Attribution from `run_analysis` for record-to-record cost differences: activity 84.7%, selectivity 10.9%, metal 3.6%, temperature 0.5%, stability 0.3%. At the reference, +1 selectivity point changes cost by **-11.16 USD/t**, while doubling activity changes cost by **-3.44 USD/t**. Thus absolute plant economics are feed dominated; among catalyst properties, **activity/productivity controls the ranking spread**, while **selectivity has the largest marginal cost leverage if it is not already near unity**.

## Sensitivity to uncertain parameters

One-at-a-time reference sensitivities computed with the model:

| parameter varied | low setting cost | high setting cost | span |
|---|---:|---:|---:|
| H2 price 2-7 USD/kg | 1375.9 | 3908.8 | 2532.8 |
| CO2 price 0-120 USD/t | 2756.4 | 3090.6 | 334.2 |
| electricity 0.06-0.18 USD/kWh | 2847.6 | 3006.0 | 158.4 |
| offsites fraction 0.15-0.45 | 2888.8 | 2909.4 | 20.6 |
| reactor catalyst-volume capital factor 50-600 USD/kgcat | 2892.4 | 2904.4 | 12.0 |
| catalyst life 1-5 y | 2900.6 | 2894.6 | 6.0 |
| CH4 recovery 0.97-0.999 | 2897.2 | 2895.4 | 1.8 |

Full-ranking sensitivity checks retained the same cheapest record, Ni14LA at 350 °C, under H2 low, H2 high, CO2 high, power high, high-capex and low-catalyst-life scenarios. The absolute cost moved strongly with H2 price, but the conclusion that feedstock dominates and lab rankings only partially transfer was robust in these scenarios.

## What the evidence could not support

- A universal rate law or mechanistic microkinetic model across Ni, Ru, alloy and support families.
- Reliable deactivation economics for most catalysts; stability is represented only when papers report deactivation time.
- Industrial catalyst shaping, pressure drop, sulfur/impurity tolerance and scale-up heat-transfer limits.
- A rigorous membrane design; separation is represented by mass-balanced recovery plus a conservative work floor.
- Market-optimized methane selling price or policy credits. The output is cost per tonne CH4, not profit.
- Exact commercial plant capital. Many equipment coefficients are assumptions with ranges; the conclusions rely on comparative costing rather than a bankable estimate.

## Bottom line

Laboratory activity and conversion are useful screens but do not uniquely predict the plant-selected catalyst and operating condition. In this CO2 methanation data set, 36-43% of operating-point rankings based on productivity or conversion change after plant costing, while catalyst-level changes are smaller at about 23%. The plant chooses Ni14LA at 350 °C in the base model. The absolute cost is dominated by H2/CO2 feed, so many lab differences are economically attenuated. Among catalyst properties, productivity/activity controls most ranking variation because it drives catalyst inventory and reactor capital for weak records; selectivity is economically powerful per percentage point but did not reorder the screened top catalysts because the leading records were already highly selective.
