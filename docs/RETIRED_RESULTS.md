# Retired and superseded results

This page is the single repository note for results that appeared in earlier development stages but must not be used in the current manuscript, figures or manuscript-facing data tables.

The active scientific sources are **NH3-FINAL-1.1**, **MEOH-D01-v3**, **Au/TiO2-RP V1.1** with V1.3 as supporting robustness, **DISCOVER V1**, and **DISCOVER-BOUNDARY-C1**. Current headline values are in [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md) and [`../data/manuscript_headline_results_2026-09-17.csv`](../data/manuscript_headline_results_2026-09-17.csv).

## NH3-FINAL-1.0

NH3-FINAL-1.0 and its headline values are superseded by **NH3-FINAL-1.1**. The earlier pressure-boundary result, including the former edge optimum, is not a current manuscript result. Current NH3 claims must trace to the frozen FINAL-1.1 source harness under `provenance/nh3_final_1_1/`.

## Historical cross-reaction leverage ratio

The previously reported normalized MeOH/NH3 leverage ratio **273-410** (midpoint approximately **328**) is retired from the current manuscript. The provenance audit classified the metric as `METRIC_EQUIVALENCE_NOT_ESTABLISHED`: the historical NH3 economic-leverage implementation could not be established sufficiently to promote that ratio under the current evidence package.

The current cross-reaction result is therefore qualitative at the pathway level:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

No replacement cross-reaction ratio is introduced.

## Preliminary Au/TiO2 control files

The preliminary Au/TiO2 V1 compact dataset and the intermediate V1.2 partial-relaxation stress test are retired from the active `data/` directory. **Au/TiO2-RP V1.1** is the canonical rank-preservation control; **V1.3** is the supporting semi-open robustness extension.

## Early DISCOVER compact snapshot

The early strong-tier-only DISCOVER compact snapshot is retired from the active `data/` directory because the manuscript-level Agent evidence is now the frozen cross-model DISCOVER V1 result plus DISCOVER-BOUNDARY-C1. Raw traces, frozen hashes and provenance records remain the authoritative evidence.

## Narrow-window counting correction

Early C1 summaries used a permissive narrow-window count that treated any bounded process-window construction as narrowing. The canonical rule now requires both:

1. a window strictly smaller than the full 14,136-state domain; and
2. successful use of that window by a later scoped action.

Under this rule, narrow-window allocation is confined to the strong tier in the measured boundary series: **7/7 at 150 CU, 20/20 at 175 CU, 1/8 at 200 CU, 0/20 at 225 CU and 0/9 at 250 CU**. The weaker tiers have **0** canonical narrow-window uses in the measured cells.

## Repository policy

Retired compact tables and intermediate analyses may be removed from the active tree when they are superseded. Frozen source provenance, audit records and Git history are retained so that the development history remains traceable without mixing obsolete values into the current manuscript-facing data surface.
