# Non-oxidative propane dehydrogenation (PDH) catalyst-to-plant ranking

Reaction modelled: **C3H8 -> C3H6 + H2**.  Files written in this run: `candidates.csv`, `records.csv`, `flowsheet.json`, `flowsheet.md`, `sources.csv`, `model.py`, `costs.csv`, `analysis.json`, `sensitivity.csv`.

## 1. Literature search, screening, and usable data

Searches targeted open-access experimental papers on direct/non-oxidative propane dehydrogenation with catalyst identity, temperature, pressure/feed composition, propane conversion, propylene selectivity, and activity/productivity or enough flow/WHSV information to infer productivity.  Excluded: reviews, computational-only papers, oxidative dehydrogenation with O2/CO2/N2O/halogens/lattice oxygen, chemical looping, non-propane feeds, and papers without enough quantitative performance data.

Screening result: 34 candidate papers, 18 included by title/abstract, 16 PDFs downloaded/OCRed, 92 usable records from 14 papers after extraction gates.  Two included Elsevier PDFs could not be downloaded automatically, and two downloaded papers did not provide usable non-oxidative PDH records under the extraction schema.

### Included papers with usable records

| DOI / paper key | Catalyst family | Records | Usable | Main missing field among rejected records |
|---|---:|---:|---:|---|
| 10.1021/acscatal.0c01580 | Zn/ZrO2 and doped zirconia | 37 | 12 | selectivity |
| 10.1021/acscatal.1c05778 | ZnO/silicalite-1 with Mg | 21 | 1 | selectivity |
| 10.1021/acscatal.2c01631 | isolated PtZn sites in self-pillared zeolite | 21 | 4 | selectivity |
| 10.1021/acscatal.6b01286 | Fe/P/Al2O3 | 11 | 11 | none |
| 10.1021/acscatal.9b02459 | Ga-Rh SCALMS | 4 | 4 | none |
| 10.1021/jacs.2c05618 | Pt-Mn/SiO2 | 8 | 6 | rate or flow+mass |
| 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 14 | 11 | selectivity |
| 10.1038/s41467-024-52518-9 | PtZn/SiO2 intermetallic/alloy | 14 | 14 | none |
| 10.1038/s41467-025-61182-6 | Pt@Sn-MFI / MFI defect catalysts | 11 | 8 | conversion |
| 10.1038/s41586-021-03923-3 | ZnOx/silicalite | 9 | 2 | selectivity |
| 10.1039/c9sc05599a | Pt-Zn/SiO2 | 4 | 4 | none |
| 10.1039/d1sc05866e | In-CHA | 8 | 1 | selectivity |
| 10.1039/d2sc03723h | PtCu single-atom alloys | 5 | 5 | none |
| 10.1039/d3sc04310j | PtSnCa/Al2O3 | 9 | 9 | none |

### Exclusions and why

Representative excluded candidates: ODH with soft oxidants/reviews (10.1021/acscatal.0c03999), CO2-assisted ODH (10.1021/acscatal.7b03805), chemical-looping ODH (10.1038/s41467-023-37818-w), oxidative vanadia/BN/NiOOH/CO2 co-conversion papers, and reviews such as 10.1039/d1gc03700e.  10.1126/sciadv.adi8219 was downloaded and parsed but yielded no usable record because conversion was not extractable in the required form.  10.1002/anie.202319887 was downloaded and parsed but yielded zero usable extracted records.  10.1016/j.fmre.2022.08.020 and 10.1016/j.apcata.2015.03.020 were not costed because the PDFs could not be downloaded through the automated routes in this run.

## 2. Mechanism and kinetics transfer

The plant model treats the extracted laboratory productivity `r` as an apparent productivity at the reported catalyst temperature and pressure, but it does **not** allow arbitrary conversion.  PDH is endothermic and equilibrium-limited; therefore the plant per-pass conversion is optimized but capped below the ideal-gas equilibrium conversion calculated from NIST-derived reaction enthalpy and entropy.

The productivity transfer is an approach-to-equilibrium plug-flow correction.  For pure-propane feed, the model uses

`Kp(T) = exp(DeltaS/R - DeltaH/RT)` and `Kp = P Xeq^2/(1-Xeq^2)`.

For a candidate operating conversion `X`, the apparent productivity is scaled by `(X/I(X))/(Xlab/I(Xlab))`, where `I(X)=integral dX/(1-Q/K)`.  This penalizes operation near equilibrium and prevents a catalyst tested at high conversion from being extrapolated as if the driving force were unchanged.

