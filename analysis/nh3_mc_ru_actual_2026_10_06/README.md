# NH3 economic Monte Carlo with the actual Ru catalyst — 2026-10-06

`run_mc_ru_actual.py` writes `draws.csv` (5,000 rows) and `summary.json`.

The preregistered cost Monte Carlo (5,000 draws, seed 20260920; Fe and Ru price multipliers, CAPEX multiplier,
electricity price, catalyst lifetime; full reoptimization over 14,136 states) charges Ru as the benchmark bed of pure
metal and gives P(C_Fe < C_Ru) = 1.000. It is reproduced first (minimum gap 2.382 USD/t). The actual Ru catalyst is
then added with inputs from a second generator (seed 20261006), so every preregistered draw keeps its values.

| Input | Range | Source |
|---|---|---|
| dispersion ratio u = D_Ru / f_Fe | log-uniform 11–50 | D_Ru 11 % (Ba–Cs–K Ru/C, 3.2 wt%; Rossetti et al., Ind. Eng. Chem. Res. 45, 4150, 2006) to ≈ 50 % (2 nm Ru in Ba–Ru/MPC; Nishi, Chen & Takagi, Catalysts 9, 480, 2019; D ≈ 1/d[nm]); f_Fe = 1 % (exposed Fe < 1 %; Liu et al., CIESC J. 51, 462, 2000) |
| Ru recovery r | uniform 0.90–0.94 | US 6,673,732 B2 (> 94 %), lower end 90 % as in Fig. 2d |
| Ru content of the supported bed | drawn from the 54 measured Ru catalysts (0.27–13.8 wt%, median 4 wt%; 56 before the PR #28 errata, same range and median) | `analysis/nh3_supported_2026_10_06` |
| bed density | uniform 500–1,000 kg m⁻³ | as in the Fig. 2d bed sensitivity |
| measured Ru activity (variants B, B0) | one of the 54 measured Ru catalysts per draw (56 before the PR #28 errata): effective descriptor, residual multiplier, Ru content | `analysis/nh3_supported_2026_10_06` |

## Results

Rerun on 2026-10-07 after two corrections (review finding A1 and the outlet-fraction fix), same seeds:

1. **Variant A now uses the Fig. 3d convention.** The benchmark-formulation reading of Fig. 3d
   (`figures/composite/fig2/fig2_ru_actual_cost.py`) lowers only the price, to p_eff = p_Ru (1 − r) / u, and keeps the
   benchmark bed of the undivided metal mass. Variant A divided both the metal mass and the bed volume by u (`alpha=u`),
   which shrinks the reactor as well. It is now evaluated at p_eff with the undivided benchmark bed, exactly as in
   Fig. 3d (at u = 11, r = 0.90: 15.572 USD/t with a 0.160 m³ bed before, 15.671 USD/t with 1.757 m³ now). A_bed, B and
   B0 keep their convention (the supported bed holds m_Ru / u at its own Ru content and density, which is what
   `fig2_ru_bed_sensitivity.csv` uses).
2. **Measured catalysts (B, B0)** use `supported_candidates.csv` after the outlet NH₃ fraction fix of
   `analysis/nh3_supported_2026_10_06` (n / (F₀ − n) instead of n / F₀).

The base reproduction still gives P(Fe cheaper) = 1.000 and minimum gap 2.382 USD/t.

| Variant | P(Fe cheaper) | before 2026-10-07 | Ru − Fe, median (USD/t) | before |
|---|---:|---:|---:|---:|
| preregistered, pure-Ru benchmark | 1.000 | 1.000 | 7.11 (reproduced) | 7.11 |
| A: u and r on the price, benchmark bed (Fig. 3d reading) | **0.480** | 0.240 | −0.01 | −0.31 |
| A_bed: u and r, supported bed (own Ru content and density) | 0.800 | 0.800 | +0.37 | +0.37 |
| B: measured Ru catalysts, with recovery | **0.943** | 0.946 | +4.35 | +4.36 |
| B0: measured Ru catalysts, no recovery | 0.989 (0.9892) | 0.989 (0.9894) | +7.41 | +7.41 |

(Before the PR #28 errata: A 0.240, A_bed 0.804, B 0.949, B0 0.989.)

Where Ru wins (P(Ru wins) given the condition; u terciles 18.2 and 30.4, r terciles 0.914 and 0.927; written by the
script to `summary.json`, `A_where_Ru_wins` and `A_bed_where_Ru_wins`):

| Condition | A_bed | A (Fig. 3d reading) | A before 2026-10-07 |
|---|---:|---:|---:|
| all draws | 0.200 | **0.520** | 0.760 |
| u in its lowest tercile | 1.3 % (0.0132) | 24 % (0.245) | 52 % |
| u in its top tercile | 45 % (0.455) | 80 % (0.800) | 95 % |
| r in its lowest / top tercile | 16 % / 23 % | 43 % / 62 % | 69 % / 84 % |
| u and r both in their top terciles | 50 % (0.498) | 87 % (0.873) | 98 % |
| u or r in its lowest tercile | 10 % (0.105) | 38 % (0.377) | 64 % |
| Ru content < 2.5 wt% | 0.5 % (0.0046) | (Ru content does not enter A) | |
| Ru content ≥ 5 wt% | 39 % (0.393) | | |
| by quintile of p_eff (low to high) | 0.55, 0.27, 0.14, 0.05, 0.00 | 0.98, 0.80, 0.55, 0.26, 0.02 | 1.00, 0.98, 0.88, 0.68, 0.26 |

A_bed is unchanged to the last digit (it does not use the measured activities and its convention is unchanged).
Within 90–94 % the recovery matters less than the dispersion ratio. With the benchmark bed (A), Ru wins in 52 % of
draws; its median cost gap to Fe is −0.01 USD/t, i.e. the Fig. 3d reading at u = 11–50 and r = 0.90–0.94 sits on the
Fe boundary.

In B the Ru wins come from five of the 54 catalysts, the same five as before: Ru/Ca(NH₂)₂, Ru/Ba–Ca(NH₂)₂,
Ru/BaO–CaH₂, Ru/Cs/Ba/CCHT and Ru/AC-G. Measured per gram of Ru, the Ru catalysts deliver a median 0.23 of the benchmark
Ru activity at their laboratory conditions (0.226; 0.220 before the outlet fix, 0.216 before the errata), and 0.060
for the 11 measured at ≥ 5 MPa (unchanged; 0.034 for 13 before the errata), well below the u ≥ 11 the Fig. 3d mapping
assumes (median of the `alpha` column of `supported_candidates.csv`, primary Ru rows with a cost).

`agent/selfcheck_report.json`, which the gate rewrites with a new timestamp only, is left at its committed version.
Earlier manuscript-impact notes: `ERRATA_RERUN_2026-10-07.md` (PR #28 errata; its variant-A and B values are superseded
by the table above).

The script calls the ACSA self-check gate first.
