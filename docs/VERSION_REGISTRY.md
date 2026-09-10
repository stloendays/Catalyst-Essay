# Canonical version and naming registry

Snapshot: 2026-09-10

This file is the human-readable source of truth for naming across the repository, manuscript notes and Notion. Version numbers belong to separate families and must not be compared across families.

## Canonical naming

| Family | Canonical label | Status | Scientific role |
|---|---|---|---|
| Ammonia scientific model | **NH3-FINAL-1.1** | frozen canonical | Current NH3 ranking, uncertainty, process reoptimization and backward-design results |
| Methanol reaction case | **MEOH-D01-v3** | canonical case | Four Re/TiO2 catalyst-temperature states; explicit recycle/separation economics and ranking reconstruction |
| Rank-preservation control | **Au/TiO2-RP V1.1** | canonical control | Literature-calibrated fixed-condition monotonic mapping used for the manuscript counterfactual |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | latest supporting extension | Semi-open temperature/feed/kinetic robustness test; supporting only, not a replacement TEA |
| Agent architecture | **Decision-aware Agent Harness** | current umbrella name | Layer A deterministic multiscale harness + Layer B decision layer |
| Drift-diagnosis benchmark | **DRIFT v2** | completed supporting benchmark | Model/interface drift diagnosis; legacy label: drift benchmark v2 |
| Reaction-transfer benchmark | **TRANSFER v1** | completed supporting benchmark | Reaction transfer, minimum-sufficient-model and next-calculation selection; legacy label: extrapolation benchmark v1 |
| Formal decision-allocation benchmark | **DISCOVER V1** | frozen canonical Agent benchmark | Closed-book, budgeted, anonymous decision allocation; original cross-model evaluation complete |
| Boundary confirmatory extension | **DISCOVER-BOUNDARY-C1** | completed confirmatory extension | Higher-n strong-tier boundary test plus reduced two-budget mini/nano Phase B on the frozen V1 protocol |
| Future DISCOVER redesign | **DISCOVER V2** | reserved, not completed | Any future change to frozen V1 task/prompt/action schema/cost model/scorer/stopping rule/policy-D constants |

## Architecture vocabulary

Use the following terms consistently:

```text
Decision-aware Agent Harness

Layer A — deterministic multiscale harness
  descriptor / DFT
  -> scaling + BEP
  -> microkinetics
  -> reactor / process
  -> economics
  -> ranking / uncertainty / backward design

Layer B — decision layer
  inspect current evidence
  -> identify decision-sensitive uncertainty / catalyst lever
  -> choose admissible scientific action
  -> execute Layer A tool/calculation
  -> update ranking / feasibility / reachability evidence
  -> stop / continue / redirect
```

Layer B may also perform model-interface transfer decisions in the TRANSFER v1 prototype: identify which modules can be reused/adapted/rebuilt, propose the minimum sufficient model, identify candidate levers and score the next calculations.

## Agent benchmark hierarchy

The Agent-related benchmark names refer to different tasks and must not be merged into one version sequence:

- **DRIFT v2**: supporting diagnostic benchmark for model/interface consistency.
- **TRANSFER v1**: supporting reaction-transfer benchmark for model transfer and next-calculation selection.
- **DISCOVER V1**: frozen formal benchmark for closed-book, budgeted decision allocation.
- **DISCOVER-BOUNDARY-C1**: confirmatory extension on the unchanged DISCOVER V1 protocol; it adds sampling at the decision boundary and does not define a new protocol version.

Therefore, `DISCOVER-BOUNDARY-C1` is **not DISCOVER V2**. `DISCOVER V2` remains reserved for a future protocol redesign.

## Current manuscript-eligible Agent claim

The original formal DISCOVER V1 result remains part of the evidence base:

- anonymous complete-decision recovery: nano **6/35**, mini **15/35**, strong **35/35**;
- positive result: full decision-chain execution is model-capability dependent;
- negative result: adaptive policy E does not show universal cross-tier superiority over fixed-VOI D.

