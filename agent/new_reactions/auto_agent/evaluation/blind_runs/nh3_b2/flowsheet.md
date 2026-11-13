H2 -> hydrogen_feed_compressor --\n                                  > synthesis_gas_mixer -> feed_effluent_exchanger -> ammonia_converter -> waste_heat_boiler -> feed_effluent_exchanger -> final_product_cooler -> ammonia_knockout -> liquid NH3 -> product_and_offsites -> product\nN2 -> nitrogen_feed_compressor --/                                                                                                                         \-> gas -> purge_splitter -> purge + recycle_compressor --recycle--> mixer

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| hydrogen_feed_compressor | compressor | Compress purchased hydrogen from battery-limit pressure to synthesis-loop pressure | hydrogen_feed | compressed_hydrogen |
| nitrogen_feed_compressor | compressor | Compress purchased nitrogen from battery-limit pressure to synthesis-loop pressure | nitrogen_feed | compressed_nitrogen |
| synthesis_gas_mixer | other | Combine stoichiometric fresh feeds with unreacted recycle gas | compressed_hydrogen, compressed_nitrogen, compressed_recycle | loop_feed |
| feed_effluent_exchanger | heat_exchanger | Recover converter-effluent sensible heat to preheat synthesis-loop feed | loop_feed, boiler_cooled_effluent | preheated_loop_feed, heat_recovered_effluent |
| ammonia_converter | reactor | Catalytically convert nitrogen and hydrogen to ammonia in an equilibrium-limited multibed converter | preheated_loop_feed | hot_converter_effluent |
| waste_heat_boiler | heat_exchanger | Remove exothermic reaction heat and recover it as useful steam-equivalent heat | hot_converter_effluent | boiler_cooled_effluent |
| final_product_cooler | heat_exchanger | Cool synthesis gas sufficiently to condense ammonia for phase separation | heat_recovered_effluent | partly_condensed_effluent |
| ammonia_knockout | knockout | Separate condensed liquid ammonia from unreacted hydrogen and nitrogen | partly_condensed_effluent | liquid_ammonia, unreacted_loop_gas |
| purge_splitter | other | Remove a small purge to prevent accumulation of feed impurities and route the remainder to recycle | unreacted_loop_gas | purge_gas, recycle_gas |
| recycle_compressor | compressor | Restore recycle-gas pressure losses before remixing with fresh synthesis gas | recycle_gas | compressed_recycle |
| product_and_offsites | offsites | Provide synthesis-loop utility distribution, controls, storage allowance, and product battery-limit handling | liquid_ammonia | ammonia_product |
