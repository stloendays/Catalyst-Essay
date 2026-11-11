# Economic ranking of literature catalysts for non-oxidative propane dehydrogenation (PDH)

Reaction: `C3H8 -> C3H6 + H2`.

## Executive answer

A plant would **not simply choose the catalyst/condition with the highest laboratory conversion**, and it would only partly follow laboratory activity or selectivity rankings.  The economic model chose, among the extracted records, **0.2Pt2.4Zn-SPP** from DOI `10.1021/acscatal.2c01631` at 550 °C, with modeled cost **685.15 USD/t propylene** and optimized plant per-pass conversion **0.339**.  The next two records were **Gaδ+ Pt0/SiO2** from DOI `10.1021/jacs.8b05378` at **691.31 USD/t** and **Pt0Znd+/SiO2** from DOI `10.1039/c9sc05599a` at **695.95 USD/t**.

The reference 750 kt/y Pt-Sn/Al2O3 PDH plant costs **736.77 USD/t** in this model.  Its largest term is feed propane, not catalyst: feed **454.06**, energy **23.75**, capital **191.03**, catalyst **4.25**, fixed/other **63.68 USD/t**.

The economic ranking changes mainly because the plant optimizes per-pass conversion against recycle/separation and equilibrium limits, and because propane feed loss from imperfect selectivity is expensive.  Activity matters strongly only when a catalyst is slow enough to expand the reactor/capital term; once activity is high, extra laboratory rate is attenuated by separation/recycle/capital dilution and selectivity/feed cost becomes the more important discriminator.

## Search, screening and exclusions

### Inclusion criteria

Included papers had to be primary experimental heterogeneous catalysis studies of **direct, non-oxidative PDH** with enough information to extract catalyst identity/composition, temperature, pressure or ambient pressure, feed composition or space velocity, propane conversion, propylene selectivity, and rate/productivity or data from which productivity could be computed.  Stability/time-on-stream was extracted when available but was not mandatory.

### Exclusion criteria

Excluded: oxidative or CO2/N2O/O2/soft-oxidant dehydrogenation, reviews, computational-only or reactive-force-field papers, process-simulation-only papers, plasma/electrified cases not comparable to thermal PDH, regeneration-only papers without fresh catalyst performance, and records missing conversion/selectivity/activity.

### Download/OCR/extraction outcome

- DOI download attempts: **20**.
- Parsed PDFs: **18**.
- Extracted papers: **18**.
- Papers with at least one usable record: **15**.
- Usable operating-point records: **68**.
- Automatically rejected extracted records included **12** records with implausibly printed rate above 50 kg product kg-cat^-1 h^-1, treated as likely unit/OCR errors.

### Papers included in the cost set

| DOI/file key | Catalyst family | Usable records | Main role in results |
|---|---:|---:|---|
| `10_1021_acscatal_2c01631` | PtZn self-pillared zeolite | 1 | Cheapest plant record |
| `10_1021_jacs_8b05378` | Ga-Pt/SiO2 | 4 | Second-best plant record; high activity/selectivity |
| `10_1039_c9sc05599a` | Pt-Zn/SiO2 | 4 | Third-best plant record |
| `10_1038_s41929_026_01488_w` | CoOx/silicalite-1 plus benchmarks | 3 | High-r, high-S low-T case |
| `10_1039_c6sc05178b` | isolated Ga/SiO2 | 1 | High-r, moderate-S |
| `10_1039_d2sc03723h` | PtCu single-atom alloy | 4 | Activity/selectivity tradeoff example |
| `10_1039_c7ra02141k` | Pt-Sn-K/theta-Al2O3 | 4 | Industrial-like Pt-Sn family |
| `10_1038_s41586_021_03923_3` | ZnOx/silicalite-1 | 2 | High conversion but lower selectivity |
| `10_1021_acs_iecr_4c02577` | Pt and Pt-Sn/Al2O3 | 6 | Low-temperature Pt/Sn comparison |
| `10_1039_c6ra27204e` | supported Ga2O3 | 13 | Conversion ranking changes strongly |
| `10_1039_d3cy01446k` | Ga sites from clusters | 1 | Lower-selectivity Ga case |
| `10_1039_d1sc05866e` | In-CHA | 1 | Low activity/selectivity penalty |
| `10_55730_1300_0527_3648` | PtB/SiO2 | 2 | Low activity penalty |
| `10_1021_acscatal_6b01286` | Fe/P/Al2O3 | 7 | Shows activity/selectivity/rate conflicts |
| `10_4236_oalib_1112358` | Fe/ZSM-5 | 15 | Low selectivity; high feed penalty |

