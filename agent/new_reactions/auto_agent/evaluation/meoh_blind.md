# MEOH blind evaluation

Loader: 699/699; rejected 0.

| Hand convention | Changed/groups | >5% | Paper bootstrap 95% CI |
|---|---:|---:|---|
| fixed_conversion | 26/63 | 19 | [0.2908827404479578, 0.5312752016129031] |
| raised_conversion | 21/63 | 10 | [0.22033050847457628, 0.46153846153846156] |

Unit conversion and ranking rules: see blind_eval.py module docstring.
The raised-conversion hand comparison retains its own frozen scenario. AI inputs are the same measured records.
NH3 hand costs are reduced catalyst-dependent costs; feed cost is outside that boundary.

## meoh_b1

Costed 699/699; scored records 699.
AI ranking: {"groups": 63, "papers": 46, "changed": 26, "gt5pct": 17, "fraction": 0.4126984126984127, "ci95": [0.288135593220339, 0.5230952380952381], "bootstrap": {"draws": 2000, "seed": 20261006, "unit": "paper"}}

| Reference quantity | Hand | AI | Relative gap |
|---|---|---|---|
| cost_usd_per_t | 972.8298126048543 | 1592.5987614899764 | 0.6370784908674061 |
| parts.feed | 715.3323610893266 | 1081.8250068994587 | 0.512338971009263 |
| shares.feed | 0.7353108959253097 | 0.6792828382506987 | -0.07619641975263503 |
| parts.energy | 18.886150176085955 | 287.0677801725413 | 14.199909854366858 |
| shares.energy | 0.01941362192171753 | 0.18025116376705663 | 8.284777693409914 |
| parts.capital | 48.49700238747237 | 208.17854144721784 | 3.2926063715021288 |
| shares.capital | 0.04985147634159827 | 0.13071625225455638 | 1.6221139642655071 |
| parts.catalyst | 0.0 | 15.527432970758538 | None |
| shares.catalyst | 0.0 | 0.009749745727688277 | None |
| parts.other | 190.11429895196932 | 0.0 | -1.0 |
| shares.other | 0.1954240058113744 | 0.0 | -1.0 |
| operating.T_K | 520.65 | 493.0 | -0.053106693556131734 |
| operating.P_bar | 70.0 | 30.0 | -0.5714285714285714 |
| operating.per_pass_conversion | 0.285 | 0.11416999820083826 | -0.5994035150847781 |
| balances.capacity_t_per_y | 1160000.0 | 100000.0 | -0.9137931034482758 |
| balances.capex_usd | 437553090.0 | 154894748.10060853 | -0.6459978191432529 |
| balances.energy_GJ_per_t | 0.7174226087781939 | 12.918050107764358 | 17.00619321122934 |
| basis.battery_limit | purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source | Gate-to-gate methanol synthesis island from separate pressurized CO2 and H2 feeds through on-spec liquid methanol storage; upstream CO2 capture and H2 production are represented by transfer prices, while wastewater and purge leave the boundary. | None |
| basis.capacity_t_per_y | 1160000.0 | 100000.0 | -0.9137931034482758 |
| basis.feeds.CO2.P_bar | 1 | 0.9 | -0.09999999999999998 |
| basis.feeds.CO2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.CO2.purity_mol_frac | 1 | 0.995 | -0.0050000000000000044 |
| basis.feeds.H2.P_bar | 30 | 0.9 | -0.97 |
| basis.feeds.H2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.H2.purity_mol_frac | 0.995 | 0.999 | 0.004020100502512669 |
| basis.operating_hours_per_y | 8000.0 | 8000.0 | 0.0 |
| basis.product.CH3OH.P_bar | None | 2.0 | None |
| basis.product.CH3OH.purity_mol_frac | None | 0.999 | None |
| basis.product.CH3OH.state | liquid; downstream distillation included | None | None |
| basis.purchased_preheat_reason.high | None | 1.0 | None |
| basis.purchased_preheat_reason.location | None | Electric trim heating is retained because feed-effluent heat recovery cannot provide startup heat and may not close the approach-temperature balance at low optimized per-pass conversion. | None |
| basis.purchased_preheat_reason.low | None | 0.0 | None |
| basis.purchased_preheat_reason.source | None |  | None |
| basis.purchased_preheat_reason.type | None | assumption | None |
| basis.utilities.cooling_water_return_temperature | None | 313.15 | None |
| basis.utilities.cooling_water_supply_temperature | None | 298.15 | None |
| basis.utilities.low_pressure_steam_pressure | None | 4.0 | None |

### Group comparison: fixed_conversion

Compared 63; verdict agreement 43; pooled cost Spearman 0.6278980853271744.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/anie.201600943 / 50 bar / H2/CO2 4 / 26 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/cbh2.70072 / 30 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1002/cctc.202000974 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | True | True | 0.006337920800578489 | 0.5087019954311558 | False | -0.308810299946281 |
| 10.1002/ente.201800747 / 40 bar / H2/CO2 3 / 21.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9248053392658508 |
| 10.1007/s11426-026-3904-1 / 20 bar / H2/CO2 3 / 6 NL/g/h | True | True | False | False | 0.00564524554683099 | 0.0 | False | -0.9999999999999999 |
| 10.1016/j.apcata.2018.04.036 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.apcatb.2017.06.069 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | True | False | 0.0 | 0.007411743091223055 | False | -0.9999999999999999 |
| 10.1016/j.cattod.2019.05.040 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2020.05.049 / 41 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | False | False | 0.5494881656364579 | 0.0 | False | 0.2727272727272727 |
| 10.1016/j.fuel.2023.127927 / 20 bar / H2/CO2 3 / 2.4 NL/g/h | True | True | True | True | 0.00293910580850687 | 0.0035847518079197283 | False | -0.6 |
| 10.1016/j.fuel.2024.131111 / 40 bar / H2/CO2 5 / 12 NL/g/h | True | True | True | True | 0.11852910476962153 | 0.019235690723959475 | True | 0.7727272727272727 |
| 10.1016/j.jcat.2012.05.020 / 30 bar / H2/CO2 3 / 13.4 NL/g/h | True | True | False | False | 0.37642527212318266 | 0.0 | False | 0.5 |
| 10.1016/j.jcat.2016.03.017 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7647058823529413 |
| 10.1016/j.jcou.2016.11.015 / 40 bar / H2/CO2 3.04 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.0689868394216906 | False | 0.6484848484848483 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18000 h-1 | True | True | True | True | 0.23078988619465535 | 0.15177052701829608 | True | 1.0 |
| 10.1021/acs.energyfuels.6c02662 / 30 bar / H2/CO2 5 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1021/acs.iecr.6c02654 / 30 bar / H2/CO2 3 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.6c02734 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8333333333333333 |
| 10.1021/acs.iecr.6c02971 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.03014190543406392 | False | 0.1666666666666667 |
| 10.1021/acs.iecr.7b01464 / 30 bar / H2/CO2 3.03 / 0.873 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7 |
| 10.1021/acscatal.0c05628 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9761904761904763 |
| 10.1021/acscatal.1c03170 / 30 bar / H2/CO2 3 / 60 NL/g/h | True | True | False | False | 0.6282436322851057 | 0.0 | False | 0.39999999999999997 |
| 10.1021/acscatal.5c05984 / 100 bar / H2/CO2 4 / 10 NL/g/h | True | True | True | True | 0.06677576667724638 | 0.0013187413881827759 | True | 0.9166666666666666 |
| 10.1021/acscatal.6c01275 / 50 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.07388133041860923 | 0.021180410798683713 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c01304 / 45 bar / H2/CO2 3 / 18 NL/g/h | True | False | True | False | 0.0 | 0.10961469976173044 | False | 0.5 |
| 10.1021/acscatal.6c02907 / 1 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 10 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.09116007328273557 | 0.023575921026842472 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 2.5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 15 NL/g/h | True | False | True | False | 0.0 | 0.3436189510493026 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 22.2 NL/g/h | True | False | True | False | 0.0 | 0.23343986878642897 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.07576922462739111 | 0.09966778723844083 | True | 0.8676691729323308 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 7.5 NL/g/h | True | False | True | False | 0.0 | 0.42648899828489606 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c03987 / 14 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.1011099180327637 | 0.11529504917996669 | True | 0.9638655462184874 |
| 10.1021/acscatal.6c03987 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9930069930069931 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 2 / 48 NL/g/h | True | True | True | True | 0.3641743828509605 | 0.12998202316848162 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | True | True | True | 0.1783189948265662 | 0.06130142486616763 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 4 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c05217 / 32 bar / H2/CO2 3 / 8 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c06647 / 50 bar / H2/CO2 3 / 9 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c06714 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.08532839889699151 | 0.49741502561082407 | False | -0.08421052631578947 |
| 10.1021/acscatal.6c06780 / 30 bar / H2/CO2 4 / 40 NL/g/h | True | False | True | False | 0.0 | 0.10567072651658926 | False | 0.7 |
| 10.1021/acscatal.9b01869 / 50 bar / H2/CO2 4 / 24000 h-1 | True | True | False | False | 0.044105922265119224 | 0.0 | False | 0.9823529411764707 |
| 10.1021/acscatal.9b03305 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.14461165180748758 | 0.029779544850016437 | False | 0.9230769230769231 |
| 10.1021/acssuschemeng.6c05638 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1021/cs500979c / 80 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.7789017761254954 |
| 10.1038/s41467-025-65929-z / 40 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.14511880454679194 | False | -0.03571428571428572 |
| 10.1038/s41467-025-65929-z / 50 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1038/s41467-026-72876-w / 20 bar / H2/CO2 3 / 450 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1038/s41557-026-02104-x / 50 bar / H2/CO2 3 / 1.5 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8008021390374331 |
| 10.1038/s41565-026-02135-y / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.4007224192487715 | 0.13709346313998783 | True | 0.9964285714285712 |
| 10.1039/c2cy20604h / 100 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | True | True | 1.5756208290777454 | 0.10404806872000516 | False | -0.39090909090909093 |
| 10.1039/c2cy20604h / 30 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.0202078120027267 | 0.0 | False | 0.38181818181818183 |
| 10.1039/c2cy20604h / 360 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.08047535391634408 | 0.0 | False | -0.7818181818181819 |
| 10.1039/c2cy20604h / 4 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9818181818181818 |
| 10.1039/c5cy00372e / 50 bar / H2/CO2 3.04 / 10 NL/g/h | True | False | True | False | 0.0 | 0.012631142442808052 | False | 0.7999999999999999 |
| 10.1039/c6ra28305e / 30 bar / H2/CO2 3 / 3600 h-1 | True | True | False | False | 0.026489322579082097 | 0.0 | False | 0.7999999999999999 |
| 10.1039/d0gc01597k / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.39999999999999997 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 12 NL/g/h | True | True | False | False | 0.03654329764560704 | 0.0 | False | 0.8881118881118882 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 24 NL/g/h | True | True | False | False | 0.13308895943349142 | 0.0 | False | 0.39999999999999997 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 8 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1126/sciadv.aea7041 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.37647211950133985 | 0.05093452572424306 | True | 0.9070263809442499 |

### Group comparison: raised_conversion

Compared 63; verdict agreement 40; pooled cost Spearman 0.559008382292818.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/anie.201600943 / 50 bar / H2/CO2 4 / 26 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/cbh2.70072 / 30 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1002/cctc.202000974 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | True | True | 0.23866645454588142 | 0.5087019954311558 | False | -0.3469490829516438 |
| 10.1002/ente.201800747 / 40 bar / H2/CO2 3 / 21.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9421579532814239 |
| 10.1007/s11426-026-3904-1 / 20 bar / H2/CO2 3 / 6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.apcata.2018.04.036 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1016/j.apcatb.2017.06.069 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | True | False | 0.0 | 0.007411743091223055 | False | -0.9999999999999999 |
| 10.1016/j.cattod.2019.05.040 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2020.05.049 / 41 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9878787878787878 |
| 10.1016/j.fuel.2023.127927 / 20 bar / H2/CO2 3 / 2.4 NL/g/h | True | True | True | True | 0.00293910580850687 | 0.0035847518079197283 | False | 0.0 |
| 10.1016/j.fuel.2024.131111 / 40 bar / H2/CO2 5 / 12 NL/g/h | True | True | True | True | 0.03507893251003047 | 0.019235690723959475 | False | 0.5636363636363637 |
| 10.1016/j.jcat.2012.05.020 / 30 bar / H2/CO2 3 / 13.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.jcat.2016.03.017 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8333333333333335 |
| 10.1016/j.jcou.2016.11.015 / 40 bar / H2/CO2 3.04 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.0689868394216906 | False | 0.6484848484848483 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18000 h-1 | True | True | True | True | 0.2602920578611956 | 0.15177052701829608 | True | 1.0 |
| 10.1021/acs.energyfuels.6c02662 / 30 bar / H2/CO2 5 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.iecr.6c02654 / 30 bar / H2/CO2 3 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.6c02734 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5833333333333334 |
| 10.1021/acs.iecr.6c02971 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.03014190543406392 | False | 0.1666666666666667 |
| 10.1021/acs.iecr.7b01464 / 30 bar / H2/CO2 3.03 / 0.873 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7 |
| 10.1021/acscatal.0c05628 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8333333333333335 |
| 10.1021/acscatal.1c03170 / 30 bar / H2/CO2 3 / 60 NL/g/h | True | True | False | False | 0.006845659527301651 | 0.0 | False | 0.39999999999999997 |
| 10.1021/acscatal.5c05984 / 100 bar / H2/CO2 4 / 10 NL/g/h | True | True | True | True | 0.05853686005349812 | 0.0013187413881827759 | True | 0.9333333333333332 |
| 10.1021/acscatal.6c01275 / 50 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.1195684616386179 | 0.021180410798683713 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c01304 / 45 bar / H2/CO2 3 / 18 NL/g/h | True | False | True | False | 0.0 | 0.10961469976173044 | False | 0.5 |
| 10.1021/acscatal.6c02907 / 1 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 10 bar / H2/CO2 3 / 30 NL/g/h | True | False | True | False | 0.0 | 0.023575921026842472 | False | 0.7999999999999999 |
| 10.1021/acscatal.6c02907 / 2.5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 15 NL/g/h | True | False | True | False | 0.0 | 0.3436189510493026 | False | -1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 22.2 NL/g/h | True | False | True | False | 0.0 | 0.23343986878642897 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | True | False | 0.0 | 0.09966778723844083 | False | 0.8796992481203006 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 7.5 NL/g/h | True | False | True | False | 0.0 | 0.42648899828489606 | False | -1.0 |
| 10.1021/acscatal.6c02907 / 5 bar / H2/CO2 3 / 30 NL/g/h | True | True | False | False | 0.003249082304640938 | 0.0 | False | 0.7999999999999999 |
| 10.1021/acscatal.6c03987 / 14 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.06144620415471924 | 0.11529504917996669 | False | 0.8641456582633054 |
| 10.1021/acscatal.6c03987 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9090909090909092 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 2 / 48 NL/g/h | True | False | True | False | 0.0 | 0.12998202316848162 | False | -0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | True | False | 0.0 | 0.06130142486616763 | False | -0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 4 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c05217 / 32 bar / H2/CO2 3 / 8 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c06647 / 50 bar / H2/CO2 3 / 9 NL/g/h | True | True | False | False | 0.20708663004896888 | 0.0 | False | 0.0 |
| 10.1021/acscatal.6c06714 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | False | True | False | 0.0 | 0.49741502561082407 | False | -0.2263157894736842 |
| 10.1021/acscatal.6c06780 / 30 bar / H2/CO2 4 / 40 NL/g/h | True | True | True | True | 0.000715399909406722 | 0.10567072651658926 | True | 0.9999999999999999 |
| 10.1021/acscatal.9b01869 / 50 bar / H2/CO2 4 / 24000 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.8088235294117646 |
| 10.1021/acscatal.9b03305 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.012095875050900595 | 0.029779544850016437 | False | 0.6433566433566434 |
| 10.1021/acssuschemeng.6c05638 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1021/cs500979c / 80 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.7611940298507462 |
| 10.1038/s41467-025-65929-z / 40 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.14511880454679194 | False | 0.0 |
| 10.1038/s41467-025-65929-z / 50 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1038/s41467-026-72876-w / 20 bar / H2/CO2 3 / 450 NL/g/h | True | True | False | False | 0.19054719950689591 | 0.0 | False | 0.39999999999999997 |
| 10.1038/s41557-026-02104-x / 50 bar / H2/CO2 3 / 1.5 NL/g/h | True | True | False | False | 0.0030350075871916626 | 0.0 | False | 0.8679812834224598 |
| 10.1038/s41565-026-02135-y / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 2.40437161291851e-06 | 0.13709346313998783 | True | 0.8821428571428571 |
| 10.1039/c2cy20604h / 100 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | True | False | 0.0 | 0.10404806872000516 | False | 0.06363636363636364 |
| 10.1039/c2cy20604h / 30 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.41818181818181827 |
| 10.1039/c2cy20604h / 360 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.014728905887972266 | 0.0 | False | -0.018181818181818184 |
| 10.1039/c2cy20604h / 4 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.14473181985254824 | 0.0 | False | 0.9090909090909091 |
| 10.1039/c5cy00372e / 50 bar / H2/CO2 3.04 / 10 NL/g/h | True | True | True | True | 0.003903945049308577 | 0.012631142442808052 | True | 0.8999999999999998 |
| 10.1039/c6ra28305e / 30 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1039/d0gc01597k / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.0 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 12 NL/g/h | True | True | False | False | 0.11207281243707645 | 0.0 | False | 0.7692307692307694 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 24 NL/g/h | True | True | False | False | 0.2000487345172044 | 0.0 | False | -0.19999999999999998 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 8 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1126/sciadv.aea7041 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.013187378216579893 | 0.05093452572424306 | True | 0.895415350465295 |

### Bottlenecks

```json
{
  "largest_cost_item": "feed",
  "hand_largest_cost_item": "feed",
  "controlling_property": "activity",
  "hand_controlling_property": "not available",
  "attribution_share": {
    "selectivity": 0.049,
    "activity": 0.947,
    "temperature": 0.001,
    "stability": 0.002,
    "metal": 0.002
  },
  "cheapest_record": "meoh:0174",
  "cheapest_catalyst": "5 wt % Re/TiO2 [Table 4 row 14]",
  "hand_cheapest_record": "meoh:0085",
  "hand_cheapest_catalyst": "0.5Ca-PZC [Text/Figure 7a, 0.5Ca-PZC, GHSV 12000 h−1]",
  "cheapest_common_record": "meoh:0174",
  "cheapest_common_catalyst": "5 wt % Re/TiO2 [Table 4 row 14]",
  "hand_cheapest_common_record": "meoh:0085",
  "hand_cheapest_common_catalyst": "0.5Ca-PZC [Text/Figure 7a, 0.5Ca-PZC, GHSV 12000 h−1]"
}
```

