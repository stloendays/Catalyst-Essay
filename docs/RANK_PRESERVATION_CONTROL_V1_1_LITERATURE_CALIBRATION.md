# Rank-Preservation Control V1.1 — literature calibration addendum

Status: **frozen before the V1.1 workflow run**  
Reaction: **CO oxidation on Au/TiO2**  
Purpose: replace V1's arbitrary relative downstream coefficients with a literature-anchored fixed-condition physical mapping while preserving the original control question.

## Why V1.1 exists

V1 established that a monotonic downstream mapping does not intrinsically create ranking inversion, but it used a relative activity normalization and arbitrary positive burden coefficients. V1.1 removes those free burden coefficients and anchors the calculation to a published Au/TiO2 flow-reactor experiment.

V1 itself is not edited or reinterpreted. V1.1 is a separate calibration layer.

## Absolute flow-reactor anchor

Primary physical anchor:

T. V. W. Janssens, A. Carlsson, A. Puig-Molina and B. S. Clausen, *Journal of Catalysis* **240** (2006) 108-113. DOI: `10.1016/j.jcat.2006.03.008`.

Values taken directly from that study for Au/TiO2:

- average Au particle diameter: **2.10 nm**;
- Au content: **4.40 wt%**;
- Au dispersion: **38%**;
- stabilized CO oxidation activity after 10-15 h on stream: **8.8 umol CO gcat^-1 s^-1**;
- catalyst mass: **21.4 mg**;
- quartz U-tube inner diameter: **2 mm**;
- catalyst powder size: **125-300 um**;
- reaction temperature: **0 C (273.15 K)**;
- reaction pressure: approximately **1 atm**;
- feed: **1% CO / 21% O2 / 78% Ar**;
- Au/TiO2 reaction flow at 0 C: **214.4 Nml min^-1**;
- activation before the low-temperature test: **400 C for 1 h**, with the same gas composition at **42 Nml min^-1**.

The paper evaluates the stabilized state because the Au/TiO2 catalyst deactivates during the first hours and reaches a nearly stable activity after roughly 10-15 h.

Using the paper's own pseudo-first-order plug-flow relation, the reported stabilized activity, catalyst mass, feed and reaction flow imply a reference conversion of about **11.1%**. V1.1 freezes that literature-implied conversion as the treatment duty. It is not selected to produce a desired ordering.

## Size-activity relation

Primary size-effect source:

S. H. Overbury, V. Schwartz, D. R. Mullins, W. Yan and S. Dai, *Journal of Catalysis* **241** (2006) 56-65. DOI: `10.1016/j.jcat.2006.04.018`.

The study reports at 298 K:

- `TOF ~ d^(-1.7 +/- 0.2)` for 7.2 wt% Au/TiO2;
- `TOF ~ d^(-0.9 +/- 0.2)` for 4.5 wt% Au/TiO2.

Because the absolute flow-reactor anchor above contains **4.40 wt% Au**, V1.1 changes the nominal TOF exponent from V1's **1.7** to **0.9**. This is a loading-matched literature choice, not a fit to the downstream ranking.

A second independent Au/TiO2 model-catalyst study, *Journal of Catalysis* **369** (2019) 175-180, DOI `10.1016/j.jcat.2018.10.038`, reports a monotonic increase in TOF with decreasing Au diameter from roughly 1.5 to 6 nm, with an exponent of about **1.8**. V1.1 therefore retains the stronger exponents as secondary sensitivity bounds.

## Physical propagation used in V1.1

The candidate set remains:

`2, 3, 4, 5, 6 nm`

For a candidate diameter `d`:

1. intrinsic TOF is scaled by the literature relation `TOF ~ d^-n`;
2. exposed Au fraction is scaled geometrically as approximately `1/d`, anchored to the measured **38% dispersion at 2.10 nm**;
3. because Au loading, support, feed, temperature, pressure and target conversion are fixed, the mass-specific CO oxidation rate determines the required catalyst mass through the same pseudo-first-order plug-flow equation used in the source paper;
4. the relative catalyst procurement burden is proportional to required catalyst mass because all candidates have the same Au/TiO2 composition and therefore the same unit-cost basis;
5. reactor packing burden is reported separately and scales with catalyst mass under the fixed powder and tube geometry.

No arbitrary weighting between catalyst and reactor terms is introduced. No absolute USD value is reported.

## Explicit adjustment magnitude relative to V1

| Quantity | V1 | V1.1 | Change |
|---|---:|---:|---:|
| reference particle size | 2.00 nm | 2.10 nm | **+5.0%** |
| nominal TOF size exponent | 1.70 | 0.90 | **-47.1%** |
| nominal effective mass-activity exponent (`TOF + dispersion`) | 2.70 | 1.90 | **-29.6%** |
| nominal 6 nm / 2 nm required-mass ratio | 19.42x | 8.06x | **-58.5%** |
| dispersion normalization | relative 1.0 | measured 0.38 at 2.10 nm | absolute physical anchor added |

Additional changes that are dimensional rather than percentage corrections:

- relative activity normalization -> **8.8 umol CO gcat^-1 s^-1** at the 2.10 nm reference state;
- no physical catalyst mass -> **21.4 mg** reference mass;
- no explicit composition -> **4.40 wt% Au**;
- abstract fixed-condition treatment -> **273.15 K, 1 atm, 1% CO / 21% O2 / 78% Ar, 214.4 Nml min^-1**;
- arbitrary positive economic coefficients -> **removed completely**.

The calibration is therefore expected to compress the magnitude of the size advantage substantially. The scientific check is whether the ranking itself survives that compression.

## Frozen pass criteria

The V1 pass/fail logic is retained:

1. activity winner = lowest-burden winner;
2. full-set Spearman rho >= 0.95;
3. Kendall tau >= 0.90;
4. zero pairwise inversions;
5. exact Top-3 preservation;
6. >= 95% full-rank preservation across the predefined literature/geometry sensitivity envelope.

## Interpretation boundary

A successful V1.1 is evidence for a **physical rank-preservation control**, not a full industrial TEA. It supports the methodological statement that the multiscale implementation does not intrinsically destroy an upstream catalyst ordering when the downstream relationship remains monotonic.
