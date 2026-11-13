flowchart LR
 B1[Boundary NH3] --> M[recycle_mixer] --> V[ammonia_vaporizer] --> HX[feed_effluent_recuperator] --> EH[electric_trim_heater] --> R[ammonia_decomposition_reactor] --> HX
 HX --> C[effluent_chiller] --> K[ammonia_knockout]
 K --> P[ammonia_recycle_pump] --> M
 K --> PSA[hydrogen_psa] --> HC[hydrogen_product_compressor] --> B2[Boundary H2]
 PSA --> O[tailgas_and_offsites] --> B3[Boundary N2-rich offgas]

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| ammonia_vaporizer | heat_exchanger | Vaporize combined fresh and recycled liquid ammonia before heat recovery | mixed_liquid_ammonia | mixed_ammonia_feed |
| recycle_mixer | other | Mix delivered liquid ammonia with recovered liquid ammonia recycle | fresh_liquid_ammonia, pressurized_ammonia_recycle | mixed_liquid_ammonia |
| feed_effluent_recuperator | heat_exchanger | Recover reactor effluent sensible heat into the mixed ammonia feed | mixed_ammonia_feed, hot_reactor_effluent | recuperated_ammonia_feed, partly_cooled_reactor_effluent |
| electric_trim_heater | furnace | Supply feed trim heat and externally supplied reactor endothermic duty electrically | recuperated_ammonia_feed | hot_ammonia_feed |
| ammonia_decomposition_reactor | reactor | Decompose ammonia to hydrogen and nitrogen over a packed catalyst bed | hot_ammonia_feed | hot_reactor_effluent |
| effluent_chiller | heat_exchanger | Cool recuperated effluent to condense unreacted ammonia | partly_cooled_reactor_effluent | chilled_reactor_effluent |
| ammonia_knockout | knockout | Separate condensed unreacted ammonia from hydrogen and nitrogen product gas | chilled_reactor_effluent | liquid_ammonia_recycle, ammonia_depleted_gas |
| ammonia_recycle_pump | pump | Return condensed ammonia to feed pressure | liquid_ammonia_recycle | pressurized_ammonia_recycle |
| hydrogen_psa | separation | Produce high-purity hydrogen from nitrogen-rich cracked gas while rejecting residual ammonia | ammonia_depleted_gas | low_pressure_hydrogen, psa_tail_gas |
| hydrogen_product_compressor | compressor | Compress purified hydrogen to the battery-limit delivery pressure | low_pressure_hydrogen | compressed_hydrogen_product |
| tailgas_and_offsites | offsites | Handle nitrogen-rich PSA tail gas and provide plant controls, cooling circulation and common facilities | psa_tail_gas | nitrogen_rich_offgas |
