# Methanol plant model benchmarked against real plants and process TEAs — 2026-10-06

Question: does the CO2-to-methanol recycle-economics model that decides the headline result (paper STY leader ≠
plant-cost leader in 33 of 83 published comparison groups, `analysis/meoh_literature_inversion_2026_10_05/`) behave like
a real plant, and could any disagreement change that result?

**Answer.**
- The model's loop sits inside the industrial and pilot-plant ranges for pressure, temperature, H2/CO2, H2 and CO2
  consumption, carbon efficiency, compression electricity, recycle ratio (at conventional per-pass conversion) and
  catalyst space velocity.
- Out of sample, it reproduces the anchor TEA's three-step design:
  - +1.2 % on net production cost;
  - +0.2 % once the catalyst charge is costed per inventory;
  - +4 % on equipment cost.
- At the Pérez-Fortes (2016) scale it reproduces the fixed capital to −4 % (secondary values; primary pending).
- Three terms differ from practice:
  1. catalyst replacement is held constant instead of scaling with inventory;
  2. the loop pressure drop is 1.5 bar against 3–4 bar in industrial loops;
  3. at high per-pass conversion the model loop circulates less gas than the Lurgi CO2 pilot.
- Setting each of these to the reference value, alone or together, gives **32–33 of 83** groups with a different winner
  (headline 33/83) and 18–19 of 44 papers.
- The disagreements do not change the ranking result. Methane and purge losses (H2 + CO2) are the largest cost-gap term
  in 31 of the 33 mismatched groups, as they are the dominant cost in every reference TEA.

Scripts (interpreter `D:\Research\CatalystForge\.venv\Scripts\python.exe`, `PYTHONIOENCODING=utf-8`):

```
python analysis/meoh_plant_benchmark_2026_10_06/lit_sensitivity.py   # 10 variants of the 33/83 rerun, ~2.5 min on 10 cores
python analysis/meoh_plant_benchmark_2026_10_06/run_benchmark.py     # Tables A and B, CAPEX scale, driver decomposition
```

