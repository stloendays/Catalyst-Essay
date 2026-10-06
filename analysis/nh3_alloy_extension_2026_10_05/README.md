# NH3 screen extended to bimetallic alloy surfaces — 2026-10-05

Every surface of the Mamun et al. (2019) bimetallic database is taken through the same chain as the 15 pure
metals: N binding energy → step-site descriptor → per-state activity on the frozen 14,136-state process library →
frozen cost model → cost optimum under the 90 m³ bed cap → comparison with Fe (15.2917 USD/t NH₃).

- Data: Mamun, Winther, Boes & Bligaard, *Scientific Data* **6**, 76 (2019), doi:10.1038/s41597-019-0080-z;
  Catalysis-Hub `MamunHighT2019` (CC BY 4.0). `fetch_mamun_n_binding.py` writes
  `mamun2019_N_binding_sites.csv`: 5,696 N* sites on 1,796 surfaces. Two independent fetches gave identical files.
- Chain: `run_alloy_chain.py` writes `alloy_chain_results.csv`, `calibration.json` and `summary.json`.

## Descriptor bridge

The model's descriptor is the step-site N formation energy of Dataset S1 (Wang & Abild-Pedersen, PNAS 2021). The
frozen workbook already places Fe with the 14-metal terrace→step regression (step = 1.1547 × terrace − 0.1701).
The Mamun values are put on the S1 terrace scale with a linear fit over the 14 pure metals present in both datasets
(slope 0.845, R² 0.973, RMS 0.22 eV). Two routes are reported:

- **Global:** the two linear maps above.
- **Element-anchored:** each element's offset between its frozen step E_N and its chain value is added in
  proportion to atomic fraction, so every pure metal sits exactly at its frozen descriptor. Ni has no pure Mamun
  surface and keeps a zero offset.

## Results with frozen prices (309 surfaces whose elements all carry a frozen price)

| | Global route | Element-anchored route |
|---|---|---|
| inside the 90 m³ bed cap | 114 | 121 |
| below Fe | Fe3Mo 14.53, Cu3Mo 14.83, Fe3W 14.90, Ni3W 15.08 | Cu3Mo 14.60, CuMo 14.70, MoNi 14.70, CoMo 15.07, CoW 15.16 |
| highest-activity surface (673 K) | Os3Pt, economic rank 32, 24.55 USD/t | AuW, economic rank 29, 23.39 USD/t |
| regret of choosing it | 69.0 % | 60.2 % |
| Spearman, activity vs cost | 0.78 | 0.74 |

Every surface below Fe, in either route, pairs one cheap 3d metal (Fe, Co, Ni, Cu) with Mo or W; that family has 23
costed members. With the global route, shifting every descriptor by ±0.33 eV (propagated calibration RMS) gives 4 and 6
surfaces below Fe.

## Self-check and pruning

- The same code path reproduces the canonical deterministic cost of every pure metal to < 1e-9 USD/t, and the
  frozen price table is unchanged after the batch.
- A descriptor-only lower bound (best-state activity, smallest reactor, cheapest process state) rules out 243 of 309
  candidates (78.6 %) before the full 14,136-state optimization. All 309 are also optimized in full: no candidate
  below Fe is ruled out.

## Extension to all priced elements (USGS Mineral Commodity Summaries 2026)

