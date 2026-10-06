# Methanol plant model benchmarked against real plants and process TEAs — 2026-10-06

Question: does the CO2-to-methanol recycle-economics model behave like a real plant? This is the model that decides the
headline result: the paper's STY leader ≠ the plant-cost leader in 33 of 83 published comparison groups
(`analysis/meoh_literature_inversion_2026_10_05/`). And could any disagreement change that result?

This is the **second pass**. All values now come from primary full texts, except three pilot-plant rows that only
Dieterich 2020 tabulates. The first pass used Pérez-Fortes 2016 and Szima 2018 only through review tables, and read the
anchor's cost split off a figure. What changed is listed in §6.

**Answer**

- **Plant metrics.** At each study's own operating point the model loop agrees with the Aspen/CHEMCAD loops of
  Campos 2022, Pérez-Fortes 2016, Van-Dal 2013, Szima 2018, Nyári 2022 and Nieminen 2019, and with the industrial
  ranges:
  - H2 0.193–0.210 t/t against 0.189–0.234;
  - CO2 1.40–1.53 t/t against 1.37–1.71;
  - carbon efficiency 0.90–0.98 against 0.81–0.98;
  - compression 0.17–0.25 MWh/t against 0.14–0.62;
  - recycle ratio 2.6–7.7 against 2.7–7.7;
  - GHSV of catalysts sized from measured STY 1.2–2.9 × 10⁴ h⁻¹ against 0.6–2.1 × 10⁴.
- **Cost, at each study's own prices, scale and finance.** On the cost terms every TEA shares (feed, power, catalyst,
  capital, plus the study's own fixed O&M), the model reproduces:
  - Pérez-Fortes to −2.4 % (706 vs 723.6 €/t);
  - Szima to +1.3 % (853 vs 842);
  - Nyári's three kinetic models to −0.9 to −5.1 %;
  - the anchor three-step design to +1.2 % (+0.2 % with the catalyst charge).
- **Pérez-Fortes, 724 vs 913 €/t.** 723.6 €/t is Pérez-Fortes's NPV = 0 **breakeven price**: production cost 666 plus
  58 of capital recovery. It is not the 724 "production cost" the secondary tables implied.
  - Run at Pérez-Fortes's own point, the model's full NPC is 841 €/t, not 913.
  - The +118 €/t that remains is the anchor's cost-accounting convention: 57 €/t of catalyst-independent direct OPEX
    plus 10 % of NPC for distribution, selling and R&D, about 126 €/t together. It is common to every catalyst.
- **Headline.**
  - Every loop term set to a primary value leaves it at **32–34/83**: loop ΔP 4.2 bar; equipment split from the Campos
    SI; recycle costs ×10, which reproduces Nyári's kinetic-model cost spread; prices.
  - **The catalyst replacement charge is the one term that moves it.** The anchor's 18.1 €/kg every 3 y gives 32/83. At
    the 95.24 €/kg used by Pérez-Fortes, Nieminen, Sollai and Battaglia the result depends on lifetime: 30/83 at 6 y,
    27/83 at 4 y, and 18/83 at Pérez-Fortes's yearly replacement.
  - An expensive, short-lived catalyst makes inventory, and so STY, count more, and paper and plant rankings converge.
    Even then 22–36 % of groups keep a different winner.

