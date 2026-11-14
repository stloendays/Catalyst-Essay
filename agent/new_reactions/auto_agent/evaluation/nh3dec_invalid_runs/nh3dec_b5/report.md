# Industrial ammonia decomposition to hydrogen: catalyst-to-plant economic ranking

**Report date:** November 13, 2026  
**Reaction:** 2 NH3 -> N2 + 3 H2  
**Evidence base:** 12 papers, 234 usable operating points  
**Cost basis:** 2024 USD at US Gulf Coast price-table conditions; every quoted plant cost is calculated by `model.py`, not copied from a process study.

## Executive answer

**Laboratory ranking is only a partial predictor of plant choice.** Catalyst-level productivity ranking selected the same plant-preferred catalyst in 8 of 11 evaluable groups (73%); at the operating-point level it changed in 7 of 12 groups (58%). Conversion was a substantially worse predictor: the preferred operating point changed in 10 of 12 groups (83%), and catalyst identity changed in 4 of 11 groups (36%). Selectivity did not discriminate because all in-scope thermal-decomposition records were stoichiometrically selective to N2 and H2.

The measured plant optimum is **3%Ru10%K/CaO at 550 °C and 40 bar**, calculated at **$4,537/t H2**. It is not the highest-productivity laboratory point. The laboratory activity maximum is **5%Ru10%K/NS**, 47.82 kg H2 kgcat-1 h-1, but its plant cost is $4,722/t. High reactor pressure moves the plant choice because it sharply reduces cracked-gas and product-compression work, while sufficient temperature/activity keeps catalyst inventory modest.

Across one-at-a-time catalyst-property attribution, **activity accounts for 74.4%** of modeled catalyst-driven cost variation, **stability 19.2%**, **metal price 5.3%**, and **temperature 1.1%**; selectivity contributes 0% in this dataset. Yet catalyst activity does not control total hydrogen cost: ammonia feed is the largest reference-plant cost. Doubling reference activity saves only $104/t H2 (2.1%) because feed, thermodynamic heat, vaporization, recycle, PSA, compression and fixed plant costs remain.

**Main design implication:** seek catalysts that combine adequate activity with long life and operation at useful pressure. Pursuing the single highest differential laboratory rate has low value after catalyst inventory becomes a small fraction of total cost.

## 1. Literature search, screening and extraction

### Inclusion criteria

- Primary experimental heterogeneous thermal NH3 decomposition to N2 + H2.
- Quantitative catalyst identity, temperature, pressure or clearly ambient pressure, feed composition, conversion/yield, and catalyst-normalized rate or flow plus catalyst mass.
- Fixed-bed data were preferred; a membrane-reactor paper was retained only where catalyst-side productivity could be reconstructed.
- Reviews, process-only studies, DFT-only studies, ammonia synthesis/oxidation/electrochemistry, plasma/photothermal-only work, duplicate datasets, and records without throughput or catalyst mass were excluded.

### Usable papers

| DOI | Year | Paper | Usable records | Catalysts |
|---|---:|---|---:|---:|
| 10_1007_s11244_017_0806_0 | 2017 | Modification of Ammonia Decomposition Activity of Ruthenium Nanoparticles by N-Doping of CNT Supports | 3 | 3 |
| 10_1021_acscatal_5c04795 | 2025 | No Time for Nitrides: How Cobalt Alloying Promotes Iron Catalysts for Ammonia Decomposition | 1 | 1 |
| 10_1021_acscatal_6c05612 | 2026 | Contrasting Roles of Rare-Earth and Ga Oxide Additives in Spinel-Derived Water-Tolerant Ni-Co/Al2O3 Catalysts for Ammonia Decomposition | 20 | 4 |
| 10_1021_acssuschemeng_8b06065 | 2019 | Efficient Ammonia Decomposition in a Catalytic Membrane Reactor To Enable Hydrogen Storage and Utilization | 2 | 1 |
| 10_1038_s41467_019_11848_9 | 2019 | Highly efficient decomposition of ammonia using high-entropy alloy catalysts | 14 | 7 |
| 10_1038_s41467_023_36339_w | 2023 | Dispersed surface Ru ensembles on MgO(111) for catalytic ammonia decomposition | 52 | 3 |
| 10_1038_s41467_026_74913_0 | 2026 | Atomically dispersed Ce species adjacent to Ni nanoparticles as hydrogen scavengers for efficient catalytic ammonia decomposition | 16 | 5 |
| 10_1039_c5sc00205b | 2015 | Ammonia decomposition catalysis using non-stoichiometric lithium imide | 5 | 5 |
| 10_1039_d0cy00686f | 2020 | High pressure ammonia decomposition on Ru–K/CaO catalysts | 55 | 11 |
| 10_1039_d0cy02336a | 2021 | Development of a Ba–CoCe catalyst for the efficient and stable decomposition of ammonia | 24 | 15 |
| 10_1039_d1ee03730g | 2022 | Hydrogen generation via ammonia decomposition on highly efficient and stable Ru-free catalysts: approaching complete conversion at 450 °C | 15 | 8 |
| 10_1039_d2fd00175f | 2023 | Metal-loaded zeolites in ammonia decomposition catalysis | 27 | 27 |

The 12 papers supply 234 usable points after unit normalization and plausibility gates. Hydrogen selectivity was set to unity only for records explicitly in the thermal NH3 -> N2 + H2 scope with no side products. Three CNT records were manually reconstructed from the published 6000 mL NH3 gcat-1 h-1 flow, NH3:He=1:2.4, catalyst loading and Table 2 conversion. Two membrane-reactor points use a documented geometric reconstruction and should be treated as higher-uncertainty records.

### Downloaded but unusable after extraction

| DOI | Paper | Reason |
|---|---|---|
| 10_1021_acs_jpclett_1c01242 | Optimization of High-Entropy Alloy Catalyst for Ammonia Decomposition and Ammonia Synthesis | No record met the complete conversion plus catalyst-normalized throughput requirement after full-text/OCR review. |
| 10_1038_s41545_025_00517_8 | Ammonia decomposition and hydrogen production via novel FeCoNiCuMnO high-entropy ceramic catalysts | No record met the complete conversion plus catalyst-normalized throughput requirement after full-text/OCR review. |
| 10_1252_jcej_14we431 | Kinetic Analysis of Decomposition of Ammonia over Nickel and Ruthenium Catalysts | No record met the complete conversion plus catalyst-normalized throughput requirement after full-text/OCR review. |

### Screening exclusions

