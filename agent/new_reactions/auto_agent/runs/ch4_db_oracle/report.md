# Thermocatalytic CO2 methanation to synthetic natural gas

**Run date:** 2026-11-10  
**Reaction:** CO2 + 4 H2 -> CH4 + 2 H2O  
**Database:** 255 catalyst-condition records from 8 coded papers

## Executive decision

- **Conditional plant choice among the 118 records that could be costed:** **CH4-036, Ni/TiO2 at 350 C and 1.013 bar lab pressure**, with measured CH4 selectivity 1.000. The optimized modeled plant cost is **$2,756.7/t CH4** at 100,000 t/y. The optimized plant uses a 30 bar reactor, 94.0% per-pass CO2 conversion, about 0.24 t catalyst inventory, and $77.5m installed methanation-island capital.
- **Industrial reference:** **CH4-184, 17 wt% Ni/Al2O3 at 350 C and 10 bar lab pressure**, representing conventional industrial Ni/alumina chemistry. Its modeled plant cost is **$2,791.3/t**, so CH4-036 saves **$34.5/t (1.24%)** in the base case. The explicit commercial catalyst record CH4-187 costs $3,079.6/t because its measured selectivity is only 0.90 under its reported test.
- **Important qualification:** this is not a proof that CH4-036 is best among all 255 records. Selectivity was still masked for 137 records. Giving every masked record the physically best possible selectivity of 1.0 produces a lower-bound winner, CH4-110, at $2,747.9/t. CH4-110 is one of a same-catalyst/same-temperature flow series adjacent to CH4-111, whose revealed selectivity is 0.986; at approximately that measured selectivity it would not beat CH4-036. Thus CH4-036 is the best supported decision, but a small residual ranking risk remains.
- **Bottleneck:** the plant is carried by **hydrogen cost**, not catalyst purchase price or lifetime. At the industrial reference, H2 is 90.0% of total modeled cost, CO2 4.9%, annualized plant capital 5.2%, electricity 0.4%, and direct catalyst cost 0.005% (heat recovery is a credit). Among catalyst properties, **selectivity is the most valuable**, followed by activity; metal price and demonstrated stability barely affect direct $/t in this model, although unmodeled downtime from deactivation could matter.
- **Do paper metrics agree with plant economics?** Only partly. In 9 nontrivial paper/pressure/feed groups evaluated conditionally, the maximum-conversion record disagreed with the cheapest costed plant option in **4/9 groups** (3/9 with regret above $1/t); the measured-productivity leader also disagreed in **4/9**. Mean regret over identity disagreements was **$46.8/t for conversion** and **$54.0/t for productivity**. High conversion/productivity often comes from hotter conditions or more promoted formulations, while the plant values selectivity and the ability to add catalyst/recycle.

## 1. Reveal strategy and budget

### Strategy

The 153-unit reveal budget was allocated where a field could change plant choice or the bottleneck conclusion:

1. **Round 1: 63 selectivities.** Revealed the conversion/rate/kinetic leaders in every comparison group, the best kinetic point of each catalyst, lower-temperature alternatives, the commercial catalyst, and the only 40 bar record.
2. **Round 2: 55 selectivities.** Filled moderate-temperature curves in P01/P02, all P05 points, the 6 and 10 bar industrially relevant P06 points, and 300/350 C neighborhoods in P07.
3. **Round 3: 35 stability cells.** Targeted the selected plant candidates, group leaders, conventional Ni/Al2O3, the commercial catalyst, and likely stability-test conditions.

### Budget result

- Selectivity reveals: **118**
- Stability reveals: **35**
- Total spent: **153/153**
- Usable stability tests found: **2/35**
  - CH4-187 commercial Ni catalyst: conversion 0.52 to 0.46 over 47 h; database extrapolation to 10% loss = 40.7 h.
  - CH4-189 Ni3Fe/Al2O3: conversion 0.71 to 0.70 over 45 h; database extrapolation to 10% loss = 303.5 h.
- The other 33 revealed stability cells contained no reported time-on-stream numbers.

This allocation reflects the plant model: one selectivity point is worth tens of dollars per tonne, while direct catalyst replacement is cents per tonne for ordinary Ni catalysts. Stability remains an evidence limitation because a 45-47 h test cannot establish a multi-year industrial life.

## 2. Plant model

### 2.1 Basis and transparent equations

Plant basis: **100,000 t/y CH4**, **8,000 operating h/y**, common industrial reactor pressure **30 bar**. Product basis is dry methane after water removal.

For each record, the laboratory conversion is not charged directly to the plant. A kinetic coefficient is inferred from the laboratory contact time:

`k_eff,lab = (F_CO2/W) * [-ln(1 - X_lab/X_eq,lab)]`

and converted to a first-order pressure-normalized coefficient:

`k_intrinsic = k_eff,lab / p_CO2,lab`.

At the plant:

`k_eff,plant = k_intrinsic * p_CO2,plant`.

For a trial plant per-pass conversion `x`, catalyst inventory is:

`W = F_CO2,in * [-ln(1 - x/X_eq,plant)] / k_eff,plant`,

where `F_CO2,in = methane production / (selectivity * x)`. This lets a plant add catalyst and recycle rather than treating low laboratory conversion as an immutable plant yield. Equilibrium is calculated from the stoichiometric gas composition with a constant-heat-capacity approximation using delta H = -165 kJ/mol and delta S = -173 J/mol/K. The plant optimizes `x` on a grid up to 97% of equilibrium and no more than 95% absolute conversion.

Feed costs scale as `1/selectivity`: stoichiometric H2 is 0.5026 t/t CH4 and CO2 is 2.7433 t/t CH4 at selectivity 1. The model conservatively treats converted CO2 not appearing as methane as lost feed and gives no CO by-product credit.

Installed capital comprises an $80m balance-of-plant term scaled with gas/recycle throughput to the 0.6 power and a $20m reference reactor term scaled with catalyst inventory to the 0.6 power. Capital is annualized with a 10.19% capital-recovery factor plus 4% fixed O&M. Electricity covers feed compression, recycle and drying. Reaction heat receives a $14.3/t credit. Catalyst inventory includes support/manufacturing, contained metals, capital carrying charge, three-year replacement, and 90% Pt recovery.

### 2.2 Parameter and source table

The detailed machine-readable table is in `sources.csv`.

| Parameter | Base | Range / treatment | Source status |
|---|---:|---:|---|
| H2 | $5.00/kg | $2-7/kg | DOE H2NEW/current electrolysis-cost context; DOE Hydrogen Shot for target context |
| CO2 delivered | $50/t | $20-150/t | Assumption informed by IEA capture-cost discussion |
| Industrial electricity | $86.2/MWh | $50-120/MWh | U.S. EIA, Sep. 2025 industrial price 8.62 cents/kWh |
| Installed methanation island | $100m | $50-150m | Assumption informed by Danish Energy Agency technology data |
| Plant | 100,000 t/y, 8,000 h/y | fixed basis | Assumption |
| CRF / fixed O&M | 10.19% / 4% | capital range carries uncertainty | 20 y, 8% real WACC assumption |
| Catalyst life | 3 y | 1-5 y; x10 perturbation | Assumption; database tests insufficient |
| Catalyst nonmetal portion | $20/kg | $10-50/kg | Assumption |
| Ni | $15.2/kg | market-sensitive | USGS 2026 MCS, 2025 average $6.88/lb |
| Pt | $45,900/kg | market-sensitive | USGS 2026 MCS, 2025 average $1,427/oz |
| Heat credit | $14.3/t CH4 | $0-30/t | Assumption: 50% heat recovery at $10/MWhth |

Other metal-price assumptions are listed in `sources.csv` and were tested by multiplying total catalyst cost by ten.

### 2.3 Industrial check

The industrial-reference cost of **$2,791/t CH4** is **$181/MWh CH4** or approximately **$50/MMBtu**, inside the located review range of roughly **$45-76/MMBtu** for synthetic methane. The Audi e-gas demonstration (6 MW electrolysis, about 1,000 t/y methane) is a scale check, not a cost calibration. The model's 30 bar, Ni-based fixed-bed reference is within published industrial methanation operating envelopes.

## 3. Results

### 3a. Plant cost of records

**118/255 records** had revealed selectivity and were fully costed. Full results are in `db/costed_records.csv`.

Top supported choices:

| Rank | Record | Catalyst | Lab T / P | Selectivity | Plant cost, $/t | Opt. conversion | Catalyst inventory |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | CH4-036 | Ni/TiO2 | 350 C / 1.013 bar | 1.000 | 2,756.7 | 0.940 | 0.24 t |
| 2 | CH4-074 | CeAlOx/Ni/Ni-foam | 280 C / 1 bar | 1.000 | 2,757.0 | 0.945 | 0.26 t |
| 3 | CH4-042 | NiMn(2:1)/TiO2 | 300 C / 1.013 bar | 1.000 | 2,759.2 | 0.940 | 0.31 t |
| 4 | CH4-037 | Ni/TiO2 | 375 C / 1.013 bar | 0.996 | 2,764.6 | 0.947 | 0.14 t |
| 5 | CH4-035 | Ni/TiO2 | 325 C / 1.013 bar | 1.000 | 2,765.5 | 0.920 | 0.44 t |

