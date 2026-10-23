# Methanol: selectivity that changes with conversion when catalyst is loaded — preregistration (2026-10-23)

Committed before any count of this folder is made. Every count below is reported whatever its direction.

## Question

The manuscript's methanol headline (21 of 63 comparisons; `analysis/meoh_catalyst_level_2026_10_19`) lets each catalyst
load more catalyst and raise its single-pass conversion along X(m) = X_eq [1 − (1 − X0/X_eq)^m] up to 0.95 X_eq at its
**measured selectivities** (`verify_2026_10_12_s6_conversion/run_s6_conversion.evaluate`). Selectivity depends on contact
time: CO from reverse water-gas shift and methanol approach their equilibria at different rates. How does the count
change when the selectivity moves with conversion?

## Evidence on the direction (fixed before modelling)

`slopes.csv`: 23 sets in 9 papers of the pooled printed cohort in which one catalyst was measured at one T, P and H₂/CO₂
at two or more space velocities. Linear slope dS_MeOH/dX: 21 of 23 negative; quartiles −2.65, −0.93 (median), −0.065.

## Selectivity models for a raised state (X > X0)

S_CH4 stays at its measured value in every model (methane is kinetically controlled; it is absent from the equilibrium
system). Methanol takes the remaining share s = S_MeOH/(S_MeOH + S_CO), and CO the rest.

| Tag | Rule |
|---|---|
| constant | measured selectivities (manuscript; must reproduce 21/63) |
| equilibrium | s moves linearly in u = X/X_eq from its measured value at u0 to the equilibrium split s_eq at u = 1, where s_eq = ξ_MeOH/(ξ_MeOH + ξ_CO) of the simultaneous CO₂-hydrogenation + RWGS equilibrium of the laboratory feed at laboratory T and P (same root as X_eq, `run_conversion_sensitivity.equilibrium_roots`). With unlimited catalyst the outlet is at equilibrium, so the split must reach s_eq there. |
| slope_median | S_MeOH = S_MeOH,0 + b (X − X0), b = −0.926 (median slope), clipped to [0, 1 − S_CH4]; CO takes the change |
| slope_q1 / slope_q3 | the same with b = −2.649 and −0.0648 (quartiles) |

STY of a raised state scales with methanol made: STY = STY0 · X S_MeOH(X) / (X0 S_MeOH,0 m). Everything else (states, purge
grid, 6.86 % inlet limit, equilibrium admission, recycled-CO rule central, catalyst identity, leaders, bootstrap) is the
frozen code.

## Reported

Catalyst-level count (63 comparisons with ≥ 2 catalysts), > 5 %, papers and paper-bootstrap CI for every model; the
laboratory-conversion count (26/63) does not depend on the model and bounds the treatment from the other side.

## Gates

1. `constant` reproduces 21/63 (10 > 5 %) through the new code path.
2. s_eq lies in [0, 1] for every laboratory feed.