### Screened/downloaded but not used in cost ranking

- `10.1016/j.fmre.2022.08.020` and `10.1016/j.fmre.2022.04.012`: screened in but download failed through the automated route.
- `10_1039_d1sc05381g`: extracted but no usable records after checks; main missing field was conversion.
- `10_1039_d5lf00031a`: extracted but no usable records; main missing field was rate or flow plus catalyst mass.
- `10_2533_chimia_2025_208`: extracted but no usable records; main missing field was temperature.
- Oxidative/CO2-assisted/review/computational examples excluded at screening included `10.1021/acscatal.0c03999`, `10.1039/d4cy01242a`, `10.1021/acscatal.4c02628`, `10.1002/cjce.25481`, `10.1007/s12209-020-00267-3`, `10.1021/acs.jpcc.3c07126`, and `10.3390/catal11091070`.

## Mechanism and kinetic transfer from lab to plant

I did not fit a universal elementary microkinetic model across Pt, Ga, Zn, Co, Fe, In and zeolite catalysts; the literature set is too heterogeneous and the extracted records are mostly integral fixed-bed performance points.  Instead, each record is transferred as an **apparent catalyst capacity** using its reported productivity.

For a candidate record, the model treats the reported productivity `r` as the productivity at the reported temperature, pressure, feed dilution and conversion.  The plant productivity at a selected per-pass conversion `x` is scaled by a first-order approach-to-equilibrium shape:

`tau(x) = -ln(1 - x / x_eq)`

and

`r_eff(x) = r_lab * [x/tau(x)] / [X_lab/tau(X_lab)]`.

The equilibrium conversion is computed for `C3H8 -> C3H6 + H2` using `Kp = y_C3H6*y_H2/y_C3H8 * P` and a van't Hoff form centered at 600 °C.  Lab feed dilution is used when normalizing the lab point; the plant reactor feed is treated as propane-rich after separation/recycle.  This makes high diluted-feed lab conversions less directly valuable to a plant, because the plant still faces equilibrium and recycle economics.

Deactivation is represented only as a cycle/inventory penalty when a time to 10% activity loss was extractable.  It is deliberately weak because short laboratory time-on-stream is not the same as industrial replacement life; regeneration and swing inventory are included, but coke chemistry is not modeled.

## Reactor and flowsheet choices

The plant model represents a large thermal PDH unit as:

1. endothermic fixed/moving-bed catalytic reactor section,
2. optimized per-pass conversion below thermodynamic equilibrium,
3. propane recycle,
4. propylene/propane separation and recycle compression/refrigeration,
5. fired heat supply for reaction and sensible heat,
6. capital scaling for the reactor/separation/recycle system,
7. catalyst inventory, regeneration swing and replacement.

The free operating variable optimized for every record is **per-pass conversion**.  Temperature and pressure are taken from the literature record, clipped to plant-reasonable bounds, because the data do not support extrapolating every catalyst to arbitrary temperature.  The model optimizes conversion rather than accepting the lab conversion because industrial cost depends on a tradeoff: low conversion increases recycle/separation, high conversion approaches equilibrium and lowers effective catalyst productivity.

Not represented explicitly: detailed propylene-propane splitter tray count, pressure profiles, hydrogen purification, byproduct slate beyond selectivity loss, coke burn heat integration, catalyst attrition, startup/turnaround, site-specific hydrogen credit, taxes, working capital, and environmental compliance.  These are outside the supportable information in the catalyst papers.

## Parameter ledger

