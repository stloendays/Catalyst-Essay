# Results at a glance

Snapshot: **2026-09-07**

## Ammonia ranking inversion

```text
Atomic activity       Industrial economic ranking
Ru   #1               Fe   #1   15.292 USD/t NH3
Os   #2        ->     Ru   #2   22.031 USD/t NH3
Fe   #3               Os   #3   25.832 USD/t NH3
```

**Decision-frontier rank statistics**

- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- Full 15-metal raw Spearman rho: **0.929**

Interpretation: global rank agreement can remain high while the ordering among the most competitive candidates reverses.

## Uncertainty and actionability

For Fe under the 90 m3 catalyst-bed criterion and 1,000 descriptor-uncertainty draws:

- Feasible: **79.9%**
- Top-1 survival: **28.2%**
- Top-3 actionable: **94.0%**

The relevant result is not uncertainty magnitude by itself, but whether the propagated uncertainty changes feasibility or candidate selection.

## Backward target versus reachable headroom

```text
Required Ru activity improvement for Fe cost parity
201.22x

Scaling-consistent reachable headroom
1.090x at 673 K
2.525x maximum over the frozen process-state library
```

Required / maximum reachable ratio: approximately **79.7x**.

The current activity-only path therefore does not close the Ru-Fe economic gap.

## Canonical operating points

- Fe: approximately **425 C / 180 bar / 30 C separator**
- Ru: approximately **450 C / 425 bar / 25 C separator**
- Os: broad shallow high-pressure minimum

The previous 300-bar edge optimum belonged to the archived FINAL-1.0 model and is not a current result.

## Catalyst-economic levers in NH3-FINAL-1.1

Current reach ordering:

```text
metal recovery      0.69
catalyst lifetime   0.16
electricity         0.12 at 20 USD/MWh (weakly discriminatory)
bed cap             0.00 in current regime
pressure upper cap  not a valid lever after boundary closure
```

The strongest tested non-activity route is therefore metal recovery, followed by catalyst lifetime.

## Methanol pathway

Current CO2-to-MeOH benchmark local leverage:

```text
STY                    0.00289
single-pass conversion 0.05883
CH4 suppression        0.37579
```

CH4 suppression is about **6.39x** more leveraged than single-pass conversion and about **130x** more leveraged than STY in this benchmark.

## Cross-reaction leverage

After cost-denominator alignment:

- MeOH CH4 suppression / NH3 TOF leverage = **273-410**
- Midpoint = approximately **328**

This is the quantitative basis for the current pathway-specific interpretation:

```text
NH3   : activity -> catalyst inventory / reactor demand
MeOH  : selectivity -> feed loss / purge / recycle
```

## Rank-preservation control

The literature-calibrated Au/TiO2 CO-oxidation control uses a fixed process condition and a common catalyst chemistry across a 2–6 nm Au particle-size series.

```text
Intrinsic activity rank      Downstream catalyst-burden rank
2 nm   #1                    2 nm   #1
3 nm   #2                    3 nm   #2
4 nm   #3         ->         4 nm   #3
5 nm   #4                    5 nm   #4
6 nm   #5                    6 nm   #5
```

- Spearman rho: **1.000**
- Kendall tau: **1.000**
- Pairwise inversions: **0**
- 10,000/10,000 predefined literature-envelope draws preserve the full ranking
- 6 nm / 2 nm required-mass ratio after literature calibration: **8.064x**
- relative to V1, that mass-ratio spread decreases by **58.5%** while the order remains unchanged

This control supports the methodological statement that multiscale propagation can preserve an upstream ordering when the downstream mapping remains physically monotonic.

## Decision-aware AI benchmark — cross-model result

DISCOVER V1 is frozen. The cross-model evaluation used the same task, prompt, 11-action schema, cost model, scorer, stopping rule and A-D baselines at all three model tiers. The seven CU budgets were **200, 250, 300, 500, 800, 1200 and 2000**, with **5 independent policy-E runs per budget per variant**. The two weaker tiers contributed 140 new traces; the strong-tier V1 traces were reused and re-scored, not re-run.

On the **anonymous closed-book task**, complete decision recovery was:

```text
nano        6/35
mini       15/35
strong     35/35
```

The complete decision requires the full chain: economic winner -> decision pair -> backward target -> reachability verdict. The strong tier completes this chain reliably; weaker tiers more often fail at pair formation or reachability even when the winner is correct. The pooled tier trend in P(full) is strong (Cochran-Armitage Z = **6.95**).

Two results must be kept separate:

1. **Positive workflow-execution result:** decision-aware workflow completion is strongly model-capability dependent, rising from 6/35 to 15/35 to 35/35 across the three tiers.
2. **Negative pre-registered superiority result:** the pre-registered Agent-specific Go criterion for **policy E > fixed-VOI policy D** was **not met across model tiers**. The 200-CU adaptive-scope advantage was repeatable only in the strong tier and did not reproduce in nano or mini.

Therefore the supported claim is: **a strong model can execute and exploit decision-aware allocation, but adaptive Agent superiority over a fixed-VOI strategy is capability-dependent and is not a universal property of the framework.** The negative result is retained; no frozen V1 protocol component was modified to improve it.

Canonical reports: `docs/CROSS_MODEL_DISCOVER_V1.md` and `docs/CROSS_MODEL_STATS_V1.md`.
