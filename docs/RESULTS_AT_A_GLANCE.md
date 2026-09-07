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

## Methanol candidate-state ranking inversion

The restored D01 v3 CO2-to-MeOH case contains four Re/TiO2 catalyst–temperature states evaluated through the same explicit recycle/separation loop at **2% purge**.

Using **STY per g Re** as the upstream intrinsic-productivity metric:

```text
Upstream intrinsic rank                  Economic NPC rank
1 wt% Re, 250 C   #1   65 g/gRe/h       5 wt% Re, 200 C   #1   943 EUR/t
1 wt% Re, 200 C   #2   55                1 wt% Re, 200 C   #2   967 EUR/t
5 wt% Re, 200 C   #3   18        ->      1 wt% Re, 250 C   #3   975 EUR/t
5 wt% Re, 250 C   #4   16                5 wt% Re, 250 C   #4   1258 EUR/t
```

Rank statistics:

- Spearman rho: **0.20**
- Kendall tau: **0.00**
- Pairwise inversions: **3 of 6**
- Upstream per-Re winner: **1 wt% Re / 250 C**, falling to economic rank **#3**
- Economic winner: **5 wt% Re / 200 C**

The top-rank reversal is conditional on the upstream screening metric. If upstream performance is defined by single-pass yield or STY per g catalyst, rho/tau and the 3/6 pairwise inversion count remain the same, but the upstream winner coincides with the economic winner. The decision-frontier inversion is therefore specific to the **Re-normalized intrinsic metric**.

Boundary: these are catalyst–temperature states at measured literature points, not four independently reoptimized catalyst identities. Re purchase price is excluded from the NPC by design.

## Methanol selectivity–recycle mechanism

Local leverage at the 5 wt% Re / 250 C benchmark is:

```text
STY                    0.00289
single-pass conversion 0.05883
CH4 suppression        0.37579
```

CH4 suppression is about **6.39x** more leveraged than single-pass conversion and about **130x** more leveraged than STY in this benchmark.

The explicit loop couples methane formation to H2 feed loss, inert accumulation, purge, recycle compression and equipment burden. The most methane-rich state, **5 wt% Re / 250 C** with **S_CH4 = 0.25**, has the highest NPC (**1258 EUR/t**) despite the highest single-pass conversion.

## Cross-reaction leverage

After cost-denominator alignment:

- MeOH CH4 suppression / NH3 TOF leverage = **273-410**
- Midpoint = approximately **328**

This is the quantitative basis for the pathway-specific interpretation:

```text
NH3   : activity -> catalyst inventory / reactor demand
MeOH  : selectivity -> feed loss / purge / recycle
```

Together with the direct MeOH rank reconstruction, the cross-reaction result shows that ranking changes arise through different catalyst-to-process pathways and can also depend on the upstream screening objective.

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

This V1.1 control remains the **canonical falsification control**: the multiscale implementation can preserve an upstream ordering when the downstream mapping remains physically monotonic.

### Semi-open robustness extension — V1.3

V1.3 relaxes the perfectly fixed operating point without replacing V1.1. Each particle-size state can independently search temperature and O2/CO ratio inside a literature-constrained low-temperature envelope, while candidate-specific activity prefactors and apparent activation energies are perturbed. The process topology and Au/TiO2 chemistry remain common.

For the **primary 273.15–293.15 K window**, the moderate stress case (10% independent activity-prefactor CV and 2 kJ/mol independent Ea perturbation) gives:

- exact full order preserved: **92.16%**
- mean Spearman rho: **0.99214**
- fraction with rho >= 0.9: **99.98%**
- mean pairwise inversions: **0.0786**

For the wider **273.15–313.15 K sensitivity window**, the same moderate stress gives:

- exact full order preserved: **72.62%**
- mean Spearman rho: **0.96802**
- fraction with rho >= 0.9: **97.56%**
- mean pairwise inversions: **0.3012**

The interpretation is deliberately narrower than a full TEA: **rank preservation does not require a perfectly fixed operating point; moderate candidate-specific kinetic and operating freedom can produce occasional local reshuffling while leaving the overall rank structure strongly preserved.** V1.3 remains a supporting robustness result because the operating penalties are generic monotone penalties rather than a fully literature-derived industrial cost model.

Primary evidence: `docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`, `data/rank_preservation_semiopen_v1_3.py`, and `data/rank_preservation_semiopen_v1_3_summary.csv`.

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
