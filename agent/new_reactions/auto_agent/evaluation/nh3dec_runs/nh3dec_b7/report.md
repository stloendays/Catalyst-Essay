# Industrial ammonia decomposition to hydrogen: catalyst-to-plant economic model

## Executive answer

The laboratory ranking is **not a reliable operating-point ranking for the plant**, although it is more informative at the catalyst-family level. Across 487 usable records from 12 papers (13 within-paper comparison groups), the plant-optimal point differed from the maximum laboratory productivity point in 11/13 groups (84.62%; paper bootstrap 95% interval 66.67–100%). At catalyst level the disagreement fell to 4/13 groups (30.77%; 95% interval 7.14–58.33%). Conversion ranking changed in 9/13 point-level groups and 4/13 catalyst-level groups. Selectivity did not rank catalysts because all in-scope thermal NH3 decomposition records were assigned the stoichiometric H2 selectivity of one; no credible coproduct pathway was reported.

The cheapest measured operating point is **8_Co@Al2O3_550 at 500 °C**, paper `10.1002/cctc.202200688`, record 29: **$3,760.54 per t H2**, 63% demonstrated and plant per-pass conversion, and 559.31 kg H2 kg-cat^-1 h^-1 extracted productivity. The highest-productivity laboratory point is the same named catalyst at 600 °C, 3,444.64 kg H2 kg-cat^-1 h^-1, but costs **$3,775.78/t H2**. Once activity is high enough that reactor/catalyst charges are small, extra temperature and conversion no longer compensate for higher heating duty.

The controlling *differentiating catalyst property* is **activity/productivity**: 90.4% of the modeled catalyst-property attribution, versus 8.9% metal cost, 0.6% temperature, 0.1% stability and 0% selectivity. Doubling reference activity reduces cost by only **$18.95/t H2**, showing strong attenuation. The dominant absolute cost is ammonia feed, not catalyst: reference cost is **$3,830.60/t H2**, including feed $2,959.39, energy $653.60, capital $137.48, catalyst $21.87 and other/fixed O&M $58.25 per tonne.

## Literature search, screening and extraction

OpenAlex searching used thermal ammonia decomposition, Ru, Ni, Co, Fe, imide/nitride, high-entropy-alloy, kinetics and hydrogen-production terms. Explicit inclusion criteria were primary steady thermal heterogeneous-catalyst experiments reporting catalyst identity, temperature, pressure, feed/flow or space velocity, catalyst mass, and conversion/rate sufficient for productivity. Exclusions were reviews; computation without new experiments; plasma, photo-, electro- or electric-field-assisted operation; membrane-enhanced conversion; ammonia synthesis only; homogeneous chemistry; duplicates; and records lacking a mass/flow basis.

The 20-download ceiling was respected. Twelve papers ultimately supplied usable data and 487 operating points:

- `10.1002/cctc.202200688` — Co/Al2O3.
- `10.1002/cctc.202400875` — Co/Sm2O3.
- `10.1016/j.fuel.2022.124384` — perovskite-derived Ni.
- `10.1016/j.jiec.2020.11.003` — supported Ru.
- `10.1038/s41467-019-11848-9` — CoMoFeNiCu high-entropy alloys.
- `10.1038/s41467-023-36339-w` — dispersed Ru/MgO(111).
- `10.1039/c5fd00179j` — lithium-calcium imides.
- `10.1039/c5sc00205b` — lithium imide.
- `10.1039/d0cy00686f` — high-pressure Ru-K/CaO and supports.
- `10.1039/d0cy02336a` — Ru-K/CaO formulation comparison.
- `10.1039/d2fd00175f` — Ru-Y compositions.
- `10.3390/catal9010104` — CoFe transient/kinetic study.

Eight downloaded papers were unusable or outside the final comparison because catalyst mass/flow, feed fraction, conversion, or a consistent productivity basis remained missing after OCR/extraction. Candidate-level inclusion/exclusion reasons are retained in `candidates.csv`; examples include membrane reactors excluded because hydrogen permeation changes conversion, computational HEA optimization excluded for no new catalyst performance, and plasma studies excluded as nonthermal operation.

