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
| Ru content of the supported bed | drawn from the 56 measured Ru catalysts (0.27–13.8 wt%, median 4 wt%) | `analysis/nh3_supported_2026_10_06` |
| bed density | uniform 500–1,000 kg m⁻³ | as in the Fig. 2d bed sensitivity |
| measured Ru activity (variant B) | one of the 56 measured Ru catalysts per draw: effective descriptor, residual multiplier, Ru content | `analysis/nh3_supported_2026_10_06` |

## Results

| Variant | P(Fe cheaper) | Ru − Fe, median (USD/t) |
|---|---:|---:|
| preregistered, pure-Ru benchmark | 1.000 | 7.11 (reproduced) |
| A: u and r, benchmark bed volume (Fig. 2d mapping) | 0.240 | −0.31 |
| A_bed: u and r, supported bed (own Ru content and density) | 0.804 | +0.40 |
| B: measured Ru catalysts, with recovery | 0.949 | +4.54 |
| B0: measured Ru catalysts, no recovery | 0.989 | +7.71 |

Where Ru wins (A_bed, P = 0.196): 1.3 % of draws with u in its lowest tercile (u < 18.2), 49 % with u and r both in
their top terciles (u ≥ 30.4, r ≥ 0.927); 0.6 % of draws below 2.5 wt% Ru, 39 % at 5 wt% or more. Within 90–94 % the
recovery matters little. In A the benchmark bed volume removes the dilution penalty of a supported bed, and Ru wins in
76 % of draws; P(Ru wins) by quintile of p_eff = p_Ru (1 − r)/u: 1.00, 0.98, 0.88, 0.68, 0.26.

In B the Ru wins come from five of the 56 catalysts: Ru/Ca(NH₂)₂, Ru/Ba–Ca(NH₂)₂, Ru/BaO–CaH₂, Ru/Cs/Ba/CCHT and
Ru/AC-G. Measured per gram of Ru, the Ru catalysts deliver a median 0.22 of the benchmark Ru activity at their
laboratory conditions (0.034 for those measured at ≥ 5 MPa), well below the u ≥ 11 the Fig. 2d mapping assumes.

The script calls the ACSA self-check gate first.
