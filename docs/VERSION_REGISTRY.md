# Canonical version and naming registry

Snapshot: **2026-09-17**

This file is the human-readable source of truth for naming across the repository and manuscript. Version numbers belong to separate families and must not be compared across families.

## Canonical naming

| Family | Canonical label | Status | Scientific role |
|---|---|---|---|
| Ammonia scientific model | **NH3-FINAL-1.1** | frozen canonical | Current NH3 ranking, uncertainty, process reoptimization and backward-design results |
| Methanol reaction case | **MEOH-D01-v3** | frozen canonical case | Four Re/TiO2 catalyst-temperature states; explicit recycle/separation economics |
| Rank-preservation control | **Au/TiO2-RP V1.1** | frozen canonical control | Literature-calibrated monotonic-mapping counterfactual |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | supporting extension | Semi-open temperature/feed/kinetic robustness test |
| Agent architecture | **Decision-aware Agent Harness** | current umbrella name | Layer A deterministic harness + Layer B decision layer |
| Drift-diagnosis benchmark | **DRIFT v2** | completed supporting benchmark | Model/interface drift diagnosis |
| Reaction-transfer benchmark | **TRANSFER v1** | completed supporting benchmark | Reaction transfer and minimum-sufficient-model selection |
| Formal decision-allocation benchmark | **DISCOVER V1** | frozen canonical Agent benchmark | Closed-book, budgeted anonymous decision allocation |
| Boundary confirmatory extension | **DISCOVER-BOUNDARY-C1** | completed confirmatory extension | Boundary mapping on the unchanged DISCOVER V1 protocol |
| Future DISCOVER redesign | **DISCOVER V2** | reserved | Any future change to the frozen V1 protocol |

## Architecture vocabulary

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
  -> identify unresolved decision component
  -> choose admissible scientific action
  -> execute Layer A calculation
  -> update ranking / feasibility / reachability
  -> stop / continue / redirect
```

## Agent benchmark hierarchy

- **DRIFT v2**: supporting diagnostic benchmark for model/interface consistency.
- **TRANSFER v1**: supporting reaction-transfer benchmark.
- **DISCOVER V1**: frozen formal benchmark for closed-book, budgeted decision allocation.
- **DISCOVER-BOUNDARY-C1**: confirmatory extension on the unchanged DISCOVER V1 protocol; it does not define a new protocol version.
- **DISCOVER V2**: reserved for a future protocol redesign.

## Current manuscript-eligible Agent claim

DISCOVER V1 anonymous complete-decision recovery:

- nano: **6/35**
- mini: **15/35**
- strong: **35/35**

The positive V1 result is model-capability dependence in full decision-chain execution. The original stronger hypothesis that adaptive policy E would show universal cross-tier superiority over fixed-VOI policy D was **not supported**.

DISCOVER-BOUNDARY-C1 sharpens the boundary without changing the frozen protocol:

- fixed-VOI policy D completes at **206 CU**;
- strong at 175 CU: **19/20** complete decisions while D is incomplete;
- strong at 225 CU: **20/20** while D is complete;
- mini at 175 / 225 CU: **0/20 / 6/20**;
- nano at 175 / 225 CU: **0/20 / 0/20**;
- **75 CU** is the lowest tested stable strong-tier complete-decision budget;
- canonical narrow-window allocation is used by the strong tier below the full-enumeration regime and by neither weaker tier in the measured C1 cells;
- under the non-binding 5000-CU allowance, median final strong-tier spend is **714 CU**.

Manuscript-safe interpretation:

> **Under the frozen benchmark, adaptive complete-decision recovery below the fixed-policy completion threshold is model-tier dependent and budget localized; it is not a universal raw-compute saving.**

## Scientific-model hierarchy

### NH3

Use **NH3-FINAL-1.1** for all current manuscript values.

### MeOH

Use **MEOH-D01-v3** for the four-state ranking reshuffle and selectivity-recycle analysis. The candidates are catalyst-temperature states, not independently reoptimized catalyst identities.

### Au/TiO2

Use **Au/TiO2-RP V1.1** as the canonical rank-preservation control. Use **Au/TiO2-RP V1.3** only as supporting semi-open robustness.

## Naming policy

1. Do not use a bare `V1`, `V2` or `v0.5` without the family name.
2. Frozen filenames and hash-pinned protocol files remain unchanged for provenance.
3. Human-facing text should use the canonical labels in this registry.
4. Historical aliases belong only in provenance/audit material or [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).
5. New protocol changes receive a new family-specific version rather than silently replacing a frozen result.
6. Confirmatory sampling on an unchanged protocol may use an extension label such as `DISCOVER-BOUNDARY-C1`.
7. Manuscript text should cite the canonical scientific model first and supporting robustness/diagnostic versions separately.

## Primary files

- Current project state: `../STATUS.md`
- Current numerical summary: `RESULTS_AT_A_GLANCE.md`
- Retired/superseded record: `RETIRED_RESULTS.md`
- MeOH reconstruction: `MEOH_RANKING_INVERSION.md`
- Au/TiO2 canonical control: `RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md`
- Au/TiO2 supporting robustness: `RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`
- Agent architecture: `AGENT_HARNESS.md`
- DISCOVER V1 formal report: `CROSS_MODEL_DISCOVER_V1.md`
- DISCOVER V1 statistics: `CROSS_MODEL_STATS_V1.md`
- C1 source/result records: `DISCOVER_BOUNDARY_C1_*`
- Machine-readable registry: `../data/version_registry.json`
