# Industrial screening of literature catalysts for non-oxidative propane dehydrogenation

**Reaction:** C3H8 → C3H6 + H2  
**Analysis date:** 10 November 2026  
**Database:** 59 catalyst × condition records from six coded papers (P01–P06).

## Executive answer

- **Industrial bottleneck:** the cost is carried primarily by **propane feed and carbon selectivity to propylene**, not precious-metal price or coke-cycle stability. In the reference plant, fresh propane is **$441.2/t propylene**, 59.9% of the net modeled cost; annualised capital is $261.3/t and energy is $74.6/t. Across the 27 costable records, selectivity is the largest one-at-a-time cost-gap term for **22/27**, activity for 4/27, and temperature/equilibrium for 1/27. Metal price and modeled regeneration are never the largest term.
- **Plant choice from the measured literature set:** **PDH-015, PtGa/SiO2 at 600 °C**, at **$658.2/t propylene** in the central case, versus **$736.7/t** for the industrial reference. Its measured selectivity is 99.1%; the optimized per-pass conversion is 45.4%; modeled inventory is 10.6 t. Its disclosed stability is weak—10% activity loss in 8.13 h—so this is a cost-screen winner, **not a claim of plant readiness**. PDH-017 is only $1.8/t behind.
- **Do paper rankings agree?** Using the two metrics named in the question (conversion and propylene productivity), the lab leader agrees with the cheapest plant choice in **8/12 comparisons (66.7%)**. There are 4 disagreements: **3 switch to another catalyst, 0 are the same catalyst at another temperature, and 1 is the same catalyst under another same-temperature condition**. Mean regret is $1,693.8/t, median $921.6/t, but this is dominated by P01's very low selectivities; the two non-P01 regrets are only $1.8 and $6.9/t.
- **Main uncertainty:** selectivity remained masked for 32/59 records, so those records cannot be responsibly costed or ruled out. Long-term irreversible lifetime is unavailable for every literature catalyst; short time-on-stream deactivation was treated as a regeneration-cycle indicator only.

## 1. Reveal strategy and budget

All **35/35** reveal units were used.

1. Revealed selectivity for 27 records: both visible-metric leaders and plausible plant contenders in every paper, with denser coverage of P02, P05 and P06 where activity/selectivity looked industrially relevant.
2. Revealed stability for eight decision-critical records: PDH-003, 015, 017, 018, 020, 027, 033 and 059. Six had numeric tests; PDH-003 and PDH-033 had no reported stability values.
3. This allocation ensured that every paper's conversion leader and product-productivity leader was costable. It did not reveal all lower-ranked records because selectivity, rather than another stability datum, was needed first to compute propane consumption.

**Treatment of masked fields:**
- Masked selectivity: no point estimate and no plant cost; these 32 records are reported as uncostable.
- Masked/no numeric stability: assumed 24 h to 10% activity loss, with 5–100 h sensitivity. This affects regeneration and online fraction, not irreversible catalyst lifetime.
- Unknown Pt loading in P06: 0.3 wt% central, 0.1–1.0 wt% sensitivity. Known 3 wt% Pt in P02/P05 was used as printed.

## 2. Plant model

### 2.1 Reference plant and costing equations

A 750,000 t/y polymer-grade-propylene plant operating 8,500 h/y was used, close to Enterprise's 1.65 billion lb/y PDH scale. The industrial material benchmark is 1.12 t propane/t propylene, corresponding to an effective molar selectivity/yield of about 93.6% after recovery losses.

For each literature record, the lab conversion was **not** imposed on the plant. A first-order approach-to-equilibrium PFR model was fitted to the measured lab conversion and converted-propane rate:

`W/F = -(Xeq/k) ln(1 - X/Xeq)`

Equilibrium is represented by `Kp(600 °C)=0.299` and a 124.3 kJ/mol van't Hoff slope. Lab dilution and reported H2 were included in the equilibrium calculation; the plant reactor feed was modeled as propane after product/H2 separation. The plant then optimized per-pass conversion from 5% to 95% of equilibrium. Increasing conversion reduces recycle but increases catalyst inventory near equilibrium.

Fresh propane consumption is `1.048/S` t/t propylene. Circulation-sensitive capital and energy scale with reactor feed per tonne product. Total installed capital is split 25% fixed, 60% circulation/separation and 15% reactor; variable blocks scale to the 0.60 power. Annual capital charge is 10% capital recovery plus 4% fixed O&M.

