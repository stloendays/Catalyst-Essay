flowchart LR
  FP[fresh propane]-->COMP[fresh_propane_pressurisation]
  COMP-->MIX[recycle_mixer]
  SPLIT[C3_splitter]--propane recycle-->MIX
  MIX-->VAP[feed_vaporiser]
  VAP-->FEE[feed_effluent_exchanger]
  FEE-->FURN[charge_furnace]
  FURN-->RXN[PDH_reactor]
  RXN--hot effluent-->FEE
  RXN--spent catalyst-->REG[catalyst_regenerator]
  REG--regenerated catalyst-->RXN
  FEE-->KO[effluent_cooler_knockout]
  KO-->PC[product_compressor]
  PC-->H2SEP[hydrogen_recovery]
  H2SEP-->H2[hydrogen product]
  H2SEP-->SPLIT
  SPLIT-->PP[propylene product]
  SPLIT-->PURGE[purge/fuel propane byproduct]
  FURN-->OFF[utilities_offsites]
  REG-->OFF

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| fresh_propane_pressurisation | compressor | raise fresh propane to reactor-loop pressure | fresh_propane | pressurised_fresh_propane |
| recycle_mixer | other | mix fresh propane with recovered propane recycle | pressurised_fresh_propane, propane_recycle | mixed_propane_feed |
| feed_vaporiser | heat_exchanger | vaporise and warm liquid propane feed before heat recovery | mixed_propane_feed | vapour_feed |
| feed_effluent_exchanger | heat_exchanger | recover sensible heat from hot reactor effluent to preheat feed | vapour_feed, hot_reactor_effluent | preheated_feed, partly_cooled_effluent |
| charge_furnace | furnace | supply endothermic PDH heat and final preheat to reactor inlet temperature | preheated_feed, fuel_gas | reactor_feed, flue_gas |
| PDH_reactor | reactor | non-oxidative propane dehydrogenation to propylene and hydrogen | reactor_feed, regenerated_catalyst | hot_reactor_effluent, spent_catalyst |
| catalyst_regenerator | regenerator | periodically burn coke and restore catalyst activity; costed as regeneration/replacement allowance | spent_catalyst, regeneration_air | regenerated_catalyst, regeneration_flue_gas |
| effluent_cooler_knockout | knockout | cool reactor effluent after heat recovery and remove condensable C3 liquid from light gas | partly_cooled_effluent, cooling_water | cooled_effluent, cooling_water_return |
| product_compressor | compressor | compress cooled reactor effluent to downstream separation pressure | cooled_effluent | compressed_effluent |
| hydrogen_recovery | separation | remove hydrogen-rich light gas before C3 splitter | compressed_effluent | hydrogen_product, C3_liquid |
| C3_splitter | separation | separate polymer-grade propylene product from unreacted propane recycle | C3_liquid | propylene_product, propane_recycle, purge_propane_byproduct |
| utilities_offsites | offsites | cooling water, flare, controls, storage, and balance-of-plant capital/utility allowance | flue_gas, regeneration_flue_gas, cooling_water_return | stack_gas, wastewater |