The frozen models (`data/meoh/meoh_d01_model.py`, `data/meoh/meoh_general_model.py`) are not modified.
`plant_variant.py` restates `meoh_general_model.economics` with the prices, scale, finance, loop pressure drop, catalyst
replacement and recycle flow exposed as keywords. At default keywords it equals the frozen model to 1.8e-12 EUR/t on 300
random states; `run_benchmark.py` asserts this. `lit_sensitivity.py` reproduces the frozen headline exactly before running
any variant: 33/83 groups, 1019/8458 inversions, costs to 4.9e-6 relative (the CSV's 6-significant-digit STY).

## 1. Sources

Every number with its locator, conversion and kind is in `reference_values.csv`. The `kind` column takes four values:

- `source_fact`: printed in the source;
- `derived`: arithmetic on printed numbers, shown in the row;
- `figure_reading`: measured on a rendered figure;
- `secondary`: a value tabulated by a review.

| ID | Source | Role | Obtained |
|---|---|---|---|
| CAMPOS22 | Lacerda de Oliveira Campos et al., *Processes* 10, 1535 (2022), doi 10.3390/pr10081535 | model anchor, one-step loop; **calibration point, not independent** | full text (KIT repository); SI blocked |
| CAMPOS22_3S | same paper, three-step loop with intermediate condensation | **out-of-sample design** on the same price basis | full text |
| DIETERICH20 | Dieterich et al., *Energy Environ. Sci.* 13, 3207 (2020), doi 10.1039/d0ee01187h | industrial loops: Table 8 licensor data; CO2 pilots: Table 11 (Lurgi, Mitsui, CRI); TEA compilation: Table 12 | full text |
| OTT12 | Ott et al., *Methanol*, Ullmann's (2012), doi 10.1002/14356007.a16_465.pub3 | low-pressure loops, catalyst lifetime | full text |
| HANSEN08 | Hansen & Højlund Nielsen, *Handbook of Heterogeneous Catalysis* (2008), doi 10.1002/9783527610044.hetcat0148 | recycle ratio, productivity | full text |
| GONZALEZ19 | González-Garay et al., *Energy Environ. Sci.* 12, 3425 (2019), doi 10.1039/c9ee01673b | Aspen CO2 loop, cost shares | full text; ESI (prices) not obtained |
| HANK18 | Hank et al., *Sustainable Energy Fuels* 2, 1244 (2018), doi 10.1039/c8se00032h | small PEM-coupled plants | full text |
| BOS20 | Bos, Kersten, Brilman, *Appl. Energy* 264, 114672 (2020), doi 10.1016/j.apenergy.2020.114672 | once-through condensing reactor | accepted version (U. Twente) |
| RIHKO10 | Rihko-Struckmann et al., *Ind. Eng. Chem. Res.* 49, 11073 (2010), doi 10.1021/ie100508w | Aspen loop, recycle ratio | full text |
| MARLIN18 | Marlin et al., *Front. Chem.* 6, 446 (2018), doi 10.3389/fchem.2018.00446 | CRI process description (few numbers) | full text |
| CRI_OLAH, CRI_SHUNLI | carbonrecycling.com project pages (George Olah; Shunli) and Dieterich 2020 p. 3221 | operating plants: capacity, CO2 use, investment | web pages, 2026-10-06 |
| PEREZFORTES16, SZIMA18 | Pérez-Fortes et al. 2016 (manuscript ref. 14) and Szima & Cormos 2018 **as tabulated by** Dieterich 2020 Table 12 and Mbatha et al., *Sustainable Energy Fuels* 5, 3490 (2021), Tables 1 and 15 | rigorous CO2 TEAs | **secondary only**; primaries are Elsevier (manual download) |

Mbatha 2021 Table 15 prints two Pérez-Fortes cells whose meaning is unclear: 295 M€/yr and 496.5 €/t per year. They are
not used. The 724 €/t production price and the 181 k€/(t/d) CAPEX come from Dieterich Table 12, which lists them under
named columns.

## 2. Table A — plant metrics (`reconciliation_plant.csv`)

Model columns:
- **M1**: anchor inputs (calibration).
- **M2**: three-step inputs (out of sample).
- **M3**: canonical economic optimum, 5 wt% Re at 200 °C, 2 % purge, inert CO (943.30 €/t).
- **M4**: canonical optimum at its own purge, 1 wt% Re at 200 °C, 0.5 % purge (895.25 €/t).
- **M5–M7**: the model at the reference studies' own operating points:
  - M5, Lurgi CO2 pilot: X 0.40, purge set so carbon efficiency is 95.25 %, catalyst from GHSV 10,500 h⁻¹;
  - M6, González-Garay: X 0.141, carbon efficiency 91.5 %;
  - M7, Pérez-Fortes: 78 bar, X 0.22, 2 % purge.

Plant-size flows are at 145 t/h. GHSV and STY use the anchor's bed density of 1.05 t/m³. "*" marks secondary values.

| Metric | M1 | M2 | M3 | M4 | M5 | M6 | M7 | References |
|---|---|---|---|---|---|---|---|---|
| Loop P (bar) | 70 | 70 | 100 | 100 | 80 | 50 | 78 | LP loops 50–100 (Ott, Dieterich); Lurgi CO2 pilot 80; Mitsui 50; CRI Olah 101; G-G 50; Hank 40; Bos 50; Rihko 50 |
| T (°C) | 247.5 | 258.5 | 200 | 200 | 250 | 224.5 | 210 | 200–300; Lurgi pilot and CRI Olah 250; G-G 221–228; Rihko 220 |
| Fresh H2/CO2 | 2.99 | 3.00 | 3.09 | 3.01 | 3.00 | 2.98 | 2.99 | Campos 3.0; Rihko 3.0; G-G slightly <3 |
| Per-pass CO2 conversion | 0.285 | 0.539 | 0.33 | 0.19 | 0.40 | 0.141 | 0.22 | Campos 0.285 / 0.539; Lurgi CO2 pilot 0.35–0.45; SRC 0.36; G-G 0.124–0.158; Pérez-Fortes* 0.22; Szima* 0.30 |
| Recycle ratio (mol recycle / mol fresh) | 2.84 | 1.12 | 3.40 | 7.33 | **1.68** | 6.63 | 3.83 | Campos 2.81 / 1.21; conventional 3–5 (Dieterich, Hansen); Lurgi SRC 3–4; MegaMethanol 2–2.7; **Lurgi CO2 pilot 4.5**; Mitsui 2.6–3.2; Rihko 3.2 |
| Purge (fraction of separator gas) | 0.02 | 0.02 | 0.02 | 0.005 | 0.031 | 0.013 | 0.02 | Campos 0.02; Mitsui 7–10 % of reactor inlet; LPMeOH 2–6 % of recycle |
| Purge flow (kmol/h) | 1105 | 420 | 1377 | 689 | 1031 | 1780 | 1520 | Campos 1100 / 455 |
| H2 (t/t MeOH) | 0.199 | 0.192 | 0.208 | 0.195 | 0.198 | 0.205 | 0.202 | stoich. 0.189; Campos 0.200 (Table 6) / 0.193; Hank 0.189–0.193; Rihko 0.197 |
| CO2 (t/t MeOH) | 1.449 | 1.398 | 1.473 | 1.417 | 1.442 | 1.501 | 1.477 | stoich. 1.374; Campos 1.457 / 1.406; CRI Olah 1.375–1.40; CRI Shunli 1.455; Hank 1.511–1.526; Rihko 1.436; Bos 1.385 |
| Carbon efficiency | 0.948 | 0.983 | 0.932 | 0.969 | 0.953 | 0.915 | 0.930 | Campos 0.943 / 0.977; conventional 0.93–0.98; Lurgi CO2 pilot 0.940–0.965; Rihko 0.968; G-G >0.915; Hank 0.90 |
| Compression electricity (MWh/t) | 0.199 | 0.188 | 0.246 | 0.240 | 0.210 | 0.183 | 0.217 | Campos whole plant 0.327 gross / 0.121 net; Bos feed compressors 0.22; Rihko 1.33 (97 kg/h, feed from 1 bar) |
| Catalyst inventory (t) | 2869 | 1434 | 161 | 264 | 118 | 2869 | 2869 | Campos 2869 / 1434 |
| GHSV (h⁻¹) | **617** | 671 | 13,050 | 14,080 | 10,500 | 1,250 | 787 | SRC 6,000–12,000; Lurgi CO2 pilot 10,500; Mitsui 10,000; Campos (derived) 604 |
| STY (kg/L/h) | 0.053 | 0.106 | 0.95 | 0.58 | 1.29 | 0.053 | 0.053 | CO2 feed 0.4–0.8; syngas 0.7–2.3 (Dieterich) |
| Catalyst lifetime | 3 y, in the constant residual | | | | | | | Campos 3 y; Ott 2–5 y; Dieterich 4–6 y (up to 8) |
| Loop ΔP (bar) | **1.5** | | | | | | | Lurgi SRC loop 3.5–4; Toyo loop 3 (Dieterich Table 8) |
| NPC (€/t, anchor prices) | 923.64 | 881.25 | 943.30 | 895.25 | 894.81 | 948.78 | 944.40 | Campos 920 (Table 7: 924.0) / 868 (871.2) |

M6 and M7 inherit the anchor's low-STY CZA bed (2869 t), so their GHSV is the anchor's, not the reference's.

## 3. Table B — cost (`reconciliation_cost.csv`, `capex_scale.csv`)

Currency and year: the model is in EUR at CEPCI 2020, the anchor's basis (USD equipment converted at 1.13 USD/EUR,
Campos p. 11).
- **Campos rows:** same basis, so no conversion.
- **Pérez-Fortes:** the secondary sources do not state the cost year. Model capital is left in EUR 2020; restating it
  to 2014 with CEPCI 576.1/596.2 would lower ACC by 3 % (−2 €/t).
