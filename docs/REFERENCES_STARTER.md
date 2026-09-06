# Reference starter map

This repository page is a **writing scaffold**, not a complete bibliography. It records the reference categories that the manuscript needs so citations can be attached to the correct scientific claims instead of collected as an undifferentiated list.

## 1. Catalyst screening and descriptor-based discovery

Use references here to establish the standard paradigm that catalyst discovery often ranks materials by adsorption energies, scaling relations, volcano relationships and intrinsic kinetic proxies.

Relevant categories:

- adsorption-energy descriptors and Sabatier / volcano concepts;
- linear scaling relations in heterogeneous catalysis;
- descriptor-based catalyst screening;
- DFT-to-microkinetic catalyst discovery workflows.

**Manuscript role:** Introduction, first paragraph. These references define the atomic-scale baseline that the present work extends to industrial decision objectives.

## 2. Scaling relations and BEP closure

Use primary literature supporting the scaling and Brønsted-Evans-Polanyi relationships used in the ammonia model, together with the source from which the current S1-derived catalyst activity manifold is constructed.

**Manuscript role:** Methods and the backward-design / reachability section.

The important distinction is between:

- a mathematically arbitrary activity multiplier, and
- an improvement reachable through a physically admissible descriptor / scaling path.

## 3. Ammonia synthesis kinetics and catalyst activity

Use references that support:

- the ammonia synthesis mechanism and microkinetic representation;
- comparative transition-metal activity trends;
- the source data underlying the 15-metal activity screen;
- Fe, Ru and Os catalytic behavior where directly relevant.

**Manuscript role:** Methods, Figure 1 context, and validation of the activity model.

## 4. Reactor / process modeling for ammonia synthesis

Use references for:

- ammonia equilibrium and reactor modeling;
- loop pressure and temperature ranges;
- ammonia condensation / separation;
- recycle-loop process representations where applicable.

**Manuscript role:** Methods and Figure 4.

The current canonical model includes a 10-1000 bar pressure grid and pressure-dependent equipment CAPEX, so references should support the process equations and operating regime rather than merely historical industrial practice.

## 5. Chemical-process cost estimation

The current NH3-FINAL-1.1 implementation uses standard chemical-engineering cost correlations for pressure-dependent equipment.

Required reference categories:

- Turton-style bare-module equipment costing;
- vessel pressure factors;
- compressor cost correlations;
- CEPCI escalation;
- annualization / discounting assumptions where used.

**Manuscript role:** Methods and Supporting Information audit.

Where a correlation is applied outside its original fitting range or clipped to a minimum valid volume, state that explicitly in Methods / SI rather than hiding it in code.

## 6. Uncertainty propagation in catalysis

Use literature connecting uncertainty in DFT / adsorption energetics to kinetic uncertainty and catalyst screening.

Relevant themes:

- energetic uncertainty in computational catalysis;
- uncertainty propagation through microkinetic models;
- probabilistic catalyst ranking;
- sensitivity and uncertainty quantification in multiscale process models.

**Manuscript role:** Introduction and Results 3.2.

The present manuscript should distinguish itself by asking whether the uncertainty survives all the way to the **industrial decision**, rather than stopping at rate uncertainty.

## 7. Techno-economic analysis linked to catalyst properties

Use references that couple catalyst performance to reactor or process economics, especially studies that go beyond a fixed catalyst-cost penalty and explicitly reoptimize process conditions.

Relevant themes:

- catalyst-aware TEA;
- reactor / process optimization under catalyst-performance variation;
- catalyst lifetime, recovery and replacement cost;
- multiscale reaction-engineering economics.

**Manuscript role:** Introduction and Discussion.

The literature gap to establish is the limited availability of continuous, candidate-specific propagation from atomistic descriptor to optimized industrial ranking.

## 8. CO2-to-methanol recycle and selectivity economics

Use references supporting:

- CO2 hydrogenation to methanol;
- Re/TiO2 catalyst benchmark data if that remains the chosen case;
- recycle-loop behavior;
- methane / byproduct formation and purge losses;
- separation and compression costs.

**Manuscript role:** Results 3.4-3.5 and Methods.

The literature here should support the process pathway, while the leverage values in this project remain model outputs.

## 9. Value of information and decision-focused scientific computation

For the AI / agent component, use literature from decision theory and active learning rather than only generic LLM-agent references.

Relevant themes:

- value of information;
- Bayesian experimental design;
- active learning / acquisition functions;
- decision-focused learning;
- autonomous scientific discovery under finite budget;
- scientific-agent evaluation based on experimental or decision efficiency.

**Manuscript role:** Framework 2.3 and Results 3.6.

The conceptual link is that the agent should prioritize a calculation because it can change the downstream decision, not simply because the corresponding variable has high variance.

## 10. Scientific agents and autonomous laboratories

Use a small number of strong references that demonstrate:

- scientific agents using tools and external models;
- autonomous experimentation or closed-loop discovery;
- agent evaluation beyond generic QA accuracy;
- chemistry / materials examples where available.

**Manuscript role:** Introduction / Discussion around scaling the framework.

Avoid allowing this literature to dominate the paper. The agent is an enabling decision layer around the scientific model, not the primary source of physical results.

## Citation workflow

For each manuscript claim, classify a citation as one of:

1. **Model-source citation** — supports an equation, dataset or parameter used directly.
2. **Context citation** — establishes the state of the field.
3. **Validation citation** — provides an independent comparison point.
4. **Methodological analogy** — motivates a concept such as value of information.

This separation will make it easier to keep the final bibliography concise and defensible.