### Difference diagnosis and uncertainty

```json
{
  "rules": "deterministic evidence comparison; categories are evidence, not causal proof",
  "largest_reference_gaps": [
    {
      "field": "balances.energy_GJ_per_t",
      "hand": 0.7174226087781939,
      "ai": 12.918050107764358,
      "relative_gap": 17.00619321122934,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.energy",
      "hand": 18.886150176085955,
      "ai": 287.0677801725413,
      "relative_gap": 14.199909854366858,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.energy",
      "hand": 0.01941362192171753,
      "ai": 0.18025116376705663,
      "relative_gap": 8.284777693409914,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.capital",
      "hand": 48.49700238747237,
      "ai": 208.17854144721784,
      "relative_gap": 3.2926063715021288,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.capital",
      "hand": 0.04985147634159827,
      "ai": 0.13071625225455638,
      "relative_gap": 1.6221139642655071,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.other",
      "hand": 190.11429895196932,
      "ai": 0.0,
      "relative_gap": -1.0,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.other",
      "hand": 0.1954240058113744,
      "ai": 0.0,
      "relative_gap": -1.0,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.feeds.H2.P_bar",
      "hand": 30,
      "ai": 0.9,
      "relative_gap": -0.97,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capacity_t_per_y",
      "hand": 1160000.0,
      "ai": 100000.0,
      "relative_gap": -0.9137931034482758,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.capacity_t_per_y",
      "hand": 1160000.0,
      "ai": 100000.0,
      "relative_gap": -0.9137931034482758,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capex_usd",
      "hand": 437553090.0,
      "ai": 154894748.10060853,
      "relative_gap": -0.6459978191432529,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "cost_usd_per_t",
      "hand": 972.8298126048543,
      "ai": 1592.5987614899764,
      "relative_gap": 0.6370784908674061,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    }
  ],
  "largest_ranking_gaps": {
    "fixed_conversion": [
      {
        "group": "10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h",
        "hand_leader": "cu-k/al2o3",
        "ai_leader": "cu/al2o3",
        "hand_gap": 1.5756208290777454,
        "ai_gap": 0.10404806872000516,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.1c03170 | 30 bar | H2/CO2 3 | 60 NL/g/h",
        "hand_leader": "pd-in2o3",
        "ai_leader": "ni-in2o3",
        "hand_gap": 0.6282436322851057,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1016/j.cattod.2020.05.049 | 41 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pd-cu/ti0.8zr0.2o2",
        "ai_leader": "pd-cu/ti0.1zr0.9o2",
        "hand_gap": 0.5494881656364579,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1002/cctc.202000974 | 20 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pdzn/zntio3",
        "ai_leader": "zno",
        "hand_gap": 0.006337920800578489,
        "ai_gap": 0.5087019954311558,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 7.5 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.42648899828489606,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c06714 | 50 bar | H2/CO2 4 | 24 NL/g/h",
        "hand_leader": "pd/cnt+in2o3-r",
        "ai_leader": "cnt+in2o3-r",
        "hand_gap": 0.08532839889699151,
        "ai_gap": 0.49741502561082407,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1016/j.jcat.2012.05.020 | 30 bar | H2/CO2 3 | 13.4 NL/g/h",
        "hand_leader": "pdznal",
        "ai_leader": "pdmgga",
        "hand_gap": 0.37642527212318266,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 15 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.3436189510493026,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 22.2 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.5",
        "hand_gap": 0.0,
        "ai_gap": 0.23343986878642897,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1038/s41467-025-65929-z | 40 bar | H2/CO2 3 | 12 NL/g/h",
        "hand_leader": "ldh-niincal",
        "ai_leader": "pfcp-niincsi",
        "hand_gap": 0.0,
        "ai_gap": 0.14511880454679194,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      }
    ],
    "raised_conversion": [
      {
        "group": "10.1021/acscatal.6c06714 | 50 bar | H2/CO2 4 | 24 NL/g/h",
        "hand_leader": "pd/in2o3-r",
        "ai_leader": "cnt+in2o3-r",
        "hand_gap": 0.0,
        "ai_gap": 0.49741502561082407,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 7.5 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.42648899828489606,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 15 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.3436189510493026,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1002/cctc.202000974 | 20 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pdzn/zntio3",
        "ai_leader": "zno",
        "hand_gap": 0.23866645454588142,
        "ai_gap": 0.5087019954311558,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 22.2 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.5",
        "hand_gap": 0.0,
        "ai_gap": 0.23343986878642897,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c06647 | 50 bar | H2/CO2 3 | 9 NL/g/h",
        "hand_leader": "znso4-derivedresidues",
        "ai_leader": "impregnatedzn/mos2",
        "hand_gap": 0.20708663004896888,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1126/sciadv.abi6012 | 40 bar | H2/CO2 3 | 24 NL/g/h",
        "hand_leader": "inni3c0.5/sio2",
        "ai_leader": "inni3c0.5/m-zro2",
        "hand_gap": 0.2000487345172044,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1038/s41467-026-72876-w | 20 bar | H2/CO2 3 | 450 NL/g/h",
        "hand_leader": "in1.9sn0.1o3.05",
        "ai_leader": "in1.9zr0.1o3.05",
        "hand_gap": 0.19054719950689591,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1038/s41467-025-65929-z | 40 bar | H2/CO2 3 | 12 NL/g/h",
        "hand_leader": "ldh-niincal",
        "ai_leader": "pfcp-niincsi",
        "hand_gap": 0.0,
        "ai_gap": 0.14511880454679194,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1039/c2cy20604h | 4 bar | H2/CO2 3.8 | 10.6 NL/g/h",
        "hand_leader": "cu-k/al2o3",
        "ai_leader": "cu-ba/al2o3",
        "hand_gap": 0.14473181985254824,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      }
    ]
  },
  "ranking_disagreements": {
    "fixed_conversion": 20,
    "raised_conversion": 23
  },
  "findings": [
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.purity_mol_frac",
        "hand": 0.995,
        "ai": 0.999
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.CO2.P_bar",
        "hand": 1,
        "ai": 0.9
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.P_bar",
        "hand": 30,
        "ai": 0.9
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "capacity_t_per_y",
        "hand": 1160000.0,
        "ai": 100000.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.CO2.purity_mol_frac",
        "hand": 1,
        "ai": 0.995
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "battery_limit",
        "hand": "purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source",
        "ai": "Gate-to-gate methanol synthesis island from separate pressurized CO2 and H2 feeds through on-spec liquid methanol storage; upstream CO2 capture and H2 production are represented by transfer prices, while wastewater and purge leave the boundary."
      },
      "impact": "different plant design basis"
    },
    {
      "category": "structure",
      "evidence": {
        "hand_units": [
          "Reactor modules",
          "Carbon dioxide compressor",
          "Hydrogen compressor",
          "Recycle/reflux compressor",
          "Reactor preheaters",
          "Heat exchangers",
          "Flash drums",
          "Distillation column",
          "Pump",
          "Furnace & blower",
          "Turbine & generator"
        ],
        "ai_units": [
          {
            "name": "CO2 feed compressor",
            "type": "compressor"
          },
          {
            "name": "H2 feed compressor",
            "type": "compressor"
          },
          {
            "name": "Feed mixer",
            "type": "other"
          },
          {
            "name": "Feed-effluent heat exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "Electric trim preheater",
            "type": "heat_exchanger"
          },
          {
            "name": "Cooled fixed-bed reactor",
            "type": "reactor"
          },
          {
            "name": "Effluent condenser and knockout",
            "type": "knockout"
          },
          {
            "name": "Recycle purge splitter",
            "type": "other"
          },
          {
            "name": "Recycle compressor",
            "type": "compressor"
          },
          {
            "name": "Methanol purification column",
            "type": "separation"
          },
          {
            "name": "Methanol product pump",
            "type": "pump"
          },
          {
            "name": "Product storage and offsites",
            "type": "offsites"
          }
        ],
        "ai_checklist": {
          "feed_preparation": {
            "included": [
              "CO2 feed compressor",
              "H2 feed compressor",
              "Feed mixer",
              "Feed-effluent heat exchanger",
              "Electric trim preheater"
            ]
          },
          "reactor_heat_supply_or_removal": {
            "included": [
              "Cooled fixed-bed reactor"
            ]
          },
          "catalyst_regeneration": {
            "excluded": "No common in-situ regeneration protocol is supported across the diverse catalyst literature; catalyst decay is represented by replacement and average-cycle inventory instead."
          },
          "product_compression": {
            "included": [
              "Methanol product pump"
            ]
          },
          "separation_and_purification": {
            "included": [
              "Effluent condenser and knockout",
              "Methanol purification column"
            ]
          },
          "recycle": {
            "included": [
              "Recycle purge splitter",
              "Recycle compressor",
              "Feed mixer"
            ]
          },
          "heat_recovery": {
            "included": [
              "Feed-effluent heat exchanger",
              "Cooled fixed-bed reactor"
            ]
          },
          "utilities_and_offsites": {
            "included": [
              "Product storage and offsites"
            ]
          }
        },
        "missing_hand_unit_types": [
          "furnace"
        ],
        "extra_ai_unit_types": [
          "knockout",
          "offsites",
          "other"
        ],
        "ai_recycle_declaration": {
          "included": [
            "Recycle purge splitter",
            "Recycle compressor",
            "Feed mixer"
          ]
        },
        "hand_kinetics": "lab conversion capped by equilibrium; purge and CO recycle optimisation"
      },
      "impact": "unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim"
    },
    {
      "category": "parameters",
      "evidence": {
        "gaps_gt20pct": [],
        "unmatched_hand_parameters": [
          "co2_feed_pressure_bar",
          "compressor_efficiency",
          "discount_rate",
          "h2_feed_pressure_bar",
          "loop_dp_bar",
          "plant_life_y"
        ],
        "hand_parameters": {
          "compressor_efficiency": 0.8,
          "discount_rate": 0.1,
          "plant_life_y": 20,
          "h2_feed_pressure_bar": 30.0,
          "co2_feed_pressure_bar": 1.0,
          "loop_dp_bar": 1.5
        },
        "ai_parameters": {
          "basis.capacity_t_per_y": 100000.0,
          "basis.operating_hours_per_y": 8000.0,
          "basis.feeds.CO2.T_K": 298.15,
          "basis.feeds.CO2.P_bar": 0.9,
          "basis.feeds.CO2.purity_mol_frac": 0.995,
          "basis.feeds.H2.T_K": 298.15,
          "basis.feeds.H2.P_bar": 0.9,
          "basis.feeds.H2.purity_mol_frac": 0.999,
          "basis.product.CH3OH.P_bar": 2.0,
          "basis.product.CH3OH.purity_mol_frac": 0.999,
          "basis.utilities.cooling_water_supply_temperature": 298.15,
          "basis.utilities.cooling_water_return_temperature": 313.15,
          "basis.utilities.low_pressure_steam_pressure": 4.0,
          "price.electricity": 80.0,
          "price.hydrogen": 3.0,
          "price.carbon_dioxide": 100.0,
          "price.catalyst_support_and_manufacturing": 20.0,
          "price.metal_Cu": 13.889122517655,
          "price.metal_Zn": 3.2849,
          "price.metal_Zr": 22.0,
          "price.metal_In": 370.0,
          "price.metal_Pd": 40670.694409279,
          "price.metal_Pt": 51508.71107755406,
          "price.metal_Co": 56.28401553583051,
          "price.metal_Au": 128732.2322756058,
          "price.metal_Rh": 265243.65919095,
          "price.metal_Ni": 16.9094555095895,
          "price.metal_Sn": 35.274,
          "price.metal_Cr": 13.007,
          "price.metal_Ce": 2.1005306603773586,
          "price.metal_Al": 3.9683,
          "price.metal_Si": 2.866006,
          "price.metal_Ga": 580.0,
          "price.metal_Fe": 8.0,
          "price.capital_recovery_factor": 0.0944,
          "price.fixed_om_fraction_of_capex": 0.04,
          "compressor.isentropic_efficiency": 0.75,
          "compressor.gamma_CO2": 1.3,
          "compressor.gamma_H2": 1.4,
          "compressor.gamma_recycle": 1.35,
          "recycle.pressure_drop_fraction": 0.05,
          "recycle.purge_min_fraction": 0.005,
          "recycle.purge_max_fraction": 0.2,
          "separation.methanol_recovery": 0.995,
          "separation.dissolved_CO2_fraction_of_reactor_feed": 0.001,
          "heat_recovery.feed_effluent_fraction": 0.75,
          "thermo.gas_cp_GJ_per_kmol_K": 3.3e-05,
          "utilities.cooling_electricity_fraction": 0.025,
          "separation.distillation_base_GJ_per_t_methanol": 1.2,
          "separation.stabilization_GJ_per_kmol_dissolved_CO2": 0.02,
          "pump.column_outlet_pressure_bar": 1.2,
          "offsites.energy_GJ_per_t": 0.05,
          "catalyst.default_life_h": 16000.0,
          "catalyst.average_activity_factor": 0.95,
          "catalyst.unspecified_active_fraction": 0.1,
          "capital.scale_exponent": 0.6,
          "capital.compressor_USD_per_kW": 2000.0,
          "capital.compressor_min_USD": 1000000.0,
          "capital.mixer_reference_USD": 500000.0,
          "capital.heat_exchanger_USD_per_kW": 500.0,
          "capital.heat_exchanger_min_USD": 750000.0,
          "capital.reactor_fixed_USD": 5000000.0,
          "capital.reactor_volume_reference_USD": 5000000.0,
          "capital.reactor_heat_removal_USD_per_kW": 300.0,
          "catalyst.bulk_density_kg_per_m3": 1000.0,
          "capital.knockout_reference_USD": 3000000.0,
          "capital.splitter_reference_USD": 300000.0,
          "capital.column_reference_USD": 8000000.0,
          "capital.pump_reference_USD": 500000.0,
          "capital.offsites_fixed_USD": 5000000.0,
          "capital.offsites_fraction_direct": 0.1,
          "capital.reference_capacity_t_per_y": 100000.0,
          "capital.reference_gas_kmol_per_t": 200.0,
          "capital.reference_liquid_kmol_per_t": 70.0,
          "thermo.methanol_reaction_heat_kJ_per_mol": -58.7,
          "thermo.rwgs_reaction_heat_kJ_per_mol": 41.2,
          "thermo.equilibrium_reaction_entropy_J_per_mol_K": -194.5,
          "thermo.equilibrium_reaction_heat_kJ_per_mol": -49.5,
          "capital.reactor_reference_m3": 20.0,
          "thermo.reaction_heat_temperature_coefficient_kJ_per_mol_K": -0.055,
          "pump.isentropic_efficiency": 0.7,
          "pump.methanol_density_kg_per_m3": 792.0
        },
        "price_table_rows": [
          {
            "parameter": "price.electricity",
            "value": "80",
            "unit": "USD/MWh",
            "source": "prices.json:electricity",
            "location": "prices.electricity",
            "type": "price_table",
            "low": "40",
            "high": "150"
          },
          {
            "parameter": "price.hydrogen",
            "value": "3",
            "unit": "USD/kg",
            "source": "prices.json:hydrogen",
            "location": "prices.hydrogen",
            "type": "price_table",
            "low": "1.5",
            "high": "7"
          },
          {
            "parameter": "price.carbon_dioxide",
            "value": "100",
            "unit": "USD/t",
            "source": "prices.json:carbon_dioxide",
            "location": "prices.carbon_dioxide",
            "type": "price_table",
            "low": "20",
            "high": "200"
          },
          {
            "parameter": "price.catalyst_support_and_manufacturing",
            "value": "20",
            "unit": "USD/kg",
            "source": "prices.json:catalyst_support_and_manufacturing",
            "location": "prices.catalyst_support_and_manufacturing",
            "type": "price_table",
            "low": "5",
            "high": "100"
          },
          {
            "parameter": "price.metal_Cu",
            "value": "13.889122517655",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cu",
            "location": "prices.metal_Cu",
            "type": "price_table",
            "low": "6.9445612588275",
            "high": "27.77824503531"
          },
          {
            "parameter": "price.metal_Zn",
            "value": "3.2849",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zn",
            "location": "prices.metal_Zn",
            "type": "price_table",
            "low": "1.64245",
            "high": "6.5698"
          },
          {
            "parameter": "price.metal_Zr",
            "value": "22",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zr",
            "location": "prices.metal_Zr",
            "type": "price_table",
            "low": "11",
            "high": "44"
          },
          {
            "parameter": "price.metal_In",
            "value": "370",
            "unit": "USD/kg",
            "source": "prices.json:metal_In",
            "location": "prices.metal_In",
            "type": "price_table",
            "low": "185",
            "high": "740"
          },
          {
            "parameter": "price.metal_Pd",
            "value": "40670.694409279",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pd",
            "location": "prices.metal_Pd",
            "type": "price_table",
            "low": "20335.3472046395",
            "high": "81341.388818558"
          },
          {
            "parameter": "price.metal_Pt",
            "value": "51508.71107755406",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pt",
            "location": "prices.metal_Pt",
            "type": "price_table",
            "low": "25754.35553877703",
            "high": "103017.42215510811"
          },
          {
            "parameter": "price.metal_Co",
            "value": "56.28401553583051",
            "unit": "USD/kg",
            "source": "prices.json:metal_Co",
            "location": "prices.metal_Co",
            "type": "price_table",
            "low": "28.142007767915256",
            "high": "112.56803107166103"
          },
          {
            "parameter": "price.metal_Au",
            "value": "128732.2322756058",
            "unit": "USD/kg",
            "source": "prices.json:metal_Au",
            "location": "prices.metal_Au",
            "type": "price_table",
            "low": "64366.1161378029",
            "high": "257464.4645512116"
          },
          {
            "parameter": "price.metal_Rh",
            "value": "265243.65919095",
            "unit": "USD/kg",
            "source": "prices.json:metal_Rh",
            "location": "prices.metal_Rh",
            "type": "price_table",
            "low": "132621.829595475",
            "high": "530487.3183819"
          },
          {
            "parameter": "price.metal_Ni",
            "value": "16.9094555095895",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ni",
            "location": "prices.metal_Ni",
            "type": "price_table",
            "low": "8.45472775479475",
            "high": "33.818911019179"
          },
          {
            "parameter": "price.metal_Sn",
            "value": "35.274",
            "unit": "USD/kg",
            "source": "prices.json:metal_Sn",
            "location": "prices.metal_Sn",
            "type": "price_table",
            "low": "17.637",
            "high": "70.548"
          },
          {
            "parameter": "price.metal_Cr",
            "value": "13.007",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cr",
            "location": "prices.metal_Cr",
            "type": "price_table",
            "low": "6.5035",
            "high": "26.014"
          },
          {
            "parameter": "price.metal_Ce",
            "value": "2.1005306603773586",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ce",
            "location": "prices.metal_Ce",
            "type": "price_table",
            "low": "1.0502653301886793",
            "high": "4.201061320754717"
          },
          {
            "parameter": "price.metal_Al",
            "value": "3.9683",
            "unit": "USD/kg",
            "source": "prices.json:metal_Al",
            "location": "prices.metal_Al",
            "type": "price_table",
            "low": "1.98415",
            "high": "7.9366"
          },
          {
            "parameter": "price.metal_Si",
            "value": "2.866006",
            "unit": "USD/kg",
            "source": "prices.json:metal_Si",
            "location": "prices.metal_Si",
            "type": "price_table",
            "low": "1.433003",
            "high": "5.732012"
          },
          {
            "parameter": "price.metal_Ga",
            "value": "580",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ga",
            "location": "prices.metal_Ga",
            "type": "price_table",
            "low": "290",
            "high": "1160"
          },
          {
            "parameter": "price.metal_Fe",
            "value": "8",
            "unit": "USD/kg",
            "source": "prices.json:metal_Fe",
            "location": "prices.metal_Fe",
            "type": "price_table",
            "low": "4",
            "high": "16"
          },
          {
            "parameter": "price.capital_recovery_factor",
            "value": "0.0944",
            "unit": "1/y",
            "source": "prices.json:capital_recovery_factor",
            "location": "prices.capital_recovery_factor",
            "type": "price_table",
            "low": "0.08",
            "high": "0.13"
          },
          {
            "parameter": "price.fixed_om_fraction_of_capex",
            "value": "0.04",
            "unit": "1/y",
            "source": "prices.json:fixed_om_fraction_of_capex",
            "location": "prices.fixed_om_fraction_of_capex",
            "type": "price_table",
            "low": "0.02",
            "high": "0.06"
          }
        ]
      },
      "impact": "price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved"
    },
    {
      "category": "data",
      "evidence": {
        "rejected": [],
        "converted": 699,
        "total": 699,
        "missing_loading_records": 553
      },
      "impact": "unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking"
    },
    {
      "category": "numerics",
      "evidence": "all converted record costs finite, positive and parts close; deterministic repeat checked",
      "impact": "does not verify the optimiser reaches a global minimum"
    }
  ],
  "uncertainty": {
    "hand": {
      "productivity_density_g_cm3": [
        0.5,
        2
      ],
      "scope": "frozen hand sensitivity; no matched AI uncertainty distribution"
    },
    "ai_assumptions": [
      {
        "parameter": "basis.capacity_t_per_y",
        "value": "100000",
        "unit": "t/y",
        "source": "basis.json",
        "location": "capacity_t_per_y",
        "type": "assumption",
        "low": "50000",
        "high": "500000"
      },
      {
        "parameter": "basis.operating_hours_per_y",
        "value": "8000",
        "unit": "h/y",
        "source": "basis.json",
        "location": "operating_hours_per_y",
        "type": "assumption",
        "low": "7500",
        "high": "8400"
      },
      {
        "parameter": "basis.feeds.CO2.T_K",
        "value": "298.15",
        "unit": "K",
        "source": "basis.json",
        "location": "feeds.CO2.T_K",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.CO2.P_bar",
        "value": "0.9",
        "unit": "bar",
        "source": "basis.json",
        "location": "feeds.CO2.P_bar",
        "type": "assumption",
        "low": "0.5",
        "high": "30"
      },
      {
        "parameter": "basis.feeds.CO2.purity_mol_frac",
        "value": "0.995",
        "unit": "fraction",
        "source": "basis.json",
        "location": "feeds.CO2.purity_mol_frac",
        "type": "assumption",
        "low": "0.98",
        "high": "0.999"
      },
      {
        "parameter": "basis.feeds.H2.T_K",
        "value": "298.15",
        "unit": "K",
        "source": "basis.json",
        "location": "feeds.H2.T_K",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.H2.P_bar",
        "value": "0.9",
        "unit": "bar",
        "source": "basis.json",
        "location": "feeds.H2.P_bar",
        "type": "assumption",
        "low": "0.5",
        "high": "30"
      },
      {
        "parameter": "basis.feeds.H2.purity_mol_frac",
        "value": "0.999",
        "unit": "fraction",
        "source": "basis.json",
        "location": "feeds.H2.purity_mol_frac",
        "type": "assumption",
        "low": "0.995",
        "high": "0.9999"
      },
      {
        "parameter": "basis.product.CH3OH.P_bar",
        "value": "2",
        "unit": "bar",
        "source": "basis.json",
        "location": "product.CH3OH.P_bar",
        "type": "assumption",
        "low": "1",
        "high": "5"
      },
      {
        "parameter": "basis.product.CH3OH.purity_mol_frac",
        "value": "0.999",
        "unit": "fraction",
        "source": "basis.json",
        "location": "product.CH3OH.purity_mol_frac",
        "type": "assumption",
        "low": "0.995",
        "high": "0.9999"
      },
      {
        "parameter": "basis.utilities.cooling_water_supply_temperature",
        "value": "298.15",
        "unit": "K",
        "source": "basis.json",
        "location": "utilities.cooling_water_supply_temperature",
        "type": "assumption",
        "low": "288.15",
        "high": "303.15"
      },
      {
        "parameter": "basis.utilities.cooling_water_return_temperature",
        "value": "313.15",
        "unit": "K",
        "source": "basis.json",
        "location": "utilities.cooling_water_return_temperature",
        "type": "assumption",
        "low": "308.15",
        "high": "323.15"
      },
      {
        "parameter": "basis.utilities.low_pressure_steam_pressure",
        "value": "4",
        "unit": "bar",
        "source": "basis.json",
        "location": "utilities.low_pressure_steam_pressure",
        "type": "assumption",
        "low": "3",
        "high": "10"
      },
      {
        "parameter": "compressor.isentropic_efficiency",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "industrial compressor design basis",
        "type": "assumption",
        "low": "0.65",
        "high": "0.85"
      },
      {
        "parameter": "compressor.gamma_CO2",
        "value": "1.30",
        "unit": "ratio",
        "source": "",
        "location": "ideal-gas engineering approximation",
        "type": "assumption",
        "low": "1.25",
        "high": "1.35"
      },
      {
        "parameter": "compressor.gamma_H2",
        "value": "1.40",
        "unit": "ratio",
        "source": "",
        "location": "ideal-gas engineering approximation",
        "type": "assumption",
        "low": "1.35",
        "high": "1.42"
      },
      {
        "parameter": "compressor.gamma_recycle",
        "value": "1.35",
        "unit": "ratio",
        "source": "",
        "location": "mixed-gas engineering approximation",
        "type": "assumption",
        "low": "1.28",
        "high": "1.40"
      },
      {
        "parameter": "recycle.pressure_drop_fraction",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "reactor-loop pressure-drop allowance",
        "type": "assumption",
        "low": "0.02",
        "high": "0.10"
      },
      {
        "parameter": "recycle.purge_min_fraction",
        "value": "0.005",
        "unit": "fraction",
        "source": "",
        "location": "optimization bound preventing inert accumulation",
        "type": "assumption",
        "low": "0.002",
        "high": "0.02"
      },
      {
        "parameter": "recycle.purge_max_fraction",
        "value": "0.20",
        "unit": "fraction",
        "source": "",
        "location": "optimization bound limiting reactant loss",
        "type": "assumption",
        "low": "0.10",
        "high": "0.40"
      },
      {
        "parameter": "separation.methanol_recovery",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "column recovery design target",
        "type": "assumption",
        "low": "0.98",
        "high": "0.999"
      },
      {
        "parameter": "separation.dissolved_CO2_fraction_of_reactor_feed",
        "value": "0.001",
        "unit": "fraction",
        "source": "",
        "location": "pressure-dependent liquid entrainment proxy",
        "type": "assumption",
        "low": "0.0001",
        "high": "0.005"
      },
      {
        "parameter": "heat_recovery.feed_effluent_fraction",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "temperature-approach and fouling allowance",
        "type": "assumption",
        "low": "0.60",
        "high": "0.90"
      },
      {
        "parameter": "thermo.gas_cp_GJ_per_kmol_K",
        "value": "0.000033",
        "unit": "GJ/kmol/K",
        "source": "",
        "location": "mean syngas heat-capacity approximation",
        "type": "assumption",
        "low": "0.000028",
        "high": "0.000040"
      },
      {
        "parameter": "utilities.cooling_electricity_fraction",
        "value": "0.025",
        "unit": "GJ electricity/GJ removed",
        "source": "",
        "location": "cooling-water pumping and fan allowance",
        "type": "assumption",
        "low": "0.01",
        "high": "0.06"
      },
      {
        "parameter": "separation.distillation_base_GJ_per_t_methanol",
        "value": "1.2",
        "unit": "GJ/t",
        "source": "",
        "location": "methanol-water purification duty allowance",
        "type": "assumption",
        "low": "0.8",
        "high": "2.0"
      },
      {
        "parameter": "separation.stabilization_GJ_per_kmol_dissolved_CO2",
        "value": "0.02",
        "unit": "GJ/kmol",
        "source": "",
        "location": "dissolved-CO2 flashing and stabilization heat proxy",
        "type": "assumption",
        "low": "0.01",
        "high": "0.05"
      },
      {
        "parameter": "pump.column_outlet_pressure_bar",
        "value": "1.2",
        "unit": "bar",
        "source": "",
        "location": "purification-column liquid outlet pressure",
        "type": "assumption",
        "low": "1.0",
        "high": "1.8"
      },
      {
        "parameter": "offsites.energy_GJ_per_t",
        "value": "0.05",
        "unit": "GJ/t",
        "source": "",
        "location": "storage and balance-of-plant electricity allowance",
        "type": "assumption",
        "low": "0.02",
        "high": "0.12"
      },
      {
        "parameter": "catalyst.default_life_h",
        "value": "16000",
        "unit": "h",
        "source": "",
        "location": "two-year continuous-service assumption",
        "type": "assumption",
        "low": "4000",
        "high": "40000"
      },
      {
        "parameter": "catalyst.average_activity_factor",
        "value": "0.95",
        "unit": "fraction",
        "source": "",
        "location": "linear decline to ten percent activity loss over a cycle",
        "type": "assumption",
        "low": "0.90",
        "high": "1.0"
      },
      {
        "parameter": "catalyst.unspecified_active_fraction",
        "value": "0.10",
        "unit": "mass fraction",
        "source": "",
        "location": "cost proxy where paper omits component loading",
        "type": "assumption",
        "low": "0.01",
        "high": "0.30"
      },
      {
        "parameter": "capital.scale_exponent",
        "value": "0.60",
        "unit": "dimensionless",
        "source": "",
        "location": "six-tenths scaling rule",
        "type": "assumption",
        "low": "0.50",
        "high": "0.75"
      },
      {
        "parameter": "capital.compressor_USD_per_kW",
        "value": "2000",
        "unit": "USD/kW",
        "source": "",
        "location": "installed compressor cost allowance",
        "type": "assumption",
        "low": "1000",
        "high": "4000"
      },
      {
        "parameter": "capital.compressor_min_USD",
        "value": "1000000",
        "unit": "USD",
        "source": "",
        "location": "minimum installed compressor train cost",
        "type": "assumption",
        "low": "500000",
        "high": "3000000"
      },
      {
        "parameter": "capital.mixer_reference_USD",
        "value": "500000",
        "unit": "USD",
        "source": "",
        "location": "installed mixing and piping allowance",
        "type": "assumption",
        "low": "200000",
        "high": "1500000"
      },
      {
        "parameter": "capital.heat_exchanger_USD_per_kW",
        "value": "500",
        "unit": "USD/kW",
        "source": "",
        "location": "installed high-pressure exchanger allowance",
        "type": "assumption",
        "low": "250",
        "high": "1000"
      },
      {
        "parameter": "capital.heat_exchanger_min_USD",
        "value": "750000",
        "unit": "USD",
        "source": "",
        "location": "minimum installed exchanger cost",
        "type": "assumption",
        "low": "300000",
        "high": "2000000"
      },
      {
        "parameter": "capital.reactor_fixed_USD",
        "value": "5000000",
        "unit": "USD",
        "source": "",
        "location": "high-pressure cooled reactor fixed allowance",
        "type": "assumption",
        "low": "2500000",
        "high": "12000000"
      },
      {
        "parameter": "capital.reactor_volume_reference_USD",
        "value": "5000000",
        "unit": "USD",
        "source": "",
        "location": "reactor volume-dependent reference allowance",
        "type": "assumption",
        "low": "2000000",
        "high": "12000000"
      },
      {
        "parameter": "capital.reactor_heat_removal_USD_per_kW",
        "value": "300",
        "unit": "USD/kW",
        "source": "",
        "location": "boiling-water cooling surface allowance",
        "type": "assumption",
        "low": "150",
        "high": "700"
      },
      {
        "parameter": "catalyst.bulk_density_kg_per_m3",
        "value": "1000",
        "unit": "kg/m3",
        "source": "",
        "location": "shaped catalyst bulk-density assumption",
        "type": "assumption",
        "low": "600",
        "high": "1400"
      },
      {
        "parameter": "capital.knockout_reference_USD",
        "value": "3000000",
        "unit": "USD",
        "source": "",
        "location": "condenser and high-pressure separator reference cost",
        "type": "assumption",
        "low": "1500000",
        "high": "7000000"
      },
      {
        "parameter": "capital.splitter_reference_USD",
        "value": "300000",
        "unit": "USD",
        "source": "",
        "location": "purge control and piping allowance",
        "type": "assumption",
        "low": "100000",
        "high": "1000000"
      },
      {
        "parameter": "capital.column_reference_USD",
        "value": "8000000",
        "unit": "USD",
        "source": "",
        "location": "methanol purification column reference cost",
        "type": "assumption",
        "low": "4000000",
        "high": "16000000"
      },
      {
        "parameter": "capital.pump_reference_USD",
        "value": "500000",
        "unit": "USD",
        "source": "",
        "location": "product pump installed allowance",
        "type": "assumption",
        "low": "200000",
        "high": "1500000"
      },
      {
        "parameter": "capital.offsites_fixed_USD",
        "value": "5000000",
        "unit": "USD",
        "source": "",
        "location": "storage and utility fixed allowance",
        "type": "assumption",
        "low": "2500000",
        "high": "12000000"
      },
      {
        "parameter": "capital.offsites_fraction_direct",
        "value": "0.10",
        "unit": "fraction",
        "source": "",
        "location": "balance-of-plant fraction of direct equipment cost",
        "type": "assumption",
        "low": "0.05",
        "high": "0.25"
      },
      {
        "parameter": "capital.reference_capacity_t_per_y",
        "value": "100000",
        "unit": "t/y",
        "source": "",
        "location": "cost-correlation reference capacity",
        "type": "assumption",
        "low": "50000",
        "high": "200000"
      },
      {
        "parameter": "capital.reference_gas_kmol_per_t",
        "value": "200",
        "unit": "kmol/t",
        "source": "",
        "location": "cost-correlation reference recycle throughput",
        "type": "assumption",
        "low": "80",
        "high": "500"
      },
      {
        "parameter": "capital.reference_liquid_kmol_per_t",
        "value": "70",
        "unit": "kmol/t",
        "source": "",
        "location": "cost-correlation reference crude-liquid throughput",
        "type": "assumption",
        "low": "50",
        "high": "100"
      },
      {
        "parameter": "thermo.methanol_reaction_heat_kJ_per_mol",
        "value": "-58.7",
        "unit": "kJ/mol",
        "source": "",
        "location": "effective fixed-thermochemistry heat at 493 K for contracted methanol reaction",
        "type": "assumption",
        "low": "-62",
        "high": "-55"
      },
      {
        "parameter": "thermo.rwgs_reaction_heat_kJ_per_mol",
        "value": "41.2",
        "unit": "kJ/mol",
        "source": "",
        "location": "standard reverse-water-gas-shift heat approximation",
        "type": "assumption",
        "low": "38",
        "high": "43"
      },
      {
        "parameter": "thermo.equilibrium_reaction_entropy_J_per_mol_K",
        "value": "-194.5",
        "unit": "J/mol/K",
        "source": "",
        "location": "effective gas-phase equilibrium entropy including heat-capacity correction",
        "type": "assumption",
        "low": "-205",
        "high": "-185"
      },
      {
        "parameter": "thermo.equilibrium_reaction_heat_kJ_per_mol",
        "value": "-49.5",
        "unit": "kJ/mol",
        "source": "",
        "location": "gas-phase equilibrium enthalpy approximation",
        "type": "assumption",
        "low": "-52",
        "high": "-47"
      },
      {
        "parameter": "capital.reactor_reference_m3",
        "value": "20",
        "unit": "m3",
        "source": "",
        "location": "reference packed catalyst volume for scaling",
        "type": "assumption",
        "low": "5",
        "high": "100"
      },
      {
        "parameter": "thermo.reaction_heat_temperature_coefficient_kJ_per_mol_K",
        "value": "-0.055",
        "unit": "kJ/mol/K",
        "source": "",
        "location": "linear heat-capacity correction over catalyst test temperatures",
        "type": "assumption",
        "low": "-0.08",
        "high": "-0.03"
      },
      {
        "parameter": "pump.isentropic_efficiency",
        "value": "0.70",
        "unit": "fraction",
        "source": "",
        "location": "liquid pump efficiency allowance",
        "type": "assumption",
        "low": "0.55",
        "high": "0.85"
      },
      {
        "parameter": "pump.methanol_density_kg_per_m3",
        "value": "792",
        "unit": "kg/m3",
        "source": "",
        "location": "ambient liquid methanol density approximation",
        "type": "assumption",
        "low": "760",
        "high": "810"
      }
    ]
  }
}
```
## meoh_b2