Deactivation is represented as a regeneration/capital severity penalty from extracted `t_cycle_h` where available.  Missing stability data default to a 24 h industrial regeneration basis and a 3 year catalyst replacement life.  This is deliberately conservative: the open literature often reports short tests that are insufficient to establish true industrial catalyst life.

## 3. Reactor and flowsheet

Submitted flowsheet hash accepted by the checker: `9aa916915d6cb563`.

The flowsheet is a continuous fixed-bed/moving-bed style PDH process with recycle and periodic catalyst regeneration allowance:

1. fresh propane pressurisation;
2. propane recycle mixing;
3. feed vaporisation;
4. feed-effluent heat exchange;
5. fired charge furnace;
6. endothermic PDH reactor;
7. catalyst regenerator allowance;
8. effluent cooler/knockout;
9. product compression;
10. hydrogen recovery;
11. C3 splitter for propylene product and propane recycle;
12. utilities/offsites.

Important inclusions: heat recovery, endothermic reactor heat, product compression, H2 separation, C3 distillation/recycle, regeneration/spare-capital penalty, offsites, hydrogen co-product credit.  Selectivity loss is treated as a propane-equivalent C3 purge/byproduct so that feed cost and carbon loss are counted while staying within the species with fixed thermochemistry used by the checker.

## 4. Plant parameters

The full parameter/source table is in `sources.csv`.  Key central values are:

| Parameter | Central value | Basis |
|---|---:|---|
| Capacity | 750,000 t/y propylene | representative world-scale PDH train; Enterprise/Honeywell-style capacity basis |
| Onstream time | 8000 h/y | assumption |
| Propane price | 390 USD/t | EIA Mont Belvieu propane converted from USD/gal |
| Natural gas | 5.0 USD/GJ | EIA industrial gas price converted to GJ |
| Industrial electricity | 0.080 USD/kWh | EIA industrial electricity price |
| Installed capex | 1.2 billion USD | assumption, 0.9-1.8 billion sensitivity |
| Capital recovery factor | 0.117 1/y | 20 y, 10% annuity assumption |
| Furnace efficiency | 0.88 | assumption |
| Heat recovery | 75% of sensible feed preheat | assumption |
| Reaction enthalpy | 124.3 kJ/mol propylene | NIST formation enthalpies |
| Reaction entropy | 126.5 J/mol/K | NIST molar entropies |
| C3 splitter energy | 0.025 GJ/kmol C3 feed | assumption, scaled with recycle |
| H2 credit | 1.5 USD/kg H2 | assumption |
| Catalyst support/manufacturing price | 20 USD/kg before metal value | assumption |

All assumptions in `sources.csv` have low/high bounds used for sensitivity checks.  The model uses only costs generated by `model.py`; no literature techno-economic cost is copied as a result.

## 5. Reference plant result

The independent checker passed on all 92 usable records.  Reference plant: 750 kt/y continuous PDH at 873.15 K, 1.5 bar, reference Pt-Sn/Al2O3 record, optimized per-pass conversion 0.276.

| Cost component | USD/t propylene |
|---|---:|
| Propane feed | 454.09 |
| Purchased energy | 69.40 |
| Capital + fixed O&M | 308.78 |
| Catalyst/regeneration | 6.54 |
| H2 credit / other | -71.86 |
| **Total** | **766.95** |

Largest reference cost component is feed.  Energy is smaller because reaction heat is only about 3 GJ/t propylene and the model includes heat recovery; capital remains large because PDH requires large recycle/separation/reactor systems at equilibrium-limited single-pass conversion.

## 6. Which catalyst/condition would the plant choose?

Lowest-cost literature operating point among the 92 usable records:

| Rank | Paper | Catalyst | T (K) | Lab X | Lab S | Lab r kg C3H6/kgcat/h | Plant X per pass | Cost USD/t |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 10.1038/s41467-024-52518-9 | PtZn1.4/SiO2 | 873.15 | 0.520 | 0.990 | 3.93 | 0.324 | 667.55 |
| 2 | 10.1039/d3sc04310j | PtSn3Ca5/Al2O3 | 873.00 | 0.520 | 0.960 | 14.06 | 0.323 | 672.32 |
| 3 | 10.1039/d3sc04310j | PtSn3Ca5/Al2O3 | 873.00 | 0.500 | 0.960 | 13.52 | 0.323 | 672.62 |
| 4 | 10.1039/d3sc04310j | PtSn3Ca5/Al2O3 | 873.00 | 0.490-0.520 | 0.950-0.960 | 13.25-13.91 | 0.323 | 672.78-678.39 |
| 5 | 10.1038/s41467-024-52518-9 | PtZn1.4/SiO2 | 873.15 | 0.589 | 0.990 | 2.10 | 0.324 | 684.91 |

Best record by paper:

| Paper | Best catalyst | Cost USD/t | Plant X |
|---|---|---:|---:|
| 10.1038/s41467-024-52518-9 | PtZn1.4/SiO2 | 667.55 | 0.324 |
| 10.1039/d3sc04310j | PtSn3Ca5/Al2O3 | 672.32 | 0.323 |
| 10.1038/s41467-024-50709-y | Pt/In-ZSM-5 | 719.63 | 0.271 |
| 10.1039/d2sc03723h | 0.1Pt7CuSiO3-680R | 722.85 | 0.271 |
| 10.1021/acscatal.2c01631 | 0.8Pt2.4Zn-SPP | 728.05 | 0.200 |
| 10.1038/s41586-021-03923-3 | ZnO-S-1_3 | 738.31 | 0.305 |
| 10.1038/s41467-025-61182-6 | Pt@Sn-MFI | 749.32 | 0.201 |
| 10.1039/c9sc05599a | Pt0 Znd+/SiO2 | 753.56 | 0.201 |
| 10.1021/jacs.2c05618 | PtMn/SiO2 | 756.51 | 0.201 |
| 10.1021/acscatal.0c01580 | 4Zn/TiZrOx | 792.36 | 0.201 |
| 10.1021/acscatal.1c05778 | 6ZnO/S-1(1.0Mg) | 875.00 | 0.201 |
| 10.1021/acscatal.6b01286 | (3Fe:P)/Al2O3 | 1050.91 | 0.293 |
| 10.1021/acscatal.9b02459 | Ga125Rh/Al2O3 SCALMS | 1067.53 | 0.179 |
| 10.1039/d1sc05866e | In-CHA(12, 1.0) | 1456.11 | 0.255 |

33 of 92 usable records beat the reference plant cost under the central assumptions.

## 7. Does laboratory ranking predict plant choice?

Short answer: **activity/productivity ranking predicts plant choice better than conversion or selectivity alone, but none is sufficient by itself.**

Ranking-change metrics from `run_analysis`:

| Lab metric used for ranking | Level | Groups | Changed | Fraction changed | 95% CI | Meaning |
|---|---|---:|---:|---:|---|---|
| Productivity | operating-point | 14 | 2 | 0.143 | 0.000-0.357 | lab productivity winner usually remains near plant winner |
| Productivity | catalyst | 12 | 1 | 0.083 | 0.000-0.273 | catalyst-level activity ranking is fairly robust |
| Conversion | operating-point | 14 | 7 | 0.500 | 0.222-0.833 | conversion ranking frequently fails |
| Conversion | catalyst | 12 | 4 | 0.333 | 0.083-0.636 | high lab conversion is often not the plant optimum |
| Selectivity | operating-point | 14 | 3 | 0.214 | 0.000-0.500 | selectivity matters, but is not alone decisive |
| Selectivity | catalyst | 12 | 3 | 0.250 | 0.000-0.546 | high selectivity can be outweighed by activity/T/equilibrium |

Where ranking changes:

* **High lab conversion is attenuated by equilibrium.**  At 823 K the plant per-pass conversion is capped near 0.20 at the model pressures, so very active low-temperature catalysts cannot use all of their apparent lab conversion advantage; they pay more recycle, compression, and C3 separation capital/energy.
* **High productivity is attenuated after it is “enough”.**  Once catalyst inventory/reactor capital is not dominant, feed and separation set a floor.  Example: the very productive 0.8Pt2.4Zn-SPP record remains good but is not the plant winner because its lower-temperature equilibrium cap gives a plant per-pass conversion of only about 0.20.
* **Selectivity is monetized mainly through propane feed.**  A +1 percentage point selectivity improvement at the reference saves 6.79 USD/t.  However, a lower-selectivity catalyst can still rank well if it operates hotter with higher feasible per-pass conversion and high productivity.
* **Metal value is small in this model.**  Metal price explains only 2.3% of the attribution because annualized catalyst inventory is small relative to propane feed and installed plant cost for most active catalysts.

## 8. Controlling catalyst property and attenuation mechanisms

Attribution shares from `analysis.json`:

| Property | Attribution share |
|---|---:|
| Activity/productivity | 0.410 |
| Selectivity | 0.266 |
| Temperature/equilibrium | 0.199 |
| Stability | 0.103 |
| Metal value | 0.023 |

Therefore, among catalyst properties, **apparent activity/productivity is the largest controller of plant cost across the extracted literature set**, followed by selectivity and operating temperature/equilibrium.  But the absolute largest plant cost term is feedstock, not catalyst.

Attenuation map:

* Feedstock cost: makes selectivity important and imposes a floor near the stoichiometric propane requirement.
* Equilibrium: caps single-pass conversion; hotter operation can reduce recycle and C3 splitter/compressor size even if lab conversion at a lower temperature looks high.
* Recycle: turns low per-pass conversion into larger flow through reactor, compressor, H2 recovery, and C3 splitter.
* Separation: reduces the value of lab conversion once per-pass conversion is optimized, because the C3 splitter cost scales with total C3 traffic, not just product.
* Equipment/capital: penalizes low productivity through catalyst inventory/reactor size, but this penalty saturates for highly active catalysts.
* Operation/energy: reaction heat is significant but smaller than feed and capital under the central energy prices; heat recovery further attenuates temperature penalties.
* Catalyst metal price: weak effect for these records because most catalysts have low precious-metal loading and inventory value is amortized.

## 9. Sensitivity to uncertain parameters

One-at-a-time sensitivity over the low/high bounds in `sources.csv` kept the identity of the best catalyst as PtZn1.4/SiO2 except for the pessimistic catalyst-life case, where PtSn3Ca5/Al2O3 narrowly became best.  The main ranking conclusion is therefore robust to feed, energy, capex, C3 splitter duty, H2 credit, and capital recovery ranges.

Selected sensitivity results:

| Parameter varied | Low-case best / cost | High-case best / cost | Notes |
|---|---|---|---|
| Propane price 300-650 USD/t | PtZn1.4/SiO2 / 572 USD/t | PtZn1.4/SiO2 / 943 USD/t | absolute costs move strongly, ranking stable |
| Base capex 0.9-1.8 BUSD | PtZn1.4/SiO2 / 603 USD/t | PtZn1.4/SiO2 / 797 USD/t | capital uncertainty large but not rank-changing |
| Gas price 3-9 USD/GJ | PtZn1.4/SiO2 / 654-694 USD/t | PtZn1.4/SiO2 | energy price secondary |
| Electricity 0.05-0.14 USD/kWh | PtZn1.4/SiO2 / 657-689 USD/t | PtZn1.4/SiO2 | compression/separation electricity secondary |
| C3 splitter intensity 0.015-0.045 GJ/kmol | PtZn1.4/SiO2 / 664-675 USD/t | PtZn1.4/SiO2 | recycle/separation matters but not enough to change winner |
| H2 credit 0.5-3 USD/kg | PtZn1.4/SiO2 / 715-596 USD/t | PtZn1.4/SiO2 | co-product credit shifts all records similarly |
| CRF 0.08-0.16 | PtZn1.4/SiO2 / 604-741 USD/t | PtZn1.4/SiO2 | capital-heavy but rank stable |
| Heat recovery 0.55-0.90 | PtZn1.4/SiO2 / 677-660 USD/t | PtZn1.4/SiO2 | heat recovery has modest effect |
| Catalyst life 1-6 y | PtSn3Ca5/Al2O3 / 672 USD/t at low life | PtZn1.4/SiO2 / 666 USD/t at high life | only sensitivity that changes best record |

## 10. What the evidence could not support

* The papers rarely provide full intrinsic kinetics, pressure orders, H2 inhibition, or measured approach-to-equilibrium rates.  The kinetic transfer therefore uses an apparent productivity correction, not a fundamental microkinetic model.
* Catalyst life is not truly industrial.  Several records have short lab stability tests; `t_cycle_h` is treated as a regeneration severity signal, not a proven replacement schedule.
* Selectivity byproducts are not fully speciated in a consistent way across papers.  The model counts selectivity loss as propane-equivalent C3 purge/byproduct to preserve mass accounting and feed penalty.
* Product purification is represented by scalable H2 recovery and C3 splitter duties, not rigorous distillation simulation.
* Capital is a transparent scaling model with source/assumption ranges, not a vendor estimate.  It is suitable for ranking and attribution, not for final investment cost.
* Lab feed dilution differs among papers.  The plant uses pure propane recycle operation; dilution effects enter only through the extracted apparent productivity and equilibrium correction.

## 11. Bottom-line answer

A plant would choose a catalyst/condition close to the high-selectivity, sufficiently active, high-temperature PtZn/PtSn family rather than simply the record with maximum lab conversion or maximum productivity.  In this data set the central winner is **PtZn1.4/SiO2 at 600 C from 10.1038/s41467-024-52518-9**, with **667.55 USD/t propylene**.  Laboratory productivity is the best single predictor, but conversion alone is unreliable because equilibrium, recycle, compression, and C3 separation reshape the optimum.  The catalyst property with the largest plant-cost leverage across the extracted literature is **activity/productivity**, while the largest absolute plant cost is still **propane feed**, making high selectivity essential for the final shortlist.
