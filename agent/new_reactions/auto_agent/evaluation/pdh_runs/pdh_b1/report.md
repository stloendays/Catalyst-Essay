# Non-oxidative propane dehydrogenation (PDH) catalyst-to-plant ranking analysis

Reaction: **C3H8 -> C3H6 + H2**.  The objective was not to copy any techno-economic study cost, but to build a transparent plant-cost model from open literature catalyst records and sourced/explicitly assumed plant parameters, then ask whether laboratory catalyst rankings predict the catalyst/condition a plant would choose.

## 1. Literature search, screening and extraction

### Screening criteria

Included papers had to be original experimental heterogeneous-catalyst studies for direct/non-oxidative PDH in an oxygen-free feed, with enough quantitative data to identify the catalyst/composition and extract temperature, pressure or a reasonable atmospheric assumption, propane conversion, propylene selectivity, and productivity or the flow/mass data needed to calculate productivity.  Inert, H2, steam or dilution were allowed if they were not oxidants.  CO2/O2/N2O/chemical-looping/soft-oxidant studies, reviews, theory-only papers, and papers without usable quantitative performance were excluded.

### Download/OCR/extraction outcome

- Screened candidates: 46.
- Included by title/abstract: 21.
- Download attempts under the cap: 20 DOI requests; 19 PDFs obtained and OCR parsed; one CrOx/nanocast alumina paper failed to download.
- Extracted records: 260 total records from 19 parsed papers.
- Usable records after unit/plausibility gates: **125 records from 16 papers**.
- Three records were rejected by a plausibility gate for impossible printed/productivity units above 50 kg product kg-cat^-1 h^-1.

| Paper key | Topic/catalyst family | extracted records | usable records | main reason unusable records failed |
|---|---:|---:|---:|---|
| 10.1002/anie.201404460 | Pt-promoted Ga/Al2O3 | 31 | 31 | none |
| 10.1002/anie.201701115 | Pt-Sn atom-trapping clusters | 6 | 0 | missing rate or flow+mass |
| 10.1021/acscatal.0c01580 | Zn-containing ZrO2-based catalysts | 42 | 13 | selectivity missing in many records |
| 10.1021/acscatal.1c05778 | ZnOx/silicalite-1 durability | 37 | 1 | selectivity missing in many records |
| 10.1021/acscatal.2c01631 | isolated PtZn4 sites | 27 | 6 | selectivity missing in many records |
| 10.1021/acscatal.6b01286 | Fe/P/Al2O3 | 12 | 12 | none |
| 10.1021/acscatal.9b00549 | Pt-Co intermetallic | 19 | 0 | missing rate or flow+mass |
| 10.1021/acscatal.9b02459 | Ga-Rh liquid-metal catalyst | 5 | 4 | missing rate or flow+mass |
| 10.1021/jacs.1c10261 | isolated Pt atoms in SiOZn nests | 10 | 4 | missing rate or flow+mass |
| 10.1021/jacs.2c05618 | Pt2Mn nanoparticles | 8 | 6 | missing rate or flow+mass |
| 10.1021/jacs.8b05378 | silica-supported Ga-Pt nanoparticles | 8 | 8 | none |
| 10.1038/s41467-020-16693-9 | single-atom Pt/intermetallics | 6 | 3 | selectivity missing in some records |
| 10.1038/s41467-022-35698-0 | tetrahedral Co(II)/silica | 2 | 2 | none |
| 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 14 | 11 | selectivity missing in some records |
| 10.1038/s41586-021-03923-3 | ZnOx in-situ formation | 6 | 2 | selectivity missing in some records |
| 10.1039/c6ra27204e | Ga2O3-supported catalysts | 17 | 17 | none |
| 10.1039/c6sc05178b | isolated Ga/silica | 1 | 1 | none |
| 10.1039/c9sc05599a | Pt-Zn/silica | 4 | 4 | none |
| 10.1126/sciadv.adi8219 | microwave-assisted PDH | 5 | 0 | conversion missing |

### Excluded paper classes

Most explicit exclusions were oxidative or CO2-assisted PDH, chemical-looping oxidative PDH, reviews, and theory-only studies.  Examples include 10.1021/acscatal.0c03999, 10.1021/acscatal.7b03805, 10.1038/s41467-023-37818-w, 10.1038/s41929-021-00730-x, 10.1038/s41467-022-32842-8, 10.1039/d1gc03700e and related ODH/review papers.  The exclusion is important: an oxidative catalyst may look superior in conversion or coke resistance because oxygen/CO2 changes the thermodynamics and heat balance, but that is not the direct PDH plant considered here.