Costed 699/699; scored records 699.
AI ranking: {"groups": 63, "papers": 46, "changed": 32, "gt5pct": 19, "fraction": 0.5079365079365079, "ci95": [0.39215686274509803, 0.603448275862069], "bootstrap": {"draws": 2000, "seed": 20261006, "unit": "paper"}}

| Reference quantity | Hand | AI | Relative gap |
|---|---|---|---|
| cost_usd_per_t | 972.8298126048543 | 1932.2452879924404 | 0.9862110134337372 |
| parts.feed | 715.3323610893266 | 1604.6123447202067 | 1.243170352696838 |
| shares.feed | 0.7353108959253097 | 0.8304392587689335 | 0.1293716214063645 |
| parts.energy | 18.886150176085955 | 191.48221609759278 | 9.138763819640259 |
| shares.energy | 0.01941362192171753 | 0.0990982963123375 | 4.10457537042476 |
| parts.capital | 48.49700238747237 | 90.17925586985233 | 0.8594810283191279 |
| shares.capital | 0.04985147634159827 | 0.04667070812916643 | -0.06380489497715569 |
| parts.catalyst | 0.0 | 7.759922207393288 | None |
| shares.catalyst | 0.0 | 0.004016013006017302 | None |
| parts.other | 190.11429895196932 | 38.21154909739506 | -0.799007495448573 |
| shares.other | 0.1954240058113744 | 0.019775723783545102 | -0.8988060668317644 |
| operating.T_K | 520.65 | 573.15 | 0.10083549409392112 |
| operating.P_bar | 70.0 | 20.0 | -0.7142857142857143 |
| operating.per_pass_conversion | 0.285 | 0.047902961817805595 | -0.831919432218226 |
| balances.capacity_t_per_y | 1160000.0 | 100000.0 | -0.9137931034482758 |
| balances.capex_usd | 437553090.0 | 95528872.74348764 | -0.7816747843250572 |
| balances.energy_GJ_per_t | 0.7174226087781939 | 30.688835978241283 | 41.77651080791263 |
| basis.battery_limit | purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source | Purified gaseous CO2 and H2 enter at stated delivery conditions; included are feed and recycle compression, mixing, heat recovery/preheat, catalytic synthesis, reaction heat removal, effluent cooling/condensation, gas-liquid separation, purge/recycle, methanol-water distillation, utilities and offsites. CO2 capture, H2 production, oxygen handling, feed transport, methanol storage/distribution and external wastewater treatment are excluded. | None |
| basis.capacity_t_per_y | 1160000.0 | 100000 | -0.9137931034482758 |
| basis.feeds.CO2.P_bar | 1 | 0.5 | -0.5 |
| basis.feeds.CO2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.CO2.purity_mol_frac | 1 | 1.0 | 0.0 |
| basis.feeds.H2.P_bar | 30 | 0.5 | -0.9833333333333333 |
| basis.feeds.H2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.H2.purity_mol_frac | 0.995 | 1.0 | 0.005025125628140614 |
| basis.operating_hours_per_y | 8000.0 | 8000 | 0.0 |
| basis.product.CH3OH.P_bar | None | 2.0 | None |
| basis.product.CH3OH.purity_mol_frac | None | 0.997 | None |
| basis.product.CH3OH.state | liquid; downstream distillation included | None | None |
| basis.purchased_preheat_reason | None | None | None |
| basis.utilities.compressor_isentropic_efficiency | None | 0.75 | None |
| basis.utilities.cooling_water_supply_T_K | None | 298.15 | None |
| basis.utilities.motor_efficiency | None | 0.95 | None |
| basis.utilities.primary_energy_factor_electricity | None | 2.5 | None |
| basis.utilities.steam_generation_efficiency | None | 0.85 | None |
| basis.utilities.steam_temperature_K | None | 453.15 | None |