For this reaction only N2 and H2 are accepted products. Where a paper did not print H2 selectivity, S=1 was assigned from stoichiometry and the absence of an in-scope coproduct pathway; this means the dataset cannot test selectivity as an empirical discriminator.

## Mechanism and transfer from laboratory to plant

The mechanistic sequence is dissociative NH3 adsorption, sequential NHx dehydrogenation, H recombination/desorption, and N recombination/desorption. Strong nitrogen binding causes N-covered surfaces and costly N2 recombination/desorption; weak binding raises NHx activation barriers. This supports a nitrogen-binding Sabatier volcano and is consistent with the Ru, Fe/Co/Ni, alloy and imide literature cited in `decisions.jsonl`.

Each measured productivity is transferred with Arrhenius scaling, an explicit negative hydrogen order, and a reversible approach-to-equilibrium factor. Conversion is not treated as an intrinsic rate: it also reflects residence time, dilution and equilibrium. Plant per-pass conversion is optimized, but cannot exceed the lower of the thermodynamic limit, a 0.65 design cap, and the conversion demonstrated by that record. Catalyst mass is gross H2 production divided by transferred net productivity, adjusted for inventory and replacement availability. Missing 10%-activity-loss times use an 8,000 h default with 2,000–24,000 h sensitivity.

## Process boundary and flowsheet

Battery limit: purchased anhydrous NH3 and utilities enter; 99.97 mol% H2 at 200 bar leaves, with N2-rich PSA tail gas and unrecovered NH3/H2 losses. Upstream NH3 manufacture, downstream H2 use and N2 revenue are excluded.

Accepted flowsheet hash: `a81b8e514a7bc000`.

1. Fresh liquid-ammonia pump.
2. Fresh/recycle mixer.
3. Feed-effluent recuperator.
4. Ammonia vaporizer and trim heater.
5. Electric reaction furnace.
6. Multitube packed-bed decomposition reactor.
7. Effluent cooler/ammonia condenser.
8. Ammonia knockout drum.
9. Liquid-ammonia recycle pump.
10. H2 PSA.
11. Product H2 compressor.
12. Utilities/offsites.

A dedicated regenerator is excluded because the screened papers do not establish a universal regenerable coke cycle; catalyst deactivation is charged through replacement and outage. The model explicitly distinguishes U6 thermodynamic reaction duty from U5 purchased electric heat, and recovered heat is internal rather than purchased energy.

## Basis and parameter provenance

Capacity is 30,000 t H2/y at 8,000 h/y. Fresh NH3 is 99.9 mol%, 240 K, 22 bar; reactor pressure is 20 bar; product H2 is 99.97 mol%, 200 bar. PSA recovery is 85%, based on the cited NREL PSA discussion for a roughly 70 mol% H2 feed. All numeric model inputs and uncertainty bounds are in `sources.csv`; all prices, capital-recovery factor and fixed-O&M fraction come unchanged from `prices.json`.

Key values include ammonia $445/t (range $300–900/t), electricity $80/MWh ($40–150/MWh), capital recovery factor 0.0944, fixed O&M 4% of capex/y, 90% recuperator effectiveness (0.60–0.90), 95% electric-heater efficiency, 99.5% NH3 condensation recovery, compressor efficiency 75%, and 300 kg/m3 catalyst bulk density. The published central-cracker capital anchor is converted to $42.51 million installed capital at its reference scale and then allocated and scaled by each unit's own process load.

The full 77-row parameter table is `sources.csv`; `basis.json` contains every boundary state and its evidence. Assumptions always carry low/high bounds.

## Reference plant

Reference catalyst: published Ni/Sm2O3 point, 550 °C, atmospheric laboratory pressure, X=0.69, S=1 and r=1.292 kg H2 kg-cat^-1 h^-1. Industrial optimization selects 550 °C, 20 bar and 0.65 per-pass conversion.