Catalyst inventory follows modeled plant productivity. Catalyst annual cost includes $20/kg fabrication/support, element values, three-year replacement, 90% Pt recovery and financing of retained Pt. Regeneration uses the disclosed time to 10% activity loss, a 1 h regeneration, and $0.05/kg-catalyst-cycle. These are explicit assumptions, not claims about a commercial regeneration design.

### 2.2 Parameter and source table

| Parameter | Central value | Range / status | Source or rationale |
|---|---:|---:|---|
| Capacity | 750,000 t/y | 650–800 kt/y | Enterprise PDH plants report 1.65 billion lb/y PGP capacity (~748 kt/y): Enterprise 2023 10-K / PDH2 disclosure, https://www.sec.gov/Archives/edgar/data/1061219/000106121924000006/epd-20231231.htm |
| Total installed capital | $1.40 bn | $1.0–2.0 bn | US EPA statement-of-basis records an estimated $1.4 bn for the Enterprise PDH unit: https://archive.epa.gov/region6/6pd/air/pd-r/ghg/web/pdf/enterprise-propane-sob03072014.pdf |
| Propane use, reference | 1.12 t/t propylene | industrial benchmark | Clariant CATOFIN material cites below 1.12 t/t; used as an effective yield benchmark: https://www.clariant.com/en/Business-Units/Catalysts/Petrochemical-and-Refining-Catalysts/CATOFIN-and-CATADIENE |
| Propane price | $394/t | $300–500/t | Constructed planning value (~$0.755/gal at 4.23 lb/gal) within EIA Mont Belvieu series; not a contracted plant price: https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EER_EPLLPA_PF4_Y35MB_DPG&f=M |
| Natural gas | $4.96/GJ | $3.5–8/GJ | Planning value based on EIA U.S. industrial-gas series: https://www.eia.gov/dnav/ng/ng_pri_sum_dcu_nus_m.htm |
| Industrial electricity | $0.0862/kWh | $0.06–0.12 | EIA industrial retail-price data: https://www.eia.gov/electricity/monthly/ |
| Thermal demand | 13.3 GJ/t propylene | 8–18 | **Assumption**, calibrated from 11.84 GJ/t propane process-energy figures and 1.12 t/t propane. Electricity is separately 100 kWh/t (75–300 sensitivity conceptually). |
| Hydrogen credit | $1.15/kg recovered H2; 90% recovery | $0.5–1.74/kg | **Discounted assumption** versus DOE natural-gas-reforming production-cost estimates; avoids crediting full merchant price: https://www.energy.gov/eere/fuelcells/hydrogen-production-natural-gas-reforming |
| Operating time | 8,500 h/y | 8,000–8,760 | **Assumption**, world-scale continuous plant with outages. |
| Annualisation | 10% CRF + 4% fixed O&M | 8–14% + 3–6% | **Assumption**. |
| Reference catalyst annual expense | $5.42m/y | $2–15m/y | **Assumption/calibration** from a reported £4.17m/y catalyst-replacement line converted at $1.30/£; not used to rank literature records. |
| Pt | $30,500/kg | $20,000–50,000 | Planning value near $950/oz; range anchored to USGS platinum-group-metal statistics: https://pubs.usgs.gov/periodicals/mcs2026/ |
| Ga / Co / base metals | $400/kg Ga; $30/kg Co; Fe $0.15, P $4, Zn $3, Pb $2.2, Sn $30, K $1 per kg | broad commodity ranges | Planning assumptions anchored to USGS 2026 commodity summaries; catalyst-grade procurement may be higher: https://pubs.usgs.gov/periodicals/mcs2026/ |
| Reaction enthalpy | 124.3 kJ/mol | 120–128 | Thermochemical value consistent with NIST gas-phase formation enthalpies: https://webbook.nist.gov/chemistry/ |
| Catalyst life / Pt recovery | 3 y / 90% | 1–5 y / 80–98% | **Assumption**; irreversible lifetime was not supplied by the papers. |
| Regeneration | 1 h, $0.05/kg-cycle | 0.5–2 h; $0.01–0.20 | **Assumption**; used only as an order-of-magnitude cyclic-deactivation penalty. |

### 2.3 Reference check

The reference model gives **$736.7/t propylene**: feed $441.2, energy $74.6, capital/fixed O&M $261.3, catalyst $7.2, regeneration $2.0, and H2 credit −$49.6. Feed is 59.9% of net cost. This is consistent in order of magnitude with open PDH techno-economic studies and with the common finding that propane feed contributes roughly 60% of cost. It is a screening model, not a bankable estimate; regional propane/propylene contracts and the financing structure can move the answer materially.

