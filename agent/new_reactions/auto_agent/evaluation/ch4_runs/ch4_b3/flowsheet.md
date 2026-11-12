flowchart LR
  CO2[CO2 feed] --> C1[CO2 feed compressor]
  H2[H2 feed] --> C2[H2 feed compressor]
  REC[recycle gas] --> RC[Recycle compressor]
  C1 --> M[Feed mixer]
  C2 --> M
  RC --> M
  M --> HX[Feed-effluent heat exchanger]
  HX --> PH[Trim preheater]
  PH --> R[Cooled methanation reactor]
  R --> HX
  HX --> KO[Effluent cooler and water knockout]
  KO --> SEP[Methane purification membrane]
  KO --> W[Waste water]
  SEP --> PC[Product compressor]
  PC --> PROD[Methane product]
  SEP --> SPL[Recycle purge splitter]
  SPL --> REC
  SPL --> PURGE[Purge gas]
  W --> OS[Utilities and offsites]
  PURGE --> OS
  OS --> OUT[vent and wastewater]

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| CO2 feed compressor | compressor | pressurise purchased dry CO2 feed to methanation loop pressure | CO2 feed | compressed CO2 |
| H2 feed compressor | compressor | pressurise purchased dry H2 feed to methanation loop pressure | H2 feed | compressed H2 |
| Recycle compressor | compressor | restore pressure of recycled unreacted gas after separation and purge | recycle gas | compressed recycle |
| Feed mixer | other | mix fresh CO2, fresh H2 and recycle to the reactor feed ratio | compressed CO2, compressed H2, compressed recycle | mixed feed |
| Feed effluent heat exchanger | heat_exchanger | recover reactor effluent sensible heat to preheat mixed feed | mixed feed, hot reactor effluent | preheated feed, cooled reactor effluent |
| Trim preheater | furnace | raise feed from heat-recovery outlet to reactor inlet temperature during start-up or low heat recovery | preheated feed | reactor feed |
| Cooled methanation reactor | reactor | convert CO2 and H2 to CH4 and water over the literature catalyst while removing exothermic heat | reactor feed | hot reactor effluent |
| Effluent cooler and water knockout | knockout | cool reacted gas below the water dew point and remove liquid water | cooled reactor effluent | dry gas, waste water |
| Methane purification membrane | separation | recover pipeline-grade CH4-rich product from unreacted CO2/H2 and any CO byproduct | dry gas | raw methane product, tail gas |
| Product compressor | compressor | compress purified methane product to delivery pressure | raw methane product | methane product |
| Recycle purge splitter | separation | split tail gas into a small purge that prevents inert/byproduct buildup and a recycle stream | tail gas | purge gas, recycle gas |
| Utilities and offsites | offsites | cooling water, instrument air, controls, flare, wastewater handling and site infrastructure | purge gas, waste water | vent and wastewater |