The completed **DISCOVER-BOUNDARY-C1** extension sharpens the boundary claim without changing the frozen protocol:

- deterministic fixed-VOI D reaches a full decision at **206 CU**;
- strong model at **175 CU**: **19/20** full decisions, Wilson 95% CI **[0.76, 0.99]**, while D is incomplete;
- strong model at **225 CU**: **20/20**, while D is complete;
- mini at **175 / 225 CU**: **0/20 / 6/20**;
- nano at **175 / 225 CU**: **0/20 / 0/20**;
- strong narrow-window construction at 175 CU: **20/20**, versus mini **4/20** and nano **0/20**;
- above the D threshold, strong E reaches the full decision at 218-221 CU versus D at 206 CU, so the result is a **budget-localized decision-completion advantage**, not a universal raw-compute saving.

Manuscript-safe interpretation:

> **Under the frozen benchmark protocol, the adaptive decision-recovery advantage below the fixed policy's completion threshold is model-tier dependent: the strong model exploits a narrow-window allocation strategy that does not transfer to the two tested weaker tiers. Policy advantage, model capability and raw compute efficiency are separate quantities.**

Phase B used a cost-motivated reduced design fixed before the first Phase B API call: mini and nano were evaluated only at **175 and 225 CU**, 20 formal runs per cell, with **0 smoke runs**. The post-run audit of this deviation is recorded in `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`.

DRIFT v2 and TRANSFER v1 support the broader description of the Agent Harness, but they should not replace DISCOVER V1 / C1 as the formal quantitative decision-allocation evidence.

## Scientific-model hierarchy

### NH3

Use **NH3-FINAL-1.1** for all current manuscript numbers. NH3-FINAL-1.0 is historical only.

### MeOH

Use **MEOH-D01-v3** for the restored four-state ranking inversion and selectivity-recycle analysis. The states are catalyst-temperature states, not four independently reoptimized catalyst identities.

### Au/TiO2

Use **Au/TiO2-RP V1.1** as the canonical rank-preservation control because it is literature calibrated and physically interpretable. Use **Au/TiO2-RP V1.3** as the latest robustness extension showing that preservation remains strong under moderate semi-open kinetic/operating freedom. A higher version number here does not automatically mean a stronger canonical claim: V1.3 contains generic monotone process penalties and therefore remains supporting evidence.

## Naming policy

1. Do not use a bare `V1`, `V2` or `v0.5` without the family name.
2. Frozen filenames and hash-pinned DISCOVER V1 protocol files remain unchanged for provenance.
3. Human-facing text should use the canonical labels in this registry.
4. Historical aliases may be retained only when explicitly marked `legacy` or `historical`.
5. New protocol changes must receive a new family-specific version rather than silently replacing a frozen result.
6. Confirmatory sampling on the unchanged V1 protocol may use an extension label such as `DISCOVER-BOUNDARY-C1`, but must preserve the original V1 record and document any sampling-design deviation explicitly.
7. Manuscript and GIST text should cite the canonical scientific model first, then supporting robustness/diagnostic versions separately.

## Primary files

- NH3 canonical status: `STATUS.md`
- MeOH reconstruction: `docs/MEOH_RANKING_INVERSION.md`
- Au/TiO2 canonical control: `docs/RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md`
- Au/TiO2 supporting robustness: `docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`
- Agent architecture: `docs/AGENT_HARNESS.md`
- DISCOVER V1 formal report: `docs/CROSS_MODEL_DISCOVER_V1.md`
- DISCOVER V1 statistics: `docs/CROSS_MODEL_STATS_V1.md`
- C1 preregistration: `docs/DISCOVER_BOUNDARY_C1_PREREGISTRATION.md`
- C1 Phase A result: `docs/DISCOVER_BOUNDARY_C1_RESULTS.md`
- C1 Phase B result: `docs/DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md`
- C1 design-deviation audit: `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`
- Machine-readable registry: `data/version_registry.json`
