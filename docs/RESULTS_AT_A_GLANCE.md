# Results at a glance

Snapshot: **2026-09-10**

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

The reshuffle is metric-independent at the global-statistics level: STY per g Re, single-pass yield and STY per g catalyst all give rho = 0.20, tau = 0.00 and 3/6 inversions. Only the identity of the upstream winner depends on the metric.

Purge robustness (396 levels, 0.5–40%): the per-Re winner is **never** the economic winner, the highest-conversion state is **never** the economic winner, rho <= **0.40** and >= **2/6** pairs invert at every purge level. Per-candidate purge reoptimization gives 1 wt% Re / 200 C > 5 wt% Re / 200 C > 1 wt% Re / 250 C > 5 wt% Re / 250 C (rho 0.40, tau 0.33, 2/6), all optima at the 0.5% bound; 2% stays canonical.

Boundary: the candidates are catalyst–temperature states at measured literature points; the loop variable (purge) is reoptimized per candidate, T/P are not. This isolates the selectivity–recycle channel, complementary to the NH3 activity–inventory–severity channel. Re purchase price is excluded from the NPC by design.

## Methanol selectivity–recycle mechanism

Local leverage at the 5 wt% Re / 250 C benchmark is:

```text
STY                    0.00289
single-pass conversion 0.05883
CH4 suppression        0.37579
```

CH4 suppression is about **6.39x** more leveraged than single-pass conversion and about **130x** more leveraged than STY in this benchmark.

The explicit loop couples methane formation to H2 feed loss, inert accumulation, purge, recycle compression and equipment burden. The most methane-rich state, **5 wt% Re / 250 C** with **S_CH4 = 0.25**, has the highest NPC (**1258 EUR/t**) despite the highest single-pass conversion.

## Cross-reaction pathway comparison — qualitative-only

The current supported cross-reaction statement is mechanistic:

```text
NH3   : activity -> catalyst inventory / reactor demand
MeOH  : selectivity -> feed loss / purge / recycle
```

The MeOH CH4-suppression leverage **0.3757939** remains directly traceable. The historical denominator-aligned MeOH/NH3 ratio **273–410** (midpoint ~**328**) is retained only as an archived pre-FINAL-1.1 result. GitHub Actions run **34449914480** returned **METRIC_EQUIVALENCE_NOT_ESTABLISHED** because the exact historical NH3 TOF economic-leverage implementation and the frozen FINAL-1.1 source harness are not retained in this repository.

Accordingly, no current quantitative cross-reaction ratio is reported. The paper retains the reaction-specific pathway contrast and does not manufacture a replacement metric.

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

For the **primary 273.15–293.15 K window**, the moderate stress case gives:

- exact full order preserved: **92.16%**
- mean Spearman rho: **0.99214**
- fraction with rho >= 0.9: **99.98%**
- mean pairwise inversions: **0.0786**

For the wider **273.15–313.15 K sensitivity window**, the same moderate stress gives:

- exact full order preserved: **72.62%**
- mean Spearman rho: **0.96802**
- fraction with rho >= 0.9: **97.56%**
- mean pairwise inversions: **0.3012**

The interpretation is deliberately narrower than a full TEA: **rank preservation does not require a perfectly fixed operating point; moderate candidate-specific kinetic and operating freedom can produce occasional local reshuffling while leaving the overall rank structure strongly preserved.**

## Decision-aware AI benchmark — DISCOVER V1

DISCOVER V1 is frozen. On the **anonymous closed-book task**, complete decision recovery was:

```text
nano        6/35
mini       15/35
strong     35/35
```

The complete decision requires the full chain: economic winner -> decision pair -> backward target -> reachability verdict. The pooled tier trend in P(full) is strong (Cochran-Armitage Z = **6.95**).

The original pre-registered Agent-specific Go criterion for **policy E > fixed-VOI policy D** was **not met across model tiers**. The apparent 200-CU adaptive advantage in V1 therefore required a boundary-focused confirmatory extension rather than a stronger universal-superiority claim.

## DISCOVER-BOUNDARY-C1 — confirmatory boundary result

C1 retains the frozen DISCOVER V1 task, prompt, 11-tool interface, CU model, scorer and stopping rule. The deterministic fixed-VOI policy D reaches the complete scientific decision at **206 CU**.

```text
                     175 CU          225 CU
strong E              19/20           20/20
mini E                  0/20            6/20
nano E                  0/20            0/20
D fixed-VOI          incomplete       complete
```

At 175 CU, narrow-window construction is used in **20/20 strong**, **4/20 mini**, and **0/20 nano** runs. At 225 CU, strong E reaches full decision at a median of approximately **218 CU** versus **206 CU** for D.

Phase B was a cost-motivated reduced extension at 175 and 225 CU: **80/80 formal runs**, **0 smoke runs**, **0 infrastructure retries**, **0 driver exceptions**, and frozen hashes **15/15 PASS** before and after.

The post-C1 manuscript claim is therefore a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed policy threshold**, not universal adaptive superiority or universal raw-compute saving.

## Audit state

The promoted NH3-FINAL-1.1, MeOH D01 v3, Au/TiO2 and DISCOVER/C1 headline results remain frozen. The second-pass audit identified one targeted exception: **F9A cross-reaction quantitative leverage must be revalidated under NH3-FINAL-1.1**. F1–F6 remain held for raw provenance/asset closure rather than numerical contradiction.

Audit records: `docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md`, `docs/CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md`, and `data/claim_evidence_registry_2026-09-10.csv`.
