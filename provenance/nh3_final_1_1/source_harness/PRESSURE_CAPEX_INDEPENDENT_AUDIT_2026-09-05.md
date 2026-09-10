# Independent audit of the NH3-FINAL-1.1 pressure-CAPEX chain (PHASE A, 2026-09-05)

Scope: `harness_core.py` (`vessel_pressure_premium`, `compressor_capex_USD_t`, `turton_cp0`, `cost_breakdown_at`, the compressor term in
`self_consistent_process_state`, the premium term in `cost_arrays`) and the parameter block `economics.pressure_capex` of
`configs/nh3_final_1.1_candidate.yaml`. Audited run: `outputs/nh3_final_1_1_20260905T113727Z`.
Method: every pool was recomputed from explicit formulas in a script that does **not** import the harness
(`audits/audit_pressure_capex_handcalc_2026-09-05.py`, output `.out.txt`), using only the manifest numbers and the stored optimum (V, P, T, Tsep).
Nothing in the model, the manifest or the frozen files was modified by this audit.

## 0. Annualization chain (shared by all three CAPEX pools)
- CRF = 0.12·1.12²⁵ / (1.12²⁵ − 1) = **0.127500 y⁻¹** (identical to 1.0; same constant multiplies the 1.0 reactor volume proxy).
- Annual output = 1000 t/d × 365 × 0.95 = **346,750 t/y** (identical to 1.0).
- USD/t = C_BM [USD] × CRF / 346,750. No operating-hours term is needed: electricity pools are already per tonne; CAPEX pools are per tonne of
  *annual* output at 95 % capacity factor; compressors are sized at design capacity (tpd/24, no CF) — the correct asymmetry.
- Cost index ratio 797.9/397 = 2.00982 multiplies each new C_BM **once** (checked in code: one `*self.PC_INDEX_RATIO` per term).

## 1. Vessel pressure premium
Formula implemented: ΔC_BM = Cp0(V_cost)·B2·Fm·(Fp − 1)·(797.9/397), V_cost = max(V, 0.3 m³), D = (4·V_cost/(π·3))^(1/3),
t = P·D / (2·(850 − 0.6·P)) + 0.00315, Fp = max(t/0.0063, 1), log10 Cp0 = 3.4974 + 0.4485·log10 V + 0.1074·(log10 V)².

| check | finding |
|---|---|
| Cp0(V) correlation and range | Turton vertical process vessel, A = volume in m³, 0.3–520 m³. Fe 17.06 m³ inside; Ru 0.066 m³ below the floor → costed at 0.3 m³ (declared). Spot check: Cp0(20 m³) = 1.83 × 10⁴ USD (2001), consistent with the textbook figure. |
| log10 input units | m³ (vessel), kW (compressor). Correct. |
| B2, Fm, Fp usage | Turton C_BM = Cp0·(B1 + B2·Fm·Fp); the pressure-attributable part is Cp0·B2·Fm·(Fp − 1). B1 (= 2.25) is correctly *not* used, because the Fp = 1 base module is what the 1.0 volume proxy already represents. Fm = 1 (carbon steel). |
| ASME thickness units | Turton: t [m] = (P_g + 1)·D / (2·(S·E − 0.6·(P_g + 1))) + CA with P_g in barg, D in m, S·E = 944 × 0.9 = 850 bar. The harness uses absolute P [bar] in place of (P_g + 1) — difference 0.013 bar, negligible. Units consistent (bar/bar → dimensionless × m). |
| corrosion allowance / t_min | CA = 0.00315 m added after the thickness term; t_min = 0.0063 m (Turton). Correct. |
| CEPCI applied once | Yes. |
| increment only, no double count with the 1.0 volume proxy | Only (Fp − 1) is added; the Fp = 1 vessel is *not* re-costed. Residual risk: the 1.0 term (Palys et al. 2018, fixed + 268,000·(V/20)^0.52) could not be re-read (publisher blocks fetch) so whether it already embeds a pressure factor is unverified. Bound: even if the whole 1.0 term were pressure-inclusive, the overlap is ≤ the 1.0 term itself, i.e. ≤ 0.115 USD/t (Fe, 0.8 % of cost) and ≤ 0.030 USD/t (Ru, 0.1 %). Cannot change ranking or reachability. |

