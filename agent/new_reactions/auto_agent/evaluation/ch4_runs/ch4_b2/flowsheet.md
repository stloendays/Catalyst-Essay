flowchart LR
  CO2[Fresh CO2] --> C1[CO2 feed compressor]
  H2[Fresh H2] --> C2[H2 feed compressor]
  C1 --> M[feed mixer]
  C2 --> M
  RC[recycle compressor] --> M
  M --> HX[feed effluent heat exchanger]
  HX --> TH[trim heater]
  TH --> R[cooled methanation reactor]
  R --> HX
  HX --> KO[effluent cooler and water knockout]
  KO --> SEP[methane purification membrane]
  SEP --> PC[product compressor]
  PC --> OS[offsites and utilities]
  SEP --> RC
  SEP --> OS
  KO --> OS
  OS --> CH4[export methane]

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| CO2 feed compressor | compressor | pressurise fresh CO2 from boundary pressure to reactor loop pressure | fresh CO2 | compressed CO2 |
| H2 feed compressor | compressor | pressurise fresh hydrogen from boundary pressure to reactor loop pressure | fresh H2 | compressed H2 |
| feed mixer | other | combine compressed fresh feeds with recycle gas | compressed CO2, compressed H2, compressed recycle gas | mixed feed |
| feed effluent heat exchanger | heat_exchanger | recover hot reactor effluent heat to preheat mixed feed | mixed feed, hot reactor effluent | preheated reactor feed, cooled reactor effluent |
| trim heater | furnace | raise preheated feed to selected reactor inlet temperature when heat recovery is insufficient | preheated reactor feed | reactor feed |
| cooled methanation reactor | reactor | convert CO2 and H2 to methane and water over the selected catalyst while removing exothermic heat | reactor feed | hot reactor effluent |
| effluent cooler and water knockout | knockout | cool effluent, condense and remove produced water before gas purification/recycle | cooled reactor effluent | dry product gas, wastewater |
| methane purification membrane | separation | separate methane product from unreacted CO2/H2 and light byproducts for recycle and purge | dry product gas | raw methane product, recycle-rich gas, purge gas |
| product compressor | compressor | compress purified methane product to pipeline delivery pressure | raw methane product | sales methane |
| recycle compressor | compressor | restore recycle-rich gas pressure after separation pressure drop and return it to the reactor loop | recycle-rich gas | compressed recycle gas |
| offsites and utilities | offsites | cooling water, boiler feedwater, flare/thermal oxidizer for purge, controls, wastewater handling and balance-of-plant services | wastewater, purge gas, sales methane | export methane, treated wastewater, stack |