## 3a. Plant cost of costable records

All values are USD per tonne propylene unless otherwise labeled. “Catalyst” and “regen” columns are annual catalyst and regeneration contributions. Costs for the 32 unrevealed-selectivity records are deliberately left unknown.

| Record   | Paper   | Catalyst                              |     S | stability measured?   |   cost $/t |   opt. X |   inventory t |   feed |   energy |   capital |   catalyst |   regen |
|:---------|:--------|:--------------------------------------|------:|:----------------------|-----------:|---------:|--------------:|-------:|---------:|----------:|-----------:|--------:|
| PDH-015  | P02     | PtGa/SiO2                             | 0.991 | True                  |      658.2 |    0.454 |          10.6 |  416.7 |     67.8 |     221   |        1.7 |     0.7 |
| PDH-017  | P02     | Pt3Sn/SiO2                            | 0.986 | True                  |      660   |    0.454 |           9.3 |  418.8 |     68   |     220.6 |        1.5 |     0.7 |
| PDH-016  | P02     | PtGa-Pb/SiO2 (Pt/Pb = 2)              | 0.996 | False                 |      666.5 |    0.454 |          27.4 |  414.6 |     67.6 |     229   |        4.4 |     0.6 |
| PDH-059  | P06     | Pt3GaK                                | 0.963 | True                  |      671.2 |    0.522 |          43.9 |  428.8 |     64.1 |     226.4 |        1.3 |     0.2 |
| PDH-036  | P06     | PtGa                                  | 0.968 | False                 |      672.9 |    0.522 |          54   |  426.6 |     63.9 |     229.4 |        1.4 |     1.2 |
| PDH-033  | P06     | Pt3GaK                                | 0.967 | False                 |      673.6 |    0.522 |          54.1 |  427   |     63.9 |     229.5 |        1.6 |     1.2 |
| PDH-029  | P06     | PtGaK                                 | 0.967 | False                 |      674.1 |    0.522 |          55.9 |  427   |     63.9 |     230.1 |        1.5 |     1.3 |
| PDH-039  | P06     | Pt3Ga                                 | 0.946 | False                 |      687.6 |    0.522 |          59.3 |  436.5 |     64.7 |     232.9 |        1.7 |     1.3 |
| PDH-027  | P05     | Pt 0 Zn d+ /SiO2                      | 0.981 | True                  |      727.9 |    0.292 |          10.3 |  420.9 |     88.3 |     265.7 |        1.7 |     0.9 |
| PDH-025  | P05     | Pt 0 Zn d+ /SiO2                      | 0.976 | False                 |      734.9 |    0.292 |          16.3 |  423.1 |     88.6 |     269.8 |        2.6 |     0.4 |
| PDH-026  | P05     | Pt 0 Zn d+ /SiO2                      | 0.963 | False                 |      749.2 |    0.292 |          25.8 |  428.8 |     89.4 |     275.8 |        4.2 |     0.6 |
| PDH-044  | P06     | 3GaK                                  | 0.89  | False                 |      752.4 |    0.504 |         149.1 |  463.9 |     68.6 |     263.9 |        2.1 |     3.4 |
| PDH-028  | P05     | Pt 0 Zn d+ /SiO2                      | 0.95  | False                 |      754.6 |    0.292 |          21.2 |  434.6 |     90.3 |     275.3 |        3.4 |     0.5 |
| PDH-051  | P06     | 3Ga                                   | 0.88  | False                 |      755.3 |    0.507 |         137.1 |  469.2 |     68.9 |     261.8 |        1.9 |     3.1 |
| PDH-042  | P06     | GaK                                   | 0.865 | False                 |      765.5 |    0.508 |         138.6 |  477.4 |     69.5 |     263.5 |        1.6 |     3.1 |
| PDH-048  | P06     | Ga                                    | 0.848 | False                 |      786.6 |    0.502 |         168.6 |  486.9 |     70.9 |     272.6 |        1.9 |     3.8 |
| PDH-018  | P03     | Dir-reduction catalyst (2% Co/SBA-15) | 0.96  | True                  |      800.1 |    0.395 |         324.7 |  430.1 |     75.5 |     311.3 |        3   |    29.9 |
| PDH-019  | P03     | H2-reduction catalyst (2% Co/SBA-15)  | 0.92  | False                 |      891.4 |    0.373 |         824.3 |  448.8 |     80.6 |     385.4 |        7.5 |    18.7 |
| PDH-020  | P04     | [(^SiO)3Ga(XOSi^)] (3, X = H or ^Si)  | 0.943 | True                  |     1043.7 |    0.229 |         977.1 |  437.9 |    108.5 |     455.9 |       11.3 |    79.7 |
| PDH-053  | P06     | Pt                                    | 0.564 | False                 |     1164   |    0.479 |         439   |  732.1 |     96.6 |     364.5 |       10.5 |    10   |
| PDH-010  | P01     | (3Fe:P)/Al2O3, with H2 pretreatment   | 0.77  | False                 |     1344.7 |    0.292 |        3467.4 |  536.2 |    109.1 |     639.4 |       31   |    78.6 |
| PDH-001  | P01     | (1Fe:P)/Al2O3                         | 0.45  | False                 |     2063.2 |    0.295 |        5749.7 |  917.6 |    166.5 |     846.6 |       51.8 |   130.3 |
| PDH-005  | P01     | (3Fe:P)/Al2O3                         | 0.26  | False                 |     2603.6 |    0.376 |        3019.9 | 1588.1 |    216.5 |     753.1 |       27   |    68.5 |
| PDH-003  | P01     | (2Fe:P)/Al2O3                         | 0.2   | False                 |     3181.1 |    0.391 |        3039.6 | 2064.6 |    263.9 |     806   |       27.3 |    68.9 |
| PDH-012  | P01     | (2Fe:P)/Al2O3, reduced at 600 °C      | 0.2   | False                 |     4079.6 |    0.298 |       12698   | 2064.6 |    338.4 |    1324.5 |      113.9 |   287.8 |
| PDH-008  | P01     | (2Fe:P)/Al2O3                         | 0.2   | False                 |     4148.6 |    0.293 |       13567.7 | 2064.6 |    343.6 |    1360.7 |      121.7 |   307.5 |
| PDH-009  | P01     | (3Fe:P)/Al2O3                         | 0.12  | False                 |     6275.1 |    0.304 |       19731.5 | 3440.9 |    535.6 |    1724.6 |      176.3 |   447.2 |

