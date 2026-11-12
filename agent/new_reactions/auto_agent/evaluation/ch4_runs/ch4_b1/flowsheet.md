flowchart LR
  CO2[Fresh CO2] --> C1[CO2 feed compressor]
  H2[Fresh H2] --> C2[H2 feed compressor]
  C1 --> M[Feed mixer]
  C2 --> M
  RC[Recycle compressor] --> M
  M --> HX[Feed-effluent heat exchanger]
  HX --> TH[Trim feed heater]
  TH --> R[Methanation reactor]
  R --> HX
  BFW[Boiler feed water] --> WHB[Reactor heat recovery]
  WHB --> U[Utilities/offsites]
  HX --> KO[Product cooler condenser]
  KO --> SEP[Gas separation]
  KO --> W[Waste water]
  SEP --> RC
  SEP --> PC[Product compressor]
  PC --> P[Pipeline methane]
  SEP --> U

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| CO2 feed compressor | compressor | Pressurise fresh CO2 feed from battery limit to reactor loop pressure. | fresh CO2 | compressed CO2 |
| H2 feed compressor | compressor | Pressurise fresh hydrogen feed from battery limit to reactor loop pressure. | fresh H2 | compressed H2 |
| Feed mixer | other | Mix compressed fresh feeds with recycle gas to the reactor stoichiometric feed ratio. | compressed CO2, compressed H2, recycle gas compressed | mixed feed |
| Feed effluent heat exchanger | heat_exchanger | Recover hot reactor effluent sensible heat to preheat mixed reactor feed. | mixed feed, hot reactor effluent | preheated feed, partly cooled effluent |
| Trim feed heater | furnace | Add any remaining heat needed to reach catalyst inlet temperature during startup or low heat-recovery operation. | preheated feed | reactor feed |
| Methanation reactor | reactor | Cooled packed-bed catalytic reactor converting CO2 and H2 to methane and water; catalyst inventory is set by literature activity and conversion target is limited by equilibrium. | reactor feed | hot reactor effluent |
| Reactor heat recovery | heat_exchanger | Remove the exothermic methanation heat from the reactor by generating steam from boiler feed water; thermal coupling to the reactor is represented in the model duty. | boiler feed water | export steam |
| Product cooler condenser | knockout | Cool reacted gas below its dew point and condense liquid water produced by methanation. | partly cooled effluent | dry gas, condensed water |
| Gas separation | separation | Separate methane product from unreacted H2 and CO2 and carbon monoxide byproduct; recover unreacted reactants for recycle and reject a purge. | dry gas | raw methane product, recycle gas, purge gas |
| Recycle compressor | compressor | Restore pressure lost through the reactor, coolers and separator for the recycle gas. | recycle gas | recycle gas compressed |
| Product compressor | compressor | Compress methane product from separation pressure to pipeline delivery pressure. | raw methane product | pipeline methane |
| Utilities and offsites | offsites | Cooling water, steam system, controls, flare/vent handling and plant infrastructure supporting all process units. | condensed water, purge gas, export steam | waste water, vent, utility condensate |