Every screened exclusion is retained in `candidates.csv`. The dominant reasons were: review/perspective rather than primary data; wrong reaction class; theoretical-only work; inaccessible or unverifiable full text; missing catalyst mass/throughput; and membrane, plasma or photothermal configurations that could not be separated into catalyst-intrinsic performance. Full exclusion log:

| DOI | Title | Exclusion reason |
|---|---|---|
| 10.1007/s11244-016-0653-4 | H2 Production via Ammonia Decomposition Using Non-Noble Metal Catalysts: A Review | Review article, not a primary experimental paper. |
| 10.1016/j.apcatb.2021.119896 | Catalytic ammonia decomposition over Ni-Ru supported on CeO2 for hydrogen production: Effect of metal loading and kinetic analysis | Title indicates a relevant Ni–Ru/CeO2 experimental and kinetic study, but no abstract was supplied and quantitative throughput, catalyst mass, and open-PDF availability cannot be verified. |
| 10.1016/j.ijhydene.2014.03.043 | In-situ H2 production via low temperature decomposition of ammonia: Insights into the role of cesium as a promoter | Relevant experimental Cs-promoted Ru/CNT study, but it is not prioritized because open full-text availability and complete productivity inputs are uncertain. |
| 10.1002/cite.202200003 | Ammonia Decomposition in the Process Chain for a Renewable Hydrogen Supply | Review article focused on catalyst and process-chain literature rather than a new experimental catalyst dataset. |
| 10.1080/01614940.2014.903637 | Toward Practical Application Of H2Generation From Ammonia Decomposition Guided by Rational Catalyst Design | Perspective/review, not a primary experimental catalyst-performance paper. |
| 10.1016/j.ijhydene.2022.07.102 | Plasma-catalytic ammonia decomposition using a packed-bed dielectric barrier discharge reactor | Plasma-catalytic dielectric-barrier-discharge study, explicitly outside the thermal heterogeneous-catalysis scope. |
| 10.1016/j.ijhydene.2020.07.090 | Hydrogen production from ammonia decomposition using Co/γ-Al2O3 catalysts – Insights into the effect of synthetic method | Title indicates a relevant Co/γ-Al2O3 synthesis-method study, but no abstract was supplied and throughput details and accessible full text cannot be verified. |
| 10.1016/j.jiec.2020.11.003 | Hydrogen production by ammonia decomposition over ruthenium supported on SiC catalyst | Title indicates relevant Ru/SiC thermal catalysis, but no abstract was supplied and neither quantitative productivity inputs nor open access can be established. |
| 10.1038/s41467-024-51810-y | Utilizing full-spectrum sunlight for ammonia decomposition to hydrogen over GaN nanowires-supported Ru nanoparticles on silicon | Photo-thermal solar-driven NH3 decomposition, excluded because activity is coupled to optical excitation rather than conventional heterogeneous thermal operation. |
| 10.1016/j.fuel.2023.128900 | A Review of Hydrogen Production from Onboard Ammonia Decomposition: Maritime Applications of Concentrated Solar Energy and Boil-Off Gas Recovery | Review of onboard ammonia decomposition and solar/waste-gas applications, not primary catalyst experimentation. |
| 10.1007/s11244-017-0806-0 | Modification of Ammonia Decomposition Activity of Ruthenium Nanoparticles by N-Doping of CNT Supports | Relevant experimental Ru/N-doped-CNT catalyst study, but lower priority because open-PDF availability and sufficient throughput reporting are uncertain. |
| 10.1016/j.ces.2023.118550 | Ammonia decomposition in a dielectric barrier discharge plasma: Insights from experiments and kinetic modeling | Dielectric-barrier-discharge plasma experiment and plasma kinetic modeling, outside the thermal catalytic scope. |
| 10.1039/d4im00112e | Catalyst design for ammonia decomposition: an overview | Overview/review of catalyst-design strategies, not a primary experimental dataset. |
| 10.1016/j.energy.2022.125209 | Highly selective Pd composite membrane on porous metal support for high-purity hydrogen production through effective ammonia decomposition | Primarily a Pd composite membrane fabrication and separation study; the abstract does not establish separable catalyst-side activity with productivity inputs. |
| 10.1016/j.fuel.2022.124384 | Self-combustion Ni and Co-based perovskites as catalyst precursors for ammonia decomposition. Effect of Ce and Mg doping | Relevant experimental Ni/Co perovskite-precursor study, but not prioritized because accessible full text and complete throughput data are uncertain. |
| 10.1016/j.cattod.2023.01.029 | Recent progress for hydrogen production from ammonia and hydrous hydrazine decomposition: A review on heterogeneous catalysts | Review article covering ammonia and hydrous-hydrazine decomposition, not primary experimental work. |
| 10.1016/j.scp.2022.100615 | New catalysts based on reduced graphene oxide for hydrogen production from ammonia decomposition | Relevant experimental Ru/reduced-graphene-oxide study, but lower priority due to uncertain open access and uncertainty that all productivity inputs are reported. |
| 10.1016/j.egyr.2020.10.032 | Alumina particle size effect on H2 production from ammonia decomposition by DBD plasma | DBD-plasma ammonia decomposition study, excluded despite quantitative flow data because it is not thermal heterogeneous catalysis. |
| 10.1002/er.5286 | Optimal design and operation of ammonia decomposition reactors | Process/reactor optimization and modeling paper rather than a new experimental catalyst-performance study. |
| 10.1016/j.cej.2023.144623 | Unraveling the promoter role of Ba in Co–Ce catalysts for ammonia decomposition using microkinetic modeling | Microkinetic-modeling-focused analysis of Ba promotion; likely overlaps the Ba–CoCe experimental system and is not preferred over the original catalyst-development dataset. |
| 10.1016/j.mcat.2021.111721 | Electrochemical activation of Ru catalyst with alkaline ion conductors for the catalytic decomposition of ammonia | Electrochemical promotion/activation of Ru using alkaline-ion conductors, excluded under the electrochemistry criterion. |
| 10.1038/s41467-025-66325-3 | Breakthrough photothermal ammonia decomposition via low-barrier Ni-CeO2-x interfaces on carbon nanotubes | Photothermal Ni–CeO2−x/CNT system whose activity depends on light excitation, outside conventional thermal catalysis. |
| 10.1155/2024/9534752 | Thermal Ammonia Decomposition for Hydrogen‐Rich Fuel Production and the Role of Waste Heat Recovery | Broad thermal-ammonia-decomposition and waste-heat-recovery review, not a primary catalyst experiment. |
| 10.1021/acscatal.5c04795 | No Time for Nitrides: How Cobalt Alloying Promotes Iron Catalysts for Ammonia Decomposition | Appears to contain relevant experimental Fe–Co alloy results, but it is a very recent article and accessible full text plus complete throughput information cannot be confirmed; excluded to keep the do |
| 10.1021/acs.jpcc.0c08432 | Kinetic Expression for Optimal Catalyst Electronic Configuration: The Case of Ammonia Decomposition | Theoretical kinetic/electronic model rather than a primary experimental catalyst-performance dataset. |
| 10.3390/catal15090811 | A Comprehensive Review on Hydrogen Production via Catalytic Ammonia Decomposition | Comprehensive review, not a primary experimental study. |
| 10.1021/acscatal.5c07452 | Multi-Scale Modeling for Plasma-Enhanced Ammonia Decomposition over Carbides and Nitrides | Plasma-enhanced decomposition and predominantly multiscale/DFT/kinetic modeling; plasma studies are excluded. |
| 10.1007/s12210-025-01329-1 | Iron-group single-atom catalysts for ammonia synthesis and decomposition | Broad title and abstract covering single-atom catalysts for both ammonia synthesis and decomposition suggest a review or perspective rather than a focused primary throughput dataset. |
| 10.3390/en18143841 | Influence of 50 Hz and 20 kHz Plasma Generator Frequency on Ammonia Decomposition for Hydrogen Recovery | Plasma-assisted ammonia decomposition; plasma studies are explicitly excluded. |
| 10.1007/s44344-026-00034-x | Advances in catalysts development and catalytic activity trends of conventional metal oxides and inorganic perovskites for hydrogen production via ammonia decomposition: a review | Review article, not a primary experimental catalyst study. |
| 10.1021/acscatal.6c05612 | Contrasting Roles of Rare-Earth and Ga Oxide Additives in Spinel-Derived Water-Tolerant Ni-Co/Al2O3 Catalysts for Ammonia Decomposition | Potentially relevant primary Ni–Co catalyst study, but the 2026 citation is prospective and an accessible full experimental paper cannot be assumed; exclude under the accessible-PDF requirement. |
| 10.3390/compounds6030042 | Advances in Gaseous Ammonia Decomposition for Hydrogen Production: Catalysts and Emerging Pathways | Review of catalytic and emerging ammonia-decomposition pathways, not primary experimental research. |
| 10.1038/s41467-026-74913-0 | Atomically dispersed Ce species adjacent to Ni nanoparticles as hydrogen scavengers for efficient catalytic ammonia decomposition | Potentially strong primary Ni–Ce–Al catalyst study, but the 2026 citation is prospective and accessible full-text quantitative data cannot presently be assured. |
| 10.1016/j.pecs.2018.07.001 | Ammonia for power | Broad review of ammonia as an energy carrier and fuel, not a primary catalyst-performance paper. |
| 10.1016/j.joule.2020.04.004 | A Roadmap to the Ammonia Economy | Title indicates a broad ammonia-economy roadmap rather than a primary experimental NH3 decomposition catalyst study. |
| 10.1038/s41565-022-01121-4 | Efficient conversion of low-concentration nitrate sources into ammonia on a Ru-dispersed Cu nanowire electrocatalyst | Electrocatalytic nitrate-to-ammonia conversion, not thermal catalytic ammonia decomposition. |
| 10.1021/acs.energyfuels.0c03685 | Review on Ammonia as a Potential Fuel: From Synthesis to Economics | Review of ammonia fuel, synthesis, and economics rather than primary decomposition experiments. |
| 10.3390/en13123062 | Ammonia as Effective Hydrogen Storage: A Review on Production, Storage and Utilization | Review of ammonia production, storage, and utilization, not primary catalyst-performance research. |
| 10.1016/j.fuel.2020.117448 | Experimental study on ammonia/hydrogen/air combustion in spark ignition engine conditions | Experimental ammonia/hydrogen/air combustion study, outside catalytic NH3 decomposition. |
| 10.1039/d0ta08810b | Recent progress in ammonia fuel cells and their potential applications | Review of ammonia fuel cells and electrocatalysis, not heterogeneous thermal decomposition. |
| 10.1039/d0gc02058c | Plasma-driven catalysis: green ammonia synthesis with intermittent electricity | Review focused on plasma-driven ammonia synthesis, not thermal NH3 decomposition. |
| 10.1021/acs.iecr.3c01419 | Ammonia as a Carbon-Free Energy Carrier: NH 3 Cracking to H 2 | Broad cracking overview suggested by the title and abstract rather than a distinct primary experimental catalyst dataset. |
| 10.1149/2.0191815jes | Review—Ammonia Oxidation Electrocatalysis for Hydrogen Generation and Fuel Cells | Review of ammonia oxidation electrocatalysis; electrochemical studies and reviews are excluded. |
| 10.1021/jacs.2c01950 | Shielding Protection by Mesoporous Catalysts for Improving Plasma-Catalytic Ambient Ammonia Synthesis | Plasma-catalytic ammonia synthesis, not thermal ammonia decomposition. |
| 10.1016/j.apcatb.2016.11.003 | Electrodeposited NiCu bimetal on carbon paper as stable non-noble anode for efficient electrooxidation of ammonia | Electrooxidation of ammonia over a NiCu anode, not heterogeneous thermal decomposition to N2 and H2. |
| 10.1016/j.ijhydene.2013.05.144 | Ammonia as hydrogen carrier for transportation; investigation of the ammonia exhaust gas fuel reforming | Transportation exhaust-gas reforming and engine integration rather than a clean, reconstructable catalyst-performance dataset for conventional NH3 decomposition. |
| 10.3390/jmse8030183 | A Preliminary Study on an Alternative Ship Propulsion System Fueled by Ammonia: Environmental and Economic Assessments | Ship propulsion environmental/economic assessment, not primary catalyst testing. |
| 10.1073/pnas.2115504119 | High-ammonia selective metal–organic framework–derived Co-doped Fe/Fe 2 O 3 catalysts for electrochemical nitrate reduction | Electrochemical nitrate reduction to ammonia, the reverse chemistry and wrong reaction class. |
| 10.3389/fmech.2022.944201 | Ammonia as Green Fuel in Internal Combustion Engines: State-of-the-Art and Future Perspectives | Review of ammonia combustion in internal-combustion engines. |
| 10.1016/j.jfueco.2022.100064 | On the use of ammonia as a fuel – A perspective | Perspective on ammonia as a fuel, not primary catalyst-performance research. |
| 10.3389/fenrg.2021.760356 | A Review on Combustion Characteristics of Ammonia as a Carbon-Free Fuel | Review of ammonia combustion characteristics, outside catalytic decomposition. |
| 10.1016/j.fuproc.2021.106772 | H2 production via ammonia decomposition in a catalytic membrane reactor | Catalytic membrane-reactor study; the abstract does not establish that intrinsic catalyst-side conversion and throughput can be separated from membrane hydrogen removal. |
| 10.3390/en14133732 | A Comprehensive Review on the Recent Development of Ammonia as a Renewable Energy Carrier | Comprehensive review of ammonia as an energy carrier, not primary experimental catalyst research. |