### Group comparison: fixed_conversion

Compared 63; verdict agreement 41; pooled cost Spearman 0.5843771320883042.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/anie.201600943 / 50 bar / H2/CO2 4 / 26 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/cbh2.70072 / 30 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1002/cctc.202000974 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | True | True | 0.006337920800578489 | 0.9945829144718783 | False | -0.4420225861976179 |
| 10.1002/ente.201800747 / 40 bar / H2/CO2 3 / 21.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8771968854282535 |
| 10.1007/s11426-026-3904-1 / 20 bar / H2/CO2 3 / 6 NL/g/h | True | True | False | False | 0.00564524554683099 | 0.0 | False | -0.9999999999999999 |
| 10.1016/j.apcata.2018.04.036 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.apcatb.2017.06.069 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | True | False | 0.0 | 0.03153588927090767 | False | -0.9999999999999999 |
| 10.1016/j.cattod.2019.05.040 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2020.05.049 / 41 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | False | False | 0.5494881656364579 | 0.0 | False | 0.2121212121212121 |
| 10.1016/j.fuel.2023.127927 / 20 bar / H2/CO2 3 / 2.4 NL/g/h | True | True | False | False | 0.00293910580850687 | 0.0 | False | -0.3 |
| 10.1016/j.fuel.2024.131111 / 40 bar / H2/CO2 5 / 12 NL/g/h | True | True | True | True | 0.11852910476962153 | 0.01966886053798933 | True | 0.9636363636363637 |
| 10.1016/j.jcat.2012.05.020 / 30 bar / H2/CO2 3 / 13.4 NL/g/h | True | True | False | False | 0.37642527212318266 | 0.0 | False | 0.5 |
| 10.1016/j.jcat.2016.03.017 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8823529411764707 |
| 10.1016/j.jcou.2016.11.015 / 40 bar / H2/CO2 3.04 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.06190923368208834 | False | 0.49090909090909085 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18000 h-1 | True | True | True | True | 0.23078988619465535 | 0.1581872384285723 | True | 1.0 |
| 10.1021/acs.energyfuels.6c02662 / 30 bar / H2/CO2 5 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1021/acs.iecr.6c02654 / 30 bar / H2/CO2 3 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.6c02734 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | True | False | 0.0 | 0.02890565579645399 | False | 0.75 |
| 10.1021/acs.iecr.6c02971 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.027047834661033 | False | 0.1666666666666667 |
| 10.1021/acs.iecr.7b01464 / 30 bar / H2/CO2 3.03 / 0.873 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8999999999999998 |
| 10.1021/acscatal.0c05628 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.1c03170 / 30 bar / H2/CO2 3 / 60 NL/g/h | True | True | False | False | 0.6282436322851057 | 0.0 | False | 0.39999999999999997 |
| 10.1021/acscatal.5c05984 / 100 bar / H2/CO2 4 / 10 NL/g/h | True | True | True | True | 0.06677576667724638 | 0.0025199483494335873 | True | 0.8333333333333333 |
| 10.1021/acscatal.6c01275 / 50 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.07388133041860923 | 0.04191549539427575 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c01304 / 45 bar / H2/CO2 3 / 18 NL/g/h | True | False | True | False | 0.0 | 0.09970383999386478 | False | 0.5 |
| 10.1021/acscatal.6c02907 / 1 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 10 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.09116007328273557 | 0.03516747583426749 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 2.5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 15 NL/g/h | True | False | True | False | 0.0 | 0.31148789756480677 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 22.2 NL/g/h | True | False | True | False | 0.0 | 0.18957653048822953 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.07576922462739111 | 0.10193050192056097 | True | 0.882706766917293 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 7.5 NL/g/h | True | False | True | False | 0.0 | 0.3683278816177571 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c03987 / 14 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.1011099180327637 | 0.05425966860693432 | True | 0.9585434173669467 |
| 10.1021/acscatal.6c03987 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9790209790209792 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 2 / 48 NL/g/h | True | True | True | True | 0.3641743828509605 | 0.13089868958193684 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | True | True | True | 0.1783189948265662 | 0.07835874988241498 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 4 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c05217 / 32 bar / H2/CO2 3 / 8 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c06647 / 50 bar / H2/CO2 3 / 9 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c06714 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.08532839889699151 | 0.6368320754862768 | False | -0.14210526315789473 |
| 10.1021/acscatal.6c06780 / 30 bar / H2/CO2 4 / 40 NL/g/h | True | False | True | False | 0.0 | 0.09857887612630267 | False | 0.7 |
| 10.1021/acscatal.9b01869 / 50 bar / H2/CO2 4 / 24000 h-1 | True | True | False | False | 0.044105922265119224 | 0.0 | False | 0.9852941176470588 |
| 10.1021/acscatal.9b03305 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.14461165180748758 | 0.030791651975977885 | True | 0.965034965034965 |
| 10.1021/acssuschemeng.6c05638 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1021/cs500979c / 80 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.6927478550642103 |
| 10.1038/s41467-025-65929-z / 40 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.13740363752594797 | False | 0.0 |
| 10.1038/s41467-025-65929-z / 50 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1038/s41467-026-72876-w / 20 bar / H2/CO2 3 / 450 NL/g/h | True | False | True | False | 0.0 | 0.07083643675440832 | False | -0.19999999999999998 |
| 10.1038/s41557-026-02104-x / 50 bar / H2/CO2 3 / 1.5 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7827540106951872 |
| 10.1038/s41565-026-02135-y / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.4007224192487715 | 0.12255081952562041 | True | 1.0 |
| 10.1039/c2cy20604h / 100 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | True | True | 1.5756208290777454 | 0.09412414081279064 | False | -0.44545454545454555 |
| 10.1039/c2cy20604h / 30 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.0202078120027267 | 0.0 | False | 0.38181818181818183 |
| 10.1039/c2cy20604h / 360 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.08047535391634408 | 0.0 | False | -0.7818181818181819 |
| 10.1039/c2cy20604h / 4 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | True | False | 0.0 | 0.17814329288321185 | False | 0.9727272727272729 |
| 10.1039/c5cy00372e / 50 bar / H2/CO2 3.04 / 10 NL/g/h | True | False | True | False | 0.0 | 0.010831378019541038 | False | 0.7999999999999999 |
| 10.1039/c6ra28305e / 30 bar / H2/CO2 3 / 3600 h-1 | True | True | True | True | 0.026489322579082097 | 0.006478018926303175 | True | 1.0 |
| 10.1039/d0gc01597k / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | True | False | 0.0 | 0.06363100672981314 | False | 0.19999999999999998 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 12 NL/g/h | True | True | True | True | 0.03654329764560704 | 0.0041982841097951695 | True | 1.0 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.13308895943349142 | 0.036301358940477035 | True | 1.0 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 8 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1126/sciadv.aea7041 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.37647211950133985 | 0.003506839623317992 | True | 0.8394092034491589 |

### Group comparison: raised_conversion

Compared 63; verdict agreement 40; pooled cost Spearman 0.5719749918379392.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/anie.201600943 / 50 bar / H2/CO2 4 / 26 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/cbh2.70072 / 30 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1002/cctc.202000974 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | True | True | 0.23866645454588142 | 0.9945829144718783 | False | -0.5837620035244517 |
| 10.1002/ente.201800747 / 40 bar / H2/CO2 3 / 21.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9724137931034482 |
| 10.1007/s11426-026-3904-1 / 20 bar / H2/CO2 3 / 6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.apcata.2018.04.036 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1016/j.apcatb.2017.06.069 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | True | False | 0.0 | 0.03153588927090767 | False | -0.9999999999999999 |
| 10.1016/j.cattod.2019.05.040 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2020.05.049 / 41 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9757575757575757 |
| 10.1016/j.fuel.2023.127927 / 20 bar / H2/CO2 3 / 2.4 NL/g/h | True | True | False | False | 0.00293910580850687 | 0.0 | False | -0.09999999999999999 |
| 10.1016/j.fuel.2024.131111 / 40 bar / H2/CO2 5 / 12 NL/g/h | True | True | True | True | 0.03507893251003047 | 0.01966886053798933 | False | 0.5545454545454546 |
| 10.1016/j.jcat.2012.05.020 / 30 bar / H2/CO2 3 / 13.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.jcat.2016.03.017 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9264705882352943 |
| 10.1016/j.jcou.2016.11.015 / 40 bar / H2/CO2 3.04 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.06190923368208834 | False | 0.49090909090909085 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18000 h-1 | True | True | True | True | 0.2602920578611956 | 0.1581872384285723 | True | 1.0 |
| 10.1021/acs.energyfuels.6c02662 / 30 bar / H2/CO2 5 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.iecr.6c02654 / 30 bar / H2/CO2 3 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.6c02734 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | True | False | 0.0 | 0.02890565579645399 | False | 0.5333333333333333 |
| 10.1021/acs.iecr.6c02971 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.027047834661033 | False | 0.1666666666666667 |
| 10.1021/acs.iecr.7b01464 / 30 bar / H2/CO2 3.03 / 0.873 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8999999999999998 |
| 10.1021/acscatal.0c05628 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8095238095238096 |
| 10.1021/acscatal.1c03170 / 30 bar / H2/CO2 3 / 60 NL/g/h | True | True | False | False | 0.006845659527301651 | 0.0 | False | 0.39999999999999997 |
| 10.1021/acscatal.5c05984 / 100 bar / H2/CO2 4 / 10 NL/g/h | True | True | True | True | 0.05853686005349812 | 0.0025199483494335873 | True | 0.8499999999999999 |
| 10.1021/acscatal.6c01275 / 50 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.1195684616386179 | 0.04191549539427575 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c01304 / 45 bar / H2/CO2 3 / 18 NL/g/h | True | False | True | False | 0.0 | 0.09970383999386478 | False | 0.5 |
| 10.1021/acscatal.6c02907 / 1 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 10 bar / H2/CO2 3 / 30 NL/g/h | True | False | True | False | 0.0 | 0.03516747583426749 | False | 0.7999999999999999 |
| 10.1021/acscatal.6c02907 / 2.5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 15 NL/g/h | True | False | True | False | 0.0 | 0.31148789756480677 | False | -1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 22.2 NL/g/h | True | False | True | False | 0.0 | 0.18957653048822953 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | True | False | 0.0 | 0.10193050192056097 | False | 0.9052631578947368 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 7.5 NL/g/h | True | False | True | False | 0.0 | 0.3683278816177571 | False | -1.0 |
| 10.1021/acscatal.6c02907 / 5 bar / H2/CO2 3 / 30 NL/g/h | True | True | False | False | 0.003249082304640938 | 0.0 | False | 0.7999999999999999 |
| 10.1021/acscatal.6c03987 / 14 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.06144620415471924 | 0.05425966860693432 | False | 0.9120448179271708 |
| 10.1021/acscatal.6c03987 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9230769230769231 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 2 / 48 NL/g/h | True | False | True | False | 0.0 | 0.13089868958193684 | False | -0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | True | False | 0.0 | 0.07835874988241498 | False | -0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 4 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c05217 / 32 bar / H2/CO2 3 / 8 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c06647 / 50 bar / H2/CO2 3 / 9 NL/g/h | True | True | False | False | 0.20708663004896888 | 0.0 | False | 0.0 |
| 10.1021/acscatal.6c06714 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | False | True | False | 0.0 | 0.6368320754862768 | False | -0.2631578947368421 |
| 10.1021/acscatal.6c06780 / 30 bar / H2/CO2 4 / 40 NL/g/h | True | True | True | True | 0.000715399909406722 | 0.09857887612630267 | True | 0.9999999999999999 |
| 10.1021/acscatal.9b01869 / 50 bar / H2/CO2 4 / 24000 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.8558823529411764 |
| 10.1021/acscatal.9b03305 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.012095875050900595 | 0.030791651975977885 | False | 0.6433566433566434 |
| 10.1021/acssuschemeng.6c05638 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1021/cs500979c / 80 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.659350307287094 |
| 10.1038/s41467-025-65929-z / 40 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.13740363752594797 | False | -0.03571428571428572 |
| 10.1038/s41467-025-65929-z / 50 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1038/s41467-026-72876-w / 20 bar / H2/CO2 3 / 450 NL/g/h | True | True | True | True | 0.19054719950689591 | 0.07083643675440832 | True | 1.0 |
| 10.1038/s41557-026-02104-x / 50 bar / H2/CO2 3 / 1.5 NL/g/h | True | True | False | False | 0.0030350075871916626 | 0.0 | False | 0.849264705882353 |
| 10.1038/s41565-026-02135-y / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 2.40437161291851e-06 | 0.12255081952562041 | True | 0.8857142857142855 |
| 10.1039/c2cy20604h / 100 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | True | False | 0.0 | 0.09412414081279064 | False | 0.14545454545454548 |
| 10.1039/c2cy20604h / 30 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.41818181818181827 |
| 10.1039/c2cy20604h / 360 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.014728905887972266 | 0.0 | False | -0.018181818181818184 |
| 10.1039/c2cy20604h / 4 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | True | True | 0.14473181985254824 | 0.17814329288321185 | True | 0.9363636363636365 |
| 10.1039/c5cy00372e / 50 bar / H2/CO2 3.04 / 10 NL/g/h | True | True | True | True | 0.003903945049308577 | 0.010831378019541038 | True | 0.8999999999999998 |
| 10.1039/c6ra28305e / 30 bar / H2/CO2 3 / 3600 h-1 | True | False | True | False | 0.0 | 0.006478018926303175 | False | 0.39999999999999997 |
| 10.1039/d0gc01597k / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | True | False | 0.0 | 0.06363100672981314 | False | -0.39999999999999997 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 12 NL/g/h | True | True | True | True | 0.11207281243707645 | 0.0041982841097951695 | True | 0.9160839160839163 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.2000487345172044 | 0.036301358940477035 | True | 0.7999999999999999 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 8 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1126/sciadv.aea7041 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.013187378216579893 | 0.003506839623317992 | True | 0.9165030308204559 |

### Bottlenecks

```json
{
  "largest_cost_item": "feed",
  "hand_largest_cost_item": "feed",
  "controlling_property": "activity",
  "hand_controlling_property": "not available",
  "attribution_share": {
    "selectivity": 0.018,
    "activity": 0.981,
    "temperature": 0.001,
    "stability": 0.0,
    "metal": 0.0
  },
  "cheapest_record": "meoh:0174",
  "cheapest_catalyst": "5 wt % Re/TiO2 [Table 4 row 14]",
  "hand_cheapest_record": "meoh:0085",
  "hand_cheapest_catalyst": "0.5Ca-PZC [Text/Figure 7a, 0.5Ca-PZC, GHSV 12000 h−1]",
  "cheapest_common_record": "meoh:0174",
  "cheapest_common_catalyst": "5 wt % Re/TiO2 [Table 4 row 14]",
  "hand_cheapest_common_record": "meoh:0085",
  "hand_cheapest_common_catalyst": "0.5Ca-PZC [Text/Figure 7a, 0.5Ca-PZC, GHSV 12000 h−1]"
}
```

### Difference diagnosis and uncertainty