The 22 elements without a frozen price take the 2025 annual-average prices of the USGS Mineral Commodity Summaries 2026
(https://pubs.usgs.gov/publication/mcs2026, per-commodity PDFs `mcs2026-<commodity>.pdf`), expressed per kg of contained
metal: oxide, ore and ferroalloy quotations are divided by the metal mass fraction (`element_prices_usgs_mcs2026.csv`
lists the quotation, unit, conversion and basis for each element; Hg uses 2024, the latest year reported). Tc has no
market price; its 101 surfaces stay uncosted. The frozen 15-metal prices are unchanged and the frozen-price results
above are reproduced exactly.

Each surface carries a `domain` label, because the activity model is fitted on transition metals:

| Layer | Costed | Inside bed cap | Below Fe, global route | Below Fe, anchored route |
|---|---:|---:|---|---|
| transition metals only (no sp metal, no group 3–5 element) | 372 | 138 | Cu3Cr 14.36, Fe3Mo, Cu3Mo, Fe3W, Ni3W | Cu3Cr 14.36, Cu3Mo, CuMo, MoNi, CoMo, CoW |
| + group 3–5 elements (Sc, Y, La, Ti, Zr, Hf, V, Nb, Ta) | 912 | 222 | 13 (Fe3V 14.30 first) | 16 (Cu3Cr first) |
| + sp metals (Al, Zn, Cd, Hg, Ga, In, Tl, Sn, Pb, Bi) | 1,695 | 406 | 52 (Al3Ti 13.85 first) | 56 |

- In the transition-metal layer every surface below Fe, in either route, is one cheap 3d metal (Fe, Co, Ni, Cu) with a
  group-6 metal (Cr, Mo, W). The highest-activity surface ranks 43rd (Os3Pt, regret 70.9 %) or 40th (AuW, 62.9 %).
- Surfaces containing sp metals lie outside the transition-metal scaling and BEP relations the activity model is built
  on (pure Al, for example, is placed near Fe on the descriptor axis and priced at 3.97 USD/kg). Group 3–5 elements form
  very stable bulk nitrides, which a surface-descriptor screen does not represent. Both layers are reported, not ranked.
- Descriptor-only pruning over all 1,695 costed surfaces rules out 1,397 (82.4 %) before full optimization, with no
  false prunes.

## Counterfactual and backward design for the leading surfaces (2026-10-06)

`run_alloy_backward.py` writes `alloy_backward.csv` and `alloy_backward_summary.json`. The expensive steps of the
hand-built Ru analysis are run only on the candidates the forward screen puts at the top: the transition-metal
surfaces below Fe in either route and the highest-activity surface of each route. Each step reoptimizes the full
14,136-state library; the forward costs reproduce `alloy_chain_results.csv`.

| Surface | Route | Cost (USD/t) | At Fe price | α* to Fe parity | Price at Fe parity (USD/kg) |
|---|---|---:|---:|---:|---:|
| Cu3Cr | global / anchored | 14.36 / 14.36 | 14.31 / 14.31 | 0.237 / 0.237 | 382 / 383 |
| Cu3Mo | global / anchored | 14.83 / 14.60 | 14.69 / 14.37 | 0.522 / 0.305 | 168 / 361 |
| Fe3Mo | global | 14.53 | 14.30 | 0.268 | 419 |
| Fe3W | global | 14.90 | 14.63 | 0.572 | 218 |
| Ni3W | global | 15.08 | 14.74 | 0.757 | 144 |
| CuMo, MoNi | anchored | 14.70 | 14.45, 14.43 | 0.378 | 327, 333 |
| CoMo | anchored | 15.07 | 14.76 | 0.753 | 136 |
| CoW | anchored | 15.17 | 14.71 | 0.850 | 167 |
| Os3Pt (highest activity) | global | 24.55 | 14.96 | 689 | 69.9 |
| AuW (highest activity) | anchored | 23.39 | 14.99 | 405 | 61.6 |

Fe: 15.29 USD/t. α* < 1 is the activity a surface below Fe can lose and still undercut Fe (Cu3Cr keeps the lead
with 24 % of its activity). Counterfactual: at the Fe price both activity leaders undercut Fe, as Ru does; the
reversal at the top is again set by metal price. Backward: they need 689-fold and 405-fold activity, and no
descriptor on the strict scaling range brings them below 24.54 and 23.20 USD/t at their own prices (they already sit at
the volcano top), so only a lower metal inventory cost can close the gap. Cu3Cr and Cu3Mo are below Fe in both routes;
Fe3Mo, Fe3W and Ni3W only in the global route and CuMo, MoNi, CoMo and CoW only in the anchored route
(α* 1.6–2.4 in the other route; CoW 193, its global-route descriptor lies far off the volcano top).
