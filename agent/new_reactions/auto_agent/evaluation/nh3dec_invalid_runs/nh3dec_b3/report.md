# Ammonia decomposition to hydrogen: catalyst-to-plant economic analysis

## Executive conclusion

A plant would **not always select the laboratory activity winner**, but the disagreements found here are economically small under the central assumptions because merchant ammonia dominates the hydrogen cost. Across the analyzable comparisons, productivity ranking changed at the operating-point level in **3 of 8 groups (37.5%; 95% interval 10–75%)** and at catalyst level in **2 of 8 groups (25%; 0–57.1%)**. Conversion ranking changed in **1 of 8 groups (12.5%)**; selectivity ranking never changed because the screened thermal decomposition studies effectively reported the stoichiometric H2/N2 product pair.

The model attributes **95.6% of the catalyst-dependent cost variation to activity/productivity**, versus temperature 1.9%, stability 1.5%, metal price 1.0%, and selectivity 0%. Nevertheless, doubling the reference catalyst activity lowers modeled cost by only **$2.36/t H2**, because feed, common separation/compression, and common capital attenuate catalyst improvements.

**Critical qualification:** `check_model` did not pass its stoichiometry gate, although its independent mass/element, equilibrium, reaction-heat, heat-supply, compression, separation, unit-accounting, finite-cost, and determinism failures had been cleared. Therefore all numerical costs and rankings below are **provisional model outputs, not a validated techno-economic result**. The atomistic `atomic.py` layer was not completed. These limitations prevent a defensible atomic/lab/plant three-optima conclusion.

## Literature search and screening

The search covered primary experimental studies of heterogeneous thermal NH3 decomposition. Inclusion required a named solid catalyst and quantitative temperature, pressure or atmospheric basis, NH3 composition, conversion or product rate, and catalyst mass/flow/space velocity sufficient for normalization. Reviews, process-only modeling, DFT-only studies, plasma, photo/photothermal, electrochemical/electric-field systems, membrane-integrated results without separable catalyst data, ammonia-borane/hydrazine decomposition, and records lacking a quantitative catalyst basis were excluded.

The download set was deliberately diverse: Ru, Ni, Co, Pd/Ni, high-entropy alloys, oxynitrides, zeolites, and imide catalysts. Twelve initially parsed papers plus one additional paper were processed. Automated extraction was rate-limited for five papers, so representative records were reconstructed from explicit tables, captions, and methods where possible. The final normalized dataset contained **313 usable operating points from 11 papers**; thus the target of 12 papers with usable records was not achieved.

Usable-paper families included:

- Co/Al2O3, DOI 10.1002/cctc.202200688.
- Sm2O3-supported Fe/Co/Ni, DOI 10.1002/cctc.202400875.
- Ni/Co perovskite-derived catalysts, DOI 10.1016/j.fuel.2022.124384.
- Oxynitride-supported catalysts, DOI 10.1038/s41427-024-00572-6.
- Co–Mo high-entropy alloy catalysts, DOI 10.1038/s41467-019-11848-9.
- Ru/MgO facets, DOI 10.1038/s41467-023-36339-w.
- Lithium–calcium imides, DOI 10.1039/c5fd00179j.
- Lithium imide and benchmark Ni/Ru catalysts, DOI 10.1039/c5sc00205b.
- Ba-promoted CoCe, DOI 10.1039/d0cy02336a.
- Ru-loaded zeolites, DOI 10.1039/d2fd00175f.
- Pd/Ni, DOI 10.1371/journal.pone.0136805.

The FeCo/K study DOI 10.2478/pjct-2014-0080 was retained as mechanistic evidence but lacked a sufficiently digitizable numerical performance point. The additional high-entropy ceramic paper DOI 10.1038/s41545-025-00517-8 was excluded after full-text inspection because it was electrochemical rather than conventional thermocatalytic decomposition. Several Elsevier and MDPI candidates could not be downloaded through the available routes. Reviews, plasma/photo/electrochemical papers, ammonia-borane studies, and modeling-only papers were excluded by the stated criteria.

For conventional NH3 decomposition records where only NH3, H2, and N2 were reported, H2 selectivity was normalized to 100%, consistent with the stoichiometric reaction. This is why selectivity has no discriminatory power in the final dataset.

## Mechanism and kinetic transfer

The selected mechanism is dissociative Langmuir–Hinshelwood chemistry: NH3 adsorption, sequential NHx dehydrogenation, recombinative H2 desorption, and typically recombinative N2 desorption as a kinetically important step. The evidence includes negligible N2 order and negative H2 order over Ru/MgO, strong negative H2 orders over CoCe, and FeCo nitriding/nitrogen-saturation behavior.

Each literature productivity was treated as an apparent catalyst-mass rate at its reported condition. Transfer to plant conditions used:

1. an apparent Arrhenius correction, central activation energy 90 kJ/mol and range 70–120 kJ/mol;
2. empirical H2 inhibition, central order 0.7 and range 0.4–1.7;
3. a thermodynamic approach-to-equilibrium multiplier, `1-Q/K`;
4. a 0.5 central activity safety factor;
5. an extrapolation limit around the reported laboratory temperature;
6. catalyst replacement based on measured time to 10% activity loss where available, otherwise a bounded default.

This preserves relative measured activity while preventing irreversible extrapolation beyond equilibrium. It does not claim that one detailed microkinetic parameter set represents Ru, Co, Ni, alloys, nitrides, and imides.

## Reactor and flowsheet

The accepted flowsheet hash is recorded by `submit_flowsheet`; the final diagram and unit list are in `flowsheet.md` and `flowsheet.json`.

The battery limit starts with merchant liquid NH3 and ends with compressed high-purity H2. The plant includes:

1. fresh-ammonia pump;
2. fresh/recycle mixer;
3. NH3 vaporizer;
4. feed–effluent recuperator;
5. externally heated multitubular packed-bed reactor;
6. reactor furnace;
7. effluent cooler;
8. NH3 recovery separator;
9. NH3 recycle pump;
10. H2 PSA;
11. H2 product compressor;
12. utilities and offsites.

The reactor choice scales the dominant laboratory fixed-bed configuration and provides controlled heat to an endothermic reaction. In-situ catalyst regeneration was excluded because no general regeneration method spans the catalyst families; catalyst replacement is costed instead. The model optimizes reactor temperature and conversion, with recycle, heat recovery, separator loading, furnace duty, catalyst inventory, and capital changing with the operating point.

## Plant basis and parameters

Central basis:

- capacity: 100,000 t H2/y, range 20,000–300,000;
- operating time: 8,000 h/y, range 7,000–8,400;
- NH3 feed: 298.15 K, 10 bar, 99.9 mol%;
- H2 product: 30 bar, 99.97 mol%;
- reactor pressure: 10 bar;
- PSA H2 recovery: 0.85, range 0.75–0.92;
- recuperator effectiveness: 0.75;
- furnace efficiency: 0.85;
- NH3 recovery: 0.995;
- compressor efficiency: 0.75.

Every numeric model input and range is listed in `sources.csv`. All commodity and catalyst-material prices, the capital recovery factor, and fixed O&M fraction are taken unchanged from `prices.json`. Principal prices are ammonia **$445/t** (range $300–900/t), natural gas **$2.50/GJ** ($2–12/GJ), electricity **$80/MWh** ($40–150/MWh), catalyst support/manufacturing **$20/kg**, Ru **$53,852.5/kg**, and the fixed capital factors CRF 0.0944/y and fixed O&M 0.04/y.

Most equipment costs are bounded engineering assumptions rather than quoted vendor estimates. This is a major evidence limitation; the full central, low, and high values remain auditable in `sources.csv`.

## Provisional reference plant result

For the Ru/MgO(111) reference record, the model reports:

| Cost component | USD/t H2 |
|---|---:|
| NH3/feed | 2,949.40 |
| Purchased energy | 127.97 |
| Capital and fixed O&M | 408.36 |
| Catalyst | 4.71 |
| Other | 0.00 |
| **Total** | **3,490.44** |

The feed share is **84.5%** of total cost, capital 11.7%, energy 3.7%, and catalyst approximately 0.1%. The sensitivity pipeline reports reference purchased primary energy of **28.12 GJ/t H2**. These values are generated by `model.py`, not copied from a process study.

Because the stoichiometry gate remains unresolved, this breakdown must be interpreted only as the output of the current model formulation.

## Laboratory ranking versus plant ranking

`run_analysis` costed 313 usable records from 11 papers. Its cheapest central-case record was **lithium–calcium imide, Li2Ca(NH)2**, from DOI 10.1039/c5fd00179j at a reported 519 °C, with provisional cost **$3,484.10/t H2**. A total of **205 of 313 operating points** were below the reference cost, but the spread was narrow relative to the approximately $3,000/t feed burden.

Ranking denominators:

| Laboratory metric | Level | Comparable groups | Groups changing winner | Fraction |
|---|---|---:|---:|---:|
| Productivity | operating point | 8 | 3 | 37.5% |
| Productivity | catalyst | 8 | 2 | 25.0% |
| Conversion | operating point | 8 | 1 | 12.5% |
| Conversion | catalyst | 8 | 1 | 12.5% |
| Selectivity | operating point | 8 | 0 | 0% |
| Selectivity | catalyst | 8 | 0 | 0% |

For productivity disagreements, two point-level changes selected another catalyst and one selected the same catalyst at another temperature. None of the ranking changes produced more than 1% regret in modeled plant cost; the median regret among changed productivity winners was only 0.02% at point level and 0.01% at catalyst level.