- **Shunli:** USD 2022 converted at the 2022 ECB average of 1.053 USD/EUR.

| Case | Term | Model | Reference | Deviation | Attribution |
|---|---|---:|---:|---:|---|
| **B1 Campos one-step** (calibration) | H2 | 615.0 | 662.1 (Fig. 11b, ±3) | −47 (−7 %) | Model uses 0.1985 t H2/t. The Fig. 11b bar implies 0.214 t/t, but the paper's own feed excess (Table 6) gives 0.200 t/t (model −0.8 %). The gap sits in the constant residual. |
| | CO2 | 64.2 | 63.8 | +0.4 | 1.449 vs 1.457 t/t |
| | electricity | 17.9 | 9.5 (net, after the Rankine credit) | +8.4 | Model counts compressors only (28.9 MW) and no Rankine credit |
| | catalyst replacement | 0 (inside residual) | 12.9 (bar); 14.9 from inputs | — | not catalyst-dependent in the model |
| | ACC | 46.0 | 46.1 | −0.1 | |
| | indirect OPEX | 123.6 | 123.6 | −0.1 | |
| | **total** | **923.6** | **924.0** (920 in text) | **−0.03 %** | calibration identity |
| **B2 Campos three-step** (out of sample) | EC (M€) | 68.7 | 66.1 | +4.0 % | model topology lacks the intermediate condensers and flash drums |
| | ACC | 37.0 | 35.6 | +4.0 % | |
| | direct OPEX | 730.6 | 723.8 | +0.9 % | |
| | **total** | **881.3** | **871.2** (868 in text) | **+1.2 %** | |
| | saving vs one-step | 42.4 | 52.8 | −10.4 | catalyst halved (2869 → 1434 t), worth 7.5 €/t in the reference, constant in the model |
| | same, with catalyst term (18.1 €/kg, 3 y) | 50.7 | 52.8 | −2.1 | |
| | total, with catalyst term | 873.0 | 871.2 | **+0.2 %** | |
| | recycle / purge (kmol/h) | 20,588 / 420 | 22,581 / 455 | −9 % / −8 % | |
| **B3 Pérez-Fortes\*** (H2 3090 €/t, CO2 0, electricity 95.1 €/MWh, 440 kt/a, 78 bar, X 0.22) | FCI (M€) | 236.4 | 235.3 (181 k€ per t/d × 1300 t/d) | **+0.4 %** | |
| | H2 | 625.7 | — | | |
| | ACC + electricity | 89.7 | 98.3 (= 724 − H2) | −8.6 | like for like |
| | residual direct + indirect OPEX | 197.5 | ≈ 0 | | Anchor (Peters/Albrecht) convention: 57.0 residual direct, 49.3 labour and 0.081·FCI, 91.3 for the 10 % of NPC. Catalyst-independent, so common-mode. |
| | **total** | **912.9** | **724** | **+26 %** | the whole gap is the cost-accounting boundary, not plant behaviour |