## 2. Mechanism and kinetic transfer

### Mechanism

The common sequence is NH3 adsorption, three successive N-H scissions, H recombination/desorption, and N recombination/desorption. Strong N binding inhibits N2 removal; weak N binding inhibits NH3 activation. Because the dataset spans Ru, Fe/Co/Ni alloys, imides and zeolitic supports, the plant model does not force a universal fitted elementary rate law onto all papers. It preserves each measured mass productivity and applies a common reversible thermodynamic correction.

### Laboratory-to-plant activity transfer

- Each record retains its demonstrated temperature and pressure; no universal Arrhenius extrapolation is imposed.
- Reported H2 productivity is divided by the laboratory approach-to-equilibrium factor and transferred with a first-order NH3 partial-pressure correction.
- Plant net rate is the effective forward rate multiplied by 1-Q/K; rate therefore vanishes at equilibrium and reverses correctly.
- Catalyst mass equals gross hourly H2 generation divided by the equilibrium-corrected productivity.
- Reported time to 10% activity loss is used where available; otherwise 16,000 h is assumed with a retained 4,000-40,000 h uncertainty range.

### Atomic-scale model

The descriptor is N adsorption energy relative to 1/2 N2. The reversible six-step `mkm_solver` model uses literature scaling/BEP structure and NIST Shomate thermochemistry. The atom-scale volcano optimum is **D = -1.562 eV**, log10(TOF/s/site) = -1.687, at 673.15 K and approximately 1 bar NH3 feed. This is a stronger-binding, Fe/Co-like region rather than the Ru descriptor used by the reference catalyst.