The full machine-readable parameter ledger is `sources.csv`.  Assumptions have low/high ranges; measured or published entries give a URL/DOI and location.  Main parameters are:

| Parameter | Base value | Unit | Type | Low | High | Source/location summary |
|---|---:|---|---|---:|---:|---|
| reference_capacity | 750000 | t/y | published |  |  | Enterprise Products PDH2 startup release: 1,650,000 lb/day propylene |
| propane_price | 0.750 | USD/gal | published |  |  | EIA Mont Belvieu annual propane spot series, 2025 value |
| propane_density | 4.24 | lb/gal | published |  |  | EIA propane explained conversion |
| natural_gas_price | 3.5 | USD/MMBtu | published |  |  | EIA Henry Hub annual spot series, rounded |
| industrial_electricity_price | 0.096 | USD/kWh | published |  |  | EIA Electric Power Monthly Table 5.6.A, rounded |
| reaction_enthalpy | 124.3 | kJ/mol | published |  |  | NIST WebBook enthalpy-of-formation combination |
| plant_capex_reference | 1.20e9 | USD | assumption | 0.80e9 | 1.80e9 | Installed 750 kt/y PDH plant order-of-magnitude |
| capital_recovery_factor | 0.12 | 1/y | assumption | 0.08 | 0.18 | Annualized capital charge |
| fixed_OM_fraction | 0.04 | 1/y | assumption | 0.02 | 0.06 | Fixed O&M fraction of installed capital |
| furnace_efficiency | 0.85 | fraction | assumption | 0.75 | 0.90 | Fired heater efficiency |
| heat_recovery_fraction | 0.75 | fraction | assumption | 0.60 | 0.85 | Feed-effluent heat recovery |
| separation_base_power | 60 | kWh/t | assumption | 35 | 100 | Base compression/refrigeration/splitter power |
| recycle_power_coeff | 12 | kWh/t per `(1/X-1)` | assumption | 5 | 25 | Incremental recycle power |
| support_catalyst_cost | 20 | USD/kg | assumption | 5 | 80 | Prepared support/fabrication excluding metals |
| catalyst_life | 3 | y | assumption | 1 | 5 | Nominal make-up life |

## Model contract checks

`check_model` passed on the reference plant and **68** usable literature records.  The checks verified finite positive cost, part sums, conversion in `(0,1]`, feed above stoichiometric minimum, monotonic non-increase of cost with selectivity and activity, and deterministic behavior.

## Reference plant economics

Reference plant: **750 kt/y PDH reference plant (Enterprise PDH2-scale, Pt-Sn/Al2O3 catalyst)**.

| Cost part | USD/t C3H6 |
|---|---:|
| Feed propane | 454.06 |
| Energy | 23.75 |
| Capital charge | 191.03 |
| Catalyst | 4.25 |
| Fixed/other O&M | 63.68 |
| **Total** | **736.77** |

Reference optimized operating point:

- Temperature: **873.15 K**.
- Pressure: **1.5 bar**.
- Optimized per-pass conversion: **0.410**.
- Largest cost term: **feed**.

## Best literature records by plant cost

| Rank | DOI/file key | Catalyst | T (K) | Lab X | Lab S | Lab r (kg/kg/h) | Plant cost (USD/t) | Optimized pass X |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `10_1021_acscatal_2c01631` | 0.2Pt2.4Zn-SPP | 823.00 | 0.245 | 0.990 | 12.65 | 685.15 | 0.339 |
| 2 | `10_1021_jacs_8b05378` | Gaδ+ Pt0/SiO2 | 823.15 | 0.319 | 0.990 | 31.50 | 691.31 | 0.325 |
| 3 | `10_1039_c9sc05599a` | Pt0Znd+/SiO2 | 823.15 | 0.302 | 0.981 | 21.44 | 695.95 | 0.326 |
| 4 | `10_1038_s41929_026_01488_w` | 1.1Co-S-1 | 773.15 | 0.660 | 0.970 | 14.42 | 706.16 | 0.200 |
| 5 | `10_1039_c6sc05178b` | isolated Ga/SiO2 | 823.15 | 0.093 | 0.943 | 13.13 | 707.85 | 0.339 |
| 6 | `10_1039_d2sc03723h` | 0.1Pt7Cu/SiO2-IM-680R | 853.15 | 0.400 | 0.920 | 5.18 | 714.81 | 0.436 |
| 7 | `10_1039_c7ra02141k` | Cat-D Pt-Sn-K/theta-Al2O3 | 873.15 | 0.389 | 0.935 | 1.39 | 727.20 | 0.434 |
| 8 | `10_1038_s41586_021_03923_3` | ZnO-S-1_3 physical mixture | 873.15 | 0.400 | 0.880 | 5.27 | 732.79 | 0.477 |

