# Composition-based catalyst cost in the methanol plant leaderboard — 2026-10-06

Builds on `analysis/meoh_plant_benchmark_2026_10_06/` (PR #26). There, the catalyst replacement charge was the one
plant term that moved the headline. The headline is that, within published CO2-to-methanol comparisons, the paper's
space-time-yield (STY) leader is not the plant-cost leader in 33 of 83 groups. That benchmark charged replacement at
one uniform price for every catalyst, but the candidates include Cu/ZnO, In2O3, Pd, Ir, Au, Re, Ga and Ni catalysts.
Here every candidate gets a price from its own extracted composition, and replacement is charged per tonne of
inventory.

**Answer**

- **Primary:** composition price, 3-year life (the anchor's). **31/83 groups (37 %)** have a different winner, in
  18/44 papers.
  - Paper-cluster bootstrap 95 % CI (10,000 resamples of the 44 papers): **22–53 %, i.e. 18–44 of 83**.
  - With the catalyst term off, the CI is 24–55 %.
- **Effect of the composition price.** It changes the plant winner in 14 groups and the verdict in 8:
  - 5 groups go from mismatch to match, and 3 go from match to mismatch;
  - the median regret of the mismatched groups rises from 2.0 % to 3.1 %.
  - Expensive leaders are pushed out: 10 wt% Ir/In2O3, Pd-rich and Ga-rich catalysts, and the Ir–Pd dual-atom
    In2O3 series.
- **Life and price variants.**
  - At the 18.1 €/kg anchor base cost, every life from 1 to 6 years gives **31–33/83**.
  - With the Pérez-Fortes 95.24 €/kg base cost the headline is **24/83 (3 y) and 21/83 (1 y)**. This is the same
    level as the uniform 95.24 €/kg price (24/83 at 3 y). At that base cost the manufacturing charge alone exceeds the
    metal value of most catalysts.
- **Self-check.** The 21 Gothe et al. 2025 Table 4 Re/TiO2 entries reproduce the frozen costs to 2.3e-13 €/t with the
  term off.
  - With the term on, Re/TiO2 costs 65.2 €/kg (1 wt% Re) and 268.9 €/kg (5 wt% Re).
  - The canonical leader, 5 wt% Re at 200 °C, rises from 943.30 to 957.14 €/t and stays the cheapest of the four
    canonical states (table in §5).

```
python analysis/meoh_catalyst_cost_2026_10_06/run_catalyst_cost_inversion.py   # ~5 min on 4 workers (CATCOST_WORKERS)
python analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py               # prices only, a few seconds
```

Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe`, with `PYTHONIOENCODING=utf-8`.

The script does not edit `data/meoh/meoh_general_model.py`, `meoh_d01_model.py` or
`run_literature_inversion.py`. The rerun copies the inversion logic (candidate construction, group STY basis,
`group_metrics`, `aggregate`) and calls the frozen `meoh_general_model.economics(..., cat_price_eur_kg=, cat_life_y=)`.

The plant treatment is recycled CO with the central RWGS rule and entry-optimal purge on the canonical 0.5–40 % grid.
Before any variant, the script asserts two things:
- the rebuilt 991 candidates equal the frozen `literature_candidates.csv`;
- the term-off run reproduces **33/83 and 1019/8458**. Costs agree to 4.9e-6 relative; that difference is the
  6-significant-figure rounding of the frozen CSV.

## 1. Result

Same metrics as the inversion README. "Flipped" counts the groups whose verdict (same or different winner) differs
from the term-off run. "Winner changed" counts the groups whose plant-cost winner differs from that run.

| Variant | Groups with a different winner | Papers | Regret, median of mismatched / max | Pairwise inversions | Flipped | Winner changed |
|---|---|---:|---|---|---:|---:|
| catalyst term off (frozen headline) | 33/83 | 19/44 | 2.0 % / 182 % | 1019/8458 | 0 | 0 |
| **composition price, 3 y (primary)** | **31/83** | **18/44** | **3.1 % / 157 %** | **1128/8458** | 8 | 14 |
| composition price, 1 y (Pérez-Fortes) | 31/83 | 18/44 | 1.9 % / 374 % | 1220/8458 | 12 | 18 |
| composition price, 4 y (Nieminen, Sollai) | 32/83 | 18/44 | 3.2 % / 159 % | 1111/8458 | 7 | 13 |
| composition price, 6 y (Dieterich upper) | 33/83 | 19/44 | 3.3 % / 162 % | 1077/8458 | 6 | 11 |
| composition price, 3 y, 95 % precious-metal recovery | 30/83 | 17/44 | 2.7 % / 157 % | 840/8458 | 7 | 12 |
| composition price, Pérez-Fortes base, 3 y | 24/83 | 16/44 | 1.9 % / 128 % | 969/8458 | 15 | 21 |
| composition price, Pérez-Fortes base, 1 y | 21/83 | 16/44 | 3.7 % / 361 % | 901/8458 | 20 | 26 |
| uniform 18.1 €/kg, 3 y (benchmark variant) | 32/83 | 18/44 | 1.9 % / 154 % | 920/8458 | 1 | 6 |
| uniform 95.24 €/kg, 3 y | 24/83 | 16/44 | 1.0 % / 111 % | 736/8458 | 9 | 15 |

**Bootstrap** (`summary.json` → `bootstrap`, seed 20261006). Papers are resampled with replacement and every group of
a drawn paper enters.

| Run | Fraction of groups | 95 % CI | Of 83 |
|---|---|---|---|
| primary | 0.373 | 0.218–0.527 | 18.1–43.7 |
| term off | 0.398 | 0.237–0.551 | 19.7–45.7 |

**Recovery variant.** It credits 95 % of the precious-metal value (Pd, Pt, Ir, Au, Ag, Re, Ru, Rh, Os) at the end of
life. The group count barely moves (30/83), but pairwise inversions fall from 1128 to 840. Recovery mainly reorders the
non-leading Pd/Ir/Au entries inside each group.

**Base cost.** The 18.1 €/kg anchor base cost and the 95.24 €/kg Pérez-Fortes value bracket the headline: 31/83 against
24/83. At 95.24 €/kg every catalyst carries at least 88.6 €/kg of manufacturing cost. Inventory then counts for more
than composition, and the result converges on the uniform-price run.

## 2. Which groups change and why (`group_changes.csv`)

There are 14 groups whose plant winner or verdict changes under the primary.
- **5 changes driven by price.** A leader with costly metal loses to a cheaper catalyst, or a costly plant winner
  loses to the STY leader.
- **3 driven by inventory alone.** The candidates share a price, and the higher-STY entry needs less catalyst.
- **6 where only the identity of the plant winner changes.** The verdict stays the same: four Cu/Al2O3 groups of
  10.1039/c2cy20604h, one Ir–Pd/In2O3 group and one In2O3-polymorph group.

Costs are €/t MeOH. "Term off" is the catalyst term off; "primary" adds the composition price at 3 y.

1. **Ir/In2O3 (10.1021/acscatal.0c05628), 50 bar, H2/CO2 4: match → mismatch.**
   - The STY leader is 10 wt% Ir/In2O3: STY 0.755 g/g/h, 192 t of catalyst, priced at **22,590 €/kg**.
   - Its replacement charge is 1,247 €/t, and its cost rises from 883 to 2,269.
   - Pristine In2O3 at 282 €/kg wins at 984 €/t, even though it needs 2.3× the inventory (445 t).
   - Regret 131 %.
2. **PdMgGa vs PdZnAl (10.1016/j.jcat.2012.05.020), 30 bar: match → mismatch.**
   - The STY leader PdMgGa is 40.5 wt% Ga at 580 USD/kg, priced at **871 €/kg**.
   - PdZnAl (Zn/Al oxide, 1.46 wt% Pd) is priced at 539 €/kg and becomes the plant winner: 3,853 against 4,284 €/t.
   - Regret 11 %.
3. **Pd on ZnTiO3 vs physical mixture (10.1002/cctc.202000974), 20 bar: mismatch → match.**
   - With the term off, PdZn/ZnTiO3 (5 wt% Pd, **1,813 €/kg**) beat the STY leader by 8 €/t.
   - The STY leader is the Pd/ZnO + TiO2 mixture: half the Pd, 914 €/kg, flag `assumed`.
   - With the term on, the leader is cheaper by 1,512 €/t, because both need about 5,000 t of catalyst.
4. **In2O3–ZrO2 (10.1021/acscatal.9b03305), 50 bar: mismatch → match.**
   - With the term off, 50In2O3–50ZrO2 (45 wt% In, **166 €/kg**) was 6.6 €/t cheaper than the STY leader.
   - The STY leader is 5 wt% In2O3/m-ZrO2 at 38 €/kg.
   - The indium charge reverses this: 1,072 against 1,088 €/t.
5. **Ir–Pd dual-atom In2O3, 10.1002/anie.202401168, 30 bar: still a mismatch, regret 0.4 % → 10.9 %.**
   - The STY leader is Ir1Pd1-In2O3 (0.44 wt% Ir + 0.25 wt% Pd), priced at **1,353 €/kg**.
   - The plant winner moves from another Ir1Pd1 point to Pd1Pd1-In2O3 (0.50 wt% Pd, 461 €/kg): 972 against
     1,078 €/t.

Three groups flip on inventory alone, because their candidates share one price:
- Ca-promoted Pd–Zn/CeO2, 10.1016/j.fuel.2023.127927, 2,928 €/kg;
- 13 % ZnO–ZrO2, 10.1126/sciadv.1701290;
- Cu–ZrO2/CNT, 10.1039/c5ra04774a.

The same direction appears with a uniform price. Composition only sets how large the charge is.

## 3. Price model (`catalyst_prices.py`)

price (€/kg) = Σ_i w_i × p_i + base

- **w_i.** Mass fraction of element i in the catalyst, metal basis. O, C, H and N carry no price.
- **base.** Calibrated so that commercial Cu/ZnO/Al2O3 equals the anchor's 18.1 €/kg.
  - The calibration composition is CuO/ZnO/Al2O3 = 60/30/10 wt%, which is Cu 47.93, Zn 24.10 and Al 5.29 wt%.
  - Its metal value is 6.64 €/kg, so **base = 11.456 €/kg**.
  - Pérez-Fortes variant: base = 95.24 − 6.64 = 88.596 €/kg.
- **USD → EUR.** ECB reference rate, 2025 annual average: **1.12998 USD/EUR** (series EXR.A.USD.EUR.SP00.A).

**Element prices** (`element_prices.csv`).

*Frozen.* These are the frozen NH3-model price set (`harness_core.PRICE`). The script reads it back from the harness
and asserts equality.

| Element | USD/kg | €/kg |
|---|---:|---:|
| Cu | 13.89 | 12.29 |
| Pd | 40,671 | 35,992 |
| Pt | 51,509 | 45,584 |
| Au | 128,732 | 113,924 |
| Ir | 252,383 | 223,351 |
| Re | 5,757.6 | 5,095.3 |
| Ni | 16.91 | 14.96 |
| Co | 56.28 | 49.81 |
| Fe | 8.00 | 7.08 |
| Ag | 1,823.6 | 1,613.8 |
| Ru | 53,852.5 | 47,657.8 |
| Rh | 265,244 | 234,732 |

*USGS MCS 2026, 2025 estimates.* Each value is from the chapter's page-1 salient-statistics table.

| Element | USD/kg | Form priced | Already in the repo? |
|---|---:|---|---|
| In | 370 | metal | yes |
| Ga | 580 | metal | yes |
| Zn | 3.28 | metal | yes |
| Y | 40 | metal | yes |
| Cd | 3.90 | metal | yes |
| Zr | 22 | sponge | yes |
| La | 1.17 | from La2O3 | yes |
| Ce | 2.10 | 1.71 $/kg CeO2 ÷ 0.814 | added |
| Al | 1.11 | alumina 590 $/t ÷ 0.529 | added |
| Ti | 5.34 | TiO2 pigment 3,200 $/t ÷ 0.599 | added |
| Si | 2.87 | silicon metal 130 ¢/lb | added |
| Mg | 2.50 | metal, European free market | added |
| Ca | 0.36 | quicklime 260 $/t ÷ 0.715 | added |
| K | 1.45 | potash 1,200 $/t K2O ÷ 0.830 | added |
| Ba | 0.36 | barite 210 $/t ÷ 0.588 | added |

The "already in the repo" values are in `analysis/nh3_alloy_extension_2026_10_05/element_prices_usgs_mcs2026.csv`.
The added values come from the MCS 2026 rare-earths, bauxite-alumina, titanium, silicon, magnesium-metal, lime, potash
and barite chapters, downloaded from pubs.usgs.gov/periodicals/mcs2026/. Each locator is in `element_prices.csv`.

**Form rule.** Elements that appear as support oxides are priced at the oxide commodity where MCS gives one: Al, Ti,
Ce, La, Ca. Zirconia has no MCS price, so Zr is priced as sponge metal. This puts the ZrO2 support at about 14 €/kg
instead of the 4–8 €/kg of chemical-grade zirconia. The term is common to every ZrO2-supported entry, so it mostly
shifts their level.

**Price spread over the 991 candidates.** The median is 56 €/kg and the interquartile range is 20.7–629 €/kg.
- **Lowest.** SiO2 at 12.6 €/kg; Cu/ZnO, Cu/Al2O3 and Cu/CeO2 at 13–20 €/kg.
- **Bulk In2O3.** 282 €/kg: 82.7 wt% In at 370 USD/kg.
- **5 wt% Pd catalysts.** About 1,813 €/kg.
- **Highest.** 10 wt% Ir/In2O3 at 22,590 €/kg.

## 4. Parsing rules and coverage

Composition comes from the extracted fields `composition`, `active_metals`, `metal_wt_pct`, `support`, `promoters` and
`catalyst_name`.

The record's own composition text comes first. A paper may reuse one name for a loading series: in 10.1038/s41467-019-11349-9,
"CP" covers 0.25–10 wt% Pd. Records with the same name are used in two cases only:
- they fill a missing text;
- they supply a measured value (ICP, XRF, "measured", "actual", "real") when every nominal value under that name equals
  the record's own. This is how In13/ZrO2 takes its measured 11.9 wt%.

Loadings on a support are metal-basis wt%.
- Precious metals, Cu, Ni and Co count as metal.
- Other dopants (In, Zn, Y, La, Ca, K, Ba, Ga, Mg, Al, Ce) count as their oxide when the support remainder is sized.
- The remainder is the support: the `support` field, else the name.

**Generic patterns.** "x wt% M", "M = x wt%", "WM = x %", "M loading/content (of|=) x wt%", "content of M = x %",
"x wt% In2O3/CuO/NiO", "In2O3/NiO content|loading = x wt%". If none matches, the parser tries `metal_wt_pct` with a
single `active_metals`, then a loading in the name: Cu(x)ZnO, Inx/ZrO2, Ir/In2O3-x, xPd/.

**Paper rules** (`PAPER_RULES`), each stated in its docstring:

| Paper | Rule |
|---|---|
| anie.202401168 | "Ir1Pd1" = 0.44 wt% Ir + 0.25 wt% Pd (ICP, Ir/Pd molar 0.97); a leading factor and the subscripts scale them (0.5Ir1Pd1 = 0.35 wt%, as the record says) |
| cctc.202000974 | 5 wt% Pd; PdZn has Pd:Zn = 1:5 molar (paper Experimental); physical mixture Pd/ZnO + TiO2 taken as 1:1 by mass (`assumed`) |
| ente.201800747 | In2O3 wt% per Cat-x from the composition field, remainder Al2O3/Al-fiber priced as Al2O3; H-In2O3/Al2O3 takes Cat-4.5's 16.4 wt% (`assumed`) |
| apcata.2018.04.036, cattod.2019.05.040 | name code: wt% Ca, Pd (P) and Zn (Z) on CeO2 (C) or ZrO2 (Zr) |
| apcatb.2019.118367 | 2.5 wt% Pd; Pd/ZnO-xAl has x wt% Al in the Zn–Al oxide; ZnO/Al2O3 taken as 1:1 (`assumed`) |
| cattod.2020.05.049 | Pd–Cu with Pd/(Pd+Cu) = 0.25 atomic; the total loading is not in the paper (it cites its ref. 27). **Unparsed**: CZA price |
| cej.2022.135090 | In2O3 : HZSM-5 = 2 : 1 by mass, zeolite priced as SiO2 (`assumed`) |
| cej.2024.149370 | 1 wt% total (paper Experimental), split by the Pd/Pt atomic ratio in the name |
| fuel.2023.128376 | y % Zn-CdZrOx: y = Zn wt%; Cd:Zr = 1.264 : 9.76 molar from the recipe (0.39 g Cd(NO3)2·4H2O, 4.19 g Zr(NO3)4·5H2O) |
| fuel.2024.131111 | xInNi3C0.5: In x wt%, Ni:In = 3 molar; C neglected |
| jcat.2012.05.020 | measured Pd:Mg:Ga, Pd:Zn:Al and Pd:Mg:Al ratios as oxides, scaled to the measured Pd wt%; CuZnAl = reference CZA (`cza_reference`) |
| jcou.2016.11.015 | Cu + ZnO wt% and Cu/Zn molar (CZA-5 has no ratio: series mean 2.34); rest Al2O3 |
| jcou.2022.102209 | Co3O4 + In2O3 by the Co:In molar ratio in the name (default 7:3); the bamboo-powder template burns off at 450 °C; 1.04 wt% K |
| mcat.2020.111105 | x wt% CuO on Ce0.4Zr0.6O2 |
| acs.iecr.7b01464 | Cu:Zn:Al = 58:25:17 molar as oxides |
| acsaem.1c01502 | ZnZr: Zn/(Zn+Zr) = 13 % molar from the recipe (1.31 g Zn(NO3)2·6H2O, 12.68 g Zr(NO3)4·5H2O); Pd 0.1 wt% |
| acsami.1c05586 | yIn-xCu/CeO2 = y wt% In, x wt% Cu (paper notation); Cu/In2O3 and In2O3/CeO2 loadings are not printed (4.8 wt% Cu and 0.92 wt% In, `assumed`) |
| acscatal.1c03170 | NiO(x)–In2O3 = x wt% NiO; M–In2O3 = 5 wt% M |
| acscatal.9b03305 | xIn2O3–yZrO2 by measured In mol % of cations; In2O3/support by measured In2O3 wt% |
| cs500979c | 10 atom % Cu of cations (15 for Cu/ZrO2(I)), as Cu + ZrO2 |
| c2cy20604h | Cu/Al2O3 = 18/82 wt%; Cu–Ba and Cu–K = 5 wt% promoter + 95 wt% Cu/Al2O3 |
| c5cy00372e | Cu:Zn:(Al+Y) = 2:1:1 molar, Y/(Al+Y) from the name, as oxides |
| c5ra04774a | actual Cu and ZrO2 wt%, rest CNTs (carbon, no price: `carbon`) |
| c6ra28305e | Cu wt% from `metal_wt_pct`, rest ZrO2 |
| sciadv.1701290 | x % ZnO–ZrO2 = Zn/(Zn+Zr) molar |
| sciadv.abi6012 | measured In and Ni wt% where given, else the InNi3C0.5 loading split by stoichiometry; on ZnO, CeO2 and TiO2 the series' 42.8 wt% (`assumed`); CuZnAl = reference CZA |

Reference Cu–ZnO–Al2O3 catalysts get the commercial CZA composition, i.e. exactly 18.1 €/kg. This applies to
10.1002/anie.201600943, 10.1016/j.jcat.2012.05.020 and 10.1126/sciadv.abi6012.

**Coverage over the 991 candidates (264 distinct catalysts).**

| Flag | Candidates | Meaning |
|---|---:|---|
| parsed | 934 | |
| `assumed` | 23 | 8 catalysts; one ratio or loading not printed, assumption above |
| `carbon` | 18 | 3 catalysts; CNT support carried at no price |
| `cza_reference` | 4 | |
| **`unparsed`** | **12** | 11 catalysts, all from Pd–Cu/TixZr1–xO2 and TixCe1–xO2 (10.1016/j.cattod.2020.05.049); CZA price |

**Audit** (`parse_audit_sample40.csv`). A random sample of 40 candidates from 24 papers (seed 20261006) was read
against the record fields. For 16 of them, from 7 papers, the paper text was also read; the locators are in the file.
The PDF text is in the extraction worktree, `wt-extraction40/agent/extraction/text/`. All 40 agree with the source.

The audit caught one defect, which is fixed: an early version pooled the texts of every record sharing a name. That
priced the 0.75 wt% Pd "CP" entries of 10.1038/s41467-019-11349-9 at the 0.25 wt% value.

## 5. Self-check: Gothe et al. 2025 Table 4 (`selfcheck_gothe.csv`)

With the term off, all 21 extracted Table 4 entries reproduce the frozen costs to **2.3e-13 €/t**, inert and recycled
CO. The four canonical states are 943.30, 961.51, 966.96 and 1258.17 €/t.

With the term on, the composition price is used at a 3-year life, with inert CO and 2 % purge (the Table 4 path):
- 1 wt% Re/TiO2 (P25): Re 1.00 wt%, Ti 59.3 wt% → **65.21 €/kg**;
- 5 wt% Re/TiO2: Re 5.00 wt%, Ti 56.9 wt% → **268.91 €/kg**.

| Canonical state | Catalyst (t) | Term off (€/t) | Term on (€/t) | Replacement (€/t) |
|---|---:|---:|---:|---:|
| 5 wt% Re, 200 °C | 161.1 | 943.30 | 957.14 | 12.45 |
| 1 wt% Re, 250 °C | 223.1 | 961.51 | 966.15 | 4.18 |
| 1 wt% Re, 200 °C | 263.6 | 966.96 | 972.45 | 4.94 |
| 5 wt% Re, 250 °C | 181.3 | 1258.17 | 1273.73 | 14.01 |

The 5 wt% catalyst carries four times the Re of the 1 wt% catalyst for 1.6× the productivity. Its lead over 1 wt% Re
at 250 °C narrows from 18.2 to 9.0 €/t, but the order of the four states is unchanged.

## 6. Judgement calls

- **Frozen metal prices.** Pd, Pt, Au, Ir and Re use the frozen NH3-model set rather than MCS 2025, as the task asked.
  MCS 2026 gives Pd 1,100 $/oz (35,366 $/kg) against the frozen 40,671. With the MCS value, Pd prices fall by about 13 %.
- **Precious-metal recovery.** Applied only in the recovery variant, which credits 95 % of the precious-metal value at
  end of life. It is not applied to In or Ga.
- **Life.** The same life applies to every catalyst. No catalyst-specific deactivation is modelled.
- **Within-group order.** The catalyst charge is a constant per candidate, so the entry-optimal purge is the same with
  and without it. The variants are nevertheless computed through `economics(...)` on the whole purge grid, as specified.
- **Unparsed catalysts.** Per the task, they get the CZA price rather than a guess at the Pd–Cu loading. All 11 sit in
  one paper, so its groups are priced uniformly, as in the benchmark.
- **Parallelism.** 4 worker processes; about 5 minutes on the laptop.

## Files

| File | Content |
|---|---|
| `catalyst_prices.py` | price model, element prices, composition parser |
| `run_catalyst_cost_inversion.py` | rerun of the headline, variants, bootstrap, self-check |
| `catalyst_prices.csv` | one row per candidate: source fields, parsed components, element wt%, metal and precious value, price (anchor and Pérez-Fortes base), rule, flag |
| `element_prices.csv` | element prices with basis, source and locator |
| `candidate_costs.csv` | per candidate: STY, catalyst tonnes, price, cost, purge and replacement charge for every variant |
| `group_metrics.csv` | per group under the primary, with the term-off verdict, winner and regret alongside |
| `group_changes.csv` | the 14 groups whose winner or verdict changes, with prices and inventories |
| `selfcheck_gothe.csv` | Table 4 entries with the term off and on |
| `parse_audit_sample40.csv` | the 40-candidate parse audit |
| `summary.json` | every metric above |
