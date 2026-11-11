# Industrial interpretation of literature catalysts for non-oxidative propane dehydrogenation (PDH)

Reaction: `C3H8 -> C3H6 + H2`.

This run built a shortcut industrial plant model from open literature data and used it to cost every usable catalyst-performance record extracted from the screened PDH papers.  The model file is `model.py`; extracted normalized records are in `records.csv`; costs are in `costs.csv`; ranking/statistical output is in `analysis.json`; parameter sources are in `sources.csv`.

## 1. Literature search, screening and exclusions

Searches targeted primary experimental papers on non-oxidative propane dehydrogenation that reported catalyst identity plus conversion, selectivity and enough rate/space-velocity/feed-flow information to estimate productivity.  The screen excluded reviews, oxidative dehydrogenation with O2/soft oxidants, CO2-assisted oxidative dehydrogenation, chemical looping, theoretical-only papers and papers without usable full text/performance data.

### Included and extracted papers

| DOI | paper theme | extracted records | usable records | main reason unusable records were dropped |
|---|---:|---:|---:|---|
| 10.1021/acscatal.0c01580 | Zn/ZrOx and doped ZrOx PDH | 40 | 12 | missing selectivity in many rate-only records |
| 10.1021/acscatal.1c05778 | Mg-stabilized ZnO/S-1 | 18 | 1 | missing selectivity in most durability/rate records |
| 10.1021/acscatal.2c01631 | PtZn sites in self-pillared zeolite | 8 | 8 | none |
| 10.1021/acscatal.6b01286 | Fe/P/Al2O3 | 14 | 11 | missing selectivity in some entries |
| 10.1021/acscatal.9b02459 | Ga-Rh SCALMS | 5 | 4 | one lacked rate or flow+mass |
| 10.1021/jacs.2c05618 | Pt-Mn/SiO2 | 8 | 6 | two lacked rate or flow+mass |
| 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 14 | 11 | missing selectivity in some entries |
| 10.1038/s41467-025-61182-6 | Pt/Sn-MFI defect-site catalyst | 9 | 9 | none |
| 10.1038/s41586-021-03923-3 | ZnOx/S-1 | 12 | 2 | missing conversion in most entries |
| 10.1039/c6ra27204e | Ga2O3 supported catalysts | 13 | 13 | none |
| 10.1039/c6sc05178b | isolated Ga sites on silica | 1 | 1 | none |
| 10.1039/c9sc05599a | subnanometric Pt-Zn/SiO2 | 4 | 4 | none |
| 10.1039/d1sc05866e | extra-framework In in chabazite | 9 | 0 | missing selectivity |

Total: 13 PDFs parsed, 155 records extracted, 82 usable records from 12 papers.  `10.1016/j.fmre.2022.08.020` was initially screened in but excluded after download failure because no usable full text was available to the automated run.  Explicitly excluded screened candidates included ODH/soft-oxidant reviews and studies, CO2-assisted ODH, chemical-looping ODH, and a probability-analysis paper without the needed experimental plant-cost inputs.

## 2. Mechanism and kinetic transfer from lab to plant

The model treats PDH as reversible, endothermic dehydrogenation limited by equilibrium:

`C3H8 <=> C3H6 + H2`.

The extracted laboratory productivity `r` is used as an apparent catalyst productivity at the reported lab temperature, pressure and composition.  To avoid pretending that a single literature point identifies a full rate law, `r` is transferred through an approach-to-equilibrium correction rather than a fitted elementary kinetic model.  For a proposed plant per-pass conversion `x`, productivity is scaled by the ratio of mean driving force at plant `x` to mean driving force at the lab conversion.  Equilibrium is represented by a van't Hoff form anchored at `Kp(873 K)=0.35 bar`, and the plant is not allowed to choose a per-pass conversion above 92% of calculated equilibrium.

Catalyst deactivation is represented only economically.  Extracted `t_cycle_h` means hours to lose about 10% activity; short values increase regeneration/replacement cost.  If no stability is reported, the model uses the default replacement-life assumption in `sources.csv`.  Very long apparent `t_cycle_h` values are capped in the model because some stability figures show activation or noisy initial/final conversions rather than true indefinite life.

## 3. Reactor and flowsheet represented

The industrial plant is a 600 kt/y propylene PDH unit.  The shortcut flowsheet includes:

- low-pressure, high-temperature catalytic PDH reactor;
- equilibrium cap on per-pass conversion;
- recycle of unconverted propane;
- propane/propylene recovery and recycle compression as a conversion-dependent electricity term;
- fired heat supply for the endothermic reaction and feed heating, with heat recovery;
- annualized installed capital based on a public Gulf-Coast PDH project analogue;
- extra capital for large recycle and bulky catalyst inventory;
- catalyst inventory, replacement and regeneration cost;
- fixed other cost for labor/maintenance/overhead not otherwise captured.

The plant optimizes per-pass conversion for each catalyst record.  It does not optimize catalyst formulation, detailed reactor temperature profile, multi-bed heat addition, detailed coke combustion/regeneration chemistry, tray-by-tray separation, hydrogen purification, or propylene product price.  Product price is intentionally omitted because the ranking question is minimum production cost per tonne of propylene, not margin.

## 4. Plant parameters

The full parameter ledger is `sources.csv`.  Values marked as assumptions have low/high bounds.  Published/measured values include a URL or DOI and a location description.

| parameter | value | unit | type | low | high |
|---|---:|---|---|---:|---:|
| reference_capacity | 600000 | t C3H6/y | assumption | 450000 | 750000 |
| stream_factor | 8000 | h/y | assumption | 7600 | 8400 |
| base_installed_capex | 900000000 | USD | published | 700000000 | 1200000000 |
| capex_reference_capacity | 750000 | t C3H6/y | published | 600000 | 900000 |
| capital_charge_factor | 0.117 | 1/y | assumption | 0.085 | 0.16 |
| propane_price | 520 | USD/t | published | 350 | 800 |
| liquid_propane_density | 4.24 | lb/gal | published | 4.1 | 4.4 |
| natural_gas_price | 3.8 | USD/MMBtu | published | 2.5 | 7.0 |
| electricity_price | 0.08 | USD/kWh | published | 0.05 | 0.12 |
| reaction_enthalpy | 125.0 | kJ/mol C3H8 | published | 120 | 130 |
| equilibrium_Kp_873K | 0.35 | bar | assumption | 0.2 | 0.6 |
| furnace_efficiency | 0.85 | fraction | assumption | 0.75 | 0.92 |
| heat_recovery | 0.65 | fraction | assumption | 0.45 | 0.8 |
| separation_electricity_base | 0.25 | GJ/t C3H6 | assumption | 0.12 | 0.6 |
| recycle_electricity_coeff | 0.15 | GJ/t C3H6 | assumption | 0.05 | 0.35 |
| fixed_other_cost | 45 | USD/t C3H6 | assumption | 25 | 90 |
| support_catalyst_price | 25 | USD/kg catalyst | assumption | 8 | 80 |
| Pt, Rh, Ga, Zn, In, Sn, Cr prices | see `sources.csv` | USD/kg | measured/published | see file | see file |
| regeneration_cost_fraction | 0.005 | fraction/cycle | assumption | 0.001 | 0.02 |
| replacement_life_default | 16000 | h | assumption | 8000 | 32000 |

## 5. Reference plant cost

`check_model` passed all contract checks on the reference plant and all 82 usable records: finite positive costs, parts summing to total, valid per-pass conversion, stoichiometric feed, monotonic selectivity/activity behavior, and deterministic output.

Reference plant: 600 kt/y Gulf Coast PDH reference, commercial Pt-Sn/Al2O3 analogue.

| part | USD/t propylene |
|---|---:|
| feed | 598.80 |
| energy | 27.60 |
| capital | 158.42 |
| catalyst | 11.29 |
| other | 65.31 |
| **total** | **861.43** |

Reference optimized operating point: 873.15 K, 1.5 bar, per-pass conversion 0.450.  The largest cost component is propane feed.  This is important: once selectivity is high, feed cost becomes nearly stoichiometric and additional laboratory conversion or activity can only affect the smaller capital, energy and catalyst terms.

## 6. Plant-selected literature catalysts

The lowest-cost record was:

| rank | DOI/paper | catalyst | T | lab X | lab S | lab r (kg C3H6/kg cat/h) | plant cost USD/t | optimized per-pass X |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 823 K | 0.20 | 0.998 | 29.46 | 787.03 | 0.798 |
| 2 | 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 823 K | 0.20 | 0.998 | 25.92 | 787.39 | 0.798 |
| 3 | 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 823 K | 0.20 | 0.998 | 20.66 | 788.16 | 0.798 |
| 4 | 10.1021/acscatal.2c01631 | 0.4Pt2.4Zn-SPP | 823 K | 0.240 | 0.990 | 26.76 | 793.76 | 0.525 |
| 5 | 10.1021/acscatal.2c01631 | 0.2Pt2.4Zn-SPP | 823 K | 0.245 | 0.990 | 12.65 | 795.76 | 0.525 |

