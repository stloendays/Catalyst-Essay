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
| measured Ru activity (variant B) | one of the 54 measured Ru catalysts per draw (56 before the PR #28 errata): effective descriptor, residual multiplier, Ru content | `analysis/nh3_supported_2026_10_06` |

## Results

Rerun on 2026-10-07 on the corrected `supported_candidates.csv` of PR #28 (Humphreys 2021 errata: 54 Ru catalysts
instead of 56, Ru/BaTiO2.5H0.5 at 0.86 wt%, corrected space velocities), same seeds. The base reproduction still gives
P(Fe cheaper) = 1.000 and minimum gap 2.382 USD/t. Variants A and the preregistered row do not use the measured table and
are unchanged to the last digit.

| Variant | P(Fe cheaper) | before PR #28 errata | Ru − Fe, median (USD/t) | before PR #28 errata |
|---|---:|---:|---:|---:|
| preregistered, pure-Ru benchmark | 1.000 | 1.000 | 7.11 (reproduced) | 7.11 |
| A: u and r, benchmark bed volume (Fig. 2d mapping) | 0.240 | 0.240 | −0.31 | −0.31 |
| A_bed: u and r, supported bed (own Ru content and density) | 0.800 | 0.804 | +0.37 | +0.40 |
| B: measured Ru catalysts, with recovery | 0.946 | 0.949 | +4.36 | +4.54 |
| B0: measured Ru catalysts, no recovery | 0.989 | 0.989 | +7.41 | +7.71 |

Where Ru wins in A_bed (P(Ru wins) given the condition; u and r terciles are unchanged, u < 18.2, u ≥ 30.4, r ≥ 0.927):

| Condition | P(Ru wins) | before PR #28 errata |
|---|---:|---:|
| all draws | 0.200 | 0.196 |
| u in its lowest tercile | 1.3 % | 1.3 % |
| u and r both in their top terciles | 50 % (0.498) | 49 % (0.491) |
| Ru content < 2.5 wt% | 0.5 % (0.0046) | 0.6 % (0.0065) |
| Ru content ≥ 5 wt% | 39 % (0.393) | 39 % (0.387) |

Within 90–94 % the recovery matters little. In A the benchmark bed volume removes the dilution penalty of a supported
bed, and Ru wins in 76 % of draws; P(Ru wins) by quintile of p_eff = p_Ru (1 − r)/u: 1.00, 0.98, 0.88, 0.68, 0.26
(unchanged).

In B the Ru wins come from five of the 54 catalysts (five of 56 before), the same five: Ru/Ca(NH₂)₂, Ru/Ba–Ca(NH₂)₂,
Ru/BaO–CaH₂, Ru/Cs/Ba/CCHT and Ru/AC-G. Measured per gram of Ru, the Ru catalysts deliver a median 0.22 of the
benchmark Ru activity at their laboratory conditions (0.220; 0.216 before), and 0.060 for the 11 measured at ≥ 5 MPa
(0.034 for 13 before), well below the u ≥ 11 the Fig. 2d mapping assumes.

Judgement calls in the rerun: the A_bed "where Ru wins" shares and the per-gram activity medians are not written by the
script; they are recomputed from `draws.csv` and from the `alpha` column of `supported_candidates.csv` (primary Ru rows
with a cost), with the definitions that reproduce the pre-errata values exactly. `agent/selfcheck_report.json`, which the
gate rewrites with a new timestamp only, is left at its committed version. Manuscript numbers affected:
`ERRATA_RERUN_2026-10-07.md`.

The script calls the ACSA self-check gate first.
