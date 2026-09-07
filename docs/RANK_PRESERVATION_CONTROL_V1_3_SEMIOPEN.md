# Rank-Preservation Control V1.3 — semi-open operating-condition test

Status: **exploratory robustness extension; V1.1 remains frozen/canonical**  
Reaction: **CO oxidation on Au/TiO2**

## Why this test exists

V1.1 is a deliberately strict falsification control: chemistry, topology and operating condition are fixed, so the literature-calibrated monotonic size–activity relation propagates directly into the catalyst-burden ranking. V1.2 relaxed the downstream mapping with an abstract independent multiplier.

V1.3 asks a more physical intermediate question:

> If the catalyst chemistry and process topology remain common, but each particle-size state is allowed to choose its own low-temperature operating point, does the 2–6 nm ranking still mostly survive?

The answer is **yes over the primary literature-supported kinetic window, and still mostly yes under a wider sensitivity window**. The result is therefore useful as robustness evidence, but it is not promoted to the canonical control because the process-penalty weights are generic monotone penalties rather than an industrial TEA.

## Literature constraints

The test is anchored to four independent pieces of evidence.

1. **V1.1 absolute-rate baseline** — Janssens et al., *Journal of Catalysis* 240 (2006) 108–113, DOI `10.1016/j.jcat.2006.03.008`: 2.10 nm Au/TiO2, 4.40 wt% Au, 273.15 K, 1% CO / 21% O2 / 78% Ar.
2. **Size-dependent temperature response** — Shao et al., *Small Methods* 2 (2018) 1800273, DOI `10.1002/smtd.201800273`: apparent activation energies 25.4, 28.0 and 33.7 kJ/mol for 2.2, 3.4 and 4.8 nm Au/TiO2, measured over 253–293 K. The experiment used 1% CO / 20% O2 / 79% He at 20,000 mL gcat^-1 h^-1.
3. **Feed-pressure response** — Diemant et al., *ChemPhysChem* 22 (2021) 542–552, DOI `10.1002/cphc.202000960`, together with the low-temperature powder studies summarized there: CO and O2 reaction orders vary substantially with condition/preparation, so V1.3 samples broad low-temperature bounds rather than fixing one kinetic order.
4. **Cross-condition rank direction** — Emmanuel et al., *Journal of Catalysis* 369 (2019) 175–180, DOI `10.1016/j.jcat.2018.10.038`: over ca. 1.5–6 nm Au/TiO2, the smaller-particle TOF advantage remains monotonic at 80 and 170 C, pressures from about 0.06 to 1.5 mbar, and multiple O2:CO ratios. This is independent evidence that rank preservation is not unique to one single operating point.

## What is free and what is not

### Free per candidate

Each 2, 3, 4, 5 and 6 nm state independently searches:

- reaction temperature;
- O2/CO feed ratio;
- the associated catalyst inventory / residence-time requirement.

Primary temperature window: **273.15–293.15 K**.  
Wider sensitivity window: **273.15–313.15 K**.  
O2/CO window: **1–21**.

### Why space velocity is not added as an independent third knob

At fixed feed duty and target conversion, required catalyst mass/reactor volume and space velocity are two representations of the same residence-time degree of freedom. Treating catalyst mass and GHSV as independently optimizable would double-count residence time. In V1.3, lower required catalyst mass corresponds directly to a higher achievable space velocity at fixed duty.

Thus the test is less fixed than V1.1 without creating an artificial extra degree of freedom.

## Semi-open objective family

For every candidate the model searches the operating grid and minimizes

`J = m_required / m_ref + w_T H(T) + w_R O(O2/CO)`

where:

- `m_required` is the catalyst mass required by the literature-anchored activity model;
- `H(T)` is a monotone temperature/heating penalty;
- `O(O2/CO)` is a monotone oxidant-excess penalty;
- `w_T` and `w_R` are sampled independently over a broad log-uniform range.

The weights are **not fitted to preserve ranking** and are not presented as absolute process costs. They simply prevent the optimization from collapsing to “always choose the highest temperature and most favorable feed composition.”

## Candidate-specific kinetic freedom

Three stress levels were tested. Each draw also samples the common reaction orders and the two process-penalty weights.

| stress | independent activity-prefactor CV | independent Ea perturbation |
|---|---:|---:|
| mild | 5% | 1 kJ/mol |
| moderate | 10% | 2 kJ/mol |
| strong | 20% | 3 kJ/mol |

This freedom is deliberately candidate-specific: a weaker particle-size state can receive a favorable kinetic perturbation and a stronger state an unfavorable one.

## Results — primary 273–293 K window

10,000 seeded optimization draws per stress level:

| stress | exact full order preserved | mean Spearman rho | fraction rho >= 0.9 | mean pairwise inversions |
|---|---:|---:|---:|---:|
| mild | **99.90%** | **0.99990** | **100.00%** | 0.0010 |
| moderate | **92.16%** | **0.99214** | **99.98%** | 0.0786 |
| strong | **64.29%** | **0.95689** | **95.95%** | 0.4032 |

The moderate case is the most useful interpretation. The operating point is no longer fixed, the candidate kinetics are no longer identical apart from particle size, and exact ordering is allowed to fail. Even so, **99.98% of draws retain rho >= 0.9**, while the mean rho is **0.992**.

## Wider 273–313 K sensitivity

The wider window intentionally extends beyond the Shao 253–293 K activation-energy fit and should therefore be read as a stress sensitivity, not as the primary result.

| stress | exact full order preserved | mean Spearman rho | fraction rho >= 0.9 | mean pairwise inversions |
|---|---:|---:|---:|---:|
| mild | **95.11%** | **0.99511** | **100.00%** | 0.0489 |
| moderate | **72.62%** | **0.96802** | **97.56%** | 0.3012 |
| strong | **43.06%** | **0.90723** | **83.22%** | 0.7816 |

This is the behavior sought from a less constrained control: the ranking is no longer artificially forced to be identical, but under moderate freedom it remains strongly ordered. Weak reshuffling occurs first among neighboring, lower-ranked states rather than as a systematic reversal of the decision frontier.

## Decision

**Keep V1.3 as a supporting robustness extension. Do not replace V1.1 as the canonical control yet.**

The useful manuscript-level interpretation, if this sensitivity is eventually used, is:

> **Rank preservation does not require a perfectly fixed operating point. Within a literature-constrained low-temperature operating envelope, moderate candidate-specific kinetic and operating freedom produces occasional local reshuffling but preserves the overall Au/TiO2 particle-size ranking with very high rank correlation.**

This is stronger than claiming preservation only under a single fixed condition, while avoiding the opposite mistake of constructing a new full industrial TEA without sufficient process data.

## Reproducibility

- canonical baseline: `data/rank_preservation_control_v1_1.csv`
- V1.3 script: `data/rank_preservation_semiopen_v1_3.py`
- V1.3 summary: `data/rank_preservation_semiopen_v1_3_summary.csv`
- draws: 10,000 per window × stress level
- primary seeds: 20260908 / 20260909 / 20260910 by stress offset
- wider-window seeds: 20260909 / 20260910 / 20260911 by stress offset