Thus, laboratory productivity is an imperfect predictor of the exact winner, especially when the plant can choose a different temperature or trade catalyst inventory against heat and equipment. However, under this cost structure, choosing the laboratory winner rather than the modeled plant winner has little economic penalty.

## Controlling catalyst property and attenuation mechanisms

One-at-a-time attribution of catalyst-dependent cost variation was:

| Property | Share |
|---|---:|
| Activity/productivity | 95.6% |
| Temperature | 1.9% |
| Stability | 1.5% |
| Metal price/composition | 1.0% |
| Selectivity | 0.0% |

Activity controls the differences that remain because it changes catalyst inventory and reactor sizing. Its effect on total H2 cost is strongly attenuated by:

- **feedstock cost:** the stoichiometric ammonia requirement is common to all catalysts and is the largest cost;
- **equilibrium:** higher activity cannot create conversion above the thermodynamic limit;
- **recycle:** lower per-pass conversion increases circulation, vaporization, heat exchange, cooling, and separator load but recovers NH3 value;
- **separation:** H2/N2 purification and product recovery are largely common costs;
- **equipment:** reactor and common-plant capital dilute catalyst-price differences;
- **operation:** higher temperature can compensate activity but raises furnace duty and may increase capital/operating burden;
- **metal loading:** even Ru cost is small when catalyst inventory and replacement are small compared with annual NH3 expenditure.

At the reference point, doubling activity changes cost by only **−$2.36/t H2**. A one-percentage-point selectivity increase has zero modeled value because baseline selectivity is already 100%.

## Deterministic sensitivity

`run_sensitivity` varied each sourced range, assumption range, and price-table range one at a time. Leading reference-cost swings were:

| Parameter | Low–high range | Reference cost swing | Cheapest record changed? | Minimum rank Spearman |
|---|---|---:|---|---:|
| NH3 price | $300–900/t | 113.9% | No | 0.9992 |
| PSA H2 recovery | 0.75–0.92 | 16.5% | No | 0.9994 |
| Plant capacity | 20–300 kt/y | 12.6% | No | 0.9985 |
| Base capital capacity | 50–200 kt/y | 10.9% | No | 0.9990 |
| Natural-gas price | $2–12/GJ | 5.47% | **Yes** | 0.9824 |
| Reactor base capex | $25–150 million | 4.89% | No | 0.9960 |
| PSA base capex | $35–150 million | 4.88% | No | 1.0000 |
| Capital recovery factor | 0.08–0.13/y | 4.35% | No | 0.9997 |
| Fixed O&M fraction | 0.02–0.06/y | 3.48% | No | 0.9998 |
| Utilities/offsites capex | $20–100 million | 3.41% | No | 0.9991 |
| Electricity price | $40–150/MWh | 3.16% | No | 0.9999 |
| Furnace base capex | $15–80 million | 2.89% | No | 0.9995 |

The ammonia-price range changes absolute economics drastically but barely changes catalyst ranking. Natural gas is the notable ranking-sensitive parameter: at its high value, the cheapest record changes to **HEA-Co55Mo15/CNF**, consistent with stronger value for lower-temperature or lower-heat operation when fuel is expensive.

## What the evidence could not support

1. The target of 12 papers with usable data was missed; 11 papers were usable.
2. Several records were reconstructed from figures or text, and automated extraction was interrupted by a usage limit.
3. Stability data were sparse; default catalyst life materially substitutes for missing measurements.
4. Industrial equipment costs, pressure choices, and some efficiencies are bounded assumptions rather than vendor quotations.
5. A universal kinetic transfer law across metals, alloys, nitrides, oxides, zeolites, and imides is not experimentally established.
6. The current `model.py` retains an unresolved `check_model` stoichiometry failure. Numerical results are therefore provisional.
7. The independent evidence-debt review and critique loop were not completed.
8. The atomic descriptor, scaling/BEP relations, `atomic.py`, `check_atomic`, and `run_three_optima` were not completed; no atomic optimum or backward-design claim is made.
9. The lithium-imide family may pose containment, phase-change, materials-handling, and scale-up constraints not represented by the generic packed-bed model. Its apparent economic win should not be treated as an investment recommendation.

## Overall answer

Laboratory activity generally identifies the economically relevant catalyst region, but it does not perfectly predict the exact catalyst and temperature a plant selects. Ranking changes arise when the plant trades intrinsic productivity against equilibrium, H2 inhibition, reaction temperature, recycle load, furnace duty, reactor size, stability, and metal cost. In the present provisional model those changes have very low regret because ammonia feed cost dominates. Activity is the main catalyst property controlling plant cost, while selectivity is already saturated and metal price is heavily diluted. The strongest practical levers are therefore ammonia price and supply, hydrogen recovery, scale, and heat integration—not further activity gains once catalyst inventory is already a small part of total cost.
