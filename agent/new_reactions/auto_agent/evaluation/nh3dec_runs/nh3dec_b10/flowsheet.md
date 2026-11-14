flowchart LR
  NH3[Fresh liquid NH3] --> C[Fresh ammonia conditioner]
  C --> M[Feed/recycle mixer]
  K[Ammonia knockout] --> P[Recycle pump/vaporizer]
  P --> M
  M --> HX[Feed-effluent exchanger]
  HX --> R[Tubular fixed-bed reactor]
  F[Fired heater] -->|hot flue gas heat| R
  R --> HX
  HX --> RC[Refrigeration condenser]
  RC --> K
  K --> PSA[Hydrogen PSA]
  PSA --> HC[H2 product compressor]
  HC --> H2[30 bar high-purity H2]
  PSA --> TS[Tail-gas splitter]
  TS --> F
  TS --> PURGE[N2-rich purge]
  NG[Natural gas + oxygen] --> F
  R --> FLUE[Cooled flue gas]
  U[Utility offsites] -. cooling/refrigeration duty .-> RC
  U -. electricity duty .-> HC

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| fresh_ammonia_conditioner | other | Let down delivered liquid ammonia to reactor pressure and provide controlled vaporisation before mixing with recycle. | fresh_nh3 | conditioned_fresh_nh3 |
| feed_recycle_mixer | other | Combine fresh ammonia with recovered unconverted ammonia recycle. | conditioned_fresh_nh3, recycle_nh3_vapor | mixed_ammonia_feed |
| feed_effluent_exchanger | heat_exchanger | Recover sensible heat from reactor effluent to preheat mixed ammonia feed and reduce purchased furnace duty. | mixed_ammonia_feed, hot_reactor_effluent | preheated_ammonia_feed, partly_cooled_effluent |
| fired_heater | furnace | Burn PSA tail hydrogen with purchased natural-gas backup and supplied oxygen to provide endothermic reactor heat. | psa_tail_fuel, purchased_natural_gas, combustion_oxygen | hot_furnace_flue_gas |
| tubular_fixed_bed_reactor | reactor | Decompose ammonia over packed catalyst in externally heated tubes at the optimized temperature and per-pass conversion. | preheated_ammonia_feed, hot_furnace_flue_gas | hot_reactor_effluent, cooled_flue_gas |
| refrigeration_condenser | heat_exchanger | Cool cracked gas to the basis refrigeration temperature for partial NH3 condensation; the modeled recovery is an uncertain split varied from zero to near-complete recovery. | partly_cooled_effluent | chilled_two_phase_effluent |
| ammonia_knockout | knockout | Separate condensed unconverted ammonia from the hydrogen-nitrogen gas. | chilled_two_phase_effluent | recovered_liquid_nh3, raw_h2_n2_gas |
| recycle_pump_vaporizer | pump | Pressurize and revaporize recovered ammonia for recycle to the feed mixer. | recovered_liquid_nh3 | recycle_nh3_vapor |
| hydrogen_psa | separation | Vacuum-pressure-swing adsorption (VPSA) at low feed pressure to recover high-purity hydrogen from nitrogen-rich cracked gas; packaged vacuum/compression power is included in this separation unit. | raw_h2_n2_gas | low_pressure_h2_product, psa_tail_gas |
| tail_gas_splitter | other | Send the combustible fraction of PSA tail gas to the fired heater and purge the remaining nitrogen-rich gas to prevent inert accumulation. | psa_tail_gas | psa_tail_fuel, nitrogen_rich_purge |
| hydrogen_product_compressor | compressor | Compress purified hydrogen from PSA pressure to the specified product delivery pressure. | low_pressure_h2_product | compressed_h2_product |
| utility_offsites | offsites | Provide plant cooling-water circulation and account for common utility and auxiliary facilities. | cooling_water_makeup | cooling_water_return |