## 2. Mechanism and kinetic transfer model

The plant model treats direct PDH as a reversible endothermic reaction limited by approach to equilibrium:

\[
Q = \frac{p_{C3H6}p_{H2}}{p_{C3H8}}, \quad r_{net} \propto 1-Q/K_p(T)
\]

For each literature record, the extracted productivity `r` calibrates an apparent catalyst productivity at its reported temperature, pressure, feed dilution and conversion.  The industrial reactor is then allowed to choose a different per-pass conversion, and productivity is scaled by the ratio of approach-to-equilibrium plug-flow integrals:

\[
r_{plant}(X) = r_{lab}\,\frac{X/I(X,T,P,y_{C3H8}=1)}{X_{lab}/I(X_{lab},T_{lab},P_{lab},y_{lab})}
\]

This is deliberately more conservative than ranking by the reported single-point rate: it penalizes pushing close to equilibrium and prevents high laboratory conversion obtained with strong dilution from being directly credited to an undiluted industrial recycle reactor.  Propylene selectivity is held at the extracted value; there was insufficient consistent evidence across all papers to fit conversion-dependent selectivity or coke kinetics.  Deactivation is represented only through the extracted time to 10% activity loss when available; otherwise a default cyclic-regeneration interval is assumed.

## 3. Reactor and flowsheet representation

The modeled plant is a low-pressure, high-temperature PDH process with:

- reactor heat duty for the endothermic reaction;
- sensible preheat and partial heat recovery;
- unreacted propane recycle;
- C3/lights separation and recycle compression/refrigeration;
- catalyst inventory, regeneration and eventual replacement;
- installed capital scaled by capacity, recycle flow and catalyst inventory;
- no propylene revenue credit, because the metric is production cost per tonne of propylene.

The reactor free variable is **per-pass propane conversion**.  The model optimizes it for every catalyst record.  High conversion lowers recycle/separation capital and energy but approaches equilibrium and lowers effective productivity; low conversion preserves rate but increases recycle.  This optimization is the main reason laboratory conversion alone performs poorly as a plant-ranking metric.

## 4. Parameter table and provenance

The machine-readable parameter table is `sources.csv`.  It contains 38 rows: 4 published values, 1 measured literature normalization value, and 33 engineering assumptions with low/high ranges for sensitivity.  Public literature did not provide enough consistent open data to make all plant parameters measured values, so uncertain economic and design quantities were explicitly marked as assumptions rather than disguised as sourced numbers.

Key parameters are summarized below; the full table in `sources.csv` gives source, exact location and low/high ranges.

| Parameter | Base value | Unit | Type | Source/location |
|---|---:|---|---|---|
| MW_C3H8 | 44.096 | g/mol | published | NIST WebBook propane page |
| MW_C3H6 | 42.080 | g/mol | published | NIST WebBook propene page |
| PDH reaction enthalpy | 124.3 | kJ/mol C3H6 | published | 10.1039/D1GC03700E thermodynamics section |
| Kp at 873 K | 0.42 | dimensionless | assumption | equilibrium calibration; low/high 0.18/0.75 |
| plant capacity | 600,000 | t/y | assumption | world-scale single-train basis; low/high 350,000/900,000 |
| operating hours | 8,000 | h/y | assumption | low/high 7,600/8,400 |
| propane price | 520 | USD/t | assumption | low/high 300/900 |
| natural gas price | 5.0 | USD/GJ | assumption | low/high 3/10 |
| electricity price | 70 | USD/MWh | assumption | low/high 45/120 |
| installed capex | 720 million | USD | assumption | low/high 450 million/1.2 billion |
| capital recovery factor | 0.12 | 1/y | assumption | low/high 0.08/0.18 |
| base separation heat | 0.9 | GJ/t | assumption | low/high 0.5/1.8 |
| base electricity | 80 | kWh/t | assumption | low/high 40/160 |
| catalyst makeup life | 24,000 | h | assumption | low/high 12,000/40,000 |
| default cycle time | 720 | h | assumption | low/high 24/2,000 |

## 5. Reference plant cost from the model

Reference catalyst record: Oleflex-like Pt-Sn/Al2O3, 873.15 K, 1.5 bar, lab conversion 0.42, selectivity 0.95, productivity 2.5 kg C3H6 kg-cat^-1 h^-1, 720 h default cycle.