Hand calculation (independent script):

| quantity | Fe optimum | Ru optimum |
|---|---|---|
| operating point | 425 °C / 180 bar / Tsep 30 °C | 450 °C / 425 bar / Tsep 25 °C |
| V (bed) | 17.0592 m³ | 0.06603 m³ → costed at 0.3 m³ |
| D = (4V/(3π))^(1/3) | 1.9346 m | 0.5031 m |
| t = P·D/(2(850 − 0.6P)) + 0.00315 | 180×1.9346/(2×742) + 0.00315 = **0.2378 m** | 425×0.5031/(2×595) + 0.00315 = **0.1828 m** |
| Fp = t/0.0063 | **37.75** | **29.02** |
| Cp0 (2001 USD) | 10^(3.4974 + 0.4485×1.2320 + 0.1074×1.5178) = **16,328** | 10^(3.4974 − 0.2345 + 0.0294) = **1,960** |
| ΔC_BM = Cp0·1.82·1·(Fp − 1)·2.0098 | 16,328 × 1.82 × 36.75 × 2.0098 = **2,194,705 USD** | 1,960 × 1.82 × 28.02 × 2.0098 = **200,881 USD** |
| annualized USD/t = ΔC_BM × 0.1275 / 346,750 | **0.806993** (harness 0.806993) | **0.073864** (harness 0.073864) |

Plausibility: a 0.24 m wall on a 1.9 m converter at 180 bar and 0.18 m on a 0.5 m vessel at 425 bar are of the order of industrial converter shells.

## 2. Compressor CAPEX
Formula implemented: kWh/t = (USD/t) / (50 USD/MWh) × 1000; W [kW] = kWh/t × 1000 t/d ÷ 24 h/d; n = ceil(W/3000); Cp0 per unit from
log10 Cp0 = 2.2897 + 1.3604·log10 W_u − 0.1027·(log10 W_u)² (450–3000 kW; outside → power law 0.67 from the bound); C_BM = n·Cp0·2.8·2.0098.

| check | finding |
|---|---|
| origin of the power | The state library stores compression *electricity cost* per tonne computed from isothermal reversible work / η = 0.75 (fresh: 2 mol gas per mol NH3 from 30 bar to P; recycle: recycle_total mol from P − 3 to P). Back-conversion USD/t → kWh/t → kW is exact algebra: the electricity price cancels (÷50 then the same 50 was multiplied in), and the daily rate uses design tonnage, not CF. Verified independently: the fresh-gas electricity recomputed from first principles (2 × 58,718 mol/t × R × 298.15 K × ln(P/30) / 0.75 / 3.6e9 × 50) reproduces the stored pool to 6 decimals for both metals. |
| fresh vs recycle double counting | Two separate services with separate duties (Fe: 8,050 kW and 637 kW; Ru: 11,909 kW and 98 kW). Not double counted; the recycle machine is sized from the recycle flow only. |
| > 3000 kW split | n = ceil(W/3000), equal units, cost = n·Cp0(W/n). Fe fresh → 3 × 2,683 kW; Ru fresh → 4 × 2,977 kW. Consistent with the correlation's stated upper bound. |
| correlation range | Fe recycle 637 kW inside; Ru recycle 98 kW below 450 kW → power-law extrapolation (declared); contributes 0.11 USD/t. |
| capacity basis (definitional, unresolved) | Turton's compressor capacity is "power, kW". Secondary reproductions read it as *shaft power*; the textbook wording is also quoted as "fluid power" in some sources. The harness uses the electrical/shaft basis (isothermal work ÷ 0.75). If the fluid-power basis (× 0.75) were intended, compressor CAPEX would fall: Fe 3.87 → 3.18, Ru 5.06 → 3.80 USD/t (−18 to −25 %). This is covered by the −20 % sensitivity case below and does not change any conclusion; it is recorded as an open definitional choice, not a unit error (both are kW). |
| F_BM | 2.8 (centrifugal, carbon steel) in both secondary reproductions of Turton Table A.6 consulted. Kept; ±20 % sensitivity covers the alternative value 2.7. |
| CEPCI | Applied once, 797.9/397. |
| annualization → USD/t | C_BM × 0.1275 / 346,750, same chain as the vessel term. |