## 3. Plant boundary, reactor and flowsheet

### Boundary and basis

- Nameplate product: 73,000 t H2/y, corresponding to 200 t/day at 8,760 h/y.
- Feed: commercial NH3 at 298.15 K and 10.0 bar; purity 99.50 mol%.
- Product: 99.990 mol% H2 at 250.0 bar.
- Upstream ammonia manufacture and downstream H2 transport/use are excluded.
- Utility links labeled H2 in `flowsheet.json` are zero-mass schema placeholders required by the validator; they are excluded from all material and thermodynamic balances.

### Reactor and operating variables

An externally electrically heated multitubular packed-bed reactor is used. Each record keeps its laboratory T and P. The plant optimizes per-pass conversion from 5% up to the smaller of 40% and 98% of equilibrium; unreacted NH3 is condensed and recycled. The 40% cap is a heat-transfer/recycle design assumption, not a measured universal optimum, and is explicitly varied from 20% to 80% in sensitivity.

### Accepted flowsheet

```mermaid
boundary NH3 -> pump -> mixer <- NH3 recycle <- knockout
                         |
                         v
feed-effluent HX -> vaporizer/trim heater -> packed-bed cracker <- electric furnace
       ^                                      |
       |______________________________________| hot effluent
partly cooled gas -> cracked-gas compressor -> condenser -> knockout -> PSA -> H2 compressor -> boundary H2
                                                                  |
                                                                  +-> boundary offgas
boundary electricity -> offsites -> all electric drives/heaters
```

Units represented: fresh NH3 pump; recycle mixer; feed/effluent exchanger; electric vaporizer/trim heater; reactor-feed pressure control; ammonia cracking reactor; electric furnace; cracked-gas compressor; NH3 condenser; NH3 knockout/recycle; H2 PSA; H2 product compressor; electrical/cooling offsites. Catalyst regeneration is excluded because no common regenerable cycle is supported across the catalyst families; replacement is costed instead.

## 4. Economic and physical model

- All duties are calculated per unit from the accepted flowsheet and depend on plant conversion.
- NH3 circulation, vaporization, sensible heating, cracked-gas flow, condensation, recycle and compression all rise as per-pass conversion falls.
- Reaction heat uses temperature-dependent enthalpy; compressor work uses staged ideal-gas compression with efficiency; PSA recovery is 90% with 88-92% evidence range.
- Capital is scaled separately for every flowsheet unit; annual capital and fixed O&M use the fixed `prices.json` capital recovery factor and O&M fraction.
- Catalyst price is built from reported component loadings plus fixed price-table metal/support prices. Inventory and replacement are costed once.
- `check_model` passes the reference and all 234 records for contract, elements, mass, equilibrium, reaction heat, heat supply, compression, separation, unit accounting, finite cost, parts sum, conversion, monotonicity and determinism. `check_atomic` also passes thermodynamics, volcano, provenance and plant linkage.

## 5. Reference plant result

Reference catalyst: 7 wt.% Ru/N-CNT1 at 673.15 K and 1.013 bar. Optimized per-pass conversion is 40%.

| Cost component | USD/t H2 | Share |
|---|---:|---:|
| Feed | 2,819.7 | 57.3% |
| Energy | 1,526.1 | 31.0% |
| Capital | 263.9 | 5.4% |
| Catalyst | 199.1 | 4.0% |
| Other | 111.8 | 2.3% |
| **Total** | **4,920.7** | **100%** |

Purchased primary energy is 68.68 GJ/t H2 and installed capital is approximately $204,102,100; the detailed physics object in `model.py`/`model_check.json` is the auditable source for unit duties and sizing.

Feed is 57.3% of cost and purchased energy 31.0%; therefore even large catalyst improvements are attenuated. Catalyst replacement is only 4.0% at the reference.

## 6. Which catalyst would the plant choose?

The lowest calculated measured-point cost is **$4,537/t H2** for **3%Ru10%K/CaO** at 550 °C. 151 of 234 records are below the reference cost.

### Ten lowest-cost literature operating points