Best record by paper/family:

| DOI/paper | best catalyst | cost USD/t | S | r |
|---|---|---:|---:|---:|
| 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 787.03 | 0.998 | 29.46 |
| 10.1021/acscatal.2c01631 | 0.4Pt2.4Zn-SPP | 793.76 | 0.990 | 26.76 |
| 10.1038/s41467-025-61182-6 | Pt@Sn-MFI | 798.41 | 0.991 | 3.30 |
| 10.1021/jacs.2c05618 | Pt(0.05)Mn/SiO2 | 813.19 | 0.973 | 2.35 |
| 10.1039/c6sc05178b | isolated Ga/silica | 824.65 | 0.943 | 13.13 |
| 10.1021/acscatal.0c01580 | 4Zn/TiZrOx | 826.65 | 0.950 | 1.25 |
| 10.1021/acscatal.1c05778 | 6ZnO/S-1(1.0Mg) | 862.94 | 0.920 | 0.321 |
| 10.1038/s41586-021-03923-3 | ZnO-S-1_3 | 863.74 | 0.880 | 5.27 |
| 10.1039/c9sc05599a | Pt0Znd+/SiO2 | 874.17 | 0.981 | 21.44 |
| 10.1039/c6ra27204e | 5Ga2O3/SBA-15 | 971.91 | 0.900 | 0.232 |
| 10.1021/acscatal.6b01286 | (3Fe:P)/Al2O3 | 1017.12 | 0.824 | 0.0398 |
| 10.1021/acscatal.9b02459 | Rh/Al2O3 | 1983.69 | 0.780 | 0.0285 |

Overall, 24 of 82 usable records beat the reference cost from the commercial Pt-Sn analogue.

## 7. Does laboratory ranking predict plant choice?

Only partly.  `run_analysis` compared within-paper lab rankings to plant-cost rankings.

| lab metric used for ranking | comparison level | groups | changed groups | fraction changed | 95% bootstrap CI | changed groups with >5% regret | median regret among changed |
|---|---|---:|---:|---:|---|---:|---:|
| productivity | operating-point | 10 | 5 | 0.500 | 0.200-0.800 | 3 | 0.0529 |
| productivity | catalyst | 9 | 5 | 0.556 | 0.222-0.889 | 3 | 0.0529 |
| conversion | operating-point | 10 | 8 | 0.800 | 0.500-1.000 | 5 | 0.0663 |
| conversion | catalyst | 9 | 6 | 0.667 | 0.333-1.000 | 4 | 0.2134 |
| selectivity | operating-point | 10 | 4 | 0.400 | 0.100-0.700 | 2 | 0.1380 |
| selectivity | catalyst | 9 | 3 | 0.333 | 0.000-0.667 | 2 | 0.2576 |

Interpretation:

- Conversion is the weakest standalone predictor.  A high lab conversion may just mean high residence time or operation near equilibrium; in the plant, per-pass conversion is re-optimized against recycle, separation and catalyst inventory.
- Productivity is more useful, but not decisive.  Activity lowers catalyst inventory and reactor-related capital, but these terms are smaller than propane feed once selectivity is high.
- Selectivity has the most direct thermodynamic/economic meaning because it sets fresh propane consumption.  However, among modern high-selectivity catalysts (roughly 0.97-0.998), the feed benefit saturates; then activity and stability decide the smaller differences.
- The plant chooses the high-selectivity, high-productivity Pt/In-ZSM-5 and PtZn/PtSn zeolite-family records, not necessarily the records with the largest reported conversion.

## 8. Controlling catalyst property and attenuation mechanisms

The one-at-a-time attribution from `run_analysis` assigns cost-change share as:

| property/effect | attribution share |
|---|---:|
| stability | 0.405 |
| activity | 0.346 |
| selectivity | 0.209 |
| metal price | 0.033 |
| temperature | 0.008 |

At the reference point, +1 percentage point selectivity changes cost by `-6.57 USD/t`, while doubling activity changes cost by `-8.31 USD/t`.

