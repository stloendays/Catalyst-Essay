# Results at a glance

Snapshot: **2026-09-20**

This page contains the current audited baseline plus the completed **2026-09-20 supervisor-requested targeted analyses**. Execution record: [`../analysis/supervisor_2026_09_20/README.md`](../analysis/supervisor_2026_09_20/README.md). Superseded values and intermediate development results are documented separately in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).

## Ammonia ranking inversion

```text
Atomic activity       Industrial economic ranking
Ru   #1               Fe   #1   15.292 USD/t NH3
Os   #2        ->     Ru   #2   22.031 USD/t NH3
Fe   #3               Os   #3   25.832 USD/t NH3
```

Decision-frontier rank statistics:

- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- Pairwise inversions: **2 of 3**
- Preferred-candidate identity: **Ru -> Fe**
- Full 15-metal raw Spearman rho: **0.929**

Because the frontier contains only three candidates, rho and tau are descriptive rank-rearrangement summaries. The direct decision-level evidence is the **2/3 pairwise inversion structure and the change in Top-1 identity**.

## Uncertainty and actionability

For Fe under the 90 m3 catalyst-bed criterion and 1,000 descriptor-uncertainty draws:

- feasible: **79.9%**
- **economic Top-1 probability: 68.1% (681/1000)**
- atomic-to-economic Top-1 survival: **28.2%**
- Top-3 actionable: **94.0%**

The 68.1% and 28.2% values are different metrics: the former is P(Fe is the economic winner); the latter is P(atomic Top-1 = economic Top-1).

Under the preregistered 5,000-draw **cost-side** Monte Carlo, **P(C_Fe < C_Ru) = 1.000**. The Ru activity-parity distribution is **70.78x / 174.27x / 462.00x** at p05 / median / p95.

## Backward target versus reachable headroom

- Ru activity improvement required for Fe cost parity: **201.22x**
- scaling-consistent headroom at 673 K: **1.090x**
- maximum headroom over the frozen process-state library: **2.525x**
- required / maximum reachable ratio: approximately **79.7x**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**

The activity-only path therefore does not close the Ru-Fe economic gap within the frozen scaling-consistent design space.

## Ru-price counterfactual and canonical cost gap

Canonical Fe / Ru costs are **15.292 / 22.031 USD/t NH3**, a Ru-Fe gap of **6.739 USD/t**. Decomposition of that gap gives fresh-feed compression **+4.632**, metal inventory **+1.763**, compressor CAPEX **+1.181**, refrigeration **+0.629**, vessel pressure **-0.733**, recycle compression **-0.647** and reactor base **-0.086 USD/t**.

When Ru metal price is set equal to Fe = **8 USD/kg** and Ru is fully reoptimized, Ru moves to **425 C / 170 bar / 30 C** and costs **14.712 USD/t**, which is **0.580 USD/t below Fe**. The Fe-over-Ru inversion therefore does not survive price equalization.

The supported mechanism is **metal cost coupled to process reoptimization**; process penalties alone are not sufficient to keep Fe ahead of equal-priced Ru in the current model.

## Canonical operating points

- Fe: approximately **425 C / 180 bar / 30 C separator**
- Ru: approximately **450 C / 425 bar / 25 C separator**
- Os: broad shallow high-pressure minimum

## Catalyst-economic levers in NH3-FINAL-1.1

```text
metal recovery      0.69
catalyst lifetime   0.16
electricity         0.12 at 20 USD/MWh
bed cap             0.00 in the current regime
pressure upper cap  not a valid lever after boundary closure
```

The strongest tested non-activity route is metal recovery, followed by catalyst lifetime.

## Methanol catalyst-state ranking reshuffle

The canonical **MEOH-D01-v3** case contains four Re/TiO2 catalyst-temperature states evaluated through the explicit recycle/separation loop at **2% purge**.

Using STY per g Re as the upstream intrinsic-productivity metric:

```text
Upstream intrinsic rank                  Economic NPC rank
1 wt% Re, 250 C   #1   65 g/gRe/h       5 wt% Re, 200 C   #1   943 EUR/t
1 wt% Re, 200 C   #2   55                1 wt% Re, 200 C   #2   967 EUR/t
5 wt% Re, 200 C   #3   18        ->      1 wt% Re, 250 C   #3   975 EUR/t
5 wt% Re, 250 C   #4   16                5 wt% Re, 250 C   #4   1258 EUR/t
```

- Spearman rho: **0.20**
- Kendall tau: **0.00**
- Pairwise inversions: **3 of 6**
- Upstream per-Re winner falls from **#1 to economic rank #3**

Across the 396-level purge sweep from 0.5% to 40%, the per-Re winner is never the economic winner, rho does not exceed **0.40**, and at least **2/6** pairs remain inverted.

In the 2026-09-20 cost-parameter MC, the four-candidate economic order is preserved in **5,000/5,000** draws under the canonical D01 boundary. A separately labelled active-Re replacement extension likewise preserves the same order in **5,000/5,000** draws.

## Methanol selectivity-recycle mechanism