```json
{
  "rules": "deterministic evidence comparison; categories are evidence, not causal proof",
  "largest_reference_gaps": [
    {
      "field": "balances.energy_GJ_per_t",
      "hand": 0.7174226087781939,
      "ai": 30.688835978241283,
      "relative_gap": 41.77651080791263,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.energy",
      "hand": 18.886150176085955,
      "ai": 191.48221609759278,
      "relative_gap": 9.138763819640259,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.energy",
      "hand": 0.01941362192171753,
      "ai": 0.0990982963123375,
      "relative_gap": 4.10457537042476,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.feed",
      "hand": 715.3323610893266,
      "ai": 1604.6123447202067,
      "relative_gap": 1.243170352696838,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "cost_usd_per_t",
      "hand": 972.8298126048543,
      "ai": 1932.2452879924404,
      "relative_gap": 0.9862110134337372,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.feeds.H2.P_bar",
      "hand": 30,
      "ai": 0.5,
      "relative_gap": -0.9833333333333333,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capacity_t_per_y",
      "hand": 1160000.0,
      "ai": 100000.0,
      "relative_gap": -0.9137931034482758,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.capacity_t_per_y",
      "hand": 1160000.0,
      "ai": 100000,
      "relative_gap": -0.9137931034482758,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.other",
      "hand": 0.1954240058113744,
      "ai": 0.019775723783545102,
      "relative_gap": -0.8988060668317644,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.capital",
      "hand": 48.49700238747237,
      "ai": 90.17925586985233,
      "relative_gap": 0.8594810283191279,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.per_pass_conversion",
      "hand": 0.285,
      "ai": 0.047902961817805595,
      "relative_gap": -0.831919432218226,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.other",
      "hand": 190.11429895196932,
      "ai": 38.21154909739506,
      "relative_gap": -0.799007495448573,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    }
  ],
  "largest_ranking_gaps": {
    "fixed_conversion": [
      {
        "group": "10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h",
        "hand_leader": "cu-k/al2o3",
        "ai_leader": "cu/al2o3",
        "hand_gap": 1.5756208290777454,
        "ai_gap": 0.09412414081279064,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1002/cctc.202000974 | 20 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pdzn/zntio3",
        "ai_leader": "zno",
        "hand_gap": 0.006337920800578489,
        "ai_gap": 0.9945829144718783,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.1c03170 | 30 bar | H2/CO2 3 | 60 NL/g/h",
        "hand_leader": "pd-in2o3",
        "ai_leader": "ni-in2o3",
        "hand_gap": 0.6282436322851057,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c06714 | 50 bar | H2/CO2 4 | 24 NL/g/h",
        "hand_leader": "pd/cnt+in2o3-r",
        "ai_leader": "cnt+in2o3-r",
        "hand_gap": 0.08532839889699151,
        "ai_gap": 0.6368320754862768,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1016/j.cattod.2020.05.049 | 41 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pd-cu/ti0.8zr0.2o2",
        "ai_leader": "pd-cu/ti0.1zr0.9o2",
        "hand_gap": 0.5494881656364579,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1016/j.jcat.2012.05.020 | 30 bar | H2/CO2 3 | 13.4 NL/g/h",
        "hand_leader": "pdznal",
        "ai_leader": "pdmgga",
        "hand_gap": 0.37642527212318266,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 7.5 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.3683278816177571,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 15 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.31148789756480677,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 22.2 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.5",
        "hand_gap": 0.0,
        "ai_gap": 0.18957653048822953,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1039/c2cy20604h | 4 bar | H2/CO2 3.8 | 10.6 NL/g/h",
        "hand_leader": "cu-ba/al2o3",
        "ai_leader": "cu-k/al2o3",
        "hand_gap": 0.0,
        "ai_gap": 0.17814329288321185,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      }
    ],
    "raised_conversion": [
      {
        "group": "10.1002/cctc.202000974 | 20 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pdzn/zntio3",
        "ai_leader": "zno",
        "hand_gap": 0.23866645454588142,
        "ai_gap": 0.9945829144718783,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c06714 | 50 bar | H2/CO2 4 | 24 NL/g/h",
        "hand_leader": "pd/in2o3-r",
        "ai_leader": "cnt+in2o3-r",
        "hand_gap": 0.0,
        "ai_gap": 0.6368320754862768,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 7.5 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.3683278816177571,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 15 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.31148789756480677,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c06647 | 50 bar | H2/CO2 3 | 9 NL/g/h",
        "hand_leader": "znso4-derivedresidues",
        "ai_leader": "impregnatedzn/mos2",
        "hand_gap": 0.20708663004896888,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 22.2 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.5",
        "hand_gap": 0.0,
        "ai_gap": 0.18957653048822953,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1038/s41467-025-65929-z | 40 bar | H2/CO2 3 | 12 NL/g/h",
        "hand_leader": "ldh-niincal",
        "ai_leader": "pfcp-niincce",
        "hand_gap": 0.0,
        "ai_gap": 0.13740363752594797,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c04842 | 30 bar | H2/CO2 2 | 48 NL/g/h",
        "hand_leader": "znzr/90cu",
        "ai_leader": "gazr/90cu",
        "hand_gap": 0.0,
        "ai_gap": 0.13089868958193684,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 30 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.10193050192056097,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c01304 | 45 bar | H2/CO2 3 | 18 NL/g/h",
        "hand_leader": "commercialmethanolsynthesiscatalyst",
        "ai_leader": "h-zro2@cu1.3znal1.6-ldh",
        "hand_gap": 0.0,
        "ai_gap": 0.09970383999386478,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      }
    ]
  },
  "ranking_disagreements": {
    "fixed_conversion": 22,
    "raised_conversion": 23
  },
  "findings": [
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.purity_mol_frac",
        "hand": 0.995,
        "ai": 1.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.CO2.P_bar",
        "hand": 1,
        "ai": 0.5
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.P_bar",
        "hand": 30,
        "ai": 0.5
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "capacity_t_per_y",
        "hand": 1160000.0,
        "ai": 100000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "battery_limit",
        "hand": "purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source",
        "ai": "Purified gaseous CO2 and H2 enter at stated delivery conditions; included are feed and recycle compression, mixing, heat recovery/preheat, catalytic synthesis, reaction heat removal, effluent cooling/condensation, gas-liquid separation, purge/recycle, methanol-water distillation, utilities and offsites. CO2 capture, H2 production, oxygen handling, feed transport, methanol storage/distribution and external wastewater treatment are excluded."
      },
      "impact": "different plant design basis"
    },
    {
      "category": "structure",
      "evidence": {
        "hand_units": [
          "Reactor modules",
          "Carbon dioxide compressor",
          "Hydrogen compressor",
          "Recycle/reflux compressor",
          "Reactor preheaters",
          "Heat exchangers",
          "Flash drums",
          "Distillation column",
          "Pump",
          "Furnace & blower",
          "Turbine & generator"
        ],
        "ai_units": [
          {
            "name": "CO2 Feed Compressor",
            "type": "compressor"
          },
          {
            "name": "H2 Feed Compressor",
            "type": "compressor"
          },
          {
            "name": "Feed Mixer",
            "type": "other"
          },
          {
            "name": "Feed-Effluent Exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "Synthesis Reactor",
            "type": "reactor"
          },
          {
            "name": "Reactor Heat Management",
            "type": "heat_exchanger"
          },
          {
            "name": "Effluent Cooler",
            "type": "heat_exchanger"
          },
          {
            "name": "Condensate Knockout",
            "type": "knockout"
          },
          {
            "name": "Recycle Purge Splitter",
            "type": "other"
          },
          {
            "name": "Recycle Compressor",
            "type": "compressor"
          },
          {
            "name": "Crude Methanol Distillation",
            "type": "separation"
          },
          {
            "name": "Utilities and Offsites",
            "type": "offsites"
          }
        ],
        "ai_checklist": {
          "feed_preparation": {
            "included": [
              "CO2 Feed Compressor",
              "H2 Feed Compressor",
              "Feed Mixer",
              "Feed-Effluent Exchanger"
            ]
          },
          "reactor_heat_supply_or_removal": {
            "included": [
              "Reactor Heat Management",
              "Feed-Effluent Exchanger"
            ]
          },
          "catalyst_regeneration": {
            "excluded": "No universal in-situ regeneration protocol is supported across the diverse catalyst families; spent catalyst replacement and lifetime are costed instead."
          },
          "product_compression": {
            "excluded": "Specification methanol leaves as a condensed liquid at the stated product pressure, so no product-gas compression is required within these battery limits."
          },
          "separation_and_purification": {
            "included": [
              "Effluent Cooler",
              "Condensate Knockout",
              "Crude Methanol Distillation"
            ]
          },
          "recycle": {
            "included": [
              "Recycle Purge Splitter",
              "Recycle Compressor",
              "Feed Mixer"
            ]
          },
          "heat_recovery": {
            "included": [
              "Reactor Heat Management",
              "Feed-Effluent Exchanger"
            ]
          },
          "utilities_and_offsites": {
            "included": [
              "Utilities and Offsites"
            ]
          }
        },
        "missing_hand_unit_types": [
          "furnace",
          "pump"
        ],
        "extra_ai_unit_types": [
          "knockout",
          "offsites",
          "other"
        ],
        "ai_recycle_declaration": {
          "included": [
            "Recycle Purge Splitter",
            "Recycle Compressor",
            "Feed Mixer"
          ]
        },
        "hand_kinetics": "lab conversion capped by equilibrium; purge and CO recycle optimisation"
      },
      "impact": "unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim"
    },
    {
      "category": "parameters",
      "evidence": {
        "gaps_gt20pct": [],
        "unmatched_hand_parameters": [
          "co2_feed_pressure_bar",
          "compressor_efficiency",
          "discount_rate",
          "h2_feed_pressure_bar",
          "loop_dp_bar",
          "plant_life_y"
        ],
        "hand_parameters": {
          "compressor_efficiency": 0.8,
          "discount_rate": 0.1,
          "plant_life_y": 20,
          "h2_feed_pressure_bar": 30.0,
          "co2_feed_pressure_bar": 1.0,
          "loop_dp_bar": 1.5
        },
        "ai_parameters": {
          "thermo.methanol_reaction_enthalpy_kJ_per_mol": -49.5,
          "thermo.methanol_reaction_entropy_J_per_mol_K": -177.0,
          "thermo.rwgs_reaction_enthalpy_kJ_per_mol": 41.2,
          "process.default_h2_co2_ratio": 3.0,
          "process.equilibrium_safety_fraction": 0.5,
          "process.minimum_per_pass_conversion": 0.02,
          "process.maximum_per_pass_conversion": 0.45,
          "process.purge_fraction": 0.05,
          "process.loop_pressure_drop_fraction": 0.05,
          "process.methanol_condensation_recovery": 0.995,
          "process.water_condensation_recovery": 0.995,
          "process.co2_liquid_carryover_fraction": 0.01,
          "process.distillation_methanol_recovery": 0.995,
          "process.distillation_reboiler_GJ_per_t_crude": 1.3,
          "process.distillation_electricity_GJ_per_t_crude": 0.05,
          "process.feed_effluent_heat_recovery_fraction": 0.65,
          "process.reactor_heat_recovery_fraction": 0.5,
          "process.cooling_COP": 15.0,
          "process.gas_heat_capacity_kJ_per_kmol_K": 31.0,
          "process.methanol_latent_heat_kJ_per_kg": 1100.0,
          "process.water_latent_heat_kJ_per_kg": 2257.0,
          "process.condensation_temperature_K": 313.15,
          "process.recycle_compressor_inlet_temperature_K": 313.15,
          "process.compressor_heat_capacity_ratio": 1.3,
          "process.driving_force_floor": 0.05,
          "process.default_catalyst_life_y": 2.0,
          "process.cycle_to_replacement_multiplier": 6.0,
          "process.minimum_catalyst_life_y": 0.25,
          "process.maximum_catalyst_life_y": 5.0,
          "process.unknown_component_wt_fraction": 0.05,
          "process.catalyst_working_fraction": 0.9,
          "capex.scale_exponent": 0.65,
          "capex.compressor_reference_cost_usd": 2000000.0,
          "capex.compressor_reference_power_kW": 1000.0,
          "capex.mixer_reference_cost_usd": 300000.0,
          "capex.heat_exchanger_reference_cost_usd": 1500000.0,
          "capex.heat_exchanger_reference_duty_MW": 5.0,
          "capex.reactor_base_cost_usd": 12000000.0,
          "capex.knockout_reference_cost_usd": 2000000.0,
          "capex.splitter_reference_cost_usd": 250000.0,
          "capex.distillation_reference_cost_usd": 18000000.0,
          "capex.offsites_fraction_direct_capex": 0.2,
          "capex.reference_loop_kmol_per_t": 500.0,
          "capex.reference_crude_t_per_t_product": 1.6,
          "capex.minimum_unit_cost_usd": 100000.0,
          "price.natural_gas": 2.5,
          "price.electricity": 80.0,
          "price.hydrogen": 3.0,
          "price.carbon_dioxide": 100.0,
          "price.catalyst_support_and_manufacturing": 20.0,
          "price.metal_Cu": 13.889122517655,
          "price.metal_Zn": 3.2849,
          "price.metal_Zr": 22.0,
          "price.metal_In": 370.0,
          "price.metal_Pd": 40670.694409279,
          "price.metal_Pt": 51508.71107755406,
          "price.metal_Ru": 53852.5,
          "price.metal_Mg": 2.5,
          "price.capital_recovery_factor": 0.0944,
          "price.fixed_om_fraction_of_capex": 0.04,
          "basis.capacity_t_per_y": 100000.0,
          "basis.operating_hours_per_y": 8000.0,
          "basis.feeds.CO2.T_K": 298.15,
          "basis.feeds.CO2.P_bar": 0.5,
          "basis.feeds.CO2.purity_mol_frac": 1.0,
          "basis.feeds.H2.T_K": 298.15,
          "basis.feeds.H2.P_bar": 0.5,
          "basis.feeds.H2.purity_mol_frac": 1.0,
          "basis.product.CH3OH.P_bar": 2.0,
          "basis.product.CH3OH.purity_mol_frac": 0.997,
          "basis.utilities.compressor_isentropic_efficiency": 0.75,
          "basis.utilities.motor_efficiency": 0.95,
          "basis.utilities.cooling_water_supply_T_K": 298.15,
          "basis.utilities.steam_temperature_K": 453.15,
          "basis.utilities.steam_generation_efficiency": 0.85,
          "basis.utilities.primary_energy_factor_electricity": 2.5,
          "capex.reactor_reference_catalyst_inventory_kg": 500000.0,
          "thermo.methanol_reaction_deltaCp_kJ_per_mol_K": -0.05,
          "capex.minimum_compressor_usd_per_kW": 300.0
        },
        "price_table_rows": [
          {
            "parameter": "price.natural_gas",
            "value": "2.5",
            "unit": "USD/GJ",
            "source": "prices.json:natural_gas",
            "location": "prices.natural_gas",
            "type": "price_table",
            "low": "2.0",
            "high": "12.0"
          },
          {
            "parameter": "price.electricity",
            "value": "80.0",
            "unit": "USD/MWh",
            "source": "prices.json:electricity",
            "location": "prices.electricity",
            "type": "price_table",
            "low": "40.0",
            "high": "150.0"
          },
          {
            "parameter": "price.hydrogen",
            "value": "3.0",
            "unit": "USD/kg",
            "source": "prices.json:hydrogen",
            "location": "prices.hydrogen",
            "type": "price_table",
            "low": "1.5",
            "high": "7.0"
          },
          {
            "parameter": "price.carbon_dioxide",
            "value": "100.0",
            "unit": "USD/t",
            "source": "prices.json:carbon_dioxide",
            "location": "prices.carbon_dioxide",
            "type": "price_table",
            "low": "20.0",
            "high": "200.0"
          },
          {
            "parameter": "price.catalyst_support_and_manufacturing",
            "value": "20.0",
            "unit": "USD/kg",
            "source": "prices.json:catalyst_support_and_manufacturing",
            "location": "prices.catalyst_support_and_manufacturing",
            "type": "price_table",
            "low": "5.0",
            "high": "100.0"
          },
          {
            "parameter": "price.metal_Cu",
            "value": "13.889122517655",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cu",
            "location": "prices.metal_Cu",
            "type": "price_table",
            "low": "6.9445612588275",
            "high": "27.77824503531"
          },
          {
            "parameter": "price.metal_Zn",
            "value": "3.2849",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zn",
            "location": "prices.metal_Zn",
            "type": "price_table",
            "low": "1.64245",
            "high": "6.5698"
          },
          {
            "parameter": "price.metal_Zr",
            "value": "22.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zr",
            "location": "prices.metal_Zr",
            "type": "price_table",
            "low": "11.0",
            "high": "44.0"
          },
          {
            "parameter": "price.metal_In",
            "value": "370.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_In",
            "location": "prices.metal_In",
            "type": "price_table",
            "low": "185.0",
            "high": "740.0"
          },
          {
            "parameter": "price.metal_Pd",
            "value": "40670.694409279",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pd",
            "location": "prices.metal_Pd",
            "type": "price_table",
            "low": "20335.3472046395",
            "high": "81341.388818558"
          },
          {
            "parameter": "price.metal_Pt",
            "value": "51508.71107755406",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pt",
            "location": "prices.metal_Pt",
            "type": "price_table",
            "low": "25754.35553877703",
            "high": "103017.42215510811"
          },
          {
            "parameter": "price.metal_Ru",
            "value": "53852.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ru",
            "location": "prices.metal_Ru",
            "type": "price_table",
            "low": "26926.25",
            "high": "107705.0"
          },
          {
            "parameter": "price.metal_Mg",
            "value": "2.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mg",
            "location": "prices.metal_Mg",
            "type": "price_table",
            "low": "1.25",
            "high": "5.0"
          },
          {
            "parameter": "price.capital_recovery_factor",
            "value": "0.0944",
            "unit": "1/y",
            "source": "prices.json:capital_recovery_factor",
            "location": "prices.capital_recovery_factor",
            "type": "price_table",
            "low": "0.08",
            "high": "0.13"
          },
          {
            "parameter": "price.fixed_om_fraction_of_capex",
            "value": "0.04",
            "unit": "1/y",
            "source": "prices.json:fixed_om_fraction_of_capex",
            "location": "prices.fixed_om_fraction_of_capex",
            "type": "price_table",
            "low": "0.02",
            "high": "0.06"
          }
        ]
      },
      "impact": "price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved"
    },
    {
      "category": "data",
      "evidence": {
        "rejected": [],
        "converted": 699,
        "total": 699,
        "missing_loading_records": 553
      },
      "impact": "unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking"
    },
    {
      "category": "numerics",
      "evidence": "all converted record costs finite, positive and parts close; deterministic repeat checked",
      "impact": "does not verify the optimiser reaches a global minimum"
    }
  ],
  "uncertainty": {
    "hand": {
      "productivity_density_g_cm3": [
        0.5,
        2
      ],
      "scope": "frozen hand sensitivity; no matched AI uncertainty distribution"
    },
    "ai_assumptions": [
      {
        "parameter": "thermo.methanol_reaction_enthalpy_kJ_per_mol",
        "value": "-49.5",
        "unit": "kJ/mol",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-52",
        "high": "-47"
      },
      {
        "parameter": "thermo.methanol_reaction_entropy_J_per_mol_K",
        "value": "-177.0",
        "unit": "J/mol/K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-185",
        "high": "-169"
      },
      {
        "parameter": "thermo.rwgs_reaction_enthalpy_kJ_per_mol",
        "value": "41.2",
        "unit": "kJ/mol",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "39",
        "high": "43"
      },
      {
        "parameter": "process.default_h2_co2_ratio",
        "value": "3.0",
        "unit": "mol/mol",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2.8",
        "high": "4.0"
      },
      {
        "parameter": "process.equilibrium_safety_fraction",
        "value": "0.5",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.4",
        "high": "0.8"
      },
      {
        "parameter": "process.minimum_per_pass_conversion",
        "value": "0.02",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.005",
        "high": "0.08"
      },
      {
        "parameter": "process.maximum_per_pass_conversion",
        "value": "0.45",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.2",
        "high": "0.65"
      },
      {
        "parameter": "process.purge_fraction",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.15"
      },
      {
        "parameter": "process.loop_pressure_drop_fraction",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.02",
        "high": "0.12"
      },
      {
        "parameter": "process.methanol_condensation_recovery",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.97",
        "high": "0.999"
      },
      {
        "parameter": "process.water_condensation_recovery",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.97",
        "high": "0.999"
      },
      {
        "parameter": "process.co2_liquid_carryover_fraction",
        "value": "0.01",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.002",
        "high": "0.05"
      },
      {
        "parameter": "process.distillation_methanol_recovery",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.98",
        "high": "0.999"
      },
      {
        "parameter": "process.distillation_reboiler_GJ_per_t_crude",
        "value": "1.3",
        "unit": "GJ/t crude",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.8",
        "high": "2.5"
      },
      {
        "parameter": "process.distillation_electricity_GJ_per_t_crude",
        "value": "0.05",
        "unit": "GJ/t crude",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.02",
        "high": "0.12"
      },
      {
        "parameter": "process.feed_effluent_heat_recovery_fraction",
        "value": "0.65",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.4",
        "high": "0.85"
      },
      {
        "parameter": "process.reactor_heat_recovery_fraction",
        "value": "0.5",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.2",
        "high": "0.8"
      },
      {
        "parameter": "process.cooling_COP",
        "value": "15.0",
        "unit": "GJ cooling/GJ electricity",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8.0",
        "high": "25.0"
      },
      {
        "parameter": "process.gas_heat_capacity_kJ_per_kmol_K",
        "value": "31.0",
        "unit": "kJ/kmol/K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "27.0",
        "high": "38.0"
      },
      {
        "parameter": "process.methanol_latent_heat_kJ_per_kg",
        "value": "1100.0",
        "unit": "kJ/kg",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1000.0",
        "high": "1200.0"
      },
      {
        "parameter": "process.water_latent_heat_kJ_per_kg",
        "value": "2257.0",
        "unit": "kJ/kg",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2100.0",
        "high": "2350.0"
      },
      {
        "parameter": "process.condensation_temperature_K",
        "value": "313.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "303.15",
        "high": "323.15"
      },
      {
        "parameter": "process.recycle_compressor_inlet_temperature_K",
        "value": "313.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "298.15",
        "high": "333.15"
      },
      {
        "parameter": "process.compressor_heat_capacity_ratio",
        "value": "1.3",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.25",
        "high": "1.4"
      },
      {
        "parameter": "process.driving_force_floor",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.2"
      },
      {
        "parameter": "process.default_catalyst_life_y",
        "value": "2.0",
        "unit": "y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.5",
        "high": "5.0"
      },
      {
        "parameter": "process.cycle_to_replacement_multiplier",
        "value": "6.0",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "3.0",
        "high": "10.0"
      },
      {
        "parameter": "process.minimum_catalyst_life_y",
        "value": "0.25",
        "unit": "y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.1",
        "high": "1.0"
      },
      {
        "parameter": "process.maximum_catalyst_life_y",
        "value": "5.0",
        "unit": "y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "3.0",
        "high": "10.0"
      },
      {
        "parameter": "process.unknown_component_wt_fraction",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.2"
      },
      {
        "parameter": "process.catalyst_working_fraction",
        "value": "0.9",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.7",
        "high": "0.98"
      },
      {
        "parameter": "capex.scale_exponent",
        "value": "0.65",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.55",
        "high": "0.8"
      },
      {
        "parameter": "capex.compressor_reference_cost_usd",
        "value": "2000000.0",
        "unit": "USD at reference power",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1000000.0",
        "high": "4000000.0"
      },
      {
        "parameter": "capex.compressor_reference_power_kW",
        "value": "1000.0",
        "unit": "kW",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "800.0",
        "high": "1500.0"
      },
      {
        "parameter": "capex.mixer_reference_cost_usd",
        "value": "300000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "150000.0",
        "high": "800000.0"
      },
      {
        "parameter": "capex.heat_exchanger_reference_cost_usd",
        "value": "1500000.0",
        "unit": "USD at reference duty",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "750000.0",
        "high": "3000000.0"
      },
      {
        "parameter": "capex.heat_exchanger_reference_duty_MW",
        "value": "5.0",
        "unit": "MW",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "3.0",
        "high": "10.0"
      },
      {
        "parameter": "capex.reactor_base_cost_usd",
        "value": "12000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "6000000.0",
        "high": "30000000.0"
      },
      {
        "parameter": "capex.knockout_reference_cost_usd",
        "value": "2000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1000000.0",
        "high": "5000000.0"
      },
      {
        "parameter": "capex.splitter_reference_cost_usd",
        "value": "250000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100000.0",
        "high": "750000.0"
      },
      {
        "parameter": "capex.distillation_reference_cost_usd",
        "value": "18000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "9000000.0",
        "high": "40000000.0"
      },
      {
        "parameter": "capex.offsites_fraction_direct_capex",
        "value": "0.2",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.1",
        "high": "0.4"
      },
      {
        "parameter": "capex.reference_loop_kmol_per_t",
        "value": "500.0",
        "unit": "kmol/t product",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "250.0",
        "high": "1000.0"
      },
      {
        "parameter": "capex.reference_crude_t_per_t_product",
        "value": "1.6",
        "unit": "t crude/t product",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.2",
        "high": "3.0"
      },
      {
        "parameter": "capex.minimum_unit_cost_usd",
        "value": "100000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "50000.0",
        "high": "300000.0"
      },
      {
        "parameter": "basis.capacity_t_per_y",
        "value": "100000",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "50000",
        "high": "500000"
      },
      {
        "parameter": "basis.operating_hours_per_y",
        "value": "8000",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "7500",
        "high": "8400"
      },
      {
        "parameter": "basis.feeds.CO2.T_K",
        "value": "298.15",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.CO2.P_bar",
        "value": "0.5",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.1",
        "high": "1.0"
      },
      {
        "parameter": "basis.feeds.CO2.purity_mol_frac",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "1.0"
      },
      {
        "parameter": "basis.feeds.H2.T_K",
        "value": "298.15",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.H2.P_bar",
        "value": "0.5",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.1",
        "high": "1.0"
      },
      {
        "parameter": "basis.feeds.H2.purity_mol_frac",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "1.0"
      },
      {
        "parameter": "basis.product.CH3OH.P_bar",
        "value": "2.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.2",
        "high": "5.0"
      },
      {
        "parameter": "basis.product.CH3OH.purity_mol_frac",
        "value": "0.997",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.995",
        "high": "0.999"
      },
      {
        "parameter": "basis.utilities.compressor_isentropic_efficiency",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.65",
        "high": "0.85"
      },
      {
        "parameter": "basis.utilities.motor_efficiency",
        "value": "0.95",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.9",
        "high": "0.98"
      },
      {
        "parameter": "basis.utilities.cooling_water_supply_T_K",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "303.15"
      },
      {
        "parameter": "basis.utilities.steam_temperature_K",
        "value": "453.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "423.15",
        "high": "523.15"
      },
      {
        "parameter": "basis.utilities.steam_generation_efficiency",
        "value": "0.85",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.75",
        "high": "0.92"
      },
      {
        "parameter": "basis.utilities.primary_energy_factor_electricity",
        "value": "2.5",
        "unit": "GJ_primary/GJ_electric",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.8",
        "high": "3.0"
      },
      {
        "parameter": "capex.reactor_reference_catalyst_inventory_kg",
        "value": "500000.0",
        "unit": "kg",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100000.0",
        "high": "2000000.0"
      },
      {
        "parameter": "thermo.methanol_reaction_deltaCp_kJ_per_mol_K",
        "value": "-0.05",
        "unit": "kJ/mol/K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-0.08",
        "high": "-0.02"
      },
      {
        "parameter": "capex.minimum_compressor_usd_per_kW",
        "value": "300.0",
        "unit": "USD/kW installed",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "200.0",
        "high": "1000.0"
      }
    ]
  }
}
```
## meoh_b3

