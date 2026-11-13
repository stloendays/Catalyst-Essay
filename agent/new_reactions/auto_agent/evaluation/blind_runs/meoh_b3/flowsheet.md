flowchart LR
CO2[Fresh CO2]-->C1[CO2 feed compressor]
H2[Fresh H2]-->C2[H2 feed compressor]
C1-->M[Mixer]
C2-->M
RC[Recycle compressor]-->M
M-->HX[Feed-effluent exchanger]
HX-->R[Cooled fixed-bed reactor]
R-->HX
HX-->COND[Effluent condenser]
COND-->KO[High-pressure knockout]
KO-->D[Methanol purification]
D-->P[Specification methanol]
D-->WW[Wastewater treatment/offsites]
KO-->S[Purge splitter]
S-->PG[Purge gas]
S-->RC
CW[Cooling-water system]-->COND
COND-->CW

| Unit | Type | Purpose | Inlets | Outlets |
| --- | --- | --- | --- | --- |
| CO2 feed compressor | compressor | Compress purchased CO2 from battery-limit pressure to synthesis pressure. | fresh CO2 | compressed CO2 |
| H2 feed compressor | compressor | Compress purchased hydrogen from battery-limit pressure to synthesis pressure. | fresh H2 | compressed H2 |
| Synthesis feed mixer | other | Mix fresh compressed feeds with compressed recycle gas. | compressed CO2, compressed H2, compressed recycle | mixed synthesis feed |
| Feed effluent exchanger | heat_exchanger | Recover reactor-effluent heat to preheat synthesis feed without purchased preheat. | mixed synthesis feed, hot reactor effluent | preheated synthesis feed, partly cooled reactor effluent |
| Methanol synthesis reactor | reactor | Convert CO2 and H2 to methanol and water in cooled catalyst-filled tubes while also allowing RWGS to CO. | preheated synthesis feed | hot reactor effluent |
| Effluent condenser | heat_exchanger | Cool reactor effluent after heat recovery to condense methanol and water. | partly cooled reactor effluent, cooling water to condenser | two phase effluent, warm cooling water from condenser |
| High pressure knockout | knockout | Separate condensed crude methanol and water from unreacted synthesis gas and CO. | two phase effluent | crude methanol liquid, uncondensed recycle gas |
| Recycle purge splitter | other | Purge CO and feed impurities while returning most unreacted gas to synthesis. | uncondensed recycle gas | purge gas, recycle gas |
| Recycle compressor | compressor | Restore recycle-loop pressure drop before remixing recycle with fresh feeds. | recycle gas | compressed recycle |
| Methanol purification | separation | Distill crude condensate to specification methanol and an aqueous bottoms stream. | crude methanol liquid | specification methanol, aqueous bottoms |
| Cooling water system | offsites | Supply and reject condenser cooling duty through the plant cooling-water utility. | cooling water makeup, warm cooling water from condenser | cooling water to condenser, cooling water blowdown |
| Wastewater treatment and plant offsites | offsites | Treat aqueous methanol-process bottoms and account for common plant infrastructure. | aqueous bottoms | treated aqueous discharge |