The optimized reference plant cost is **813.48 USD/t propylene**.

| Cost part | USD/t C3H6 | Share |
|---|---:|---:|
| propane feed | 573.59 | 70.5% |
| energy | 31.38 | 3.9% |
| capital + fixed O&M | 184.98 | 22.7% |
| catalyst/regeneration | 3.53 | 0.4% |
| other variable | 20.00 | 2.5% |
| **total** | **813.48** | **100%** |

Reference optimized operation: 873.15 K, 1.5 bar, **0.4396 per-pass conversion**.  Balances: propane feed 1.102 t/t propylene, primary purchased energy 6.21 GJ/t, installed capital about 716 million USD at 600 kt/y.

The dominant term is feedstock.  Therefore selectivity has an amplified plant value: every lost mole of propylene selectivity buys extra propane.  By contrast, very high activity mainly reduces catalyst inventory/reactor increment and has a smaller effect once separation and feed dominate.

## 6. Literature catalyst plant ranking

The model-costed 125 usable records.  The cheapest operating point was:

- **Pt/In-ZSM-5**, 10.1038/s41467-024-50709-y, 550 °C, extracted X = 0.20, S = 0.998, r = 30.63 kg kg-cat^-1 h^-1.
- Model cost: **774.86 USD/t propylene**.
- Main cost terms: feed 546.00, capital 176.73, catalyst 1.15 USD/t; optimized per-pass conversion 0.450.

There were **25 records below the reference plant cost**.  The top cluster consisted of very high-selectivity Pt/In-ZSM-5 and high-selectivity/high-productivity PtGa/PtGa-Pb/PtSn-type records.  Low-selectivity or low-productivity Fe/P and Ga2O3 records became very expensive even when their laboratory conversions were respectable.

### Does laboratory ranking predict plant choice?

Only partially.  Ranking changes were frequent:

| Lab ranking metric | Level | groups/papers compared | changed | fraction changed | 95% bootstrap CI | median regret among changed cases |
|---|---|---:|---:|---:|---:|---:|
| productivity | operating-point | 14 | 6 | 0.4286 | 0.2143-0.7143 | 0.6199 |
| productivity | catalyst-level | 13 | 6 | 0.4615 | 0.2308-0.7692 | 0.6199 |
| conversion | operating-point | 14 | 10 | 0.7143 | 0.5000-0.9286 | 0.0239 |
| conversion | catalyst-level | 13 | 5 | 0.3846 | 0.1538-0.6923 | 0.9346 |
| selectivity | operating-point | 14 | 5 | 0.3571 | 0.1429-0.6429 | 0.9677 |
| selectivity | catalyst-level | 13 | 5 | 0.3846 | 0.1538-0.6923 | 0.9677 |

The poorest predictor was single-pass laboratory conversion at the operating-point level: **10 of 14 comparisons changed**.  Five of these were the same catalyst at another temperature, showing that simply choosing the hottest/highest-conversion point can be wrong after recycle, equilibrium approach and energy/capital tradeoffs are included.  Productivity and selectivity were better, but still failed in about 36-46% of catalyst-level comparisons because the plant objective combines feed loss, recycle, capital and deactivation.

## 7. Why rankings change

### Feedstock cost amplifies selectivity

The reference cost is feed-dominated.  The model gives **-6.86 USD/t for +1 percentage point selectivity** at the reference catalyst.  A 1-point selectivity loss is therefore economically larger than many changes in catalyst metal cost.  This is why high-selectivity Pt/In-ZSM-5 and PtGa/PtGa-Pb records rise to the top even when another record has higher conversion.

### Activity is important, but attenuated by the flowsheet

A factor-of-two activity increase at the reference reduces cost by only **3.15 USD/t**.  The reason is that activity mainly changes catalyst mass, reactor increment and catalyst replacement.  It does not halve feedstock cost, and it does not eliminate the need for C3 separation/recycle.  Across the full data set, activity still matters because some records have extremely low productivity and enormous catalyst inventory; however, once activity reaches a few kg kg-cat^-1 h^-1, the marginal value of further rate is much smaller than selectivity.

### Conversion is attenuated by equilibrium and recycle optimization

High laboratory conversion often reflects dilution, high temperature, or operation close to equilibrium.  The plant can choose per-pass conversion; it is not forced to operate at the reported laboratory conversion.  Low per-pass conversion increases recycle and capital, but high per-pass conversion reduces net rate near equilibrium.  The optimizer usually settles around 0.45-0.58 for the best high-temperature records.  Therefore, laboratory conversion is not a robust economic ranking metric.