Costed 699/699; scored records 699.
AI ranking: {"groups": 63, "papers": 46, "changed": 33, "gt5pct": 17, "fraction": 0.5238095238095238, "ci95": [0.4067796610169492, 0.6323529411764706], "bootstrap": {"draws": 2000, "seed": 20261006, "unit": "paper"}}

| Reference quantity | Hand | AI | Relative gap |
|---|---|---|---|
| cost_usd_per_t | 972.8298126048543 | 1230.1278694494808 | 0.26448414050519675 |
| parts.feed | 715.3323610893266 | 949.6842735434664 | 0.32761262484652964 |
| shares.feed | 0.7353108959253097 | 0.7720207769688842 | 0.04992429902371964 |
| parts.energy | 18.886150176085955 | 79.0614392617166 | 3.186212569771148 |
| shares.energy | 0.01941362192171753 | 0.0642709113623277 | 2.3106089951421915 |
| parts.capital | 48.49700238747237 | 152.5157761710088 | 2.1448495507509207 |
| shares.capital | 0.04985147634159827 | 0.12398367678578341 | 1.4870612845286182 |
| parts.catalyst | 0.0 | 48.86638047328903 | None |
| shares.catalyst | 0.0 | 0.03972463488300464 | None |
| parts.other | 190.11429895196932 | 0.0 | -1.0 |
| shares.other | 0.1954240058113744 | 0.0 | -1.0 |
| operating.T_K | 520.65 | 513.15 | -0.014405070584845858 |
| operating.P_bar | 70.0 | 100.0 | 0.4285714285714286 |
| operating.per_pass_conversion | 0.285 | 0.2298218980199328 | -0.1936073753686568 |
| balances.capacity_t_per_y | 1160000.0 | 100000.0 | -0.9137931034482758 |
| balances.capex_usd | 437553090.0 | 113479000.1272387 | -0.7406508999233928 |
| balances.energy_GJ_per_t | 0.7174226087781939 | 11.255620028037415 | 14.688967548996388 |
| basis.battery_limit | purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source | Separate purchased gaseous CO2 and H2 at ambient conditions through compression, synthesis, recycle, condensation, purification, heat recovery, utilities and offsites; upstream CO2 capture and H2 manufacture are excluded and charged through feed prices; products are specification methanol, purge gas and treated aqueous waste. | None |
| basis.capacity_t_per_y | 1160000.0 | 100000.0 | -0.9137931034482758 |
| basis.feeds.CO2.P_bar | 1 | 1.01325 | 0.013249999999999984 |
| basis.feeds.CO2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.CO2.purity_mol_frac | 1 | 0.99 | -0.010000000000000009 |
| basis.feeds.H2.P_bar | 30 | 1.01325 | -0.966225 |
| basis.feeds.H2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.H2.purity_mol_frac | 0.995 | 0.999 | 0.004020100502512669 |
| basis.feeds.H2O.P_bar | None | 1.01325 | None |
| basis.feeds.H2O.T_K | None | 298.15 | None |
| basis.feeds.H2O.purity_mol_frac | None | 1.0 | None |
| basis.operating_hours_per_y | 8000.0 | 8000.0 | 0.0 |
| basis.product.CH3OH.P_bar | None | 5.0 | None |
| basis.product.CH3OH.purity_mol_frac | None | 0.997 | None |
| basis.product.CH3OH.state | liquid; downstream distillation included | None | None |
| basis.purchased_preheat_reason | None | None | None |
| basis.utilities.cooling_water_return_temperature | None | 313.15 | None |
| basis.utilities.cooling_water_supply_temperature | None | 298.15 | None |
| basis.utilities.reactor_steam_pressure | None | 10.0 | None |

### Group comparison: fixed_conversion

Compared 63; verdict agreement 44; pooled cost Spearman 0.5931319691499022.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/anie.201600943 / 50 bar / H2/CO2 4 / 26 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/cbh2.70072 / 30 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1002/cctc.202000974 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | True | True | 0.006337920800578489 | 1.601176895164055 | False | -0.589138004291471 |
| 10.1002/ente.201800747 / 40 bar / H2/CO2 3 / 21.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9225806451612902 |
| 10.1007/s11426-026-3904-1 / 20 bar / H2/CO2 3 / 6 NL/g/h | True | True | False | False | 0.00564524554683099 | 0.0 | False | -0.9999999999999999 |
| 10.1016/j.apcata.2018.04.036 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.apcatb.2017.06.069 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2019.05.040 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2020.05.049 / 41 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | False | False | 0.5494881656364579 | 0.0 | False | -0.35757575757575755 |
| 10.1016/j.fuel.2023.127927 / 20 bar / H2/CO2 3 / 2.4 NL/g/h | True | True | True | True | 0.00293910580850687 | 0.0041382837450147925 | False | -0.6 |
| 10.1016/j.fuel.2024.131111 / 40 bar / H2/CO2 5 / 12 NL/g/h | True | True | True | True | 0.11852910476962153 | 0.018884734499238442 | True | 0.9545454545454546 |
| 10.1016/j.jcat.2012.05.020 / 30 bar / H2/CO2 3 / 13.4 NL/g/h | True | True | True | True | 0.37642527212318266 | 0.18005819151258362 | True | 1.0 |
| 10.1016/j.jcat.2016.03.017 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.786764705882353 |
| 10.1016/j.jcou.2016.11.015 / 40 bar / H2/CO2 3.04 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.020516886214085206 | False | 0.709090909090909 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18000 h-1 | True | True | True | True | 0.23078988619465535 | 0.13639494639240657 | True | 1.0 |
| 10.1021/acs.energyfuels.6c02662 / 30 bar / H2/CO2 5 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1021/acs.iecr.6c02654 / 30 bar / H2/CO2 3 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.6c02734 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.iecr.6c02971 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.02356211730463298 | False | 0.1666666666666667 |
| 10.1021/acs.iecr.7b01464 / 30 bar / H2/CO2 3.03 / 0.873 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7 |
| 10.1021/acscatal.0c05628 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.1c03170 / 30 bar / H2/CO2 3 / 60 NL/g/h | True | True | True | True | 0.6282436322851057 | 0.2551737128014713 | True | 1.0 |
| 10.1021/acscatal.5c05984 / 100 bar / H2/CO2 4 / 10 NL/g/h | True | True | True | True | 0.06677576667724638 | 0.008492517145811673 | True | 0.8833333333333333 |
| 10.1021/acscatal.6c01275 / 50 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.07388133041860923 | 0.018539246928003683 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c01304 / 45 bar / H2/CO2 3 / 18 NL/g/h | True | False | True | False | 0.0 | 0.1039869045114703 | False | 0.5 |
| 10.1021/acscatal.6c02907 / 1 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 10 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.09116007328273557 | 0.032544680920693736 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 2.5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 15 NL/g/h | True | False | True | False | 0.0 | 0.2845075843408942 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 22.2 NL/g/h | True | False | True | False | 0.0 | 0.17414585382873415 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.07576922462739111 | 0.09575246561339457 | True | 0.8736842105263156 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 7.5 NL/g/h | True | False | True | False | 0.0 | 0.33583330966563096 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c03987 / 14 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.1011099180327637 | 0.057259222646021124 | True | 0.9521008403361345 |
| 10.1021/acscatal.6c03987 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9930069930069931 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 2 / 48 NL/g/h | True | True | True | True | 0.3641743828509605 | 0.12493154649874039 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | True | True | True | 0.1783189948265662 | 0.07401441692395383 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 4 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c05217 / 32 bar / H2/CO2 3 / 8 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c06647 / 50 bar / H2/CO2 3 / 9 NL/g/h | True | False | True | False | 0.0 | 0.006973839867956411 | False | 0.6000000000000001 |
| 10.1021/acscatal.6c06714 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.08532839889699151 | 0.010074369699464292 | True | 0.8929824561403509 |
| 10.1021/acscatal.6c06780 / 30 bar / H2/CO2 4 / 40 NL/g/h | True | False | True | False | 0.0 | 0.10768689579659774 | False | 0.7 |
| 10.1021/acscatal.9b01869 / 50 bar / H2/CO2 4 / 24000 h-1 | True | True | True | True | 0.044105922265119224 | 0.020721162973771134 | True | 0.976470588235294 |
| 10.1021/acscatal.9b03305 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.14461165180748758 | 0.03979192702633272 | False | 0.9580419580419581 |
| 10.1021/acssuschemeng.6c05638 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1021/cs500979c / 80 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.48703339048930516 |
| 10.1038/s41467-025-65929-z / 40 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.11824814800859951 | False | 0.03571428571428572 |
| 10.1038/s41467-025-65929-z / 50 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1038/s41467-026-72876-w / 20 bar / H2/CO2 3 / 450 NL/g/h | True | False | True | False | 0.0 | 0.03915302506637852 | False | -0.19999999999999998 |
| 10.1038/s41557-026-02104-x / 50 bar / H2/CO2 3 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.05593552335957974 | False | 0.7650401069518717 |
| 10.1038/s41565-026-02135-y / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.4007224192487715 | 0.1144569702860796 | True | 1.0 |
| 10.1039/c2cy20604h / 100 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | True | True | 1.5756208290777454 | 0.178112743119347 | False | -0.39090909090909093 |
| 10.1039/c2cy20604h / 30 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.0202078120027267 | 0.0 | False | 0.38181818181818183 |
| 10.1039/c2cy20604h / 360 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.08047535391634408 | 0.0 | False | -0.7636363636363637 |
| 10.1039/c2cy20604h / 4 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | True | False | 0.0 | 0.007457200819521725 | False | 0.9727272727272729 |
| 10.1039/c5cy00372e / 50 bar / H2/CO2 3.04 / 10 NL/g/h | True | False | True | False | 0.0 | 0.009917632294877077 | False | 0.7999999999999999 |
| 10.1039/c6ra28305e / 30 bar / H2/CO2 3 / 3600 h-1 | True | True | True | True | 0.026489322579082097 | 0.027721068422341677 | True | 1.0 |
| 10.1039/d0gc01597k / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 12 NL/g/h | True | True | False | False | 0.03654329764560704 | 0.0 | False | 0.9370629370629372 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 24 NL/g/h | True | True | False | False | 0.13308895943349142 | 0.0 | False | 0.39999999999999997 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 8 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1126/sciadv.aea7041 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.37647211950133985 | 0.0024699397847240956 | True | 0.7640228805600615 |