Specific fixed capital of the model at each reference scale (`capex_scale.csv`; the model operates at the anchor point
and is scaled with its own exponents):

| Reference | Capacity (t/a) | Model FCI (€/(t/a)) | Reference (€/(t/a)) | Model / reference |
|---|---:|---:|---:|---:|
| Campos one-step | 1,160,000 | 358 | 359 | 1.00 |
| Pérez-Fortes\* (CO2 and H2 supplied externally) | 440,000 | 512 | 535 | 0.96 |
| CRI Shunli (design + equipment only, EUR 2022) | 110,000 | 857 | 777 | 1.10 |
| Bos 2020 methanol section (condensing reactor, Lang 5) | 65,000 | 1,043 | 169 | 6.2 |
| Hank 2018 (assumed 810 €/(t/a)) | 4,188 | 2,908 | 810 | 3.6 |

**Cost shares.** At the anchor:
- feed (H2 + CO2) is 73.5 % of model NPC (H2 66.6 %, CO2 6.9 %), against reactants 78–80 % in Campos and 78.6 % on the
  Fig. 11b bars;
- the reference ranges are H2 51.6–89.4 % and CO2 3.2–26.7 % (González-Garay), and H2 ≈ 83 % (Schemme, via Dieterich);
- ACC is 5.0 % of NPC, against 4–5 % in Campos;
- electricity is 1.9 %, against catalyst + electricity < 3 % in Campos.