Best by paper among costed records:

| Paper | Record | Cost, $/t |
|---|---|---:|
| P01 | CH4-017 | 2,781.4 |
| P02 | CH4-036 | 2,756.7 |
| P03 | CH4-074 | 2,757.0 |
| P04 | CH4-120 | 2,781.6 |
| P05 | CH4-158 | 2,827.5 |
| P06 | CH4-184 | 2,791.3 |
| P07 | CH4-204 | 2,782.6 |
| P08 | CH4-255 | 3,695.0 |

For the 137 records with masked selectivity, no single point cost is reported. `db/all_S1_bound.csv` gives an intentionally optimistic lower bound by assigning selectivity 1.0. This is not a prediction; it identifies where masked data could still change the decision.

P08 is especially uncertain: CH4-255 was measured in a batch autoclave with liquid cyclohexane and non-stoichiometric 4 MPa CO2 + 4 MPa H2. Scaling that record with the same gas-phase first-order law is only a screening calculation, not a bankable plant design.

### 3b. Paper ranking versus plant ranking

Comparison groups are same paper, pressure and feed. Trivial one-catalyst groups are excluded. Results are conditional on the revealed/costed candidates; denominators and coverage are in `db/group_comparisons.csv`.

- **Conversion leader:** 4 disagreements in 9 nontrivial groups; 3/9 have regret above $1/t. All four identity disagreements selected another catalyst, although P04 is an economic tie (~$0.00003/t).
- **Productivity leader:** 4 disagreements in 9 groups. Three selected another catalyst; one selected the same catalyst at another temperature.
- **Mean regret among identity disagreements:** $46.8/t for conversion, $54.0/t for productivity.
- **Largest regret:** $88.2/t in P07, where the 400 C high-Pt loading metric leader loses to CH4-204 at 350 C with only 0.03% Pt and higher selectivity.

Material examples:

| Group | Cheapest plant record | Lab-metric choice | Type | Regret, $/t |
|---|---|---|---|---:|
| P01, 1.013 bar | CH4-017 | CH4-025 | other catalyst | 58.2 |
| P02, 1.013 bar | CH4-036 | CH4-063 | other catalyst | 41.1 |
| P03, 1 bar, productivity | CH4-074 | CH4-111 | same catalyst, other T | 28.7 |
| P07, 1 bar | CH4-204 | CH4-226/254 | other catalyst | 88.2 |

Interpretation: laboratory conversion and productivity conflate kinetic activity, equilibrium, residence time and temperature. A plant can compensate for activity with more catalyst and recycle; it cannot cheaply compensate for lost selectivity because every lost point wastes expensive H2.

### 3c. Bottleneck and attribution

Industrial reference CH4-184 cost breakdown:

| Component | $/t CH4 | Share of gross modeled total |
|---|---:|---:|
| H2 | 2,513.25 | 90.04% |
| CO2 | 137.16 | 4.91% |
| Annualized capital + fixed O&M | 143.87 | 5.15% |
| Electricity | 11.19 | 0.40% |
| Catalyst | 0.13 | 0.005% |
| Heat credit | -14.30 | credit |
| **Total** | **2,791.29** | |

Perturbations at the reference:

- **+1 selectivity point:** about **-$26.8/t** for a 0.99 to 1.00 improvement. Selectivity is bounded at 1, so this is a near-reference marginal value.
- **2x activity:** approximately **-$15.6/t**, mainly through a smaller reactor; re-optimization can change this slightly.
- **10x stability/lifetime:** approximately **-$0.09/t** in direct catalyst replacement.
- **H2 +$0.10/kg:** **+$50.3/t**.

Thus the non-catalyst bottleneck is unequivocally **low-cost hydrogen**. The catalyst bottleneck is **selectivity**, then activity/reactor size. Metal cost and direct replacement life are economically negligible for ordinary Ni catalysts at this productivity. Stability could still dominate availability if it forces shutdowns or regeneration, but the database does not contain enough duration/regeneration data to quantify that pathway.

One-at-a-time record-level attribution relative to CH4-184 is saved in `db/oat_attribution.csv`. It separately replaces selectivity, intrinsic activity, temperature metallurgy factor, stability assumption and metal cost with the reference value at each record's optimized operating point. These OAT terms are deliberately non-additive; an interaction residual is retained. Examples:

- CH4-036's $34.5/t advantage is almost entirely activity/reactor-capital benefit; selectivity is tied at 1.0.
- CH4-204 loses $26.8/t of feed value from 0.99 selectivity versus the reference but recovers about $35/t through higher inferred activity/smaller capital.
- CH4-187's $288/t disadvantage is approximately $294/t of extra H2+CO2, partly offset by slightly lower capital.
- CH4-255's $904/t disadvantage is primarily reactor capital from low screened activity, plus a $60/t selectivity/feed penalty.

### 3d. Backward design

Target = industrial reference CH4-184 at **$2,791.3/t**.

- P01 CH4-017, P02 CH4-036, P03 CH4-074, P04 CH4-120 and P07 CH4-204 already meet the modeled target under the common three-year-life assumption.
- P05 CH4-158 would need selectivity to rise from **0.980 to about 0.993** at unchanged activity/capital.
- Commercial CH4-187 would need selectivity to rise from **0.900 to about 0.998** at unchanged activity/capital.
- P08 CH4-255 cannot reach the target by selectivity alone; the formal requirement is an impossible **1.47**. Infinite activity at its current selectivity still leaves a lower bound near **$2,890/t** because of feed loss and high-throughput balance-of-plant. It needs both near-unity selectivity and a different, much more productive/scale-compatible process; its batch-liquid test is not directly transferable.
- Reducing ordinary Ni catalyst price does not materially help any record. Even a tenfold catalyst-cost change did not change the winner.

### 3e. One-at-a-time sensitivity

| Scenario | Winner | Winner cost, $/t | Gap vs CH4-184 |
|---|---|---:|---:|
| Base | CH4-036 | 2,756.7 | -34.5 |
| H2 $2/kg | CH4-036 | 1,248.8 | -34.5 |
| H2 $7/kg | CH4-036 | 3,762.0 | -34.5 |
| CO2 $20/t | CH4-036 | 2,674.4 | -34.5 |
| CO2 $150/t | CH4-036 | 3,031.1 | -34.5 |
| Capital 0.5x | CH4-036 | 2,701.8 | -17.6 |
| Capital 1.5x | CH4-036 | 2,811.7 | -51.5 |
| Electricity $50/MWh | CH4-036 | 2,752.3 | -34.3 |
| Electricity $120/MWh | CH4-036 | 2,760.9 | -34.7 |
| Catalyst cost 10x | CH4-036 | 2,756.9 | -35.5 |

The winner is stable across these one-at-a-time uncertainties among the 118 costed records. CH4-074 remains within $0.3/t of CH4-036, so the exact order of those two should not be treated as practically significant. Capital uncertainty changes the size, but not the sign, of the advantage over conventional Ni/Al2O3. The absolute SNG cost remains extremely sensitive to H2 price.

## 4. What the masked data cannot support

1. **Global winner:** 137 selectivities remain masked. The optimistic-selectivity bound shows that several masked records could mathematically beat CH4-036 by up to $8.8/t. Neighboring revealed selectivities make some of these bounds unlikely, but not impossible.
2. **Complete productivity ranking:** product productivity requires selectivity. Rankings are therefore only complete within the 118 revealed records, though all group conversion leaders were explicitly revealed.
3. **Industrial lifetime:** only two usable tests were found, both shorter than 50 h. No multi-year life, regeneration schedule, sulfur tolerance, thermal-cycle resistance or water/impurity tolerance can be inferred.
4. **Availability/regeneration cost:** the direct catalyst replacement calculation is robustly small, but plant downtime could be expensive. It was not invented in the absence of data.
5. **Batch-to-flow transfer:** P08 cannot be reliably scaled to a commercial gas-phase fixed bed from the available batch-liquid record.
6. **Support and shaping:** pressure drop, pellet strength, heat-transfer limits and hot-spot control are not in the database. They could overturn a small modeled advantage such as the $0.3/t difference between CH4-036 and CH4-074.

## 5. Files produced

- `report.md` — this report
- `sources.csv` — parameter/source table
- `db/costed_records.csv` — 118 fully costed records
- `db/group_comparisons.csv` — paper-metric versus plant comparisons
- `db/oat_attribution.csv` — record-level one-at-a-time attribution
- `db/all_S1_bound.csv` — optimistic bound for masked selectivity
- `db/group_bounds.csv` — group results under that bound
- `scripts/model_py.py` — plant model and optimizer
- `scripts/attribution_py.py` — attribution calculation
- `scripts/sensitivity_py.py` and supporting scripts — sensitivity and diagnostics

## 6. Run time and cost

Ledger read at 2026-11-10T21:47:56: **10.1 wall-clock minutes** and **$5.06 USD equivalent at GPT-5.5 list price**. The ledger recorded 890,626 total tokens, 25 agent calls, 33.8 s Python tool time, and the full 153-unit reveal budget spent.