Local leverage at 5 wt% Re / 250 C:

```text
STY                    0.00289
single-pass conversion 0.05883
CH4 suppression        0.37579
```

CH4 suppression is approximately **6.39x** more leveraged than single-pass conversion and about **130x** more leveraged than STY in this benchmark. The explicit loop couples methane formation to H2 feed loss, inert accumulation, purge, recycle compression and equipment burden.

## Cross-reaction pathway comparison

The current cross-reaction result is mechanistic:

```text
NH3
intrinsic activity + metal cost
 -> catalyst inventory + preferred operating regime
 -> compression / reactor / equipment burden

MeOH
selectivity
 -> reactant loss / gas accumulation
 -> purge / recycle / compression
```

Each reaction is evaluated against its own frozen downstream economic objective. Absolute NH3 and MeOH cost values are not compared across reactions; the transferable object is the catalyst-to-process coupling topology.

No current quantitative cross-reaction leverage ratio is reported. The retired historical metric is documented only in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).

## Rank-preservation control

The literature-calibrated **Au/TiO2-RP V1.1** control preserves the complete 2-6 nm order:

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
- 6 nm / 2 nm required-catalyst ratio: **8.064x**

### Supporting semi-open robustness — V1.3

For the primary 273.15-293.15 K window under moderate stress:

- exact full order preserved: **92.16%**
- mean Spearman rho: **0.99214**
- rho >= 0.9 in **99.98%** of draws

For the wider 273.15-313.15 K sensitivity window:

- exact full order preserved: **72.62%**
- mean Spearman rho: **0.96802**
- rho >= 0.9 in **97.56%** of draws

V1.1 remains the canonical control; V1.3 is supporting robustness.

## Decision-aware AI benchmark — DISCOVER V1

On the frozen anonymous closed-book task, complete decision recovery was:

```text
nano        6/35
mini       15/35
strong     35/35
```

The frozen primary endpoint is `full_decision_correct = winner_correct ∧ pair_decision_correct ∧ reachability_correct`: economic winner, decision pair and reachability verdict. The workflow uses `BACKWARD` to support the reachability classification, but numerical recovery of the backward parity multiplier is a separate quantitative secondary endpoint. The original across-tier adaptive-vs-fixed superiority criterion was not met.

## DISCOVER-BOUNDARY-C1

The deterministic fixed-VOI policy reaches the complete scientific decision at **206 CU**.

```text
                     175 CU          225 CU
strong adaptive       19/20           20/20
mini adaptive           0/20            6/20
nano adaptive           0/20            0/20
fixed-VOI             incomplete       complete
```

For the strong tier, **75 CU** is the lowest tested stable complete-decision budget. At **50 CU**, completion is **13/20**, while winner and decision pair remain 20/20 and reachability is the limiting component.

The primary decision endpoint and the quantitative target separate. Strong adaptive reaches **20/20 complete decisions at 75 CU**, where canonical **201.22x** backward parity-multiplier recovery is only **9/20**; that quantitative target reaches **20/20 at 225 CU**.

Under the canonical narrow-window rule, the strong tier uses narrow-window allocation in **7/7 at 150 CU**, **20/20 at 175 CU**, **1/8 at 200 CU**, **0/20 at 225 CU** and **0/9 at 250 CU**. In the same 175-CU cell the weaker tiers show **0/20 mini** and **0/20 nano**, and neither weak tier has canonical narrow-window use in any measured cell.

Under the non-binding 5000-CU allowance, the strong tier still completes 20/20. Median complete-decision stabilization is **566 CU**, median final spend is **714 CU**, median post-stability overrun is **148 CU**, and canonical narrow-window use is **0/20**. The interpretation is therefore not only post-stability overspending: without binding budget pressure, the policy also stops compressing the process search and reaches decision stability much later.

The manuscript claim is therefore a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy completion threshold**.

Oracle analysis gives a **7-CU scorer-complete floor** and a **22-CU protocol-complete S1-S3 minimum**, with 22 CU used for manuscript normalization. Relative to 22 CU: 75 CU = **3.41x**, the strong 75-CU cell median decision-stable spend of 52.5 CU = **2.39x**, fixed-policy 206 CU = **9.36x**, and non-binding decision-stable median 566 CU = **25.73x**.

## Targeted confirmation status

The 2026-09-20 requested analyses are **complete**. Machine-readable results and figures are under [`../analysis/supervisor_2026_09_20/`](../analysis/supervisor_2026_09_20/).

## Evidence state

NH3-FINAL-1.1, MEOH-D01-v3, Au/TiO2-RP V1.1/V1.3 and DISCOVER/C1 remain the audited provenance families. The 2026-09-20 extensions change interpretation and uncertainty reporting without overwriting those frozen sources. The publication-facing manuscript now uses six composite main figures assembled from the existing provenance-bearing source assets; the composite render step remains a production task.

Primary evidence maps: `data/claim_evidence_registry_2026-09-10.csv` and `data/figure_lock_registry_2026-09-10.csv`.