| Metric | Result |
|---|---:|
| Total cost | $3,830.60/t H2 |
| Ammonia feed | $2,959.39/t |
| Purchased energy | $653.60/t |
| Annualized capital | $137.48/t |
| Catalyst replacement | $21.87/t |
| Fixed O&M/other | $58.25/t |
| Purchased primary energy | 74.28 GJ/t H2 |
| Installed capex | model unit sum; reported in the reference output |
| Capacity | 30,000 t H2/y |

Feed is 77.3% of total reference cost, energy 17.1%, capital 3.6%, catalyst 0.57%, and other 1.52%. Thus catalyst improvements affect a comparatively narrow cost slice unless activity is so low that reactor inventory and catalyst replacement become large.

## Laboratory versus plant ranking

Denominators are 13 comparison groups covering 12 papers and 487 records.

| Laboratory ranking variable | Point-level plant winner changes | Catalyst-level winner changes |
|---|---:|---:|
| Productivity/activity | 11/13 = 84.62% | 4/13 = 30.77% |
| Conversion | 9/13 = 69.23% | 4/13 = 30.77% |
| Selectivity | 0/13 | 0/13 |

For productivity-ranked point changes, seven were the same catalyst at another temperature and four selected another catalyst. Seven changes exceeded 1% regret, five exceeded 5%, and three exceeded 10%; median regret among changed groups was 4.27%. At catalyst level, three changes exceeded 5% and one exceeded 10%, with 7.98% median regret among changed groups.

Forty-seven records beat the reference. The cheapest point is $70.06/t below reference. Laboratory ranking changes primarily because temperature and demonstrated conversion alter furnace duty and recycle, whereas very high activity has diminishing value after catalyst inventory and reactor capital become small. Ru can rank strongly in activity but lose through metal replacement cost; high-temperature records can maximize rate while paying more heat; low-conversion records require more recycle, preheat, cooling and separation throughput.

The one-at-a-time catalyst-property attribution is:

- Activity/productivity: 90.4%.
- Metal price/loading: 8.9%.
- Temperature: 0.6%.
- Stability: 0.1%.
- Selectivity: 0%, because S has no observed variation.

This does **not** mean activity controls total hydrogen cost. Ammonia feed controls the total. Activity controls most of the *catalyst-caused spread*, but its benefit is attenuated by feed cost, thermodynamic conversion limits, the demonstrated-conversion cap, recycle and heat integration, PSA loss, compression and the small capital/catalyst share.

## Deterministic sensitivity

`run_sensitivity` perturbed every sourced range, assumption and price-table range one at a time. For the 80-record ranking subset, the cheapest catalyst remained `8_Co@Al2O3_550` in **77/77** perturbations; minimum Spearman rank correlation was **0.9855**.

Largest reference-cost sensitivities:

| Parameter range | Reference cost swing | Ranking winner changed? |
|---|---:|---:|
| NH3 price, $300–900/t | 104.17% | No |
| Electricity, $40–150/MWh | 23.46% | No |
| PSA H2 recovery, 0.75–0.90 | 17.51% | No |
| Reference installed capital | 4.64% | No |
| Recuperator effectiveness, 0.60–0.90 | 3.53% | No |
| Plant capacity, 10–100 kt/y | 3.47% | No |
| Maximum per-pass design cap, 0.50–0.80 | 2.89% | No |
| Product pressure, 30–415 bar | 2.72% | No |
| Catalyst support/manufacturing price | 2.41% | No |
| Default catalyst cycle, 2,000–24,000 h | 2.06% | No |

The key conclusion is robust: feed price and PSA recovery move absolute cost strongly but barely alter catalyst ranking; activity and metal cost explain the residual catalyst differences.

## Atomic, laboratory and industrial optima

The atom-scale model uses N adsorption energy relative to 1/2 N2, descriptor range -1.6 to +0.2 eV/N, a reversible NH3/NHx/H/N network declared through `mkm_solver`, and a fast limiting-step envelope for descriptor-grid evaluation. The atom-scale optimum at the industrial inlet condition is **D = -0.547 eV/N**, log10(TOF/s/site)=5.436 at 823.15 K and a 20 bar NH3 inlet. It lies between the representative Ru and Co descriptors and expresses the strong/weak binding compromise.