**Lowest five:** PDH-015 $658.2/t; PDH-017 $660.0/t; PDH-016 $666.5/t; PDH-059 $671.2/t; PDH-036 $672.9/t. The winner's margin over PDH-017 is only $1.8/t, so those two are economically tied at this model's precision.

## 3b. Paper ranking versus plant ranking

| Paper   | Lab metric           | Lab leader   | Plant choice   | Agree?   | Disagreement type                               |   Regret $/t |
|:--------|:---------------------|:-------------|:---------------|:---------|:------------------------------------------------|-------------:|
| P01     | conversion           | PDH-009      | PDH-010        | False    | other catalyst                                  |       4930.3 |
| P01     | product_productivity | PDH-003      | PDH-010        | False    | other catalyst                                  |       1836.3 |
| P02     | conversion           | PDH-015      | PDH-015        | True     | agree                                           |          0   |
| P02     | product_productivity | PDH-017      | PDH-015        | False    | other catalyst                                  |          1.8 |
| P03     | conversion           | PDH-018      | PDH-018        | True     | agree                                           |          0   |
| P03     | product_productivity | PDH-018      | PDH-018        | True     | agree                                           |          0   |
| P04     | conversion           | PDH-020      | PDH-020        | True     | agree                                           |          0   |
| P04     | product_productivity | PDH-020      | PDH-020        | True     | agree                                           |          0   |
| P05     | conversion           | PDH-025      | PDH-027        | False    | same catalyst, other same-temperature condition |          6.9 |
| P05     | product_productivity | PDH-027      | PDH-027        | True     | agree                                           |          0   |
| P06     | conversion           | PDH-059      | PDH-059        | True     | agree                                           |          0   |
| P06     | product_productivity | PDH-059      | PDH-059        | True     | agree                                           |          0   |

Denominator: six same-paper/same-pressure/same-feed groups × two requested lab metrics = **12 comparisons**. Agreement is 8/12. If converted-reactant rate is added as a third metric, agreement is 12/18 and disagreement 6/18; the qualitative conclusion is unchanged.

The very large P01 regrets are real consequences of the disclosed selectivities in the database: its conversion leader PDH-009 has only 12% selectivity and its rate/productivity leader PDH-003 has 20%, whereas the plant-cost winner within P01, PDH-010, has 77%. Ranking on conversion or converted-propane rate therefore rewards propane destruction.