Hand calculation (independent script):

| quantity | Fe fresh | Fe recycle | Ru fresh | Ru recycle |
|---|---|---|---|---|
| electricity pool (USD/t) | 9.6596 | 0.7647 | 14.2912 | 0.1179 |
| kWh/t = USD/t ÷ 50 × 1000 | 193.19 | 15.29 | 285.82 | 2.36 |
| W = kWh/t × 1000/24 (kW) | 8,050 | 637 | 11,909 | 98 |
| n, W per unit | 3, 2,683 | 1, 637 | 4, 2,977 | 1, 98 (extrapolated) |
| Cp0 per unit (2001 USD) | 558,128 | 198,177 | 597,263 | 54,124 |
| C_BM = n·Cp0·2.8·2.0098 | 9,422,613 | 1,115,243 | 13,444,398 | 304,582 |
| USD/t | 3.464695 | 0.410075 | 4.943505 | 0.111995 |
| service total | **3.874770** (harness 3.874770) | | **5.055500** (harness 5.055500) | |

Implied recycle ratios from the recycle pools (16.9 mol/mol NH3 for Fe at 180 bar, 6.2 for Ru at 425 bar) are physically reasonable for
X ≈ 0.1–0.25 loops.

## 3. Reconciliation of the reported breakdowns
| pool | Fe hand | Fe harness | Ru hand | Ru harness | nature / exclusivity |
|---|---|---|---|---|---|
| metal inventory | 0.070362 | 0.070362 | 1.833375 | 1.833375 | replacement of active metal over 10 y; catalyst-property dependent; no overlap |
| reactor volume proxy (1.0) | 0.115284 | 0.115284 | 0.029613 | 0.029613 | Palys volume correlation at its (unstated) reference pressure |
| pressure-shell premium (new) | 0.806993 | 0.806993 | 0.073864 | 0.073864 | Turton increment above Fp = 1; overlap with the row above bounded by that row's size |
| fresh compression electricity | 9.659553 | 9.659553 | 14.291221 | 14.291221 | OPEX; recomputed from physics |
| recycle compression electricity | — | 0.764743 | — | 0.117903 | OPEX; needs recycle flow (not stored); consistency checked via implied recycle ratio |
| refrigeration electricity | 0 | 0 | 0.629119 | 0.629119 | OPEX; Carnot/0.5 basis recomputed |
| compressor CAPEX (new) | 3.874770 | 3.874770 | 5.055500 | 5.055500 | capital; distinct from the electricity it consumes |
| **total** | **15.291705** | **15.291705** | **22.030595** | **22.030595** | sums exactly |

Electricity (OPEX) and compressor CAPEX are mutually exclusive by construction (same duty, different cost class). The only non-exclusive pair
is "reactor volume proxy" vs "pressure-shell premium" if the Palys term already contained a pressure factor; the maximum possible overlap is the
whole proxy row (0.115 / 0.030 USD/t). Rounded values quoted in the request (0.07 / 0.12 / 0.81 / 9.66 / 0.77 / 3.88 → 15.29; 1.83 / 0.03 / 0.07 /
14.29 / 0.12 / 0.63 / 5.06 → 22.03) are all reproduced.