| Rank | Catalyst | DOI | T (°C) | P (bar) | Productivity | Cost (USD/t H2) |
|---:|---|---|---:|---:|---:|---:|
| 1 | 3%Ru10%K/CaO | 10_1039_d0cy00686f | 550 | 40.00 | 0.648 | 4,537.0 |
| 2 | K-CoNi(alloy)-MgO-CeO2-SrO | 10_1039_d1ee03730g | 500 | 1.50 | 2.7 | 4,705.6 |
| 3 | 5%Ru10%K/NS | 10_1039_d0cy00686f | 400 | 1.01 | 47.8 | 4,721.5 |
| 4 | 5%Ru10%K/MgO | 10_1039_d0cy00686f | 400 | 1.01 | 41.1 | 4,722.2 |
| 5 | 5%Ru10%K/MWCNT | 10_1039_d0cy00686f | 400 | 1.01 | 32.5 | 4,723.4 |
| 6 | HEA-Co25Mo45/CNF (Co25Mo45Fe10Ni10Cu10) | 10_1038_s41467_019_11848_9 | 422 | 1.01 | 0.0809 | 4,730.5 |
| 7 | CsRu/YSZ catalytic membrane reactor | 10_1021_acssuschemeng_8b06065 | 450 | 5.00 | 0.105 | 4,742.0 |
| 8 | 13.7La | 10_1021_acscatal_6c05612 | 400 | 1.00 | 0.423 | 4,742.6 |
| 9 | 13.3Ce | 10_1021_acscatal_6c05612 | 400 | 1.00 | 0.387 | 4,744.4 |
| 10 | Ni8Ce1Al1Ox | 10_1038_s41467_026_74913_0 | 400 | 1.01 | 0.318 | 4,745.3 |

The first-ranked 40-bar Ru-K/CaO point wins despite modest measured productivity because reactor pressure eliminates the 1-to-20 bar cracked-gas compression step and lowers the ratio for final H2 compression. This illustrates a rank reversal caused by the operating condition rather than catalyst chemistry alone.

### Ranking agreement with laboratory metrics

| Laboratory metric | Comparison level | Groups | Rank changed | Fraction changed | >5% regret |
|---|---|---:|---:|---:|---:|
| Productivity | point level | 12 | 7 | 58.3% | 1 |
| Productivity | catalyst level | 11 | 3 | 27.3% | 1 |
| Conversion | point level | 12 | 10 | 83.3% | 2 |
| Conversion | catalyst level | 11 | 4 | 36.4% | 1 |
| Selectivity | point level | 12 | 0 | 0.0% | 0 |
| Selectivity | catalyst level | 11 | 0 | 0.0% | 0 |

Interpretation: productivity is reasonably useful for catalyst-family screening but unreliable for choosing temperature/pressure. Conversion is mostly a reactor residence-time/equilibrium outcome and is the poorest operating-point predictor. Selectivity cannot rank these catalysts because the scoped chemistry has no measured carbon-containing or oxidation coproducts.

### Catalyst-property attribution

| Property | Share of catalyst-driven cost variation |
|---|---:|
| Selectivity | 0.0% |
| Activity | 74.4% |
| Temperature | 1.1% |
| Stability | 19.2% |
| Metal | 5.3% |

At the reference, doubling activity changes cost by -103.6 USD/t H2. Activity mainly reduces catalyst inventory and reactor capital; once those are small, further rate gains are strongly attenuated. Stability remains important because replacement cost scales directly with life. Ru price matters but is less influential than activity and life. Temperature has a small attribution share because feed and compression dominate and the model credits heat recovery.

## 7. Three optima and backward design

| Optimum | Result | Denominator/basis |
|---|---|---|
| Atomic | D = -1.562 eV; logTOF = -1.687 | 201 descriptor grid points from -1.90 to -0.25 eV |
| Laboratory | 5%Ru10%K/NS, r = 47.8 kg/kg/h | 234 usable measured operating points |
| Industrial measured | 3%Ru10%K/CaO, 4,537.0 USD/t | 234 usable measured operating points |

Backward design from the atomic volcano favors an Fe/Co-like N-binding energy near -1.56 eV, but plant economics then favor a low-cost metal realizing that descriptor. At the same descriptor and site/loading assumptions, calculated costs are:

| Metal price case | Cost (USD/t H2) | Metal price (USD/kg) |
|---|---:|---:|
| Fe | 4,750.4 | 8.00 |
| Co | 4,751.2 | 56.28 |
| Ru | 5,667.4 | 53,852.50 |
| Ni | 4,750.6 | 16.91 |
| Cu | 4,750.5 | 13.89 |

Descriptor mapping status: above_volcano 70, matched 127, outside_declared_range 31 (denominator 228 mapped points).

The atomic optimum, laboratory maximum and plant optimum disagree for defensible reasons: the atomistic model isolates intrinsic site kinetics; laboratory productivity folds in dispersion/loading and test conditions; the plant also values pressure, life, metal cost, recycle, separation and compression. The model therefore recommends designing inexpensive Fe/Co/Ni-like surfaces near the descriptor optimum rather than reproducing Ru chemistry at any cost.

## 8. Deterministic sensitivity

The sensitivity engine varied every sourced range, assumption and price-table range one at a time. Across 59 perturbations, the cheapest record was unchanged in 58; the minimum Spearman rank correlation was 0.935. Catalyst life was the only perturbation that changed the winner in the summarized leading drivers.