## 3c. Bottleneck and attribution

### Reference cost breakdown

| Item | $/t propylene | Share of net cost |
|---|---:|---:|
| Fresh propane | 441.2 | 59.9% |
| Annualised capital + fixed O&M | 261.3 | 35.5% |
| Energy | 74.6 | 10.1% |
| Catalyst | 7.2 | 1.0% |
| Regeneration | 2.0 | 0.3% |
| H2 credit | −49.6 | −6.7% |
| **Net** | **736.7** | **100%** |

### One-at-a-time levers at the reference

- +1 percentage point selectivity: **−$4.66/t**.
- 2× activity: **−$17.95/t**, mainly by shrinking the modeled reactor block and inventory.
- 10× coke-cycle stability: **−$1.80/t** under the central regeneration assumptions.
- +$10/t propane: **+$11.20/t propylene**.

Thus, at a mature reference catalyst, a large activity doubling has more value than one selectivity point, but **feedstock price and selectivity carry the total cost**. Across the literature gaps, selectivity is dominant in 22/27 records; activity is dominant in four low-rate records; temperature/equilibrium is dominant in one. Metal cost does not dominate any record.

The full one-at-a-time attribution for every costed record is saved in `analysis_attribution.csv`. Important examples:

- PDH-009 gap to reference: +$5,538/t; setting only selectivity to the reference removes $5,163/t.
- PDH-003: +$2,444/t; selectivity term $2,333/t.
- PDH-010: +$608/t; selectivity term $193/t and 2× activity saves $181/t.
- PDH-018: +$63/t; it is already more selective than reference, but 2× activity saves $47.7/t and 10× stability saves $37.0/t.
- PDH-015: −$78.5/t versus reference; its selectivity advantage is worth $32.5/t and its high activity/compact reactor supplies the rest.

## 3d. Backward design

Records already below the reference need no improvement in this deterministic screen. For records above the reference, the one-at-a-time requirement is:

| Record   |   Base $/t | S needed alone   | Activity needed alone   | Metal-price factor alone   |
|:---------|-----------:|:-----------------|:------------------------|:---------------------------|
| PDH-001  |     2063.2 | not sufficient   | not sufficient          | not sufficient             |
| PDH-003  |     3181.1 | not sufficient   | not sufficient          | not sufficient             |
| PDH-005  |     2603.6 | not sufficient   | not sufficient          | not sufficient             |
| PDH-008  |     4148.6 | not sufficient   | not sufficient          | not sufficient             |
| PDH-009  |     6275.1 | not sufficient   | not sufficient          | not sufficient             |
| PDH-010  |     1344.7 | not sufficient   | not sufficient          | not sufficient             |
| PDH-012  |     4079.6 | not sufficient   | not sufficient          | not sufficient             |
| PDH-018  |      800.1 | not sufficient   | 2.73x                   | not sufficient             |
| PDH-019  |      891.4 | not sufficient   | 11.47x                  | not sufficient             |
| PDH-020  |     1043.7 | not sufficient   | not sufficient          | not sufficient             |
| PDH-026  |      749.2 | 98.27%           | 3.11x                   | not sufficient             |
| PDH-028  |      754.6 | 97.78%           | 22.89x                  | not sufficient             |
| PDH-042  |      765.5 | 90.55%           | 2.91x                   | not sufficient             |
| PDH-044  |      752.4 | 91.27%           | 1.60x                   | not sufficient             |
| PDH-048  |      786.6 | 91.69%           | 8.19x                   | not sufficient             |
| PDH-051  |      755.3 | 90.66%           | 1.84x                   | not sufficient             |
| PDH-053  |     1164   | 96.98%           | not sufficient          | not sufficient             |

Interpretation:
- PDH-018 can reach the reference with about **2.73× activity**; selectivity alone cannot do it because it is already 96% selective and remains burdened by rate/stability/capital.
- PDH-026 can reach with **98.27% selectivity** or **3.11× activity**.
- PDH-042 can reach with **90.55% selectivity** or **2.91× activity**.
- PDH-044 can reach with **91.27% selectivity** or **1.60× activity**.
- The low-selectivity P01 records cannot reach the reference by changing only selectivity, only activity up to 10,000×, or eliminating metal cost; they need simultaneous gains and/or a different process configuration.
- Catalyst metal price alone does not rescue any above-reference catalyst, confirming that metal purchase is not the industrial bottleneck under recovery.