The apparent controlling property is therefore not a single laboratory headline metric.  For low-selectivity catalysts, selectivity dominates because propane feed loss is the largest absolute cost.  Among high-selectivity catalysts, stability and activity dominate the remaining differences because they reduce catalyst replacement/regeneration, reactor inventory and capital.  Metal cost is attenuated because precious-metal loadings are small and catalyst cost is a small cost part unless reported stability is very poor.  Temperature effects are attenuated because equilibrium, heat recovery and the dominance of feed cost make moderate temperature differences less important than selectivity/activity/stability.

Attenuation by plant features:

- **Feedstock cost:** makes selectivity important, but also masks activity differences because feed is a large common near-stoichiometric term for all selective catalysts.
- **Equilibrium:** limits useful per-pass conversion; a high lab conversion cannot always be converted into high plant value.
- **Recycle/separation:** penalizes very low per-pass conversion, but the plant can optimize conversion rather than accept the lab value.
- **Equipment/capital:** activity matters through reactor/catalyst inventory, but capital is smaller than feed.
- **Operation/regeneration:** poor stability can dominate a record even with good initial conversion/selectivity; stable or unreported-stability records are not heavily penalized under the default assumption.

## 9. Sensitivity to uncertain parameters

A one-at-a-time sweep over low/high values in `sources.csv` was run for propane price, capex, capital charge factor, regeneration cost, support catalyst price, electricity price and equilibrium constant.  In every tested case, the winner remained Pt/In-ZSM-5 from `10.1038/s41467-024-50709-y`.  The absolute cost moved mainly with propane price and capital assumptions; the count of records below the reference varied modestly, about 24-30 records depending on the case.  Regeneration-cost and support-price sweeps mainly affected unstable/low-activity records and did not change the leading high-selectivity/high-activity family.  Equilibrium-constant and electricity sweeps had small effects on the top ranking because the chosen records already combine high selectivity with enough productivity for the plant to find a good conversion/recycle compromise.

This conclusion is less robust for second-tier records: several PtZn, PtSn-MFI, PtMn, Ga and Zn/TiZrOx records lie within about 40 USD/t of one another, so detailed commercial catalyst durability, forming strength, regeneration yield, heat-transfer design and separation design could reorder them.

## 10. What the evidence could not support

- Literature papers do not report a consistent intrinsic rate law; therefore the model uses productivity plus approach-to-equilibrium scaling rather than fitting adsorption/reaction constants.
- Many papers omit selectivity, catalyst mass, full carbon balance or long stability data; 73 of 155 extracted records were unusable for plant costing.
- Extracted stability values are heterogeneous: some are single-cycle decline, some multi-cycle, some inferred from plots, and some records report activation rather than decay.  The economic deactivation treatment is therefore approximate.
- Public PDH capex and utility prices are project- and time-specific; the model uses a public analogue and sensitivity bounds, not a proprietary process design estimate.
- The model does not value hydrogen coproduct, purge losses, product-price margin, detailed propylene/propane splitter capital, catalyst shaping pressure drop, commercial regeneration constraints, environmental permitting or licensing fees.
- The report should therefore be read as a ranking/attenuation analysis rather than a bankable PDH design.

## 11. Bottom-line answers

1. **Does lab ranking predict plant choice?**  Not reliably.  Within-paper ranking changes occur for 50% of productivity comparisons, 80% of conversion comparisons and 40% of selectivity comparisons at operating-point level.
2. **Where does ranking change?**  It changes when high lab conversion is obtained at low selectivity, low productivity or poor stability; it also changes when a plant can choose a different per-pass conversion than the lab test.
3. **Why?**  The plant minimizes total cost, not conversion.  Feed dominates, equilibrium limits conversion, recycle/separation attenuate conversion, and capital/catalyst costs translate activity/stability into smaller but still decisive cost terms.
4. **Which property controls plant cost?**  Selectivity controls the large feed-loss penalty at low selectivity; among high-selectivity catalysts, stability and activity control the ranking.  In this dataset the modeled attribution shares are stability 0.405, activity 0.346, selectivity 0.209, metal 0.033 and temperature 0.008.
5. **Which catalyst would the modeled plant choose?**  Pt/In-ZSM-5 from `10.1038/s41467-024-50709-y`, with modeled cost about `787 USD/t propylene`, followed closely by PtZn self-pillared zeolite and Pt/Sn-MFI records.
