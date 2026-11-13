flowchart LR
H2[H2 feed] --> C1[H2 feed compressor]
N2[N2 feed] --> C2[N2 feed compressor]
C1 --> M1[makeup gas mixer]
C2 --> M1
M1 --> M2[loop feed mixer]
RC[recycle compressor] --> M2
M2 --> HX[feed-effluent heat exchanger]
HX --> EH[recovered-heat trim exchanger]
EH --> R[ammonia synthesis reactor]
R --> HX
HX --> S[ammonia condenser separator]
S --> L[NH3 product letdown]
L --> P[NH3 product]
S --> PS[purge splitter]
PS --> RC
PS --> O[purge handling and offsites]
O --> V[treated purge]

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| H2 feed compressor | compressor | Compress purified hydrogen from battery-limit pressure to synthesis-loop pressure | H2 feed | compressed H2 |
| N2 feed compressor | compressor | Compress purified nitrogen from battery-limit pressure to synthesis-loop pressure | N2 feed | compressed N2 |
| makeup gas mixer | other | Combine stoichiometric compressed makeup hydrogen and nitrogen | compressed H2, compressed N2 | makeup gas |
| loop feed mixer | other | Combine makeup gas with compressed recycle gas | makeup gas, compressed recycle gas | combined loop feed |
| feed effluent heat exchanger | heat_exchanger | Recover reactor-effluent sensible heat into the combined loop feed | combined loop feed, temperature-controlled reactor effluent | preheated loop feed, cooled reactor effluent |
| recovered-heat trim exchanger | heat_exchanger | Use recovered reactor heat or steam to supply residual steady-state feed preheat without purchased fuel | preheated loop feed | reactor feed |
| ammonia synthesis reactor | reactor | Convert N2 and H2 to NH3 in multiple fixed catalyst beds with interbed heat removal | reactor feed | hot reactor effluent |
| interbed heat recovery exchanger | heat_exchanger | Represent integrated interbed cooling and converter outlet steam generation for temperature control | hot reactor effluent | temperature-controlled reactor effluent |
| ammonia condenser separator | separation | Cool the high-pressure loop gas, condense NH3, and separate liquid ammonia from unreacted gas | cooled reactor effluent | crude liquid ammonia, separator gas |
| purge splitter | other | Purge a small gas fraction to prevent accumulation of feed impurities while sending the balance to recycle | separator gas | purge gas, recycle gas |
| recycle compressor | compressor | Restore recycle-gas pressure losses and return unreacted N2 and H2 to the loop | recycle gas | compressed recycle gas |
| NH3 product letdown | other | Reduce liquid-ammonia pressure to the product battery-limit pressure | crude liquid ammonia | NH3 product |
| purge handling and offsites | offsites | Safely meter and route the small hydrogen-rich purge and provide loop electrical/cooling-water infrastructure | purge gas | treated purge |
