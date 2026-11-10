# Plant-model parameters and their sources (2026-11-10)

Values in `params_process.json`; metal prices from the repository's frozen sets (`build_params.py`).
Sources were read by a research subagent; (S) marks values seen only in a search summary.

## PDH

| parameter | source |
|---|---|
| propane_usd_t | EIA Mont Belvieu propane spot 2024 0.778 USD/gal at 4.2 lb/gal = 408 USD/t |
| reference X, S | Oleflex: 86 % selectivity at 40 % single-pass conversion (Dong, Altvater, Mark, Hermans, OSTI 1866245, p17); propane use 1.2 lb per lb propylene (PetroLogistics SEC 424B4 2012) = S 0.873 |
| reference T | Oleflex 525-705 C, 1-3 bar (Moffat PhD thesis, Glasgow 2023, p5); 640 C and 1.5 bar chosen inside that window |
| h2_ratio | assumption (not found in an open source) |
| t_cycle_h | Oleflex CCR cycle 5-8 days (Dong et al. p17): 6.5 d |
| catalyst_life_y | reactor catalyst replaced about every three years (PetroLogistics SEC 424B4) |
| capex | 1.30 bn USD (Dec 2012) for 1.654 bn lb/y = 750 kt/y, annualised at 7 %, 20 y (Enterprise Products PDH, EPA GHG permit application) |
| e_proc_GJ_per_t_feed | calibrated so that the reference plant buys 17.5 GJ natural gas per t propylene after burning its own H2 and light ends (PetroLogistics: 9.96 M MMBtu for ~601 kt propylene) |
| power_kWh_per_t_feed | calibrated to PetroLogistics fuel + utilities 35.4 M USD/y minus gas 25.9 M USD/y = ~16 USD/t propylene at 0.08 USD/kWh |
| reference r, Pt 0.3 wt%, Sn 0.3 wt% | assumption (Oleflex Pt loading not in an open source; '<1 wt%' search summary only) |
| thermo | dH298 124.3 kJ/mol (Moffat Eq. 1); equilibrium fit as noted |

## CH4

| parameter | source |
|---|---|
| plant | 2-5 adiabatic stages with intercooling, 200-550 C, 20 bar reference case; >= 98 % CO2 conversion needs <300 C at 20 bar in the last stage (Goetz et al., Renew. Energy 85 (2016) 1371) |
| capex | 175 EUR/kW_SNG (Goetz 2016, consistent with Outotec; range 130 EUR/kW at 110 MW to 400 EUR/kW at 5 MW) x 1.33 USD/EUR (2014) x 96.4 MW_SNG (50 kt/y CH4 at 8000 h, HHV) |
| reference r | GHSV 3500 h-1 inside the 2000-5000 h-1 of technical adiabatic fixed beds (Goetz Table 4), 20 % CO2 in the feed, bed density 1.0 kg/L (assumption), X 0.80 -> 0.40 kg CH4/kg/h |
| h2_usd_kg | 3 USD/kg: the anchor of Becker, Penev & Braun, J. Energy Resour. Technol. 2019 (132 USD/MWh SNG); grey ~2, electrolytic 5-7 (DOE Liftoff 2024) |
| co2_usd_t | 104 USD/t CO2 captured (Enterprise Products EPA application 2012) rounded to 100 |
| catalyst | Ni 20 wt%, base 20 USD/kg, life 4 y: assumptions (no open source found) |
| thermo | standard formation data, dH298 -165.0 kJ/mol, dG298 -113.5 kJ/mol |

## Common

crf 0.0944 = 7 %/y over 20 y (Enterprise Products PDH, EPA GHG permit application 2012). gas 2.5 USD/GJ = 2.60 USD/MMBtu paid by the PetroLogistics Catofin plant (SEC 424B4, 2012); Henry Hub 2024 2.19 USD/MMBtu (EIA). fixed O&M 4 %/y of capex, power 0.08 USD/kWh, metal recovery 0.95 and financing 0.08/y: assumptions as in the NH3/methanol chains.

## URLs

- Moffat PhD thesis, Glasgow 2023: https://theses.gla.ac.uk/83545/3/2022MoffatPhD.pdf
- Dong, Altvater, Mark, Hermans (OSTI 1866245): https://www.osti.gov/servlets/purl/1866245
- PetroLogistics LP SEC 424B4 (2012): https://www.sec.gov/Archives/edgar/data/1523733/000104746912005401/a2209406z424b4.htm
- Enterprise Products PDH, EPA GHG permit application (2012): https://archive.epa.gov/region6/6pd/air/pd-r/ghg/web/pdf/enterprise-propane-dehydrogenation-app.pdf
- EIA Mont Belvieu propane spot: https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EER_EPLLPA_PF4_Y44MB_DPG&f=A
- EIA Henry Hub: https://www.eia.gov/dnav/ng/hist/rngwhhdA.htm
- USGS MCS 2025 PGM / gallium / chromium: https://pubs.usgs.gov/periodicals/mcs2025/
- Goetz et al., Renew. Energy 85 (2016) 1371, doi 10.1016/j.renene.2015.07.066
- Becker, Penev, Braun, J. Energy Resour. Technol. 2019, doi 10.1115/1.4041381 (S, abstract)
- DOE Clean Hydrogen Liftoff, Dec 2024 update (S)