Thirteen literature records were below the reference cost.

## Does laboratory ranking predict the plant choice?

Mostly no for conversion, partly for activity and selectivity.

`run_analysis` compared the record selected by a lab metric within each multi-record paper/group against the record selected by plant cost.

| Lab ranking metric | Point-level changed / denominator | Fraction | Catalyst-level changed / denominator | Fraction | Median regret when changed |
|---|---:|---:|---:|---:|---:|
| Productivity/activity `r` | 4 / 11 | 0.364 | 3 / 10 | 0.300 | 14.35% point-level; 27.42% catalyst-level |
| Conversion `X` | 8 / 11 | 0.727 | 5 / 10 | 0.500 | 10.62% point-level; 18.64% catalyst-level |
| Selectivity `S` | 4 / 11 | 0.364 | 3 / 10 | 0.300 | 8.50% point-level; 16.06% catalyst-level |

### Examples of ranking changes

- **Conversion fails most often.**  In `10_1039_c6ra27204e`, the highest-conversion Ga2O3/ZSM-5 record (`X = 0.781`) costs **1033.7 USD/t**, whereas the plant chooses 5Ga2O3/Al2O3 (`X = 0.460`) at **811.2 USD/t**.  The high conversion is not free: it comes with poorer economic balance after selectivity, approach-to-equilibrium productivity and capital/recycle effects.
- **High lab conversion can be near-equilibrium/dilution-specific.**  In `10_1021_jacs_8b05378`, the highest-conversion Ga-Pt point (`X = 0.407`) costs **1210.3 USD/t**, but the plant chooses another Ga-Pt point at `X = 0.319` costing **691.3 USD/t**.
- **Activity helps but is attenuated once high enough.**  The top three catalysts all have high `r`, but the fastest of them is not the cheapest because catalyst/reaction rate affects only the reactor/capital/catalyst fraction, not the full feed bill.
- **Selectivity usually helps, but selectivity alone is not enough.**  In the Fe/P/Al2O3 set, records with higher apparent selectivity can still be uneconomic if the extracted rate is too low or if other costs inflate capital.

## Which catalyst property controls cost?

The answer depends on the part of catalyst space:

1. **Across all extracted literature records, activity and selectivity both matter.**  The one-at-a-time attribution over the full usable set assigned **54.1%** of explainable variation to activity and **43.4%** to selectivity; temperature, stability and metal price together were below 3%.
2. **Near an industrially viable catalyst, feed/selectivity is the sharper marginal lever.**  At the reference plant, +1 absolute percentage point selectivity changes cost by **-5.17 USD/t**, while doubling activity changes cost by **-10.73 USD/t**.  In other words, once a catalyst is already active enough, two selectivity points are comparable to a factor-of-two activity gain.
3. **Very low activity is a gatekeeper.**  Slow catalysts require large reactor/catalyst inventory and increase the capital term.  This is why activity dominates some global comparisons.
4. **Metal price is attenuated.**  Catalyst cost is only **4.25 USD/t** in the reference and remains a small term for low-loading Pt/Zn/Ga/Pt-Sn cases.  Precious metal price changes would matter more only for high loading, short life or very low productivity.

## How plant physics attenuates lab metrics