The laboratory optimum is `8_Co@Al2O3_550`, record 36, r=3,444.64 kg H2 kg-cat^-1 h^-1. The measured industrial optimum is the same catalyst formulation at record 29 and 500 °C, but at much lower laboratory productivity. Descriptor-only plant optimization also selects D=-0.547 eV/N for Fe-, Ru-, Co- and Ni-price cases; costs are approximately $3,877.93/t for Fe, Co and Ni and $3,878.45/t for Ru. The descriptor benefit is mostly kinetic; once the optimum is reached, metal-price differences are small in the full plant total.

Of 487 usable records, 431 map to Fe/Ru/Co/Ni descriptors; 56 imide, mixed/unsupported or otherwise unmapped records are excluded from descriptor comparisons. Pairwise disagreements were:

- Atomic vs laboratory: 26,282/53,304 non-tied pairs.
- Atomic vs industrial: 36,454/53,592 non-tied pairs.
- Laboratory vs industrial: 26,029/92,072 non-tied pairs.

A descriptor-only counterfactual moves the reference effective descriptor from -0.896 to -0.547 eV and reduces its modeled cost from $6,922.33 to $3,878.45/t at the Ru price, a $3,043.88/t decrease. However, backward-design targets of 10% and 5% below the reference cost are reported as **not reachable** within the declared descriptor range and fixed flowsheet/boundary; ammonia and utility costs set a floor that catalytic activity alone cannot cross.

## Evidence debt and limitations

Two consequential assumptions remain explicitly unresolved and are retained in sensitivity:

1. Recuperator effectiveness 0.60–0.90: exchanger architecture and minimum temperature approach are design-specific; no open source fixes one value for all catalyst temperatures.
2. Maximum absolute per-pass conversion 0.50–0.80: equilibrium data do not establish a universal industrial packed-bed design cap across all catalyst families.

Additional limitations: extracted productivity may inherit reported-volume and catalyst-mass uncertainty; pellet-scale transport is not separately fitted; the same hydrogen-inhibition transfer form is used across catalyst families; most papers provide short stability tests; imides and multicomponent catalysts lack a unique metal descriptor; assigned S=1 suppresses any selectivity analysis; the atomic scaling/BEP coefficients are a literature-constrained reduced model rather than a catalyst-specific DFT database; nitrogen coproduct has no revenue credit; and detailed vessel/mechanical design is represented by load-scaled installed capital rather than a vendor quote.

## Reproducible artifacts

- `candidates.csv`: all screened papers and reasons.
- `records.csv`: normalized extracted records and usability.
- `flowsheet.json`, `flowsheet.md`, `basis.json`: accepted process definition.
- `sources.csv`, `prices.json`: all numeric provenance and fixed prices.
- `model.py`: industrial costing and physics model.
- `atomic.py`: atom-scale descriptor model.
- `costs.csv`, `analysis.json`: record costs and ranking analysis.
- `sensitivity.json`: deterministic uncertainty table.
- `three_optima.json`: atomic/laboratory/industrial optima and backward design.
- `decisions.jsonl`, `evidence_debt.json`: modeling choices and evidence resolution.

## Final conclusion

A plant should not select an ammonia-decomposition catalyst by the hottest or fastest laboratory point. It should select a sufficiently active, inexpensive catalyst at the lowest temperature and highest evidenced per-pass conversion that minimize recycle and heating without paying for unnecessary activity or noble metal. In this evidence set that is a cobalt/alumina point at 500 °C. Activity is the main catalyst property, but ammonia feed, PSA recovery, heat integration and conversion/recycle design dominate the full economic outcome and sharply attenuate the value of further activity gains.


### Exact retained uncertainty keys

- `process.recuperator_effectiveness`: low 0.60, high 0.90.
- `process.maximum_absolute_per_pass_conversion`: low 0.50, high 0.80.