### Temperature has mixed effects

Higher temperature improves equilibrium and often activity, but raises sensible/reaction heat duty and can lower selectivity or stability.  The attribution share assigned to temperature was only **0.062**, because most temperature benefit is already embedded in the reported activity/selectivity, and the plant can trade conversion against recycle.

### Stability matters, but data are inconsistent

The attribution share for stability was **0.170**.  This is meaningful, but less certain than selectivity/activity because many papers either did not report comparable deactivation or reported short tests under different pretreatments/regeneration conditions.  The model therefore uses reported time-to-10%-loss when extractable and a default otherwise.

### Metal cost is small in this model

Metal attribution was **0.011**.  Even Pt, Rh or In cost is diluted over high productivity and multi-year life.  Metal matters for inventory cash and supply risk, but in the modeled production-cost metric it is far below feedstock and installed capital.

## 8. Sensitivity to uncertain parameters

A separate sensitivity run varied major assumed parameters over the low/high ranges in `sources.csv`.  The reference cost is most sensitive to propane price and installed capital:

| Case | Reference cost (USD/t) | Top high-S/high-r class in sensitivity run |
|---|---:|---|
| base | 813.48 | Pt/In-ZSM-5 / PtGa-Pb top cluster |
| propane price low, 300 USD/t | 570.81 | high-selectivity Pt cluster remains best |
| propane price high, 900 USD/t | 1232.64 | high-selectivity Pt cluster remains best |
| base capex low, 450 MUSD | 745.15 | high-selectivity Pt cluster remains best |
| base capex high, 1.2 BUSD | 934.95 | high-selectivity Pt cluster remains best |
| equilibrium Kp low | 846.03 | high-selectivity/high-activity Pt cluster remains best |
| equilibrium Kp high | 798.20 | high-selectivity/high-activity Pt cluster remains best |
| Pt metal price high | 815.22 | high-selectivity/high-activity Pt cluster remains best |

The exact first-ranked record can switch within the leading Pt/In-ZSM-5, PtGa-Pb/PtGa/PtSn family depending on parsing of metal loadings and parameter extremes, but the main conclusion was robust: **plant choice is controlled primarily by selectivity and adequate activity, not by maximum laboratory conversion or cheapest metal**.

## 9. What the evidence could not support

1. **No universal kinetic law across catalysts.**  The literature records use different feeds, dilutions, contact times and reporting conventions.  A single mechanistic microkinetic model for Pt, Ga, Zn, Fe, Co and Cr families was not supportable from the extracted data.
2. **No reliable selectivity-vs-conversion model.**  Many papers report only one or a few points; side-product distributions are inconsistent.  Selectivity was therefore held at the reported value.
3. **Deactivation and regeneration are not standardized.**  Some papers report hours-on-stream, others regeneration cycles, others only fresh performance.  Stability attribution is useful directionally but less certain than selectivity/activity.
4. **Commercial PDH capital and utility data are not fully public.**  Many process parameters had to be explicit assumptions with ranges.  The ranking conclusion survived broad economic sensitivity, but absolute USD/t should be treated as a model estimate, not a quoted plant cost.
5. **Hydrogen credit was not monetized.**  The model charges PDH production cost and does not subtract byproduct H2 value.  If H2 were credited, absolute costs would fall, but catalyst ranking would change little unless catalyst choice changed H2 purity/recovery or side-product hydrogen consumption.

## 10. Bottom-line answer

The laboratory ranking does **not** reliably predict the plant choice.  It is especially unsafe to rank by conversion: operating-point conversion rankings changed in 10/14 comparisons.  Productivity and selectivity are better but still incomplete.  The plant prefers catalysts that combine **very high propylene selectivity** with **sufficient productivity** under conditions that allow an economical per-pass conversion below the equilibrium cliff.  In this data set the best plant-cost records are high-selectivity Pt/In-ZSM-5 and Pt-Ga/Pt-Ga-Pb/Pt-Sn-like catalysts, not necessarily the records with the highest reported laboratory conversion.

The controlling property is **propylene selectivity**, closely followed by **activity once low-activity records are included**.  Feedstock cost makes selectivity economically dominant; equilibrium/recycle/separation attenuate the value of laboratory conversion; capital and catalyst inventory attenuate the value of activity at high rates; metal price is a minor production-cost term.
