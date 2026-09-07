# Rank-Preservation Control V1.2 — partial-relaxation stress test

Status: **exploratory robustness extension; V1.1 remains frozen and canonical**  
Reaction: **CO oxidation on Au/TiO2**

## Question

V1.1 holds temperature, pressure, feed composition and process topology fixed. This is useful as a falsification control, but it is intentionally restrictive. The present test asks a narrower question:

> If we stop fixing every downstream consequence and allow each candidate a moderate candidate-specific process/equipment advantage or penalty, does the Au/TiO2 ordering still mostly survive?

This is a robustness test, not a new industrial TEA. No parameter is fitted to obtain rank preservation.

## What is still common

The catalyst chemistry and candidate definition remain the same controlled Au/TiO2 particle-size series (2, 3, 4, 5 and 6 nm). The V1.1 literature-calibrated activity and required-catalyst-mass values are retained as the physical baseline. The process topology remains common.

The literature basis also supports a monotonic size-activity direction over more than one operating condition: the powder series is monotonic at 298 K, while an independent planar Au/TiO2 study reports the same direction at 80 and 170 C, over multiple O2:CO ratios and pressures. This does not by itself supply an industrial cost model, but it argues against rank preservation being unique to one single laboratory condition.

## What is relaxed

Instead of forcing identical downstream burden for a given catalyst mass, each candidate receives an independent multiplicative downstream factor

`B_i,relaxed = B_i,V1.1 * f_i`

with

`f_i ~ Uniform(1-delta, 1+delta)`.

The factor represents unresolved candidate-specific operating or equipment effects after relaxing the fixed-condition assumption. It is deliberately independent across candidates and is not correlated with activity, so it can favor a weaker candidate or penalize a stronger one. This makes the test more permissive than a shared process perturbation.

Because this factor is an abstract robustness envelope rather than a literature-derived process model, delta should be interpreted as **stress-test magnitude**, not as a physically measured uncertainty.

## Analytical robustness margin

The V1.1 required catalyst masses are:

`19.505, 42.143, 72.797, 111.235, 157.284 mg`

for 2, 3, 4, 5 and 6 nm, respectively.

For arbitrary independent factors within +/-delta, full ordering is guaranteed only if every adjacent pair remains separated in the worst case. The limiting pair is 5 versus 6 nm, which gives

`delta < 0.17149`.

Thus **up to approximately +/-17.1% candidate-specific downstream variation, the full 2 > 3 > 4 > 5 > 6 ordering is mathematically guaranteed**, without requiring identical process burden across candidates.

## Monte Carlo partial-relaxation sweep

100,000 seeded draws were run at each delta. Rank 1 corresponds to the lowest downstream burden.

| candidate-specific envelope | full ranking preserved | mean Spearman rho | rho >= 0.9 | mean pairwise inversions | <=1 inversion |
|---:|---:|---:|---:|---:|---:|
| +/-10% | 100.0% | 1.0000 | 100.0% | 0.000 | 100.0% |
| +/-15% | 100.0% | 1.0000 | 100.0% | 0.000 | 100.0% |
| +/-17% | 100.0% | 1.0000 | 100.0% | 0.000 | 100.0% |
| +/-20% | 98.971% | 0.99897 | 100.0% | 0.010 | 100.0% |
| +/-25% | 93.492% | 0.99349 | 100.0% | 0.065 | 100.0% |
| +/-30% | 85.021% | 0.98496 | 99.942% | 0.150 | 99.942% |
| +/-40% | 66.164% | 0.96422 | 98.465% | 0.354 | 98.465% |

At **+/-25%**, the exact full order is still retained in about **93.5%** of draws; when it changes, the observed change is at most one pairwise inversion. At **+/-30%**, exact full preservation falls to about **85.0%**, but the ranking remains strongly correlated with the upstream order (mean rho approximately **0.985**) and more than **99.9%** of draws have at most one inversion.

## Interpretation

This gives a useful intermediate control between two extremes:

- **V1.1:** fully fixed-condition monotonic mapping -> exact rank preservation.
- **V1.2 stress test:** allow moderate independent candidate-specific downstream freedom -> ranking is no longer guaranteed to be identical, but it is still usually preserved or only weakly reshuffled.
- **NH3 / MeOH:** catalyst properties activate materially different downstream pathways and the decision frontier can be substantially reshaped.

The result therefore does not require the manuscript to claim that every process condition is fixed in order for preservation to occur. A more precise statement is:

> **Ranking preservation remains robust under moderate downstream flexibility, whereas strong inversion requires candidate-specific coupling large enough to overcome the upstream separation between candidates.**

For the current Au/TiO2 baseline, that separation is large enough that a generic +/-25% candidate-specific downstream perturbation preserves the complete order in about 93.5% of draws, and +/-30% still leaves the rank structure largely intact.

## Writing boundary

This V1.2 result should not yet replace V1.1 as the main literature-calibrated control, because the relaxed multiplier is a robustness envelope rather than a mechanistic process model. If used in the manuscript, it is best presented as a sensitivity/robustness extension showing that rank preservation is not an artefact of requiring perfectly identical downstream conditions.

## Reproducibility

- Baseline: `data/rank_preservation_control_v1_1.csv`
- Script: `data/rank_preservation_partial_relaxation.py`
- Output: `data/rank_preservation_partial_relaxation.csv`
- Draws: 100,000 per envelope
- Base seed: 20260907