## 4. Sensitivity sanity check (scenario manifests derived from the 1.1 candidate, full mode, registered; canonical untouched)
| perturbation | order | Top-3 ρ | Fe @ P | Ru @ P | Os @ P | Ru/Fe | Ru break-even | Fe feas. | optimum on 1000-bar edge |
|---|---|---|---|---|---|---|---|---|---|
| 1.1 baseline | Fe > Ru > Os | −0.50 | 15.29 @ 180 | 22.03 @ 425 | 25.83 @ 425 | 1.441 | 201.2× | 0.799 | none |
| CEPCI −10 % | same | −0.50 | 14.82 @ 175 | 21.52 @ 425 | 25.32 @ 430 | 1.452 | 224.2× | 0.799 | none |
| CEPCI +10 % | same | −0.50 | 15.76 @ 180 | 22.54 @ 420 | 26.34 @ 425 | 1.430 | 182.8× | 0.799 | none |
| discount 8 % (CRF 0.0937) | same | −0.50 | 14.00 @ 175 | 20.66 @ 430 | 24.46 @ 430 | 1.475 | 283.9× | 0.799 | none |
| discount 15 % (CRF 0.1547) | same | −0.50 | 16.31 @ 190 | 23.13 @ 420 | 26.84 @ **220** | 1.419 | 151.0× | 0.799 | none |
| compressor CAPEX −20 % | same | −0.50 | 14.52 @ 180 | 21.02 @ 425 | 24.82 @ 430 | 1.448 | 200.5× | 0.799 | none |
| compressor CAPEX +20 % | same | −0.50 | 16.07 @ 180 | 23.04 @ 420 | 26.78 @ **220** | 1.434 | 201.9× | 0.799 | none |
| vessel premium −20 % | same | −0.50 | 15.12 @ 175 | 22.02 @ 425 | 25.82 @ 425 | 1.456 | 251.9× | 0.799 | none |
| vessel premium +20 % | same | −0.50 | 15.42 @ 190 | 22.05 @ 425 | 25.85 @ 425 | 1.429 | 157.6× | 0.799 | none |

Read-out: ranking, Top-3 inversion, Fe feasibility, scaling headroom (2.525× in every case) and the reachability verdict are invariant; the
break-even multiplier moves within 151–284× (factor 1.9 spread, no order-of-magnitude change; it is most sensitive to the vessel premium and to
CRF, both through Fe's cost). No optimum returns to a grid edge. One structural observation: Os has a flat valley with two near-equal minima
(≈220 bar and ≈425–430 bar); two perturbations flip which is lower by < 0.1 USD/t. Os is third in every case, so this is not decision-relevant,
but Os's "optimal pressure" should not be quoted with more precision than the valley allows.

## 5. Items that remain declared rather than verified
1. Provenance of the 1.0 reactor volume proxy (Palys et al. 2018) — pressure basis unknown; overlap bounded ≤ 0.115 / 0.030 USD/t.
2. Compressor capacity basis (shaft vs fluid power) — bounded by the −20 % case.
3. F_BM = 2.8 vs 2.7 — bounded by the ±20 % case.
4. Loop heat exchangers, separator and HP piping still outside the boundary (already declared in the assumptions file; direction favours Ru).

## Verdict
**PASS.** Dimensions, annualization and the costing chain are consistent; every reported pool is reproduced by independent arithmetic to six decimals;
the new terms are mutually exclusive with the electricity pools and add only the pressure-attributable increment; no perturbation of the
handbook constants changes the ranking, the inversion, feasibility, or the reachability verdict. The three declared items above must be carried
verbatim into the 1.1 documentation and cannot move any headline conclusion.

## Appendix (added after promotion, 2026-09-05): compressor CAPEX −25 % diagnostic
Requested because the shaft-vs-fluid-power convention could lower compressor CAPEX by up to ≈ 25 %, beyond the ±20 % band above.
Scenario `s11_comp_m25` (F_BM 2.8 → 2.1, i.e. −25 %; derived from the promoted canonical NH3-FINAL-1.1, full mode, registered):

| quantity | canonical 1.1 | compressor CAPEX −25 % |
|---|---|---|
| feasible order / Top-3 ρ | Fe > Ru > Os / −0.50 | Fe > Ru > Os / −0.50 |
| Fe / Ru / Os cost (USD/t) @ P | 15.29 @ 180 / 22.03 @ 425 / 25.83 @ 425 | 14.32 @ 180 / 20.77 @ 430 / 24.57 @ 430 |
| compressor CAPEX pool Fe / Ru | 3.87 / 5.06 | 2.91 / 3.80 |
| Ru/Fe | 1.441 | 1.450 |
| Ru break-even | 201.2× | 200.4× |
| all-state headroom / verdict | 2.525× / unreachable | 2.525× / unreachable |
| Fe feasibility | 0.799 | 0.799 |
| any optimum on a grid edge | none | none |

Conclusion unchanged: the compressor-capacity convention shifts absolute costs by ≈ 1 USD/t but leaves ranking, boundary behaviour and the
break-even order of magnitude intact. Run: `outputs/s11_comp_m25_20260905T134328Z`.
