# Results at a glance

Snapshot: **2026-09-06**

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

## Decision-aware AI benchmark

Formal DISCOVER single-model snapshot:

- **11** scientific actions
- **1 CU = 1000 MKM state solves**
- **70** policy-E runs
- **392** total scored traces with A-D baselines
- **35/35** complete correct anonymous decisions
- **34/35** exact break-even recoveries
- **0** infrastructure retries
- **0** action errors

The benchmark evaluates scientific compute allocation rather than generic tool-use success.
