# NH3-FINAL-1.3: separator VLE from the measured BASF table, multistage compression (items A+B, 2026-10-22)

Protocol: `PREREGISTRATION.md`. Code: `harness13.py` (subclass of the 1.2 harness; only the loop state changes),
`run_13.py` (`NH3_MODEL=1.2`, ~2 min). Outputs: `results.json`, `benchmark_rescore.csv`.

The 1.2 numbers recomputed on this code path equal the manuscript's: descriptor Fe 11.516 / Ru 16.632 / Os 19.746 USD/t,
Ru price parity 404 USD/kg, activity multiple 115; measured laws Fe 15.307 USD/t, Ru/C −3.83 / +2.13 USD/t at 0 / 12 %/y,
break-even 6.49 %/y (own optima) and 4.57 %/y (KAAP-type loop), −1.99 / −0.65 USD/t at 2.10 %/y, bulk-Ru parity
3,371 USD/kg or 15.7-fold activity.

## Gates

| Gate | Result |
|---|---|
| G1 VLE hold-out, Uhde Fig. 57 stream 5 (21 °C, 18.02 MPa, 8.51 %) | 7.98 % (−6.2 %; 1.2: 4.93 %, −42 %) — pass |
| G1 VLE hold-out, stream 6 (0 °C, 17.88 MPa, 4.18 %) | 4.04 % (−3.3 %; 1.2: 2.38 %, −43 %) — pass |
| G2 compression E01 / E02 / E03 (±30 %) | −46 % / −41 % / −38 % (1.2: −42 / −36 / −77 %) — **fail** |
| G3 registered state-level items (Tables A, E, V) | 18/32 in 1.3, 18/32 in 1.2 (gained V01, A16; lost A11, A24) |

Converter-inlet NH₃ moves from −63 % (typical, 1.2) to −28 to −47 %: the separator vapour is now right, and what remains
is loop topology — in the industrial loops make-up gas enters ahead of the refrigerated separator and the loop carries
8–12 % inert gas, neither of which the model has. Standard multistage polytropic compression (η_p 0.78, intercooling to
40 °C, 9.2-bar recycle) does not close the compression gap; the plants draw about 1.7 times the modelled power.
1.3 is therefore a structural robustness check, not a replacement of 1.2.

## Results, 1.2 → 1.3

| Quantity | 1.2 | 1.3 |
|---|---:|---:|
| Descriptor order | Fe < Ru < Os | Fe < Ru < Os |
| Fe / Ru / Os (USD/t) | 11.52 / 16.63 / 19.75 | 12.64 / 17.81 / 21.50 |
| Ru − Fe (USD/t) | 5.12 | 5.17 |
| Fe optimum; Ru optimum | 425 °C, 105 bar; 450 °C, 220 bar | 425 °C, 150 bar; 450 °C, 320 bar |
| Ru price parity (USD/kg) | 404 | 527 |
| Ru activity multiple for parity | 115 | 87.5 |
| Measured laws: Fe benchmark (USD/t) | 15.31 | 16.41 |
| Ru/C − Fe at 0 / 2.10 / 12 %/y, own optima | −3.83 / −1.99 / +2.13 | −3.01 / −0.70 / +3.24 |
| Ru/C − Fe at 2.10 %/y, KAAP-type loop | −0.65 | −0.77 |
| Break-even financing rate, own optima / KAAP | 6.49 / 4.57 %/y | 3.24 / 4.84 %/y |
| Bulk Ru parity: price (USD/kg) / activity | 3,371 / 15.7× | 1,894 / 27.5× |

Every qualitative conclusion holds: Fe leads on the descriptor model by the same margin; bulk Ru needs a price cut of
more than 90 % or a large activity gain; supported Ru/C undercuts fused iron at the 2.10 %/y reference rate on both
bases, and the break-even rate stays above the reference rate. The descriptor optima move to higher pressure because the
separator now returns more NH₃ at low pressure.