### Group comparison: raised_conversion

Compared 63; verdict agreement 43; pooled cost Spearman 0.5460383613900975.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/anie.201600943 / 50 bar / H2/CO2 4 / 26 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/cbh2.70072 / 30 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1002/cctc.202000974 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | True | True | True | 0.23866645454588142 | 1.601176895164055 | False | 0.11097659402744148 |
| 10.1002/ente.201800747 / 40 bar / H2/CO2 3 / 21.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9697441601779755 |
| 10.1007/s11426-026-3904-1 / 20 bar / H2/CO2 3 / 6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.apcata.2018.04.036 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1016/j.apcatb.2017.06.069 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2019.05.040 / 30 bar / H2/CO2 3 / 2.4 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1016/j.cattod.2020.05.049 / 41 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7575757575757575 |
| 10.1016/j.fuel.2023.127927 / 20 bar / H2/CO2 3 / 2.4 NL/g/h | True | True | True | True | 0.00293910580850687 | 0.0041382837450147925 | False | 0.0 |
| 10.1016/j.fuel.2024.131111 / 40 bar / H2/CO2 5 / 12 NL/g/h | True | True | True | True | 0.03507893251003047 | 0.018884734499238442 | False | 0.5090909090909091 |
| 10.1016/j.jcat.2012.05.020 / 30 bar / H2/CO2 3 / 13.4 NL/g/h | True | False | True | False | 0.0 | 0.18005819151258362 | False | 0.5 |
| 10.1016/j.jcat.2016.03.017 / 20 bar / H2/CO2 3 / 3.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7009803921568628 |
| 10.1016/j.jcou.2016.11.015 / 40 bar / H2/CO2 3.04 / 1.5 NL/g/h | True | False | True | False | 0.0 | 0.020516886214085206 | False | 0.709090909090909 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1016/j.jes.2023.05.010 / 30 bar / H2/CO2 4 / 18000 h-1 | True | True | True | True | 0.2602920578611956 | 0.13639494639240657 | True | 1.0 |
| 10.1021/acs.energyfuels.6c02662 / 30 bar / H2/CO2 5 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.iecr.6c02654 / 30 bar / H2/CO2 3 / 18 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.6c02734 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8166666666666667 |
| 10.1021/acs.iecr.6c02971 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.02356211730463298 | False | 0.1666666666666667 |
| 10.1021/acs.iecr.7b01464 / 30 bar / H2/CO2 3.03 / 0.873 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7 |
| 10.1021/acscatal.0c05628 / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8095238095238096 |
| 10.1021/acscatal.1c03170 / 30 bar / H2/CO2 3 / 60 NL/g/h | True | True | True | True | 0.006845659527301651 | 0.2551737128014713 | True | 1.0 |
| 10.1021/acscatal.5c05984 / 100 bar / H2/CO2 4 / 10 NL/g/h | True | True | True | True | 0.05853686005349812 | 0.008492517145811673 | True | 0.9 |
| 10.1021/acscatal.6c01275 / 50 bar / H2/CO2 3 / 24 NL/g/h | True | True | True | True | 0.1195684616386179 | 0.018539246928003683 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c01304 / 45 bar / H2/CO2 3 / 18 NL/g/h | True | False | True | False | 0.0 | 0.1039869045114703 | False | 0.5 |
| 10.1021/acscatal.6c02907 / 1 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 10 bar / H2/CO2 3 / 30 NL/g/h | True | False | True | False | 0.0 | 0.032544680920693736 | False | 0.7999999999999999 |
| 10.1021/acscatal.6c02907 / 2.5 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 15 NL/g/h | True | False | True | False | 0.0 | 0.2845075843408942 | False | -1.0 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 22.2 NL/g/h | True | False | True | False | 0.0 | 0.17414585382873415 | False | -0.5 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | True | False | 0.0 | 0.09575246561339457 | False | 0.8390977443609022 |
| 10.1021/acscatal.6c02907 / 20 bar / H2/CO2 3 / 7.5 NL/g/h | True | False | True | False | 0.0 | 0.33583330966563096 | False | -1.0 |
| 10.1021/acscatal.6c02907 / 5 bar / H2/CO2 3 / 30 NL/g/h | True | True | False | False | 0.003249082304640938 | 0.0 | False | 0.7999999999999999 |
| 10.1021/acscatal.6c03987 / 14 bar / H2/CO2 3 / 30 NL/g/h | True | True | True | True | 0.06144620415471924 | 0.057259222646021124 | False | 0.8963585434173669 |
| 10.1021/acscatal.6c03987 / 20 bar / H2/CO2 3 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8951048951048951 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 2 / 48 NL/g/h | True | False | True | False | 0.0 | 0.12493154649874039 | False | -0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 3 / 48 NL/g/h | True | False | True | False | 0.0 | 0.07401441692395383 | False | -0.9999999999999999 |
| 10.1021/acscatal.6c04842 / 30 bar / H2/CO2 4 / 48 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c05217 / 32 bar / H2/CO2 3 / 8 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.6c06647 / 50 bar / H2/CO2 3 / 9 NL/g/h | True | True | True | True | 0.20708663004896888 | 0.006973839867956411 | True | 0.7999999999999999 |
| 10.1021/acscatal.6c06714 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | False | True | False | 0.0 | 0.010074369699464292 | False | 0.8614035087719297 |
| 10.1021/acscatal.6c06780 / 30 bar / H2/CO2 4 / 40 NL/g/h | True | True | True | True | 0.000715399909406722 | 0.10768689579659774 | True | 0.9999999999999999 |
| 10.1021/acscatal.9b01869 / 50 bar / H2/CO2 4 / 24000 h-1 | True | False | True | False | 0.0 | 0.020721162973771134 | False | 0.8764705882352942 |
| 10.1021/acscatal.9b03305 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.012095875050900595 | 0.03979192702633272 | False | 0.6503496503496504 |
| 10.1021/acssuschemeng.6c05638 / 30 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.5 |
| 10.1021/cs500979c / 80 bar / H2/CO2 3 / 3600 h-1 | True | False | False | True | 0.0 | 0.0 | True | 0.3222124670763828 |
| 10.1038/s41467-025-65929-z / 40 bar / H2/CO2 3 / 12 NL/g/h | True | False | True | False | 0.0 | 0.11824814800859951 | False | 0.0 |
| 10.1038/s41467-025-65929-z / 50 bar / H2/CO2 3 / 12 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1038/s41467-026-72876-w / 20 bar / H2/CO2 3 / 450 NL/g/h | True | True | True | True | 0.19054719950689591 | 0.03915302506637852 | True | 1.0 |
| 10.1038/s41557-026-02104-x / 50 bar / H2/CO2 3 / 1.5 NL/g/h | True | True | True | True | 0.0030350075871916626 | 0.05593552335957974 | True | 0.8666443850267381 |
| 10.1038/s41565-026-02135-y / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 2.40437161291851e-06 | 0.1144569702860796 | True | 0.8857142857142855 |
| 10.1039/c2cy20604h / 100 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | True | False | 0.0 | 0.178112743119347 | False | 0.06363636363636364 |
| 10.1039/c2cy20604h / 30 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.41818181818181827 |
| 10.1039/c2cy20604h / 360 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | False | False | 0.014728905887972266 | 0.0 | False | -0.03636363636363637 |
| 10.1039/c2cy20604h / 4 bar / H2/CO2 3.8 / 10.6 NL/g/h | True | True | True | True | 0.14473181985254824 | 0.007457200819521725 | True | 0.9 |
| 10.1039/c5cy00372e / 50 bar / H2/CO2 3.04 / 10 NL/g/h | True | True | True | True | 0.003903945049308577 | 0.009917632294877077 | True | 0.8999999999999998 |
| 10.1039/c6ra28305e / 30 bar / H2/CO2 3 / 3600 h-1 | True | False | True | False | 0.0 | 0.027721068422341677 | False | 0.39999999999999997 |
| 10.1039/d0gc01597k / 50 bar / H2/CO2 4 / 21 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 12 NL/g/h | True | True | False | False | 0.11207281243707645 | 0.0 | False | 0.8391608391608393 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 3 / 24 NL/g/h | True | True | False | False | 0.2000487345172044 | 0.0 | False | -0.19999999999999998 |
| 10.1126/sciadv.abi6012 / 40 bar / H2/CO2 8 / 30 NL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1126/sciadv.aea7041 / 50 bar / H2/CO2 4 / 24 NL/g/h | True | True | True | True | 0.013187378216579893 | 0.0024699397847240956 | True | 0.8706565354734056 |

### Bottlenecks

```json
{
  "largest_cost_item": "feed",
  "hand_largest_cost_item": "feed",
  "controlling_property": "selectivity",
  "hand_controlling_property": "not available",
  "attribution_share": {
    "selectivity": 0.901,
    "activity": 0.04,
    "temperature": 0.005,
    "stability": 0.015,
    "metal": 0.039
  },
  "cheapest_record": "meoh:0174",
  "cheapest_catalyst": "5 wt % Re/TiO2 [Table 4 row 14]",
  "hand_cheapest_record": "meoh:0085",
  "hand_cheapest_catalyst": "0.5Ca-PZC [Text/Figure 7a, 0.5Ca-PZC, GHSV 12000 h−1]",
  "cheapest_common_record": "meoh:0174",
  "cheapest_common_catalyst": "5 wt % Re/TiO2 [Table 4 row 14]",
  "hand_cheapest_common_record": "meoh:0085",
  "hand_cheapest_common_catalyst": "0.5Ca-PZC [Text/Figure 7a, 0.5Ca-PZC, GHSV 12000 h−1]"
}
```

### Difference diagnosis and uncertainty

