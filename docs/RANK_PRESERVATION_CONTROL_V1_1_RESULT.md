# Rank-Preservation Control V1.1 — result

Status: **literature-calibrated physical rank-preservation control**  
Reaction: **CO oxidation on Au/TiO2**  
Candidate states: **2, 3, 4, 5 and 6 nm Au particle diameter**

## Literature-calibrated basis

V1.1 replaces the arbitrary positive downstream burden coefficients used in V1 with a fixed-condition reactor calculation anchored to published Au/TiO2 CO-oxidation data.

Absolute-rate anchor:

- reference Au diameter: **2.10 nm**
- Au loading: **4.40 wt%**
- measured dispersion: **38%**
- stabilized activity: **8.8 umol CO gcat^-1 s^-1**
- catalyst mass: **21.4 mg**
- condition: **273.15 K, 1 atm, 1% CO / 21% O2 / 78% Ar**
- flow: **214.4 Nml min^-1**
- literature-implied fixed conversion: **11.14%**

The nominal particle-size activity exponent is **0.9**, matched to the closest-loading literature series. Stronger reported exponents are retained as sensitivity bounds rather than fitted to the observed downstream ranking.

## Adjustment magnitude from V1

| Quantity | V1 | V1.1 | Change |
|---|---:|---:|---:|
| Reference particle diameter | 2.00 nm | 2.10 nm | **+5.0%** |
| Nominal TOF size exponent | 1.70 | 0.90 | **-47.1%** |
| Effective mass-activity exponent | 2.70 | 1.90 | **-29.6%** |
| 6 nm / 2 nm required-mass ratio | 19.42x | 8.064x | **-58.5%** |

Additional structural changes:

- normalized dispersion is replaced by the measured **38% at 2.10 nm**;
- arbitrary V1 coefficients `a`, `b`, `gamma` and `common` are removed;
- absolute catalyst activity, Au loading, catalyst mass, feed, flow, temperature and reactor diameter are literature anchored;
- no unsupported absolute USD values are introduced.

## Frozen V1.1 result

| Au diameter | Mass activity (umol CO gcat^-1 s^-1) | Required catalyst (mg) | Required Au (mg) | Burden vs best |
|---:|---:|---:|---:|---:|
| 2 nm | 9.6548 | 19.505 | 0.858 | **1.000x** |
| 3 nm | 4.4686 | 42.143 | 1.854 | **2.161x** |
| 4 nm | 2.5869 | 72.797 | 3.203 | **3.732x** |
| 5 nm | 1.6930 | 111.235 | 4.894 | **5.703x** |
| 6 nm | 1.1973 | 157.284 | 6.920 | **8.064x** |

Activity order:

`2 nm > 3 nm > 4 nm > 5 nm > 6 nm`

Downstream catalyst-burden order:

`2 nm > 3 nm > 4 nm > 5 nm > 6 nm`

Rank statistics:

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- Top-3 exact preservation = **PASS**
- 10,000/10,000 predefined literature-envelope draws preserve the full ranking
- all six frozen criteria = **PASS**

## Figure

The mirror rank-flow figure is:

[`../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg`](../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg)

It is deliberately constructed as the visual counterpart to an inversion plot: all candidate trajectories remain non-crossing after downstream propagation.

## Source data

Machine-readable V1.1 data:

[`../data/rank_preservation_control_v1_1.csv`](../data/rank_preservation_control_v1_1.csv)

## Interpretation

The literature recalibration materially weakens the predicted particle-size advantage—the 6 nm / 2 nm required-mass spread contracts by **58.5%**—yet the rank order remains exact. The result therefore does not depend on the arbitrary coefficients used in V1.

The valid manuscript claim is limited and specific:

> The multiscale implementation can preserve an upstream catalyst ordering when the catalyst-to-process mapping remains physically monotonic and does not activate a competing process-severity or topology penalty.

This control is not a full industrial TEA and should not be used to claim absolute process economics for Au/TiO2 CO oxidation.