## 4. Where the model agrees and where it does not

**Agrees, within the spread of the references:**

| Item | Model | References |
|---|---|---|
| Loop pressure and temperature | inside | 50–100 bar, 200–300 °C |
| H2 consumption | 0.195–0.208 t/t | 0.189–0.214 |
| CO2 consumption | 1.40–1.50 t/t | 1.375–1.526; operating plants: Olah 1.375–1.40, Shunli 1.455 |
| Carbon efficiency | 0.915–0.983 | 0.90–0.98 |
| Compression electricity | 0.18–0.25 MWh/t | Bos 0.22; Campos gross whole plant 0.33 |
| Recycle ratio at per-pass conversion 0.22–0.33 | 2.8–3.8 | conventional 3–5; Mitsui 2.6–3.2; Rihko 3.2 |

- **Catalyst space velocity.** For catalysts sized from measured STY (the Re states, and the literature candidates),
  GHSV is 10,000–14,000 h⁻¹ and STY 0.6–1.3 kg/L/h. References: 6,000–12,000 h⁻¹ and 0.4–0.8 kg/L/h (CO2 feed).
- **Cost structure.** The model has the references' cost structure: feed dominant (73.5 % vs 78–80 %), capital 4–5 %,
  and power and catalyst a few percent.
- **Out-of-sample and capital checks:**
  - the three-step design is reproduced to +1.2 % on cost (+0.2 % with the catalyst term) and +4 % on equipment;
  - fixed capital at 440 kt/a is reproduced to −4 % to +0.4 % (Pérez-Fortes, secondary);
  - Shunli is +10 %, against a design + equipment figure, which is a narrower scope than FCI.

**Disagrees:**

1. **Catalyst replacement is not proportional to inventory.** The anchor charges the catalyst every 3 years (18.1 €/kg,
   12.9–14.9 €/t). The model keeps that charge in a constant residual. This is why the model under-predicts the
   three-step saving by 10.4 €/t (20 %); adding the term closes the gap to 2.1 €/t.
2. **Loop pressure drop.** The model uses 1.5 bar. Industrial loops run at 3–4 bar (Lurgi SRC loop 3.5–4, Toyo loop 3).
   The model's recycle-compression power is therefore 2.5× too low; at the anchor point this is 1.0 → 2.6 MW, about
   1 €/t.
3. **Recycle at high per-pass conversion.** At the Lurgi CO2 pilot's 35–45 % per pass and 95 % carbon efficiency, the
   model loop recirculates 1.7 mol per mol of fresh feed, against 4.5 reported. The pilot gas carries inerts that the
   model's pure H2/CO2 make-up does not.
4. **Anchor bed size.** The anchor's own CZA bed is about 10× industrial size (GHSV 604–617 h⁻¹ against 6,000–12,000).
   This affects only the anchor point. Catalysts in the model are sized from their measured STY.