```
python analysis/meoh_plant_benchmark_2026_10_06/lit_sensitivity.py   # 18 variants, ~2.7 min on 8 workers
python analysis/meoh_plant_benchmark_2026_10_06/run_benchmark.py     # Tables A and B, CAPEX scale, driver decomposition
```

Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe`, with `PYTHONIOENCODING=utf-8`. Use at most 8 workers
(`BENCH_WORKERS`): each takes about 0.8 GB.

- **Frozen models.** `data/meoh/meoh_d01_model.py` and `data/meoh/meoh_general_model.py` are unchanged.
- **`plant_variant.py`.** Restates `meoh_general_model.economics` with the following exposed as keywords:
  - prices, scale and hours;
  - finance and CEPCI year;
  - loop pressure drop;
  - catalyst replacement;
  - recycle-flow multiplier;
  - equipment split.

  At default keywords it equals the frozen model to 1.8e-12 EUR/t; `run_benchmark.py` asserts this.
- **`lit_sensitivity.py`.** Reproduces the frozen headline exactly (33/83, 1019/8458) before running any variant.

## 1. Sources (`reference_values.csv`, 249 values)

Each value has its locator (PDF page / printed page, table or figure) and the conversion applied. The `kind` column:

| Kind | Rows | What it means |
|---|---:|---|
| `source_fact` | 175 | printed number |
| `derived` | 60 | arithmetic on printed numbers, shown in the row |
| `secondary` | 13 | Lurgi and Mitsui CO2 pilots and the CRI George Olah operating conditions, as tabulated by Dieterich 2020. Their primaries were not downloaded. |
| `figure_reading` | 1 | Nyári's Fig. 6 cost split, which the paper does not tabulate |

When a value replaced an earlier secondary value or figure reading, the old value is kept in `note`.

| ID | Source | Role |
|---|---|---|
| CAMPOS22 (+ SI) | Lacerda de Oliveira Campos et al., *Processes* 10, 1535 (2022), 10.3390/pr10081535, and its Supplementary Material (Tables S9–S19) | model anchor (calibration point) and its three-step design (out of sample) |
| PEREZFORTES16 | Pérez-Fortes et al., *Appl. Energy* 161, 718 (2016), 10.1016/j.apenergy.2015.07.067; JRC report EUR 27629 (10.2790/981669) | rigorous CO2 TEA, H2 bought (manuscript ref. 14) |
| SZIMA18 | Szima & Cormos, *J. CO2 Util.* 24, 555 (2018), 10.1016/j.jcou.2018.02.007 | rigorous TEA; electrolyser electricity inside, electrolyser CAPEX excluded |
| NYARI22 | Nyári et al., *Energy Convers. Manag.* 271, 116200 (2022), 10.1016/j.enconman.2022.116200 | one plant, three CZA kinetic models: catalyst → cost |
| NIEMINEN19 | Nieminen, Laari, Koiranen, *Processes* 7, 405 (2019), 10.3390/pr7070405 | gas-phase reference loop, H2 bought |
| SCHORN21 | Schorn et al., *Adv. Appl. Energy* 3, 100050 (2021), 10.1016/j.adapen.2021.100050 | NPC grid over H2 and CO2 prices |
| VANDAL13 | Van-Dal & Bouallou, *J. Clean. Prod.* 57, 38 (2013), 10.1016/j.jclepro.2013.06.008 | loop (no economics) |
| SOLLAI23, BATTAGLIA21, ZHANG19 | *J. CO2 Util.* 68, 102345 (2023); 44, 101407 (2021); *Energies* 12, 3742 (2019) | loops with the electrolyser inside: Table A only |
| CORDERO22 | Cordero-Lanzac et al., *J. Energy Chem.* 68, 255 (2022), 10.1016/j.jechem.2021.09.045 | In2O3/Co plant; origin of the anchor's prices (3.5 USD/kg and 50 USD/t ÷ 1.13) |
| BOZZANO16, DIETERICH20, OTT12, HANSEN08, NESTLER18 | industrial-loop reviews (Prog. Energy Combust. Sci. 2016; EES 2020; Ullmann's 2012; Handbook Het. Catal. 2008; CIT 2018) | industrial ranges |
| GONZALEZ19, HANK18, BOS20, RIHKO10, MARLIN18, CRI_OLAH, CRI_SHUNLI | first pass, unchanged | |

Yusuf 2023 (Fuel 332, 126027) was read but is not used. It feeds H2/CO2 = 7, gives no CAPEX figure, and reports a
yield above its own conversion. Nyári 2020 (J. CO2 Util.) is still missing and is left out.

## 2. Table A — plant metrics (`reconciliation_plant.csv`)

Model columns, with recycled CO and the central RWGS rule unless noted:

| Column | Case |
|---|---|
| M1 | anchor one-step (calibration) |
| M2 | anchor three-step inputs |
| M3 | canonical optimum, 5 wt% Re 200 °C, 2 % purge, inert CO (943.30 €/t) |
| M4 | 1 wt% Re 200 °C at 0.5 % purge (895.25) |
| M5 | Lurgi CO2 pilot point\* |
| M6 | González-Garay point |
| M7 | Pérez-Fortes: X 0.2197, 76 bar, inlet H2/CO2 3.8, outlet 288 °C, 1 % purge, 44.5 t |
| M8 | Van-Dal: X 0.33, 75.7 bar, 1 % purge, 44.5 t |
| M9 | Szima: X 0.3005, 80 bar, 1 % purge |
| M10, M11 | Nyári Slotboom and VD: X and purge fitted to each model's recycle ratio and yield |
| M12 | Nieminen: X 0.203, S 0.961, 50 bar, 1 % purge, 3.49 t |

Selected rows follow. All rows and every reference value are in the CSV.

| Metric | M1 | M3 | M7 PF | M8 VD | M9 Szima | M10 Ny-Sl | M11 Ny-VD | M12 Nieminen | References (primary) |
|---|---|---|---|---|---|---|---|---|---|
| Per-pass CO2 conversion | 0.285 | 0.33 | 0.2197 | 0.33 | 0.3005 | 0.275 (fit) | 0.118 (fit) | 0.203 | PF 0.2197; VD 0.33; Szima 0.3005; Nieminen 0.203; Zhang 0.21 |
| Recycle ratio | 2.84 | 3.40 | 5.38 | 2.65 | 2.92 | 2.89 | 7.67 | 4.75 | Campos 2.81; PF ≈4.7; VD 5.0; Nieminen 5.3; Zhang 5.2; Nyári 2.89–7.67; Bozzano ≈5; industrial 3–5 |
| H2 (t/t) | 0.199 | 0.208 | 0.199 | 0.193 | 0.193 | 0.201 | 0.210 | 0.197 | Campos 0.200 (pure); **PF 0.199**; VD 0.204; **Szima 0.194**; **Nyári 0.202 / 0.211**; Nieminen 0.234; Schorn 0.189 |
| CO2 (t/t) | 1.449 | 1.473 | 1.438 | 1.405 | 1.407 | 1.466 | 1.534 | 1.439 | Campos 1.457; PF 1.460; VD 1.484; Szima 1.41; Nyári 1.47 / 1.53; Nieminen 1.706 |
| Carbon efficiency | 0.948 | 0.932 | 0.955 | 0.978 | 0.976 | 0.937 | 0.896 | 0.954 | Campos 0.943; PF 0.9385; VD 0.925; Szima 0.9725; Nyári 0.937 / 0.896; Nieminen 0.805 |
| Compression (MWh/t) | 0.199 | 0.246 | 0.213 | 0.201 | 0.208 | 0.201 | 0.223 | 0.169 | compressors only: Campos 0.325, PF 0.305, Szima 0.229, Sollai 0.207; whole plant: Nyári 0.140 / 0.474, Nieminen 0.624, Schorn 0.154 |
| GHSV (h⁻¹) | 617 | 13,050 | 24,780 | 15,010 | 2,050 | 13,160 | 28,920 | 11,710 | PF ≈21,000; SRC 6,000–12,000 |
| STY (kg/L/h) | 0.053 | 0.95 | 1.30 | 1.40 | 0.18 | 1.11 | 1.06 | 0.68 | PF 1.31; VD 1.42; CO2 feed 0.4–0.8 |
| Catalyst lifetime | 3 y, in the constant residual | | | | | | | | PF 1 y (yearly replacement); Nyári 3; Campos 3; Nieminen, Sollai, Zhang 4; Bozzano 3–4; Dieterich 4–6 |
| Loop ΔP (bar) | 1.5 | | | | | | | | **PF 4.2; VD 4.6; Zhang 4**; Schorn 1; Lurgi SRC 3.5–4 |

\*M5 is unchanged from the first pass: X 0.40, carbon efficiency 95.25 %, GHSV 10,500. Its recycle ratio of 1.68 against
the pilot's 4.5 remains a secondary-value comparison.

## 3. Table B — cost at each study's own assumptions (`reconciliation_cost.csv`)

Each model run uses the study's own:
- prices for H2, CO2 and electricity;
- catalyst price and lifetime;
- capacity and hours;
- discount rate and plant life;
- CEPCI year (2014, 2017, 2018 or 2021 vs 2020; CEPCI annual averages 576.1 / 567.5 / 603.1 / 708.0 / 596.2).

"Like-for-like" adds up the terms every TEA shares: feed + compression electricity + catalyst replacement + capital
annuity at the study's own rate, plus the study's own fixed O&M. "Anchor convention" is the model's full NPC, which
also carries the anchor's catalyst-independent residual direct OPEX and the 10 % of NPC for selling and R&D.

| Case | Term | Model | Reference | Deviation | Attribution |
|---|---|---:|---:|---:|---|
| **B1 Campos one-step** (calibration; SI Table S19) | H2 | 615.0 | 663.4 | −48 | Campos prices the 31.1 t/h H2 **stream**, which includes 0.5 % N2 (2.0 t/h). Pricing the model's pure H2 the same way gives ×1.0698 = 657.9. |
| | CO2 / catalyst / power | 64.2 / 0 / 17.9 | 64.6 / 14.9 / 10.9 | | The model holds the catalyst in the constant residual. Model power is compressors only (28.9 vs 47.18 MW) with no Rankine credit (29.82 MW). |
| | ACC / indirect / **total** | 46.0 / 123.6 / **923.6** | 46.1 / 123.6 / **924.0** | **−0.03 %** | calibration identity |
| **B2 Campos three-step** (out of sample) | total | 881.3 | 871.2 | +1.2 % | |
| | total with the catalyst term (18.1 €/kg, 3 y) | 873.0 | 871.2 | **+0.2 %** | |
| | saving vs one-step | 42.4 | 52.8 | −10.4 | the halved catalyst charge, 7.5 €/t, is constant in the canonical model |
| | saving with the catalyst term | 50.7 | 52.8 | −2.1 | |
| | EC / recycle / purge | 68.7 M€ / 20,588 / 420 | 66.1 / 22,581 / 456 | +4 % / −9 % / −8 % | |
| **B3 Pérez-Fortes 2016** (H2 3090, CO2 0, electricity 95.1, 55.1 t/h, 8 %, 20 y, CEPCI 2014, catalyst 95.24 €/kg every year) | H2 | 613.6 | 615.7 (95.9 % of VCP) | −0.3 % | model 0.1986 t/t vs 0.199 |
| | power + utilities | 20.2 | 16.7 | +3.5 | no turbine credit in the model |
| | catalyst | 9.6 | 9.6 | 0 | 44.5 t × 95.24 €/kg / 1 y in both |
| | capital | 38.1 | 57.6 | −19.4 | Reference = breakeven 723.6 minus cost 666.05. It includes the 3-year build and ramp-up. Model FCI is 151.8 M€ against TFCC 200 M€; the difference is Pérez-Fortes's 304-SS material factor 1.3 × location 1.043 (151.8 × 1.356 = 206). |
| | fixed O&M | 33.6 | 24.6 | +9.1 | |
| | **like-for-like total** | **706.1** | **723.6** | **−2.4 %** | |
| | anchor-convention total | 841.4 | 723.6 | +16 % | +126 €/t of residual direct + 10 % of NPC, common-mode |
| **B4 Szima 2018** (H2 = 53.4 kWh/kg × 60 €/MWh = 3204 €/t; CO2 credit 10 €/t; 8 %, 25 y; CEPCI 2017) | H2 / CO2 / catalyst | 619.1 / −14.1 / 33.5 | 616.9 / −14.1 / 33.5 | 0.4 % / 0 / 0 | |
| | capital | 66.6 | 56.6 | +10.0 | model FCI 65.0 vs TFCC 55.55 M€ |
| | **like-for-like total** | **852.7** | **842** (VOC + FOC + capital) | **+1.3 %** | |
| **B5 Nyári 2022** (H2 3000, CO2 50, electricity 40, 7.4 t/h, 7 %, 20 y; X and purge fitted) | Kiss / VD / Slotboom like-for-like | 803 / 840 / 794 | 823 / 885 / 801 | −2.4 / −5.1 / −0.9 % | |
| | **VD − Slotboom** (only the kinetics differ) | **46** | **84** | | The H2 term matches: model +27.6, reference +27.7. The reference adds electricity (474 vs 140 kWh/t), steam, cooling and capital for the larger recycle. The model reproduces 84 only with loop ΔP 4.2 bar and recycle-driven costs ×10 (variant `recycle_weight_nyari`). |
| **B6 Nieminen 2019** (H2 3000, CO2 50, electricity 60, 2.275 t/h, 5 %, 20 y; catalyst 95.24 €/kg, 4 y) | like-for-like | 922 | 1028 (no O2 credit) | −10 % | Nieminen loses 89 kg/h H2 and 560 kg/h CO2 in flash gases (carbon efficiency 0.805 against the model's 0.954). Separation losses are not in the model. |
| **B7 Schorn 2021** Table 2 grid | (H2 1, CO2 0) / (3, 40) / (4.5, 0) | 299 / 735 / 966 | 254 / 691 / 921 | +45 in every cell | Constant offset: the slopes agree (model H2 0.199 vs 0.189 t/t) and the gap is capital (model FCI 3.6× Schorn's 60 M€). |

**Specific fixed capital** (`capex_scale.csv`; model at each study's own point and cost year):

| Reference | Model / reference |
|---|---|
| Campos one-step | 1.00 |
| Campos three-step | 1.04 |
| Pérez-Fortes | 0.76 (1.03 after the SS × location factor 1.356) |
| Szima | 1.17 |
| Nieminen (17.9 M€) | 1.09 |
| Shunli (design + equipment) | 1.10 |
| Schorn | 3.6 |
| Bos | 6.2 |
| Hank | 3.6 |

## 4. Where the model agrees, where it does not, and the weight of each term

**Agrees.**
- **Feed.** H2 and CO2 per tonne match every TEA that buys H2 to within 1 %: Pérez-Fortes, Szima, Nyári, Campos once the
  N2 in the H2 stream is counted, and Schorn's slope. The term that carries the methane-loss penalty has the right size.
- **Loop.** Carbon efficiency, recycle ratio and compression power fall inside the reference spread.
- **Capital.** Within 0.76–1.17 of four rigorous TEAs, and 1.03 for Pérez-Fortes after its material factor.

**Disagrees, by term.**

1. **Catalyst replacement.** It is not proportional to inventory. The reference charges range from 6 €/kg/a (Campos:
   18.1 €/kg over 3 y) to 24 €/kg/a (95.24 €/kg over 4 y: Nieminen, Sollai) and 95 €/kg/a (Pérez-Fortes, replaced yearly).
2. **Loop pressure drop.** 1.5 bar in the model against 4.2 (PF), 4.6 (VD) and 4 bar (Zhang).
3. **Recycle-driven costs.** In Nyári's plant they rise much more steeply with recycle ratio than in the model. That
   plant's VD − Slotboom spread is 84 €/t; the model gives 46, and only the H2 part matches.
4. **Separation losses.** Nieminen loses about 15 % of the carbon in flash gases.
5. **Cost-accounting convention.** The anchor convention adds about 120–130 €/t of catalyst-independent cost compared
   with lean TEAs (PF, Szima).

**Weight of each term in the 33 mismatched groups** (`mismatch_driver_shares.csv`). The cost gap is the paper's STY
winner minus the plant-cost winner, both at their optimal purges:

| Basis | Median gap (€/t) | Feed (CH4 / purge loss) | Reactor-inventory capital | Catalyst replacement | Recycle compression (power) | Recycle-flow equipment | Groups where feed is the largest term |
|---|---:|---:|---:|---:|---:|---:|---:|
| canonical | 17.5 | +16.9 | −3.3 | 0 | +1.3 | +1.9 | 31 / 33 |
| catalyst 18.1 €/kg, 3 y | 15.2 | +16.9 | −3.3 | −2.0 | +1.3 | +1.9 | 31 / 33 |
| catalyst 3 y + ΔP 3.75 + recycle ×2.68 | 24.0 | +16.9 | −3.3 | −2.0 | +8.6 | +3.8 | 23 / 33 |
| primary weights: catalyst 95.24 €/kg 1 y + ΔP 4.2 + recycle ×10 | 15.3 | +16.9 | −3.3 | −32.3 | +36.3 | +8.9 | 7 / 33 (recycle compression largest in 26) |

The inventory terms favour the paper's STY winner. Recycle terms and feed losses favour the plant winner. With every
term at its primary-source upper value they roughly cancel in the median group, and the plant ranking is then set by
recycle compression rather than by feed.

## 5. Sensitivity: the headline rerun with primary-source values (`lit_sensitivity.py`, `sensitivity_summary.json`)

Setup: 991 candidates in 83 groups, recycled CO with the central RWGS rule, entry-optimal purge. 8 workers, 160 s.

| Variant (source of the value) | Groups with a different winner | Papers | Pairwise inversions | Median regret, mismatched | Flags changed | Cost winners changed |
|---|---|---:|---|---:|---:|---:|
| **baseline (frozen model)** | **33/83** | 19 | 1019/8458 | 2.0 % | 0 | 0 |
| loop ΔP 4.2 bar (PF stream table) | 33/83 | 19 | 1021/8458 | 2.3 % | 0 | 1 |
| loop ΔP 3.75 bar (Lurgi SRC) | 33/83 | 19 | 1022/8458 | 2.3 % | 0 | 1 |
| equipment split from the Campos SI Table S17 | 33/83 | 19 | 1019/8458 | 2.0 % | 0 | 0 |
| recycle flow ×2.68 (Lurgi pilot\*) | 33/83 | 19 | 1020/8458 | 2.5 % | 0 | 2 |
| **recycle costs ×10 + ΔP 4.2 (reproduces Nyári's spread)** | **34/83** | 20 | 1056/8458 | 5.1 % | 1 | 7 |
| PF prices (H2 3090, CO2 0, electricity 95.1) | 33/83 | 19 | 1006/8458 | 2.0 % | 0 | 0 |
| H2 price ½ | 32/83 | 19 | 949/8458 | 2.0 % | 1 | 4 |
| catalyst 18.1 €/kg, 3 y (Campos) | 32/83 | 18 | 920/8458 | 1.9 % | 1 | 6 |
| catalyst 18.1 €/kg, 5 y | 32/83 | 18 | 950/8458 | 2.0 % | 1 | 6 |
| **catalyst 95.24 €/kg, 6 y** (Dieterich lifetime) | **30/83** | 18 | 837/8458 | 1.3 % | 3 | 9 |
| **catalyst 95.24 €/kg, 4 y** (Nieminen, Sollai) | **27/83** | 17 | 782/8458 | 1.1 % | 6 | 13 |
| **catalyst 95.24 €/kg, 1 y** (PF yearly replacement) | **18/83** | 14 | 513/8458 | 1.0 % | 15 | 20 |
| catalyst 95.24/4 y + ΔP 4.2 + recycle ×10 | 33/83 | 19 | 905/8458 | 3.5 % | 0 | 7 |
| catalyst 95.24/1 y + ΔP 4.2 + recycle ×10 | 25/83 | 18 | 743/8458 | 2.6 % | 8 | 13 |
| catalyst 18.1/3 y + ΔP 3.75 | 33/83 | 19 | 928/8458 | 2.2 % | 0 | 5 |
| catalyst 18.1/3 y + ΔP 3.75 + recycle ×2.68 | 33/83 | 19 | 951/8458 | 2.8 % | 0 | 4 |
| catalyst 18.1/3 y + ΔP 3.75 + H2 ½ | 32/83 | 19 | 874/8458 | 1.5 % | 1 | 6 |

**What moves 33/83:**

- **Loop terms, prices and equipment split.** None of them does (32–34/83).
- **Catalyst replacement charged per tonne of inventory.** This does. The canonical model has none:
  - at a representative charge (95.24 €/kg over 4–6 y) the headline is 27–30/83 (33–36 %);
  - at Pérez-Fortes's yearly replacement it is 18/83 (22 %).
- **Combined primary loop weights.** Recycle costs scaled to Nyári's spread pull the other way: with the catalyst at
  95.24/4 y the headline is back to 33/83 (25/83 at 1 y).
- **Regret.** In every variant the median regret of the mismatched groups stays at 1.0–5.1 %.
- **Data file.** The groups whose winner changes are listed in `sensitivity_winner_changes.csv`.

## 6. Changes versus the first (secondary-value) pass

| Item | First pass | Now (primary) |
|---|---|---|
| Pérez-Fortes "724 €/t" | Read as a production cost (Dieterich Table 12). Model 913 against 724 (+26 %), at the anchor's selectivity and catalyst bed, 2 % purge, 10 %/20 y and EUR 2020. | It is the NPV = 0 breakeven selling price, 723.6 (AE Table 5). Production cost without capital is 666.05 (VCP 641.48 + FCP 24.57). Model at PF's own point, prices, catalyst and 8 % finance: **706 like-for-like (−2.4 %)**, 841 under the anchor convention (+16 %, all of it the 126 €/t common-mode convention). |
| Pérez-Fortes plant | 78 bar, X 0.22, CAPEX 181 k€/(t/d) (Dieterich) | 76 bar reactor feed (78 is the compression pressure); X 0.2197; TFCC 200 M€ + WC 20 M€; 44.5 t catalyst replaced yearly at 95.24 €/kg; loop ΔP 4.2 bar; H2 0.199 and CO2 1.460 t/t |
| Szima | 785.52 €/t (Mbatha) | 785.5 is VOC + FOC with no capital. With capital it is 842 (derived). Model like-for-like 853 (+1.3 %). |
| Campos cost split | Fig. 11b readings: H2 768, CO2 74, catalyst 15, power 11 M€/a | SI Table S19: 769.50, 74.93, 17.31, 12.66 M€/a. The 7 % H2 gap is now explained: N2 in the priced H2 stream. |
| Loop pressure drop | Dieterich licensor data only | PF 4.2, VD 4.6, Zhang 4 bar; the 4.2 bar variant gives 33/83 |
| Catalyst charge | 18.1 €/kg, 3 y (Campos) | Primary range 6–95 €/kg/a; this is the term that moves the headline (above) |
| Recycle weight | Lurgi pilot ×2.68 | Nyári's kinetic-model spread needs ×10; 34/83 |
| New Table B rows | — | Szima, Nyári ×3, Nieminen, Schorn |

## 7. Judgement calls

- **Pérez-Fortes model inputs.**
  - Reactor-inlet H2/CO2 is 3.8, derived from the stream-13 wt% (Table B.7).
  - The RWGS window is evaluated at the 288 °C outlet.
  - S_CO is 0.018, from "0.4 % of the CO2 to CO" at 21.97 % conversion.
  - The Pérez-Fortes capital term in Table B is the breakeven price minus the production cost, which includes the
    3-year construction and the ramp-up.
- **Szima.**
  - The H2 price is the electrolysis electricity only (53.4 kWh/kg × 60 €/MWh), because Szima's CAPEX excludes the
    electrolyser.
  - The catalyst bed is taken as 71.8 m³ × 0.98 × 1.05 t/m³ ≈ 74 t, with the lifetime set so the charge equals Szima's
    3.35 M€/a.
  - The reference total of 842 €/t is VOC + FOC plus CRF(8 %, 25 y) on TFCC + WC (derived).
- **Nyári.** Per-pass conversion and purge are fitted so the model loop has each kinetic model's recycle ratio and
  yield; the selectivity is the anchor's. The fixed cost of about 26 €/t is read off Fig. 6.
- **Nieminen.** The fixed cost (≈150), cooling water (43) and steam credit (−50) come from Fig. 5 / Fig. 6 and derived
  values. Hours are 7250 (implied by Fig. 5).
- **Schorn.** O&M = Table 2 intercept 63 €/t minus capital 14.1 minus power 15.0 = 33.9 €/t (derived). The model takes
  equilibrium per-pass conversion at 80 bar, 250 °C and the lowest grid purge, since the reference has none.
- **Model run at the reference points.**
  - It uses each study's reported catalyst inventory where one is given. Otherwise it uses the anchor's productivity
    (González-Garay, Schorn).
  - In Table A the cost row is at anchor prices with the case's scale.
- **Earlier choices still apply.** Recycle ratio = recycle / fresh make-up (molar). CEPCI annual averages as listed in §3.
  - The canonical Re states use `data/meoh/meoh_candidate_ranking_D01v3.csv`.
  - `meoh_d01_model.FROZEN["1wtRe_250C"]` lists S_CH4 = 0.03, S_CO = 0, whereas the ranking file and workbook have 0.01
    and 0.02. No published number depends on it, and the frozen file is not touched.

Downloaded full texts are kept outside the repository, in `D:\论文-AI4S\literature\meoh_plant_benchmark` (`manifest.csv`).
The only reference still missing is in `manual_download_dois.txt`.
