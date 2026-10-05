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

## Results (309 surfaces whose elements all carry a frozen price)

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
- 1,487 surfaces contain an element without a frozen price (Nb, Ti, Al, La, V, Zr, Hf, Sn, Ta, Tc, Y, Zn, Cd, In,
  Sc, Pb, Ga, Cr, Hg, Tl, Mn, Bi) and are not costed.
