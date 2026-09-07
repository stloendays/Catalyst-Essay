# Rank-Preservation Control V1.1 — result

Status: **GitHub Actions PASS**  
Workflow run: `34086221856`  
Frozen version: `RANK-PRESERVATION-CONTROL-V1.1`

## Result

V1.1 replaced the arbitrary positive burden coefficients used in V1 with a literature-anchored fixed-condition reactor calculation. The candidate order remained unchanged after this calibration.

### Literature-implied operating target

The physical reference state uses the Au/TiO2 experiment of Janssens et al., *Journal of Catalysis* 240 (2006) 108-113, DOI `10.1016/j.jcat.2006.03.008`:

- 2.10 nm average Au diameter;
- 4.40 wt% Au;
- 38% Au dispersion;
- stabilized activity 8.8 umol CO gcat^-1 s^-1;
- 21.4 mg catalyst;
- 273.15 K and approximately 1 atm;
- 1% CO / 21% O2 / 78% Ar;
- 214.4 Nml min^-1 reaction flow.

Using the pseudo-first-order plug-flow relation reported in the paper gives a reference conversion of **11.14%**. This conversion was derived from the source experiment rather than selected as a free parameter.

## Calibration magnitude relative to V1

| Quantity | V1 | V1.1 | Change |
|---|---:|---:|---:|
| reference particle size | 2.00 nm | 2.10 nm | **+5.0%** |
| nominal TOF size exponent | 1.70 | 0.90 | **-47.1%** |
| effective mass-activity exponent | 2.70 | 1.90 | **-29.6%** |
| nominal 6 nm / 2 nm required-mass ratio | 19.42x | 8.064x | **-58.5%** |

The nominal TOF exponent was changed to **0.9** because Overbury et al., *Journal of Catalysis* 241 (2006) 56-65, DOI `10.1016/j.jcat.2006.04.018`, report `TOF ~ d^(-0.9 +/- 0.2)` for a 4.5 wt% Au/TiO2 series, which is the closest loading match to the 4.40 wt% absolute-rate anchor. The stronger reported size exponents are retained only as sensitivity bounds.

Additional changes:

- normalized dispersion -> measured **38% at 2.10 nm**;
- relative activity scale -> **8.8 umol CO gcat^-1 s^-1** absolute reference activity;
- no physical catalyst inventory -> **21.4 mg** reference catalyst mass;
- unspecified composition -> **4.40 wt% Au**;
- arbitrary burden coefficients `a`, `b`, `gamma`, `common` -> **removed completely**.

## Physical propagation result

| Au diameter | Mass activity (umol CO gcat^-1 s^-1) | Required catalyst (mg) | Required Au (mg) | Burden vs best |
|---:|---:|---:|---:|---:|
| 2 nm | 9.6548 | 19.505 | 0.858 | 1.000x |
| 3 nm | 4.4686 | 42.143 | 1.854 | 2.161x |
| 4 nm | 2.5869 | 72.797 | 3.203 | 3.732x |
| 5 nm | 1.6930 | 111.235 | 4.894 | 5.703x |
| 6 nm | 1.1973 | 157.284 | 6.920 | 8.064x |

Activity ranking:

`2 nm > 3 nm > 4 nm > 5 nm > 6 nm`

Catalyst-procurement / packing-burden ranking, best to worst:

`2 nm > 3 nm > 4 nm > 5 nm > 6 nm`

Rank statistics:

- Spearman rho = **1.000**;
- Kendall tau = **1.000**;
- pairwise inversions = **0**;
- Top-3 exact preservation = **PASS**.

## Literature-envelope robustness

Across **10,000** draws spanning:

- TOF size exponent `0.7-2.0`;
- dispersion exponent `0.8-1.2`;

exact full-rank preservation was **1.0000**, with minimum Spearman rho = **1.000**.

All six preregistered criteria passed.

## Scientific interpretation

The calibration changes the magnitude substantially: the predicted 6 nm / 2 nm catalyst-mass penalty contracts by about **58.5%**, from 19.42x to 8.064x. Despite that compression, the ordering is unchanged.

This is the useful control result. Rank preservation is not being obtained from the original arbitrary economic weights; those weights have been removed. Instead, the preserved order follows from an independently supported monotonic Au-size/activity relation propagated through a fixed-condition reactor duty with common Au/TiO2 composition.

The result should be described as a **literature-calibrated physical rank-preservation control**, not as a full industrial TEA. Absolute USD values are not reported because the cited sources do not provide a process-scale catalyst replacement interval or a reactor CAPEX basis.