| Parameter | Type | Low cost | High cost | Cost swing | Low energy | High energy | Winner changes? | Min rank rho |
|---|---|---:|---:|---:|---:|---:|---|---:|
| price.ammonia | price_table | 4,002 | 7,804 | 77.3% | 68.7 | 68.7 | no | 1.000 |
| price.electricity | price_table | 4,158 | 6,256 | 42.6% | 68.7 | 68.7 | no | 0.974 |
| process.maximum_per_pass_conversion | assumption | 5,870 | 4,436 | 29.1% | 106.1 | 49.9 | no | 0.981 |
| process.default_catalyst_life_h | assumption | 5,518 | 4,801 | 14.6% | 68.7 | 68.7 | yes | 0.935 |
| price.metal_Ru | price_table | 4,822 | 5,119 | 6.0% | 68.7 | 68.7 | no | 0.959 |
| process.psa_h2_recovery | published | 5,026 | 4,820 | 4.2% | 70.1 | 67.3 | no | 1.000 |
| capital.hydrogen_PSA_ref_usd | assumption | 4,853 | 5,034 | 3.7% | 68.7 | 68.7 | no | 1.000 |
| capital.cracked_gas_compressor_ref_usd | assumption | 4,876 | 5,025 | 3.0% | 68.7 | 68.7 | no | 1.000 |
| finance.capital_recovery_factor | price_table | 4,880 | 5,020 | 2.8% | 68.7 | 68.7 | no | 0.997 |
| process.compressor_efficiency | assumption | 4,998 | 4,861 | 2.8% | 71.7 | 66.4 | no | 1.000 |
| process.heat_recovery_fraction | assumption | 5,011 | 4,875 | 2.8% | 72.7 | 66.7 | no | 0.983 |
| finance.fixed_om_fraction_of_capex | price_table | 4,865 | 4,977 | 2.3% | 68.7 | 68.7 | no | 0.999 |
| capital.ammonia_knockout_ref_usd | assumption | 4,891 | 4,990 | 2.0% | 68.7 | 68.7 | no | 1.000 |
| process.electric_heater_efficiency | published | 4,980 | 4,888 | 1.9% | 71.3 | 67.2 | no | 1.000 |
| thermo.NH3_vaporization_kJ_per_mol | published | 4,868 | 4,958 | 1.8% | 66.4 | 70.3 | no | 1.000 |
| capital.hydrogen_product_compressor_ref_usd | assumption | 4,895 | 4,985 | 1.8% | 68.7 | 68.7 | no | 1.000 |
| basis.utilities.psa_feed_pressure | assumption | 4,881 | 4,963 | 1.7% | 67.0 | 70.4 | no | 1.000 |
| process.nh3_recovery_fraction | assumption | 4,984 | 4,904 | 1.6% | 68.7 | 68.7 | no | 1.000 |
| capital.offsites_fraction | assumption | 4,898 | 4,970 | 1.5% | 68.7 | 68.7 | no | 0.999 |
| process.feed_cp_kJ_per_kmolK | assumption | 4,893 | 4,957 | 1.3% | 67.6 | 70.1 | no | 0.998 |
| capital.electric_reactor_furnace_ref_usd | assumption | 4,904 | 4,966 | 1.3% | 68.7 | 68.7 | no | 1.000 |
| process.heat_loss_fraction | assumption | 4,907 | 4,968 | 1.2% | 68.1 | 70.7 | no | 1.000 |
| process.maximum_pressure_ratio_per_stage | assumption | 4,907 | 4,958 | 1.0% | 68.1 | 70.1 | no | 1.000 |
| process.psa_specific_electricity_kWh_per_kg | assumption | 4,898 | 4,947 | 1.0% | 67.7 | 69.9 | no | 1.000 |
| basis.utilities.ambient_temperature | assumption | 4,899 | 4,942 | 0.9% | 67.9 | 69.5 | no | 1.000 |
| capital.ammonia_vaporizer_ref_usd | assumption | 4,909 | 4,944 | 0.7% | 68.7 | 68.7 | no | 1.000 |
| capital.ammonia_cracking_reactor_ref_usd | assumption | 4,913 | 4,942 | 0.6% | 68.7 | 68.7 | no | 0.951 |
| basis.feeds.NH3.purity_mol_frac | assumption | 4,935 | 4,907 | 0.6% | 68.7 | 68.7 | no | 1.000 |
| thermo.deltaCp_rxn_J_per_2molK | published | 4,906 | 4,933 | 0.5% | 68.0 | 69.2 | no | 0.999 |
| capital.feed_effluent_exchanger_ref_usd | assumption | 4,912 | 4,937 | 0.5% | 68.7 | 68.7 | no | 0.999 |
| thermo.deltaH_rxn_kJ_per_2mol_NH3 | published | 4,910 | 4,934 | 0.5% | 68.2 | 69.2 | no | 1.000 |
| capital.ammonia_condenser_ref_usd | assumption | 4,914 | 4,937 | 0.5% | 68.7 | 68.7 | no | 1.000 |
| basis.operating_hours_per_y | assumption | 4,936 | 4,921 | 0.3% | 68.7 | 68.7 | no | 1.000 |
| process.compressor_k | assumption | 4,907 | 4,922 | 0.3% | 68.2 | 68.7 | no | 1.000 |
| process.cooling_electricity_kWh_per_GJ | assumption | 4,917 | 4,930 | 0.3% | 68.5 | 69.1 | no | 1.000 |
| capital.scaling_exponent | assumption | 4,917 | 4,929 | 0.3% | 68.7 | 68.7 | no | 0.999 |
| process.catalyst_bulk_density_kg_per_m3 | assumption | 4,928 | 4,917 | 0.2% | 68.7 | 68.7 | no | 0.989 |
| capital.recycle_mixer_ref_usd | assumption | 4,919 | 4,925 | 0.1% | 68.7 | 68.7 | no | 1.000 |
| capital.minimum_scale_fraction | assumption | 4,921 | 4,926 | 0.1% | 68.7 | 68.7 | no | 0.998 |
| price.catalyst_support_and_manufacturing | price_table | 4,920 | 4,925 | 0.1% | 68.7 | 68.7 | no | 0.987 |
| capital.fresh_ammonia_pump_ref_usd | assumption | 4,919 | 4,924 | 0.1% | 68.7 | 68.7 | no | 1.000 |
| process.product_cp_kJ_per_kmolK | assumption | 4,920 | 4,922 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| basis.feeds.NH3.P_bar | assumption | 4,921 | 4,920 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| basis.product.H2.purity_mol_frac | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| process.pump_efficiency | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| process.liquid_NH3_density_kg_per_m3 | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| thermo.deltaS_rxn_J_per_molK | published | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| basis.feeds.NH3.T_K | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| basis.utilities.cooling_temperature | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| price.metal_Fe | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| price.metal_Co | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 0.999 |
| price.metal_Ni | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| price.metal_K | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| price.metal_Ba | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| price.metal_Ce | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| process.default_active_metal_loading | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| process.min_per_pass_conversion | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| process.equilibrium_margin | assumption | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |
| price.metal_Cu | price_table | 4,921 | 4,921 | 0.0% | 68.7 | 68.7 | no | 1.000 |

Key sensitivity interpretation: ammonia and electricity prices dominate absolute cost but scarcely alter ranking; the per-pass conversion assumption dominates energy and recycle burden but also leaves the winner unchanged; catalyst life materially affects both cost and rank; Ru price changes reference cost by 6% across its fixed table range but does not change the leading record.

## 9. Evidence debt and limitations

