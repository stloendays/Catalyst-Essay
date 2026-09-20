# Supervisor cost-side Monte Carlo preregistration — 2026-09-20

**Status: frozen before outcome calculation.** This file defines the primary NH3 cost-side Monte Carlo requested by the supervisor on 2026-09-20. It does not alter NH3-FINAL-1.1 descriptor uncertainty or the canonical model.

## Scope

The analysis isolates uncertainty in economic parameters while holding the frozen NH3-FINAL-1.1 catalyst descriptors, microkinetics, process-state library, engineering constraints and pressure-CAPEX equations unchanged.

Each draw reoptimizes Fe and Ru over the full 14,136-state process library. The Ru activity parity multiplier alpha* is then recomputed against that draw's reoptimized Fe cost, with Ru reoptimized at every activity multiplier.

## Primary prior

- draws: **5,000**
- seed: **20260920**
- parameter dependence: independent across the four uncertainty sources below, except that CAPEX, electricity and lifetime are shared between Fe and Ru within a draw.
- Fe and Ru metal-price multipliers are sampled independently.

### 1. Metal purchase price

For each metal independently:

`log(price_multiplier) ~ Uniform(log(0.5), log(2.0))`

This is a bounded multiplicative uncertainty range, not a market forecast. Baseline prices remain Fe = 8 USD/kg and Ru = 53,852.5 USD/kg.

### 2. CAPEX coefficient

One common multiplier per draw:

`capex_multiplier ~ Uniform(0.8, 1.2)`

It multiplies all capital pools in the reduced NH3 boundary: reactor-volume base, converter-shell pressure premium and compressor CAPEX. The band matches the existing +/-20% capital-cost sensitivity scale used in the FINAL-1.1 audit.

### 3. Electricity price

One common value per draw:

`electricity_USD_MWh ~ Uniform(20, 100)`

It rescales fresh-feed compression, recycle compression and refrigeration electricity linearly. Compressor CAPEX is not rescaled by electricity price because it is sized from physical compressor duty.

### 4. Catalyst lifetime

One common value per draw:

`catalyst_life_y ~ Uniform(5, 20)`

It affects active-metal replacement cost only, consistent with the implemented NH3 cost equation.

## Outputs fixed in advance

1. **P(C_Fe < C_Ru)** after full per-draw process reoptimization.
2. **alpha*** distribution, where alpha* is the intrinsic Ru activity multiplier at which reoptimized Ru cost equals the same draw's reoptimized Fe cost.
3. Fe and Ru cost quantiles and the frequency of process-optimum states, for interpretation only.
4. The complete draw-level table, including sampled parameters and optimized costs, retained as provenance.

Report alpha* with at least p05, median and p95 and the fraction of draws, if any, in which Ru is already at or below Fe at alpha = 1.

## Interpretation rule

The probability is conditional on the bounded prior above and must not be described as a market-frequency forecast. The equal-price counterfactual is a separate causal diagnostic and is not part of the Monte Carlo prior.

## MeOH note

MEOH-D01-v3 currently excludes Re purchase price and catalyst lifetime from the canonical NPC boundary. The requested four-candidate MeOH rank-probability calculation therefore requires an explicit supervisor-requested boundary extension or an analysis restricted to the cost parameters already present in D01 v3. That extension will be frozen separately after the workbook accounting structure is audited.