5. **Cost-accounting convention.** The anchor's Peters/Albrecht convention carries 57 €/t of catalyst-independent
   direct OPEX and 10 % of NPC for distribution, selling and R&D. A lean TEA (Pérez-Fortes) gives 724 against the model's
   913 €/t at the same prices. The difference is common to every catalyst and multiplies all catalyst-dependent terms by
   the same 1/0.9.
6. **Scale.** At 4–65 kt/a the model's six-tenths scaling gives 3–6× the specific capital assumed by Hank and Bos. This
   does not enter the ranking, because every candidate is costed at 145 t/h.

**Relative weight of the terms that decide the ranking** (`mismatch_driver_decomposition.csv`,
`mismatch_driver_shares.csv`). For each of the 33 mismatched groups, the cost gap is split into terms: the paper's STY
winner minus the plant-cost winner, at their optimal purges.

| Basis | Median gap (€/t) | Median feed (CH4 / purge loss) term | Median reactor-inventory capital | Median recycle compression (power) | Median recycle-flow equipment | Groups where feed is the largest term |
|---|---:|---:|---:|---:|---:|---:|
| Canonical model | 17.5 | +16.9 | −3.3 | +1.3 | +1.9 | 31 / 33 |
| + catalyst replacement (18.1 €/kg, 3 y) | 15.2 | +16.9 | −3.3, plus −2.0 replacement | +1.3 | +1.9 | 31 / 33 |
| + loop ΔP 3.75 bar + recycle ×2.68 | 24.0 | +16.9 | −3.3, plus −2.0 replacement | +8.6 | +3.8 | 23 / 33 (recycle compression in the other 10) |

- **Inventory term.** The paper's STY winner always has the smaller catalyst inventory, so the inventory term favours it.
  Charging the reference catalyst replacement narrows the gap but does not close it.
- **Industrial-loop recycle costs.** Raising recycle costs to industrial-loop levels widens the gap.
- **Sign of the gap.** In both cases the sign is set by the methane and purge losses. This is the feed share that
  dominates every reference TEA.

## 5. Sensitivity: the headline rerun with reference values (`lit_sensitivity.py`, `sensitivity_summary.json`)

All 991 candidates and 83 groups are rerun with the primary plant treatment (recycled CO, central RWGS rule,
entry-optimal purge) and the term set to the reference value.

| Variant (reference value) | Groups with a different winner | Papers | Pairwise inversions | Median regret, mismatched | Groups whose mismatch flag changes | Groups whose cost winner changes |
|---|---|---:|---|---:|---:|---:|
| **baseline (frozen model)** | **33/83** | 19 | 1019/8458 | 2.0 % | 0 | 0 |
| catalyst replacement 18.1 €/kg, 3 y (Campos Table 2, §2.7) | 32/83 | 18 | 920/8458 | 1.9 % | 1 | 6 |
| catalyst replacement 18.1 €/kg, 5 y (Dieterich 4–6 y) | 32/83 | 18 | 950/8458 | 2.0 % | 1 | 6 |
| loop ΔP 3.75 bar (Lurgi SRC loop 3.5–4 bar) | 33/83 | 19 | 1022/8458 | 2.3 % | 0 | 1 |
| recycle flow ×2.68 (Lurgi CO2 pilot 4.5 vs model 1.68) | 33/83 | 19 | 1020/8458 | 2.5 % | 0 | 2 |
| H2 price ½ (1548.7 €/t; H2 share at the low end of the references) | 32/83 | 19 | 949/8458 | 2.0 % | 1 | 4 |
| Pérez-Fortes prices (H2 3090, CO2 0, electricity 95.1)\* | 33/83 | 19 | 1006/8458 | 2.0 % | 0 | 0 |
| catalyst 3 y + ΔP 3.75 bar | 33/83 | 19 | 928/8458 | 2.2 % | 0 | 5 |
| catalyst 3 y + ΔP 3.75 bar + recycle ×2.68 | 33/83 | 19 | 951/8458 | 2.8 % | 0 | 4 |
| catalyst 3 y + ΔP 3.75 bar + H2 ½ | 32/83 | 19 | 874/8458 | 1.5 % | 1 | 6 |

