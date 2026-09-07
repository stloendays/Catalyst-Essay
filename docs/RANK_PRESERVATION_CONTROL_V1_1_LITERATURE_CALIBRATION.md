# Rank-Preservation Control V1.1 — literature calibration

Status: **literature-calibrated physical mapping**  
Reaction: **CO oxidation on Au/TiO2**

V1.1 preserves the original V1 methodological control but replaces its arbitrary positive downstream burden coefficients with a fixed-condition reactor calculation anchored to published Au/TiO2 CO-oxidation data. No parameter is fitted to an observed economic ranking.

## Absolute-rate anchor

Janssens et al., *Journal of Catalysis* **240** (2006) 108–113, DOI: `10.1016/j.jcat.2006.03.008`.

Values used:

- average Au diameter: **2.10 nm**
- Au loading: **4.40 wt%**
- measured dispersion: **38%**
- stabilized CO-oxidation activity after 10–15 h: **8.8 umol CO gcat^-1 s^-1**
- catalyst mass: **21.4 mg**
- condition: **273.15 K, 1 atm, 1% CO / 21% O2 / 78% Ar**
- Au/TiO2 flow: **214.4 Nml min^-1**
- quartz U-tube inner diameter: **2 mm**
- catalyst powder size: **125–300 um**

Using the pseudo-first-order plug-flow relation reported in the source, these values imply a fixed reference conversion of **11.14%**. This is derived from the literature experiment and is not manually chosen as a rank-preserving duty.

## Particle-size dependence

The nominal V1 exponent `n = 1.7` is replaced by **n = 0.9** because Overbury et al., *Journal of Catalysis* **241** (2006) 56–65, DOI `10.1016/j.jcat.2006.04.018`, report approximately `TOF ~ d^(-0.9 +/- 0.2)` for their **4.5 wt%** Au/TiO2 series, the closest loading match to the 4.40 wt% absolute-rate anchor.

The stronger literature trends (`n = 1.7` and approximately `n = 1.8`) are retained as secondary sensitivity bounds rather than used as the nominal mapping.

## Explicit adjustment magnitude relative to V1

| Quantity | V1 | V1.1 | Change |
|---|---:|---:|---:|
| reference diameter | 2.00 nm | 2.10 nm | **+5.0%** |
| nominal TOF size exponent | 1.70 | 0.90 | **-47.1%** |
| effective mass-activity exponent | 2.70 | 1.90 | **-29.6%** |
| 6 nm / 2 nm required-mass ratio | 19.42x | 8.064x | **-58.5%** |

Additional structural changes:

- V1 normalized dispersion is replaced by the measured **38% at 2.10 nm**;
- arbitrary V1 coefficients `a`, `b`, `gamma` and `common` are removed completely;
- absolute catalyst activity, Au loading, catalyst mass, feed, flow, temperature and reactor diameter are literature anchored;
- absolute USD is still not reported because the cited sources do not supply a process-scale replacement interval or an industrial reactor-CAPEX basis.

## V1.1 output

| Au diameter | Mass activity (umol CO gcat^-1 s^-1) | Required catalyst (mg) | Required Au (mg) | Burden vs best |
|---:|---:|---:|---:|---:|
| 2 nm | 9.6548 | 19.505 | 0.858 | 1.000x |
| 3 nm | 4.4686 | 42.143 | 1.854 | 2.161x |
| 4 nm | 2.5869 | 72.797 | 3.203 | 3.732x |
| 5 nm | 1.6930 | 111.235 | 4.894 | 5.703x |
| 6 nm | 1.1973 | 157.284 | 6.920 | 8.064x |

The activity order and downstream catalyst-burden order are both:

`2 nm > 3 nm > 4 nm > 5 nm > 6 nm`

with:

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- 10,000/10,000 predefined literature-envelope draws preserving the full ranking
- all six frozen criteria = **PASS**

## Interpretation

The literature calibration substantially compresses the predicted catalyst-burden spread, but it does not change the candidate ordering. The rank preservation therefore does not depend on the original arbitrary burden coefficients. It follows from the independently supported monotonic size–activity relation combined with a fixed process condition and a common Au/TiO2 composition.

This remains a rank-preservation control rather than a full industrial TEA. The supported claim is that the multiscale implementation can preserve an upstream ordering when no competing process-severity or topology penalty is introduced.

## Figure and source data

- Mirror rank-flow figure: [`../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg`](../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg)
- Machine-readable result: [`../data/rank_preservation_control_v1_1.csv`](../data/rank_preservation_control_v1_1.csv)