- **Feedstock cost attenuates activity gains.**  No amount of rate improvement reduces the stoichiometric propane required for propylene; feed is the largest cost part.
- **Equilibrium attenuates high conversion.**  Lab conversions under diluted feeds do not transfer directly to propane-rich plant feed.
- **Recycle/separation attenuate low-conversion operation.**  A plant can avoid equilibrium by lowering per-pass conversion, but recycle and splitter duty rise.
- **Capital attenuates rate improvements.**  Reactor productivity affects only part of the installed cost, while separations/heaters/offsites remain.
- **Operation/regeneration attenuates stability claims.**  Lab time-on-stream is not equivalent to full industrial catalyst life; the model only applies a swing inventory penalty.
- **Equipment heat integration attenuates temperature effects.**  Hotter operation changes sensible heat and materials factors, but reaction heat and feed/capital dominate.

## Sensitivity to uncertain parameters

The following one-at-a-time scenario calculations were run by re-costing all usable records with `model.py`.

| Scenario | Winner | Winner cost | Runner-up cost | Reference cost | Conclusion |
|---|---|---:|---:|---:|---|
| Base | 0.2Pt2.4Zn-SPP | 685.15 | 691.31 | 736.77 | PtZn-SPP wins |
| Propane 0.50 USD/gal | 0.2Pt2.4Zn-SPP | 547.56 | 553.71 | 585.41 | Winner unchanged |
| Propane 1.20 USD/gal | 0.2Pt2.4Zn-SPP | 932.82 | 938.97 | 1009.20 | Winner unchanged; feed dominates more |
| Low capex/CRF | 0.2Pt2.4Zn-SPP | 561.03 | 569.87 | 609.41 | Winner unchanged |
| High capex/CRF | Gaδ+ Pt0/SiO2 | 948.55 | 948.91 | 1007.39 | Activity/capital makes Ga-Pt tie/slightly win |
| Cheap energy | 0.2Pt2.4Zn-SPP | 675.29 | 681.29 | 726.70 | Winner unchanged |
| Expensive energy | 0.2Pt2.4Zn-SPP | 713.57 | 719.95 | 766.19 | Winner unchanged |
| Weak heat recovery | 0.2Pt2.4Zn-SPP | 689.57 | 695.83 | 741.32 | Winner unchanged |
| Strong heat recovery | 0.2Pt2.4Zn-SPP | 682.97 | 689.06 | 734.52 | Winner unchanged |
| Cheap catalyst/long life | 0.2Pt2.4Zn-SPP | 684.69 | 686.00 | 734.77 | Top gap narrows |
| Expensive catalyst/short life | 0.2Pt2.4Zn-SPP | 688.69 | 707.04 | 749.56 | Winner unchanged |
| Low equilibrium K | 0.2Pt2.4Zn-SPP | 695.95 | 701.68 | 738.04 | Winner unchanged |
| High equilibrium K | 0.2Pt2.4Zn-SPP | 676.35 | 682.07 | 733.14 | Winner unchanged |

Sensitivity conclusion: the exact identity of the best catalyst is robust except under very high capital charge, where the high-activity Ga-Pt record becomes essentially tied with PtZn-SPP.  The broader conclusion is robust: the plant prefers **high-selectivity, high-activity catalysts at operating points that do not chase maximum lab conversion**.

## What the evidence could not support

- A single intrinsic kinetic mechanism across all catalyst families.
- Reliable extrapolation of each catalyst to arbitrary temperature/pressure.
- Industrial deactivation/regeneration schedules from short lab time-on-stream.
- Detailed byproduct economics because many papers report only propylene selectivity, not complete carbon distribution.
- Site-specific hydrogen credit or integration with downstream polypropylene.
- Definitive capex; public PDH announcements rarely isolate installed PDH unit cost from offsites and project scope.
- Error bars from OCR/figure digitization beyond the automated plausibility gates.

## Files produced

- `records.csv`: extracted and normalized catalyst-performance records.
- `sources.csv`: parameter ledger with sources and assumption ranges.
- `model.py`: plant-cost model implementing the contract.
- `costs.csv`: costed usable records.
- `analysis.json`: ranking/attribution metrics.
- `sensitivity.csv` and `sensitivity.json`: scenario calculations.
