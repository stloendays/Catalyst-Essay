# NH3-KINETIC-COST-v1

A working measured-kinetics / SI-cold-loop / equal-product economic integration,
stacked on PR #92. No archived scientific model, original manuscript or the
NH3-FINAL-1.2 32/64 benchmark is changed.

## Calculation chain

`Fe KM1 or promoted Ru/C rate -> isothermal bed integral -> SI two-flash recycle -> equal net NH3 production -> actual makeup, utilities, inventory and equipment cost -> candidate-specific optimum -> forward fixed-bed recycle verification`.

The grid search uses inverse reactor design: conversion is a design coordinate;
each catalyst's required bed is integrated using its own measured rate. Designs
at/beyond hot equilibrium or above the shared 90 m3 bed cap are excluded. The
selected bed is subsequently fixed and solved FORWARD inside the recycle
fixed point. That forward calculation takes NO prescribed conversion and is
initialized at 80% of the design feed. It predicts conversion and production.

## Sources and material bases

- Fe KM1: existing `analysis/nh3_staged_converter_2026_10_12/kinetics.py` and
  `parameters.yaml`, Dyson-Simon DOI 10.1021/i160028a013. Rate per m3 bed.
- Ru: Rossetti et al., DOI 10.1021/ie051398g, same repository implementation.
  Measured 3.2 wt% promoted Ru/C, bulk density 590 kg/m3. Original mol N2/L/h
  rate is multiplied by 2*1000/3600 to obtain mol NH3/m3/s. No FCAL, 11x
  dispersion adjustment or automatic 8 wt% loading extrapolation.
- Hot-side Newton-Cooper activities and Gillespie-Beattie equilibrium use
  atm, sharing the same thermodynamic driving force for Fe and Ru.
- Cold-side PR uses the uploaded Mace/Vrabec SI, Section 4/Table S27,
  DOI 10.1021/acs.jced.3c00327, through unchanged PR #92. Cold k(T) is NOT
  extrapolated into the hot reactor.
- Cost coefficients are inherited from the canonical manifest and existing
  lifecycle conventions: catalyst purchases at years 0/10/20, metal recovery
  at years 10/20/25, Fe 8 USD/kg catalyst, Ru 53852.5 USD/kg Ru, Ru/C
  support/fabrication 8 USD/kg catalyst. These are carried scenarios, not
  current commodity quotes.

CI checks the new rate implementation against existing source kinetics at nine
T/P points. A local standalone package lacking that upstream source module
skips only this reference check; the GitHub repository requires it to pass.

## Fair comparison

All intensive designs are scaled to 1500 t/d of actual NH3 component recovered
in both liquids, not to equal raw feed or total impure-liquid mass. The required
PFR volume scales with the flows. Nonlinear reactor/compressor capital is then
recomputed, not scaled from old cost-per-ton values.

Delivered makeup is charged ONCE. Engineering price scenarios: H2 2, N2 0.10,
CH4 0.20, Ar 0 USD/kg. The common stoichiometric-feed baseline is 437.338 USD/t.
Subtracting it gives the decision-relevant cost, with the same ordering as the
full modeled feed-plus-cost total. Purge and dissolved losses are diagnostic
parts of actual feed, not duplicate costs. Fresh compression is recalculated
at each design's delivery pressure instead of retaining 182 bar for a 100-bar
process. The boundary includes compression/cold2, inventory and reactor/pressure
shell/compressor capital; detailed heat integration and separator/HX/piping
capital remain outside it. No complete commercial-ammonia production cost is
claimed.

## Initial local engineering result

Common grid: P=100/160/188/220 bar; hot T=400/425/450 C; X=0.14/0.20/0.275/0.35;
cold2=0 C; purge=1.5/3%. 32 cold states all converged after computational retry;
192 catalyst-state designs, feasible Fe 34 and Ru 57. Runtime budget failures
were recorded as unresolved and retried at lower concurrency, not relabeled
physically impossible.

At 12% inventory annualization and 95.55% Ru recovery, both selected grid
states are 425 C, 220 bar, X=0.275 and purge=1.5%:

| Component | Fe | Ru/C |
|---|---:|---:|
| Bed volume, m3 | 81.584 | 24.419 |
| Excess-feed USD/t | 22.993 | 22.993 |
| Utilities USD/t | 14.943 | 14.943 |
| Inventory USD/t | 0.650 | 5.900 |
| Reactor/pressure-shell capital USD/t | 4.099 | 1.088 |
| Compressor capital USD/t | 4.560 | 4.560 |
| **Decision-relevant USD/t** | **47.245** | **49.484** |

Ru saves about 3.011 USD/t in reactor capital but adds about 5.250 USD/t in
inventory: a 2.239 USD/t disadvantage in this scenario. Independently forward
solved fixed beds each recover approximately 1500 t/d without input conversion.

Reoptimizing at zero inventory annualization gives Fe 47.024 and Ru 39.972 USD/t.
With equipment annualization held at 12%, the conditional grid crossover
inventory rate is about 7.010%. A uniform measured Ru/C rate multiplier reaches
grid parity at about 1.471x. This is NOT the manuscript's DFT descriptor/scaling
headroom or historical 114.67x target; the formulations and objectives differ.

## Interpretation limits relevant to the result

The two rate sources do not have a shared experimentally fitted pressure
interval: Fe KM1 149-309 atm and Ru/C 50-100 bar. Every row retains the domain
flag. Thus the common grid is a conditional engineering transfer/extrapolation;
the selected Ru state at 220 bar is not externally validated kinetics. The
Ru lambda=1 source ratio convention is retained as the recycled H2/N2 ratio
varies. No Os measured rate is fabricated.

The selected pressure and purge are grid edges, not a demonstrated global
optimum. This is an isothermal, prescribed-pressure-loss reactor/loop model,
not a detailed adiabatic multi-bed hydraulic simulation. Those extensions and
heat/pressure/economic sensitivity can change the numerical margins.

## Execution

```bash
python -m pip install numpy scipy pyyaml
python -m unittest discover -s analysis/nh3_kinetic_cost_coupling_v1 -p 'test_*.py' -v
python analysis/nh3_kinetic_cost_coupling_v1/run_study.py --out-dir artifacts/nh3-kinetic-cost
python analysis/nh3_kinetic_cost_coupling_v1/run_study.py --out-dir artifacts/nh3-kinetic-cost --retry-unresolved
```

Cold calculations use two bounded subprocess workers and checkpoint successful
and unresolved cases. `--batch-cold` supports time-limited local runtimes.
Outputs: REPORT.md, summary.json, candidate_grid.csv, finance_scenarios.csv,
H2_price_scenarios.csv, forward_checks.json and cold_cache.json. The workflow
checks that the full 32-state set completes and leaves upstream science intact.