1. **Catalyst life:** retained as uncertainty (4,000-40,000 h). Most papers report tens to hundreds of hours, not industrial replacement cycles. At the low-life bound the preferred catalyst changes to a high-entropy alloy.
2. **Maximum per-pass conversion:** retained as uncertainty (20-80%). It changes reference cost by 29% and purchased energy by 82%, although the leading catalyst remains unchanged.
3. **Cross-paper productivity:** catalyst masses, supports, dispersions and reporting conventions differ; reconstructed membrane and CNT records are more uncertain than directly reported mass rates.
4. **Selectivity:** all records are assigned stoichiometric H2 selectivity because the scoped thermal reaction reported only N2/H2; this conclusion does not transfer to oxidative or plasma processes.
5. **Pressure extrapolation:** each catalyst keeps its demonstrated pressure. This favors high-pressure records through compressor savings, but the sparse pressure literature prevents a catalyst-independent pressure-rate law.
6. **Capital estimates:** unit reference costs are ranged assumptions unless a direct source is listed; ranking is nevertheless stable because feed and energy dominate.
7. **Atomic model:** one N-binding descriptor cannot capture promoters, support basicity, bifunctional imides, ensemble density or reconstruction. Several laboratory points lie outside or above the declared volcano, indicating missing descriptors/site effects.
8. **Utility stream labels:** H2 utility placeholders exist only because the flowsheet validator requires a valid formula; they carry zero mass and are excluded from balances.

## 10. Parameter provenance table

The table below is the complete `sources.csv` used by `model.py`. Price rows are frozen `prices.json` entries; assumptions always include low/high bounds.

| Parameter | Value | Unit | Type | Low | High | Source | Exact location |
|---|---:|---|---|---:|---:|---|---|
| basis.capacity_t_per_y | 73000.0 | t H2/y | published |  |  | DOI:10.1016/j.ijhydene.2021.07.102 | Abstract: plant designed for up to 200 metric tonnes per day of high-purity hydrogen; annualized as 200 x 365 |
| basis.operating_hours_per_y | 8760.0 | h/y | assumption | 8000.0 | 8760.0 |  | Continuous nameplate interpretation of 200 t/day; 8760 h/y central, 8000 h/y lower availability case. |
| basis.feeds.NH3.T_K | 298.15 | K | assumption | 283.15 | 313.15 |  |  |
| basis.feeds.NH3.P_bar | 10.0 | bar | assumption | 8.0 | 18.0 |  |  |
| basis.feeds.NH3.purity_mol_frac | 0.995 | mol/mol | assumption | 0.99 | 0.9999 |  |  |
| basis.feeds.H2.T_K | 1.0 | K | assumption | 1.0 | 1.0 |  | H2 is a schema-valid placeholder species on zero-mass electricity/heat utility streams only; it is excluded from process boundary balances. |
| basis.feeds.H2.P_bar | 1.0 | bar | assumption | 1.0 | 1.0 |  | H2 is a schema-valid placeholder species on zero-mass electricity/heat utility streams only; it is excluded from process boundary balances. |
| basis.feeds.H2.purity_mol_frac | 1.0 | mol/mol | assumption | 1.0 | 1.0 |  | H2 is a schema-valid placeholder species on zero-mass electricity/heat utility streams only; it is excluded from process boundary balances. |
| basis.product.H2.P_bar | 250.0 | bar | published |  |  | DOI:10.1016/j.ijhydene.2021.07.102 | Abstract: high-purity hydrogen compressed to 250 bar |
| basis.product.H2.purity_mol_frac | 0.9999 | mol/mol | assumption | 0.999 | 0.99999 |  |  |
| basis.utilities.ambient_temperature | 298.15 | K | assumption | 283.15 | 313.15 |  |  |
| basis.utilities.cooling_temperature | 303.15 | K | assumption | 293.15 | 313.15 |  |  |
| basis.utilities.psa_feed_pressure | 20.0 | bar | assumption | 10.0 | 30.0 |  |  |
| price.ammonia | 445.0 | USD/t | price_table | 300.0 | 900.0 | prices.json:ammonia | prices.ammonia |
| price.electricity | 80.0 | USD/MWh | price_table | 40.0 | 150.0 | prices.json:electricity | prices.electricity |
| price.catalyst_support_and_manufacturing | 20.0 | USD/kg | price_table | 5.0 | 100.0 | prices.json:catalyst_support_and_manufacturing | prices.catalyst_support_and_manufacturing |
| price.metal_Ru | 53852.5 | USD/kg | price_table | 26926.25 | 107705.0 | prices.json:metal_Ru | prices.metal_Ru |
| price.metal_Fe | 8.0 | USD/kg | price_table | 4.0 | 16.0 | prices.json:metal_Fe | prices.metal_Fe |
| price.metal_Co | 56.28401553583051 | USD/kg | price_table | 28.142007767915256 | 112.56803107166104 | prices.json:metal_Co | prices.metal_Co |
| price.metal_Ni | 16.9094555095895 | USD/kg | price_table | 8.45472775479475 | 33.818911019179 | prices.json:metal_Ni | prices.metal_Ni |
| price.metal_K | 1.4455393066229791 | USD/kg | price_table | 0.7227696533114896 | 2.8910786132459583 | prices.json:metal_K | prices.metal_K |
| price.metal_Ba | 0.3569000679809653 | USD/kg | price_table | 0.1784500339904826 | 0.7138001359619306 | prices.json:metal_Ba | prices.metal_Ba |
| price.metal_Ce | 2.1005306603773586 | USD/kg | price_table | 1.0502653301886793 | 4.201061320754717 | prices.json:metal_Ce | prices.metal_Ce |
| finance.capital_recovery_factor | 0.0944 | 1/y | price_table | 0.08 | 0.13 | prices.json:capital_recovery_factor | prices.capital_recovery_factor |
| finance.fixed_om_fraction_of_capex | 0.04 | 1/y | price_table | 0.02 | 0.06 | prices.json:fixed_om_fraction_of_capex | prices.fixed_om_fraction_of_capex |
| thermo.deltaH_rxn_kJ_per_2mol_NH3 | 92.22 | kJ per 2 mol NH3 | published | 90.0 | 95.0 | DOI:10.18434/T4D303 | NIST Chemistry WebBook SRD 69: NH3 gas-phase standard enthalpy of formation -46.11 kJ/mol; elements zero |
| thermo.deltaS_rxn_J_per_molK | 198.1 | J per stoichiometric reaction/K | published | 190.0 | 210.0 | DOI:10.18434/T4D303 | NIST Chemistry WebBook standard gas entropies at 298.15 K combined as S(N2)+3S(H2)-2S(NH3) |
| thermo.NH3_vaporization_kJ_per_mol | 23.35 | kJ/mol NH3 | published | 21.0 | 25.0 | DOI:10.18434/T4D303 | NIST Chemistry WebBook NH3 enthalpy-of-vaporization table near normal boiling point |
| process.heat_recovery_fraction | 0.8 | fraction | assumption | 0.6 | 0.9 |  |  |
| process.electric_heater_efficiency | 0.95 | fraction | published | 0.9 | 0.98 | https://www.kanthal.com/en/knowledge-hub/inspiring-stories/electric-industrial-heating-demystified/ | Energy Efficiency section states electric industrial heating can achieve up to 95% thermal efficiency. |
| process.heat_loss_fraction | 0.05 | fraction | assumption | 0.02 | 0.15 |  |  |
| process.nh3_recovery_fraction | 0.995 | fraction | assumption | 0.98 | 0.999 |  |  |
| process.psa_h2_recovery | 0.9 | fraction H2 | published | 0.88 | 0.92 | https://link.springer.com/content/pdf/10.1007/978-981-19-4767-4_25.pdf | Chapter text reports ammonia-decomposition-gas PSA refining technology with hydrogen recovery of 90% or more. |
| process.psa_specific_electricity_kWh_per_kg | 0.3 | kWh/kg H2 | assumption | 0.05 | 0.6 |  |  |
| process.compressor_efficiency | 0.75 | fraction | assumption | 0.65 | 0.85 |  |  |
| process.compressor_k | 1.4 | Cp/Cv | assumption | 1.3 | 1.41 |  |  |
| process.pump_efficiency | 0.75 | fraction | assumption | 0.6 | 0.85 |  |  |
| process.liquid_NH3_density_kg_per_m3 | 610.0 | kg/m3 | assumption | 580.0 | 680.0 |  |  |
| process.default_catalyst_life_h | 16000.0 | h | assumption | 4000.0 | 40000.0 |  |  |
| process.default_active_metal_loading | 0.1 | kg/kg | assumption | 0.03 | 0.3 |  |  |
| process.catalyst_bulk_density_kg_per_m3 | 800.0 | kg/m3 | assumption | 400.0 | 1400.0 |  |  |
| process.min_per_pass_conversion | 0.05 | fraction | assumption | 0.02 | 0.2 |  |  |
| process.equilibrium_margin | 0.98 | fraction equilibrium | assumption | 0.9 | 0.995 |  |  |
| process.feed_cp_kJ_per_kmolK | 55.0 | kJ/kmol/K | assumption | 40.0 | 75.0 |  |  |
| process.product_cp_kJ_per_kmolK | 35.0 | kJ/kmol/K | assumption | 28.0 | 45.0 |  |  |
| process.cooling_electricity_kWh_per_GJ | 5.0 | kWh/GJ | assumption | 2.0 | 12.0 |  |  |
| process.maximum_pressure_ratio_per_stage | 3.5 | ratio | assumption | 2.5 | 5.0 |  |  |
| capital.fresh_ammonia_pump_ref_usd | 1000000.0 | USD | assumption | 400000.0 | 2500000.0 |  |  |
| capital.recycle_mixer_ref_usd | 500000.0 | USD | assumption | 200000.0 | 1500000.0 |  |  |
| capital.feed_effluent_exchanger_ref_usd | 15000000.0 | USD at 100 MW | assumption | 7000000.0 | 30000000.0 |  |  |
| capital.ammonia_vaporizer_ref_usd | 8000000.0 | USD at 50 MW | assumption | 3000000.0 | 18000000.0 |  |  |
| capital.electric_reactor_furnace_ref_usd | 25000000.0 | USD at 100 MW | assumption | 12000000.0 | 60000000.0 |  |  |
| capital.ammonia_cracking_reactor_ref_usd | 30000000.0 | USD at 100 m3 | assumption | 12000000.0 | 80000000.0 |  |  |
| capital.cracked_gas_compressor_ref_usd | 25000000.0 | USD at 20 MW | assumption | 10000000.0 | 60000000.0 |  |  |
| capital.ammonia_condenser_ref_usd | 10000000.0 | USD at 100 MW | assumption | 4000000.0 | 25000000.0 |  |  |
| capital.ammonia_knockout_ref_usd | 5000000.0 | USD at 1000 kmol/h | assumption | 2000000.0 | 12000000.0 |  |  |
| capital.hydrogen_PSA_ref_usd | 50000000.0 | USD at 73000 t/y | assumption | 20000000.0 | 100000000.0 |  |  |
| capital.hydrogen_product_compressor_ref_usd | 30000000.0 | USD at 20 MW | assumption | 12000000.0 | 75000000.0 |  |  |
| capital.offsites_fraction | 0.15 | fraction direct capex | assumption | 0.08 | 0.3 |  |  |
| capital.scaling_exponent | 0.65 | dimensionless | assumption | 0.55 | 0.75 |  |  |
| capital.minimum_scale_fraction | 0.05 | fraction reference scale | assumption | 0.01 | 0.15 |  |  |
| thermo.deltaCp_rxn_J_per_2molK | 33.3 | J per stoichiometric reaction/K | published | 25.0 | 40.0 | DOI:10.18434/T4D303 | NIST Chemistry WebBook gas heat capacities; effective average for N2 + 3 H2 - 2 NH3 from 298 to 1000 K |
| process.maximum_per_pass_conversion | 0.4 | fraction | assumption | 0.2 | 0.8 |  |  |
| price.metal_Cu | 13.889122517655 | USD/kg | price_table | 6.9445612588275 | 27.77824503531 | prices.json:metal_Cu | prices.metal_Cu |