- **Headline result.** It stands at 32–33/83 (39–40 %) in every variant.
- **Where winners change.** The groups whose cost winner changes are mostly the Bansode 2013 (10.1039/c2cy20604h) Cu/Al2O3 series
  (`sensitivity_winner_changes.csv`), where both candidates are low-conversion points. In every case but one the new
  winner is still not the STY leader.
- **The flag that moves.** The single mismatch flag that moves is CZ/CNTs-3 at 260 vs 280 °C (RSC Adv. 2015,
  10.1039/c5ra04774a) under the catalyst term. Under H2 at half price it is 13 % ZnO–ZrO2 (Wang 2017, 10.1126/sciadv.1701290).

## 6. Judgement calls

- **Recycle ratio definition.** Recycle ratio = recycle / fresh make-up (molar), as in Dieterich Tables 8 and 11.
  - Rihko-Struckmann's 4.2 is reactor inlet / fresh, so recycle / fresh = 3.2.
  - Campos's ratios are derived from Table 6 recycle flows and the Section 2.4 feed (minimum feed × (1 + excess)).
- **Campos H2 and CO2 consumption.** Taken from the stated feed excess on a pure-component basis. The Fig. 11b H2 bar
  (≈768 M€/a) implies 0.214 t/t. Both are listed.
- **Figure readings.** Fig. 11b bars were measured on a 3× render of p. 19:
  - axis 0–100 at 1.506 px per M€;
  - break segment 700–800 at 1.542 px per M€;
  - uncertainty ±2–3 M€/a.
- **Model at reference operating points.** These rows use the anchor's selectivity (99.5 % MeOH, 0.5 % CO), recycled
  CO (central rule) and H2/CO2 = 3 at the reactor inlet. The purge is matched to the reference carbon efficiency where
  one is given (Lurgi pilot 95.25 %, mid of 94.0–96.5; González-Garay 91.5 %). Otherwise it is 2 %. The Lurgi-pilot
  catalyst mass is set from its GHSV of 10,500 h⁻¹.
- **Canonical inputs.** The canonical Re states use the inputs of `data/meoh/meoh_candidate_ranking_D01v3.csv`.
  - `meoh_d01_model.FROZEN["1wtRe_250C"]` lists S_CH4 = 0.03, S_CO = 0, whereas the ranking file and workbook have
    0.01 and 0.02.
  - Only its STY and Re wt% are read elsewhere (`meoh_measurement_mc.py`), so no published number is affected. The dict
    entry should be corrected in a separate change; the frozen file was not touched here.
- **Catalyst replacement term.** It replaces the anchor's own replacement charge (17.31 M€/a) in the residual, so the
  anchor point is unchanged.
- **Recycle ×2.68.** It enlarges the recycle used for compression and for gas-flow-sized equipment only. Species balance,
  purge and feed are unchanged. It is a cost-term stress, not a new loop model.
- **Pérez-Fortes and Szima.** Used only through the two reviews' tables, and marked secondary throughout. Szima's
  785.52 €/t includes electrolysis, so it was not mapped to an H2 price and is not in Table B.

## 7. Pending

`manual_download_dois.txt` lists the full texts nus-fetch could not retrieve. Elsevier is behind a bot check off the NUS
network, and MDPI refused the automated browser. **Pérez-Fortes 2016** (manuscript ref. 14) is the indispensable one: its
stream table, price year and cost breakdown would turn the B3 row from secondary into primary. Van-Dal 2013, Szima 2018,
Nyári 2020, Sollai 2023 and Battaglia 2021 would add independent rows. The Campos SI (Section H) would replace the
Fig. 11b readings.

Downloaded PDFs are kept outside the repository in `D:\论文-AI4S\literature\meoh_plant_benchmark` (with `manifest.csv`).