```json
{
  "rules": "deterministic evidence comparison; categories are evidence, not causal proof",
  "largest_reference_gaps": [
    {
      "field": "balances.energy_GJ_per_t",
      "hand": 0.7174226087781939,
      "ai": 11.255620028037415,
      "relative_gap": 14.688967548996388,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.energy",
      "hand": 18.886150176085955,
      "ai": 79.0614392617166,
      "relative_gap": 3.186212569771148,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.energy",
      "hand": 0.01941362192171753,
      "ai": 0.0642709113623277,
      "relative_gap": 2.3106089951421915,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.capital",
      "hand": 48.49700238747237,
      "ai": 152.5157761710088,
      "relative_gap": 2.1448495507509207,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.capital",
      "hand": 0.04985147634159827,
      "ai": 0.12398367678578341,
      "relative_gap": 1.4870612845286182,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.other",
      "hand": 190.11429895196932,
      "ai": 0.0,
      "relative_gap": -1.0,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.other",
      "hand": 0.1954240058113744,
      "ai": 0.0,
      "relative_gap": -1.0,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.feeds.H2.P_bar",
      "hand": 30,
      "ai": 1.01325,
      "relative_gap": -0.966225,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capacity_t_per_y",
      "hand": 1160000.0,
      "ai": 100000.0,
      "relative_gap": -0.9137931034482758,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.capacity_t_per_y",
      "hand": 1160000.0,
      "ai": 100000.0,
      "relative_gap": -0.9137931034482758,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capex_usd",
      "hand": 437553090.0,
      "ai": 113479000.1272387,
      "relative_gap": -0.7406508999233928,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.P_bar",
      "hand": 70.0,
      "ai": 100.0,
      "relative_gap": 0.4285714285714286,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    }
  ],
  "largest_ranking_gaps": {
    "fixed_conversion": [
      {
        "group": "10.1002/cctc.202000974 | 20 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pdzn/zntio3",
        "ai_leader": "zno",
        "hand_gap": 0.006337920800578489,
        "ai_gap": 1.601176895164055,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h",
        "hand_leader": "cu-k/al2o3",
        "ai_leader": "cu/al2o3",
        "hand_gap": 1.5756208290777454,
        "ai_gap": 0.178112743119347,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1016/j.cattod.2020.05.049 | 41 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pd-cu/ti0.8zr0.2o2",
        "ai_leader": "pd-cu/ti0.1zr0.9o2",
        "hand_gap": 0.5494881656364579,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 7.5 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.33583330966563096,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 15 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.2845075843408942,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 22.2 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.5",
        "hand_gap": 0.0,
        "ai_gap": 0.17414585382873415,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1126/sciadv.abi6012 | 40 bar | H2/CO2 3 | 24 NL/g/h",
        "hand_leader": "inni3c0.5/sio2",
        "ai_leader": "inni3c0.5/m-zro2",
        "hand_gap": 0.13308895943349142,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1038/s41467-025-65929-z | 40 bar | H2/CO2 3 | 12 NL/g/h",
        "hand_leader": "ldh-niincal",
        "ai_leader": "pfcp-niincce",
        "hand_gap": 0.0,
        "ai_gap": 0.11824814800859951,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c06780 | 30 bar | H2/CO2 4 | 40 NL/g/h",
        "hand_leader": "cza-2zr",
        "ai_leader": "cza-8zr",
        "hand_gap": 0.0,
        "ai_gap": 0.10768689579659774,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.9b03305 | 50 bar | H2/CO2 4 | 24 NL/g/h",
        "hand_leader": "25in2o3-75zro2",
        "ai_leader": "50in2o3-50zro2",
        "hand_gap": 0.14461165180748758,
        "ai_gap": 0.03979192702633272,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      }
    ],
    "raised_conversion": [
      {
        "group": "10.1002/cctc.202000974 | 20 bar | H2/CO2 3 | 3.6 NL/g/h",
        "hand_leader": "pdzn/zntio3",
        "ai_leader": "zno",
        "hand_gap": 0.23866645454588142,
        "ai_gap": 1.601176895164055,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 7.5 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.33583330966563096,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 15 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.25",
        "hand_gap": 0.0,
        "ai_gap": 0.2845075843408942,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1126/sciadv.abi6012 | 40 bar | H2/CO2 3 | 24 NL/g/h",
        "hand_leader": "inni3c0.5/sio2",
        "ai_leader": "inni3c0.5/m-zro2",
        "hand_gap": 0.2000487345172044,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1016/j.jcat.2012.05.020 | 30 bar | H2/CO2 3 | 13.4 NL/g/h",
        "hand_leader": "pdmgga",
        "ai_leader": "pdznal",
        "hand_gap": 0.0,
        "ai_gap": 0.18005819151258362,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h",
        "hand_leader": "cu-ba/al2o3",
        "ai_leader": "cu/al2o3",
        "hand_gap": 0.0,
        "ai_gap": 0.178112743119347,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c02907 | 20 bar | H2/CO2 3 | 22.2 NL/g/h",
        "hand_leader": "cuzn-nh4hco3",
        "ai_leader": "cuzn-naoh-0.5",
        "hand_gap": 0.0,
        "ai_gap": 0.17414585382873415,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1021/acscatal.6c04842 | 30 bar | H2/CO2 2 | 48 NL/g/h",
        "hand_leader": "znzr/90cu",
        "ai_leader": "gazr/90cu",
        "hand_gap": 0.0,
        "ai_gap": 0.12493154649874039,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1038/s41467-025-65929-z | 40 bar | H2/CO2 3 | 12 NL/g/h",
        "hand_leader": "ldh-niincal",
        "ai_leader": "pfcp-niincce",
        "hand_gap": 0.0,
        "ai_gap": 0.11824814800859951,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      },
      {
        "group": "10.1126/sciadv.abi6012 | 40 bar | H2/CO2 3 | 12 NL/g/h",
        "hand_leader": "inni3c0.5/sio2",
        "ai_leader": "inni3c0.5/m-zro2",
        "hand_gap": 0.11207281243707645,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data"
        ]
      }
    ]
  },
  "ranking_disagreements": {
    "fixed_conversion": 19,
    "raised_conversion": 20
  },
  "findings": [
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.purity_mol_frac",
        "hand": 0.995,
        "ai": 0.999
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.CO2.P_bar",
        "hand": 1,
        "ai": 1.01325
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.P_bar",
        "hand": 30,
        "ai": 1.01325
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "capacity_t_per_y",
        "hand": 1160000.0,
        "ai": 100000.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.CO2.purity_mol_frac",
        "hand": 1,
        "ai": 0.99
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "battery_limit",
        "hand": "purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source",
        "ai": "Separate purchased gaseous CO2 and H2 at ambient conditions through compression, synthesis, recycle, condensation, purification, heat recovery, utilities and offsites; upstream CO2 capture and H2 manufacture are excluded and charged through feed prices; products are specification methanol, purge gas and treated aqueous waste."
      },
      "impact": "different plant design basis"
    },
    {
      "category": "structure",
      "evidence": {
        "hand_units": [
          "Reactor modules",
          "Carbon dioxide compressor",
          "Hydrogen compressor",
          "Recycle/reflux compressor",
          "Reactor preheaters",
          "Heat exchangers",
          "Flash drums",
          "Distillation column",
          "Pump",
          "Furnace & blower",
          "Turbine & generator"
        ],
        "ai_units": [
          {
            "name": "CO2 feed compressor",
            "type": "compressor"
          },
          {
            "name": "H2 feed compressor",
            "type": "compressor"
          },
          {
            "name": "Synthesis feed mixer",
            "type": "other"
          },
          {
            "name": "Feed effluent exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "Methanol synthesis reactor",
            "type": "reactor"
          },
          {
            "name": "Effluent condenser",
            "type": "heat_exchanger"
          },
          {
            "name": "High pressure knockout",
            "type": "knockout"
          },
          {
            "name": "Recycle purge splitter",
            "type": "other"
          },
          {
            "name": "Recycle compressor",
            "type": "compressor"
          },
          {
            "name": "Methanol purification",
            "type": "separation"
          },
          {
            "name": "Cooling water system",
            "type": "offsites"
          },
          {
            "name": "Wastewater treatment and plant offsites",
            "type": "offsites"
          }
        ],
        "ai_checklist": {
          "feed_preparation": {
            "included": [
              "CO2 feed compressor",
              "H2 feed compressor",
              "Synthesis feed mixer",
              "Feed effluent exchanger"
            ]
          },
          "reactor_heat_supply_or_removal": {
            "included": [
              "Methanol synthesis reactor"
            ]
          },
          "catalyst_regeneration": {
            "excluded": "No in-situ regeneration is assumed because the literature does not establish a common regeneration protocol across catalyst families; spent catalyst is periodically replaced and annualized."
          },
          "product_compression": {
            "excluded": "Specification methanol leaves distillation as a pressurized liquid at the required 5 bar battery-limit condition, so no separate product compressor is required."
          },
          "separation_and_purification": {
            "included": [
              "Effluent condenser",
              "High pressure knockout",
              "Methanol purification"
            ]
          },
          "recycle": {
            "included": [
              "Recycle purge splitter",
              "Recycle compressor",
              "Synthesis feed mixer"
            ]
          },
          "heat_recovery": {
            "included": [
              "Feed effluent exchanger"
            ]
          },
          "utilities_and_offsites": {
            "included": [
              "Cooling water system",
              "Wastewater treatment and plant offsites"
            ]
          }
        },
        "missing_hand_unit_types": [
          "furnace",
          "pump"
        ],
        "extra_ai_unit_types": [
          "knockout",
          "offsites",
          "other"
        ],
        "ai_recycle_declaration": {
          "included": [
            "Recycle purge splitter",
            "Recycle compressor",
            "Synthesis feed mixer"
          ]
        },
        "hand_kinetics": "lab conversion capped by equilibrium; purge and CO recycle optimisation"
      },
      "impact": "unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim"
    },
    {
      "category": "parameters",
      "evidence": {
        "gaps_gt20pct": [],
        "unmatched_hand_parameters": [
          "co2_feed_pressure_bar",
          "compressor_efficiency",
          "discount_rate",
          "h2_feed_pressure_bar",
          "loop_dp_bar",
          "plant_life_y"
        ],
        "hand_parameters": {
          "compressor_efficiency": 0.8,
          "discount_rate": 0.1,
          "plant_life_y": 20,
          "h2_feed_pressure_bar": 30.0,
          "co2_feed_pressure_bar": 1.0,
          "loop_dp_bar": 1.5
        },
        "ai_parameters": {
          "price.natural_gas": 2.5,
          "price.electricity": 80.0,
          "price.hydrogen": 3.0,
          "price.carbon_dioxide": 100.0,
          "price.catalyst_support_and_manufacturing": 20.0,
          "finance.capital_recovery_factor": 0.0944,
          "finance.fixed_om_fraction_of_capex": 0.04,
          "price.metal_Al": 3.9683,
          "price.metal_Ce": 2.1005306603773586,
          "price.metal_Co": 56.28401553583051,
          "price.metal_Cu": 13.889122517655,
          "price.metal_Fe": 8.0,
          "price.metal_Ga": 580.0,
          "price.metal_In": 370.0,
          "price.metal_Mo": 91.227284092153,
          "price.metal_Ni": 16.9094555095895,
          "price.metal_Pd": 40670.694409279,
          "price.metal_Pt": 51508.71107755406,
          "price.metal_Si": 2.866006,
          "price.metal_Zn": 3.2849,
          "price.metal_Zr": 22.0,
          "thermo.dH_methanol_kJ_per_mol": -49.5,
          "thermo.dH_rwgs_kJ_per_mol": 41.2,
          "thermo.dG_methanol_298_kJ_per_mol": 3.8,
          "thermo.dCp_methanol_J_per_molK": -56.0,
          "process.purge_fraction": 0.03,
          "process.methanol_recovery": 0.995,
          "process.methanol_condensation_fraction": 0.995,
          "process.water_condensation_fraction": 0.999,
          "process.recycle_pressure_drop_bar": 3.0,
          "process.feed_preheat_recovery_fraction": 0.7,
          "process.distillation_energy_GJ_per_t_feed": 1.8,
          "process.wastewater_energy_GJ_per_t": 0.05,
          "process.cooling_electricity_GJ_per_GJ": 0.02,
          "process.electricity_primary_energy_factor": 2.5,
          "compressor.isentropic_efficiency": 0.75,
          "compressor.intercool_temperature_K": 313.15,
          "kinetics.activation_energy_J_per_mol": 60000.0,
          "kinetics.order_CO2": 0.5,
          "kinetics.order_H2": 0.5,
          "kinetics.max_activity_extrapolation_factor": 10.0,
          "kinetics.minimum_driving_force": 0.05,
          "operation.T_min_K": 473.15,
          "operation.T_max_K": 573.15,
          "operation.P_min_bar": 30.0,
          "operation.P_max_bar": 100.0,
          "operation.minimum_conversion": 0.02,
          "operation.equilibrium_fraction": 0.95,
          "catalyst.default_life_y": 4.0,
          "catalyst.default_average_activity": 0.9,
          "catalyst.replacement_activity_fraction": 0.5,
          "catalyst.bulk_density_kg_per_m3": 1000.0,
          "capital.scaling_exponent": 0.65,
          "capital.compressor_usd_per_MW": 2000000.0,
          "capital.compressor_min_usd": 1000000.0,
          "capital.mixer_usd": 300000.0,
          "capital.heat_exchanger_usd_per_MW": 600000.0,
          "capital.heat_exchanger_min_usd": 500000.0,
          "capital.reactor_base_usd": 15000000.0,
          "capital.knockout_base_usd": 2000000.0,
          "capital.splitter_usd": 200000.0,
          "capital.distillation_base_usd": 15000000.0,
          "capital.cooling_system_base_usd": 5000000.0,
          "capital.wastewater_base_usd": 3000000.0,
          "capital.offsites_fraction_direct": 0.1,
          "capital.reference_capacity_t_per_y": 100000.0,
          "capital.reference_cooling_MW": 10.0,
          "capital.reactor_inventory_factor": 0.5,
          "capital.reference_catalyst_volume_m3": 100.0,
          "operation.selectivity_conversion_cap_intercept": 0.05,
          "operation.selectivity_conversion_cap_slope": 0.3,
          "basis.capacity_t_per_y": 100000.0,
          "basis.operating_hours_per_y": 8000.0,
          "basis.feeds.CO2.T_K": 298.15,
          "basis.feeds.CO2.P_bar": 1.01325,
          "basis.feeds.CO2.purity_mol_frac": 0.99,
          "basis.feeds.H2.T_K": 298.15,
          "basis.feeds.H2.P_bar": 1.01325,
          "basis.feeds.H2.purity_mol_frac": 0.999,
          "basis.feeds.H2O.T_K": 298.15,
          "basis.feeds.H2O.P_bar": 1.01325,
          "basis.feeds.H2O.purity_mol_frac": 1.0,
          "basis.product.CH3OH.P_bar": 5.0,
          "basis.product.CH3OH.purity_mol_frac": 0.997,
          "basis.utilities.cooling_water_supply_temperature": 298.15,
          "basis.utilities.cooling_water_return_temperature": 313.15,
          "basis.utilities.reactor_steam_pressure": 10.0
        },
        "price_table_rows": [
          {
            "parameter": "price.natural_gas",
            "value": "2.5",
            "unit": "USD/GJ",
            "source": "prices.json:natural_gas",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "2.0",
            "high": "12.0"
          },
          {
            "parameter": "price.electricity",
            "value": "80.0",
            "unit": "USD/MWh",
            "source": "prices.json:electricity",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "40.0",
            "high": "150.0"
          },
          {
            "parameter": "price.hydrogen",
            "value": "3.0",
            "unit": "USD/kg",
            "source": "prices.json:hydrogen",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "1.5",
            "high": "7.0"
          },
          {
            "parameter": "price.carbon_dioxide",
            "value": "100.0",
            "unit": "USD/t",
            "source": "prices.json:carbon_dioxide",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "20.0",
            "high": "200.0"
          },
          {
            "parameter": "price.catalyst_support_and_manufacturing",
            "value": "20.0",
            "unit": "USD/kg",
            "source": "prices.json:catalyst_support_and_manufacturing",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "5.0",
            "high": "100.0"
          },
          {
            "parameter": "finance.capital_recovery_factor",
            "value": "0.0944",
            "unit": "1/y",
            "source": "prices.json:capital_recovery_factor",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "0.08",
            "high": "0.13"
          },
          {
            "parameter": "finance.fixed_om_fraction_of_capex",
            "value": "0.04",
            "unit": "1/y",
            "source": "prices.json:fixed_om_fraction_of_capex",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "0.02",
            "high": "0.06"
          },
          {
            "parameter": "price.metal_Al",
            "value": "3.9683",
            "unit": "USD/kg",
            "source": "prices.json:metal_Al",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "1.98415",
            "high": "7.9366"
          },
          {
            "parameter": "price.metal_Ce",
            "value": "2.1005306603773586",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ce",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "1.0502653301886793",
            "high": "4.201061320754717"
          },
          {
            "parameter": "price.metal_Co",
            "value": "56.28401553583051",
            "unit": "USD/kg",
            "source": "prices.json:metal_Co",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "28.142007767915256",
            "high": "112.56803107166104"
          },
          {
            "parameter": "price.metal_Cu",
            "value": "13.889122517655",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cu",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "6.9445612588275",
            "high": "27.77824503531"
          },
          {
            "parameter": "price.metal_Fe",
            "value": "8.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Fe",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "4.0",
            "high": "16.0"
          },
          {
            "parameter": "price.metal_Ga",
            "value": "580.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ga",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "290.0",
            "high": "1160.0"
          },
          {
            "parameter": "price.metal_In",
            "value": "370.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_In",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "185.0",
            "high": "740.0"
          },
          {
            "parameter": "price.metal_Mo",
            "value": "91.227284092153",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mo",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "45.61364204607651",
            "high": "182.45456818430603"
          },
          {
            "parameter": "price.metal_Ni",
            "value": "16.9094555095895",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ni",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "8.45472775479475",
            "high": "33.818911019179"
          },
          {
            "parameter": "price.metal_Pd",
            "value": "40670.694409279",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pd",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "20335.3472046395",
            "high": "81341.388818558"
          },
          {
            "parameter": "price.metal_Pt",
            "value": "51508.71107755406",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pt",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "25754.35553877703",
            "high": "103017.42215510811"
          },
          {
            "parameter": "price.metal_Si",
            "value": "2.866006",
            "unit": "USD/kg",
            "source": "prices.json:metal_Si",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "1.433003",
            "high": "5.732012"
          },
          {
            "parameter": "price.metal_Zn",
            "value": "3.2849",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zn",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "1.64245",
            "high": "6.5698"
          },
          {
            "parameter": "price.metal_Zr",
            "value": "22.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zr",
            "location": "workspace fixed price table",
            "type": "price_table",
            "low": "11.0",
            "high": "44.0"
          }
        ]
      },
      "impact": "price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved"
    },
    {
      "category": "data",
      "evidence": {
        "rejected": [],
        "converted": 699,
        "total": 699,
        "missing_loading_records": 553
      },
      "impact": "unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking"
    },
    {
      "category": "numerics",
      "evidence": "all converted record costs finite, positive and parts close; deterministic repeat checked",
      "impact": "does not verify the optimiser reaches a global minimum"
    }
  ],
  "uncertainty": {
    "hand": {
      "productivity_density_g_cm3": [
        0.5,
        2
      ],
      "scope": "frozen hand sensitivity; no matched AI uncertainty distribution"
    },
    "ai_assumptions": [
      {
        "parameter": "process.purge_fraction",
        "value": "0.03",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.1"
      },
      {
        "parameter": "process.methanol_recovery",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.98",
        "high": "0.999"
      },
      {
        "parameter": "process.methanol_condensation_fraction",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.98",
        "high": "0.999"
      },
      {
        "parameter": "process.water_condensation_fraction",
        "value": "0.999",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.98",
        "high": "1.0"
      },
      {
        "parameter": "process.recycle_pressure_drop_bar",
        "value": "3.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "8.0"
      },
      {
        "parameter": "process.feed_preheat_recovery_fraction",
        "value": "0.7",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.5",
        "high": "0.9"
      },
      {
        "parameter": "process.distillation_energy_GJ_per_t_feed",
        "value": "1.8",
        "unit": "GJ/t crude liquid",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.8",
        "high": "4.0"
      },
      {
        "parameter": "process.wastewater_energy_GJ_per_t",
        "value": "0.05",
        "unit": "GJ/t water",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.2"
      },
      {
        "parameter": "process.cooling_electricity_GJ_per_GJ",
        "value": "0.02",
        "unit": "GJ electricity/GJ heat rejected",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.005",
        "high": "0.05"
      },
      {
        "parameter": "process.electricity_primary_energy_factor",
        "value": "2.5",
        "unit": "GJ primary/GJ electricity",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2.0",
        "high": "3.2"
      },
      {
        "parameter": "compressor.isentropic_efficiency",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.65",
        "high": "0.85"
      },
      {
        "parameter": "compressor.intercool_temperature_K",
        "value": "313.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "298.15",
        "high": "323.15"
      },
      {
        "parameter": "kinetics.activation_energy_J_per_mol",
        "value": "60000.0",
        "unit": "J/mol",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "30000.0",
        "high": "100000.0"
      },
      {
        "parameter": "kinetics.order_CO2",
        "value": "0.5",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.0",
        "high": "1.0"
      },
      {
        "parameter": "kinetics.order_H2",
        "value": "0.5",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.0",
        "high": "1.5"
      },
      {
        "parameter": "kinetics.max_activity_extrapolation_factor",
        "value": "10.0",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "3.0",
        "high": "30.0"
      },
      {
        "parameter": "kinetics.minimum_driving_force",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.2"
      },
      {
        "parameter": "operation.T_min_K",
        "value": "473.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "453.15",
        "high": "493.15"
      },
      {
        "parameter": "operation.T_max_K",
        "value": "573.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "543.15",
        "high": "603.15"
      },
      {
        "parameter": "operation.P_min_bar",
        "value": "30.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20.0",
        "high": "50.0"
      },
      {
        "parameter": "operation.P_max_bar",
        "value": "100.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "80.0",
        "high": "150.0"
      },
      {
        "parameter": "operation.minimum_conversion",
        "value": "0.02",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.005",
        "high": "0.05"
      },
      {
        "parameter": "operation.equilibrium_fraction",
        "value": "0.95",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.85",
        "high": "0.99"
      },
      {
        "parameter": "catalyst.default_life_y",
        "value": "4.0",
        "unit": "y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "8.0"
      },
      {
        "parameter": "catalyst.default_average_activity",
        "value": "0.9",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.7",
        "high": "1.0"
      },
      {
        "parameter": "catalyst.replacement_activity_fraction",
        "value": "0.5",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.3",
        "high": "0.8"
      },
      {
        "parameter": "catalyst.bulk_density_kg_per_m3",
        "value": "1000.0",
        "unit": "kg/m3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "500.0",
        "high": "1500.0"
      },
      {
        "parameter": "capital.scaling_exponent",
        "value": "0.65",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.55",
        "high": "0.8"
      },
      {
        "parameter": "capital.compressor_usd_per_MW",
        "value": "2000000.0",
        "unit": "USD/MW",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1000000.0",
        "high": "4000000.0"
      },
      {
        "parameter": "capital.compressor_min_usd",
        "value": "1000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "500000.0",
        "high": "2500000.0"
      },
      {
        "parameter": "capital.mixer_usd",
        "value": "300000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100000.0",
        "high": "1000000.0"
      },
      {
        "parameter": "capital.heat_exchanger_usd_per_MW",
        "value": "600000.0",
        "unit": "USD/MW",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "300000.0",
        "high": "1200000.0"
      },
      {
        "parameter": "capital.heat_exchanger_min_usd",
        "value": "500000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "200000.0",
        "high": "1500000.0"
      },
      {
        "parameter": "capital.reactor_base_usd",
        "value": "15000000.0",
        "unit": "USD at basis capacity",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000000.0",
        "high": "30000000.0"
      },
      {
        "parameter": "capital.knockout_base_usd",
        "value": "2000000.0",
        "unit": "USD at basis capacity",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1000000.0",
        "high": "5000000.0"
      },
      {
        "parameter": "capital.splitter_usd",
        "value": "200000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "50000.0",
        "high": "500000.0"
      },
      {
        "parameter": "capital.distillation_base_usd",
        "value": "15000000.0",
        "unit": "USD at 100000 t/y crude",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000000.0",
        "high": "30000000.0"
      },
      {
        "parameter": "capital.cooling_system_base_usd",
        "value": "5000000.0",
        "unit": "USD at 10 MW rejected",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2000000.0",
        "high": "10000000.0"
      },
      {
        "parameter": "capital.wastewater_base_usd",
        "value": "3000000.0",
        "unit": "USD at basis capacity",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1000000.0",
        "high": "8000000.0"
      },
      {
        "parameter": "capital.offsites_fraction_direct",
        "value": "0.1",
        "unit": "fraction of direct unit capital",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.05",
        "high": "0.25"
      },
      {
        "parameter": "capital.reference_capacity_t_per_y",
        "value": "100000.0",
        "unit": "t/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "50000.0",
        "high": "200000.0"
      },
      {
        "parameter": "capital.reference_cooling_MW",
        "value": "10.0",
        "unit": "MW",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "5.0",
        "high": "30.0"
      },
      {
        "parameter": "capital.reactor_inventory_factor",
        "value": "0.5",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.2",
        "high": "1.5"
      },
      {
        "parameter": "capital.reference_catalyst_volume_m3",
        "value": "100.0",
        "unit": "m3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "40.0",
        "high": "300.0"
      },
      {
        "parameter": "operation.selectivity_conversion_cap_intercept",
        "value": "0.05",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.02",
        "high": "0.1"
      },
      {
        "parameter": "operation.selectivity_conversion_cap_slope",
        "value": "0.3",
        "unit": "fraction/fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.15",
        "high": "0.6"
      }
    ]
  }
}
```

## Across-build agreement

```json
{
  "reference_spread": 0.5707678331498807,
  "spread_within20pct": false,
  "pairwise_spearman": {
    "D:\\agent_runs\\meoh_b1 vs D:\\agent_runs\\meoh_b2": 0.9811369606825128,
    "D:\\agent_runs\\meoh_b1 vs D:\\agent_runs\\meoh_b3": 0.8878443640752557,
    "D:\\agent_runs\\meoh_b2 vs D:\\agent_runs\\meoh_b3": 0.8607865867575235
  },
  "pairwise_ge08": true,
  "quantitative_consistency": false,
  "common_successful_records": 699,
  "conclusions": {
    "largest_cost_item": {
      "status": "robust (all agree)",
      "values": {
        "D:\\agent_runs\\meoh_b1": "feed",
        "D:\\agent_runs\\meoh_b2": "feed",
        "D:\\agent_runs\\meoh_b3": "feed"
      }
    },
    "controlling_property": {
      "status": "majority",
      "values": {
        "D:\\agent_runs\\meoh_b1": "activity",
        "D:\\agent_runs\\meoh_b2": "activity",
        "D:\\agent_runs\\meoh_b3": "selectivity"
      }
    },
    "cheapest_common_catalyst": {
      "status": "robust (all agree)",
      "values": {
        "D:\\agent_runs\\meoh_b1": "5 wt % Re/TiO2 [Table 4 row 14]",
        "D:\\agent_runs\\meoh_b2": "5 wt % Re/TiO2 [Table 4 row 14]",
        "D:\\agent_runs\\meoh_b3": "5 wt % Re/TiO2 [Table 4 row 14]"
      }
    }
  }
}
```

Primary build (median reference cost): D:\agent_runs\meoh_b1

## Loader exclusions

[]
