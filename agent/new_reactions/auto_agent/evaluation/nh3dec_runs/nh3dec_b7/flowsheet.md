flowchart LR
B1[Boundary NH3] --> U1[Fresh NH3 pump] --> U2[Feed-recycle mixer] --> U3[Feed-effluent recuperator] --> U4[Vaporizer/trim heater] --> U5[Electric furnace] --> U6[Packed-bed reactor]
U6 -->|hot effluent| U3
U3 --> U7[NH3 condenser] --> U8[Knockout drum]
U8 -->|liquid NH3| U9[Recycle pump] --> U2
U8 -->|H2/N2 gas| U10[Hydrogen PSA]
U10 -->|H2| U11[Product compressor] --> B2[Boundary H2]
U10 -->|tail gas| U12[Utilities/offsites] --> B3[Boundary tail gas]

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| U1 Fresh ammonia pump | pump | Raise liquid fresh ammonia to the reactor-loop pressure and overcome plant pressure losses. | fresh_NH3 | pressurized_fresh_NH3 |
| U2 Feed-recycle mixer | other | Combine pressurized fresh ammonia with recovered liquid ammonia recycle. | pressurized_fresh_NH3, recycle_NH3 | mixed_liquid_NH3 |
| U3 Feed-effluent recuperator | heat_exchanger | Recover reactor-effluent sensible heat to warm and partly vaporize the mixed ammonia feed. | mixed_liquid_NH3, hot_reactor_effluent | recuperated_NH3, cooled_reactor_effluent |
| U4 Ammonia vaporizer and trim heater | heat_exchanger | Complete ammonia vaporization and provide controlled feed temperature with electric trim heat when recuperation is insufficient. | recuperated_NH3 | vaporized_NH3 |
| U5 Electric reaction furnace | furnace | Supply feed superheat and the endothermic reaction duty to the externally heated reactor tubes. | vaporized_NH3 | furnace_heated_NH3 |
| U6 Packed-bed ammonia decomposition reactor | reactor | Convert ammonia over the selected literature catalyst to nitrogen and hydrogen at optimized temperature and per-pass conversion. | furnace_heated_NH3 | hot_reactor_effluent |
| U7 Ammonia condenser | heat_exchanger | Cool recuperator effluent and condense residual ammonia using cooling water. | cooled_reactor_effluent | two_phase_effluent |
| U8 Ammonia knockout drum | knockout | Separate condensed ammonia from the hydrogen-nitrogen product gas. | two_phase_effluent | recovered_liquid_NH3, crude_H2_N2_gas |
| U9 Ammonia recycle pump | pump | Return recovered liquid ammonia to the feed mixer and restore recycle-loop pressure loss. | recovered_liquid_NH3 | recycle_NH3 |
| U10 Hydrogen PSA | separation | Recover high-purity hydrogen from nitrogen, residual ammonia, and unrecovered hydrogen. | crude_H2_N2_gas | purified_H2, PSA_tail_gas |
| U11 Hydrogen product compressor | compressor | Compress purified hydrogen from reactor-loop pressure to the battery-limit delivery pressure. | purified_H2 | compressed_product_H2 |
| U12 Utilities and offsites | offsites | Provide cooling-water circulation, electrical distribution, controls, and safe handling of the nitrogen-rich PSA tail gas. | PSA_tail_gas | N2_rich_tail_gas |
