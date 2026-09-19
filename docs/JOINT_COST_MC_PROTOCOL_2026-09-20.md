# Joint cost-parameter Monte Carlo protocol — 2026-09-20

**Status: FROZEN BEFORE OUTCOME READOUT.** This is a targeted robustness extension requested by the supervisor on 2026-09-20. It does not replace NH3-FINAL-1.1 or MEOH-D01-v3.

## Scientific question

How stable are the Fe-vs-Ru economic decision, the Ru activity parity target (alpha*), and the four-state MeOH ranking when cost-side parameters vary jointly?

This is a **scenario-envelope Monte Carlo**, not an empirical probability forecast of future commodity markets. The distributions below are stress-test distributions around the frozen models.

## NH3 draw definition

Draw count: **1000**  
Seed: **20260920**

Independent draws:

- Fe metal-price multiplier: Uniform(0.5, 1.5) applied to the frozen Fe price.
- Ru metal-price multiplier: Uniform(0.5, 1.5) applied to the frozen Ru price.
- common CAPEX multiplier: Uniform(0.8, 1.2), applied to the reactor base term, converter-shell pressure premium and compressor CAPEX.
- electricity price: Uniform(20, 100) USD/MWh.
- catalyst lifetime: Uniform(5, 20) years.

Rationale for the non-price bounds: the frozen Agent environment already declares electricity 20–100 USD/MWh and catalyst life 5–20 y as plausible ranges; the prior pressure-CAPEX audit used +/-20% capital-cost perturbations. The +/-50% metal-price multipliers are a deliberately broad symmetric stress envelope because the current frozen price table mixes catalyst-grade/market anchors and is not an empirical time-series model.

For every draw:

1. keep the frozen descriptor/kinetic model and 14,136-state process library unchanged;
2. reoptimize Fe and Ru over the full admissible process library under the sampled costs;
3. record whether C_Fe < C_Ru;
4. solve alpha* such that reoptimized Ru cost at the sampled cost parameters equals reoptimized Fe cost, using the canonical activity-multiplier definition.

Primary NH3 outputs:

- P(C_Fe < C_Ru);
- alpha* median, 5th–95th percentile, and full draw table;
- distributions of optimized T/P/Tsep and cost gap as supporting diagnostics.

## MeOH draw definition

The same supervisor request asks for the four-candidate rank-probability matrix. MEOH-D01-v3 excludes Re purchase price by design and does not currently contain a catalyst-lifetime replacement term. Therefore metal-price and lifetime uncertainty must **not** be silently injected into the MeOH model as new cost equations.

The formal MeOH extension will vary only cost coefficients that already exist in the frozen D01-v3 workbook unless a separate, explicit catalyst-cost extension is defined and audited. The rank-probability output must state exactly which sampled cost terms enter the workbook.

## Interpretation boundary

- Probabilities are conditional on this frozen stress envelope.
- They are not market forecasts.
- The separate Ru-price-equalization counterfactual is a causal stress test and is not part of the +/-50% price MC.
