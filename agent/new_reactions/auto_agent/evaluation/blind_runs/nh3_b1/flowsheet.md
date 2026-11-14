boundary N2+H2 -> makeup_compressor -> feed_mixer -> feed_effluent_exchanger -> ammonia_converter -> waste_heat_boiler -> feed_effluent_exchanger -> ammonia_condenser -> ammonia_separator -> liquid NH3 -> product_letdown_storage -> boundary NH3; separator gas -> purge_splitter -> purge boundary + recycle_compressor -> feed_mixer; boundary utilities -> utilities_offsites -> boundary return

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| makeup_compressor | compressor | Compress fresh N2 and H2 from near-ambient battery-limit pressure to synthesis-loop pressure. | fresh_feed | compressed_makeup |
| feed_mixer | other | Mix compressed makeup gas with recompressed recycle gas. | compressed_makeup, compressed_recycle | cold_loop_feed |
| feed_effluent_exchanger | heat_exchanger | Recover converter-effluent sensible heat to preheat synthesis gas without purchased preheat. | cold_loop_feed, hot_recovered_effluent | preheated_feed, cooled_recovered_effluent |
| ammonia_converter | reactor | Adiabatic catalytic fixed-bed conversion of N2 and H2 to NH3 at the catalyst record temperature and optimized per-pass conversion. | preheated_feed | hot_converter_effluent |
| waste_heat_boiler | heat_exchanger | Remove exothermic reaction heat and recover it internally before feed-effluent exchange and condensation. | hot_converter_effluent | hot_recovered_effluent |
| ammonia_condenser | knockout | Cool loop gas and condense synthesized ammonia for phase separation. | cooled_recovered_effluent | two_phase_effluent |
| ammonia_separator | separation | Separate condensed liquid NH3 product from unreacted N2/H2 recycle gas. | two_phase_effluent | liquid_ammonia, separator_gas |
| purge_splitter | other | Purge a small fraction of separator gas to prevent impurity accumulation and send the remainder to recycle. | separator_gas | purge_gas, recycle_gas |
| recycle_compressor | compressor | Restore recycle-loop pressure drop before mixing with makeup feed. | recycle_gas | compressed_recycle |
| product_letdown_storage | other | Let down and condition pressurized liquid ammonia to the product battery-limit state without product compression. | liquid_ammonia | ammonia_product |
| utilities_offsites | offsites | Provide cooling-water circulation, controls, storage allowance, and common synthesis-loop offsites. | utility_supply | utility_return |
