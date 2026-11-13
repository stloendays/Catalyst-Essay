flowchart LR; CO2[Fresh CO2]-->C1[CO2 feed compressor]; H2[Fresh H2]-->C2[H2 feed compressor]; C1-->M[Feed mixer]; C2-->M; RC[Recycle compressor]-->M; M-->HX[Feed-effluent heat exchanger]; HX-->EH[Electric trim preheater]; EH-->R[Cooled fixed-bed reactor]; R-->HX; HX-->KO[Effluent condenser and knockout]; KO-->L[Crude liquid]; KO-->G[Separator gas]; G-->SP[Recycle purge splitter]; SP-->PG[Purge boundary]; SP-->RC; L-->D[Methanol purification column]; D-->W[Aqueous bottoms boundary]; D-->P[Methanol product pump]; P-->O[Product storage and offsites]; O-->MP[Methanol product boundary]

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| CO2 feed compressor | compressor | Compress fresh captured CO2 from the battery-limit pressure to reactor pressure. | fresh CO2 | compressed CO2 |
| H2 feed compressor | compressor | Compress fresh hydrogen from the battery-limit pressure to reactor pressure. | fresh H2 | compressed H2 |
| Feed mixer | other | Combine fresh CO2, fresh H2 and compressed recycle gas at the selected stoichiometric feed ratio. | compressed CO2, compressed H2, compressed recycle | mixed reactor feed |
| Feed-effluent heat exchanger | heat_exchanger | Recover sensible heat from reactor effluent to preheat the mixed reactor feed. | mixed reactor feed, hot reactor effluent | recovered preheated feed, partly cooled effluent |
| Electric trim preheater | heat_exchanger | Supply only the residual sensible heat needed to reach catalyst inlet temperature, including startup capability. | recovered preheated feed | reactor inlet feed |
| Cooled fixed-bed reactor | reactor | Convert CO2 and H2 to methanol and water while removing exothermic reaction heat by boiling-water cooling. | reactor inlet feed | hot reactor effluent |
| Effluent condenser and knockout | knockout | Cool reactor effluent and condense crude methanol, water and a small pressure-dependent dissolved CO2 load from unreacted gas and CO byproduct. | partly cooled effluent | crude methanol liquid, separator gas |
| Recycle purge splitter | other | Purge CO and feed impurities while returning most uncondensed CO2 and H2 to the reactor loop. | separator gas | purge gas, recycle gas |
| Recycle compressor | compressor | Restore recycle gas pressure after loop pressure drop. | recycle gas | compressed recycle |
| Methanol purification column | separation | Purify condensed crude methanol to the product specification and reject reaction water, methanol loss and dissolved CO2. | crude methanol liquid | purified methanol, aqueous bottoms |
| Methanol product pump | pump | Deliver liquid methanol from column pressure to the specified product battery-limit pressure. | purified methanol | pressurized methanol |
| Product storage and offsites | offsites | Provide product storage, cooling-water circulation, electrical distribution and balance-of-plant services. | pressurized methanol | methanol product |