## 11. Reproducibility artifacts

- `basis.json`: battery limits and physical basis.
- `flowsheet.json` / `flowsheet.md`: accepted unit/stream definition and hash.
- `records.csv`: normalized literature records and usability flags.
- `sources.csv`: parameter provenance and ranges.
- `model.py`: plant model and optimizer.
- `atomic.py`: descriptor microkinetic model.
- `model_check.json`, `atomic_check.json`: passed independent gates.
- `costs.csv`, `analysis.json`: record costs and ranking analysis.
- `sensitivity.json`: deterministic one-at-a-time sensitivity.
- `three_optima.json`: atomic, laboratory and industrial optima and backward design.
- `evidence_debt.json`, `critique.json`: retained uncertainties and independent review responses.

## Final conclusion

Laboratory activity is useful for eliminating weak catalysts, but it is not sufficient to select the industrial operating point. In this evidence base, plant ranking changes mainly when pressure/compression, equilibrium/recycle, catalyst life and catalyst inventory are included. The best measured plant point is a high-pressure promoted Ru/CaO condition rather than the highest laboratory productivity point. Activity is the most important catalyst property, but ammonia feed and purchased energy attenuate its economic value; after a moderate rate is reached, stability and pressure-compatible operation are more valuable than another order of magnitude in differential laboratory activity.