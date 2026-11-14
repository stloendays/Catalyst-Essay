CO2 -> [CO2 Feed Compressor] --\
                                  > [Feed Mixer] -> [Feed-Effluent Exchanger] -> [Synthesis Reactor] -> [Reactor Heat Management] --hot side--> [Feed-Effluent Exchanger] -> [Effluent Cooler] -> [Condensate Knockout] --liquid--> [Crude Methanol Distillation] -> CH3OH product
H2  -> [H2 Feed Compressor] --/                                                                                                                                        |                                      \-> [Utilities and Offsites] -> treated water
                                                                                                                                                                      \--gas--> [Recycle Purge Splitter] --purge--> boundary
                                                                                                                                                                                        \-> [Recycle Compressor] -> recycle to Feed Mixer

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| CO2 Feed Compressor | compressor | Compress purchased CO2 from delivery pressure to synthesis-loop pressure. | co2_feed | compressed_co2 |
| H2 Feed Compressor | compressor | Compress purchased hydrogen from delivery pressure to synthesis-loop pressure. | h2_feed | compressed_h2 |
| Feed Mixer | other | Combine fresh CO2 and H2 with compressed recycle gas at the reactor feed ratio. | compressed_co2, compressed_h2, recycle_compressed | mixed_feed |
| Feed-Effluent Exchanger | heat_exchanger | Recover reactor-effluent sensible heat to preheat the mixed synthesis feed. | mixed_feed, temperature_controlled_effluent | preheated_feed, heat_recovered_effluent |
| Synthesis Reactor | reactor | Convert CO2 and H2 to methanol and water with concurrent reverse water-gas shift over the selected catalyst. | preheated_feed | reactor_effluent |
| Reactor Heat Management | heat_exchanger | Supply or remove net reaction heat to control the multi-bed reactor temperature, recovering useful heat when the net chemistry is exothermic. | reactor_effluent | temperature_controlled_effluent |
| Effluent Cooler | heat_exchanger | Cool heat-recovered effluent to condense methanol and water before phase separation. | heat_recovered_effluent | cooled_effluent |
| Condensate Knockout | knockout | Separate condensed crude methanol-water liquid from uncondensed H2, CO2 and CO-rich recycle gas. | cooled_effluent | crude_methanol, uncondensed_gas |
| Recycle Purge Splitter | other | Purge a controlled fraction of uncondensed gas to prevent CO and impurity accumulation and send the remainder to recycle. | uncondensed_gas | purge_gas, recycle_gas |
| Recycle Compressor | compressor | Restore recycle gas pressure losses before remixing with fresh feeds. | recycle_gas | recycle_compressed |
| Crude Methanol Distillation | separation | Purify crude condensate to specification methanol and reject a water-rich bottoms stream. | crude_methanol | methanol_product, water_bottoms |
| Utilities and Offsites | offsites | Provide common cooling, steam, electrical distribution and wastewater handling and account for associated installed facilities. | water_bottoms | treated_water |