## 3e. Sensitivity

| scenario               | winner   |   winner_cost |   margin |   reference_cost |
|:-----------------------|:---------|--------------:|---------:|-----------------:|
| central                | PDH-015  |         658.2 |      1.8 |            736.7 |
| low_propane            | PDH-015  |         558.8 |      1.3 |            631.5 |
| high_propane           | PDH-015  |         770.3 |      2.4 |            855.4 |
| low_capex              | PDH-015  |         595.1 |      1.9 |            662   |
| high_capex             | PDH-015  |         752.9 |      1.6 |            848.7 |
| low_energy             | PDH-015  |         640.5 |      1.8 |            717.3 |
| high_energy            | PDH-015  |         695.1 |      1.9 |            777.1 |
| low_Pt                 | PDH-015  |         657.7 |      1.9 |            736.7 |
| high_Pt                | PDH-015  |         659.2 |      1.7 |            736.7 |
| fast_regen_cheap       | PDH-015  |         657.2 |      1.7 |            736.7 |
| slow_regen_costly      | PDH-015  |         661.1 |      2.2 |            736.7 |
| unknown_stability_5h   | PDH-015  |         658.2 |      1.8 |            736.7 |
| unknown_stability_100h | PDH-015  |         658.2 |      1.8 |            736.7 |
| unknown_Pt_01wt        | PDH-015  |         658.2 |      1.8 |            736.7 |
| unknown_Pt_10wt        | PDH-015  |         658.2 |      1.8 |            736.7 |
| life_1y                | PDH-015  |         659.2 |      1.7 |            736.7 |
| life_5y                | PDH-015  |         658   |      1.8 |            736.7 |

PDH-015 remains the winner in all listed one-at-a-time scenarios, but its margin over PDH-017 is only $1.3–2.4/t. The **identity of the top pair is robust; their order is not practically significant**. Propane price moves the reference cost by over $220/t across the tested range, much more than catalyst-metal or regeneration assumptions. The P06 Pt-loading sensitivity does not affect the winner because PDH-015 has a reported 3 wt% Pt loading; it does affect P06 catalyst costs, but not enough to change the top five.

## 4. What the masked data cannot support

1. **No global winner across all 59 records:** 32 selectivities remain masked. Any one of them could combine high selectivity with adequate activity and beat PDH-015.
2. **No bankable lifetime claim:** time-on-stream tests describe short deactivation and often coke accumulation, not multi-year mechanical/chemical life through thousands of regenerations.
3. **No scale-up guarantee:** heat transfer, pellet diffusion, pressure drop, impurities, propylene separation and regenerability are not represented by powder-scale rates.
4. **No firm P06 metal bill:** Pt wt% is missing. The 0.1–1 wt% sensitivity did not change the central winner, but it prevents a precise inventory value for P06.
5. **No by-product credit beyond H2:** methane/ethane/coke were assigned zero credit. Fuel-gas use could modestly lower cost, but low selectivity would still be strongly penalized because propylene yield is lost.

## 5. Decision

**Screening decision:** choose **PDH-015** if forced to choose from the revealed literature data, with PDH-017 as an economically indistinguishable backup and PDH-059 as the most credible long-duration candidate because it reports ~100 h to 10% loss over a 336 h test. Before a plant decision, require cyclic regeneration testing, impurity tolerance, shaped-pellet productivity and at least thousands of hours of cumulative operation. A risk-adjusted owner could rationally retain the commercial reference until those data exist.

**Bottleneck decision:** PDH economics are feedstock/selectivity-led. Research should prioritize propylene selectivity and retained yield under cyclic operation; activity matters when it is low enough to enlarge reactor/catalyst inventory, while precious-metal price is secondary after recovery.

## 6. Reproducibility and files

- `scripts/pdh_analysis.py` — equilibrium/kinetic fit, optimization, costing, attribution, backward design and sensitivity.
- `analysis_record_costs.csv` — all 27 costable records.
- `analysis_rankings.csv` — groupwise lab-versus-plant ranking.
- `analysis_attribution.csv` — record-level one-at-a-time attribution.
- `analysis_backward.csv` — backward-design requirements.
- `analysis_sensitivity.csv` — one-at-a-time scenarios.
- `db/visible.csv`, `db/revealed.csv` — source database views.

## 7. Run time and cost

From `ledger.json` read near completion: **9.5 wall-minutes** and **$3.75 USD-equivalent model cost** at that read. Final file-writing overhead occurred after the read, so these are slightly conservative.
