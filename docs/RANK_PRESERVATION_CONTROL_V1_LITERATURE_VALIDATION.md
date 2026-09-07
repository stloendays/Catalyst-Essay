# Rank-Preservation Control V1 — Literature validation

Status: **pre-model literature validation**  
Reaction: **CO oxidation on Au/TiO2**  
Purpose: identify a catalyst-state series for which the upstream activity ordering is independently supported before any downstream economic propagation is evaluated.

## Scope

This control is intentionally narrow. It does **not** assert a universal particle-size law for all Au/TiO2 catalysts. It uses a controlled Au/TiO2 particle-size series for which multiple studies report the same monotonic activity direction over an overlapping size interval.

## Primary anchor A — powder Au/TiO2 in a flow reactor

Overbury, Schwartz, Mullins, Yan and Dai, *Journal of Catalysis* **241** (2006) 56–65, DOI: `10.1016/j.jcat.2006.04.018`.

Relevant facts reported by the paper:

- Au/TiO2 (P25) catalysts were studied in a flow reactor.
- Au particle size was varied by sequential thermal treatment of the same catalyst, reducing confounding from support type, synthesis route, Au loading and incidental impurities within a series.
- Mean Au particle sizes were in the approximately **2–10 nm** range.
- At **298 K**, TOF decreased monotonically with increasing particle diameter.
- Reported scaling was approximately `TOF ~ d^(-1.7 +/- 0.2)` for the 7.2 wt% Au/TiO2 series and `TOF ~ d^(-0.9 +/- 0.2)` for the 4.5 wt% series.

The 4.5 wt% series later becomes the nominal V1.1 particle-size anchor because it is the closest loading match to the 4.40 wt% absolute-rate calibration.

## Independent anchor B — model planar Au/TiO2 library

Emmanuel, Hayden and Saleh-Subaie, *Journal of Catalysis* **369** (2019) 175–180, DOI: `10.1016/j.jcat.2018.10.038`.

Relevant facts reported by the paper:

- Au/TiO2 particle diameters span approximately **1.5–6 nm**.
- CO oxidation was studied at **80 C and 170 C**, at total pressures from approximately **0.06 to 1.5 mbar**, and with multiple O2:CO ratios.
- Under all reported conditions, TOF increased monotonically as Au particle diameter decreased.
- The reported trend was approximately `TOF ~ d^(-1.8)`.

This paper provides independent confirmation that the monotonic direction is not unique to one temperature or one O2:CO ratio in the model-catalyst system.

## Boundary evidence — why the control must remain series-specific

Other Au/TiO2 preparations do not always produce the same simple size trend. For example, a 2014 *Journal of Physical Chemistry C* study (DOI: `10.1021/jp504681f`) reported a catalyst with a mean Au particle size near **3.8 nm** as the most active member of its own preparation series.

That observation is not treated as a contradiction to the control. It demonstrates that support state, preparation route, Au loading, interface structure and other variables can change the observed size–activity relationship. Therefore:

> **V1/V1.1 is a controlled-series rank-preservation test, not a universal statement about Au/TiO2 chemistry.**

## Frozen candidate interval

To remain inside the overlap of the two monotonic literature anchors, the control uses:

`d = 2, 3, 4, 5, 6 nm`

These are representative benchmark states sampled from the experimentally supported overlap interval. They are not claimed to reproduce the exact specimen list of either source paper.

## V1 relative upstream model

The original V1 nominal relation was:

`TOF_rel(d) = (d / 2 nm)^(-1.7)`

with literature sensitivity checks at the weaker 4.5 wt% slope and the independent planar-model slope.

## V1.1 calibration decision

V1.1 preserves the candidate set and control logic but replaces the nominal `1.7` slope with **0.9**, matching the closest-loading powder series to the **4.40 wt%** absolute-rate anchor used in the physical mapping. The stronger literature exponents remain sensitivity bounds.

The full calibration and its adjustment magnitude are documented in [`RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md`](RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md).

## Decision

**PASS for a controlled rank-preservation test.**

The literature supports a fixed-condition test in which:

1. the active element and support remain unchanged across candidate states;
2. the upstream activity direction is independently constrained before downstream propagation;
3. temperature, pressure, feed composition and process topology are held externally fixed;
4. catalyst inventory and reactor burden respond to productivity;
5. the current claim is rank preservation under this controlled mapping, not a universal industrial-economic law.
