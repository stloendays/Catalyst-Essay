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

This is the primary anchor for the V1 control because it supplies a powder catalyst, flow-reactor measurement, an explicit common-condition activity relation and a within-series strategy that minimizes preparation confounding.

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

> **V1 is a controlled-series rank-preservation test, not a universal statement about Au/TiO2 chemistry.**

## Frozen candidate interval

To remain inside the overlap of the two monotonic literature anchors, V1 uses the following representative catalyst states:

`d = 2, 3, 4, 5, 6 nm`

These are benchmark states sampled from the experimentally supported overlap interval. They are not claimed to reproduce the exact specimen list of either source paper.

## Upstream activity model to freeze

Nominal intrinsic activity is represented only as a **relative** literature-anchored proxy:

`TOF_rel(d) = (d / 2 nm)^(-n)`

with:

- nominal `n = 1.7`;
- common-series uncertainty `n = 1.7 +/- 0.2` for the primary anchor;
- secondary sensitivity checks at `n = 0.9 +/- 0.2` and `n = 1.8`.

No absolute TOF, absolute conversion, reactor productivity or USD value will be invented from the power law.

## Decision

**PASS for a methodological rank-preservation control.**

The literature supports a preregistered fixed-condition test in which:

1. the active element and support remain unchanged across candidate states;
2. the upstream activity direction is independently constrained before economics are evaluated;
3. temperature, pressure, feed composition and process topology are held externally fixed;
4. catalyst inventory and reactor burden are allowed to respond monotonically to productivity;
5. the output is a **relative economic ranking / cost index**, not an industrial absolute TEA.

This control can test whether the multiscale framework preserves ranking when the downstream mapping is intentionally free of competing process-severity, recycle or separation penalties.
